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
    r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}",
    re.IGNORECASE,
)
# Full month YYYY pattern e.g. "June 2006"
_FULL_MON_YYYY = re.compile(
    r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}",
    re.IGNORECASE,
)
# Masked GST: starts with 2 alphanumeric chars, has asterisks in middle
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
# Helper: dismiss "Unlock IndiaMART" popup via Skip link
# ---------------------------------------------------------------------------
def _dismiss_login_popup(page: Page):
    try:
        skip = page.locator(
            "a#idfpclose, a.idfpclose, a.skptxt"
        ).first
        if skip.is_visible(timeout=3000):
            print("  [POPUP] Login popup detected — clicking Skip")
            skip.click(force=True)
            page.wait_for_timeout(1000)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Helper: extract text of a SPECIFIC element by precise selectors
# Returns (text, selector_used) or (None, None) if nothing matched
# ---------------------------------------------------------------------------
def _get_specific_text(page: Page, selectors: list, timeout: int = 4000):
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if loc.is_visible(timeout=timeout):
                text = loc.inner_text().strip()
                if text:
                    return text, sel
        except Exception:
            continue
    return None, None


# ---------------------------------------------------------------------------
# Suite runner
# ---------------------------------------------------------------------------
def run(page: Page) -> TestResult:
    tr = TestResult(page)
    print("\n[Suite 06] Company Details")

    # ── TC-5949 ──────────────────────────────────────────────────────────────
    # Company details section is displayed
    land_on_pdp_direct(page, DIRECT_PDP_URL)
    _dismiss_login_popup(page)
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
    _dismiss_login_popup(page)
    try:
        _click_and_expect_form_hl(
            page, [SEL["contact_supplier"]], "TC-5950 contact_supplier"
        )
        tr.add("TC-5950", "Clicking Contact Supplier opens enquiry form", "PASS")
    except Exception as exc:
        tr.add("TC-5950", "Clicking Contact Supplier opens enquiry form", "FAIL", str(exc)[:120])

    # ── TC-5951 ──────────────────────────────────────────────────────────────
    # GST number present and masked (e.g. 07**********1Z2)
    # Target: the specific inline GST span/div — NOT a large ancestor container.
    # From live DOM: "GST- \n07**********1Z2" is rendered as two sibling nodes
    # inside a small wrapper. We look for the masked number itself directly.
    land_on_pdp_direct(page, DIRECT_PDP_URL)
    _dismiss_login_popup(page)
    try:
        # These selectors target ONLY the element that holds the masked GST number,
        # not any large ancestor that contains the whole page.
        GST_SELECTORS = [
            # Specific GST number element (contains asterisks — very precise)
            "span.gst-number",
            "span[class*='gst']",
            "div[class*='gst']",
            # Text-based: look for element whose own text matches the masked pattern
            # Use XPath to match elements whose own text (not descendants) has asterisks
            "xpath=//span[contains(text(),'**')]",
            "xpath=//div[contains(@class,'gst') and contains(text(),'**')]",
            "xpath=//td[contains(text(),'**') and string-length(normalize-space(text())) < 20]",
            "xpath=//li[contains(text(),'**') and string-length(normalize-space(text())) < 20]",
        ]

        gst_text = None
        used_sel = None

        # First pass: try class-based selectors
        for sel in GST_SELECTORS:
            try:
                loc = page.locator(sel).first
                if loc.is_visible(timeout=3000):
                    candidate = loc.inner_text().strip()
                    # Accept only if text is short (< 60 chars) and contains masked GST pattern
                    if len(candidate) < 60 and _GST_MASKED.search(candidate):
                        gst_text = candidate
                        used_sel = sel
                        break
            except Exception:
                continue

        # Second pass: scan all text nodes on the page for the GST pattern
        if not gst_text:
            all_texts = page.evaluate(
                """() => {
                    const results = [];
                    const walker = document.createTreeWalker(
                        document.body,
                        NodeFilter.SHOW_TEXT,
                        null,
                        false
                    );
                    let node;
                    while ((node = walker.nextNode())) {
                        const t = node.textContent.trim();
                        if (t.length > 5 && t.length < 30 && t.includes('*')) {
                            results.push(t);
                        }
                    }
                    return results;
                }"""
            )
            for t in all_texts:
                if _GST_MASKED.search(t):
                    gst_text = t
                    used_sel = "text_node_scan"
                    break

        print(f"  [CHECK] [TC-5951] GST text: '{gst_text}' (via: {used_sel})")

        if gst_text:
            assert "*" in gst_text, f"GST not masked: '{gst_text}'"
            assert _GST_MASKED.search(gst_text), \
                f"GST masking pattern invalid: '{gst_text}'"
            tr.add("TC-5951", "GST number present and masked", "PASS", gst_text[:60])
        else:
            tr.add("TC-5951", "GST number present and masked", "SKIP",
                   "GST masked number not found on page — may not be applicable")

    except Exception as exc:
        tr.add("TC-5951", "GST number present and masked", "FAIL", str(exc)[:120])

    # ── TC-5952 ──────────────────────────────────────────────────────────────
    # TrustSEAL / Mobile / Email badges present (if applicable)
    land_on_pdp_direct(page, DIRECT_PDP_URL)
    _dismiss_login_popup(page)
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
    # IndiaMART Member Since — dates must be in Mon YYYY or Month YYYY format
    # From live DOM the "About the Company" block contains all these fields.
    land_on_pdp_direct(page, DIRECT_PDP_URL)
    _dismiss_login_popup(page)
    try:
        # Target the "About the Company" section specifically.
        # These selectors are ordered from most-specific to most-general.
        INFO_SECTION_SELECTORS = [
            # Specific "About the Company" section wrappers
            "#company-details",
            "#companyDetails",
            "[id*='about-company']",
            "[id*='aboutCompany']",
            "[class*='about-company']",
            "[class*='aboutCompany']",
            # Narrower class-based selectors
            ".comp-dtl-wrap",
            ".comp_dtl_wrap",
            "[class*='comp-dtl']",
            "[class*='company-dtl']",
            "[class*='seller-dtl']",
            "[class*='comp_dtl']",
            "[id*='comp-info']",
            "[id*='company-info']",
        ]

        section_text = None
        for sel in INFO_SECTION_SELECTORS:
            try:
                loc = page.locator(sel).first
                if loc.is_visible(timeout=3000):
                    candidate = loc.inner_text().strip()
                    # Accept only if it's a focused block (not the whole page)
                    # and contains at least one expected field label
                    if (len(candidate) < 3000 and
                            any(kw in candidate for kw in
                                ["Legal Status", "Annual Turnover", "Member Since",
                                 "GST Registration"])):
                        section_text = candidate
                        print(f"  [CHECK] [TC-5953] Matched section via: {sel}")
                        break
            except Exception:
                continue

        # Fallback: use JS to find the "About the Company" heading and grab its parent
        if not section_text:
            section_text = page.evaluate(
                """() => {
                    // Find heading containing "About the Company"
                    const headings = [...document.querySelectorAll('h2,h3,h4,div,span')];
                    for (const el of headings) {
                        if (el.children.length === 0 &&
                            el.textContent.trim() === 'About the Company') {
                            // Walk up to find the section container
                            let parent = el.parentElement;
                            for (let i = 0; i < 4; i++) {
                                if (parent && parent.innerText &&
                                    parent.innerText.length > 100 &&
                                    parent.innerText.length < 3000) {
                                    return parent.innerText;
                                }
                                parent = parent ? parent.parentElement : null;
                            }
                        }
                    }
                    return null;
                }"""
            )
            if section_text:
                print("  [CHECK] [TC-5953] Matched section via JS heading search")

        if not section_text:
            tr.add("TC-5953", "Company info fields present and formatted", "SKIP",
                   "Could not isolate company info section")
            return tr

        print(f"  [CHECK] [TC-5953] Info section text:\n    {section_text[:300].replace(chr(10), ' | ')}")

        results = []

        # Legal Status of Firm
        if "Legal Status" in section_text:
            results.append("Legal Status ✓")
        else:
            results.append("Legal Status — not found")

        # GST Registration Date — must match Mon YYYY or full Month YYYY
        if "GST Registration Date" in section_text or "GST Reg" in section_text:
            segment = section_text[section_text.lower().find("gst reg"):
                                   section_text.lower().find("gst reg") + 80]
            match = _MON_YYYY.search(segment) or _FULL_MON_YYYY.search(segment)
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

        # IndiaMART Member Since — must match Mon YYYY or full Month YYYY
        if "Member Since" in section_text:
            segment = section_text[section_text.find("Member Since"):
                                   section_text.find("Member Since") + 80]
            match = _MON_YYYY.search(segment) or _FULL_MON_YYYY.search(segment)
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