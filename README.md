# SEO Automation Agent (LangGraph)

An AI agent that audits a website, finds SEO problems, and produces a prioritised fix plan with
ready-to-use title/meta suggestions. It combines **deterministic rule-based checks** (fast, free,
reliable) with **LLM reasoning** (copywriting and prioritisation).

> **Target website placeholder:** set `TARGET_URL` in `.env` (default `https://tracevenue.com/`)
> or pass `--url` on the command line.

---

## 1. Quick start

```bash
# 1. Create a virtual environment
python -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure
cp .env.example .env                # Windows: copy .env.example .env
#   - edit TARGET_URL  (the website placeholder)
#   - choose LLM: local Ollama (e.g. LLM_MODEL=ollama:qwen2.5) or paid cloud keys


# 4. Run
python main.py                                           # uses TARGET_URL from .env
python main.py --url https://tracevenue.com/ --max-pages 20
python main.py --url https://example.com --no-ai         # rule-based audit only, no API key needed
```

Output goes to `reports/`:
- `seo_<domain>_<date>.md`: the full human-readable report
- `seo_<domain>_<date>_issues.csv`: every issue (severity, code, URL) for Excel/Sheets

---

## 2. Architecture

```
START -> crawl_node -> technical_node -> audit_node -> keyword_node -+-> ai_node -> report_node -> END
                                                                     |                ^
                                                                     +-- (no LLM key)-+
```

| File | Responsibility |
|---|---|
| `main.py` | CLI entry point, handles the URL placeholder |
| `config.py` | Settings loaded from `.env` |
| `agent.py` | LangGraph state + nodes + graph wiring |
| `tools/crawler.py` | Same-domain BFS crawler + HTML parser |
| `tools/technical.py` | robots.txt, sitemap, HTTPS, broken links, PageSpeed API |
| `tools/audit.py` | On-page rule engine + health score |
| `tools/keywords.py` | Keyword/phrase extraction |
| `tools/report.py` | Markdown + CSV report writer |

---

## 3. Tasks the agent performs (and how)

### A. Technical SEO: fully automated

| Task | How it is done | Module |
|---|---|---|
| Site crawling | Breadth-first crawl of internal links from the start URL, up to `MAX_PAGES`, with a polite delay and a custom User-Agent | `crawler.py` |
| HTTP error detection | Records the status code of every crawled page; 4xx/5xx and unreachable pages are flagged **critical** | `crawler.py`, `audit.py` |
| Broken link detection | Collects all internal + external links, checks each with HEAD (falls back to GET) in parallel; status 0 or >=400 is reported with the page it was found on | `technical.py` |
| robots.txt check | Fetches `/robots.txt`, confirms it exists, detects a global `Disallow: /`, extracts sitemap URLs | `technical.py` |
| Sitemap check | Fetches the sitemap (from robots.txt or `/sitemap.xml`) and counts `<loc>` URLs | `technical.py` |
| HTTPS enforcement | Verifies the site URL is HTTPS and that `http://` redirects to `https://` | `technical.py` |
| Core Web Vitals / speed | Calls the Google PageSpeed Insights API (Lighthouse, mobile): performance score, LCP, CLS, TBT, FCP | `technical.py` |
| Server response time | Measures per-page response time; >1.5 s is flagged | `crawler.py`, `audit.py` |
| Mobile-friendliness signal | Checks for the `viewport` meta tag | `audit.py` |
| Canonical / noindex | Detects missing canonical tags and `noindex` directives that hide pages from search | `audit.py` |
| Structured data | Parses JSON-LD blocks and lists schema types; flags pages with none | `crawler.py`, `audit.py` |

### B. On-page SEO: fully automated detection

| Task | How it is done |
|---|---|
| Title tag audit | Missing, too short (<30), too long (>60), duplicated across pages |
| Meta description audit | Missing, too short (<70), too long (>160), duplicated across pages |
| Heading structure | No H1, or multiple H1s |
| Image alt text | Counts images without alt text per page |
| Thin content | Word count under 300 words |
| Internal linking | Flags pages with no internal links (dead ends) |
| Social tags / language | Missing Open Graph tags, missing `lang` attribute |

Every finding gets a severity (critical / high / medium / low). The **health score (0-100)** is the average
of per-page scores, where each page loses points per issue (critical 40, high 15, medium 7, low 2).

### C. Keyword analysis: automated, human decides

| Task | How it is done |
|---|---|
| Keyword themes | Tokenises title, H1 and body text (title/H1 weighted x2), removes stop words, counts top terms and 2-word phrases across the site |
| Per-page focus terms | Top 5 terms per page |

This shows what the site *currently* targets. It does not replace real search-volume data (see Future Scope).

### D. AI-assisted tasks (needs an LLM key): agent drafts, human approves

| Task | How it is done |
|---|---|
| Title + meta rewrites | For pages with title/meta issues (max 8 per run to control cost), the LLM receives the current title, meta, H1 and page text, and returns **structured JSON** (Pydantic schema) with a new title (30-60 chars), new meta (120-160 chars) and a one-line reason |
| Prioritised action plan | The LLM receives aggregated issue counts, technical results, PageSpeed data and top site terms, and writes a plan: *do this week / this month / later* |

### E. Reporting: automated

Markdown report with score, severity table, technical summary, broken links, issues by type, keyword themes,
AI suggestions and the action plan, plus a CSV of every issue.

---

## 4. What the agent deliberately does NOT do

| Not automated | Why |
|---|---|
| Publishing changes to the live site | A wrong redirect or noindex can de-index pages, so the agent only **suggests** |
| Link building / digital PR | Needs real relationships and newsworthy content; automated link schemes are penalised |
| Original expertise (E-E-A-T), case studies, quotes | Must come from real people and real experience |
| Business strategy and migrations | Depends on goals, budget and trade-offs |
| JavaScript-rendered content | The base crawler reads raw HTML only (see Future Scope) |

---

## 5. Configuration (`.env`)

| Variable | Meaning | Default |
|---|---|---|
| `TARGET_URL` | **Website placeholder** | `https://tracevenue.com/` |
| `MAX_PAGES` | Crawl limit | 25 |
| `CRAWL_DELAY_SECONDS` | Delay between requests | 0.5 |
| `LLM_MODEL` | `provider:model` | `anthropic:claude-sonnet-4-6` |
| `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` | LLM credentials (one is enough) | empty |
| `PAGESPEED_API_KEY` | Optional, raises PageSpeed quota | empty |

Only audit sites you own or have permission to crawl, and keep the crawl delay polite.

---

## 6. Known limitations

- Raw-HTML crawling: sites built as client-side SPAs may show empty titles/content (the crawler does not run JavaScript).
- Keyword step is frequency-based, with no search volume or difficulty data.
- Broken-link check is capped at 80 links per run; some servers block bots with 403/429.
- PageSpeed is tested for the homepage only.
- The crawler does not obey `robots.txt` disallow rules yet (add before crawling third-party sites).

---

## 7. Future scope

**Near term**
1. **Playwright rendering** for JavaScript-heavy sites.
2. **Respect robots.txt** rules and rate limits per domain.
3. **Google Search Console + GA4 APIs**: real clicks, impressions, CTR and rankings. Auto-detect traffic drops and pages ranking at positions 8-20 (quick wins).
4. **Human-in-the-loop with LangGraph `interrupt`**: approve or reject each AI suggestion before it is exported.
5. **Embedding-based internal link suggestions** and keyword clustering by search intent.

**Mid term**
6. **Competitor and SERP analysis** via a SERP API (SerpAPI, DataForSEO): content gaps and what ranks and why.
7. **Keyword research with volume and difficulty** (Google Keyword Planner, DataForSEO, Ahrefs/Semrush APIs).
8. **Content briefs and drafts** with fact-check and brand-voice steps, never auto-published.
9. **Schema generator** that produces JSON-LD (Organization, LocalBusiness, FAQ, Product) per page type.
10. **Image optimisation checks** (size, format, lazy loading) and per-page Lighthouse runs.
11. **Scheduling and alerts**: weekly runs (cron / GitHub Actions) with Slack or email summaries and diffs against the last report.

**Long term**
12. **CMS integration** (WordPress / Shopify / GitHub PRs) to apply approved fixes automatically.
13. **Backlink prospecting and outreach drafting** with human-reviewed sending.
14. **Dashboard** (Streamlit or React + FastAPI) with history, trends and multi-site support.
15. **Evaluation harness**: golden test sites, LangSmith tracing, and tracking suggestion accept-rate.
16. **Multi-agent split**: Auditor, Researcher, Writer and Reviewer agents coordinated by a supervisor.
