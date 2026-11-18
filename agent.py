"""LangGraph workflow:  crawl -> technical -> audit -> keywords -> (AI fixes) -> report"""
from typing import TypedDict, Optional

from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field

import config
from tools.crawler import crawl
from tools.technical import check_robots, check_sitemap, check_https, check_broken_links, pagespeed
from tools.audit import audit_pages, health_score
from tools.keywords import top_keywords
from tools.report import write_report


class SEOState(TypedDict, total=False):
    url: str
    pages: list
    technical: dict
    issues: list
    score: int
    keywords: dict
    fixes: list
    ai_plan: str
    report_path: str


# ---------- structured output for the LLM ----------
class MetaFix(BaseModel):
    url: str
    new_title: str = Field(description="30-60 chars, primary keyword near the start, brand at end")
    new_meta_description: str = Field(description="120-160 chars, benefit-led with a call to action")
    reasoning: str = Field(description="One sentence on why this is better")


class MetaFixList(BaseModel):
    fixes: list[MetaFix]


def _llm():
    import os
    parts = config.LLM_MODEL.split(":", 1)
    provider = parts[0].lower()
    model_name = parts[1] if len(parts) > 1 else ""

    if provider == "ollama":
        ollama_url = getattr(config, "OLLAMA_BASE_URL", "http://localhost:11434")
        try:
            from langchain_ollama import ChatOllama
            return ChatOllama(
                model=model_name or "qwen2.5",
                base_url=ollama_url,
                temperature=0.3,
                num_predict=1500,
            )
        except ImportError:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=model_name or "qwen2.5",
                base_url=f"{ollama_url.rstrip('/')}/v1",
                api_key="ollama",
                temperature=0.3,
                max_tokens=1500,
            )


    if provider == "openai" and os.getenv("OPENAI_BASE_URL"):
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model_name or "gpt-4o-mini",
            base_url=os.getenv("OPENAI_BASE_URL"),
            api_key=os.getenv("OPENAI_API_KEY", "local"),
            temperature=0.3,
        )

    from langchain.chat_models import init_chat_model
    return init_chat_model(config.LLM_MODEL, temperature=0.3)


# ---------- nodes ----------
def crawl_node(s: SEOState):
    print(f"[1/6] Crawling {s['url']} (max {config.MAX_PAGES} pages)...")
    pages = crawl(s["url"], config.MAX_PAGES)
    print(f"      crawled {len(pages)} pages")
    return {"pages": pages}


def technical_node(s: SEOState):
    print("[2/6] Technical checks (robots, sitemap, HTTPS, links, PageSpeed)...")
    robots = check_robots(s["url"])
    tech = {
        "robots": robots,
        "sitemap": check_sitemap(s["url"], robots),
        "https": check_https(s["url"]),
        "broken_links": check_broken_links(s["pages"]),
        "pagespeed": pagespeed(s["url"]),
    }
    return {"technical": tech}


def audit_node(s: SEOState):
    print("[3/6] On-page audit...")
    issues = audit_pages(s["pages"])
    for b in s["technical"]["broken_links"]:
        issues.append({"severity": "high", "url": b["found_on"], "code": "BROKEN_LINK",
                       "issue": f"Broken link {b['link']} (status {b['status']})"})
    t = s["technical"]
    if not t["robots"]["found"]:
        issues.append({"severity": "medium", "url": s["url"], "code": "NO_ROBOTS", "issue": "robots.txt not found"})
    if not t["sitemap"]["found"]:
        issues.append({"severity": "high", "url": s["url"], "code": "NO_SITEMAP", "issue": "sitemap.xml not found"})
    if t["https"]["is_https"] is False or t["https"]["http_redirects_to_https"] is False:
        issues.append({"severity": "critical", "url": s["url"], "code": "HTTPS", "issue": "HTTPS not enforced"})
    score = health_score(s["pages"], issues)
    print(f"      {len(issues)} issues found | health score {score}/100")
    return {"issues": issues, "score": score}


def keyword_node(s: SEOState):
    print("[4/6] Extracting keyword themes...")
    return {"keywords": top_keywords(s["pages"])}


def route_after_keywords(s: SEOState):
    return "ai_node" if config.llm_available() else "report_node"


def ai_node(s: SEOState):
    print(f"[5/6] AI analysis with {config.LLM_MODEL}...")
    fixes = []
    plan = ""
    try:
        llm = _llm()
        ok = [p for p in s["pages"] if p.status == 200 and p.title is not None]

        # (a) rewrite metadata for pages that have title/meta problems
        bad_codes = {"TITLE_MISSING", "TITLE_LONG", "TITLE_SHORT", "META_MISSING", "META_LONG",
                     "META_SHORT", "TITLE_DUPLICATE", "META_DUPLICATE"}
        bad_urls = {i["url"] for i in s["issues"] if i["code"] in bad_codes}
        targets = [p for p in ok if p.url in bad_urls][:3]  # cap to top 3 for speed on CPU
        if targets:
            brief = "\n\n".join(
                f"URL: {p.url}\nCurrent title: {p.title}\nCurrent meta: {p.meta_description}\n"
                f"H1: {p.h1[:1]}\nPage text: {p.text_sample[:350]}" for p in targets)
            prompt = ("You are a senior SEO copywriter. Rewrite the title and meta description for each page below. "
                      "Keep them accurate to the page content, never invent facts, avoid keyword stuffing.\n\n" + brief)
            result = llm.with_structured_output(MetaFixList).invoke(prompt)
            fixes = [f.model_dump() for f in result.fixes]


        # (b) prioritised action plan from the issue summary
        from collections import Counter
        summary = Counter((i["severity"], i["code"]) for i in s["issues"]).most_common(25)
        kw = ", ".join(w for w, _ in s["keywords"]["top_terms"][:10])
        raw_plan = llm.invoke(
            f"You are an SEO strategist. Site: {s['url']}. Health score {s['score']}/100.\n"
            f"Issue counts (severity, code, pages): {summary}\n"
            f"Technical: {s['technical']['https']}, robots found={s['technical']['robots']['found']}, "
            f"sitemap found={s['technical']['sitemap']['found']}, broken links={len(s['technical']['broken_links'])}, "
            f"pagespeed={s['technical']['pagespeed']}\nTop site terms: {kw}\n\n"
            "Write a prioritised action plan in Markdown: 'Do this week', 'Do this month', 'Later'. "
            "Max 10 bullets total, each with the reason and expected impact. Be specific and concise."
        ).content
        if isinstance(raw_plan, list):  # some providers return content blocks
            raw_plan = "".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in raw_plan)
        plan = raw_plan
    except Exception as e:
        print(f"      [Warning] AI analysis skipped due to error: {e}")
        plan = f"*AI analysis skipped due to error: {e}*"

    return {"fixes": fixes, "ai_plan": plan}



def report_node(s: SEOState):
    print("[6/6] Writing report...")
    # Preserve the Markdown path for the command-line workflow; the web API also
    # exposes the companion PDF and CSV paths returned by write_report().
    return {"report_path": write_report(s)["md"]}


def build_graph():
    g = StateGraph(SEOState)
    for name, fn in [("crawl_node", crawl_node), ("technical_node", technical_node), ("audit_node", audit_node),
                     ("keyword_node", keyword_node), ("ai_node", ai_node), ("report_node", report_node)]:
        g.add_node(name, fn)
    g.add_edge(START, "crawl_node")
    g.add_edge("crawl_node", "technical_node")
    g.add_edge("technical_node", "audit_node")
    g.add_edge("audit_node", "keyword_node")
    g.add_conditional_edges("keyword_node", route_after_keywords, ["ai_node", "report_node"])
    g.add_edge("ai_node", "report_node")
    g.add_edge("report_node", END)
    return g.compile()
