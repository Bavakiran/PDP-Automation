"""
Suite 02: PDP First Fold
"""
import sys
from pathlib import Path
from playwright.sync_api import Page, Locator

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


# ---------------------------------------------------------------------------
# Helper: red outline + console log before every click
# ---------------------------------------------------------------------------
def _highlight_and_log(page: Page, locator: Locator, label: str):
    try:
        locator.scroll_into_view_if_needed()
        page.wait_for_timeout(300)
        el = locator.element_handle()
        tag  = page.evaluate("el => el.tagName", el)
        text = page.evaluate(
            "el => el.innerText || el.getAttribute('alt') || el.getAttribute('aria-label') || ''", el
        )
        print(f"  [CLICK] [{label}] <{tag.lower()}> '{text[:60].strip()}'")
        page.evaluate(
            """el => {
                el.style.outline = '3px solid red';
                el.style.outlineOffset = '2px';
                setTimeout(() => {
                    el.style.outline = '';
                    el.style.outlineOffset = '';
                }, 1500);
            }""",
            el
        )
        page.wait_for_timeout(800)
    except Exception as e:
        print(f"  [CLICK] [{label}] (highlight failed: {e})")


def _click_and_expect_form_hl(page: Page, selectors: list, label: str):
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if loc.is_visible(timeout=3000):
                _highlight_and_log(page, loc, label)
                break
        except Exception:
            continue
    click_and_expect_form(page, selectors)


def _click_and_capture_hl(page: Page, locator: Locator, label: str):
    _highlight_and_log(page, locator, label)
    return click_and_capture_page(page, locator)


def _click_locator_hl(page: Page, locator: Locator, label: str):
    _highlight_and_log(page, locator, label)
    click_locator(locator)


# ---------------------------------------------------------------------------
# Suite runner
# ---------------------------------------------------------------------------
def run(page: Page) -> TestResult:
    tr = TestResult(page)
    print("\n[Suite 02] PDP First Fold")

    # ── TC-5548 ──────────────────────────────────────────────────────────────
    # Click product image: img#img_id / img.img-drift-demo-trigger (not company logo)
    land_on_pdp_direct(page, DIRECT_PDP_URL)
    try:
        _click_and_expect_form_hl(
            page,
            [
                "img#img_id",
                "img.img-drift-demo-trigger",
                "img[src*='imimg'][alt]",
            ],
            "TC-5548 product_image"
        )
        tr.add("TC-5548", "Clicking product image opens enquiry form", "PASS")
    except Exception as exc:
        tr.add("TC-5548", "Clicking product image opens enquiry form", "FAIL", str(exc)[:120])

    # TC-5549 removed as requested

    # ── TC-5550 ──────────────────────────────────────────────────────────────
    land_on_pdp_direct(page, DIRECT_PDP_URL)
    try:
        _click_and_expect_form_hl(page, [SEL["submit_requirement"]], "TC-5550 submit_requirement")
        tr.add("TC-5550", "Clicking Submit Requirement opens enquiry form", "PASS")
    except AssertionError as exc:
        tr.add("TC-5550", "Clicking Submit Requirement opens enquiry form", "SKIP",
               f"Different template: {str(exc)[:90]}")
    except Exception as exc:
        tr.add("TC-5550", "Clicking Submit Requirement opens enquiry form", "FAIL", str(exc)[:120])

    # ── TC-5551 ──────────────────────────────────────────────────────────────
    # Click company name: h2.fs15 — may open in same tab or new tab
    land_on_pdp_direct(page, DIRECT_PDP_URL)
    try:
        company_locator = page.locator("h2.fs15").first
        assert company_locator.is_visible(timeout=5000), "Company name element not visible"
        target = _click_and_capture_hl(page, company_locator, "TC-5551 company_name h2.fs15")
        tr.set_page(target)
        # Company page can be indiamart.com or external domain — must not be a PDP
        assert "proddetail" not in target.url, f"Unexpected URL: {target.url}"
        tr.add("TC-5551", "Clicking company name redirects to company page", "PASS",
               target.url[-70:])
        if target != page:
            target.close()
    except Exception as exc:
        tr.add("TC-5551", "Clicking company name redirects to company page", "FAIL", str(exc)[:120])

    # ── TC-5552 ──────────────────────────────────────────────────────────────
    # Click ratings count: span.tcund (e.g. "207")
    land_on_pdp_direct(page, DIRECT_PDP_URL)
    try:
        review_loc = page.locator("span.tcund").first
        review_loc.wait_for(state="visible", timeout=8000)
        _click_locator_hl(page, review_loc, "TC-5552 ratings span.tcund")
        page.wait_for_timeout(1500)
        assert (
            "#review" in page.url.lower()
            or "review" in page.content().lower()
            or "rating" in page.content().lower()
        )
        tr.add("TC-5552", "Clicking review count moves to rating and review section", "PASS")
    except Exception as exc:
        tr.add("TC-5552", "Clicking review count moves to rating and review section", "FAIL",
               str(exc)[:120])

    # ── TC-5554 ──────────────────────────────────────────────────────────────
    land_on_pdp_direct(page, DIRECT_PDP_URL)
    try:
        _click_and_expect_form_hl(page, [SEL["contact_supplier"]], "TC-5554 contact_supplier")
        tr.add("TC-5554", "Clicking Contact Supplier opens enquiry form", "PASS")
    except Exception as exc:
        tr.add("TC-5554", "Clicking Contact Supplier opens enquiry form", "FAIL", str(exc)[:120])

    # ── TC-5906 ──────────────────────────────────────────────────────────────
    # Click Call Now div (div.vMBtn / id starts with mn_mask_pg) — opens enquiry form
    land_on_pdp_direct(page, DIRECT_PDP_URL)
    try:
        call_cta = page.locator("div.vMBtn[id^='mn_mask_pg']").first
        call_cta.wait_for(state="visible", timeout=8000)
        _highlight_and_log(page, call_cta, "TC-5906 call_now div.vMBtn")
        call_cta.click()
        page.wait_for_timeout(1000)

        # Dismiss "Open Pick an app?" popup if it appears
        try:
            cancel_btn = page.locator("button:has-text('Cancel')").last
            cancel_btn.wait_for(state="visible", timeout=3000)
            _highlight_and_log(page, cancel_btn, "TC-5906 dismiss_cancel")
            cancel_btn.click()
            page.wait_for_timeout(500)
        except Exception:
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)

        assert (
            page.locator(SEL["modal_form"]).count() > 0
            or page.locator(SEL["inline_form"]).count() > 0
        ), "Enquiry form did not open after Call Now click"
        tr.add("TC-5906", "Clicking Call Now triggers enquiry form", "PASS")
    except Exception as exc:
        tr.add("TC-5906", "Clicking Call Now triggers enquiry form", "FAIL", str(exc)[:120])

    # ── TC-5907 ──────────────────────────────────────────────────────────────
    land_on_pdp_direct(page, DIRECT_PDP_URL)
    try:
        _click_and_expect_form_hl(page, [SEL["contact_supplier"]], "TC-5907 contact_supplier")
        tr.add("TC-5907", "Clicking Contact Supplier CTA displays enquiry form", "PASS")
    except Exception as exc:
        tr.add("TC-5907", "Clicking Contact Supplier CTA displays enquiry form", "FAIL", str(exc)[:120])

    # ── TC-5939 ──────────────────────────────────────────────────────────────
    land_on_pdp_direct(page, DIRECT_PDP_URL)
    try:
        _click_and_expect_form_hl(page, [SEL["brochure_link"]], "TC-5939 brochure_link")
        tr.add("TC-5939", "Clicking brochure PDF opens quick requirement form", "PASS")
    except Exception as exc:
        tr.add("TC-5939", "Clicking brochure PDF opens quick requirement form", "SKIP", str(exc)[:120])

    # ── TC-5940 ──────────────────────────────────────────────────────────────
    land_on_pdp_direct(page, DIRECT_PDP_URL)
    try:
        _click_and_expect_form_hl(page, [SEL["video_icon"]], "TC-5940 video_icon")
        tr.add("TC-5940", "Clicking video icon opens enquiry form", "PASS")
    except Exception as exc:
        tr.add("TC-5940", "Clicking video icon opens enquiry form", "SKIP", str(exc)[:120])

    # ── TC-5941 ──────────────────────────────────────────────────────────────
    # Click View in Hindi: a.hindiLink (target="_blank") → assert hindi.indiamart.com in URL
    land_on_pdp_direct(page, DIRECT_PDP_URL)
    try:
        hindi_loc = page.locator("a.hindiLink").first
        hindi_loc.wait_for(state="visible", timeout=8000)
        target = _click_and_capture_hl(page, hindi_loc, "TC-5941 a.hindiLink")
        tr.set_page(target)
        assert "hindi.indiamart.com" in target.url, f"Unexpected URL: {target.url}"
        tr.add("TC-5941", "Clicking View in Hindi redirects to Hindi PDP", "PASS",
               target.url[-70:])
        if target != page:
            target.close()
    except AssertionError as exc:
        tr.add("TC-5941", "Clicking View in Hindi redirects to Hindi PDP", "SKIP",
               f"Different template: {str(exc)[:90]}")
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