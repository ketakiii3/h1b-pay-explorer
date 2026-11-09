# H-1B Pay Explorer: handoff

Status as of **Nov 9, 2026**. Team: Anamika Mishra (akm2259), Ketaki (kvd2112). Path: **Text2SQL**.

**In one line:** the project is built, tested on the real data (26/26), pushed to GitHub and **live at https://h1b-pay-explorer-314308831335.us-east1.run.app**. Left: link Cloud Run to GitHub for automatic redeploys (2 min in the console), plus a few README items only we can write.

| Thing | Where |
| --- | --- |
| Code | https://github.com/ketakiii3/h1b-pay-explorer (private, branch `main`) |
| GCP project | `ieor-project-1-kvd2112` (billing on, Vertex AI on) |
| Database in GCS | `gs://ieor-project-1-kvd2112-h1b-data/v1/h1b.duckdb` (114 MB, region `us-east1`) |
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
| Basics (1) | README.md | ✅ written; 3 TODOs left (see below) |
| | Valid `submission.json` | ✅ has the live URL, both UNIs, `"path": "text2sql"` |
| Functionality (9) | Deployed and reachable | ✅ live and tested (chat, chart, offer calculator) · ⚠️ continuous deploy from GitHub still to link (task 1) |
| | Clear purpose | ✅ the first screen says what it does, who it's for and how to use it |
| | Answers correctly | ✅ self-check **26/26** locally on the full data, about 12 s per answer |
| Data (4) | Unique dataset or problem | ✅ the H-1B LCA plus wage-weighted lottery angle (confirm no one else on the sign-up sheet has it) |
| | Data the model doesn't know | ✅ the no-tools model guesses or refuses on all 3 sample queries (in the README) |
| | Admits what the data can't answer | ✅ 5/5 "can't answer" checks refused, with no SQL run |
| Path (7) | Text2SQL items above | ✅ all four |
| Creativity (4) | Frontend changed from the starter | ✅ fully new design, plus an instant offer calculator |
| | Agent does something interesting | ✅ salary → wage level → lottery entries; shows the job code changes the entries (the $175k San Jose example) |
| Team rule | One data source per member (2) | ✅ DOL LCA disclosure data and OFLC prevailing wage tables |
| Submit | Grader collaborators added | ❌ not yet |
| | Repo URL on CourseWorks | ❌ not yet (one person submits) |

## What's left, in order

| # | Task | Who | Time |
| --- | --- | --- | --- |
| 1 | Link GitHub for continuous deploy (the spec requires it): see "Continuous deploy" below | Ketaki | 2 min |
| 2 | ~~Put the live URL in `submission.json` and the README~~ ✅ done | – | – |
| 3 | Add collaborators `codeboi07`, `bhuvighosh3`, `nniishhh`, `x`, and Anamika, on GitHub → Settings → Collaborators | Ketaki | 2 min |
| 4 | Write README **"Why we built this"** (2-3 sentences, your own voice: this is the Originality & Voice score) | Ketaki / Anamika | 10 min |
| 5 | Fill in the `correct (y/n)` column in `evals/role_spotcheck.csv` (100 rows), then put "X/100 correct" in the README's **Role classifier accuracy** line | either | 15 min |
| 6 | Add a screenshot or GIF of a chart answer to the top of the README | either | 5 min |
| 7 | Run the self-check against the live URL: `uv run python evals/check.py --url <URL> --label deployed`, and add the row to the README's evals table | Ketaki | 10 min |
| 8 | Billing → Budgets & alerts: a budget for `ieor-project-1-kvd2112` | Ketaki | 2 min |
| 9 | Open the live URL in a private window and on a phone, and click every example question | both | 5 min |
| 10 | Submit the repo URL on CourseWorks | one person | 1 min |

`grep -n TODO README.md` shows the 3 README spots (tasks 4, 5, 6).

## How to see it on the web (GCP)

**The app:** https://h1b-pay-explorer-314308831335.us-east1.run.app

**The service in the GCP console:** https://console.cloud.google.com/run?project=ieor-project-1-kvd2112 → click **h1b-pay-explorer**. The URL is at the top. Tabs: **Metrics** (requests, latency), **Logs** (errors), **Revisions** (each deploy), **Edit & deploy new revision** (settings, env vars).

**The data:** https://console.cloud.google.com/storage/browser/ieor-project-1-kvd2112-h1b-data?project=ieor-project-1-kvd2112

The first question after the app has been idle takes about 50 s while it starts up and downloads the database from GCS; later answers take about 12 s. Health check: `https://h1b-pay-explorer-314308831335.us-east1.run.app/health`.

### Current settings

Region `us-east1`, public, 2 GiB memory, 1 CPU, startup boost, 600 s request timeout, 0-3 instances, service account `h1b-runner` (can only call Gemini and read the bucket). Env vars: `GCS_BUCKET=ieor-project-1-kvd2112-h1b-data`, `GCS_OBJECT=v1/h1b.duckdb`, `MODEL=vertex_ai/gemini-3.5-flash`, `VERTEX_LOCATION=global`, `VERTEXAI_PROJECT=ieor-project-1-kvd2112`.

### Continuous deploy (task 1: needs your GitHub login, 2 minutes)

The spec asks for continuous deploy from GitHub. Right now the service was deployed from the laptop (`gcloud run deploy --source .`). To link it:

1. Open https://console.cloud.google.com/run/detail/us-east1/h1b-pay-explorer?project=ieor-project-1-kvd2112
2. Click **Set up continuous deployment** (top bar).
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
