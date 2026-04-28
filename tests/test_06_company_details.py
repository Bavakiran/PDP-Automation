"""
Suite 06: Company Details
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
    print("\n[Suite 06] Company Details")

    land_on_pdp_direct(page, DIRECT_PDP_URL)

    try:
        section = first_visible(page, [SEL["company_section"], SEL["company_link"]])
        text = section.inner_text()
        assert len(text.strip()) > 0
        tr.add("TC-5949", "Company details are displayed", "PASS", text[:60].replace("\n", " "))
    except Exception as exc:
        tr.add("TC-5949", "Company details are displayed", "FAIL", str(exc)[:120])

    land_on_pdp_direct(page, DIRECT_PDP_URL)
    try:
        click_and_expect_form(page, [SEL["contact_supplier"]])
        tr.add("TC-5950", "Clicking Contact Seller opens enquiry form", "PASS")
    except Exception as exc:
        tr.add("TC-5950", "Clicking Contact Seller opens enquiry form", "FAIL", str(exc)[:120])

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
