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
