"""Run one question three ways and save the traces for the README.

    uv run compare.py "Median ML engineer offer at Google in NYC, FY2025?" \
        --gold "SELECT median(wage_annual_from) FROM lca WHERE employer='Google' AND role_family='Machine Learning Engineer' AND area_code='35620' AND fiscal_year=2025 AND case_status='CERTIFIED' AND wage_flag='ok'"
    uv run compare.py --check top-nyc-mle --runs 3      # a question from evals/checks.jsonl, 3 runs each

1. no tools:   the same model, no tools and no system prompt (what the model "knows")
2. plain:      baseline.py, one run_sql over the raw DOL table
3. agent:      app.py, the H-1B Analyst

Writes traces/<slug>.json (every tool call and answer) and prints a Markdown block to paste into
the README. With --runs N it reports how often each agent was right, so you only claim a failure
that repeats (rule of thumb: plain wrong >= 2/3 runs, agent right 3/3).
"""

import argparse
import asyncio
import json
import re
import sys
from pathlib import Path

import litellm

import app
import baseline

sys.path.insert(0, str(Path(__file__).parent / "evals"))
import check  # noqa: E402

TRACES = Path(__file__).parent / "traces"


async def no_tools(question: str) -> str:
    r = await litellm.acompletion(model=app.MODEL, vertex_location=app.VERTEX_LOCATION,
                                  messages=[{"role": "user", "content": question}], temperature=0.1)
    return r.choices[0].message.content


def details(title: str, out: dict) -> str:
    calls = "\n\n".join(f"**{c['name']}** `{json.dumps(c['args'])[:600]}`\n```\n{c['result'][:900]}\n```" for c in out["tool_calls"])
    return f"<details><summary>{title}: {len(out['tool_calls'])} tool calls</summary>\n\n{calls or '(none)'}\n\n**Answer:** {out['response']}\n\n</details>"


async def main():
    p = argparse.ArgumentParser()
    p.add_argument("question", nargs="?")
    p.add_argument("--gold", help="gold SQL, run on the agent's database")
    p.add_argument("--check", help="use a question + gold from evals/checks.jsonl")
    p.add_argument("--runs", type=int, default=1)
    args = p.parse_args()

    app.load_store()
    spec = {"compare": "scalar"}
    if args.check:
        spec = next(json.loads(line) for line in (Path("evals/checks.jsonl")).read_text().splitlines()
                    if line.strip() and json.loads(line)["id"] == args.check)
        question = spec["question"]
    else:
        question = args.question
        if args.gold:
            spec["gold_sql"] = args.gold
    gold = check.gold_value(spec) if "gold_sql" in spec else None

    nt = await no_tools(question)
    runs = []
    for _ in range(args.runs):
        plain = await baseline.ask_plain(question)
        agent = await app.ask(question)
        verdict = {}
        if gold is not None:
            verdict = {"plain_ok": check.score(spec, plain, gold)[0], "agent_ok": check.score(spec, agent, gold)[0]}
        runs.append({"plain": plain, "agent": agent, **verdict})
        print(f"run {len(runs)}: {verdict or 'no gold'}", flush=True)

    TRACES.mkdir(exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", question.lower()).strip("-")[:60]
    (TRACES / f"{slug}.json").write_text(json.dumps(
        {"question": question, "gold": gold, "gold_sql": spec.get("gold_sql"), "no_tools": nt, "runs": runs},
        indent=1, default=str))

    last = runs[-1]
    tally = ""
    if gold is not None:
        tally = (f"\n\nPlain agent right in {sum(r['plain_ok'] for r in runs)}/{len(runs)} runs; "
                 f"H-1B Analyst right in {sum(r['agent_ok'] for r in runs)}/{len(runs)} runs.")
    print(f"""
### {question}

**Expected:** {gold} (gold SQL on `lca`).{tally}

**No tools:** {nt[:600]}

{details("Plain run_sql agent", last["plain"])}

{details("H-1B Analyst", last["agent"])}

Saved traces/{slug}.json
""")


if __name__ == "__main__":
    asyncio.run(main())
