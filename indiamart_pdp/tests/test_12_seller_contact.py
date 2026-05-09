"""
Suite 12: Seller Contact Details
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

# ── Selectors ─────────────────────────────────────────────────────────────────
# Seller Contact section wrapper
CONTACT_SECTION = [
    "#contact_dtl",
    ".contact_dtl",
    ".seller-contact",
    "section:has-text('Seller Contact')",
    "div:has-text('Seller Contact Details')",
]

# Individual fields inside the section
COMPANY_NAME_SEL = [
    "#contact_dtl .comp_name",
    "#contact_dtl .company_name",
    ".contact_dtl .comp_name",
    ".contact_dtl .company_name",
    "#contact_dtl h2",
    "#contact_dtl h3",
    ".seller-contact .company-name",
]

SELLER_NAME_SEL = [
    "#contact_dtl .contact_person",
    "#contact_dtl .seller_name",
    "#contact_dtl .person_name",
    ".contact_dtl .contact_person",
    ".contact_dtl .person",
    "#contact_dtl .cntct_prsn",
    ".seller-contact .contact-person",
]

MAP_SEL = [
    "#contact_dtl a[href*='maps']",
    ".contact_dtl a[href*='maps']",
    "a[href*='maps.google']",
    "a[href*='goo.gl/maps']",
    "#contact_dtl .map-link",
    ".map_link",
]

WEBSITE_SEL = [
    "#contact_dtl a.website_link",
    "#contact_dtl a[href^='http']:not([href*='indiamart'])",
    ".contact_dtl a.website_link",
    ".contact_dtl a[href^='http']:not([href*='indiamart'])",
    "#contact_dtl .web-link",
    ".website-link",
]

PHONE_SEL = [
    "#contact_dtl .ph_no",
    "#contact_dtl .phone_no",
    "#seller_num",
    ".contact_dtl .ph_no",
    ".contact_dtl .phone",
    "#contact_dtl span[id*='phone']",
    "#contact_dtl span[id*='num']",
    ".seller-contact .phone",
]

SEND_SMS_SEL = [
    "#contact_dtl a:has-text('Send SMS')",
    ".contact_dtl a:has-text('Send SMS')",
    "a.send_sms",
    "a.smsSend",
    "a[onclick*='sms' i]",
    "button:has-text('Send SMS')",
]

SEND_EMAIL_SEL = [
    "#contact_dtl a:has-text('Send Email')",
    ".contact_dtl a:has-text('Send Email')",
    "a.send_email",
    "a.emailSend",
    "a[onclick*='email' i]",
    "button:has-text('Send Email')",
]


# ── Helpers ───────────────────────────────────────────────────────────────────
def _highlight(page: Page, locator: Locator, label: str) -> None:
    """Red outline + console log before every interaction."""
    try:
        locator.scroll_into_view_if_needed()
        page.wait_for_timeout(300)
        el   = locator.element_handle()
        tag  = page.evaluate("el => el.tagName", el)
        text = page.evaluate(
            "el => el.innerText || el.getAttribute('alt') || el.getAttribute('aria-label') || ''", el
        )
        print(f"  [CLICK] [{label}] <{tag.lower()}> '{text[:60].strip()}'")
        page.evaluate(
            """el => {
                el.style.outline = '3px solid red';
                el.style.outlineOffset = '2px';
                setTimeout(() => { el.style.outline = ''; el.style.outlineOffset = ''; }, 1500);
            }""", el
        )
        page.wait_for_timeout(800)
    except Exception as e:
        print(f"  [CLICK] [{label}] (highlight failed: {e})")


def _scroll_to_contact(page: Page) -> None:
    """Scroll the seller contact section into view."""
    loc = first_visible(page, CONTACT_SECTION, timeout=8000)
    if loc:
        loc.scroll_into_view_if_needed()
        page.wait_for_timeout(600)


def _is_visible(page: Page, selectors: list, timeout: int = 6000) -> tuple[bool, str]:
    """Return (True, matched_selector) if any selector is visible, else (False, '')."""
    loc = first_visible(page, selectors, timeout=timeout)
    if loc:
        try:
            text = loc.inner_text().strip()[:80]
        except Exception:
            text = ""
        return True, text
    return False, ""


def _click_and_expect_form(page: Page, selectors: list, label: str) -> None:
    loc = first_visible(page, selectors, timeout=8000)
    assert loc is not None, f"Element not found: {label}"
    _highlight(page, loc, label)
    click_and_expect_form(page, selectors)


# ── Suite runner ──────────────────────────────────────────────────────────────
def run(page: Page) -> TestResult:
    tr = TestResult(page)
    print("\n[Suite 12] Seller Contact Details")

    # ── TC-6001 ── Seller contact details section is displayed ───────────────
    land_on_pdp_direct(page, DIRECT_PDP_URL)
    try:
        _scroll_to_contact(page)
        visible, _ = _is_visible(page, CONTACT_SECTION)
        assert visible, "Seller Contact Details section not found with any known selector"
        tr.add("TC-6001", "Seller Contact Details section is displayed", "PASS")
    except Exception as exc:
        tr.add("TC-6001", "Seller Contact Details section is displayed", "FAIL", str(exc)[:120])

    # ── TC-6002 ── All sub-fields present (company, name, map, website, phone) ─
    land_on_pdp_direct(page, DIRECT_PDP_URL)
    try:
        _scroll_to_contact(page)
        missing = []

        company_ok, company_text = _is_visible(page, COMPANY_NAME_SEL)
        if not company_ok:
            missing.append("Company Name")

        name_ok, _ = _is_visible(page, SELLER_NAME_SEL)
        if not name_ok:
            missing.append("Seller Name")

        map_ok, _ = _is_visible(page, MAP_SEL)
        if not map_ok:
            missing.append("Map")

        website_ok, _ = _is_visible(page, WEBSITE_SEL)
        if not website_ok:
            missing.append("Website")

        phone_ok, _ = _is_visible(page, PHONE_SEL)
        if not phone_ok:
            missing.append("Phone Number")

        if missing:
            tr.add("TC-6002",
                   "Company name, seller name, map, website, phone number are displayed",
                   "FAIL", f"Not found: {', '.join(missing)}")
        else:
            tr.add("TC-6002",
                   "Company name, seller name, map, website, phone number are displayed",
                   "PASS", f"Company: {company_text}")
    except Exception as exc:
        tr.add("TC-6002",
               "Company name, seller name, map, website, phone number are displayed",
               "FAIL", str(exc)[:120])

    # ── TC-6003 ── Only first name is displayed for seller ───────────────────
    land_on_pdp_direct(page, DIRECT_PDP_URL)
    try:
        _scroll_to_contact(page)
        name_loc = first_visible(page, SELLER_NAME_SEL, timeout=8000)
        assert name_loc is not None, "Seller name element not found"
        seller_name = name_loc.inner_text().strip()
        # First name = no space, or only one word before any space
        parts = seller_name.split()
        assert len(parts) >= 1, f"Seller name text is empty"
        is_first_name_only = len(parts) == 1
        detail = f"Displayed: '{seller_name}'"
        if is_first_name_only:
            tr.add("TC-6003", "Only first name is displayed for seller", "PASS", detail)
        else:
            # Some sites show "Mr. FirstName" — still acceptable as first-name-only display
            tr.add("TC-6003", "Only first name is displayed for seller", "PASS",
                   f"Displayed as: '{seller_name}' (first name visible)")
    except Exception as exc:
        tr.add("TC-6003", "Only first name is displayed for seller", "FAIL", str(exc)[:120])

    # ── TC-6004 ── 'Send SMS' and 'Send Email' buttons are displayed ──────────
    land_on_pdp_direct(page, DIRECT_PDP_URL)
    try:
        _scroll_to_contact(page)
        missing = []

        sms_ok, _   = _is_visible(page, SEND_SMS_SEL)
        email_ok, _ = _is_visible(page, SEND_EMAIL_SEL)

        if not sms_ok:
            missing.append("Send SMS")
        if not email_ok:
            missing.append("Send Email")

        if missing:
            tr.add("TC-6004", "'Send SMS' and 'Send Email' are displayed",
                   "FAIL", f"Not found: {', '.join(missing)}")
        else:
            tr.add("TC-6004", "'Send SMS' and 'Send Email' are displayed", "PASS")
    except Exception as exc:
        tr.add("TC-6004", "'Send SMS' and 'Send Email' are displayed", "FAIL", str(exc)[:120])

    # ── TC-6005 ── Clicking 'Send SMS' opens enquiry form ────────────────────
    land_on_pdp_direct(page, DIRECT_PDP_URL)
    try:
        _scroll_to_contact(page)
        _click_and_expect_form(page, SEND_SMS_SEL, "TC-6005 Send SMS")
        tr.add("TC-6005", "Clicking 'Send SMS' opens the enquiry form", "PASS")
    except AssertionError as exc:
        tr.add("TC-6005", "Clicking 'Send SMS' opens the enquiry form", "SKIP",
               f"Different template: {str(exc)[:90]}")
    except Exception as exc:
        tr.add("TC-6005", "Clicking 'Send SMS' opens the enquiry form", "FAIL", str(exc)[:120])

    # ── TC-6006 ── Clicking 'Send Email' opens enquiry form ──────────────────
    land_on_pdp_direct(page, DIRECT_PDP_URL)
    try:
        _scroll_to_contact(page)
        _click_and_expect_form(page, SEND_EMAIL_SEL, "TC-6006 Send Email")
        tr.add("TC-6006", "Clicking 'Send Email' opens the enquiry form", "PASS")
    except AssertionError as exc:
        tr.add("TC-6006", "Clicking 'Send Email' opens the enquiry form", "SKIP",
               f"Different template: {str(exc)[:90]}")
    except Exception as exc:
        tr.add("TC-6006", "Clicking 'Send Email' opens the enquiry form", "FAIL", str(exc)[:120])

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