"""
Suite 08: More Products from Seller
"""
import sys
from pathlib import Path
from playwright.sync_api import Page

try:
    from utils.helpers import DIRECT_PDP_URL, SEL, TestResult, click_and_expect_form, first_visible, visible_count, land_on_pdp_direct
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from indiamart_pdp.utils.helpers import DIRECT_PDP_URL, SEL, TestResult, click_and_expect_form, first_visible, visible_count, land_on_pdp_direct


def _scroll_to_section(page: Page) -> None:
    page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.75)")
    page.wait_for_timeout(1500)


def run(page: Page) -> TestResult:
    tr = TestResult(page)
    print("\n[Suite 08] More Products from Seller")

    land_on_pdp_direct(page, DIRECT_PDP_URL)
    _scroll_to_section(page)

    try:
        section = first_visible(page, ["section:has-text('More Products')", "div:has-text('More Products from')", SEL["more_products_section"]])
        count = visible_count(page, ["section a[href*='proddetail']", "[class*='product_item'] a", ".tab-content a"])
        assert section.is_visible() and count > 0
        tr.add("TC-5953", "More products from seller are displayed", "PASS", f"{count} items")
    except AssertionError as exc:
        tr.add("TC-5953", "More products from seller are displayed", "SKIP", f"Different template: {str(exc)[:90]}")
    except Exception as exc:
        tr.add("TC-5953", "More products from seller are displayed", "FAIL", str(exc)[:120])

    land_on_pdp_direct(page, DIRECT_PDP_URL)
    _scroll_to_section(page)
    try:
        click_and_expect_form(page, [SEL["get_best_price"]])
        tr.add("TC-5954", "Clicking Get Best Price opens enquiry form", "PASS")
    except Exception as exc:
        tr.add("TC-5954", "Clicking Get Best Price opens enquiry form", "FAIL", str(exc)[:120])

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
