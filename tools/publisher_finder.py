"""Publisher & Blogger Outreach Contact Finder

Finds blogs, magazines and publishers in a given niche and location
(e.g. "Event Planning" in "Mohali, Chandigarh, Tricity") that are relevant
to that niche, then extracts publicly listed contact details:

  - Emails found on the site (syntax-checked, optional MX check; NOT verified inboxes)
  - Phone numbers & WhatsApp links
  - Publication name, domain, DA score, bio / description
  - Contact page, guest-post / contribution guidelines page
  - Editor / founder names, job titles and address (from JSON-LD when present)
  - Social profiles (LinkedIn, Instagram, Twitter/X, Facebook)
  - Exports to a formatted Excel (.xlsx) workbook and a CSV.

Note: contacts are scraped from public pages. Include an opt-out line in outreach
(India DPDP Act, and GDPR / CAN-SPAM if you pitch abroad).

Usage:
    finder = PublisherFinder("Event Planning", "Mohali, Chandigarh, Tricity")
    result = finder.search_and_extract()       # single use, closes its HTTP clients
    open("publishers.xlsx", "wb").write(build_publisher_excel(result))
"""
from __future__ import annotations

import csv
import io
import json
import logging
import math
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple
from urllib.parse import unquote, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

try:  # optional: pip install dnspython  (enables the MX check)
    import dns.resolver as _dns
except Exception:  # noqa: BLE001
    _dns = None

log = logging.getLogger(__name__)

# Re-use DA score caching from the opportunities tool if available
try:
    from tools.opportunities import get_da
except Exception:  # noqa: BLE001
    def get_da(domains: list[str]) -> dict[str, tuple[int, str]]:
        return {d: (None, "Unknown") for d in domains}


# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
HEADERS_HTTP = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Search engines, social sites, marketplaces and listing directories are not publishers.
BLOCKED_DOMAINS = {
    "google.com", "google.co.in", "youtube.com", "facebook.com", "twitter.com",
    "x.com", "instagram.com", "linkedin.com", "pinterest.com", "wikipedia.org",
    "quora.com", "reddit.com", "amazon.com", "amazon.in", "flipkart.com",
    "yahoo.com", "bing.com", "duckduckgo.com", "msn.com", "apple.com",
    "microsoft.com", "wordpress.org", "github.com", "play.google.com",
    "justdial.com", "sulekha.com", "indiamart.com", "urbanpro.com", "tripadvisor.com",
    "tripadvisor.in", "yellowpages.com", "yelp.com", "medium.com", "tumblr.com",
    "wedmegood.com", "weddingwire.in", "shaadisaga.com", "bookmyshow.com",
    "eventbrite.com", "eventbrite.in", "naukri.com", "indeed.com", "glassdoor.com",
    "clutch.co", "sortlist.com", "goodfirms.co",
}

JUNK_EMAIL_DOMAINS = {
    "example.com", "domain.com", "email.com", "yoursite.com", "sentry.io",
    "wixpress.com", "cloudflare.com", "gravatar.com", "mysite.com", "test.com",
    "yourdomain.com", "sentry-next.wixpress.com",
}
# Exact local-part matches only (so "namrata@" or "userservices@" are kept).
JUNK_LOCALS = {
    "user", "name", "yourname", "your-name", "someone", "noreply", "no-reply",
    "donotreply", "do-not-reply", "example", "test", "email", "username",
}
FILE_EXTS = {"png", "jpg", "jpeg", "gif", "svg", "webp", "css", "js", "ico", "woff", "woff2", "ttf", "pdf"}
FREE_MAIL = {"gmail.com", "yahoo.com", "yahoo.in", "outlook.com", "hotmail.com",
             "rediffmail.com", "proton.me", "protonmail.com", "icloud.com"}
PREFERRED_LOCALS = ["editor", "editorial", "submission", "guest", "contribute", "content",
                    "press", "partner", "contact", "hello", "info", "admin"]

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}\b")
# Only explicit obfuscations: "[at]", "(at)", "{at}", "[@]" and "[dot]". Never a bare word "at".
_OBF_AT = re.compile(r"\s*[\[\(\{]\s*(?:at|@)\s*[\]\)\}]\s*", re.I)
_OBF_DOT = re.compile(r"\s*[\[\(\{]\s*dot\s*[\]\)\}]\s*", re.I)

# Indian mobile (optionally +91 / 91 / 0 prefix), digit-boundary guarded.
PHONE_RE = re.compile(r"(?<![\d.])(?:(?:\+|00)?91[\-\s.]?)?0?[6-9]\d{4}[\-\s.]?\d{5}(?!\d)")
# Chandigarh / Mohali / Panchkula landline: 0172 + 7 digits.
LANDLINE_RE = re.compile(r"(?<![\d.])(?:(?:\+|00)?91[\-\s.]?)?0?172[\-\s.]?\d{7}(?!\d)")
WA_RE = re.compile(r"(?:wa\.me/|[?&]phone=)\+?(\d{10,13})", re.I)

# Matched against the URL *path* only (never the domain).
GUIDE_PATH = re.compile(
    r"(?:^|[/_-])(write-for-us|writeforus|guest-post(?:ing|s)?|guest-blog(?:ging)?|"
    r"submit-(?:a-)?(?:post|article|guest-post|story)|submissions?|contribute|contributors?|"
    r"become-a-(?:contributor|writer|author|guest-blogger)|guidelines|editorial-(?:policy|guidelines))"
    r"(?:$|[/_.-])", re.I)
CONTACT_PATH = re.compile(
    r"(?:^|[/_-])(contact(?:-us|us)?|reach-us|get-in-touch|about(?:-us|us)?|team|our-team|"
    r"editorial(?:-team)?|advertise(?:-with-us)?|press|authors?)(?:$|[/_.-])", re.I)
BLOG_PATH = re.compile(r"(?:^|[/_-])(blog|blogs|magazine|news|articles|stories|insights)(?:$|[/_.-])", re.I)

ANCHOR_GUIDE = re.compile(
    r"^(write for us|guest post(ing)?|guest blogging|become a (contributor|writer|author)|contribute|"
    r"submit (a |your )?(post|article|guest post|story)|submission guidelines)$", re.I)
ANCHOR_CONTACT = re.compile(
    r"^(contact( us)?|get in touch|reach us|about( us)?|advertise( with us)?|our team|editorial team)$", re.I)
ANCHOR_BLOG = re.compile(r"^(blog|blogs|magazine|news|articles|stories)$", re.I)

PROBE_CONTACT = ["/contact-us", "/contact"]
PROBE_ABOUT = ["/about-us", "/about"]
PROBE_GUIDE = ["/write-for-us", "/guest-post"]

TRICITY_CITIES = ["Mohali", "Chandigarh", "Panchkula", "Zirakpur", "Kharar", "SAS Nagar"]
_TRICITY_ALIASES = {"tricity", "tri-city", "tri city", "chandigarh tricity", "chandigarh tri-city"}
_WORLDWIDE = {"worldwide", "global", "all", ""}

# Niche -> (relevance tokens, query variants). Tokens are prefix-matched (event -> events).
_NICHE_PROFILES = [
    ("event", ["event", "wedding", "party", "celebrat", "decor", "banquet"],
     ["event management", "wedding planning", "party planning", "corporate events"]),
    ("wedding", ["wedding", "bride", "event", "decor", "bridal"],
     ["wedding planner", "bridal", "event planning"]),
]
_STOPWORDS = {"and", "the", "for", "with", "in", "of", "to", "a"}

MIN_RELEVANCE = 3          # publishers scoring below this are dropped
MAX_QUERIES = 14
PAGE_CAP = 1_500_000       # chars of HTML kept per page

_ddg_lock = threading.Lock()
_MX_CACHE: Dict[str, Optional[bool]] = {}


# --------------------------------------------------------------------------- #
# Search
# --------------------------------------------------------------------------- #
def _ddgs_search(query: str, n: int = 12) -> list[dict]:
    """Run a DDG text search; returns dicts with href/title/body (empty list on failure)."""
    with _ddg_lock:
        res: list[dict] = []
        try:
            try:
                from ddgs import DDGS
            except ImportError:
                from duckduckgo_search import DDGS
            with DDGS() as d:
                for kwargs in ({"region": "in-en", "backend": "auto"}, {"backend": "auto"}, {}):
                    try:
                        res = list(d.text(query, max_results=n, **kwargs))
                        if res:
                            break
                    except Exception as e:  # noqa: BLE001
                        log.debug("ddgs %r with %s failed: %s", query, kwargs, e)
            time.sleep(0.5)
        except Exception as e:  # noqa: BLE001
            log.warning("ddgs search failed for %r: %s", query, e)
        return res


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #
def _extract_domain(url: str) -> str:
    netloc = urlparse(url).netloc if "//" in url else url
    netloc = netloc.lower().split("@")[-1].split(":")[0]
    return netloc[4:] if netloc.startswith("www.") else netloc


def _is_blocked(dom: str) -> bool:
    return any(dom == b or dom.endswith("." + b) for b in BLOCKED_DOMAINS)


def _norm_url(u: str) -> str:
    return u.split("#")[0].rstrip("/").lower()


def _dedupe(items: Iterable[str]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for i in items:
        if i and i not in seen:
            seen.add(i)
            out.append(i)
    return out


def _has_mx(domain: str) -> Optional[bool]:
    """True/False if DNS says the domain can/can't receive mail; None if unknown or no dnspython."""
    if _dns is None:
        return None
    if domain in _MX_CACHE:
        return _MX_CACHE[domain]
    result: Optional[bool]
    try:
        result = len(_dns.resolve(domain, "MX", lifetime=4)) > 0
    except _dns.NXDOMAIN:
        result = False
    except _dns.NoAnswer:
        try:
            result = len(_dns.resolve(domain, "A", lifetime=4)) > 0
        except Exception:  # noqa: BLE001
            result = False
    except Exception:  # noqa: BLE001
        result = None
    _MX_CACHE[domain] = result
    return result


def _clean_email(email: str) -> Optional[str]:
    e = email.strip().lower().strip(".,;:()<>[]\"'")
    if not EMAIL_RE.fullmatch(e):
        return None
    local, dom = e.rsplit("@", 1)
    if len(local) > 64 or ".." in e or local in JUNK_LOCALS:
        return None
    if dom.rsplit(".", 1)[-1] in FILE_EXTS:
        return None
    if dom in JUNK_EMAIL_DOMAINS or any(dom.endswith("." + jd) for jd in JUNK_EMAIL_DOMAINS):
        return None
    return e


def _email_rank(e: str, site_domain: str) -> Tuple[int, int, str]:
    """Lower = better: same-site first, then free-mail, then third-party; then editor > info > admin."""
    local, dom = e.split("@", 1)
    if dom == site_domain or dom.endswith("." + site_domain) or site_domain.endswith("." + dom):
        origin = 0
    elif dom in FREE_MAIL:
        origin = 1
    else:
        origin = 2
    pref = next((i for i, p in enumerate(PREFERRED_LOCALS) if p in local), len(PREFERRED_LOCALS))
    return (origin, pref, e)


def _decode_cf(h: str) -> Optional[str]:
    """Decode Cloudflare data-cfemail / email-protection hex."""
    try:
        r = int(h[:2], 16)
        return "".join(chr(int(h[i:i + 2], 16) ^ r) for i in range(2, len(h), 2))
    except Exception:  # noqa: BLE001
        return None


def _emails_from_text(text: str) -> List[str]:
    t = _OBF_DOT.sub(".", _OBF_AT.sub("@", text))
    return EMAIL_RE.findall(t)


def _clean_phone(raw: str) -> Optional[str]:
    """Normalise Indian mobiles / 0172 landlines; accept explicit +CC international numbers only."""
    s = raw.strip()
    d = re.sub(r"\D", "", s)
    plus = s.startswith("+")
    if s.startswith("00"):
        d, plus = d[2:], True

    mobile = None
    if len(d) == 12 and d.startswith("91") and d[2] in "6789":
        mobile = d[2:]
    elif len(d) == 11 and d.startswith("0") and d[1] in "6789":
        mobile = d[1:]
    elif len(d) == 10 and d[0] in "6789":
        mobile = d
    if mobile:
        if len(set(mobile)) <= 2:  # 9999999999, 9898989898 ...
            return None
        return f"+91 {mobile[:5]} {mobile[5:]}"

    for prefix in ("0172", "91172", "172"):
        if d.startswith(prefix) and len(d) == len(prefix) + 7:
            return f"+91 172 {d[len(prefix):]}"

    if plus and 8 <= len(d) <= 15:
        return "+" + d
    return None


def _phones_from_text(text: str) -> List[str]:
    out = []
    for rx in (PHONE_RE, LANDLINE_RE):
        for m in rx.findall(text):
            p = _clean_phone(m)
            if p:
                out.append(p)
    return out


_SOCIAL_RESERVED = {
    "twitter": {"home", "intent", "share", "i", "search", "hashtag", "explore", "login",
                "settings", "privacy", "tos", "messages", "compose", "widgets.js"},
    "instagram": {"p", "reel", "reels", "explore", "accounts", "stories", "tv", "direct"},
    "facebook": {"sharer", "sharer.php", "share", "share.php", "plugins", "dialog", "tr",
                 "login", "login.php", "groups", "events", "watch", "marketplace", "policies",
                 "help", "privacy", "hashtag", "ads"},
}


def _classify_social(urls: Iterable[str]) -> Dict[str, str]:
    out = {"linkedin": "", "twitter": "", "instagram": "", "facebook": ""}
    for u in urls:
        try:
            p = urlparse(u)
        except ValueError:
            continue
        host = (p.netloc or "").lower().split(":")[0]
        host = host[4:] if host.startswith("www.") else host
        segs = [s for s in p.path.split("/") if s]
        if not segs:
            continue
        s0 = segs[0].lower()

        if host == "linkedin.com" or host.endswith(".linkedin.com"):
            if s0 in ("company", "school") and len(segs) > 1:
                if "/company/" not in out["linkedin"]:  # a company page always wins
                    out["linkedin"] = f"https://www.linkedin.com/{s0}/{segs[1]}"
            elif s0 == "in" and len(segs) > 1 and not out["linkedin"]:
                out["linkedin"] = f"https://www.linkedin.com/in/{segs[1]}"
        elif host in ("twitter.com", "x.com", "mobile.twitter.com"):
            if (not out["twitter"] and s0 not in _SOCIAL_RESERVED["twitter"]
                    and re.fullmatch(r"[A-Za-z0-9_]{1,15}", segs[0])):
                out["twitter"] = f"https://x.com/{segs[0]}"
        elif host == "instagram.com" or host.endswith(".instagram.com"):
            if (not out["instagram"] and s0 not in _SOCIAL_RESERVED["instagram"]
                    and re.fullmatch(r"[A-Za-z0-9_.]{1,30}", segs[0])):
                out["instagram"] = f"https://www.instagram.com/{segs[0]}"
        elif host == "facebook.com" or host.endswith(".facebook.com"):
            if out["facebook"] or s0 in _SOCIAL_RESERVED["facebook"]:
                continue
            if s0 == "pages" and len(segs) > 1:
                out["facebook"] = "https://www.facebook.com/" + "/".join(segs[:3])
            elif s0 == "profile.php" and p.query:
                out["facebook"] = f"https://www.facebook.com/profile.php?{p.query}"
            elif re.fullmatch(r"[A-Za-z0-9_.\-]{3,60}", segs[0]):
                out["facebook"] = f"https://www.facebook.com/{segs[0]}"
    return out


def _parse_cities(location: str) -> Tuple[List[str], bool]:
    """Split a location string; expand 'Tricity' into its member cities."""
    if (location or "").strip().lower() in _WORLDWIDE:
        return [], False
    cities: List[str] = []
    tri = False
    for part in re.split(r"[,/|;]+", location):
        p = part.strip()
        if not p:
            continue
        if p.lower() in _TRICITY_ALIASES:
            tri = True
        elif p.lower() not in [c.lower() for c in cities]:
            cities.append(p)
    if tri:
        for c in TRICITY_CITIES:
            if c.lower() not in [x.lower() for x in cities]:
                cities.append(c)
    return cities, tri


# --------------------------------------------------------------------------- #
# Page parsing
# --------------------------------------------------------------------------- #
def _walk_jsonld(node: Any, out: List[Tuple[str, dict]], key: str = "", depth: int = 0) -> None:
    if depth > 6:
        return
    if isinstance(node, list):
        for x in node:
            _walk_jsonld(x, out, key, depth + 1)
    elif isinstance(node, dict):
        out.append((key, node))
        for k, v in node.items():
            if isinstance(v, (dict, list)):
                _walk_jsonld(v, out, k, depth + 1)


def _as_list(v: Any) -> List[Any]:
    return v if isinstance(v, list) else ([] if v in (None, "") else [v])


def _parse_jsonld(blocks: List[Any]) -> Dict[str, Any]:
    info: Dict[str, Any] = {"org_name": "", "emails": [], "phones": [], "address": "",
                            "people": [], "same_as": []}
    nodes: List[Tuple[str, dict]] = []
    for b in blocks:
        _walk_jsonld(b, nodes)

    for key, n in nodes:
        types = [str(t).lower() for t in _as_list(n.get("@type"))]
        is_org = any(t in {"organization", "localbusiness", "newsmediaorganization", "corporation",
                           "professionalservice", "eventvenue"} for t in types)
        if is_org and not info["org_name"] and isinstance(n.get("name"), str):
            info["org_name"] = n["name"].strip()

        for em in _as_list(n.get("email")):
            if isinstance(em, str):
                info["emails"].append(em.replace("mailto:", "").strip())
        for ph in _as_list(n.get("telephone")):
            if isinstance(ph, (str, int)):
                info["phones"].append(str(ph))
        for sa in _as_list(n.get("sameAs")):
            if isinstance(sa, str):
                info["same_as"].append(sa)

        if not info["address"] and "address" in n:
            a = n["address"]
            if isinstance(a, str):
                info["address"] = a.strip()
            elif isinstance(a, dict):
                country = a.get("addressCountry")
                if isinstance(country, dict):
                    country = country.get("name")
                parts = [a.get("streetAddress"), a.get("addressLocality"), a.get("addressRegion"),
                         a.get("postalCode"), country]
                info["address"] = ", ".join(str(x).strip() for x in parts if x and isinstance(x, (str, int)))

        if "person" in types and isinstance(n.get("name"), str):
            title = n.get("jobTitle")
            if title or key in {"founder", "employee", "member", "editor", "owner", "creator"}:
                label = n["name"].strip() + (f" ({title.strip()})" if isinstance(title, str) and title.strip() else "")
                info["people"].append(label)
    return info


def _parse_page(html: str, page_url: str) -> Dict[str, Any]:
    """Pull everything we need out of one page *before* stripping scripts for the text view."""
    soup = BeautifulSoup(html, "html.parser")
    info: Dict[str, Any] = {
        "url": page_url, "title": "", "site_name": "", "description": "", "headings": "",
        "author": "", "links": [], "mailto": [], "tel": [], "wa": [], "cf": [],
        "jsonld": {}, "text": "",
    }

    if soup.title and soup.title.string:
        info["title"] = soup.title.string.strip()
    og = soup.find("meta", attrs={"property": "og:site_name"})
    if og and og.get("content"):
        info["site_name"] = og["content"].strip()
    dtag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
    if dtag and dtag.get("content"):
        info["description"] = re.sub(r"\s+", " ", dtag["content"]).strip()
    atag = soup.find("meta", attrs={"name": "author"})
    if atag and atag.get("content"):
        info["author"] = atag["content"].strip()[:80]
    info["headings"] = " ".join(h.get_text(" ", strip=True) for h in soup.find_all(["h1", "h2", "h3"])[:30])

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        low = href.lower()
        if low.startswith("mailto:"):
            for part in unquote(href[7:].split("?")[0]).split(","):
                info["mailto"].append(part.strip())
        elif low.startswith("tel:"):
            info["tel"].append(unquote(href[4:]))
        elif "email-protection#" in low:
            info["cf"].append(href.split("#", 1)[1])
        elif low.startswith(("#", "javascript:", "data:")) or not href:
            continue
        else:
            if "whatsapp" in low or "wa.me/" in low:
                m = WA_RE.search(href)
                if m:
                    info["wa"].append(m.group(1))
            info["links"].append((urljoin(page_url, href), a.get_text(" ", strip=True)))
    for t in soup.select("[data-cfemail]"):
        info["cf"].append(t.get("data-cfemail", ""))

    blocks = []
    for s in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            blocks.append(json.loads(s.string or s.get_text() or ""))
        except Exception:  # noqa: BLE001
            continue
    info["jsonld"] = _parse_jsonld(blocks)

    for t in soup(["script", "style", "noscript", "template"]):
        t.decompose()
    info["text"] = soup.get_text(" ", strip=True)[:200_000]
    return info


# --------------------------------------------------------------------------- #
# Finder
# --------------------------------------------------------------------------- #
class PublisherFinder:
    def __init__(
        self,
        niche: str,
        location: str = "",
        keywords: str = "",
        max_publishers: int = 20,
        progress: Optional[Callable[[str, int, int], None]] = None,
    ):
        self.niche = (niche or "General Business").strip()
        self.location = (location or "Worldwide").strip()
        self.keywords = (keywords or "").strip()
        self.max_publishers = max(5, min(max_publishers, 50))
        self.progress = progress

        self.cities, self.tricity = _parse_cities(self.location)
        self.loc_tokens = {c.lower() for c in self.cities}
        if self.tricity:
            self.loc_tokens |= {"tricity", "tri-city", "tri city"}
        if not self.loc_tokens:  # unusual free-text location, e.g. "Punjab"
            self.loc_tokens = {t.lower() for t in re.split(r"[,;\s]+", self.location)
                               if len(t) > 3 and t.lower() not in _WORLDWIDE}

        self.variants, tokens = self._niche_profile()
        self._rel_re = (re.compile(r"\b(?:" + "|".join(re.escape(t) for t in tokens) + ")", re.I)
                        if tokens else None)

        self._client = httpx.Client(
            headers=HEADERS_HTTP, timeout=8.0, follow_redirects=True,
            limits=httpx.Limits(max_connections=30, max_keepalive_connections=15),
        )
        self._insecure_client: Optional[httpx.Client] = None
        self._insecure_lock = threading.Lock()

    # ----- lifecycle ------------------------------------------------------- #
    def close(self) -> None:
        for c in (self._client, self._insecure_client):
            try:
                if c is not None:
                    c.close()
            except Exception:  # noqa: BLE001
                pass

    def __enter__(self) -> "PublisherFinder":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def _notify(self, msg: str, step: int = 0, total_steps: int = 4) -> None:
        if self.progress:
            self.progress(msg, step, total_steps)

    # ----- niche relevance ------------------------------------------------- #
    def _niche_profile(self) -> Tuple[List[str], List[str]]:
        low = self.niche.lower()
        for key, tokens, variants in _NICHE_PROFILES:
            if key in low:
                extra = [w for w in re.findall(r"[a-z]{4,}", self.keywords.lower()) if w not in _STOPWORDS]
                return variants, _dedupe(tokens + extra)
        words = [w for w in re.findall(r"[a-z0-9]{3,}", f"{low} {self.keywords.lower()}") if w not in _STOPWORDS]
        return [], _dedupe(words)

    def _relevance(self, head: str, body: str, snippet: str = "") -> int:
        rx = self._rel_re
        if rx is None:
            return MIN_RELEVANCE
        return (len(rx.findall(head)) * 3 + min(len(rx.findall(body)), 15)
                + len(rx.findall(snippet)) * 2)

    # ----- HTTP ------------------------------------------------------------ #
    def _insecure(self) -> httpx.Client:
        with self._insecure_lock:
            if self._insecure_client is None:
                self._insecure_client = httpx.Client(
                    headers=HEADERS_HTTP, timeout=8.0, follow_redirects=True, verify=False)
            return self._insecure_client

    def _get(self, url: str) -> Optional[httpx.Response]:
        """GET with TLS verification; retry without it only on certificate errors."""
        try:
            r = self._client.get(url)
        except httpx.HTTPError as e:
            msg = str(e).upper()
            if "CERTIFICATE" not in msg and "SSL" not in msg:
                return None
            try:
                r = self._insecure().get(url)
            except Exception:  # noqa: BLE001
                return None
        except Exception:  # noqa: BLE001
            return None
        if r.status_code >= 400:
            return None
        ctype = r.headers.get("content-type", "").lower()
        if ctype and "html" not in ctype and "xml" not in ctype:
            return None
        return r

    def _fetch_page(self, url: str) -> Optional[Dict[str, Any]]:
        r = self._get(url)
        if r is None:
            return None
        try:
            return _parse_page(r.text[:PAGE_CAP], str(r.url))
        except Exception as e:  # noqa: BLE001
            log.debug("parse failed %s: %s", url, e)
            return None

    # ----- discovery ------------------------------------------------------- #
    def generate_queries(self) -> list[str]:
        n = self.niche
        kw = self.keywords
        q: List[str] = []

        if self.cities:
            main = self.cities[0]
            q.append(f'{n} blog {main}')
            for c in self.cities[:3]:
                q.append(f'"{n}" "{c}" "write for us" OR "guest post"')
            q.append(f'"{n}" blog OR magazine OR news "{main}"')
            q.append(f'best {n} blogs {main}')
            for c in self.cities[1:3]:
                q.append(f'{n} bloggers {c}')
            if self.tricity:
                q.append(f'"{n}" Tricity blog OR magazine')
            for v in self.variants[:3]:
                q.append(f'{v} blog OR magazine {main}')
            # Few publishers are strictly local, so also look India-wide; location is a ranking bonus.
            q.append(f'{n} "write for us" India')
            q.append(f'best {n} blogs India')
            if self.variants:
                q.append(f'{self.variants[0]} "guest post" India')
            if kw:
                q.append(f'"{n}" {main} {kw}')
        else:
            q.append(f'"{n}" blog OR magazine OR publisher "write for us"')
            q.append(f'top "{n}" blogs "contact us"')
            q.append(f'"{n}" guest post submission websites')
            for v in self.variants[:3]:
                q.append(f'{v} "write for us"')
            if kw:
                q.append(f'"{n}" {kw} blog')
        return _dedupe(q)[:MAX_QUERIES]

    def discover_candidate_domains(self) -> Dict[str, str]:
        """Returns {domain: search snippet text}, best candidates first."""
        self._notify(f"Searching web for {self.niche} publishers in {self.location}...", step=1)
        agg: Dict[str, Dict[str, Any]] = {}

        for q in self.generate_queries():
            for hit in _ddgs_search(q, n=12):
                dom = _extract_domain(hit.get("href") or "")
                if not dom or "." not in dom or _is_blocked(dom):
                    continue
                entry = agg.setdefault(dom, {"hits": 0, "text": ""})
                entry["hits"] += 1
                if len(entry["text"]) < 800:
                    entry["text"] += f" {hit.get('title') or ''} {hit.get('body') or ''}"
            if len(agg) >= self.max_publishers * 4:
                break

        def prio(item: Tuple[str, Dict[str, Any]]) -> int:
            return item[1]["hits"] * 2 + self._relevance("", "", item[1]["text"])

        ordered = sorted(agg.items(), key=prio, reverse=True)
        self._notify(f"Discovered {len(ordered)} candidate publisher domains to inspect.", step=1)
        return {d: v["text"] for d, v in ordered}

    # ----- inspection ------------------------------------------------------ #
    def _probe(self, base: str, paths: List[str], scanned: Set[str]) -> Optional[Dict[str, Any]]:
        for p in paths:
            page = self._fetch_page(urljoin(base, p))
            if not page:
                continue
            final = urlparse(page["url"])
            if final.path.strip("/") == "" or _norm_url(page["url"]) in scanned:
                continue  # redirected back to the homepage = soft 404
            scanned.add(_norm_url(page["url"]))
            return page
        return None

    def inspect_publisher(self, domain: str, snippet: str = "") -> Optional[Dict[str, Any]]:
        """Inspect one domain; returns None if unreachable or not relevant to the niche."""
        home = None
        for scheme in ("https", "http"):
            home = self._fetch_page(f"{scheme}://{domain}/")
            if home:
                break
        if not home:
            return None

        final_url = home["url"]
        site = _extract_domain(final_url)
        if _is_blocked(site):
            return None
        pages: List[Dict[str, Any]] = [home]
        scanned: Set[str] = {_norm_url(final_url)}

        # 1. Classify internal links by URL path (and short, exact anchor text)
        guide_c: List[str] = []
        contact_c: List[str] = []
        blog_signal = False
        for full, anchor in home["links"]:
            if _extract_domain(full) != site:
                continue
            path = urlparse(full).path
            a = anchor.strip()
            short = len(a) <= 40
            if GUIDE_PATH.search(path) or (short and ANCHOR_GUIDE.match(a)):
                guide_c.append(full)
            elif CONTACT_PATH.search(path) or (short and ANCHOR_CONTACT.match(a)):
                contact_c.append(full)
            if BLOG_PATH.search(path) or (short and ANCHOR_BLOG.match(a)):
                blog_signal = True

        def is_contact(u: str) -> bool:
            return bool(re.search(r"contact|get-in-touch|reach-us", urlparse(u).path, re.I))

        contact_c = _dedupe(contact_c)
        contact_page_url = next(iter(sorted([u for u in contact_c if is_contact(u)], key=len)), "")
        guidelines_url = next(iter(sorted(_dedupe(guide_c), key=len)), "")

        # 2. Scan the best discovered pages (contact first, then about/team, then guidelines)
        others = [u for u in sorted(contact_c, key=len) if u != contact_page_url]
        queue = ([contact_page_url] if contact_page_url else []) + others[:2] + \
                ([guidelines_url] if guidelines_url else [])
        for u in queue:
            if _norm_url(u) in scanned:
                continue
            scanned.add(_norm_url(u))
            pg = self._fetch_page(u)
            if pg:
                pages.append(pg)

        # 3. Probe common paths for anything JS menus hid from us
        base = f"{urlparse(final_url).scheme}://{urlparse(final_url).netloc}/"
        if not contact_page_url:
            pg = self._probe(base, PROBE_CONTACT, scanned)
            if pg:
                pages.append(pg)
                contact_page_url = pg["url"]
        if not guidelines_url:
            pg = self._probe(base, PROBE_GUIDE, scanned)
            if pg:
                pages.append(pg)
                guidelines_url = pg["url"]
        if not any(re.search(r"about", urlparse(p["url"]).path, re.I) for p in pages):
            pg = self._probe(base, PROBE_ABOUT, scanned)
            if pg:
                pages.append(pg)

        # 4. Relevance gate
        head = " ".join([home["title"], home["site_name"], home["description"], home["headings"]])
        body = " ".join(p["text"] for p in pages).lower()
        relevance = self._relevance(head, body, snippet)
        if relevance < MIN_RELEVANCE:
            return None

        # 5. Emails (mailto + Cloudflare-protected + JSON-LD + visible text)
        raw_emails: List[str] = []
        for p in pages:
            raw_emails += p["mailto"]
            raw_emails += [d for d in (_decode_cf(h) for h in p["cf"]) if d]
            raw_emails += p["jsonld"].get("emails", [])
            raw_emails += _emails_from_text(p["text"])
        emails = _dedupe(e for e in (_clean_email(x) for x in raw_emails) if e)
        emails = [e for e in emails if _has_mx(e.split("@")[1]) is not False]
        emails.sort(key=lambda e: _email_rank(e, site))

        # 6. Phones / WhatsApp
        wa_numbers: Set[str] = set()
        raw_phones: List[str] = []
        for p in pages:
            raw_phones += p["tel"] + p["jsonld"].get("phones", [])
            raw_phones += _phones_from_text(p["text"])
            for w in p["wa"]:
                norm = _clean_phone(w if w.startswith("91") or len(w) == 10 else "+" + w)
                if norm:
                    wa_numbers.add(norm)
                    raw_phones.append(norm)
        phones = _dedupe(x for x in (_clean_phone(r) for r in raw_phones) if x)
        phones = sorted(phones, key=lambda x: x not in wa_numbers)  # WhatsApp numbers first
        phone_display = [f"{p} (WhatsApp)" if p in wa_numbers else p for p in phones]

        # 7. Identity: name, bio, people, address
        ld_org = next((p["jsonld"]["org_name"] for p in pages if p["jsonld"].get("org_name")), "")
        name = home["site_name"] or ld_org
        if not name and home["title"]:
            parts = [x.strip() for x in re.split(r"\s+[|\-–—:]\s+", home["title"]) if x.strip()]
            stem = re.sub(r"[^a-z0-9]", "", site.split(".")[0])
            match = next((x for x in parts if stem and stem in re.sub(r"[^a-z0-9]", "", x.lower())), "")
            name = match or (parts[-1] if len(parts) > 1 else (parts[0] if parts else ""))
        if not name or len(name) < 2:
            name = site.split(".")[0].title()

        desc = next((p["description"] for p in pages if p["description"]), "")[:300]
        people = _dedupe([x for p in pages for x in p["jsonld"].get("people", [])])
        if home["author"] and not any(home["author"] in x for x in people):
            people.append(home["author"])
        address = next((p["jsonld"]["address"] for p in pages if p["jsonld"].get("address")), "")

        # 8. Socials (from hrefs + JSON-LD sameAs only)
        urls = [u for p in pages for u, _ in p["links"]] + [u for p in pages for u in p["jsonld"].get("same_as", [])]
        social = _classify_social(urls)

        # 9. Location match
        lowered = (body + " " + address.lower())
        location_mentioned = bool(self.loc_tokens) and any(t in lowered for t in self.loc_tokens)

        # 10. Outreach status (guidelines page != "accepts guest posts")
        if emails and phones:
            status = "Email & phone found"
        elif emails:
            status = "Email found"
        elif phones:
            status = "Phone / WhatsApp found"
        elif contact_page_url:
            status = "Contact page only (use form)"
        elif guidelines_url:
            status = "Guidelines page found"
        elif any(social.values()):
            status = "Social channels only"
        else:
            status = "Website only"

        return {
            "name": name[:70],
            "domain": domain,
            "url": final_url,
            "description": desc or f"Publication in the {self.niche} space.",
            "emails": emails[:5],
            "primary_email": emails[0] if emails else "",
            "phones": phone_display[:3],
            "primary_phone": phone_display[0] if phone_display else "",
            "people": people[:5],
            "address": address,
            "contact_page_url": contact_page_url,
            "guidelines_url": guidelines_url,
            "linkedin": social["linkedin"],
            "twitter": social["twitter"],
            "instagram": social["instagram"],
            "facebook": social["facebook"],
            "location_mentioned": location_mentioned,
            "location": self.location,
            "niche": self.niche,
            "relevance": relevance,
            "blog_signal": blog_signal,
            "outreach_status": status,
        }

    def _safe_inspect(self, item: Tuple[str, str]) -> Optional[Dict[str, Any]]:
        domain, snippet = item
        try:
            return self.inspect_publisher(domain, snippet)
        except Exception as e:  # noqa: BLE001
            log.warning("inspect failed for %s: %s", domain, e)
            return None

    # ----- pipeline -------------------------------------------------------- #
    @staticmethod
    def _score(p: Dict[str, Any]) -> float:
        s = min(p["relevance"], 30) * 2
        s += 15 if p["location_mentioned"] else 0
        s += 20 if p["guidelines_url"] else 0
        s += 10 if p["blog_signal"] else 0
        s += 12 if p["emails"] else 0
        s += 6 if p["phones"] else 0
        s += 3 if p["contact_page_url"] else 0
        s += (p.get("da_score") or 0) * 0.3
        return round(s, 1)

    def search_and_extract(self) -> Dict[str, Any]:
        """Discover -> inspect (relevance-filtered) -> DA -> rank. Single use: closes HTTP clients."""
        try:
            return self._run()
        finally:
            self.close()

    def _run(self) -> Dict[str, Any]:
        candidates = self.discover_candidate_domains()
        empty = {
            "niche": self.niche, "location": self.location, "keywords": self.keywords,
            "total_publishers": 0, "publishers": [],
            "summary": {"emails_found": 0, "phones_found": 0, "guidelines_found": 0, "with_contact_form": 0},
        }
        if not candidates:
            empty["notice"] = ("No publisher domains found. The search backend may have failed "
                               "(check the 'ddgs' package) or the query is too narrow.")
            return empty

        to_inspect = list(candidates.items())[: min(self.max_publishers * 3, 120)]
        self._notify(f"Inspecting {len(to_inspect)} websites for relevance and contacts...", step=2)
        with ThreadPoolExecutor(max_workers=8) as ex:
            results = list(ex.map(self._safe_inspect, to_inspect))
        valid = [r for r in results if r]
        dropped = len(to_inspect) - len(valid)

        self._notify("Fetching authority (DA) scores...", step=3)
        try:
            da_map = get_da([p["domain"] for p in valid])
        except Exception as e:  # noqa: BLE001
            log.warning("DA lookup failed: %s", e)
            da_map = {}
        for p in valid:
            da_val, src = da_map.get(p["domain"], (None, "Unknown"))
            p["da_score"], p["da_source"] = da_val, src
            p["score"] = self._score(p)

        valid.sort(key=lambda p: p["score"], reverse=True)
        publishers = valid[: self.max_publishers]

        emails_count = sum(1 for p in publishers if p["emails"])
        phones_count = sum(1 for p in publishers if p["phones"])
        self._notify(f"Completed! {len(publishers)} publishers ({emails_count} with email, "
                     f"{phones_count} with phone/WhatsApp).", step=4)

        return {
            "niche": self.niche,
            "location": self.location,
            "keywords": self.keywords,
            "total_publishers": len(publishers),
            "publishers": publishers,
            "summary": {
                "emails_found": emails_count,
                "phones_found": phones_count,
                "guidelines_found": sum(1 for p in publishers if p["guidelines_url"]),
                "with_contact_form": sum(1 for p in publishers if p["contact_page_url"]),
                "skipped_unreachable_or_irrelevant": dropped,
                "mx_check_enabled": _dns is not None,
            },
            "notice": (
                f"Found {len(publishers)} relevant publishers for '{self.niche}' in {self.location}. "
                f"{emails_count} have extracted emails and {phones_count} have phone/WhatsApp numbers "
                f"(extracted from public pages, not verified)."
            ),
        }


# --------------------------------------------------------------------------- #
# Excel (.xlsx) report
# --------------------------------------------------------------------------- #
FILL_NAVY = "1E3A8A"
FILL_GREEN = "D1FAE5"
FILL_GREY = "F3F4F6"
BORDER_COLOR = "E5E7EB"

# (header, width, key) - key is resolved in _excel_values
_XL_COLUMNS: List[Tuple[str, int, str]] = [
    ("#", 5, "idx"),
    ("Publication / Blog Name", 28, "name"),
    ("Website", 30, "url"),
    ("DA", 8, "da"),
    ("Relevance", 10, "score"),
    ("Primary Email", 30, "primary_email"),
    ("All Emails", 32, "emails"),
    ("Phone / WhatsApp", 24, "phones"),
    ("Contact Person(s)", 30, "people"),
    ("Address", 30, "address"),
    ("Outreach Status", 24, "status"),
    ("Contact Page", 30, "contact"),
    ("Guidelines Page", 30, "guide"),
    ("Location Match", 16, "loc"),
    ("About / Bio", 48, "desc"),
    ("LinkedIn", 28, "linkedin"),
    ("Instagram", 26, "instagram"),
    ("Twitter / X", 24, "twitter"),
    ("Facebook", 26, "facebook"),
    ("Outreach Notes", 28, "notes"),
]
_XL_LINK_KEYS = {"url", "contact", "guide", "linkedin", "instagram", "twitter", "facebook"}
_XL_CENTER_KEYS = {"idx", "da", "score", "loc"}


def _xl_safe(v: Any) -> Any:
    """Stop text that starts with '=' from being stored as a formula."""
    if isinstance(v, str) and v.startswith(("=", "@")):
        return "'" + v
    return v


def _excel_values(pub: dict, idx: int, has_location: bool) -> Dict[str, Any]:
    if has_location:
        loc = "Yes (local)" if pub.get("location_mentioned") else "No"
    else:
        loc = "N/A"
    return {
        "idx": idx,
        "name": pub.get("name", ""),
        "url": pub.get("url", ""),
        "da": pub.get("da_score"),            # blank (None) keeps numeric sorting intact
        "score": pub.get("score"),
        "primary_email": pub.get("primary_email", ""),
        "emails": "\n".join(pub.get("emails", [])),
        "phones": "\n".join(pub.get("phones", [])),
        "people": "\n".join(pub.get("people", [])),
        "address": pub.get("address", ""),
        "status": pub.get("outreach_status", ""),
        "contact": pub.get("contact_page_url", ""),
        "guide": pub.get("guidelines_url", ""),
        "loc": loc,
        "desc": pub.get("description", ""),
        "linkedin": pub.get("linkedin", ""),
        "instagram": pub.get("instagram", ""),
        "twitter": pub.get("twitter", ""),
        "facebook": pub.get("facebook", ""),
        "notes": "",
    }


def build_publisher_excel(result: dict) -> bytes:
    """Build a styled workbook: clickable links, wrapped text, frozen header, filters."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Publisher Contacts"

    thin = Side(style="thin", color=BORDER_COLOR)
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    ncols = len(_XL_COLUMNS)
    last_col = get_column_letter(ncols)

    niche = result.get("niche", "General")
    location = result.get("location", "Worldwide")
    publishers = result.get("publishers", [])
    summary = result.get("summary", {})
    has_location = (location or "").strip().lower() not in _WORLDWIDE

    ws.merge_cells(f"A1:{last_col}1")
    c = ws["A1"]
    c.value = f"Publisher & Blogger Outreach Contacts: {niche} ({location})"
    c.font = Font(name="Calibri", size=15, bold=True, color="FFFFFF")
    c.fill = PatternFill(start_color=FILL_NAVY, end_color=FILL_NAVY, fill_type="solid")
    c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.row_dimensions[1].height = 36

    ws.merge_cells(f"A2:{last_col}2")
    c = ws["A2"]
    c.value = (
        f"Total: {result.get('total_publishers', len(publishers))}  |  "
        f"With email: {summary.get('emails_found', 0)}  |  "
        f"With phone/WhatsApp: {summary.get('phones_found', 0)}  |  "
        f"Guidelines pages: {summary.get('guidelines_found', 0)}"
    )
    c.font = Font(name="Calibri", size=10, italic=True, color="4B5563")
    c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.row_dimensions[2].height = 20

    ws.merge_cells(f"A3:{last_col}3")
    c = ws["A3"]
    c.value = ("Contacts were extracted from public web pages and are not verified. "
               "Include an opt-out line in outreach (DPDP Act / GDPR / CAN-SPAM).")
    c.font = Font(name="Calibri", size=9, italic=True, color="9CA3AF")
    c.alignment = Alignment(horizontal="left", vertical="center", indent=1)

    header_row = 4
    ws.row_dimensions[header_row].height = 26
    for ci, (title, width, key) in enumerate(_XL_COLUMNS, start=1):
        cell = ws.cell(row=header_row, column=ci, value=title)
        cell.font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="3B82F6", end_color="3B82F6", fill_type="solid")
        cell.alignment = Alignment(horizontal="center" if key in _XL_CENTER_KEYS else "left",
                                   vertical="center", wrap_text=True)
        cell.border = border
        ws.column_dimensions[get_column_letter(ci)].width = width

    for r, pub in enumerate(publishers, start=header_row + 1):
        vals = _excel_values(pub, r - header_row, has_location)
        has_contact = bool(pub.get("emails") or pub.get("phones"))
        lines = 1
        for ci, (title, width, key) in enumerate(_XL_COLUMNS, start=1):
            val = vals[key]
            cell = ws.cell(row=r, column=ci, value=_xl_safe(val))
            cell.border = border
            cell.font = Font(name="Calibri", size=10, bold=(key in {"primary_email", "phones"} and has_contact))
            cell.alignment = Alignment(
                horizontal="center" if key in _XL_CENTER_KEYS else "left",
                vertical="top", wrap_text=True)
            if has_contact:
                cell.fill = PatternFill(start_color=FILL_GREEN, end_color=FILL_GREEN, fill_type="solid")
            elif r % 2 == 0:
                cell.fill = PatternFill(start_color=FILL_GREY, end_color=FILL_GREY, fill_type="solid")

            if key in _XL_LINK_KEYS and isinstance(val, str) and val.startswith("http") and len(val) < 2000:
                cell.hyperlink = val
                cell.font = Font(name="Calibri", size=10, color="2563EB", underline="single")
            elif key == "primary_email" and val:
                cell.hyperlink = f"mailto:{val}"
                cell.font = Font(name="Calibri", size=10, bold=True, color="2563EB", underline="single")

            if isinstance(val, str) and val:
                est = sum(math.ceil(max(len(part), 1) / max(width - 2, 1)) for part in val.split("\n"))
                lines = max(lines, est)
        ws.row_dimensions[r].height = min(max(20, 14 * lines + 4), 150)

    ws.freeze_panes = f"A{header_row + 1}"
    ws.auto_filter.ref = f"A{header_row}:{last_col}{header_row + max(len(publishers), 1)}"

    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


# --------------------------------------------------------------------------- #
# CSV report
# --------------------------------------------------------------------------- #
def _csv_safe(v: Any) -> Any:
    """Excel treats cells starting with = + - @ as formulas; keep phones like +91 as text."""
    if isinstance(v, str) and v[:1] in ("=", "+", "-", "@"):
        return "'" + v
    return v


def build_publisher_csv(result: dict, bom: bool = True) -> str:
    """CSV text. bom=True prepends a UTF-8 BOM so Excel reads Hindi/Punjabi names correctly.
    If you write the file with encoding='utf-8-sig' yourself, pass bom=False."""
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow([
        "#", "Publisher Name", "Website URL", "Domain", "DA", "Relevance", "Primary Email",
        "All Emails", "Phones / WhatsApp", "Contact Person(s)", "Address", "Outreach Status",
        "Contact Page URL", "Guidelines Page URL", "Location Match", "Bio / Description",
        "LinkedIn", "Instagram", "Twitter / X", "Facebook",
    ])
    has_location = (result.get("location") or "").strip().lower() not in _WORLDWIDE
    for i, p in enumerate(result.get("publishers", []), start=1):
        loc = ("Yes" if p.get("location_mentioned") else "No") if has_location else "N/A"
        row = [
            i, p.get("name", ""), p.get("url", ""), p.get("domain", ""),
            p.get("da_score") if p.get("da_score") is not None else "",
            p.get("score", ""), p.get("primary_email", ""),
            "; ".join(p.get("emails", [])), "; ".join(p.get("phones", [])),
            "; ".join(p.get("people", [])), p.get("address", ""), p.get("outreach_status", ""),
            p.get("contact_page_url", ""), p.get("guidelines_url", ""), loc,
            p.get("description", ""), p.get("linkedin", ""), p.get("instagram", ""),
            p.get("twitter", ""), p.get("facebook", ""),
        ]
        w.writerow([_csv_safe(c) for c in row])
    text = out.getvalue()
    return ("\ufeff" + text) if bom else text


# --------------------------------------------------------------------------- #
# CLI:  python publisher_finder.py "Event Planning" "Mohali, Chandigarh, Tricity"
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)
    niche_arg = sys.argv[1] if len(sys.argv) > 1 else "Event Planning"
    loc_arg = sys.argv[2] if len(sys.argv) > 2 else "Mohali, Chandigarh, Tricity"
    res = PublisherFinder(niche_arg, loc_arg, progress=lambda m, s, t: print(f"[{s}/{t}] {m}")).search_and_extract()
    with open("publishers.xlsx", "wb") as fh:
        fh.write(build_publisher_excel(res))
    with open("publishers.csv", "w", newline="", encoding="utf-8") as fh:
        fh.write(build_publisher_csv(res))
    print(res["notice"])