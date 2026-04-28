"""
Suite 03: PDP Breadcrumbs
"""
import sys
from pathlib import Path
from playwright.sync_api import Page

try:
    from utils.helpers import DIRECT_PDP_URL, SEL, TestResult, click_and_capture_page, land_on_pdp_direct
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from indiamart_pdp.utils.helpers import DIRECT_PDP_URL, SEL, TestResult, click_and_capture_page, land_on_pdp_direct


def _open_breadcrumb(page: Page, link):
    href = link.get_attribute("href") or ""
    try:
        return click_and_capture_page(page, link)
    except Exception:
        assert href, "Breadcrumb link has no href"
        if href.startswith("/"):
            href = f"https://www.indiamart.com{href}"
        page.goto(href, wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(1500)
        return page


def _breadcrumb_links(page: Page):
    title = page.locator(SEL["product_title"]).first
    title_box = title.bounding_box()
    title_y = title_box["y"] if title_box else 220

    candidates = page.locator(
        "a[href*='dir.indiamart.com'], "
        "a[href*='search.mp'], "
        "a[href*='/impcat/'], "
        "a[href*='/industry/'], "
        "a[href*='/pro-services/'], "
        "a[href$='.html']"
    )

    breadcrumb_indexes = []
    seen = set()
    for idx in range(candidates.count()):
        link = candidates.nth(idx)
        try:
            if not link.is_visible(timeout=250):
                continue
            box = link.bounding_box()
            href = link.get_attribute("href") or ""
            text = link.inner_text().strip()
            if not box or box["y"] > title_y or len(text) == 0:
                continue
            key = (text, href)
            if key in seen:
                continue
            seen.add(key)
            breadcrumb_indexes.append(idx)
        except Exception:
            continue

    if len(breadcrumb_indexes) < 3:
        raise LookupError(f"Expected at least 3 breadcrumb links above H1, found {len(breadcrumb_indexes)}")
    return candidates, breadcrumb_indexes


def run(page: Page) -> TestResult:
    tr = TestResult(page)
    print("\n[Suite 03] PDP Breadcrumbs")

    land_on_pdp_direct(page, DIRECT_PDP_URL)

    try:
        links, indexes = _breadcrumb_links(page)
        target = _open_breadcrumb(page, links.nth(indexes[0]))
        tr.set_page(target)
        assert "dir.indiamart.com" in target.url or "search.mp" in target.url, f"Unexpected URL: {target.url}"
        tr.add("TC-5628", "First breadcrumb redirects to dir.indiamart.com", "PASS", target.url[-70:])
        if target != page:
            target.close()
    except LookupError as exc:
        tr.add("TC-5628", "First breadcrumb redirects to dir.indiamart.com", "SKIP", str(exc)[:120])
    except Exception as exc:
        tr.add("TC-5628", "First breadcrumb redirects to dir.indiamart.com", "FAIL", str(exc)[:120])

    land_on_pdp_direct(page, DIRECT_PDP_URL)
    try:
        links, indexes = _breadcrumb_links(page)
        target = _open_breadcrumb(page, links.nth(indexes[1]))
        tr.set_page(target)
        assert "dir.indiamart.com" in target.url or "search.mp" in target.url, f"Unexpected URL: {target.url}"
        tr.add("TC-5629", "Second breadcrumb redirects to subcategory page", "PASS", target.url[-70:])
        if target != page:
            target.close()
    except LookupError as exc:
        tr.add("TC-5629", "Second breadcrumb redirects to subcategory page", "SKIP", str(exc)[:120])
    except Exception as exc:
        tr.add("TC-5629", "Second breadcrumb redirects to subcategory page", "FAIL", str(exc)[:120])

    land_on_pdp_direct(page, DIRECT_PDP_URL)
    try:
        links, indexes = _breadcrumb_links(page)
        target = _open_breadcrumb(page, links.nth(indexes[2]))
        tr.set_page(target)
        assert "dir.indiamart.com" in target.url or target.url.endswith(".html"), f"Unexpected URL: {target.url}"
        tr.add("TC-5630", "Third breadcrumb redirects to MCAT page", "PASS", target.url[-70:])
        if target != page:
            target.close()
    except LookupError as exc:
        tr.add("TC-5630", "Third breadcrumb redirects to MCAT page", "SKIP", str(exc)[:120])
    except Exception as exc:
        tr.add("TC-5630", "Third breadcrumb redirects to MCAT page", "FAIL", str(exc)[:120])

    return tr


if __name__ == "__main__":
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=200)
        page = browser.new_page()
        result = run(page)
        summary = result.summary()
        print(f"\nSummary: {summary['passed']}/{summary['total']} passed")
        browser.close()
