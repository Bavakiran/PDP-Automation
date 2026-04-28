"""
Suite 05: Find Related Categories
"""
import sys
from pathlib import Path
from playwright.sync_api import Page

try:
    from utils.helpers import DIRECT_PDP_URL, TestResult, click_and_capture_page, click_and_expect_form, first_visible, land_on_pdp_direct
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from indiamart_pdp.utils.helpers import DIRECT_PDP_URL, TestResult, click_and_capture_page, click_and_expect_form, first_visible, land_on_pdp_direct


def _scroll_to_section(page: Page) -> None:
    page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.65)")
    page.wait_for_timeout(1500)


def run(page: Page) -> TestResult:
    tr = TestResult(page)
    print("\n[Suite 05] Find Related Categories")

    land_on_pdp_direct(page, DIRECT_PDP_URL)
    _scroll_to_section(page)

    try:
        heading = first_visible(page, ["h2:has-text('Related')", "h2:has-text('Categorie')", "h3:has-text('Related')"])
        links = page.locator("a[href*='dir.indiamart.com'], a[href*='search.mp'], a[href*='.html']")
        assert heading.is_visible() and links.count() > 0
        tr.add("TC-5946", "Related categories section displays category links", "PASS", f"{links.count()} links")
    except Exception as exc:
        tr.add("TC-5946", "Related categories section displays category links", "FAIL", str(exc)[:120])

    land_on_pdp_direct(page, DIRECT_PDP_URL)
    _scroll_to_section(page)
    try:
        target = click_and_capture_page(page, first_visible(page, ["a[href*='dir.indiamart.com']", "a[href*='search.mp']", "a[href*='.html']"]))
        tr.set_page(target)
        assert "dir.indiamart.com" in target.url or "search.mp" in target.url, f"Unexpected URL: {target.url}"
        tr.add("TC-5947", "Clicking category title redirects to MCAT/Search page", "PASS", target.url[-70:])
        if target != page:
            target.close()
    except Exception as exc:
        tr.add("TC-5947", "Clicking category title redirects to MCAT/Search page", "FAIL", str(exc)[:120])

    land_on_pdp_direct(page, DIRECT_PDP_URL)
    _scroll_to_section(page)
    try:
        click_and_expect_form(page, ["button:has-text('Get Quotes')", "a:has-text('Get Quotes')", "button:has-text('Get Best Price')", "a:has-text('Get Best Price')"])
        tr.add("TC-5948", "Clicking Get Quotes opens BL form", "PASS")
    except Exception as exc:
        tr.add("TC-5948", "Clicking Get Quotes opens BL form", "FAIL", str(exc)[:120])

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
