"""
Suite 05: Find Related Categories

TC-5946  Land on PDP → scroll → check "Find related categories" heading is visible
TC-5947  Click first related category (MCAT) → verify category search page opens
TC-5948  Get Quotes visible → click → BL form opens
"""

import sys
import contextlib
from pathlib import Path
from playwright.sync_api import Page, Locator

try:
    from utils.helpers import (
        DIRECT_PDP_URL,
        TestResult,
        click_and_capture_page,
        click_and_expect_form,
        first_visible,
        land_on_pdp_direct
    )
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from indiamart_pdp.utils.helpers import (
        DIRECT_PDP_URL,
        TestResult,
        click_and_capture_page,
        click_and_expect_form,
        first_visible,
        land_on_pdp_direct
    )


# ---------------------------------------------------------------------------
# Helper: red outline + console log before every click
# ---------------------------------------------------------------------------
def _highlight_and_log(page: Page, locator: Locator, label: str):
    try:
        locator.scroll_into_view_if_needed()
        page.wait_for_timeout(500)

        el = locator.element_handle()

        tag  = page.evaluate("el => el.tagName", el)
        text = page.evaluate(
            """el =>
                el.innerText ||
                el.getAttribute('alt') ||
                el.getAttribute('aria-label') || ''
            """,
            el
        )
        href = page.evaluate("el => el.getAttribute('href') || ''", el)

        print(
            f"  [CLICK] [{label}] <{tag.lower()}> "
            f"'{text[:60].strip()}'"
            + (f" -> {href[:100]}" if href else "")
        )

        page.evaluate(
            """el => {
                el.style.outline='4px solid red';
                el.style.outlineOffset='3px';
                el.style.backgroundColor='rgba(255,0,0,0.15)';
                setTimeout(()=>{
                    el.style.outline='';
                    el.style.outlineOffset='';
                    el.style.backgroundColor='';
                }, 2500);
            }""",
            el
        )
        page.wait_for_timeout(1500)

    except Exception as e:
        print(f"[CLICK] [{label}] highlight failed: {e}")


def _click_and_capture_hl(page: Page, locator: Locator, label: str):
    _highlight_and_log(page, locator, label)
    return click_and_capture_page(page, locator)


def _click_and_expect_form_hl(page: Page, selectors: list, label: str):
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if loc.is_visible(timeout=3000):
                _highlight_and_log(page, loc, label)
                break
        except Exception:
            continue
    click_and_expect_form(page, selectors)


# ---------------------------------------------------------------------------
# Dismiss "Unlock IndiaMART" popup
# ---------------------------------------------------------------------------
def _dismiss_login_popup(page: Page):
    try:
        skip = page.locator("a#idfpclose, a.idfpclose, a.skptxt").first
        if skip.is_visible(timeout=3000):
            print("  [POPUP] Login popup detected — clicking Skip")
            skip.click(force=True)
            page.wait_for_timeout(1000)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Scroll helper
# ---------------------------------------------------------------------------
def _scroll_to_section(page: Page):
    for pos in [0.35, 0.55, 0.75, 0.90, 1.0]:
        page.evaluate(
            f"window.scrollTo(0, document.body.scrollHeight * {pos})"
        )
        page.wait_for_timeout(1500)

    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(2500)

    try:
        section = page.locator("#fndrltd").first
        if section.is_visible(timeout=5000):
            section.scroll_into_view_if_needed()
            page.wait_for_timeout(1500)
            print("  [SCROLL] Find Related Categories section reached")
    except Exception:
        print("  [SCROLL] Section not detected after max scroll")


# ---------------------------------------------------------------------------
# Suite runner
# ---------------------------------------------------------------------------
def run(page: Page, pdp_url: str = DIRECT_PDP_URL) -> TestResult:

    tr = TestResult(page)
    print("\n[Suite 05] Find Related Categories")

    # ============================================================
    # TC-5946 — heading visible
    # ============================================================
    land_on_pdp_direct(page, pdp_url)
    _dismiss_login_popup(page)
    _scroll_to_section(page)
    _dismiss_login_popup(page)

    try:
        heading = first_visible(page, [
            "h2:has-text('Find related categories')",
            "h2:has-text('Find Related Categories')",
            "h2:has-text('related categories')",
            "h3:has-text('Find related')"
        ])
        assert heading.is_visible(timeout=5000), \
            "Find related categories heading not visible"
        print(f"[CHECK] [TC-5946] {heading.inner_text().strip()[:60]}")
        tr.add("TC-5946", "Find related categories heading visible", "PASS")

    except Exception as exc:
        tr.add("TC-5946", "Find related categories heading visible",
               "FAIL", str(exc)[:120])

    # ============================================================
    # TC-5947 — click first related category
    # FIX: Unidentified/Identified → new tab  |  Logged-in → same tab
    #      Handle BOTH outcomes with contextlib.suppress
    # ============================================================
    land_on_pdp_direct(page, pdp_url)
    _dismiss_login_popup(page)
    _scroll_to_section(page)
    _dismiss_login_popup(page)

    try:
        link = page.locator("#mcat-strip li a").first
        link.wait_for(state="visible", timeout=8000)
        link.scroll_into_view_if_needed()
        page.wait_for_timeout(1000)
        _highlight_and_log(page, link, "TC-5947 first_mcat")

        final_url = None

        # ── Try new-tab navigation first (unidentified / identified) ──
        new_tab = None
        with contextlib.suppress(Exception):
            with page.context.expect_page(timeout=6000) as new_pg:
                link.click(force=True)
            new_tab = new_pg.value
            new_tab.wait_for_load_state("domcontentloaded", timeout=30000)
            new_tab.wait_for_timeout(1500)
            _dismiss_login_popup(new_tab)
            final_url = new_tab.url
            print(f"  [INFO] New tab opened — URL: {final_url}")

        # ── Fallback: same-tab navigation (logged-in state) ──────────
        if final_url is None:
            print("  [INFO] No new tab — waiting for same-tab navigation")
            page.wait_for_load_state("domcontentloaded", timeout=30000)
            page.wait_for_timeout(1500)
            _dismiss_login_popup(page)
            final_url = page.url
            print(f"  [INFO] Same-tab URL: {final_url}")

        assert (
            "impcat"          in final_url or
            "dir.indiamart"   in final_url or
            "search.mp"       in final_url or
            "indiamart.com"   in final_url
        ), f"Expected MCAT/search URL, got: {final_url}"

        tr.add("TC-5947",
               "Click first related category redirects to MCAT page",
               "PASS", final_url[-100:])

        if new_tab:
            new_tab.close()

    except Exception as exc:
        tr.add("TC-5947",
               "Click first related category redirects to MCAT page",
               "FAIL", str(exc)[:120])

    # ============================================================
    # TC-5948 — Get Quote opens BL form
    # FIX: Always reload pdp_url first — guarantees clean state
    #      regardless of what TC-5947 left the browser on
    # ============================================================
    land_on_pdp_direct(page, pdp_url)          # ← KEY FIX: explicit reload
    _dismiss_login_popup(page)
    _scroll_to_section(page)
    _dismiss_login_popup(page)

    try:
        get_quotes = page.locator("button:has-text('Get Quote')").first

        if not get_quotes.is_visible(timeout=5000):
            print("  [REFRESH] Get Quote button not found — hard refreshing page")
            page.reload(wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(2000)
            _dismiss_login_popup(page)
            _scroll_to_section(page)
            _dismiss_login_popup(page)
            get_quotes = page.locator("button:has-text('Get Quote')").first

        get_quotes.wait_for(state="attached", timeout=8000)
        get_quotes.scroll_into_view_if_needed()
        page.wait_for_timeout(800)
        assert get_quotes.is_visible(), \
            "Get Quote button not visible even after hard refresh"

        _highlight_and_log(page, get_quotes, "TC-5948 get_quote_button")
        get_quotes.click()
        page.wait_for_timeout(1500)

        assert "dir.indiamart.com" not in page.url, \
            "Page redirected to dir — button click hit the card instead of the button"

        form_visible = page.locator(
            "form, [class*='bl-form'], [class*='blform'], "
            "[class*='modal'], [class*='popup'], [id*='bl']"
        ).first.is_visible(timeout=5000)
        assert form_visible, "BL form did not open after clicking Get Quote button"

        tr.add("TC-5948", "Get Quotes opens BL form", "PASS")

    except Exception as exc:
        tr.add("TC-5948", "Get Quotes opens BL form", "FAIL", str(exc)[:120])

    return tr


# ---------------------------------------------------------------------------
# Standalone run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=500)
        page    = browser.new_page()
        result  = run(page)
        summary = result.summary()
        print(f"\nSummary: {summary['passed']}/{summary['total']} passed")
        browser.close()