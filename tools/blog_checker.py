"""
Blog & Article AI Auditor (tools/blog_checker.py)

Audits any blog post / article / content URL against a project's niche.

Checks:
  1. Project context and niche (label + the site's own niche terms)
  2. Indexability gate (noindex, nosnippet, robots.txt, canonical, HTTP status)
  3. On-page structure: title, meta, headings, word count, readability
  4. Links and anchor text (internal / external / generic / empty / off-topic / optional broken-link check)
  5. Search intent label: Informational | Commercial | Transactional | Navigational
  6. Keyword matrix: every keyword is checked against BOTH the intent and the niche
  7. Google AI Overviews / GEO readiness (heuristic score, gated by indexability)

Note: the GEO score is a heuristic. Google says AI Overviews use normal Search
indexing and snippet eligibility; there is no official "AI bot score".
"""
import re
import json
import math
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import urljoin, urlparse, urldefrag
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

from config import USER_AGENT

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 " + USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
    "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't",
    "down", "during", "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have",
    "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself",
    "him", "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into",
    "is", "isn't", "it", "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my",
    "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our",
    "ours", "ourselves", "out", "over", "own", "same", "shan't", "she", "she'd", "she'll", "she's",
    "should", "shouldn't", "so", "some", "such", "than", "that", "that's", "the", "their", "theirs",
    "them", "themselves", "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
    "they've", "this", "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasn't",
    "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's", "when", "when's",
    "where", "where's", "which", "while", "who", "who's", "whom", "why", "why's", "with", "won't",
    "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself",
    "yourselves", "will", "can", "just", "also", "get", "one", "like", "use", "make", "even", "new",
    "see", "way", "may", "many", "much", "well"
}

# Words that appear on almost every homepage and say nothing about the niche
WEB_NOISE = {
    "home", "welcome", "official", "website", "site", "page", "contact", "about", "company", "best",
    "free", "online", "services", "service", "solutions", "login", "blog", "news", "now", "today",
    "top", "leading", "premium", "quality", "our", "team", "india", "global", "world", "all", "get"
}

GENERIC_ANCHORS = {
    "click here", "read more", "learn more", "here", "link", "website", "this page",
    "source", "continue reading", "more info", "visit here", "check this out", "page",
    "view more", "find out more", "go here", "this link", "article", "post", "more", "this"
}

INTENT_TRIGGERS = {
    "Informational": [
        "how to", "what is", "what are", "guide", "tutorial", "tips", "ideas", "examples",
        "why", "explained", "overview", "definition", "strategies", "learn", "basics",
        "step by step", "understanding", "causes", "types of", "benefits of", "history", "ways to"
    ],
    "Commercial": [
        "best", "top", "review", "reviews", "vs", "versus", "comparison", "compare",
        "alternatives", "pros and cons", "worth it", "rating", "features", "breakdown",
        "difference between", "cheapest", "fastest", "premium", "buyers guide", "top rated"
    ],
    "Transactional": [
        "buy", "purchase", "order", "price", "pricing", "cost", "discount", "coupon",
        "deal", "hire", "book now", "book a", "quote", "get started", "trial", "download now",
        "subscribe", "shop", "cheap", "sale", "package", "demo"
    ],
    "Navigational": [
        "login", "sign in", "portal", "contact us", "official site", "dashboard",
        "account", "customer service", "help desk", "phone number"
    ]
}

INTENT_EXPLANATIONS = {
    "Informational": "The content educates, explains concepts, answers questions, or gives actionable guidance.",
    "Commercial": "The content compares options, highlights features/reviews, or evaluates alternatives for researchers who are close to a decision.",
    "Transactional": "The content pushes a purchase, pricing, booking, or signup with direct calls to action.",
    "Navigational": "The content is built around brand-specific access: portals, logins, contact details, or locations.",
}

NICHE_CATEGORIES = {
    "Digital Marketing & SEO": ["seo", "marketing", "digital marketing", "agency", "traffic", "leads", "adwords", "ppc", "content marketing"],
    "SaaS & Software": ["saas", "software", "platform", "cloud", "api", "developer", "tool", "automation", "crm", "analytics", "app"],
    "E-Commerce & Retail": ["shop", "store", "buy", "cart", "products", "fashion", "apparel", "checkout", "shipping", "ecommerce"],
    "Finance & FinTech": ["finance", "fintech", "investing", "crypto", "banking", "loans", "insurance", "credit", "wealth", "tax"],
    "Healthcare & Wellness": ["health", "medical", "clinic", "doctor", "wellness", "fitness", "therapy", "dental", "care"],
    "Real Estate & Property": ["real estate", "property", "realtor", "homes for sale", "apartments", "mortgage", "housing"],
    "Legal & Professional Services": ["lawyer", "attorney", "legal", "law firm", "consulting", "accounting", "advisory"],
    "Travel & Hospitality": ["travel", "hotel", "resort", "booking", "flights", "vacation", "tours", "destinations"],
    "Event Management & Entertainment": ["event", "events", "wedding", "venue", "party", "conference", "tickets", "catering"],
    "Education & EdTech": ["course", "education", "academy", "training", "university", "learn", "tutor", "school", "bootcamp"],
}

NICHE_SEMANTIC_CONTEXT = {
    "Event Management & Entertainment": [
        "event", "events", "wedding", "weddings", "marriage", "bridal", "groom", "venue", "venues",
        "hall", "banquet", "ballroom", "resort", "lawn", "farmhouse", "party", "parties", "celebration",
        "celebrations", "kitty", "gathering", "conference", "conferences", "seminar", "summit", "expo",
        "retreat", "gala", "reception", "ceremony", "function", "festive", "festival", "festivals",
        "diwali", "holi", "eid", "christmas", "halloween", "thanksgiving", "new year", "birthday",
        "anniversary", "catering", "caterer", "caterers", "food", "menu", "buffet", "decor", "decoration",
        "decorations", "theme", "themes", "floral", "flowers", "lighting", "dj", "music", "entertainment",
        "sound", "stage", "performer", "photographer", "photography", "videography", "invitation",
        "invitations", "rsvp", "guest", "guests", "attendee", "attendees", "tickets", "ticket",
        "booking", "bookings", "reservation", "reservations", "timeline", "schedule", "advance",
        "checklist", "quotes", "quote", "budget", "pricing", "cost", "rates", "packages", "package",
        "estimate", "availability", "slots", "organizer", "planner", "planning"
    ],
    "Digital Marketing & SEO": [
        "seo", "marketing", "digital", "agency", "traffic", "leads", "adwords", "ppc", "content",
        "rankings", "ranking", "serp", "backlinks", "backlink", "link", "links", "authority", "da",
        "organic", "keywords", "keyword", "meta", "crawl", "index", "technical", "analytics",
        "conversion", "conversions", "ctr", "bounce", "audit", "strategy", "campaign", "campaigns",
        "google", "googlebot", "search", "semrush", "ahrefs", "social", "media", "funnel", "copywriting"
    ],
    "SaaS & Software": [
        "saas", "software", "platform", "cloud", "api", "apis", "developer", "developers", "tool",
        "tools", "automation", "automate", "crm", "analytics", "app", "apps", "integration",
        "integrations", "workflow", "workflows", "dashboard", "dashboards", "features", "feature",
        "pricing", "subscription", "trial", "demo", "deployment", "deploy", "security", "compliance",
        "scalability", "user", "users", "onboarding", "interface", "backend", "frontend", "database"
    ],
    "Real Estate & Property": [
        "real estate", "property", "properties", "realtor", "realtors", "homes", "home", "apartments",
        "apartment", "flat", "flats", "villa", "villas", "house", "houses", "housing", "mortgage",
        "loan", "loans", "plot", "plots", "land", "commercial", "residential", "rent", "rental",
        "lease", "leasing", "buy", "buying", "sale", "seller", "buyer", "tenant", "landlord", "sqft",
        "square feet", "builder", "builders", "amenities", "location", "possession", "registry", "rera"
    ],
    "Healthcare & Wellness": [
        "health", "medical", "clinic", "clinics", "doctor", "doctors", "physician", "wellness",
        "fitness", "therapy", "therapist", "dental", "dentist", "care", "symptoms", "symptom",
        "diagnosis", "treatment", "treatments", "cure", "medicine", "medicines", "hospital", "patient",
        "patients", "diet", "nutrition", "workout", "exercise", "mental", "recovery", "consultation"
    ],
    "Finance & FinTech": [
        "finance", "financial", "fintech", "investing", "investment", "investments", "crypto",
        "banking", "bank", "banks", "loans", "loan", "insurance", "credit", "wealth", "tax", "taxes",
        "stocks", "stock", "equity", "portfolio", "returns", "roi", "savings", "interest", "advisor",
        "retirement", "budget", "capital", "fund", "funds", "mutual funds", "broker", "brokerage"
    ],
    "E-Commerce & Retail": [
        "shop", "shopping", "store", "stores", "buy", "buying", "cart", "products", "product",
        "fashion", "apparel", "checkout", "shipping", "delivery", "ecommerce", "retail", "orders",
        "order", "tracking", "returns", "refund", "discount", "discounts", "coupon", "coupons",
        "deal", "deals", "sale", "sales", "review", "reviews", "inventory", "catalog", "unboxing"
    ],
    "Travel & Hospitality": [
        "travel", "traveler", "travelers", "hotel", "hotels", "resort", "resorts", "booking",
        "bookings", "flights", "flight", "vacation", "vacations", "tours", "tour", "destinations",
        "destination", "itinerary", "sightseeing", "trip", "trips", "stay", "stays", "guide",
        "luggage", "packing", "visa", "tourist", "attractions", "commute", "hospitality", "tickets"
    ],
    "Education & EdTech": [
        "course", "courses", "education", "academy", "training", "university", "universities",
        "college", "colleges", "learn", "learning", "tutor", "tutors", "school", "schools", "bootcamp",
        "curriculum", "syllabus", "degree", "diploma", "certificate", "admissions", "study", "exam",
        "exams", "test", "preparation", "lecture", "student", "students", "career", "placement"
    ],
    "Legal & Professional Services": [
        "lawyer", "lawyers", "attorney", "attorneys", "legal", "law firm", "consulting", "consultant",
        "consultants", "accounting", "accountant", "advisory", "advisor", "compliance", "audit",
        "litigation", "contract", "contracts", "agreement", "counsel", "corporate law", "taxation"
    ]
}

ARTICLE_SCHEMA_TYPES = {"Article", "BlogPosting", "NewsArticle", "TechArticle"}
HIGH_AUTHORITY_DOMAINS = {
    "wikipedia.org", "google.com", "forbes.com", "hubspot.com", "nytimes.com", "searchenginejournal.com",
    "moz.com", "nih.gov", "medium.com", "statista.com", "developers.google.com", "support.google.com",
    "semrush.com", "ahrefs.com", "searchengineland.com", "w3.org", "mozilla.org",
}
STAT_RE = re.compile(r"\d+(?:\.\d+)?\s?%|[$€£₹]\s?\d[\d,]*(?:\.\d+)?|(?<!\d)(?:19|20)\d{2}(?!\d)")


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #
_RE_CACHE: Dict[str, "re.Pattern"] = {}


def _phrase_re(phrase: str):
    pat = _RE_CACHE.get(phrase)
    if pat is None:
        pat = re.compile(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", re.I)
        _RE_CACHE[phrase] = pat
    return pat


def _count_phrase(text: str, phrase: str) -> int:
    """Whole-word / whole-phrase count (so 'vs' does not match 'canvas')."""
    return len(_phrase_re(phrase).findall(text))


def _stem(word: str) -> str:
    """Very light stemmer so 'backlinks' matches 'backlink' and 'marketing' matches 'market'."""
    w = word.lower()
    for suf in ("ing", "ed", "es", "ly", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[: -len(suf)]
    return w


def _stems(text: str) -> set:
    return {_stem(t) for t in re.findall(r"[a-zA-Z]{3,}", text.lower()) if t not in STOP_WORDS}


def _clean_url(url: str) -> str:
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return urldefrag(url)[0]


def _host(url_or_netloc: str) -> str:
    netloc = urlparse(url_or_netloc).netloc if "//" in url_or_netloc else url_or_netloc
    netloc = netloc.lower().split("@")[-1].split(":")[0]
    return netloc[4:] if netloc.startswith("www.") else netloc


def _same_site(host: str, sites: List[str]) -> bool:
    return any(s and (host == s or host.endswith("." + s)) for s in sites)


def _is_high_authority(host: str) -> bool:
    if host.endswith((".gov", ".edu")) or ".gov." in host or ".edu." in host:
        return True
    return any(host == d or host.endswith("." + d) for d in HIGH_AUTHORITY_DOMAINS)


def _fetch(url: str, timeout: int = 15) -> Tuple[Optional[requests.Response], str]:
    """Returns (response, error_message). Never raises."""
    try:
        return requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True), ""
    except requests.exceptions.Timeout:
        return None, "request timed out"
    except requests.exceptions.SSLError:
        return None, "SSL certificate error"
    except requests.exceptions.ConnectionError:
        return None, "could not connect (DNS or network error)"
    except Exception as e:  # noqa: BLE001
        return None, str(e)[:120]


def _meta_content(soup: BeautifulSoup, **attrs) -> str:
    tag = soup.find("meta", attrs=attrs)
    return (tag.get("content") or "").strip() if tag else ""


def _top_terms(weighted_texts: List[Tuple[str, int]], limit: int = 12) -> List[str]:
    counter: Counter = Counter()
    for text, weight in weighted_texts:
        for tok in re.findall(r"[a-zA-Z]{3,}", text.lower()):
            if tok in STOP_WORDS or tok in WEB_NOISE:
                continue
            counter[tok] += weight
    return [t for t, _ in counter.most_common(limit)]


def _extract_main_content(soup: BeautifulSoup):
    """Isolates the main article body to avoid header/nav/footer noise."""
    candidates = soup.find_all(["article", "main"])
    if candidates:
        # the biggest <article>/<main> is almost always the real post
        return max(candidates, key=lambda c: len(c.get_text(strip=True)))
    for sel in [".post-content", ".article-content", ".entry-content", ".blog-post", ".post-body", "#content", ".content"]:
        found = soup.select(sel)
        if found:
            return found[0]
    return soup.body or soup


def _calculate_readability(text: str) -> Dict[str, Any]:
    """Flesch Reading Ease + approximate grade level."""
    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if len(s.strip()) > 3]
    words = re.findall(r"\b[a-zA-Z]+\b", text)
    word_count = len(words)
    sentence_count = max(len(sentences), 1)

    if word_count < 20:
        return {"score": 60, "grade": "Standard", "reading_time_min": 1, "avg_sentence_len": 12}

    def count_syllables(w: str) -> int:
        w = w.lower()
        if len(w) <= 3:
            return 1
        w = re.sub(r"(?:[^laeiouy]|ed|es|e)$", "", w)
        w = re.sub(r"^y", "", w)
        return max(len(re.findall(r"[aeiouy]{1,2}", w)), 1)

    syllables = sum(count_syllables(w) for w in words)
    asl = word_count / sentence_count
    asw = syllables / word_count
    flesch = max(0, min(100, round(206.835 - 1.015 * asl - 84.6 * asw, 1)))

    if flesch >= 80:
        grade = "Easy to Read (Grade 6)"
    elif flesch >= 60:
        grade = "Plain English (Grade 8-9)"
    elif flesch >= 50:
        grade = "Fairly Difficult (High School)"
    else:
        grade = "Complex / Technical (College level)"

    return {
        "score": flesch,
        "grade": grade,
        "reading_time_min": max(1, math.ceil(word_count / 200)),
        "avg_sentence_len": round(asl, 1),
    }


def _parse_schema(soup: BeautifulSoup) -> Tuple[List[dict], List[str]]:
    objs: List[dict] = []
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or tag.get_text() or "")
        except Exception:  # noqa: BLE001
            continue
        stack = [data]
        while stack:
            cur = stack.pop()
            if isinstance(cur, list):
                stack.extend(cur)
            elif isinstance(cur, dict):
                objs.append(cur)
                if "@graph" in cur:
                    stack.append(cur["@graph"])
    types: List[str] = []
    for o in objs:
        t = o.get("@type")
        if isinstance(t, list):
            types.extend(str(x) for x in t)
        elif t:
            types.append(str(t))
    return objs, types


# --------------------------------------------------------------------------- #
# 1. Project / niche analysis
# --------------------------------------------------------------------------- #
def analyze_project_niche(project_url: str, override_niche: Optional[str] = None) -> Dict[str, Any]:
    """
    Returns the niche label AND the site's own niche terms (used to judge keyword fit).
    An override label is used as the niche; the site is still read (if reachable) for extra terms.
    """
    clean = _clean_url(project_url)
    domain = _host(clean)
    override = (override_niche or "").strip()

    def _resolve_category_terms(label: str) -> Tuple[Optional[str], List[str]]:
        lbl = label.lower()
        matched = None
        for cat in NICHE_CATEGORIES:
            c_low = cat.lower()
            if c_low in lbl or lbl in c_low:
                matched = cat
                break
            if any(w in lbl for w in c_low.replace("&", " ").split() if len(w) > 3):
                matched = cat
                break
        terms = []
        if matched:
            terms.extend([k for k in NICHE_CATEGORIES[matched] if " " not in k])
            if matched in NICHE_SEMANTIC_CONTEXT:
                terms.extend(NICHE_SEMANTIC_CONTEXT[matched])
        return matched, list(dict.fromkeys(terms))

    override_cat, init_cat_terms = _resolve_category_terms(override) if override else (None, [])

    result: Dict[str, Any] = {
        "niche": override or "General Business",
        "detected_from": "User Override" if override else "Default",
        "title": "",
        "description": "",
        "domain": domain,
        "niche_terms": _top_terms([(override, 5)]) if override else [],
        "category_terms": list(init_cat_terms),
    }

    resp, err = _fetch(clean)
    if resp is None or resp.status_code != 200:
        reason = err or f"HTTP {resp.status_code}"
        if not override:
            result["detected_from"] = f"Default (project site unreachable: {reason})"
        return result

    soup = BeautifulSoup(resp.text, "html.parser")
    title = (soup.title.string or "").strip() if soup.title and soup.title.string else ""
    meta_desc = _meta_content(soup, name="description") or _meta_content(soup, property="og:description")
    meta_kw = _meta_content(soup, name="keywords")
    site_name = _meta_content(soup, property="og:site_name")
    h1s = [h.get_text(strip=True) for h in soup.find_all("h1") if h.get_text(strip=True)]
    h2s = [h.get_text(strip=True) for h in soup.find_all("h2") if h.get_text(strip=True)][:10]

    site_terms = _top_terms(
        [(title, 3), (meta_desc, 3), (" ".join(h1s), 3), (meta_kw, 2), (site_name, 1), (" ".join(h2s), 1)],
        limit=12,
    )
    # the domain itself is a niche hint ("tracevenue" -> not helpful, but "seoagency" etc. can be)
    full_text = f"{title} {meta_desc} {meta_kw} {' '.join(h1s)}".lower()

    best_cat, best_score = None, 0
    for cat, kws in NICHE_CATEGORIES.items():
        score = sum(1 for kw in kws if _count_phrase(full_text, kw))
        if score > best_score:
            best_cat, best_score = cat, score

    target_label = (override or best_cat or "General Business").lower()
    matched_cat = None
    for cat in NICHE_CATEGORIES:
        c_low = cat.lower()
        if c_low in target_label or target_label in c_low:
            matched_cat = cat
            break
        if any(w in target_label for w in c_low.replace("&", " ").split() if len(w) > 3):
            matched_cat = cat
            break

    chosen_cat = matched_cat or best_cat
    category_terms: List[str] = []
    if chosen_cat:
        category_terms.extend([k for k in NICHE_CATEGORIES[chosen_cat] if " " not in k])
        if chosen_cat in NICHE_SEMANTIC_CONTEXT:
            category_terms.extend(NICHE_SEMANTIC_CONTEXT[chosen_cat])

    terms = list(dict.fromkeys(result["niche_terms"] + site_terms))  # override tokens first, no dupes
    result.update({
        "niche": override or best_cat or "General Business",
        "detected_from": "User Override + Homepage Terms" if override else ("Homepage Metadata & Headings" if best_cat else "Default (no strong niche signal)"),
        "title": title,
        "description": meta_desc,
        "niche_terms": terms,
        "category_terms": category_terms,
    })
    return result


# --------------------------------------------------------------------------- #
# 2. Indexability gate
# --------------------------------------------------------------------------- #
def _normalize_for_compare(url: str) -> str:
    p = urlparse(url)
    return f"{_host(url)}{p.path.rstrip('/')}"


def _check_indexability(final_url: str, soup: BeautifulSoup, resp: requests.Response, canonical: str) -> Dict[str, Any]:
    blocking: List[str] = []
    warnings: List[str] = []

    directives = [(m.get("content") or "").lower()
                  for m in soup.find_all("meta", attrs={"name": re.compile(r"^(robots|googlebot)$", re.I)})]
    directives.append(resp.headers.get("X-Robots-Tag", "").lower())
    joined = " ".join(directives)
    tokens = set(re.split(r"[,\s]+", joined))
    compact = joined.replace(" ", "")

    if "noindex" in tokens or "none" in tokens:
        blocking.append("noindex directive: this page cannot appear in Google Search or AI Overviews.")
    if "nosnippet" in tokens or "max-snippet:0" in compact:
        blocking.append("nosnippet / max-snippet:0: Google is not allowed to quote this page.")

    try:
        r = requests.get(urljoin(final_url, "/robots.txt"), headers=HEADERS, timeout=8)
        if r.status_code == 200:
            rp = RobotFileParser()
            rp.parse(r.text.splitlines())
            if not rp.can_fetch("Googlebot", final_url):
                blocking.append("robots.txt blocks Googlebot from this URL.")
        elif r.status_code >= 500:
            warnings.append(f"robots.txt returned HTTP {r.status_code}; Google may pause crawling.")
    except Exception:  # noqa: BLE001
        warnings.append("Could not read robots.txt to verify Googlebot access.")

    if canonical:
        canon_abs = urljoin(final_url, canonical)
        if _normalize_for_compare(canon_abs) != _normalize_for_compare(final_url):
            warnings.append(f"Canonical points to a different URL ({canon_abs}); Google may index that URL instead of this one.")
    else:
        warnings.append("No canonical tag found.")

    return {"indexable": not blocking, "blocking": blocking, "warnings": warnings}


# --------------------------------------------------------------------------- #
# 3. Link health (optional)
# --------------------------------------------------------------------------- #
def _check_one_link(url: str) -> Tuple[str, Optional[int]]:
    try:
        r = requests.head(url, headers=HEADERS, timeout=8, allow_redirects=True)
        if r.status_code in (403, 405, 501):
            r = requests.get(url, headers=HEADERS, timeout=8, allow_redirects=True, stream=True)
            r.close()
        return url, r.status_code
    except Exception:  # noqa: BLE001
        return url, None


def _find_broken_links(links: List[Dict[str, Any]], limit: int = 20) -> List[Dict[str, Any]]:
    urls = list(dict.fromkeys(l["url"] for l in links))[:limit]
    broken = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        for url, status in pool.map(_check_one_link, urls):
            # 401/403/429/999 usually mean "bot blocked", not broken
            if status is None or status in (404, 410) or 500 <= status < 600:
                broken.append({"url": url, "status": status or "unreachable"})
    return broken


# --------------------------------------------------------------------------- #
# 4. Intent / keyword helpers
# --------------------------------------------------------------------------- #
def _keyword_intent(keyword: str) -> str:
    kw = keyword.lower()
    scores = {intent: sum(1 for t in trig if _count_phrase(kw, t)) for intent, trig in INTENT_TRIGGERS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Neutral"  # no intent word = no intent signal


def _intent_ok(kw_intent: str, primary: str) -> bool:
    if kw_intent in ("Neutral", primary):
        return True
    # Informational and Commercial research overlap naturally
    return {kw_intent, primary} == {"Informational", "Commercial"}


# --------------------------------------------------------------------------- #
# 5. Citation knowledge base & replacement generators
# --------------------------------------------------------------------------- #
NICHE_AUTHORITY_CITATIONS: Dict[str, List[Dict[str, str]]] = {
    "Event Management & Entertainment": [
        {
            "source": "Statista / Global Event Research",
            "topic": "Global Meetings & Event Industry Size and Growth Benchmarks",
            "domain": "statista.com",
            "anchor": "Statista Event Industry Growth Report",
            "reason": "Provides verified market size and budget figures to ground industry assertions.",
        },
        {
            "source": "Skift Meetings / EventMB",
            "topic": "Event Experience Design & Modern Event Technology Trends",
            "domain": "skift.com",
            "anchor": "Skift Meetings Industry Benchmark",
            "reason": "Premier publication for event planning metrics, vendor standards, and venue data.",
        },
        {
            "source": "Wikipedia Knowledge Base",
            "topic": "Event Management Standards & Protocol Definitions",
            "domain": "en.wikipedia.org",
            "anchor": "Wikipedia: Event Management Overview",
            "reason": "Connects your article to recognized Google Knowledge Graph conceptual entities.",
        },
        {
            "source": "Forbes / Harvard Business Review",
            "topic": "ROI of In-Person Corporate Events and Networking Impact",
            "domain": "forbes.com",
            "anchor": "Forbes Insights on In-Person Gatherings",
            "reason": "High-authority business publication reinforcing E-E-A-T credibility.",
        },
    ],
    "Digital Marketing & SEO": [
        {
            "source": "Google Search Central",
            "topic": "Google Search Essentials & Quality Rater Documentation",
            "domain": "developers.google.com/search",
            "anchor": "Google Search Central Documentation",
            "reason": "Primary search engine documentation directly backing technical SEO recommendations.",
        },
        {
            "source": "HubSpot Research",
            "topic": "State of Marketing & Content Conversion Benchmarks",
            "domain": "hubspot.com",
            "anchor": "HubSpot State of Marketing Report",
            "reason": "Widely recognized conversion and marketing benchmarks.",
        },
        {
            "source": "Search Engine Land / Journal",
            "topic": "Search Engine Algorithm Updates & Industry Research",
            "domain": "searchengineland.com",
            "anchor": "Search Engine Land Industry Analysis",
            "reason": "Recognized digital marketing publication enhancing domain authority signals.",
        },
    ],
    "SaaS & Software": [
        {
            "source": "Gartner / Forrester Research",
            "topic": "Enterprise Software Market Trends & Technology Adoption",
            "domain": "gartner.com",
            "anchor": "Gartner Technology Benchmark",
            "reason": "Gold standard for IT software evaluations and enterprise market sizing.",
        },
        {
            "source": "GitHub / Stack Overflow",
            "topic": "Developer Ecosystem Survey & Architecture Benchmarks",
            "domain": "github.com",
            "anchor": "Developer Ecosystem Report",
            "reason": "Primary engineering source recognized by algorithmic evaluators.",
        },
        {
            "source": "W3C Standards",
            "topic": "Web Standards and Protocols Specification",
            "domain": "w3.org",
            "anchor": "W3C Technical Standards",
            "reason": "Grounds technical definitions in official web architecture specifications.",
        },
    ],
    "E-Commerce & Retail": [
        {
            "source": "Baymard Institute",
            "topic": "E-Commerce Checkout Usability & Cart Abandonment Rates",
            "domain": "baymard.com",
            "anchor": "Baymard E-commerce Checkout Benchmark",
            "reason": "The definitive UX research authority on e-commerce purchase workflows.",
        },
        {
            "source": "Statista E-Commerce",
            "topic": "Global Online Retail & Mobile Shopping Statistics",
            "domain": "statista.com",
            "anchor": "Statista Global E-Commerce Data",
            "reason": "Substantiates retail volume, conversion rates, and consumer adoption.",
        },
    ],
    "Healthcare & Wellness": [
        {
            "source": "National Institutes of Health (NIH) / PubMed",
            "topic": "Peer-Reviewed Clinical Studies and Medical Research",
            "domain": "ncbi.nlm.nih.gov",
            "anchor": "NIH Peer-Reviewed Clinical Study",
            "reason": "Essential for Health/YMYL queries where Google demands peer-reviewed consensus.",
        },
        {
            "source": "World Health Organization (WHO) / CDC",
            "topic": "Official Public Health Data & Prevention Protocols",
            "domain": "who.int",
            "anchor": "WHO Public Health Guidelines",
            "reason": "Institutional authority establishing maximum E-E-A-T score.",
        },
    ],
    "Finance & FinTech": [
        {
            "source": "Federal Reserve Economic Data (FRED)",
            "topic": "Macroeconomic Trends, Interest Rates & Consumer Spending",
            "domain": "stlouisfed.org",
            "anchor": "Federal Reserve Economic Data (FRED)",
            "reason": "Unquestionable macroeconomic authority essential for Financial YMYL content.",
        },
        {
            "source": "Investopedia / SEC",
            "topic": "Regulatory Frameworks & Standard Financial Definitions",
            "domain": "investopedia.com",
            "anchor": "Investopedia Financial Reference",
            "reason": "Grounds financial concepts in official regulatory and educational standards.",
        },
    ],
    "Real Estate & Property": [
        {
            "source": "National Association of Realtors (NAR)",
            "topic": "Residential Real Estate Trends & Median Price Index",
            "domain": "nar.realtor",
            "anchor": "NAR Real Estate Market Report",
            "reason": "The primary industry authority on property market transactions and housing data.",
        },
        {
            "source": "Zillow Research",
            "topic": "Rental Price Index and Housing Value Forecasts",
            "domain": "zillow.com/research",
            "anchor": "Zillow Home Value Index",
            "reason": "Recognized national real estate index for neighborhood pricing.",
        },
    ],
    "Travel & Hospitality": [
        {
            "source": "UN Tourism (UNWTO)",
            "topic": "Global Travel Trends & Hospitality Growth Statistics",
            "domain": "unwto.org",
            "anchor": "UN Tourism International Travel Report",
            "reason": "Global international tourism authority establishing worldwide travel statistics.",
        },
        {
            "source": "Statista Travel & Tourism",
            "topic": "Hotel Occupancy Rates and Travel Booking Benchmarks",
            "domain": "statista.com",
            "anchor": "Statista Hospitality Industry Data",
            "reason": "Substantiates hotel, flight, and tourism economic data.",
        },
    ],
}

UNIVERSAL_AUTHORITY_CITATIONS: List[Dict[str, str]] = [
    {
        "source": "Statista / Primary Research",
        "topic": "Industry Market Size, Growth Forecast & Consumer Statistics",
        "domain": "statista.com",
        "anchor": "Statista Market Research Report",
        "reason": "Backing statements with verifiable statistical data boosts information gain.",
    },
    {
        "source": "Wikipedia Knowledge Base",
        "topic": "Topical Definition & Standard Nomenclature",
        "domain": "en.wikipedia.org",
        "anchor": "Wikipedia Topical Overview",
        "reason": "Connects your article to core Knowledge Graph entities recognized by Google AI.",
    },
    {
        "source": "Pew Research Center / Forbes",
        "topic": "Consumer Demographics & Industry Trends Study",
        "domain": "pewresearch.org",
        "anchor": "Pew Research / Forbes Industry Analysis",
        "reason": "Adds non-commercial editorial credibility and independent validation.",
    },
]


def _get_niche_citations(niche: str, title: str = "") -> List[Dict[str, str]]:
    """Returns 3-4 authoritative citation suggestions matching the detected niche."""
    clean_niche = (niche or "").strip().lower()
    for cat_name, citations in NICHE_AUTHORITY_CITATIONS.items():
        # Match if category name or any of its words are in the niche string
        cat_words = [w.lower() for w in re.split(r"[\s&/,]+", cat_name) if len(w) > 3]
        if any(w in clean_niche for w in cat_words):
            return citations
    return UNIVERSAL_AUTHORITY_CITATIONS


def _suggest_anchor(link_obj: Dict[str, Any], niche: str, article_topic: str) -> str:
    """Generates a high-quality, keyword-rich replacement anchor for generic/long/empty links."""
    url = link_obj.get("url", "")
    anchor = (link_obj.get("anchor") or "").strip()
    u = urlparse(url)
    path = u.path.strip("/")

    # 1. Look for clean, descriptive slug terms in target URL
    slug_parts = [p for p in re.split(r"[-_/.]", path) if p and not p.isdigit() and len(p) > 2]
    clean_parts = [
        p for p in slug_parts
        if p.lower() not in {
            "blog", "post", "html", "php", "index", "article", "category", "tag", "archives",
            "en", "us", "item", "default", "pages", "content"
        }
    ]

    clean_niche = (niche or "Services").split("/")[0].strip()
    clean_topic = (article_topic or "").split("|")[0].split("-")[0].strip()

    if clean_parts:
        slug_text = " ".join(clean_parts[:4]).title()
        lower_slug = slug_text.lower()
        if "contact" in lower_slug:
            return f"Contact Our {clean_niche} Team"
        if "about" in lower_slug:
            return f"About Our {clean_niche} Team"
        if "pricing" in lower_slug or "cost" in lower_slug:
            return f"View {clean_niche} Pricing & Packages"
        if "service" in lower_slug or "package" in lower_slug:
            return f"Explore {slug_text}"
        if link_obj.get("is_too_long"):
            return slug_text
        if link_obj.get("is_generic") or link_obj.get("is_empty"):
            return f"Explore {slug_text}"
        return slug_text

    # 2. If anchor was overly long (>8 words), distill meaningful words
    if link_obj.get("is_too_long") and anchor and not anchor.startswith("http"):
        meaningful = [w for w in anchor.split() if w.lower() not in STOP_WORDS]
        if len(meaningful) >= 2:
            return " ".join(meaningful[:4]).title()

    # 3. Destination heuristic
    url_lower = url.lower()
    if "contact" in url_lower:
        return f"Contact Our {clean_niche} Team"
    if "service" in url_lower or "package" in url_lower:
        return f"Browse {clean_niche} Packages"
    if "about" in url_lower:
        return f"About Our {clean_niche} Agency"
    if "portfolio" in url_lower or "gallery" in url_lower:
        return f"View {clean_niche} Portfolio"
    if "pricing" in url_lower or "cost" in url_lower:
        return f"Check {clean_niche} Pricing"

    if clean_topic:
        return f"Read Our {clean_topic[:30]} Guide"
    return f"Explore {clean_niche} Services"


def _suggest_keyword_replacement(
    wrong_kw: str,
    status: str,
    kw_intent: str,
    primary_intent: str,
    niche: str,
    niche_terms: List[str],
    article_title: str = "",
) -> Tuple[str, str]:
    """Generates a contextual, natural search-optimized replacement keyword.
    Never mechanically concatenates niche + keyword + planning."""
    clean = " ".join(w for w in re.sub(r"[^a-zA-Z0-9\s]", "", wrong_kw).split()).title()
    niche_main = (niche or "Business").split("/")[0].strip()
    niche_core = "Event" if "event" in niche_main.lower() else niche_main.split()[-1]
    primary_intent = primary_intent or "Informational"

    words = clean.split()
    words_lower = [w.lower() for w in words]
    kw_lower = clean.lower()
    title_lower = (article_title or "").lower()

    # Detect any specific occasion/festival in the keyword or article title
    festivals = ["diwali", "holi", "eid", "christmas", "new year", "halloween", "thanksgiving", "wedding", "birthday", "anniversary", "kitty"]
    detected_occasion = None
    for fest in festivals:
        if fest in kw_lower or fest in title_lower:
            detected_occasion = fest.title()
            break

    # 1. Festival / Occasion Timing (e.g. "weeks before diwali", "diwali dates")
    timing_words = {"week", "weeks", "month", "months", "day", "days", "advance", "early", "timeline", "before", "schedule", "when"}
    if any(w in words_lower for w in timing_words) and detected_occasion:
        sug = f"{detected_occasion} Party Booking Timeline" if primary_intent == "Informational" else f"Advance {detected_occasion} Venue Booking"
        reason = f"Converts conversational timeline mention into a search-aligned {primary_intent} keyword for {detected_occasion.lower()} planning."
        return sug, reason

    # 2. Advance Booking / Timelines without specific festival (e.g. "far advance", "advance booking")
    if ("advance" in words_lower or "far advance" in kw_lower or "early" in words_lower) and any(w in words_lower for w in {"far", "early", "book", "booking", "advance", "timeline"}):
        if primary_intent == "Informational":
            sug = f"How Far in Advance to Book {niche_core} Venues"
        elif primary_intent == "Commercial":
            sug = f"Best Early Booking {niche_core} Packages"
        else:
            sug = f"Book {niche_core} Venues in Advance"
        reason = f"Transforms conversational advance-timing fragment into an actionable {primary_intent} search query."
        return sug, reason

    # 3. Urgency / Availability / Capacity (e.g. "fill fast", "sold out", "availability", "slots")
    urgency_terms = {"fill", "fast", "rush", "sold", "slots", "availability", "capacity", "crowd"}
    if any(w in words_lower for w in urgency_terms):
        if primary_intent == "Informational":
            sug = f"Peak Season {niche_core} Availability & Booking Tips"
        elif primary_intent == "Commercial":
            sug = f"Top {niche_core} Venues with Instant Booking"
        else:
            sug = f"Reserve {niche_core} Slots Early"
        reason = f"Replaces conversational availability fragment with a search-intent {primary_intent} query."
        return sug, reason

    # 4. Quotes / Budget / Cost / Estimates (e.g. "quotes", "pricing", "budget")
    pricing_terms = {"quotes", "quote", "cost", "pricing", "price", "budget", "rates", "fee", "estimate", "packages"}
    if any(w in words_lower for w in pricing_terms):
        if primary_intent == "Informational":
            sug = f"{niche_core} Budget Breakdown & Cost Estimation"
        elif primary_intent == "Commercial":
            sug = f"{niche_core} Vendor Quotes & Price Comparison"
        else:
            sug = f"Get Free {niche_core} Vendor Quotes"
        reason = f"Upgrades standalone pricing term into a high-intent {primary_intent} keyword for vendor evaluation."
        return sug, reason

    # 5. Decor / Themes / Styling (e.g. "rose gold", "emerald", "decor", "aesthetic")
    decor_terms = {"rose", "emerald", "gold", "silver", "decor", "theme", "palette", "color", "aesthetic", "floral", "design", "lighting"}
    if any(w in words_lower for w in decor_terms):
        if primary_intent == "Informational":
            sug = f"{clean} {niche_core} Theme & Decor Ideas"
        elif primary_intent == "Commercial":
            sug = f"Best {clean} Decor Packages for {niche_core}s"
        else:
            sug = f"Book {clean} Decorators"
        reason = f"Aligns styling concept with popular {primary_intent} visual search queries."
        return sug, reason

    # 6. Gatherings / Celebrations (e.g. "kitty party", "gathering", "celebration", "meetup")
    gathering_terms = {"kitty", "gathering", "party", "celebration", "meetup", "get-together", "function", "ceremony"}
    if any(w in words_lower for w in gathering_terms):
        prefix = f"{detected_occasion} " if detected_occasion and detected_occasion.lower() not in kw_lower else ""
        if primary_intent == "Informational":
            sug = f"{prefix}{clean} Hosting & Planning Checklist"
        elif primary_intent == "Commercial":
            sug = f"Best {prefix}{clean} Venues & Packages"
        else:
            sug = f"Book {prefix}{clean} Spaces"
        reason = f"Enhances casual gathering phrase into a structured {primary_intent} search keyword."
        return sug, reason

    # 7. Specific occasion on its own (e.g. "Diwali", "New Year")
    if detected_occasion and len(words) <= 2:
        if primary_intent == "Informational":
            sug = f"{detected_occasion} Celebration Ideas & Checklist"
        elif primary_intent == "Commercial":
            sug = f"Best {detected_occasion} Party Venues & Packages"
        else:
            sug = f"Book {detected_occasion} Event Venues"
        reason = f"Expands single festive reference into a complete {primary_intent} search query."
        return sug, reason

    # 8. Conversational fragments / generic words
    # Never mechanically prepend "Event " and append " Planning"
    if len(words) <= 2:
        if primary_intent == "Informational":
            sug = f"{clean} Guide for {niche_main}"
        elif primary_intent == "Commercial":
            sug = f"Top {clean} Options & Comparison"
        elif primary_intent == "Transactional":
            sug = f"Book {clean} for {niche_main}"
        else:
            sug = f"{clean} Overview & Best Practices"
    else:
        if primary_intent == "Informational":
            sug = f"{clean}: Best Practices & Tips"
        elif primary_intent == "Commercial":
            sug = f"{clean} Options & Review"
        else:
            sug = f"{clean} Services & Solutions"

    reason = f"Converts off-target wording into a search-aligned {primary_intent} keyword matching the {niche_main} context."
    return sug, reason


# --------------------------------------------------------------------------- #
# Main audit
# --------------------------------------------------------------------------- #
def audit_blog_post(
    project_url: str,
    blog_url: str,
    niche: Optional[str] = None,
    focus_keyword: Optional[str] = None,
    check_links: bool = False,
) -> Dict[str, Any]:
    """
    Audits a blog post/article against the project's niche and Google AI Overview readiness.
    check_links=True also tests up to 20 links for 404/410/5xx (slower).
    """
    project_clean = _clean_url(project_url)
    blog_clean = _clean_url(blog_url)

    # ---- 1. Project context -------------------------------------------------
    project_ctx = analyze_project_niche(project_clean, override_niche=niche)
    project_niche = project_ctx["niche"]
    project_domain = project_ctx["domain"]
    niche_terms: List[str] = project_ctx["niche_terms"]
    niche_stems = {_stem(t) for t in niche_terms} | {_stem(t) for t in project_ctx["category_terms"]}

    # ---- 2. Fetch blog ------------------------------------------------------
    resp, err = _fetch(blog_clean)
    if resp is None:
        raise ValueError(f"Could not fetch blog post at {blog_clean}: {err}.")
    if resp.status_code != 200:
        hint = " (the site may be blocking bots, e.g. Cloudflare)" if resp.status_code in (403, 429, 503) else ""
        raise ValueError(f"Blog URL returned HTTP {resp.status_code}{hint}: {blog_clean}")
    if "html" not in resp.headers.get("Content-Type", "html").lower():
        raise ValueError(f"URL is not an HTML page (Content-Type: {resp.headers.get('Content-Type')}).")

    final_url = resp.url
    soup = BeautifulSoup(resp.text, "html.parser")
    article_soup = _extract_main_content(soup)

    # ---- Metadata -----------------------------------------------------------
    title = (soup.title.string or "").strip() if soup.title and soup.title.string else ""
    meta_desc = _meta_content(soup, name="description") or _meta_content(soup, property="og:description")
    canon_tag = soup.find("link", rel="canonical")
    canonical = (canon_tag.get("href") or "").strip() if canon_tag else ""

    schema_objs, schema_types = _parse_schema(soup)
    has_article_schema = any(t in ARTICLE_SCHEMA_TYPES for t in schema_types)
    has_faq_schema = "FAQPage" in schema_types
    has_howto_schema = "HowTo" in schema_types
    article_obj = next((o for o in schema_objs if str(o.get("@type", "")) in ARTICLE_SCHEMA_TYPES
                        or (isinstance(o.get("@type"), list) and ARTICLE_SCHEMA_TYPES & set(o["@type"]))), {})

    # Author
    author = ""
    a_tag = soup.find("meta", attrs={"name": "author"}) or soup.find("a", rel="author")
    if a_tag:
        author = (a_tag.get("content") or a_tag.get_text(strip=True) or "").strip()
    if not author:
        sa = article_obj.get("author")
        if isinstance(sa, list) and sa:
            sa = sa[0]
        if isinstance(sa, dict):
            author = str(sa.get("name", "")).strip()
        elif isinstance(sa, str):
            author = sa.strip()
    if not author:
        for sel in [".author", ".author-name", ".byline", "[itemprop='author']"]:
            found = soup.select(sel)
            if found:
                author = found[0].get_text(strip=True)[:40]
                break

    # Dates
    date_tag = soup.find("meta", attrs={"property": "article:published_time"}) or soup.find("time")
    publish_date = ""
    if date_tag:
        publish_date = date_tag.get("content") or date_tag.get("datetime") or date_tag.get_text(strip=True) or ""
    publish_date = publish_date or str(article_obj.get("datePublished", ""))
    modified_date = _meta_content(soup, property="article:modified_time") or str(article_obj.get("dateModified", ""))

    # ---- Headings (article scope first, page as fallback) ---------------------
    def _heads(tag: str, fallback: bool) -> List[str]:
        found = [h.get_text(" ", strip=True) for h in article_soup.find_all(tag) if h.get_text(strip=True)]
        if not found and fallback:
            found = [h.get_text(" ", strip=True) for h in soup.find_all(tag) if h.get_text(strip=True)]
        return found

    h1s = _heads("h1", True)          # H1 often sits outside <article>
    h2s = _heads("h2", False)
    h3s = _heads("h3", False)

    # ---- Body text (paragraphs + list items) -----------------------------------
    blocks = [el.get_text(" ", strip=True) for el in article_soup.find_all(["p", "li"])]
    paragraphs = [p.get_text(" ", strip=True) for p in article_soup.find_all("p") if len(p.get_text(strip=True)) > 20]
    full_text = " ".join(b for b in blocks if len(b) > 20)
    all_visible_text = f"{title} {' '.join(h1s)} {' '.join(h2s)} {' '.join(h3s)} {full_text}"
    all_lower = all_visible_text.lower()
    word_count = len(re.findall(r"\b[a-zA-Z0-9_-]+\b", full_text))
    readability = _calculate_readability(full_text)
    first_100 = " ".join(full_text.split()[:100]).lower()
    slug = urlparse(final_url).path.replace("-", " ").replace("_", " ").lower()

    # ---- Indexability gate ------------------------------------------------------
    indexability = _check_indexability(final_url, soup, resp, canonical)
    if word_count < 150 and (len(soup.find_all("script")) > 8 or soup.find(id=re.compile(r"^(root|__next|app)$"))):
        indexability["warnings"].append(
            "Very little server-rendered text found. The content may be rendered by JavaScript, so this audit "
            "(and some crawlers) may not see it. Check with Search Console's URL Inspection tool.")

    # ---- Images -------------------------------------------------------------------
    imgs = article_soup.find_all("img")
    imgs_with_alt = sum(1 for i in imgs if (i.get("alt") or "").strip())
    alt_ratio = (imgs_with_alt / len(imgs)) if imgs else 1.0

    # ---- 3. Links & anchors ---------------------------------------------------------
    blog_domain = _host(final_url)
    own_sites = [blog_domain, project_domain]
    focus_lower = (focus_keyword or "").strip().lower()

    internal_links: List[Dict[str, Any]] = []
    external_links: List[Dict[str, Any]] = []
    seen_links = set()
    generic_count = empty_count = long_count = exact_match_count = 0

    for a in article_soup.find_all("a", href=True):
        raw = a["href"].strip()
        if not raw or raw.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        full_href = urldefrag(urljoin(final_url, raw))[0]
        anchor = a.get_text(" ", strip=True)
        img = a.find("img")
        if not anchor and img and (img.get("alt") or "").strip():
            anchor = img["alt"].strip()
        key = (full_href, anchor.lower())
        if key in seen_links:
            continue
        seen_links.add(key)

        link_host = _host(full_href)
        rel = a.get("rel", [])
        rel = rel.split() if isinstance(rel, str) else rel
        is_empty = not anchor
        is_naked = anchor.lower().startswith(("http://", "https://", "www."))
        is_generic = anchor.lower().strip(" .:>»→") in GENERIC_ANCHORS or is_naked
        is_long = len(anchor.split()) > 8
        is_exact = bool(focus_lower) and anchor.lower() == focus_lower
        generic_count += is_generic
        empty_count += is_empty
        long_count += is_long
        exact_match_count += is_exact

        link_obj = {
            "url": full_href,
            "anchor": anchor or "(Empty / Image)",
            "domain": link_host or blog_domain,
            "is_generic": is_generic,
            "is_empty": is_empty,
            "is_too_long": is_long,
            "nofollow": "nofollow" in rel or "sponsored" in rel or "ugc" in rel,
        }
        if not link_host or _same_site(link_host, own_sites):
            internal_links.append(link_obj)
        else:
            link_obj["high_authority"] = _is_high_authority(link_host)
            external_links.append(link_obj)

    broken_links = _find_broken_links(internal_links + external_links) if check_links else []

    # ---- 4. Search intent label -----------------------------------------------------
    intent_scores = {k: 0 for k in INTENT_TRIGGERS}
    h1_title = f"{title} {' '.join(h1s)}".lower()
    h2_text = " ".join(h2s).lower()
    body_lower = full_text.lower()
    for intent_name, triggers in INTENT_TRIGGERS.items():
        for tr in triggers:
            if _count_phrase(h1_title, tr):
                intent_scores[intent_name] += 4
            if _count_phrase(slug, tr):
                intent_scores[intent_name] += 3
            if _count_phrase(h2_text, tr):
                intent_scores[intent_name] += 2
            intent_scores[intent_name] += min(_count_phrase(body_lower, tr), 5)

    if sum(intent_scores.values()) == 0:
        intent_scores["Informational"] = 5  # blogs default to informational

    total_pts = sum(intent_scores.values())
    intent_breakdown = {k: round(v / total_pts * 100) for k, v in intent_scores.items()}
    ranked = sorted(intent_breakdown.items(), key=lambda kv: kv[1], reverse=True)
    primary_intent = ranked[0][0]
    gap = ranked[0][1] - ranked[1][1]
    intent_confidence = "High" if gap >= 30 else "Medium" if gap >= 15 else "Low (mixed intent)"
    secondary_intent = ranked[1][0] if ranked[1][1] >= 20 else None

    # ---- 5. Keyword extraction & alignment ---------------------------------------------
    clean_words = re.findall(r"\b[a-zA-Z]{3,}\b", all_lower)
    filtered_words = [w for w in clean_words if w not in STOP_WORDS]
    CONV_FRAGMENTS = {
        "fill", "fast", "far", "advance", "sure", "look", "come", "take", "give", "put",
        "set", "keep", "let", "back", "away", "ahead", "last", "next", "first", "still",
        "already", "well", "ever", "never", "always", "really", "quite", "rather", "much",
        "many", "good", "great", "thing", "things", "lot", "lots", "kind", "kinds"
    }
    bigrams = [
        f"{a} {b}" for a, b in zip(clean_words, clean_words[1:])
        if a not in STOP_WORDS and b not in STOP_WORDS and not (a in CONV_FRAGMENTS and b in CONV_FRAGMENTS)
    ]
    trigrams = [
        f"{a} {b} {c}" for a, b, c in zip(clean_words, clean_words[1:], clean_words[2:])
        if a not in STOP_WORDS and c not in STOP_WORDS and not (a in CONV_FRAGMENTS and b in CONV_FRAGMENTS and c in CONV_FRAGMENTS)
    ]
    word_counts, bigram_counts, trigram_counts = Counter(filtered_words), Counter(bigrams), Counter(trigrams)

    def _placement(phrase: str) -> Dict[str, bool]:
        p = phrase.lower()
        return {
            "in_title": bool(_count_phrase(title.lower(), p)),
            "in_h1": any(_count_phrase(h.lower(), p) for h in h1s),
            "in_h2": any(_count_phrase(h.lower(), p) for h in h2s),
            "in_first_100_words": bool(_count_phrase(first_100, p)),
        }

    keywords: List[Dict[str, Any]] = []
    seen_tokens: set = set()

    if focus_lower:
        count_fk = _count_phrase(all_lower, focus_lower)
        keywords.append({
            "keyword": focus_keyword.strip(),
            "type": "Focus Keyword",
            "count": count_fk,
            "density": round(count_fk * len(focus_lower.split()) / max(word_count, 1) * 100, 2),
            **_placement(focus_lower),
            "in_meta_description": bool(_count_phrase(meta_desc.lower(), focus_lower)),
            "in_url": focus_lower in slug,
        })

    def _add(phrase: str, count: int, kind: str, n_words: int):
        toks = set(phrase.split())
        if toks and toks <= seen_tokens and n_words < 3:   # already covered by a longer phrase
            return
        seen_tokens.update(toks)
        keywords.append({
            "keyword": phrase.title(),
            "type": kind,
            "count": count,
            "density": round(count * n_words / max(word_count, 1) * 100, 2),
            **_placement(phrase),
        })

    for phrase, c in trigram_counts.most_common(5):
        if c >= 2:
            _add(phrase, c, "Long-tail (3-word)", 3)
    for phrase, c in bigram_counts.most_common(8):
        if c >= 2:
            _add(phrase, c, "Keyphrase (2-word)", 2)
    for word, c in word_counts.most_common(6):
        if c >= 3:
            _add(word, c, "Core Term (1-word)", 1)
    keywords = keywords[:15]

    # Judge each keyword against intent AND contextual niche
    # Include article context stems from title and main headings so topical sub-themes are aligned
    article_context_stems = _stems(title + " " + " ".join(h1s) + " " + " ".join(h2s[:5]))
    expanded_niche_stems = set(niche_stems)
    if bool(article_context_stems & niche_stems):
        expanded_niche_stems.update(article_context_stems)

    for kw in keywords:
        k_intent = _keyword_intent(kw["keyword"])
        kw["intent"] = k_intent
        kw["intent_aligned"] = _intent_ok(k_intent, primary_intent)
        if expanded_niche_stems:
            kw["niche_aligned"] = bool(_stems(kw["keyword"]) & expanded_niche_stems)
        else:
            kw["niche_aligned"] = None   # unknown: project site gave no niche terms
        if kw["niche_aligned"] is None:
            kw["status"] = "Optimal (niche unknown)" if kw["intent_aligned"] else "Off-Intent"
        elif kw["intent_aligned"] and kw["niche_aligned"]:
            kw["status"] = "Optimal"
        elif not kw["intent_aligned"] and not kw["niche_aligned"]:
            kw["status"] = "Off-Intent & Off-Niche"
        elif not kw["intent_aligned"]:
            kw["status"] = "Off-Intent"
        else:
            kw["status"] = "Off-Niche"

    misaligned = [{"keyword": k["keyword"], "status": k["status"], "intent": k["intent"]}
                  for k in keywords if k["status"] not in ("Optimal", "Optimal (niche unknown)")]
    aligned_n = len(keywords) - len(misaligned)
    aligned_pct = round(aligned_n / len(keywords) * 100) if keywords else 0
    keyword_alignment = {
        "aligned": aligned_n,
        "total": len(keywords),
        "percent": aligned_pct,
        "verdict": "Strong" if aligned_pct >= 80 else "Moderate" if aligned_pct >= 60 else "Weak",
        "misaligned": misaligned,
        "primary_intent": primary_intent,
        "niche": project_niche,
        "niche_known": bool(niche_stems),
    }

    # Overall niche alignment: how many of the site's top terms show up in this post
    article_stems = _stems(all_visible_text)
    check_terms = niche_terms[:8]
    niche_hits = sum(1 for t in check_terms if _stem(t) in article_stems)
    niche_alignment_score = round(niche_hits / len(check_terms) * 100) if check_terms else None

    # Off-topic anchors: descriptive anchors sharing no words with the niche or the post's own top terms
    topic_stems = niche_stems | {_stem(w) for w, _ in word_counts.most_common(25)}
    off_topic_anchor_count = 0
    for l in internal_links + external_links:
        if not l["is_generic"] and not l["is_empty"]:
            l["on_topic"] = bool(_stems(l["anchor"]) & topic_stems)
            off_topic_anchor_count += (not l["on_topic"])

    # ---- 6. Google AI Overviews / GEO readiness (heuristic) ---------------------------------
    question_headings = sum(
        1 for h in (h1s + h2s + h3s)
        if h.strip().endswith("?") or re.search(r"\b(what|how|why|when|which|who|where)\b", h.lower()))

    answer_blocks = 0
    for h in article_soup.find_all(["h2", "h3"]):
        nxt = h.find_next_sibling()
        if nxt is not None and nxt.name == "p" and 30 <= len(nxt.get_text().split()) <= 80:
            answer_blocks += 1
    concise_definition = False
    for p in paragraphs[:5]:
        if 35 <= len(p.split()) <= 75 and any(c in p.lower() for c in
                ["is defined as", "refers to", "means", "is a", "to achieve this", "the main", "in simple terms"]):
            concise_definition = True
            answer_blocks += 1
            break
    snippet_sample = ""
    if paragraphs:
        snippet_sample = paragraphs[0][:280] + ("..." if len(paragraphs[0]) > 280 else "")

    ordered_lists = len(article_soup.find_all("ol"))
    unordered_lists = len(article_soup.find_all("ul"))
    tables = len(article_soup.find_all("table"))
    stat_numbers = len(STAT_RE.findall(full_text))

    skipped_level = bool(h3s) and not h2s
    has_credible_sources = any(l.get("high_authority") for l in external_links) or len(external_links) >= 2
    self_canonical = bool(canonical) and _normalize_for_compare(urljoin(final_url, canonical)) == _normalize_for_compare(final_url)

    checks: List[Dict[str, Any]] = []

    def _check(aspect, pts, ok_status, bad_status, ok_detail, bad_detail):
        passed = pts >= 14
        checks.append({
            "aspect": aspect, "passed": passed, "points": f"{pts}/20",
            "status": ok_status if passed else bad_status,
            "detail": ok_detail if passed else bad_detail,
        })
        return pts

    da_pts = min(8, question_headings * 3) + min(12, answer_blocks * 6)
    s1 = _check(
        "Direct Answer Blocks", da_pts, "Optimized", "Needs Refinement",
        f"{answer_blocks} concise answer block(s) and {question_headings} question-style heading(s) found.",
        "Add a 40-60 word self-contained answer directly under question-style subheadings so it can be quoted.")

    st_pts = ((8 if ordered_lists + unordered_lists + tables >= 2 else 4 if ordered_lists + unordered_lists + tables >= 1 else 0)
              + (8 if len(h2s) >= 3 else 4 if len(h2s) >= 2 else 0)
              + (4 if len(h1s) == 1 and not skipped_level else 0))
    s2 = _check(
        "Structure & Quotability", st_pts, "High Quotability", "Add Formatted Elements",
        f"{ordered_lists} numbered list(s), {unordered_lists} bullet list(s), {tables} table(s), {len(h2s)} H2 section(s).",
        "Use exactly one H1, 3+ H2 sections, plus numbered steps, bullets or comparison tables.")

    ig_pts = min(10, stat_numbers * 2) + (10 if word_count >= 1000 else 7 if word_count >= 600 else 4 if word_count >= 300 else 0)
    s3 = _check(
        "Information Gain & Data", ig_pts, "Strong Information Gain", "Lacks Unique Data",
        f"{stat_numbers} concrete figure(s) (percentages, amounts, years) and {word_count} words.",
        "Add original statistics, benchmarks, dated facts, quotes or first-hand examples; thin generic text gets summarised away.")

    ee_pts = (5 if author else 0) + (5 if has_article_schema else 0) + (5 if has_credible_sources else 0) + (5 if publish_date else 0)
    s4 = _check(
        "E-E-A-T & Credibility", ee_pts, "Authoritative", "Add Author & Citations",
        f"Author ({author or 'found'}), publish date, Article schema and outbound citations look good.",
        "Show an author byline with credentials, a visible publish date, Article/BlogPosting schema, and cite reputable sources.")

    fm_pts = (6 if modified_date else 0) + (6 if imgs else 0) + (4 if alt_ratio >= 0.8 else 0) + (4 if self_canonical else 0)
    s5 = _check(
        "Freshness, Media & Canonical", fm_pts, "Healthy", "Needs Attention",
        f"Modified date present, {len(imgs)} image(s) ({round(alt_ratio * 100)}% with alt text), self-referencing canonical.",
        "Add a visible 'last updated' date, relevant images with alt text, and a self-referencing canonical tag.")

    ai_bot_score = s1 + s2 + s3 + s4 + s5
    if not indexability["indexable"]:
        ai_bot_score = min(ai_bot_score, 25)
        badge = "Not Eligible (blocked from Search)"
        summary = "Content quality does not matter until the blocking issue below is fixed: " + "; ".join(indexability["blocking"])
    elif ai_bot_score >= 80:
        badge = "High Citation Potential"
        summary = "Strong answer blocks, structure and information gain. Likely well positioned for AI Overview citation."
    elif ai_bot_score >= 60:
        badge = "Moderate Citation Potential"
        summary = "Solid base. Tighter 45-word answers, tables and original data would improve AI Overview inclusion."
    else:
        badge = "Optimization Required"
        summary = "Currently structured for traditional reading. Restructure into question-and-answer sections with data."

    # ---- 7. Recommendations -------------------------------------------------------------------
    fixes: List[Dict[str, Any]] = []

    def _fix(priority, category, title_, action, fix_type=None, suggestions=None):
        rec = {"priority": priority, "category": category, "title": title_, "action": action}
        if fix_type:
            rec["type"] = fix_type
        if suggestions:
            rec["suggestions"] = suggestions
        fixes.append(rec)

    for issue in indexability["blocking"]:
        _fix("Critical", "Indexability", "Page is blocked from Google", issue)
    for w in indexability["warnings"]:
        if not w.startswith("No canonical"):
            _fix("Medium", "Indexability", "Crawl / canonical warning", w)
        else:
            _fix("Medium", "Indexability", "Add a canonical tag", "Add <link rel=\"canonical\"> pointing to this page's own URL.")
    if not title:
        _fix("High", "On-Page", "Missing <title>", "Add a unique title of roughly 30-60 characters.")
    elif len(title) > 60 or len(title) < 30:
        _fix("Medium", "On-Page", f"Title length is {len(title)} characters", "Aim for 30-60 characters so it is not truncated in results.")
    if not meta_desc:
        _fix("Medium", "On-Page", "Missing meta description", "Write a 120-160 character summary that includes the primary keyword.")
    elif not 120 <= len(meta_desc) <= 160:
        _fix("Low", "On-Page", f"Meta description is {len(meta_desc)} characters", "Aim for 120-160 characters.")
    if len(h1s) != 1:
        _fix("High", "On-Page", f"{len(h1s)} H1 tags found", "Use exactly one H1 that states the post's topic.")
    if focus_lower:
        fk = keywords[0]
        missing = [lbl for key, lbl in [("in_title", "title"), ("in_h1", "H1"), ("in_first_100_words", "first 100 words"),
                                         ("in_meta_description", "meta description"), ("in_url", "URL slug")] if not fk.get(key)]
        if missing:
            _fix("High", "Keywords", f"Focus keyword missing from: {', '.join(missing)}", f"Place '{focus_keyword.strip()}' naturally in these spots.")
        if fk["density"] > 3:
            _fix("Medium", "Keywords", f"Focus keyword density {fk['density']}%", "Possible keyword stuffing; keep it natural (roughly 0.5-2%).")
        if exact_match_count > 3:
            _fix("Medium", "Links & Anchors", f"{exact_match_count} exact-match anchors", "Vary anchor text; many identical keyword anchors look manipulative.")
    if misaligned:
        kw_suggestions = []
        for m in misaligned:
            sug_kw, sug_reason = _suggest_keyword_replacement(
                m["keyword"], m["status"], m.get("intent", ""), primary_intent, project_niche, niche_terms,
                article_title=title
            )
            m["suggested_replacement"] = sug_kw
            m["suggestion_reason"] = sug_reason
            kw_suggestions.append({
                "current": m["keyword"],
                "issue": m["status"],
                "replacement": sug_kw,
                "reason": sug_reason,
            })

        for kw in keywords:
            for s in kw_suggestions:
                if kw["keyword"].lower() == s["current"].lower():
                    kw["suggested_replacement"] = s["replacement"]
                    kw["suggestion_reason"] = s["reason"]
                    break

        _fix(
            "High" if aligned_pct < 60 else "Medium",
            "Keywords",
            f"{len(misaligned)} keyword(s) off intent or niche",
            f"Replace off-target phrases with {primary_intent} keywords directly connected to {project_niche}:",
            fix_type="keywords",
            suggestions=kw_suggestions,
        )
    if intent_confidence.startswith("Low") and secondary_intent:
        _fix("Medium", "Search Intent", f"Mixed intent ({primary_intent} + {secondary_intent})",
             "Pick one dominant intent for this URL, or split the content into two focused pages.")
    if generic_count:
        generic_links = [l for l in (internal_links + external_links) if l.get("is_generic")]
        generic_sugs = []
        for l in generic_links[:10]:
            sug_anchor = _suggest_anchor(l, project_niche, title)
            generic_sugs.append({
                "current": l["anchor"],
                "url": l["url"],
                "issue": "Generic / Naked Anchor",
                "replacement": sug_anchor,
                "reason": "Descriptive anchor text provides clear semantic context to Google AI and visitors.",
            })
        _fix(
            "High",
            "Links & Anchors",
            f"Replace {generic_count} generic/naked anchor(s)",
            "Replace low-value anchors ('click here', raw URLs) with keyword-rich descriptive text:",
            fix_type="anchors",
            suggestions=generic_sugs,
        )
    if empty_count:
        empty_links = [l for l in (internal_links + external_links) if l.get("is_empty")]
        empty_sugs = []
        for l in empty_links[:10]:
            sug_anchor = _suggest_anchor(l, project_niche, title)
            empty_sugs.append({
                "current": "(Empty / Image Link)",
                "url": l["url"],
                "issue": "Empty Anchor / Missing Alt",
                "replacement": sug_anchor,
                "reason": "Add descriptive anchor text or image alt text so search crawlers can parse the link destination.",
            })
        _fix(
            "Medium",
            "Links & Anchors",
            f"{empty_count} link(s) with empty anchor text",
            "Add descriptive text or alt text for these unlabelled links:",
            fix_type="anchors",
            suggestions=empty_sugs,
        )
    if long_count:
        long_links = [l for l in (internal_links + external_links) if l.get("is_too_long")]
        long_sugs = []
        for l in long_links[:10]:
            sug_anchor = _suggest_anchor(l, project_niche, title)
            long_sugs.append({
                "current": l["anchor"],
                "url": l["url"],
                "issue": f"Too Long ({len(l['anchor'].split())} words)",
                "replacement": sug_anchor,
                "reason": "Shorten to 2-5 concise words to avoid anchor text dilution and spam signals.",
            })
        _fix(
            "Low",
            "Links & Anchors",
            f"{long_count} anchor(s) longer than 8 words",
            "Condense verbose anchor text into focused, natural phrasing:",
            fix_type="anchors",
            suggestions=long_sugs,
        )
    if off_topic_anchor_count:
        off_topic_links = [l for l in (internal_links + external_links) if not l.get("on_topic", True) and not l.get("is_generic") and not l.get("is_empty")]
        off_topic_sugs = []
        for l in off_topic_links[:10]:
            sug_anchor = _suggest_anchor(l, project_niche, title)
            off_topic_sugs.append({
                "current": l["anchor"],
                "url": l["url"],
                "issue": "Off-Topic Anchor",
                "replacement": sug_anchor,
                "reason": f"Aligns link text with {project_niche} terminology and target destination relevance.",
            })
        _fix(
            "Low",
            "Links & Anchors",
            f"{off_topic_anchor_count} anchor(s) unrelated to the topic or niche",
            f"Replace off-topic anchors with terms that reflect {project_niche} and the target destination:",
            fix_type="anchors",
            suggestions=off_topic_sugs,
        )
    if len(internal_links) < 2:
        _fix("Medium", "Internal Linking", "Add internal topic-cluster links", f"Link to related pages on {project_domain} to build topical authority.")
    citation_recommendations = _get_niche_citations(project_niche, title)
    if external_links and not any(l.get("high_authority") for l in external_links):
        _fix(
            "Low",
            "Links & Anchors",
            "No high-authority external sources",
            "Boost credibility by referencing reputable industry publications or scientific/market studies:",
            fix_type="citations",
            suggestions=citation_recommendations,
        )
    if not external_links:
        _fix(
            "Medium",
            "Links & Anchors",
            "No outbound citations",
            f"Add 2+ citations to authoritative third-party sources to build E-E-A-T for {project_niche}:",
            fix_type="citations",
            suggestions=citation_recommendations,
        )
    for b in broken_links:
        _fix("High", "Links & Anchors", f"Broken link ({b['status']})", b["url"])
    if not has_article_schema:
        _fix("High", "Google AI Bot", "Add Article/BlogPosting JSON-LD", "Include headline, author, datePublished, dateModified and publisher.")
    if not author:
        _fix("Medium", "E-E-A-T", "No author detected", "Add a visible byline with author credentials.")
    if not publish_date:
        _fix("Medium", "E-E-A-T", "No publish date detected", "Show a visible publish date and add datePublished to schema.")
    if word_count < 600:
        _fix("High", "Content Depth", f"Thin content ({word_count} words)", "In-depth posts that earn AI citations usually run 1,000+ words with clear subtopics.")
    if answer_blocks == 0:
        _fix("High", "Google AI Bot", "Add direct answer blocks", "Under each question-style heading, add a 40-60 word self-contained answer.")
    if imgs and alt_ratio < 0.8:
        _fix("Low", "Media", f"Only {round(alt_ratio * 100)}% of images have alt text", "Add descriptive alt text to every content image.")
    if not has_faq_schema and question_headings >= 3:
        _fix("Low", "Google AI Bot", "Consider FAQ markup", "You have several question headings; an FAQ section with FAQPage schema may help.")

    order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    fixes.sort(key=lambda f: order[f["priority"]])

    # ---- Overall score (continuous sub-scores) ------------------------------------------------------
    link_score = 100 - min(40, generic_count * 10) - min(15, empty_count * 5) - min(30, len(broken_links) * 10) \
        - (20 if len(internal_links) < 2 else 0) - (10 if not external_links else 0)
    link_score = max(0, link_score)
    structure_score = (25 * bool(title and 30 <= len(title) <= 60) + 25 * bool(120 <= len(meta_desc) <= 160)
                       + 25 * (len(h1s) == 1) + 25 * bool(len(h2s) >= 2 and word_count >= 600))
    kw_score = aligned_pct if keywords else 50

    overall = int(ai_bot_score * 0.35 + kw_score * 0.25 + link_score * 0.20 + structure_score * 0.20)
    overall = max(0, min(100, overall))
    if not indexability["indexable"]:
        overall = min(overall, 40)

    return {
        "blog_url": blog_clean,
        "final_url": final_url,
        "project_url": project_clean,
        "project_niche": project_niche,
        "niche_detected_from": project_ctx["detected_from"],
        "niche_terms": niche_terms,
        "niche_alignment_score": niche_alignment_score,   # None = project niche terms unavailable
        "overall_health_score": overall,
        "score_breakdown": {
            "ai_bot_readiness": ai_bot_score, "keyword_alignment": kw_score,
            "links_and_anchors": link_score, "on_page_structure": structure_score,
        },

        # Meta & structure
        "title": title, "title_length": len(title),
        "meta_description": meta_desc, "meta_length": len(meta_desc),
        "canonical": canonical,
        "author": author or "Not detected",
        "publish_date": publish_date or "Not detected",
        "modified_date": modified_date or "Not detected",
        "word_count": word_count,
        "readability": readability,
        "headings": {"h1": h1s, "h2": h2s, "h3": h3s, "total_h2": len(h2s), "total_h3": len(h3s)},
        "schema_types": schema_types,
        "images": {"total": len(imgs), "with_alt": imgs_with_alt},

        # Indexability gate
        "indexability": indexability,

        # Intent
        "primary_intent": primary_intent,
        "secondary_intent": secondary_intent,
        "intent_confidence": intent_confidence,
        "intent_breakdown": intent_breakdown,
        "intent_explanation": INTENT_EXPLANATIONS[primary_intent],

        # Keywords
        "keywords": keywords,
        "keyword_alignment": keyword_alignment,

        # Links
        "links_summary": {
            "total_links": len(internal_links) + len(external_links),
            "internal_count": len(internal_links),
            "external_count": len(external_links),
            "generic_anchor_count": generic_count,
            "empty_anchor_count": empty_count,
            "long_anchor_count": long_count,
            "exact_match_anchor_count": exact_match_count,
            "off_topic_anchor_count": off_topic_anchor_count,
            "broken_links": broken_links,
            "broken_check_ran": check_links,
            "internal_links": internal_links[:15],
            "external_links": external_links[:15],
        },

        # Google AI Overviews / GEO (heuristic)
        "ai_bot_readiness": {
            "score": ai_bot_score,
            "badge": badge,
            "summary": summary,
            "checks": checks,
            "snippet_sample": snippet_sample,
            "suggested_ai_overview": f"**Google AI Bot Summary for '{title}':**\n"
                                     f"{snippet_sample or 'This article provides actionable insights into ' + project_niche + '.'}",
            "disclaimer": "Heuristic score. Google uses normal Search indexing and snippet eligibility for AI Overviews; there is no official AI-readiness score.",
        },

        "recommendations": fixes,
    }


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Audit a blog post against a project's niche")
    ap.add_argument("project_url")
    ap.add_argument("blog_url")
    ap.add_argument("--niche", default=None)
    ap.add_argument("--focus", default=None, help="focus keyword")
    ap.add_argument("--check-links", action="store_true", help="test up to 20 links for 404/5xx")
    args = ap.parse_args()
    print(json.dumps(audit_blog_post(args.project_url, args.blog_url, args.niche, args.focus, args.check_links),
                     indent=2, ensure_ascii=False, default=str))