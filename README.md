# H-1B Pay Explorer

Who sponsors your role, what they actually offer, and what your offer is worth in the new wage-weighted H-1B lottery, answered from every H-1B filing the Department of Labor published from FY2024 to FY2026 Q3.

**Live app:** https://h1b-pay-explorer-314308831335.us-east1.run.app

**Team:** Ketaki Dabade (kvd2112) and Anamika Mishra (akm2259) · **Path:** Text2SQL

<!-- TODO: screenshot or GIF of a chart answer -->

## Why we built this

> TODO (Ketaki, in your own words, 2-3 sentences): why this matters to you as an international student. For example: what you didn't know when you were applying, and what changed when the lottery became wage-weighted in 2026.

Since February 27, 2026, the H-1B lottery is no longer one ticket per person. A registration is entered once per wage level of the offered salary: Level I gets 1 entry and Level IV gets 4. So two offers for the same job can have very different odds, and the level depends on where the salary sits in an official table for that occupation and metro. Students hear numbers like "Google pays new grads X" or "staffing firms file everyone at Level I", but almost nobody checks the filings. Every employer has to file a public Labor Condition Application (LCA) before an H-1B petition, with the job, worksite, offered wage and wage level. That data exists, but it is millions of messy rows in government Excel files, and a general-purpose model doesn't know it.

## Who it's for

- F-1 and OPT students deciding where to apply: who actually sponsors my role in my city, and at what level?
- Anyone holding an H-1B offer: what wage level is it, how many lottery entries does it get, and how does it compare with real filings?
- Career advisors and student groups who want numbers instead of rumors.

## How to use it

1. **Check an offer** (left panel): type a salary, a role and a city. You get the wage level, the lottery entries, the four official thresholds on a ladder, the raise needed to reach the next level, and where your salary sits among real filings for that role and metro. This runs instantly and calls no model.
2. **Ask a question** (right panel): click one of the example questions or type your own. The agent answers in a few sentences with a chart and the table behind it. You can sort the table and download it as a CSV.
3. **Open "Show work"** under any answer to see each tool call: the names it resolved, the exact SQL and what came back.

## Sample queries for grading

| # | Question | Expected answer | Source |
| --- | --- | --- | --- |
| 1 | What was the median offered salary for software engineers at Google in the New York City area in FY2025? | **$186,000**, across 465 certified filings with valid wages | `lca` table in `h1b.duckdb` (GCS): `employer = 'Google'`, `role_family = 'Software Engineer'`, `area_code = '35620'`, `fiscal_year = 2025`, certified, `wage_flag = 'ok'` |
| 2 | How many lottery entries would a $175,000 machine learning engineer offer in San Jose get? | **1 entry (Level I)** if filed as Software Developer (SOC 15-1252, the most common code): Level I is $152,797 and Level II $187,075. **2 entries** if filed as Data Scientist (SOC 15-2051, Level II from $169k). The agent explains both. | `wage_levels` table (OFLC `ALC_Export.csv`, wage year 2026-27) and `lca` for which codes employers use |
| 3 | How many H-1B visas did Meta get approved in 2025? | A clear "the data can't answer this": LCAs are filings, not approvals or visas. No SQL is run, and the agent offers Meta's certified LCAs instead. | `limitations` in `data/mappings.json` |

**Same model with no tools and no system prompt, next to our agent** (`uv run compare.py`, traces in `traces/`):

| # | No tools, no system prompt | H-1B Pay Explorer |
| --- | --- | --- |
| 1 | Doesn't know FY2025 data. It guesses from "late 2024 and early 2025 LCA filings" that the median is "approximately **$190,000 to $210,000**", then quotes crowdsourced levels. | **$186,000**, from 465 certified FY2025 filings in the New York-Newark-Jersey City area. |
| 2 | Reads "lottery entries" as startup stock options first. For the H-1B it says "**Exactly 1 entry**", which was right before the 2026 wage-weighted rule and is wrong now. | **1 or 2 entries depending on the SOC code**: Level I as a Software Developer ($12k short of Level II), Level II as a Data Scientist, with 1,551 and 899 San Jose filings under each code. |
| 3 | Says it has no access to USCIS data and points to the USCIS Employer Data Hub. | Says LCAs stop before the petition, so approvals aren't in the data, runs no SQL, and offers Meta's certified LCAs for FY2025. |

## Plain `run_sql` agent vs this agent

`baseline.py` is the plain agent: the same Gemini model (`gemini-3.5-flash`), one `run_sql` tool over the H-1B rows exactly as DOL ships them, and a one-line prompt (the `nyc-311-agent` shape). `compare.py` ran five candidate questions 3 times each against both agents. We kept only failures that repeated. Full traces: `traces/*.json`.

| Question | Gold | Plain agent right | Our agent right |
| --- | --- | --- | --- |
| Meta certified data scientist positions, FY2025 | 689 | **0/3** | 3/3 |
| Lottery entries for a $120k data scientist offer in NYC | 2 | **0/3** | 3/3 |
| Top 5 data scientist sponsors, FY2025 | Goldman Sachs, Amazon, Microsoft, Meta, Walmart | 1/3 | 3/3 |
| Top 5 NYC ML engineer sponsors, FY2025 | Bloomberg, Yahoo, Meta, JPMorgan Chase, Pinterest | 1/3 | 3/3 |
| Median Google software engineer offer, NYC, FY2025 | $186,000 | 2/3 | 3/3 |

### Failure 1: "How many certified data scientist positions did Meta file for in FY2025?"

**Expected: 689** (`SELECT sum(total_worker_positions) FROM lca WHERE employer = 'Meta' AND role_family = 'Data Scientist' AND fiscal_year = 2025 AND case_status = 'CERTIFIED'`).

**Why the plain agent failed:** it spent its whole step budget fighting the raw data. Dates are Excel serial numbers (it had to work out that `45566` is 2024-10-01), `ILIKE '%Meta%'` also matches Kennametal and Metaforge IT, Meta files under several spellings, and "data scientist" is either a free-text title or a SOC code that also covers Data Engineers. Run 1 answered 836 positions; runs 2 and 3 hit the 15-turn limit with no answer. Ours resolved Meta, the role and the year with lookups and ran one query.

<details><summary>Plain agent, run 1: 14 tool calls, answered 836</summary>

1. `run_sql`
   ```sql
   DESCRIBE lca;
   ```
   → `{"columns": ["column_name", "column_type", "null", "key", "default", "extra"], "rows": [["case_number", "VARCHAR", "YES", null, null, null], ["case_status", "VARCHAR", "YES", null, null, null], ["received_date", "VARCHAR…`
2. `run_sql`
   ```sql
   SELECT DISTINCT source_file FROM lca LIMIT 100;
   ```
   → `{"columns": ["source_file"], "rows": [["LCA_Disclosure_Data_FY2024_Q3.xlsx"], ["LCA_Disclosure_Data_FY2024_Q4.xlsx"], ["LCA_Disclosure_Data_FY2025_Q1.xlsx"], ["LCA_Disclosure_Data_FY2025_Q4.xlsx"], ["LCA_Disclosure_Data_…`
3. `run_sql`
   ```sql
   SELECT DISTINCT case_status FROM lca;
   ```
   → `{"columns": ["case_status"], "rows": [["Denied"], ["Certified"], ["Certified - Withdrawn"], ["Withdrawn"]], "truncated": false}`
4. `run_sql`
   ```sql
   SELECT DISTINCT employer_name FROM lca WHERE employer_name ILIKE '%Meta%' LIMIT 100;
   ```
   → `{"columns": ["employer_name"], "rows": [["Meta Platforms, Inc"], ["IQA Metal, Inc."], ["META IT CORP"], ["Kennametal, Inc."], ["Metafindsolutins Inc"], ["Prime Architectural Metal and Glass Inc"], ["Meta Platforms, Inc."…`
5. `run_sql`
   ```sql
   SELECT DISTINCT job_title, soc_code, soc_title
FROM lca
WHERE employer_name ILIKE 'Meta Platforms, Inc%'
  AND (job_title ILIKE '%Data Scientist%' OR soc_title ILIKE '%Data Scientist%')
LIMIT 100;
   ```
   → `{"columns": ["job_title", "soc_code", "soc_title"], "rows": [["Data Science Manager", "15-2051.00", "Data Scientists"], ["Data Scientist", "15-2051.00", "Data Scientists"], ["Data Scientist", "15-2041.00", "Statisticians…`
6. `run_sql`
   ```sql
   SELECT DISTINCT total_worker_positions FROM lca WHERE employer_name ILIKE 'Meta Platforms, Inc%' LIMIT 10;
   ```
   → `{"columns": ["total_worker_positions"], "rows": [["1"], ["25"], ["12"]], "truncated": false}`
7. `run_sql`
   ```sql
   SELECT
  case_status,
  COUNT(*) as num_applications,
  SUM(CAST(total_worker_positions AS INT)) as sum_positions
FROM lca
WHERE employer_name ILIKE 'Meta Platforms, Inc%'
  AND source_file LIKE '%FY2025%'
  AND (job_title ILIKE '%Data Scientist%' OR soc_title ILIKE '%Data Scientists%')
GROUP BY case_status;
   ```
   → `{"columns": ["case_status", "num_applications", "sum_positions"], "rows": [["Certified", 572, 836]], "truncated": false}`
8. `run_sql`
   ```sql
   SELECT
  COUNT(CASE WHEN job_title ILIKE 'Data Scientist' THEN 1 END) as app_exact_job,
  SUM(CASE WHEN job_title ILIKE 'Data Scientist' THEN CAST(total_worker_positions AS INT) ELSE 0 END) as pos_exact_job,
  
  COUNT(CASE WHEN job_title ILIKE '%Data Scientist%' THEN 1 END) as app_contains_job,
  SUM(CASE WHEN job_title ILIKE '%Data Scientist%' THEN CAST(total_worker_positions AS INT) ELSE 0 END) as pos_contains_job,
  
  COUNT(CASE WHEN soc_title ILIKE '%Data Scientist%' THEN 1 END) as app_soc,
  SUM(CASE WHEN soc_title ILIKE '%Data Scientist%' THEN CAST(total_worker_positions AS INT) ELSE 0 END) as pos_soc,
  
  COUNT(CASE WHEN soc_code = '15-2051.00' THEN 1 END) as app_soc_code,
  SUM(CA
   ```
   → `{"columns": ["app_exact_job", "pos_exact_job", "app_contains_job", "pos_contains_job", "app_soc", "pos_soc", "app_soc_code", "pos_soc_code"], "rows": [[268, 532, 338, 602, 451, 715, 451, 715]], "truncated": false}`
9. `run_sql`
   ```sql
   SELECT DISTINCT soc_code, soc_title
FROM lca
WHERE employer_name ILIKE 'Meta Platforms, Inc%'
  AND source_file LIKE '%FY2025%'
  AND soc_title ILIKE '%Data Scientist%';
   ```
   → `{"columns": ["soc_code", "soc_title"], "rows": [["15-2051.00", "Data Scientists"]], "truncated": false}`
10. `run_sql`
   ```sql
   SELECT DISTINCT employer_name, COUNT(*) as count
FROM lca
WHERE employer_name ILIKE '%Meta%'
  AND source_file LIKE '%FY2025%'
  AND (job_title ILIKE '%Data Scientist%' OR soc_title ILIKE '%Data Scientists%')
GROUP BY employer_name;
   ```
   → `{"columns": ["employer_name", "count"], "rows": [["Meta Platforms, Inc", 569], ["MetaMetrics, Inc.", 2], ["Metaforge IT Solutions", 1], ["GoMeta Inc.", 2], ["Metallurg, Inc.", 1], ["META SOFT INC", 3], ["MetaSource, LLC"…`
11. `run_sql`
   ```sql
   SELECT case_status, COUNT(*) as count, SUM(CAST(total_worker_positions AS INT)) as positions
FROM lca
WHERE employer_name ILIKE 'Meta Platforms, Inc%'
  AND source_file LIKE '%FY2025%'
  AND (job_title ILIKE '%Data Scientist%' OR soc_title ILIKE '%Data Scientists%')
GROUP BY case_status;
   ```
   → `{"columns": ["case_status", "count", "positions"], "rows": [["Certified", 572, 836]], "truncated": false}`
12. `run_sql`
   ```sql
   SELECT case_status, COUNT(*), SUM(CAST(total_worker_positions AS INT)) as positions
FROM lca
WHERE employer_name ILIKE 'Meta Platforms, Inc%'
  AND source_file LIKE '%FY2025%'
GROUP BY case_status;
   ```
   → `{"columns": ["case_status", "count_star()", "positions"], "rows": [["Certified - Withdrawn", 1, 1], ["Certified", 6418, 8917], ["Denied", 1, 1]], "truncated": false}`
13. `run_sql`
   ```sql
   SELECT
  job_title,
  soc_code,
  soc_title,
  COUNT(*) as apps,
  SUM(CAST(total_worker_positions AS INT)) as positions
FROM lca
WHERE employer_name ILIKE 'Meta Platforms, Inc%'
  AND source_file LIKE '%FY2025%'
  AND case_status = 'Certified'
  AND (job_title ILIKE '%Data Scientist%' OR soc_title ILIKE '%Data Scientists%')
GROUP BY job_title, soc_code, soc_title
ORDER BY positions DESC, apps DESC;
   ```
   → `{"columns": ["job_title", "soc_code", "soc_title", "apps", "positions"], "rows": [["Data Scientist", "15-2051.00", "Data Scientists", 178, 442], ["Data Engineer", "15-2051.00", "Data Scientists", 121, 121], ["Software En…`
14. `run_sql`
   ```sql
   SELECT DISTINCT job_title, COUNT(*)
FROM lca
WHERE employer_name ILIKE 'Meta Platforms, Inc%'
  AND source_file LIKE '%FY2025%'
  AND case_status = 'Certified'
  AND job_title ILIKE 'Data Scientist'
GROUP BY job_title;
   ```
   → `{"columns": ["job_title", "count_star()"], "rows": [["Data Scientist", 267], ["Data scientist", 1]], "truncated": false}`

**Answer:** In FY2025, the number of certified data scientist positions Meta filed for depends on how "Data Scientist" is defined (by exact job title, broader job title variations, or the official SOC occupation code). 

Here is the exact breakdown for **Meta Platforms, Inc.** (the primary filing entity) in the FY2025 LCA disclosure data:

### 1. By Job Title
* **Exact Job Title ("Data Scientist"):** 
  * **Certified Applications:** 268
  * **Total Certified Positions:** **532**
* **Any Job Title containing "Data Scientist"** *(includes "Senior Data Scientist", "Data Scientist, Analytics", "Research Data Scientist", etc.)*:
  * **Certified Applications:** 338
  * **Total Certified Positions:** **602**

### 2. By SOC Occupational Classification ("Data Scientists" - SOC Code 15-2051.00)
Under this official Department of Labor category, employers can classify internal titles (such as Software Engineer 

</details>

<details><summary>Plain agent, run 2: 15 tool calls, ran out of turns</summary>

1. `run_sql`
   ```sql
   DESCRIBE lca;
   ```
   → `{"columns": ["column_name", "column_type", "null", "key", "default", "extra"], "rows": [["case_number", "VARCHAR", "YES", null, null, null], ["case_status", "VARCHAR", "YES", null, null, null], ["received_date", "VARCHAR…`
2. `run_sql`
   ```sql
   SELECT DISTINCT employer_name, count(*) 
FROM lca 
WHERE employer_name ILIKE '%meta%' 
GROUP BY 1 
ORDER BY 2 DESC 
LIMIT 20;
   ```
   → `{"columns": ["employer_name", "count_star()"], "rows": [["Meta Platforms, Inc", 14550], ["Meta Platforms, Inc.", 1680], ["Meta Platforms, Inc. ", 462], ["META PLATFORMS, INC.", 451], ["META PLATFORMS, INC. ", 386], ["MET…`
3. `run_sql`
   ```sql
   SELECT DISTINCT source_file FROM lca;
   ```
   → `{"columns": ["source_file"], "rows": [["LCA_Disclosure_Data_FY2024_Q4.xlsx"], ["LCA_Disclosure_Data_FY2025_Q3.xlsx"], ["LCA_Disclosure_Data_FY2025_Q1.xlsx"], ["LCA_Disclosure_Data_FY2024_Q3.xlsx"], ["LCA_Disclosure_Data_…`
4. `run_sql`
   ```sql
   SELECT MIN(received_date), MAX(received_date), MIN(decision_date), MAX(decision_date) 
FROM lca 
WHERE source_file LIKE '%FY2025%';
   ```
   → `{"columns": ["min(received_date)", "max(received_date)", "min(decision_date)", "max(decision_date)"], "rows": [["43763", "45930", "45566", "45930"]], "truncated": false}`
5. `run_sql`
   ```sql
   SELECT CAST(45566 AS INTEGER) + DATE '1899-12-30' AS date_val;
   ```
   → `{"columns": ["date_val"], "rows": [["2024-10-01"]], "truncated": false}`
6. `run_sql`
   ```sql
   SELECT CAST(45930 AS INTEGER) + DATE '1899-12-30' AS date_val;
   ```
   → `{"columns": ["date_val"], "rows": [["2025-09-30"]], "truncated": false}`
7. `run_sql`
   ```sql
   SELECT case_status, COUNT(*) 
FROM lca 
WHERE employer_name ILIKE 'Meta Platforms, Inc%' 
  AND source_file LIKE '%FY2025%' 
GROUP BY 1;
   ```
   → `{"columns": ["case_status", "count_star()"], "rows": [["Certified - Withdrawn", 1], ["Certified", 6418], ["Denied", 1]], "truncated": false}`
8. `run_sql`
   ```sql
   SELECT job_title, COUNT(*), SUM(CAST(total_worker_positions AS INTEGER)) 
FROM lca 
WHERE employer_name ILIKE 'Meta Platforms, Inc%' 
  AND source_file LIKE '%FY2025%' 
  AND job_title ILIKE '%Data Scientist%' 
GROUP BY 1 
ORDER BY 2 DESC;
   ```
   → `{"columns": ["job_title", "count_star()", "sum(CAST(total_worker_positions AS INTEGER))"], "rows": [["Data Scientist", 267, 531], ["Data Scientist, Analytics", 35, 35], ["Data Scientist, Product Analytics", 21, 21], ["Da…`
9. `run_sql`
   ```sql
   SELECT DISTINCT soc_code, soc_title 
FROM lca 
WHERE employer_name ILIKE 'Meta Platforms, Inc%' 
  AND source_file LIKE '%FY2025%' 
  AND job_title ILIKE '%Data Scientist%';
   ```
   → `{"columns": ["soc_code", "soc_title"], "rows": [["15-1221.00", "Computer and Information Research Scientists"], ["15-1243.01", "Data Warehousing Specialists"], ["11-3021.00", "Computer and Information Systems Managers"],…`
10. `run_sql`
   ```sql
   SELECT job_title, soc_title, COUNT(*), SUM(CAST(total_worker_positions AS INTEGER)) 
FROM lca 
WHERE employer_name ILIKE 'Meta Platforms, Inc%' 
  AND source_file LIKE '%FY2025%' 
  AND (soc_title ILIKE '%Data Scientist%' OR soc_code = '15-2051.00') 
GROUP BY 1, 2 
ORDER BY 3 DESC;
   ```
   → `{"columns": ["job_title", "soc_title", "count_star()", "sum(CAST(total_worker_positions AS INTEGER))"], "rows": [["Data Scientist", "Data Scientists", 178, 442], ["Data Engineer", "Data Scientists", 121, 121], ["Software…`
11. `run_sql`
   ```sql
   SELECT 
  case_status, 
  COUNT(*) as cases_count, 
  SUM(CAST(total_worker_positions AS INTEGER)) as positions_count
FROM lca 
WHERE employer_name ILIKE 'Meta Platforms, Inc%' 
  AND source_file LIKE '%FY2025%' 
  AND job_title ILIKE '%Data Scientist%'
GROUP BY 1;
   ```
   → `{"columns": ["case_status", "cases_count", "positions_count"], "rows": [["Certified", 338, 602]], "truncated": false}`
12. `run_sql`
   ```sql
   SELECT 
  case_status, 
  COUNT(*) as cases_count, 
  SUM(CAST(total_worker_positions AS INTEGER)) as positions_count
FROM lca 
WHERE employer_name ILIKE 'Meta Platforms, Inc%' 
  AND source_file LIKE '%FY2025%' 
  AND (job_title = 'Data Scientist' OR job_title = 'Data scientist')
GROUP BY 1;
   ```
   → `{"columns": ["case_status", "cases_count", "positions_count"], "rows": [["Certified", 268, 532]], "truncated": false}`
13. `run_sql`
   ```sql
   SELECT 
  case_status, 
  COUNT(*) as cases_count, 
  SUM(CAST(total_worker_positions AS INTEGER)) as positions_count
FROM lca 
WHERE employer_name ILIKE 'Meta Platforms, Inc%' 
  AND source_file LIKE '%FY2025%' 
  AND (soc_code LIKE '15-2051%' OR soc_title ILIKE '%Data Scientist%')
GROUP BY 1;
   ```
   → `{"columns": ["case_status", "cases_count", "positions_count"], "rows": [["Certified", 615, 879]], "truncated": false}`
14. `run_sql`
   ```sql
   SELECT DISTINCT employer_name, count(*) 
FROM lca 
WHERE employer_name ILIKE '%Meta Platforms%' 
GROUP BY 1 
ORDER BY 2 DESC;
   ```
   → `{"columns": ["employer_name", "count_star()"], "rows": [["Meta Platforms, Inc", 14550], ["Meta Platforms, Inc.", 1680], ["Meta Platforms, Inc. ", 462], ["META PLATFORMS, INC.", 451], ["META PLATFORMS, INC. ", 386]], "tru…`
15. `run_sql`
   ```sql
   SELECT DISTINCT employer_name, count(*) 
FROM lca 
WHERE employer_name ILIKE 'Meta%' 
  AND source_file LIKE '%FY2025%'
GROUP BY 1 
ORDER BY 2 DESC;
   ```
   → `{"columns": ["employer_name", "count_star()"], "rows": [["Meta Platforms, Inc", 6397], ["Meta Platforms, Inc.", 23], ["Metaforge IT Solutions", 20], ["METAFORGE IT SOLUTIONS", 19], ["META IT CORP", 12], ["Metanoia Soluti…`

**Answer:** FAILED: MaxTurnsExceeded: Max turns (15) exceeded

</details>

<details><summary>H-1B Pay Explorer: 6 tool calls, answered 689</summary>

1. `read_mappings` `{}` → `{"as_of": "FY2026 Q3", "tables": {"lca": {"description": "One row per H-1B Labor Condition Application (LCA) filed with the Department of Labor, FY2024 Q1 to FY2026 Q3, amendments deduplicated. An LCA…`
2. `find_employer` `{"name": "Meta"}` → `{"matches": [{"employer_id": 7, "employer": "Meta", "employer_type": "big_tech", "filings": 17537, "match_score": 100, "name_variants_merged": 7, "sample_variants": ["Meta Platforms, Inc", "Meta Platf…`
3. `find_role` `{"text": "data scientist"}` → `{"role_family": "Data Scientist", "matched_by": "rules", "main_soc_codes": [{"soc_code": "15-2051", "soc_title": "Data Scientists", "filings": 38958}, {"soc_code": "15-2041", "soc_title": "Statisticia…`
4. `run_sql`
   ```sql
   SELECT count(*) AS filings, sum(total_worker_positions) AS positions FROM lca WHERE employer_id = 7 AND role_family = 'Data Scientist' AND case_status = 'CERTIFIED' AND fiscal_year = 2025
   ```
   → `{"columns": ["filings", "positions"], "rows": [[425, 689]], "row_count": 1, "truncated": false}`
5. `run_sql`
   ```sql
   SELECT fiscal_year, count(*) AS filings, sum(total_worker_positions) AS positions, median(wage_annual_from) AS median_pay FROM lca WHERE employer_id = 7 AND role_family = 'Data Scientist' AND case_status = 'CERTIFIED' AND wage_flag = 'ok' GROUP BY 1 ORDER BY 1
   ```
   → `{"columns": ["fiscal_year", "filings", "positions", "median_pay"], "rows": [[2024, 463, 463, 190120.0], [2025, 425, 689, 200527.0], [2026, 317, 1157, 208000.0]], "row_count": 3, "truncated": false}`
6. `make_chart` `{"mark": "line", "title": "Meta Certified Data Scientist Positions by Fiscal Year", "y": "positions", "color": null, "x": "fiscal_year"}` → `{"ok": true, "note": "Chart shown to the user. Do not describe the chart's styling."}`

**Answer:** Meta filed for **689 certified data scientist positions** across 425 Labor Condition Applications (LCAs) in FY2025.

* **Rising demand:** Certified positions grew from 463 in FY2024 (across 463 filings) to 689 in FY2025, continuing to surge with 1,157 positions in partial FY2026.
* **Offered pay:** The median offered salary for these certified data scientists in FY2025 was $201k (based on 425 filings with valid salary data).
* **Filing structure:** Meta began using bulk filings in FY2025, averaging about 1.6 positions per certified LCA, whereas in FY2024 every certified LCA requested exactly one worker position.

</details>

### Failure 2: "How many lottery entries would a $120,000 data scientist offer in NYC get?"

**Expected: 2 entries.** In the OFLC 2026-27 table for SOC 15-2051 in New York-Newark-Jersey City, Level II starts at $115,835 and Level III at $144,414, so $120k is Level II.

**Why the plain agent failed:** all three runs answered **"exactly 1 entry"**. The model's training knowledge predates the wage-weighted rule (effective Feb 27, 2026), and the raw table has no wage thresholds, only the prevailing wage each employer happened to cite. Ours computes the level from the official table with the `wage_level` tool.

<details><summary>Plain agent, run 1: 5 tool calls, answered "exactly 1 entry"</summary>

1. `run_sql`
   ```sql
   DESCRIBE lca;
   ```
   → `{"columns": ["column_name", "column_type", "null", "key", "default", "extra"], "rows": [["case_number", "VARCHAR", "YES", null, null, null], ["case_status", "VARCHAR", "YES", null, null, null], ["received_date", "VARCHAR…`
2. `run_sql`
   ```sql
   SELECT pw, pw_wage_level, count(*) 
FROM lca 
WHERE (job_title ILIKE '%data scientist%' OR soc_title ILIKE '%data scientist%') 
  AND worksite_city ILIKE '%new york%' 
GROUP BY 1, 2 
LIMIT 10;
   ```
   → `{"columns": ["pw", "pw_wage_level", "count_star()"], "rows": [["111966", "II", 552], ["39.79", "I", 24], ["101400", "III", 1], ["126281", null, 1], ["124659", null, 2], ["90522", "I", 1], ["151306", null, 3], ["87418", n…`
3. `run_sql`
   ```sql
   SELECT pw_wage_level, MIN(CAST(pw AS DOUBLE)) as min_pw, MAX(CAST(pw AS DOUBLE)) as max_pw, AVG(CAST(pw AS DOUBLE)) as avg_pw, COUNT(*) as cnt
FROM lca
WHERE (job_title ILIKE '%data scientist%' OR soc_title ILIKE '%data scientist%')
  AND worksite_city ILIKE '%new york%'
  AND pw_unit = 'Year'
  AND pw ~ '^[0-9.]+$'
GROUP BY pw_wage_level
ORDER BY pw_wage_level;
   ```
   → `{"columns": ["pw_wage_level", "min_pw", "max_pw", "avg_pw", "cnt"], "rows": [["I", 44179.0, 100235.0, 79883.40981240981, 693], ["II", 77272.0, 182957.0, 108838.30379008746, 1715], ["III", 90272.0, 223642.0, 138427.410845…`
4. `run_sql`
   ```sql
   SELECT soc_code, soc_title, COUNT(*) 
FROM lca 
WHERE job_title ILIKE '%data scientist%' AND worksite_city ILIKE '%new york%' 
GROUP BY 1, 2 
ORDER BY 3 DESC 
LIMIT 5;
   ```
   → `{"columns": ["soc_code", "soc_title", "count_star()"], "rows": [["15-2051.00", "Data Scientists", 1483], ["15-2041.00", "Statisticians", 186], ["15-2031.00", "Operations Research Analysts", 53], ["15-2051.01", "Business …`
5. `run_sql`
   ```sql
   SELECT pw_wage_level, MIN(CAST(pw AS DOUBLE)) as min_pw, MAX(CAST(pw AS DOUBLE)) as max_pw, AVG(CAST(pw AS DOUBLE)) as avg_pw, COUNT(*) as cnt
FROM lca
WHERE soc_code = '15-2051.00'
  AND worksite_city ILIKE '%new york%'
  AND pw_unit = 'Year'
  AND pw ~ '^[0-9.]+$'
GROUP BY pw_wage_level
ORDER BY pw_wage_level;
   ```
   → `{"columns": ["pw_wage_level", "min_pw", "max_pw", "avg_pw", "cnt"], "rows": [["I", 50378.0, 82763.0, 80035.69018404908, 652], ["II", 77272.0, 111996.0, 108962.82503192849, 1566], ["III", 90272.0, 164403.0, 138645.1102941…`

**Answer:** Under current H-1B selection rules, a candidate with a $120,000 Data Scientist offer in New York City would get **exactly 1 entry** in the H-1B lottery. 

Here is a breakdown of why this is the case, how your salary compares to real LCA (Labor Condition Application) wage levels in NYC, and how previous policy proposals might have affected this.

---

### 1. Current Rules: The Beneficiary-Centric Lottery
Under the modern **beneficiary-centric selection system** (implemented by USCIS starting in March 2024 for the FY 2025 cap), the H-1B lottery is based on **unique passport/travel document numbers**, not the number of job offers or the salary of those offers. 

* **One Entry per Person:** Each unique candidate gets exactly **one entry** in the lottery pool, regardless of whether they have a $120,000 offer, a $300,000 offer, or multiple offers from different employers.
* **Employer Registration:** The employer offering $120,000 will submit **one registration** for you. If you are selected, that employer (and any other employer who registered you) is notified and allowed to file an H-1B petition on your behalf.

---

### 2. How a $120,000 Offer Compares to NYC Data Scientist Wage Level

</details>

<details><summary>H-1B Pay Explorer: 6 tool calls, answered 2 entries</summary>

1. `read_mappings` `{}` → `{"as_of": "FY2026 Q3", "tables": {"lca": {"description": "One row per H-1B Labor Condition Application (LCA) filed with the Department of Labor, FY2024 Q1 to FY2026 Q3, amendments deduplicated. An LCA…`
2. `find_location` `{"place": "NYC"}` → `{"area_code": "35620", "metro_name": "New York-Newark-Jersey City, NY-NJ", "matched_by": "alias"}`
3. `find_role` `{"text": "data scientist"}` → `{"role_family": "Data Scientist", "matched_by": "rules", "main_soc_codes": [{"soc_code": "15-2051", "soc_title": "Data Scientists", "filings": 38958}, {"soc_code": "15-2041", "soc_title": "Statisticia…`
4. `wage_level` `{"role": "data scientist", "soc_code": "15-2051", "salary": 120000, "location": "NYC"}` → `{"salary": 120000.0, "role_family": "Data Scientist", "soc_code": "15-2051", "soc_title": "Data Scientists", "area_code": "35620", "metro_name": "New York-Newark-Jersey City, NY-NJ", "wage_level": 2, …`
5. `run_sql`
   ```sql
   SELECT offer_lottery_entries, count(*) as filings, round(100.0 * count(*) / sum(count(*)) over (), 1) as pct FROM lca WHERE area_code = '35620' AND role_family = 'Data Scientist' AND case_status = 'CERTIFIED' GROUP BY 1 ORDER BY 1
   ```
   → `{"columns": ["offer_lottery_entries", "filings", "pct"], "rows": [[0, 678, 8.2], [1, 1640, 19.8], [2, 1924, 23.2], [3, 2026, 24.4], [4, 2017, 24.3], [null, 8, 0.1]], "row_count": 6, "truncated": false}`
6. `make_chart` `{"title": "Distribution of H-1B Lottery Entries, NYC Data Scientists (FY24-FY26)", "y": "filings", "color": null, "x": "offer_lottery_entries", "mark": "bar"}` → `{"ok": true, "note": "Chart shown to the user. Do not describe the chart's styling."}`

**Answer:** A $120,000 data scientist offer in the New York City metro area would receive **2 entries** in the wage-weighted H-1B lottery.

* **Wage Level II:** This salary ($120k) passes the Level II threshold of $115,835 but falls $24k short of Level III ($144k) for Data Scientists (SOC 15-2051) under the 2026–27 OFLC wage tables.
* **Peer Comparison:** A $120k offer sits in the 29th percentile. The median offered pay across 8,293 certified Data Scientist filings in NYC from FY2024 to FY2026 Q3 was $145k. 
* **Overall NYC Distribution:** Among those 8,293 certified NYC filings, 23.2% (1,924 filings) qualified for exactly 2 entries, whereas 48.7% (4,043 filings) secured 3 or 4 entries by meeting higher wage levels.

</details>

## Data

Two sources, one per team member:

| Source | What it is | Rows | Where |
| --- | --- | --- | --- |
| [DOL OFLC LCA disclosure data](https://www.dol.gov/agencies/eta/foreign-labor/performance) | Every Labor Condition Application decided FY2024 Q1 - FY2026 Q3 (9 `.xlsx` files, 1 GB: FY2024 and FY2025 by quarter, FY2026 as one cumulative file) | 1,532,089 H-1B filings after deduplication (532,850 in FY2024, 572,287 in FY2025, 426,952 in FY2026 Q1-Q3) | `lca` table |
| [OFLC prevailing wage tables, wage year 2026-27](https://flag.dol.gov/wage-data/wage-data-downloads) | Level I-IV wages for every occupation (SOC) x wage area, plus the area-to-county map | 442,919 SOC x area rows | `wage_levels`, `areas` tables |

**To rebuild:** download the 9 LCA files in a browser (dol.gov blocks scripts) into `raw/lca/`, unzip `OFLC_Wages_2026-27.zip` into `raw/pw/`, then run `uv run build.py`. **Hosting:** the full database (`data/h1b.duckdb`, 121 MB, over GitHub's 100 MB limit) lives in a Google Cloud Storage bucket. At startup the Cloud Run service copies it from GCS and DuckDB opens it read-only, so every question is answered with DuckDB SQL over data hosted in GCS. A 2% sample (`data/h1b_sample.duckdb`) and `data/mappings.json` are committed, so `uv run app.py` works from a fresh clone.

**Dropped:** E-3 and H-1B1 filings (not H-1B), and earlier copies of amended cases (we keep each case's latest decision). Withdrawn and denied filings are kept, with `case_status`, and excluded by default.

## The offline build step (`build.py`)

The raw data has traps that make naive SQL wrong. Each one is fixed once, offline, so the agent never has to know about it:

| Trap in the raw data | Example | Fix in `build.py` |
| --- | --- | --- |
| Wages come in five units | `$52.40` per **Hour** next to `$109,000` per **Year** | `wage_annual_from` (Hour x 2080, Week x 52, Bi-Weekly x 26, Month x 12) |
| Unit mistakes | an hourly rate typed with unit Year | `wage_flag`; excluded from pay statistics |
| One company, many legal names | `GOOGLE LLC`, `Google LLC.`, `Google Inc.` | name normalization + `employer_overrides.csv` → one `employer_id` |
| Free-text job titles | `Machine Learning Eng II`, `SWE III`, `MLE` | rules → SOC-code fallback → (optional) Gemini → `role_family`, `seniority` |
| City spellings | `NYC`, `NEW YORK CITY`, `Brooklyn`, `Manhattan` | county → OFLC wage area → `area_code`, `metro_name` |
| Filings vs workers | one LCA can cover 10 positions | `total_worker_positions` documented; agent sums it for "how many jobs" |
| Withdrawn, denied and amended cases mixed together | | dedupe by case, `case_status` enum, guardrail note |
| No wage level for the offer itself | only the employer's chosen PW level is filed | `offer_wage_level` and `offer_lottery_entries` computed against the 2026-27 OFLC table |

It also writes `data/mappings.json`, the agent's offline context: every table and column with a hand-written description and its exact enum values, a glossary (LCA vs petition vs visa, wage levels, cap-exempt), join hints, four example queries, and the list of things the data cannot answer.

**Build quality** (from `docs/build_report.md`, certified filings):

| Check | Result |
| --- | --- |
| Usable annual wage (`wage_flag = 'ok'`) | 99.85% |
| Resolved to an employer | 100% (126,465 raw name spellings → 107,638 employers; Amazon alone had 53) |
| Assigned a role family | 98.7% (title rules 74%, SOC-code fallback 24%) |
| Mapped to an OFLC wage area | 99.9% |
| Offer wage level computed | 98.4% |

**What the build taught us:** Google files almost every engineer, ML included, as plain "Software Engineer", so "Google ML engineers in NYC" has no filings. The agent explains that instead of reporting zero.

**Role classifier accuracy:** TODO. We hand-checked 100 random (title, role family) labels: X/100 correct.

## How the agent works

`app.py` runs one agent, the **H-1B Analyst** (OpenAI Agents SDK + LiteLLM + Gemini on Vertex AI), over a read-only DuckDB connection with no file or network access.

| Tool | What it does | What goes wrong without it |
| --- | --- | --- |
| `read_mappings` | Schema, glossary, join hints, example queries, limitations | the model guesses column meanings |
| `get_enum_values` | Exact values of enum columns | `case_status = 'Certified'` matches nothing (it's `CERTIFIED`) |
| `find_employer` | Fuzzy match → `employer_id` (handles "TCS", "JP Morgan", "facebook") | `LIKE '%GOOGLE%'` misses variants or catches the wrong companies |
| `find_role` | "ML engineer" → `role_family` | searching titles misses "Machine Learning Eng II" |
| `find_location` | "NYC", "Bay Area" → OFLC wage area | `city = 'New York'` misses Brooklyn and Jersey City |
| `wage_level` | Salary + role + city → Level I-IV, lottery entries, thresholds, peer percentile | the model has no wage tables, so it guesses |
| `run_sql` | DuckDB, up to 200 rows, 20-second limit | |
| `make_chart` | Turns the last result into a Vega-Lite chart on the page | results stay as text |

**Guardrails** (`check_sql`, a tool input guardrail): the model reads the rejection and rewrites its query. It rejects aggregating raw wages, filtering on employer names, job titles or raw city spellings, pay statistics without `wage_flag = 'ok'`, and anything that isn't a single `SELECT`/`WITH`. A query on `lca` without a `case_status` filter comes back with a note.

**Admitting limits:** the prompt makes the agent check `limitations` first. If a question needs data we don't have (approvals, visas, actual salaries, individuals, green cards, after June 2026, exact lottery odds), it says so in one sentence, runs no SQL and suggests what it can answer instead.

`/chat` keeps the Project 1 shape (`response`, `session_id`, `tool_calls`), and every tool call carries an `agent` field. It adds `chart` (Vega-Lite) and `table` (the last result) for the page.

## Self-check (evals)

`evals/checks.jsonl` holds 26 questions with gold SQL: 11 numbers, 3 offer calculations, 7 top-k rankings and 5 questions the data can't answer. Gold values come from running the gold SQL on the same database. `uv run python evals/check.py` scores the agent (`--url` scores the deployed app). None of them is a few-shot example in the prompt.

| Date | Target | Score | Change |
| --- | --- | --- | --- |
| 2026-11-09 | local, full database | **26/26** (p50 12 s per answer) | first run on real data |

## What it can't answer

LCAs stop before the petition. The data can't tell you who won the lottery, who got a visa, what people were actually paid, anything about an individual, green-card sponsorship, or your exact odds (the pool of registrations by level isn't public). Ask "How many H-1Bs did Meta get approved?" and the agent says so, then offers Meta's certified filings and offered pay instead.

## Run it locally

```bash
uv sync
gcloud auth application-default login
uv run app.py            # http://localhost:8000, on the committed 2% sample unless data/h1b.duckdb exists
uv run pytest            # 32 deterministic checks, no model calls
```

## Files

| File | Role |
| --- | --- |
| `build.py` | Offline build: raw DOL files → `data/h1b.duckdb`, the sample, `mappings.json`, `docs/build_report.md` |
| `h1b_common.py` | Normalizers shared by the build and the agent (employers, titles, cities, wages) |
| `employer_overrides.csv` | Hand-curated grouping of big employers' legal entities |
| `app.py` | FastAPI server, the agent, its tools and guardrails |
| `index.html` | The page: offer checker, chat, charts, sortable tables, "Show work" |
| `baseline.py`, `compare.py` | The plain agent and the three-way comparison that produced the traces above |
| `evals/` | Self-check questions, scorer, score history |

## Limits

- The wage levels use the 2026-27 OFLC table for every year, so levels for FY2024 filings are approximate.
- A petition with several worksites uses the lowest level across them; the calculator assumes one worksite.
- Role families come from titles and SOC codes; some titles are ambiguous ("Consultant", "Engineer II").
- An LCA is a filing, not a hire. Staffing firms file many LCAs that never become petitions.
