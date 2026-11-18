"""Site-level technical checks: robots.txt, sitemap, HTTPS, broken links, PageSpeed."""
import re
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

import requests

from config import USER_AGENT, PAGESPEED_API_KEY

HEADERS = {"User-Agent": USER_AGENT}


def _origin(url: str) -> str:
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}"


def check_robots(url: str) -> dict:
    robots_url = _origin(url) + "/robots.txt"
    out = {"url": robots_url, "found": False, "sitemaps": [], "blocks_all": False}
    try:
        r = requests.get(robots_url, headers=HEADERS, timeout=10)
        if r.status_code == 200 and "html" not in r.headers.get("Content-Type", ""):
            out["found"] = True
            out["sitemaps"] = re.findall(r"(?im)^sitemap:\s*(\S+)", r.text)
            out["blocks_all"] = bool(re.search(r"(?is)user-agent:\s*\*\s*disallow:\s*/\s*$", r.text, re.M))
    except requests.RequestException as e:
        out["error"] = str(e)
    return out


def check_sitemap(url: str, robots: dict) -> dict:
    candidates = robots.get("sitemaps") or [_origin(url) + "/sitemap.xml"]
    out = {"found": False, "url": None, "url_count": 0}
    for sm in candidates:
        try:
            r = requests.get(sm, headers=HEADERS, timeout=15)
            if r.status_code == 200 and "<loc>" in r.text:
                out.update(found=True, url=sm, url_count=len(re.findall(r"<loc>", r.text)))
                break
        except requests.RequestException:
            continue
    return out


def check_https(url: str) -> dict:
    out = {"is_https": url.startswith("https://"), "http_redirects_to_https": None}
    try:
        http_url = "http://" + urlparse(url).netloc
        r = requests.get(http_url, headers=HEADERS, timeout=10, allow_redirects=True)
        out["http_redirects_to_https"] = r.url.startswith("https://")
    except requests.RequestException:
        pass
    return out


def _check_link(link: str):
    try:
        r = requests.head(link, headers=HEADERS, timeout=10, allow_redirects=True)
        if r.status_code in (403, 405, 501):
            r = requests.get(link, headers=HEADERS, timeout=10, stream=True)
        return link, r.status_code
    except requests.RequestException:
        return link, 0


def check_broken_links(pages: list, limit: int = 80) -> list:
    """Returns [{'link', 'status', 'found_on'}] for links that fail (>=400 or unreachable)."""
    source = {}
    for p in pages:
        for l in p.internal_links + p.external_links:
            source.setdefault(l, p.url)
    links = list(source)[:limit]
    with ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(_check_link, links))
    return [{"link": l, "status": s, "found_on": source[l]} for l, s in results if s == 0 or s >= 400]


def pagespeed(url: str, strategy: str = "mobile") -> dict:
    """Google PageSpeed Insights (Lighthouse) - Core Web Vitals + performance score."""
    api = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    params = {"url": url, "strategy": strategy, "category": "performance"}
    if PAGESPEED_API_KEY:
        params["key"] = PAGESPEED_API_KEY
    try:
        r = requests.get(api, params=params, timeout=90)
        r.raise_for_status()
        lh = r.json()["lighthouseResult"]
        a = lh["audits"]
        return {
            "strategy": strategy,
            "performance_score": round(lh["categories"]["performance"]["score"] * 100),
            "LCP": a["largest-contentful-paint"]["displayValue"],
            "CLS": a["cumulative-layout-shift"]["displayValue"],
            "TBT": a["total-blocking-time"]["displayValue"],
            "FCP": a["first-contentful-paint"]["displayValue"],
        }
    except Exception as e:  # network/quota errors should not stop the agent
        return {"error": f"PageSpeed unavailable: {e}"}
