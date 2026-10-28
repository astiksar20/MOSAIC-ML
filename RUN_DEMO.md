# MOSAIC-ML — Run the demo (Windows, PowerShell)

Everything needed is in this folder: trained models, the built dashboard, and a
test APK. **No training, no npm, no Docker needed for the demo.**

Needs: Python 3.10 (what you already have). About 500 MB free RAM.

---

## 1. Unzip

Unzip to `D:\MOSAIC-ML` so the path is `D:\MOSAIC-ML\api\main.py`.

## 2. Install (one time, ~3 minutes)

```powershell
cd D:\MOSAIC-ML
python -m pip install -r requirements.txt
```

Check the versions match the trained models:

```powershell
python -c "import sklearn, numpy, scipy; print(sklearn.__version__, numpy.__version__, scipy.__version__)"
```

Expect exactly: `1.6.1 1.26.4 1.15.3`

## 3. Start the app

```powershell
python -m uvicorn api.main:app --port 7860
```

Wait for `Application startup complete`.

## 4. Open it

Go to **http://127.0.0.1:7860** in your browser.

- The header should say the API is **online**.
- Upload `D:\MOSAIC-ML\test_apks\com.github.yeriomin.smsscheduler_5.apk`.
- The result shows: feature coverage, ML verdict, permission risk, CVE lookup,
  final assessment, and the scan appears in history.

Health check (optional): **http://127.0.0.1:7860/health** → `"status": "healthy"`

Stop the server with `Ctrl + C`.

---

## What to show

| Show | Where |
|---|---|
| The working website | http://127.0.0.1:7860 |
| Model results | `reports/results/model_evaluation.json` |
| Training run with graphs (Colab) | `notebooks/MOSAIC_ML_Model_Training.ipynb`. Already executed, so outputs show without running. Upload to colab.research.google.com to rerun. |
| All graphs | `reports/figures/` (Fig 2–11) |
| The numbers behind each graph | `reports/results/*.csv` |
| Research paper draft | `MOSAIC-ML_IEEE_Paper.docx` |

---

## If something goes wrong

| Problem | Fix |
|---|---|
| `InconsistentVersionWarning` | Step 2 was skipped: `python -m pip install "scikit-learn==1.6.1"` |
| Port 7860 in use | Use `--port 8000` and open http://127.0.0.1:8000 |
| Page loads but API says offline | You opened the page some other way; use the URL above |
| CVE section shows "lookup failed" | No internet, or NVD is rate-limiting. The rest still works. |

---

## Retraining (optional, NOT needed for the demo)

Only if you want to reproduce the numbers yourself. Needs the MH-100K files in
`data/mh100k/` and **3–4 GB free RAM** (close Chrome first).

```powershell
python scripts\convert_to_csr.py        # expect a 135.5 MB file, not 275 MB
python scripts\tune_models.py           # ~10 minutes, 9 configurations
python scripts\make_model_figures.py    # Figures 4-8
```
