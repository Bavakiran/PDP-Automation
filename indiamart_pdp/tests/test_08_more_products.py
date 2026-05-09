"""
Suite 08: More Products from Seller

TC-5953  More products section displayed with image, product name, price (if applicable)
TC-5954  Product details (image, name, price) displayed correctly
TC-5955  Clicking product name redirects to PDP (same tab)
TC-5956  Get Best Price CTA should NOT be displayed in this section
"""
import sys
from pathlib import Path
from playwright.sync_api import Page, Locator

try:
    from utils.helpers import (
        DIRECT_PDP_URL,
        SEL,
        TestResult,
        click_and_expect_form,
        first_visible,
        visible_count,
        land_on_pdp_direct,
    )
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from indiamart_pdp.utils.helpers import (
        DIRECT_PDP_URL,
        SEL,
        TestResult,
        click_and_expect_form,
        first_visible,
        visible_count,
        land_on_pdp_direct,
    )


# ---------------------------------------------------------------------------
# Helper: dismiss "Unlock IndiaMART" popup via Skip link
# ---------------------------------------------------------------------------
def _dismiss_login_popup(page: Page):
    try:
        skip = page.locator("a#idfpclose, a.idfpclose, a.skptxt").first
        if skip.is_visible(timeout=3000):
            print("  [POPUP] Login popup detected — clicking Skip")
            skip.click(force=True)
            page.wait_for_timeout(1000)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Helper: red outline + console log before every click
# ---------------------------------------------------------------------------
def _highlight_and_log(page: Page, locator: Locator, label: str):
    try:
        locator.scroll_into_view_if_needed()
        page.wait_for_timeout(500)
        el = locator.element_handle()
        tag  = page.evaluate("el => el.tagName", el)
        text = page.evaluate(
            "el => el.innerText || el.getAttribute('alt') || el.getAttribute('aria-label') || ''",
            el
        )
        href = page.evaluate("el => el.getAttribute('href') || ''", el)
        print(
            f"  [CLICK] [{label}] <{tag.lower()}> '{text[:60].strip()}'"
            + (f" -> {href[:80]}" if href else "")
        )
        page.evaluate(
            """el => {
                el.style.outline = '4px solid red';
                el.style.outlineOffset = '3px';
                el.style.backgroundColor = 'rgba(255,0,0,0.15)';
                setTimeout(() => {
                    el.style.outline = '';
                    el.style.outlineOffset = '';
                    el.style.backgroundColor = '';
                }, 2500);
            }""",
            el
        )
        page.wait_for_timeout(1500)
    except Exception as e:
        print(f"  [CLICK] [{label}] (highlight failed: {e})")


# ---------------------------------------------------------------------------
# Scroll helper
# ---------------------------------------------------------------------------
def _scroll_to_section(page: Page) -> None:
    page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.75)")
    page.wait_for_timeout(1500)


# ---------------------------------------------------------------------------
# Check if "More Products from Seller" section exists
# ---------------------------------------------------------------------------
def _has_more_products_section(page: Page) -> bool:
    try:
        section = page.locator(
            "section:has-text('More Products'), "
            "div:has-text('More Products from'), "
            "#Seller_More_Products, "
            "#smpprds"
        ).first
        return section.is_visible(timeout=5000)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Suite runner
# ---------------------------------------------------------------------------
def run(page: Page) -> TestResult:
    tr = TestResult(page)
    print("\n[Suite 08] More Products from Seller")

    # ── Section presence check (shared gate for all TCs) ────────────────────
    land_on_pdp_direct(page, DIRECT_PDP_URL)
    _dismiss_login_popup(page)
    _scroll_to_section(page)
    _dismiss_login_popup(page)

    if not _has_more_products_section(page):
        detail = "More Products from Seller section not present — skipping all TCs"
        print(f"  [SKIP] {detail}")
        tr.add("TC-5953", "More products section displayed", "SKIP", detail)
        tr.add("TC-5954", "Product details (image, name, price) displayed", "SKIP", detail)
        tr.add("TC-5955", "Clicking product name redirects to PDP", "SKIP", detail)
        tr.add("TC-5956", "Get Best Price CTA not displayed in section", "SKIP", detail)
        return tr

    # ── TC-5953 ──────────────────────────────────────────────────────────────
    # Section is displayed with products
    try:
        count = visible_count(page, [
            "#Seller_More_Products a.product_item",
            "#smpprds a.product_item",
            "ul.products a[href*='proddetail']",
            "a[href*='proddetail'][class*='product_item']",
        ])
        assert count > 0, "No product cards found in More Products section"
        print(f"  [CHECK] [TC-5953] {count} product cards found")
        tr.add("TC-5953", "More products section displayed", "PASS", f"{count} items")
    except Exception as exc:
        tr.add("TC-5953", "More products section displayed", "FAIL", str(exc)[:120])

    # ── TC-5954 ──────────────────────────────────────────────────────────────
    # Check image, product name (span.PName), price displayed for first card
    land_on_pdp_direct(page, DIRECT_PDP_URL)
    _dismiss_login_popup(page)
    _scroll_to_section(page)
    _dismiss_login_popup(page)
    try:
        # First product card anchor
        first_card = page.locator(
            "#Seller_More_Products a.product_item, "
            "#smpprds a.product_item, "
            "a[href*='proddetail'][class*='product_item']"
        ).first
        first_card.wait_for(state="visible", timeout=8000)
        first_card.scroll_into_view_if_needed()

        results = []

        # Image check
        img = first_card.locator("img").first
        if img.is_visible(timeout=3000):
            src = img.get_attribute("src") or ""
            assert src, "Product image src is empty"
            results.append(f"Image ✓ ({src[-40:]})")
        else:
            results.append("Image — not found")

        # Product name: span.PName
        name_loc = first_card.locator("span.PName").first
        if name_loc.is_visible(timeout=3000):
            name_text = name_loc.inner_text().strip()
            assert name_text, "Product name is empty"
            results.append(f"Name ✓ ('{name_text[:40]}')")
        else:
            results.append("Name — not found")

        # Price check (optional — skip if not present)
        price_loc = first_card.locator(
            "p[class*='price'], span[class*='price'], "
            "[class*='pdinb'], [class*='price']"
        ).first
        if price_loc.is_visible(timeout=3000):
            price_text = price_loc.inner_text().strip()
            results.append(f"Price ✓ ('{price_text[:30]}')")
        else:
            results.append("Price — not applicable")

        print(f"  [CHECK] [TC-5954] {' | '.join(results)}")

        # Fail only if image or name missing
        assert "Image ✓" in " ".join(results), "Product image missing"
        assert "Name ✓" in " ".join(results), "Product name missing"

        tr.add("TC-5954", "Product details (image, name, price) displayed", "PASS",
               " | ".join(results)[:120])
    except Exception as exc:
        tr.add("TC-5954", "Product details (image, name, price) displayed", "FAIL", str(exc)[:120])

    # ── TC-5955 ──────────────────────────────────────────────────────────────
    # Clicking product name (span.PName inside anchor) → opens PDP in same tab
    land_on_pdp_direct(page, DIRECT_PDP_URL)
    _dismiss_login_popup(page)
    _scroll_to_section(page)
    _dismiss_login_popup(page)
    try:
        # Click the first product card (target="_self" — same tab)
        first_card = page.locator(
            "#Seller_More_Products a.product_item, "
            "#smpprds a.product_item, "
            "a[href*='proddetail'][class*='product_item']"
        ).first
        first_card.wait_for(state="visible", timeout=8000)
        first_card.scroll_into_view_if_needed()

        _highlight_and_log(page, first_card, "TC-5955 product_name")

        # target="_self" → same tab navigation
        first_card.click()
        page.wait_for_load_state("domcontentloaded", timeout=60000)
        page.wait_for_timeout(2000)
        _dismiss_login_popup(page)

        final_url = page.url
        print(f"  [INFO] [TC-5955] Redirected to: {final_url}")
        assert "proddetail" in final_url, f"Expected PDP URL, got: {final_url}"
        tr.add("TC-5955", "Clicking product name redirects to PDP (same tab)", "PASS",
               final_url[-70:])
    except Exception as exc:
        tr.add("TC-5955", "Clicking product name redirects to PDP (same tab)", "FAIL", str(exc)[:120])

    # ── TC-5956 ──────────────────────────────────────────────────────────────
    # Get Best Price CTA should NOT be displayed inside More Products section
    land_on_pdp_direct(page, DIRECT_PDP_URL)
    _dismiss_login_popup(page)
    _scroll_to_section(page)
    _dismiss_login_popup(page)
    try:
        section_loc = page.locator(
            "#Seller_More_Products, #smpprds"
        ).first
        section_loc.wait_for(state="visible", timeout=8000)

        # Check Get Best Price is not inside the section
        gbp_inside = section_loc.locator(
            "a:has-text('Get Best Price'), button:has-text('Get Best Price')"
        )
        count = gbp_inside.count()
        print(f"  [CHECK] [TC-5956] Get Best Price count inside section: {count}")
        assert count == 0, \
            f"Get Best Price CTA found {count} time(s) inside More Products section"
        tr.add("TC-5956", "Get Best Price CTA not displayed in More Products section", "PASS")
    except Exception as exc:
        tr.add("TC-5956", "Get Best Price CTA not displayed in More Products section", "FAIL",
               str(exc)[:120])

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