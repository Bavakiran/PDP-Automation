"""
Shared helpers for IndiaMart PDP smoke tests.
"""
import os
import re
import time
from datetime import datetime
from pathlib import Path

from playwright.sync_api import Locator, Page, TimeoutError as PlaywrightTimeoutError

DIRECT_PDP_URL = "https://www.indiamart.com/proddetail/3-ply-face-mask-with-meltblown-filter-iso-sitra-certified-22661882162.html"

SEL = {
    "search_input": "input#search_string",
    "product_link": "a[href*='proddetail']",
    "product_title": "h1.center-heading, h1",
    "product_image": "img.main-img, img[class*='mainImg'], img[class*='prodImg'], .prod-img img, img[id*='prodImg'], img[src*='imimg'], picture img",
    "get_best_price": "button:has-text('Get Best Price'), a:has-text('Get Best Price')",
    "submit_requirement": "button:has-text('Submit Requirement'), a:has-text('Submit Requirement'), button:has-text('Submit requirement'), a:has-text('Submit requirement')",
    "contact_supplier": ".pdp_enq, button:has-text('Contact Supplier'), a:has-text('Contact Supplier'), button:has-text('Contact Seller'), a:has-text('Contact Seller')",
    "call_now": "button:has-text('Call Now'), a:has-text('Call Now'), a[href^='tel:']",
    "chat_now": "button:has-text('Chat Now'), a:has-text('Chat Now'), [id*='bl_form'], [class*='chatIcon'], [class*='chat-icon'], button[aria-label*='chat'], a[aria-label*='chat']",
    "hindi_link": "a.hindiLink, a[href*='hindi.indiamart.com']",
    "video_icon": ".ytub1.psimg, [class*='video'], .img-yt, [class*='yuTd'], iframe[src*='youtube']",
    "review_link": ".ratings-summary-box a, [class*='rating'] a, [class*='review'] a, .ratings-summary-box, [class*='rating']",
    "rating_summary": ".ratings-summary-box, [class*='review-carousel'], [class*='rating']",
    "company_link": "h2.fs15, .company-name a, a.company-link, a[href*='/impcat/'], a[href*='/company/'], a[href*='/profile/'], [class*='company'] a",
    "brochure_link": "a[href*='.pdf'], a:has-text('PDF'), a:has-text('Brochure'), a:has(span:has-text('Product Brochure')), span:has-text('Product Brochure')",
    "breadcrumb_container": "[class*='brdcrmb'], [class*='breadCrumb'], [class*='breadcrumb'], nav[aria-label*='breadcrumb'], [itemtype*='BreadcrumbList']",
    "breadcrumb_links": "[class*='brdcrmb'] a, [class*='breadCrumb'] a, [class*='breadcrumb'] a, nav[aria-label*='breadcrumb'] a, [itemtype*='BreadcrumbList'] a",
    "modal_form": ".frmcont, [id*='t0901'], [class*='be-frmcont'], [class*='enqModal'], [class*='quick']",
    "inline_form": "[id*='enq'], .benq, [class*='benq'], form",
    "mobile_input": "input[name*='mobile'], input[placeholder*='mobile'], input[type='tel']",
    "product_input": "input[name*='title'], input[id*='prodtitle'], textarea, input[placeholder*='Product']",
    "more_products_section": "section.tab-content, section, div",
    "company_section": "[class*='supp'], [class*='seller'], [class*='company'], [class*='comp-detail']",
    "footer_links": "footer a, [class*='footer'] a",
}

TIMEOUT = 30_000


def land_on_pdp_via_search(page: Page, keyword: str = "tmt bar") -> Page:
    page.goto("https://dir.indiamart.com", wait_until="domcontentloaded", timeout=60_000)
    page.wait_for_timeout(1500)
    page.locator(SEL["search_input"]).click(force=True)
    page.locator(SEL["search_input"]).fill(keyword)
    page.wait_for_timeout(1500)
    page.keyboard.press("Enter")
    page.wait_for_load_state("domcontentloaded", timeout=60_000)
    page.wait_for_timeout(2000)

    with page.context.expect_page() as new_page_info:
        page.locator(SEL["product_link"]).first.click()
    pdp = new_page_info.value
    pdp.wait_for_load_state("domcontentloaded", timeout=60_000)
    pdp.wait_for_timeout(2000)
    return pdp


def land_on_pdp_direct(page: Page, url: str = DIRECT_PDP_URL) -> None:
    page.goto(url, wait_until="domcontentloaded", timeout=60_000)
    page.wait_for_timeout(2000)


def first_visible(page: Page, selectors: list[str], timeout: int = 8_000) -> Locator:
    deadline = time.time() + (timeout / 1000)
    last_error = "No selector matched"
    while time.time() < deadline:
        for selector in selectors:
            locator = page.locator(selector)
            count = min(locator.count(), 8)
            for idx in range(count):
                candidate = locator.nth(idx)
                try:
                    if candidate.is_visible(timeout=250):
                        return candidate
                except Exception:
                    last_error = f"Selector not visible: {selector}"
        page.wait_for_timeout(200)
    raise AssertionError(last_error)


def click_locator(locator: Locator) -> None:
    locator.scroll_into_view_if_needed(timeout=5_000)
    try:
        locator.click(timeout=5_000)
    except Exception:
        locator.click(timeout=5_000, force=True)


def find_enquiry_surface(page: Page, timeout: int = 8_000) -> Locator:
    selectors = [
        SEL["modal_form"],
        f"{SEL['inline_form']}:has({SEL['mobile_input']})",
        SEL["inline_form"],
    ]
    return first_visible(page, selectors, timeout=timeout)


def click_and_expect_form(page: Page, selectors: list[str], timeout: int = 8_000) -> Locator:
    click_locator(first_visible(page, selectors, timeout=timeout))
    page.wait_for_timeout(1500)
    return find_enquiry_surface(page, timeout=timeout)


def dismiss_optional_popup(page: Page) -> None:
    for selector in [
        "button:has-text('Close')",
        "button:has-text('Cancel')",
        "[aria-label='Close']",
        "[aria-label='Cancel']",
        ".close",
    ]:
        try:
            locator = page.locator(selector).first
            if locator.count() > 0 and locator.is_visible(timeout=300):
                locator.click(timeout=1000, force=True)
                page.wait_for_timeout(500)
                return
        except Exception:
            pass
    try:
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
    except Exception:
        pass


def click_and_capture_page(page: Page, locator: Locator, timeout: int = 6_000) -> Page:
    try:
        with page.context.expect_page(timeout=timeout) as new_page_info:
            click_locator(locator)
        new_page = new_page_info.value
        new_page.wait_for_load_state("domcontentloaded", timeout=60_000)
        new_page.wait_for_timeout(1500)
        return new_page
    except PlaywrightTimeoutError:
        before = page.url
        click_locator(locator)
        try:
            page.wait_for_load_state("domcontentloaded", timeout=10_000)
        except Exception:
            pass
        page.wait_for_timeout(1500)
        assert page.url != before or page.locator(SEL["product_title"]).count() > 0, "Click did not open a target page"
        return page


def is_pdp(page: Page) -> bool:
    return "proddetail" in page.url and page.locator(SEL["product_title"]).count() > 0


def visible_count(page: Page, selectors: list[str]) -> int:
    total = 0
    for selector in selectors:
        locator = page.locator(selector)
        count = min(locator.count(), 12)
        for idx in range(count):
            try:
                if locator.nth(idx).is_visible(timeout=250):
                    total += 1
            except Exception:
                pass
        if total:
            return total
    return 0


class TestResult:
    def __init__(self, page: Page | None = None):
        self.results: list[dict] = []
        self.page = page
        run_id = os.environ.get("PDP_SCREENSHOT_RUN_ID") or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.screenshot_dir = Path(__file__).resolve().parents[1] / "reports" / "screenshots" / run_id
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

    def set_page(self, page: Page | None):
        self.page = page

    def _capture_screenshot(self, tc_id: str, status: str) -> str:
        if self.page is None or self.page.is_closed():
            return ""
        safe_tc_id = re.sub(r"[^A-Za-z0-9_-]+", "_", tc_id)
        screenshot_path = self.screenshot_dir / f"{safe_tc_id}_{status.lower()}.png"
        try:
            self.page.screenshot(path=str(screenshot_path), full_page=True)
            return str(screenshot_path.resolve())
        except Exception:
            return ""

    def add(self, tc_id: str, name: str, status: str, detail: str = ""):
        screenshot = self._capture_screenshot(tc_id, status)
        self.results.append({
            "tc_id": tc_id,
            "name": name,
            "status": status,
            "detail": detail,
            "screenshot": screenshot,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        })
        icon = "[PASS]" if status == "PASS" else ("[SKIP]" if status == "SKIP" else "[FAIL]")
        suffix = f": {detail}" if detail else ""
        message = f"  {icon} [{tc_id}] {name} - {status}{suffix}"
        print(message.encode("ascii", errors="replace").decode("ascii"))

    def summary(self) -> dict:
        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        skipped = sum(1 for r in self.results if r["status"] == "SKIP")
        return {"total": total, "passed": passed, "failed": failed, "skipped": skipped}


def safe_check(func):
    def wrapper(page, tr: TestResult, *args, **kwargs):
        try:
            return func(page, tr, *args, **kwargs)
        except Exception as exc:
            tc_id = kwargs.get("tc_id", "?")
            tr.add(tc_id, func.__name__, "FAIL", str(exc)[:120])
    return wrapper


def generate_html_report(all_results: list[dict], output_path: str = "reports/pdp_smoke_report.html"):
    Path(output_path).parent.mkdir(exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = sum(r["total"] for r in all_results)
    passed = sum(r["passed"] for r in all_results)
    failed = sum(r["failed"] for r in all_results)
    skipped = sum(r["skipped"] for r in all_results)
    pct = round(passed / total * 100, 1) if total else 0

    rows = ""
    for suite in all_results:
        for tc in suite.get("results", []):
            color = "#d4edda" if tc["status"] == "PASS" else ("#fff3cd" if tc["status"] == "SKIP" else "#f8d7da")
            screenshot_cell = (
                f"<a href=\"file:///{tc.get('screenshot', '').replace(chr(92), '/')}\">Open</a>"
                if tc.get("screenshot")
                else ""
            )
            rows += f"""<tr style="background:{color}">
              <td>{tc['tc_id']}</td>
              <td>{tc['name']}</td>
              <td><b>{tc['status']}</b></td>
              <td style="font-size:12px">{tc.get('detail', '')}</td>
              <td style="font-size:12px">{screenshot_cell}</td>
              <td>{tc['timestamp']}</td>
            </tr>"""

    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>IndiaMart PDP Smoke Report</title>
<style>
  body{{font-family:Arial,sans-serif;margin:20px;background:#f5f5f5}}
  h1{{color:#333}} .summary{{display:flex;gap:20px;margin:20px 0}}
  .box{{padding:15px 25px;border-radius:8px;text-align:center;color:#fff;font-size:18px;font-weight:bold}}
  .pass{{background:#28a745}} .fail{{background:#dc3545}} .skip{{background:#ffc107;color:#333}} .total{{background:#17a2b8}}
  table{{width:100%;border-collapse:collapse;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.1)}}
  th{{background:#343a40;color:#fff;padding:10px;text-align:left}}
  td{{padding:8px 10px;border-bottom:1px solid #dee2e6;font-size:13px}}
</style></head><body>
<h1>IndiaMart PDP Smoke Test Report</h1>
<p>Generated: {now}</p>
<div class="summary">
  <div class="box total">Total: {total}</div>
  <div class="box pass">Passed: {passed}</div>
  <div class="box fail">Failed: {failed}</div>
  <div class="box skip">Skipped: {skipped}</div>
  <div class="box pass">Pass Rate: {pct}%</div>
</div>
<table><thead><tr><th>TC ID</th><th>Test Name</th><th>Status</th><th>Detail</th><th>Screenshot</th><th>Time</th></tr></thead>
<tbody>{rows}</tbody></table></body></html>"""

    Path(output_path).write_text(html, encoding="utf-8")
    print(f"\nReport saved: {output_path}")
    return output_path
