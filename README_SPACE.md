---
title: MOSAIC-ML Backend
emoji: 🛡️
colorFrom: indigo
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
---

# MOSAIC-ML backend

Android APK static analysis: ML malware classification, permission-based risk
scoring, CVE/NVD correlation and a prototype HIDS module.

## Endpoints

- `GET /` - service information
- `GET /health` - reports whether the model, vocabulary and permission weights loaded
- `POST /analyze-apk` - multipart upload of a `.apk` file

## Environment variables

Set these under Settings -> Variables and secrets.

| Name | Purpose | Default |
|---|---|---|
| `ALLOWED_ORIGINS` | Comma-separated frontend origins for CORS | `http://localhost:5173,http://127.0.0.1:5173` |
| `NVD_API_KEY` | Raises the NVD limit from 5 to 50 requests / 30s | unset |
| `MAX_UPLOAD_MB` | Upload size limit | `150` |
| `MODEL_PATH` | Alternative model location | bundled model |

Set `ALLOWED_ORIGINS` to your deployed frontend URL, or the browser will
block every request.

## Limitations

- Uploaded APKs are analysed statically and are never executed.
- APKs are held in temporary storage and deleted after analysis. Nothing is persisted.
- HIDS telemetry is synthetic prototype data, not device monitoring.
- A CVE keyword match does not establish that an APK is affected.
- Feature coverage is reported with every scan. When it is low, the ML
  prediction is flagged as unreliable rather than presented as a verdict.
