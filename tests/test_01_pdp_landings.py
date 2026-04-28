"""
Suite 01: PDP Landings

TC-5543  Landing via Search Results Page
TC-5546  Landing via MCAT Page
TC-5547  Landing via Company Page
TC-5989  Landing via Homepage (recently viewed)
"""

import sys
from pathlib import Path
from playwright.sync_api import Page

try:
    from utils.helpers import TestResult
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from indiamart_pdp.utils.helpers import TestResult


SEARCH_URL = "https://dir.indiamart.com"


# -----------------------------------------------------------
# Shared: reload if popup/overlay detected
# -----------------------------------------------------------
def _hard_refresh_if_popup(page: Page):
    try:
        overlay = page.locator(
            "div[class*='popup'], div[class*='modal'], "
            "div[class*='overlay'], div[id*='popup'], "
            "div[id*='modal'], div[class*='dialog']"
        )
        if overlay.first.is_visible(timeout=2000):
            page.reload(wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(2000)
    except Exception:
        pass


# -----------------------------------------------------------
# Shared: navigate to dir.indiamart.com, type keyword, Enter
# -----------------------------------------------------------
def _search_and_enter(page: Page, keyword: str):
    page.goto(SEARCH_URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(1500)
    _hard_refresh_if_popup(page)

    search_box = page.locator("input[name='ss']")
    search_box.click()
    search_box.fill(keyword)
    page.wait_for_timeout(500)
    search_box.press("Enter")
    page.wait_for_load_state("domcontentloaded", timeout=60000)
    page.wait_for_timeout(2000)
    _hard_refresh_if_popup(page)


# -----------------------------------------------------------
# TC-5543
# -----------------------------------------------------------
def _tc5543_search_to_pdp(page: Page, tr: TestResult):
    """
    dir.indiamart.com → search "tmt bar" → Enter
    → click first product name → PDP
    """
    try:
        _search_and_enter(page, "tmt bar")

        assert (
            "dir.indiamart.com" in page.url or "search.mp" in page.url
        ), f"Did not reach SERP: {page.url}"

        with page.context.expect_page() as new_pg:
            page.locator("a[href*='proddetail']").first.click()

        pdp = new_pg.value
        pdp.wait_for_load_state("domcontentloaded", timeout=60000)
        pdp.wait_for_timeout(2000)
        _hard_refresh_if_popup(pdp)
        tr.set_page(pdp)

        assert "proddetail" in pdp.url
        assert pdp.locator("h1").first.is_visible(timeout=8000)

        tr.add("TC-5543", "Search Results to PDP landing", "PASS",
               pdp.url.split("?")[0][-60:])
        pdp.close()

    except Exception as exc:
        tr.add("TC-5543", "Search Results to PDP landing", "FAIL", str(exc)[:150])


# -----------------------------------------------------------
# TC-5546
# -----------------------------------------------------------
def _tc5546_mcat_to_pdp(page: Page, tr: TestResult):
    """
    dir.indiamart.com → scroll to Drugs & Pharmaceuticals
    → click Cough Syrup subcategory → click first product name → PDP
    """
    try:
        page.goto(SEARCH_URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2000)
        _hard_refresh_if_popup(page)

        drugs_link = page.locator(
            "a[href*='drugs-medicines'], "
            "a:has-text('Drugs & Pharmaceuticals'), "
            "a:has-text('Drugs & Pharma')"
        ).first
        drugs_link.scroll_into_view_if_needed()
        page.wait_for_timeout(800)

        cough_syrup_link = page.locator(
            "a[href*='cough-syrup'], "
            "a:has-text('Cough Syrup')"
        ).first
        cough_syrup_link.wait_for(state="visible", timeout=8000)
        cough_syrup_link.click()
        page.wait_for_load_state("domcontentloaded", timeout=60000)
        page.wait_for_timeout(2000)
        _hard_refresh_if_popup(page)

        with page.context.expect_page() as new_pg:
            page.locator(
                "a.prdtitle[href*='proddetail'], "
                "a[class*='prdtitle'][href*='proddetail'], "
                "a[href*='proddetail']"
            ).first.click()

        pdp = new_pg.value
        pdp.wait_for_load_state("domcontentloaded", timeout=60000)
        pdp.wait_for_timeout(2000)
        _hard_refresh_if_popup(pdp)
        tr.set_page(pdp)

        assert "proddetail" in pdp.url
        assert pdp.locator("h1").first.is_visible(timeout=8000)

        tr.add("TC-5546", "MCAT Page to PDP landing", "PASS",
               pdp.url.split("?")[0][-60:])
        pdp.close()

    except Exception as exc:
        tr.add("TC-5546", "MCAT Page to PDP landing", "FAIL", str(exc)[:150])


# -----------------------------------------------------------
# TC-5547
# -----------------------------------------------------------
def _tc5547_company_page_to_pdp(page: Page, tr: TestResult):
    """
    dir.indiamart.com → search "Digital marketing services" → Enter
    → click first company name (data-click="^CompanyName", opens new tab)
    → click any product image (img[id^='chngImg'])
    → click product name (a[id^='title-']) → PDP
    """
    try:
        _search_and_enter(page, "Digital marketing services near benguluru")

        # Company name: target="_blank" — capture the new tab
        company_link = page.locator("a[data-click='^CompanyName']").first
        company_link.wait_for(state="visible", timeout=15000)
        with page.context.expect_page() as company_pg:
            company_link.click()

        company_page = company_pg.value
        company_page.wait_for_load_state("domcontentloaded", timeout=60000)
        company_page.wait_for_timeout(2000)
        _hard_refresh_if_popup(company_page)

        assert "indiamart.com" in company_page.url, \
            f"Company page did not load: {company_page.url}"

        # Click any product image on the company page
        product_image = company_page.locator("img[id^='chngImg']").first
        product_image.wait_for(state="visible", timeout=10000)
        product_image.click()
        company_page.wait_for_timeout(1500)
        _hard_refresh_if_popup(company_page)

        # Click product name → opens PDP in new tab
        with company_page.context.expect_page() as new_pg:
            company_page.locator("a[id^='title-']").first.click()

        pdp = new_pg.value
        pdp.wait_for_load_state("domcontentloaded", timeout=60000)
        pdp.wait_for_timeout(2000)
        _hard_refresh_if_popup(pdp)
        tr.set_page(pdp)

        assert "proddetail" in pdp.url, f"Not a PDP URL: {pdp.url}"
        title = pdp.locator("h1").first
        assert title.is_visible(timeout=8000), "Product title not visible"

        tr.add("TC-5547", "Company Page to PDP landing", "PASS",
               f"Product: '{title.inner_text()[:50]}'")
        pdp.close()
        company_page.close()

    except Exception as exc:
        tr.add("TC-5547", "Company Page to PDP landing", "FAIL", str(exc)[:150])


# -----------------------------------------------------------
# TC-5989
# -----------------------------------------------------------
def _tc5989_homepage_to_pdp(page: Page, tr: TestResult):
    """
    dir.indiamart.com → search "Digital marketing services" → Enter
    → click first product name on SERP (seeds recently viewed)
    → close PDP tab → click IndiaMART logo on SERP
    → click recently viewed product name on homepage → PDP
    """
    try:
        _search_and_enter(page, "Digital marketing services near benguluru")

        # Step 1: click 6th product name on SERP to seed recently viewed
        # a.cardlinks[href*='proddetail'] nth(5) = 6th position (0-indexed)
        sixth_product = page.locator("a.cardlinks[href*='proddetail']").nth(5)
        sixth_product.wait_for(state="visible", timeout=15000)
        with page.context.expect_page() as seed_pg:
            sixth_product.click()
        seed_page = seed_pg.value
        seed_page.wait_for_load_state("domcontentloaded", timeout=60000)
        seed_page.wait_for_timeout(1500)
        seed_page.close()

        # Step 2: click IndiaMART logo on SERP → homepage
        logo = page.locator(
            "a.hd_logo, "
            "a[class*='hd_logo'], "
            "a[href='https://www.indiamart.com/']"
        ).first
        logo.wait_for(state="visible", timeout=8000)
        logo.click()
        page.wait_for_load_state("domcontentloaded", timeout=60000)
        page.wait_for_timeout(2500)
        _hard_refresh_if_popup(page)

        assert "indiamart.com" in page.url and "proddetail" not in page.url, \
            f"Did not land on homepage: {page.url}"

        # Step 3: click recently viewed product name
        recently_viewed = page.locator(
            "a.pernm[href*='proddetail'], "
            "a[class*='pernm'][href*='proddetail'], "
            "a[href*='imhome=1'][href*='proddetail']"
        ).first
        recently_viewed.wait_for(state="visible", timeout=15000)

        with page.context.expect_page() as new_pg:
            recently_viewed.click()

        pdp = new_pg.value
        pdp.wait_for_load_state("domcontentloaded", timeout=60000)
        pdp.wait_for_timeout(2000)
        _hard_refresh_if_popup(pdp)
        tr.set_page(pdp)

        assert "proddetail" in pdp.url, f"Not a PDP URL: {pdp.url}"
        title = pdp.locator("h1").first
        assert title.is_visible(timeout=8000), "Product title not visible"

        tr.add("TC-5989", "Homepage to PDP landing (recently viewed)", "PASS",
               f"Product: '{title.inner_text()[:50]}'")
        pdp.close()

    except Exception as exc:
        tr.add("TC-5989", "Homepage to PDP landing (recently viewed)", "FAIL",
               str(exc)[:150])


# -----------------------------------------------------------
# Suite Runner
# -----------------------------------------------------------
def run(page: Page) -> TestResult:
    tr = TestResult(page)
    print("\n[Suite 01] PDP Landings")

    _tc5543_search_to_pdp(page, tr)
    _tc5546_mcat_to_pdp(page, tr)
    _tc5547_company_page_to_pdp(page, tr)
    _tc5989_homepage_to_pdp(page, tr)

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