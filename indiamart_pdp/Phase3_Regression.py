"""
Phase3_Regression.py  -  Fully Logged In (mobile + OTP)
"""
import sys, importlib, datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, Page

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
from utils.helpers import TestResult

BASE_URL = "https://www.indiamart.com"
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

def login(page: Page) -> None:
    print("\n" + "="*60)
    print("  PHASE 3 - FULLY LOGGED IN (mobile + OTP)")
    print("="*60)
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(2500)
    try:
        skip = page.locator("a#idfpclose,a.idfpclose,a.skptxt,a:has-text('Skip'),span:has-text('Skip')").first
        if skip.is_visible(timeout=2000):
            skip.click(force=True)
            page.wait_for_timeout(800)
    except Exception:
        pass
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
    sign_in_link = page.locator("a.cont_s.cpo.Hd_db").first
    try:
        sign_in_link.wait_for(state="visible", timeout=5000)
        sign_in_link.click()
    except Exception:
        print("[Login] Hidden - JS fallback")
        sign_in_link.evaluate("el => el.click()")
    page.wait_for_timeout(1000)
    mobile_inp = page.locator("#mobile")
    mobile_inp.wait_for(state="visible", timeout=10000)
    mobile_inp.fill(MOBILE)
    print(f"[Login] Entered mobile: {MOBILE}")
    page.locator("#logintoidentify").click()
    print("[Login] Clicked Submit")
    page.wait_for_timeout(2500)
    print(f"[Login] Settled on: {page.url}")
    continue_btn = page.locator("button.login-btn")
    try:
        continue_btn.wait_for(state="visible", timeout=15000)
    except Exception:
        try:
            page.wait_for_url("*buyer.indiamart.com*", timeout=10000)
            page.wait_for_load_state("domcontentloaded", timeout=10000)
            page.wait_for_timeout(1000)
            print(f"[Login] Redirected to: {page.url}")
            continue_btn.wait_for(state="visible", timeout=10000)
        except Exception as e:
            raise Exception(f"button.login-btn not found on {page.url}: {e}")
    print(f"[Login] Found: '{continue_btn.inner_text().strip()}'")
    continue_btn.click()
    page.wait_for_timeout(1000)
    print("[Login] Clicked Continue with OTP")
    otp_first = page.locator("input#first")
    otp_first.wait_for(state="visible", timeout=15000)
    print("[Login] OTP modal visible - entering digits")
    for field_id, digit in zip(["first","second","third","fourth"], list(OTP.ljust(4,"0"))):
        inp = page.locator(f"input#{field_id}")
        inp.wait_for(state="visible", timeout=5000)
        inp.click()
        inp.fill(digit)
        page.wait_for_timeout(300)
    print(f"[Login] Entered OTP: {OTP}")
    otp_accepted = False
    try:
        page.wait_for_selector("p#after_verified", state="visible", timeout=5000)
        print("[Login] Login Successful message detected")
        otp_accepted = True
    except Exception:
        pass
    if not otp_accepted:
        try:
            page.wait_for_function(
                "() => !window.location.href.includes('buyer.indiamart.com') || document.querySelector('p#after_verified')",
                timeout=15000)
            print("[Login] Post-OTP redirect detected")
            otp_accepted = True
        except Exception:
            pass
    if not otp_accepted:
        page.wait_for_timeout(3000)
    print(f"[Login] Phase 3 login complete - URL: {page.url}\n")

def run_suite(page: Page) -> list:
    results = []
    for mod_name in MODULES:
        print(f"\n  >> {mod_name}")
        try:
            mod = importlib.import_module(mod_name)
            result: TestResult = mod.run(page)
            s = result.summary()
            results.append({"suite": mod_name.split(".")[-1], "results": result.results,
                "total": s["total"], "passed": s["passed"], "failed": s["failed"], "skipped": s["skipped"]})
            print(f"     {s['passed']}/{s['total']} passed | {s['failed']} failed | {s['skipped']} skipped")
        except Exception as exc:
            print(f"     CRASHED: {exc}")
            results.append({"suite": mod_name.split(".")[-1],
                "results": [{"tc_id":"--","name":"Suite crash","status":"FAIL","detail":str(exc)[:200],"screenshot":"","timestamp":datetime.datetime.now().strftime("%H:%M:%S")}],
                "total":1,"passed":0,"failed":1,"skipped":0})
    return results

def generate_report(results, output_path):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total=sum(r["total"] for r in results); passed=sum(r["passed"] for r in results)
    failed=sum(r["failed"] for r in results); skipped=sum(r["skipped"] for r in results)
    pct=round(passed/total*100,1) if total else 0
    colour={"PASS":"#d4edda","FAIL":"#f8d7da","SKIP":"#fff3cd"}
    rows=""
    for suite in results:
        rows+=f'<tr><td colspan="6" style="background:#343a40;color:#fff;font-weight:bold;padding:8px 10px">{suite["suite"]} <span style="background:#28a745;color:#fff;padding:1px 8px;border-radius:4px;font-size:11px">Fully Logged In</span></td></tr>'
        for tc in suite["results"]:
            sc=tc.get("screenshot","")
            sc_cell=f'<a href="file:///{sc.replace(chr(92),"/")}" target="_blank">screenshot</a>' if sc else ""
            rows+=f'<tr style="background:{colour.get(tc["status"],"#fff")}"><td>{tc["tc_id"]}</td><td>{tc["name"]}</td><td><b>{tc["status"]}</b></td><td style="font-size:12px">{tc.get("detail","")}</td><td>{sc_cell}</td><td>{tc["timestamp"]}</td></tr>'
    html=f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>Phase 3 Report</title>
<style>body{{font-family:Arial,sans-serif;margin:20px;background:#f5f5f5}}h1{{color:#333}}
.kpi{{display:flex;gap:16px;margin:16px 0 24px}}.box{{padding:12px 22px;border-radius:8px;text-align:center;color:#fff;font-size:18px;font-weight:bold}}
.pass{{background:#28a745}}.fail{{background:#dc3545}}.skip{{background:#ffc107;color:#333}}.total{{background:#17a2b8}}
table{{width:100%;border-collapse:collapse;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.1)}}
th{{background:#343a40;color:#fff;padding:10px;text-align:left}}td{{padding:8px 10px;border-bottom:1px solid #dee2e6;font-size:13px}}</style></head><body>
<h1>Phase 3 - Fully Logged In Report</h1><p style="color:#666">Mobile: {MOBILE} | OTP: {OTP} | Generated: {now}</p>
<div class="kpi"><div class="box total">Total: {total}</div><div class="box pass">Passed: {passed}</div>
<div class="box fail">Failed: {failed}</div><div class="box skip">Skipped: {skipped}</div><div class="box pass">Pass Rate: {pct}%</div></div>
<table><thead><tr><th>TC ID</th><th>Test Name</th><th>Status</th><th>Detail</th><th>Screenshot</th><th>Time</th></tr></thead>
<tbody>{rows}</tbody></table></body></html>"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"\nReport: {output_path}")

def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=HEADLESS, slow_mo=150)
        page = browser.new_context().new_page()
        login(page)
        results = run_suite(page)
        browser.close()
    report_path = BASE_DIR.parent / "reports" / "pdp_phase3_report.html"
    generate_report(results, report_path)
    total_fail = sum(r["failed"] for r in results)
    print(f"\nDONE - Failures: {total_fail}")
    sys.exit(1 if total_fail else 0)

if __name__ == "__main__":
    main()
