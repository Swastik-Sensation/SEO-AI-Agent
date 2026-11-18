"""Writes Markdown, PDF, and CSV reports for a completed SEO audit."""
import csv
import os
from collections import Counter
from datetime import date
from urllib.parse import urlparse

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from config import REPORT_DIR


def _safe_text(value) -> str:
    """Escape report content before adding it to ReportLab paragraphs."""
    return (str(value).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace("\n", "<br/>"))


def _report_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ReportTitle", parent=styles["Title"], fontName="Helvetica-Bold",
        fontSize=24, leading=29, textColor=colors.HexColor("#172554"), spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="ReportSubtitle", parent=styles["Normal"], fontSize=9, leading=13,
        textColor=colors.HexColor("#64748b"), spaceAfter=20,
    ))
    styles.add(ParagraphStyle(
        name="ReportHeading", parent=styles["Heading2"], fontName="Helvetica-Bold",
        fontSize=14, leading=18, textColor=colors.HexColor("#1e3a8a"),
        spaceBefore=16, spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="ReportBody", parent=styles["BodyText"], fontSize=9.5, leading=14,
        textColor=colors.HexColor("#1f2937"), spaceAfter=5,
    ))
    styles.add(ParagraphStyle(
        name="ReportSmall", parent=styles["BodyText"], fontSize=8, leading=10,
        textColor=colors.HexColor("#334155"),
    ))
    return styles


def _table(rows, widths=None, font_size=8):
    table = Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
        ("LEADING", (0, 0), (-1, -1), font_size + 3),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return table


def write_pdf_report(state: dict, path: str, sev: Counter, code_counts: Counter, example: dict):
    """Create a polished, print-friendly PDF version of the audit report."""
    styles = _report_styles()
    doc = SimpleDocTemplate(path, pagesize=A4, rightMargin=0.55 * inch,
                            leftMargin=0.55 * inch, topMargin=0.55 * inch,
                            bottomMargin=0.55 * inch, title="SEO Audit Report")
    issues, tech = state["issues"], state["technical"]
    story = [
        Paragraph("SEO Audit Report", styles["ReportTitle"]),
        Paragraph(_safe_text(state["url"]), styles["ReportSubtitle"]),
        _table([
            ["Health score", "Pages crawled", "Issues found", "Generated"],
            [f"{state['score']}/100", str(len(state["pages"])), str(len(issues)), str(date.today())],
        ], [1.55 * inch, 1.55 * inch, 1.55 * inch, 1.55 * inch], font_size=9),
        Paragraph("Issue overview", styles["ReportHeading"]),
        _table([
            ["Critical", "High", "Medium", "Low"],
            [str(sev["critical"]), str(sev["high"]), str(sev["medium"]), str(sev["low"])],
        ], [1.55 * inch] * 4, font_size=9),
    ]

    if state.get("ai_plan"):
        story += [Paragraph("Prioritised action plan", styles["ReportHeading"])]
        for line in str(state["ai_plan"]).splitlines():
            clean = line.lstrip("# -*").strip()
            if clean:
                story.append(Paragraph(_safe_text(clean), styles["ReportBody"]))

    https = tech["https"]
    sitemap = tech["sitemap"]
    technical_rows = [["Check", "Result"]]
    technical_rows += [
        ["HTTPS", "Enabled" if https["is_https"] else "Not enabled"],
        ["HTTP to HTTPS redirect", str(https["http_redirects_to_https"])],
        ["robots.txt", "Found" if tech["robots"]["found"] else "Missing"],
        ["sitemap.xml", f"Found - {sitemap.get('url_count', 0)} URLs" if sitemap["found"] else "Missing"],
        ["Broken links", str(len(tech["broken_links"]))],
    ]
    ps = tech.get("pagespeed", {})
    if ps and "error" not in ps:
        technical_rows.append(["PageSpeed", f"Score {ps.get('performance_score', 'n/a')} | LCP {ps.get('LCP', 'n/a')} | CLS {ps.get('CLS', 'n/a')}"])
    story += [Paragraph("Technical SEO", styles["ReportHeading"]), _table(technical_rows, [2.1 * inch, 4.1 * inch])]

    story += [Paragraph("Issues by type", styles["ReportHeading"])]
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    issue_rows = [["Severity", "Code", "Example", "Pages"]]
    for (severity, code), count in sorted(code_counts.items(), key=lambda item: order[item[0][0]]):
        issue_rows.append([severity.title(), code, Paragraph(_safe_text(example[code][:140]), styles["ReportSmall"]), str(count)])
    story.append(_table(issue_rows, [0.85 * inch, 1.1 * inch, 3.55 * inch, 0.7 * inch]))

    if tech["broken_links"]:
        story += [Paragraph("Broken links", styles["ReportHeading"])]
        link_rows = [["Link", "Status", "Found on"]]
        for broken in tech["broken_links"][:30]:
            link_rows.append([
                Paragraph(_safe_text(broken["link"]), styles["ReportSmall"]), str(broken["status"]),
                Paragraph(_safe_text(broken["found_on"]), styles["ReportSmall"]),
            ])
        story.append(_table(link_rows, [2.75 * inch, 0.6 * inch, 2.85 * inch]))

    keywords = state.get("keywords", {})
    if keywords:
        story += [Paragraph("Keyword themes", styles["ReportHeading"])]
        story.append(Paragraph("<b>Top terms:</b> " + _safe_text(", ".join(f"{word} ({count})" for word, count in keywords.get("top_terms", [])[:12])), styles["ReportBody"]))
        story.append(Paragraph("<b>Top phrases:</b> " + _safe_text(", ".join(f"{word} ({count})" for word, count in keywords.get("top_phrases", [])[:10])), styles["ReportBody"]))

    doc.build(story)


def write_report(state: dict) -> dict:
    os.makedirs(REPORT_DIR, exist_ok=True)
    domain = urlparse(state["url"]).netloc.replace(":", "_")
    stem = f"{REPORT_DIR}/seo_{domain}_{date.today().isoformat()}"
    issues, tech = state["issues"], state["technical"]
    sev = Counter(i["severity"] for i in issues)
    code_counts = Counter((i["severity"], i["code"]) for i in issues)
    example = {}
    for i in issues:
        example.setdefault(i["code"], i["issue"])

    L = [f"# SEO Audit Report: {state['url']}", f"_Generated {date.today()} | pages crawled: {len(state['pages'])}_", "",
         f"## Health score: **{state['score']}/100**", "",
         f"| Critical | High | Medium | Low |\n|---|---|---|---|\n| {sev['critical']} | {sev['high']} | {sev['medium']} | {sev['low']} |", ""]

    if state.get("ai_plan"):
        L += ["## Prioritised action plan (AI)", state["ai_plan"], ""]

    L += ["## Technical SEO",
          f"- HTTPS: {'yes' if tech['https']['is_https'] else 'NO'} | HTTP->HTTPS redirect: {tech['https']['http_redirects_to_https']}",
          f"- robots.txt: {'found' if tech['robots']['found'] else 'MISSING'}"
          + (" | WARNING: blocks all crawlers" if tech['robots'].get('blocks_all') else ""),
          f"- sitemap.xml: {'found, ' + str(tech['sitemap']['url_count']) + ' URLs' if tech['sitemap']['found'] else 'MISSING'}",
          f"- Broken links: {len(tech['broken_links'])}"]
    ps = tech.get("pagespeed", {})
    if "error" in ps:
        L.append(f"- PageSpeed: {ps['error']}")
    elif ps:
        L.append(f"- PageSpeed ({ps['strategy']}): score {ps['performance_score']} | LCP {ps['LCP']} | CLS {ps['CLS']} | TBT {ps['TBT']}")
    if tech["broken_links"]:
        L += ["", "| Broken link | Status | Found on |", "|---|---|---|"]
        L += [f"| {b['link']} | {b['status']} | {b['found_on']} |" for b in tech["broken_links"][:30]]

    L += ["", "## Issues by type", "| Severity | Code | Description | Pages |", "|---|---|---|---|"]
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    for (s, c), n in sorted(code_counts.items(), key=lambda x: order[x[0][0]]):
        L.append(f"| {s} | {c} | e.g. {example[c][:90]} | {n} |")

    kw = state.get("keywords", {})
    if kw:
        L += ["", "## Keyword themes found on site",
              "**Top terms:** " + ", ".join(f"{w} ({n})" for w, n in kw["top_terms"][:12]),
              "", "**Top phrases:** " + ", ".join(f"{w} ({n})" for w, n in kw["top_phrases"][:10])]

    if state.get("fixes"):
        L += ["", "## AI-suggested metadata (review before publishing)", ""]
        for f in state["fixes"]:
            L += [f"### {f['url']}", f"- **New title:** {f['new_title']} ({len(f['new_title'])} chars)",
                  f"- **New meta description:** {f['new_meta_description']} ({len(f['new_meta_description'])} chars)",
                  f"- _Why:_ {f['reasoning']}", ""]

    md_path = stem + ".md"
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    with open(stem + "_issues.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["severity", "code", "url", "issue"])
        w.writeheader()
        w.writerows(issues)
    pdf_path = stem + ".pdf"
    write_pdf_report(state, pdf_path, sev, code_counts, example)
    return {"md": md_path, "pdf": pdf_path, "csv": stem + "_issues.csv"}
