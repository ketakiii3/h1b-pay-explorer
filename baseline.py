"""The plain run_sql agent, for the README comparison only. Not part of the deployed app.

Same model as app.py, but the nyc-311-agent shape: one run_sql tool over the H-1B rows exactly as
DOL ships them (data/baseline.duckdb, built by build.py), a one-line prompt, no offline context,
no lookup tools, no guardrails.

    uv run baseline.py "Median ML engineer offer at Google in NYC in FY2025?"
"""

import asyncio
import json
import sys
from pathlib import Path

import duckdb
from agents import Agent, ModelSettings, RunHooks, Runner, function_tool, set_tracing_disabled
from agents.extensions.models.litellm_model import LitellmModel

import app  # same model settings

set_tracing_disabled(True)
DB = Path(__file__).parent / "data" / "baseline.duckdb"
MAX_ROWS = 100
db = duckdb.connect(str(DB), read_only=True) if DB.exists() else None


@function_tool
def run_sql(query: str) -> str:
    """Run a SQL query against the database and return the results.

    Args:
        query: A DuckDB SQL query.
    """
    with db.cursor() as cursor:
        try:
            cursor.execute(query)
            rows = cursor.fetchmany(MAX_ROWS + 1)
        except duckdb.Error as e:
            return json.dumps({"error": str(e)})
        columns = [c[0] for c in cursor.description or []]
    return json.dumps({"columns": columns, "rows": rows[:MAX_ROWS], "truncated": len(rows) > MAX_ROWS}, default=str)


plain_agent = Agent(
    name="Plain SQL Agent",
    instructions="You answer questions about H-1B Labor Condition Application data. The data is in the `lca` table.",
    model=LitellmModel(model=app.MODEL, api_key="unused"),
    model_settings=ModelSettings(extra_args={"vertex_location": app.VERTEX_LOCATION, "timeout": 90, "num_retries": 2}),
    tools=[run_sql],
)


async def ask_plain(question: str) -> dict:
    if db is None:
        raise SystemExit("No data/baseline.duckdb. Run `uv run build.py` first.")
    hooks = app.RecordToolCalls()
    try:
        result = await Runner.run(plain_agent, question, hooks=hooks, max_turns=15)
        response = result.final_output
    except Exception as e:  # noqa: BLE001
        response = f"FAILED: {type(e).__name__}: {str(e)[:200]}"
    return {"response": response, "tool_calls": hooks.tool_calls}


if __name__ == "__main__":
    out = asyncio.run(ask_plain(" ".join(sys.argv[1:]) or input("QUESTION: ")))
    for c in out["tool_calls"]:
        print(f"TOOL {c['name']}({json.dumps(c['args'])}) -> {c['result'][:300]}\n")
    print("ANSWER:", out["response"])
