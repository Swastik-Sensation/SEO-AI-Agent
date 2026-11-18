"""Layered presence checker: is <target> (e.g. tracevenue.com) already registered / linked on a site?

Every site ends with exactly one of three tags:

  Registered      a link to the target was found, with proof (evidence URL + method + confidence)
  Not Registered  every applicable check ran successfully and found nothing
  Unverified      checks were blocked / inconclusive / not possible -> SEO team confirms manually

No single check is trusted on its own. Layers (cheap -> expensive):

  1. Team tracker      URLs the SEO team says they submitted -> fetched live and inspected
  2. Backlink data     referring domains/pages from GSC / Ahrefs / Moz export (or Moz API)
  3. Profile probe     predictable profile URLs (tracevenue.wordpress.com, medium.com/@tracevenue ...)
  4. Footprint search  site:<domain> "tracevenue.com" via ddgs (positive-only, last resort)

Link detection is also layered, so a link that is really there is not missed:
  - parsed <a href> anchors (also catches redirect wrappers like ?u=https%3A%2F%2Ftracevenue.com)
  - raw page source (escaped URLs, JSON blobs, plain-text URLs)
  - optional headless-browser render for JS-only pages (SEO_USE_PLAYWRIGHT=1)

Rules that keep "Not Registered" honest:
  - blocked / login-wall / JS-only / timeout / bot challenge  -> Unverified, never Not Registered
  - sites that answer 200 for non-existent profiles (soft-404) -> probe ignored as a negative
  - if the team says "done" but we cannot see the link      -> Unverified (needs a human)

Env vars (all optional):
  SEO_USE_PLAYWRIGHT=1       render JS-only pages with Playwright (pip install playwright; playwright install chromium)
  SEO_FOOTPRINT=1|0          enable footprint search layer (default 1)
  SEO_FOOTPRINT_MAX=60       max footprint searches per run (search engines rate-limit)
  SEO_MOZ_BACKLINKS=1        pull referring domains from the Moz Links API (uses MOZ_ACCESS_ID / MOZ_SECRET_KEY)
  SEO_MOZ_BACKLINK_PAGES=10  pages of 50 referring domains to pull
  SEO_REGISTERED_TTL_DAYS=14 re-verify "Registered" results after this many days
  SEO_CACHE_DB               shared SQLite file (same one opportunities.py uses)

Self-test the probe URL patterns against a handle you KNOW exists on most platforms:
  python tools/presence_checker.py --probe-test microsoft
"""
from __future__ import annotations

import csv
import io
import logging
import os
import random
import re
import socket
import sqlite3
import string
import sys
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date, datetime
from html import unescape
from html.parser import HTMLParser
from typing import Callable
from urllib.parse import unquote, urlparse

import httpx

log = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #
CACHE_DB = os.getenv("SEO_CACHE_DB", "da_cache.sqlite3")
REGISTERED_TTL = int(os.getenv("SEO_REGISTERED_TTL_DAYS", "14")) * 24 * 3600

try:
    import playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

USE_PLAYWRIGHT = os.getenv("SEO_USE_PLAYWRIGHT", "1" if PLAYWRIGHT_AVAILABLE else "0") == "1"
USE_FOOTPRINT = os.getenv("SEO_FOOTPRINT", "1") == "1"
FOOTPRINT_MAX = int(os.getenv("SEO_FOOTPRINT_MAX", "60"))
USE_MOZ_BACKLINKS = os.getenv("SEO_MOZ_BACKLINKS", "0") == "1"
MOZ_BACKLINK_PAGES = int(os.getenv("SEO_MOZ_BACKLINK_PAGES", "10"))
MOZ_ID = os.getenv("MOZ_ACCESS_ID", "")
MOZ_SECRET = os.getenv("MOZ_SECRET_KEY", "")

FETCH_TIMEOUT = 12
MAX_HTML_CHARS = 1_500_000
BROWSER_UA = os.getenv(
    "SEO_CHECK_UA",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
)
BLOCK_CODES = {401, 403, 405, 406, 429, 451, 999}      # 999 = LinkedIn
RANK = {"High": 3, "Medium": 2, "Low": 1}

# Hosts where several seeds share one root domain (google.com, apple.com): keep the full host as key
HOST_LEVEL_ROOTS = {"google.com", "apple.com"}
# Platform hosted on a different domain than the seed's domain
DOMAIN_ALIASES = {
    "blogspot.com": "blogger.com",
    "jimdofree.com": "jimdo.com",
    "mystrikingly.com": "strikingly.com",
    "yolasite.com": "yola.com",
    "hashnode.dev": "hashnode.com",
    "site123.me": "site123.com",
    "wordpress.org": "wordpress.org",
}
TWO_LEVEL_SUFFIXES = {"co.uk", "com.au", "co.in", "com.br", "co.nz", "co.za", "org.uk", "com.sg"}


# --------------------------------------------------------------------------- #
# Domain helpers
# --------------------------------------------------------------------------- #
def _host(s: str) -> str:
    s = (s or "").strip().lower()
    host = urlparse(s if "//" in s else f"//{s}").netloc or s
    host = host.split("@")[-1].split(":")[0]
    return host[4:] if host.startswith("www.") else host


def root_domain(url_or_host: str) -> str:
    host = _host(url_or_host)
    parts = host.split(".")
    if len(parts) >= 3 and ".".join(parts[-2:]) in TWO_LEVEL_SUFFIXES:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


def site_key(url_or_host: str) -> str:
    """Canonical key used to match seeds, team sheet rows and backlink rows to each other."""
    host = _host(url_or_host)
    root = root_domain(host)
    if root in HOST_LEVEL_ROOTS and host != root:
        return host
    return DOMAIN_ALIASES.get(root, root)


def slug_variants(target: str, project_name: str = "", handles: list[str] | None = None) -> list[str]:
    """Handles to try on profile URLs: tracevenue, Tracevenue, tracevenue1 ... (case-preserved)."""
    out: list[str] = []
    for h in (handles or []):
        h = re.sub(r"[^A-Za-z0-9._-]", "", (h or "").lstrip("@"))
        if h:
            out.append(h)
    out.append(root_domain(target).split(".")[0])
    name = (project_name or "")
    out.append(re.sub(r"[^A-Za-z0-9]", "", name))
    out.append(re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-"))
    return list(dict.fromkeys(s for s in out if s))[:6]


def _fill(pattern: str, slug: str, target: str) -> str:
    return pattern.replace("{slug}", slug).replace("{target}", target)


# --------------------------------------------------------------------------- #
# Link detection (HTML analysis)
# --------------------------------------------------------------------------- #
@dataclass
class Finding:
    level: str = "none"          # "anchor" | "source" | "none"
    href: str = ""
    rel: str = ""
    anchor_text: str = ""

    @property
    def link_type(self) -> str:
        return "nofollow" if any(k in self.rel for k in ("nofollow", "ugc", "sponsored")) else "dofollow"


class _AnchorParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.anchors: list[tuple[str, str, str]] = []
        self._cur: list[str] | None = None

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            d = dict(attrs)
            href = d.get("href")
            self._cur = [href, d.get("rel") or "", ""] if href else None

    def handle_data(self, data):
        if self._cur is not None and len(self._cur[2]) < 120:
            self._cur[2] += data

    def handle_endtag(self, tag):
        if tag == "a" and self._cur is not None:
            self.anchors.append((self._cur[0], self._cur[1], self._cur[2]))
            self._cur = None


def _domain_regex(target: str) -> re.Pattern:
    t = re.escape(target.lower())
    # must not be glued to other characters: blocks "nottracevenue.com" and "tracevenue.com.evil.io"
    return re.compile(rf"(?<![A-Za-z0-9-])(?:[A-Za-z0-9-]+\.)*{t}(?![A-Za-z0-9-])(?!\.[A-Za-z0-9])", re.I)


def analyze_html(html: str, target: str) -> Finding:
    """Looks for the target in anchors first, then anywhere in the (decoded) source."""
    if not html:
        return Finding()
    target = target.lower()
    low = html.lower()
    decoded = unquote(unescape(low)).replace("\\/", "/")
    if target not in low and target not in decoded:
        return Finding()
    rx = _domain_regex(target)
    parser = _AnchorParser()
    try:
        parser.feed(html)
        parser.close()
    except Exception:                                       # noqa: BLE001
        pass
    for href, rel, text in parser.anchors:
        h = unquote(unescape(href)).lower()
        if target in h and rx.search(h):
            return Finding("anchor", href.strip(), rel.lower(), re.sub(r"\s+", " ", text).strip()[:80])
    if rx.search(decoded):
        return Finding("source")
    return Finding()


_TAG_RE = re.compile(r"<script.*?</script>|<style.*?</style>|<[^>]+>", re.S | re.I)
_JS_MARKERS = ('id="root"', "id='root'", 'id="__next"', 'id="app"', "enable javascript",
               "requires javascript", "you need to enable javascript", "<noscript")
_CHALLENGE = ("just a moment...", "cf-browser-verification", "attention required! | cloudflare",
              "verify you are human", "are you a robot", "px-captcha", "/cdn-cgi/challenge-platform")
_LOGIN_HINTS = ("/login", "/signin", "/sign-in", "/accounts/login", "accounts.google.com", "/auth/")


def looks_js_shell(html: str) -> bool:
    text = re.sub(r"\s+", " ", _TAG_RE.sub(" ", html)).strip()
    low = html.lower()
    return len(text) < 500 and any(m in low for m in _JS_MARKERS)


def looks_blocked(html: str) -> bool:
    return len(html) < 40000 and any(m in html[:8000].lower() for m in _CHALLENGE)


# --------------------------------------------------------------------------- #
# HTTP fetching
# --------------------------------------------------------------------------- #
@dataclass
class Fetched:
    state: str                   # ok | missing | blocked | error
    status: int = 0
    html: str = ""
    final_url: str = ""
    reason: str = ""


GENUINE_HEADERS = {
    "User-Agent": BROWSER_UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Ch-Ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}

try:
    import primp
    _primp_client = primp.Client(
        impersonate="chrome",
        impersonate_os="windows",
        follow_redirects=True,
        timeout=FETCH_TIMEOUT,
    )
except Exception:
    _primp_client = None

_client = httpx.Client(
    headers=GENUINE_HEADERS,
    follow_redirects=True,
    timeout=FETCH_TIMEOUT,
    limits=httpx.Limits(max_connections=60, max_keepalive_connections=20),
)
_DNS_ERRORS = ("name or service not known", "nodename nor servname", "getaddrinfo failed",
               "no address associated", "temporary failure in name resolution")
_net_cache = {"ts": 0.0, "ok": True}


def _network_ok() -> bool:
    """Guards against reading a local network outage as 'this profile does not exist'."""
    if time.time() - _net_cache["ts"] < 60:
        return _net_cache["ok"]
    try:
        socket.getaddrinfo("example.com", 443)
        ok = True
    except OSError:
        ok = False
    _net_cache.update(ts=time.time(), ok=ok)
    return ok


def fetch(url: str, retries: int = 1) -> Fetched:
    reason = "unknown error"
    for attempt in range(retries + 1):
        html = ""
        code = 0
        final = url
        try:
            if _primp_client is not None:
                r = _primp_client.get(url)
                code = r.status_code
                html = r.text[:MAX_HTML_CHARS]
                final = str(r.url) if hasattr(r, "url") else url
            else:
                r = _client.get(url)
                code = r.status_code
                html = r.text[:MAX_HTML_CHARS]
                final = str(r.url)
        except Exception as exc:
            # Fallback to standard httpx if primp fails or raises exception
            try:
                r = _client.get(url)
                code = r.status_code
                html = r.text[:MAX_HTML_CHARS]
                final = str(r.url)
            except httpx.TimeoutException:
                reason = "timeout"
                time.sleep(0.8 * (attempt + 1))
                continue
            except httpx.ConnectError as e:
                if any(k in str(e).lower() for k in _DNS_ERRORS) and _network_ok():
                    return Fetched("missing", 0, reason="host does not exist (DNS)")
                reason = "connection error"
                time.sleep(0.8 * (attempt + 1))
                continue
            except Exception as e:                              # noqa: BLE001
                reason = f"{type(e).__name__}"
                continue

        if code in BLOCK_CODES:
            return Fetched("blocked", code, reason=f"HTTP {code}")
        if code in (404, 410):
            return Fetched("missing", code, reason=f"HTTP {code}")
        if code >= 500 and attempt < retries:
            reason = f"HTTP {code}"
            time.sleep(0.8 * (attempt + 1))
            continue
        if code >= 400:
            return Fetched("error", code, reason=f"HTTP {code}")
        if looks_blocked(html):
            return Fetched("blocked", code, reason="bot challenge page")
        req_path, fin_path = urlparse(url).path.lower(), urlparse(final).path.lower()
        if any(h in (fin_path + " " + urlparse(final).netloc.lower()) for h in _LOGIN_HINTS) \
                and not any(h in req_path for h in _LOGIN_HINTS):
            return Fetched("blocked", code, final_url=final, reason="redirected to login")
        return Fetched("ok", code, html, final)
    return Fetched("error", 0, reason=reason)


_pw_lock = threading.Lock()
_pw_warned = False


def render_with_playwright(url: str) -> str:
    """Renders page with real headless Chromium to bypass bot challenges and execute JS."""
    global _pw_warned
    if not USE_PLAYWRIGHT:
        return ""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        if not _pw_warned:
            log.warning("Playwright is not installed")
            _pw_warned = True
        return ""
    with _pw_lock:                                          # one browser at a time keeps memory sane
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
                )
                try:
                    context = browser.new_context(
                        user_agent=BROWSER_UA,
                        viewport={"width": 1366, "height": 768},
                        locale="en-US",
                    )
                    page = context.new_page()
                    page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                    page.goto(url, wait_until="domcontentloaded", timeout=18000)
                    time.sleep(1.0)
                    return page.content()
                finally:
                    browser.close()
        except Exception as e:                              # noqa: BLE001
            log.warning("Playwright render failed for %s: %s", url, e)
            return ""


# --------------------------------------------------------------------------- #
# Signals
# --------------------------------------------------------------------------- #
@dataclass
class Signal:
    layer: str                   # Team tracker | Backlink data | Profile probe | Footprint search
    kind: str                    # positive | negative | failure
    confidence: str = "Medium"   # High | Medium | Low
    url: str = ""
    note: str = ""
    blocking: bool = True        # a blocking failure prevents "Not Registered"
    link_type: str = ""


# --------------------------------------------------------------------------- #
# SQLite cache (only "Registered" results are cached; everything else is rechecked every run)
# --------------------------------------------------------------------------- #
_db_lock = threading.Lock()


def _db() -> sqlite3.Connection:
    conn = sqlite3.connect(CACHE_DB, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS presence_cache ("
        "target TEXT, domain TEXT, method TEXT, evidence_url TEXT, confidence TEXT, "
        "link_type TEXT, note TEXT, ts REAL, matched_suffix TEXT, PRIMARY KEY (target, domain))"
    )
    try:
        cur = conn.execute("PRAGMA table_info(presence_cache)")
        cols = [c[1] for c in cur.fetchall()]
        if "matched_suffix" not in cols:
            conn.execute("ALTER TABLE presence_cache ADD COLUMN matched_suffix TEXT")
    except Exception:
        pass
    return conn


def _cache_get_all_registered(target: str) -> dict[str, dict]:
    """Fetch all cached Registered results for a target in one query."""
    out: dict[str, dict] = {}
    cutoff = time.time() - REGISTERED_TTL
    with _db_lock, _db() as conn:
        try:
            cur = conn.execute(
                "SELECT domain, method, evidence_url, confidence, link_type, note, ts, matched_suffix "
                "FROM presence_cache WHERE target=? AND ts>?", (target, cutoff)
            )
            for row in cur.fetchall():
                out[row[0]] = {
                    "registered": "Registered",
                    "check_method": f"Cached: {row[1]}",
                    "evidence_url": row[2] or "",
                    "confidence": row[3] or "High",
                    "link_type": row[4] or "",
                    "check_note": row[5] or "",
                    "checked_on": datetime.fromtimestamp(row[6]).date().isoformat(),
                    "link_suffix": row[7] if len(row) > 7 and row[7] else ""
                }
        except Exception as e:
            log.warning("Failed to fetch registered cache: %s", e)
    return out


def _cache_get(target: str, domain: str) -> dict | None:
    with _db_lock, _db() as conn:
        row = conn.execute(
            "SELECT method, evidence_url, confidence, link_type, note, ts, matched_suffix FROM presence_cache "
            "WHERE target=? AND domain=? AND ts>?", (target, domain, time.time() - REGISTERED_TTL),
        ).fetchone()
    if not row:
        return None
    return {"registered": "Registered", "check_method": f"Cached: {row[0]}", "evidence_url": row[1] or "",
            "confidence": row[2] or "High", "link_type": row[3] or "", "check_note": row[4] or "",
            "checked_on": datetime.fromtimestamp(row[5]).date().isoformat(),
            "link_suffix": row[6] if len(row) > 6 and row[6] else ""}


def _cache_put(target: str, domain: str, res: dict) -> None:
    matched = res.get("link_suffix") or ""
    with _db_lock, _db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO presence_cache (target, domain, method, evidence_url, confidence, link_type, note, ts, matched_suffix) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (target, domain, res.get("check_method", ""), res.get("evidence_url", ""), res.get("confidence", "High"),
             res.get("link_type", ""), res.get("check_note", ""), time.time(), matched),
        )


# --------------------------------------------------------------------------- #
# Footprint search helper
# --------------------------------------------------------------------------- #
_ddg_lock = threading.Lock()


def _ddgs(query: str, n: int = 6) -> tuple[list[dict], bool]:
    with _ddg_lock:                                         # serialise + throttle: engines rate-limit hard
        try:
            from ddgs import DDGS
            with DDGS() as d:
                try:
                    res = list(d.text(query, backend="api", max_results=n))
                except Exception:
                    res = list(d.text(query, backend="html", max_results=n))
            time.sleep(random.uniform(0.5, 1.0))
            return res, True
        except Exception as e:                              # noqa: BLE001
            if "no results" in str(e).lower() or "0 results" in str(e).lower():
                return [], True
            log.warning("ddgs failed for %r: %s", query, e)
            time.sleep(1.0)
            return [], False


# --------------------------------------------------------------------------- #
# The checker
# --------------------------------------------------------------------------- #
class PresenceChecker:
    def __init__(self, target: str, project_name: str = "", handles: list[str] | None = None,
                 referring: dict[str, list[str]] | None = None,
                 team_done: dict[str, list[str]] | None = None,
                 trust_team_reports: bool = False, force_recheck: bool = False,
                 link_suffix: str = "",
                 link_suffixes: list[str] | str | None = None,
                 progress: Callable[[str], None] | None = None):
        self.target = root_domain(target)

        # Parse multiple suffixes (e.g. ['/tracevenue', '/Tracevenue', '/tracevenue1'])
        parsed_suffixes: list[str] = []
        if isinstance(link_suffixes, str) and link_suffixes.strip():
            parsed_suffixes.extend(re.split(r"[,;\n\r\t]+", link_suffixes))
        elif isinstance(link_suffixes, (list, tuple)):
            for s in link_suffixes:
                if isinstance(s, str) and s.strip():
                    parsed_suffixes.extend(re.split(r"[,;\n\r\t]+", s))

        if link_suffix and isinstance(link_suffix, str) and link_suffix.strip():
            parsed_suffixes.extend(re.split(r"[,;\n\r\t]+", link_suffix))

        # Clean slugs while preserving case
        clean_slugs: list[str] = []
        display_suffixes: list[str] = []
        seen_slugs = set()

        for item in parsed_suffixes:
            clean = re.sub(r"^[/@]+", "", item.strip()).strip()
            if clean and clean not in seen_slugs:
                seen_slugs.add(clean)
                clean_slugs.append(clean)
                display_suffixes.append(f"/{clean}")

        if not clean_slugs:
            default_clean = root_domain(target).split(".")[0].strip()
            if default_clean:
                clean_slugs.append(default_clean)
                display_suffixes.append(f"/{default_clean}")

        self.clean_slugs = clean_slugs
        self.link_suffixes = display_suffixes
        self.link_suffix = ", ".join(display_suffixes)

        base_slugs = slug_variants(self.target, project_name, handles)
        self.slugs = []
        for s in clean_slugs + base_slugs:
            if s and s not in self.slugs:
                self.slugs.append(s)

        self.referring = referring or {}
        self.referring_loaded = bool(self.referring)
        self.team_done = team_done or {}
        self.trust_team = trust_team_reports
        self.force = force_recheck
        self.progress = progress
        self._memo: dict[tuple, dict] = {}
        self._memo_lock = threading.Lock()
        self._soft404: dict[str, bool] = {}
        self._soft_lock = threading.Lock()
        self._fp_used = 0
        self._fp_lock = threading.Lock()

    # ---- page inspection shared by all layers ----------------------------- #
    def _inspect(self, url: str) -> tuple[str, Finding, Fetched]:
        """Returns (state, finding, fetched). state: ok | js | missing | blocked | error."""
        f = fetch(url)
        if f.state == "blocked" and USE_PLAYWRIGHT:
            rendered = render_with_playwright(url)
            if rendered and not looks_blocked(rendered):
                f = Fetched("ok", 200, rendered, url)
        if f.state != "ok":
            return f.state, Finding(), f
        finding = analyze_html(f.html, self.target)
        if finding.level == "none" and (looks_js_shell(f.html) or looks_blocked(f.html)):
            rendered = render_with_playwright(url)
            if not rendered:
                return "js", finding, f                     # cannot decide without rendering
            finding = analyze_html(rendered, self.target)
        return "ok", finding, f

    def _positive(self, layer: str, url: str, finding: Finding, extra: str = "") -> Signal:
        if finding.level == "anchor":
            txt = f" (anchor: '{finding.anchor_text}')" if finding.anchor_text else ""
            return Signal(layer, "positive", "High", url,
                          f"Link to {self.target} found, {finding.link_type}{txt}{extra}", link_type=finding.link_type)
        return Signal(layer, "positive", "Medium", url,
                      f"{self.target} found in page source but not as a clean link - verify visually{extra}")

    def _soft404_site(self, pattern: str) -> bool:
        """True if the site answers 200 for a profile that cannot exist -> probe results unreliable."""
        with self._soft_lock:
            if pattern in self._soft404:
                return self._soft404[pattern]
        ctrl = "zz" + "".join(random.choices(string.ascii_lowercase, k=14))
        res = fetch(_fill(pattern, ctrl, self.target), retries=0).state != "missing"
        with self._soft_lock:
            self._soft404[pattern] = res
        return res

    # ---- layer 1: SEO team tracker ---------------------------------------- #
    def _team_layer(self, domain: str) -> tuple[list[Signal], bool]:
        if domain not in self.team_done:
            return [], False
        layer, urls, sigs = "Team tracker", self.team_done[domain], []
        if not urls:
            if self.trust_team:
                sigs.append(Signal(layer, "positive", "Low", "", "Team reports done (no URL to verify)"))
            else:
                sigs.append(Signal(layer, "failure", note="Team reports done but gave no URL to verify"))
            return sigs, True
        for url in urls[:3]:
            state, finding, f = self._inspect(url)
            if finding.level != "none":
                return [self._positive(layer, url, finding)], True
            if state == "ok":
                sigs.append(Signal(layer, "failure", url=url,
                                   note=f"Team URL loads but no link to {self.target} found (removed? check manually)"))
            elif state == "missing":
                sigs.append(Signal(layer, "failure", url=url, note="Team URL is gone (404) - post removed?"))
            elif self.trust_team:
                sigs.append(Signal(layer, "positive", "Low", url,
                                   f"Team-reported; page cannot be machine-checked ({f.reason or state})"))
                return sigs, True
            else:
                sigs.append(Signal(layer, "failure", url=url,
                                   note=f"Team URL cannot be machine-checked ({f.reason or state})"))
        return sigs, True

    # ---- layer 2: backlink data ------------------------------------------- #
    def _backlink_layer(self, domain: str) -> list[Signal]:
        layer = "Backlink data"
        if not self.referring_loaded:
            return []
        if domain not in self.referring:
            return [Signal(layer, "negative", "Low", "", "Not in backlink data (data can lag by weeks)", blocking=False)]
        urls = self.referring[domain]
        if not urls:
            return [Signal(layer, "positive", "Medium", "",
                           "Domain-level match in backlink data - confirm it is OUR submission")]
        for url in urls[:2]:
            state, finding, f = self._inspect(url)
            if finding.level != "none":
                return [self._positive(layer, url, finding)]
            if state == "ok":
                return [Signal(layer, "failure", url=url, note="Backlink data lists this page but the link is no longer there")]
            if state != "missing":
                return [Signal(layer, "positive", "Medium", url,
                               f"Listed in backlink data; page not re-verified ({f.reason or state})")]
        return [Signal(layer, "failure", url=urls[0], note="Page listed in backlink data returns 404")]

    # ---- layer 3: profile probe -------------------------------------------- #
    def _probe_layer(self, link: dict) -> list[Signal]:
        layer, sigs, seen = "Profile probe", [], set()
        domain = link.get("domain", "")

        # Build list of patterns to check:
        patterns = list(link.get("probe") or [])
        # Always check domain with user's link suffix: /{slug} and /@{slug}
        if domain:
            patterns.append(f"https://{domain}/{{slug}}")
            patterns.append(f"https://{domain}/@{{slug}}")

        NOT_FOUND_TERMS = (
            "page not found", "user not found", "profile not found",
            "account not found", "channel not found", "author not found",
            "404 not found", "404 - not found", "error 404",
            "this page doesn't exist", "this page does not exist",
            "this account doesn't exist", "this account does not exist",
            "user does not exist", "doesn't exist yet", "does not exist yet",
            "could not find", "nothing here", "no user by this name",
            "claim this handle", "claim this username", "handle available"
        )

        for pat in patterns:
            for slug in self.slugs:
                url = _fill(pat, slug, self.target)
                if url in seen:
                    continue
                seen.add(url)
                state, finding, f = self._inspect(url)

                # Direct backlink found on the page
                if finding.level != "none":
                    link["link_suffix"] = f"/{slug}"
                    link["tested_url"] = url
                    link["evidence_url"] = url
                    return [self._positive(layer, url, finding)]

                # Check if the page is live and has actual profile content
                if state == "ok":
                    title_m = re.search(r"<title[^>]*>(.*?)</title>", f.html, re.I | re.S)
                    title_text = unescape(title_m.group(1)).strip().lower() if title_m else ""
                    h1_m = re.search(r"<h1[^>]*>(.*?)</h1>", f.html, re.I | re.S)
                    h1_text = re.sub(r"<[^>]+>", "", h1_m.group(1)).strip().lower() if h1_m else ""
                    html_lower = f.html.lower()

                    is_soft_404 = (
                        any(t in title_text for t in NOT_FOUND_TERMS) or
                        any(t in h1_text for t in NOT_FOUND_TERMS) or
                        (len(f.html.strip()) < 500 and any(t in html_lower for t in NOT_FOUND_TERMS))
                    )

                    if not is_soft_404 and (slug.lower() in html_lower or self.target in html_lower or len(f.html) > 1500):
                        # Verified registered profile with live content!
                        link["link_suffix"] = f"/{slug}"
                        link["tested_url"] = url
                        link["evidence_url"] = url
                        display_title = title_text[:80] if title_text else "Profile active"
                        return [Signal(layer, "positive", "High", url,
                                       f"Active profile found with live content at {url} ({display_title})")]
                    else:
                        sigs.append(Signal(layer, "negative", "High", url,
                                           f"Profile does not exist at {url} (page not found / unallocated handle)"))

                elif state == "missing":
                    sigs.append(Signal(layer, "negative", "High", url, f"Profile not found at {url} ({f.reason})"))
                elif state == "blocked":
                    sigs.append(Signal(layer, "failure", url=url, note=f"Profile URL blocked ({f.reason}) - verify manually"))
                elif state == "js":
                    sigs.append(Signal(layer, "failure", url=url, note="Profile is JS-rendered - verify manually"))
                else:
                    sigs.append(Signal(layer, "failure", url=url, note=f"Probe could not run ({f.reason or state})"))

        link["link_suffix"] = self.link_suffix
        link["tested_url"] = f"https://{domain}{self.link_suffix}" if domain else ""
        return sigs

    # ---- layer 4: footprint search (positive-only) --------------------------- #
    def _footprint_layer(self, domain: str) -> list[Signal]:
        layer = "Footprint search"
        if not USE_FOOTPRINT:
            return []
        with self._fp_lock:
            if self._fp_used >= FOOTPRINT_MAX:
                return []
            self._fp_used += 1
        hits, ok = _ddgs(f'site:{domain} "{self.target}"')
        if not ok:
            return [Signal(layer, "failure", note="Search engine rate-limited", blocking=False)]
        for h in hits:
            href = h.get("href") or ""
            if not href or site_key(href) != site_key(domain):
                continue
            state, finding, _ = self._inspect(href)
            if finding.level != "none":
                return [self._positive(layer, href, finding)]
            snippet = ((h.get("body") or "") + " " + (h.get("title") or "")).lower()
            if self.target in snippet:
                return [Signal(layer, "positive", "Low", href, "Search result mentions the target; page not confirmed")]
        return [Signal(layer, "negative", "Medium", "", f"No indexed public pages mentioning {self.target}", blocking=False)]

    # ---- decision ---------------------------------------------------------- #
    def _decide(self, link: dict, signals: list[Signal], claimed: bool) -> dict:
        today = date.today().isoformat()
        pos = sorted((s for s in signals if s.kind == "positive"), key=lambda s: -RANK[s.confidence])
        if pos:
            best = pos[0]
            layers = list(dict.fromkeys(s.layer for s in pos))
            conf = "High" if len(layers) > 1 and best.confidence == "Medium" else best.confidence
            note = best.note + (f" | confirmed by {len(layers)} independent layers" if len(layers) > 1 else "")
            return dict(registered="Registered", check_method=" + ".join(layers), confidence=conf,
                        evidence_url=next((s.url for s in pos if s.url), ""),
                        link_type=next((s.link_type for s in pos if s.link_type), ""),
                        check_note=note, checked_on=today)

        negs = [s for s in signals if s.kind == "negative"]
        fails = [s for s in signals if s.kind == "failure" and s.blocking]
        fail_note = "; ".join(dict.fromkeys(s.note for s in fails if s.note))[:300]
        base = dict(registered="Unverified", confidence="", evidence_url="", link_type="", checked_on=today)

        if claimed:
            return {**base, "check_method": "Team tracker",
                    "evidence_url": next((s.url for s in fails if s.url), ""),
                    "check_note": fail_note or "Team reports done but it could not be verified - check manually"}
        if fails:
            return {**base, "check_method": "Inconclusive", "check_note": fail_note}
        if link.get("login_wall"):
            return {**base, "check_method": "Blocked / login required",
                    "check_note": "Platform blocks automated checks - verify manually"}
        if negs:
            best = max(negs, key=lambda s: RANK[s.confidence])
            layers = list(dict.fromkeys(s.layer for s in negs))
            notes = "; ".join(dict.fromkeys(s.note for s in negs))[:300]
            return dict(registered="Not Registered", check_method=" + ".join(layers), confidence=best.confidence,
                        evidence_url="", link_type="", check_note=notes, checked_on=today)
        return dict(registered="Not Registered", check_method="Direct inspection", confidence="Medium",
                    evidence_url="", link_type="",
                    check_note=f"No prior profile or backlink found for {self.target} - ready for submission",
                    checked_on=today)

    # ---- public API --------------------------------------------------------- #
    def check_one(self, link: dict) -> None:
        domain = link["domain"]
        key = (domain, tuple(link.get("probe") or []), bool(link.get("login_wall")), self.link_suffix)
        with self._memo_lock:
            memo = self._memo.get(key)
        if memo:
            link.update(memo)
            return
        try:
            if not self.force and domain not in self.team_done:
                cached = _cache_get(self.target, domain)
                if cached:
                    cached["link_suffix"] = self.link_suffix
                    link.update(cached)
                    return
            signals: list[Signal] = []
            team_sigs, claimed = self._team_layer(domain)
            signals += team_sigs
            signals += self._backlink_layer(domain)
            signals += self._probe_layer(link)
            if not any(s.kind == "positive" for s in signals):
                signals += self._footprint_layer(domain)
            res = self._decide(link, signals, claimed)
            res["link_suffix"] = link.get("link_suffix") or self.link_suffix
            if not res.get("evidence_url") and link.get("tested_url"):
                res["tested_url"] = link.get("tested_url")
            if res["registered"] == "Registered" and res["confidence"] in ("High", "Medium"):
                _cache_put(self.target, domain, res)
        except Exception as e:                              # noqa: BLE001
            log.exception("Presence check crashed for %s", domain)
            res = dict(registered="Unverified", check_method="Check error", confidence="", evidence_url="",
                       link_type="", check_note=f"Checker error: {type(e).__name__}", checked_on=date.today().isoformat(),
                       link_suffix=self.link_suffix)
        with self._memo_lock:
            self._memo[key] = res
        link.update(res)

    def check_links(self, links: list[dict], max_workers: int = 8) -> dict:
        if not self.force:
            cached_registered = _cache_get_all_registered(self.target)
            to_probe: list[dict] = []
            for link in links:
                domain = link.get("domain", "")
                if domain in cached_registered and domain not in self.team_done:
                    cached = dict(cached_registered[domain])
                    if not cached.get("link_suffix"):
                        cached["link_suffix"] = self.link_suffix
                    link.update(cached)
                else:
                    to_probe.append(link)

            skipped = len(links) - len(to_probe)
            if skipped > 0 and self.progress:
                self.progress(f"{skipped} sites already registered in SQLite database for {self.target}; probing remaining {len(to_probe)} non-registered sites...")
        else:
            to_probe = links

        if to_probe:
            with ThreadPoolExecutor(max_workers) as ex:
                list(ex.map(self.check_one, to_probe))
        return dict(Counter(l.get("registered", "Unverified") for l in links))


# --------------------------------------------------------------------------- #
# Loaders: SEO team sheet and backlink exports (CSV or XLSX)
# --------------------------------------------------------------------------- #
_URL_RE = re.compile(r"https?://[^\s,;|\"'<>]+", re.I)
_DONE_WORDS = {"done", "completed", "complete", "live", "posted", "published", "submitted",
               "approved", "registered", "yes", "y", "active"}


def _read_rows(content: bytes, filename: str) -> list[list[str]]:
    name = (filename or "").lower()
    if name.endswith((".xlsx", ".xlsm")):
        from openpyxl import load_workbook
        wb = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        rows: list[list[str]] = []
        for ws in wb.worksheets:
            for r in ws.iter_rows(values_only=True):
                rows.append([("" if c is None else str(c)).strip() for c in r])
        return [r for r in rows if any(r)]
    text = content.decode("utf-8-sig", errors="replace")
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
    return [[c.strip() for c in r] for r in csv.reader(io.StringIO(text), dialect) if any(c.strip() for c in r)]


def _find_cols(header: list[str], keywords: tuple[str, ...]) -> list[int]:
    return [i for i, h in enumerate(header) if any(k in h for k in keywords)]


def load_team_sheet(content: bytes, filename: str, target: str = "") -> dict[str, list[str]]:
    """SEO team's submission sheet -> {site_key: [submitted URLs]}. Rows with a Status column are
    only used when the status looks like done/live/completed. Domain-only rows become claims
    without URL (empty list)."""
    rows = _read_rows(content, filename)
    if len(rows) < 2:
        return {}
    header = [h.lower() for h in rows[0]]
    status_cols = _find_cols(header, ("status",))
    url_cols = (_find_cols(header, ("live", "posted", "published", "submitted", "submission", "backlink",
                                    "evidence", "profile url", "post url"))
                or _find_cols(header, ("url", "link")))
    dom_cols = _find_cols(header, ("domain", "website", "site", "platform", "name"))
    own = root_domain(target) if target else ""
    out: dict[str, list[str]] = {}
    for row in rows[1:]:
        if status_cols:
            st = (row[status_cols[0]] if status_cols[0] < len(row) else "").lower()
            if st not in _DONE_WORDS:
                continue
        cells = [row[i] for i in (url_cols or range(len(row))) if i < len(row)]
        urls = [u.rstrip(").,") for c in cells for u in _URL_RE.findall(c)]
        urls = [u for u in urls if not own or root_domain(u) != own]
        if urls:
            for u in urls:
                lst = out.setdefault(site_key(u), [])
                if u not in lst:
                    lst.append(u)
            continue
        for i in dom_cols:
            val = row[i] if i < len(row) else ""
            if val and "." in val and " " not in val:
                out.setdefault(site_key(val), [])
                break
    return out


def load_backlink_export(content: bytes, filename: str, target: str = "") -> dict[str, list[str]]:
    """GSC 'Top linking sites', Ahrefs/Semrush/Moz exports -> {site_key: [source page URLs]}.
    Domain-only exports give empty URL lists (domain-level match)."""
    rows = _read_rows(content, filename)
    if len(rows) < 2:
        return {}
    header = [h.lower() for h in rows[0]]
    url_cols = _find_cols(header, ("referring page", "source url", "source page", "linking page", "page url", "url from"))
    dom_cols = _find_cols(header, ("referring domain", "root domain", "source domain", "domain", "site"))
    own = root_domain(target) if target else ""
    out: dict[str, list[str]] = {}
    for row in rows[1:]:
        if url_cols and url_cols[0] < len(row) and row[url_cols[0]].lower().startswith("http"):
            u = row[url_cols[0]]
            if own and root_domain(u) == own:
                continue
            lst = out.setdefault(site_key(u), [])
            if u not in lst:
                lst.append(u)
            continue
        col = dom_cols[0] if dom_cols else 0
        val = row[col] if col < len(row) else ""
        if val and "." in val and " " not in val and not (own and root_domain(val) == own):
            out.setdefault(site_key(val), [])
    return out


def fetch_moz_referring(target: str, max_pages: int = MOZ_BACKLINK_PAGES) -> dict[str, list[str]]:
    """Optional: referring root domains from Moz Links API v2 (opt-in, uses API rows).
    NOTE: verify endpoint/field names against the current Moz Links API docs; failures are non-fatal."""
    out: dict[str, list[str]] = {}
    if not (MOZ_ID and MOZ_SECRET):
        return out
    token = None
    for _ in range(max(1, max_pages)):
        body: dict = {"target": root_domain(target), "target_scope": "root_domain", "limit": 50}
        if token:
            body["next_token"] = token
        try:
            r = httpx.post("https://lsapi.seomoz.com/v2/linking_root_domains",
                           auth=(MOZ_ID, MOZ_SECRET), json=body, timeout=30)
            r.raise_for_status()
            data = r.json()
        except Exception as e:                              # noqa: BLE001
            log.warning("Moz linking_root_domains failed: %s", e)
            break
        for res in data.get("results", []):
            dom = res.get("root_domain") or res.get("source_root_domain") or res.get("domain")
            if dom:
                out.setdefault(site_key(dom), [])
        token = data.get("next_token")
        if not token:
            break
    return out


# --------------------------------------------------------------------------- #
# Self-test for probe patterns:  python tools/presence_checker.py --probe-test microsoft
# --------------------------------------------------------------------------- #
def _probe_test(slug: str) -> None:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from submission_seeds import SUBMISSION_PLATFORMS
    seen, rows = set(), []
    for cat in SUBMISSION_PLATFORMS.values():
        for p in cat["platforms"]:
            for pat in p.get("probe", []):
                if pat not in seen:
                    seen.add(pat)
                    rows.append((p["name"], _fill(pat, slug, "example.com")))
    with ThreadPoolExecutor(8) as ex:
        results = list(ex.map(lambda r: fetch(r[1], retries=0), rows))
    print(f"{'PLATFORM':28} {'STATE':8} URL")
    for (name, url), res in zip(rows, results):
        print(f"{name[:27]:28} {res.state:8} {url}  {res.reason}")
    print("\n'missing' on a handle that exists = wrong URL pattern -> fix it in submission_seeds.PROBE_PATTERNS")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--probe-test":
        _probe_test(sys.argv[2])
    else:
        print(__doc__)