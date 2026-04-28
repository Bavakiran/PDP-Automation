"""
Suite 11: Header / Footer
"""
import sys
from pathlib import Path
from playwright.sync_api import Page

try:
    from utils.helpers import DIRECT_PDP_URL, SEL, TestResult, click_and_capture_page, first_visible, land_on_pdp_direct
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from indiamart_pdp.utils.helpers import DIRECT_PDP_URL, SEL, TestResult, click_and_capture_page, first_visible, land_on_pdp_direct


def run(page: Page) -> TestResult:
    tr = TestResult(page)
    print("\n[Suite 11] Header / Footer")

    land_on_pdp_direct(page, DIRECT_PDP_URL)

    try:
        logo = first_visible(page, ["a.hd_logo", "a[aria-label='IndiaMART']", "a:has-text('IndiaMART')"])
        href = logo.get_attribute("href") or ""
        if href.startswith("/"):
            href = f"https://www.indiamart.com{href}"
        assert "indiamart.com" in href, f"Unexpected href: {href}"
        try:
            target = click_and_capture_page(page, logo)
        except Exception:
            page.goto(href, wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_timeout(1200)
            target = page
        tr.set_page(target)
        assert "indiamart.com" in target.url, f"Unexpected URL: {target.url}"
        tr.add("TC-5959", "Header CTA redirection works", "PASS", target.url[-70:])
        if target != page:
            target.close()
    except Exception as exc:
        tr.add("TC-5959", "Header CTA redirection works", "FAIL", str(exc)[:120])

    land_on_pdp_direct(page, DIRECT_PDP_URL)
    try:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1200)
        target = click_and_capture_page(page, first_visible(page, [SEL["footer_links"]]))
        tr.set_page(target)
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
