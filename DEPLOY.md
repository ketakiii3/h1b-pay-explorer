# Deploy H-1B Pay Explorer: step by step

Each step ends with a **✅ Check**. Don't move on until it passes. Commands assume you're in the
`h1b-pay-explorer/` folder. Steps 1-4 are on your laptop; steps 5-10 are GCP.

Set these once per terminal (use your own project ID; your last project ran in `us-east1`):

```bash
export PROJECT_ID=ieor-project-1-kvd2112
export REGION=us-east1
export BUCKET=${PROJECT_ID}-h1b-data
export SA=h1b-runner@${PROJECT_ID}.iam.gserviceaccount.com
```

---

## 1. Log in again (your gcloud tokens have expired)

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project $PROJECT_ID
gcloud auth application-default set-quota-project $PROJECT_ID
```

✅ **Check:** `gcloud storage buckets list` runs without an `invalid_grant` error.

## 2. Get the real LCA files ✅ done

The 9 DOL files (FY2024 Q1-Q4, FY2025 Q1-Q4, FY2026 Q3 cumulative) are already in `raw/lca/`, and the
OFLC wage tables are in `raw/pw/`. If you ever need them again: https://www.dol.gov/agencies/eta/foreign-labor/performance
→ Disclosure Data → LCA Programs (browser only; dol.gov blocks scripts).

## 3. Build the database

```bash
uv run build.py            # already run once: about 3 min from scratch, 1 min with the cached Parquet
```

Optional and worth doing for the ambition score: label the job titles the rules miss with Gemini (cached in `role_cache.json`, so you only pay once):

```bash
uv run build.py --llm
```

✅ **Check** the report it prints (also saved to `docs/build_report.md`):
- Last run: 1,532,089 filings (FY2024 532,850 · FY2025 572,287 · FY2026 Q1-Q3 426,952); `h1b.duckdb` is 121 MB, so 2 GiB memory is plenty
- `wage_flag = 'ok'` ≥ 99.5%, `has employer_id` ≥ 95%, `has area_code` ≥ 97%, `role_family not 'Other'` ≥ 90%
- `ls -lh data/` shows the size of `h1b.duckdb`. **Write it down**: it sets Cloud Run memory in step 7.

If a column error appears (`has no column for …`), open the record layout PDF and add the new
column name to `COLUMN_MAP` at the top of `build.py`.

## 4. Test locally

```bash
uv run pytest -q                         # 32 passed
uv run app.py                            # open http://localhost:8000
```

In the browser: check a $120k Data Scientist offer in New York City, then click every example question.
Then run the self-check (about 10 minutes):

```bash
uv run python evals/check.py --label "first real-data run"
```

✅ **Check:** the page header shows the real row count and **no red "Synthetic" banner**, every chip returns a chart or table, and the self-check scores ≥ 20/26. If a check fails, open `evals/results/<latest>.json` to see the agent's SQL.

## 5. Push to GitHub

```bash
git init -b main
git add -A
git status              # data/h1b.duckdb and raw/ must NOT be listed; data/h1b_sample.duckdb and data/mappings.json MUST be
git commit -m "H-1B Pay Explorer: Text2SQL agent over DOL LCA filings"
gh repo create h1b-pay-explorer --private --source . --push
for u in codeboi07 bhuvighosh3 nniishhh x; do gh api -X PUT repos/{owner}/h1b-pay-explorer/collaborators/$u; done
```

Also add Anamika Mishra as a collaborator.

✅ **Check:** the repo on GitHub has `app.py`, `pyproject.toml`, `uv.lock`, `Procfile`, `README.md`, `submission.json` at the root, and no file over 100 MB.

## 6. GCP: APIs, bucket, service account (one time)

```bash
gcloud services enable aiplatform.googleapis.com run.googleapis.com cloudbuild.googleapis.com \
  artifactregistry.googleapis.com storage.googleapis.com

# Bucket in the same region as Cloud Run, so the startup download is fast
gcloud storage buckets create gs://$BUCKET --location=$REGION --uniform-bucket-level-access
gcloud storage cp data/h1b.duckdb gs://$BUCKET/v1/h1b.duckdb

# The identity the app runs as: it may call Gemini and read the bucket, nothing else
gcloud iam service-accounts create h1b-runner --display-name="H-1B Pay Explorer runtime"
gcloud projects add-iam-policy-binding $PROJECT_ID --member=serviceAccount:$SA --role=roles/aiplatform.user
gcloud storage buckets add-iam-policy-binding gs://$BUCKET --member=serviceAccount:$SA --role=roles/storage.objectViewer
```

✅ **Check:** `gcloud storage ls -l gs://$BUCKET/v1/` shows `h1b.duckdb` with the same size as your local file.

## 7. Create the Cloud Run service with continuous deploy (console)

Same flow as your last project ("Deploying to Cloud Run from GitHub"):

1. Console → **Cloud Run** → **Deploy container** → **Service**.
2. Choose **Continuously deploy from a repository (source or function)** → **Set up with Cloud Build**.
   - Connect GitHub if asked, pick `h1b-pay-explorer`, branch `^main$`.
   - Build type: **Go, Node.js, Python, Java, .NET Core, Ruby or PHP via Google Cloud's buildpacks**. Leave the entrypoint empty: the `Procfile` sets it.
3. Service name `h1b-pay-explorer`, region **us-east1**.
4. Authentication: **Allow public access**. (Last time you put IAP in front for Columbia accounts. That works too, but only if every grader and peer can sign in, and public is simpler to grade.)
5. Open **Containers, Volumes, Networking, Security**:
   - **Settings:** memory **2 GiB** if `h1b.duckdb` is under 700 MB, otherwise **4 GiB** (the file is copied into `/tmp`, which uses memory). CPU **1**. **Startup CPU boost** on.
   - **Request timeout:** **600** seconds (graders wait up to 5 minutes).
   - **Variables & secrets**, add:

     | Name | Value |
     | --- | --- |
     | `GCS_BUCKET` | your bucket name, `ieor-project-1-kvd2112-h1b-data` |
     | `GCS_OBJECT` | `v1/h1b.duckdb` |
     | `MODEL` | `vertex_ai/gemini-3.5-flash` |
     | `VERTEX_LOCATION` | `global` |
     | `VERTEXAI_PROJECT` | your project ID |

   - **Security** tab → Service account: **h1b-runner**.
   - Revision scaling: min **0**, max **3**. Concurrency **10**.
6. **Create.** The first build takes 3-6 minutes.

✅ **Check:** the service shows a green tick and a URL ending in `.run.app`.

## 8. Verify the deployment

```bash
URL=$(gcloud run services describe h1b-pay-explorer --region $REGION --format='value(status.url)')
curl -s $URL/health                         # {"ok":true,"database":"h1b.duckdb"}  ← must say h1b.duckdb, not h1b_sample
curl -s -X POST $URL/api/offer -H 'content-type: application/json' \
  -d '{"salary":175000,"role":"ML engineer","location":"San Jose"}' | head -c 300; echo
time curl -s -X POST $URL/chat -H 'content-type: application/json' \
  -d '{"message":"Top 5 sponsors of data scientists in FY2025"}' | head -c 600; echo
```

Then open the URL on your phone and in a private window, and click every chip.
Finally, score the live app:

```bash
uv run python evals/check.py --url $URL --label "deployed"
```

✅ **Check:** `/health` says `h1b.duckdb`; `/chat` answers in under 60 seconds with a `chart`; the live self-check scores within 1-2 of your local score.

**If something fails:**

| Symptom | Fix |
| --- | --- |
| Build fails | Cloud Build → History → the failed build's log. Usually a missing `uv.lock` commit. |
| Service won't start | Cloud Run → Logs. `403` on storage → step 6 bucket binding; out of memory → raise memory to 4 GiB. |
| `/health` says `h1b_sample.duckdb` | `GCS_BUCKET` isn't set on the service. |
| Chat says "model call failed … PermissionDenied" | The service account lacks `roles/aiplatform.user`, or the model isn't available in `global` for your project: try `MODEL=vertex_ai/gemini-3.5-flash-lite`. |
| First answer is slow | Cold start downloads the database. Set min instances to 1 during grading (costs money: check your budget). |

## 9. Finish the README and submission

1. Put the live URL in `submission.json` (`deploy_url`) and at the top of `README.md`.
2. Generate the comparisons the README needs:

```bash
uv run compare.py --check pay-google-swe-nyc --runs 3
uv run compare.py --check top-ds-sponsors --runs 3
uv run compare.py --check count-meta-ds-positions --runs 3
uv run compare.py --check top-nyc-mle --runs 3
uv run compare.py --check offer-ds-120k-nyc --runs 3
```

   Keep the **two** questions where the plain agent is wrong in at least 2 of 3 runs and ours is right in 3 of 3. Paste their printed blocks into "Plain run_sql agent vs this agent". Then run `compare.py` on the 3 sample queries and paste the no-tools vs agent answers.
3. Fill in every `TODO` in the README, including the "Why we built this" paragraph in your own words.
4. `python -m json.tool submission.json`, then commit and push. Cloud Run redeploys automatically.

✅ **Check:** `grep -n TODO README.md` prints nothing; the new revision is serving.

## 10. Keep it running

- Billing → **Budgets & alerts** → a budget for this project with alerts at 50/90/100%.
- Don't delete the service, the bucket or the project until grades are out.
- To ship a rebuilt database without downtime: upload it as `v2/h1b.duckdb`, then commit the new `data/mappings.json` and change `GCS_OBJECT` to `v2/h1b.duckdb` together. The mappings must match the database.

## Submit

One person submits the GitHub repo URL on CourseWorks.
