"""
Business Profile Auditor (tools/profile_checker.py)  --  v3

Audits public business and citation profiles (Medium, Substack, Dev.to, GitHub,
About.me, Crunchbase, Behance, Dribbble, Gravatar, Yelp, Directories, etc.).

Primary Audit Focus:
  1. Website Backlink Verification:
     - Checks if the business website URL is present and clickable in the bio or profile.
     - Detects plain-text domain mentions that lack clickable links.
     - Checks link security (HTTPS vs HTTP) and destination liveness.
  2. Bio / About Content Correctness:
     - Extracts the bio/about text across any platform.
     - Evaluates whether the content accurately describes the business name, niche, and services.
     - Checks niche alignment against the business's official website.
     - Checks for clear call-to-action (CTA) and platform character limits.
     - Identifies core industry keywords present vs missing.
  3. AI Bio Analysis & Optimized Rewrites:
     - Evaluates bio correctness with AI.
     - Generates 3 ready-to-use bio variations (Short, Value-Focused, SEO Keyword-Rich)
       with the website link seamlessly included.
"""
from __future__ import annotations

import json
import logging
import os
import re
import socket
import time
import xml.etree.ElementTree as ET
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from urllib.parse import parse_qs, unquote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

import config

log = logging.getLogger(__name__)

__all__ = ["audit_profile"]

# --------------------------------------------------------------------------------------
# Constants & Headers
# --------------------------------------------------------------------------------------

BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

GENUINE_HEADERS = {
    "User-Agent": BROWSER_UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
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

STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
    "could", "did", "do", "does", "doing", "down", "during", "each", "few", "for", "from", "further",
    "had", "has", "have", "having", "he", "her", "here", "him", "his", "how", "i", "if", "in", "into",
    "is", "it", "its", "just", "me", "more", "most", "my", "no", "nor", "not", "of", "off", "on", "once",
    "only", "or", "other", "our", "out", "over", "own", "same", "she", "should", "so", "some", "such",
    "than", "that", "the", "their", "theirs", "them", "then", "there", "these", "they", "this", "those",
    "through", "to", "too", "under", "until", "up", "very", "was", "we", "were", "what", "when", "where",
    "which", "while", "who", "whom", "why", "with", "would", "you", "your", "yours", "com", "www", "https", "http",
}

CTA_KEYWORDS = [
    "visit", "learn more", "contact", "subscribe", "get started", "book", "try", "follow", "sign up",
    "discover", "join", "read", "check out", "download", "demo", "reach out", "explore", "official website",
    "find out more", "see more", "click here", "browse", "shop", "hire us",
]

PLATFORM_LIMITS: Dict[str, int] = {
    "Medium": 160,
    "Dev.to": 200,
    "Substack": 250,
    "Twitter / X": 160,
    "GitHub": 160,
    "LinkedIn": 260,
    "About.me": 300,
    "Behance": 250,
    "Dribbble": 200,
    "Crunchbase": 300,
    "ProductHunt": 200,
    "Web Profile / Directory": 250,
}

REDIRECT_HOSTS = {"l.facebook.com", "lm.facebook.com", "l.instagram.com", "away.vk.com", "t.co"}
REDIRECT_PARAMS = ("url", "u", "q", "to", "target", "redirect", "redirect_url", "redirecturl", "dest")

BLOCK_CODES = {401, 403, 405, 406, 429, 451, 999}
_CHALLENGE = ("cf-chl-", "challenge-running", "turnstile", "captcha", "security check", "ddos-guard", "just a moment...")

try:
    import primp
    _PRIMP_CLIENT = primp.Client(impersonate="chrome", impersonate_os="windows", follow_redirects=True, timeout=12)
except Exception:
    _PRIMP_CLIENT = None

_REQUESTS_SESSION = requests.Session()
_REQUESTS_SESSION.headers.update(GENUINE_HEADERS)

# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------

def _clean_text(text: str) -> str:
    return " ".join((text or "").split()).strip()


def _normalize_url(url: Optional[str]) -> str:
    url = (url or "").strip()
    if url and "://" not in url:
        url = "https://" + url
    return url


def _strip_www(host: str) -> str:
    host = (host or "").strip().lower()
    return host[4:] if host.startswith("www.") else host


def _extract_domain(url: str) -> str:
    try:
        host = urlparse(url if "://" in url else f"https://{url}").netloc.lower().split("@")[-1].split(":")[0]
        return _strip_www(host)
    except Exception:
        return ""


def _domain_matches(domain: str, target: str) -> bool:
    if not domain or not target:
        return False
    domain = _strip_www(domain)
    target = _strip_www(target)
    return domain == target or domain.endswith("." + target)


def _looks_blocked(html: str) -> bool:
    if not html:
        return True
    return len(html) < 35000 and any(m in html[:8000].lower() for m in _CHALLENGE)


def _detect_platform(profile_url: str) -> str:
    domain = _extract_domain(profile_url)
    table = [
        ("medium.com", "Medium"), ("substack.com", "Substack"), ("dev.to", "Dev.to"),
        ("hashnode.", "Hashnode"), ("quora.com", "Quora"), ("github.com", "GitHub"),
        ("linkedin.com", "LinkedIn"), ("producthunt.com", "ProductHunt"),
        ("crunchbase.com", "Crunchbase"), ("twitter.com", "Twitter / X"), ("x.com", "Twitter / X"),
        ("about.me", "About.me"), ("behance.net", "Behance"), ("dribbble.com", "Dribbble"),
        ("gravatar.com", "Gravatar"), ("linktr.ee", "Linktree"), ("bento.me", "Bento"),
        ("yelp.com", "Yelp"), ("yellowpages.com", "YellowPages"),
    ]
    for needle, name in table:
        if needle in domain:
            return name
    return "Web Profile / Directory"


def _unwrap_redirect(url: str) -> str:
    try:
        p = urlparse(url)
        host = _strip_www(p.netloc.lower())
        if host.endswith("google.com") and p.path == "/url":
            qs = {k.lower(): v for k, v in parse_qs(p.query).items()}
            for key in REDIRECT_PARAMS:
                vals = qs.get(key)
                if vals and vals[0].startswith("http"):
                    return vals[0]
        if host in REDIRECT_HOSTS:
            qs = {k.lower(): v for k, v in parse_qs(p.query).items()}
            for key in REDIRECT_PARAMS:
                vals = qs.get(key)
                if vals and vals[0].startswith("http"):
                    return vals[0]
    except Exception:
        pass
    return url


# --------------------------------------------------------------------------------------
# Robust Fetching (Primp -> Requests -> Playwright Fallback)
# --------------------------------------------------------------------------------------

def _render_with_playwright(url: str) -> str:
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
            )
            try:
                context = browser.new_context(
                    user_agent=BROWSER_UA,
                    viewport={"width": 1366, "height": 768},
                    locale="en-US"
                )
                page = context.new_page()
                page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                page.goto(url, wait_until="domcontentloaded", timeout=18000)
                time.sleep(1.0)
                return page.content()
            finally:
                browser.close()
    except Exception as exc:
        log.warning("Playwright render failed for %s: %s", url, exc)
        return ""


def _fetch_page(url: str, timeout: int = 12) -> Tuple[str, Optional[int], str]:
    """Returns (html, status_code, error)."""
    html = ""
    status = 0
    err = ""

    # 1. Try primp with genuine browser impersonation
    if _PRIMP_CLIENT is not None:
        try:
            r = _PRIMP_CLIENT.get(url)
            status = r.status_code
            html = r.text
        except Exception as exc:
            err = str(exc)

    # 2. Try requests if primp failed or got blocked
    if not html or status in BLOCK_CODES or _looks_blocked(html):
        try:
            r = _REQUESTS_SESSION.get(url, timeout=timeout, allow_redirects=True)
            status = r.status_code
            html = r.text
            err = "" if status == 200 else f"HTTP {status}"
        except Exception as exc:
            err = f"{type(exc).__name__}: {exc}"

    # 3. If still blocked or JS shell, use Playwright
    if (status in BLOCK_CODES or _looks_blocked(html) or not html) and url.startswith("http"):
        rendered = _render_with_playwright(url)
        if rendered and not _looks_blocked(rendered):
            return rendered, 200, ""

    return html, status, err


def _check_link_liveness(url: str) -> Optional[int]:
    try:
        r = _REQUESTS_SESSION.head(url, timeout=6, allow_redirects=True)
        if r.status_code in (403, 405) or r.status_code >= 400:
            r = _REQUESTS_SESSION.get(url, timeout=6, allow_redirects=True, stream=True)
            r.close()
        return r.status_code
    except Exception:
        return None


# --------------------------------------------------------------------------------------
# Business Context Extraction (Money Site)
# --------------------------------------------------------------------------------------

def _extract_project_context(project_url: str, user_niche: Optional[str] = None) -> dict:
    domain = _extract_domain(project_url)
    context = {
        "url": project_url,
        "domain": domain,
        "name": domain.split(".")[0].title() if domain else "Business",
        "niche": user_niche or "General Business",
        "keywords": [],
        "description": "",
    }
    if not project_url:
        return context

    html, status, err = _fetch_page(project_url, timeout=10)
    if not html:
        context["fetch_error"] = err
        return context

    try:
        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        desc_tag = (soup.find("meta", attrs={"name": "description"})
                    or soup.find("meta", attrs={"property": "og:description"}))
        meta_desc = desc_tag["content"].strip() if desc_tag and desc_tag.get("content") else ""
        h1 = soup.find("h1")
        h1_text = _clean_text(h1.get_text()) if h1 else ""
        body_text = soup.body.get_text(separator=" ", strip=True) if soup.body else ""

        words = re.findall(r"\b[a-zA-Z]{3,}\b", (title + " " + h1_text + " " + meta_desc + " " + body_text[:4000]).lower())
        freq = Counter(w for w in words if w not in STOP_WORDS)
        top_kws = [w for w, _ in freq.most_common(12)]

        brand_guess = re.split(r"\s[-|–—]\s|\|", title)[0].strip()
        if brand_guess and len(brand_guess) < 40:
            context["name"] = brand_guess
        context["description"] = meta_desc or h1_text or title
        context["keywords"] = top_kws
        if not user_niche and top_kws:
            context["niche"] = " / ".join(top_kws[:3]).title()
    except Exception as exc:
        context["fetch_error"] = str(exc)

    return context


# --------------------------------------------------------------------------------------
# Profile Metadata & Bio Extraction
# --------------------------------------------------------------------------------------

def _extract_profile_metadata(profile_url: str, html: str) -> dict:
    platform = _detect_platform(profile_url)
    soup = BeautifulSoup(html, "html.parser")

    # Name extraction
    name = ""
    for sel in ['h1[class*="name"]', 'h1[class*="title"]', 'h1', 'h2[class*="name"]', '.profile-name', '[data-testid*="name"]']:
        el = soup.select_one(sel)
        if el and _clean_text(el.get_text()):
            name = _clean_text(el.get_text())
            break
    if not name:
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            name = og_title["content"].strip()
    if not name and soup.title and soup.title.string:
        name = soup.title.string.strip()
    name = re.sub(r"\s*[–\-|]\s*(Medium|Substack|Dev\.to|Hashnode|Quora|GitHub|LinkedIn|Crunchbase).*$", "", name, flags=re.I).strip()

    # Bio / About text extraction
    bio = ""
    bio_selectors = [
        'p[class*="bio"]', 'p[class*="about"]', 'p[class*="desc"]',
        'div[class*="bio"]', 'div[class*="about"]', 'div[class*="desc"]',
        '.profile-bio', '.user-bio', '[data-testid="author-bio"]',
        '[data-testid*="bio"]', '.about-me', '.biography', 'section[id*="about"] p',
        '.profile-description', '.entity-description',
    ]
    for sel in bio_selectors:
        for c in soup.select(sel):
            txt = _clean_text(c.get_text())
            if len(txt) > len(bio) and len(txt) < 1500 and not any(tag in txt.lower() for tag in ["cookie", "javascript"]):
                bio = txt
                break
        if bio:
            break

    # Schema.org description fallback
    if not bio:
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                if isinstance(data, dict):
                    d = data.get("description") or data.get("about")
                    if isinstance(d, str) and len(d) > len(bio):
                        bio = _clean_text(d)
            except Exception:
                pass

    # Meta description fallback
    if not bio:
        meta_bio = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
        if meta_bio and meta_bio.get("content"):
            raw_meta = meta_bio["content"].strip()
            # Clean generic site slogans
            if not any(raw_meta.lower().startswith(s) for s in ["read writing from", "follow", "see posts from"]):
                bio = _clean_text(raw_meta)
            else:
                cleaned = re.sub(r"^(?:Read writing from|Follow|See posts from)\s+[^·|]+[·|]\s*", "", raw_meta, flags=re.I).strip()
                if cleaned:
                    bio = _clean_text(cleaned)

    # Avatar
    avatar_url = ""
    og_image = soup.find("meta", property="og:image")
    if og_image and og_image.get("content"):
        avatar_url = og_image["content"].strip()
    if not avatar_url:
        img = soup.select_one('img[class*="avatar"], img[class*="profile"], img[alt*="avatar"], img[alt*="profile"]')
        if img and img.get("src"):
            avatar_url = urljoin(profile_url, img["src"])

    # Extract all outbound links on the profile
    profile_domain = _extract_domain(profile_url)
    all_links = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        full_url = _unwrap_redirect(urljoin(profile_url, href))
        domain = _extract_domain(full_url)
        rel = [r.lower() for r in (a.get("rel") or [])]
        anchor = _clean_text(a.get_text())
        is_in_bio = False
        # Check if anchor is inside a bio-like container
        p_parent = a.find_parent(lambda tag: any(k in str(tag.get("class", "")).lower() for k in ["bio", "about", "desc"]))
        if p_parent:
            is_in_bio = True

        all_links.append({
            "url": full_url,
            "domain": domain,
            "anchor": anchor or "[No Anchor Text / Icon]",
            "nofollow": any(r in rel for r in ["nofollow", "ugc", "sponsored"]),
            "is_in_bio": is_in_bio,
        })

    return {
        "platform": platform,
        "name": name or "Profile Owner",
        "bio": bio,
        "avatar_url": avatar_url,
        "external_links": all_links,
        "profile_domain": profile_domain,
    }


# --------------------------------------------------------------------------------------
# Website Backlink Analysis
# --------------------------------------------------------------------------------------

def _audit_website_backlink(target_url: str, target_domain: str, bio_text: str, external_links: List[dict]) -> dict:
    target_domain = _strip_www(target_domain)
    matching_links = [l for l in external_links if _domain_matches(l.get("domain", ""), target_domain)]

    # Check if target domain is mentioned in the bio text
    plain_text_in_bio = False
    if target_domain:
        # Regex to find target domain not enclosed in href
        domain_pattern = re.compile(rf"(?<![\w@/.-]){re.escape(target_domain)}(?![\w.-])", re.IGNORECASE)
        if domain_pattern.search(bio_text or ""):
            plain_text_in_bio = True

    bio_links = [l for l in matching_links if l.get("is_in_bio")]

    if matching_links:
        primary = matching_links[0]
        placement = "Both Bio & Profile Field" if bio_links and len(matching_links) > len(bio_links) else ("In Bio Text" if bio_links else "Profile Website Button")
        is_https = primary["url"].lower().startswith("https://")
        liveness = _check_link_liveness(primary["url"])

        return {
            "found": True,
            "status": "VERIFIED_CLICKABLE",
            "placement": placement,
            "target_url": target_url,
            "matching_url": primary["url"],
            "anchor_text": primary["anchor"],
            "is_https": is_https,
            "is_dofollow": not primary.get("nofollow", False),
            "status_code": liveness,
            "matching_count": len(matching_links),
            "plain_text_in_bio": plain_text_in_bio,
            "summary": f"Direct clickable link pointing to {target_domain} verified on profile ({placement}).",
        }

    if plain_text_in_bio:
        return {
            "found": False,
            "status": "PLAIN_TEXT_IN_BIO",
            "placement": "In Bio (Plain Text)",
            "target_url": target_url,
            "matching_url": "",
            "anchor_text": "",
            "is_https": False,
            "is_dofollow": False,
            "status_code": None,
            "matching_count": 0,
            "plain_text_in_bio": True,
            "summary": f"Target domain '{target_domain}' is written in bio text, but it is NOT an active clickable link.",
        }

    return {
        "found": False,
        "status": "MISSING",
        "placement": "None",
        "target_url": target_url,
        "matching_url": "",
        "anchor_text": "",
        "is_https": False,
        "is_dofollow": False,
        "status_code": None,
        "matching_count": 0,
        "plain_text_in_bio": False,
        "summary": f"No backlink or mention of {target_domain} was found on this profile.",
    }


# --------------------------------------------------------------------------------------
# Bio Content Correctness & Quality Check
# --------------------------------------------------------------------------------------

def _audit_bio_content(bio_text: str, project_context: dict, platform: str) -> dict:
    char_count = len(bio_text or "")
    limit = PLATFORM_LIMITS.get(platform, 250)
    has_bio = bool(bio_text and char_count >= 10)

    # 1. Business Name Check
    biz_name = project_context.get("name", "").strip()
    biz_tokens = set(re.findall(r"[a-z0-9]{3,}", biz_name.lower()))
    domain_token = (project_context.get("domain", "") or "").split(".")[0].lower()
    if domain_token and len(domain_token) >= 3:
        biz_tokens.add(domain_token)

    bio_lower = (bio_text or "").lower()
    name_matched = any(tok in bio_lower for tok in biz_tokens) if biz_tokens else False

    # 2. Niche & Keyword Coverage
    target_kws = project_context.get("keywords", [])
    niche = project_context.get("niche", "").lower()
    niche_words = [w for w in re.findall(r"[a-z0-9]{3,}", niche) if w not in STOP_WORDS]
    all_target_terms = list(dict.fromkeys(niche_words + target_kws))

    matched_kws = [kw for kw in all_target_terms if kw in bio_lower]
    missing_kws = [kw for kw in all_target_terms if kw not in bio_lower][:8]

    # Calculate Alignment Score (0 - 100)
    if not has_bio:
        alignment_score = 0
    else:
        # Base 50 points if bio has reasonable length & vocabulary
        score = 40.0
        if name_matched:
            score += 25.0
        if matched_kws:
            score += min(35.0, len(matched_kws) * 12.0)
        alignment_score = int(min(100.0, score))

    if alignment_score >= 80:
        alignment_verdict = "High Alignment"
    elif alignment_score >= 50:
        alignment_verdict = "Moderate Alignment"
    else:
        alignment_verdict = "Low / Unaligned"

    # 3. Call to Action (CTA)
    cta_phrase = None
    for cta in CTA_KEYWORDS:
        if cta in bio_lower:
            cta_phrase = cta.title()
            break
    has_cta = bool(cta_phrase)

    # 4. Correctness Verdict
    if not has_bio:
        correctness_verdict = "Missing Bio"
        correctness_details = "The profile has no bio or about description. Visitors have no context about your business."
    elif alignment_score >= 75 and name_matched:
        correctness_verdict = "Correct & Niche-Aligned"
        correctness_details = f"Bio accurately represents {biz_name} and clearly covers your {project_context.get('niche', 'industry')} offerings."
    elif name_matched or alignment_score >= 50:
        correctness_verdict = "Partially Correct (Needs Tweaks)"
        correctness_details = "Bio mentions relevant business concepts, but is missing core keywords, a strong value proposition, or a clear call to action."
    else:
        correctness_verdict = "Inaccurate / Missing Info"
        correctness_details = f"Bio does not mention {biz_name} or relevant industry terms. It may be generic, outdated, or misaligned with your official site."

    return {
        "has_bio": has_bio,
        "bio_text": bio_text,
        "char_count": char_count,
        "platform_limit": limit,
        "is_within_limit": char_count <= limit,
        "business_name_match": name_matched,
        "business_name_expected": biz_name,
        "niche_alignment_score": alignment_score,
        "niche_alignment_verdict": alignment_verdict,
        "keywords_present": matched_kws[:6],
        "keywords_missing": missing_kws[:6],
        "has_cta": has_cta,
        "cta_phrase": cta_phrase,
        "correctness_verdict": correctness_verdict,
        "correctness_details": correctness_details,
    }


# --------------------------------------------------------------------------------------
# Issues Evaluation & Profile Health Score
# --------------------------------------------------------------------------------------

def _evaluate_issues(backlink: dict, bio: dict, profile_meta: dict) -> Tuple[List[dict], int, str]:
    issues: List[dict] = []
    score = 100

    # 1. Backlink Issues
    if backlink["status"] == "MISSING":
        issues.append({
            "severity": "critical",
            "code": "MISSING_WEBSITE_BACKLINK",
            "category": "Website Backlink in Bio",
            "issue": f"Profile does not link to your official website ({backlink.get('target_url')}).",
            "impact": "Zero referral traffic and complete loss of profile authority / citation signal.",
            "recommendation": f"Add {backlink.get('target_url')} directly to the profile bio or website link field.",
        })
        score -= 35
    elif backlink["status"] == "PLAIN_TEXT_IN_BIO":
        issues.append({
            "severity": "high",
            "code": "PLAIN_TEXT_LINK_NOT_CLICKABLE",
            "category": "Website Backlink in Bio",
            "issue": "Your website domain is written in the bio text, but it is not a clickable hyperlink.",
            "impact": "Visitors cannot tap or click through to your site, and search engines do not register a formal backlink.",
            "recommendation": "Format the URL as a clickable link in the bio editor or add it to the platform's official Website field.",
        })
        score -= 15
    elif backlink["status"] == "VERIFIED_CLICKABLE":
        if not backlink.get("is_https"):
            issues.append({
                "severity": "medium",
                "code": "INSECURE_HTTP_BACKLINK",
                "category": "Security & Protocol",
                "issue": f"Backlink uses insecure 'http://' instead of 'https://' ({backlink.get('matching_url')}).",
                "impact": "Browser security warnings and potential loss of user trust.",
                "recommendation": "Update the URL in your profile settings to start with https://",
            })
            score -= 8

    # 2. Bio Content Issues
    if not bio["has_bio"]:
        issues.append({
            "severity": "high",
            "code": "MISSING_BIO",
            "category": "Bio Content Quality",
            "issue": "Profile has no bio or about description.",
            "impact": "Leaves visitors with zero context about what your company does and harms search visibility.",
            "recommendation": "Add a professional bio highlighting your value proposition and core services.",
        })
        score -= 25
    else:
        if not bio["business_name_match"]:
            issues.append({
                "severity": "medium",
                "code": "BUSINESS_NAME_MISSING_IN_BIO",
                "category": "Brand Consistency",
                "issue": f"Bio does not mention your brand name ({bio.get('business_name_expected')}).",
                "impact": "Weaker brand recognition and entity association in search engines.",
                "recommendation": f"Introduce your brand name clearly in the opening sentence: '{bio.get('business_name_expected')} is...'",
            })
            score -= 10

        if bio["niche_alignment_score"] < 50:
            issues.append({
                "severity": "high",
                "code": "BIO_NICHE_MISMATCH",
                "category": "Niche Relevance",
                "issue": "Bio content is weakly aligned with your business niche and services.",
                "impact": "Confuses target visitors and fails to rank for your core industry keywords.",
                "recommendation": "Rewrite the bio to directly reflect your primary products, solutions, and target audience.",
            })
            score -= 15

        if not bio["has_cta"]:
            issues.append({
                "severity": "low",
                "code": "MISSING_CALL_TO_ACTION",
                "category": "Conversion & Growth",
                "issue": "Bio lacks a clear call-to-action (CTA).",
                "impact": "Fewer visitors take the next step to visit your website or contact your team.",
                "recommendation": "Add a crisp CTA like 'Explore our tools at...', 'Learn more at...', or 'Contact us today.'",
            })
            score -= 6

        if not bio["is_within_limit"]:
            issues.append({
                "severity": "low",
                "code": "BIO_EXCEEDS_PLATFORM_LIMIT",
                "category": "Formatting & Display",
                "issue": f"Bio length ({bio['char_count']} chars) exceeds the {profile_meta.get('platform')} limit of {bio['platform_limit']} chars.",
                "impact": "The tail end of the bio (often the link or CTA) may be truncated on public screens.",
                "recommendation": f"Trim bio to under {bio['platform_limit']} characters.",
            })
            score -= 5

    final_score = max(5, min(100, score))
    if final_score >= 85:
        badge = "Excellent"
    elif final_score >= 70:
        badge = "Good"
    elif final_score >= 50:
        badge = "Needs Improvement"
    else:
        badge = "Critical Attention Needed"

    return issues, final_score, badge


# --------------------------------------------------------------------------------------
# AI Bio Analysis & Ready-to-Use Rewrites
# --------------------------------------------------------------------------------------

def _generate_ai_bio_suggestions(profile_meta: dict, project_context: dict, bio_info: dict, backlink_info: dict) -> dict:
    brand = project_context.get("name", "Your Business")
    niche = project_context.get("niche", "Industry")
    url = project_context.get("url", "https://yourwebsite.com")
    domain = project_context.get("domain", "yourwebsite.com")
    platform = profile_meta.get("platform", "Web Profile")
    limit = PLATFORM_LIMITS.get(platform, 160)
    current_bio = bio_info.get("bio_text", "")

    # Fallback smart templates
    short_bio = f"{brand} | Modern {niche} solutions. Visit {domain} to learn more."
    if len(short_bio) > limit:
        short_bio = f"{brand}: {niche}. Learn more at {domain}"

    value_bio = f"At {brand}, we deliver innovative {niche} designed for modern teams. Discover how we can help your business grow at {url}"
    keyword_bio = f"{brand} is a leading provider of {niche}. Explore our latest tools, guides, and resources at {url}"

    assessment = (
        f"Profile bio audited for {brand} ({platform}). "
        + ("Website link is properly linked." if backlink_info.get("found") else "Website link is missing and should be added.")
    )

    if config.llm_available():
        try:
            from agent import _llm
            llm = _llm()
            prompt = (
                "You are an expert Social & Off-Page SEO Profile Specialist.\n"
                f"Business Name: {brand}\n"
                f"Niche/Industry: {niche}\n"
                f"Target Website: {url}\n"
                f"Platform: {platform} (Maximum character limit: {limit})\n"
                f"Current Bio: {current_bio or '(Empty / None)'}\n"
                f"Target Keywords: {', '.join(project_context.get('keywords', [])[:5])}\n\n"
                "Task:\n"
                "1. Analyze whether the current bio is correct, accurate, and aligned with the business.\n"
                "2. Provide 3 optimized, ready-to-use bio rewrites that include the website URL/domain and a strong CTA:\n"
                f"   - 'short_bio': Punchy and concise, strictly under {limit} characters.\n"
                "   - 'value_bio': Value-proposition focused (140-240 characters).\n"
                "   - 'keyword_bio': High-intent SEO keyword rich (140-240 characters).\n\n"
                'Return JSON strictly in this format:\n'
                '{\n'
                '  "assessment": "Brief 2-sentence evaluation of bio correctness and what needs fixing.",\n'
                '  "short_bio": "...",\n'
                '  "value_bio": "...",\n'
                '  "keyword_bio": "..."\n'
                '}'
            )
            raw = llm.invoke(prompt).content
            cleaned_json = re.sub(r"^```(?:json)?\s*", "", raw.strip())
            cleaned_json = re.sub(r"\s*```$", "", cleaned_json.strip())
            parsed = json.loads(cleaned_json)
            if isinstance(parsed, dict):
                if parsed.get("assessment"):
                    assessment = str(parsed["assessment"])
                if parsed.get("short_bio"):
                    short_bio = str(parsed["short_bio"])[:limit]
                if parsed.get("value_bio"):
                    value_bio = str(parsed["value_bio"])
                if parsed.get("keyword_bio"):
                    keyword_bio = str(parsed["keyword_bio"])
        except Exception as exc:
            log.warning("AI bio generation fallback: %s", exc)

    return {
        "assessment": assessment,
        "short_bio": short_bio,
        "short_bio_length": len(short_bio),
        "value_bio": value_bio,
        "value_bio_length": len(value_bio),
        "keyword_bio": keyword_bio,
        "keyword_bio_length": len(keyword_bio),
        "bio_rewrite": short_bio,
        "bio_rewrite_length": len(short_bio),
    }


# --------------------------------------------------------------------------------------
# Optional Post Discovery (Non-Penalizing)
# --------------------------------------------------------------------------------------

def _discover_optional_posts(profile_url: str, html: str, max_posts: int = 5) -> List[dict]:
    """Extracts posts if present, but zero posts does NOT penalize a business profile."""
    posts = []
    if not html:
        return posts
    try:
        soup = BeautifulSoup(html, "html.parser")
        seen_urls = set()
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            title = _clean_text(a.get_text())
            if len(title) > 18 and any(k in href for k in ["/p/", "/post/", "/story/", "/article/", "/blog/"]):
                full_url = urljoin(profile_url, href)
                if full_url not in seen_urls and full_url != profile_url:
                    seen_urls.add(full_url)
                    posts.append({
                        "title": title,
                        "url": full_url,
                        "published_at": "",
                        "verified": True,
                        "has_target_backlink": False,
                    })
            if len(posts) >= max_posts:
                break
    except Exception:
        pass
    return posts


# --------------------------------------------------------------------------------------
# Main Public Pipeline
# --------------------------------------------------------------------------------------

def audit_profile(
    project_url: str,
    profile_url: str,
    business_name: Optional[str] = None,
    niche: Optional[str] = None,
    max_posts: int = 5,
    progress_callback: Optional[Callable[[str, int], None]] = None,
) -> dict:
    """Main audit pipeline for Business Profile Checking.

    Focuses directly on:
      1. Checking if the website link is in the bio / profile and is clickable.
      2. Checking if the content written in the bio is correct and aligned with the business.
    """
    def log(msg: str, step: int):
        if progress_callback:
            progress_callback(msg, step)

    project_url = _normalize_url(project_url)
    profile_url = _normalize_url(profile_url)

    # Step 1: Business context
    log("Extracting business context and official website signals...", 1)
    project_ctx = _extract_project_context(project_url, niche)
    if business_name:
        project_ctx["name"] = business_name
    target_domain = project_ctx["domain"]

    # Step 2: Fetch public profile page
    log(f"Fetching public profile page at {profile_url}...", 2)
    profile_html, status_code, err = _fetch_page(profile_url)

    # Step 3: Extract profile bio & metadata
    log("Auditing profile bio, about section, and brand identifiers...", 3)
    profile_meta = _extract_profile_metadata(profile_url, profile_html) if profile_html else {
        "platform": _detect_platform(profile_url), "name": business_name or "Profile Owner",
        "bio": "", "avatar_url": "", "external_links": [], "profile_domain": _extract_domain(profile_url)
    }

    # Step 4: Website backlink verification
    log(f"Verifying website backlink for {target_domain} in bio & profile...", 4)
    backlink_info = _audit_website_backlink(
        target_url=project_url,
        target_domain=target_domain,
        bio_text=profile_meta["bio"],
        external_links=profile_meta["external_links"]
    )
    profile_meta["website_link_found"] = backlink_info["found"]
    profile_meta["matching_website_links"] = [backlink_info["matching_url"]] if backlink_info["matching_url"] else []

    # Step 5: Bio content correctness & quality audit
    log("Analyzing bio content correctness, niche relevance & brand alignment...", 5)
    bio_info = _audit_bio_content(
        bio_text=profile_meta["bio"],
        project_context=project_ctx,
        platform=profile_meta["platform"]
    )

    # Optional post discovery (strictly non-penalizing)
    discovered_posts = _discover_optional_posts(profile_url, profile_html, max_posts)

    # Step 6: Issues evaluation & score calculation
    log("Evaluating profile issues and computing Health Score...", 6)
    issues, score, badge = _evaluate_issues(backlink_info, bio_info, profile_meta)

    # Step 7: AI Bio recommendations & rewrites
    log("Generating AI bio correctness assessment & copy-paste rewrites...", 7)
    ai_suggestions = _generate_ai_bio_suggestions(profile_meta, project_ctx, bio_info, backlink_info)

    issues_by_severity = Counter(i["severity"] for i in issues)

    result = {
        "profile_url": profile_url,
        "project_url": project_url,
        "platform": profile_meta["platform"],
        "score": score,
        "badge": badge,
        "profile_meta": profile_meta,
        "project_context": project_ctx,
        "backlink_analysis": backlink_info,
        "bio_analysis": bio_info,
        "issues": issues,
        "issues_by_severity": {
            "critical": issues_by_severity.get("critical", 0),
            "high": issues_by_severity.get("high", 0),
            "medium": issues_by_severity.get("medium", 0),
            "low": issues_by_severity.get("low", 0),
        },
        "ai_suggestions": ai_suggestions,
        "posts": discovered_posts,
        "posts_count": len(discovered_posts),
        "coverage": {
            "source": "web_profile_inspection",
            "posts_discovered": len(discovered_posts),
            "posts_verified": len(discovered_posts),
            "notes": ["Audit centered on profile bio & website backlink presence."]
        }
    }

    return result
