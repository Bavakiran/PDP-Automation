"""
Capture a screenshot of the "Find Similar Products" section on a PDP.

Usage:
    python capture_similar_products_screenshot.py
    python capture_similar_products_screenshot.py --url "https://www.indiamart.com/proddetail/warehouse-storage-rack-2854599577433.html"
    python capture_similar_products_screenshot.py --output "reports/my_similar_section.png"
"""
import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright

from config import USER_AGENT, VIEWPORT

DEFAULT_PDP_URL = "https://www.indiamart.com/proddetail/warehouse-storage-rack-2854599577433.html"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "reports" / "find_similar_products_section.png"


def capture(url: str, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={**VIEWPORT, "height": 1600}, user_agent=USER_AGENT)
        page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(3000)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.5)")
        page.wait_for_timeout(2000)

        target = None
        for selector in [
            "section:has-text('Pallet Racks')",
            "section:has-text('Heavy Duty Racks')",
            "div:has-text('Pallet Racks')",
            "div:has-text('Heavy Duty Racks')",
            "section:has-text('Find Similar')",
            "div:has-text('Find Similar')",
        ]:
            locator = page.locator(selector).first
            try:
                if locator.count() > 0 and locator.is_visible(timeout=500):
                    target = locator
                    break
            except Exception:
                pass

        if target is not None:
            target.scroll_into_view_if_needed(timeout=5_000)
            page.wait_for_timeout(1000)
            target.screenshot(path=str(output_path))
        else:
            page.screenshot(path=str(output_path), full_page=True)

        browser.close()

    return output_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=DEFAULT_PDP_URL, help="PDP URL to capture")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output image path")
    args = parser.parse_args()

    saved_to = capture(args.url, Path(args.output).resolve())
    print(f"Screenshot saved: {saved_to}")


if __name__ == "__main__":
    main()
