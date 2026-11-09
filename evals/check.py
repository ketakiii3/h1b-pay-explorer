"""Self-check: run every question in evals/checks.jsonl through the agent and score it against gold SQL.

    uv run python evals/check.py                       # in-process, local database
    uv run python evals/check.py --url https://...run.app   # against the deployed app
    uv run python evals/check.py --only top-nyc-mle   # one check

Scoring:
    scalar      the gold number appears (within 2%, or +-1 for small numbers) in the agent's last SQL
                result or in its answer text ("$152k" counts as 152,000)
    topk        at least 60% of the gold top-k names appear in the agent's last SQL result or answer
    tool_value  the agent called the named tool and its result field equals the gold value
    refusal     the agent ran no SQL (it should say what the data can't answer)

Gold values come from running gold_sql on the same database the agent uses, so the set works on the
full data and the sample alike. Results go to evals/results/<timestamp>.json and evals/history.csv.
"""

import argparse
import asyncio
import csv
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import app  # noqa: E402

HERE = Path(__file__).parent


def numbers_in(text: str) -> list[float]:
    out = []
    for m in re.finditer(r"\$?(\d[\d,]*(?:\.\d+)?)\s*([kKmM])?\b", text or ""):
        v = float(m.group(1).replace(",", ""))
        v *= {"k": 1e3, "m": 1e6}.get((m.group(2) or "").lower(), 1)
        out.append(v)
    return out


def close(a: float, b: float) -> bool:
    return abs(a - b) <= 1 if abs(b) < 100 else abs(a - b) / abs(b) <= 0.02


def last_sql_result(tool_calls) -> dict | None:
    for c in reversed(tool_calls):
        if c["name"] == "run_sql":
            try:
                r = json.loads(c["result"])
                if "rows" in r:
                    return r
            except json.JSONDecodeError:
                pass
    return None


def score(check: dict, out: dict, gold) -> tuple[bool, str]:
    calls = out["tool_calls"]
    kind = check["compare"]
    if kind == "refusal":
        n = sum(c["name"] == "run_sql" for c in calls)
        return n == 0, f"{n} run_sql calls"
    if gold is None:
        return False, "gold query returned nothing on this database"
    if kind == "tool_value":
        for c in calls:
            if c["name"] == check["tool"]:
                try:
                    got = json.loads(c["result"]).get(check["field"])
                except json.JSONDecodeError:
                    continue
                return got == gold, f"got {got}, gold {gold}"
        return False, f"never called {check['tool']}"
    res = last_sql_result(calls)
    haystack = json.dumps(res["rows"], default=str) if res else ""
    if kind == "scalar":
        found = numbers_in(haystack) + numbers_in(out["response"])
        ok = any(close(v, float(gold)) for v in found)
        return ok, f"gold {gold}"
    if kind == "topk":
        text = (haystack + " " + out["response"]).lower()
        hits = [g for g in gold if str(g).lower() in text]
        return len(hits) >= 0.6 * len(gold), f"{len(hits)}/{len(gold)} of {gold}"
    return False, f"unknown compare {kind}"


def gold_value(check: dict):
    if "gold_sql" not in check:
        return None
    rows = app.store.q(check["gold_sql"])
    if check["compare"] == "topk":
        return [r[0] for r in rows] or None
    return rows[0][0] if rows and rows[0][0] is not None else None


async def run_remote(url: str, question: str) -> dict:
    import httpx

    async with httpx.AsyncClient(timeout=300) as client:
        r = await client.post(url.rstrip("/") + "/chat", json={"message": question})
        r.raise_for_status()
        return r.json()


async def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", help="score the deployed app instead of the local agent")
    p.add_argument("--only", help="comma-separated check ids")
    p.add_argument("--label", default="", help="note for evals/history.csv, e.g. 'added find_location'")
    args = p.parse_args()

    app.load_store()
    checks = [json.loads(line) for line in (HERE / "checks.jsonl").read_text().splitlines() if line.strip()]
    if args.only:
        checks = [c for c in checks if c["id"] in args.only.split(",")]

    results, passed = [], 0
    for c in checks:
        gold = gold_value(c)
        t = time.time()
        try:
            out = await (run_remote(args.url, c["question"]) if args.url else app.ask(c["question"]))
        except Exception as e:  # noqa: BLE001
            out = {"response": f"ERROR {e}", "tool_calls": []}
        secs = time.time() - t
        ok, why = score(c, out, gold)
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  {c['id']:<26} {secs:5.1f}s  {len(out['tool_calls']):2d} calls  {why}", flush=True)
        results.append({"id": c["id"], "ok": ok, "why": why, "seconds": round(secs, 1), "gold": gold,
                         "response": out["response"], "tool_calls": out["tool_calls"]})

    n = len(checks)
    secs = sorted(r["seconds"] for r in results)
    p50 = secs[len(secs) // 2] if secs else 0
    print(f"\nScore {passed}/{n} = {passed / max(n, 1):.0%}   (±{1 / max(n, 1) ** 0.5:.0%} margin)   p50 {p50}s")
    stamp = time.strftime("%Y%m%d-%H%M%S")
    (HERE / "results").mkdir(exist_ok=True)
    (HERE / "results" / f"{stamp}.json").write_text(json.dumps(results, indent=1, default=str))
    new = not (HERE / "history.csv").exists()
    with (HERE / "history.csv").open("a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["timestamp", "target", "database", "passed", "total", "p50_seconds", "label"])
        w.writerow([stamp, args.url or "local", app.store.source, passed, n, p50, args.label])


if __name__ == "__main__":
    asyncio.run(main())
