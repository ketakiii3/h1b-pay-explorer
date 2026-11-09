loaded h1b.duckdb: 1,532,089 filings, 107,638 employers
15:50:55 - LiteLLM:WARNING: vertex_and_google_ai_studio_gemini.py:1265 - DeprecationWarning: `temperature`, `top_p`, and `top_k` continue to function for Gemini 3+ (gemini-3.5-flash) but are planned for removal in a future release. Move sampling guidance into the `system` instructions instead.
run 1: {'plain_ok': True, 'agent_ok': True}
run 2: {'plain_ok': False, 'agent_ok': True}
run 3: {'plain_ok': False, 'agent_ok': True}

### Top 5 employers by certified machine learning engineer positions in the New York City area in FY2025.

**Expected:** ['Bloomberg', 'Yahoo Holdings', 'Meta', 'JPMorgan Chase', 'Pinterest'] (gold SQL on `lca`).

Plain agent right in 1/3 runs; H-1B Analyst right in 3/3 runs.

**No tools:** Because Fiscal Year 2025 (which runs from October 1, 2024, to September 30, 2025) is currently ongoing, complete and finalized data for the entire fiscal year is not yet available. Additionally, my knowledge cutoff is January 2025, meaning I cannot provide real-time updates or post-January 2025 statistics.

However, in the context of fiscal year data, **"certified positions"** typically refers to **H-1B Labor Condition Applications (LCAs)** approved by the U.S. Department of Labor (DOL) for foreign workers, which is the most reliable metric for tracking specific engineering roles by employer a

<details><summary>Plain run_sql agent: 15 tool calls</summary>

**run_sql** `{"query": "PRAGMA table_info(lca);"}`
```
{"columns": ["cid", "name", "type", "notnull", "dflt_value", "pk"], "rows": [[0, "case_number", "VARCHAR", false, null, false], [1, "case_status", "VARCHAR", false, null, false], [2, "received_date", "VARCHAR", false, null, false], [3, "decision_date", "VARCHAR", false, null, false], [4, "visa_class", "VARCHAR", false, null, false], [5, "job_title", "VARCHAR", false, null, false], [6, "soc_code", "VARCHAR", false, null, false], [7, "soc_title", "VARCHAR", false, null, false], [8, "full_time", "VARCHAR", false, null, false], [9, "begin_date", "VARCHAR", false, null, false], [10, "total_worker_positions", "VARCHAR", false, null, false], [11, "new_employment", "VARCHAR", false, null, false], [12, "continued_employment", "VARCHAR", false, null, false], [13, "change_previous_employment", "VARCHAR", false, null, false], [14, "new_concurrent_employment", "VARCHAR", false, null, false], [15, "ch
```

**run_sql** `{"query": "SELECT distinct source_file FROM lca;"}`
```
{"columns": ["source_file"], "rows": [["LCA_Disclosure_Data_FY2025_Q1.xlsx"], ["LCA_Disclosure_Data_FY2024_Q1.xlsx"], ["LCA_Disclosure_Data_FY2024_Q3.xlsx"], ["LCA_Disclosure_Data_FY2025_Q2.xlsx"], ["LCA_Disclosure_Data_FY2024_Q4.xlsx"], ["LCA_Disclosure_Data_FY2025_Q4.xlsx"], ["LCA_Disclosure_Data_FY2026_Q3.xlsx"], ["LCA_Disclosure_Data_FY2025_Q3.xlsx"], ["LCA_Disclosure_Data_FY2024_Q2.xlsx"]], "truncated": false}
```

**run_sql** `{"query": "SELECT case_status, COUNT(*) FROM lca GROUP BY 1;"}`
```
{"columns": ["case_status", "count_star()"], "rows": [["Certified - Withdrawn", 87320], ["Withdrawn", 25043], ["Certified", 1433993], ["Denied", 9674]], "truncated": false}
```

**run_sql** `{"query": "SELECT count(*), sum(try_cast(total_worker_positions as integer)) FROM lca WHERE total_worker_positions IS NOT NULL;"}`
```
{"columns": ["count_star()", "sum(TRY_CAST(total_worker_positions AS INTEGER))"], "rows": [[1556030, 2604529]], "truncated": false}
```

**run_sql** `{"query": "SELECT job_title, count(*) FROM lca WHERE job_title ILIKE '%machine learning engineer%' GROUP BY 1 ORDER BY 2 DESC LIMIT 15;"}`
```
{"columns": ["job_title", "count_star()"], "rows": [["Machine Learning Engineer", 2549], ["Senior Machine Learning Engineer", 855], ["Machine Learning Engineer II", 286], ["Staff Machine Learning Engineer", 277], ["Sr. Machine Learning Engineer", 202], ["Principal Machine Learning Engineer", 88], ["Machine Learning Engineer (4)", 86], ["MACHINE LEARNING ENGINEER", 80], ["Sr Machine Learning Engineer", 71], ["Machine Learning Engineer (5)", 68], ["Machine Learning Engineer I", 60], ["Lead Machine Learning Engineer", 57], ["Machine Learning Engineer ", 48], ["Senior Staff Machine Learning Engineer", 45], ["Machine Learning Engineer III", 32]], "truncated": false}
```

**run_sql** `{"query": "SELECT worksite_city, worksite_state, count(*)\nFROM lca\nWHERE worksite_state = 'NY'\nGROUP BY 1, 2\nORDER BY 3 DESC\nLIMIT 15;"}`
```
{"columns": ["worksite_city", "worksite_state", "count_star()"], "rows": [["New York", "NY", 81352], ["NEW YORK", "NY", 4903], ["Brooklyn", "NY", 4535], ["Bronx", "NY", 1965], ["Albany", "NY", 1704], ["Rochester", "NY", 1665], ["Buffalo", "NY", 1639], ["Long Island City", "NY", 1500], ["New York City", "NY", 831], ["Syracuse", "NY", 768], ["Flushing", "NY", 716], ["Ithaca", "NY", 677], ["New York ", "NY", 564], ["Upton", "NY", 533], ["Tarrytown", "NY", 513]], "truncated": false}
```

**run_sql** `{"query": "SELECT worksite_city, count(*), sum(try_cast(total_worker_positions as integer))\nFROM lca\nWHERE source_file LIKE '%FY2025%'\n  AND case_status = 'Certified'\n  AND job_title ILIKE '%machine learning engineer%'\n  AND worksite_state = 'NY'\nGROUP BY 1\nORDER BY 2 DESC;"}`
```
{"columns": ["worksite_city", "count_star()", "sum(TRY_CAST(total_worker_positions AS INTEGER))"], "rows": [["New York", 160, 343], ["Brooklyn", 13, 15], ["Long Island City", 4, 4], ["New York City", 4, 4], ["Queens", 2, 2], ["Rochester", 2, 2], ["NEW YORK", 2, 2], ["Buffalo", 1, 1], ["Uniondale", 1, 1], ["Yonkers", 1, 1], ["Fairport", 1, 1], ["Amherst", 1, 1], ["New YorK", 1, 1]], "truncated": false}
```

**run_sql** `{"query": "SELECT employer_name, count(*), sum(try_cast(total_worker_positions as integer)) as positions\nFROM lca\nWHERE source_file LIKE '%FY2025%'\n  AND case_status = 'Certified'\n  AND job_title ILIKE '%machine learning engineer%'\n  AND worksite_state = 'NY'\n  AND (worksite_city ILIKE 'New York%' OR worksite_city ILIKE 'New YorK%')\nGROUP BY 1\nORDER BY positions DESC\nLIMIT 15;"}`
```
{"columns": ["employer_name", "count_star()", "positions"], "rows": [["Bloomberg L.P.", 19, 173], ["Yahoo Holdings Inc.", 2, 31], ["Pinterest, Inc.", 14, 14], ["SNAP INC.", 11, 11], ["SPOTIFY USA, INC.", 11, 11], ["Meta Platforms, Inc", 10, 10], ["Reddit, Inc. ", 5, 5], ["Aetna Resources LLC", 4, 4], ["Kensho Technologies LLC", 4, 4], ["Peloton Interactive, Inc.", 3, 3], ["Populus Group LLC", 3, 3], ["Stripe, Inc.", 3, 3], ["PATREON, INC.", 3, 3], ["Apple Inc.", 3, 3], ["Harbor AI Inc.", 2, 2]], "truncated": false}
```

**run_sql** `{"query": "SELECT employer_name, count(*), sum(try_cast(total_worker_positions as integer)) as positions\nFROM lca\nWHERE source_file LIKE '%FY2025%'\n  AND case_status = 'Certified'\n  AND job_title ILIKE '%machine learning engineer%'\n  AND worksite_state = 'NY'\n  AND (\n    worksite_city ILIKE 'New York%' \n    OR worksite_city ILIKE 'New YorK%'\n    OR worksite_city ILIKE 'Brooklyn%'\n    OR worksite_city ILIKE 'Bronx%'\n    OR worksite_city ILIKE 'Queens%'\n    OR worksite_city ILIKE 'Long Island City%'\n    OR worksite_city ILIKE 'Flushing%'\n    OR worksite_city ILIKE 'Staten Island%'\`
```
{"columns": ["employer_name", "count_star()", "positions"], "rows": [["Bloomberg L.P.", 19, 173], ["Yahoo Holdings Inc.", 2, 31], ["Pinterest, Inc.", 14, 14], ["SNAP INC.", 11, 11], ["SPOTIFY USA, INC.", 11, 11], ["Meta Platforms, Inc", 10, 10], ["Reddit, Inc. ", 5, 5], ["Kensho Technologies LLC", 4, 4], ["Aetna Resources LLC", 4, 4], ["Etsy, Inc.", 4, 4], ["Populus Group LLC", 3, 3], ["CSC Holdings, LLC", 3, 3], ["Coinbase, Inc.", 3, 3], ["Apple Inc.", 3, 3], ["Peloton Interactive, Inc.", 3, 3]], "truncated": false}
```

**run_sql** `{"query": "SELECT soc_code, soc_title, count(*)\nFROM lca\nWHERE source_file LIKE '%FY2025%'\n  AND case_status = 'Certified'\n  AND job_title ILIKE '%machine learning engineer%'\n  AND worksite_state = 'NY'\nGROUP BY 1, 2\nORDER BY 3 DESC;"}`
```
{"columns": ["soc_code", "soc_title", "count_star()"], "rows": [["15-1252.00", "Software Developers", 118], ["15-2051.00", "Data Scientists", 54], ["15-1221.00", "Computer and Information Research Scientists", 13], ["15-2041.00", "Statisticians", 2], ["15-2031.00", "Operations Research Analysts", 1], ["11-9041.00", "Architectural and Engineering Managers", 1], ["11-3021.00", "Computer and Information Systems Managers", 1], ["15-2051.01", "Business Intelligence Analysts", 1], ["17-2031.00", "Bioengineers and Biomedical Engineers", 1], ["15-1299.08", "Computer Systems Engineers/Architects", 1]], "truncated": false}
```

**run_sql** `{"query": "SELECT job_title, count(*)\nFROM lca\nWHERE source_file LIKE '%FY2025%'\n  AND case_status = 'Certified'\n  AND job_title ILIKE '%machine learning%'\n  AND worksite_state = 'NY'\nGROUP BY 1\nORDER BY 2 DESC\nLIMIT 20;"}`
```
{"columns": ["job_title", "count_star()"], "rows": [["Machine Learning Engineer", 95], ["Senior Machine Learning Engineer", 20], ["Software Engineer, Machine Learning", 16], ["Machine Learning Engineer II", 11], ["Staff Machine Learning Engineer", 7], ["Machine Learning Research", 7], ["Sr. Machine Learning Engineer", 6], ["Machine Learning Engineer (4)", 5], ["Machine Learning Team Leader", 5], ["Machine Learning", 5], ["Senior Applied Machine Learning Engineer", 4], ["Machine Learning Software Engineer", 4], ["Machine Learning Engineer (3)", 3], ["Sr Machine Learning Engineer", 3], ["Sr. Software Engineer, Machine Learning", 3], ["Machine Learning Infrastructure Engineer", 2], ["Machine Learning Engineer II, Ads Recommendation", 2], ["Machine Learning Data Scientist", 2], ["Senior Software Engineer, Machine Learning", 2], ["Machine Learning Engineer I", 2]], "truncated": false}
```

**run_sql** `{"query": "SELECT job_title, count(*)\nFROM lca\nWHERE source_file LIKE '%FY2025%'\n  AND case_status = 'Certified'\n  AND job_title ILIKE '%ML%'\n  AND worksite_state = 'NY'\nGROUP BY 1\nORDER BY 2 DESC\nLIMIT 15;"}`
```
{"columns": ["job_title", "count_star()"], "rows": [["AI/ML Engineer", 7], ["Vice President, Applied AI ML Lead", 5], ["Associate, Applied AI ML Associate Sr", 4], ["Enterprise ML/AI Technical Sales", 2], ["ML Data Associate III", 1], ["Senior ML Engineer", 1], ["Sr. Scientist / Engineer I, RFML", 1], ["Data Scientist, ML/AI", 1], ["Senior AI/ML Data Engineer", 1], ["AI/ML Developer", 1], ["BSA/AML & Sanctions Systems Analyst Sr. (AML/OFAC Systems)", 1], ["Associate, Applied AI ML Lead", 1], ["Founding Robotics ML Engineer", 1], ["Executive Director, Applied AI ML Director", 1], ["STAFF ML ENGINEER", 1]], "truncated": false}
```

**run_sql** `{"query": "SELECT employer_name, count(*), sum(try_cast(total_worker_positions as integer)) as positions\nFROM lca\nWHERE source_file LIKE '%FY2025%'\n  AND case_status = 'Certified'\n  AND (\n    job_title ILIKE '%machine learning%engineer%'\n    OR job_title ILIKE '%ml%engineer%'\n  )\n  AND worksite_state = 'NY'\n  AND (\n    worksite_city ILIKE 'New York%' \n    OR worksite_city ILIKE 'New YorK%'\n    OR worksite_city ILIKE 'Brooklyn%'\n    OR worksite_city ILIKE 'Bronx%'\n    OR worksite_city ILIKE 'Queens%'\n    OR worksite_city ILIKE 'Long Island City%'\n    OR worksite_city ILIKE 'Flus`
```
{"columns": ["employer_name", "count_star()", "positions"], "rows": [["Bloomberg L.P.", 19, 173], ["Yahoo Holdings Inc.", 2, 31], ["Pinterest, Inc.", 14, 14], ["Meta Platforms, Inc", 13, 13], ["SPOTIFY USA, INC.", 11, 11], ["SNAP INC.", 11, 11], ["Reddit, Inc. ", 5, 5], ["Aetna Resources LLC", 4, 4], ["Etsy, Inc.", 4, 4], ["Kensho Technologies LLC", 4, 4], ["Hinge, Inc.", 4, 4], ["Populus Group LLC", 4, 4], ["Peloton Interactive, Inc.", 3, 3], ["VIAI LLC", 1, 3], ["CSC Holdings, LLC", 3, 3]], "truncated": false}
```

**run_sql** `{"query": "SELECT employer_name, job_title, total_worker_positions, worksite_city\nFROM lca\nWHERE source_file LIKE '%FY2025%'\n  AND case_status = 'Certified'\n  AND (\n    job_title ILIKE '%machine learning%engineer%'\n    OR job_title ILIKE '%ml%engineer%'\n  )\n  AND worksite_state = 'NY'\n  AND (\n    worksite_city ILIKE 'New York%' \n    OR worksite_city ILIKE 'New YorK%'\n  )\n  AND employer_name IN ('Bloomberg L.P.', 'Yahoo Holdings Inc.')\nORDER BY employer_name, total_worker_positions DESC;"}`
```
{"columns": ["employer_name", "job_title", "total_worker_positions", "worksite_city"], "rows": [["Bloomberg L.P.", "Machine Learning Engineer", "15", "New York"], ["Bloomberg L.P.", "Machine Learning Engineer", "15", "New York"], ["Bloomberg L.P.", "Machine Learning Engineer", "15", "New York"], ["Bloomberg L.P.", "Machine Learning Engineer", "15", "New York"], ["Bloomberg L.P.", "Machine Learning Engineer", "15", "New York"], ["Bloomberg L.P.", "Machine Learning Engineer", "15", "New York"], ["Bloomberg L.P.", "Machine Learning Engineer", "15", "New York"], ["Bloomberg L.P.", "Machine Learning Engineer", "15", "New York"], ["Bloomberg L.P.", "Machine Learning Engineer", "15", "New York"], ["Bloomberg L.P.", "Machine Learning Engineer", "15", "New York"], ["Bloomberg L.P.", "Machine Learning Engineer", "15", "New York"], ["Bloomberg L.P.", "Machine Learning Engineer", "1", "New York"], [
```

**run_sql** `{"query": "SELECT worksite_city, count(*), sum(try_cast(total_worker_positions as integer)) as positions\nFROM lca\nWHERE source_file LIKE '%FY2025%'\n  AND case_status = 'Certified'\n  AND job_title ILIKE '%machine learning engineer%'\n  AND worksite_state = 'NY'\nGROUP BY 1\nORDER BY positions DESC;"}`
```
{"columns": ["worksite_city", "count_star()", "positions"], "rows": [["New York", 160, 343], ["Brooklyn", 13, 15], ["Long Island City", 4, 4], ["New York City", 4, 4], ["Rochester", 2, 2], ["NEW YORK", 2, 2], ["Queens", 2, 2], ["Uniondale", 1, 1], ["Buffalo", 1, 1], ["New YorK", 1, 1], ["Yonkers", 1, 1], ["Fairport", 1, 1], ["Amherst", 1, 1]], "truncated": false}
```

**Answer:** FAILED: MaxTurnsExceeded: Max turns (15) exceeded

</details>

<details><summary>H-1B Analyst: 5 tool calls</summary>

**read_mappings** `{}`
```
{"as_of": "FY2026 Q3", "tables": {"lca": {"description": "One row per H-1B Labor Condition Application (LCA) filed with the Department of Labor, FY2024 Q1 to FY2026 Q3, amendments deduplicated. An LCA is a filing an employer must make BEFORE an H-1B petition; it is not an approval or a visa.", "columns": [{"name": "case_number", "type": "VARCHAR", "description": "DOL case number, unique per row."}, {"name": "case_status", "type": "VARCHAR", "description": "DOL decision. Use 'CERTIFIED' for filings employers could actually use.", "is_enum": true}, {"name": "fiscal_year", "type": "INTEGER", "description": "US federal fiscal year of the decision (Oct 1 - Sep 30). FY2026 = Oct 2025 - Sep 2026.", "is_enum": true}, {"name": "quarter", "type": "INTEGER", "description": "Fiscal quarter 1-4 (Q1 = Oct-Dec).", "is_enum": true}, {"name": "received_date", "type": "DATE", "description": "Date DOL rece
```

**find_location** `{"place": "New York City area"}`
```
{"area_code": "35620", "metro_name": "New York-Newark-Jersey City, NY-NJ", "matched_by": "worksite city 'New York City, NY'"}
```

**find_role** `{"text": "machine learning engineer"}`
```
{"role_family": "Machine Learning Engineer", "matched_by": "rules", "main_soc_codes": [{"soc_code": "15-1252", "soc_title": "Software Developers", "filings": 5337}, {"soc_code": "15-2051", "soc_title": "Data Scientists", "filings": 3017}, {"soc_code": "15-1221", "soc_title": "Computer and Information Research Scientists", "filings": 607}], "example_titles": ["machine learning engineer", "senior machine learning engineer", "artificial intelligence engineer", "software engineer machine learning", "staff machine learning engineer", "machine learning engineer ii"]}
```

**run_sql** `{"query": "SELECT employer, sum(total_worker_positions) AS positions, count(*) AS filings, median(wage_annual_from) FILTER (WHERE wage_flag = 'ok') AS median_pay FROM lca WHERE area_code = '35620' AND role_family = 'Machine Learning Engineer' AND fiscal_year = 2025 AND case_status = 'CERTIFIED' GROUP BY employer ORDER BY positions DESC LIMIT 5"}`
```
{"columns": ["employer", "positions", "filings", "median_pay"], "rows": [["Bloomberg", 173, 19, 151819.0], ["Yahoo Holdings", 31, 2, 118674.5], ["Meta", 27, 27, 218402.0], ["JPMorgan Chase", 24, 24, 177500.0], ["Pinterest", 14, 14, 123656.0]], "row_count": 5, "truncated": false}
```

**make_chart** `{"y": "positions", "mark": "bar", "color": null, "x": "employer", "title": "Top Employers by ML Engineer Positions, NYC Area, FY2025"}`
```
{"ok": true, "note": "Chart shown to the user. Do not describe the chart's styling."}
```

**Answer:** Bloomberg led the New York City area in FY2025 with 173 certified machine learning engineer positions.

* **Bloomberg** ranked first with 173 positions across 19 certified filings (a small sample), offering a median annual salary of $152k.
* **Yahoo Holdings** followed with 31 positions across just 2 filings (a small sample), offering a median salary of $119k.
* **Meta** and **JPMorgan Chase** sponsored 27 and 24 positions, respectively, with Meta offering a median salary of $218k across 27 filings and JPMorgan Chase offering $178k across 24 filings.
* **Pinterest** rounded out the top five with 14 positions across 14 filings (a small sample) and a median salary of $124k.

</details>

Saved traces/top-5-employers-by-certified-machine-learning-engineer-posit.json

