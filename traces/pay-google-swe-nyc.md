loaded h1b.duckdb: 1,532,089 filings, 107,638 employers
15:46:38 - LiteLLM:WARNING: vertex_and_google_ai_studio_gemini.py:1265 - DeprecationWarning: `temperature`, `top_p`, and `top_k` continue to function for Gemini 3+ (gemini-3.5-flash) but are planned for removal in a future release. Move sampling guidance into the `system` instructions instead.
run 1: {'plain_ok': True, 'agent_ok': True}
run 2: {'plain_ok': False, 'agent_ok': True}
run 3: {'plain_ok': True, 'agent_ok': True}

### What was the median offered salary for software engineers at Google in the New York City area in FY2025?

**Expected:** 186000.0 (gold SQL on `lca`).

Plain agent right in 2/3 runs; H-1B Analyst right in 3/3 runs.

**No tools:** Complete, official salary data for the entirety of **Fiscal Year 2025** (which runs from October 1, 2024, to September 30, 2025) is not yet fully aggregated or released by the U.S. Department of Labor (DOL). 

However, we can look at the most recent **Labor Condition Application (LCA)** filings for H-1B visas—which represent the official base salaries offered by Google to software engineers in New York City—alongside real-time crowdsourced data to provide a highly accurate picture of the current market.

### 1. Estimated Median Base Salary (Offered Salary via LCAs)
Based on late 2024 and early

<details><summary>Plain run_sql agent: 15 tool calls</summary>

**run_sql** `{"query": "DESCRIBE lca;"}`
```
{"columns": ["column_name", "column_type", "null", "key", "default", "extra"], "rows": [["case_number", "VARCHAR", "YES", null, null, null], ["case_status", "VARCHAR", "YES", null, null, null], ["received_date", "VARCHAR", "YES", null, null, null], ["decision_date", "VARCHAR", "YES", null, null, null], ["visa_class", "VARCHAR", "YES", null, null, null], ["job_title", "VARCHAR", "YES", null, null, null], ["soc_code", "VARCHAR", "YES", null, null, null], ["soc_title", "VARCHAR", "YES", null, null, null], ["full_time", "VARCHAR", "YES", null, null, null], ["begin_date", "VARCHAR", "YES", null, null, null], ["total_worker_positions", "VARCHAR", "YES", null, null, null], ["new_employment", "VARCHAR", "YES", null, null, null], ["continued_employment", "VARCHAR", "YES", null, null, null], ["change_previous_employment", "VARCHAR", "YES", null, null, null], ["new_concurrent_employment", "VARCHAR"
```

**run_sql** `{"query": "SELECT DISTINCT source_file FROM lca;"}`
```
{"columns": ["source_file"], "rows": [["LCA_Disclosure_Data_FY2024_Q2.xlsx"], ["LCA_Disclosure_Data_FY2026_Q3.xlsx"], ["LCA_Disclosure_Data_FY2025_Q2.xlsx"], ["LCA_Disclosure_Data_FY2024_Q3.xlsx"], ["LCA_Disclosure_Data_FY2025_Q1.xlsx"], ["LCA_Disclosure_Data_FY2024_Q1.xlsx"], ["LCA_Disclosure_Data_FY2025_Q3.xlsx"], ["LCA_Disclosure_Data_FY2024_Q4.xlsx"], ["LCA_Disclosure_Data_FY2025_Q4.xlsx"]], "truncated": false}
```

**run_sql** `{"query": "SELECT employer_name, count(*) as count\nFROM lca\nWHERE employer_name ILIKE '%google%'\nGROUP BY employer_name\nORDER BY count DESC;"}`
```
{"columns": ["employer_name", "count"], "rows": [["Google LLC", 25071], ["Google Public Sector LLC ", 23], ["Google Client Services LLC", 2]], "truncated": false}
```

**run_sql** `{"query": "SELECT job_title, count(*) as count\nFROM lca\nWHERE employer_name ILIKE '%Google%' AND job_title ILIKE '%software engineer%'\nGROUP BY job_title\nORDER BY count DESC\nLIMIT 50;"}`
```
{"columns": ["job_title", "count"], "rows": [["Software Engineer", 15294], ["Senior Software Engineer", 301], ["Staff Software Engineer", 143], ["Software Engineer ", 120], ["Software Engineer, Site Reliability", 113], ["Software Engineer Manager", 103], ["Software Engineering Manager", 47], ["Software Engineer, Site Reliability Engineering", 42], ["Software Engineer Site Reliability", 39], ["Software Engineer, Site Reliability Engineer", 31], ["Site Reliability Engineer - Software Engineer", 16], ["Software Engineer - Manager", 13], ["Senior Staff Software Engineer", 10], ["Software Engineering", 6], ["Software Engineering Manager, Site Reliability", 6], ["Software Engineer III", 5], ["Senior Software Engineer, Site Reliability", 4], ["GDM Software Engineer", 4], ["Site Reliability Engineer, Software Engineer", 4], [" Software Engineer", 3], ["GDM Senior Software Engineer", 3], ["Resear
```

**run_sql** `{"query": "SELECT worksite_city, worksite_state, count(*) as count\nFROM lca\nWHERE employer_name ILIKE '%Google%' AND (worksite_city ILIKE '%New York%' OR worksite_state = 'NY')\nGROUP BY worksite_city, worksite_state\nORDER BY count DESC;"}`
```
{"columns": ["worksite_city", "worksite_state", "count"], "rows": [["New York", "NY", 2666], ["Brooklyn", "NY", 4], ["New York City", "NY", 4], ["Long Island City", "NY", 2], ["Queens", "NY", 2], ["New york", "NY", 1], ["New York ", "NY", 1], ["Tonawanda", "NY", 1], ["Amherst", "NY", 1], ["NewYork", "NY", 1], ["New Yrok", "NY", 1], ["Buffalo", "NY", 1], ["Glen Oaks", "NY", 1]], "truncated": false}
```

**run_sql** `{"query": "SELECT DISTINCT TRIM(worksite_city) as city, worksite_state\nFROM lca\nWHERE employer_name ILIKE '%Google%' AND source_file LIKE '%FY2025%' AND (worksite_city ILIKE '%New York%' OR worksite_state = 'NY')\nORDER BY city;"}`
```
{"columns": ["city", "worksite_state"], "rows": [["Amherst", "NY"], ["Brooklyn", "NY"], ["Buffalo", "NY"], ["New York", "NY"], ["New York City", "NY"], ["New Yrok", "NY"], ["NewYork", "NY"], ["Queens", "NY"], ["Tonawanda", "NY"]], "truncated": false}
```

**run_sql** `{"query": "SELECT wage_from, wage_to, wage_unit, count(*) as count\nFROM lca\nWHERE employer_name ILIKE '%Google%' AND source_file LIKE '%FY2025%'\nGROUP BY wage_from, wage_to, wage_unit\nLIMIT 10;"}`
```
{"columns": ["wage_from", "wage_to", "wage_unit", "count"], "rows": [["200000", null, "Year", 107], ["154000", null, "Year", 33], ["178000", null, "Year", 22], ["195700", null, "Year", 1], ["199000", null, "Year", 29], ["170000", null, "Year", 104], ["230000", null, "Year", 62], ["195500", null, "Year", 3], ["197000", null, "Year", 44], ["201500", null, "Year", 1]], "truncated": false}
```

**run_sql** `{"query": "SELECT wage_unit, count(*) as count\nFROM lca\nWHERE employer_name ILIKE '%Google%' AND source_file LIKE '%FY2025%'\nGROUP BY wage_unit;"}`
```
{"columns": ["wage_unit", "count"], "rows": [["Week", 3], ["Month", 5], ["Hour", 13], ["Year", 8767]], "truncated": false}
```

**run_sql** `{"query": "SELECT TRIM(job_title) as job, TRIM(worksite_city) as city, wage_from, wage_unit, source_file\nFROM lca\nWHERE employer_name ILIKE '%Google%'\n  AND source_file LIKE '%FY2025%'\n  AND (TRIM(worksite_city) ILIKE '%New York%' OR TRIM(worksite_city) IN ('NewYork', 'New Yrok'))\n  AND TRIM(job_title) = 'Software Engineer';"}`
```
{"columns": ["job", "city", "wage_from", "wage_unit", "source_file"], "rows": [["Software Engineer", "New York", "190200", "Year", "LCA_Disclosure_Data_FY2025_Q1.xlsx"], ["Software Engineer", "New York", "186000", "Year", "LCA_Disclosure_Data_FY2025_Q1.xlsx"], ["Software Engineer", "New York", "191000", "Year", "LCA_Disclosure_Data_FY2025_Q1.xlsx"], ["Software Engineer", "New York", "186000", "Year", "LCA_Disclosure_Data_FY2025_Q1.xlsx"], ["Software Engineer", "New York", "157000", "Year", "LCA_Disclosure_Data_FY2025_Q1.xlsx"], ["Software Engineer", "New York", "215000", "Year", "LCA_Disclosure_Data_FY2025_Q1.xlsx"], ["Software Engineer", "New York", "187000", "Year", "LCA_Disclosure_Data_FY2025_Q1.xlsx"], ["Software Engineer", "New York", "187000", "Year", "LCA_Disclosure_Data_FY2025_Q1.xlsx"], ["Software Engineer", "New York", "186000", "Year", "LCA_Disclosure_Data_FY2025_Q1.xlsx"], ["
```

**run_sql** `{"query": "SELECT wage_unit, count(*)\nFROM lca\nWHERE employer_name ILIKE '%Google%'\n  AND source_file LIKE '%FY2025%'\n  AND (TRIM(worksite_city) ILIKE '%New York%' OR TRIM(worksite_city) IN ('NewYork', 'New Yrok'))\n  AND TRIM(job_title) = 'Software Engineer'\nGROUP BY wage_unit;"}`
```
{"columns": ["wage_unit", "count_star()"], "rows": [["Month", 1], ["Year", 435]], "truncated": false}
```

**run_sql** `{"query": "WITH normalized_wages AS (\n  SELECT\n    case_number,\n    TRIM(job_title) as job_title,\n    TRIM(worksite_city) as worksite_city,\n    worksite_state,\n    CAST(wage_from AS DOUBLE) as wage_raw,\n    wage_unit,\n    CASE\n      WHEN wage_unit = 'Year' THEN CAST(wage_from AS DOUBLE)\n      WHEN wage_unit = 'Month' THEN CAST(wage_from AS DOUBLE) * 12\n      WHEN wage_unit = 'Week' THEN CAST(wage_from AS DOUBLE) * 52\n      WHEN wage_unit = 'Hour' THEN CAST(wage_from AS DOUBLE) * 2080\n      ELSE NULL\n    END as wage_annual\n  FROM lca\n  WHERE employer_name ILIKE '%Google%'\n    A`
```
{"columns": ["job_group", "geo_group", "count", "median_salary", "avg_salary"], "rows": [["Exact Job Title (Software Engineer)", "NYC City Only", 436, 186000.0, 194482.63990825688], ["Exact Job Title (Software Engineer)", "Other NY", 3, 167000.0, 169666.66666666666], ["Exact Job Title (Software Engineer)", "NYC Boroughs", 2, 190000.0, 190000.0], ["Broader Job Title (Contains Software Engineer)", "NYC Boroughs", 2, 190000.0, 190000.0], ["Broader Job Title (Contains Software Engineer)", "Other NY", 3, 167000.0, 169666.66666666666], ["Broader Job Title (Contains Software Engineer)", "NYC City Only", 455, 186000.0, 195526.221978022]], "truncated": false}
```

**run_sql** `{"query": "WITH normalized_wages AS (\n  SELECT\n    case_number,\n    TRIM(job_title) as job_title,\n    TRIM(worksite_city) as worksite_city,\n    worksite_state,\n    CAST(wage_from AS DOUBLE) as wage_raw,\n    wage_unit,\n    CASE\n      WHEN wage_unit = 'Year' THEN CAST(wage_from AS DOUBLE)\n      WHEN wage_unit = 'Month' THEN CAST(wage_from AS DOUBLE) * 12\n      WHEN wage_unit = 'Week' THEN CAST(wage_from AS DOUBLE) * 52\n      WHEN wage_unit = 'Hour' THEN CAST(wage_from AS DOUBLE) * 2080\n      ELSE NULL\n    END as wage_annual\n  FROM lca\n  WHERE employer_name ILIKE '%Google%'\n    A`
```
{"columns": ["job_group", "geo_group", "count", "median_salary", "avg_salary"], "rows": [["Exact Job Title (Software Engineer)", "NYC Area (including Boroughs)", 438, 186000.0, 194462.17123287672], ["Broader Job Title (Contains Software Engineer)", "NYC Area (including Boroughs)", 457, 186000.0, 195502.03719912472], ["Exact Job Title (Software Engineer)", "New York City Only", 436, 186000.0, 194482.63990825688], ["Broader Job Title (Contains Software Engineer)", "New York City Only", 455, 186000.0, 195526.221978022]], "truncated": false}
```

**run_sql** `{"query": "WITH normalized_wages AS (\n  SELECT\n    case_number,\n    TRIM(job_title) as job_title,\n    TRIM(worksite_city) as worksite_city,\n    worksite_state,\n    CAST(wage_from AS DOUBLE) as wage_raw,\n    wage_unit,\n    CASE\n      WHEN wage_unit = 'Year' THEN CAST(wage_from AS DOUBLE)\n      WHEN wage_unit = 'Month' THEN CAST(wage_from AS DOUBLE) * 12\n      WHEN wage_unit = 'Week' THEN CAST(wage_from AS DOUBLE) * 52\n      WHEN wage_unit = 'Hour' THEN CAST(wage_from AS DOUBLE) * 2080\n      ELSE NULL\n    END as wage_annual\n  FROM lca\n  WHERE employer_name ILIKE '%Google%'\n    A`
```
{"columns": ["cnt", "med", "avg"], "rows": [[436, 186000.0, 194482.63990825688]], "truncated": false}
```

**run_sql** `{"query": "WITH normalized_wages AS (\n  SELECT\n    case_number,\n    TRIM(job_title) as job_title,\n    TRIM(worksite_city) as worksite_city,\n    worksite_state,\n    CAST(wage_from AS DOUBLE) as wage_raw,\n    wage_unit,\n    CASE\n      WHEN wage_unit = 'Year' THEN CAST(wage_from AS DOUBLE)\n      WHEN wage_unit = 'Month' THEN CAST(wage_from AS DOUBLE) * 12\n      WHEN wage_unit = 'Week' THEN CAST(wage_from AS DOUBLE) * 52\n      WHEN wage_unit = 'Hour' THEN CAST(wage_from AS DOUBLE) * 2080\n      ELSE NULL\n    END as wage_annual\n  FROM lca\n  WHERE employer_name = 'Google LLC'\n    AND`
```
{"columns": ["cnt", "med", "avg"], "rows": [[436, 186000.0, 194482.63990825688]], "truncated": false}
```

**run_sql** `{"query": "WITH normalized_wages AS (\n  SELECT\n    TRIM(job_title) as job_title,\n    TRIM(worksite_city) as worksite_city,\n    CASE\n      WHEN wage_unit = 'Year' THEN CAST(wage_from AS DOUBLE)\n      WHEN wage_unit = 'Month' THEN CAST(wage_from AS DOUBLE) * 12\n      WHEN wage_unit = 'Week' THEN CAST(wage_from AS DOUBLE) * 52\n      WHEN wage_unit = 'Hour' THEN CAST(wage_from AS DOUBLE) * 2080\n      ELSE NULL\n    END as wage_annual\n  FROM lca\n  WHERE employer_name = 'Google LLC'\n    AND source_file LIKE '%FY2025%'\n    AND TRIM(job_title) = 'Software Engineer'\n    AND TRIM(worksite_`
```
{"error": "Catalog Error: Scalar Function with name percentile_cont does not exist!\nDid you mean \"percent_rank\"?\n\nLINE 20:   PERCENTILE_CONT(wage_annual, 0.25) as p25_wage,\n           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^"}
```

**Answer:** FAILED: MaxTurnsExceeded: Max turns (15) exceeded

</details>

<details><summary>H-1B Analyst: 7 tool calls</summary>

**read_mappings** `{}`
```
{"as_of": "FY2026 Q3", "tables": {"lca": {"description": "One row per H-1B Labor Condition Application (LCA) filed with the Department of Labor, FY2024 Q1 to FY2026 Q3, amendments deduplicated. An LCA is a filing an employer must make BEFORE an H-1B petition; it is not an approval or a visa.", "columns": [{"name": "case_number", "type": "VARCHAR", "description": "DOL case number, unique per row."}, {"name": "case_status", "type": "VARCHAR", "description": "DOL decision. Use 'CERTIFIED' for filings employers could actually use.", "is_enum": true}, {"name": "fiscal_year", "type": "INTEGER", "description": "US federal fiscal year of the decision (Oct 1 - Sep 30). FY2026 = Oct 2025 - Sep 2026.", "is_enum": true}, {"name": "quarter", "type": "INTEGER", "description": "Fiscal quarter 1-4 (Q1 = Oct-Dec).", "is_enum": true}, {"name": "received_date", "type": "DATE", "description": "Date DOL rece
```

**find_employer** `{"name": "Google"}`
```
{"matches": [{"employer_id": 4, "employer": "Google", "employer_type": "big_tech", "filings": 25088, "match_score": 100, "name_variants_merged": 3, "sample_variants": ["Google LLC", "Google Public Sector LLC", "Google Client Services LLC"]}, {"employer_id": 1089, "employer": "Gofo", "employer_type": "other", "filings": 147, "match_score": 77, "name_variants_merged": 7, "sample_variants": ["GOFO Inc.", "GOFO Inc", "GOFO, Inc.", "GOFO, Inc"]}, {"employer_id": 11975, "employer": "Hooglee", "employer_type": "other", "filings": 13, "match_score": 77, "name_variants_merged": 1, "sample_variants": ["Hooglee Corp."]}, {"employer_id": 90702, "employer": "Goop", "employer_type": "other", "filings": 1, "match_score": 77, "name_variants_merged": 1, "sample_variants": ["Goop, Inc."]}, {"employer_id": 92405, "employer": "Glex", "employer_type": "other", "filings": 1, "match_score": 77, "name_variants_
```

**find_location** `{"place": "NYC"}`
```
{"area_code": "35620", "metro_name": "New York-Newark-Jersey City, NY-NJ", "matched_by": "alias"}
```

**find_role** `{"text": "software engineer"}`
```
{"role_family": "Software Engineer", "matched_by": "rules", "main_soc_codes": [{"soc_code": "15-1252", "soc_title": "Software Developers", "filings": 398062}, {"soc_code": "15-1299", "soc_title": "Computer Systems Engineers/Architects", "filings": 44586}, {"soc_code": "15-1251", "soc_title": "Computer Programmers", "filings": 33979}], "example_titles": ["software engineer", "software developer", "senior software engineer", "software engineering", "manager jc50 computer systems engineers architects", "software development engineer ii"]}
```

**run_sql** `{"query": "SELECT median(wage_annual_from) AS median_pay, count(*) AS filings, sum(total_worker_positions) AS positions FROM lca WHERE employer_id = 4 AND role_family = 'Software Engineer' AND area_code = '35620' AND fiscal_year = 2025 AND case_status = 'CERTIFIED' AND wage_flag = 'ok';"}`
```
{"columns": ["median_pay", "filings", "positions"], "rows": [[186000.0, 465, 465]], "row_count": 1, "truncated": false}
```

**run_sql** `{"query": "SELECT fiscal_year, median(wage_annual_from) AS median_pay, count(*) AS filings FROM lca WHERE employer_id = 4 AND role_family = 'Software Engineer' AND area_code = '35620' AND case_status = 'CERTIFIED' AND wage_flag = 'ok' GROUP BY 1 ORDER BY 1;"}`
```
{"columns": ["fiscal_year", "median_pay", "filings"], "rows": [[2024, 182000.0, 535], [2025, 186000.0, 465], [2026, 200000.0, 350]], "row_count": 3, "truncated": false}
```

**make_chart** `{"mark": "line", "color": null, "y": "median_pay", "x": "fiscal_year", "title": "Median Software Engineer Offered Salary, Google (NYC Metro)"}`
```
{"ok": true, "note": "Chart shown to the user. Do not describe the chart's styling."}
```

**Answer:** The median offered salary for software engineers at Google in the New York City metro area was $186,000 in FY2025.

* **FY2025 filings**: This median is based on 465 certified Labor Condition Applications (LCAs) representing 465 worker positions with reliable wage data.
* **Year-over-year growth**: This is a slight increase from FY2024, which saw a median offered salary of $182,000 across 535 certified filings.
* **FY2026 trajectory**: Partial data for FY2026 shows the median salary climbing further to $200,000 based on 350 certified filings.

</details>

Saved traces/what-was-the-median-offered-salary-for-software-engineers-at.json

