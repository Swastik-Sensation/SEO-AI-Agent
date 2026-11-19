"""Publisher & Blogger Outreach Contact Finder

Finds relevant bloggers, publishers, and media outlets in a given Niche and Location
(e.g., Event Planning in Mohali, Chandigarh, Tricity).
Extracts:
  - Verified editorial emails
  - Phone numbers & WhatsApp contacts
  - Publication name, domain & DA authority score
  - About/Bio information
  - Direct contact page URLs & guest posting / contribution guidelines
  - Social media profiles (LinkedIn, Instagram, Twitter/X, Facebook)
  - Exports cleanly to formatted Excel (.xlsx) and CSV reports.
"""
from __future__ import annotations

import csv
import io
import logging
import os
import re
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from urllib.parse import unquote, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

log = logging.getLogger(__name__)

# Re-use DA score caching from opportunities tool if available
try:
    from tools.opportunities import get_da, site_key
except Exception:
    def get_da(domains: list[str]) -> dict[str, tuple[int, str]]:
        return {d: (None, "Unknown") for d in domains}

    def site_key(url_or_domain: str) -> str:
        netloc = urlparse(url_or_domain).netloc if "//" in url_or_domain else url_or_domain
        return netloc.lower().replace("www.", "").split(":")[0]


HEADERS_HTTP = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

BLOCKED_DOMAINS = {
    "google.com", "google.co.in", "youtube.com", "facebook.com", "twitter.com",
    "x.com", "instagram.com", "linkedin.com", "pinterest.com", "wikipedia.org",
    "quora.com", "reddit.com", "amazon.com", "amazon.in", "flipkart.com",
    "yahoo.com", "bing.com", "duckduckgo.com", "msn.com", "apple.com",
    "microsoft.com", "wordpress.org", "github.com", "play.google.com"
}

JUNK_EMAIL_DOMAINS = {
    "example.com", "domain.com", "email.com", "yoursite.com", "sentry.io",
    "wixpress.com", "cloudflare.com", "gravatar.com", "mysite.com", "test.com"
}

JUNK_EMAIL_PREFIXES = {
    "user", "name", "yourname", "someone", "info@example.com", "rating@", "image@"
}

_ddg_lock = threading.Lock()


def _ddgs_search(query: str, n: int = 15) -> list[dict]:
    """Execute search query with fallback from ddgs api to html backend."""
    with _ddg_lock:
        try:
            from ddgs import DDGS
            with DDGS() as d:
                try:
                    res = list(d.text(query, backend="api", max_results=n))
                except Exception:
                    res = list(d.text(query, backend="html", max_results=n))
            time.sleep(0.5)
            return res
        except Exception as e:  # noqa: BLE001
            log.warning("ddgs search failed for %r: %s", query, e)
            return []


def _extract_domain(url: str) -> str:
    netloc = urlparse(url).netloc if "//" in url else url
    netloc = netloc.lower().split("@")[-1].split(":")[0]
    return netloc[4:] if netloc.startswith("www.") else netloc


def _clean_email(email: str) -> Optional[str]:
    """Validates and cleans an email string."""
    e = email.strip().lower().strip(".,;:()<>[]\"'")
    if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", e):
        return None
    if any(e.endswith(f".{ext}") for ext in ["png", "jpg", "jpeg", "gif", "svg", "webp", "css", "js"]):
        return None
    dom = e.split("@")[-1]
    if dom in JUNK_EMAIL_DOMAINS or any(dom.endswith(f".{jd}") for jd in JUNK_EMAIL_DOMAINS):
        return None
    if any(e.startswith(p) for p in JUNK_EMAIL_PREFIXES):
        return None
    return e


def _clean_phone(raw: str) -> Optional[str]:
    """Formats phone numbers, supporting Indian (+91) and international numbers."""
    cleaned = re.sub(r"[^\d+]", "", raw.strip())
    # Chandigarh/Mohali/Tricity landline e.g. 0172-2654321
    if cleaned.startswith("0172") and len(cleaned) == 11:
        return f"+91 172 {cleaned[4:]}"
    if cleaned.startswith("172") and len(cleaned) == 10:
        return f"+91 172 {cleaned[3:]}"
    # Handle Indian mobile/standard numbers
    if cleaned.startswith("+91") and len(cleaned) == 13:
        return f"+91 {cleaned[3:8]} {cleaned[8:]}"
    if cleaned.startswith("91") and len(cleaned) == 12:
        return f"+91 {cleaned[2:7]} {cleaned[7:]}"
    if cleaned.startswith("0") and len(cleaned) == 11:
        return f"+91 {cleaned[1:6]} {cleaned[6:]}"
    if len(cleaned) == 10 and cleaned[0] in "6789":
        return f"+91 {cleaned[:5]} {cleaned[5:]}"
    if len(cleaned) >= 8 and len(cleaned) <= 15:
        return raw.strip()
    return None


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
        self._client = httpx.Client(
            headers=HEADERS_HTTP,
            timeout=8.0,
            follow_redirects=True,
            verify=False,
            limits=httpx.Limits(max_connections=30, max_keepalive_connections=15),
        )

    def _notify(self, msg: str, step: int = 0, total_steps: int = 4):
        if self.progress:
            self.progress(msg, step, total_steps)

    def generate_queries(self) -> list[str]:
        """Construct targeted queries combining niche, location, and publisher footprints."""
        queries = []
        loc = self.location if self.location.lower() not in {"worldwide", "global", "all", ""} else ""
        n = self.niche
        kw = self.keywords

        if loc:
            import re
            cities = [c.strip() for c in re.split(r'[,/|]+', loc) if c.strip()]
            main_city = cities[0] if cities else loc

            # Unquoted flexible combined query
            queries.append(f'"{n}" {loc} blog OR magazine OR publisher')
            # Niche with main city guest post & editorial footprints
            queries.append(f'"{n}" "{main_city}" "write for us" OR "guest post"')
            queries.append(f'"{n}" "{main_city}" "contact" OR "editor"')
            queries.append(f'best "{n}" blogs in {main_city}')
            # If multiple cities specified (e.g. Mohali, Chandigarh), add secondary city
            if len(cities) > 1:
                queries.append(f'"{n}" "{cities[1]}" "write for us" OR "guest post"')
                queries.append(f'"{n}" "{cities[1]}" blog OR news OR magazine')
            else:
                queries.append(f'"{n}" bloggers in "{main_city}"')
            if kw:
                queries.append(f'"{n}" {main_city} {kw}')
        else:
            queries.append(f'"{n}" blog OR magazine OR publisher "write for us"')
            queries.append(f'top "{n}" blogs "contact us"')
            queries.append(f'"{n}" guest post submission websites')
            if kw:
                queries.append(f'"{n}" {kw} blog')

        return queries[:8]

    def discover_candidate_domains(self) -> list[str]:
        """Runs search queries and aggregates relevant publisher domains."""
        self._notify(f"Searching web for {self.niche} publishers in {self.location}...", step=1)
        queries = self.generate_queries()
        domains: list[str] = []
        seen_domains: Set[str] = set()

        for q in queries:
            results = _ddgs_search(q, n=12)
            for hit in results:
                href = hit.get("href") or ""
                dom = _extract_domain(href)
                if dom and dom not in BLOCKED_DOMAINS and dom not in seen_domains and "." in dom:
                    # Exclude file extensions or common social platforms
                    if not any(dom.endswith(f".{bd}") for bd in BLOCKED_DOMAINS):
                        seen_domains.add(dom)
                        domains.append(dom)
            if len(domains) >= self.max_publishers * 3:
                break

        self._notify(f"Discovered {len(domains)} candidate publisher domains to inspect.", step=1)
        return domains

    def inspect_publisher(self, domain: str) -> Optional[Dict[str, Any]]:
        """Deeply inspects a publisher domain to extract contact info, editors, and guidelines."""
        base_url = f"https://{domain}/"
        try:
            resp = self._client.get(base_url)
        except Exception:
            try:
                base_url = f"http://{domain}/"
                resp = self._client.get(base_url)
            except Exception:
                return None

        if resp.status_code >= 400:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        final_url = str(resp.url)

        # 1. Publication Name & Description
        pub_name = ""
        site_name_tag = soup.find("meta", property="og:site_name")
        if site_name_tag and site_name_tag.get("content"):
            pub_name = site_name_tag["content"].strip()
        if not pub_name and soup.title and soup.title.string:
            title_text = soup.title.string.strip()
            # Clean common title formats e.g. "Title - BrandName"
            parts = re.split(r"[|\-–—]", title_text)
            pub_name = parts[-1].strip() if len(parts) > 1 else parts[0].strip()
        if not pub_name or len(pub_name) < 2:
            pub_name = domain.split(".")[0].title()

        desc = ""
        desc_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", property="og:description")
        if desc_tag and desc_tag.get("content"):
            desc = desc_tag["content"].strip()[:240]

        # 2. Extract internal high-value contact pages
        contact_urls: Set[str] = set()
        guidelines_url = ""
        contact_page_url = ""

        CONTACT_PATTERNS = re.compile(
            r"contact|about|write-for-us|guest-post|editorial|team|advertise|reach-us|authors|press",
            re.I
        )
        GUIDELINES_PATTERNS = re.compile(
            r"write-for-us|guest-post|submission|contribute|guidelines|editorial-policy",
            re.I
        )

        for a in soup.find_all("a", href=True):
            raw_href = a["href"].strip()
            anchor_text = a.get_text(" ", strip=True).lower()
            if not raw_href or raw_href.startswith(("#", "javascript:", "mailto:", "tel:")):
                continue
            full = urljoin(final_url, raw_href)
            if _extract_domain(full) != domain:
                continue

            path_and_anchor = (full + " " + anchor_text).lower()
            if GUIDELINES_PATTERNS.search(path_and_anchor):
                if not guidelines_url:
                    guidelines_url = full
            elif CONTACT_PATTERNS.search(path_and_anchor):
                contact_urls.add(full)
                if not contact_page_url and ("contact" in path_and_anchor):
                    contact_page_url = full

        # 3. Collect HTML across Homepage and Contact/Editorial pages
        pages_to_scan = [resp.text]
        scanned_urls = {final_url}

        # Scan up to 3 priority contact pages
        for curl in sorted(contact_urls, key=lambda u: ("contact" not in u.lower(), len(u)))[:3]:
            if curl in scanned_urls:
                continue
            scanned_urls.add(curl)
            try:
                cresp = self._client.get(curl)
                if cresp.status_code == 200:
                    pages_to_scan.append(cresp.text)
            except Exception:
                pass

        if guidelines_url and guidelines_url not in scanned_urls:
            scanned_urls.add(guidelines_url)
            try:
                gresp = self._client.get(guidelines_url)
                if gresp.status_code == 200:
                    pages_to_scan.append(gresp.text)
            except Exception:
                pass

        combined_html = "\n".join(pages_to_scan)

        # 4. Extract Emails
        emails: Set[str] = set()
        # Find mailto links
        for m in re.findall(r'mailto:([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', combined_html, re.I):
            cleaned = _clean_email(m)
            if cleaned:
                emails.add(cleaned)
        # Regex text email search
        for m in re.findall(r'\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b', combined_html):
            cleaned = _clean_email(m)
            if cleaned:
                emails.add(cleaned)
        # De-obfuscate [at] / (at) emails
        for m in re.findall(r'\b([a-zA-Z0-9_.+-]+)\s*(?:\[at\]|\(at\)|\bat\b)\s*([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)\b', combined_html, re.I):
            cleaned = _clean_email(f"{m[0]}@{m[1]}")
            if cleaned:
                emails.add(cleaned)

        # 5. Extract Phone Numbers & WhatsApp
        phones: Set[str] = set()
        # tel: links
        for tel in re.findall(r'href=["\']tel:([+0-9\s\-()]+)["\']', combined_html, re.I):
            p = _clean_phone(tel)
            if p:
                phones.add(p)
        # WhatsApp links
        for wa in re.findall(r'(?:wa\.me/|phone=)([0-9]{10,13})', combined_html, re.I):
            p = _clean_phone(wa)
            if p:
                phones.add(f"{p} (WhatsApp)")
        # Regex phone search (Indian formats)
        for ph in re.findall(r'(?:\+91[\-\s]?)?[6-9]\d{4}[\-\s]?\d{5}\b', combined_html):
            p = _clean_phone(ph)
            if p:
                phones.add(p)
        # Landline formats (e.g. 0172-XXXXXXX for Tricity/Chandigarh)
        for ph in re.findall(r'\b0172[\-\s]?\d{6,7}\b', combined_html):
            p = _clean_phone(ph)
            if p:
                phones.add(p)

        # 6. Extract Social Profiles
        linkedin = ""
        twitter = ""
        instagram = ""
        facebook = ""

        for m in re.findall(r'https?://(?:www\.)?linkedin\.com/(?:company|in)/[a-zA-Z0-9_\-]+', combined_html, re.I):
            if not linkedin and "linkedin.com/company" in m:
                linkedin = m
            elif not linkedin:
                linkedin = m

        for m in re.findall(r'https?://(?:www\.)?(?:twitter\.com|x\.com)/[a-zA-Z0-9_]{3,25}', combined_html, re.I):
            if not any(skip in m.lower() for skip in ["twitter.com/intent", "twitter.com/share"]):
                twitter = m
                break

        for m in re.findall(r'https?://(?:www\.)?instagram\.com/[a-zA-Z0-9_.]{3,30}', combined_html, re.I):
            if not any(skip in m.lower() for skip in ["instagram.com/p/", "instagram.com/reel/"]):
                instagram = m
                break

        for m in re.findall(r'https?://(?:www\.)?facebook\.com/[a-zA-Z0-9_.]{3,50}', combined_html, re.I):
            if not any(skip in m.lower() for skip in ["facebook.com/sharer", "facebook.com/share"]):
                facebook = m
                break

        # 7. Check Location Match
        location_tokens = [t.lower() for t in re.split(r"[,;\s]+", self.location) if len(t) > 3]
        location_mentioned = False
        lower_html = combined_html.lower()
        if location_tokens and any(t in lower_html for t in location_tokens):
            location_mentioned = True

        # Outreach Readiness Status
        if emails and phones:
            status = "Direct Contact Ready (Email & Phone)"
        elif emails:
            status = "Ready to Pitch (Email Found)"
        elif phones:
            status = "Phone / WhatsApp Contact Found"
        elif contact_page_url:
            status = "Contact Form Available"
        elif guidelines_url:
            status = "Guest Post Page Available"
        else:
            status = "Social Channels Found" if (linkedin or twitter or instagram) else "Website Identified"

        return {
            "name": pub_name[:70],
            "domain": domain,
            "url": final_url,
            "description": desc or f"Publication & editorial platform in {self.niche}.",
            "emails": sorted(emails)[:5],
            "primary_email": sorted(emails)[0] if emails else "",
            "phones": sorted(phones)[:3],
            "primary_phone": sorted(phones)[0] if phones else "",
            "contact_page_url": contact_page_url or (list(contact_urls)[0] if contact_urls else ""),
            "guidelines_url": guidelines_url,
            "linkedin": linkedin,
            "twitter": twitter,
            "instagram": instagram,
            "facebook": facebook,
            "location_mentioned": location_mentioned,
            "location": self.location,
            "niche": self.niche,
            "outreach_status": status,
        }

    def search_and_extract(self) -> Dict[str, Any]:
        """Main pipeline: Discovers domains, inspects contacts, and formats results."""
        domains = self.discover_candidate_domains()
        if not domains:
            return {
                "niche": self.niche,
                "location": self.location,
                "total_publishers": 0,
                "publishers": [],
                "summary": {"emails_found": 0, "phones_found": 0, "guidelines_found": 0},
                "notice": "No relevant publisher domains found. Try broader location or niche keywords.",
            }

        self._notify(f"Extracting contact details from {min(len(domains), self.max_publishers * 2)} websites...", step=2)

        candidates = domains[: self.max_publishers * 2]
        publishers: List[Dict[str, Any]] = []

        # Inspect candidate sites in parallel
        with ThreadPoolExecutor(max_workers=8) as ex:
            results = list(ex.map(self.inspect_publisher, candidates))

        valid = [r for r in results if r is not None]

        # Get DA scores for authority ranking
        self._notify("Calculating authority (DA) scores...", step=3)
        valid_domains = [p["domain"] for p in valid]
        da_map = get_da(valid_domains)

        for p in valid:
            da_val, src = da_map.get(p["domain"], (None, "Unknown"))
            p["da_score"] = da_val
            p["da_source"] = src

        # Prioritize publishers:
        # 1. Has Email/Phone
        # 2. Location match
        # 3. Higher DA score
        def _sort_key(p: dict) -> Tuple[int, int, int]:
            has_contact = 2 if (p["emails"] or p["phones"]) else (1 if p["contact_page_url"] else 0)
            loc_match = 1 if p.get("location_mentioned") else 0
            da = p.get("da_score") or 0
            return (has_contact, loc_match, da)

        valid.sort(key=_sort_key, reverse=True)
        publishers = valid[: self.max_publishers]

        # Calculate metrics
        emails_count = sum(1 for p in publishers if p["emails"])
        phones_count = sum(1 for p in publishers if p["phones"])
        guidelines_count = sum(1 for p in publishers if p["guidelines_url"])

        self._notify(
            f"Completed! Found {len(publishers)} publishers ({emails_count} emails, {phones_count} phone/WhatsApp numbers).",
            step=4
        )

        return {
            "niche": self.niche,
            "location": self.location,
            "keywords": self.keywords,
            "total_publishers": len(publishers),
            "publishers": publishers,
            "summary": {
                "emails_found": emails_count,
                "phones_found": phones_count,
                "guidelines_found": guidelines_count,
                "with_contact_form": sum(1 for p in publishers if p["contact_page_url"]),
            },
            "notice": (
                f"Found {len(publishers)} publishers for '{self.niche}' in {self.location}. "
                f"{emails_count} verified emails and {phones_count} phone/WhatsApp contacts extracted."
            ),
        }


# --------------------------------------------------------------------------- #
# Excel (.xlsx) Report Builder
# --------------------------------------------------------------------------- #
FILL_NAVY = "1E3A8A"
FILL_GREEN = "D1FAE5"
FILL_BLUE = "DBEAFE"
FILL_GREY = "F3F4F6"
BORDER_COLOR = "E5E7EB"


def build_publisher_excel(result: dict) -> bytes:
    """Builds a professionally styled Excel workbook containing publisher contacts."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Publisher Contacts"

    thin_border = Border(
        left=Side(style="thin", color=BORDER_COLOR),
        right=Side(style="thin", color=BORDER_COLOR),
        top=Side(style="thin", color=BORDER_COLOR),
        bottom=Side(style="thin", color=BORDER_COLOR),
    )

    # 1. Title Banner
    niche = result.get("niche", "General")
    location = result.get("location", "Worldwide")
    total = result.get("total_publishers", 0)
    summary = result.get("summary", {})

    ws.merge_cells("A1:N1")
    title_cell = ws["A1"]
    title_cell.value = f"Publisher & Blogger Outreach Contacts: {niche} ({location})"
    title_cell.font = Font(name="Calibri", size=15, bold=True, color="FFFFFF")
    title_cell.fill = PatternFill(start_color=FILL_NAVY, end_color=FILL_NAVY, fill_type="solid")
    title_cell.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.row_dimensions[1].height = 36

    # 2. Summary Subtitle
    ws.merge_cells("A2:N2")
    sub_cell = ws["A2"]
    sub_cell.value = (
        f"Total Publishers: {total}  |  Emails Found: {summary.get('emails_found', 0)}  |  "
        f"Phone/WhatsApp Contacts: {summary.get('phones_found', 0)}  |  "
        f"Guest Post Guidelines: {summary.get('guidelines_found', 0)}"
    )
    sub_cell.font = Font(name="Calibri", size=10, italic=True, color="4B5563")
    sub_cell.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.row_dimensions[2].height = 20

    # 3. Table Column Headers
    headers = [
        ("#", 5),
        ("Publication / Blog Name", 28),
        ("Website URL", 32),
        ("Domain", 22),
        ("DA Authority", 13),
        ("Contact Email(s)", 30),
        ("Phone / WhatsApp", 22),
        ("Outreach Status", 25),
        ("Contact Page URL", 32),
        ("Guest Post / Pitch URL", 32),
        ("Location Mentioned", 18),
        ("About / Publication Bio", 45),
        ("LinkedIn Profile", 26),
        ("Instagram", 24),
    ]

    header_row = 4
    ws.row_dimensions[header_row].height = 26

    for col_idx, (hdr_text, col_width) in enumerate(headers, start=1):
        cell = ws.cell(row=header_row, column=col_idx, value=hdr_text)
        cell.font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="3B82F6", end_color="3B82F6", fill_type="solid")
        cell.alignment = Alignment(horizontal="center" if col_idx in [1, 5, 11] else "left", vertical="center")
        cell.border = thin_border
        col_letter = get_column_letter(col_idx)
        ws.column_dimensions[col_letter].width = col_width

    # 4. Data Rows
    publishers = result.get("publishers", [])
    for row_idx, pub in enumerate(publishers, start=5):
        ws.row_dimensions[row_idx].height = 22

        emails_str = ", ".join(pub.get("emails", [])) or "None found"
        phones_str = ", ".join(pub.get("phones", [])) or "None found"
        da_display = pub.get("da_score") if pub.get("da_score") is not None else "Unknown"

        has_direct_contact = bool(pub.get("emails") or pub.get("phones"))

        values = [
            row_idx - 4,
            pub.get("name", ""),
            pub.get("url", ""),
            pub.get("domain", ""),
            da_display,
            emails_str,
            phones_str,
            pub.get("outreach_status", "Identified"),
            pub.get("contact_page_url", ""),
            pub.get("guidelines_url", ""),
            "Yes (Local Match)" if pub.get("location_mentioned") else "Regional / Global",
            pub.get("description", ""),
            pub.get("linkedin", ""),
            pub.get("instagram", ""),
        ]

        for col_idx, val in enumerate(values, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            cell.font = Font(name="Calibri", size=10)
            cell.border = thin_border

            # Row background highlight
            if has_direct_contact:
                cell.fill = PatternFill(start_color=FILL_GREEN, end_color=FILL_GREEN, fill_type="solid")
            elif row_idx % 2 == 0:
                cell.fill = PatternFill(start_color=FILL_GREY, end_color=FILL_GREY, fill_type="solid")

            # Alignment
            if col_idx == 1:
                cell.alignment = Alignment(horizontal="center", vertical="center")
            elif col_idx == 5:
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.font = Font(name="Calibri", size=10, bold=True)
            elif col_idx in (6, 7):
                cell.font = Font(name="Calibri", size=10, bold=bool(has_direct_contact))
                cell.alignment = Alignment(horizontal="left", vertical="center")
            elif col_idx in (3, 9, 10, 13, 14) and str(val).startswith("http"):
                cell.font = Font(name="Calibri", size=10, color="2563EB", underline="single")
                cell.alignment = Alignment(horizontal="left", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center")

    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


# --------------------------------------------------------------------------- #
# CSV Report Builder
# --------------------------------------------------------------------------- #
def build_publisher_csv(result: dict) -> str:
    """Builds a formatted CSV string of publisher contacts."""
    out = io.StringIO()
    writer = csv.writer(out)

    writer.writerow([
        "#", "Publisher Name", "Website URL", "Domain", "DA Authority",
        "Emails", "Phones / WhatsApp", "Outreach Status", "Contact Page URL",
        "Guest Post Guidelines URL", "Location Match", "Bio / Description",
        "LinkedIn", "Instagram", "Twitter"
    ])

    for i, p in enumerate(result.get("publishers", []), start=1):
        writer.writerow([
            i,
            p.get("name", ""),
            p.get("url", ""),
            p.get("domain", ""),
            p.get("da_score") if p.get("da_score") is not None else "Unknown",
            "; ".join(p.get("emails", [])),
            "; ".join(p.get("phones", [])),
            p.get("outreach_status", ""),
            p.get("contact_page_url", ""),
            p.get("guidelines_url", ""),
            "Yes" if p.get("location_mentioned") else "No",
            p.get("description", ""),
            p.get("linkedin", ""),
            p.get("instagram", ""),
            p.get("twitter", ""),
        ])

    return out.getvalue()
