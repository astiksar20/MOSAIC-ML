> **SUPERSEDED.** Historical notes from an earlier stage. The numbers below are
> from before retraining. Current, verified results are in `START_HERE.md`.

# MOSAIC-ML — Work Package (2026-10-20)

Everything produced during the Stage 0–3 session. Unzip this **into your
repository root**; the folder structure already matches.

---

## IMPORTANT — before you copy anything

One file in here **replaces** an existing file of yours:

    api/main.py        <-- MODIFIED (your original + 150 new lines)

Everything else is new and overwrites nothing.

Back up your current copy first:

    copy api\main.py api\main.py.backup

Then, before committing anything, run this once so your diffs are readable:

    git config core.autocrlf true

Without it, `api/main.py` will show ~317 changed lines instead of the 150 that
actually changed, because your working tree uses CRLF line endings.

---

## Where each file goes

| File | Destination | New or modified |
|---|---|---|
| `api/main.py` | `api/` | **MODIFIED** — adds the `permission_risk` section |
| `risk/permission_risk.py` | `risk/` | new |
| `risk/permission_weights.json` | `risk/` | new — fitted weights |
| `requirements.txt` | repo root | new |
| `tests_permission_risk.py` | repo root | new |
| `scripts/*.py` | `scripts/` | new |
| `notebooks/*.ipynb` | `notebooks/` | new |
| `reports/**` | `reports/` | new |

---

## Add this to `.gitignore` BEFORE staging

    data/processed/
    reports/results/feature_frequency_by_class.csv
    reports/results/nonzero_features_per_app.csv
    reports/results/*.npy

`data/processed/` is not in this zip. It holds a 135 MB converted matrix that
exceeds GitHub's 100 MB file limit. Regenerate it locally (see below) — it is
not meant to live in version control.

---

## Reproducing everything

Order matters: later scripts depend on the converted matrix.

```
pip install -r requirements.txt

# 1. Convert the dense matrix to sparse (creates data/processed/, ~2 min)
#    Needed because mh100.npz stores a DENSE 2.53 GB array, which is what
#    caused the earlier MemoryError.
python scripts/convert_to_csr.py

# 2. Audit the dataset
python scripts/audit_dataset.py

# 3. Train and compare the models (~10 min)
python scripts/run_stage2_comparison.py

# 4. Fit the permission weights on the training split
python scripts/fit_permission_weights.py

# 5. Compare the two analyses
python scripts/compare_two_analyses.py

# 6. Figures
python scripts/make_stage1_figures.py
python scripts/make_stage2_figures.py
python scripts/make_stage3_figures.py

# 7. Tests
python tests_permission_risk.py
```

---

## Measured results (not estimates)

### Model comparison — validation split, deduplicated, seed 42

| Model | Accuracy | Balanced acc. | Malware recall | Malware F1 | FPR |
|---|---|---|---|---|---|
| **Logistic Regression** | 0.9738 | **0.9598** | 0.9409 | 0.9039 | 0.0212 |
| Linear SVM | 0.9674 | 0.9573 | 0.9435 | 0.8836 | 0.0289 |
| Random Forest (100) | 0.9736 | 0.9527 | 0.9243 | 0.9016 | 0.0190 |
| Random Forest (30) | 0.9729 | 0.9493 | 0.9174 | 0.8986 | 0.0187 |
| Decision Tree | 0.9562 | 0.9017 | 0.8278 | 0.8318 | 0.0245 |
| Bernoulli NB | 0.8642 | 0.8949 | 0.9365 | 0.6436 | 0.1467 |
| *CONTROL: active-count only* | 0.9450 | 0.8794 | 0.7904 | 0.7901 | 0.0317 |

Final test, evaluated once, Logistic Regression: **accuracy 0.9704**,
balanced accuracy 0.9494, malware recall 0.9209, ROC-AUC 0.9763.
Confusion matrix: TN 7,467 · FP 169 · FN 91 · TP 1,060.

### Permission-risk score — held-out test split

ROC-AUC 0.7734 · PR-AUC 0.2804 · defined for 84.9% of apps.
Mean score: benign 0.646, malware 0.691 — heavy overlap.

---

## Known problems, unfixed

1. **Feature mapper reaches 0.67% of the model.** The analyzer never extracts
   intents or API calls, so 24,667 of 24,833 features (99.33%) are unreachable.
   Measured: the real test APK scores P(malware)=0.1333; an all-zero vector
   scores 0.1250. The ML output is not usable evidence until this is fixed.

2. **NVD failure crashes the whole endpoint.** Confirmed by an actual HTTP 500
   during testing: `search_cve()` has no exception handling, so any network
   error, 403 or 429 rate-limit takes down the entire `/analyze-apk` request.
   Nothing is returned — no ML result, no permission score.

3. **HIDS telemetry is synthetic**, hardcoded in `api/main.py`.

4. **No CORS middleware, no upload validation, no environment variables.**
   All three block deployment.

5. **42.54% of MH-100K rows are duplicates**; 296 duplicate groups carry
   conflicting labels.

---

## Things to be careful about in the paper

- The dataset has a shortcut: a model using only the *count* of active features
  scores 0.9450 accuracy. Real models beat it by just +2.9 points on accuracy,
  but by **+15 points on malware recall**. Report balanced accuracy and recall,
  never accuracy alone.
- MH-100K labels are `vt_detection >= 4` (verified at 100% agreement). The
  `CLASS` column in `mh100_labels.csv` disagrees on 10,505 rows and matches no
  threshold — do not use it.
- 10,992 apps flagged by 1–3 VirusTotal engines are labelled benign (greyware).
- 172 apps have `vt_detection = -1` (no scan result) and are labelled benign.
- MH-100K spans 2010–2022. Nothing here supports claims about current APKs.
- The permission-risk formula is an **adaptation** of Ogwara et al. (2024),
  evaluated on MH-100K. They did not validate this implementation.
- NVD connectivity was **never tested** — the analysis environment blocked it.

---

## Citations (verified against the originals)

Bragança, H., Rocha, V., Barcellos, L., Souto, E., Kreutz, D., & Feitosa, E.
(2023). Android malware detection with MH-100K: An innovative dataset for
advanced research. *Data in Brief*, 51, 109750.
https://doi.org/10.1016/j.dib.2023.109750

> Note: first author is **Bragança**, not Rocha. Published size is 101,975
> samples; your local copy has 101,934.

Ogwara, N. O., Petrova, K., Yang, M. L., & MacDonell, S. G. (2024). A Risk
Assessment Framework for Mobile Apps in Mobile Cloud Computing Environments.
*Future Internet*, 16(8), 271. https://doi.org/10.3390/fi16080271

Molina-Coronado, B., Mori, U., Mendiburu, A., & Miguel-Alonso, J. (2023).
Towards a fair comparison and realistic evaluation framework of Android malware
detectors based on static analysis and machine learning. *Computers & Security*,
124, 102996. https://doi.org/10.1016/j.cose.2022.102996
