"""Find high-authority off-page & local SEO submission websites for each SEO task, and tell the
SEO team on which of them the target site (e.g. tracevenue.com) is ALREADY registered.

Pipeline per category (categories run in parallel):
  1. Seed list      -> verified SUBMISSION_PLATFORMS dict (submission_seeds.py)
  2. Discover       -> ddgs search + listicle page scraping to find extra domains
  3. Enrich         -> real DA from Moz (fallback: Open PageRank estimate), cached in SQLite
  4. Validate       -> site must be reachable (unreachable sites are dropped, not re-added)
  5. Rank           -> sort by DA desc (unknown DA last), keep up to MAX_PER_CATEGORY
  6. Presence check -> Registered / Not Registered / Unverified via layered checks
                       (team tracker -> backlink data -> profile probe -> footprint search),
                       see presence_checker.py
  7. Export         -> build_excel(result) returns an .xlsx (Status column is last)

Env vars (all optional):
  MOZ_ACCESS_ID, MOZ_SECRET_KEY   Moz Links API v2 credentials (real Domain Authority)
  OPR_API_KEY                     Open PageRank key (fallback, estimate only)
  SEO_MIN_DA (default 80), SEO_MAX_PER_CATEGORY (default 50), SEO_CACHE_DB
  + the presence-check variables documented in presence_checker.py
"""
from __future__ import annotations

import json
import logging
import os
import re
import sqlite3
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from io import BytesIO
from typing import Callable
from urllib.parse import urlparse

import httpx
from openpyxl import Workbook
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

# Seed platforms + presence checker live next to this file (tools/)
import sys as _sys, os as _os
_tools_dir = _os.path.dirname(__file__)
if _tools_dir not in _sys.path:
    _sys.path.insert(0, _tools_dir)
try:
    from tools.submission_seeds import SUBMISSION_PLATFORMS
    from tools.presence_checker import (PresenceChecker, fetch_moz_referring, site_key,
                                      USE_MOZ_BACKLINKS, USE_FOOTPRINT, USE_PLAYWRIGHT)
except ImportError:
    from submission_seeds import SUBMISSION_PLATFORMS
    from presence_checker import (PresenceChecker, fetch_moz_referring, site_key,
                                  USE_MOZ_BACKLINKS, USE_FOOTPRINT, USE_PLAYWRIGHT)

log = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #
MIN_DA = int(os.getenv("SEO_MIN_DA", "80"))
MAX_PER_CATEGORY = int(os.getenv("SEO_MAX_PER_CATEGORY", "50"))
MAX_CANDIDATES = 200            # discovered domains to score per category (higher = better fill at DA>=80)
CACHE_TTL = 30 * 24 * 3600      # authority changes slowly -> 30 days
CACHE_DB = os.getenv("SEO_CACHE_DB", "da_cache.sqlite3")

MOZ_ID = os.getenv("MOZ_ACCESS_ID", "")
MOZ_SECRET = os.getenv("MOZ_SECRET_KEY", "")
OPR_KEY = os.getenv("OPR_API_KEY", "")

HEADERS_HTTP = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Domains known to be active authority hubs; avoid false-negative drops from aggressive bot shields
TOP_TRUSTED_DOMAINS = {
    "google.com", "youtube.com", "linkedin.com", "reddit.com", "pinterest.com",
    "medium.com", "quora.com", "tumblr.com", "flickr.com", "apple.com", "bing.com",
    "microsoft.com", "github.com", "gitlab.com", "wordpress.com", "blogger.com",
    "vimeo.com", "canva.com", "slideshare.net", "issuu.com", "dribbble.com",
    "behance.net", "craigslist.org", "discord.com", "threads.net", "substack.com",
    "ycombinator.com", "producthunt.com", "archive.org", "wix.com", "weebly.com",
}

SKIP_DISCOVERY = set()

DISCOVERY_QUERIES: dict[str, list[str]] = {
    "Blog Post Submission": [
        "free guest post submission sites list",
        "best free blogging platforms to publish articles",
        "high authority sites that accept guest posts list",
    ],
    "PR Submission": [
        "free press release submission sites list",
        "high DA free press release distribution websites",
    ],
    "Profile Creation": [
        "high DA profile creation sites list",
        "best business profile creation sites for backlinks",
    ],
    "Business Listing": [
        "free business listing sites list",
        "high DA business directory submission sites",
    ],
    "Map Citation": [
        "map citation sites list local SEO",
        "local map listing sites free submit business location",
    ],
    "Classified Ads": [
        "free classified ads posting sites list",
        "high DA classified submission sites",
    ],
    "PPT / Video Submission": [
        "presentation sharing sites list high DA",
        "video sharing and document sharing sites for SEO backlinks",
    ],
    "Infographic Submission": [
        "infographic submission sites list free",
        "free infographic directories to submit",
    ],
    "Image Submission": [
        "image sharing sites list for SEO",
        "free photo sharing websites with profile backlinks",
    ],
    "Micro Blog Submission": [
        "microblogging sites list high DA",
        "web 2.0 blogging sites list",
    ],
    "Blog Promotion": [
        "content curation and blog promotion sites list",
        "sites to promote blog posts free",
    ],
    "Blog Comments": [
        "high DA blog commenting sites list",
        "comment network sites for SEO",
    ],
    "Competitor Backlinks": [
        "blog directories and RSS submission sites",
        "sites to submit blog RSS feed free",
    ],
    "Google Business Profile": [
        "local business directory citation sites",
        "best local search directories for business",
    ],
    "Quora Links": [
        "best QA websites to answer questions for backlinks",
        "top question and answer forum sites",
    ],
    "Reddit Communities": [
        "best niche community forums for sharing content",
        "discussion forums to promote business",
    ],
    "Pinterest Submission": [
        "social bookmarking sites list high DA",
        "visual bookmarking and curation platforms",
    ],
    "Reblogging": [
        "content syndication platforms to republish blog posts",
        "best sites for reblogging articles",
    ],
    "Google Stacking": [
        "google entity stacking properties list",
        "google authority stack for SEO",
    ],
}

BLOCKED_DOMAINS = {
    "google.com", "bing.com", "duckduckgo.com", "facebook.com", "twitter.com", "x.com",
    "instagram.com", "wikipedia.org", "w3.org", "schema.org", "wordpress.org", "github.com",
    "cloudflare.com", "gstatic.com", "googleapis.com", "googletagmanager.com", "apple.com",
    "amazon.com", "pinterest.com", "t.co", "bit.ly", "gravatar.com", "fonts.googleapis.com",
}
TWO_LEVEL_SUFFIXES = {"co.uk", "com.au", "co.in", "com.br", "co.nz", "co.za", "org.uk", "com.sg"}

GENERIC_HOW_TO = (
    "Open the site, create a free account, and submit your content/business details "
    "with your website URL. Confirm the site accepts this task type before posting."
)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def root_domain(url_or_host: str) -> str:
    """medium.com, www.medium.com, https://x.medium.com/abc -> medium.com"""
    s = url_or_host.strip().lower()
    host = urlparse(s if "//" in s else f"//{s}").netloc or s
    host = host.split(":")[0]
    if host.startswith("www."):
        host = host[4:]
    parts = host.split(".")
    if len(parts) >= 3 and ".".join(parts[-2:]) in TWO_LEVEL_SUFFIXES:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:]) if len(parts) >= 2 else host



# --------------------------------------------------------------------------- #
# SQLite cache for authority scores and niche opportunity lists
# --------------------------------------------------------------------------- #
_db_lock = threading.Lock()


def _db() -> sqlite3.Connection:
    conn = sqlite3.connect(CACHE_DB, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS da_cache ("
        "domain TEXT PRIMARY KEY, da INTEGER, source TEXT, ts REAL)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS niche_opportunities ("
        "niche TEXT, category TEXT, domain TEXT, name TEXT, url TEXT, "
        "da_score INTEGER, da_source TEXT, listing_source TEXT, cost TEXT, "
        "action TEXT, how_to_perform TEXT, probe_json TEXT, login_wall INTEGER, "
        "is_seed INTEGER, ts REAL, PRIMARY KEY (niche, category, domain))"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_niche_cat ON niche_opportunities(niche, category)"
    )
    return conn


def _load_niche_opportunities(niche: str, category: str) -> list[dict]:
    """Load previously discovered & verified opportunity websites for this niche + category from SQLite."""
    clean_n = (niche or "general").strip().lower()
    with _db_lock, _db() as conn:
        rows = conn.execute(
            "SELECT name, url, domain, da_score, da_source, listing_source, "
            "cost, action, how_to_perform, probe_json, login_wall, is_seed "
            "FROM niche_opportunities WHERE niche = ? AND category = ? "
            "ORDER BY rowid ASC",
            (clean_n, category),
        ).fetchall()
    links = []
    for r in rows:
        probe = []
        if r[9]:
            try:
                probe = json.loads(r[9])
            except Exception:
                probe = []
        link = _build_link(
            name=r[0],
            url=r[1],
            domain=r[2],
            da=r[3],
            da_source=r[4] or "Unknown",
            listing_source=r[5] or "Saved Opportunity",
            cost=r[6] or "Free",
            action=r[7] or "Register & Submit",
            how_to=r[8] or GENERIC_HOW_TO,
            probe=probe,
            login_wall=bool(r[10]),
            is_seed=bool(r[11]),
        )
        links.append(link)
    return links


def _save_niche_opportunities(niche: str, category: str, links: list[dict]) -> None:
    """Store discovered & verified opportunity websites for this niche + category in SQLite."""
    if not links:
        return
    clean_n = (niche or "general").strip().lower()
    now = time.time()
    records = []
    for l in links:
        records.append((
            clean_n,
            category,
            site_key(l["domain"]),
            l.get("name") or l.get("domain"),
            l.get("url") or f"https://{l['domain']}/",
            l.get("da_score"),
            l.get("da_source") or "Unknown",
            l.get("source") or "Opportunity",
            l.get("cost") or "Free",
            l.get("action") or "Register & Submit",
            l.get("how_to_perform") or GENERIC_HOW_TO,
            json.dumps(l.get("probe") or []),
            1 if l.get("login_wall") else 0,
            1 if l.get("is_seed") else 0,
            now,
        ))
    with _db_lock, _db() as conn:
        conn.executemany(
            "INSERT OR REPLACE INTO niche_opportunities ("
            "niche, category, domain, name, url, da_score, da_source, listing_source, "
            "cost, action, how_to_perform, probe_json, login_wall, is_seed, ts"
            ") VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            records,
        )


def _cache_get(domains: list[str]) -> dict[str, tuple[int, str]]:
    out: dict[str, tuple[int, str]] = {}
    cutoff = time.time() - CACHE_TTL
    with _db_lock, _db() as conn:
        for i in range(0, len(domains), 500):
            chunk = domains[i:i + 500]
            q = ",".join("?" * len(chunk))
            rows = conn.execute(
                f"SELECT domain, da, source FROM da_cache WHERE ts > ? AND source IN ('Moz', 'OPR-estimate') AND domain IN ({q})",
                [cutoff, *chunk],
            ).fetchall()
            out.update({d: (da, src) for d, da, src in rows})
    return out


def _cache_put(items: dict[str, tuple[int, str]]) -> None:
    if not items:
        return
    now = time.time()
    with _db_lock, _db() as conn:
        conn.executemany(
            "INSERT OR REPLACE INTO da_cache(domain, da, source, ts) VALUES (?,?,?,?)",
            [(d, da, src, now) for d, (da, src) in items.items()],
        )


# --------------------------------------------------------------------------- #
# Authority metrics (Moz = real DA, Open PageRank = rough estimate)
# --------------------------------------------------------------------------- #
def _moz_batch(domains: list[str]) -> dict[str, tuple[int, str]]:
    out: dict[str, tuple[int, str]] = {}
    for i in range(0, len(domains), 50):                  # Moz allows 50 targets per request
        chunk = domains[i:i + 50]
        try:
            r = httpx.post(
                "https://lsapi.seomoz.com/v2/url_metrics",
                auth=(MOZ_ID, MOZ_SECRET),
                json={"targets": chunk},
                timeout=30,
            )
            r.raise_for_status()
            results = r.json().get("results", [])
            for dom, res in zip(chunk, results):            # results come back in request order
                da = res.get("domain_authority")
                if da is not None:
                    out[dom] = (int(round(da)), "Moz")
        except Exception as e:                              # noqa: BLE001
            log.warning("Moz batch failed: %s", e)
    return out


def _opr_batch(domains: list[str]) -> dict[str, tuple[int, str]]:
    out: dict[str, tuple[int, str]] = {}
    for i in range(0, len(domains), 100):
        chunk = domains[i:i + 100]
        try:
            r = httpx.get(
                "https://openpagerank.com/api/v1.0/getPageRank",
                params=[("domains[]", d) for d in chunk],
                headers={"API-OPR": OPR_KEY},
                timeout=30,
            )
            r.raise_for_status()
            for item in r.json().get("response", []):
                if item.get("status_code") == 200 and item.get("page_rank_decimal") is not None:
                    # PageRank 0-10 scaled to 0-100: an ESTIMATE, not a true DA
                    out[item["domain"]] = (int(round(item["page_rank_decimal"] * 10)), "OPR-estimate")
        except Exception as e:                              # noqa: BLE001
            log.warning("OpenPageRank batch failed: %s", e)
    return out


def get_da(domains: list[str]) -> dict[str, tuple[int, str]]:
    """domain -> (da, source) for REAL data only (Moz, then Open PageRank). Cached.
    Domains with no real data are simply absent: we no longer invent a number for them."""
    domains = sorted(set(domains))
    result = _cache_get(domains)
    missing = [d for d in domains if d not in result]
    if missing:
        fresh: dict[str, tuple[int, str]] = {}
        if MOZ_ID and MOZ_SECRET:
            fresh.update(_moz_batch(missing))
        still = [d for d in missing if d not in fresh]
        if still and OPR_KEY:
            fresh.update(_opr_batch(still))
        _cache_put(fresh)
        result.update(fresh)
    return result


# --------------------------------------------------------------------------- #
# Discovery (ddgs + listicle scraping)
# --------------------------------------------------------------------------- #
def _ddgs_search(query: str, n: int = 15) -> list[dict]:
    try:
        from ddgs import DDGS
        with DDGS() as d:
            try:
                return list(d.text(query, backend="api", max_results=n))
            except Exception:
                return list(d.text(query, backend="html", max_results=n))
    except Exception as e:                                  # noqa: BLE001
        log.warning("ddgs failed for %r: %s", query, e)
        return []


def _niche_discovery_queries(cat_name: str, niche: str) -> list[str]:
    clean_niche = (niche or "").strip()
    base = DISCOVERY_QUERIES.get(cat_name, [])
    if not clean_niche or clean_niche.lower() in {"general business", "general", "all", "unknown"}:
        return base
    niche_queries = {
        "Blog Post Submission": [
            f"{clean_niche} guest post submission sites list",
            f"{clean_niche} 'write for us' blogs accept guest posts",
        ],
        "PR Submission": [
            f"{clean_niche} press release submission sites distribution",
            f"{clean_niche} news distribution websites free",
        ],
        "Profile Creation": [
            f"{clean_niche} profile creation directory sites list",
            f"{clean_niche} community profile creation platforms",
        ],
        "Business Listing": [
            f"{clean_niche} business listing directories list",
            f"{clean_niche} local business directory submission",
        ],
        "Map Citation": [
            f"{clean_niche} map citations directory listing local",
            f"{clean_niche} locations submit business directory",
        ],
        "Classified Ads": [
            f"{clean_niche} classified ads posting sites list free",
            f"{clean_niche} classifieds submit ad",
        ],
        "PPT / Video Submission": [
            f"{clean_niche} document sharing presentation sites list",
            f"{clean_niche} video sharing platforms",
        ],
        "Infographic Submission": [
            f"{clean_niche} infographic submission directories list",
            f"{clean_niche} visual charts data submission",
        ],
        "Image Submission": [
            f"{clean_niche} photo sharing portfolio submission sites",
            f"{clean_niche} image gallery submission",
        ],
        "Document Sharing": [
            f"{clean_niche} document sharing pdf whitepapers sites",
            f"{clean_niche} research document submission",
        ],
        "Podcast Submission": [
            f"{clean_niche} podcast directories submit show",
            f"{clean_niche} audio directories submission",
        ],
        "Forum Submission": [
            f"{clean_niche} discussion forums community list",
            f"{clean_niche} message boards online community",
        ],
        "Q&A Submission": [
            f"{clean_niche} question and answer community sites",
            f"{clean_niche} ask questions community",
        ],
        "Social Bookmarking": [
            f"{clean_niche} social bookmarking sites list submit link",
            f"{clean_niche} resource bookmarking sites",
        ],
        "Web 2.0 Submission": [
            f"{clean_niche} web 2.0 blogs sites list",
            f"{clean_niche} free web 2.0 creation sites",
        ],
        "Event Submission": [
            f"{clean_niche} event listing submission websites free",
            f"{clean_niche} submit events online",
        ],
        "Job Posting": [
            f"{clean_niche} job boards post jobs free",
            f"{clean_niche} careers directory listing",
        ],
        "Review Sites": [
            f"{clean_niche} review sites list customer ratings",
            f"{clean_niche} tools review platforms",
        ],
        "Coupon / Deal Submission": [
            f"{clean_niche} coupons discounts submission sites",
            f"{clean_niche} deals submit website",
        ],
    }
    specific = niche_queries.get(cat_name, [f"{clean_niche} {cat_name.lower()} sites list"])
    return specific + base[:1]


def discover_domains(cat_name: str, known: set[str], niche: str = "") -> list[str]:
    """Return candidate root domains found on listicle pages for this category and niche."""
    queries = _niche_discovery_queries(cat_name, niche)
    if not queries or cat_name in SKIP_DISCOVERY:
        return []

    pages: list[str] = []
    for q in queries:
        for hit in _ddgs_search(q):
            href = hit.get("href") or ""
            if href and root_domain(href) not in {"youtube.com", "quora.com", "reddit.com"}:
                pages.append(href)
    pages = list(dict.fromkeys(pages))[:6]

    counts: Counter[str] = Counter()
    for page in pages:
        page_dom = root_domain(page)
        try:
            html = httpx.get(page, headers=HEADERS_HTTP, timeout=12, follow_redirects=True).text
        except Exception:                                   # noqa: BLE001
            continue
        for link in set(re.findall(r'href=["\'](https?://[^"\'#\s>]+)', html)):
            dom = root_domain(link)
            if dom and dom != page_dom and dom not in BLOCKED_DOMAINS and dom not in known and "." in dom:
                counts[dom] += 1

    return [d for d, _ in counts.most_common(MAX_CANDIDATES)]


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #
def is_alive(url: str) -> bool:
    dom = root_domain(url)
    if dom in TOP_TRUSTED_DOMAINS:
        return True
    try:
        r = httpx.get(
            url,
            headers=HEADERS_HTTP,
            timeout=8,
            follow_redirects=True,
            verify=False,
        )
        if r.status_code == 404 or r.status_code == 410 or r.status_code >= 500:
            return False
        return True
    except Exception:                                       # noqa: BLE001
        return False


# --------------------------------------------------------------------------- #
# Per-category processing
# --------------------------------------------------------------------------- #
def _build_link(name, url, domain, da, da_source, listing_source, cost, action, how_to,
                probe=None, login_wall=False, is_seed=False) -> dict:
    return {
        "title": name,
        "name": name,
        "url": url,
        "domain": domain,
        "da_score": da,                                     # None = unknown
        "da": f"DA {da}" if da is not None else "DA unknown",
        "da_source": da_source,
        "cost": cost,
        "action": action,
        "how_to_perform": how_to,
        "snippet": how_to,
        "source": listing_source,
        "is_seed": is_seed,
        # presence-check inputs (filled from the seed) and outputs (filled by PresenceChecker)
        "probe": list(probe or []),
        "login_wall": bool(login_wall),
        "registered": "Not checked",
        "confidence": "",
        "evidence_url": "",
        "check_method": "",
        "link_type": "",
        "check_note": "",
        "checked_on": "",
    }


def process_category(cat_name: str, info: dict, min_da: int, max_items: int,
                     progress: Callable[[str], None] | None = None,
                     checker: PresenceChecker | None = None,
                     niche: str = "") -> dict:
    seeds = info["platforms"]
    # site_key keeps docs.google.com / sites.google.com etc. separate instead of collapsing to google.com
    seed_keys = {site_key(p["domain"]) for p in seeds}

    # 1. Check existing niche opportunities in SQLite
    cached_links = _load_niche_opportunities(niche, cat_name)
    existing_domains = {site_key(l["domain"]) for l in cached_links}

    if len(cached_links) >= max_items:
        # Existing list is already complete - reuse immediately
        links = [dict(l) for l in cached_links[:max_items]]
        dropped = 0
    else:
        # Need to find more web links to add to the existing list
        known_domains = seed_keys | existing_domains
        found = discover_domains(cat_name, known=known_domains, niche=niche)
        scores = get_da(list(seed_keys) + found)

        candidates: list[dict] = []
        seen_domains: set[str] = set(existing_domains)

        # 1. Seeds: real Moz / OPR data only; if no verified score exists, label as DA unknown
        for p in seeds:
            dom = site_key(p["domain"])
            if dom in seen_domains:
                continue
            seen_domains.add(dom)
            real = scores.get(dom)
            if real:
                da, src = real
            else:
                da, src = None, "Unknown"
            candidates.append(_build_link(
                p["name"], p["url"], dom, da, src, "Seed platform",
                p.get("cost", "100% Free"), p.get("action", "Register & Submit"),
                p.get("how_to_perform", GENERIC_HOW_TO),
                probe=p.get("probe"), login_wall=p.get("login_wall"),
                is_seed=True,
            ))

        # 2. Live discovered domains
        for dom in found:
            if dom in seen_domains:
                continue
            seen_domains.add(dom)
            da, src = scores.get(dom, (None, "Unknown"))
            candidates.append(_build_link(
                dom, f"https://{dom}/", dom, da, src, "Discovered - verify manually",
                "Check on site", "Register & Submit", GENERIC_HOW_TO,
                is_seed=False,
            ))

        # Niche relevance scoring: match against user's specific project industry keywords
        niche_tokens = set(re.findall(r"[a-z0-9]{3,}", (niche or "").lower()))
        niche_tokens = {t for t in niche_tokens if t not in {"general", "business", "services", "company", "and", "the", "for", "with", "site", "sites"}}

        def _niche_score(c: dict) -> int:
            if not niche_tokens:
                return 0
            txt = (c.get("name", "") + " " + c.get("domain", "") + " " + c.get("how_to_perform", "")).lower()
            return sum(1 for tok in niche_tokens if tok in txt)

        # Sort: verified high DA (>=80) top, followed by lower verified DA, followed by unknown DA at lowest.
        # Within each authority tier, websites directly matching the project's niche are prioritized first.
        def _sort_key(c: dict):
            has_real = c["da_score"] is not None
            da_val = c["da_score"] or 0
            is_seed = 1 if c.get("is_seed") else 0
            n_score = _niche_score(c)
            tier = 3 if (has_real and da_val >= 80) else (2 if has_real else 1)
            return (tier, n_score, da_val, is_seed)

        candidates.sort(key=_sort_key, reverse=True)

        needed = max_items - len(cached_links)
        new_live_links: list[dict] = []
        idx = 0
        dropped = 0
        while len(new_live_links) < needed and idx < len(candidates):
            batch = candidates[idx: idx + max(10, needed - len(new_live_links) + 10)]
            idx += len(batch)
            with ThreadPoolExecutor(max_workers=10) as ex:
                flags = list(ex.map(lambda c: is_alive(c["url"]), batch))
            new_live_links += [c for c, ok in zip(batch, flags) if ok]
            dropped += flags.count(False)

        links = (cached_links + new_live_links)[:max_items]

        # Save all verified opportunities for this niche + category into SQLite
        if links:
            _save_niche_opportunities(niche, cat_name, links)

    # Presence check: is the target already registered on these sites?
    presence_counts: dict = {}
    if checker is not None and links:
        if progress:
            progress(f"{cat_name}: checking if {checker.target} is already registered on {len(links)} sites...")
        try:
            presence_counts = checker.check_links(links)
        except Exception as e:                              # noqa: BLE001
            log.exception("Presence check failed for %s: %s", cat_name, e)
            for l in links:
                l.update(registered="Unverified", check_method="Check error", check_note=str(e)[:200])
            presence_counts = {"Unverified": len(links)}

    high_da_count = sum(1 for l in links if (l.get("da_score") or 0) >= 80)
    note = f"{high_da_count} sites with DA >= 80, plus {len(links) - high_da_count} additional opportunities."
    if dropped:
        note += f" {dropped} unreachable sites were dropped."

    if progress:
        extra = ""
        if presence_counts:
            extra = (f" | Registered {presence_counts.get('Registered', 0)}, "
                     f"Not Registered {presence_counts.get('Not Registered', 0)}, "
                     f"Unverified {presence_counts.get('Unverified', 0)}")
        progress(f"{cat_name}: {len(links)} sites ready{extra}")

    return {
        "category": cat_name,
        "icon": info["icon"],
        "description": info["description"],
        "task_type": info["task_type"],
        "links": links,
        "total_count": len(links),
        "requested_count": max_items,
        "short": len(links) < max_items,
        "presence": presence_counts,
        "note": note,
    }


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #
def find_opportunities(context: dict, per_category: int = MAX_PER_CATEGORY,
                       progress: Callable[[str], None] | None = None,
                       min_da: int = MIN_DA,
                       presence: dict | None = None) -> dict:
    """Return categorized submission websites (up to per_category each).

    presence (optional) switches the registered/not-registered check on:
      {"target": "tracevenue.com",            required
       "handles": ["tracevenue_official"],     extra profile handles to probe
       "team_done": {site_key: [urls]},        from presence_checker.load_team_sheet
       "referring": {site_key: [urls]},        from presence_checker.load_backlink_export
       "trust_team_reports": False,            count unverifiable team claims as Registered (Low)
       "force_recheck": False}                 ignore cached Registered results
    """
    project = context.get("project_name", "").strip()[:80]
    niche = context.get("niche", "General Business").strip()[:80]
    location = context.get("location", "Worldwide").strip()[:80]
    audience = context.get("target_audience", "General audience").strip()[:80]

    if not (MOZ_ID and MOZ_SECRET):
        msg = ("MOZ_ACCESS_ID / MOZ_SECRET_KEY not set: DA falls back to Open PageRank (if configured); "
               "sites without verified authority scores are shown as DA unknown.")
        log.warning(msg)
        if progress:
            progress(msg)

    # ---- presence checker (one shared instance for all categories) ----
    checker: PresenceChecker | None = None
    if presence and presence.get("target"):
        referring = dict(presence.get("referring") or {})
        if not referring and USE_MOZ_BACKLINKS:
            if progress:
                progress("Pulling referring domains from Moz Links API...")
            referring = fetch_moz_referring(presence["target"])
        checker = PresenceChecker(
            target=presence["target"], project_name=project,
            handles=presence.get("handles"), referring=referring,
            team_done=presence.get("team_done"),
            trust_team_reports=bool(presence.get("trust_team_reports")),
            force_recheck=bool(presence.get("force_recheck")),
            link_suffix=presence.get("link_suffix", ""),
            link_suffixes=presence.get("link_suffixes"),
            progress=progress,
        )
        if progress:
            layers = [f"team tracker ({len(checker.team_done)} sites)" if checker.team_done else None,
                      f"backlink data ({len(referring)} domains)" if referring else None,
                      f"profile probe (handles: {', '.join(checker.slugs)})",
                      "footprint search" if USE_FOOTPRINT else None,
                      "JS rendering" if USE_PLAYWRIGHT else None]
            progress(f"Presence check for {checker.target} using: " + ", ".join(l for l in layers if l))

    total_cats = len(SUBMISSION_PLATFORMS)
    if progress:
        progress(f"[0/{total_cats}] Searching {total_cats} categories (up to {per_category} sites each)...")

    tracker = {"done": 0, "total": total_cats, "lock": threading.Lock()}

    def _worker(name, info):
        if progress:
            with tracker["lock"]:
                cur = tracker["done"]
            progress(f"[{cur}/{tracker['total']}] Processing {name}: checking authority platforms & discovery for {niche}...")
        res = process_category(name, info, min_da, per_category, progress, checker, niche=niche)
        with tracker["lock"]:
            tracker["done"] += 1
            completed = tracker["done"]
        if progress:
            pcounts = res.get("presence", {})
            extra = ""
            if pcounts:
                extra = f" | Registered {pcounts.get('Registered', 0)}, Not Registered {pcounts.get('Not Registered', 0)}, Unverified {pcounts.get('Unverified', 0)}"
            progress(f"[{completed}/{tracker['total']}] Finished {name}: {res.get('total_count', 0)} sites ready{extra}")
        return res

    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = [
            ex.submit(_worker, name, info)
            for name, info in SUBMISSION_PLATFORMS.items()
        ]
        categories, failed = [], 0
        for (name, info), fut in zip(SUBMISSION_PLATFORMS.items(), futures):
            try:
                categories.append(fut.result())
            except Exception as e:                          # noqa: BLE001
                failed += 1
                log.exception("Category %s failed: %s", name, e)

    total = sum(c["total_count"] for c in categories)
    high = sum(1 for c in categories for l in c["links"] if (l.get("da_score") or 0) >= min_da)
    short = [c["category"] for c in categories if c.get("short")]
    all_links = [l for c in categories for l in c["links"]]
    pcount = Counter(l.get("registered") for l in all_links)

    notice = f"Found {total} websites across {len(categories)} categories for {niche} ({high} with DA >= {min_da})."
    if short:
        notice += f" {len(short)} categories have fewer than {per_category} sites."
    if checker is not None:
        notice += (f" Presence of {checker.target}: {pcount.get('Registered', 0)} Registered, "
                   f"{pcount.get('Not Registered', 0)} Not Registered, {pcount.get('Unverified', 0)} Unverified.")

    return {
        "project_name": project,
        "niche": niche,
        "location": location,
        "target_audience": audience,
        "min_da": min_da,
        "categories": categories,
        "total_links": total,
        "total_categories": len(categories),
        "failed_categories": failed,
        "presence_enabled": checker is not None,
        "target_domain": checker.target if checker else "",
        "presence_summary": {
            "registered": pcount.get("Registered", 0),
            "not_registered": pcount.get("Not Registered", 0),
            "unverified": pcount.get("Unverified", 0),
        } if checker else {},
        "notice": notice,
    }


# --------------------------------------------------------------------------- #
# Excel export (Status is always the LAST column)
# --------------------------------------------------------------------------- #
STATUS_OPTIONS = '"Pending,In Progress,Completed,Skipped"'
REGISTERED_OPTIONS = '"Registered,Not Registered,Unverified"'
FILL_GREEN, FILL_ORANGE, FILL_GREY = "C6EFCE", "FFD8A8", "D9D9D9"


def _columns(presence: bool) -> list[tuple[str, int, Callable]]:
    """(header, width, getter(n, cat, link)). Presence columns only when the check was run."""
    cols: list[tuple[str, int, Callable]] = [
        ("#", 5, lambda n, c, l: n),
        ("Category", 24, lambda n, c, l: c["category"]),
        ("Task Type", 26, lambda n, c, l: c["task_type"]),
        ("Website", 26, lambda n, c, l: l["name"]),
        ("URL", 40, lambda n, c, l: l["url"]),
        ("Link Suffix", 20, lambda n, c, l: l.get("link_suffix", "")),
    ]
    if presence:
        cols.append(("Registered", 16, lambda n, c, l: l.get("registered", "Unverified")))
    cols += [
        ("DA", 7, lambda n, c, l: l["da_score"] if l.get("da_score") is not None else "n/a"),
        ("DA Source", 24, lambda n, c, l: l.get("da_source", "")),
        ("Listing Source", 24, lambda n, c, l: l.get("source", "")),
        ("Cost", 16, lambda n, c, l: l["cost"]),
        ("Action", 32, lambda n, c, l: l["action"]),
        ("How To Perform", 70, lambda n, c, l: l["how_to_perform"]),
    ]
    if presence:
        cols += [
            ("Confidence", 11, lambda n, c, l: l.get("confidence", "")),
            ("Evidence URL", 40, lambda n, c, l: l.get("evidence_url", "")),
            ("Check Method", 30, lambda n, c, l: l.get("check_method", "")),
            ("Link Type", 11, lambda n, c, l: l.get("link_type", "")),
            ("Check Note", 55, lambda n, c, l: l.get("check_note", "")),
            ("Checked On", 12, lambda n, c, l: l.get("checked_on", "")),
        ]
    # Registered sites are pre-marked Completed; everything else is Pending work for the team
    cols.append(("Status", 14, lambda n, c, l: "Completed" if presence and l.get("registered") == "Registered" else "Pending"))
    return cols


def _style_header(ws) -> None:
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="1F4E78")
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


def _cf_fill(color: str) -> PatternFill:
    return PatternFill(start_color=color, end_color=color, fill_type="solid")


def build_excel(result: dict) -> bytes:
    """Build the downloadable .xlsx. The team filters the Registered column to see what is left to do,
    and marks work done via the Status dropdown (Registered rows start as Completed)."""
    presence = bool(result.get("presence_enabled"))
    cols = _columns(presence)
    headers = [c[0] for c in cols]
    idx = {h: i for i, h in enumerate(headers, 1)}

    wb = Workbook()
    ws = wb.active
    ws.title = "SEO Submission List"
    ws.append(headers)
    _style_header(ws)

    n = 0
    for cat in result["categories"]:
        for link in cat["links"]:
            n += 1
            ws.append([getter(n, cat, link) for _, _, getter in cols])
            row = n + 1
            for col_name in ("URL", "Evidence URL"):
                if col_name in idx:
                    cell = ws.cell(row=row, column=idx[col_name])
                    if isinstance(cell.value, str) and cell.value.startswith("http"):
                        cell.hyperlink = cell.value
                        cell.style = "Hyperlink"

    last_row = ws.max_row
    status_col = get_column_letter(len(headers))

    if last_row >= 2:
        # Registered column: colour + manual-override dropdown (team can correct after a manual check)
        if presence:
            rl = get_column_letter(idx["Registered"])
            rng = f"{rl}2:{rl}{last_row}"
            ws.conditional_formatting.add(rng, FormulaRule(formula=[f'${rl}2="Registered"'], fill=_cf_fill(FILL_GREEN)))
            ws.conditional_formatting.add(rng, FormulaRule(formula=[f'${rl}2="Not Registered"'], fill=_cf_fill(FILL_ORANGE)))
            ws.conditional_formatting.add(rng, FormulaRule(formula=[f'${rl}2="Unverified"'], fill=_cf_fill(FILL_GREY)))
            dv_reg = DataValidation(type="list", formula1=REGISTERED_OPTIONS, allow_blank=True)
            ws.add_data_validation(dv_reg)
            dv_reg.add(rng)

        dv = DataValidation(type="list", formula1=STATUS_OPTIONS, allow_blank=False)
        ws.add_data_validation(dv)
        dv.add(f"{status_col}2:{status_col}{last_row}")
        ws.conditional_formatting.add(
            f"A2:{status_col}{last_row}",
            FormulaRule(formula=[f'${status_col}2="Completed"'], fill=_cf_fill(FILL_GREEN)),
        )
        ws.auto_filter.ref = f"A1:{status_col}{last_row}"
        wrap_cols = [idx[h] for h in ("How To Perform", "Check Note") if h in idx]
        for row in ws.iter_rows(min_row=2):
            for ci in wrap_cols:
                row[ci - 1].alignment = Alignment(wrap_text=True, vertical="top")

    for i, (_, w, _) in enumerate(cols, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "A2"

    # ---- Summary sheet ----
    ss = wb.create_sheet("Summary")
    head = ["Category", "Task Type", "Sites Found", "Requested"]
    if presence:
        head += ["Registered", "Not Registered", "Unverified", "To Work On"]
    head += ["Min DA", "Note"]
    ss.append(head)
    _style_header(ss)
    tot = {"found": 0, "req": 0, "R": 0, "NR": 0, "U": 0}
    for cat in result["categories"]:
        p = cat.get("presence") or {}
        r, nr, u = p.get("Registered", 0), p.get("Not Registered", 0), p.get("Unverified", 0)
        row = [cat["category"], cat["task_type"], cat["total_count"], cat["requested_count"]]
        if presence:
            row += [r, nr, u, nr + u]
        row += [result.get("min_da", MIN_DA), cat["note"]]
        ss.append(row)
        tot["found"] += cat["total_count"]; tot["req"] += cat["requested_count"]
        tot["R"] += r; tot["NR"] += nr; tot["U"] += u
    total_row = ["TOTAL", "", tot["found"], tot["req"]]
    if presence:
        total_row += [tot["R"], tot["NR"], tot["U"], tot["NR"] + tot["U"]]
    total_row += ["", ""]
    ss.append(total_row)
    for c in ss[ss.max_row]:
        c.font = Font(bold=True)
    widths = [26, 28, 12, 12] + ([12, 15, 12, 12] if presence else []) + [8, 60]
    for i, w in enumerate(widths, 1):
        ss.column_dimensions[get_column_letter(i)].width = w

    # ---- Legend sheet (so the team knows how to read the tags) ----
    if presence:
        lg = wb.create_sheet("Legend")
        lg.append(["Term", "Meaning"])
        _style_header(lg)
        target = result.get("target_domain", "the target site")
        for term, meaning in [
            ("Registered", f"A link to {target} was found on the site. Evidence URL, check method and confidence show how it was proven."),
            ("Not Registered", "Every applicable check ran successfully and found nothing. Safe to work on, but confirm if Confidence is Low."),
            ("Unverified", "The platform blocks automated checks, the page needs JavaScript/login, or the checks were inconclusive. Verify manually."),
            ("Confidence: High", "Link anchor seen on a live page, or two independent layers agree (Registered); profile page loaded without the link (Not Registered)."),
            ("Confidence: Medium", "Domain found in page source / backlink data, or profile URL returned 404 (handle may differ)."),
            ("Confidence: Low", "Only weak evidence: absent from backlink data (it lags), search snippet, or team-reported without machine check."),
            ("Check Method", "Layers that produced the result: Team tracker, Backlink data, Profile probe, Footprint search."),
            ("Link Type", "dofollow / nofollow as read from the anchor's rel attribute."),
            ("Manual override", "The Registered column has a dropdown: after checking by hand, set the correct value and update Status."),
        ]:
            lg.append([term, meaning])
        lg.column_dimensions["A"].width = 22
        lg.column_dimensions["B"].width = 120
        for row in lg.iter_rows(min_row=2):
            row[1].alignment = Alignment(wrap_text=True, vertical="top")

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    res = find_opportunities(
        {"project_name": "Tracevenue", "niche": "Event venues", "location": "India"},
        progress=print,
        presence={"target": "tracevenue.com"},
    )
    print(res["notice"])
    with open("seo_submission_list.xlsx", "wb") as f:
        f.write(build_excel(res))
    print("Saved seo_submission_list.xlsx")