# MOSAIC-ML — Deployment

One container serves the dashboard and the API from a single port, so **one
deploy gives you a complete website at one URL**.

```
/              dashboard
/api           service information
/health        status (model, vocabulary, weights, storage)
/analyze-apk   POST an APK
/scans         scan history
```

---

## Run it locally first

```
docker compose up --build
```

Open `http://localhost:7860`. That is the same thing that gets deployed, so if
it works here it will work there.

Without Docker:

```
cd dashboard && npm install && npm run build && cd ..
python -m uvicorn api.main:app --port 7860
```

The API serves `dashboard/dist` automatically once it exists.

---

## Deploying — what is automatic and what is not

**I cannot deploy this for you, and no tool can.** Hosting requires an account,
and account creation requires a human. What *can* be automatic is everything
after the first setup: once a Space is connected, every later change rebuilds
and redeploys on its own with no further action from you.

So the honest shape is: **about ten minutes of your time once, then hands-off.**

### Hugging Face Spaces (recommended)

Free, 16 GB RAM, no cold-start spin-down, and it accepts a browser upload — so
you do not need Git installed.

1. Sign in at `huggingface.co`, then **New Space**.
2. Name it, pick **Docker** as the SDK, choose **Blank**, set it Public.
3. Upload the repository contents through **Files → Add file → Upload files**.
   Include: `Dockerfile`, `requirements.txt`, `analyzer/`, `api/`, `cve/`,
   `feature_engineering/`, `hids/`, `risk/`, `storage/`, `ml/predict.py`,
   `ml/models/`, `data/mh100k/mh100-features-all.csv`, and `dashboard/`
   (source, not `node_modules` or `dist`).
   **Do not upload** `data/mh100k/mh100.npz`, `data/mh100k/mh100_labels.csv`
   or `data/processed/` — they are training-only and total about 230 MB.
4. Rename `README_SPACE.md` to `README.md`. Its YAML header tells Spaces to
   use Docker and port 7860; without it the Space will not start.
5. **Settings → Variables and secrets**, add `NVD_API_KEY` as a secret.
6. Watch the build log. First build takes 5–10 minutes.

Your URL will be `https://<your-name>-<space-name>.hf.space`.

**From then on it is automatic.** Editing any file in the Space triggers a
rebuild and redeploy. Nothing else is needed from you.

### Why not Vercel or Render

Vercel hosts static sites and serverless functions; it will not run a
long-lived Python process that loads a model and parses APKs. Render works but
its free tier gives 512 MB of RAM and spins down after 15 minutes idle, so the
first request after a pause takes about 50 seconds. Spaces avoids both problems.

---

## "Will it appear if I search for it?"

Not immediately, and not automatically.

A deployed Space is reachable by URL straight away. Appearing in Google results
is a separate thing: a crawler has to find the page, index it, and decide to
rank it. That normally takes **days to weeks** for a new URL, and a subdomain on
a shared host rarely ranks for anything but its exact name.

If you need it findable:

- Submit the URL to Google Search Console (free, speeds up discovery)
- Add a `<meta name="description">` to `dashboard/index.html`
- Link to it from somewhere already indexed — your GitHub profile, for instance

For a project demo, sharing the URL directly is what actually matters.

---

## Environment variables

| Name | Purpose | Default |
|---|---|---|
| `ALLOWED_ORIGINS` | CORS origins. Not needed when the dashboard is served from the same origin. | localhost:5173 |
| `NVD_API_KEY` | Raises the NVD limit from 5 to 50 requests / 30 s | unset |
| `MAX_UPLOAD_MB` | Upload size limit | 150 |
| `MODEL_PATH` | Serve a different classifier: `ml/models/random_forest.joblib` or `ml/models/logistic_regression.joblib`. `linear_svm.joblib` is refused (no probability output) and `/health` says why. | selected_model.joblib |
| `SQLITE_PATH` | SQLite file location. The image sets `/app/db/mosaic.db`. | storage/mosaic.db |
| `DATABASE_URL` | PostgreSQL connection string | unset → SQLite |

---

## Persistence

SQLite is the default and needs no setup, but **a deployed container has an
ephemeral filesystem**: the database file is wiped on every restart, so scan
history does not survive. Acceptable for a demonstration.

For durable history, create a free PostgreSQL instance at `neon.tech`, set
`DATABASE_URL` to its connection string, and uncomment `psycopg[binary]` in
`requirements.txt`. `storage/history.py` switches backend automatically.

---

## Verified, and not

**Verified in development:** the single-container routing (dashboard at `/`,
API on its own paths, deep-link fallback), a real APK upload end to end through
the browser against the same-origin API, SQLite write and read-back, upload
rejection for non-APK files, and the health endpoint reporting what actually
loaded.

**Verified without Docker:** the exact files the Dockerfile copies, assembled
into a clean folder; the frontend rebuilt from scratch with `npm ci` (identical
bundle); dependencies installed from `requirements.txt` alone into a fresh
Python 3.10; the server started with the container's command; every route; the
container's HEALTHCHECK command; a real APK scan in a browser; SQLite at
`/app/db`-style path.

**Not verified:** the image itself has never been built. A Docker daemon ran,
but Docker Hub was blocked from that environment, so the base images could not
be pulled. The first `docker build` is the remaining step.

**Not verified:** NVD has never returned a record. Every test ran against a
blocked network, so the code's success path is unexercised. Add your API key
and confirm before relying on it.
