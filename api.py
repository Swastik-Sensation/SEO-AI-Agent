"""
FastAPI backend for the SEO AI Agent React frontend.
Run with: uvicorn api:app --reload --port 8000

Extra dependency for the sheet uploads:  pip install python-multipart
"""
import csv
import os
import re
import sys
import time
import uuid
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from fastapi import FastAPI, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).parent))
import config

app = FastAPI(title="SEO AI Agent API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# in-memory job store
jobs: dict = {}
opportunity_jobs: dict = {}
blog_jobs: dict = {}
profile_jobs: dict = {}
publisher_jobs: dict = {}
# parsed sheets uploaded for the presence check: upload_id -> {"kind", "filename", "data", "count"}
presence_uploads: dict = {}

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
ALLOWED_UPLOAD_EXT = (".csv", ".xlsx", ".xlsm")


class CrawlRequest(BaseModel):
    url: str
    max_pages: int = 5


class RunAuditRequest(BaseModel):
    url: str
    niche: Optional[str] = None
    max_pages: int = 25
    use_ai: bool = True


class OpportunityRequest(BaseModel):
    url: str
    project_name: Optional[str] = None
    niche: Optional[str] = None
    location: Optional[str] = None
    target_audience: Optional[str] = None
    links_per_category: int = 50
    # ── presence check: "is this site already registered on each listed website?" ──
    check_presence: bool = True                 # Registered / Not Registered / Unverified tagging
    link_suffix: Optional[str] = None           # Profile link suffix / handle (e.g. /tracevenue or tracevenue)
    link_suffixes: Optional[list[str]] = None   # Multiple suffixes (e.g. ["/tracevenue", "/Tracevenue", "/tracevenue1"])
    brand_handles: list[str] = Field(default_factory=list)   # extra profile handles to probe, e.g. ["tracevenue_official"]
    team_sheet_id: Optional[str] = None         # id returned by /api/opportunities/upload/team-sheet
    backlink_export_id: Optional[str] = None    # id returned by /api/opportunities/upload/backlink-export
    trust_team_reports: bool = False            # count team claims we cannot machine-verify as Registered (Low)
    force_recheck: bool = False                 # ignore cached "Registered" results


class BlogCheckRequest(BaseModel):
    project_url: str
    blog_url: str
    niche: Optional[str] = None
    focus_keyword: Optional[str] = None
    check_links: bool = False


class ProfileCheckRequest(BaseModel):
    project_url: str
    profile_url: str
    business_name: Optional[str] = None
    niche: Optional[str] = None
    max_posts: int = 5


class PublisherSearchRequest(BaseModel):
    niche: str
    location: Optional[str] = "Worldwide"
    keywords: Optional[str] = None
    max_publishers: int = 20
    check_mx: bool = False


def _safe_url(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


import csv

def _generate_opportunity_csv(job_id: str, result: dict) -> str:
    os.makedirs("reports", exist_ok=True)
    csv_path = os.path.abspath(f"reports/opportunities_{job_id[:8]}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Category", "Title", "Domain", "URL", "Link Suffix", "DA Authority", "DA Source", "Action Type",
                         "Source", "Snippet", "Registered", "Confidence", "Evidence URL", "Check Method",
                         "Link Type", "Check Note", "Checked On"])
        for cat in result.get("categories", []):
            cat_name = cat.get("category", "")
            for link in cat.get("links", []):
                writer.writerow([
                    cat_name,
                    link.get("title", ""),
                    link.get("domain", ""),
                    link.get("url", ""),
                    link.get("link_suffix", ""),
                    link.get("da", ""),
                    link.get("da_source", ""),
                    link.get("action", ""),
                    link.get("source", ""),
                    link.get("snippet", ""),
                    link.get("registered", ""),
                    link.get("confidence", ""),
                    link.get("evidence_url", ""),
                    link.get("check_method", ""),
                    link.get("link_type", ""),
                    link.get("check_note", ""),
                    link.get("checked_on", ""),
                ])
    return csv_path


def _generate_opportunity_xlsx(job_id: str, result: dict) -> str:
    """The Excel file the SEO team works from (Registered column + Status dropdown)."""
    from tools.opportunities import build_excel
    os.makedirs("reports", exist_ok=True)
    xlsx_path = os.path.abspath(f"reports/opportunities_{job_id[:8]}.xlsx")
    with open(xlsx_path, "wb") as f:
        f.write(build_excel(result))
    return xlsx_path


def _run_opportunity_search(job_id: str, context: dict, links_per_category: int, presence: Optional[dict] = None):
    job = opportunity_jobs[job_id]
    job["status"] = "running"
    job["log"] = []

    def progress(message: str):
        job["log"].append({"message": message, "timestamp": time.time()})

    try:
        from tools.opportunities import find_opportunities
    except ImportError as exc:
        job["status"] = "error"
        job["error"] = (
            f"Search dependency unavailable ({exc}). Install the backend requirements "
            "in the same Python that runs the API: pip install -r requirements.txt"
        )
        return

    try:
        result = find_opportunities(context, max(1, min(links_per_category, 50)), progress, presence=presence)
        job["result"] = result
        job["csv_path"] = _generate_opportunity_csv(job_id, result)
        job["xlsx_path"] = _generate_opportunity_xlsx(job_id, result)
        if not result.get("total_links"):
            progress("No public links found this run. Search engines may be rate limiting; try again shortly.")
        job["status"] = "done"
    except Exception as exc:
        job["status"] = "error"
        job["error"] = str(exc)


def _generate_blog_csv(job_id: str, result: dict) -> str:
    os.makedirs("reports", exist_ok=True)
    csv_path = os.path.abspath(f"reports/blog_audit_{job_id[:8]}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["=== BLOG & INTENT AUDIT SUMMARY ==="])
        writer.writerow(["Blog URL", result.get("blog_url", "")])
        writer.writerow(["Project URL", result.get("project_url", "")])
        writer.writerow(["Project Niche", result.get("project_niche", "")])
        align_score = result.get("niche_alignment_score")
        writer.writerow(["Niche Alignment", f"{align_score}%" if align_score is not None else "Extracted from Project"])
        writer.writerow(["Overall Health Score", f"{result.get('overall_health_score', '')}/100"])
        writer.writerow(["Primary Search Intent", result.get("primary_intent", "")])
        if result.get("secondary_intent"):
            writer.writerow(["Secondary Intent", result.get("secondary_intent", "")])
        writer.writerow(["Intent Confidence", result.get("intent_confidence", "")])
        idx = result.get("indexability", {})
        writer.writerow(["Indexable", "Yes" if idx.get("indexable") else "No"])
        if not idx.get("indexable") and idx.get("reasons"):
            writer.writerow(["Indexability Blockers", "; ".join(idx.get("reasons", []))])
        writer.writerow(["Google AI Bot Readiness", f"{result.get('ai_bot_readiness', {}).get('score', '')}/100 ({result.get('ai_bot_readiness', {}).get('badge', '')})"])
        writer.writerow([])
        writer.writerow(["=== KEYWORD & INTENT ALIGNMENT ==="])
        writer.writerow(["Keyword", "Type", "Count", "Density %", "In Title", "In H1", "In H2", "In First 100 Words", "Intent", "Intent Aligned", "Niche Aligned", "Status", "Recommendation"])
        for kw in result.get("keywords", []):
            writer.writerow([
                kw.get("keyword", ""),
                kw.get("type", ""),
                kw.get("count", ""),
                f"{kw.get('density', '')}%",
                "Yes" if kw.get("in_title") else "No",
                "Yes" if kw.get("in_h1") else "No",
                "Yes" if kw.get("in_h2") else "No",
                "Yes" if kw.get("in_first_100_words") else "No",
                kw.get("intent", ""),
                "Yes" if kw.get("intent_aligned") else "No",
                "Yes" if kw.get("niche_aligned") else "No",
                kw.get("status", ""),
                kw.get("recommendation", "")
            ])
        writer.writerow([])
        writer.writerow(["=== LINKS & ANCHOR TEXT AUDIT ==="])
        writer.writerow(["Type", "Anchor Text", "Target URL", "Domain", "Generic Warning", "Empty Warning", "Nofollow"])
        for link in result.get("links_summary", {}).get("internal_links", []):
            writer.writerow(["Internal", link.get("anchor", ""), link.get("url", ""), link.get("domain", ""), "Yes" if link.get("is_generic") else "No", "Yes" if link.get("is_empty") else "No", "Yes" if link.get("nofollow") else "No"])
        for link in result.get("links_summary", {}).get("external_links", []):
            writer.writerow(["External", link.get("anchor", ""), link.get("url", ""), link.get("domain", ""), "Yes" if link.get("is_generic") else "No", "Yes" if link.get("is_empty") else "No", "Yes" if link.get("nofollow") else "No"])
        writer.writerow([])
        writer.writerow(["=== ACTIONABLE FIXES & REPLACEMENT SUGGESTIONS ==="])
        writer.writerow(["Priority", "Category", "Title", "Type", "Wrong / Problematic Item", "Issue Details", "Suggested Replacement / Citation", "Target URL / Domain", "SEO Rationale"])
        for rec in result.get("recommendations", []):
            sugs = rec.get("suggestions", [])
            if sugs:
                for s in sugs:
                    writer.writerow([
                        rec.get("priority", ""),
                        rec.get("category", ""),
                        rec.get("title", ""),
                        rec.get("type", ""),
                        s.get("current") or s.get("source", ""),
                        s.get("issue") or s.get("topic", ""),
                        s.get("replacement") or s.get("anchor", ""),
                        s.get("url") or s.get("domain", ""),
                        s.get("reason", "")
                    ])
            else:
                writer.writerow([
                    rec.get("priority", ""),
                    rec.get("category", ""),
                    rec.get("title", ""),
                    rec.get("type", "general"),
                    rec.get("action", ""),
                    "", "", "", ""
                ])
    return csv_path


def _run_blog_audit_task(job_id: str, req: BlogCheckRequest):
    def log(msg: str, step: int):
        entry = {"timestamp": time.time(), "message": msg, "step": step}
        if job_id in blog_jobs:
            blog_jobs[job_id]["log"].append(entry)
            blog_jobs[job_id]["current_step"] = step

    try:
        from tools.blog_checker import audit_blog_post
        log("Analyzing project website and extracting niche context...", step=1)
        time.sleep(0.4)
        
        log(f"Fetching and parsing blog article at {req.blog_url}...", step=2)
        time.sleep(0.4)
        
        log("Checking indexability gates, robots.txt, and link anchors...", step=3)
        time.sleep(0.4)
        
        log("Classifying search intent (Commercial/Transactional/Informational/Navigational)...", step=4)
        time.sleep(0.4)
        
        log("Evaluating Google AI Search Bot (GEO / AI Overviews) readiness...", step=5)
        res = audit_blog_post(
            project_url=req.project_url,
            blog_url=req.blog_url,
            niche=req.niche,
            focus_keyword=req.focus_keyword,
            check_links=getattr(req, "check_links", False)
        )
        
        log("Generating keyword alignment matrix and CSV report...", step=6)
        csv_path = _generate_blog_csv(job_id, res)
        blog_jobs[job_id]["csv_path"] = csv_path

        blog_jobs[job_id]["result"] = res
        blog_jobs[job_id]["status"] = "done"
        log("Blog audit complete!", step=6)
    except Exception as exc:
        if job_id in blog_jobs:
            blog_jobs[job_id]["status"] = "error"
            blog_jobs[job_id]["error"] = str(exc)
            log(f"Error: {exc}", step=6)


def _generate_profile_csv(job_id: str, result: dict) -> str:
    os.makedirs("reports", exist_ok=True)
    csv_path = os.path.abspath(f"reports/profile_audit_{job_id[:8]}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["=== BUSINESS PROFILE AUDIT SUMMARY ==="])
        writer.writerow(["Profile URL", result.get("profile_url", "")])
        writer.writerow(["Target Website", result.get("project_url", "")])
        writer.writerow(["Platform", result.get("platform", "")])
        meta = result.get("profile_meta", {})
        writer.writerow(["Profile Name", meta.get("name", "")])
        writer.writerow(["Health Score", f"{result.get('score', '')}/100 ({result.get('badge', '')})"])
        writer.writerow([])

        # Backlink in Bio Audit
        backlink = result.get("backlink_analysis", {})
        writer.writerow(["=== WEBSITE BACKLINK IN BIO AUDIT ==="])
        writer.writerow(["Backlink Status", backlink.get("status", "")])
        writer.writerow(["Clickable Link Verified", "Yes" if backlink.get("found") else "No"])
        writer.writerow(["Link Placement", backlink.get("placement", "")])
        writer.writerow(["Matching URL", backlink.get("matching_url", "")])
        writer.writerow(["Anchor Text", backlink.get("anchor_text", "")])
        writer.writerow(["Protocol (HTTPS)", "Yes" if backlink.get("is_https") else "No"])
        writer.writerow(["Dofollow Link", "Yes" if backlink.get("is_dofollow") else "No"])
        writer.writerow(["Liveness HTTP Status", backlink.get("status_code", "N/A")])
        writer.writerow(["Summary", backlink.get("summary", "")])
        writer.writerow([])

        # Bio Content Correctness Audit
        bio = result.get("bio_analysis", {})
        writer.writerow(["=== BIO CONTENT CORRECTNESS AUDIT ==="])
        writer.writerow(["Extracted Bio Text", bio.get("bio_text", "")])
        writer.writerow(["Bio Correctness Verdict", bio.get("correctness_verdict", "")])
        writer.writerow(["Correctness Assessment", bio.get("correctness_details", "")])
        writer.writerow(["Business Name Mentioned", "Yes" if bio.get("business_name_match") else "No"])
        writer.writerow(["Niche Alignment Score", f"{bio.get('niche_alignment_score', 0)}% ({bio.get('niche_alignment_verdict', '')})"])
        writer.writerow(["Keywords Present in Bio", ", ".join(bio.get("keywords_present", []))])
        writer.writerow(["Keywords Missing in Bio", ", ".join(bio.get("keywords_missing", []))])
        writer.writerow(["Call to Action (CTA) Present", "Yes" if bio.get("has_cta") else "No"])
        writer.writerow(["CTA Phrase", bio.get("cta_phrase", "None")])
        writer.writerow(["Character Length", f"{bio.get('char_count', 0)} / {bio.get('platform_limit', 0)} chars"])
        writer.writerow([])

        # Issues
        writer.writerow(["=== 'WHAT IS NOT RIGHT' - ISSUES & RECOMMENDATIONS ==="])
        writer.writerow(["Severity", "Code", "Category", "Issue", "Business Impact", "Actionable Recommendation"])
        for issue in result.get("issues", []):
            writer.writerow([
                issue.get("severity", "").upper(),
                issue.get("code", ""),
                issue.get("category", ""),
                issue.get("issue", ""),
                issue.get("impact", ""),
                issue.get("recommendation", ""),
            ])
        writer.writerow([])

        # AI Bio Suggestions
        ai = result.get("ai_suggestions", {})
        writer.writerow(["=== AI OPTIMIZED BIO REWRITES (WITH WEBSITE LINK) ==="])
        writer.writerow(["AI Assessment", ai.get("assessment", "")])
        writer.writerow(["Short Bio (<= 160 chars)", ai.get("short_bio", "")])
        writer.writerow(["Value-Focused Bio", ai.get("value_bio", "")])
        writer.writerow(["SEO Keyword-Rich Bio", ai.get("keyword_bio", "")])
    return csv_path


def _run_profile_audit_task(job_id: str, req: ProfileCheckRequest):
    def log(msg: str, step: int):
        entry = {"timestamp": time.time(), "message": msg, "step": step}
        if job_id in profile_jobs:
            profile_jobs[job_id]["log"].append(entry)
            profile_jobs[job_id]["current_step"] = step

    try:
        from tools.profile_checker import audit_profile
        
        res = audit_profile(
            project_url=_safe_url(req.project_url.strip()),
            profile_url=_safe_url(req.profile_url.strip()),
            business_name=req.business_name.strip() if req.business_name else None,
            niche=req.niche.strip() if req.niche else None,
            max_posts=max(1, min(req.max_posts, 10)),
            progress_callback=log
        )
        
        log("Generating Profile Audit CSV report...", step=6)
        csv_path = _generate_profile_csv(job_id, res)
        profile_jobs[job_id]["csv_path"] = csv_path
        profile_jobs[job_id]["result"] = res
        profile_jobs[job_id]["status"] = "done"
        log("Profile audit complete!", step=6)
    except Exception as exc:
        if job_id in profile_jobs:
            profile_jobs[job_id]["status"] = "error"
            profile_jobs[job_id]["error"] = str(exc)
            log(f"Error: {exc}", step=6)


def _run_publisher_search_task(job_id: str, req: PublisherSearchRequest):
    def log(msg: str, step: int, total_steps: int = 4):
        entry = {"timestamp": time.time(), "message": msg, "step": step}
        if job_id in publisher_jobs:
            publisher_jobs[job_id]["log"].append(entry)
            publisher_jobs[job_id]["current_step"] = step

    try:
        from tools.publisher_finder import PublisherFinder, build_publisher_excel, build_publisher_csv
        finder = PublisherFinder(
            niche=req.niche,
            location=req.location or "",
            keywords=req.keywords or "",
            max_publishers=max(5, min(req.max_publishers, 50)),
            progress=log,
            check_mx=getattr(req, "check_mx", False),
        )
        result = finder.search_and_extract()

        os.makedirs("reports", exist_ok=True)
        xlsx_bytes = build_publisher_excel(result)
        xlsx_path = os.path.abspath(f"reports/publishers_{job_id[:8]}.xlsx")
        with open(xlsx_path, "wb") as f:
            f.write(xlsx_bytes)

        csv_text = build_publisher_csv(result, bom=True)
        csv_path = os.path.abspath(f"reports/publishers_{job_id[:8]}.csv")
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write(csv_text)

        if job_id in publisher_jobs:
            publisher_jobs[job_id]["result"] = result
            publisher_jobs[job_id]["xlsx_path"] = xlsx_path
            publisher_jobs[job_id]["csv_path"] = csv_path
            publisher_jobs[job_id]["status"] = "done"
    except Exception as exc:
        if job_id in publisher_jobs:
            publisher_jobs[job_id]["status"] = "error"
            publisher_jobs[job_id]["error"] = str(exc)
            log(f"Error: {exc}", step=4)


def _crawl_for_niche(url: str, max_pages: int = 5) -> dict:
    try:
        from tools.crawler import crawl
        from tools.keywords import top_keywords

        pages = crawl(url, min(max_pages, 5))
        if not pages:
            return {"niche": "Unknown", "keywords": [], "pages_crawled": 0}

        kw_data = top_keywords(pages)
        top_terms = [w for w, _ in kw_data.get("top_terms", [])[:8]]
        top_phrases = [w for w, _ in kw_data.get("top_phrases", [])[:5]]

        niche_keywords = {
            "Event Management": ["event", "venue", "booking", "conference", "wedding", "party"],
            "E-commerce": ["shop", "buy", "cart", "product", "price", "order", "store"],
            "SaaS / Technology": ["software", "platform", "api", "dashboard", "integration", "cloud"],
            "Healthcare": ["health", "medical", "doctor", "clinic", "patient", "treatment"],
            "Real Estate": ["property", "real estate", "buy", "rent", "apartment", "house", "listing"],
            "Education": ["course", "learn", "student", "training", "education", "school"],
            "Finance": ["finance", "investment", "bank", "loan", "money", "trading"],
            "Travel & Hospitality": ["hotel", "travel", "tour", "destination", "booking", "flight"],
            "Food & Restaurant": ["food", "restaurant", "menu", "delivery", "recipe", "chef"],
            "Marketing & Agency": ["marketing", "seo", "agency", "digital", "brand", "campaign"],
        }

        detected = "General Business"
        best_score = 0
        all_terms = " ".join(top_terms + top_phrases).lower()
        for niche, kws in niche_keywords.items():
            score = sum(1 for kw in kws if kw in all_terms)
            if score > best_score:
                best_score = score
                detected = niche

        return {
            "niche": detected,
            "keywords": top_terms,
            "phrases": top_phrases,
            "pages_crawled": len(pages),
        }
    except Exception as e:
        return {"niche": "Unknown", "error": str(e), "pages_crawled": 0}


def _run_full_audit(job_id: str, url: str, max_pages: int, use_ai: bool):
    try:
        jobs[job_id]["status"] = "running"
        jobs[job_id]["log"] = []

        def log(msg: str, step: int = None):
            entry = {"message": msg, "timestamp": time.time()}
            if step is not None:
                entry["step"] = step
            jobs[job_id]["log"].append(entry)

        # Step 1: Crawl
        log(f"Crawling up to {max_pages} pages...", step=1)
        jobs[job_id]["current_step"] = 1
        from tools.crawler import crawl
        pages = crawl(url, max_pages)
        log(f"Crawled {len(pages)} pages", step=1)
        jobs[job_id]["pages_count"] = len(pages)

        # Step 2: Technical
        jobs[job_id]["current_step"] = 2
        log("Running technical checks...", step=2)
        from tools.technical import check_robots, check_sitemap, check_https, check_broken_links, pagespeed
        robots = check_robots(url)
        tech = {
            "robots": robots,
            "sitemap": check_sitemap(url, robots),
            "https": check_https(url),
            "broken_links": check_broken_links(pages),
            "pagespeed": pagespeed(url),
        }
        log("Technical checks complete", step=2)

        # Step 3: Audit
        jobs[job_id]["current_step"] = 3
        log("Running on-page SEO audit...", step=3)
        from tools.audit import audit_pages, health_score
        issues = audit_pages(pages)
        for b in tech["broken_links"]:
            issues.append({"severity": "high", "url": b["found_on"], "code": "BROKEN_LINK",
                           "issue": f"Broken link {b['link']} (status {b['status']})"})
        t = tech
        if not t["robots"]["found"]:
            issues.append({"severity": "medium", "url": url, "code": "NO_ROBOTS", "issue": "robots.txt not found"})
        if not t["sitemap"]["found"]:
            issues.append({"severity": "high", "url": url, "code": "NO_SITEMAP", "issue": "sitemap.xml not found"})
        if t["https"]["is_https"] is False or t["https"]["http_redirects_to_https"] is False:
            issues.append({"severity": "critical", "url": url, "code": "HTTPS", "issue": "HTTPS not enforced"})
        score = health_score(pages, issues)
        log(f"{len(issues)} issues found | health score {score}/100", step=3)
        jobs[job_id]["score"] = score
        jobs[job_id]["issues_count"] = len(issues)

        # Step 4: Keywords
        jobs[job_id]["current_step"] = 4
        log("Extracting keyword themes...", step=4)
        from tools.keywords import top_keywords
        keywords = top_keywords(pages)
        log("Keyword extraction complete", step=4)

        # Step 5: AI Analysis
        jobs[job_id]["current_step"] = 5
        fixes = []
        ai_plan = ""
        if use_ai and config.llm_available():
            log(f"Running AI analysis with {config.LLM_MODEL}...", step=5)
            try:
                from agent import _llm, MetaFixList
                from collections import Counter
                llm = _llm()
                ok = [p for p in pages if p.status == 200 and p.title is not None]
                bad_codes = {"TITLE_MISSING", "TITLE_LONG", "TITLE_SHORT", "META_MISSING", "META_LONG",
                             "META_SHORT", "TITLE_DUPLICATE", "META_DUPLICATE"}
                bad_urls = {i["url"] for i in issues if i["code"] in bad_codes}
                targets = [p for p in ok if p.url in bad_urls][:3]
                if targets:
                    brief = "\n\n".join(
                        f"URL: {p.url}\nCurrent title: {p.title}\nCurrent meta: {p.meta_description}\n"
                        f"H1: {p.h1[:1]}\nPage text: {p.text_sample[:350]}" for p in targets)
                    prompt = ("You are a senior SEO copywriter. Rewrite titles and meta descriptions. "
                              "Keep them accurate, no keyword stuffing.\n\n" + brief)
                    result = llm.with_structured_output(MetaFixList).invoke(prompt)
                    fixes = [f.model_dump() for f in result.fixes]
                summary = Counter((i["severity"], i["code"]) for i in issues).most_common(25)
                kw = ", ".join(w for w, _ in keywords["top_terms"][:10])
                raw_plan = llm.invoke(
                    f"SEO strategist. Site: {url}. Health score {score}/100.\n"
                    f"Issues: {summary}\nTop terms: {kw}\n\n"
                    "Write prioritised action plan in Markdown: 'Do this week', 'Do this month', 'Later'. Max 10 bullets."
                ).content
                if isinstance(raw_plan, list):
                    raw_plan = "".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in raw_plan)
                ai_plan = raw_plan
                log("AI analysis complete", step=5)
            except Exception as e:
                log(f"AI analysis skipped: {e}", step=5)
                ai_plan = f"*AI analysis skipped: {e}*"
        else:
            log("AI analysis skipped (no LLM configured)", step=5)

        # Step 6: Report
        jobs[job_id]["current_step"] = 6
        log("Generating reports...", step=6)
        state = {"url": url, "pages": pages, "technical": tech, "issues": issues,
                 "score": score, "keywords": keywords, "fixes": fixes, "ai_plan": ai_plan}
        from tools.report import write_report
        report_paths = write_report(state)
        log("Reports generated!", step=6)

        jobs[job_id]["status"] = "done"
        jobs[job_id]["report_md"] = report_paths["md"]
        jobs[job_id]["report_pdf"] = report_paths["pdf"]
        jobs[job_id]["report_csv"] = report_paths["csv"]
        jobs[job_id]["result"] = {
            "score": score,
            "issues_count": len(issues),
            "pages_count": len(pages),
            "issues_by_severity": {sev: sum(1 for i in issues if i["severity"] == sev)
                                   for sev in ["critical", "high", "medium", "low"]},
            "top_issues": issues[:20],
            "technical": {
                "https": tech["https"],
                "robots": {"found": tech["robots"]["found"]},
                "sitemap": {"found": tech["sitemap"]["found"], "url_count": tech["sitemap"].get("url_count", 0)},
                "broken_links_count": len(tech["broken_links"]),
                "pagespeed": tech.get("pagespeed", {}),
            },
            "keywords": {
                "top_terms": keywords.get("top_terms", [])[:10],
                "top_phrases": keywords.get("top_phrases", [])[:5],
            },
            "ai_plan": ai_plan,
            "fixes": fixes,
        }
    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)


@app.get("/api/health")
def health():
    return {"status": "ok", "llm_model": config.LLM_MODEL, "llm_available": config.llm_available()}


@app.post("/api/detect-niche")
def detect_niche(req: CrawlRequest):
    url = _safe_url(req.url)
    result = _crawl_for_niche(url, req.max_pages)
    return {"url": url, **result}


@app.post("/api/audit/start")
def start_audit(req: RunAuditRequest, background_tasks: BackgroundTasks):
    url = _safe_url(req.url)
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "id": job_id, "url": url, "status": "queued",
        "created_at": time.time(), "current_step": 0, "total_steps": 6, "log": [],
    }
    background_tasks.add_task(_run_full_audit, job_id, url, req.max_pages, req.use_ai)
    return {"job_id": job_id, "url": url, "status": "queued"}


# ── Opportunities: presence-check sheet uploads ───────────────────────────────
async def _read_upload(file: UploadFile) -> bytes:
    name = (file.filename or "").lower()
    if not name.endswith(ALLOWED_UPLOAD_EXT):
        raise HTTPException(status_code=400, detail="Upload a .csv, .xlsx or .xlsm file")
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 5 MB)")
    if not content:
        raise HTTPException(status_code=400, detail="File is empty")
    return content


def _store_upload(kind: str, filename: str, data: dict) -> dict:
    upload_id = str(uuid.uuid4())
    presence_uploads[upload_id] = {"kind": kind, "filename": filename, "data": data, "created_at": time.time()}
    # keep memory bounded: drop the oldest uploads beyond 50
    if len(presence_uploads) > 50:
        for old in sorted(presence_uploads, key=lambda k: presence_uploads[k]["created_at"])[:-50]:
            presence_uploads.pop(old, None)
    with_url = sum(1 for urls in data.values() if urls)
    return {
        "upload_id": upload_id, "kind": kind, "filename": filename,
        "sites": len(data), "sites_with_urls": with_url,
        "preview": [{"site": s, "urls": u[:2]} for s, u in list(data.items())[:10]],
    }


@app.post("/api/opportunities/upload/team-sheet")
async def upload_team_sheet(file: UploadFile = File(...), target_url: Optional[str] = Form(None)):
    """SEO team's submission sheet (CSV/XLSX). Rows with a Status column count only when done/live/completed.
    Pass target_url so the project's own domain is ignored inside the sheet."""
    content = await _read_upload(file)
    try:
        from tools.presence_checker import load_team_sheet
        target = urlparse(_safe_url(target_url)).netloc if target_url else ""
        data = load_team_sheet(content, file.filename, target)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not parse sheet: {exc}")
    if not data:
        raise HTTPException(status_code=400, detail="No submitted URLs or domains found in the sheet")
    return _store_upload("team_sheet", file.filename, data)


@app.post("/api/opportunities/upload/backlink-export")
async def upload_backlink_export(file: UploadFile = File(...), target_url: Optional[str] = Form(None)):
    """Referring domains/pages export from Google Search Console, Ahrefs, Semrush or Moz (CSV/XLSX)."""
    content = await _read_upload(file)
    try:
        from tools.presence_checker import load_backlink_export
        target = urlparse(_safe_url(target_url)).netloc if target_url else ""
        data = load_backlink_export(content, file.filename, target)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not parse export: {exc}")
    if not data:
        raise HTTPException(status_code=400, detail="No referring domains found in the export")
    return _store_upload("backlink_export", file.filename, data)


@app.post("/api/opportunities/start")
def start_opportunity_search(req: OpportunityRequest, background_tasks: BackgroundTasks):
    url = _safe_url(req.url)

    # Normalize multiple suffixes
    raw_suffixes: list[str] = []
    if req.link_suffixes:
        for s in req.link_suffixes:
            if s and s.strip():
                raw_suffixes.extend(re.split(r"[,;\n\r\t]+", s.strip()))
    if req.link_suffix and req.link_suffix.strip():
        raw_suffixes.extend(re.split(r"[,;\n\r\t]+", req.link_suffix.strip()))

    clean_suffixes: list[str] = []
    seen: set[str] = set()
    for s in raw_suffixes:
        clean = re.sub(r"^[/@]+", "", s.strip()).strip()
        if clean and clean not in seen:
            seen.add(clean)
            clean_suffixes.append(f"/{clean}")

    link_suffix = ", ".join(clean_suffixes) if clean_suffixes else (req.link_suffix or "").strip()

    context = {
        "project_name": (req.project_name or urlparse(url).netloc.replace("www.", "")).strip(),
        "niche": (req.niche or "General Business").strip(),
        "location": (req.location or "Worldwide").strip(),
        "target_audience": (req.target_audience or "General audience").strip(),
        "link_suffix": link_suffix,
        "link_suffixes": clean_suffixes,
    }

    presence = None
    if req.check_presence:
        team = presence_uploads.get(req.team_sheet_id) if req.team_sheet_id else None
        backlinks = presence_uploads.get(req.backlink_export_id) if req.backlink_export_id else None
        if req.team_sheet_id and not team:
            raise HTTPException(status_code=404, detail="team_sheet_id not found - upload the sheet again")
        if req.backlink_export_id and not backlinks:
            raise HTTPException(status_code=404, detail="backlink_export_id not found - upload the export again")
        presence = {
            "target": urlparse(url).netloc.replace("www.", ""),
            "link_suffix": link_suffix,
            "link_suffixes": clean_suffixes,
            "handles": [h.strip() for h in req.brand_handles if h and h.strip()][:3],
            "team_done": team["data"] if team else {},
            "referring": backlinks["data"] if backlinks else {},
            "trust_team_reports": req.trust_team_reports,
            "force_recheck": req.force_recheck,
        }

    job_id = str(uuid.uuid4())
    opportunity_jobs[job_id] = {
        "id": job_id, "url": url, "context": context, "status": "queued",
        "created_at": time.time(), "log": [],
        "presence": {
            "enabled": bool(presence),
            "team_sheet": team["filename"] if presence and team else None,
            "backlink_export": backlinks["filename"] if presence and backlinks else None,
        },
    }
    background_tasks.add_task(_run_opportunity_search, job_id, context, req.links_per_category, presence)
    return {"job_id": job_id, "url": url, "context": context, "status": "queued",
            "presence": opportunity_jobs[job_id]["presence"]}


@app.get("/api/opportunities/{job_id}/status")
def get_opportunity_status(job_id: str):
    job = opportunity_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {key: job.get(key) for key in ("id", "url", "context", "status", "log", "error", "presence")}


@app.get("/api/opportunities/{job_id}/result")
def get_opportunity_result(job_id: str):
    job = opportunity_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "done":
        raise HTTPException(status_code=400, detail=f"Job not done yet (status: {job['status']})")
    return {"job_id": job_id, "url": job["url"], **job["result"]}


@app.get("/api/opportunities/{job_id}/download/csv")
def download_opportunity_csv(job_id: str):
    job = opportunity_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    path = job.get("csv_path")
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="CSV report not found")
    return FileResponse(path, media_type="text/csv", filename=os.path.basename(path))


@app.get("/api/opportunities/{job_id}/download/xlsx")
def download_opportunity_xlsx(job_id: str):
    job = opportunity_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    path = job.get("xlsx_path")
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Excel report not found")
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=os.path.basename(path),
    )


# ── Blog Checker Endpoints ────────────────────────────────────────────────────
@app.post("/api/blog-checker/start")
def start_blog_check(req: BlogCheckRequest, background_tasks: BackgroundTasks):
    p_url = _safe_url(req.project_url.strip())
    b_url = _safe_url(req.blog_url.strip())
    job_id = str(uuid.uuid4())
    blog_jobs[job_id] = {
        "id": job_id,
        "project_url": p_url,
        "blog_url": b_url,
        "status": "queued",
        "current_step": 0,
        "total_steps": 6,
        "created_at": time.time(),
        "log": [],
    }
    background_tasks.add_task(_run_blog_audit_task, job_id, req)
    return {"job_id": job_id, "project_url": p_url, "blog_url": b_url, "status": "queued"}


@app.get("/api/blog-checker/{job_id}/status")
def get_blog_check_status(job_id: str):
    job = blog_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "id": job_id,
        "status": job.get("status"),
        "current_step": job.get("current_step", 0),
        "total_steps": job.get("total_steps", 6),
        "log": job.get("log", []),
        "error": job.get("error")
    }


@app.get("/api/blog-checker/{job_id}/result")
def get_blog_check_result(job_id: str):
    job = blog_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.get("status") != "done":
        raise HTTPException(status_code=400, detail=f"Job not done yet (status: {job.get('status')})")
    return {"job_id": job_id, **job.get("result", {})}


@app.get("/api/blog-checker/{job_id}/download/csv")
def download_blog_csv(job_id: str):
    job = blog_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    path = job.get("csv_path")
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="CSV report not found")
    return FileResponse(path, media_type="text/csv", filename=os.path.basename(path))


# ── Profile Checker Endpoints ─────────────────────────────────────────────────
@app.post("/api/profile-checker/start")
def start_profile_check(req: ProfileCheckRequest, background_tasks: BackgroundTasks):
    p_url = _safe_url(req.project_url.strip())
    prof_url = _safe_url(req.profile_url.strip())
    job_id = str(uuid.uuid4())
    profile_jobs[job_id] = {
        "id": job_id,
        "project_url": p_url,
        "profile_url": prof_url,
        "status": "queued",
        "current_step": 0,
        "total_steps": 7,
        "created_at": time.time(),
        "log": [],
    }
    background_tasks.add_task(_run_profile_audit_task, job_id, req)
    return {"job_id": job_id, "project_url": p_url, "profile_url": prof_url, "status": "queued"}


@app.get("/api/profile-checker/{job_id}/status")
def get_profile_check_status(job_id: str):
    job = profile_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "id": job_id,
        "status": job.get("status"),
        "current_step": job.get("current_step", 0),
        "total_steps": job.get("total_steps", 7),
        "log": job.get("log", []),
        "error": job.get("error")
    }


@app.get("/api/profile-checker/{job_id}/result")
def get_profile_check_result(job_id: str):
    job = profile_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.get("status") != "done":
        raise HTTPException(status_code=400, detail=f"Job not done yet (status: {job.get('status')})")
    return {"job_id": job_id, **job.get("result", {})}


@app.get("/api/profile-checker/{job_id}/download/csv")
def download_profile_csv(job_id: str):
    job = profile_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    path = job.get("csv_path")
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="CSV report not found")
    return FileResponse(path, media_type="text/csv", filename=os.path.basename(path))


# --- Publisher Finder Endpoints ---

@app.post("/api/publishers/start")
def start_publisher_search(req: PublisherSearchRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    publisher_jobs[job_id] = {
        "status": "running",
        "current_step": 1,
        "total_steps": 4,
        "created_at": time.time(),
        "log": [],
        "niche": req.niche,
        "location": req.location,
    }
    background_tasks.add_task(_run_publisher_search_task, job_id, req)
    return {"job_id": job_id, "niche": req.niche, "location": req.location, "status": "queued"}


@app.get("/api/publishers/{job_id}/status")
def get_publisher_status(job_id: str):
    job = publisher_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "id": job_id,
        "status": job.get("status"),
        "current_step": job.get("current_step", 1),
        "total_steps": job.get("total_steps", 4),
        "log": job.get("log", []),
        "error": job.get("error"),
    }


@app.get("/api/publishers/{job_id}/result")
def get_publisher_result(job_id: str):
    job = publisher_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.get("status") != "done":
        raise HTTPException(status_code=400, detail=f"Job not done yet (status: {job.get('status')})")
    return {"job_id": job_id, **job.get("result", {})}


@app.get("/api/publishers/{job_id}/download/xlsx")
def download_publisher_xlsx(job_id: str):
    job = publisher_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    path = job.get("xlsx_path")
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Excel file not found")
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=os.path.basename(path),
    )


@app.get("/api/publishers/{job_id}/download/csv")
def download_publisher_csv(job_id: str):
    job = publisher_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    path = job.get("csv_path")
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="CSV file not found")
    return FileResponse(path, media_type="text/csv", filename=os.path.basename(path))



@app.get("/api/audit/{job_id}/status")
def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    job = jobs[job_id]
    return {
        "id": job_id, "status": job["status"],
        "current_step": job.get("current_step", 0),
        "total_steps": job.get("total_steps", 6),
        "log": job.get("log", []),
        "score": job.get("score"),
        "issues_count": job.get("issues_count"),
        "pages_count": job.get("pages_count"),
        "error": job.get("error"),
    }


@app.get("/api/audit/{job_id}/result")
def get_result(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    job = jobs[job_id]
    if job["status"] != "done":
        raise HTTPException(status_code=400, detail=f"Job not done yet (status: {job['status']})")
    return {"job_id": job_id, "url": job["url"], **job.get("result", {})}


@app.get("/api/audit/{job_id}/download/csv")
def download_csv(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    path = jobs[job_id].get("report_csv")
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="CSV report not found")
    return FileResponse(path, media_type="text/csv", filename=os.path.basename(path))


@app.get("/api/audit/{job_id}/download/md")
def download_md(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    path = jobs[job_id].get("report_md")
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Markdown report not found")
    return FileResponse(path, media_type="text/markdown", filename=os.path.basename(path))


@app.get("/api/audit/{job_id}/download/pdf")
def download_pdf(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    path = jobs[job_id].get("report_pdf")
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="PDF report not found")
    return FileResponse(path, media_type="application/pdf", filename=os.path.basename(path))


@app.get("/api/jobs")
def list_jobs():
    return [
        {"id": jid, "url": j["url"], "status": j["status"],
         "score": j.get("score"), "created_at": j["created_at"]}
        for jid, j in sorted(jobs.items(), key=lambda x: -x[1]["created_at"])
    ]