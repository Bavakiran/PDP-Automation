"""config.py — shared configuration"""

BASE_URL   = "https://www.indiamart.com"
SEARCH_URL = "https://dir.indiamart.com"

# Direct PDP URL used for stable tests (confirmed working product)
DIRECT_PDP_URL = "https://www.indiamart.com/proddetail/16mm-vizag-steel-tmt-bars-2858961425462.html"

BROWSER_OPTIONS = {
    "headless": False,
    "slow_mo":  200,
}

VIEWPORT = {"width": 1440, "height": 900}

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"
)

TIMEOUT = 30_000

# ── Regression login credentials ──────────────────────────────────────────────
MOBILE_NUMBER = "9500144262"    # Phase 2 — identified (no OTP)
OTP           = ""              # Phase 2 — leave blank
HEADLESS      = False

# ── LLM Gateway (AI Visual Checker) ───────────────────────────────────────────
LLM_BASE_URL = "https://imllm.intermesh.net"
LLM_API_KEY  = "sk-6FNmFgd7M7hDn6IggecNjA"  
LLM_MODEL    = "google/gemini-2.5-flash-lite"      # vision-capable, low token cost