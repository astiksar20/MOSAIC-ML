# MOSAIC-ML — Final Package

**2026-10-24.** Every number here was produced by executing the code in this
folder. Nothing is estimated.

**To run the demo, open `RUN_DEMO.md`.** Three commands, no training needed.

---

## What changed in this version

1. **Retrained on the corrected data** with a proper search: 9 configurations
   across the three models, each scored on validation only. The test split was
   used once, by the winner.
2. **New selected model: class-weighted Logistic Regression.** It misses 20
   fewer malware apps than before on the same test set (66 vs 86).
3. **All graphs regenerated** (Figures 2–11) from the corrected matrix, with
   the numbers behind each graph saved as CSV.
4. **Docker fixed**: Python 3.10 to match training; the database volume no
   longer hides code.
5. **The dashboard names the model actually loaded**, not a hardcoded one.
6. **Linear SVM is refused by the API with a clear message** instead of
   crashing a scan. It outputs no probability, and one cannot be invented.

---

## Verified results

Deduplicated to **58,576 unique apps** (malware 13.1%). Stratified 70/15/15,
seed 42. Python 3.10.20, scikit-learn 1.6.1, NumPy 1.26.4, SciPy 1.15.3.

### All 9 configurations tried (validation, n = 8,786)

| Configuration | Balanced acc. | Malware recall | Malware F1 | FPR |
|---|---|---|---|---|
| LR C=1 | 0.9598 | 0.9417 | 0.9017 | 0.0221 |
| **LR C=1 class-weighted** ← selected | **0.9631** | **0.9565** | 0.8867 | 0.0303 |
| LR C=0.1 class-weighted | 0.9630 | 0.9565 | 0.8860 | 0.0305 |
| LR C=10 class-weighted | 0.9630 | 0.9557 | 0.8877 | 0.0297 |
| SVM C=1 | 0.9573 | 0.9435 | 0.8836 | 0.0289 |
| SVM C=1 class-weighted | 0.9594 | 0.9530 | 0.8740 | 0.0343 |
| SVM C=0.1 class-weighted | 0.9612 | 0.9548 | 0.8802 | 0.0323 |
| RF 30 trees | 0.9493 | 0.9174 | 0.8986 | 0.0187 |
| RF 30 trees class-weighted | 0.9504 | 0.9191 | **0.9007** | **0.0183** |
| *Control: feature count only* | *0.8794* | *0.7904* | *0.7901* | *0.0317* |

### Best of each model (validation)

| Model | Accuracy | Balanced | Recall | Precision | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|---|
| Logistic Regression | 0.9680 | **0.9631** | **0.9565** | 0.8264 | 0.9793 | 0.9050 |
| Linear SVM | 0.9660 | 0.9612 | 0.9548 | 0.8164 | 0.9767 | 0.8742 |
| Random Forest (30) | **0.9735** | 0.9504 | 0.9191 | **0.8830** | **0.9823** | **0.9052** |

Random Forest has the highest accuracy and precision; Logistic Regression
catches the most malware. Selection was on balanced accuracy, decided in
advance, so Logistic Regression was selected.

### Final test, evaluated once (Logistic Regression, class-weighted)

| Accuracy | Balanced | Precision | Recall | F1 | FPR | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|---|---|
| 0.9675 | **0.9569** | 0.8314 | **0.9427** | 0.8836 | 0.0288 | 0.9785 | 0.8978 |

Confusion matrix: TN 7,416 · FP 220 · **FN 66** · TP 1,085.

### Compared with the previous model, same test set

| | Before (LR, unweighted) | Now (LR, class-weighted) |
|---|---|---|
| Malware missed | 86 | **66** |
| Recall | 0.9253 | **0.9427** |
| Balanced accuracy | 0.9515 | **0.9569** |
| Accuracy | **0.9709** | 0.9675 |
| False alarms | **170** | 220 |

Accuracy went *down* slightly while detection went *up*. For a malware
detector that is the right trade, and it is reported as it is.

### Why accuracy alone is misleading here

- Predicting "benign" for everything scores **0.869** accuracy.
- A model given only the *count* of active features scores **0.9450**.
- Malware apps have a median of **42** active features vs **2,082** for benign
  (Figure 3), so feature count alone is a strong shortcut.

On validation, the selected model beats the count-only control by **16.6 points of recall** (0.9565 vs 0.7904).

### Permission risk score (Analysis A)

Weights fitted on the training split only. Refitting on the corrected matrix
reproduced **identical** weights. READ_PHONE_STATE 0.7947 (highest), SEND_SMS
0.3399 (lowest). Test ROC-AUC **0.7734**, PR-AUC **0.2804**, defined for 84.9%
of apps.

### The two analyses together (Figure 11, test split)

- Correlation between the two scores: **0.30**, so they carry different
  information.
- When both flag an app it is malware **87.0%** of the time, vs **83.1%** when
  only the ML model flags it: **+3.8 points**.
- When only the permission score flags it: **1.4%** malware. As a standalone
  detector it fails.

So the permission score can *confirm* an ML flag but must never *overrule* it.

---

## Figures (`reports/figures/`)

| Figure | Shows | Data |
|---|---|---|
| 2 | Class distribution (raw 101,934 apps) | `fig02_class_distribution.csv` |
| 3 | Sparsity and the feature-count shortcut | `fig03_sparsity_stats.json` |
| 4 | Six metrics, three models + control | `fig04_model_comparison.csv` |
| 5 | Confusion matrices, validation + final test | `fig05_confusion_matrices.csv` |
| 6 | ROC and precision-recall curves | `fig06_roc_points.csv`, `fig06_pr_points.csv` |
| 7 | Threshold trade-off for the selected model | `fig07_threshold_analysis.csv` |
| 8 | All 9 configurations tried | `fig08_tuning_grid.csv` |
| 9 | Permission weights | `risk/permission_weights.json` |
| 10 | Permission score evaluation | `permission_risk_evaluation.json` |
| 11 | The two analyses compared | `two_analyses_comparison.json` |

The figure script reloads the saved models and checks they reproduce the
recorded confusion matrices exactly before drawing anything. They do.

### Colab notebook

`notebooks/MOSAIC_ML_Model_Training.ipynb` runs the same 9-configuration search
with the same protocol and draws Figures 4, 5, 6 and 8. It is shipped
**already executed**, so its outputs and graphs show without running it. Its
last section compares its numbers with the shipped ones. The older notebook,
which trained seven models, is in `notebooks/_superseded/`, as are its result
files in `reports/results/_superseded/`.

---

## Docker

```
docker compose up --build
```

Then open http://localhost:7860.

**Honest status:** the image itself has not been built. Docker Hub is blocked
from the environment this was made in. What *was* verified: the exact files
the Dockerfile copies, assembled into a clean folder; the frontend built from
scratch with `npm ci` (same bundle as shipped); Python dependencies installed
from `requirements.txt` alone into a fresh Python 3.10; the server started with
the container's own command; every route, the container's HEALTHCHECK command,
a real APK scan in a browser, and SQLite at the container's database path. The
first real `docker build` is the remaining unverified step.

---

## Retraining (optional)

Needs MH-100K in `data/mh100k/` and 3–4 GB free RAM.

```
python scripts\convert_to_csr.py          # must give 135.5 MB, NOT 275 MB
python scripts\tune_models.py             # 9 configurations, ~15 min
python scripts\make_model_figures.py      # Figures 4-8
python scripts\make_stage1_figures.py     # Figures 2-3
python scripts\fit_permission_weights.py  # weights + Figure 10 data
python scripts\make_stage3_figures.py     # Figures 9-10
python scripts\compare_two_analyses.py    # Figure 11
```

`scripts/train_and_evaluate.py` is the **previous** trainer (unweighted, 3
fixed configs). It still works, but running it overwrites the models and the
results above. Use `tune_models.py`.

**Never run** `scripts/_BROKEN_convert_to_csr_streaming.py.bak`. It is the
script that corrupted the matrix (it misreads MH-100K's column-major layout).

---

## The research paper and the evidence document

- `MOSAIC-ML_IEEE_Paper.docx` (+ `.pdf` preview): the sample draft, updated with
  the final verified results and verified 2025-2026 references. Regenerate with
  `node scripts/make_paper.js`. Every number in it is taken from
  `reports/results/`.
- `MOSAIC-ML_Evidence.docx`: 34 screenshots and graphs as proof (notebook run,
  results, graphs, dashboard, backend API, database, tests). Sources are in
  `reports/evidence/`, `reports/notebook_proof/` and `reports/figures/`.
  Regenerate with `node scripts/make_evidence_doc.js`.

**Dataset count:** the MH-100K article reports 101,975 samples; the released
feature matrix and label file both contain 101,934 rows. The paper states this.

## Still not built or not verified

- Docker image never built (see above).
- NVD has never returned a record: every run was on a blocked network. Add
  `NVD_API_KEY` and confirm.
- HIDS telemetry is synthetic, hardcoded in `api/main.py`, and labelled so.
- The 40/40/20 aggregate is a prototype formula, marked `DEPRECATED_PROTOTYPE`.
- No probability calibration; single split, no confidence intervals.
- Manifest security checks (exported components, `debuggable`, cleartext).

---

## Corrections on record

- The original chance-level results were caused by a **corrupt feature
  matrix**, not a scikit-learn version mismatch. I diagnosed the version
  mismatch first and that was wrong.
- I earlier described the class ratio as ~10% malware. That holds for the raw
  101,934 apps; after deduplication it is **13.1%**, so the all-benign baseline
  is 0.869, not 0.90.
