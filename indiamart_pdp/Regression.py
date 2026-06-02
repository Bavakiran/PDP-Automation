"""
Regression.py  —  IndiaMart PDP Regression Suite
=================================================
Phase 1 -> UNIDENTIFIED   — test_01 to test_12, no login
Phase 2 -> IDENTIFIED     — login via mobile 8610237001 + OTP 1411, test_02 to test_12
Phase 3 -> FULLY LOGGED IN — login via mobile 8610237001 + OTP 1411, test_02 to test_12

Mandatory popup ("Login to connect with suppliers"):
  - If popup appears -> reload once
  - If still appears -> fill mobile 8610237001, click CONTINUE, enter OTP 1411

Usage:  python Regression.py
"""

import sys
import importlib
import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, Page

# ── Path setup ────────────────────────────────────────────────────────────────
BASE_DIR  = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from utils.helpers import TestResult
from utils.ai_visual_checker import ai_verify_failures, row_colour as _ai_row_colour

# ── Config ────────────────────────────────────────────────────────────────────
try:
    from config import BASE_URL, HEADLESS
except ImportError:
    BASE_URL = "https://www.indiamart.com"
    HEADLESS = False

# Single mobile + OTP used across ALL phases and the mandatory popup
MOBILE   = "8610237001"
OTP      = "1411"

# ── Phase definitions ─────────────────────────────────────────────────────────
SMOKE_MODULES = [
    "tests.test_01_pdp_landings",
    "tests.test_02_pdp_first_fold",
    "tests.test_03_pdp_breadcrumbs",
    "tests.test_04_find_similar_products",
    "tests.test_05_find_related_categories",
    "tests.test_06_company_details",
    "tests.test_07_chat_bl_form",
    "tests.test_08_more_products",
    "tests.test_09_about_the_company",
    "tests.test_10_inline_BL",
    "tests.test_11_header_footer",
    "tests.test_12_seller_contact",
]

IDENTIFIED_MODULES = [
    "tests.test_02_pdp_first_fold",
    "tests.test_03_pdp_breadcrumbs",
    "tests.test_04_find_similar_products",
    "tests.test_05_find_related_categories",
    "tests.test_06_company_details",
    "tests.test_07_chat_bl_form",
    "tests.test_08_more_products",
    "tests.test_09_about_the_company",
    "tests.test_10_inline_BL",
    "tests.test_11_header_footer",
    "tests.test_12_seller_contact",
]

LOGGED_IN_MODULES = IDENTIFIED_MODULES


# ═══════════════════════════════════════════════════════════════════════════════
# SHARED OTP FILLER
# Used by the mandatory popup handler, Phase 2, and Phase 3
# ═══════════════════════════════════════════════════════════════════════════════
def _enter_otp(page: Page, label: str = "OTP") -> None:
    """
    Waits for the OTP modal (input#first visible), then types each digit
    using press_sequentially() so the onkeyup handler fires and auto-submits.
    Confirms via p#after_verified.
    """
    otp_first = page.locator("input#first")
    otp_first.wait_for(state="visible", timeout=15000)
    print(f"[{label}] OTP modal visible — entering digits")

    digits     = list(OTP.ljust(4, "0"))
    otp_fields = ["first", "second", "third", "fourth"]

    for field_id, digit in zip(otp_fields, digits):
        inp = page.locator(f"input#{field_id}")
        inp.wait_for(state="visible", timeout=5000)
        inp.click()
        # press_sequentially fires keydown -> input -> keyup
        # This triggers the onkeyup="moveToNext1imlogv1(...)" handler
        # which auto-advances focus and submits on the 4th digit.
        # fill() does NOT fire keyboard events — that was the root cause bug.
        inp.press_sequentially(digit, delay=100)
        page.wait_for_timeout(300)
        print(f"[{label}]   input#{field_id} <- '{digit}'")

    print(f"[{label}] All digits entered: {OTP}")

    # Wait for "Login Successful" confirmation
    confirmed = False
    try:
        page.wait_for_selector("p#after_verified", state="visible", timeout=10000)
        print(f"[{label}] Login Successful confirmed")
        confirmed = True
    except Exception:
        pass

    if not confirmed:
        try:
            el  = page.locator("p#after_verified")
            el.wait_for(state="attached", timeout=5000)
            if "successful" in el.inner_text().lower():
                print(f"[{label}] Login Successful (text check)")
                confirmed = True
        except Exception:
            pass

    if not confirmed:
        page.wait_for_timeout(3000)
        print(f"[{label}] Could not confirm Login Successful — continuing")

    page.wait_for_timeout(1500)


# ═══════════════════════════════════════════════════════════════════════════════
# MANDATORY POPUP HANDLER
# "Login to connect with suppliers" popup — Phase 1 & 2
# ═══════════════════════════════════════════════════════════════════════════════
def _is_supplier_popup_visible(page: Page) -> bool:
    try:
        return page.locator("text='Login to connect with suppliers'").first.is_visible(timeout=3000)
    except Exception:
        pass
    try:
        return page.locator("button:has-text('CONTINUE')").first.is_visible(timeout=2000)
    except Exception:
        return False


def handle_mandatory_popup(page: Page) -> None:
    """
    If the "Login to connect with suppliers" popup appears:
      1. Reload once — if gone, continue.
      2. If still present — fill mobile, click CONTINUE, enter OTP.
    """
    if not _is_supplier_popup_visible(page):
        print("[Popup] No supplier popup — OK")
        return

    print("[Popup] Supplier popup detected — reloading")
    page.reload(wait_until="domcontentloaded")
    page.wait_for_timeout(2500)

    if not _is_supplier_popup_visible(page):
        print("[Popup] Popup gone after reload — OK")
        return

    print("[Popup] Popup persists — logging in via popup")

    # Fill mobile number
    mobile_inp = page.locator(
        "input[placeholder='Enter your mobile number'], "
        "input[type='tel'], input[name='mobile']"
    ).first
    mobile_inp.wait_for(state="visible", timeout=8000)
    mobile_inp.click()
    mobile_inp.fill(MOBILE)
    print(f"[Popup] Entered mobile: {MOBILE}")

    # Click CONTINUE
    page.locator("button:has-text('CONTINUE')").first.click()
    print("[Popup] Clicked CONTINUE")
    page.wait_for_timeout(1500)

    # Enter OTP
    _enter_otp(page, label="Popup")
    print("[Popup] Mandatory popup handled\n")


# ═══════════════════════════════════════════════════════════════════════════════
# SHARED: open header Sign In modal
# ═══════════════════════════════════════════════════════════════════════════════
def _open_signin_modal(page: Page) -> None:
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(2500)
    handle_mandatory_popup(page)

    # Dismiss other interstitials
    try:
        skip = page.locator(
            "a#idfpclose, a.idfpclose, a.skptxt, "
            "a:has-text('Skip'), span:has-text('Skip')"
        ).first
        if skip.is_visible(timeout=2000):
            skip.click(force=True)
            page.wait_for_timeout(800)
    except Exception:
        pass

    hd_pr = page.locator(".Hd_pr").first
    try:
        hd_pr.wait_for(state="visible", timeout=15000)
    except Exception:
        print("[Login] .Hd_pr not visible — reloading")
        page.reload(wait_until="domcontentloaded")
        page.wait_for_timeout(2500)
        handle_mandatory_popup(page)
        hd_pr.wait_for(state="visible", timeout=15000)
    hd_pr.click()
    page.wait_for_timeout(1500)

    sign_in_link = page.locator("a.cont_s.cpo.Hd_db").first
    try:
        sign_in_link.wait_for(state="visible", timeout=5000)
        sign_in_link.click()
    except Exception:
        print("[Login] Sign-in link hidden — JS fallback")
        sign_in_link.evaluate("el => el.click()")
    page.wait_for_timeout(1000)


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 1: unidentified — no login
# ═══════════════════════════════════════════════════════════════════════════════
def setup_unidentified(page: Page) -> None:
    print("\n" + "="*60)
    print("  PHASE 1 — UNIDENTIFIED (no login)")
    print("="*60)
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(2500)
    handle_mandatory_popup(page)
    print("[Phase 1] Page ready — unidentified state\n")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 2: identified — mobile 8610237001, click Get OTP, enter 1411
# ═══════════════════════════════════════════════════════════════════════════════
def login_identified(page: Page) -> None:
    """
    Phase 2 login flow:
      1. Open Sign In modal from header
      2. Enter mobile 8610237001
      3. Click Submit (#logintoidentify)
      4. If "Get OTP" / "Continue with OTP" button appears -> click it
      5. Enter OTP 1411 via press_sequentially
      6. Confirm login
    """
    print("\n" + "="*60)
    print("  PHASE 2 — IDENTIFIED (mobile + OTP)")
    print("="*60)

    _open_signin_modal(page)
    print("[Phase 2] Opened Sign In modal")

    # Step 1: enter mobile
    mobile_inp = page.locator("#mobile")
    mobile_inp.wait_for(state="visible", timeout=10000)
    mobile_inp.click()
    mobile_inp.fill(MOBILE)
    print(f"[Phase 2] Entered mobile: {MOBILE}")

    # Step 2: submit
    page.locator("#logintoidentify").click()
    print("[Phase 2] Clicked Submit")
    page.wait_for_timeout(2500)
    print(f"[Phase 2] Settled on: {page.url}")

    # Step 3: click "Get OTP" / "Continue with OTP" button
    # Covers both selector variants seen on www and buyer.indiamart.com
    get_otp_btn = page.locator(
        "button.login-btn, "
        "button:has-text('Get OTP'), "
        "button:has-text('Continue with OTP'), "
        "button:has-text('CONTINUE')"
    ).first
    try:
        get_otp_btn.wait_for(state="visible", timeout=15000)
        print(f"[Phase 2] Found OTP button: '{get_otp_btn.inner_text().strip()}'")
        get_otp_btn.click()
        page.wait_for_timeout(1000)
        print("[Phase 2] Clicked Get OTP button")
    except Exception:
        # Some accounts skip straight to OTP modal — check if modal is already visible
        try:
            page.locator("input#first").wait_for(state="visible", timeout=5000)
            print("[Phase 2] OTP modal appeared without needing button click")
        except Exception as e:
            raise Exception(f"[Phase 2] Could not find Get OTP button or OTP modal: {e}")

    # Step 4: enter OTP
    _enter_otp(page, label="Phase2")

    # Step 5: navigate back to base URL for tests
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(2000)
    handle_mandatory_popup(page)
    print("[Phase 2] Login complete — navigated back to base URL\n")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 3: fully logged in — mobile 8610237001 + OTP 1411
# ═══════════════════════════════════════════════════════════════════════════════
def login_fully_logged_in(page: Page) -> None:
    """
    Phase 3 login flow (fresh browser context, no cookies):
      1. Open Sign In modal from header
      2. Enter mobile 8610237001 -> Submit
      3. Redirect to buyer.indiamart.com -> click "Continue with OTP"
      4. Enter OTP 1411 via press_sequentially (no submit button — onkeyup fires)
      5. Confirm via p#after_verified
    """
    print("\n" + "="*60)
    print("  PHASE 3 — FULLY LOGGED IN (mobile + OTP)")
    print("="*60)

    _open_signin_modal(page)
    print("[Phase 3] Opened Sign In modal")

    # Step 1: enter mobile
    mobile_inp = page.locator("#mobile")
    mobile_inp.wait_for(state="visible", timeout=10000)
    mobile_inp.click()
    mobile_inp.fill(MOBILE)
    print(f"[Phase 3] Entered mobile: {MOBILE}")

    # Step 2: submit
    page.locator("#logintoidentify").click()
    print("[Phase 3] Clicked Submit")
    page.wait_for_timeout(2500)
    print(f"[Phase 3] Settled on: {page.url}")

    # Step 3: click "Continue with OTP"
    continue_btn = page.locator("button.login-btn")
    try:
        continue_btn.wait_for(state="visible", timeout=15000)
    except Exception:
        try:
            page.wait_for_url("*buyer.indiamart.com*", timeout=10000)
            page.wait_for_load_state("domcontentloaded", timeout=10000)
            page.wait_for_timeout(1000)
            print(f"[Phase 3] Redirected to: {page.url}")
            continue_btn.wait_for(state="visible", timeout=10000)
        except Exception as e:
            raise Exception(f"[Phase 3] button.login-btn not found on {page.url}: {e}")
    print(f"[Phase 3] Found: '{continue_btn.inner_text().strip()}'")
    continue_btn.click()
    page.wait_for_timeout(1000)
    print("[Phase 3] Clicked Continue with OTP")

    # Step 4: enter OTP
    _enter_otp(page, label="Phase3")
    print("[Phase 3] Login complete\n")


# ═══════════════════════════════════════════════════════════════════════════════
# Suite runner
# ═══════════════════════════════════════════════════════════════════════════════
def run_suite(page: Page, modules: list, phase_label: str) -> list:
    suite_results = []
    for mod_name in modules:
        print(f"\n  >> {mod_name}")
        try:
            mod    = importlib.import_module(mod_name)
            result: TestResult = mod.run(page)
            s      = result.summary()
            suite_results.append({
                "suite":   f"[{phase_label}] {mod_name.split('.')[-1]}",
                "results": result.results,
                "total":   s["total"],
                "passed":  s["passed"],
                "failed":  s["failed"],
                "skipped": s["skipped"],
            })
            print(f"     {s['passed']}/{s['total']} passed"
                  f" | {s['failed']} failed | {s['skipped']} skipped")
        except Exception as exc:
            print(f"     CRASHED: {exc}")
            suite_results.append({
                "suite":   f"[{phase_label}] {mod_name.split('.')[-1]}",
                "results": [{
                    "tc_id": "--", "name": "Suite-level crash",
                    "status": "FAIL", "detail": str(exc)[:200],
                    "screenshot": "",
                    "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
                }],
                "total": 1, "passed": 0, "failed": 1, "skipped": 0,
            })
    return suite_results


# ═══════════════════════════════════════════════════════════════════════════════
# HTML report
# ═══════════════════════════════════════════════════════════════════════════════
def _colour(status: str) -> str:
    return {"PASS": "#d4edda", "FAIL": "#f8d7da",
            "SKIP": "#fff3cd"}.get(status.upper(), "#f5f5f5")


def generate_regression_report(
    smoke: list, identified: list, logged_in: list, output_path: Path
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    all_suites = smoke + identified + logged_in
    total   = sum(r["total"]   for r in all_suites)
    passed  = sum(r["passed"]  for r in all_suites)
    failed  = sum(r["failed"]  for r in all_suites)
    skipped = sum(r["skipped"] for r in all_suites)
    pct     = round(passed / total * 100, 1) if total else 0

    def phase_rows(suites, badge_color, badge_text):
        html = ""
        for suite in suites:
            html += (
                f'<tr><td colspan="6" style="background:#343a40;color:#fff;font-weight:bold;'
                f'padding:8px 10px;font-size:13px">{suite["suite"]}'
                f'&nbsp;<span style="background:{badge_color};color:#fff;padding:1px 8px;'
                f'border-radius:4px;font-size:11px">{badge_text}</span></td></tr>'
            )
            for tc in suite["results"]:
                sc = tc.get("screenshot", "")
                sc_cell = (
                    f'<a href="file:///{sc.replace(chr(92), "/")}" target="_blank">screenshot</a>'
                    if sc else ""
                )
                html += (
                    f'<tr style="background:{_colour(tc["status"])}">'
                    f'<td>{tc["tc_id"]}</td><td>{tc["name"]}</td>'
                    f'<td><b>{tc["status"]}</b></td>'
                    f'<td style="font-size:12px">{tc.get("detail","")}</td>'
                    f'<td style="text-align:center">{sc_cell}</td>'
                    f'<td>{tc["timestamp"]}</td></tr>'
                )
        return html

    def phase_summary(suites, label, badge_color):
        p  = sum(r["passed"]  for r in suites)
        f  = sum(r["failed"]  for r in suites)
        s  = sum(r["skipped"] for r in suites)
        t  = sum(r["total"]   for r in suites)
        pc = round(p / t * 100, 1) if t else 0
        return (
            f'<tr><td><span style="background:{badge_color};color:#fff;padding:2px 10px;'
            f'border-radius:4px;font-size:12px">{label}</span></td>'
            f'<td style="color:#28a745;font-weight:bold">{p}</td>'
            f'<td style="color:#dc3545;font-weight:bold">{f}</td>'
            f'<td style="color:#856404;font-weight:bold">{s}</td>'
            f'<td>{t}</td><td>{pc}%</td></tr>'
        )

    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>IndiaMart PDP Regression Report</title>
<style>
  body{{font-family:Arial,sans-serif;margin:20px;background:#f5f5f5}}
  h1,h2{{color:#333}}
  h2{{margin:28px 0 8px;font-size:16px;border-left:4px solid #343a40;padding-left:8px}}
  .kpi{{display:flex;gap:16px;margin:16px 0 24px;flex-wrap:wrap}}
  .box{{padding:12px 22px;border-radius:8px;text-align:center;color:#fff;font-size:18px;font-weight:bold}}
  .pass{{background:#28a745}} .fail{{background:#dc3545}}
  .skip{{background:#ffc107;color:#333}} .total{{background:#17a2b8}}
  table{{width:100%;border-collapse:collapse;background:#fff;border-radius:8px;
         overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.1);margin-bottom:24px}}
  th{{background:#343a40;color:#fff;padding:10px;text-align:left}}
  td{{padding:8px 10px;border-bottom:1px solid #dee2e6;font-size:13px}}
  tr:last-child td{{border-bottom:none}}
</style></head><body>
<h1>IndiaMart PDP Regression Report</h1>
<p style="color:#666">Mobile: {MOBILE} | OTP: {OTP} | Generated: {now}</p>
<div class="kpi">
  <div class="box total">Total: {total}</div>
  <div class="box pass">Passed: {passed}</div>
  <div class="box fail">Failed: {failed}</div>
  <div class="box skip">Skipped: {skipped}</div>
  <div class="box pass">Pass Rate: {pct}%</div>
</div>
<h2>Phase Summary</h2>
<table><thead><tr>
  <th>Phase</th><th>Passed</th><th>Failed</th><th>Skipped</th><th>Total</th><th>Pass Rate</th>
</tr></thead><tbody>
  {phase_summary(smoke,      "Phase 1 — Unidentified",    "#17a2b8")}
  {phase_summary(identified, "Phase 2 — Identified",      "#6f42c1")}
  {phase_summary(logged_in,  "Phase 3 — Fully Logged In", "#28a745")}
</tbody></table>
<h2>Phase 1 — Unidentified (No Login)</h2>
<table><thead><tr>
  <th>TC ID</th><th>Test Name</th><th>Status</th><th>Detail</th><th>Screenshot</th><th>Time</th>
</tr></thead><tbody>{phase_rows(smoke, "#17a2b8", "Unidentified")}</tbody></table>
<h2>Phase 2 — Identified (Mobile: {MOBILE})</h2>
<table><thead><tr>
  <th>TC ID</th><th>Test Name</th><th>Status</th><th>Detail</th><th>Screenshot</th><th>Time</th>
</tr></thead><tbody>{phase_rows(identified, "#6f42c1", "Identified")}</tbody></table>
<h2>Phase 3 — Fully Logged In (Mobile: {MOBILE} | OTP: {OTP})</h2>
<table><thead><tr>
  <th>TC ID</th><th>Test Name</th><th>Status</th><th>Detail</th><th>Screenshot</th><th>Time</th>
</tr></thead><tbody>{phase_rows(logged_in, "#28a745", "Fully Logged In")}</tbody></table>
</body></html>"""

    output_path.write_text(html, encoding="utf-8")
    print(f"\nReport saved: {output_path}")


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════
def main() -> None:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=HEADLESS, slow_mo=150)

        # ── Phase 1 + 2: share one context ───────────────────────────────────
        ctx12  = browser.new_context()
        page12 = ctx12.new_page()

        setup_unidentified(page12)
        smoke_results = run_suite(page12, SMOKE_MODULES, "Unidentified")

        login_identified(page12)
        identified_results = run_suite(page12, IDENTIFIED_MODULES, "Identified")

        ctx12.close()

        # ── Phase 3: fresh context — clean guest state ────────────────────────
        ctx3  = browser.new_context()
        page3 = ctx3.new_page()

        login_fully_logged_in(page3)
        logged_in_results = run_suite(page3, LOGGED_IN_MODULES, "Fully Logged In")

        ctx3.close()
        browser.close()

    # ── AI visual check on failures ───────────────────────────────────────────
    print("\n" + "="*60)
    print("  AI VISUAL VERIFICATION OF FAILURES")
    print("="*60)
    smoke_results      = ai_verify_failures(smoke_results,      page=None, mod_prefix="tests.")
    identified_results = ai_verify_failures(identified_results, page=None, mod_prefix="tests.")
    logged_in_results  = ai_verify_failures(logged_in_results,  page=None, mod_prefix="tests.")

    report_path = BASE_DIR.parent / "reports" / "pdp_regression_report.html"
    generate_regression_report(smoke_results, identified_results, logged_in_results, report_path)

    total_fail = sum(
        r["failed"] for r in smoke_results + identified_results + logged_in_results
    )
    print(f"\n{'='*60}")
    print(f"  DONE — Total failures: {total_fail}")
    print("="*60)
    sys.exit(1 if total_fail else 0)


if __name__ == "__main__":
    main()