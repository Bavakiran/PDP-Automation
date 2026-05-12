"""
Regression.py  —  IndiaMart PDP Regression Suite
=================================================
Phase 1 → UNIDENTIFIED    — test_01 to test_12, no login
Phase 2 → IDENTIFIED      — login via mobile only (no OTP), test_02 to test_12
Phase 3 → FULLY LOGGED IN — login via mobile + OTP (1411), test_02 to test_12

Usage:  python Regression.py
"""

import sys
import importlib
import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, Page

# ── Path setup ────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
from utils.helpers import TestResult

# ── Config ────────────────────────────────────────────────────────────────────
try:
    from config import BASE_URL, MOBILE_NUMBER, OTP, HEADLESS
except ImportError:
    BASE_URL      = "https://www.indiamart.com"
    MOBILE_NUMBER = "9500144262"   # Phase 2 — identified (no OTP needed)
    OTP           = ""
    HEADLESS      = False

# Phase 3 credentials
LOGGED_IN_MOBILE = "8610237001"
LOGGED_IN_OTP    = "1411"          # 4-digit static OTP

# ── Module lists ──────────────────────────────────────────────────────────────
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

LOGGED_IN_MODULES = IDENTIFIED_MODULES   # same test_02–test_12, different login state


# ══════════════════════════════════════════════════════════════════════════════
# SHARED HELPER — open the Sign In modal from BASE_URL
# ══════════════════════════════════════════════════════════════════════════════
def _open_signin_modal(page: Page) -> None:
    """Navigate to BASE_URL and open the Sign In modal."""
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(2500)

    # Dismiss popup/overlay if present
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

    # Click Sign In header trigger
    hd_pr = page.locator(".Hd_pr").first
    try:
        hd_pr.wait_for(state="visible", timeout=15000)
    except Exception:
        print("[Login] .Hd_pr not visible — reloading page")
        page.reload(wait_until="domcontentloaded")
        page.wait_for_timeout(2500)
        hd_pr.wait_for(state="visible", timeout=15000)
    hd_pr.click()
    page.wait_for_timeout(1500)

    # Click the Sign In modal link
    sign_in_link = page.locator("a.cont_s.cpo.Hd_db").first
    try:
        sign_in_link.wait_for(state="visible", timeout=5000)
        sign_in_link.click()
    except Exception:
        print("[Login] Sign In link hidden — JS click fallback")
        sign_in_link.evaluate("el => el.click()")
    page.wait_for_timeout(1000)


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 2 — IDENTIFIED (mobile only, no OTP)
# ══════════════════════════════════════════════════════════════════════════════
def login_identified(page: Page) -> None:
    """
    Enter mobile number and submit — this puts the session into 'identified' state.
    We do NOT complete OTP. After submit we navigate back to BASE_URL for tests.
    """
    print("\n" + "="*60)
    print("  PHASE 2 — IDENTIFIED (mobile only, no OTP)")
    print("="*60)

    _open_signin_modal(page)
    print("[Login P2] Sign In modal opened")

    # Enter mobile
    mobile_inp = page.locator("#mobile")
    mobile_inp.wait_for(state="visible", timeout=10000)
    mobile_inp.fill(MOBILE_NUMBER)
    print(f"[Login P2] Entered mobile: {MOBILE_NUMBER}")

    # Submit
    page.locator("#logintoidentify").click()
    print("[Login P2] Clicked Submit")

    # Wait for page to settle (may redirect or stay)
    page.wait_for_timeout(3000)
    print(f"[Login P2] Settled on: {page.url}")

    # Return to BASE_URL so tests start from a clean, known page
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(2000)
    print("[Login P2] Phase 2 identified — ready\n")


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 3 — FULLY LOGGED IN (mobile + OTP)
# ══════════════════════════════════════════════════════════════════════════════
def login_fully_logged_in(page: Page) -> None:
    """
    Full login flow:
      1. Open Sign In modal → enter mobile → Submit
      2. Page redirects to buyer.indiamart.com (multiple internal redirects)
      3. Poll URL until we land on buyer.indiamart.com (avoids wait_for_url timeout)
      4. Click button.login-btn "Continue with OTP"
      5. Fill input#first / second / third / fourth with OTP digits
      6. Login auto-submits after 4th digit — wait for redirect away from buyer domain
    """
    print("\n" + "="*60)
    print("  PHASE 3 — FULLY LOGGED IN (mobile + OTP)")
    print("="*60)

    _open_signin_modal(page)
    print("[Login P3] Sign In modal opened")

    # ── Step 1: enter mobile ─────────────────────────────────────
    mobile_inp = page.locator("#mobile")
    mobile_inp.wait_for(state="visible", timeout=10000)
    mobile_inp.fill(LOGGED_IN_MOBILE)
    print(f"[Login P3] Entered mobile: {LOGGED_IN_MOBILE}")

    # ── Step 2: submit ───────────────────────────────────────────
    page.locator("#logintoidentify").click()
    print("[Login P3] Clicked Submit")

    # ── Step 3: poll until URL lands on buyer.indiamart.com ──────
    # Using wait_for_url() with wait_until="domcontentloaded" causes a
    # TimeoutError because the site does 3+ internal redirects within
    # buyer.indiamart.com and the domcontentloaded event keeps resetting.
    # Polling page.url every 500 ms sidesteps this entirely.
    print("[Login P3] Waiting for buyer.indiamart.com redirect...")
    for _ in range(40):                     # max ~20 s
        page.wait_for_timeout(500)
        if "buyer.indiamart.com" in page.url:
            break
    else:
        raise RuntimeError(
            f"[Login P3] Never reached buyer.indiamart.com — stuck at: {page.url}"
        )
    # Let all internal redirects within buyer domain finish settling
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(2000)
    print(f"[Login P3] Landed on: {page.url}")

    # ── Step 4: click "Continue with OTP" ────────────────────────
    page.wait_for_timeout(2000)   # extra settle before button appears
    continue_btn = page.locator("button.login-btn")
    continue_btn.wait_for(state="visible", timeout=15000)
    print(f"[Login P3] Found button: '{continue_btn.inner_text().strip()}'")
    continue_btn.click()
    page.wait_for_timeout(1500)
    print("[Login P3] Clicked 'Continue with OTP'")

    # ── Step 5: fill OTP digits one by one ───────────────────────
    # DOM: <div id="auth_code1">
    #        <input id="first" maxlength="1">  <input id="second" ...>
    #        <input id="third" ...>            <input id="fourth" ...>
    #      </div>
    # onkeyup auto-advances focus; 400 ms gap lets it fire between fields.
    otp_first = page.locator("input#first")
    otp_first.wait_for(state="visible", timeout=15000)
    print("[Login P3] OTP modal visible — entering digits")

    for field_id, digit in zip(
        ["first", "second", "third", "fourth"],
        list(LOGGED_IN_OTP.ljust(4, "0"))
    ):
        inp = page.locator(f"input#{field_id}")
        inp.wait_for(state="visible", timeout=5000)
        inp.click()
        inp.fill(digit)
        page.wait_for_timeout(400)
        print(f"[Login P3] Entered '{digit}' → input#{field_id}")

    print(f"[Login P3] OTP {LOGGED_IN_OTP} entered — waiting for auto-login...")

    # ── Step 6: wait for auto-login (redirect away from buyer domain) ─
    try:
        page.wait_for_url(
            lambda url: "buyer.indiamart.com" not in url,
            timeout=15000
        )
        print(f"[Login P3] Auto-login successful — URL: {page.url}")
    except Exception:
        # No redirect — session may already be active or page stayed put
        page.wait_for_timeout(3000)
        print(f"[Login P3] Post-OTP URL (no redirect): {page.url}")

    print("[Login P3] Phase 3 login complete\n")


# ══════════════════════════════════════════════════════════════════════════════
# SUITE RUNNER
# ══════════════════════════════════════════════════════════════════════════════
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
                    "tc_id":      "--",
                    "name":       "Suite-level crash",
                    "status":     "FAIL",
                    "detail":     str(exc)[:200],
                    "screenshot": "",
                    "timestamp":  datetime.datetime.now().strftime("%H:%M:%S"),
                }],
                "total": 1, "passed": 0, "failed": 1, "skipped": 0,
            })
    return suite_results


# ══════════════════════════════════════════════════════════════════════════════
# HTML REPORT
# ══════════════════════════════════════════════════════════════════════════════
def _row_colour(status: str) -> str:
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

    # ── Helper: build detail rows for one phase ───────────────────
    def phase_rows(suites, badge_color, badge_text):
        html = ""
        for suite in suites:
            html += (
                f'<tr><td colspan="6" style="background:#343a40;color:#fff;'
                f'font-weight:bold;padding:8px 10px;font-size:13px">'
                f'{suite["suite"]}&nbsp;'
                f'<span style="background:{badge_color};color:#fff;padding:1px 8px;'
                f'border-radius:4px;font-size:11px">{badge_text}</span>'
                f'</td></tr>'
            )
            for tc in suite["results"]:
                sc = tc.get("screenshot", "")
                sc_cell = (
                    f'<a href="file:///{sc.replace(chr(92), "/")}" target="_blank">📷</a>'
                    if sc else ""
                )
                html += (
                    f'<tr style="background:{_row_colour(tc["status"])}">'
                    f'<td>{tc["tc_id"]}</td>'
                    f'<td>{tc["name"]}</td>'
                    f'<td><b>{tc["status"]}</b></td>'
                    f'<td style="font-size:12px">{tc.get("detail", "")}</td>'
                    f'<td style="text-align:center">{sc_cell}</td>'
                    f'<td>{tc["timestamp"]}</td>'
                    f'</tr>'
                )
        return html

    # ── Helper: phase summary row ─────────────────────────────────
    def phase_summary_row(suites, label, badge_color):
        p  = sum(r["passed"]  for r in suites)
        f  = sum(r["failed"]  for r in suites)
        s  = sum(r["skipped"] for r in suites)
        t  = sum(r["total"]   for r in suites)
        pc = round(p / t * 100, 1) if t else 0
        return (
            f'<tr>'
            f'<td><span style="background:{badge_color};color:#fff;padding:2px 10px;'
            f'border-radius:4px;font-size:12px">{label}</span></td>'
            f'<td style="color:#28a745;font-weight:bold">{p}</td>'
            f'<td style="color:#dc3545;font-weight:bold">{f}</td>'
            f'<td style="color:#856404;font-weight:bold">{s}</td>'
            f'<td>{t}</td>'
            f'<td>{pc}%</td>'
            f'</tr>'
        )

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>IndiaMart PDP — Full Regression Report</title>
  <style>
    body  {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
    h1    {{ color: #333; }}
    h2    {{ color: #333; margin: 28px 0 8px; font-size: 16px;
             border-left: 4px solid #343a40; padding-left: 8px; }}
    .kpi  {{ display: flex; gap: 16px; margin: 16px 0 24px; flex-wrap: wrap; }}
    .box  {{ padding: 12px 22px; border-radius: 8px; text-align: center;
             color: #fff; font-size: 18px; font-weight: bold; }}
    .pass  {{ background: #28a745; }}
    .fail  {{ background: #dc3545; }}
    .skip  {{ background: #ffc107; color: #333; }}
    .total {{ background: #17a2b8; }}
    table  {{ width: 100%; border-collapse: collapse; background: #fff;
              border-radius: 8px; overflow: hidden;
              box-shadow: 0 1px 4px rgba(0,0,0,.1); margin-bottom: 28px; }}
    th     {{ background: #343a40; color: #fff; padding: 10px; text-align: left; }}
    td     {{ padding: 8px 10px; border-bottom: 1px solid #dee2e6; font-size: 13px; }}
    tr:last-child td {{ border-bottom: none; }}
  </style>
</head>
<body>

<h1>IndiaMart PDP — Full Regression Report</h1>
<p style="color:#666">Generated: {now}</p>

<!-- ── Overall KPI ── -->
<div class="kpi">
  <div class="box total">Total: {total}</div>
  <div class="box pass">Passed: {passed}</div>
  <div class="box fail">Failed: {failed}</div>
  <div class="box skip">Skipped: {skipped}</div>
  <div class="box pass">Pass Rate: {pct}%</div>
</div>

<!-- ── Phase Summary ── -->
<h2>Phase Summary</h2>
<table>
  <thead>
    <tr>
      <th>Phase</th><th>Passed</th><th>Failed</th>
      <th>Skipped</th><th>Total</th><th>Pass Rate</th>
    </tr>
  </thead>
  <tbody>
    {phase_summary_row(smoke,      "Phase 1 — Unidentified",    "#17a2b8")}
    {phase_summary_row(identified, "Phase 2 — Identified",      "#6f42c1")}
    {phase_summary_row(logged_in,  "Phase 3 — Fully Logged In", "#28a745")}
  </tbody>
</table>

<!-- ── Phase 1 Detail ── -->
<h2>Phase 1 — Unidentified (No Login)</h2>
<table>
  <thead>
    <tr>
      <th>TC ID</th><th>Test Name</th><th>Status</th>
      <th>Detail</th><th>Screenshot</th><th>Time</th>
    </tr>
  </thead>
  <tbody>{phase_rows(smoke, "#17a2b8", "Unidentified")}</tbody>
</table>

<!-- ── Phase 2 Detail ── -->
<h2>Phase 2 — Identified (Mobile: {MOBILE_NUMBER})</h2>
<table>
  <thead>
    <tr>
      <th>TC ID</th><th>Test Name</th><th>Status</th>
      <th>Detail</th><th>Screenshot</th><th>Time</th>
    </tr>
  </thead>
  <tbody>{phase_rows(identified, "#6f42c1", "Identified")}</tbody>
</table>

<!-- ── Phase 3 Detail ── -->
<h2>Phase 3 — Fully Logged In (Mobile: {LOGGED_IN_MOBILE} | OTP: {LOGGED_IN_OTP})</h2>
<table>
  <thead>
    <tr>
      <th>TC ID</th><th>Test Name</th><th>Status</th>
      <th>Detail</th><th>Screenshot</th><th>Time</th>
    </tr>
  </thead>
  <tbody>{phase_rows(logged_in, "#28a745", "Fully Logged In")}</tbody>
</table>

</body>
</html>"""

    output_path.write_text(html, encoding="utf-8")
    print(f"\nReport saved → {output_path}")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main() -> None:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=HEADLESS, slow_mo=150)

        # ── Phase 1 (unidentified) ────────────────────────────────
        print("\n" + "="*60)
        print("  PHASE 1 — UNIDENTIFIED (no login)")
        print("="*60)
        ctx1  = browser.new_context()
        page1 = ctx1.new_page()
        smoke_results = run_suite(page1, SMOKE_MODULES, "Unidentified")
        ctx1.close()

        # ── Phase 2 (identified — mobile only) ───────────────────
        ctx2  = browser.new_context()
        page2 = ctx2.new_page()
        login_identified(page2)
        identified_results = run_suite(page2, IDENTIFIED_MODULES, "Identified")
        ctx2.close()

        # ── Phase 3 (fully logged in — mobile + OTP) ─────────────
        # Fresh context so there are no leftover cookies from Phase 2.
        # The Sign In modal only appears for guests, so we must start clean.
        ctx3  = browser.new_context()
        page3 = ctx3.new_page()
        login_fully_logged_in(page3)
        logged_in_results = run_suite(page3, LOGGED_IN_MODULES, "Fully Logged In")
        ctx3.close()

        browser.close()

    report_path = BASE_DIR.parent / "reports" / "pdp_regression_report.html"
    generate_regression_report(smoke_results, identified_results, logged_in_results, report_path)

    total_fail = sum(
        r["failed"]
        for r in smoke_results + identified_results + logged_in_results
    )
    print(f"\n{'='*60}")
    print(f"  DONE — Total failures: {total_fail}")
    print("="*60)
    sys.exit(1 if total_fail else 0)


if __name__ == "__main__":
    main()