# MOSAIC-ML — Android Vulnerability and Intrusion Risk Analysis

A static Android risk-analysis system that keeps its evidence **separate**:
an ML malware classifier, a permission-risk score, a CVE/NVD lookup and a
HIDS prototype are each reported with their own reliability, instead of being
merged into one opaque number.

Upload an APK → the dashboard shows feature coverage, the ML verdict, the
permission score, CVE results and the scan history.

---

## Run it (Windows / macOS / Linux)

Needs Python 3.10. No Docker, no Node.js required — the built dashboard is included.

```bash
python -m pip install -r requirements.txt
python -m uvicorn api.main:app --port 7860
```

Open **http://127.0.0.1:7860** and upload `test_apks/com.github.yeriomin.smsscheduler_5.apk`.

| URL | What |
|---|---|
| `/` | Dashboard |
| `/health` | Status: model, vocabulary, weights, storage |
| `/docs` | Interactive API (Swagger) |
| `/analyze-apk` | `POST` an APK |
| `/scans` | Scan history (SQLite; PostgreSQL via `DATABASE_URL`) |

Frontend dev server (optional): `cd dashboard && npm install && npm run dev`, with the backend on port 8000.
Docker (optional): `docker compose up --build`. See `DEPLOY.md`.

---

## Results (MH-100K, verified by execution)

Deduplicated to **58,576 unique apps** (13.1% malware), stratified 70/15/15,
seed 42. Three alternative models, 9 configurations scored on **validation
only**; the test split was evaluated **once**.

| Best of each model (validation) | Accuracy | Balanced acc. | Malware recall | F1 | ROC-AUC |
|---|---|---|---|---|---|
| **Logistic Regression** (class-weighted) ← selected | 0.9680 | **0.9631** | **0.9565** | 0.8867 | 0.9793 |
| Linear SVM (class-weighted, C = 0.1) | 0.9660 | 0.9612 | 0.9548 | 0.8802 | 0.9767 |
| Random Forest, 30 trees (class-weighted) | 0.9735 | 0.9504 | 0.9191 | 0.9007 | 0.9823 |
| *Control: feature count only* | *0.9450* | *0.8794* | *0.7904* | *0.7901* | — |

**Final test (once):** accuracy 0.9675 · balanced accuracy **0.9569** ·
precision 0.8314 · recall **0.9427** · F1 0.8836 · MCC 0.8670 · ROC-AUC 0.9785.
Confusion: TN 7,416 · FP 220 · FN 66 · TP 1,085.

**Why the control matters:** a model that sees only *how many* features an
app has scores 0.945 accuracy, because malware in MH-100K has a median of 42
active features vs 2,082 for benign apps. Accuracy alone is misleading here;
the real models beat the control by 16.6 points of malware recall.

**Permission risk** (Ogwara et al., 2024): `r = √(α(1−β))`, `R(a) = Σ r / k`,
undefined (not 0) when k = 0. Weights fitted on the training split only.
Test ROC-AUC 0.7734: a corroborating signal, not a standalone detector.

Reproducible: `notebooks/MOSAIC_ML_Model_Training.ipynb` re-runs the whole
search and prints **MATCH** against the shipped numbers.

---

## Repository layout

| Path | Contents |
|---|---|
| `api/` | FastAPI backend; also serves the dashboard |
| `analyzer/`, `feature_engineering/` | Androguard static extraction, vocabulary mapping, coverage |
| `ml/` | `predict.py` + trained models (`selected_model.joblib`) |
| `risk/` | Permission-risk scoring and fitted weights |
| `cve/` | NVD client (records / zero / failed reported separately) |
| `hids/` | HIDS prototype (synthetic data, labelled as such) |
| `storage/` | SQLite / PostgreSQL scan history |
| `dashboard/` | React frontend (`dist/` is prebuilt) |
| `scripts/` | Data conversion, training (`tune_models.py`), figures, paper |
| `notebooks/` | Executed Colab notebook |
| `reports/` | Figures, result JSON/CSV, evidence screenshots |
| `MOSAIC-ML_IEEE_Paper.docx` / `.pdf` | Paper (sample draft) |
| `MOSAIC-ML_Evidence.docx` | Screenshots and outputs as proof |

## Retraining

Download MH-100K (Bragança et al., *Data in Brief* 51, 2023) into `data/mh100k/`, then:

```bash
python scripts/convert_to_csr.py      # must produce 135.5 MB
python scripts/tune_models.py         # 9 configurations, ~15 min, 3–4 GB RAM
python scripts/make_model_figures.py
```

## Honest limitations

Single split, no confidence intervals, no probability calibration · corpus
spans 2010–2022 · HIDS data is synthetic · NVD matches are keyword candidates ·
the 40/40/20 combined score is a deprecated prototype formula · the Docker
image has not yet been built on a real machine.

**Author:** Astik Sarkar
