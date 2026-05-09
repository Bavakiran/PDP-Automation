"""
Regression.py  —  IndiaMart PDP Regression Suite
=================================================
Phase 1 → UNIDENTIFIED  — test_01 to test_11, no login
Phase 2 → IDENTIFIED    — login first, then test_02 to test_11

Usage:  python Regression.py
"""

import sys
import importlib
import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, Page

# ── Path setup ────────────────────────────────────────────────────────────────
BASE_DIR  = Path(__file__).resolve().parent          # …/indiamart_pdp/
sys.path.insert(0, str(BASE_DIR))

from utils.helpers import TestResult                 # reuse existing class

# ── Config ────────────────────────────────────────────────────────────────────
try:
    from config import BASE_URL, MOBILE_NUMBER, OTP, HEADLESS
except ImportError:
    BASE_URL      = "https://www.indiamart.com"
    MOBILE_NUMBER = "9500144262"
    OTP           = ""       # blank → 60-second pause for manual OTP entry
    HEADLESS      = False

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


# ── Login ─────────────────────────────────────────────────────────────────────
def login(page: Page) -> None:
    import time
    print("\n" + "="*60)
    print("  PHASE 2 — LOGIN (Identified)")
    print("="*60)

    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle", timeout=15000)
    print(f"[Login] Opened: {BASE_URL}")

    page.locator(".Hd_pr").first.click()
    print("[Login] Clicked .Hd_pr")
    page.wait_for_timeout(1500)

    sign_in_link = page.locator("a.cont_s.cpo.Hd_db").first
    try:
        sign_in_link.wait_for(state="visible", timeout=5000)
        sign_in_link.click()
    except Exception:
        print("[Login] Element hidden — using JS click fallback")
        sign_in_link.evaluate("el => el.click()")
    print("[Login] Clicked Sign In link")
    page.wait_for_timeout(1000)

    mobile_inp = page.locator("#mobile")
    mobile_inp.wait_for(state="visible", timeout=10000)
    mobile_inp.fill(MOBILE_NUMBER)
    print(f"[Login] Entered mobile: {MOBILE_NUMBER}")

    page.locator("#logintoidentify").click()
    print("[Login] Clicked Submit")

    try:
        otp_inp = page.locator("#otp")
        otp_inp.wait_for(state="visible", timeout=15000)
        if OTP:
            otp_inp.fill(OTP)
            page.locator("#submitOtp").click()
            print(f"[Login] Entered OTP and submitted")
        else:
            print("[Login] OTP field visible — waiting 60 s for manual entry …")
            time.sleep(60)
    except Exception:
        print("[Login] No OTP field — continuing.")

    try:
        page.wait_for_selector(".usr_lgnm, .loggedIn", timeout=15000)
        print("[Login] ✅ Login confirmed\n")
    except Exception:
        print("[Login] ⚠️  Could not confirm login state — proceeding.\n")


# ── Suite runner ──────────────────────────────────────────────────────────────
def run_suite(page: Page, modules: list, phase_label: str) -> list:
    """Run each module's run(page) and return a list of result dicts
    compatible with helpers.generate_html_report."""
    suite_results = []
    for mod_name in modules:
        print(f"\n  ▶ {mod_name}")
        try:
            mod    = importlib.import_module(mod_name)
            result: TestResult = mod.run(page)
            s      = result.summary()
            suite_results.append({
                "suite":   f"[{phase_label}] {mod_name.split('.')[-1]}",
                "results": result.results,          # list of tc dicts (tc_id, name, status, detail, screenshot, timestamp)
                "total":   s["total"],
                "passed":  s["passed"],
                "failed":  s["failed"],
                "skipped": s["skipped"],
            })
            print(f"     ✅ {s['passed']}/{s['total']} passed  "
                  f"| {s['failed']} failed | {s['skipped']} skipped")
        except Exception as exc:
            print(f"     ❌ Suite crashed: {exc}")
            suite_results.append({
                "suite":   f"[{phase_label}] {mod_name.split('.')[-1]}",
                "results": [{
                    "tc_id": "—", "name": "Suite-level crash",
                    "status": "FAIL", "detail": str(exc)[:200],
                    "screenshot": "", "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
                }],
                "total": 1, "passed": 0, "failed": 1, "skipped": 0,
            })
    return suite_results


# ── HTML report (extends helpers style, adds phase sections) ──────────────────
def generate_regression_report(smoke: list, identified: list, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    all_suites = smoke + identified

    total   = sum(r["total"]   for r in all_suites)
    passed  = sum(r["passed"]  for r in all_suites)
    failed  = sum(r["failed"]  for r in all_suites)
    skipped = sum(r["skipped"] for r in all_suites)
    pct     = round(passed / total * 100, 1) if total else 0

    def phase_rows(suites, badge_color, badge_text):
        html = ""
        for suite in suites:
            # Suite header row spanning all columns
            html += f"""<tr>
              <td colspan="6" style="background:#343a40;color:#fff;
                  font-weight:bold;padding:8px 10px;font-size:13px">
                {suite['suite']}
                &nbsp;<span style="background:{badge_color};color:#fff;
                  padding:1px 8px;border-radius:4px;font-size:11px">{badge_text}</span>
              </td></tr>"""
            for tc in suite["results"]:
                color = ("#d4edda" if tc["status"] == "PASS"
                         else ("#fff3cd" if tc["status"] == "SKIP" else "#f8d7da"))
                screenshot_cell = (
                    f'<a href="file:///{tc.get("screenshot","").replace(chr(92),"/")}"'
                    f' target="_blank">Open</a>'
                    if tc.get("screenshot") else ""
                )
                html += f"""<tr style="background:{color}">
                  <td>{tc['tc_id']}</td>
                  <td>{tc['name']}</td>
                  <td><b>{tc['status']}</b></td>
                  <td style="font-size:12px">{tc.get('detail','')}</td>
                  <td style="font-size:12px">{screenshot_cell}</td>
                  <td>{tc['timestamp']}</td></tr>"""
        return html

    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>IndiaMart PDP Regression Report</title>
<style>
  body{{font-family:Arial,sans-serif;margin:20px;background:#f5f5f5}}
  h1,h2{{color:#333}}
  h2{{margin:28px 0 8px;font-size:16px;border-left:4px solid #343a40;padding-left:8px}}
  .summary{{display:flex;gap:20px;margin:20px 0;flex-wrap:wrap}}
  .box{{padding:15px 25px;border-radius:8px;text-align:center;color:#fff;
        font-size:18px;font-weight:bold}}
  .pass{{background:#28a745}} .fail{{background:#dc3545}}
  .skip{{background:#ffc107;color:#333}} .total{{background:#17a2b8}}
  table{{width:100%;border-collapse:collapse;background:#fff;border-radius:8px;
         overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.1);margin-bottom:24px}}
  th{{background:#343a40;color:#fff;padding:10px;text-align:left}}
  td{{padding:8px 10px;border-bottom:1px solid #dee2e6;font-size:13px}}
</style></head><body>
<h1>IndiaMart PDP Regression Report</h1>
<p>Generated: {now} &nbsp;|&nbsp; Mobile: {MOBILE_NUMBER}</p>

<div class="summary">
  <div class="box total">Total: {total}</div>
  <div class="box pass">Passed: {passed}</div>
  <div class="box fail">Failed: {failed}</div>
  <div class="box skip">Skipped: {skipped}</div>
  <div class="box pass">Pass Rate: {pct}%</div>
</div>

<h2>Phase 1 — Unidentified (No Login)</h2>
<table>
  <thead><tr>
    <th>TC ID</th><th>Test Name</th><th>Status</th>
    <th>Detail</th><th>Screenshot</th><th>Time</th>
  </tr></thead>
  <tbody>{phase_rows(smoke, "#17a2b8", "Unidentified")}</tbody>
</table>

<h2>Phase 2 — Identified (Logged In as {MOBILE_NUMBER})</h2>
<table>
  <thead><tr>
    <th>TC ID</th><th>Test Name</th><th>Status</th>
    <th>Detail</th><th>Screenshot</th><th>Time</th>
  </tr></thead>
  <tbody>{phase_rows(identified, "#28a745", "Identified")}</tbody>
</table>

</body></html>"""

    output_path.write_text(html, encoding="utf-8")
    print(f"\n📄 Report saved: {output_path}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=HEADLESS, slow_mo=150)
        context = browser.new_context()
        page    = context.new_page()

        # Phase 1 — Unidentified
        print("\n" + "="*60)
        print("  PHASE 1 — UNIDENTIFIED (no login)")
        print("="*60)
        smoke_results = run_suite(page, SMOKE_MODULES, "Unidentified")

        # Phase 2 — Login then Identified
        login(page)
        identified_results = run_suite(page, IDENTIFIED_MODULES, "Identified")

        browser.close()

    report_path = BASE_DIR.parent / "reports" / "pdp_regression_report.html"
    generate_regression_report(smoke_results, identified_results, report_path)

    total_fail = sum(r["failed"] for r in smoke_results + identified_results)
    print(f"\n{'='*60}")
    print(f"  DONE — Failures: {total_fail}")
    print("="*60)
    sys.exit(1 if total_fail else 0)


if __name__ == "__main__":
    main()