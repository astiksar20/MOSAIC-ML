> **SUPERSEDED (2026-10-24).** Written on 2026-10-20, before the database,
> the corrected matrix and the retraining. Several statements below are no
> longer true (for example, a database now exists: `storage/history.py`).
> The current status and unfinished work are in **`START_HERE.md`**.

# MOSAIC-ML — Status and Unfinished Work
**Generated:** 2026-10-20

This file lists what exists, what was fixed in this pass, and what is **not
built**. Everything marked "not built" must be described as such in the
report. Do not describe planned work as implemented.

---

## Fixed in this pass

| # | Problem | Status |
|---|---|---|
| 1 | Paths resolved against the working directory, so the app crashed with `FileNotFoundError` when started from anywhere but the repo root | **Fixed** — paths now anchor to the module file via `PROJECT_ROOT`. Verified by running the full API from `/tmp`. |
| 2 | Fix 2 was never installed — no CORS, no upload validation, placeholder health check, androguard log flood | **Fixed** — all applied and verified |
| 3 | The model was reloaded from disk on every request (16 MB) | **Fixed** — cached in `ml/predict.py` |
| 4 | The Colab notebook trained models but saved none, so nothing could be deployed from it | **Fixed** — two cells added that refit on train+validation, save a model bundle with metadata, then reload and verify it |

### Verified working, from a non-root working directory

```
/health          -> healthy (model, vocabulary, permission weights all load)
/analyze-apk     -> 200, coverage 97/24833, 9 response sections
.txt upload      -> 400 rejected
fake .apk        -> 400 rejected (ZIP header check)
CORS preflight   -> 200 with the correct origin
NVD unreachable  -> scan still returns 200, reports lookup_failed
```

---

## NOT BUILT — state these as limitations

### 1. No database. Nothing is persisted.
There is no SQLite, PostgreSQL or SQLAlchemy code anywhere in the repository.
No models, no session, no migrations, no storage calls. Every scan result is
returned in the HTTP response and then discarded.

> Any earlier document claiming "Database: locally initialized SQLite" is
> incorrect. There has never been a database in this project.

Building it means: a schema, a session layer, save calls in the endpoint,
retrieval endpoints, and frontend components to display history.

### 2. HIDS telemetry is synthetic
`api/main.py` hardcodes `["normal_file_access", "unexpected_sms",
"unknown_network_connection"]`. These events have no relationship to the
uploaded APK. The Isolation Forest runs on fabricated runtime data.

Never present HIDS output as behaviour observed from the uploaded app.

### 3. NVD has never been tested live
The client was rewritten with retry, backoff, caching, API-key support and
three distinct outcome states, but **every test ran against a blocked
network**. The success path has never executed. Get an API key from
`nvd.nist.gov/developers/request-an-api-key`, set `NVD_API_KEY`, and verify
before relying on it.

### 4. The frontend does not display the new API sections
The response now carries `feature_coverage`, `cve_lookup` and
`permission_risk`. No React component reads any of them. The dashboard will
render without error but will silently omit all three.

### 5. The Docker image was never built
Docker has no daemon in the environment where this was prepared. The
Dockerfile is written against Hugging Face Spaces' documented requirements
(port 7860, UID 1000) and every `COPY` path was verified to exist, but the
build itself is **unverified**. Expect to iterate on the first deploy.

### 6. The 40/40/20 weighted sum is still in use
`risk/risk_engine.py` still produces the LOW/MEDIUM/HIGH verdict, now marked
`DEPRECATED_PROTOTYPE` with caveats attached. It has not been replaced by the
evidence-based engine. Its HIDS input is synthetic, so most of its value comes
from fabricated data.

### 7. Not done
- Exported-component / `debuggable` / `allowBackup` / cleartext-traffic checks
- SHA-256 hashing of uploads
- Normalized finding schema
- Figures 1, 7, 8, 12, 13, 14
- The research paper
- Deployment to Vercel and Hugging Face

---

## Model notes

The shipped `ml/random_forest_model.joblib` was trained with
**scikit-learn 1.6.1**. `requirements.txt` pins that version, so the Docker
container is internally consistent. A local environment running a different
version will emit `InconsistentVersionWarning`; that is expected and affects
local runs only.

Measured in this pass: **Logistic Regression produces a 0.2 MB model against
Random Forest's 15.8 MB** — 79× smaller, with higher balanced accuracy
(0.9598 vs 0.9527). Worth considering for deployment; the notebook now saves
whichever model wins.

---

## Deployment order

1. Get the code onto GitHub (Git is not currently installed locally)
2. Create a Hugging Face Space, Docker SDK
3. Upload the repository; `README_SPACE.md` becomes the Space's `README.md`
4. Set `ALLOWED_ORIGINS` to the Vercel URL, and `NVD_API_KEY`
5. Check `/health` returns `healthy` with all three checks true
6. Deploy the frontend on Vercel, root directory `dashboard`, with
   `VITE_API_URL` pointing at the Space
7. Upload a real APK end to end before relying on it

**Test with a large APK before any demo.** The test fixture is small; DEX
analysis of a 50 MB APK uses far more memory.
