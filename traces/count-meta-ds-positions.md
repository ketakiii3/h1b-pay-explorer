loaded h1b.duckdb: 1,532,089 filings, 107,638 employers
15:48:37 - LiteLLM:WARNING: vertex_and_google_ai_studio_gemini.py:1265 - DeprecationWarning: `temperature`, `top_p`, and `top_k` continue to function for Gemini 3+ (gemini-3.5-flash) but are planned for removal in a future release. Move sampling guidance into the `system` instructions instead.
run 1: {'plain_ok': False, 'agent_ok': True}
run 2: {'plain_ok': False, 'agent_ok': True}
run 3: {'plain_ok': False, 'agent_ok': True}

### How many certified data scientist positions did Meta file for in FY2025?

**Expected:** 689 (gold SQL on `lca`).

Plain agent right in 0/3 runs; H-1B Analyst right in 3/3 runs.

**No tools:** I do not have access to the complete or finalized data for Fiscal Year 2025 (FY2025), as the fiscal year runs from October 1, 2024, through September 30, 2025, and my knowledge cutoff is January 2025. 

The U.S. Department of Labor (DOL) typically releases disclosure data for Labor Condition Applications (LCAs for H-1B visas) and permanent labor certifications (PERM) on a quarterly basis, with the fully consolidated data for the entire fiscal year only becoming available late in the calendar year or the following year. 

To find the most up-to-date or eventually finalized numbers for Meta's FY

<details><summary>Plain run_sql agent: 15 tool calls</summary>

**run_sql** `{"query": "DESCRIBE lca;"}`
```
{"columns": ["column_name", "column_type", "null", "key", "default", "extra"], "rows": [["case_number", "VARCHAR", "YES", null, null, null], ["case_status", "VARCHAR", "YES", null, null, null], ["received_date", "VARCHAR", "YES", null, null, null], ["decision_date", "VARCHAR", "YES", null, null, null], ["visa_class", "VARCHAR", "YES", null, null, null], ["job_title", "VARCHAR", "YES", null, null, null], ["soc_code", "VARCHAR", "YES", null, null, null], ["soc_title", "VARCHAR", "YES", null, null, null], ["full_time", "VARCHAR", "YES", null, null, null], ["begin_date", "VARCHAR", "YES", null, null, null], ["total_worker_positions", "VARCHAR", "YES", null, null, null], ["new_employment", "VARCHAR", "YES", null, null, null], ["continued_employment", "VARCHAR", "YES", null, null, null], ["change_previous_employment", "VARCHAR", "YES", null, null, null], ["new_concurrent_employment", "VARCHAR"
```

**run_sql** `{"query": "SELECT DISTINCT case_status FROM lca;"}`
```
{"columns": ["case_status"], "rows": [["Certified - Withdrawn"], ["Certified"], ["Withdrawn"], ["Denied"]], "truncated": false}
```

**run_sql** `{"query": "SELECT DISTINCT employer_name FROM lca WHERE employer_name ILIKE '%Meta%' LIMIT 20;"}`
```
{"columns": ["employer_name"], "rows": [["Meta Platforms, Inc"], ["Liquidmetal Ventures Management LLC"], ["Meta Platforms, Inc. "], ["Meta Platforms, Inc."], ["Meta Hub IT Solutions Inc"], ["META PLATFORMS, INC."], ["META PLATFORMS, INC. "], ["Fortune Plastic & Metal Inc."], ["METAGENICS LLC"], ["General Metabolics, LLC"], ["American Metal Technologies LLC"], ["Elite Metal Framing & Construction"], ["Metagenomi, Inc."], ["Climax Metal Products Company"], ["Kennametal, Inc. "], ["META SOFT INC"], ["Titan Metal Industries, Inc."], ["Metacubes LLC"], ["Metaphore Biotechnologies, Inc."], ["PRIMETALS TECHNOLOGIES USA LLC"]], "truncated": false}
```

**run_sql** `{"query": "SELECT source_file, COUNT(*) FROM lca GROUP BY 1;"}`
```
{"columns": ["source_file", "count_star()"], "rows": [["LCA_Disclosure_Data_FY2024_Q4.xlsx", 117339], ["LCA_Disclosure_Data_FY2025_Q2.xlsx", 128673], ["LCA_Disclosure_Data_FY2026_Q3.xlsx", 426952], ["LCA_Disclosure_Data_FY2025_Q4.xlsx", 114826], ["LCA_Disclosure_Data_FY2025_Q1.xlsx", 104046], ["LCA_Disclosure_Data_FY2024_Q3.xlsx", 212766], ["LCA_Disclosure_Data_FY2024_Q1.xlsx", 96294], ["LCA_Disclosure_Data_FY2024_Q2.xlsx", 120408], ["LCA_Disclosure_Data_FY2025_Q3.xlsx", 234726]], "truncated": false}
```

**run_sql** `{"query": "SELECT MIN(decision_date), MAX(decision_date) FROM lca WHERE source_file LIKE '%FY2025%';"}`
```
{"columns": ["min(decision_date)", "max(decision_date)"], "rows": [["45566", "45930"]], "truncated": false}
```

**run_sql** `{"query": "SELECT DATE '1899-12-30' + INTERVAL (45566) DAY;"}`
```
{"columns": ["(CAST('1899-12-30' AS DATE) + to_days(CAST(trunc(CAST(45566 AS DOUBLE)) AS INTEGER)))"], "rows": [["2024-10-01 00:00:00"]], "truncated": false}
```

**run_sql** `{"query": "SELECT DATE '1899-12-30' + INTERVAL (45930) DAY;"}`
```
{"columns": ["(CAST('1899-12-30' AS DATE) + to_days(CAST(trunc(CAST(45930 AS DOUBLE)) AS INTEGER)))"], "rows": [["2025-09-30 00:00:00"]], "truncated": false}
```

**run_sql** `{"query": "SELECT job_title, COUNT(*), SUM(CAST(total_worker_positions AS INTEGER)) \nFROM lca \nWHERE (employer_name ILIKE '%Meta Platforms%') \n  AND source_file LIKE '%FY2025%' \n  AND job_title ILIKE '%Data Scientist%'\nGROUP BY job_title;"}`
```
{"columns": ["job_title", "count_star()", "sum(CAST(total_worker_positions AS INTEGER))"], "rows": [["Data Scientist, Product Analytics", 21, 21], ["Data Scientist, RL Product Marketing DS", 1, 1], ["Data Scientist / Data Science Manager", 1, 1], ["Data Scientists", 1, 1], ["Data Scientist, Data Center", 1, 1], ["Data Scientists, Analytics", 1, 1], ["Data Scientist Analytics", 1, 1], ["Data scientist", 1, 1], ["Data Scientist Manager", 3, 3], ["Data Scientist", 267, 531], ["Data Scientist, Product", 1, 1], ["Data Scientist, Small Business Group", 1, 1], ["Data Scientist, Analytics", 35, 35], ["Senior Data Scientist", 2, 2], ["Data Scientist - Legal", 1, 1]], "truncated": false}
```

**run_sql** `{"query": "SELECT DISTINCT employer_name \nFROM lca \nWHERE employer_name ILIKE '%Meta%' \n  AND source_file LIKE '%FY2025%'\nORDER BY employer_name;"}`
```
{"columns": ["employer_name"], "rows": [["3V Metals, Inc"], ["AA Metals, Inc."], ["Adukemeta LLC"], ["Alubar Metals Missouri, LLC"], ["American Metalcraft, Inc."], ["Ardagh Metal Packaging USA Corp."], ["Artmeta LLC"], ["Atek Metal Technologies LLC"], ["BASF Environmental Catalyst and Metal Solutions"], ["BASF Metals LLC"], ["Boston Electrometallurgical Corporation"], ["CHUANGYI METALS CORP. "], ["CNA METALS LIMITED"], ["Carlisle Architectural Metals LLC"], ["Chemetall U.S., Inc."], ["Climax Metal Products Company"], ["Conmeta, Inc."], ["Cortec Precision Sheet Metal, Inc"], ["Desktop Metal Operating, Inc. "], ["Detroit Tool Metal Products"], ["Dixie Metal Products Inc"], ["EAGLE METAL PRODUCTS LLC"], ["ERD METAL INC"], ["ERD METAL, INC."], ["East Coast Metal Structures Corp"], ["Elite Metal Framing and Construction"], ["Ernst Metal Technologies, LLC"], ["FAIST LIGHT METALS TENNESSEE, LLC
```

**run_sql** `{"query": "SELECT DISTINCT employer_name, count(*) \nFROM lca \nWHERE employer_name ILIKE '%Meta%' \n  AND (employer_name ILIKE 'Meta %' OR employer_name ILIKE 'META %')\nGROUP BY 1 \nORDER BY 2 DESC;"}`
```
{"columns": ["employer_name", "count_star()"], "rows": [["Meta Platforms, Inc", 14550], ["Meta Platforms, Inc.", 1680], ["Meta Platforms, Inc. ", 462], ["META PLATFORMS, INC.", 451], ["META PLATFORMS, INC. ", 386], ["META IT CORP", 51], ["META SOFT INC", 27], ["META IT SYSTEMS LLC", 26], ["Meta Hub IT Solutions Inc", 13], ["Meta Payments Inc. (formerly known as Facebook Payments, Inc)", 10], ["Meta Hub IT Solutions Inc.", 9], ["Meta Info Solutions Inc", 3], ["Meta Soft Inc.", 3], ["Meta Protocol, Inc. ", 2], ["Meta One Inc", 2], ["Meta Protocol, Inc.", 2], ["Meta Nau Inc.", 1], ["META ONE INC", 1], ["Meta Supply Chain Management Inc", 1], ["Meta Development LLC", 1], ["Meta Info Solutions Inc.", 1], ["Meta Tools Technologies LLC", 1]], "truncated": false}
```

**run_sql** `{"query": "SELECT DISTINCT soc_code, soc_title \nFROM lca \nWHERE (employer_name ILIKE 'Meta Platforms%' OR employer_name ILIKE 'META PLATFORMS%') \n  AND source_file LIKE '%FY2025%' \n  AND (job_title ILIKE '%Data Scientist%' OR soc_title ILIKE '%Data Scientist%')\nORDER BY 1, 2;"}`
```
{"columns": ["soc_code", "soc_title"], "rows": [["11-3021.00", "Computer and Information Systems Managers"], ["13-1081.02", "Logistics Analysts"], ["15-1221.00", "Computer and Information Research Scientists"], ["15-1243.01", "Data Warehousing Specialists"], ["15-1253.00", "Software Quality Assurance Analysts and Testers"], ["15-2031.00", "Operations Research Analysts"], ["15-2041.00", "Statisticians"], ["15-2051.00", "Data Scientists"], ["15-2051.01", "Business Intelligence Analysts"]], "truncated": false}
```

**run_sql** `{"query": "SELECT \n  case_status,\n  job_title,\n  soc_code,\n  soc_title,\n  COUNT(*) as cases,\n  SUM(CAST(total_worker_positions AS INTEGER)) as positions\nFROM lca\nWHERE (employer_name ILIKE 'Meta Platforms%' OR employer_name ILIKE 'META PLATFORMS%')\n  AND source_file LIKE '%FY2025%'\n  AND (job_title ILIKE '%Data Scientist%' OR soc_title ILIKE '%Data Scientist%' OR soc_code = '15-2051.00')\nGROUP BY 1, 2, 3, 4\nORDER BY cases DESC;"}`
```
{"columns": ["case_status", "job_title", "soc_code", "soc_title", "cases", "positions"], "rows": [["Certified", "Data Scientist", "15-2051.00", "Data Scientists", 178, 442], ["Certified", "Data Engineer", "15-2051.00", "Data Scientists", 121, 121], ["Certified", "Software Engineer", "15-2051.00", "Data Scientists", 56, 56], ["Certified", "Data Scientist", "15-2051.01", "Business Intelligence Analysts", 55, 55], ["Certified", "Data Scientist", "15-2031.00", "Operations Research Analysts", 20, 20], ["Certified", "Data Scientist, Analytics", "15-2051.00", "Data Scientists", 19, 19], ["Certified", "Data Scientist, Product Analytics", "15-2051.00", "Data Scientists", 12, 12], ["Certified", "Data Scientist, Analytics", "15-2051.01", "Business Intelligence Analysts", 11, 11], ["Certified", "Data Scientist", "15-2041.00", "Statisticians", 10, 10], ["Certified", "Research Scientist", "15-2051.00"
```

**run_sql** `{"query": "SELECT \n  case_status,\n  COUNT(*) as cases,\n  SUM(CAST(total_worker_positions AS INTEGER)) as positions\nFROM lca\nWHERE (employer_name ILIKE 'Meta Platforms%' OR employer_name ILIKE 'META PLATFORMS%')\n  AND source_file LIKE '%FY2025%'\n  AND (job_title ILIKE '%Data Scientist%' OR soc_title ILIKE '%Data Scientist%' OR soc_code = '15-2051.00')\nGROUP BY 1\nORDER BY cases DESC;"}`
```
{"columns": ["case_status", "cases", "positions"], "rows": [["Certified", 572, 836]], "truncated": false}
```

**run_sql** `{"query": "SELECT \n  employer_name,\n  case_status,\n  COUNT(*) as cases,\n  SUM(CAST(total_worker_positions AS INTEGER)) as positions\nFROM lca\nWHERE employer_name ILIKE '%Meta%'\n  AND source_file LIKE '%FY2025%'\n  AND (job_title ILIKE '%Data Scientist%' OR soc_title ILIKE '%Data Scientist%' OR soc_code = '15-2051.00')\nGROUP BY 1, 2\nORDER BY cases DESC;"}`
```
{"columns": ["employer_name", "case_status", "cases", "positions"], "rows": [["Meta Platforms, Inc", "Certified", 569, 761], ["Meta Platforms, Inc.", "Certified", 3, 75], ["META SOFT INC", "Certified", 3, 3], ["MetaMetrics, Inc.", "Certified", 2, 2], ["Fluent Metal Inc.", "Certified", 1, 1], ["American Metalcraft, Inc.", "Certified", 1, 1], ["GoMeta Inc.", "Withdrawn", 1, 1], ["Metallurg, Inc.", "Certified", 1, 1], ["METASENSE INC.", "Certified", 1, 1], ["MetaSource, LLC", "Certified", 1, 1], ["Metaforge IT Solutions", "Certified", 1, 1], ["GoMeta Inc.", "Certified", 1, 1]], "truncated": false}
```

**run_sql** `{"query": "SELECT \n  job_title,\n  COUNT(*) as cases,\n  SUM(CAST(total_worker_positions AS INTEGER)) as positions\nFROM lca\nWHERE (employer_name ILIKE 'Meta Platforms%')\n  AND source_file LIKE '%FY2025%'\n  AND job_title ILIKE '%Data Scientist%'\nGROUP BY 1\nORDER BY cases DESC;"}`
```
{"columns": ["job_title", "cases", "positions"], "rows": [["Data Scientist", 267, 531], ["Data Scientist, Analytics", 35, 35], ["Data Scientist, Product Analytics", 21, 21], ["Data Scientist Manager", 3, 3], ["Senior Data Scientist", 2, 2], ["Data Scientist, RL Product Marketing DS", 1, 1], ["Data Scientist Analytics", 1, 1], ["Data Scientist, Data Center", 1, 1], ["Data Scientists, Analytics", 1, 1], ["Data Scientist / Data Science Manager", 1, 1], ["Data Scientist, Product", 1, 1], ["Data Scientist, Small Business Group", 1, 1], ["Data scientist", 1, 1], ["Data Scientists", 1, 1], ["Data Scientist - Legal", 1, 1]], "truncated": false}
```

**Answer:** FAILED: MaxTurnsExceeded: Max turns (15) exceeded

</details>

<details><summary>H-1B Analyst: 6 tool calls</summary>

**read_mappings** `{}`
```
{"as_of": "FY2026 Q3", "tables": {"lca": {"description": "One row per H-1B Labor Condition Application (LCA) filed with the Department of Labor, FY2024 Q1 to FY2026 Q3, amendments deduplicated. An LCA is a filing an employer must make BEFORE an H-1B petition; it is not an approval or a visa.", "columns": [{"name": "case_number", "type": "VARCHAR", "description": "DOL case number, unique per row."}, {"name": "case_status", "type": "VARCHAR", "description": "DOL decision. Use 'CERTIFIED' for filings employers could actually use.", "is_enum": true}, {"name": "fiscal_year", "type": "INTEGER", "description": "US federal fiscal year of the decision (Oct 1 - Sep 30). FY2026 = Oct 2025 - Sep 2026.", "is_enum": true}, {"name": "quarter", "type": "INTEGER", "description": "Fiscal quarter 1-4 (Q1 = Oct-Dec).", "is_enum": true}, {"name": "received_date", "type": "DATE", "description": "Date DOL rece
```

**find_employer** `{"name": "Meta"}`
```
{"matches": [{"employer_id": 7, "employer": "Meta", "employer_type": "big_tech", "filings": 17537, "match_score": 100, "name_variants_merged": 7, "sample_variants": ["Meta Platforms, Inc", "Meta Platforms, Inc.", "META PLATFORMS, INC.", "WhatsApp"]}, {"employer_id": 3710, "employer": "Meta IT", "employer_type": "other", "filings": 51, "match_score": 94, "name_variants_merged": 1, "sample_variants": ["META IT CORP"]}, {"employer_id": 6222, "employer": "Meta Soft", "employer_type": "other", "filings": 30, "match_score": 94, "name_variants_merged": 2, "sample_variants": ["META SOFT INC", "Meta Soft Inc."]}, {"employer_id": 7123, "employer": "Meta IT Systems", "employer_type": "other", "filings": 26, "match_score": 94, "name_variants_merged": 1, "sample_variants": ["META IT SYSTEMS LLC"]}, {"employer_id": 8054, "employer": "Meta Hub IT Solutions", "employer_type": "other", "filings": 22, "ma
```

**find_role** `{"text": "data scientist"}`
```
{"role_family": "Data Scientist", "matched_by": "rules", "main_soc_codes": [{"soc_code": "15-2051", "soc_title": "Data Scientists", "filings": 38958}, {"soc_code": "15-2041", "soc_title": "Statisticians", "filings": 6341}, {"soc_code": "15-2031", "soc_title": "Operations Research Analysts", "filings": 969}], "example_titles": ["data scientist", "senior data scientist", "data scientist ii", "data scientist iii", "data science", "machine learning"]}
```

**run_sql** `{"query": "SELECT count(*) AS filings, sum(total_worker_positions) AS positions FROM lca WHERE employer_id = 7 AND role_family = 'Data Scientist' AND case_status = 'CERTIFIED' AND fiscal_year = 2025"}`
```
{"columns": ["filings", "positions"], "rows": [[425, 689]], "row_count": 1, "truncated": false}
```

**run_sql** `{"query": "SELECT fiscal_year, count(*) AS filings, sum(total_worker_positions) AS positions FROM lca WHERE employer_id = 7 AND role_family = 'Data Scientist' AND case_status = 'CERTIFIED' GROUP BY 1 ORDER BY 1"}`
```
{"columns": ["fiscal_year", "filings", "positions"], "rows": [[2024, 463, 463], [2025, 425, 689], [2026, 317, 1157]], "row_count": 3, "truncated": false}
```

**make_chart** `{"y": "positions", "mark": "bar", "x": "fiscal_year", "title": "Meta Certified Data Scientist Positions by Fiscal Year", "color": null}`
```
{"ok": true, "note": "Chart shown to the user. Do not describe the chart's styling."}
```

**Answer:** Meta filed for **689 certified data scientist positions** across 425 filings in FY2025.

* **FY2025 context:** These 425 certified Labor Condition Applications (LCAs) for the Data Scientist role family covered 689 total worker positions.
* **Comparison to FY2024:** In the prior fiscal year, Meta filed 463 certified LCAs representing 463 positions (all single-worker filings).
* **FY2026 trend:** In the current fiscal year (partial, through FY2026 Q3), Meta's certified filings stand at 317, but they represent 1,157 positions due to several multi-worker filings.

</details>

Saved traces/how-many-certified-data-scientist-positions-did-meta-file-fo.json

