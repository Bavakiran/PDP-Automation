"""
Regression.py  —  IndiaMart PDP Regression Suite
=================================================
Phase 1 → UNIDENTIFIED   — test_01 to test_12, no login
Phase 2 → IDENTIFIED     — login via mobile (no OTP), test_02 to test_12
Phase 3 → FULLY LOGGED IN — login via mobile + OTP (1411), test_02 to test_12

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

# ── Config ────────────────────────────────────────────────────────────────────
try:
    from config import BASE_URL, MOBILE_NUMBER, OTP, HEADLESS
except ImportError:
    BASE_URL      = "https://www.indiamart.com"
    MOBILE_NUMBER = "9500144262"    # Phase 2 — identified (no OTP needed)
    OTP           = ""
    HEADLESS      = False

# Phase 3 credentials (static OTP)
LOGGED_IN_MOBILE = "8610237001"
LOGGED_IN_OTP    = "1411"           # 4-digit static OTP

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

LOGGED_IN_MODULES = IDENTIFIED_MODULES   # same test_02–test_12, different login state


# ── Shared: open header Sign In modal ────────────────────────────────────────
def _open_signin_modal(page: Page) -> None:
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(2500)  # domcontentloaded already done; avoid networkidle (IndiaMart keeps connections open)

    page.locator(".Hd_pr").first.click()
    page.wait_for_timeout(1500)

    sign_in_link = page.locator("a.cont_s.cpo.Hd_db").first
    try:
        sign_in_link.wait_for(state="visible", timeout=5000)
        sign_in_link.click()
    except Exception:
        print("[Login] Element hidden — JS click fallback")
        sign_in_link.evaluate("el => el.click()")
    page.wait_for_timeout(1000)


# ── Phase 2 login: mobile only (no OTP) ──────────────────────────────────────
def login_identified(page: Page) -> None:
    import time
    print("\n" + "="*60)
    print("  PHASE 2 — LOGIN IDENTIFIED (mobile only)")
    print("="*60)

    _open_signin_modal(page)
    print(f"[Login] Opened Sign In modal")

    mobile_inp = page.locator("#mobile")
    mobile_inp.wait_for(state="visible", timeout=10000)
    mobile_inp.fill(MOBILE_NUMBER)
    print(f"[Login] Entered mobile: {MOBILE_NUMBER}")

    page.locator("#logintoidentify").click()
    print("[Login] Clicked Submit")

    try:
        otp_first = page.locator("input#first")
        otp_first.wait_for(state="visible", timeout=15000)
        if OTP:
            digits = list(OTP.ljust(4))
            for field_id, digit in zip(["first","second","third","fourth"], digits):
                page.locator(f"input#{field_id}").fill(digit)
            page.locator("button.login-btn").click()
            print(f"[Login] Entered OTP and clicked Continue with OTP")
        else:
            print("[Login] OTP screen appeared — waiting 60 s for manual entry …")
            time.sleep(60)
    except Exception:
        print("[Login] No OTP screen — continuing.")

    try:
        page.wait_for_selector(".usr_lgnm, .loggedIn, p#after_verified", timeout=15000)
        print("[Login] ✅ Phase 2 login confirmed\n")
    except Exception:
        print("[Login] ⚠️  Could not confirm Phase 2 login — proceeding.\n")


# ── Phase 3 login: mobile + static OTP ───────────────────────────────────────
def login_fully_logged_in(page: Page) -> None:
    """
    Confirmed login flow (from DOM + browser screenshots):
      1. www.indiamart.com → Sign In modal → enter LOGGED_IN_MOBILE → Submit
      2. Redirects to buyer.indiamart.com
      3. Click button.login-btn "Continue with OTP"  ← must click BEFORE OTP inputs appear
      4. OTP modal (div#auth_code1): fill input#first/second/third/fourth
      5. OTP auto-submits via onkeyup; confirm via p#after_verified
    """
    print("\n" + "="*60)
    print("  PHASE 3 — FULLY LOGGED IN (mobile + OTP)")
    print("="*60)

    _open_signin_modal(page)
    print("[Login] Opened Sign In modal")

    # Step 1: enter mobile
    mobile_inp = page.locator("#mobile")
    mobile_inp.wait_for(state="visible", timeout=10000)
    mobile_inp.fill(LOGGED_IN_MOBILE)
    print(f"[Login] Entered mobile: {LOGGED_IN_MOBILE}")

    # Step 2: submit
    page.locator("#logintoidentify").click()
    print("[Login] Clicked Submit (#logintoidentify)")

    # Step 3: wait for page to settle after Submit
    # The redirect destination varies by account:
    #   - Some accounts → buyer.indiamart.com (then button.login-btn is there)
    #   - Other accounts → stay on www.indiamart.com (button.login-btn appears in modal)
    # So we just wait for the button regardless of which page we land on.
    page.wait_for_timeout(2500)
    print(f"[Login] Settled on: {page.url}")

    # Step 4: click "Continue with OTP" — triggers OTP input modal
    # Works on both www.indiamart.com and buyer.indiamart.com
    continue_btn = page.locator("button.login-btn")
    try:
        continue_btn.wait_for(state="visible", timeout=15000)
    except Exception:
        # If still not found, try after a redirect (buyer.indiamart.com)
        try:
            page.wait_for_url("*buyer.indiamart.com*", timeout=10000)
            page.wait_for_load_state("domcontentloaded", timeout=10000)
            page.wait_for_timeout(1000)
            print(f"[Login] Late redirect to: {page.url}")
            continue_btn.wait_for(state="visible", timeout=10000)
        except Exception as e:
            raise Exception(f"button.login-btn not found on {page.url}: {e}")
    print(f"[Login] Found: '{continue_btn.inner_text().strip()}'")
    continue_btn.click()
    page.wait_for_timeout(1000)
    print("[Login] Clicked 'Continue with OTP'")

    # Step 5: OTP modal appears — fill input#first / second / third / fourth
    # DOM: <div id="auth_code1">
    #        <input id="first" maxlength="1"> <input id="second" ...>
    #        <input id="third" ...>           <input id="fourth" ...>
    #      </div>
    otp_first = page.locator("input#first")
    otp_first.wait_for(state="visible", timeout=15000)
    print("[Login] OTP modal visible — entering digits")

    digits     = list(LOGGED_IN_OTP.ljust(4, "0"))   # ["1","4","1","1"]
    otp_fields = ["first", "second", "third", "fourth"]
    for i, (field_id, digit) in enumerate(zip(otp_fields, digits)):
        inp = page.locator(f"input#{field_id}")
        inp.wait_for(state="visible", timeout=5000)
        inp.click()
        inp.fill(digit)
        page.wait_for_timeout(300)   # let onkeyup auto-advance fire between fields

    print(f"[Login] Entered OTP: {LOGGED_IN_OTP}")

    # Step 6: confirm login
    # p#after_verified ("Login Successful") appears briefly then page redirects.
    # Catch it in a short window first; if missed, wait for the redirect itself.
    otp_accepted = False

    try:
        # Short window to catch the flash message
        page.wait_for_selector("p#after_verified", state="visible", timeout=5000)
        print("[Login] ✅ 'Login Successful' message detected")
        otp_accepted = True
    except Exception:
        pass

    if not otp_accepted:
        # Message was missed — wait for post-login redirect away from OTP page
        try:
            page.wait_for_function(
                "() => !window.location.href.includes('buyer.indiamart.com') "
                "|| document.querySelector('p#after_verified')",
                timeout=15000
            )
            print("[Login] ✅ Post-OTP redirect detected — login confirmed")
            otp_accepted = True
        except Exception:
            pass

    if not otp_accepted:
        # Last resort: just wait and check current URL
        page.wait_for_timeout(3000)
        current_url = page.url
        if "buyer.indiamart.com" not in current_url or "login" not in current_url.lower():
            print(f"[Login] ✅ Login confirmed via URL: {current_url}")
        else:
            print(f"[Login] ⚠️  Login state unclear — URL: {current_url}\n")

    print("[Login] ✅ Phase 3 login complete\n")


# ── Suite runner ──────────────────────────────────────────────────────────────
def run_suite(page: Page, modules: list, phase_label: str) -> list:
    suite_results = []
    for mod_name in modules:
        print(f"\n  ▶ {mod_name}")
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
            print(f"     ✅ {s['passed']}/{s['total']} passed"
                  f" | {s['failed']} failed | {s['skipped']} skipped")
        except Exception as exc:
            print(f"     ❌ Crashed: {exc}")
            suite_results.append({
                "suite":   f"[{phase_label}] {mod_name.split('.')[-1]}",
                "results": [{
                    "tc_id": "—", "name": "Suite-level crash",
                    "status": "FAIL", "detail": str(exc)[:200],
                    "screenshot": "",
                    "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
                }],
                "total": 1, "passed": 0, "failed": 1, "skipped": 0,
            })
    return suite_results


# ── HTML report ───────────────────────────────────────────────────────────────
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
            html += f"""<tr>
              <td colspan="6" style="background:#343a40;color:#fff;font-weight:bold;
                  padding:8px 10px;font-size:13px">
                {suite['suite']}
                &nbsp;<span style="background:{badge_color};color:#fff;padding:1px 8px;
                  border-radius:4px;font-size:11px">{badge_text}</span>
              </td></tr>"""
            for tc in suite["results"]:
                sc = tc.get("screenshot", "")
                sc_cell = (f'<a href="file:///{sc.replace(chr(92),"/")}" target="_blank">📷</a>'
                           if sc else "")
                html += f"""<tr style="background:{_colour(tc['status'])}">
                  <td>{tc['tc_id']}</td>
                  <td>{tc['name']}</td>
                  <td><b>{tc['status']}</b></td>
                  <td style="font-size:12px">{tc.get('detail','')}</td>
                  <td style="font-size:12px;text-align:center">{sc_cell}</td>
                  <td>{tc['timestamp']}</td></tr>"""
        return html

    def phase_summary(suites, label, badge_color):
        p = sum(r["passed"]  for r in suites)
        f = sum(r["failed"]  for r in suites)
        s = sum(r["skipped"] for r in suites)
        t = sum(r["total"]   for r in suites)
        pc = round(p / t * 100, 1) if t else 0
        return f"""<tr>
          <td><span style="background:{badge_color};color:#fff;padding:2px 10px;
              border-radius:4px;font-size:12px">{label}</span></td>
          <td style="color:#28a745;font-weight:bold">{p}</td>
          <td style="color:#dc3545;font-weight:bold">{f}</td>
          <td style="color:#856404;font-weight:bold">{s}</td>
          <td>{t}</td><td>{pc}%</td></tr>"""

    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>IndiaMart PDP Regression Report</title>
<style>
  body{{font-family:Arial,sans-serif;margin:20px;background:#f5f5f5}}
  h1,h2{{color:#333}}
  h2{{margin:28px 0 8px;font-size:16px;border-left:4px solid #343a40;padding-left:8px}}
  .kpi{{display:flex;gap:16px;margin:16px 0 24px;flex-wrap:wrap}}
  .box{{padding:12px 22px;border-radius:8px;text-align:center;color:#fff;
        font-size:18px;font-weight:bold}}
  .pass{{background:#28a745}} .fail{{background:#dc3545}}
  .skip{{background:#ffc107;color:#333}} .total{{background:#17a2b8}}
  table{{width:100%;border-collapse:collapse;background:#fff;border-radius:8px;
         overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.1);margin-bottom:24px}}
  th{{background:#343a40;color:#fff;padding:10px;text-align:left}}
  td{{padding:8px 10px;border-bottom:1px solid #dee2e6;font-size:13px}}
  tr:last-child td{{border-bottom:none}}
</style></head><body>
<h1>IndiaMart PDP Regression Report</h1>
<p style="color:#666">Generated: {now}</p>

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
  {phase_summary(smoke,       "Phase 1 — Unidentified",    "#17a2b8")}
  {phase_summary(identified,  "Phase 2 — Identified",      "#6f42c1")}
  {phase_summary(logged_in,   "Phase 3 — Fully Logged In", "#28a745")}
</tbody></table>

<h2>Phase 1 — Unidentified (No Login)</h2>
<table><thead><tr>
  <th>TC ID</th><th>Test Name</th><th>Status</th><th>Detail</th><th>Screenshot</th><th>Time</th>
</tr></thead><tbody>{phase_rows(smoke, "#17a2b8", "Unidentified")}</tbody></table>

<h2>Phase 2 — Identified (Mobile: {MOBILE_NUMBER})</h2>
<table><thead><tr>
  <th>TC ID</th><th>Test Name</th><th>Status</th><th>Detail</th><th>Screenshot</th><th>Time</th>
</tr></thead><tbody>{phase_rows(identified, "#6f42c1", "Identified")}</tbody></table>

<h2>Phase 3 — Fully Logged In (Mobile: {LOGGED_IN_MOBILE} | OTP: {LOGGED_IN_OTP})</h2>
<table><thead><tr>
  <th>TC ID</th><th>Test Name</th><th>Status</th><th>Detail</th><th>Screenshot</th><th>Time</th>
</tr></thead><tbody>{phase_rows(logged_in, "#28a745", "Fully Logged In")}</tbody></table>

</body></html>"""

    output_path.write_text(html, encoding="utf-8")
    print(f"\n📄 Report saved: {output_path}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=HEADLESS, slow_mo=150)

        # ── Phase 1 + 2: share one context (Phase 2 logs in on top of Phase 1) ─
        ctx12  = browser.new_context()
        page12 = ctx12.new_page()

        print("\n" + "="*60)
        print("  PHASE 1 — UNIDENTIFIED (no login)")
        print("="*60)
        smoke_results = run_suite(page12, SMOKE_MODULES, "Unidentified")

        login_identified(page12)
        identified_results = run_suite(page12, IDENTIFIED_MODULES, "Identified")

        ctx12.close()   # discard Phase 1+2 session/cookies

        # ── Phase 3: fresh context — no cookies, starts as guest ─────────────
        # Must use a new context because ctx12 is already logged in;
        # the Sign In modal (a.cont_s.cpo.Hd_db) only appears for logged-out users.
        ctx3  = browser.new_context()
        page3 = ctx3.new_page()

        login_fully_logged_in(page3)
        logged_in_results = run_suite(page3, LOGGED_IN_MODULES, "Fully Logged In")

        ctx3.close()
        browser.close()

    report_path = BASE_DIR.parent / "reports" / "pdp_regression_report.html"
    generate_regression_report(smoke_results, identified_results, logged_in_results, report_path)

    total_fail = sum(r["failed"] for r in smoke_results + identified_results + logged_in_results)
    print(f"\n{'='*60}")
    print(f"  DONE — Total failures: {total_fail}")
    print("="*60)
    sys.exit(1 if total_fail else 0)


if __name__ == "__main__":
    main()