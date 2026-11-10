### How many H-1B visas did Meta get approved in 2025?

**Expected:** 6294 (gold SQL on `petitions`).

H-1B Analyst right in 3/3 runs. The plain agent hit the 15-turn limit with no answer in all 3 runs; its database has only the raw LCA rows, no petitions. (The scorer marked one plain run right because its last query returned 6,243 certified LCA positions, within 1% of the gold number. That run gave no answer.)

**No tools:** Complete, official data for the number of H-1B visas approved for Meta (or any other specific employer) in **2025** is not yet fully available. 

There are two main reasons for this:

1. **Fiscal Year vs. Calendar Year:** The U.S. Citizenship and Immigration Services (USCIS) operates on a fiscal year (FY) system. FY 2025 runs from October 1, 2024, to September 30, 2025. The lottery for the FY 2025 cap was held in March 2024, and petitions were processed throughout late 2024 and into 2025. 
2. **Reporting Lag:** USCIS typically publishes employer-specific approval and denial data on its officia

<details><summary>Plain run_sql agent: 15 tool calls</summary>

**run_sql** `{"query": "DESCRIBE lca;"}`
```
{"columns": ["column_name", "column_type", "null", "key", "default", "extra"], "rows": [["case_number", "VARCHAR", "YES", null, null, null], ["case_status", "VARCHAR", "YES", null, null, null], ["received_date", "VARCHAR", "YES", null, null, null], ["decision_date", "VARCHAR", "YES", null, null, null], ["visa_class", "VARCHAR", "YES", null, null, null], ["job_title", "VARCHAR", "YES", null, null, null], ["soc_code", "VARCHAR", "YES", null, null, null], ["soc_title", "VARCHAR", "YES", null, null, null], ["full_time", "VARCHAR", "YES", null, null, null], ["begin_date", "VARCHAR", "YES", null, null, null], ["total_worker_positions", "VARCHAR", "YES", null, null, null], ["new_employment", "VARCHAR", "YES", null, null, null], ["continued_employment", "VARCHAR", "YES", null, null, null], ["change_previous_employment", "VARCHAR", "YES", null, null, null], ["new_concurrent_employment", "VARCHAR"
```

**run_sql** `{"query": "SELECT case_status, COUNT(*) FROM lca GROUP BY 1;"}`
```
{"columns": ["case_status", "count_star()"], "rows": [["Certified - Withdrawn", 87320], ["Withdrawn", 25043], ["Certified", 1433993], ["Denied", 9674]], "truncated": false}
```

**run_sql** `{"query": "SELECT visa_class, COUNT(*) FROM lca GROUP BY 1;"}`
```
{"columns": ["visa_class", "count_star()"], "rows": [["H-1B", 1556030]], "truncated": false}
```

**run_sql** `{"query": "SELECT min(decision_date), max(decision_date) FROM lca;"}`
```
{"columns": ["min(decision_date)", "max(decision_date)"], "rows": [["45201", "46203"]], "truncated": false}
```

**run_sql** `{"query": "SELECT decision_date, received_date, begin_date, employer_name FROM lca LIMIT 10;"}`
```
{"columns": ["decision_date", "received_date", "begin_date", "employer_name"], "rows": [["45838", "45838", "45898", "TRUSTEES OF THE UNIVERSITY OF PENNSYLVANIA"], ["45838", "45838", "45844", "Accenture LLP"], ["45838", "45838", "45852", "Bean Infosystems LLC"], ["45838", "45838", "45901", "INFOTECH PRISM LLC"], ["45838", "45838", "45841", "Illinois Wesleyan University"], ["45838", "45838", "45870", "University of Louisville"], ["45838", "45838", "45907", "Ernst & Young U.S. LLP"], ["45838", "45838", "45931", "TATA CONSULTANCY SERVICES LIMITED"], ["45838", "45838", "45844", "Accenture LLP"], ["45838", "45838", "45901", "Washington University"]], "truncated": false}
```

**run_sql** `{"query": "SELECT CAST('1899-12-30' AS DATE) + CAST(45838 AS INTEGER) AS date_val;"}`
```
{"columns": ["date_val"], "rows": [["2025-06-30"]], "truncated": false}
```

**run_sql** `{"query": "SELECT YEAR(CAST('1899-12-30' AS DATE) + CAST(decision_date AS INTEGER)) AS decision_year, COUNT(*) \nFROM lca \nGROUP BY 1 \nORDER BY 1;"}`
```
{"columns": ["decision_year", "count_star()"], "rows": [[2023, 96294], [2024, 554559], [2025, 557922], [2026, 347255]], "truncated": false}
```

**run_sql** `{"query": "SELECT employer_name, COUNT(*) \nFROM lca \nWHERE UPPER(employer_name) LIKE '%META %' OR UPPER(employer_name) LIKE '%META,%' OR UPPER(employer_name) = 'META' \nGROUP BY 1 \nORDER BY 2 DESC;"}`
```
{"columns": ["employer_name", "count_star()"], "rows": [["Meta Platforms, Inc", 14550], ["Meta Platforms, Inc.", 1680], ["Meta Platforms, Inc. ", 462], ["META PLATFORMS, INC.", 451], ["META PLATFORMS, INC. ", 386], ["META IT CORP", 51], ["SYNMETA LLC", 36], ["META SOFT INC", 27], ["META IT SYSTEMS LLC", 26], ["Meta Hub IT Solutions Inc", 13], ["Meta Payments Inc. (formerly known as Facebook Payments, Inc)", 10], ["Meta Hub IT Solutions Inc.", 9], ["Adukemeta LLC", 5], ["Kymeta Corporation", 4], ["Meta Soft Inc.", 3], ["Conmeta, Inc.", 3], ["Meta Info Solutions Inc", 3], ["Encore Meta World LLC", 2], ["Meta Protocol, Inc. ", 2], ["GoMeta Inc.", 2], ["Meta Protocol, Inc.", 2], ["Meta One Inc", 2], ["Artmeta LLC", 1], ["Meta Supply Chain Management Inc", 1], ["New Meta Entertainment, Inc.", 1], ["Meta Info Solutions Inc.", 1], ["Meta Tools Technologies LLC", 1], ["Meta Nau Inc.", 1], ["META
```

**run_sql** `{"query": "SELECT DISTINCT employer_name, COUNT(*) \nFROM lca \nWHERE UPPER(employer_name) LIKE 'META PLATFORMS%' \nGROUP BY 1 \nORDER BY 2 DESC;"}`
```
{"columns": ["employer_name", "count_star()"], "rows": [["Meta Platforms, Inc", 14550], ["Meta Platforms, Inc.", 1680], ["Meta Platforms, Inc. ", 462], ["META PLATFORMS, INC.", 451], ["META PLATFORMS, INC. ", 386]], "truncated": false}
```

**run_sql** `{"query": "SELECT DISTINCT employer_name, COUNT(*) \nFROM lca \nWHERE UPPER(employer_name) LIKE 'META %' \nGROUP BY 1 \nORDER BY 2 DESC \nLIMIT 30;"}`
```
{"columns": ["employer_name", "count_star()"], "rows": [["Meta Platforms, Inc", 14550], ["Meta Platforms, Inc.", 1680], ["Meta Platforms, Inc. ", 462], ["META PLATFORMS, INC.", 451], ["META PLATFORMS, INC. ", 386], ["META IT CORP", 51], ["META SOFT INC", 27], ["META IT SYSTEMS LLC", 26], ["Meta Hub IT Solutions Inc", 13], ["Meta Payments Inc. (formerly known as Facebook Payments, Inc)", 10], ["Meta Hub IT Solutions Inc.", 9], ["Meta Info Solutions Inc", 3], ["Meta Soft Inc.", 3], ["Meta Protocol, Inc. ", 2], ["Meta Protocol, Inc.", 2], ["Meta One Inc", 2], ["META ONE INC", 1], ["Meta Info Solutions Inc.", 1], ["Meta Tools Technologies LLC", 1], ["Meta Supply Chain Management Inc", 1], ["Meta Nau Inc.", 1], ["Meta Development LLC", 1]], "truncated": false}
```

**run_sql** `{"query": "SELECT total_worker_positions, COUNT(*) FROM lca GROUP BY 1 LIMIT 10;"}`
```
{"columns": ["total_worker_positions", "count_star()"], "rows": [["15", 1360], ["29", 5], ["24", 1], ["26", 5], ["1250", 4], ["38", 1], ["170", 1], ["225", 1], ["3", 9154], ["125", 28]], "truncated": false}
```

**run_sql** `{"query": "SELECT \n    YEAR(CAST('1899-12-30' AS DATE) + CAST(decision_date AS INTEGER)) AS decision_year,\n    case_status,\n    COUNT(*) AS case_count,\n    SUM(CAST(total_worker_positions AS INTEGER)) AS total_workers\nFROM lca\nWHERE UPPER(employer_name) LIKE 'META PLATFORMS%'\nGROUP BY 1, 2\nORDER BY 1, 2;"}`
```
{"columns": ["decision_year", "case_status", "case_count", "total_workers"], "rows": [[2023, "Certified", 999, 999], [2023, "Certified - Withdrawn", 4, 4], [2023, "Denied", 2, 2], [2023, "Withdrawn", 7, 7], [2024, "Certified", 6360, 6720], [2024, "Certified - Withdrawn", 186, 186], [2024, "Denied", 13, 13], [2024, "Withdrawn", 9, 9], [2025, "Certified", 5613, 7992], [2025, "Withdrawn", 1, 1], [2026, "Certified", 4335, 12567]], "truncated": false}
```

**run_sql** `{"query": "SELECT \n    YEAR(CAST('1899-12-30' AS DATE) + CAST(decision_date AS INTEGER)) AS decision_year,\n    MIN(CAST('1899-12-30' AS DATE) + CAST(decision_date AS INTEGER)) AS min_date,\n    MAX(CAST('1899-12-30' AS DATE) + CAST(decision_date AS INTEGER)) AS max_date,\n    COUNT(*) AS cnt\nFROM lca\nGROUP BY 1\nORDER BY 1;"}`
```
{"columns": ["decision_year", "min_date", "max_date", "cnt"], "rows": [[2023, "2023-10-02", "2023-12-31", 96294], [2024, "2024-01-01", "2024-12-31", 554559], [2025, "2025-01-01", "2025-12-31", 557922], [2026, "2026-01-01", "2026-06-30", 347255]], "truncated": false}
```

**run_sql** `{"query": "SELECT \n    YEAR(CAST('1899-12-30' AS DATE) + CAST(begin_date AS INTEGER)) AS begin_year,\n    MIN(CAST('1899-12-30' AS DATE) + CAST(begin_date AS INTEGER)) AS min_date,\n    MAX(CAST('1899-12-30' AS DATE) + CAST(begin_date AS INTEGER)) AS max_date,\n    COUNT(*) AS cnt\nFROM lca\nGROUP BY 1\nORDER BY 1;"}`
```
{"columns": ["begin_year", "min_date", "max_date", "cnt"], "rows": [[2019, "2019-10-15", "2019-12-30", 28], [2020, "2020-01-01", "2020-12-31", 1420], [2021, "2021-01-01", "2021-12-31", 6065], [2022, "2022-01-01", "2022-12-31", 12051], [2023, "2023-01-01", "2023-12-31", 71920], [2024, "2024-01-01", "2024-12-31", 516856], [2025, "2025-01-01", "2025-12-31", 559238], [2026, "2026-01-01", "2026-12-30", 388452]], "truncated": false}
```

**run_sql** `{"query": "SELECT DISTINCT source_file FROM lca;"}`
```
{"columns": ["source_file"], "rows": [["LCA_Disclosure_Data_FY2025_Q2.xlsx"], ["LCA_Disclosure_Data_FY2025_Q4.xlsx"], ["LCA_Disclosure_Data_FY2024_Q4.xlsx"], ["LCA_Disclosure_Data_FY2024_Q2.xlsx"], ["LCA_Disclosure_Data_FY2026_Q3.xlsx"], ["LCA_Disclosure_Data_FY2025_Q3.xlsx"], ["LCA_Disclosure_Data_FY2024_Q3.xlsx"], ["LCA_Disclosure_Data_FY2025_Q1.xlsx"], ["LCA_Disclosure_Data_FY2024_Q1.xlsx"]], "truncated": false}
```

**Answer:** FAILED: MaxTurnsExceeded: Max turns (15) exceeded

</details>

<details><summary>H-1B Analyst: 4 tool calls</summary>

**read_mappings** `{}`
```
{"as_of": "FY2026 Q3", "tables": {"lca": {"description": "One row per H-1B Labor Condition Application (LCA) filed with the Department of Labor, FY2024 Q1 to FY2026 Q3, amendments deduplicated. An LCA is a filing an employer must make BEFORE an H-1B petition; it is not an approval or a visa.", "columns": [{"name": "case_number", "type": "VARCHAR", "description": "DOL case number, unique per row."}, {"name": "case_status", "type": "VARCHAR", "description": "DOL decision. Use 'CERTIFIED' for filings employers could actually use.", "is_enum": true}, {"name": "fiscal_year", "type": "INTEGER", "description": "US federal fiscal year of the decision (Oct 1 - Sep 30). FY2026 = Oct 2025 - Sep 2026.", "is_enum": true}, {"name": "quarter", "type": "INTEGER", "description": "Fiscal quarter 1-4 (Q1 = Oct-Dec).", "is_enum": true}, {"name": "received_date", "type": "DATE", "description": "Date DOL rece
```

**find_employer** `{"name": "Meta"}`
```
{"matches": [{"employer_id": 7, "employer": "Meta", "employer_type": "big_tech", "filings": 17537, "match_score": 100, "name_variants_merged": 7, "sample_variants": ["Meta Platforms, Inc", "Meta Platforms, Inc.", "META PLATFORMS, INC.", "WhatsApp"]}, {"employer_id": 3726, "employer": "Meta IT", "employer_type": "other", "filings": 51, "match_score": 94, "name_variants_merged": 1, "sample_variants": ["META IT CORP"]}, {"employer_id": 6240, "employer": "Meta Soft", "employer_type": "other", "filings": 30, "match_score": 94, "name_variants_merged": 2, "sample_variants": ["META SOFT INC", "Meta Soft Inc."]}, {"employer_id": 7107, "employer": "Meta IT Systems", "employer_type": "other", "filings": 26, "match_score": 94, "name_variants_merged": 1, "sample_variants": ["META IT SYSTEMS LLC"]}, {"employer_id": 8141, "employer": "Meta Hub IT Solutions", "employer_type": "other", "filings": 22, "ma
```

**run_sql** `{"query": "SELECT fiscal_year, approved, new_employment_approved, continuation_approved, change_employer_approved, denied, round(100.0 * approved / nullif(approved + denied, 0), 1) as approval_pct FROM petitions WHERE employer_id = 7 ORDER BY fiscal_year"}`
```
{"columns": ["fiscal_year", "approved", "new_employment_approved", "continuation_approved", "change_employer_approved", "denied", "approval_pct"], "rows": [[2024, 4848, 918, 2152, 1250, 29, 99.4], [2025, 6294, 1554, 122, 1975, 59, 99.1], [2026, 3999, 887, 11, 898, 73, 98.2]], "row_count": 3, "truncated": false}
```

**make_chart** `{"mark": "bar", "color": null, "y": "approved", "title": "Meta Approved H-1B Petitions by Fiscal Year", "x": "fiscal_year"}`
```
{"ok": true, "note": "Chart shown to the user. Do not describe the chart's styling."}
```

**Answer:** In fiscal year 2025, Meta had 6,294 H-1B petitions approved by USCIS (note that approved petitions represent USCIS decisions, not actual visas issued by the State Department or lottery wins).

* **New hires:** 1,554 approved petitions were for new employment (mostly first-time, lottery-selected hires).
* **Transfers and extensions:** The remaining approvals included 1,975 transfers from other companies and 122 continuation extensions.
* **Approval rate:** Meta achieved a 99.1% approval rate in FY2025, with only 59 petitions denied.
* **Yearly context:** Approvals rose from 4,848 in FY2024, before declining to 3,999 in FY2026.

</details>
