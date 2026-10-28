# MOSAIC-ML — Stage 0 / Stage 1 Audit Report

**Date:** 2026-10-19
**Scope:** Repository audit (Stage 0) and data/feature pipeline verification (Stage 1).
**Method:** Every number below was produced by running code against the actual
repository contents. Items that were not executed are stated as not run.

---

## 1. Repository state

| Item | Finding |
|---|---|
| Branch | `main`, 1 commit behind `origin/main` |
| Incoming commit | `6137c12` — adds `README.md` only (69 lines). Safe to pull. |
| Working tree | 13 files shown as modified |
| **Real** uncommitted change | **`.gitignore` only (+4 lines)** |
| Other 12 files | Differ by **CRLF line endings only** (`git diff --ignore-all-space` is empty) |
| Dependency manifest | **Absent** — no `requirements.txt`, `pyproject.toml`, or lockfile for the backend |

**No work has been lost.** The alarming 13-file diff is a line-ending artifact.

Recommended before any further change:

```
git config core.autocrlf true
git add .gitignore && git commit -m "Update .gitignore"
git pull --ff-only
```

### Module inventory (all present, all readable)

| Module | Lines | State |
|---|---|---|
| `analyzer/apk_analyzer.py` | 34 | Works. Extracts permissions, activities, services, receivers, providers. |
| `feature_engineering/apk_feature_mapper.py` | 122 | Works but structurally incomplete — see §4. |
| `ml/train_model.py` | 72 | Works. Densifies the matrix (2.53 GB spike). |
| `ml/baseline.py` | 64 | Works. Produced the recorded 97.50% result. |
| `ml/predict.py` | 42 | Works. |
| `ml/random_forest_model.joblib` | 15.8 MB | Genuine `RandomForestClassifier`, 30 trees, `n_features_in_=24833`, `classes_=[0 1]`, saved with scikit-learn **1.6.1**. |
| `cve/nvd_client.py` | 133 | Parser fully implemented (CVSS v3.1/v3.0/v2 + CWE). Operational gaps in §6. |
| `hids/*.py` | 288 | Works. Telemetry is hard-coded synthetic. |
| `risk/risk_engine.py` | 122 | Contains the unsupported 40/40/20 weighted sum. |
| `api/main.py` | 317 | `GET /`, `GET /health`, `POST /analyze-apk` all present. |
| `dashboard/` | React + Vite | `axios`, `lucide-react`. Build: `vite build` → `dist`. |

---

## 2. Dataset structure (verified, not assumed)

`data/mh100k/mh100.npz` is **not** a SciPy sparse archive. It is a plain `.npz`
containing six arrays:

| Array | Shape | Meaning |
|---|---|---|
| `data` | (101934, 24833) `int8` | Feature matrix, stored **dense** |
| `column_names` | (24833,) | Feature vocabulary |
| `classes` | (101934,) | Labels |
| `sha256` | (101934,) | Per-row APK hash |
| `metadata` | (101934, 9) | Full metadata table |
| `metadata_columns` | (9,) | Column names for the above |

**The dense `data` array is 2.53 GB in memory.** This is the direct cause of the
earlier Random Forest `MemoryError`. A CSR conversion has been written to
`data/processed/mh100_csr.npz` (135 MB on disk, 185,917,518 stored non-zeros).
`data/mh100k/` was not modified.

### Vocabulary — the published structure is confirmed exactly

| Block | Local count | Published (Bragança et al. 2023) | Match |
|---|---|---|---|
| `Permission::` | 166 | 166 | yes |
| `Intent::` | 250 | 250 | yes |
| `APICall::` | 24,417 | 24,417 | yes |
| **Total** | **24,833** | **24,833** | yes |

Vocabulary order in `mh100-features-all.csv` matches `column_names` in the `.npz`.

> **Trap:** the `index` column in `mh100-features-all.csv` starts at **5**, not 0.
> It indexes the *original* dataframe, which carried 5 leading metadata columns.
> Using it as a matrix column position would be off by 5. The current mapper does
> not use it (it uses row order), so the mapper is correct here — but any future
> code that reads that column must subtract 5.

### Row counts

| Source | Rows |
|---|---|
| `mh100.npz` matrix | 101,934 |
| `mh100_labels.csv` (parsed with a CSV reader) | 101,934 |
| Published MH-100K | 101,975 |

**Correction to earlier project notes:** `wc -l` reports 101,976 lines for the
labels CSV, but the correct parsed row count is **101,934** — several app-name
fields contain embedded newlines. The local copy is 41 samples short of the
published 101,975; that gap is in the downloaded source data, not in processing.

### Row alignment is PROVEN, not assumed

Matching `.npz` `sha256` against the CSV `SHA256` column positionally:
**101,934 / 101,934 (100.00%) agreement, in order.** Row *i* of the matrix is
row *i* of the labels file.

---

## 3. The label conflict — resolved

Two different label sets exist in the data, and they disagree on **10,505 rows**.

| Label source | Benign | Malware |
|---|---|---|
| `.npz` `classes` (used by all training code) | 92,134 | 9,800 |
| CSV `CLASS` column | 89,213 | 12,721 |

Tested against the `vt_detection` column (number of VirusTotal engines flagging):

| Rule | Agreement with `.npz` `classes` |
|---|---|
| `vt_detection >= 3` | 98.56% |
| **`vt_detection >= 4`** | **100.00%** |
| `vt_detection >= 5` | 98.48% |

The CSV `CLASS` column matches **no** threshold (best 92.08% at `>= 1`).

**Conclusion: use the `.npz` `classes`.** It is exactly `vt_detection >= 4` — a
defined, reproducible rule. The existing training code already uses it. The CSV
`CLASS` column should be treated as unreliable and not used.

Document the threshold as a project decision, and note that Ogwara et al. (2024)
used a stricter `>= 15` on their own sample. Threshold choice is a good
sensitivity-analysis axis for the paper.

### Label-quality caveats (all counted, not estimated)

- **10,992 apps** flagged by 1–3 engines are labelled **benign** — greyware.
- **172 apps** have `vt_detection = -1` (no VT result) and are labelled **benign**;
  "unknown" is being folded into "benign".

---

## 4. Feature mapper — the central defect

Measured on the real fixture `test_apks/com.github.yeriomin.smsscheduler_5.apk`:

| Measurement | Value |
|---|---|
| Permissions declared by the APK | 5 |
| Features matched into the 24,833-dim vector | **5 (0.0201%)** |
| Candidate strings generated by the mapper | 18 |
| Candidate strings that exist in the vocabulary | 5 |

**This is not a matching bug.** All 5 of the APK's `android.permission.*` entries
were mapped correctly. The defect is structural:

1. The mapper emits `Activity::`, `Service::`, `Receiver::`, `Provider::` prefixes.
   **None of these exist anywhere in the vocabulary.** 13 of the 18 generated
   strings are dead by construction.
2. The mapper emits **zero** `Intent::` and **zero** `APICall::` features.
   That is **24,667 of 24,833 features (99.33%) unreachable by construction.**

The analyzer never extracts intents or API calls, so the mapper has nothing to map.

### Consequence, measured

| Input | Model output P(malware) |
|---|---|
| Real APK vector (5 features) | **0.1333** |
| All-zero vector (0 features) | **0.1250** |

The entire static analysis moves the prediction by **0.0083**. The current ML
output is, in practice, the model's response to an empty input.

For context: training apps carry a mean of **1,824** active features (median 1,993).
Only **5 of 101,934** training apps (0.0049%) have ≤ 5 active features. The
production input is far outside the training distribution.

**The ML section of the API response is not currently usable evidence.**

---

## 5. A dataset shortcut that undermines the 97.5% headline

Active-feature counts differ enormously by class:

| Class | Median active features | % with < 100 active |
|---|---|---|
| Benign | 2,082 | 2.9% |
| Malware | 42 | **78.3%** |

A classifier using **one** input — the count of active features, ignoring *which*
features — achieves on the same stratified split:

| Model | Accuracy | Balanced acc. | Malware F1 | ROC-AUC |
|---|---|---|---|---|
| **Count only (1 feature, depth-3 tree)** | **0.9516** | 0.8542 | 0.7445 | 0.9296 |
| Recorded Random Forest (24,833 features) | 0.9750 | not recorded | 0.87 | not recorded |

The 24,833-feature model is only ~2.3 accuracy points above a single-number
shortcut. This strongly suggests many malware APKs failed API-call extraction
(packing/obfuscation/DEX parse failure), leaving near-empty rows — so the model
can learn "extraction produced little" rather than genuine malicious behaviour.

This must appear in threats to validity. It also means **accuracy alone is not a
defensible selection metric**, and the count-only control belongs in the
comparison table as a baseline.

---

## 6. Other verified findings

### Duplicates
- **43,358 duplicate rows (42.54%)**; only **58,576 of 101,934 rows are unique**
  (identical sets of active feature indices).
- **296 duplicate groups carry conflicting labels** — identical features, different
  labels. These are an irreducible error floor for any model.
- Random splitting places copies of the same app in both train and test. This
  inflates every reported metric (Molina-Coronado et al. 2023, factor 1).

### API (`api/main.py`)
- `GET /`, `GET /health`, `POST /analyze-apk` all present.
- Temporary file cleanup **is** handled in a `finally` block with `os.remove`.
- **No CORS middleware at all** — a deployed frontend on another origin will be
  blocked by the browser. Blocks Stage 8.
- **No upload validation** — no extension check, no size limit.
- **No environment variables** anywhere in `api/` or `cve/` — model path, NVD key
  and CORS origins are all hard-coded. Blocks deployment.
- Response sections present: `apk_analysis`, `ml_analysis`, `risk_analysis`.
  **Missing:** `permission_risk`, `feature_coverage`, `limitations`.
- Frontend already reads `import.meta.env.VITE_API_URL` (note: the master prompt
  says `VITE_API_BASE_URL` — pick one name and use it consistently).

### CVE / NVD (`cve/nvd_client.py`)
- The parser is **fully implemented** and correctly handles `cvssMetricV31`,
  `cvssMetricV30`, `cvssMetricV2` and CWE.
- **Not tested live** — this audit environment blocks `services.nvd.nist.gov`
  at the proxy (403). Must be run on your machine.
- No API key support → 5 requests / 30 s. With a key it is 50 / 30 s.
- No retry, no backoff, no delay between requests.
- `raise_for_status()` is not wrapped — a 403/429 will crash the whole
  `/analyze-apk` request rather than degrade.
- It searches **every** component (18 for the test APK) → rate limiting is certain.
- Search terms are raw permission/component names (e.g. `android.permission.SEND_SMS`).
  These are not products; keyword hits on them cannot establish affectedness.
- No CVSS v4.0 handling.

### HIDS
- Telemetry is hard-coded in `api/main.py`:
  `["normal_file_access", "unexpected_sms", "unknown_network_connection"]`.
  Confirmed synthetic; unrelated to the uploaded APK.

### Risk engine
- The 40% ML / 40% HIDS / 20% CVSS weighted sum is present as described.
- Its `__main__` example uses `ml_probability = 0.1333` — the exact value produced
  by the near-empty feature vector.

---

## 7. What was NOT run

- NVD live queries — blocked by this environment's proxy.
- Retraining of any model — the recorded 97.50% has **not** yet been reproduced.
- The frontend build (`npm install` / `vite build`).
- Any end-to-end `POST /analyze-apk` request.
- No repository source file was modified during this audit.

---

## 8. Smallest safe plan, in priority order

1. **Extract intents and API calls** in `analyzer/apk_analyzer.py` and emit
   `Intent::` / `APICall::` features in the mapper. Everything downstream depends
   on this. Remove the dead `Activity::`/`Service::`/`Receiver::`/`Provider::` paths.
2. **Add a coverage gate** to the API: report matched count and percentage, and
   refuse to present a confident ML verdict below a threshold set in advance.
3. **Deduplicate before splitting**, and split by unique feature row so copies
   cannot straddle train and test.
4. **Add the count-only control** to the model comparison so the real contribution
   of the 24,833 features is visible.
5. Add `requirements.txt`, CORS, upload validation and environment variables
   before any deployment attempt.
6. Keep using `.npz` `classes` (VT ≥ 4). Do not use the CSV `CLASS` column.

---

## Artifacts produced by this audit

| Path | Contents |
|---|---|
| `reports/results/dataset_audit.json` | Full machine-readable audit record |
| `reports/results/dataset_audit_summary.csv` | Flat metric table for the appendix |
| `reports/results/feature_frequency_by_class.csv` | Per-feature counts by class (whole dataset — **exploratory only**; Stage 3 must recompute on the training split) |
| `reports/results/nonzero_features_per_app.csv` | Source data for Figure 3 |
| `reports/results/fig02_class_distribution.csv` | Source data for Figure 2 |
| `reports/results/fig03_sparsity_stats.json` | Source data for Figure 3 |
| `reports/figures/fig02_class_distribution.png` | Figure 2 |
| `reports/figures/fig03_sparsity.png` | Figure 3 |
| `data/processed/mh100_csr.npz` | CSR matrix (fixes the MemoryError) |
| `data/processed/mh100_meta.npz` | Vocabulary, labels, hashes, metadata |
| `scripts/audit_dataset.py` | Regenerates the audit |
| `scripts/make_stage1_figures.py` | Regenerates Figures 2 and 3 |

---

# Stage 2 — Model comparison (EXECUTED)

Run locally on the real data with `scripts/run_stage2_comparison.py`.
Protocol: deduplicated to **58,576 unique rows**, stratified **70/15/15**,
seed 42, labels `vt_detection >= 4`. Test split evaluated **once**.

Split sizes: train 41,003 · validation 8,786 · test 8,787.

## Validation results (all measured)

| Model | Accuracy | Balanced acc. | Macro F1 | Malware recall | Malware F1 | FPR | ROC-AUC | Fit (s) |
|---|---|---|---|---|---|---|---|---|
| **Logistic Regression** | **0.9738** | **0.9598** | 0.9444 | 0.9409 | 0.9039 | 0.0212 | 0.9795 | 45.0 |
| Linear SVM | 0.9674 | 0.9573 | 0.9323 | 0.9435 | 0.8836 | 0.0289 | 0.9756 | 128.9 |
| Random Forest (100) | 0.9736 | 0.9527 | 0.9432 | 0.9243 | 0.9016 | 0.0190 | 0.9839 | 233.3 |
| Random Forest (30) | 0.9729 | 0.9493 | 0.9415 | 0.9174 | 0.8986 | 0.0187 | 0.9822 | 70.0 |
| Decision Tree | 0.9562 | 0.9017 | 0.9033 | 0.8278 | 0.8318 | 0.0245 | 0.9017 | 88.0 |
| Bernoulli NB | 0.8642 | 0.8949 | 0.7798 | 0.9365 | 0.6436 | 0.1467 | 0.8964 | 0.7 |
| **CONTROL: active-count only** | 0.9450 | 0.8794 | 0.8792 | 0.7904 | 0.7901 | 0.0317 | 0.9452 | 0.01 |

## Final test result (evaluated once, Logistic Regression)

| Metric | Value |
|---|---|
| Accuracy | 0.9704 |
| Balanced accuracy | 0.9494 |
| Macro F1 | 0.9368 |
| Malware precision | 0.8625 |
| Malware recall | 0.9209 |
| Malware F1 | 0.8908 |
| False positive rate | 0.0221 |
| False negative rate | 0.0791 |
| ROC-AUC | 0.9763 |
| PR-AUC | 0.9021 |
| Confusion matrix | TN 7,467 · FP 169 · FN 91 · TP 1,060 |

**91 malware samples were missed; 169 benign apps were wrongly flagged.**

## Two findings that change project decisions

**1. Logistic Regression beats Random Forest.** On balanced accuracy LR scores
0.9598 against RF's 0.9527, trains 5× faster (45 s vs 233 s), and produces a far
smaller artifact than a 15.8 MB forest. The project's assumption that Random
Forest is the right model is not supported. RF does win on ROC-AUC (0.9839) and
FPR (0.0190), so state the trade-off rather than declaring a single winner.

**2. The shortcut control explains most of the raw accuracy, but not the
detection capability.** Gains of the best model over the one-number control:

| Metric | Best | Control | Gain |
|---|---|---|---|
| Accuracy | 0.9738 | 0.9450 | **+0.0288** |
| Balanced accuracy | 0.9598 | 0.8794 | **+0.0805** |
| Malware F1 | 0.9039 | 0.7901 | **+0.1138** |
| Malware recall | 0.9409 | 0.7904 | **+0.1504** |

On accuracy alone the 24,833 features look almost worthless (+2.9 points). On
malware recall they are worth **+15 points**. This is the clearest possible
demonstration of why accuracy is the wrong headline metric for this dataset, and
it belongs in the paper as a result in its own right, not just a caveat.

## Relationship to the previously recorded 97.50%

The earlier figure came from a different protocol: all 101,934 rows (duplicates
retained), 80/20 split, no validation split. It is **not** directly comparable to
the numbers above, which use deduplicated data and a sealed test split. The
earlier number was not reproduced under its original protocol; that remains
outstanding if a like-for-like comparison is wanted.

## Stage 2 caveats

- Single split. No repeated runs, no confidence intervals.
- No probability calibration was fitted or evaluated. Do not describe any output
  as a calibrated probability.
- KNN was not run (cost on 24,833 sparse dimensions).
- No hyperparameter search was performed; defaults plus two RF sizes.
- These numbers describe MH-100K (2010–2022). They say nothing about live scan
  behaviour, because the feature mapper reaches only 0.0201% of the vocabulary
  at scan time.

## Stage 2 artifacts

| Path | Contents |
|---|---|
| `notebooks/MOSAIC_ML_Stage2_Model_Comparison.ipynb` | Google Colab notebook, same protocol |
| `scripts/run_stage2_comparison.py` | Local runner that produced the tables above |
| `scripts/make_stage2_figures.py` | Regenerates Figures 4 and 5 |
| `reports/results/model_comparison_validation.csv` | Full validation table |
| `reports/results/final_test_result.csv` | Single test evaluation |
| `reports/results/stage2_run_record.json` | Seeds, versions, split sizes, all metrics |
| `reports/figures/fig04_model_comparison.png` | Figure 4 |
| `reports/figures/fig05_confusion_matrices.png` | Figure 5 |
| `requirements.txt` | Pins scikit-learn 1.6.1 to match the saved model |
