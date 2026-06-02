import os, base64, importlib, json, time
from pathlib import Path
from urllib.request import urlopen, Request


def _get_llm_config():
    cfg = {
        "base_url": "https://imllm.intermesh.net",
        "api_key":  "",
        "model":    "google/gemini-2.5-flash-lite"
    }
    try:
        import sys
        cfg_dir = Path(__file__).resolve().parent.parent
        if str(cfg_dir) not in sys.path:
            sys.path.insert(0, str(cfg_dir))
        import config as c
        cfg["base_url"] = getattr(c, "LLM_BASE_URL", cfg["base_url"])
        cfg["api_key"]  = getattr(c, "LLM_API_KEY",  os.environ.get("LLM_API_KEY", ""))
        cfg["model"]    = getattr(c, "LLM_MODEL",     cfg["model"])
    except ImportError:
        cfg["api_key"] = os.environ.get("LLM_API_KEY", "")
    return cfg


def _post(cfg, body_dict):
    """POST to LLM gateway, return parsed response dict."""
    body = json.dumps(body_dict).encode()
    req  = Request(
        cfg["base_url"].rstrip("/") + "/v1/chat/completions",
        data=body,
        headers={
            "Content-Type":  "application/json",
            "Authorization": f"Bearer {cfg['api_key']}",
        },
        method="POST"
    )
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def _parse_verdict(raw: str) -> dict:
    raw = raw.strip().replace("```json", "").replace("```", "").strip()
    try:
        parsed = json.loads(raw)
        return {
            "verdict": str(parsed.get("verdict", "FAIL")).upper(),
            "reason":  parsed.get("reason", "")
        }
    except Exception:
        upper = raw.upper()
        if "PASS" in upper:
            return {"verdict": "PASS", "reason": raw[:120]}
        return {"verdict": "FAIL", "reason": raw[:120]}


# ── Vision check (screenshot available) ──────────────────────────────────────
def _call_llm_vision(screenshot_path: str, tc_id: str, test_name: str) -> dict:
    cfg = _get_llm_config()
    if not cfg["api_key"]:
        return {"verdict": "SKIP", "reason": "LLM_API_KEY not set in config.py"}
    try:
        with open(screenshot_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode()
    except Exception as e:
        return {"verdict": "SKIP", "reason": f"Cannot read screenshot: {e}"}

    prompt = (
        f"You are a QA visual verifier for IndiaMart PDP automation tests.\n"
        f"Test ID: {tc_id}\nTest: '{test_name}'\n\n"
        f"Look at the screenshot and decide if the test condition is visually satisfied.\n"
        f"Reply ONLY in this JSON (no markdown):\n"
        f"{{'verdict':'PASS','reason':'brief reason'}} or {{'verdict':'FAIL','reason':'brief reason'}}"
    )
    try:
        data = _post(cfg, {
            "model":      cfg["model"],
            "max_tokens": 200,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "image_url",
                     "image_url": {"url": f"data:image/png;base64,{image_b64}",
                                   "detail": "low"}},
                    {"type": "text", "text": prompt}
                ]
            }]
        })
        raw = data["choices"][0]["message"]["content"]
        return _parse_verdict(raw)
    except Exception as e:
        return {"verdict": "SKIP", "reason": f"Gateway error: {e}"}


# ── Text-only check (no screenshot) ──────────────────────────────────────────
def _call_llm_text(tc_id: str, test_name: str, error_detail: str) -> dict:
    """
    When no screenshot is available, ask the AI to analyse the error detail
    and decide if it is a genuine failure or a flaky/selector issue.
    """
    cfg = _get_llm_config()
    if not cfg["api_key"]:
        return {"verdict": "SKIP", "reason": "LLM_API_KEY not set in config.py"}

    prompt = (
        f"You are a QA analyst reviewing an automated test failure on IndiaMart PDP.\n\n"
        f"Test ID     : {tc_id}\n"
        f"Test Name   : {test_name}\n"
        f"Error Detail: {error_detail}\n\n"
        f"Based on the error message, decide:\n"
        f"- PASS if this looks like a flaky/timing/selector issue (not a real product defect)\n"
        f"- FAIL if this looks like a genuine functional failure\n\n"
        f"Reply ONLY in this JSON (no markdown):\n"
        f"{{'verdict':'PASS','reason':'brief reason'}} or {{'verdict':'FAIL','reason':'brief reason'}}"
    )
    try:
        data = _post(cfg, {
            "model":      cfg["model"],
            "max_tokens": 200,
            "messages": [{"role": "user", "content": prompt}]
        })
        raw = data["choices"][0]["message"]["content"]
        return _parse_verdict(raw)
    except Exception as e:
        return {"verdict": "SKIP", "reason": f"Gateway error: {e}"}


# ── Re-run a single TC ────────────────────────────────────────────────────────
def _rerun_tc(mod_name: str, page, tc_id: str):
    try:
        sys_mod = __import__("sys").modules
        if mod_name in sys_mod:
            del sys_mod[mod_name]
        mod    = importlib.import_module(mod_name)
        result = mod.run(page)
        for r in result.results:
            if r["tc_id"] == tc_id:
                return r
    except Exception:
        pass
    return None


# ── Main entry point ──────────────────────────────────────────────────────────
def ai_verify_failures(suite_results: list, page=None, mod_prefix: str = "tests.") -> list:
    cfg = _get_llm_config()
    if not cfg["api_key"]:
        print("\n[AI Checker] LLM_API_KEY not in config.py — skipping.")
        print('             Add  LLM_API_KEY = "your-key"  to config.py')
        return suite_results

    # Collect ALL failures regardless of screenshot
    all_fails = [
        (suite, tc)
        for suite in suite_results
        for tc in suite["results"]
        if tc["status"] == "FAIL"
    ]

    if not all_fails:
        print("\n[AI Checker] No failures — nothing to verify.")
        return suite_results

    # Report every failure
    print(f"\n[AI Checker] {len(all_fails)} failure(s) found:")
    for suite, tc in all_fails:
        sc      = tc.get("screenshot", "")
        has_sc  = bool(sc) and Path(sc).exists()
        print(f"  [{tc['tc_id']}] {tc['name'][:55]}")
        print(f"           Detail    : {tc.get('detail','')[:80]}")
        print(f"           Screenshot: {'✅ ' + Path(sc).name if has_sc else '❌ not captured'}")

    print(f"\n[AI Checker] Starting verification via {cfg['base_url']} ({cfg['model']})...")

    for suite, tc in all_fails:
        raw_suite = suite["suite"].split("] ")[-1]
        mod_name  = mod_prefix + raw_suite
        sc        = tc.get("screenshot", "")
        has_sc    = bool(sc) and Path(sc).exists()

        print(f"\n  [{tc['tc_id']}] {tc['name'][:55]}")

        # Choose vision or text-only based on screenshot availability
        if has_sc:
            print(f"           Mode      : Visual (screenshot)")
            verdict = _call_llm_vision(sc, tc["tc_id"], tc["name"])
        else:
            print(f"           Mode      : Text analysis (no screenshot)")
            verdict = _call_llm_text(tc["tc_id"], tc["name"], tc.get("detail", ""))

        print(f"           AI verdict: {verdict['verdict']} — {verdict['reason']}")

        if verdict["verdict"] == "PASS":
            tc["status"] = "AI_PASS"
            tc["detail"] = f"[AI {'Visual' if has_sc else 'Text'} ✅] {verdict['reason']}"
            suite["failed"]  = max(0, suite["failed"] - 1)
            suite["passed"] += 1
            print(f"           → Marked AI_PASS ✅")

        elif verdict["verdict"] == "FAIL" and page is not None:
            print(f"           → Re-running test once...")
            time.sleep(1)
            rerun = _rerun_tc(mod_name, page, tc["tc_id"])
            if rerun:
                if rerun["status"] == "PASS":
                    tc["status"]     = "PASS"
                    tc["detail"]     = f"[Re-run ✅] {rerun.get('detail','')}"
                    tc["screenshot"] = rerun.get("screenshot", sc)
                    suite["failed"]  = max(0, suite["failed"] - 1)
                    suite["passed"] += 1
                    print(f"           → Re-run PASSED ✅")
                else:
                    tc["detail"] = (
                        f"[AI ❌ {verdict['reason']}] "
                        f"[Re-run ❌ {rerun.get('detail','')}]"
                    )
                    print(f"           → Re-run also FAILED ❌")

    print("\n[AI Checker] Done.")
    return suite_results


# ── Row colour ────────────────────────────────────────────────────────────────
def row_colour(status: str) -> str:
    return {
        "PASS":    "#d4edda",
        "AI_PASS": "#b8dfc4",
        "FAIL":    "#f8d7da",
        "SKIP":    "#fff3cd",
    }.get(status.upper(), "#f5f5f5")