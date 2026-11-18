"""Rule-based on-page audit. Deterministic and fast: no LLM involved."""
from collections import defaultdict

WEIGHTS = {"critical": 40, "high": 15, "medium": 7, "low": 2}


def _issue(sev, page, code, msg):
    return {"severity": sev, "url": page, "code": code, "issue": msg}


def audit_pages(pages: list) -> list:
    issues = []
    titles, descs = defaultdict(list), defaultdict(list)

    for p in pages:
        u = p.url
        if p.error:
            issues.append(_issue("critical", u, "UNREACHABLE", f"Could not fetch page: {p.error}"))
            continue
        if p.status >= 400:
            issues.append(_issue("critical", u, "HTTP_ERROR", f"Page returns HTTP {p.status}"))
            continue
        if not p.title and not p.h1 and not p.word_count:
            continue  # non-HTML or empty response

        if "noindex" in p.robots_meta:
            issues.append(_issue("high", u, "NOINDEX", "Page has a noindex directive (will not appear in search)"))

        # Title
        if not p.title:
            issues.append(_issue("high", u, "TITLE_MISSING", "Missing <title> tag"))
        else:
            titles[p.title.lower()].append(u)
            if len(p.title) > 60:
                issues.append(_issue("medium", u, "TITLE_LONG", f"Title is {len(p.title)} chars (>60, may be truncated)"))
            elif len(p.title) < 30:
                issues.append(_issue("medium", u, "TITLE_SHORT", f"Title is only {len(p.title)} chars (<30)"))

        # Meta description
        if not p.meta_description:
            issues.append(_issue("high", u, "META_MISSING", "Missing meta description"))
        else:
            descs[p.meta_description.lower()].append(u)
            n = len(p.meta_description)
            if n > 160:
                issues.append(_issue("medium", u, "META_LONG", f"Meta description is {n} chars (>160)"))
            elif n < 70:
                issues.append(_issue("medium", u, "META_SHORT", f"Meta description is only {n} chars (<70)"))

        # Headings
        if not p.h1:
            issues.append(_issue("high", u, "H1_MISSING", "No H1 heading"))
        elif len(p.h1) > 1:
            issues.append(_issue("medium", u, "H1_MULTIPLE", f"{len(p.h1)} H1 tags found (use one)"))

        # Content / media
        if p.word_count < 300:
            issues.append(_issue("medium", u, "THIN_CONTENT", f"Only {p.word_count} words (<300)"))
        if p.images_missing_alt:
            issues.append(_issue("medium", u, "IMG_ALT", f"{p.images_missing_alt}/{p.images_total} images missing alt text"))

        # Technical on-page
        if not p.viewport:
            issues.append(_issue("high", u, "NO_VIEWPORT", "Missing viewport meta tag (mobile-friendliness)"))
        if not p.canonical:
            issues.append(_issue("low", u, "NO_CANONICAL", "No canonical URL set"))
        if not p.schema_types:
            issues.append(_issue("low", u, "NO_SCHEMA", "No structured data (JSON-LD) found"))
        if not p.og_tags:
            issues.append(_issue("low", u, "NO_OG", "No Open Graph tags (social previews)"))
        if not p.lang:
            issues.append(_issue("low", u, "NO_LANG", "<html> has no lang attribute"))
        if p.response_time > 1.5:
            issues.append(_issue("medium", u, "SLOW_RESPONSE", f"Server response took {p.response_time}s (>1.5s)"))
        if not p.internal_links:
            issues.append(_issue("medium", u, "NO_INTERNAL_LINKS", "Page has no internal links (possible dead end)"))

    for t, urls in titles.items():
        if len(urls) > 1:
            for u in urls:
                issues.append(_issue("high", u, "TITLE_DUPLICATE", f"Duplicate title shared with {len(urls)-1} other page(s)"))
    for d, urls in descs.items():
        if len(urls) > 1:
            for u in urls:
                issues.append(_issue("medium", u, "META_DUPLICATE", f"Duplicate meta description shared with {len(urls)-1} other page(s)"))
    return issues


def health_score(pages: list, issues: list) -> int:
    """0-100 score: average of per-page scores, each reduced by weighted issues."""
    if not pages:
        return 0
    penalty = defaultdict(int)
    for i in issues:
        penalty[i["url"]] += WEIGHTS[i["severity"]]
    return round(sum(max(0, 100 - penalty[p.url]) for p in pages) / len(pages))
