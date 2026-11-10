# H-1B Pay Explorer: handoff

Status as of **Nov 10, 2026**. Team: Ketaki Dabade (kvd2112) and Anamika Mishra (akm2259). Path: **Text2SQL**.

**In one line:** the project is built, tested on the real data (33/33), pushed to GitHub and **live at https://h1b-pay-explorer-314308831335.us-east1.run.app**. Continuous deploy from GitHub is on: every push to `main` redeploys automatically. Left: ship the Nov 10 update (below), collaborators, and submitting.

## Nov 10 update: USCIS petitions added (not deployed yet)

A third data source, from a different agency: the **USCIS H-1B Employer Data Hub** (FY2024 to FY2026), exported from the hub's Crosstab View into `raw/uscis/`. `build.py` now writes a `petitions` table (approvals and denials per employer and fiscal year) on the same `employer_id` as `lca`; 97.2% of approvals match an `lca` employer. The agent can now answer "how many H-1Bs did Meta get approved?" (6,294 approved petitions in FY2025, 1,554 of them new employment) and compare filings with approvals.

Changed locally, **not committed or pushed**: `build.py`, `app.py` (prompt), `index.html` (two Approvals chips, new Limits chip, USCIS in sources), `employer_overrides.csv` (EY spelling, Fidelity), `evals/checks.jsonl` (33 checks: Meta approvals is now a scored answer, plus 3 more petition checks and a new refusal), `tests/test_app.py` (49 tests, all pass), `data/mappings.json`, `data/h1b_sample.duckdb`, `docs/build_report.md`, `README.md`. `data/h1b.duckdb` was rebuilt locally (124 MB).

To ship it, in this order:

| # | Step | Command |
| --- | --- | --- |
| 1 ✅ 33/33 | Score the new database locally | `uv run python evals/check.py --label "USCIS petitions added"` |
| 2 ✅ ours 3/3 | Record sample query 3 (no tools, plain agent, ours) | `uv run compare.py "How many H-1B visas did Meta get approved in 2025?" --gold "SELECT sum(approved) FROM petitions WHERE employer = 'Meta' AND fiscal_year = 2025" --runs 3` |
| 3 ✅ | Fill the sample query 3 cell in the README from that trace, and add the eval row | done |
| 4 | Upload the new database | `gcloud storage cp data/h1b.duckdb gs://ieor-project-1-kvd2112-h1b-data/v2/h1b.duckdb` |
| 5 | Point Cloud Run at it | `gcloud run services update h1b-pay-explorer --region us-east1 --project ieor-project-1-kvd2112 --update-env-vars GCS_OBJECT=v2/h1b.duckdb` |
| 6 | Commit and push (redeploys) | `git add -A && git commit -m "Add USCIS petition approvals as a third data source" && git push` |
| 7 | Score the live app and add the row to the README | `uv run python evals/check.py --url https://h1b-pay-explorer-314308831335.us-east1.run.app --label deployed` |

Do steps 4 to 6 close together: the new code expects the `petitions` table, and the old database doesn't have it.

| Thing | Where |
| --- | --- |
| Code | https://github.com/ketakiii3/h1b-pay-explorer (private, branch `main`) |
| GCP project | `ieor-project-1-kvd2112` (billing on, Vertex AI on) |
| Database in GCS | `gs://ieor-project-1-kvd2112-h1b-data/v1/h1b.duckdb` (114 MB, region `us-east1`); `v2/h1b.duckdb` after the Nov 10 update ships |
| **Live app** | **https://h1b-pay-explorer-314308831335.us-east1.run.app** (Cloud Run, `us-east1`, public) |
| Cloud Run console | https://console.cloud.google.com/run/detail/us-east1/h1b-pay-explorer/metrics?project=ieor-project-1-kvd2112 |
| Deploy guide | [DEPLOY.md](DEPLOY.md) |
| Local folder | `~/h1b_pay_explorer/h1b-pay-explorer` (raw DOL files in `raw/`, not in git) |

---

## Text2SQL requirements: all four done

| Requirement | Status | Evidence |
| --- | --- | --- |
| Offline build step that supports the agent writing SQL | ✅ | `build.py` turns 9 DOL files (1 GB) into `h1b.duckdb` and `data/mappings.json`: wages converted to yearly amounts, 126,465 employer spellings merged into 107,638 employers, job titles sorted into role families (98.6% covered), worksites mapped to OFLC wage areas (99.9%), and each offer's wage level and lottery entries computed. Report: `docs/build_report.md`. |
| Nicely present results (table or visualization) | ✅ | Each answer is a card with a headline number, a **Chart** tab (Vega-Lite), a **Table** tab (money and % formatting, inline bars, sorting, CSV download), a **SQL** tab and a **How I got this** step timeline. |
| README: two questions the plain `run_sql` agent got wrong and ours got right, both traces | ✅ | Meta data scientist positions (plain **0/3**, ours 3/3) and lottery entries for a $120k offer (plain **0/3**, ours 3/3), with traces in `<details>` blocks. Raw traces are in `traces/`. |
| Host data in BigQuery, CloudSQL or GCS, queryable with DuckDB | ✅ | The database is in GCS. On startup the app downloads it (tested: 4.1 s, 1,532,089 rows) and opens it read-only with DuckDB. |

> The "plain agent failures" are **supposed** to be failures. `baseline.py` is a deliberately bare agent that the assignment requires us to beat. **Our agent got every one of those questions right.**

## Full rubric: what's done, what's left

| Section | Item | Status |
| --- | --- | --- |
| Basics (1) | README.md | ✅ written; no placeholders left |
| | Valid `submission.json` | ✅ has the live URL, both UNIs, `"path": "text2sql"` |
| Functionality (9) | Deployed and reachable | ✅ live and tested (chat, chart, offer calculator), continuous deploy from GitHub `main` via a Cloud Build trigger |
| | Clear purpose | ✅ the first screen says what it does, who it's for and how to use it |
| | Answers correctly | ✅ self-check **33/33** locally on the full data, about 15 s per answer |
| Data (4) | Unique dataset or problem | ✅ the H-1B LCA plus wage-weighted lottery angle (confirm no one else on the sign-up sheet has it) |
| | Data the model doesn't know | ✅ the no-tools model guesses or refuses on all 3 sample queries (in the README) |
| | Admits what the data can't answer | ✅ 5/5 "can't answer" checks refused, with no SQL run |
| Path (7) | Text2SQL items above | ✅ all four |
| Creativity (4) | Frontend changed from the starter | ✅ fully new design, plus an instant offer calculator |
| | Agent does something interesting | ✅ salary → wage level → lottery entries; shows the job code changes the entries (the $175k San Jose example) |
| Team rule | One data source per member (2) | ✅ DOL LCA disclosure data, OFLC prevailing wage tables, and (Nov 10) the USCIS H-1B Employer Data Hub |
| Submit | Grader collaborators added | ❌ not yet |
| | Repo URL on CourseWorks | ❌ not yet (one person submits) |

## What's left, in order

| # | Task | Who | Time |
| --- | --- | --- | --- |
| 1 | ~~Link GitHub for continuous deploy~~ ✅ done (Cloud Build trigger on `main`) | – | – |
| 2 | ~~Put the live URL in `submission.json` and the README~~ ✅ done | – | – |
| 3 | Add collaborators `codeboi07`, `bhuvighosh3`, `nniishhh`, `x`, and Anamika, on GitHub → Settings → Collaborators | Ketaki | 2 min |
| 4 | ~~Write README "Why we built this"~~ ✅ done | – | – |
| 5 | ~~Role spot-check~~ ✅ done: 93/100, misses fixed (in README) | – | – |
| 7 | Run the self-check against the live URL: `uv run python evals/check.py --url <URL> --label deployed`, and add the row to the README's evals table | Ketaki | 10 min |
| 8 | Billing → Budgets & alerts: a budget for `ieor-project-1-kvd2112` | Ketaki | 2 min |
| 9 | Open the live URL in a private window and on a phone, and click every example question | both | 5 min |
| 10 | Submit the repo URL on CourseWorks | one person | 1 min |


## How to see it on the web (GCP)

**The app:** https://h1b-pay-explorer-314308831335.us-east1.run.app

**The service in the GCP console:** https://console.cloud.google.com/run?project=ieor-project-1-kvd2112 → click **h1b-pay-explorer**. The URL is at the top. Tabs: **Metrics** (requests, latency), **Logs** (errors), **Revisions** (each deploy), **Edit & deploy new revision** (settings, env vars).

**The data:** https://console.cloud.google.com/storage/browser/ieor-project-1-kvd2112-h1b-data?project=ieor-project-1-kvd2112

The first question after the app has been idle takes about 50 s while it starts up and downloads the database from GCS; later answers take about 12 s. Health check: `https://h1b-pay-explorer-314308831335.us-east1.run.app/health`.

### Current settings

Region `us-east1`, public, 2 GiB memory, 1 CPU, startup boost, 600 s request timeout, 0-3 instances, service account `h1b-runner` (can only call Gemini and read the bucket). Env vars: `GCS_BUCKET=ieor-project-1-kvd2112-h1b-data`, `GCS_OBJECT=v1/h1b.duckdb`, `MODEL=vertex_ai/gemini-3.5-flash`, `VERTEX_LOCATION=global`, `VERTEXAI_PROJECT=ieor-project-1-kvd2112`.

### Continuous deploy ✅ set up

Every push to `main` on GitHub builds and deploys a new revision (watch it under **Revision History** or Cloud Build → History). It was set up like this, in case it ever needs redoing:

1. Open https://console.cloud.google.com/run/detail/us-east1/h1b-pay-explorer?project=ieor-project-1-kvd2112 (signed in as kvd2112@columbia.edu: switch accounts with the profile picture, top right)
2. **Source** tab (scroll the tab bar right) → **Connect to repo**.
3. Provider **GitHub** → **Authenticate** (sign in as `ketakiii3`, install the Google Cloud Build app on `h1b-pay-explorer`) → pick repo `ketakiii3/h1b-pay-explorer`.
4. Branch `^main$` → Build type **Go, Node.js, Python, Java, .NET Core, Ruby or PHP via Google Cloud's buildpacks** → leave the entrypoint empty → **Save**.
5. Check: push any small change (for example a README edit) and watch a new revision appear under **Revisions** in about 5 minutes.

The settings and env vars above are kept; continuous deploy only changes where the code comes from.

### Redeploying by hand (if ever needed)

```bash
cd ~/h1b_pay_explorer/h1b-pay-explorer
gcloud run deploy h1b-pay-explorer --source . --region us-east1 --project ieor-project-1-kvd2112
```

## Key results (for slides, peers, the README)

- **1,532,089** H-1B filings, FY2024 Q1 to FY2026 Q3; Amazon alone filed under **53** name variants.
- A **$120k data scientist offer in NYC** is Level II (2 entries) and beats only **29%** of 5,700 real filings (median $145k).
- A **$175k ML engineer offer in San Jose** gets **1 entry** if filed as Software Developer, but **2** if filed as Data Scientist. The job code matters.
- **Google files almost every engineer, ML included, as "Software Engineer"**, so "Google ML engineers in NYC" has no filings.
- **Bloomberg** filed the most NYC ML engineer positions in FY2025 (173), six times the next employer.
- **Goldman Sachs** was the top data scientist sponsor in FY2025 by positions (2,817), filing "Associate" roles in batches of 100.
- **AI engineer filings grew about 5x**: 335 certified (FY2024), then 923 (FY2025), then 1,734 (FY2026 Q1-Q3). Forward Deployed roles are led by Palantir, BCG and Salesforce.
- **FY2025 median offers:** ML Engineer $175k, Forward Deployed $163k, Research Scientist $159k, AI Engineer $138k, Data Scientist $135k.
- No-tools Gemini says a lottery offer gets "exactly 1 entry". It doesn't know about the 2026 wage-weighted rule.

## How it's built (one paragraph)

`build.py` (offline, on the laptop) reads the raw DOL Excel files and the OFLC wage tables and writes `data/h1b.duckdb` (full, uploaded to GCS), `data/h1b_sample.duckdb` (2%, in git, so the app runs from a fresh clone) and `data/mappings.json` (the agent's schema notes, glossary and limits). `app.py` is FastAPI plus the OpenAI Agents SDK with Gemini on Vertex. The agent has 8 tools: read_mappings, get_enum_values, find_employer, find_role, find_location, wage_level, run_sql and make_chart. Guardrails reject known-bad SQL (raw wages, name `LIKE`s, missing `wage_flag`) so the model rewrites it. `index.html` is the whole frontend. `baseline.py` and `compare.py` produce the plain-agent comparison, `evals/check.py` runs the 26-question self-check, and `tests/` has 32 offline tests (`uv run pytest`).

## Rebuilding or changing things

| To… | Run |
| --- | --- |
| Rebuild the database after changing `build.py` or `h1b_common.py` | `uv run build.py` (about 1 min) |
| Ship a rebuilt database | upload as `v2/h1b.duckdb`, commit the new `data/mappings.json` **and** change `GCS_OBJECT` to `v2/h1b.duckdb` on Cloud Run, all together |
| Test without Gemini | `uv run pytest` |
| Score the agent | `uv run python evals/check.py [--url <live URL>]` |
| Regenerate a comparison | `uv run compare.py --check <id> --runs 3` |

## Notes

- Your gcloud and Gemini logins are `kvd2112@columbia.edu`, with quota project `ieor-project-1-kvd2112`. Cloud Run uses the `h1b-runner` service account, not your login.
- `raw/` (1 GB of DOL files) and `data/h1b.duckdb` are not in git on purpose (over the size limit). The DOL files can be downloaded again from https://www.dol.gov/agencies/eta/foreign-labor/performance (browser only).
- Commits go out with no Claude co-author lines.
