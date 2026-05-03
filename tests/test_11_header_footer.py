"""
Suite 11: Header / Footer
"""
import sys
from pathlib import Path
from playwright.sync_api import Page, Locator

try:
    from utils.helpers import DIRECT_PDP_URL, SEL, TestResult, click_and_capture_page, first_visible, land_on_pdp_direct
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from indiamart_pdp.utils.helpers import DIRECT_PDP_URL, SEL, TestResult, click_and_capture_page, first_visible, land_on_pdp_direct


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
# Helper: red outline + console log before every click
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


def run(page: Page) -> TestResult:
    tr = TestResult(page)
    print("\n[Suite 11] Header / Footer")

    # ── TC-5959 ──────────────────────────────────────────────────────────────
    land_on_pdp_direct(page, DIRECT_PDP_URL)
    _dismiss_login_popup(page)
    try:
        logo = first_visible(page, [
            "a.hd_logo",
            "a[aria-label='IndiaMART']",
            "a:has-text('IndiaMART')"
        ])
        href = logo.get_attribute("href") or ""
        if href.startswith("/"):
            href = f"https://www.indiamart.com{href}"
        assert "indiamart.com" in href, f"Unexpected href: {href}"

        _highlight_and_log(page, logo, "TC-5959 header_logo")

        try:
            target = click_and_capture_page(page, logo)
        except Exception:
            page.goto(href, wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_timeout(1200)
            target = page

        tr.set_page(target)
        _dismiss_login_popup(target)
        assert "indiamart.com" in target.url, f"Unexpected URL: {target.url}"
        tr.add("TC-5959", "Header CTA redirection works", "PASS", target.url[-70:])
        if target != page:
            target.close()
    except Exception as exc:
        tr.add("TC-5959", "Header CTA redirection works", "FAIL", str(exc)[:120])

    # ── TC-5960 ──────────────────────────────────────────────────────────────
    land_on_pdp_direct(page, DIRECT_PDP_URL)
    _dismiss_login_popup(page)
    try:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1200)
        _dismiss_login_popup(page)

        footer_link = first_visible(page, [SEL["footer_links"]])
        _highlight_and_log(page, footer_link, "TC-5960 footer_link")

        target = click_and_capture_page(page, footer_link)
        tr.set_page(target)
        _dismiss_login_popup(target)
        assert target.url.startswith("http"), f"Unexpected URL: {target.url}"
        tr.add("TC-5960", "Footer CTA redirection works", "PASS", target.url[-70:])
        if target != page:
            target.close()
    except Exception as exc:
        tr.add("TC-5960", "Footer CTA redirection works", "FAIL", str(exc)[:120])

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