"""
conftest.py  –  shared fixtures for the regression suite
Place this file inside the  tests/  folder.

Login flow (IndiaMart PDP):
  1. Click the "Sign In" trigger in the header  (.Hd_pr)
  2. Click the modal "Sign In" link              (.cont_s.cpo.Hd_db)
  3. Type mobile number into  #mobile
  4. Click Submit                                (#logintoidentify)
  5. Wait for OTP input and enter OTP            (#otp  –  update selector if different)
"""

import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# ── Pull these from config.py if you already have them there ──────────────────
try:
    from config import BASE_URL, MOBILE_NUMBER, OTP, HEADLESS
except ImportError:
    BASE_URL      = "https://www.indiamart.com"   # override in config.py
    MOBILE_NUMBER = "9500144262"
    OTP           = ""          # set via config.py or env var; leave blank to pause
    HEADLESS      = False
# ─────────────────────────────────────────────────────────────────────────────


def _build_driver(headless: bool = False) -> webdriver.Chrome:
    """Return a configured Chrome WebDriver instance."""
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    return driver


def _login(driver: webdriver.Chrome, base_url: str, mobile: str, otp: str) -> None:
    """
    Performs the full IndiaMart header login flow.

    Steps
    -----
    1. Open base URL
    2. Click header "Sign In" label  → class=Hd_pr
    3. Click modal "Sign In" link    → class=cont_s cpo Hd_db
    4. Enter mobile number           → id=mobile
    5. Click Submit                  → id=logintoidentify
    6. Enter OTP (if provided)       → id=otp  (update selector as needed)
    """
    wait = WebDriverWait(driver, 20)

    # 1. Navigate to the base URL
    driver.get(base_url)
    print(f"\n[Login] Opened: {base_url}")

    # 2. Click the "Sign In" header trigger
    sign_in_trigger = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, ".Hd_pr"))
    )
    sign_in_trigger.click()
    print("[Login] Clicked Sign In trigger (.Hd_pr)")

    # 3. Click the modal "Sign In" link
    sign_in_link = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "a.cont_s.cpo.Hd_db"))
    )
    sign_in_link.click()
    print("[Login] Clicked Sign In modal link (.cont_s.cpo.Hd_db)")

    # 4. Enter mobile number
    mobile_input = wait.until(
        EC.visibility_of_element_located((By.ID, "mobile"))
    )
    mobile_input.clear()
    mobile_input.send_keys(mobile)
    print(f"[Login] Entered mobile number: {mobile}")

    # 5. Click Submit
    submit_btn = wait.until(
        EC.element_to_be_clickable((By.ID, "logintoidentify"))
    )
    submit_btn.click()
    print("[Login] Clicked Submit (#logintoidentify)")

    # 6. Handle OTP
    #    – If OTP is known (e.g. from config), enter it automatically.
    #    – If blank, pause execution so a human can enter it manually.
    try:
        otp_input = wait.until(
            EC.visibility_of_element_located((By.ID, "otp"))   # ← update if selector differs
        )
        if otp:
            otp_input.clear()
            otp_input.send_keys(otp)
            print(f"[Login] Entered OTP: {otp}")

            # Click the OTP submit / verify button  (update selector as needed)
            otp_submit = driver.find_element(By.ID, "submitOtp")  # ← update if needed
            otp_submit.click()
            print("[Login] Submitted OTP")
        else:
            print("[Login] OTP field detected – please enter OTP manually in the browser.")
            print("[Login] Waiting 60 s for manual OTP entry …")
            time.sleep(60)   # give the user time to enter OTP manually

    except Exception:
        # OTP step may not always appear (e.g. auto-login in staging)
        print("[Login] No OTP field found – continuing without OTP step.")

    # 7. Confirm login succeeded (look for a post-login element, e.g. user avatar)
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".usr_lgnm, .loggedIn")))
        print("[Login] ✅ Login successful – logged-in element detected.\n")
    except Exception:
        print("[Login] ⚠️  Could not confirm login state – proceeding anyway.\n")


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def logged_in_driver():
    """
    Session-scoped fixture: creates ONE browser, logs in once,
    then shares the driver across all tests in the session.
    Browser is closed after the last test.
    """
    driver = _build_driver(headless=HEADLESS)
    _login(driver, BASE_URL, MOBILE_NUMBER, OTP)
    yield driver
    driver.quit()


@pytest.fixture(scope="session")
def driver(logged_in_driver):
    """
    Alias so that test files that already use `driver` as the fixture
    name work without any changes.
    """
    return logged_in_driver