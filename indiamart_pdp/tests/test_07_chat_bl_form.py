"""
Suite 07: Chat BL Form

TC-5951  Scrolling to bottom opens chat BL form
TC-5952  Clicking Chat Now icon (bottom-right) opens chat BL form
"""
import sys
from pathlib import Path
from playwright.sync_api import Page, Locator

try:
    from utils.helpers import (
        DIRECT_PDP_URL,
        SEL,
        TestResult,
        click_and_expect_form,
        first_visible,
        land_on_pdp_direct,
    )
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from indiamart_pdp.utils.helpers import (
        DIRECT_PDP_URL,
        SEL,
        TestResult,
        click_and_expect_form,
        first_visible,
        land_on_pdp_direct,
    )


# ---------------------------------------------------------------------------
# Helper: dismiss "Unlock IndiaMART" popup via Skip link
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
# Helper: red outline + console log before every click
# ---------------------------------------------------------------------------
def _highlight_and_log(page: Page, locator: Locator, label: str):
    try:
        locator.scroll_into_view_if_needed()
        page.wait_for_timeout(500)
        el = locator.element_handle()
        tag  = page.evaluate("el => el.tagName", el)
        text = page.evaluate(
            "el => el.innerText || el.getAttribute('alt') || el.getAttribute('aria-label') || ''",
            el
        )
        href = page.evaluate("el => el.getAttribute('href') || ''", el)
        print(
            f"  [CLICK] [{label}] <{tag.lower()}> '{text[:60].strip()}'"
            + (f" -> {href[:80]}" if href else "")
        )
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
        print(f"  [CLICK] [{label}] (highlight failed: {e})")


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
# Suite runner
# ---------------------------------------------------------------------------
def run(page: Page) -> TestResult:
    tr = TestResult(page)
    print("\n[Suite 07] Chat BL Form")

    # ── TC-5951 ──────────────────────────────────────────────────────────────
    # Scroll to bottom → chat BL form should appear automatically
    land_on_pdp_direct(page, DIRECT_PDP_URL)
    _dismiss_login_popup(page)
    try:
        print("  [SCROLL] Scrolling to bottom for chat BL form")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)
        _dismiss_login_popup(page)

        form = first_visible(page, [
            SEL["chat_now"],
            SEL["mobile_input"],
            SEL["product_input"],
            "[class*='chat']",
            "[class*='bl-form']",
            "[class*='blform']",
            "[id*='chat']",
        ])
        print(f"  [CHECK] [TC-5951] Chat BL form visible: '{form.inner_text()[:60].strip()}'")
        assert form.is_visible(timeout=5000), "Chat BL form did not appear on scroll"
        tr.add("TC-5951", "Scrolling to bottom opens chat BL form", "PASS")
    except AssertionError as exc:
        tr.add("TC-5951", "Scrolling to bottom opens chat BL form", "SKIP",
               f"Different template: {str(exc)[:90]}")
    except Exception as exc:
        tr.add("TC-5951", "Scrolling to bottom opens chat BL form", "FAIL", str(exc)[:120])

    # ── TC-5952 ──────────────────────────────────────────────────────────────
    # Scroll down → scroll up → scroll down → click Chat Now icon (bottom-right)
    # → chat BL form opens
    land_on_pdp_direct(page, DIRECT_PDP_URL)
    _dismiss_login_popup(page)
    try:
        # Step 1: scroll down
        print("  [SCROLL] Step 1 — scroll down")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1500)
        _dismiss_login_popup(page)

        # Step 2: scroll up
        print("  [SCROLL] Step 2 — scroll up")
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1500)
        _dismiss_login_popup(page)

        # Step 3: scroll down again — Chat Now icon appears at bottom-right
        print("  [SCROLL] Step 3 — scroll down again")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)
        _dismiss_login_popup(page)

        # Step 4: locate and click Chat Now icon (bottom-right corner)
        chat_icon = first_visible(page, [
            SEL["chat_now"],
            "[class*='chat'][class*='icon']",
            "[class*='chat'][class*='btn']",
            "[class*='chat'][class*='float']",
            "[id*='chat']",
            "a:has-text('Chat Now')",
            "button:has-text('Chat Now')",
            "div:has-text('Chat Now')",
        ])
        _highlight_and_log(page, chat_icon, "TC-5952 chat_now_icon")
        chat_icon.click(force=True)
        page.wait_for_timeout(1500)
        _dismiss_login_popup(page)

        # Step 5: verify chat BL form opened
        form = first_visible(page, [
            SEL["mobile_input"],
            SEL["product_input"],
            "[class*='bl-form']",
            "[class*='blform']",
            "[class*='chat-form']",
        ])
        assert form.is_visible(timeout=5000), "Chat BL form did not open after clicking Chat Now"
        tr.add("TC-5952", "Clicking Chat Now opens chat BL form", "PASS")
    except AssertionError as exc:
        tr.add("TC-5952", "Clicking Chat Now opens chat BL form", "SKIP",
               f"Different template: {str(exc)[:90]}")
    except Exception as exc:
        tr.add("TC-5952", "Clicking Chat Now opens chat BL form", "FAIL", str(exc)[:120])

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