"""A tiny evaluation harness.

Run a suite of cases against an N-ATLaS backend, measure pass rate and latency,
and print a report. Use it to prove your integration works, to compare a fine-tune
against base N-ATLaS, or to catch regressions in CI.

Suite = JSON list of cases. Each case:
  {"name": "...", "kind": "chat", "input": "...",
   "contains": ["..."], "any_of": ["..."], "equals": "..."}
  {"name": "...", "kind": "extract", "input": "...",
   "schema": {...}, "expect": {"field": value}}
"""
import json
import time
from typing import Any, Dict, List

from .extract import extract
from .types import Message


def _check_text(got: str, case: Dict[str, Any]):
    low = got.lower()
    if "equals" in case and got.strip() != case["equals"].strip():
        return False, f"expected == {case['equals']!r}"
    if "contains" in case:
        missing = [s for s in case["contains"] if s.lower() not in low]
        if missing:
            return False, f"missing {missing}"
    if "any_of" in case and not any(s.lower() in low for s in case["any_of"]):
        return False, f"none of {case['any_of']} present"
    return True, "ok"


def run_case(client, case: Dict[str, Any]) -> Dict[str, Any]:
    kind = case.get("kind", "chat")
    t0 = time.time()
    try:
        if kind == "extract":
            got = extract(client, case["input"], case["schema"])
            ok, reason = True, "ok"
            for k, v in case.get("expect", {}).items():
                if str(got.get(k)).strip().lower() != str(v).strip().lower():
                    ok, reason = False, f"field '{k}': got {got.get(k)!r}, want {v!r}"
                    break
            got_repr = json.dumps(got, ensure_ascii=False)
        else:
            msgs = case["input"]
            msgs = [Message("user", msgs)] if isinstance(msgs, str) else \
                   [Message(m["role"], m["content"]) for m in msgs]
            got_repr = client.chat(msgs).text
            ok, reason = _check_text(got_repr, case)
    except Exception as e:
        return {"name": case.get("name", "?"), "passed": False,
                "reason": f"error: {e}", "got": "", "latency_ms": (time.time() - t0) * 1000}
    return {"name": case.get("name", "?"), "passed": ok, "reason": reason,
            "got": got_repr[:300], "latency_ms": (time.time() - t0) * 1000}


def run_suite(client, cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    results = [run_case(client, c) for c in cases]
    passed = sum(1 for r in results if r["passed"])
    lat = [r["latency_ms"] for r in results if r["latency_ms"]]
    return {
        "total": len(results),
        "passed": passed,
        "pass_rate": round(passed / len(results), 3) if results else 0.0,
        "avg_latency_ms": round(sum(lat) / len(lat), 1) if lat else 0.0,
        "cases": results,
    }


def to_markdown(report: Dict[str, Any]) -> str:
    lines = [
        f"# N-ATLaS eval report",
        f"- Pass rate: **{report['passed']}/{report['total']}** "
        f"({report['pass_rate'] * 100:.0f}%)",
        f"- Avg latency: {report['avg_latency_ms']} ms",
        "",
        "| Case | Result | Latency | Detail |",
        "| --- | --- | --- | --- |",
    ]
    for c in report["cases"]:
        mark = "PASS" if c["passed"] else "FAIL"
        lines.append(f"| {c['name']} | {mark} | {c['latency_ms']:.0f} ms | {c['reason']} |")
    return "\n".join(lines)


def load_suite(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
