"""Offline build: raw DOL files -> a clean, query-ready DuckDB file + the agent's mappings.

Run once on your laptop, never on Cloud Run:

    uv run build.py              # rules + SOC fallback for role families
    uv run build.py --llm        # also ask Gemini to label titles the rules miss (cached)

Inputs (download by hand, see README "Data"):
    raw/lca/*.xlsx|*.csv|*.parquet   DOL OFLC LCA disclosure files, FY2024 Q1 .. FY2026 Q3
    raw/pw/ALC_Export.csv            OFLC prevailing wages (wage year 2026-27), Level I-IV per SOC x area
    raw/pw/Geography.csv             OFLC area <-> county/town
    raw/uscis/*.csv                  USCIS H-1B Employer Data Hub exports (Crosstab View -> Download -> CSV),
                                     FY2024 .. FY2026: petition approvals and denials per employer

Outputs:
    data/h1b.duckdb           full database (upload to GCS; too big for GitHub)
    data/h1b_sample.duckdb    2% of filings + all lookup tables (committed, for local runs)
    data/mappings.json        the agent's offline context: columns, enums, glossary, limits
    data/baseline.duckdb      raw H-1B rows as DOL ships them, for baseline.py (local only)
    docs/build_report.md      row counts and coverage numbers for the README

Steps:
    1. Load every quarter, keep H-1B, map DOL column names, dedupe amendments.
    2. Annualize wages (hour/week/bi-weekly/month/year) and flag outliers.
    3. Resolve employers: normalize names, apply employer_overrides.csv, group.
    4. Classify roles: title rules -> SOC fallback -> (optional) Gemini, cached in role_cache.json.
    5. Map worksites to OFLC wage areas (county, then town, then the city's usual area).
    6. Build the Level I-IV wage table and compute each offer's level and lottery entries.
    7. Load USCIS petition decisions and match each petitioner to the same employer_id.
    8. Write the database, the sample and mappings.json.
"""

import argparse
import csv
import io
import json
import re
import time
from collections import Counter
from pathlib import Path

import duckdb

import h1b_common as hc

ROOT = Path(__file__).parent
RAW = ROOT / "raw"
DATA = ROOT / "data"
DOCS = ROOT / "docs"
CACHE = RAW / "cache"
ROLE_CACHE = ROOT / "role_cache.json"
SAMPLE_RATE = 0.02

# Our name -> DOL column names it may appear under (names drift across years).
COLUMN_MAP = {
    "case_number": ["CASE_NUMBER"],
    "case_status": ["CASE_STATUS"],
    "received_date": ["RECEIVED_DATE"],
    "decision_date": ["DECISION_DATE"],
    "visa_class": ["VISA_CLASS"],
    "job_title": ["JOB_TITLE"],
    "soc_code": ["SOC_CODE"],
    "soc_title": ["SOC_TITLE"],
    "full_time": ["FULL_TIME_POSITION"],
    "begin_date": ["BEGIN_DATE"],
    "total_worker_positions": ["TOTAL_WORKER_POSITIONS", "TOTAL_WORKERS"],
    "new_employment": ["NEW_EMPLOYMENT"],
    "continued_employment": ["CONTINUED_EMPLOYMENT"],
    "change_previous_employment": ["CHANGE_PREVIOUS_EMPLOYMENT"],
    "new_concurrent_employment": ["NEW_CONCURRENT_EMPLOYMENT"],
    "change_employer": ["CHANGE_EMPLOYER"],
    "amended_petition": ["AMENDED_PETITION"],
    "employer_name": ["EMPLOYER_NAME"],
    "employer_city": ["EMPLOYER_CITY"],
    "employer_state": ["EMPLOYER_STATE"],
    "naics_code": ["NAICS_CODE"],
    "worksite_city": ["WORKSITE_CITY"],
    "worksite_county": ["WORKSITE_COUNTY"],
    "worksite_state": ["WORKSITE_STATE"],
    "worksite_zip": ["WORKSITE_POSTAL_CODE"],
    "wage_from": ["WAGE_RATE_OF_PAY_FROM"],
    "wage_to": ["WAGE_RATE_OF_PAY_TO"],
    "wage_unit": ["WAGE_UNIT_OF_PAY"],
    "pw": ["PREVAILING_WAGE"],
    "pw_unit": ["PW_UNIT_OF_PAY"],
    "pw_wage_level": ["PW_WAGE_LEVEL"],
    "h1b_dependent": ["H_1B_DEPENDENT", "H1B_DEPENDENT"],
    "willful_violator": ["WILLFUL_VIOLATOR"],
    "total_worksite_locations": ["TOTAL_WORKSITE_LOCATIONS"],
}
REQUIRED = ["case_number", "case_status", "visa_class", "job_title", "soc_code", "employer_name",
            "worksite_city", "worksite_state", "wage_from", "wage_unit"]


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# --- 1. Load ---


def lca_files() -> tuple[list[Path], bool]:
    files = sorted(p for p in (RAW / "lca").glob("*") if p.suffix.lower() in {".xlsx", ".csv", ".parquet"})
    real = [p for p in files if "SYNTHETIC" not in p.name.upper()]
    if real:
        return real, False
    if files:
        log("Only SYNTHETIC files in raw/lca: building a dev-only database.")
        return files, True
    raise SystemExit("No LCA files in raw/lca/. Download them first (README > Data).")


def to_parquet(con, path: Path) -> Path:
    """Convert one raw file to Parquet once, all columns as text, so later runs are fast."""
    CACHE.mkdir(parents=True, exist_ok=True)
    out = CACHE / (path.stem + ".parquet")
    if out.exists() and out.stat().st_mtime > path.stat().st_mtime:
        return out
    log(f"converting {path.name}")
    if path.suffix.lower() == ".xlsx":
        con.execute("INSTALL excel; LOAD excel;")
        src = f"read_xlsx('{path}', all_varchar = true)"
    elif path.suffix.lower() == ".csv":
        src = f"read_csv('{path}', all_varchar = true, header = true)"
    else:
        src = f"read_parquet('{path}')"
    con.execute(f"COPY (SELECT * FROM {src}) TO '{out}' (FORMAT parquet, COMPRESSION zstd)")
    return out


def fiscal_period(name: str) -> tuple[int | None, int | None]:
    m = re.search(r"FY\s*(\d{4}).*?Q([1-4])", name, re.IGNORECASE)
    return (int(m.group(1)), int(m.group(2))) if m else (None, None)


def load_lca(con):
    files, synthetic = lca_files()
    parts = []
    for f in files:
        pq = to_parquet(con, f)
        cols = {d[0].upper(): d[0] for d in con.execute(f"SELECT * FROM '{pq}' LIMIT 0").description}
        select = []
        for ours, theirs in COLUMN_MAP.items():
            src = next((cols[t] for t in theirs if t in cols), None)
            select.append(f'"{src}"::VARCHAR AS {ours}' if src else f"NULL::VARCHAR AS {ours}")
            if src is None and ours in REQUIRED:
                raise SystemExit(f"{f.name} has no column for {ours} (tried {theirs}). Check the record layout.")
        fy, q = fiscal_period(f.name)
        select += [f"'{f.name}' AS source_file", f"{fy or 'NULL'}::INT AS file_fy", f"{q or 'NULL'}::INT AS file_q"]
        parts.append(f"SELECT {', '.join(select)} FROM '{pq}'")

    con.execute("CREATE OR REPLACE TABLE raw_union AS " + " UNION ALL ".join(parts))

    # The plain agent (baseline.py) sees H-1B rows as DOL ships them, original column names.
    con.execute("""
        CREATE OR REPLACE MACRO unit_name(x) AS CASE regexp_replace(upper(trim(x)), '[^A-Z]', '', 'g')
            WHEN 'HOUR' THEN 'Hour' WHEN 'WEEK' THEN 'Week' WHEN 'BIWEEKLY' THEN 'Bi-Weekly'
            WHEN 'MONTH' THEN 'Month' WHEN 'YEAR' THEN 'Year' END;
        CREATE OR REPLACE MACRO parse_num(x) AS
            try_cast(regexp_replace(trim(x), '[$,\\s]', '', 'g') AS DOUBLE);
        CREATE OR REPLACE MACRO parse_date(x) AS coalesce(
            try_cast(try_cast(x AS TIMESTAMP) AS DATE),
            try_cast(x AS DATE),
            try_strptime(x, '%m/%d/%Y')::DATE,
            CASE WHEN regexp_full_match(trim(x), '\\d{5}(\\.0+)?')
                 THEN DATE '1899-12-30' + try_cast(try_cast(x AS DOUBLE) AS INT) END);
    """)
    return synthetic


def clean_lca(con):
    con.execute("""
        CREATE OR REPLACE TABLE stage AS
        SELECT
            trim(case_number) AS case_number,
            upper(trim(case_status)) AS case_status,
            parse_date(received_date) AS received_date,
            parse_date(decision_date) AS decision_date,
            trim(job_title) AS job_title,
            left(trim(soc_code), 7) AS soc_code,
            trim(soc_title) AS soc_title,
            upper(left(trim(full_time), 1)) AS full_time,
            coalesce(try_cast(parse_num(total_worker_positions) AS INT), 1) AS total_worker_positions,
            coalesce(try_cast(parse_num(new_employment) AS INT), 0) AS new_employment,
            coalesce(try_cast(parse_num(continued_employment) AS INT), 0) AS continued_employment,
            coalesce(try_cast(parse_num(change_previous_employment) AS INT), 0) AS change_previous_employment,
            coalesce(try_cast(parse_num(new_concurrent_employment) AS INT), 0) AS new_concurrent_employment,
            coalesce(try_cast(parse_num(change_employer) AS INT), 0) AS change_employer,
            coalesce(try_cast(parse_num(amended_petition) AS INT), 0) AS amended_petition,
            trim(employer_name) AS employer_name_raw,
            upper(trim(employer_state)) AS employer_state,
            left(trim(naics_code), 6) AS naics_code,
            trim(worksite_city) AS worksite_city_raw,
            trim(worksite_county) AS worksite_county,
            upper(trim(worksite_state)) AS worksite_state,
            left(trim(worksite_zip), 5) AS worksite_zip,
            parse_num(wage_from) AS wage_from_raw,
            parse_num(wage_to) AS wage_to_raw,
            unit_name(wage_unit) AS wage_unit,
            parse_num(pw) AS pw_raw,
            unit_name(pw_unit) AS pw_unit,
            CASE WHEN upper(trim(pw_wage_level)) IN ('I', 'II', 'III', 'IV') THEN upper(trim(pw_wage_level)) END AS pw_wage_level,
            CASE WHEN upper(trim(h1b_dependent)) LIKE 'Y%' THEN 'Y'
                 WHEN upper(trim(h1b_dependent)) LIKE 'N%' THEN 'N' END AS h1b_dependent,
            CASE WHEN upper(trim(willful_violator)) LIKE 'Y%' THEN 'Y'
                 WHEN upper(trim(willful_violator)) LIKE 'N%' THEN 'N' END AS willful_violator,
            coalesce(try_cast(parse_num(total_worksite_locations) AS INT), 1) AS total_worksite_locations,
            source_file, file_fy, file_q
        FROM raw_union
        WHERE upper(trim(visa_class)) = 'H-1B' AND case_number IS NOT NULL
        -- An amended case appears again in a later file: keep its latest decision.
        QUALIFY row_number() OVER (PARTITION BY trim(case_number)
                                   ORDER BY parse_date(decision_date) DESC NULLS LAST, source_file DESC) = 1
    """)
    # US fiscal year: Oct 1 - Sep 30. Prefer the file's label; fall back to the decision date.
    con.execute("""
        ALTER TABLE stage ADD COLUMN fiscal_year INT;
        ALTER TABLE stage ADD COLUMN quarter INT;
        UPDATE stage SET
            fiscal_year = coalesce(file_fy, year(decision_date) + CASE WHEN month(decision_date) >= 10 THEN 1 ELSE 0 END),
            -- DOL files are cumulative within a fiscal year, so the file name's quarter is only a
            -- fallback: a case decided in November is Q1 even if it came from the Q3 file.
            quarter = coalesce(CASE WHEN month(decision_date) >= 10 THEN 1
                                    WHEN month(decision_date) <= 3 THEN 2
                                    WHEN month(decision_date) <= 6 THEN 3
                                    WHEN decision_date IS NOT NULL THEN 4 END, file_q);
    """)
    log(f"stage: {con.execute('SELECT count(*) FROM stage').fetchone()[0]:,} H-1B filings after dedupe")


# --- 2. Wages ---


def annualize(con):
    con.execute("""
        CREATE OR REPLACE MACRO annual(v, unit) AS CASE unit
            WHEN 'Hour' THEN v * 2080 WHEN 'Week' THEN v * 52 WHEN 'Bi-Weekly' THEN v * 26
            WHEN 'Month' THEN v * 12 WHEN 'Year' THEN v END;
        ALTER TABLE stage ADD COLUMN wage_annual_from DOUBLE;
        ALTER TABLE stage ADD COLUMN wage_annual_to DOUBLE;
        ALTER TABLE stage ADD COLUMN pw_annual DOUBLE;
        ALTER TABLE stage ADD COLUMN wage_flag VARCHAR;
        UPDATE stage SET
            wage_annual_from = round(annual(wage_from_raw, wage_unit)),
            wage_annual_to = round(annual(CASE WHEN wage_to_raw > 0 THEN wage_to_raw ELSE wage_from_raw END, wage_unit)),
            pw_annual = round(annual(pw_raw, pw_unit));
        UPDATE stage SET wage_flag = CASE
            WHEN wage_annual_from IS NULL OR wage_annual_from <= 0 THEN 'missing'
            WHEN wage_unit = 'Year' AND wage_from_raw < 1000 THEN 'unit_mixup_hourly_as_year'
            WHEN wage_unit = 'Hour' AND wage_from_raw > 1000 THEN 'unit_mixup_year_as_hourly'
            WHEN wage_annual_from < 20000 THEN 'too_low'
            WHEN wage_annual_from > 1000000 THEN 'too_high'
            ELSE 'ok' END;
    """)
    for flag, n in con.execute("SELECT wage_flag, count(*) FROM stage GROUP BY 1 ORDER BY 2 DESC").fetchall():
        log(f"  wage_flag {flag}: {n:,}")


# --- 3. Employers ---


def load_overrides() -> list[tuple[re.Pattern, str, str]]:
    with open(ROOT / "employer_overrides.csv") as f:
        return [(re.compile(r["pattern"]), r["canonical_name"], r["employer_type"]) for r in csv.DictReader(f)]


EMPLOYER_KEYS: dict[str, int] = {}  # group key -> employer_id, reused to match USCIS petitioners
LOOSE_KEYS: dict[str, int] = {}  # second-chance key (see loose_key) -> employer_id


def loose_key(raw: str) -> str:
    """A forgiving key for matching USCIS names to DOL names: USCIS drops apostrophes ("LOWES" for
    "LOWE'S") and writes "D B A" where DOL files "DBA" or "D/B/A"."""
    s = re.sub(r"\bD\s*/?\s*B\s*/?\s*A\b.*$", " ", raw.upper().replace("'", "").replace("\u2019", ""))
    return hc.normalize_employer(s).replace(" ", "")


def employer_key(raw: str, overrides) -> tuple[str, str | None]:
    """The key that groups one company's name variants: an override's canonical name, else the normalized name."""
    norm = hc.normalize_employer(raw)
    hit = next((canon for pat, canon, _ in overrides if pat.search(norm)), None)
    return ("OVR:" + hit if hit else "NORM:" + norm), hit


def resolve_employers(con):
    overrides = load_overrides()
    names = con.execute("""
        SELECT employer_name_raw, count(*) AS n, any_value(naics_code) AS naics,
               avg(CASE WHEN h1b_dependent = 'Y' THEN 1.0 ELSE 0 END) AS dep_share
        FROM stage WHERE employer_name_raw IS NOT NULL GROUP BY 1 ORDER BY 1
    """).fetchall()

    # Group key: an override's canonical name, else the normalized name.
    rows = []
    for raw, n, naics, dep in names:
        norm = hc.normalize_employer(raw)
        hit = next(((canon, etype) for pat, canon, etype in overrides if pat.search(norm)), None)
        key = "OVR:" + hit[0] if hit else "NORM:" + norm
        rows.append((raw, norm, key, hit[0] if hit else None, hit[1] if hit else None, n, naics, dep))

    groups: dict[str, dict] = {}
    for raw, norm, key, canon, etype, n, naics, dep in rows:
        g = groups.setdefault(key, {"names": Counter(), "n": 0, "naics": Counter(), "dep": 0.0,
                                    "canon": canon, "etype": etype})
        g["names"][raw] += n
        g["n"] += n
        if naics:
            g["naics"][naics] += n
        g["dep"] += dep * n

    employers, alias_rows = [], []
    for i, (key, g) in enumerate(sorted(groups.items(), key=lambda kv: (-kv[1]["n"], kv[0])), start=1):
        canon = g["canon"] or titlecase_company(g["names"].most_common(1)[0][0])
        naics = g["naics"].most_common(1)[0][0] if g["naics"] else None
        dep_share = g["dep"] / g["n"]
        etype = g["etype"] or employer_type(canon, naics, dep_share, g["n"])
        employers.append((i, canon, etype, naics, g["n"], len(g["names"]), round(dep_share, 3),
                          [a for a, _ in g["names"].most_common(25)]))
        alias_rows += [(raw, i) for raw in g["names"]]
        EMPLOYER_KEYS[key] = i
        for raw in g["names"]:  # biggest employer first, so it wins a shared loose key
            LOOSE_KEYS.setdefault(loose_key(raw), i)

    con.execute("""CREATE OR REPLACE TABLE employers (employer_id INT, employer VARCHAR, employer_type VARCHAR,
               naics_code VARCHAR, filings INT, alias_count INT, h1b_dependent_share DOUBLE, aliases VARCHAR[])""")
    con.executemany("INSERT INTO employers VALUES (?, ?, ?, ?, ?, ?, ?, ?)", employers)
    con.execute("CREATE OR REPLACE TABLE employer_alias (employer_name_raw VARCHAR, employer_id INT)")
    con.executemany("INSERT INTO employer_alias VALUES (?, ?)", alias_rows)
    log(f"employers: {len(names):,} raw names -> {len(employers):,} employers")


def titlecase_company(raw: str) -> str:
    keep_upper = {"LLC", "LLP", "IBM", "USA", "US", "NA", "IT", "AI", "HCL", "KPMG", "EY", "PWC", "SAP", "AT&T"}
    raw = re.sub(r"[,\s]+(INC|LLC|L\.L\.C|LLP|LP|L\.P|CORP|CORPORATION|CO|LTD|LIMITED|PLC|N\.A)\.?$", "", raw.strip(), flags=re.I)
    words = re.sub(r"\s+", " ", raw.strip().rstrip(".,")).split(" ")
    return " ".join(w if w.upper() in keep_upper else w.capitalize() for w in words)


def employer_type(name: str, naics: str | None, dep_share: float, n: int) -> str:
    if (naics or "").startswith("6113") or re.search(r"UNIVERSITY|COLLEGE|INSTITUTE OF TECHNOLOGY", name.upper()):
        return "university"
    if (naics or "")[:4] in ("5415", "5416", "5613") and dep_share >= 0.5:
        return "staffing_it_services"
    if dep_share >= 0.5 and n >= 10:
        return "h1b_dependent"
    return "other"


# --- 4. Roles ---


def classify_roles(con, use_llm: bool):
    pairs = con.execute("SELECT job_title, soc_code, count(*) FROM stage GROUP BY 1, 2").fetchall()
    cache = json.loads(ROLE_CACHE.read_text()) if ROLE_CACHE.exists() else {}
    out, unmatched = [], Counter()
    for title, soc, n in pairs:
        norm = hc.normalize_title(title)
        family, how = hc.classify(norm, soc)
        if family == "Other" and norm in cache:
            family, how = cache[norm], "llm"
        if family == "Other":
            unmatched[norm] += n
        out.append((title, soc, norm, family, how, hc.seniority(norm)))

    if use_llm and unmatched:
        cache |= llm_classify([t for t, n in unmatched.most_common() if n >= 2 and t not in cache][:20000])
        ROLE_CACHE.write_text(json.dumps(cache, indent=0, sort_keys=True))
        out = [(t, s, nm, cache.get(nm, f) if f == "Other" else f, "llm" if f == "Other" and nm in cache else h, sn)
               for t, s, nm, f, h, sn in out]

    con.execute("""CREATE OR REPLACE TABLE role_titles (job_title VARCHAR, soc_code VARCHAR, title_norm VARCHAR,
               role_family VARCHAR, classified_by VARCHAR, seniority VARCHAR)""")
    con.executemany("INSERT INTO role_titles VALUES (?, ?, ?, ?, ?, ?)", out)
    for how, n in con.execute("""SELECT classified_by, count(*) FROM stage s JOIN role_titles r
                             ON s.job_title IS NOT DISTINCT FROM r.job_title AND s.soc_code IS NOT DISTINCT FROM r.soc_code
                             GROUP BY 1 ORDER BY 2 DESC""").fetchall():
        log(f"  roles by {how}: {n:,}")


def llm_classify(titles: list[str]) -> dict[str, str]:
    import litellm

    families = [f for f in hc.ROLE_FAMILIES if f != "Other"] + ["Other"]
    labels = {}
    for i in range(0, len(titles), 200):
        batch = titles[i:i + 200]
        prompt = ("Classify each H-1B job title into exactly one role family from this list:\n"
                  + json.dumps(families) + "\nReturn a JSON object mapping each title to its family.\n\n"
                  + json.dumps(batch))
        for attempt in range(3):
            try:
                r = litellm.completion(model="vertex_ai/gemini-3.5-flash-lite", vertex_location="global",
                                       messages=[{"role": "user", "content": prompt}],
                                       response_format={"type": "json_object"})
                got = json.loads(r.choices[0].message.content)
                labels |= {t: f for t, f in got.items() if t in batch and f in families}
                break
            except Exception as e:  # noqa: BLE001 - retry anything, log it
                log(f"  llm batch {i // 200} attempt {attempt + 1} failed: {e}")
        log(f"  llm labeled {len(labels):,}/{len(titles):,}")
    return labels


# --- 5. Places ---


def map_locations(con):
    geo = RAW / "pw" / "Geography.csv"
    con.execute(f"CREATE OR REPLACE TABLE geography AS SELECT * FROM read_csv('{geo}', all_varchar = true)")
    state_ab = dict(con.execute("SELECT DISTINCT upper(State), StateAb FROM geography").fetchall())
    county_area = {}
    for area, name, st, county in con.execute("SELECT Area, AreaName, StateAb, CountyTownName FROM geography").fetchall():
        county_area.setdefault((hc.normalize_county(county), st), (area, name))

    places = con.execute("""SELECT worksite_city_raw, worksite_county, worksite_state, count(*)
                        FROM stage GROUP BY 1, 2, 3""").fetchall()
    resolved, by_city = [], Counter()
    for city, county, state, n in places:
        st = state if state and len(state) == 2 else state_ab.get((state or "").upper(), state)
        city_norm = hc.normalize_city(city, st)
        hit = county_area.get((hc.normalize_county(county), st)) or county_area.get((hc.normalize_county(city), st))
        if city_norm == "NEW YORK CITY" and st == "NY" and not hit:
            hit = county_area.get(("NEW YORK", "NY"))
        resolved.append([city, county, state, st, city_norm, hit])
        if hit:
            by_city[(city_norm, st, hit)] += n

    # Fallback: a city with no usable county goes to the area its other filings use most.
    usual = {}
    for (city_norm, st, hit), n in by_city.most_common():
        usual.setdefault((city_norm, st), hit)
    rows = []
    for city, county, state, st, city_norm, hit in resolved:
        hit = hit or usual.get((city_norm, st))
        rows.append((city, county, state, st, city_norm.title() if city_norm else None,
                     hit[0] if hit else None, hit[1] if hit else None))
    con.execute("""CREATE OR REPLACE TABLE place_map (worksite_city_raw VARCHAR, worksite_county VARCHAR,
               worksite_state VARCHAR, state_ab VARCHAR, worksite_city VARCHAR, area_code VARCHAR, metro_name VARCHAR)""")
    con.executemany("INSERT INTO place_map VALUES (?, ?, ?, ?, ?, ?, ?)", rows)


# --- 6. Wage levels ---


def build_wage_levels(con):
    alc = RAW / "pw" / "ALC_Export.csv"
    con.execute(f"""
        CREATE OR REPLACE TABLE areas AS
        SELECT Area AS area_code, any_value(AreaName) AS metro_name,
               string_agg(DISTINCT StateAb, ',' ORDER BY StateAb) AS states,
               count(*) AS counties_or_towns
        FROM geography GROUP BY 1;

        CREATE OR REPLACE TABLE wage_levels AS
        SELECT a.Area AS area_code, g.metro_name, a.SocCode AS soc_code, o.soc_title,
               round(try_cast(a.Level1 AS DOUBLE) * 2080) AS level_1,
               round(try_cast(a.Level2 AS DOUBLE) * 2080) AS level_2,
               round(try_cast(a.Level3 AS DOUBLE) * 2080) AS level_3,
               round(try_cast(a.Level4 AS DOUBLE) * 2080) AS level_4,
               try_cast(a.GeoLvl AS INT) AS geo_level
        FROM read_csv('{alc}', all_varchar = true) a
        LEFT JOIN areas g ON g.area_code = a.Area
        LEFT JOIN (SELECT soc_code, any_value(soc_title) AS soc_title FROM (
                       SELECT soc_code, soc_title FROM stage WHERE soc_title IS NOT NULL) GROUP BY 1) o
               ON o.soc_code = a.SocCode
        WHERE try_cast(a.Level1 AS DOUBLE) > 0;
    """)
    log(f"wage_levels: {con.execute('SELECT count(*) FROM wage_levels').fetchone()[0]:,} SOC x area rows")


# --- 7. Assemble ---


def assemble(con):
    con.execute("""
        CREATE OR REPLACE TABLE lca AS
        SELECT
            s.case_number, s.case_status, s.fiscal_year, s.quarter, s.received_date, s.decision_date,
            s.job_title, r.title_norm, r.role_family, r.seniority, s.soc_code, s.soc_title, s.full_time,
            s.total_worker_positions,
            CASE WHEN s.new_employment > 0 THEN 'new_employment'
                 WHEN s.change_employer > 0 THEN 'change_employer'
                 WHEN s.new_concurrent_employment > 0 THEN 'new_concurrent'
                 WHEN s.continued_employment > 0 THEN 'continuation'
                 WHEN s.change_previous_employment > 0 THEN 'change_same_employer'
                 WHEN s.amended_petition > 0 THEN 'amended'
                 ELSE 'unspecified' END AS filing_type,
            s.new_employment, s.continued_employment, s.change_employer,
            e.employer_id, e.employer, e.employer_type, s.employer_name_raw, s.naics_code,
            p.worksite_city, s.worksite_city_raw, s.worksite_county, p.state_ab AS worksite_state, s.worksite_zip,
            p.area_code, p.metro_name,
            s.wage_from_raw, s.wage_to_raw, s.wage_unit, s.wage_annual_from, s.wage_annual_to, s.wage_flag,
            s.pw_annual, s.pw_wage_level,
            CASE s.pw_wage_level WHEN 'I' THEN 1 WHEN 'II' THEN 2 WHEN 'III' THEN 3 WHEN 'IV' THEN 4 END AS pw_level_num,
            CASE WHEN s.wage_flag <> 'ok' OR w.level_1 IS NULL THEN NULL
                 WHEN s.wage_annual_from >= w.level_4 THEN 4 WHEN s.wage_annual_from >= w.level_3 THEN 3
                 WHEN s.wage_annual_from >= w.level_2 THEN 2 WHEN s.wage_annual_from >= w.level_1 THEN 1
                 ELSE 0 END AS offer_wage_level,
            s.h1b_dependent, s.willful_violator, s.total_worksite_locations, s.source_file
        FROM stage s
        LEFT JOIN employer_alias a ON a.employer_name_raw = s.employer_name_raw
        LEFT JOIN employers e ON e.employer_id = a.employer_id
        LEFT JOIN role_titles r ON r.job_title IS NOT DISTINCT FROM s.job_title
                                AND r.soc_code IS NOT DISTINCT FROM s.soc_code
        LEFT JOIN place_map p ON p.worksite_city_raw IS NOT DISTINCT FROM s.worksite_city_raw
                              AND p.worksite_county IS NOT DISTINCT FROM s.worksite_county
                              AND p.worksite_state IS NOT DISTINCT FROM s.worksite_state
        LEFT JOIN wage_levels w ON w.area_code = p.area_code AND w.soc_code = s.soc_code;

        ALTER TABLE lca ADD COLUMN offer_lottery_entries INT;
        UPDATE lca SET offer_lottery_entries = offer_wage_level;

        -- Small, deduplicated lookup the find_role tool searches.
        CREATE OR REPLACE TABLE role_titles_summary AS
        SELECT title_norm, role_family, seniority, count(*) AS filings
        FROM lca WHERE title_norm <> '' GROUP BY ALL;
    """)
    n = con.execute("SELECT count(*) FROM lca").fetchone()[0]
    stage_n = con.execute("SELECT count(*) FROM stage").fetchone()[0]
    assert n == stage_n, f"join fan-out: lca {n} != stage {stage_n}"
    log(f"lca: {n:,} rows")


# --- 7. USCIS petitions ---

# Our column prefix -> the hub's column prefix. Each has an "Approval" and a "Denial" column.
USCIS_KINDS = {
    "new_employment": "New Employment",
    "continuation": "Continuation",
    "change_same_employer": "Change with Same Employer",
    "new_concurrent": "New Concurrent",
    "change_employer": "Change of Employer",
    "amended": "Amended",
}
PETITION_COUNTS = [f"{k}_{s}" for k in USCIS_KINDS for s in ("approved", "denied")]


def read_uscis(path: Path):
    """Yield one dict per row of a hub export. Tableau writes UTF-16, tab-separated; a re-saved CSV also works."""
    raw = path.read_bytes()
    text = raw.decode("utf-16" if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else "utf-8-sig")
    delimiter = "\t" if "\t" in text.split("\n", 1)[0] else ","
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    header = [h.strip() for h in next(reader)]
    for row in reader:
        yield dict(zip(header, row))


def load_petitions(con):
    """USCIS first decisions on H-1B petitions, one row per employer and fiscal year, on our employer_id."""
    con.execute(f"""CREATE OR REPLACE TABLE petitions (fiscal_year INT, employer_id INT, employer VARCHAR,
               in_lca BOOLEAN, industry VARCHAR, name_variants INT,
               {", ".join(c + " BIGINT" for c in PETITION_COUNTS)}, approved BIGINT, denied BIGINT)""")
    files = sorted((RAW / "uscis").glob("*.csv"))
    if not files:
        log("No raw/uscis/*.csv: petitions table left empty.")
        return
    overrides = load_overrides()
    canon_by_id = dict(con.execute("SELECT employer_id, employer FROM employers").fetchall())
    num = lambda v: int((v or "0").replace(",", "") or 0)  # noqa: E731
    groups: dict[tuple[int, str], dict] = {}
    raw_rows = 0
    for f in files:
        for d in read_uscis(f):
            name = (d.get("Employer (Petitioner) Name") or "").strip()
            fy = d.get("Fiscal Year", "").strip()
            if not fy.isdigit():
                continue
            raw_rows += 1
            key, canon = employer_key(name, overrides) if name else ("NONE", None)
            eid = EMPLOYER_KEYS.get(key) or (LOOSE_KEYS.get(loose_key(name)) if name else None)
            if eid:
                key = f"ID:{eid}"  # every spelling that reaches one employer lands in one row
            g = groups.setdefault((int(fy), key), {"names": Counter(), "industry": Counter(), "canon": canon,
                                                   "eid": eid, "counts": dict.fromkeys(PETITION_COUNTS, 0)})
            total = 0
            for ours, theirs in USCIS_KINDS.items():
                a, den = num(d.get(f"{theirs} Approval")), num(d.get(f"{theirs} Denial"))
                g["counts"][f"{ours}_approved"] += a
                g["counts"][f"{ours}_denied"] += den
                total += a + den
            g["names"][name] += max(total, 1)
            if d.get("Industry (NAICS) Code", "").strip():
                g["industry"][d["Industry (NAICS) Code"].strip()] += max(total, 1)

    rows = []
    for (fy, key), g in groups.items():
        eid = g["eid"]
        if key == "NONE":
            employer = "(name not reported)"
        else:
            employer = canon_by_id.get(eid) or g["canon"] or titlecase_company(g["names"].most_common(1)[0][0])
        c = g["counts"]
        approved = sum(v for k, v in c.items() if k.endswith("_approved"))
        denied = sum(v for k, v in c.items() if k.endswith("_denied"))
        industry = g["industry"].most_common(1)[0][0] if g["industry"] else None
        rows.append((fy, eid, employer, eid is not None, industry, len(g["names"]),
                     *[c[k] for k in PETITION_COUNTS], approved, denied))
    con.executemany(f"INSERT INTO petitions VALUES ({', '.join('?' * len(rows[0]))})", rows)
    matched, total = con.execute("SELECT sum(approved) FILTER (in_lca), sum(approved) FROM petitions").fetchone()
    log(f"petitions: {raw_rows:,} USCIS rows -> {len(rows):,} employer-years; "
        f"{100 * matched / max(total, 1):.1f}% of approvals matched to an LCA employer")


def write_baseline(con, path: Path):
    """The plain agent's database: H-1B rows with DOL's own column names and no cleaning."""
    path.unlink(missing_ok=True)
    con.execute(f"ATTACH '{path}' AS base")
    con.execute("""CREATE TABLE base.lca AS
               SELECT * EXCLUDE (file_fy, file_q) FROM raw_union WHERE upper(trim(visa_class)) = 'H-1B'""")
    con.execute("DETACH base")


def write_db(con, path: Path, sample: bool):
    path.unlink(missing_ok=True)
    con.execute(f"ATTACH '{path}' AS out")
    where = f"WHERE hash(case_number) % 1000 < {int(SAMPLE_RATE * 1000)}" if sample else ""
    con.execute(f"CREATE TABLE out.lca AS SELECT * FROM lca {where} ORDER BY fiscal_year, employer_id")
    for t in ["employers", "wage_levels", "areas", "role_titles_summary", "petitions"]:
        con.execute(f"CREATE TABLE out.{t} AS SELECT * FROM {t}")
    con.execute("DETACH out")
    log(f"wrote {path.name} ({path.stat().st_size / 1e6:.1f} MB)")


# --- Mappings: the agent's offline context ---

DESCRIPTIONS = {
    "lca": {
        "_table": "One row per H-1B Labor Condition Application (LCA) filed with the Department of Labor, FY2024 Q1 to FY2026 Q3, amendments deduplicated. An LCA is a filing an employer must make BEFORE an H-1B petition; it is not an approval or a visa.",
        "case_number": "DOL case number, unique per row.",
        "case_status": "DOL decision. Use 'CERTIFIED' for filings employers could actually use.",
        "fiscal_year": "US federal fiscal year of the decision (Oct 1 - Sep 30). FY2026 = Oct 2025 - Sep 2026.",
        "quarter": "Fiscal quarter 1-4 (Q1 = Oct-Dec).",
        "received_date": "Date DOL received the LCA.",
        "decision_date": "Date DOL decided the LCA.",
        "job_title": "Job title as typed by the employer (free text, messy). Do not filter on it: use role_family.",
        "title_norm": "Lowercased job title with abbreviations expanded (sr -> senior, ml -> machine learning).",
        "role_family": "Clean role category built offline from the title and SOC code. Get the value from find_role.",
        "seniority": "Seniority parsed from the title: intern, junior, mid, senior, staff_plus, manager or unspecified.",
        "soc_code": "Standard Occupational Classification code, e.g. 15-1252 = Software Developers.",
        "soc_title": "Name of the SOC occupation.",
        "full_time": "'Y' if full-time.",
        "total_worker_positions": "Number of workers this one LCA covers. SUM it to count jobs; COUNT(*) counts filings.",
        "filing_type": "Why the LCA was filed. 'new_employment' is the closest proxy for a new (often lottery) hire; 'continuation' is an extension; 'change_employer' is a transfer.",
        "new_employment": "Workers in this filing who are new employment.",
        "continued_employment": "Workers who are continuing employment (extensions).",
        "change_employer": "Workers transferring from another employer.",
        "employer_id": "Resolved employer key: all legal-name variants of one company share it. Get it from find_employer.",
        "employer": "Canonical employer name (e.g. 'Google' for GOOGLE LLC, Google Inc.). Get it from find_employer.",
        "employer_type": "big_tech, finance, consulting, staffing_it_services, h1b_dependent, university or other. Universities are usually cap-exempt (no lottery).",
        "employer_name_raw": "Employer name exactly as filed. Do not filter on it: use employer_id.",
        "naics_code": "Employer's industry code (NAICS).",
        "worksite_city": "Normalized worksite city ('New York City' covers Manhattan, Brooklyn, NYC, ...).",
        "worksite_city_raw": "Worksite city as typed by the employer.",
        "worksite_county": "Worksite county as filed.",
        "worksite_state": "Two-letter worksite state.",
        "worksite_zip": "Five-digit worksite ZIP code.",
        "area_code": "OFLC wage area (metro) code for the worksite. Get it from find_location.",
        "metro_name": "OFLC wage area name, e.g. 'New York-Newark-Jersey City, NY-NJ'.",
        "wage_from_raw": "Offered wage as filed, in wage_unit (mixes hourly and yearly). Never aggregate it.",
        "wage_to_raw": "Top of the offered wage range as filed, in wage_unit, often blank.",
        "wage_unit": "Unit of the raw wage: Hour, Week, Bi-Weekly, Month or Year.",
        "wage_annual_from": "Offered wage converted to a yearly amount (Hour x 2080, Week x 52, Bi-Weekly x 26, Month x 12). Use this for pay.",
        "wage_annual_to": "Top of the offered range, yearly (equals wage_annual_from when no range).",
        "wage_flag": "'ok' or why the wage is unreliable. Filter wage_flag = 'ok' for any pay statistic.",
        "pw_annual": "Prevailing wage the employer cited, yearly.",
        "pw_wage_level": "Wage level (I-IV) the EMPLOYER chose for the prevailing wage. Blank when a survey or union wage was used.",
        "pw_level_num": "pw_wage_level as a number 1-4.",
        "offer_wage_level": "Level (0-4) the OFFERED annual wage reaches in the 2026-27 OFLC table for this SOC and area; 0 = below Level I. Computed offline.",
        "offer_lottery_entries": "Lottery entries (1-4) this offer would get under the wage-weighted H-1B lottery, from offer_wage_level. Approximate: uses the 2026-27 wage table for all years.",
        "h1b_dependent": "'Y' if the employer declared itself H-1B dependent (a large share of its workforce is on H-1B).",
        "willful_violator": "'Y' if DOL found the employer a willful violator.",
        "total_worksite_locations": "Number of worksites on the filing.",
        "source_file": "DOL file the row came from.",
    },
    "employers": {
        "_table": "One row per resolved employer.",
        "employer_id": "Employer key (joins lca.employer_id).",
        "employer": "Canonical name.",
        "employer_type": "See lca.employer_type.",
        "naics_code": "Most common NAICS code across its filings.",
        "filings": "Number of H-1B LCAs in the data.",
        "alias_count": "How many raw name spellings were merged into this employer.",
        "h1b_dependent_share": "Share of its filings marked H-1B dependent.",
        "aliases": "Up to 25 raw name spellings, most common first.",
    },
    "wage_levels": {
        "_table": "OFLC prevailing wage thresholds for wage year Jul 2026 - Jun 2027, annualized (hourly x 2080). One row per area x SOC code.",
        "area_code": "OFLC wage area code (joins lca.area_code).",
        "metro_name": "Area name.",
        "soc_code": "SOC code (joins lca.soc_code).",
        "soc_title": "SOC occupation name.",
        "level_1": "Level I (entry) annual wage.",
        "level_2": "Level II annual wage.",
        "level_3": "Level III annual wage.",
        "level_4": "Level IV (fully competent) annual wage.",
        "geo_level": "1 = wage from this area's own data; higher = borrowed from a wider area.",
    },
    "areas": {
        "_table": "OFLC wage areas (metros and non-metro regions).",
        "area_code": "Area code.", "metro_name": "Area name.", "states": "States it covers.",
        "counties_or_towns": "Number of counties/towns in it.",
    },
    "role_titles_summary": {
        "_table": "Distinct normalized titles with their role family and filing counts. find_role searches this.",
        "title_norm": "Normalized title.", "role_family": "Role family.", "seniority": "Parsed seniority.",
        "filings": "Filings with this title.",
    },
    "petitions": {
        "_table": "USCIS H-1B Employer Data Hub, FY2024 to FY2026: the FIRST DECISION U.S. Citizenship and Immigration Services made on H-1B petitions (Form I-129), one row per employer and fiscal year. This is the step AFTER the LCA. Employer-level only: no role, salary, wage level or worksite. An approved petition is not yet a visa. FY2026 covers the full fiscal year (to Sep 30, 2026), while lca stops at FY2026 Q3.",
        "fiscal_year": "Fiscal year USCIS decided the petitions (Oct 1 - Sep 30). A petition is usually decided months after its LCA, often in the next fiscal year.",
        "employer_id": "Same key as lca.employer_id and employers.employer_id; NULL when the petitioner has no LCA in this database. Get it from find_employer.",
        "employer": "Canonical employer name (the lca name when matched, else the USCIS name).",
        "in_lca": "True when the petitioner was matched to an employer in lca.",
        "industry": "Employer's NAICS sector as USCIS reports it, e.g. '54 - Professional, Scientific, and Technical Services'.",
        "name_variants": "How many USCIS petitioner spellings were merged into this row.",
        "new_employment_approved": "Approved petitions for NEW employment: first-time H-1B workers, mostly lottery (cap) winners plus cap-exempt hires. The closest count to 'new H-1B hires approved'.",
        "new_employment_denied": "Denied new-employment petitions.",
        "continuation_approved": "Approved extensions for workers continuing with the same employer.",
        "continuation_denied": "Denied extensions.",
        "change_same_employer_approved": "Approved petitions changing the job terms with the same employer.",
        "change_same_employer_denied": "Denied same-employer change petitions.",
        "new_concurrent_approved": "Approved petitions for a second, concurrent H-1B job.",
        "new_concurrent_denied": "Denied concurrent petitions.",
        "change_employer_approved": "Approved transfers: workers already in H-1B status moving to this employer.",
        "change_employer_denied": "Denied transfers.",
        "amended_approved": "Approved amended petitions.",
        "amended_denied": "Denied amended petitions.",
        "approved": "All approved petitions that year (sum of the six *_approved columns).",
        "denied": "All denied petitions that year (sum of the six *_denied columns).",
    },
}

GLOSSARY = {
    "LCA": "Labor Condition Application: the employer's wage attestation to the Department of Labor, filed before an H-1B petition. Certified LCA != approved petition != visa. Many LCAs are never used.",
    "petition": "Form I-129, filed with USCIS after the LCA is certified. The `petitions` table has USCIS's first decisions (approved or denied) per employer and fiscal year. Pipeline: LCA (DOL) -> lottery registration (new cap-subject hires only) -> petition (USCIS) -> visa (State Department). Approval rate = approved / (approved + denied).",
    "LCAs vs petitions": "Employers file far more LCAs than petitions: one worker can need several LCAs (new worksite, amendment, extension), and many LCAs are never used. Compare the two as a ratio per employer, and say that fiscal years do not line up exactly.",
    "wage level": "OFLC sets four prevailing-wage levels per occupation and area: Level I (entry) to Level IV (fully competent).",
    "wage-weighted lottery": "Since the DHS rule effective Feb 27, 2026 (FY2027 cap season onward), each H-1B registration is entered once per wage level of the offered wage: Level I = 1 entry, II = 2, III = 3, IV = 4. Higher-paid offers have proportionally better odds.",
    "lottery entries": "offer_lottery_entries: 1-4, from the level the offered wage reaches in the OFLC table. 0 means the wage is below Level I.",
    "cap-exempt": "Universities, their affiliated nonprofits and nonprofit/government research organizations can sponsor H-1Bs without the lottery.",
    "fiscal year": "Oct 1 - Sep 30. FY2026 Q3 ends June 30, 2026 (the last data in this database).",
    "H-1B dependent": "An employer with a large share of H-1B workers; must make extra attestations. Common among IT staffing/outsourcing firms.",
    "filings vs workers": "COUNT(*) counts LCAs; SUM(total_worker_positions) counts positions.",
}

LIMITATIONS = [
    "Who won the lottery or was issued a visa. (Approved and denied PETITIONS per employer and fiscal year ARE available, in `petitions`.)",
    "Petition approvals or denials for a specific role, salary, wage level or city: `petitions` is employer-level only.",
    "Salaries actually paid: LCAs show the wage offered on the filing.",
    "Anything about an individual person, interview odds, offer rates or green-card (PERM) sponsorship.",
    "LCA filings after FY2026 Q3 (June 30, 2026), petition decisions after FY2026 (Sep 30, 2026), or anything before FY2024.",
    "Whether the $100,000 H-1B fee applies to a specific case, or immigration/legal advice.",
    "Exact selection probability: entries are known, but the total pool of registrations by level is not in this data.",
]

JOIN_HINTS = [
    "lca.employer_id = employers.employer_id",
    "lca.area_code = wage_levels.area_code AND lca.soc_code = wage_levels.soc_code",
    "lca.area_code = areas.area_code",
    "petitions.employer_id = lca.employer_id (aggregate lca per employer_id and fiscal_year BEFORE joining: petitions has one row per employer-year)",
]

EXAMPLE_QUERIES = [
    {"question": "Median offered pay and filing count for one employer's role family, by fiscal year",
     "sql": "SELECT fiscal_year, median(wage_annual_from) AS median_pay, count(*) AS filings FROM lca WHERE employer_id = 42 AND role_family = 'Data Engineer' AND case_status = 'CERTIFIED' AND wage_flag = 'ok' GROUP BY 1 ORDER BY 1"},
    {"question": "Share of an employer's new-employment filings at each employer-chosen wage level",
     "sql": "SELECT pw_wage_level, count(*) AS filings, round(100.0 * count(*) / sum(count(*)) OVER (), 1) AS pct FROM lca WHERE employer_id = 42 AND filing_type = 'new_employment' AND case_status = 'CERTIFIED' AND pw_wage_level IS NOT NULL GROUP BY 1 ORDER BY 1"},
    {"question": "Top employers by worker positions in a metro for a role family",
     "sql": "SELECT employer, sum(total_worker_positions) AS positions, count(*) AS filings FROM lca WHERE area_code = '12060' AND role_family = 'Software Engineer' AND case_status = 'CERTIFIED' GROUP BY 1 ORDER BY positions DESC LIMIT 10"},
    {"question": "Average lottery entries for offers by employer type",
     "sql": "SELECT employer_type, round(avg(offer_lottery_entries), 2) AS avg_entries, count(*) AS filings FROM lca WHERE case_status = 'CERTIFIED' AND offer_lottery_entries > 0 GROUP BY 1 ORDER BY avg_entries DESC"},
    {"question": "One employer's petition approvals, denials and approval rate by fiscal year",
     "sql": "SELECT fiscal_year, new_employment_approved, new_employment_denied, approved, denied, round(100.0 * approved / nullif(approved + denied, 0), 1) AS approval_pct FROM petitions WHERE employer_id = 42 ORDER BY 1"},
    {"question": "Certified new-employment LCA positions per approved new-employment petition, for one employer and year",
     "sql": "WITH f AS (SELECT employer_id, sum(new_employment) AS lca_new_positions FROM lca WHERE employer_id = 42 AND fiscal_year = 2025 AND case_status = 'CERTIFIED' GROUP BY 1) SELECT p.employer, f.lca_new_positions, p.new_employment_approved, round(f.lca_new_positions / nullif(p.new_employment_approved, 0), 1) AS lca_positions_per_approval FROM petitions p JOIN f USING (employer_id) WHERE p.fiscal_year = 2025"},
]


def write_mappings(con, synthetic: bool, path: Path):
    tables = {}
    for table, cols in DESCRIPTIONS.items():
        columns = []
        for name, dtype, *_ in con.execute(f"DESCRIBE {table}").fetchall():
            col = {"name": name, "type": dtype, "description": cols.get(name, "")}
            if dtype in ("VARCHAR", "INTEGER") and name not in {"case_number", "job_title", "title_norm", "employer",
                                                                "employer_name_raw", "worksite_city_raw", "worksite_zip",
                                                                "soc_title", "metro_name", "area_code", "naics_code", "name_variants"}:
                distinct = con.execute(f"SELECT count(DISTINCT {name}) FROM {table}").fetchone()[0]
                if distinct <= 60:
                    col["enum_values"] = [v for (v,) in con.execute(
                        f"SELECT DISTINCT {name} FROM {table} WHERE {name} IS NOT NULL ORDER BY 1").fetchall()]
            columns.append(col)
        tables[table] = {"description": cols["_table"], "columns": columns}

    stats = dict(zip(["rows", "employers", "min_fy", "max_fy"], con.execute(
        "SELECT count(*), count(DISTINCT employer_id), min(fiscal_year), max(fiscal_year) FROM lca").fetchone()))
    max_q = con.execute(f"SELECT max(quarter) FROM lca WHERE fiscal_year = {stats['max_fy']}").fetchone()[0]
    stats["petition_rows"], stats["petition_approvals"] = con.execute(
        "SELECT count(*), coalesce(sum(approved), 0) FROM petitions").fetchone()
    mappings = {
        "synthetic": synthetic,
        "as_of": f"FY{stats['max_fy']} Q{max_q}",
        "stats": stats,
        "tables": tables,
        "glossary": GLOSSARY,
        "join_hints": JOIN_HINTS,
        "limitations": LIMITATIONS,
        "example_queries": EXAMPLE_QUERIES,
    }
    path.write_text(json.dumps(mappings, indent=2, default=str))
    log(f"wrote {path.name}")
    return stats


def write_report(con, stats, synthetic):
    q = lambda sql: con.execute(sql).fetchone()[0]  # noqa: E731
    certified = q("SELECT count(*) FROM lca WHERE case_status = 'CERTIFIED'")
    pct = lambda cond: 100.0 * q(f"SELECT count(*) FROM lca WHERE case_status = 'CERTIFIED' AND {cond}") / max(certified, 1)  # noqa: E731
    by_fy = con.execute("""SELECT fiscal_year, count(*) AS filings, count(*) FILTER (case_status = 'CERTIFIED') AS certified,
                              sum(total_worker_positions) FILTER (case_status = 'CERTIFIED') AS positions
                       FROM lca GROUP BY 1 ORDER BY 1""").fetchall()
    by_how = con.execute("""SELECT r.classified_by, count(*) FROM lca l JOIN role_titles r
                        ON r.job_title IS NOT DISTINCT FROM l.job_title AND r.soc_code IS NOT DISTINCT FROM l.soc_code
                        GROUP BY 1 ORDER BY 2 DESC""").fetchall()
    wage_ok = pct("wage_flag = 'ok'")
    role_ok = pct("role_family <> 'Other'")
    lines = [
        "# Build report", "",
        f"Generated {time.strftime('%Y-%m-%d %H:%M')} by `uv run build.py`." + (" **SYNTHETIC DATA: dev only.**" if synthetic else ""), "",
        "| Fiscal year | Filings | Certified | Certified positions |", "| --- | --- | --- | --- |",
        *[f"| FY{fy} | {a:,} | {b:,} | {c or 0:,} |" for fy, a, b, c in by_fy], "",
        "| Coverage (certified rows) | Value | Target |", "| --- | --- | --- |",
        f"| wage_flag = 'ok' | {wage_ok:.2f}% | >= 99.5% |",
        f"| has employer_id | {pct('employer_id IS NOT NULL'):.2f}% | >= 95% |",
        f"| role_family not 'Other' | {role_ok:.2f}% | >= 95% |",
        f"| has area_code | {pct('area_code IS NOT NULL'):.2f}% | >= 97% |",
        f"| has offer_wage_level | {pct('offer_wage_level IS NOT NULL'):.2f}% | >= 90% |", "",
        f"Employers after resolution: {stats['employers']:,}.", "",
        "Role families assigned by: " + ", ".join(f"{h} {n:,}" for h, n in by_how), "",
    ]
    pet = con.execute("""SELECT fiscal_year, count(*), sum(approved), sum(denied), sum(new_employment_approved),
                            100.0 * sum(approved) FILTER (in_lca) / nullif(sum(approved), 0),
                            100.0 * count(*) FILTER (in_lca) / count(*)
                     FROM petitions GROUP BY 1 ORDER BY 1""").fetchall()
    if pet:
        lines += [
            "## USCIS petitions (H-1B Employer Data Hub)", "",
            "| Fiscal year | Employers | Approved | Denied | New-employment approved | Approvals matched to an LCA employer | Employers matched |",
            "| --- | --- | --- | --- | --- | --- | --- |",
            *[f"| FY{fy} | {n:,} | {a:,} | {d:,} | {new:,} | {m:.1f}% | {em:.1f}% |" for fy, n, a, d, new, m, em in pet], "",
        ]
    DOCS.mkdir(exist_ok=True)
    (DOCS / "build_report.md").write_text("\n".join(lines))
    print("\n".join(lines))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--llm", action="store_true", help="label leftover titles with Gemini (needs gcloud ADC)")
    args = parser.parse_args()

    DATA.mkdir(exist_ok=True)
    con = duckdb.connect()  # in-memory workspace; outputs are ATTACHed files
    con.execute("SET preserve_insertion_order = false")
    synthetic = load_lca(con)
    clean_lca(con)
    annualize(con)
    resolve_employers(con)
    classify_roles(con, args.llm)
    map_locations(con)
    build_wage_levels(con)
    assemble(con)
    load_petitions(con)
    write_db(con, DATA / "h1b.duckdb", sample=False)
    write_db(con, DATA / "h1b_sample.duckdb", sample=True)
    write_baseline(con, DATA / "baseline.duckdb")
    stats = write_mappings(con, synthetic, DATA / "mappings.json")
    write_report(con, stats, synthetic)


if __name__ == "__main__":
    main()
