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
# Shared: dismiss popup by clicking Skip, fallback hard-refresh
# Handles both:
#   "Login to connect with suppliers" (dir.indiamart.com popup)
#   "Unlock the best of IndiaMART"   (www.indiamart.com popup)
# -----------------------------------------------------------
def _hard_refresh_if_popup(page: Page):
    try:
        # First try: click Skip (preferred — keeps page state)
        skip = page.locator(
            "a#idfpclose, "
            "a.idfpclose, "
            "a.skptxt, "
            "a:has-text('Skip'), "
            "span:has-text('Skip')"
        ).first
        if skip.is_visible(timeout=3000):
            print("  [POPUP] Clicking Skip to dismiss popup")
            skip.click(force=True)
            page.wait_for_timeout(1000)
            return
    except Exception:
        pass

    # Second try: hard refresh if overlay still blocking
    try:
        overlay = page.locator(
            "div:has-text('Login to connect with suppliers'), "
            "div:has-text('Looking for New Suppliers?'), "
            "div:has-text('Unlock the best of IndiaMART'), "
            "div[class*='popup'], div[class*='modal'], "
            "div[class*='overlay'], div[id*='popup'], "
            "div[id*='modal'], div[class*='dialog'], "
            "div#identyfy_usr_ctl, div[class*='iden_bg']"
        ).first
        if overlay.is_visible(timeout=2000):
            print("  [POPUP] Skip not found — hard refreshing page")
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
    → scroll down → click any product image (img[id^='chngImg'])
    → click product name (a[id^='title-']) → PDP
    """
    try:
        _search_and_enter(page, "Digital marketing services near benguluru")

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

        # Step 1: click first product name in the slider/listing
        # e.g. <a class="slider-product-name">Digital Marketing Services...</a>
        slider_name = company_page.locator("a.slider-product-name").first
        slider_name.wait_for(state="visible", timeout=10000)
        slider_name.click()
        company_page.wait_for_timeout(1500)
        _hard_refresh_if_popup(company_page)

        # Step 2: click the product title link to open PDP in new tab
        # e.g. <a class="FM_c1 FM_Lsp1 Fm_lh5 FM_c12 FM_cp" id="title-3">...</a>
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
    → click 6th product on SERP (seeds recently viewed)
    → dismiss popup → click IndiaMART logo → recently viewed → PDP
    """
    try:
        _search_and_enter(page, "Digital marketing services near benguluru")

        # Step 1: click 6th product to seed recently viewed
        sixth_product = page.locator("a.cardlinks[href*='proddetail']").nth(5)
        sixth_product.wait_for(state="visible", timeout=15000)
        with page.context.expect_page() as seed_pg:
            sixth_product.click()
        seed_page = seed_pg.value
        seed_page.wait_for_load_state("domcontentloaded", timeout=60000)
        seed_page.wait_for_timeout(1500)
        seed_page.close()

        page.wait_for_timeout(1000)
        _hard_refresh_if_popup(page)

        # Step 2: click IndiaMART logo → homepage
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