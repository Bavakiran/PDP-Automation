# IndiaMart PDP – Daily Execution Smoke Test Suite

Automated Playwright (Python) test suite mapped **1-to-1** against the
TestLink suite **"PDP daily Execution smoke testcases"** (ID: 370946).

---

## 📁 Project Structure

```
indiamart_pdp_smoke/
├── config.py                              ← URLs, timeouts, browser settings
├── main.py                                ← Runner entry-point
├── generate_sample_report.py             ← Preview report without network
├── utils/
│   └── helpers.py                        ← Shared helpers + HTML report engine
├── tests/
│   ├── test_01_pdp_landings.py           ← Suite: PDP Landings         (5 TCs)
│   ├── test_02_pdp_first_fold.py         ← Suite: PDP First Fold      (12 TCs)
│   ├── test_03_pdp_breadcrumbs.py        ← Suite: PDP Breadcrumbs      (3 TCs)
│   ├── test_04_find_similar_products.py  ← Suite: Find Similar Prods   (4 TCs)
│   ├── test_05_find_related_categories.py← Suite: Find Related Cats    (3 TCs)
│   ├── test_06_company_details.py        ← Suite: Company Details       (2 TCs)
│   ├── test_07_enquiry_form.py           ← Suite: Enquiry Form          (2 TCs)
│   ├── test_08_more_products.py          ← Suite: More Products         (2 TCs)
│   ├── test_09_about_the_company.py      ← Suite: About the Company     (2 TCs)
│   ├── test_10_get_quotes.py             ← Suite: Get Quotes            (2 TCs)
│   └── test_11_header_footer.py          ← Suite: Header / Footer       (2 TCs)
└── reports/
    └── pdp_smoke_<timestamp>.html        ← Auto-generated HTML report
```

---

## ⚙️ Setup

### Prerequisites
- Python 3.9+
- pip

### Install

```bash
pip install playwright
playwright install chromium
```

---

## ▶️ Running Tests

```bash
# Run all 39 test cases (all 11 suites)
python main.py

# Run a specific suite only
python main.py --suite landings
python main.py --suite firstfold
python main.py --suite breadcrumbs
python main.py --suite similar
python main.py --suite categories
python main.py --suite company
python main.py --suite enquiry
python main.py --suite moreproducts
python main.py --suite aboutcompany
python main.py --suite getquotes
python main.py --suite headerfooter

# Run with visible browser (useful for debugging)
python main.py --headed

# Combine: single suite with visible browser
python main.py --suite firstfold --headed

# Preview the HTML report without live network
python generate_sample_report.py
```

A timestamped HTML report is saved automatically to `reports/pdp_smoke_<YYYYMMDD_HHMMSS>.html`.

---

## 🗺️ TestLink → Automation Mapping

| TestLink Suite | File | TCs |
|---|---|---|
| PDP Landings (370947) | test_01_pdp_landings.py | 5543, 5546, 5547, 5905, 5989 |
| PDP First Fold (371125) | test_02_pdp_first_fold.py | 5548–5554, 5906, 5907, 5939–5941 |
| PDP Breadcrumbs (381112) | test_03_pdp_breadcrumbs.py | 5628, 5629, 5630 |
| Find Similar Products (458441) | test_04_find_similar_products.py | 5942–5945 |
| Find Related Categories (458442) | test_05_find_related_categories.py | 5946–5948 |
| Company Details (458443) | test_06_company_details.py | 5949, 5950 |
| Enquiry Form (458444) | test_07_enquiry_form.py | 5951, 5952 |
| More Products (458445) | test_08_more_products.py | 5953, 5954 |
| About the Company (458446) | test_09_about_the_company.py | 5955, 5956 |
| Get Quotes (458447) | test_10_get_quotes.py | 5957, 5958 |
| Header/Footer (458448) | test_11_header_footer.py | 5959, 5960 |

**Total: 39 automated test cases**

---

## 📊 HTML Report

The report groups results by TestLink sub-suite and shows:
- TC ID (matches TestLink external ID)
- Full test case name (matches TestLink TC name exactly)
- PASS / FAIL / SKIP status with colour coding
- Failure detail message
- Execution duration per TC
- Pass rate % summary card

---

## 🔧 Configuration (`config.py`)

| Setting | Default | Description |
|---|---|---|
| `SEARCH_KEYWORD` | `"tmt bar"` | Product used for most landing flows |
| `BREADCRUMB_PDP_URL` | Tata Tiscon TMT URL | Fixed PDP for breadcrumb tests |
| `GOOGLE_PDP_URL` | Papad Machine URL | Fixed PDP for TC-5905 |
| `HEADLESS` | `True` | Set `False` to see browser |
| `NAV_TIMEOUT` | `60000` ms | Page navigation timeout |
| `TIMEOUT` | `20000` ms | Element wait timeout |

---

## 📝 Notes

- **TC-5939 / TC-5940** (Brochure PDF / Video icon): These are optional elements
  not present on every PDP. The tests raise a descriptive `AssertionError` if
  the element is absent so they show as `FAIL` — change to `skip()` if you
  want them non-blocking on PDPs without those elements.
- **TC-5906** (Call Now → receive call): Physical call delivery cannot be
  automated; the test verifies the CTA is clickable and triggers the correct
  modal/tel: link.
- All tests re-use the `land_on_pdp_via_search()` helper so the full
  landing flow is exercised as part of every suite.
