"""H-1B Pay Explorer: a Text2SQL agent over every H-1B Labor Condition Application, FY2024 - FY2026 Q3.

build.py does the hard data work offline (wages annualized, employers resolved, roles classified,
worksites mapped to wage areas, wage levels computed). This file serves the agent that queries it.
"""

import json
import os
import re
import threading
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path

import duckdb
import uvicorn
from agents import (
    Agent,
    ModelSettings,
    RunContextWrapper,
    RunHooks,
    Runner,
    SQLiteSession,
    ToolGuardrailFunctionOutput,
    function_tool,
    set_tracing_disabled,
    tool_input_guardrail,
)
from agents.extensions.models.litellm_model import LitellmModel
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from rapidfuzz import fuzz, process

import h1b_common as hc

# Traces upload to OpenAI by default, which needs an OpenAI key. We're on Gemini.
set_tracing_disabled(True)

ROOT = Path(__file__).parent
DATA = ROOT / "data"
MODEL = os.environ.get("MODEL", "vertex_ai/gemini-3.5-flash")
VERTEX_LOCATION = os.environ.get("VERTEX_LOCATION", "global")
GCS_BUCKET = os.environ.get("GCS_BUCKET")  # set on Cloud Run: the full database lives in GCS
GCS_OBJECT = os.environ.get("GCS_OBJECT", "v1/h1b.duckdb")
ON_CLOUD_RUN = "K_SERVICE" in os.environ
SESSIONS_DB = "/tmp/conversations.db" if ON_CLOUD_RUN else str(ROOT / "conversations.db")
MAX_ROWS = 200
SQL_TIMEOUT_S = 20
AGENT_NAME = "H-1B Analyst"

MAPPINGS = json.loads((DATA / "mappings.json").read_text())


# --- The Database ---


class Store:
    """The read-only database plus the small lookup lists the matching tools search in memory."""

    db: duckdb.DuckDBPyConnection | None = None
    source = ""
    employers: list[dict] = []
    alias_choices: dict[str, int] = {}
    places: list[dict] = []
    place_choices: dict[str, int] = {}
    family_socs: dict[str, list] = {}
    title_choices: dict[str, str] = {}

    def q(self, sql: str, params: list | None = None) -> list[tuple]:
        with self.db.cursor() as cur:
            return cur.execute(sql, params or []).fetchall()


store = Store()


def locate_database() -> Path:
    """Full database: local data/h1b.duckdb, else downloaded from GCS. Fallback: the committed sample."""
    if (DATA / "h1b.duckdb").exists():
        return DATA / "h1b.duckdb"
    if GCS_BUCKET:
        from google.cloud import storage

        dest = Path("/tmp/h1b.duckdb")
        if not dest.exists():
            t = time.time()
            storage.Client().bucket(GCS_BUCKET).blob(GCS_OBJECT).download_to_filename(dest)
            print(f"downloaded gs://{GCS_BUCKET}/{GCS_OBJECT} in {time.time() - t:.1f}s", flush=True)
        return dest
    return DATA / "h1b_sample.duckdb"


def load_store():
    if store.db is not None:
        return
    path = locate_database()
    # The security boundary is the connection: read-only, no file or network access, and the
    # agent can't SET its way out of either.
    store.db = duckdb.connect(str(path), read_only=True,
                              config={"enable_external_access": False, "lock_configuration": True})
    store.source = path.name

    store.employers = [
        {"employer_id": i, "employer": n, "employer_type": t, "filings": f, "aliases": a or []}
        for i, n, t, f, a in store.q("SELECT employer_id, employer, employer_type, filings, aliases FROM employers")
    ]
    store.alias_choices = {}
    for e in store.employers:
        for name in [e["employer"], *e["aliases"]]:
            store.alias_choices.setdefault(hc.normalize_employer(name), e["employer_id"])

    store.places = [
        {"city": c, "state": s, "area_code": a, "metro_name": m, "filings": n}
        for c, s, a, m, n in store.q("""
            SELECT worksite_city, worksite_state, area_code, metro_name, count(*) AS n FROM lca
            WHERE area_code IS NOT NULL AND worksite_city IS NOT NULL GROUP BY ALL ORDER BY n DESC""")
    ]
    store.place_choices = {}
    for i, p in enumerate(store.places):
        store.place_choices.setdefault(f"{p['city']} {p['state']}".upper(), i)
        store.place_choices.setdefault(p["city"].upper(), i)

    store.family_socs = {}
    for fam, soc, title, n in store.q("""
            SELECT role_family, soc_code, any_value(soc_title), count(*) AS n FROM lca
            WHERE case_status = 'CERTIFIED' GROUP BY 1, 2 ORDER BY n DESC"""):
        store.family_socs.setdefault(fam, []).append({"soc_code": soc, "soc_title": title, "filings": n})

    store.title_choices = dict(store.q("""
        SELECT title_norm, arg_max(role_family, filings) FROM role_titles_summary
        WHERE filings >= 2 GROUP BY 1"""))
    n = store.q("SELECT count(*) FROM lca")[0][0]
    print(f"loaded {store.source}: {n:,} filings, {len(store.employers):,} employers", flush=True)


# --- Per-request state: the last SQL result feeds the chart and the table ---


@dataclass
class RequestState:
    last_result: dict | None = None
    chart: dict | None = None
    sql_calls: int = 0
    notes: list = field(default_factory=list)


# --- Lookup tools: they hide the data's traps from the SQL the model writes ---


@function_tool
def read_mappings() -> str:
    """Read the database schema: tables, columns (type, description, whether it's an enum),
    glossary, join hints, example queries and the LIMITATIONS of the data. Call this first."""
    tables = {
        name: {"description": t["description"],
               "columns": [{k: c[k] for k in ("name", "type", "description")} | ({"is_enum": True} if "enum_values" in c else {})
                           for c in t["columns"]]}
        for name, t in MAPPINGS["tables"].items()
    }
    return json.dumps({"as_of": MAPPINGS["as_of"], "tables": tables, "glossary": MAPPINGS["glossary"],
                       "join_hints": MAPPINGS["join_hints"], "limitations": MAPPINGS["limitations"],
                       "example_queries": MAPPINGS["example_queries"]})


@function_tool
def get_enum_values(column: str) -> str:
    """Exact valid values of an enum column. Match them exactly: equality is case-sensitive.

    Args:
        column: 'table.column', e.g. 'lca.case_status' or 'lca.role_family'.
    """
    table, _, col = column.partition(".") if "." in column else ("lca", "", column)
    t = MAPPINGS["tables"].get(table)
    match = next((c for c in (t or {}).get("columns", []) if c["name"] == col), None)
    if match is None:
        return json.dumps({"error": f"No column '{column}'. Call read_mappings for the columns."})
    if "enum_values" not in match:
        return json.dumps({"error": f"'{column}' is not an enum column. Use the find_* tools for employers, roles and places."})
    return json.dumps({"column": column, "enum_values": match["enum_values"]}, default=str)


def match_employers(name: str, limit: int = 5) -> list[dict]:
    alias = hc.EMPLOYER_ALIASES.get(name.strip().lower())
    query = hc.normalize_employer(alias or name)
    if not query:
        return []
    best: dict[int, float] = {}
    for alias, score, _ in process.extract(query, list(store.alias_choices), scorer=fuzz.WRatio, limit=40):
        eid = store.alias_choices[alias]
        score += 8 if alias == query else 0
        score += 4 if alias.startswith(query + " ") else 0
        best[eid] = max(best.get(eid, 0), score)
    by_id = {e["employer_id"]: e for e in store.employers}
    ranked = sorted(best.items(), key=lambda kv: (-round(kv[1]), -by_id[kv[0]]["filings"]))[:limit]
    return [{"employer_id": eid, "employer": by_id[eid]["employer"], "employer_type": by_id[eid]["employer_type"],
             "filings": by_id[eid]["filings"], "match_score": round(min(s, 100)),
             "name_variants_merged": len(by_id[eid]["aliases"]), "sample_variants": by_id[eid]["aliases"][:4]}
            for eid, s in ranked]


@function_tool
def find_employer(name: str) -> str:
    """Find an employer's employer_id. One company files under many legal names (GOOGLE LLC, Google Inc.);
    all of them share one employer_id. Always filter SQL on employer_id, never on a name.

    Args:
        name: The company as the user wrote it, e.g. 'google', 'JP Morgan', 'TCS'.
    """
    matches = match_employers(name)
    if not matches:
        return json.dumps({"error": f"No employer like '{name}'."})
    top = matches[0]
    if top["match_score"] < 70:
        return json.dumps({"error": f"No employer close to '{name}' in the data. It may not file H-1B LCAs.",
                           "closest": [m["employer"] for m in matches[:3]]})
    note = ("Confident match." if top["match_score"] >= 90 else
            "Weak match: confirm with the user or mention the alternatives.")
    return json.dumps({"matches": matches, "note": note})


def match_role(text: str) -> dict:
    family = hc.role_from_user_text(text)
    how = "rules"
    if family is None or family not in store.family_socs:
        hit = process.extractOne(hc.normalize_title(text), list(store.title_choices), scorer=fuzz.WRatio)
        if hit and hit[1] >= 80:
            family, how = store.title_choices[hit[0]], f"similar title '{hit[0]}'"
    if family is None or family not in store.family_socs:
        return {"error": f"No role family for '{text}'.", "role_families": sorted(store.family_socs)}
    socs = store.family_socs[family][:3]
    examples = [t for (t,) in store.q(
        "SELECT title_norm FROM role_titles_summary WHERE role_family = ? ORDER BY filings DESC LIMIT 6", [family])]
    return {"role_family": family, "matched_by": how, "main_soc_codes": socs, "example_titles": examples}


@function_tool
def find_role(text: str) -> str:
    """Map a role in plain words ('ML engineer', 'quant', 'data scientist') to its role_family.
    Job titles are free text; filter SQL on role_family, never on job_title.

    Args:
        text: The role as the user wrote it.
    """
    return json.dumps(match_role(text))


def match_place(text: str) -> dict:
    t = text.strip().lower().removesuffix(", usa").strip()
    target = hc.PLACE_ALIASES.get(t)
    if target:
        hits = [p for p in store.places if (p["metro_name"] or "").startswith(target)]
        if hits:
            p = hits[0]
            return {"area_code": p["area_code"], "metro_name": p["metro_name"], "matched_by": "alias"}
    city = hc.normalize_city(text.split(",")[0])
    hit = process.extractOne(f"{city} {text.split(',')[1].strip().upper()}" if "," in text else city,
                             list(store.place_choices), scorer=fuzz.WRatio)
    if hit and hit[1] >= 85:
        p = store.places[store.place_choices[hit[0]]]
        return {"area_code": p["area_code"], "metro_name": p["metro_name"], "matched_by": f"worksite city '{p['city']}, {p['state']}'"}
    areas = store.q("SELECT area_code, metro_name FROM areas")
    hit = process.extractOne(text, {a: m for a, m in areas}, scorer=fuzz.WRatio)
    if hit and hit[1] >= 80:
        return {"area_code": hit[2], "metro_name": hit[0], "matched_by": "OFLC area name"}
    return {"error": f"No wage area for '{text}'. Try a city and state, e.g. 'Austin, TX'."}


@function_tool
def find_location(place: str) -> str:
    """Map a city or region to its OFLC wage area (metro). Filter SQL on area_code: it covers every
    spelling of the city (NYC, Manhattan, Brooklyn...) and its suburbs.

    Args:
        place: e.g. 'NYC', 'Seattle', 'Bay Area', 'Austin, TX'.
    """
    return json.dumps(match_place(place))


def compute_wage_level(salary: float, role: str, location: str, soc_code: str | None = None) -> dict:
    r = match_role(role)
    if "error" in r:
        return r
    p = match_place(location)
    if "error" in p:
        return p
    socs = [soc_code] if soc_code else [s["soc_code"] for s in r["main_soc_codes"]]
    rows = []
    for soc in socs:
        rows = store.q("""SELECT soc_code, soc_title, level_1, level_2, level_3, level_4, geo_level
                          FROM wage_levels WHERE area_code = ? AND soc_code = ?""", [p["area_code"], soc])
        if rows:
            break
    if not rows:
        return {"error": f"No OFLC wage table for {r['role_family']} in {p['metro_name']}."}
    soc, soc_title, *thresholds, geo = rows[0]
    level = hc.wage_level(salary, thresholds)
    nxt = thresholds[level] if level < 4 else None
    peers = store.q("""
        SELECT count(*), round(100.0 * count(*) FILTER (wage_annual_from <= ?) / greatest(count(*), 1), 1),
               median(wage_annual_from)
        FROM lca WHERE role_family = ? AND area_code = ? AND case_status = 'CERTIFIED' AND wage_flag = 'ok'
          AND fiscal_year >= 2025""", [salary, r["role_family"], p["area_code"]])[0]
    return {
        "salary": salary, "role_family": r["role_family"], "soc_code": soc, "soc_title": soc_title,
        "area_code": p["area_code"], "metro_name": p["metro_name"],
        "wage_level": level, "lottery_entries": hc.LOTTERY_ENTRIES[level],
        "thresholds": {"level_1": thresholds[0], "level_2": thresholds[1], "level_3": thresholds[2], "level_4": thresholds[3]},
        "raise_needed_for_next_level": None if nxt is None else round(nxt - salary),
        "peer_filings_fy2025_on": peers[0], "salary_percentile_among_peer_filings": peers[1],
        "peer_median_offer": peers[2],
        "wage_year": "OFLC 2026-27 (Jul 2026 - Jun 2027)",
        "approximate": geo != 1,
        "note": ("Below Level I: an LCA can't be certified at this wage for this SOC and area." if level == 0 else
                 f"Level {level} = {level} lottery entr{'y' if level == 1 else 'ies'} under the wage-weighted lottery."),
    }


@function_tool
def wage_level(salary: float, role: str, location: str, soc_code: str | None = None) -> str:
    """Turn an offer into its OFLC wage level (I-IV) and wage-weighted H-1B lottery entries (1-4), with the
    four salary thresholds, the raise needed for the next level, and where the salary sits among real
    filings for the same role and metro.

    Args:
        salary: Annual salary in USD, e.g. 120000.
        role: Role in plain words, e.g. 'data scientist'.
        location: City or metro, e.g. 'NYC'.
        soc_code: Optional SOC code override, e.g. '15-2051'.
    """
    return json.dumps(compute_wage_level(salary, role, location, soc_code), default=str)


# --- Guardrails: block the mistakes the plain agent makes ---


def _reject(msg: str) -> ToolGuardrailFunctionOutput:
    # The model reads this instead of a result, and tries again.
    return ToolGuardrailFunctionOutput.reject_content("Rejected: " + msg)


SQL_RULES = [
    (r"\b(avg|median|mean|sum|min|max|quantile\w*|percentile\w*)\s*\(\s*(distinct\s+)?(\w+\.)?wage_(from|to)_raw",
     "wage_from_raw mixes hourly, monthly and yearly amounts. Aggregate wage_annual_from instead."),
    (r"\b(\w+\.)?(employer|employer_name_raw)\s+(not\s+)?i?like\b|\bemployer_name_raw\s*=",
     "employer names have many spellings. Call find_employer and filter on employer_id."),
    (r"\b(\w+\.)?(job_title|title_norm)\s+(not\s+)?i?like\b|\bjob_title\s*=",
     "job titles are free text. Call find_role and filter on role_family."),
    (r"\b(\w+\.)?worksite_city(_raw)?\s+(not\s+)?i?like\b|\bworksite_city_raw\s*=",
     "city spellings vary. Call find_location and filter on area_code."),
]


def check_sql(query: str) -> str | None:
    """Why a query must be rewritten, or None if it may run."""
    bare = re.sub(r"--[^\n]*|/\*.*?\*/", " ", query, flags=re.S).strip()
    if not re.match(r"(?is)^\(?\s*(select|with)\b", bare):
        return "only SELECT or WITH queries are allowed."
    if ";" in bare.rstrip().rstrip(";"):
        return "one statement per call."
    for pattern, msg in SQL_RULES:
        if re.search(pattern, bare, re.I):
            return msg
    if re.search(r"\b(avg|median|quantile\w*|percentile\w*)\s*\(\s*(\w+\.)?wage_annual", bare, re.I) and "wage_flag" not in bare:
        return "add wage_flag = 'ok' to exclude unit mix-ups and bad wages from pay statistics."
    return None


@tool_input_guardrail
def sql_guardrails(data) -> ToolGuardrailFunctionOutput:
    problem = check_sql(json.loads(data.context.tool_arguments or "{}").get("query", ""))
    return _reject(problem) if problem else ToolGuardrailFunctionOutput.allow()


@function_tool(tool_input_guardrails=[sql_guardrails])
def run_sql(ctx: RunContextWrapper[RequestState], query: str) -> str:
    """Run one DuckDB SELECT against the H-1B database. Returns up to 200 rows.

    Args:
        query: A DuckDB SQL query.
    """
    ctx.context.sql_calls += 1
    # The SDK runs tools in threads. Each call gets its own cursor: DuckDB connections aren't thread-safe.
    with store.db.cursor() as cursor:
        timer = threading.Timer(SQL_TIMEOUT_S, cursor.interrupt)
        timer.start()
        try:
            cursor.execute(query)
            rows = cursor.fetchmany(MAX_ROWS + 1)
        except duckdb.Error as e:
            # The model cannot see an exception. Return something it can reason about.
            msg = "Query took too long; add filters or aggregate." if "INTERRUPT" in str(e).upper() else str(e)
            return json.dumps({"error": msg[:800]})
        finally:
            timer.cancel()
        columns = [c[0] for c in cursor.description or []]
    result = {"columns": columns, "rows": [list(r) for r in rows[:MAX_ROWS]], "row_count": min(len(rows), MAX_ROWS),
              "truncated": len(rows) > MAX_ROWS}
    if re.search(r"\blca\b", query, re.I) and "case_status" not in query.lower():
        result["note"] = "No case_status filter: withdrawn and denied filings are included."
    ctx.context.last_result = json.loads(json.dumps(result, default=str))
    return json.dumps(result, default=str)


def _vl_type(values: list) -> str:
    vals = [v for v in values if v is not None]
    if vals and all(isinstance(v, (int, float)) for v in vals):
        return "quantitative"
    return "nominal"


@function_tool
def make_chart(ctx: RunContextWrapper[RequestState], mark: str, x: str, y: str,
               color: str | None = None, title: str = "") -> str:
    """Draw the LAST run_sql result as a chart in the page. Call once per answer when there are 3+ rows.

    Args:
        mark: 'bar' (compare categories), 'line' (over fiscal years/quarters) or 'point' (two numbers).
        x: Column for the x axis (the category or the time column).
        y: Column for the y axis (the number).
        color: Optional column to split by.
        title: Short chart title, e.g. 'Median ML engineer offer, NYC, FY2025'.
    """
    res = ctx.context.last_result
    if not res or not res["rows"]:
        return json.dumps({"error": "Run a query with results first."})
    cols = res["columns"]
    for f in [x, y] + ([color] if color else []):
        if f not in cols:
            return json.dumps({"error": f"'{f}' is not in the last result. Columns: {cols}"})
    if mark not in ("bar", "line", "point"):
        return json.dumps({"error": "mark must be bar, line or point."})
    data = [dict(zip(cols, r)) for r in res["rows"]]
    xt, yt = _vl_type([d[x] for d in data]), _vl_type([d[y] for d in data])
    if x in ("fiscal_year", "quarter", "fy", "year"):
        xt = "ordinal"
    enc = {"x": {"field": x, "type": xt}, "y": {"field": y, "type": yt}}
    if mark == "bar" and xt == "nominal" and yt == "quantitative":
        # Horizontal bars: long employer names stay readable.
        enc = {"y": {"field": x, "type": "nominal", "sort": "-x", "title": None},
               "x": {"field": y, "type": "quantitative"}}
    if color:
        enc["color"] = {"field": color, "type": "nominal" if color not in ("fiscal_year",) else "ordinal"}
    enc["tooltip"] = [{"field": c, "type": _vl_type([d[c] for d in data])} for c in cols]
    ctx.context.chart = {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "title": title, "data": {"values": data}, "mark": {"type": mark, "point": mark == "line"},
        "encoding": enc, "width": "container",
    }
    return json.dumps({"ok": True, "note": "Chart shown to the user. Do not describe the chart's styling."})


# --- The Agent ---

INSTRUCTIONS = f"""\
You are the H-1B Analyst. You help international students and anyone weighing an H-1B offer understand
who sponsors a role, what they offer, and how many entries an offer gets in the wage-weighted H-1B lottery.
Your data: every H-1B Labor Condition Application (LCA) the Department of Labor published from FY2024 Q1
to {MAPPINGS['as_of']}, cleaned offline, plus the OFLC 2026-27 prevailing-wage tables.

How to work:
1. Call read_mappings once per conversation, first. Check its `limitations` against the question.
   If the data cannot answer it, say so in one sentence, say what you CAN answer instead, and run no SQL.
2. Resolve every name before SQL: find_employer -> employer_id, find_role -> role_family,
   find_location -> area_code. Call them together in one turn when you need several.
   For an offer ("$120k data scientist in NYC"), call wage_level.
3. Write one focused DuckDB query (run_sql). Defaults unless the user asks otherwise:
   case_status = 'CERTIFIED'; pay = median(wage_annual_from) with wage_flag = 'ok';
   "how many jobs/workers" = sum(total_worker_positions); "how many filings" = count(*).
   "New grads" / "entry level": pw_wage_level = 'I' (employer-chosen level) and/or seniority in ('junior','intern').
   "Lottery odds" for filings: offer_lottery_entries (1-4). Universities (employer_type = 'university') are
   usually cap-exempt, so they skip the lottery: say so when they appear.
4. If the result has 3 or more rows, call make_chart exactly once on it.

How to answer:
- First sentence answers the question with the key number.
- Then 2-4 short bullets of evidence. Always state the fiscal years, the filters, and the number of filings
  behind each statistic; when it is under 20, call it a small sample.
- Medians, never means, for pay. Round money to the nearest $1k (e.g. $152k).
- LCAs are filings, not approvals: never call them visas, approvals or hires.
- Plain English. No SQL unless asked. No tables in the text: the page shows the result table.
- Use only numbers from tool results. Never invent figures. Under 170 words.
"""

agent = Agent(
    name=AGENT_NAME,
    instructions=INSTRUCTIONS,
    # LiteLLM routes the call to Gemini. api_key is unused: Vertex AI authenticates with gcloud credentials.
    model=LitellmModel(model=MODEL, api_key="unused"),
    model_settings=ModelSettings(extra_args={"vertex_location": VERTEX_LOCATION, "timeout": 90, "num_retries": 2}),
    tools=[read_mappings, get_enum_values, find_employer, find_role, find_location, wage_level, run_sql, make_chart],
)


class RecordToolCalls(RunHooks):
    """Records each tool call, with the agent that made it, for the page to show. One per request."""

    def __init__(self):
        self.tool_calls = []

    async def on_tool_end(self, context, agent, tool, result):
        args = getattr(context, "tool_arguments", None) or "{}"
        self.tool_calls += [{"agent": agent.name, "name": tool.name, "args": json.loads(args), "result": str(result)[:6000]}]


async def ask(message: str, session_id: str | None = None, max_turns: int = 15) -> dict:
    """Run the agent once. Used by /chat, evals/check.py and compare.py."""
    load_store()
    session_id = session_id or str(uuid.uuid4())
    session = SQLiteSession(session_id, SESSIONS_DB)
    hooks, state = RecordToolCalls(), RequestState()
    try:
        result = await Runner.run(agent, message, session=session, hooks=hooks, context=state, max_turns=max_turns)
        response = result.final_output
    except Exception as e:  # noqa: BLE001 - show it in the chat, not as a 500
        name = type(e).__name__
        response = ("That question needed more steps than I allow. Try narrowing it (one employer, role or city)."
                    if name == "MaxTurnsExceeded" else
                    f"Sorry, the model call failed ({name}). Try again in a moment. Details: {str(e)[:200]}")
    table = state.last_result if state.last_result and state.last_result["rows"] else None
    return {"response": response, "session_id": session_id, "tool_calls": hooks.tool_calls,
            "chart": state.chart, "table": table}


# --- FastAPI App ---


@asynccontextmanager
async def lifespan(app):
    load_store()
    yield


app = FastAPI(lifespan=lifespan)


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    tool_calls: list[dict]
    chart: dict | None = None
    table: dict | None = None


class OfferRequest(BaseModel):
    salary: float
    role: str
    location: str


@app.get("/")
def index():
    return FileResponse(ROOT / "index.html")


@app.get("/health")
def health():
    return {"ok": store.db is not None, "database": store.source}


@app.get("/api/meta")
def meta():
    """Facts for the page header and the calculator's dropdowns."""
    metros = [m for (m,) in store.q("""SELECT metro_name FROM lca WHERE metro_name IS NOT NULL
                                       GROUP BY 1 ORDER BY count(*) DESC LIMIT 40""")]
    roles = [f for (f,) in store.q("""SELECT role_family FROM lca WHERE role_family NOT IN ('Other')
                                      GROUP BY 1 ORDER BY count(*) DESC""")]
    return {"as_of": MAPPINGS["as_of"], "stats": MAPPINGS["stats"], "synthetic": MAPPINGS.get("synthetic", False),
            "database": store.source, "metros": metros, "roles": roles}


@app.post("/api/offer")
def offer(req: OfferRequest):
    """The lottery calculator: deterministic, no model call, instant."""
    if not 10_000 <= req.salary <= 2_000_000:
        return JSONResponse({"error": "Enter a yearly salary between $10,000 and $2,000,000."}, status_code=400)
    return compute_wage_level(req.salary, req.role, req.location)


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    return await ask(request.message, request.session_id)


@app.post("/clear")
async def clear(session_id: str | None = None):
    if session_id:
        await SQLiteSession(session_id, SESSIONS_DB).clear_session()
    return {"status": "ok"}


if __name__ == "__main__":
    # Cloud Run sets PORT and needs 0.0.0.0; locally this is http://localhost:8000.
    uvicorn.run(app, host="0.0.0.0" if ON_CLOUD_RUN else "127.0.0.1", port=int(os.environ.get("PORT", 8000)))
