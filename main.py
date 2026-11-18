"""Run:  python main.py            (uses TARGET_URL from .env)
        python main.py --url https://example.com --max-pages 10"""
import argparse

import config
from agent import build_graph


def main():
    ap = argparse.ArgumentParser(description="SEO automation agent")
    ap.add_argument("--url", default=config.TARGET_URL, help="Website to optimise (placeholder default in .env)")
    ap.add_argument("--max-pages", type=int, default=None)
    ap.add_argument("--no-ai", action="store_true", help="Skip LLM steps (rule-based audit only)")
    args = ap.parse_args()

    if args.max_pages:
        config.MAX_PAGES = args.max_pages
    if args.no_ai:
        config.llm_available = lambda: False
    if not args.url.startswith(("http://", "https://")):
        args.url = "https://" + args.url

    print(f"\n=== SEO Agent | target: {args.url} ===")
    if not config.llm_available():
        print("(No LLM key found / --no-ai set: running rule-based audit only)\n")

    result = build_graph().invoke({"url": args.url})
    print(f"\nDone. Health score: {result['score']}/100")
    print(f"Report: {result['report_path']}")


if __name__ == "__main__":
    main()
