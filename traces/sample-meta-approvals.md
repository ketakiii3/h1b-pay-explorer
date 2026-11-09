loaded h1b.duckdb: 1,532,089 filings, 107,638 employers
16:04:34 - LiteLLM:WARNING: vertex_and_google_ai_studio_gemini.py:1265 - DeprecationWarning: `temperature`, `top_p`, and `top_k` continue to function for Gemini 3+ (gemini-3.5-flash) but are planned for removal in a future release. Move sampling guidance into the `system` instructions instead.
run 1: no gold

### How many H-1B visas did Meta get approved in 2025?

**Expected:** None (gold SQL on `lca`).

**No tools:** I do not have access to real-time databases or the live United States Citizenship and Immigration Services (USCIS) H-1B Employer Data Hub to provide the exact, finalized number of H-1B visas approved for Meta (Meta Platforms, Inc.) for the calendar year 2025 or Fiscal Year 2025. 

To find the exact and official figures, you can consult the following resources:

1. **USCIS H-1B Employer Data Hub:** USCIS regularly updates a searchable database where you can filter by fiscal year, employer name (e.g., "Meta Platforms"), and state to see the exact number of approved and denied initial and continu

<details><summary>Plain run_sql agent: 15 tool calls</summary>

**run_sql** `{"query": "DESCRIBE lca;"}`
```
{"columns": ["column_name", "column_type", "null", "key", "default", "extra"], "rows": [["case_number", "VARCHAR", "YES", null, null, null], ["case_status", "VARCHAR", "YES", null, null, null], ["received_date", "VARCHAR", "YES", null, null, null], ["decision_date", "VARCHAR", "YES", null, null, null], ["visa_class", "VARCHAR", "YES", null, null, null], ["job_title", "VARCHAR", "YES", null, null, null], ["soc_code", "VARCHAR", "YES", null, null, null], ["soc_title", "VARCHAR", "YES", null, null, null], ["full_time", "VARCHAR", "YES", null, null, null], ["begin_date", "VARCHAR", "YES", null, null, null], ["total_worker_positions", "VARCHAR", "YES", null, null, null], ["new_employment", "VARCHAR", "YES", null, null, null], ["continued_employment", "VARCHAR", "YES", null, null, null], ["change_previous_employment", "VARCHAR", "YES", null, null, null], ["new_concurrent_employment", "VARCHAR"
```

**run_sql** `{"query": "SELECT DISTINCT employer_name, count(*) \nFROM lca \nWHERE employer_name ILIKE '%Meta%' \nGROUP BY employer_name \nORDER BY count(*) DESC \nLIMIT 30;"}`
```
{"columns": ["employer_name", "count_star()"], "rows": [["Meta Platforms, Inc", 14550], ["Meta Platforms, Inc.", 1680], ["Meta Platforms, Inc. ", 462], ["META PLATFORMS, INC.", 451], ["META PLATFORMS, INC. ", 386], ["METAFORGE IT SOLUTIONS", 51], ["META IT CORP", 51], ["Metaforge IT Solutions", 49], ["Mesabi Metallics Company LLC", 42], ["SYNMETA LLC", 36], ["Metapicks LLC", 34], ["PRIMETALS TECHNOLOGIES USA LLC", 30], ["META SOFT INC", 27], ["META IT SYSTEMS LLC", 26], ["Metasoft LLC", 23], ["Metanoia Solutions, Inc.", 21], ["Boston Electrometallurgical Corporation", 21], ["Metagenomi, Inc.", 18], ["Metahorizon Inc.", 17], ["METASENSE INC.", 17], ["METASENSE, INC.", 15], ["Meta Hub IT Solutions Inc", 13], ["East Coast Metal Structures Corp", 12], ["Meta Payments Inc. (formerly known as Facebook Payments, Inc)", 10], ["METAHORIZON INC.", 10], ["METATEK SOLUTIONS LLC", 9], ["Meta Hub IT S
```

**run_sql** `{"query": "SELECT DISTINCT case_status FROM lca;"}`
```
{"columns": ["case_status"], "rows": [["Certified - Withdrawn"], ["Certified"], ["Withdrawn"], ["Denied"]], "truncated": false}
```

**run_sql** `{"query": "SELECT decision_date, COUNT(*) FROM lca GROUP BY decision_date LIMIT 10;"}`
```
{"columns": ["decision_date", "count_star()"], "rows": [["45567", 1797], ["45889", 1782], ["45885", 2], ["45870", 1664], ["45863", 1759], ["45857", 4], ["45844", 5], ["45843", 2], ["45842", 17], ["45667", 1445]], "truncated": false}
```

**run_sql** `{"query": "SELECT DATE '1899-12-30' + INTERVAL (45567) DAY, DATE '1899-12-30' + INTERVAL (45889) DAY;"}`
```
{"columns": ["(CAST('1899-12-30' AS DATE) + to_days(CAST(trunc(CAST(45567 AS DOUBLE)) AS INTEGER)))", "(CAST('1899-12-30' AS DATE) + to_days(CAST(trunc(CAST(45889 AS DOUBLE)) AS INTEGER)))"], "rows": [["2024-10-02 00:00:00", "2025-08-20 00:00:00"]], "truncated": false}
```

**run_sql** `{"query": "SELECT \n    MIN(DATE '1899-12-30' + INTERVAL (TRY_CAST(decision_date AS INTEGER)) DAY) AS min_decision_date,\n    MAX(DATE '1899-12-30' + INTERVAL (TRY_CAST(decision_date AS INTEGER)) DAY) AS max_decision_date,\n    MIN(DATE '1899-12-30' + INTERVAL (TRY_CAST(begin_date AS INTEGER)) DAY) AS min_begin_date,\n    MAX(DATE '1899-12-30' + INTERVAL (TRY_CAST(begin_date AS INTEGER)) DAY) AS max_begin_date\nFROM lca;"}`
```
{"columns": ["min_decision_date", "max_decision_date", "min_begin_date", "max_begin_date"], "rows": [["2023-10-02 00:00:00", "2026-06-30 00:00:00", "2019-10-15 00:00:00", "2026-12-30 00:00:00"]], "truncated": false}
```

**run_sql** `{"query": "SELECT \n    EXTRACT(YEAR FROM (DATE '1899-12-30' + INTERVAL (TRY_CAST(decision_date AS INTEGER)) DAY)) AS decision_year,\n    case_status,\n    COUNT(*) AS case_count,\n    SUM(TRY_CAST(total_worker_positions AS INTEGER)) AS total_workers\nFROM lca\nWHERE employer_name ILIKE '%Meta Platforms%'\nGROUP BY decision_year, case_status\nORDER BY decision_year, case_status;"}`
```
{"columns": ["decision_year", "case_status", "case_count", "total_workers"], "rows": [[2023, "Certified", 999, 999], [2023, "Certified - Withdrawn", 4, 4], [2023, "Denied", 2, 2], [2023, "Withdrawn", 7, 7], [2024, "Certified", 6360, 6720], [2024, "Certified - Withdrawn", 186, 186], [2024, "Denied", 13, 13], [2024, "Withdrawn", 9, 9], [2025, "Certified", 5613, 7992], [2025, "Withdrawn", 1, 1], [2026, "Certified", 4335, 12567]], "truncated": false}
```

**run_sql** `{"query": "SELECT DISTINCT decision_date, DATE '1899-12-30' + INTERVAL (TRY_CAST(decision_date AS INTEGER)) DAY AS dec_date\nFROM lca\nWHERE employer_name ILIKE '%Meta Platforms%' AND EXTRACT(YEAR FROM (DATE '1899-12-30' + INTERVAL (TRY_CAST(decision_date AS INTEGER)) DAY)) IN (2025, 2026)\nORDER BY decision_date LIMIT 20;"}`
```
{"columns": ["decision_date", "dec_date"], "rows": [["45659", "2025-01-02 00:00:00"], ["45660", "2025-01-03 00:00:00"], ["45663", "2025-01-06 00:00:00"], ["45664", "2025-01-07 00:00:00"], ["45665", "2025-01-08 00:00:00"], ["45667", "2025-01-10 00:00:00"], ["45671", "2025-01-14 00:00:00"], ["45672", "2025-01-15 00:00:00"], ["45673", "2025-01-16 00:00:00"], ["45674", "2025-01-17 00:00:00"], ["45678", "2025-01-21 00:00:00"], ["45679", "2025-01-22 00:00:00"], ["45680", "2025-01-23 00:00:00"], ["45681", "2025-01-24 00:00:00"], ["45684", "2025-01-27 00:00:00"], ["45685", "2025-01-28 00:00:00"], ["45686", "2025-01-29 00:00:00"], ["45687", "2025-01-30 00:00:00"], ["45688", "2025-01-31 00:00:00"], ["45691", "2025-02-03 00:00:00"]], "truncated": false}
```

**run_sql** `{"query": "SELECT DISTINCT decision_date, DATE '1899-12-30' + INTERVAL (TRY_CAST(decision_date AS INTEGER)) DAY AS dec_date\nFROM lca\nWHERE employer_name ILIKE '%Meta Platforms%' AND EXTRACT(YEAR FROM (DATE '1899-12-30' + INTERVAL (TRY_CAST(decision_date AS INTEGER)) DAY)) = 2026\nORDER BY decision_date LIMIT 20;"}`
```
{"columns": ["decision_date", "dec_date"], "rows": [["46024", "2026-01-02 00:00:00"], ["46027", "2026-01-05 00:00:00"], ["46028", "2026-01-06 00:00:00"], ["46029", "2026-01-07 00:00:00"], ["46030", "2026-01-08 00:00:00"], ["46031", "2026-01-09 00:00:00"], ["46034", "2026-01-12 00:00:00"], ["46035", "2026-01-13 00:00:00"], ["46036", "2026-01-14 00:00:00"], ["46037", "2026-01-15 00:00:00"], ["46038", "2026-01-16 00:00:00"], ["46042", "2026-01-20 00:00:00"], ["46043", "2026-01-21 00:00:00"], ["46044", "2026-01-22 00:00:00"], ["46045", "2026-01-23 00:00:00"], ["46048", "2026-01-26 00:00:00"], ["46049", "2026-01-27 00:00:00"], ["46050", "2026-01-28 00:00:00"], ["46051", "2026-01-29 00:00:00"], ["46052", "2026-01-30 00:00:00"]], "truncated": false}
```

**run_sql** `{"query": "SELECT source_file, COUNT(*) FROM lca GROUP BY source_file;"}`
```
{"columns": ["source_file", "count_star()"], "rows": [["LCA_Disclosure_Data_FY2024_Q4.xlsx", 117339], ["LCA_Disclosure_Data_FY2025_Q3.xlsx", 234726], ["LCA_Disclosure_Data_FY2025_Q2.xlsx", 128673], ["LCA_Disclosure_Data_FY2026_Q3.xlsx", 426952], ["LCA_Disclosure_Data_FY2025_Q1.xlsx", 104046], ["LCA_Disclosure_Data_FY2024_Q3.xlsx", 212766], ["LCA_Disclosure_Data_FY2024_Q1.xlsx", 96294], ["LCA_Disclosure_Data_FY2024_Q2.xlsx", 120408], ["LCA_Disclosure_Data_FY2025_Q4.xlsx", 114826]], "truncated": false}
```

**run_sql** `{"query": "SELECT CURRENT_DATE;"}`
```
{"columns": ["CURRENT_DATE"], "rows": [["2026-11-09"]], "truncated": false}
```

**run_sql** `{"query": "SELECT \n    employer_name,\n    case_status,\n    COUNT(*) as case_count,\n    SUM(TRY_CAST(total_worker_positions AS INTEGER)) as total_workers\nFROM lca\nWHERE employer_name ILIKE 'Meta Platforms%'\n  AND EXTRACT(YEAR FROM (DATE '1899-12-30' + INTERVAL (TRY_CAST(decision_date AS INTEGER)) DAY)) = 2025\nGROUP BY employer_name, case_status;"}`
```
{"columns": ["employer_name", "case_status", "case_count", "total_workers"], "rows": [["Meta Platforms, Inc.", "Certified", 17, 425], ["Meta Platforms, Inc", "Withdrawn", 1, 1], ["Meta Platforms, Inc", "Certified", 5596, 7567]], "truncated": false}
```

**run_sql** `{"query": "SELECT \n    employer_name,\n    case_status,\n    COUNT(*) as case_count,\n    SUM(TRY_CAST(total_worker_positions AS INTEGER)) as total_workers\nFROM lca\nWHERE employer_name ILIKE '%Meta%'\n  AND EXTRACT(YEAR FROM (DATE '1899-12-30' + INTERVAL (TRY_CAST(decision_date AS INTEGER)) DAY)) = 2025\nGROUP BY employer_name, case_status\nORDER BY total_workers DESC;"}`
```
{"columns": ["employer_name", "case_status", "case_count", "total_workers"], "rows": [["Meta Platforms, Inc", "Certified", 5596, 7567], ["Meta Platforms, Inc.", "Certified", 17, 425], ["Metaforge IT Solutions", "Certified", 25, 70], ["SYNMETA LLC", "Certified", 7, 19], ["METAFORGE IT SOLUTIONS", "Certified", 18, 18], ["Mesabi Metallics Company LLC", "Certified", 17, 17], ["PRIMETALS TECHNOLOGIES USA LLC", "Certified", 10, 10], ["East Coast Metal Structures Corp", "Certified", 10, 10], ["METATEK SOLUTIONS LLC", "Certified", 9, 9], ["METASENSE INC.", "Certified", 7, 7], ["Meta Payments Inc. (formerly known as Facebook Payments, Inc)", "Certified", 7, 7], ["Metanoia Solutions, Inc.", "Certified", 7, 7], ["Metagenomi, Inc.", "Certified", 6, 6], ["Metagenomi, Inc.", "Certified - Withdrawn", 6, 6], ["Meta Hub IT Solutions Inc.", "Certified", 6, 6], ["Metahorizon Inc.", "Certified", 6, 6], ["ME
```

**run_sql** `{"query": "SELECT DISTINCT employer_name FROM lca WHERE employer_name ILIKE '%META PLATFORMS%';"}`
```
{"columns": ["employer_name"], "rows": [["META PLATFORMS, INC."], ["Meta Platforms, Inc"], ["Meta Platforms, Inc."], ["META PLATFORMS, INC. "], ["Meta Platforms, Inc. "]], "truncated": false}
```

**run_sql** `{"query": "SELECT \n    employer_name,\n    case_status,\n    COUNT(*) as case_count,\n    SUM(TRY_CAST(total_worker_positions AS INTEGER)) as total_workers\nFROM lca\nWHERE employer_name ILIKE 'Meta Platforms%'\n  AND EXTRACT(YEAR FROM (DATE '1899-12-30' + INTERVAL (TRY_CAST(decision_date AS INTEGER)) DAY)) = 2025\nGROUP BY employer_name, case_status;"}`
```
{"columns": ["employer_name", "case_status", "case_count", "total_workers"], "rows": [["Meta Platforms, Inc.", "Certified", 17, 425], ["Meta Platforms, Inc", "Withdrawn", 1, 1], ["Meta Platforms, Inc", "Certified", 5596, 7567]], "truncated": false}
```

**Answer:** FAILED: MaxTurnsExceeded: Max turns (15) exceeded

</details>

<details><summary>H-1B Analyst: 1 tool calls</summary>

**read_mappings** `{}`
```
{"as_of": "FY2026 Q3", "tables": {"lca": {"description": "One row per H-1B Labor Condition Application (LCA) filed with the Department of Labor, FY2024 Q1 to FY2026 Q3, amendments deduplicated. An LCA is a filing an employer must make BEFORE an H-1B petition; it is not an approval or a visa.", "columns": [{"name": "case_number", "type": "VARCHAR", "description": "DOL case number, unique per row."}, {"name": "case_status", "type": "VARCHAR", "description": "DOL decision. Use 'CERTIFIED' for filings employers could actually use.", "is_enum": true}, {"name": "fiscal_year", "type": "INTEGER", "description": "US federal fiscal year of the decision (Oct 1 - Sep 30). FY2026 = Oct 2025 - Sep 2026.", "is_enum": true}, {"name": "quarter", "type": "INTEGER", "description": "Fiscal quarter 1-4 (Q1 = Oct-Dec).", "is_enum": true}, {"name": "received_date", "type": "DATE", "description": "Date DOL rece
```

**Answer:** I cannot show how many actual H-1B visas Meta got approved in 2025 because this database contains Department of Labor Labor Condition Applications (LCAs) filed before the petition stage, not USCIS visa approvals. However, I can tell you how many LCAs Meta had certified in fiscal year 2025.

</details>

Saved traces/how-many-h-1b-visas-did-meta-get-approved-in-2025.json

