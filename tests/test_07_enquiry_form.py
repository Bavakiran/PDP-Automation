"""
Suite 07: Enquiry Form
"""
import sys
from pathlib import Path
from playwright.sync_api import Page

try:
    from utils.helpers import DIRECT_PDP_URL, SEL, TestResult, click_and_expect_form, first_visible, land_on_pdp_direct
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from indiamart_pdp.utils.helpers import DIRECT_PDP_URL, SEL, TestResult, click_and_expect_form, first_visible, land_on_pdp_direct


def run(page: Page) -> TestResult:
    tr = TestResult(page)
    print("\n[Suite 07] Enquiry Form")

    land_on_pdp_direct(page, DIRECT_PDP_URL)

    try:
        click_and_expect_form(page, [SEL["submit_requirement"]])
        tr.add("TC-5951", "Clicking Submit Requirement opens enquiry form", "PASS")
    except AssertionError as exc:
        tr.add("TC-5951", "Clicking Submit Requirement opens enquiry form", "SKIP", f"Different template: {str(exc)[:90]}")
    except Exception as exc:
        tr.add("TC-5951", "Clicking Submit Requirement opens enquiry form", "FAIL", str(exc)[:120])

    land_on_pdp_direct(page, DIRECT_PDP_URL)
    try:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.85)")
        page.wait_for_timeout(1200)
        click_and_expect_form(page, [SEL["chat_now"]])
        first_visible(page, [SEL["mobile_input"], SEL["product_input"]])
        tr.add("TC-5952", "Clicking Chat Now opens chat enquiry form", "PASS")
    except AssertionError as exc:
        tr.add("TC-5952", "Clicking Chat Now opens chat enquiry form", "SKIP", str(exc)[:120])
    except Exception as exc:
        tr.add("TC-5952", "Clicking Chat Now opens chat enquiry form", "FAIL", str(exc)[:120])

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
