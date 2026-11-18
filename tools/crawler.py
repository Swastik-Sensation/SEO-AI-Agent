"""Crawler: fetches pages on the same domain and extracts SEO-relevant data."""
import json
import time
from collections import deque
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse, urldefrag

import requests
from bs4 import BeautifulSoup

from config import USER_AGENT, CRAWL_DELAY

HEADERS = {"User-Agent": USER_AGENT}
SKIP_EXT = (".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".pdf", ".zip",
            ".css", ".js", ".ico", ".mp4", ".mp3", ".xml", ".json")


@dataclass
class Page:
    url: str
    status: int = 0
    final_url: str = ""
    response_time: float = 0.0
    title: str = ""
    meta_description: str = ""
    h1: list = field(default_factory=list)
    h2_count: int = 0
    canonical: str = ""
    robots_meta: str = ""
    viewport: bool = False
    lang: str = ""
    images_total: int = 0
    images_missing_alt: int = 0
    og_tags: dict = field(default_factory=dict)
    schema_types: list = field(default_factory=list)
    word_count: int = 0
    text_sample: str = ""
    internal_links: list = field(default_factory=list)
    external_links: list = field(default_factory=list)
    error: str = ""


def _clean(url: str) -> str:
    return urldefrag(url)[0]


def _same_domain(url: str, base: str) -> bool:
    strip = lambda h: h.lower().removeprefix("www.")
    return strip(urlparse(url).netloc) == strip(urlparse(base).netloc)


def _schema_types(soup) -> list:
    types = []
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        items = data if isinstance(data, list) else data.get("@graph", [data])
        for item in items:
            if isinstance(item, dict) and "@type" in item:
                t = item["@type"]
                types.extend(t if isinstance(t, list) else [t])
    return types


def parse_page(url: str, resp: requests.Response, elapsed: float) -> Page:
    page = Page(url=url, status=resp.status_code, final_url=resp.url, response_time=round(elapsed, 2))
    if "text/html" not in resp.headers.get("Content-Type", ""):
        return page
    soup = BeautifulSoup(resp.text, "html.parser")

    page.title = (soup.title.string or "").strip() if soup.title and soup.title.string else ""
    desc = soup.find("meta", attrs={"name": "description"})
    page.meta_description = (desc.get("content") or "").strip() if desc else ""
    page.h1 = [h.get_text(" ", strip=True) for h in soup.find_all("h1")]
    page.h2_count = len(soup.find_all("h2"))
    canon = soup.find("link", rel="canonical")
    page.canonical = canon.get("href", "") if canon else ""
    robots = soup.find("meta", attrs={"name": "robots"})
    page.robots_meta = (robots.get("content") or "").lower() if robots else ""
    page.viewport = soup.find("meta", attrs={"name": "viewport"}) is not None
    page.lang = (soup.html.get("lang", "") if soup.html else "")
    imgs = soup.find_all("img")
    page.images_total = len(imgs)
    page.images_missing_alt = sum(1 for i in imgs if not (i.get("alt") or "").strip())
    page.og_tags = {m.get("property"): m.get("content") for m in soup.find_all("meta")
                    if (m.get("property") or "").startswith("og:")}
    page.schema_types = _schema_types(soup)

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text(" ", strip=True)
    page.word_count = len(text.split())
    page.text_sample = text[:4000]

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith(("mailto:", "tel:", "javascript:", "#")):
            continue
        full = _clean(urljoin(resp.url, href))
        (page.internal_links if _same_domain(full, url) else page.external_links).append(full)
    return page


def crawl(start_url: str, max_pages: int = 25) -> list:
    """Breadth-first crawl limited to the start URL's domain."""
    queue, seen, pages = deque([_clean(start_url)]), set(), []
    while queue and len(pages) < max_pages:
        url = queue.popleft()
        if url in seen or url.lower().endswith(SKIP_EXT):
            continue
        seen.add(url)
        try:
            t0 = time.time()
            resp = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
            page = parse_page(url, resp, time.time() - t0)
        except requests.RequestException as e:
            page = Page(url=url, error=str(e))
        pages.append(page)
        for link in page.internal_links:
            if link not in seen:
                queue.append(link)
        time.sleep(CRAWL_DELAY)
    return pages
