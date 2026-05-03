"""
Suite 09: About the Company

TC-5955  Scroll to Product Details section → click Company Details tab
         → assert About the Company section text is present

TC-5956  Under Company Details tab → verify:
         - GST masked (e.g. 27**********1ZG)
         - IEC code masked (e.g. ******53H)
         - GST Registration Date in Mon YYYY format
         - IndiaMART Member Since in Mon YYYY format
         - Other fields (Legal Status, Nature of Business, Employees,
           Annual Turnover, Exports to) displayed if present
"""
import re
import sys
from pathlib import Path
from playwright.sync_api import Page, Locator

try:
    from utils.helpers import DIRECT_PDP_URL, SEL, TestResult, first_visible, land_on_pdp_direct
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from indiamart_pdp.utils.helpers import DIRECT_PDP_URL, SEL, TestResult, first_visible, land_on_pdp_direct

# Mon YYYY pattern — handles both abbrev (Jun) and full (June)
_MON_YYYY = re.compile(
    r"(January|February|March|April|May|June|July|August|September|October|November|December"
    r"|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}"
)
# Masked pattern: starts with alphanumeric, contains * in middle
_MASKED = re.compile(r"[A-Z0-9*]{2,}\*+[A-Z0-9*]+")


# ---------------------------------------------------------------------------
# Helper: dismiss "Unlock IndiaMART" popup
# ---------------------------------------------------------------------------
def _dismiss_login_popup(page: Page):
    try:
        skip = page.locator(
            "a#idfpclose, a.idfpclose, a.skptxt, "
            "text=Skip"
        ).first
        if skip.is_visible(timeout=5000):
            print("  [POPUP] Login popup detected — clicking Skip")
            skip.click(force=True)
            page.wait_for_timeout(1000)
            return
    except Exception:
        pass

    # Fallback: hard refresh if popup overlay is still blocking
    try:
        overlay = page.locator(
            "div#identyfy_usr_ctl, "
            "div[class*='iden_bg'], "
            "div[class*='wd_box1']"
        ).first
        if overlay.is_visible(timeout=2000):
            print("  [POPUP] Overlay still present — hard refreshing")
            page.reload(wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(2000)
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
            "el => el.innerText || el.getAttribute('alt') || el.getAttribute('aria-label') || ''", el
        )
        print(f"  [CLICK] [{label}] <{tag.lower()}> '{text[:60].strip()}'")
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
# Scroll to Product Details section
# ---------------------------------------------------------------------------
def _scroll_to_product_details(page: Page):
    try:
        # Dismiss popup first before scrolling
        _dismiss_login_popup(page)

        # Scroll the tab nav into view
        tab_nav = page.locator("a[href*='#abt'], a[href*='#pdpDP']").first
        if tab_nav.is_visible(timeout=3000):
            tab_nav.scroll_into_view_if_needed()
        else:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.5)")

        page.wait_for_timeout(1500)
        # Dismiss popup that may appear after scroll
        _dismiss_login_popup(page)
        print("  [SCROLL] Scrolled to Product Details section")
    except Exception:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.5)")
        page.wait_for_timeout(1500)
        _dismiss_login_popup(page)


# ---------------------------------------------------------------------------
# Click "Company Details" tab
# ---------------------------------------------------------------------------
def _click_company_details_tab(page: Page):
    # Target the anchor specifically — not the nav container
    tab = page.locator("a[href*='#abt']").first

    # Fallback: find the link whose text is exactly "Company Details"
    if not tab.is_visible(timeout=3000):
        tab = page.locator("nav a, ul.tabs a, [class*='tab'] a").filter(
            has_text="Company Details"
        ).first

    tab.wait_for(state="visible", timeout=8000)
    _highlight_and_log(page, tab, "TC Company Details tab a[href*='#abt']")
    tab.click()
    page.wait_for_timeout(3000)   # wait for content to render after tab switch

    # Dismiss popup that may appear after tab click
    _dismiss_login_popup(page)
    print("  [INFO] Company Details tab clicked")


# ---------------------------------------------------------------------------
# Suite runner
# ---------------------------------------------------------------------------
def run(page: Page) -> TestResult:
    tr = TestResult(page)
    print("\n[Suite 09] About the Company")

    # ── TC-5955 ──────────────────────────────────────────────────────────────
    # Scroll to Product Details → click Company Details tab → text present
    land_on_pdp_direct(page, DIRECT_PDP_URL)
    _dismiss_login_popup(page)
    try:
        _scroll_to_product_details(page)
        _dismiss_login_popup(page)
        _click_company_details_tab(page)

        # Wait for company details content to fully render after tab click
        page.wait_for_timeout(2000)

        # The data is in the container wrapping "About the Company" heading + fields
        # Try multiple parent containers that hold the actual field data
        about_section = None
        for sel in [
            "div.tab-content #abt",
            "#abt ~ div",                          # sibling after #abt anchor
            "div:has(> h2:has-text('About the Company'))",
            "section:has(h2:has-text('About the Company'))",
            "[class*='about-company']",
            "[class*='abt-comp']",
            "[class*='comp-abt']",
        ]:
            loc = page.locator(sel).first
            try:
                if loc.is_visible(timeout=2000):
                    txt = loc.inner_text().strip()
                    if any(k in txt for k in [
                        "Legal", "GST", "Turnover", "Member",
                        "Employees", "Nature", "Export", "Annual"
                    ]):
                        about_section = loc
                        break
            except Exception:
                continue

        # Final fallback: extract only the About the Company block from body
        if about_section is None:
            body_text = page.locator("body").inner_text()
            # Find the LAST occurrence — "About the Company" heading in the section
            # (earlier occurrences may be in "More Products" or other widgets)
            idx = body_text.rfind("About the Company")
            if idx != -1:
                text = body_text[idx:idx + 600].strip()
            else:
                text = ""
        else:
            text = about_section.inner_text().strip()

        assert any(k in text for k in [
            "Legal", "GST", "Turnover", "Member", "Employees",
            "Nature", "Export", "Annual"
        ]), "About the Company section not found or empty after tab click"

        print("  [CHECK] [TC-5955] About the Company section is present with content")
        tr.add("TC-5955", "About the Company section text is present", "PASS")
    except Exception as exc:
        tr.add("TC-5955", "About the Company section text is present", "FAIL", str(exc)[:120])

    # ── TC-5956 ──────────────────────────────────────────────────────────────
    # Under Company Details — verify masking and date formats
    land_on_pdp_direct(page, DIRECT_PDP_URL)
    _dismiss_login_popup(page)
    try:
        _scroll_to_product_details(page)
        _dismiss_login_popup(page)
        _click_company_details_tab(page)

        # Wait for content to render after tab click
        page.wait_for_timeout(2000)

        # Find the container that actually holds the company fields
        section_text = ""
        for sel in [
            "div.tab-content #abt",
            "#abt ~ div",
            "div:has(> h2:has-text('About the Company'))",
            "section:has(h2:has-text('About the Company'))",
            "[class*='about-company']",
            "[class*='abt-comp']",
            "[class*='comp-abt']",
        ]:
            loc = page.locator(sel).first
            try:
                if loc.is_visible(timeout=2000):
                    txt = loc.inner_text().strip()
                    if any(k in txt for k in [
                        "Legal", "GST", "Turnover", "Member",
                        "Employees", "Nature", "Export", "Annual"
                    ]):
                        section_text = txt
                        break
            except Exception:
                continue

        # Final fallback: use rfind to get the actual section, not earlier widgets
        if not section_text:
            body_text = page.locator("body").inner_text()
            idx = body_text.rfind("About the Company")
            if idx != -1:
                section_text = body_text[idx:idx + 800].strip()

        assert section_text, "Could not find company details section text"
        print(f"  [CHECK] [TC-5956] Full section text:\n    "
              f"{section_text[:400].replace(chr(10), ' | ')}")

        results = []
        failures = []

        # ── GST masked ───────────────────────────────────────────────────────
        if "GST" in section_text and "GST Registration" not in section_text.split("GST")[0]:
            # Extract the GST value line
            gst_lines = [
                line.strip() for line in section_text.splitlines()
                if line.strip() and not any(k in line for k in
                   ["Registration Date", "Import", "Legal", "Nature", "Turnover",
                    "Member", "Employee", "Export"])
                and "GST" not in line and re.search(r"\*", line)
            ]
            gst_value = gst_lines[0] if gst_lines else ""
            if gst_value and _MASKED.search(gst_value):
                results.append(f"GST masked ✓ ({gst_value})")
            elif gst_value:
                failures.append(f"GST not masked: '{gst_value}'")
                results.append(f"GST masking FAIL ({gst_value})")
            else:
                results.append("GST — not found (optional)")

        # ── IEC code masked ──────────────────────────────────────────────────
        if "Import Export Code" in section_text or "IEC" in section_text:
            # Find line after IEC label
            iec_match = re.search(
                r"Import Export Code.*?\n(.+)", section_text
            )
            iec_value = iec_match.group(1).strip() if iec_match else ""
            if iec_value and _MASKED.search(iec_value):
                results.append(f"IEC masked ✓ ({iec_value})")
            elif iec_value:
                failures.append(f"IEC not masked: '{iec_value}'")
                results.append(f"IEC masking FAIL ({iec_value})")
            else:
                results.append("IEC — not found (optional)")
        else:
            results.append("IEC — not present (optional)")

        # ── GST Registration Date → Mon YYYY ────────────────────────────────
        if "GST Registration Date" in section_text:
            idx = section_text.find("GST Registration Date")
            snippet = section_text[idx:idx + 60]
            match = _MON_YYYY.search(snippet)
            if match:
                results.append(f"GST Reg Date ✓ ({match.group()})")
            else:
                failures.append(f"GST Reg Date format invalid in: '{snippet[:40]}'")
                results.append("GST Reg Date format FAIL")
        else:
            results.append("GST Reg Date — not found (optional)")

        # ── IndiaMART Member Since → Mon YYYY ───────────────────────────────
        if "Member Since" in section_text:
            idx = section_text.find("Member Since")
            snippet = section_text[idx:idx + 60]
            match = _MON_YYYY.search(snippet)
            if match:
                results.append(f"Member Since ✓ ({match.group()})")
            else:
                failures.append(f"Member Since format invalid in: '{snippet[:40]}'")
                results.append("Member Since format FAIL")
        else:
            results.append("Member Since — not found (optional)")

        # ── Optional fields (just log presence) ─────────────────────────────
        for field in ["Legal Status", "Nature of Business",
                      "Number of Employees", "Annual Turnover", "Exports to"]:
            if field in section_text:
                results.append(f"{field} ✓")

        print(f"  [RESULT] [TC-5956] {' | '.join(results)}")

        if failures:
            tr.add("TC-5956", "Company Details fields validated", "FAIL",
                   "; ".join(failures)[:120])
        else:
            tr.add("TC-5956", "Company Details fields validated", "PASS",
                   " | ".join(r for r in results if "✓" in r)[:120])

    except Exception as exc:
        tr.add("TC-5956", "Company Details fields validated", "FAIL", str(exc)[:120])

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