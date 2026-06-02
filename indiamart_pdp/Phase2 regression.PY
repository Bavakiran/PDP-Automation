"""
Phase2_Regression.py  —  Identified (mobile on www.indiamart.com + OTP on PDP popup)
======================================================================================
Login flow:
  1. www.indiamart.com -> Sign In -> enter mobile 8610237001 -> Submit
  2. Page redirects to buyer.indiamart.com — wait, do nothing
  3. Navigate to PDP URL
  4. Wait up to 15s for PDP OTP popup -> click GET OTP -> enter 1411

IMPORTANT: No background thread. All popup handling on main thread only.
Popup is checked before every test module run.

Usage:  python Phase2_Regression.py
"""

import sys
import importlib
import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, Page

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from utils.helpers import TestResult

BASE_URL = "https://www.indiamart.com"
PDP_URL  = "https://www.indiamart.com/proddetail/meatzza-chicken-meat-balls-21210423630.html?pos=2&kwd=chicken&tags=rk:B|plc:1|dt:0|db:01|prc:1|dtp:p|pfs:1|sv:T|rsf:gd|prv:385|ri:T_B_0_P|em:1-|-res:RC2|ktp:SA1|mtp:G|wc:1|lcf:3|cq:chennai|qr_nm:gl-gd|cs:17285|com-cf:nl|ptrs:na|mc:105842|cat:691|qry_typ:P|lang:en|tyr:1|qrd:260601|mrd:260601|prdt:260602|msf:ls|pfen:1|gli:U0G0I0|gc:Chennai|ic:Chennai|scw:1|emt:10|v=4|crs=xnh-city|r=4"
MOBILE   = "8610237001"
OTP      = "1411"
HEADLESS = False

MODULES = [
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


# ═══════════════════════════════════════════════════════════════════════════════
# PDP POPUP HANDLER  (main thread only — no threading)
# ═══════════════════════════════════════════════════════════════════════════════

def handle_pdp_otp_popup(page: Page, wait_ms: int = 2000) -> bool:
    """
    Check if 'Login with One Time Password' popup is visible.
    If yes: click GET OTP -> fill .lcp-otp-box inputs -> confirm.
    wait_ms: how long to wait for GET OTP button to appear.
    Returns True if handled, False if not present.
    """
    try:
        get_otp_btn = page.locator(
            "button:has-text('Get OTP'), button:has-text('GET OTP')"
        ).first
        if not get_otp_btn.is_visible(timeout=wait_ms):
            return False
    except Exception:
        return False

    print("\n[PDPPopup] *** Popup visible — handling ***")

    # Click GET OTP
    try:
        get_otp_btn.click()
        print("[PDPPopup] Clicked GET OTP")
    except Exception as e:
        print(f"[PDPPopup] Could not click GET OTP: {e}")
        return False

    page.wait_for_timeout(1500)

    # Wait for OTP input boxes
    try:
        page.locator("input.lcp-otp-box").first.wait_for(state="visible", timeout=10000)
    except Exception as e:
        print(f"[PDPPopup] OTP boxes not visible: {e}")
        return False

    print("[PDPPopup] Entering OTP digits")
    otp_boxes = page.locator("input.lcp-otp-box")
    digits    = list(OTP.ljust(4, "0"))

    for i in range(min(otp_boxes.count(), 4)):
        try:
            inp = otp_boxes.nth(i)
            inp.wait_for(state="visible", timeout=3000)
            inp.click()
            inp.press_sequentially(digits[i], delay=100)
            page.wait_for_timeout(300)
            print(f"[PDPPopup]   box[{i}] <- '{digits[i]}'")
        except Exception as e:
            print(f"[PDPPopup]   box[{i}] error: {e}")

    print(f"[PDPPopup] OTP entered: {OTP}")

    # Confirm popup closed
    confirmed = False
    try:
        page.wait_for_selector(
            "div[data-component='desktop/login-connect-popup']",
            state="hidden", timeout=10000
        )
        print("[PDPPopup] Popup closed — login confirmed")
        confirmed = True
    except Exception:
        pass

    if not confirmed:
        try:
            page.wait_for_selector("text='Login Successful'", state="visible", timeout=5000)
            print("[PDPPopup] Login Successful text detected")
            confirmed = True
        except Exception:
            pass

    if not confirmed:
        page.wait_for_timeout(3000)
        print("[PDPPopup] Could not confirm — continuing")
    else:
        page.wait_for_timeout(1500)

    print("[PDPPopup] Done\n")
    return True


def wait_for_pdp_popup(page: Page, timeout_ms: int = 15000) -> bool:
    """
    Used on the FIRST PDP landing after login.
    Actively waits up to timeout_ms for the popup to appear, then handles it.
    The popup appears with a delay after page load.
    """
    print(f"[PDPPopup] Waiting up to {timeout_ms//1000}s for OTP popup...")
    try:
        page.wait_for_selector(
            "button:has-text('Get OTP'), button:has-text('GET OTP')",
            state="visible",
            timeout=timeout_ms
        )
        print("[PDPPopup] GET OTP button appeared")
    except Exception:
        print("[PDPPopup] Popup did not appear within timeout")
        return False

    return handle_pdp_otp_popup(page, wait_ms=2000)


# ═══════════════════════════════════════════════════════════════════════════════
# LOGIN
# ═══════════════════════════════════════════════════════════════════════════════

def login(page: Page) -> None:
    print("\n" + "="*60)
    print("  PHASE 2 — IDENTIFIED")
    print("  Flow: www Sign In -> mobile -> (buyer: wait) -> PDP OTP popup")
    print("="*60)

    # Step 1: open www.indiamart.com
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(2500)

    # Dismiss interstitials
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

    # Step 2: click .Hd_pr Sign In trigger
    hd_pr = page.locator(".Hd_pr").first
    try:
        hd_pr.wait_for(state="visible", timeout=15000)
    except Exception:
        page.reload(wait_until="domcontentloaded")
        page.wait_for_timeout(2500)
        hd_pr.wait_for(state="visible", timeout=15000)
    hd_pr.click()
    page.wait_for_timeout(1500)
    print("[Login] Clicked .Hd_pr")

    # Step 3: click Sign In modal link
    sign_in_link = page.locator("a.cont_s.cpo.Hd_db").first
    try:
        sign_in_link.wait_for(state="visible", timeout=5000)
        sign_in_link.click()
    except Exception:
        print("[Login] Sign-in link hidden — JS fallback")
        sign_in_link.evaluate("el => el.click()")
    page.wait_for_timeout(1000)

    # Step 4: enter mobile
    mobile_inp = page.locator("#mobile")
    mobile_inp.wait_for(state="visible", timeout=10000)
    mobile_inp.click()
    mobile_inp.fill(MOBILE)
    print(f"[Login] Entered mobile: {MOBILE}")

    # Step 5: submit — redirect to buyer.indiamart.com, do NOT touch anything there
    page.locator("#logintoidentify").click()
    print("[Login] Clicked Submit — waiting for redirect (no OTP on buyer)")
    page.wait_for_timeout(3000)
    print(f"[Login] Settled on: {page.url}")

    # Step 6: go to PDP
    print(f"[Login] Going to PDP: {PDP_URL}")
    page.goto(PDP_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(2000)
    print(f"[Login] PDP loaded: {page.url}")

    # Step 7: reload the PDP — popup only appears on a refreshed page load
    print("[Login] Reloading PDP to trigger OTP popup...")
    page.reload(wait_until="domcontentloaded")
    page.wait_for_timeout(2000)
    print(f"[Login] PDP reloaded: {page.url}")

    # Step 8: wait for OTP popup to appear after reload
    handled = wait_for_pdp_popup(page, timeout_ms=15000)
    if not handled:
        print("[Login] Popup not shown after reload — will check again before tests")

    print("[Login] Phase 2 login complete\n")


# ═══════════════════════════════════════════════════════════════════════════════
# Suite runner — popup checked before every module (main thread)
# ═══════════════════════════════════════════════════════════════════════════════

def run_suite(page: Page) -> list:
    results = []

    for mod_name in MODULES:
        print(f"\n  >> {mod_name}")

        # Check and handle popup before each module — main thread, no threading
        handle_pdp_otp_popup(page, wait_ms=2000)

        try:
            mod    = importlib.import_module(mod_name)
            result: TestResult = mod.run(page)
            s      = result.summary()
            results.append({
                "suite":   mod_name.split(".")[-1],
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
            results.append({
                "suite":   mod_name.split(".")[-1],
                "results": [{
                    "tc_id": "--", "name": "Suite-level crash",
                    "status": "FAIL", "detail": str(exc)[:200],
                    "screenshot": "",
                    "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
                }],
                "total": 1, "passed": 0, "failed": 1, "skipped": 0,
            })

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# HTML report
# ═══════════════════════════════════════════════════════════════════════════════

def generate_report(results: list, output_path: Path) -> None:
    now     = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total   = sum(r["total"]   for r in results)
    passed  = sum(r["passed"]  for r in results)
    failed  = sum(r["failed"]  for r in results)
    skipped = sum(r["skipped"] for r in results)
    pct     = round(passed / total * 100, 1) if total else 0
    colour  = {"PASS": "#d4edda", "FAIL": "#f8d7da", "SKIP": "#fff3cd"}

    rows = ""
    for suite in results:
        rows += (
            f'<tr><td colspan="6" style="background:#343a40;color:#fff;font-weight:bold;'
            f'padding:8px 10px">{suite["suite"]}'
            f'&nbsp;<span style="background:#6f42c1;color:#fff;padding:1px 8px;'
            f'border-radius:4px;font-size:11px">Identified</span></td></tr>'
        )
        for tc in suite["results"]:
            sc = tc.get("screenshot", "")
            sc_cell = (
                f'<a href="file:///{sc.replace(chr(92), "/")}" target="_blank">screenshot</a>'
                if sc else ""
            )
            rows += (
                f'<tr style="background:{colour.get(tc["status"], "#fff")}">'
                f'<td>{tc["tc_id"]}</td><td>{tc["name"]}</td>'
                f'<td><b>{tc["status"]}</b></td>'
                f'<td style="font-size:12px">{tc.get("detail","")}</td>'
                f'<td style="text-align:center">{sc_cell}</td>'
                f'<td>{tc["timestamp"]}</td></tr>'
            )

    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Phase 2 — Identified Report</title>
<style>
  body{{font-family:Arial,sans-serif;margin:20px;background:#f5f5f5}}
  h1{{color:#333}}
  .kpi{{display:flex;gap:16px;margin:16px 0 24px;flex-wrap:wrap}}
  .box{{padding:12px 22px;border-radius:8px;text-align:center;color:#fff;
        font-size:18px;font-weight:bold}}
  .pass{{background:#28a745}} .fail{{background:#dc3545}}
  .skip{{background:#ffc107;color:#333}} .total{{background:#17a2b8}}
  table{{width:100%;border-collapse:collapse;background:#fff;border-radius:8px;
         overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.1)}}
  th{{background:#343a40;color:#fff;padding:10px;text-align:left}}
  td{{padding:8px 10px;border-bottom:1px solid #dee2e6;font-size:13px}}
</style></head><body>
<h1>Phase 2 — Identified Report</h1>
<p style="color:#666">Mobile: {MOBILE} | OTP: {OTP} | Generated: {now}</p>
<div class="kpi">
  <div class="box total">Total: {total}</div>
  <div class="box pass">Passed: {passed}</div>
  <div class="box fail">Failed: {failed}</div>
  <div class="box skip">Skipped: {skipped}</div>
  <div class="box pass">Pass Rate: {pct}%</div>
</div>
<table><thead><tr>
  <th>TC ID</th><th>Test Name</th><th>Status</th>
  <th>Detail</th><th>Screenshot</th><th>Time</th>
</tr></thead><tbody>{rows}</tbody></table>
</body></html>"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"\nReport: {output_path}")


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=HEADLESS, slow_mo=150)
        page    = browser.new_context().new_page()

        login(page)
        results = run_suite(page)
        browser.close()

    report_path = BASE_DIR.parent / "reports" / "pdp_phase2_report.html"
    generate_report(results, report_path)

    total_fail = sum(r["failed"] for r in results)
    print(f"\n{'='*60}")
    print(f"  DONE — Failures: {total_fail}")
    print("="*60)
    sys.exit(1 if total_fail else 0)


if __name__ == "__main__":
    main()