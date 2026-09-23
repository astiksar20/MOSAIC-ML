# MOSAIC-ML Frontend Dashboard

A modern, Salar-inspired SaaS cybersecurity dashboard for **MOSAIC-ML** (Android Vulnerability & Intrusion Risk Analyzer).

---

## 🌟 Overview

The **MOSAIC-ML Dashboard** provides a dark-mode cybersecurity visualization suite for analyzing Android application packages (.APK). It communicates with the FastAPI backend at `http://127.0.0.1:8000` to deliver real-time risk assessment, machine learning classification, static component inspection, CVE/NVD vulnerability intelligence, and HIDS intrusion telemetry.

---

## 🚀 Quick Start

### 1. Ensure Backend is Running
Start the FastAPI server from the repository root:
```bash
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```
Verify the backend is live at `http://127.0.0.1:8000/health`.

### 2. Start the React Frontend Dashboard
Navigate into the `dashboard/` folder and run the development server:
```bash
cd dashboard
npm run dev
```
Open your browser at `http://localhost:5173`.

---

## 🏗️ Architecture & Component Structure

```
dashboard/
├── src/
│   ├── components/
│   │   ├── Sidebar.jsx        # Navigation & framework status
│   │   ├── Header.jsx         # Header & live API status indicator (● API Online)
│   │   ├── ApkUploader.jsx    # Hero drag-and-drop file uploader & scanner
│   │   ├── SummaryCards.jsx   # 5-card metric summary grid
│   │   ├── ApkAnalysis.jsx    # Static manifest, permissions & components accordion
│   │   ├── MlAnalysis.jsx     # Random Forest MH-100K probability visualizer
│   │   ├── CveAnalysis.jsx    # NVD vulnerability intelligence cards & zero-match notice
│   │   ├── HidsAnalysis.jsx   # HIDS rule alerts & behavioral anomaly indicators
│   │   ├── RiskAnalysis.jsx   # Centerpiece SVG radial score gauge & recommendations
│   │   ├── Explainability.jsx # "Why this result?" evidence audit trail
│   │   ├── SettingsModal.jsx  # Endpoint & proxy configuration modal
│   │   └── AboutModal.jsx     # Academic architecture overview modal
│   │
│   ├── pages/
│   │   └── Dashboard.jsx      # Main layout coordinator & API state manager
│   │
│   ├── services/
│   │   └── api.js             # Axios client with fallback & error handler
│   │
│   ├── index.css              # Custom Salar-style dark glassmorphism CSS
│   ├── App.jsx                # Root application entry
│   └── main.jsx               # DOM renderer
│
├── vite.config.js             # Dev proxy redirecting /api -> http://127.0.0.1:8000
├── package.json
└── README.md
```

---

## 🔌 API Integration & CORS Note

- **Endpoint:** `POST /analyze-apk` (Multipart Form-Data, field: `file`)
- **Proxy Setup:** Vite dev server uses `/api` proxying to avoid CORS restrictions during development:
  ```javascript
  // vite.config.js
  proxy: {
    '/api': {
      target: 'http://127.0.0.1:8000',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, ''),
    }
  }
  ```
- **Optional Direct CORS Note:** If deploying without Vite proxy, add FastAPI `CORSMiddleware` in `api/main.py`:
  ```python
  from fastapi.middleware.cors import CORSMiddleware

  app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```

---

## 🛡️ Academic Integrity & Terminology Standard

The dashboard strictly adheres to academic cybersecurity reporting standards:
1. **ML Outputs:** Displayed as `"ML Classification: MALWARE / BENIGN"` with explicit probability metrics, not unverified definitive claims.
2. **CVE/NVD Intelligence:** "0 CVEs returned" is accurately presented as `"No matching CVE records returned based on component lookup"`.
3. **HIDS Telemetry:** Explicitly labeled with notice: *"Runtime detection currently uses prototype telemetry for demonstration. Actual device runtime telemetry is not yet connected."*
4. **Risk Index:** Labeled as *"MOSAIC-ML Prototype Risk Score"* and annotated with *"Risk score is a prototype aggregation of available signals and has not yet been experimentally calibrated as a probability of compromise."*
