"""
Suite 10: Get Quotes from Verified Suppliers
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
    print("\n[Suite 10] Get Quotes from Verified Suppliers")

    land_on_pdp_direct(page, DIRECT_PDP_URL)

    try:
        click_and_expect_form(page, [SEL["get_best_price"], SEL["submit_requirement"]])
        field = first_visible(page, [SEL["product_input"]])
        value = field.input_value() if hasattr(field, "input_value") else ""
        text = value or field.get_attribute("value") or field.inner_text()
        assert "tmt" in text.lower() or len(text.strip()) > 0, "Product name is not prefilled"
        tr.add("TC-5957", "Product name is prefilled in enquiry text box", "PASS", text[:50])
    except Exception as exc:
        tr.add("TC-5957", "Product name is prefilled in enquiry text box", "FAIL", str(exc)[:120])

    land_on_pdp_direct(page, DIRECT_PDP_URL)
    try:
        click_and_expect_form(page, [SEL["submit_requirement"], SEL["get_best_price"]])
        tr.add("TC-5958", "Clicking Submit Requirement opens BL form", "PASS")
    except Exception as exc:
        tr.add("TC-5958", "Clicking Submit Requirement opens BL form", "FAIL", str(exc)[:120])

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
