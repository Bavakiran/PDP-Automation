import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL      = "https://www.indiamart.com"
MOBILE_PHASE2 = "9500144262"
HEADLESS      = False

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=HEADLESS, slow_mo=300)
    ctx  = browser.new_context()
    page = ctx.new_page()

    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(2500)

    page.locator(".Hd_pr").first.click()
    page.wait_for_timeout(1500)

    sign_in_link = page.locator("a.cont_s.cpo.Hd_db").first
    try:
        sign_in_link.wait_for(state="visible", timeout=5000)
        sign_in_link.click()
    except Exception:
        sign_in_link.evaluate("el => el.click()")
    page.wait_for_timeout(1000)

    mobile_inp = page.locator("#mobile")
    mobile_inp.wait_for(state="visible", timeout=10000)
    mobile_inp.fill(MOBILE_PHASE2)
    print(f"[Step 2] Filled first mobile: {MOBILE_PHASE2}")

    login_btn = page.locator("button.login-btn")
    login_btn.wait_for(state="visible", timeout=10000)
    print(f"[Step 3] Clicking: {login_btn.inner_text().strip()}")
    login_btn.click()
    page.wait_for_timeout(2000)

    visible_inputs = page.evaluate("""
        () => [...document.querySelectorAll('input')]
              .filter(el => el.offsetParent !== null)
              .map(el => ({id: el.id, name: el.name, type: el.type,
                           placeholder: el.placeholder, className: el.className}))
    """)
    print("\\n[Step 4] Visible inputs after clicking login-btn:")
    for inp in visible_inputs:
        print("  ", inp)

    print("\\nPress ENTER to close...")
    input()
    browser.close()
