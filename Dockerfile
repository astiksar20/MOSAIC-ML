# MOSAIC-ML - single container serving BOTH the API and the dashboard.
#
# Stage 1 builds the React bundle. Stage 2 runs FastAPI and serves that
# bundle as static files, so one deployed URL gives the whole application:
#   /            -> dashboard
#   /health      -> service status
#   /analyze-apk -> analysis endpoint
#   /scans       -> scan history
#
# Targets Hugging Face Spaces (Docker SDK): port 7860, non-root UID 1000.
# Both matter - a different port or a root-owned writable path makes the
# Space fail to start with no useful error.

# ---------- stage 1: frontend ----------
FROM node:22-slim AS web

WORKDIR /web
COPY dashboard/package.json dashboard/package-lock.json* ./
RUN npm ci --no-audit --no-fund 2>/dev/null || npm install --no-audit --no-fund

COPY dashboard/ ./
# Empty base URL: the dashboard is served from the same origin as the API,
# so requests go to /health, /analyze-apk etc. with no cross-origin hop.
ENV VITE_API_URL=""
RUN npm run build


# ---------- stage 2: runtime ----------
# 3.10 to match the training environment (see requirements.txt).
FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Backend. Only what the API needs at runtime - the MH-100K matrix and the
# CSR artifact are training-only and would add 230 MB for no benefit.
COPY --chown=user analyzer/            ./analyzer/
COPY --chown=user api/                 ./api/
COPY --chown=user cve/                 ./cve/
COPY --chown=user feature_engineering/ ./feature_engineering/
COPY --chown=user hids/                ./hids/
COPY --chown=user risk/                ./risk/
COPY --chown=user storage/             ./storage/
COPY --chown=user ml/predict.py        ./ml/predict.py
COPY --chown=user ml/models/           ./ml/models/
COPY --chown=user data/mh100k/mh100-features-all.csv ./data/mh100k/mh100-features-all.csv

# Frontend bundle from stage 1.
COPY --chown=user --from=web /web/dist ./dashboard/dist

# SQLite lives in its own directory, NOT inside storage/ (which holds code).
# Mounting a volume over a code directory would hide updated code behind a
# stale copy. The container filesystem is ephemeral, so without a volume this
# is demo persistence only - wiped on restart.
ENV SQLITE_PATH=/app/db/mosaic.db
RUN mkdir -p /app/db

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:7860/health',timeout=4).status==200 else 1)"

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
