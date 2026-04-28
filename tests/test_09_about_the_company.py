"""
Suite 09: About the Company
"""
import sys
from pathlib import Path
from playwright.sync_api import Page

try:
    from utils.helpers import DIRECT_PDP_URL, SEL, TestResult, first_visible, land_on_pdp_direct
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from indiamart_pdp.utils.helpers import DIRECT_PDP_URL, SEL, TestResult, first_visible, land_on_pdp_direct


def _scroll_to_section(page: Page) -> None:
    page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.82)")
    page.wait_for_timeout(1500)


def run(page: Page) -> TestResult:
    tr = TestResult(page)
    print("\n[Suite 09] About the Company")

    land_on_pdp_direct(page, DIRECT_PDP_URL)
    _scroll_to_section(page)

    try:
        section = first_visible(page, ["section:has-text('About the Company')", "div:has-text('About the Company')", "[class*='about']"])
        assert len(section.inner_text().strip()) > 0
        tr.add("TC-5955", "About the company details are displayed", "PASS")
    except Exception as exc:
        tr.add("TC-5955", "About the company details are displayed", "FAIL", str(exc)[:120])

    land_on_pdp_direct(page, DIRECT_PDP_URL)
    _scroll_to_section(page)
    try:
        ratings = first_visible(page, [SEL["rating_summary"], "text=/review|rating/i"])
        assert ratings.is_visible()
        tr.add("TC-5956", "Ratings and reviews are displayed", "PASS", ratings.inner_text()[:50].replace("\n", " "))
    except Exception as exc:
        tr.add("TC-5956", "Ratings and reviews are displayed", "FAIL", str(exc)[:120])

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
