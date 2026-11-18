"""Central configuration. Edit .env (or pass --url) to change the target site."""
import os
from dotenv import load_dotenv

load_dotenv()

# >>> PLACEHOLDER: the website the agent will optimise <<<
TARGET_URL = os.getenv("TARGET_URL", "https://tracevenue.com/")

MAX_PAGES = int(os.getenv("MAX_PAGES", "25"))
CRAWL_DELAY = float(os.getenv("CRAWL_DELAY_SECONDS", "0.5"))
LLM_MODEL = os.getenv("LLM_MODEL", "ollama:qwen2.5")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
PAGESPEED_API_KEY = os.getenv("PAGESPEED_API_KEY", "")
USER_AGENT = "SEOAgentBot/0.1 (educational SEO audit project)"
REPORT_DIR = "reports"


def llm_available() -> bool:
    provider = LLM_MODEL.split(":")[0].lower()
    if provider == "anthropic":
        return bool(os.getenv("ANTHROPIC_API_KEY"))
    if provider == "openai":
        return bool(os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_BASE_URL"))
    if provider == "ollama":
        return True
    return True  # other providers: assume configured

