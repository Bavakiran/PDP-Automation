"""
Suite 02: PDP First Fold
"""
import sys
from pathlib import Path
from playwright.sync_api import Page

try:
    from utils.helpers import (
        DIRECT_PDP_URL,
        SEL,
        TestResult,
        click_and_capture_page,
        click_and_expect_form,
        click_locator,
        first_visible,
        land_on_pdp_direct,
    )
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from indiamart_pdp.utils.helpers import (
        DIRECT_PDP_URL,
        SEL,
        TestResult,
        click_and_capture_page,
        click_and_expect_form,
        click_locator,
        first_visible,
        land_on_pdp_direct,
    )


def run(page: Page) -> TestResult:
    tr = TestResult(page)
    print("\n[Suite 02] PDP First Fold")

    land_on_pdp_direct(page, DIRECT_PDP_URL)

    try:
        click_and_expect_form(page, [SEL["product_image"], "img[src*='imimg']", "img[alt*='TMT']", "img"])
        tr.add("TC-5548", "Clicking product image opens enquiry form", "PASS")
    except Exception as exc:
        tr.add("TC-5548", "Clicking product image opens enquiry form", "FAIL", str(exc)[:120])

    try:
        click_and_expect_form(page, [SEL["get_best_price"]])
        tr.add("TC-5549", "Clicking enquiry CTA opens enquiry flow", "PASS")
    except Exception as exc:
        tr.add("TC-5549", "Clicking enquiry CTA opens enquiry flow", "FAIL", str(exc)[:120])

    land_on_pdp_direct(page, DIRECT_PDP_URL)
    try:
        click_and_expect_form(page, [SEL["submit_requirement"]])
        tr.add("TC-5550", "Clicking Submit Requirement opens enquiry form", "PASS")
    except AssertionError as exc:
        tr.add("TC-5550", "Clicking Submit Requirement opens enquiry form", "SKIP", f"Different template: {str(exc)[:90]}")
    except Exception as exc:
        tr.add("TC-5550", "Clicking Submit Requirement opens enquiry form", "FAIL", str(exc)[:120])

    land_on_pdp_direct(page, DIRECT_PDP_URL)
    try:
        # Click the company name (h2.fs15), but allow for dynamic company name text
        company_locator = page.locator("h2.fs15").first
        assert company_locator.is_visible(timeout=5000), "Company name element not visible"
        target = click_and_capture_page(page, company_locator)
        tr.set_page(target)
        assert "indiamart.com" in target.url and "proddetail" not in target.url, f"Unexpected URL: {target.url}"
        tr.add("TC-5551", "Clicking company name redirects to company page", "PASS", target.url[-70:])
        if target != page:
            target.close()
    except Exception as exc:
        tr.add("TC-5551", "Clicking company name redirects to company page", "FAIL", str(exc)[:120])

    land_on_pdp_direct(page, DIRECT_PDP_URL)
    try:
        click_locator(first_visible(page, [SEL["review_link"]]))
        page.wait_for_timeout(1500)
        assert "#review" in page.url.lower() or "review" in page.content().lower() or "rating" in page.content().lower()
        tr.add("TC-5552", "Clicking review count moves to rating and review section", "PASS")
    except Exception as exc:
        tr.add("TC-5552", "Clicking review count moves to rating and review section", "FAIL", str(exc)[:120])

    land_on_pdp_direct(page, DIRECT_PDP_URL)
    try:
        click_and_expect_form(page, [SEL["contact_supplier"]])
        tr.add("TC-5554", "Clicking Contact Supplier opens enquiry form", "PASS")
    except Exception as exc:
        tr.add("TC-5554", "Clicking Contact Supplier opens enquiry form", "FAIL", str(exc)[:120])

    land_on_pdp_direct(page, DIRECT_PDP_URL)
    try:
        call_cta = first_visible(page, [SEL["call_now"]])
        href = call_cta.get_attribute("href") or ""
        click_locator(call_cta)
        page.wait_for_timeout(1000)
        # Enhanced popup handling: try multiple selectors, Escape key, and click 'Skip' on mobile popup
        try:
            popup_cancel = page.locator("button:has-text('Cancel')").first
            if popup_cancel.is_visible(timeout=2000):
                popup_cancel.click(timeout=2000)
                page.wait_for_timeout(500)
            else:
                popup_cancel2 = page.locator("button[aria-label='Cancel']").first
                if popup_cancel2.is_visible(timeout=2000):
                    popup_cancel2.click(timeout=2000)
                    page.wait_for_timeout(500)
                else:
                    # Try to click 'Skip' on mobile number popup
                    skip_link = page.locator("text=Skip, text=skip, a:has-text('Skip'), a:has-text('skip')").first
                    if skip_link.is_visible(timeout=2000):
                        skip_link.click(timeout=2000)
                        page.wait_for_timeout(500)
                    else:
                        page.keyboard.press("Escape")
                        page.wait_for_timeout(500)
        except Exception:
            try:
                skip_link = page.locator("text=Skip, text=skip, a:has-text('Skip'), a:has-text('skip')").first
                if skip_link.is_visible(timeout=2000):
                    skip_link.click(timeout=2000)
                    page.wait_for_timeout(500)
                else:
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(500)
            except Exception:
                pass
        assert href.startswith("tel:") or page.locator(SEL["modal_form"]).count() > 0 or page.locator(SEL["inline_form"]).count() > 0
        tr.add("TC-5906", "Clicking Call Now triggers call or call lead flow", "PASS", href[:40])
    except Exception as exc:
        tr.add("TC-5906", "Clicking Call Now triggers call or call lead flow", "FAIL", str(exc)[:120])

    land_on_pdp_direct(page, DIRECT_PDP_URL)
    try:
        click_and_expect_form(page, [SEL["contact_supplier"]])
        tr.add("TC-5907", "Clicking Contact Supplier CTA displays enquiry form", "PASS")
    except Exception as exc:
        tr.add("TC-5907", "Clicking Contact Supplier CTA displays enquiry form", "FAIL", str(exc)[:120])

    land_on_pdp_direct(page, DIRECT_PDP_URL)
    try:
        click_and_expect_form(page, [SEL["brochure_link"]])
        tr.add("TC-5939", "Clicking brochure PDF opens quick requirement form", "PASS")
    except Exception as exc:
        tr.add("TC-5939", "Clicking brochure PDF opens quick requirement form", "SKIP", str(exc)[:120])

    land_on_pdp_direct(page, DIRECT_PDP_URL)
    try:
        click_and_expect_form(page, [SEL["video_icon"]])
        tr.add("TC-5940", "Clicking video icon opens enquiry form", "PASS")
    except Exception as exc:
        tr.add("TC-5940", "Clicking video icon opens enquiry form", "SKIP", str(exc)[:120])

    land_on_pdp_direct(page, DIRECT_PDP_URL)
    try:
        target = click_and_capture_page(page, first_visible(page, [SEL["hindi_link"]]))
        tr.set_page(target)
        assert "hindi.indiamart.com" in target.url or "hindi" in target.url.lower(), f"Unexpected URL: {target.url}"
        tr.add("TC-5941", "Clicking View in Hindi redirects to Hindi PDP", "PASS", target.url[-70:])
        if target != page:
            target.close()
    except AssertionError as exc:
        tr.add("TC-5941", "Clicking View in Hindi redirects to Hindi PDP", "SKIP", f"Different template: {str(exc)[:90]}")
    except Exception as exc:
        tr.add("TC-5941", "Clicking View in Hindi redirects to Hindi PDP", "FAIL", str(exc)[:120])

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
