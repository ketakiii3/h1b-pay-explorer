loaded h1b.duckdb: 1,532,089 filings, 107,638 employers
15:44:31 - LiteLLM:WARNING: vertex_and_google_ai_studio_gemini.py:1265 - DeprecationWarning: `temperature`, `top_p`, and `top_k` continue to function for Gemini 3+ (gemini-3.5-flash) but are planned for removal in a future release. Move sampling guidance into the `system` instructions instead.
run 1: {'plain_ok': True, 'agent_ok': True}
run 2: {'plain_ok': False, 'agent_ok': True}
run 3: {'plain_ok': False, 'agent_ok': True}

### Who were the top 5 sponsors of data scientists nationally in FY2025, by positions?

**Expected:** ['Goldman Sachs', 'Amazon', 'Microsoft', 'Meta', 'Walmart'] (gold SQL on `lca`).

Plain agent right in 1/3 runs; H-1B Analyst right in 3/3 runs.

**No tools:** Because Fiscal Year 2025 (FY2025) is currently ongoing and official, fully consolidated immigration data is typically not finalized and released by the U.S. Citizenship and Immigration Services (USCIS) until after the fiscal year ends, **complete and official national data for the entirety of FY2025 is not yet available.** Additionally, I do not have real-time data access to pull live-updating labor condition applications (LCAs) or H-1B petition filings.

However, based on historical filing trends from recent fiscal years (FY2023 and FY2024), the top sponsors for "Data Scientist" positions in 

<details><summary>Plain run_sql agent: 15 tool calls</summary>

**run_sql** `{"query": "DESCRIBE lca;"}`
```
{"columns": ["column_name", "column_type", "null", "key", "default", "extra"], "rows": [["case_number", "VARCHAR", "YES", null, null, null], ["case_status", "VARCHAR", "YES", null, null, null], ["received_date", "VARCHAR", "YES", null, null, null], ["decision_date", "VARCHAR", "YES", null, null, null], ["visa_class", "VARCHAR", "YES", null, null, null], ["job_title", "VARCHAR", "YES", null, null, null], ["soc_code", "VARCHAR", "YES", null, null, null], ["soc_title", "VARCHAR", "YES", null, null, null], ["full_time", "VARCHAR", "YES", null, null, null], ["begin_date", "VARCHAR", "YES", null, null, null], ["total_worker_positions", "VARCHAR", "YES", null, null, null], ["new_employment", "VARCHAR", "YES", null, null, null], ["continued_employment", "VARCHAR", "YES", null, null, null], ["change_previous_employment", "VARCHAR", "YES", null, null, null], ["new_concurrent_employment", "VARCHAR"
```

**run_sql** `{"query": "SELECT received_date, decision_date, source_file FROM lca LIMIT 10;"}`
```
{"columns": ["received_date", "decision_date", "source_file"], "rows": [["45401", "45408", "LCA_Disclosure_Data_FY2024_Q3.xlsx"], ["45401", "45408", "LCA_Disclosure_Data_FY2024_Q3.xlsx"], ["45401", "45408", "LCA_Disclosure_Data_FY2024_Q3.xlsx"], ["45401", "45408", "LCA_Disclosure_Data_FY2024_Q3.xlsx"], ["45401", "45408", "LCA_Disclosure_Data_FY2024_Q3.xlsx"], ["45401", "45408", "LCA_Disclosure_Data_FY2024_Q3.xlsx"], ["45402", "45408", "LCA_Disclosure_Data_FY2024_Q3.xlsx"], ["45401", "45408", "LCA_Disclosure_Data_FY2024_Q3.xlsx"], ["45402", "45408", "LCA_Disclosure_Data_FY2024_Q3.xlsx"], ["45402", "45408", "LCA_Disclosure_Data_FY2024_Q3.xlsx"]], "truncated": false}
```

**run_sql** `{"query": "SELECT DISTINCT source_file FROM lca;"}`
```
{"columns": ["source_file"], "rows": [["LCA_Disclosure_Data_FY2024_Q4.xlsx"], ["LCA_Disclosure_Data_FY2025_Q3.xlsx"], ["LCA_Disclosure_Data_FY2025_Q2.xlsx"], ["LCA_Disclosure_Data_FY2026_Q3.xlsx"], ["LCA_Disclosure_Data_FY2024_Q3.xlsx"], ["LCA_Disclosure_Data_FY2024_Q1.xlsx"], ["LCA_Disclosure_Data_FY2025_Q1.xlsx"], ["LCA_Disclosure_Data_FY2025_Q4.xlsx"], ["LCA_Disclosure_Data_FY2024_Q2.xlsx"]], "truncated": false}
```

**run_sql** `{"query": "SELECT count(*) FROM lca WHERE source_file LIKE '%FY2025%';"}`
```
{"columns": ["count_star()"], "rows": [[582271]], "truncated": false}
```

**run_sql** `{"query": "SELECT DISTINCT soc_code, soc_title FROM lca WHERE LOWER(soc_title) LIKE '%data scientist%' OR LOWER(job_title) LIKE '%data scientist%';"}`
```
{"columns": ["soc_code", "soc_title"], "rows": [["15-2051.01", "Data Scientists"], ["19-2012.00", "Physicists"], ["19-2042.00", "Geoscientists, Except Hydrologists and Geographers"], ["19-3011.00", "Economists"], ["15-1299.02", "Geographic Information Systems Technologists and Technicians"], ["13-1161.00", "Market Research Analysts and Marketing Specialists"], ["15-1199.08", "Business Intelligence Analysts"], ["13-2054.00", "Financial Risk Specialists"], ["11-3051.00", "Industrial Production Managers"], ["19-2021.00", "Atmospheric and Space Scientists"], ["17-2051.01", "Transportation Engineers"], ["19-2099.00", "Physical Scientists, All Other"], ["17-2021.00", "Agricultural Engineers"], ["13-2011.00", "Accountants and Auditors"], ["17-2071.00", "Electrical Engineers"], ["15-1221.00", "Computer and Information Research Scientists"], ["15-1133.00", "Software Developers, Systems Software"]
```

**run_sql** `{"query": "SELECT total_worker_positions, COUNT(*) FROM lca GROUP BY total_worker_positions LIMIT 10;"}`
```
{"columns": ["total_worker_positions", "count_star()"], "rows": [["3", 9154], ["21", 7], ["125", 28], ["15", 1360], ["26", 5], ["29", 5], ["24", 1], ["38", 1], ["1250", 4], ["7", 145]], "truncated": false}
```

**run_sql** `{"query": "SELECT case_status, COUNT(*) FROM lca GROUP BY case_status;"}`
```
{"columns": ["case_status", "count_star()"], "rows": [["Denied", 9674], ["Withdrawn", 25043], ["Certified", 1433993], ["Certified - Withdrawn", 87320]], "truncated": false}
```

**run_sql** `{"query": "SELECT employer_name, \n       SUM(TRY_CAST(total_worker_positions AS INTEGER)) AS positions_job_title\nFROM lca \nWHERE source_file LIKE '%FY2025%'\n  AND case_status IN ('Certified', 'Certified - Withdrawn')\n  AND LOWER(job_title) LIKE '%data scientist%'\nGROUP BY employer_name\nORDER BY positions_job_title DESC\nLIMIT 10;"}`
```
{"columns": ["employer_name", "positions_job_title"], "rows": [["Amazon.com Services LLC", 1502], ["Meta Platforms, Inc", 527], ["Oracle America, Inc.", 406], ["WAL-MART ASSOCIATES, INC.", 336], ["Amazon Web Services, Inc.", 240], ["Google LLC", 224], ["Cisco Systems, Inc.", 193], ["Apple Inc.", 184], ["TikTok Inc.", 112], ["NVIDIA Corporation", 111]], "truncated": false}
```

**run_sql** `{"query": "SELECT employer_name, \n       SUM(TRY_CAST(total_worker_positions AS INTEGER)) AS positions_soc\nFROM lca \nWHERE source_file LIKE '%FY2025%'\n  AND case_status IN ('Certified', 'Certified - Withdrawn')\n  AND (soc_code LIKE '15-2051%' OR LOWER(soc_title) LIKE 'data scientists%')\nGROUP BY employer_name\nORDER BY positions_soc DESC\nLIMIT 10;"}`
```
{"columns": ["employer_name", "positions_soc"], "rows": [["Amazon.com Services LLC", 7175], ["Microsoft Corporation", 2867], ["Amazon Web Services, Inc.", 1148], ["GOLDMAN SACHS & CO. LLC", 1006], ["GOLDMAN SACHS SERVICES LLC", 934], ["GOLDMAN SACHS BANK USA", 927], ["WAL-MART ASSOCIATES, INC.", 884], ["Meta Platforms, Inc", 804], ["Cisco Systems, Inc.", 726], ["KFORCE INC. ", 610]], "truncated": false}
```

**run_sql** `{"query": "SELECT job_title, COUNT(*), SUM(TRY_CAST(total_worker_positions AS INTEGER)) AS pos \nFROM lca \nWHERE source_file LIKE '%FY2025%'\n  AND case_status IN ('Certified', 'Certified - Withdrawn')\n  AND (soc_code LIKE '15-2051%' OR LOWER(soc_title) LIKE 'data scientists%')\n  AND employer_name LIKE 'GOLDMAN SACHS%'\nGROUP BY job_title\nORDER BY pos DESC\nLIMIT 10;"}`
```
{"columns": ["job_title", "count_star()", "pos"], "rows": [["ANALYST", 9, 900], ["VICE PRESIDENT", 9, 900], ["ASSOCIATE", 9, 900], ["Associate, Data Analytics", 11, 11], ["Snr Analyst, Technology Audit", 9, 9], ["Associate, Technology Audit", 9, 9], ["Vice President, Product Management", 9, 9], ["Associate, Product Management", 5, 5], ["Vice President, Data Analytics", 5, 5], ["Analyst, Data Analytics BI", 5, 5]], "truncated": false}
```

**run_sql** `{"query": "SELECT job_title, COUNT(*), SUM(TRY_CAST(total_worker_positions AS INTEGER)) AS pos \nFROM lca \nWHERE source_file LIKE '%FY2025%'\n  AND case_status IN ('Certified', 'Certified - Withdrawn')\n  AND (soc_code LIKE '15-2051%' OR LOWER(soc_title) LIKE 'data scientists%')\n  AND employer_name LIKE 'Microsoft%'\nGROUP BY job_title\nORDER BY pos DESC\nLIMIT 10;"}`
```
{"columns": ["job_title", "count_star()", "pos"], "rows": [["Research, Applied and Data Sciences", 15, 1500], ["Data Engineering", 135, 531], ["Data Science", 263, 263], ["Applied Sciences", 191, 191], ["Product Management", 94, 94], ["Technical Program Management", 61, 61], ["Data Analytics", 38, 38], ["Research Sciences", 33, 33], ["Security Research", 30, 30], ["Business Analytics", 24, 24]], "truncated": false}
```

**run_sql** `{"query": "SELECT job_title, COUNT(*), SUM(TRY_CAST(total_worker_positions AS INTEGER)) AS pos \nFROM lca \nWHERE source_file LIKE '%FY2025%'\n  AND case_status IN ('Certified', 'Certified - Withdrawn')\n  AND (soc_code LIKE '15-2051%' OR LOWER(soc_title) LIKE 'data scientists%')\n  AND employer_name = 'Amazon.com Services LLC'\nGROUP BY job_title\nORDER BY pos DESC\nLIMIT 10;"}`
```
{"columns": ["job_title", "count_star()", "pos"], "rows": [["Business Intelligence Engineer II", 323, 1836], ["Data Scientist II", 136, 856], ["Business Intelligence Engineer III", 119, 776], ["Business Analyst II", 108, 606], ["Business Intelligence Engineer I", 85, 517], ["Data Scientist III", 85, 472], ["Data Engineer II", 109, 380], ["Manager III, Business Intelligence", 37, 289], ["Business Analyst III", 43, 232], ["Business Analyst I", 34, 142]], "truncated": false}
```

**run_sql** `{"query": "SELECT employer_name, \n       SUM(TRY_CAST(total_worker_positions AS INTEGER)) AS positions_all_job_title\nFROM lca \nWHERE source_file LIKE '%FY2025%'\n  AND LOWER(job_title) LIKE '%data scientist%'\nGROUP BY employer_name\nORDER BY positions_all_job_title DESC\nLIMIT 10;"}`
```
{"columns": ["employer_name", "positions_all_job_title"], "rows": [["Amazon.com Services LLC", 1502], ["Meta Platforms, Inc", 527], ["Oracle America, Inc.", 406], ["WAL-MART ASSOCIATES, INC.", 338], ["Amazon Web Services, Inc.", 240], ["Google LLC", 225], ["Cisco Systems, Inc.", 193], ["Apple Inc.", 184], ["TikTok Inc.", 113], ["NVIDIA Corporation", 111]], "truncated": false}
```

**run_sql** `{"query": "SELECT employer_name, \n       SUM(TRY_CAST(total_worker_positions AS INTEGER)) AS positions_all_soc\nFROM lca \nWHERE source_file LIKE '%FY2025%'\n  AND (soc_code LIKE '15-2051%' OR LOWER(soc_title) LIKE 'data scientists%')\nGROUP BY employer_name\nORDER BY positions_all_soc DESC\nLIMIT 10;"}`
```
{"columns": ["employer_name", "positions_all_soc"], "rows": [["Amazon.com Services LLC", 7197], ["Microsoft Corporation", 2868], ["Amazon Web Services, Inc.", 1148], ["GOLDMAN SACHS & CO. LLC", 1107], ["GOLDMAN SACHS SERVICES LLC", 935], ["GOLDMAN SACHS BANK USA", 927], ["WAL-MART ASSOCIATES, INC.", 895], ["Meta Platforms, Inc", 804], ["Cisco Systems, Inc.", 726], ["KFORCE INC. ", 610]], "truncated": false}
```

**run_sql** `{"query": "SELECT DISTINCT soc_code, soc_title \nFROM lca \nWHERE source_file LIKE '%FY2025%' \n  AND (LOWER(soc_title) LIKE '%data scientist%' OR LOWER(soc_code) LIKE '15-2051%')\nORDER BY soc_code;"}`
```
{"columns": ["soc_code", "soc_title"], "rows": [["12-2051.00", "Data Scientists"], ["15-1251.00", "Data Scientists"], ["15-2051", "Data Scientist"], ["15-2051", "DATA SCIENTISTS"], ["15-2051", "Business Intelligence Analysts"], ["15-2051", "DATA SCIENTIST"], ["15-2051", "Data Scientists"], ["15-2051.00", "Data Scientist"], ["15-2051.00", "Business Intelligence Analysts"], ["15-2051.00", "Data Scientists"], ["15-2051.01", "Data Scientists"], ["15-2051.01", "Business Intelligence Analysts"], ["15-2051.01", "Business Intelligence Analyst"], ["15-2051.01", "Business intelligence Analyst"], ["15-2051.01", "BUSINESS INTELLIGENCE ANALYSTS"], ["15-2051.02", "Business Intelligence Analyst"], ["15-2051.02", "Clinical Data Managers"]], "truncated": false}
```

**Answer:** FAILED: MaxTurnsExceeded: Max turns (15) exceeded

</details>

<details><summary>H-1B Analyst: 4 tool calls</summary>

**read_mappings** `{}`
```
{"as_of": "FY2026 Q3", "tables": {"lca": {"description": "One row per H-1B Labor Condition Application (LCA) filed with the Department of Labor, FY2024 Q1 to FY2026 Q3, amendments deduplicated. An LCA is a filing an employer must make BEFORE an H-1B petition; it is not an approval or a visa.", "columns": [{"name": "case_number", "type": "VARCHAR", "description": "DOL case number, unique per row."}, {"name": "case_status", "type": "VARCHAR", "description": "DOL decision. Use 'CERTIFIED' for filings employers could actually use.", "is_enum": true}, {"name": "fiscal_year", "type": "INTEGER", "description": "US federal fiscal year of the decision (Oct 1 - Sep 30). FY2026 = Oct 2025 - Sep 2026.", "is_enum": true}, {"name": "quarter", "type": "INTEGER", "description": "Fiscal quarter 1-4 (Q1 = Oct-Dec).", "is_enum": true}, {"name": "received_date", "type": "DATE", "description": "Date DOL rece
```

**find_role** `{"text": "data scientist"}`
```
{"role_family": "Data Scientist", "matched_by": "rules", "main_soc_codes": [{"soc_code": "15-2051", "soc_title": "Data Scientists", "filings": 38958}, {"soc_code": "15-2041", "soc_title": "Statisticians", "filings": 6341}, {"soc_code": "15-2031", "soc_title": "Operations Research Analysts", "filings": 969}], "example_titles": ["data scientist", "senior data scientist", "data scientist ii", "data scientist iii", "data science", "machine learning"]}
```

**run_sql** `{"query": "SELECT employer, sum(total_worker_positions) AS positions, count(*) AS filings, median(wage_annual_from) FILTER (WHERE wage_flag = 'ok') AS median_pay FROM lca WHERE role_family = 'Data Scientist' AND fiscal_year = 2025 AND case_status = 'CERTIFIED' GROUP BY 1 ORDER BY positions DESC LIMIT 5"}`
```
{"columns": ["employer", "positions", "filings", "median_pay"], "rows": [["Goldman Sachs", 2817, 144, 101700.0], ["Amazon", 2495, 668, 155000.0], ["Microsoft", 1100, 704, 168702.0], ["Meta", 689, 425, 200527.0], ["Walmart", 664, 664, 152148.0]], "row_count": 5, "truncated": false}
```

**make_chart** `{"color": null, "x": "employer", "title": "Top Data Scientist Sponsors by Positions, FY2025", "mark": "bar", "y": "positions"}`
```
{"ok": true, "note": "Chart shown to the user. Do not describe the chart's styling."}
```

**Answer:** Goldman Sachs was the top sponsor of data scientists nationally in FY2025, sponsoring 2,817 worker positions.

* **Goldman Sachs** led with 2,817 positions across 144 certified LCAs, offering a median salary of $102k.
* **Amazon** followed with 2,495 positions from 668 certified filings, offering a median salary of $155k.
* **Microsoft** sponsored 1,100 positions across 704 certified filings with a median salary of $169k, followed by **Meta** with 689 positions across 425 certified filings and a median salary of $201k.
* **Walmart** completed the top five with 664 positions from 664 certified filings, offering a median salary of $152k.

</details>

Saved traces/who-were-the-top-5-sponsors-of-data-scientists-nationally-in.json

