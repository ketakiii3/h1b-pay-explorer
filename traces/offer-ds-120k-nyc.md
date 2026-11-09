loaded h1b.duckdb: 1,532,089 filings, 107,638 employers
15:53:32 - LiteLLM:WARNING: vertex_and_google_ai_studio_gemini.py:1265 - DeprecationWarning: `temperature`, `top_p`, and `top_k` continue to function for Gemini 3+ (gemini-3.5-flash) but are planned for removal in a future release. Move sampling guidance into the `system` instructions instead.
run 1: {'plain_ok': False, 'agent_ok': True}
run 2: {'plain_ok': False, 'agent_ok': True}
run 3: {'plain_ok': False, 'agent_ok': True}

### How many lottery entries would a $120,000 data scientist offer in NYC get?

**Expected:** 2 (gold SQL on `lca`).

Plain agent right in 0/3 runs; H-1B Analyst right in 3/3 runs.

**No tools:** In New York City, the term "lottery" almost always refers to the **NYC Housing Connect** affordable housing lottery. 

With a **$120,000 salary** as a single applicant, you fall into the **"Middle Income"** bracket, which is one of the most active and abundant brackets in the NYC housing lottery system.

Here is a breakdown of how many lotteries you can apply for, what your options look like, and your realistic chances of winning.

---

### 1. How many lotteries can you apply to?
**There is no limit.** You can apply to **every single building** that has units matching your income bracket and h

<details><summary>Plain run_sql agent: 7 tool calls</summary>

**run_sql** `{"query": "DESCRIBE lca;"}`
```
{"columns": ["column_name", "column_type", "null", "key", "default", "extra"], "rows": [["case_number", "VARCHAR", "YES", null, null, null], ["case_status", "VARCHAR", "YES", null, null, null], ["received_date", "VARCHAR", "YES", null, null, null], ["decision_date", "VARCHAR", "YES", null, null, null], ["visa_class", "VARCHAR", "YES", null, null, null], ["job_title", "VARCHAR", "YES", null, null, null], ["soc_code", "VARCHAR", "YES", null, null, null], ["soc_title", "VARCHAR", "YES", null, null, null], ["full_time", "VARCHAR", "YES", null, null, null], ["begin_date", "VARCHAR", "YES", null, null, null], ["total_worker_positions", "VARCHAR", "YES", null, null, null], ["new_employment", "VARCHAR", "YES", null, null, null], ["continued_employment", "VARCHAR", "YES", null, null, null], ["change_previous_employment", "VARCHAR", "YES", null, null, null], ["new_concurrent_employment", "VARCHAR"
```

**run_sql** `{"query": "SELECT * FROM lca WHERE LOWER(job_title) LIKE '%data scientist%' AND LOWER(worksite_city) LIKE '%new york%' LIMIT 10;"}`
```
{"columns": ["case_number", "case_status", "received_date", "decision_date", "visa_class", "job_title", "soc_code", "soc_title", "full_time", "begin_date", "total_worker_positions", "new_employment", "continued_employment", "change_previous_employment", "new_concurrent_employment", "change_employer", "amended_petition", "employer_name", "employer_city", "employer_state", "naics_code", "worksite_city", "worksite_county", "worksite_state", "worksite_zip", "wage_from", "wage_to", "wage_unit", "pw", "pw_unit", "pw_wage_level", "h1b_dependent", "willful_violator", "total_worksite_locations", "source_file"], "rows": [["I-200-24110-905949", "Certified", "45401", "45408", "H-1B", "Senior Data Scientist", "15-2051.00", "Data Scientists", "Y", "45566", "1", "0", "0", "1", "0", "0", "0", "THE BOSTON CONSULTING GROUP, INC. ", "BOSTON", "MA", "541611", " New York", "NEW YORK", "NY", "10001", "161500"
```

**run_sql** `{"query": "SELECT pw_wage_level, MIN(CAST(pw AS DOUBLE)) as min_pw, MAX(CAST(pw AS DOUBLE)) as max_pw, COUNT(*) as count \nFROM lca \nWHERE soc_code = '15-2051.00' AND TRIM(UPPER(worksite_city)) = 'NEW YORK' AND worksite_state = 'NY' AND pw_unit = 'Year'\nGROUP BY pw_wage_level;"}`
```
{"columns": ["pw_wage_level", "min_pw", "max_pw", "count"], "rows": [["IV", 103293.0, 179088.0, 871], [null, 55546.11, 198550.0, 200], ["III", 90272.0, 141170.0, 943], ["I", 50378.0, 82763.0, 647], ["II", 77272.0, 111996.0, 1541]], "truncated": false}
```

**run_sql** `{"query": "SELECT pw_wage_level, CAST(pw AS DOUBLE) as pw_val, COUNT(*) as cnt\nFROM lca \nWHERE soc_code = '15-2051.00' AND TRIM(UPPER(worksite_city)) = 'NEW YORK' AND worksite_state = 'NY' AND pw_unit = 'Year'\nGROUP BY pw_wage_level, pw_val\nORDER BY cnt DESC\nLIMIT 30;"}`
```
{"columns": ["pw_wage_level", "pw_val", "cnt"], "rows": [["II", 109491.0, 569], ["II", 111966.0, 537], ["IV", 169541.0, 413], ["III", 139506.0, 411], ["II", 108306.0, 370], ["III", 141170.0, 311], ["I", 79456.0, 273], ["IV", 170373.0, 268], ["III", 135782.0, 202], ["I", 82763.0, 180], ["IV", 163238.0, 175], ["I", 80850.0, 158], ["II", 77272.0, 24], ["II", 78062.0, 16], [null, 150433.0, 14], [null, 97443.0, 12], ["II", 81224.0, 12], ["I", 64251.0, 11], ["II", 102482.0, 11], [null, 92825.0, 9], [null, 163524.0, 9], ["IV", 153525.0, 8], ["I", 76960.0, 8], ["III", 128003.0, 8], [null, 96786.0, 7], ["I", 67787.0, 7], [null, 113243.0, 6], [null, 123033.0, 6], [null, 95595.0, 6], ["I", 63710.0, 6]], "truncated": false}
```

**run_sql** `{"query": "SHOW TABLES;"}`
```
{"columns": ["name"], "rows": [["lca"]], "truncated": false}
```

**run_sql** `{"query": "SELECT DISTINCT pw_wage_level, pw, source_file\nFROM lca \nWHERE soc_code = '15-2051.00' AND TRIM(UPPER(worksite_city)) = 'NEW YORK' AND worksite_state = 'NY' AND pw_unit = 'Year'\nORDER BY pw_wage_level, CAST(pw AS DOUBLE);"}`
```
{"columns": ["pw_wage_level", "pw", "source_file"], "rows": [["I", "50378", "LCA_Disclosure_Data_FY2024_Q2.xlsx"], ["I", "54974", "LCA_Disclosure_Data_FY2025_Q3.xlsx"], ["I", "63710", "LCA_Disclosure_Data_FY2025_Q4.xlsx"], ["I", "63710", "LCA_Disclosure_Data_FY2024_Q2.xlsx"], ["I", "63710", "LCA_Disclosure_Data_FY2024_Q1.xlsx"], ["I", "63710", "LCA_Disclosure_Data_FY2024_Q3.xlsx"], ["I", "64251", "LCA_Disclosure_Data_FY2025_Q4.xlsx"], ["I", "64251", "LCA_Disclosure_Data_FY2026_Q3.xlsx"], ["I", "65146", "LCA_Disclosure_Data_FY2025_Q3.xlsx"], ["I", "65146", "LCA_Disclosure_Data_FY2024_Q4.xlsx"], ["I", "67787", "LCA_Disclosure_Data_FY2025_Q1.xlsx"], ["I", "67787", "LCA_Disclosure_Data_FY2025_Q2.xlsx"], ["I", "67787", "LCA_Disclosure_Data_FY2025_Q3.xlsx"], ["I", "67787", "LCA_Disclosure_Data_FY2024_Q4.xlsx"], ["I", "67787", "LCA_Disclosure_Data_FY2025_Q4.xlsx"], ["I", "76960", "LCA_Disclosur
```

**run_sql** `{"query": "SELECT source_file, pw_wage_level, CAST(pw AS DOUBLE) as pw_val, COUNT(*) as cnt\nFROM lca \nWHERE soc_code = '15-2051.00' AND TRIM(UPPER(worksite_city)) = 'NEW YORK' AND worksite_state = 'NY' AND pw_unit = 'Year'\nGROUP BY source_file, pw_wage_level, pw_val\nORDER BY source_file DESC, pw_wage_level, pw_val;"}`
```
{"columns": ["source_file", "pw_wage_level", "pw_val", "cnt"], "rows": [["LCA_Disclosure_Data_FY2026_Q3.xlsx", "I", 64251.0, 9], ["LCA_Disclosure_Data_FY2026_Q3.xlsx", "I", 76960.0, 2], ["LCA_Disclosure_Data_FY2026_Q3.xlsx", "I", 79456.0, 262], ["LCA_Disclosure_Data_FY2026_Q3.xlsx", "I", 80850.0, 3], ["LCA_Disclosure_Data_FY2026_Q3.xlsx", "I", 82763.0, 5], ["LCA_Disclosure_Data_FY2026_Q3.xlsx", "II", 77272.0, 18], ["LCA_Disclosure_Data_FY2026_Q3.xlsx", "II", 94910.0, 1], ["LCA_Disclosure_Data_FY2026_Q3.xlsx", "II", 102482.0, 1], ["LCA_Disclosure_Data_FY2026_Q3.xlsx", "II", 108306.0, 6], ["LCA_Disclosure_Data_FY2026_Q3.xlsx", "II", 109491.0, 495], ["LCA_Disclosure_Data_FY2026_Q3.xlsx", "II", 111966.0, 10], ["LCA_Disclosure_Data_FY2026_Q3.xlsx", "III", 90272.0, 4], ["LCA_Disclosure_Data_FY2026_Q3.xlsx", "III", 128003.0, 2], ["LCA_Disclosure_Data_FY2026_Q3.xlsx", "III", 135782.0, 4], ["LCA_
```

**Answer:** Under the current H-1B regulations and proposed selection frameworks, here is how a **$120,000 Data Scientist offer in New York City** is treated:

### 1. In the Actual H-1B Lottery (Current "Beneficiary-Centric" System)
Under the current beneficiary-centric selection process implemented in 2024 (for the FY 2025 cap and onward), every applicant receives **exactly one entry** in the lottery, regardless of:
* Offered salary ($120,000)
* Job title (Data Scientist)
* Geographic location (New York City)

Multiple registrations submitted by different employers for the same person are consolidated into a single entry based on passport/identification information to ensure a fair 1-candidate-to-1-entry ratio.

---

### 2. What Prevailing Wage Level Does a $120,000 Offer Map To?
If we analyze the LCA data for **Data Scientists** (`SOC 15-2051.00`) in **New York, NY**, the standard prevailing wage thresholds are:

| Wage Level | Prevailing Wage (FY 2024) | Prevailing Wage (FY 2025/2026) |
| :--- | :--- | :--- |
| **Level I (Entry)** | ~$80,850 | **$79,456 - $82,763** |
| **Level II (Qualified)** | ~$108,306 | **$109,491 - $111,966** |
| **Level III (Experienced)** | ~$135,782 | **$139,506 - $141,170** |
| **Level IV (Fully Competent)** | ~$163,238 | **$169,541 - $170,373** |

* **Your Offer:** $120,000
* **Classification:** Since $120,000 is higher than the Level II requirement (~$109,491) but lower than the Level III requirement (~$139,506), this offer would be officially categorized under a **Level II prevailing wage level**.

---

### 3. Under the Proposed "Wage-Level Based" Selection System
The Trump administration previously proposed (but courts subsequently vacated) a wage-level-prioritized selection process. If a similar wage-based selection framework were ever enacted:
* **Level IV & Level III** offers would get first priority (typically historical simulations show a 100% selection rate).
* **Level II** offers (like this $120,000 one) would only be selected if there are leftover cap spaces after Levels IV and III are fully exhausted. In highly competitive years, simulations show Level II selection rates range from **0% to 20%**, and Level I selection rates are **0%**.

</details>

<details><summary>H-1B Analyst: 6 tool calls</summary>

**read_mappings** `{}`
```
{"as_of": "FY2026 Q3", "tables": {"lca": {"description": "One row per H-1B Labor Condition Application (LCA) filed with the Department of Labor, FY2024 Q1 to FY2026 Q3, amendments deduplicated. An LCA is a filing an employer must make BEFORE an H-1B petition; it is not an approval or a visa.", "columns": [{"name": "case_number", "type": "VARCHAR", "description": "DOL case number, unique per row."}, {"name": "case_status", "type": "VARCHAR", "description": "DOL decision. Use 'CERTIFIED' for filings employers could actually use.", "is_enum": true}, {"name": "fiscal_year", "type": "INTEGER", "description": "US federal fiscal year of the decision (Oct 1 - Sep 30). FY2026 = Oct 2025 - Sep 2026.", "is_enum": true}, {"name": "quarter", "type": "INTEGER", "description": "Fiscal quarter 1-4 (Q1 = Oct-Dec).", "is_enum": true}, {"name": "received_date", "type": "DATE", "description": "Date DOL rece
```

**find_location** `{"place": "NYC"}`
```
{"area_code": "35620", "metro_name": "New York-Newark-Jersey City, NY-NJ", "matched_by": "alias"}
```

**find_role** `{"text": "data scientist"}`
```
{"role_family": "Data Scientist", "matched_by": "rules", "main_soc_codes": [{"soc_code": "15-2051", "soc_title": "Data Scientists", "filings": 38958}, {"soc_code": "15-2041", "soc_title": "Statisticians", "filings": 6341}, {"soc_code": "15-2031", "soc_title": "Operations Research Analysts", "filings": 969}], "example_titles": ["data scientist", "senior data scientist", "data scientist ii", "data scientist iii", "data science", "machine learning"]}
```

**wage_level** `{"location": "NYC", "soc_code": "15-2051", "role": "data scientist", "salary": 120000}`
```
{"salary": 120000.0, "role_family": "Data Scientist", "soc_code": "15-2051", "soc_title": "Data Scientists", "area_code": "35620", "metro_name": "New York-Newark-Jersey City, NY-NJ", "wage_level": 2, "lottery_entries": 2, "thresholds": {"level_1": 87256.0, "level_2": 115835.0, "level_3": 144414.0, "level_4": 172994.0}, "raise_needed_for_next_level": 24414, "peer_filings_fy2025_on": 5700, "salary_percentile_among_peer_filings": 29.4, "peer_median_offer": 145140.5, "wage_year": "OFLC 2026-27 (Jul 2026 - Jun 2027)", "approximate": false, "note": "Level 2 = 2 lottery entries under the wage-weighted lottery."}
```

**run_sql** `{"query": "SELECT \n    offer_lottery_entries, \n    count(*) AS filings, \n    median(wage_annual_from) AS median_pay,\n    round(100.0 * count(*) / sum(count(*)) OVER (), 1) AS pct\nFROM lca \nWHERE area_code = '35620' \n  AND role_family = 'Data Scientist' \n  AND case_status = 'CERTIFIED' \n  AND wage_flag = 'ok'\nGROUP BY 1 \nORDER BY 1\n"}`
```
{"columns": ["offer_lottery_entries", "filings", "median_pay", "pct"], "rows": [[0, 678, 81172.0, 8.2], [1, 1640, 109491.0, 19.8], [2, 1924, 135000.0, 23.2], [3, 2026, 160000.0, 24.5], [4, 2017, 195000.0, 24.3], [null, 1, 139626.0, 0.0]], "row_count": 6, "truncated": false}
```

**make_chart** `{"mark": "bar", "y": "filings", "color": null, "title": "NYC Data Scientist Filings by Lottery Entries (FY2024-FY2026 Q3)", "x": "offer_lottery_entries"}`
```
{"ok": true, "note": "Chart shown to the user. Do not describe the chart's styling."}
```

**Answer:** A $120,000 data scientist offer in the New York metro area would get **2 lottery entries** in the wage-weighted H-1B lottery.

* **Wage Tier:** This $120k salary falls into Level II, which requires a minimum of $116k for Data Scientists in NYC (SOC 15-2051) under the 2026–27 wage guidelines. A raise of $24k is needed to reach Level III (3 entries) at $144k.
* **Local Distribution:** Out of 8,286 certified Data Scientist filings in the NYC metro from FY2024 to FY2026 Q3, 23.2% (1,924 filings) qualified for 2 entries, with a median offered pay of $135k.
* **Peer Comparison:** This offer sits at the 29th percentile of peer offers. The overall median pay for these NYC filings is $145k, and 19.8% of filings (1,640) qualified for just 1 entry (Level I, median $109k).

</details>

Saved traces/how-many-lottery-entries-would-a-120-000-data-scientist-offe.json

