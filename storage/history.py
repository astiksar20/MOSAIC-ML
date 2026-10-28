"""
MOSAIC-ML - scan history storage.

A deliberately small persistence layer: one table, one row per scan. It stores
the analysis result and the APK's SHA-256, never the APK itself.

Backend selection
-----------------
    DATABASE_URL unset  -> SQLite at storage/mosaic.db
    DATABASE_URL set    -> PostgreSQL (Neon, Supabase, ...), if psycopg is installed

On Hugging Face Spaces and Render the container filesystem is EPHEMERAL: a
SQLite file is wiped whenever the instance restarts. That is acceptable for a
demo but means history is not durable. Set DATABASE_URL to a managed Postgres
instance for persistence that survives restarts.

Every function here fails soft. A storage problem must never take down a scan,
so errors are returned rather than raised, and the API reports them as status.
"""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
SQLITE_PATH = os.environ.get(
    "SQLITE_PATH", str(PROJECT_ROOT / "storage" / "mosaic.db")
)

_PG = None
if DATABASE_URL:
    try:
        import psycopg

        _PG = psycopg
    except ImportError:
        _PG = None


def backend_name() -> str:
    if DATABASE_URL and _PG:
        return "postgresql"
    if DATABASE_URL and not _PG:
        return "sqlite (DATABASE_URL set but psycopg not installed)"
    return "sqlite"


def _connect():
    if DATABASE_URL and _PG:
        return _PG.connect(DATABASE_URL)
    Path(SQLITE_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(SQLITE_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


_SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS scans (
    scan_id           TEXT PRIMARY KEY,
    created_utc       TEXT NOT NULL,
    file_name         TEXT,
    apk_sha256        TEXT,
    package_name      TEXT,
    matched_features  INTEGER,
    coverage_percent  REAL,
    coverage_reliable INTEGER,
    ml_label          TEXT,
    ml_probability    REAL,
    permission_score  REAL,
    permission_status TEXT,
    cve_records       INTEGER,
    cve_failed        INTEGER,
    risk_score        REAL,
    risk_category     TEXT,
    report_json       TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_scans_created ON scans (created_utc DESC);
CREATE INDEX IF NOT EXISTS idx_scans_sha     ON scans (apk_sha256);
"""

_PG_SCHEMA = """
CREATE TABLE IF NOT EXISTS scans (
    scan_id           TEXT PRIMARY KEY,
    created_utc       TIMESTAMPTZ NOT NULL,
    file_name         TEXT,
    apk_sha256        TEXT,
    package_name      TEXT,
    matched_features  INTEGER,
    coverage_percent  DOUBLE PRECISION,
    coverage_reliable BOOLEAN,
    ml_label          TEXT,
    ml_probability    DOUBLE PRECISION,
    permission_score  DOUBLE PRECISION,
    permission_status TEXT,
    cve_records       INTEGER,
    cve_failed        INTEGER,
    risk_score        DOUBLE PRECISION,
    risk_category     TEXT,
    report_json       TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_scans_created ON scans (created_utc DESC);
CREATE INDEX IF NOT EXISTS idx_scans_sha     ON scans (apk_sha256);
"""

_READY = False
_INIT_ERROR = None


def init_db() -> tuple[bool, str | None]:
    """Create the table if absent. Safe to call repeatedly."""
    global _READY, _INIT_ERROR
    if _READY:
        return True, None
    try:
        with _connect() as conn:
            cur = conn.cursor()
            if DATABASE_URL and _PG:
                cur.execute(_PG_SCHEMA)
            else:
                cur.executescript(_SQLITE_SCHEMA)
            conn.commit()
        _READY, _INIT_ERROR = True, None
    except Exception as exc:
        _READY, _INIT_ERROR = False, f"{type(exc).__name__}: {exc}"
    return _READY, _INIT_ERROR


_COLUMNS = (
    "scan_id, created_utc, file_name, apk_sha256, package_name, "
    "matched_features, coverage_percent, coverage_reliable, ml_label, "
    "ml_probability, permission_score, permission_status, cve_records, "
    "cve_failed, risk_score, risk_category, report_json"
)


def save_scan(report: dict, apk_sha256: str | None = None) -> dict:
    """Persist one scan. Returns a status dict; never raises."""
    ok, err = init_db()
    if not ok:
        return {"stored": False, "error": err, "backend": backend_name()}

    scan_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    cov = report.get("feature_coverage") or {}
    ml = report.get("ml_analysis") or {}
    perm = report.get("permission_risk") or {}
    cve = (report.get("cve_lookup") or {}).get("status_counts") or {}
    risk = report.get("risk_analysis") or {}
    apk = report.get("apk_analysis") or {}

    values = (
        scan_id,
        now.isoformat() if not (DATABASE_URL and _PG) else now,
        report.get("filename"),
        apk_sha256,
        apk.get("package_name"),
        cov.get("matched_features"),
        cov.get("coverage_percent"),
        bool(cov.get("reliable")) if not (DATABASE_URL and _PG) else cov.get("reliable"),
        ml.get("label"),
        ml.get("malware_probability"),
        perm.get("score"),
        perm.get("status"),
        cve.get("records_returned"),
        cve.get("lookup_failed"),
        risk.get("risk_score"),
        risk.get("risk_category"),
        json.dumps(report, default=str),
    )

    placeholder = "%s" if (DATABASE_URL and _PG) else "?"
    marks = ", ".join([placeholder] * 17)

    try:
        with _connect() as conn:
            conn.cursor().execute(
                f"INSERT INTO scans ({_COLUMNS}) VALUES ({marks})", values
            )
            conn.commit()
        return {
            "stored": True,
            "scan_id": scan_id,
            "backend": backend_name(),
            "created_utc": now.isoformat(timespec="seconds"),
        }
    except Exception as exc:
        return {
            "stored": False,
            "error": f"{type(exc).__name__}: {exc}",
            "backend": backend_name(),
        }


def list_scans(limit: int = 25) -> dict:
    """Most recent scans, newest first. Summary rows, not full reports."""
    ok, err = init_db()
    if not ok:
        return {"scans": [], "error": err, "backend": backend_name()}

    ph = "%s" if (DATABASE_URL and _PG) else "?"
    try:
        with _connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT scan_id, created_utc, file_name, package_name, "
                "matched_features, coverage_percent, coverage_reliable, "
                "ml_label, ml_probability, permission_score, permission_status, "
                "risk_score, risk_category "
                f"FROM scans ORDER BY created_utc DESC LIMIT {ph}",
                (min(int(limit), 200),),
            )
            cols = [d[0] for d in cur.description]
            rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        for r in rows:
            if not isinstance(r.get("created_utc"), str):
                r["created_utc"] = str(r["created_utc"])
        return {"scans": rows, "count": len(rows), "backend": backend_name()}
    except Exception as exc:
        return {
            "scans": [],
            "error": f"{type(exc).__name__}: {exc}",
            "backend": backend_name(),
        }


def get_scan(scan_id: str) -> dict | None:
    """One full stored report, or None."""
    ok, _ = init_db()
    if not ok:
        return None
    ph = "%s" if (DATABASE_URL and _PG) else "?"
    try:
        with _connect() as conn:
            cur = conn.cursor()
            cur.execute(f"SELECT report_json FROM scans WHERE scan_id = {ph}", (scan_id,))
            row = cur.fetchone()
        if not row:
            return None
        return json.loads(row[0])
    except Exception:
        return None


def stats() -> dict:
    ok, err = init_db()
    if not ok:
        return {"available": False, "error": err, "backend": backend_name()}
    try:
        with _connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM scans")
            total = cur.fetchone()[0]
        return {
            "available": True,
            "backend": backend_name(),
            "total_scans": int(total),
            "persistence_note": (
                "SQLite on an ephemeral container filesystem. History is lost "
                "when the instance restarts. Set DATABASE_URL for durable storage."
                if backend_name().startswith("sqlite")
                else "Managed PostgreSQL. History survives restarts."
            ),
        }
    except Exception as exc:
        return {"available": False, "error": f"{type(exc).__name__}: {exc}",
                "backend": backend_name()}


if __name__ == "__main__":
    print("MOSAIC-ML storage")
    print("=" * 46)
    print("backend:", backend_name())
    ok, err = init_db()
    print("schema ready:", ok, err or "")
    print("stats:", stats())
