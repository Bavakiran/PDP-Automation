"""
IndiaMart PDP Daily Smoke Test Runner.
"""
import argparse
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

from config import VIEWPORT, USER_AGENT
from utils.helpers import generate_html_report

SUITES = {
    "landings": "test_01_pdp_landings",
    "first_fold": "test_02_pdp_first_fold",
    "breadcrumbs": "test_03_pdp_breadcrumbs",
    "similar": "test_04_find_similar_products",
    "categories": "test_05_find_related_categories",
    "company": "test_06_company_details",
    "chatBL": "test_07_chat_bl_form",
    "more_products": "test_08_more_products",
    "about": "test_09_about_the_company",
    "get_quotes": "test_10_inline_BL",
    "header_footer": "test_11_header_footer",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", choices=list(SUITES.keys()), help="Run a single suite")
    parser.add_argument("--headless", action="store_true", help="Run Chromium in headless mode")
    args = parser.parse_args()

    headless = args.headless
    suites_to_run = [SUITES[args.suite]] if args.suite else list(SUITES.values())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.environ["PDP_SCREENSHOT_RUN_ID"] = timestamp

    print(f"\n{'=' * 60}")
    print("  IndiaMart PDP Daily Smoke Test")
    print(f"  Suites: {len(suites_to_run)} | Headless: {headless}")
    print(f"{'=' * 60}")

    all_results = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless, slow_mo=200)
        ctx = browser.new_context(viewport=VIEWPORT, user_agent=USER_AGENT)

        for module_name in suites_to_run:
            page = ctx.new_page()
            try:
                mod = __import__(f"tests.{module_name}", fromlist=["run"])
                tr = mod.run(page)
                summary = tr.summary()
                all_results.append({**summary, "results": tr.results, "suite": module_name})
                print(f"  -> {summary['passed']}/{summary['total']} passed")
            except Exception as exc:
                print(f"  Suite {module_name} crashed: {exc}")
                all_results.append({
                    "total": 1,
                    "passed": 0,
                    "failed": 1,
                    "skipped": 0,
                    "results": [{
                        "tc_id": "?",
                        "name": module_name,
                        "status": "FAIL",
                        "detail": str(exc),
                        "timestamp": "",
                    }],
                    "suite": module_name,
                })
            finally:
                for open_page in list(ctx.pages):
                    try:
                        open_page.close()
                    except Exception:
                        pass

        browser.close()

    total = sum(r["total"] for r in all_results)
    passed = sum(r["passed"] for r in all_results)
    failed = sum(r["failed"] for r in all_results)
    skipped = sum(r["skipped"] for r in all_results)
    pct = round(passed / total * 100, 1) if total else 0

    print(f"\n{'=' * 60}")
    print(f"  FINAL: {passed}/{total} passed ({pct}%) | {failed} failed | {skipped} skipped")
    print(f"{'=' * 60}")

    reports_dir = Path(__file__).resolve().parent / "reports"
    timestamped_report = reports_dir / f"pdp_smoke_{timestamp}.html"
    latest_report = reports_dir / "pdp_smoke_report.html"

    report = Path(generate_html_report(all_results, str(timestamped_report))).resolve()
    shutil.copyfile(report, latest_report)

    print(f"  Report: {report}")
    print(f"  Latest: {latest_report.resolve()}")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
