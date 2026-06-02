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


# ── Shared: dismiss popup ─────────────────────────────────────────────────────
def _hard_refresh_if_popup(page: Page):
    try:
        skip = page.locator(
            "a#idfpclose, a.idfpclose, a.skptxt, "
            "a:has-text('Skip'), span:has-text('Skip')"
        ).first
        if skip.is_visible(timeout=3000):
            print("  [POPUP] Clicking Skip to dismiss popup")
            skip.click(force=True)
            page.wait_for_timeout(1000)
            return
    except Exception:
        pass
    try:
        overlay = page.locator(
            "div:has-text('Login to connect with suppliers'), "
            "div:has-text('Looking for New Suppliers?'), "
            "div:has-text('Unlock the best of IndiaMART'), "
            "div[class*='popup'], div[class*='modal'], div[class*='overlay'], "
            "div[id*='popup'], div[id*='modal'], div[class*='dialog'], "
            "div#identyfy_usr_ctl, div[class*='iden_bg']"
        ).first
        if overlay.is_visible(timeout=2000):
            print("  [POPUP] Skip not found — hard refreshing page")
            page.reload(wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(2000)
    except Exception:
        pass


# ── Shared: search ────────────────────────────────────────────────────────────
def _search_and_enter(page: Page, keyword: str):
    page.goto(SEARCH_URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(1500)
    _hard_refresh_if_popup(page)

    search_box = page.locator("input[name='ss']")
    search_box.wait_for(state="visible", timeout=15000)
    search_box.click(force=True)
    search_box.fill(keyword)
    page.wait_for_timeout(500)
    search_box.press("Enter")
    page.wait_for_load_state("domcontentloaded", timeout=60000)
    page.wait_for_timeout(2000)
    _hard_refresh_if_popup(page)


# ── TC-5543 ───────────────────────────────────────────────────────────────────
def _tc5543_search_to_pdp(page: Page, tr: TestResult):
    """Search Results → click first product → PDP"""
    try:
        _search_and_enter(page, "tmt bar")
        assert "dir.indiamart.com" in page.url or "search.mp" in page.url, \
            f"Did not reach SERP: {page.url}"

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


# ── TC-5546 ───────────────────────────────────────────────────────────────────
def _tc5546_mcat_to_pdp(page: Page, tr: TestResult):
    """MCAT (Cough Syrup category) → first product → PDP"""
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

        cough_link = page.locator(
            "a[href*='cough-syrup'], a:has-text('Cough Syrup')"
        ).first
        cough_link.wait_for(state="visible", timeout=8000)
        cough_link.click()
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


# ── TC-5547 ───────────────────────────────────────────────────────────────────
def _tc5547_company_page_to_pdp(page: Page, tr: TestResult):
    """
    SERP → click company name → company page
    → scroll down → click 'View Details'
    → click product name link (target="_blank") → PDP
    """
    try:
        _search_and_enter(page, "digital printing services")

        # Open company page in new tab
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
        print(f"  [TC-5547] Company page: {company_page.url}")

        # Step 1 — scroll down to reveal product listings
        company_page.evaluate("window.scrollBy(0, 600)")
        company_page.wait_for_timeout(1500)

        # Step 2 — click first "View Details" button
        view_details = company_page.locator(
            "span.viewall-text:has-text('View Details')"
        ).first
        view_details.wait_for(state="visible", timeout=10000)
        view_details.scroll_into_view_if_needed()
        company_page.wait_for_timeout(500)
        view_details.click()
        company_page.wait_for_timeout(2000)
        print(f"  [CLICK] [TC-5547 view_details] Clicked 'View Details'")

        # Step 3 — click the product name link (opens PDP in new tab)
        # <a href="//www.indiamart.com/proddetail/..." target="_blank">Product Name</a>
        product_link = company_page.locator(
            "a[href*='indiamart.com/proddetail/'][target='_blank'], "
            "a[href*='/proddetail/'][target='_blank'], "
            "a[href*='proddetail/']"
        ).first
        product_link.wait_for(state="visible", timeout=10000)
        product_name = product_link.inner_text().strip()[:60]
        product_href = product_link.get_attribute("href") or ""
        print(f"  [CLICK] [TC-5547 product_name] <a> '{product_name}' → {product_href[:60]}")

        with company_page.context.expect_page() as new_pg:
            product_link.click()

        pdp = new_pg.value
        pdp.wait_for_load_state("domcontentloaded", timeout=60000)
        pdp.wait_for_timeout(2000)
        _hard_refresh_if_popup(pdp)
        tr.set_page(pdp)

        assert "proddetail" in pdp.url, f"Not a PDP URL: {pdp.url}"
        title_h1 = pdp.locator("h1").first
        assert title_h1.is_visible(timeout=8000), "Product h1 not visible"
        tr.add("TC-5547", "Company Page to PDP landing", "PASS",
               f"Product: '{title_h1.inner_text()[:50]}'")
        print(f"  [PASS] [TC-5547] Company Page to PDP landing - PASS: {pdp.url.split('indiamart.com')[-1][:60]}")
        pdp.close()
        company_page.close()

    except Exception as exc:
        tr.add("TC-5547", "Company Page to PDP landing", "FAIL", str(exc)[:200])
        print(f"  [FAIL] [TC-5547] Company Page to PDP landing - FAIL: {exc}")


# ── TC-5989 ───────────────────────────────────────────────────────────────────
def _tc5989_homepage_to_pdp(page: Page, tr: TestResult):
    """
    SERP → click 6th product (seeds recently viewed)
    → click logo → homepage → click recently viewed → PDP
    """
    try:
        _search_and_enter(page, "digital printing services")

        sixth = page.locator("a.cardlinks[href*='proddetail']").nth(5)
        sixth.wait_for(state="visible", timeout=15000)
        with page.context.expect_page() as seed_pg:
            sixth.click()
        seed_page = seed_pg.value
        seed_page.wait_for_load_state("domcontentloaded", timeout=60000)
        seed_page.wait_for_timeout(1500)
        seed_page.close()

        page.wait_for_timeout(1000)
        _hard_refresh_if_popup(page)

        logo = page.locator(
            "a.hd_logo, a[class*='hd_logo'], a[href='https://www.indiamart.com/']"
        ).first
        logo.wait_for(state="visible", timeout=8000)
        logo.click()
        page.wait_for_load_state("domcontentloaded", timeout=60000)
        page.wait_for_timeout(3000)
        _hard_refresh_if_popup(page)

        assert "indiamart.com" in page.url and "proddetail" not in page.url, \
            f"Did not land on homepage: {page.url}"

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


# ── Suite runner ──────────────────────────────────────────────────────────────
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
        s = result.summary()
        print(f"\nSummary: {s['passed']}/{s['total']} passed "
              f"| {s['failed']} failed | {s['skipped']} skipped")
        browser.close()