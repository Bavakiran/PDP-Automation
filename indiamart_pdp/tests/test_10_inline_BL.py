"""
Suite 10: Get Quotes from Verified Suppliers

TC-5957  Scroll to inline BL form section
         ("Tell us what you need" / "Get Quotes from Verified Suppliers")
         → verify section heading is displayed

TC-5958  In the same inline BL form section
         → verify product name input is prefilled
         → value fully or partially matches the PDP h1 product title
"""
import sys
from pathlib import Path
from playwright.sync_api import Page, Locator

try:
    from utils.helpers import DIRECT_PDP_URL, SEL, TestResult, first_visible, land_on_pdp_direct
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from indiamart_pdp.utils.helpers import DIRECT_PDP_URL, SEL, TestResult, first_visible, land_on_pdp_direct


# ---------------------------------------------------------------------------
# Helper: dismiss "Unlock IndiaMART" popup
# ---------------------------------------------------------------------------
def _dismiss_login_popup(page: Page):
    try:
        skip = page.locator(
            "a#idfpclose, a.idfpclose, a.skptxt, text=Skip"
        ).first
        if skip.is_visible(timeout=5000):
            print("  [POPUP] Login popup detected — clicking Skip")
            skip.click(force=True)
            page.wait_for_timeout(1000)
            return
    except Exception:
        pass
    try:
        overlay = page.locator(
            "div#identyfy_usr_ctl, div[class*='iden_bg'], div[class*='wd_box1']"
        ).first
        if overlay.is_visible(timeout=2000):
            print("  [POPUP] Overlay still present — hard refreshing")
            page.reload(wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(2000)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Helper: red outline + console log
# ---------------------------------------------------------------------------
def _highlight_and_log(page: Page, locator: Locator, label: str):
    try:
        locator.scroll_into_view_if_needed()
        page.wait_for_timeout(500)
        el = locator.element_handle()
        tag  = page.evaluate("el => el.tagName", el)
        text = page.evaluate(
            "el => el.innerText || el.getAttribute('alt') || el.getAttribute('aria-label') || ''", el
        )
        print(f"  [CHECK] [{label}] <{tag.lower()}> '{text[:80].strip()}'")
        page.evaluate(
            """el => {
                el.style.outline = '4px solid red';
                el.style.outlineOffset = '3px';
                el.style.backgroundColor = 'rgba(255,0,0,0.15)';
                setTimeout(() => {
                    el.style.outline = '';
                    el.style.outlineOffset = '';
                    el.style.backgroundColor = '';
                }, 2500);
            }""",
            el
        )
        page.wait_for_timeout(1500)
    except Exception as e:
        print(f"  [CHECK] [{label}] (highlight failed: {e})")


# ---------------------------------------------------------------------------
# Scroll to the inline BL form section and return its locator
# Heading variants:
#   "Tell us what you need, and we'll help you get quotes"
#   "Get Quotes from Verified Suppliers"
#   id="t0102_hdg1", class="be-fhdg"
# ---------------------------------------------------------------------------
def _scroll_to_bl_section(page: Page) -> Locator:
    # Scroll down gradually to trigger lazy-load of the inline BL section
    for pct in [0.4, 0.6, 0.75, 0.88, 1.0]:
        page.evaluate(f"window.scrollTo(0, document.body.scrollHeight * {pct})")
        page.wait_for_timeout(1000)
        _dismiss_login_popup(page)

        # Check if section appeared after this scroll step
        container = page.locator("#t0102_inlineBL").first
        try:
            if container.is_visible(timeout=1500):
                container.scroll_into_view_if_needed()
                page.wait_for_timeout(1000)
                _dismiss_login_popup(page)
                heading = page.locator("#t0102_hdg1").first
                print(f"  [SCROLL] BL section found at {int(pct*100)}% scroll: "
                      f"'{heading.inner_text().strip()[:80]}'")
                return heading
        except Exception:
            continue

    raise Exception("Inline BL form section (#t0102_inlineBL) not found after full scroll")


# ---------------------------------------------------------------------------
# Suite runner
# ---------------------------------------------------------------------------
def run(page: Page) -> TestResult:
    tr = TestResult(page)
    print("\n[Suite 10] Get Quotes from Verified Suppliers")

    # ── TC-5957 ──────────────────────────────────────────────────────────────
    # Scroll to inline BL form section → verify heading is displayed
    land_on_pdp_direct(page, DIRECT_PDP_URL)
    _dismiss_login_popup(page)
    try:
        heading = _scroll_to_bl_section(page)
        _highlight_and_log(page, heading, "TC-5957 inline_bl_heading")

        assert heading.is_visible(timeout=5000), \
            "Inline BL form heading not visible"
        heading_text = heading.inner_text().strip()
        assert len(heading_text) > 0, "Inline BL form heading is empty"

        tr.add("TC-5957", "Inline BL form section is displayed", "PASS",
               heading_text[:80])
    except Exception as exc:
        tr.add("TC-5957", "Inline BL form section is displayed", "FAIL", str(exc)[:120])

    # ── TC-5958 ──────────────────────────────────────────────────────────────
    # Scroll to inline BL form → verify product name is prefilled
    # and fully or partially matches the PDP h1 title
    land_on_pdp_direct(page, DIRECT_PDP_URL)
    _dismiss_login_popup(page)
    try:
        # Get the H1 product title first (before scrolling away)
        h1_loc = page.locator("h1.center-heading, h1").first
        h1_loc.wait_for(state="visible", timeout=8000)
        h1_text = h1_loc.inner_text().strip()
        print(f"  [INFO] [TC-5958] H1 product title: '{h1_text[:80]}'")

        # Scroll to inline BL section
        _scroll_to_bl_section(page)

        # Find the product name input in the inline BL form
        # Product input is inside div#t0901_prodtitle
        product_input = page.locator(
            "#t0901_prodtitle input, "
            "#t0901_prodtitle textarea, "
            "#t0102_inlineBL input[type='text'], "
            "#t0102_inlineBL textarea"
        ).first
        product_input.wait_for(state="visible", timeout=8000)
        _highlight_and_log(page, product_input, "TC-5958 product_name_input")

        # Get prefilled value
        try:
            prefilled = product_input.input_value()
        except Exception:
            prefilled = product_input.get_attribute("value") or product_input.inner_text()
        prefilled = (prefilled or "").strip()
        print(f"  [CHECK] [TC-5958] Prefilled value: '{prefilled[:80]}'")

        assert len(prefilled) > 0, "Product name input is empty — not prefilled"

        # Check full or partial match with H1 title (case-insensitive)
        h1_words = set(h1_text.lower().split())
        prefilled_words = set(prefilled.lower().split())
        common_words = h1_words & prefilled_words
        # Remove common stop words from match check
        stop = {"with", "and", "the", "of", "in", "for", "a", "an", "to", "&"}
        meaningful_common = common_words - stop

        assert len(meaningful_common) > 0, (
            f"Prefilled value '{prefilled}' does not match H1 '{h1_text}'"
        )
        print(f"  [CHECK] [TC-5958] Matching words: {meaningful_common}")

        tr.add("TC-5958", "Product name prefilled matches PDP title", "PASS",
               f"'{prefilled[:50]}' matches H1")
    except Exception as exc:
        tr.add("TC-5958", "Product name prefilled matches PDP title", "FAIL", str(exc)[:120])

    return tr


if __name__ == "__main__":
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=200)
        page = browser.new_page()
        result = run(page)
        summary = result.summary()
        print(f"\nSummary: {summary['passed']}/{summary['total']} passed")
        browser.close()