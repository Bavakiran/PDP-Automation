"""
Suite 06: Company Details

TC-5949  Company details section is displayed
TC-5950  Clicking Contact Supplier opens enquiry form
TC-5951  GST number is present and masked (e.g. 07*********1Z2)
TC-5952  TrustSEAL / Mobile / Email badges present (if applicable)
TC-5953  Company info fields present and in correct format (if applicable)
         - Legal Status of Firm
         - GST Registration Date  (Mon YYYY)
         - Annual Turnover
         - IndiaMART Member Since (Mon YYYY)
"""
import re
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
        land_on_pdp_direct,
    )

# Mon YYYY pattern  e.g. "Jul 2017", "Jun 2006"
_MON_YYYY = re.compile(
    r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}"
)
# Masked GST: alphanumeric with at least one * in the middle
_GST_MASKED = re.compile(r"[A-Z0-9]{2}\*+[A-Z0-9]+")


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


# ---------------------------------------------------------------------------
# Suite runner
# ---------------------------------------------------------------------------
def run(page: Page) -> TestResult:
    tr = TestResult(page)
    print("\n[Suite 06] Company Details")

    # ── TC-5949 ──────────────────────────────────────────────────────────────
    # Company details section is displayed
    land_on_pdp_direct(page, DIRECT_PDP_URL)
    try:
        section = first_visible(page, [SEL["company_section"], SEL["company_link"]])
        text = section.inner_text()
        assert len(text.strip()) > 0
        tr.add("TC-5949", "Company details are displayed", "PASS",
               text[:60].replace("\n", " "))
    except Exception as exc:
        tr.add("TC-5949", "Company details are displayed", "FAIL", str(exc)[:120])

    # ── TC-5950 ──────────────────────────────────────────────────────────────
    # Clicking Contact Supplier opens enquiry form
    land_on_pdp_direct(page, DIRECT_PDP_URL)
    try:
        _click_and_expect_form_hl(
            page, [SEL["contact_supplier"]], "TC-5950 contact_supplier"
        )
        tr.add("TC-5950", "Clicking Contact Supplier opens enquiry form", "PASS")
    except Exception as exc:
        tr.add("TC-5950", "Clicking Contact Supplier opens enquiry form", "FAIL", str(exc)[:120])

    # ── TC-5951 ──────────────────────────────────────────────────────────────
    # GST number present and masked (e.g. 07*********1Z2)
    land_on_pdp_direct(page, DIRECT_PDP_URL)
    try:
        gst_loc = page.locator(
            "[class*='gst'], [id*='gst'], "
            "span:has-text('GST-'), div:has-text('GST-')"
        ).first
        if gst_loc.is_visible(timeout=5000):
            gst_text = gst_loc.inner_text().strip()
            print(f"  [CHECK] [TC-5951] GST text: '{gst_text}'")
            assert "GST" in gst_text.upper(), "GST label not found"
            assert "*" in gst_text, f"GST not masked: '{gst_text}'"
            assert _GST_MASKED.search(gst_text), \
                f"GST masking pattern invalid: '{gst_text}'"
            tr.add("TC-5951", "GST number present and masked", "PASS", gst_text[:60])
        else:
            tr.add("TC-5951", "GST number present and masked", "SKIP",
                   "GST element not found — may not be applicable")
    except Exception as exc:
        tr.add("TC-5951", "GST number present and masked", "FAIL", str(exc)[:120])

    # ── TC-5952 ──────────────────────────────────────────────────────────────
    # TrustSEAL / Mobile / Email badges present (if applicable)
    land_on_pdp_direct(page, DIRECT_PDP_URL)
    try:
        badges_found = []

        trust_loc = page.locator(
            "[class*='trustseal'], [class*='TrustSeal'], "
            "span:has-text('TrustSEAL'), img[alt*='TrustSEAL']"
        ).first
        if trust_loc.is_visible(timeout=3000):
            badges_found.append("TrustSEAL")

        mobile_loc = page.locator(
            "[class*='mobile'], span:has-text('Mobile'), "
            "i[class*='mobile'], img[alt*='Mobile']"
        ).first
        if mobile_loc.is_visible(timeout=3000):
            badges_found.append("Mobile")

        email_loc = page.locator(
            "[class*='email'], span:has-text('E-Mail'), "
            "span:has-text('Email'), i[class*='mail'], img[alt*='Email']"
        ).first
        if email_loc.is_visible(timeout=3000):
            badges_found.append("E-Mail")

        logo_loc = page.locator(
            "[class*='comp-logo'], [class*='company-logo'], "
            "[class*='seller-logo'], img[class*='logo']"
        ).first
        if logo_loc.is_visible(timeout=3000):
            badges_found.append("Logo")

        if badges_found:
            print(f"  [CHECK] [TC-5952] Badges found: {badges_found}")
            tr.add("TC-5952", "Company badges present", "PASS",
                   ", ".join(badges_found))
        else:
            tr.add("TC-5952", "Company badges present", "SKIP",
                   "No badges found — may not be applicable")
    except Exception as exc:
        tr.add("TC-5952", "Company badges present", "FAIL", str(exc)[:120])

    # ── TC-5953 ──────────────────────────────────────────────────────────────
    # Company info fields: Legal Status, GST Reg Date, Annual Turnover,
    # IndiaMART Member Since — dates must be in Mon YYYY format
    land_on_pdp_direct(page, DIRECT_PDP_URL)
    try:
        # Get full text of the company info section
        info_section = page.locator(
            "[class*='comp-dtl'], [class*='company-dtl'], "
            "[class*='seller-dtl'], [class*='comp_dtl'], "
            "[id*='comp-info'], [id*='company-info']"
        ).first

        if not info_section.is_visible(timeout=5000):
            # fallback: grab broader section around the legal status label
            info_section = page.locator(
                "div:has-text('Legal Status'), "
                "div:has-text('Annual Turnover'), "
                "div:has-text('Member Since')"
            ).first

        section_text = info_section.inner_text() if info_section.is_visible(timeout=3000) else ""
        print(f"  [CHECK] [TC-5953] Info section text:\n    {section_text[:300].replace(chr(10), ' | ')}")

        results = []

        # Legal Status of Firm
        if "Legal Status" in section_text:
            results.append("Legal Status ✓")
        else:
            results.append("Legal Status — not found")

        # GST Registration Date — must match Mon YYYY
        if "GST Registration Date" in section_text or "GST Reg" in section_text:
            match = _MON_YYYY.search(section_text[section_text.find("GST Reg"):section_text.find("GST Reg") + 60])
            if match:
                results.append(f"GST Reg Date ✓ ({match.group()})")
            else:
                results.append("GST Reg Date — format invalid (expected Mon YYYY)")
        else:
            results.append("GST Reg Date — not found")

        # Annual Turnover
        if "Annual Turnover" in section_text or "Turnover" in section_text:
            results.append("Annual Turnover ✓")
        else:
            results.append("Annual Turnover — not found")

        # IndiaMART Member Since — must match Mon YYYY
        if "Member Since" in section_text:
            match = _MON_YYYY.search(section_text[section_text.find("Member Since"):section_text.find("Member Since") + 60])
            if match:
                results.append(f"Member Since ✓ ({match.group()})")
            else:
                results.append("Member Since — format invalid (expected Mon YYYY)")
        else:
            results.append("Member Since — not found")

        found_count = sum(1 for r in results if "✓" in r)
        print(f"  [CHECK] [TC-5953] {' | '.join(results)}")

        if found_count == 0:
            tr.add("TC-5953", "Company info fields present and formatted", "SKIP",
                   "No info fields found — may not be applicable")
        else:
            # Fail only if a present date field has wrong format
            format_errors = [r for r in results if "format invalid" in r]
            assert not format_errors, \
                "Date format errors: " + "; ".join(format_errors)
            tr.add("TC-5953", "Company info fields present and formatted", "PASS",
                   " | ".join(results)[:120])

    except Exception as exc:
        tr.add("TC-5953", "Company info fields present and formatted", "FAIL", str(exc)[:120])

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