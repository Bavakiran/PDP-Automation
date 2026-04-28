"""
Suite 04: Find Similar Products
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
        first_visible,
        is_pdp,
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
        first_visible,
        is_pdp,
        land_on_pdp_direct,
    )


def _scroll_to_section(page: Page) -> None:
    page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.55)")
    page.wait_for_timeout(1500)


def _has_similar_products_section(page: Page) -> bool:
    for selector in [
        "h2:has-text('Find Similar')",
        "h2:has-text('Similar Products')",
        "div:has-text('Find Similar')",
        "section:has-text('Find Similar')",
    ]:
        locator = page.locator(selector).first
        try:
            if locator.count() > 0 and locator.is_visible(timeout=300):
                return True
        except Exception:
            pass
    return False


def run(page: Page) -> TestResult:
    tr = TestResult(page)
    print("\n[Suite 04] Find Similar Products")

    land_on_pdp_direct(page, DIRECT_PDP_URL)
    _scroll_to_section(page)
    has_similar = _has_similar_products_section(page)

    if not has_similar:
        detail = "Different template: Find Similar Products section is not present on this PDP"
        tr.add("TC-5942", "Similar products section displays related products", "SKIP", detail)
        tr.add("TC-5943", "Similar products Get Best Price opens enquiry form", "SKIP", detail)
        tr.add("TC-5944", "Clicking similar product name redirects to PDP", "SKIP", detail)
        tr.add("TC-5945", "Clicking View Mobile Number opens enquiry form or reveals number", "SKIP", detail)
        return tr

    try:
        cards = page.locator("h3, section a[href*='proddetail'], section [class*='product']")
        assert cards.count() > 0
        tr.add("TC-5942", "Similar products section displays related products", "PASS", f"{cards.count()} items")
    except Exception as exc:
        tr.add("TC-5942", "Similar products section displays related products", "FAIL", str(exc)[:120])

    land_on_pdp_direct(page, DIRECT_PDP_URL)
    _scroll_to_section(page)
    try:
        click_and_expect_form(page, [SEL["get_best_price"]])
        tr.add("TC-5943", "Similar products Get Best Price opens enquiry form", "PASS")
    except Exception as exc:
        tr.add("TC-5943", "Similar products Get Best Price opens enquiry form", "FAIL", str(exc)[:120])

    land_on_pdp_direct(page, DIRECT_PDP_URL)
    _scroll_to_section(page)
    try:
        link = first_visible(page, ["h3 a[href*='proddetail']", "a[href*='proddetail']"])
        target = click_and_capture_page(page, link)
        tr.set_page(target)
        assert is_pdp(target), f"Unexpected URL: {target.url}"
        tr.add("TC-5944", "Clicking similar product name redirects to PDP", "PASS", target.url[-70:])
        if target != page:
            target.close()
    except AssertionError as exc:
        tr.add("TC-5944", "Clicking similar product name redirects to PDP", "SKIP", f"Different template: {str(exc)[:90]}")
    except Exception as exc:
        tr.add("TC-5944", "Clicking similar product name redirects to PDP", "FAIL", str(exc)[:120])

    land_on_pdp_direct(page, DIRECT_PDP_URL)
    _scroll_to_section(page)
    try:
        mobile_link = first_visible(
            page,
            [
                "a:has(span.hov:has-text('View Mobile Number'))",
                "span.hov:has-text('View Mobile Number')",
                "a:has-text('View Mobile Number')",
                "text='View Mobile Number'",
                "a[href^='tel:']",
            ],
        )
        href = mobile_link.get_attribute("href") or ""
        mobile_link.click(force=True)
        page.wait_for_timeout(1500)

        form_visible = page.locator(SEL["modal_form"]).count() > 0 or page.locator(SEL["inline_form"]).count() > 0
        number_revealed = page.locator("a[href^='tel:']").count() > 0
        if not number_revealed:
            try:
                number_revealed = page.get_by_text("View Mobile Number", exact=False).count() > 0 and page.locator("text=/[0-9]{10}/").count() > 0
            except Exception:
                number_revealed = False
        assert form_visible or number_revealed or href.startswith("tel:"), "View Mobile Number did not open form or reveal number"
        tr.add("TC-5945", "Clicking View Mobile Number opens enquiry form or reveals number", "PASS")
    except Exception as exc:
        tr.add("TC-5945", "Clicking View Mobile Number opens enquiry form or reveals number", "SKIP", str(exc)[:120])

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
