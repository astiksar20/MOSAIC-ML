from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import tempfile
import os
import zipfile
from pathlib import Path

import numpy as np

# Anchored to this file, so the API works regardless of working directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent


# =====================================
# CONFIGURATION (environment variables)
# =====================================
#
# Nothing below is hardcoded for deployment. Set these in Render / Vercel.

# Comma-separated list of allowed frontend origins.
# Defaults to the local Vite dev server.
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.environ.get(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if o.strip()
]

# Upload limit. An APK larger than this is rejected before anything reads it.
MAX_UPLOAD_MB = int(os.environ.get("MAX_UPLOAD_MB", "150"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024

from analyzer.apk_analyzer import (
    analyze_apk,
    get_cve_search_components
)

from cve.nvd_client import search_multiple_components

from feature_engineering.apk_feature_mapper import (
    create_feature_vector,
    compute_coverage
)

from ml.predict import predict_apk

from hids.hids_engine import run_hids

from risk.risk_engine import (
    generate_risk_report
)

from risk.permission_risk import (
    load_weights,
    compute_permission_score
)

from storage.history import (
    save_scan,
    list_scans,
    get_scan,
    stats as storage_stats,
    init_db
)

import hashlib


# Permission-risk weights are fitted on the TRAINING SPLIT ONLY and loaded
# once at startup. If the file is missing the API still serves; the
# permission_risk section then reports that the weights are unavailable
# rather than silently returning a score of zero.
try:
    PERMISSION_WEIGHTS, PERMISSION_META = load_weights(
        str(PROJECT_ROOT / "risk" / "permission_weights.json")
    )
except Exception as exc:
    PERMISSION_WEIGHTS, PERMISSION_META = None, {}
    PERMISSION_LOAD_ERROR = f"{type(exc).__name__}: {exc}"
else:
    PERMISSION_LOAD_ERROR = None


app = FastAPI(
    title="MOSAIC-ML API",
    description="Android vulnerability and intrusion risk analysis API",
    version="1.0.0"
)


# Without this the browser blocks every request from a deployed frontend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    # Any local dev server port (Vite moves to 5174, 5175... when 5173 is busy).
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# Service information. This used to live at "/", but "/" now serves the
# dashboard in the single-container build, and FastAPI matches routes in
# registration order - so an earlier "/" would shadow the frontend.
@app.get("/api")
def home():
    return {
        "project": "MOSAIC-ML",
        "status": "running",
        "endpoints": [
            "/health", "/analyze-apk", "/scans", "/scans/{scan_id}"
        ]
    }


@app.get("/health")
def health():
    """Reports what is actually loadable, not just that the process is up."""

    model_path = os.environ.get(
        "MODEL_PATH",
        str(PROJECT_ROOT / "ml" / "models" / "selected_model.joblib")
    )
    vocab_path = str(
        PROJECT_ROOT / "data" / "mh100k" / "mh100-features-all.csv"
    )

    # Actually load the model (cached after the first call), so a missing,
    # incompatible or probability-less model shows up here, not mid-scan.
    model_loaded, model_label, model_error = False, None, None
    try:
        from ml.predict import load_model, model_name
        model_label = model_name(load_model())
        model_loaded = True
    except Exception as exc:
        model_error = f"{type(exc).__name__}: {exc}"

    checks = {
        "model_file": os.path.exists(model_path),
        "model_loads": model_loaded,
        "feature_vocabulary": os.path.exists(vocab_path),
        "permission_weights": PERMISSION_WEIGHTS is not None,
    }

    return {
        "status": "healthy" if all(checks.values()) else "degraded",
        "checks": checks,
        "model": model_label,
        "model_error": model_error,
        "permission_weights_error": PERMISSION_LOAD_ERROR,
        "allowed_origins": ALLOWED_ORIGINS,
        "max_upload_mb": MAX_UPLOAD_MB,
        "nvd_api_key_configured": bool(
            os.environ.get("NVD_API_KEY", "").strip()
        ),
        "storage": storage_stats(),
    }


@app.get("/scans")
def scan_history(limit: int = 25):
    """Recent scans, newest first. Summary rows, not full reports."""
    return list_scans(limit=limit)


@app.get("/scans/{scan_id}")
def scan_detail(scan_id: str):
    """One stored report in full."""
    report = get_scan(scan_id)
    if report is None:
        raise HTTPException(
            status_code=404,
            detail=f"No stored scan with id {scan_id}"
        )
    return report


@app.post("/analyze-apk")
async def analyze_uploaded_apk(
    file: UploadFile = File(...)
):

    # =====================================
    # Save uploaded APK temporarily
    # =====================================

    # =====================================
    # Validate BEFORE touching the file
    # =====================================

    filename = file.filename or ""

    if not filename.lower().endswith(".apk"):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Expected a .apk file, received '{filename}'. "
                "Only Android package files are accepted."
            )
        )

    contents = await file.read()

    if len(contents) == 0:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty."
        )

    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=(
                f"File is {len(contents) / 1024 / 1024:.1f} MB, over the "
                f"{MAX_UPLOAD_MB} MB limit."
            )
        )

    # An APK is a ZIP archive. This rejects renamed non-APK files before
    # androguard touches them. The APK is never executed.
    if contents[:2] != b"PK":
        raise HTTPException(
            status_code=400,
            detail=(
                "This file is not a valid Android package. An APK is a ZIP "
                "archive, and this file does not begin with a ZIP header."
            )
        )

    # SHA-256 identifies the analysed artifact. The APK itself is never stored.
    apk_sha256 = hashlib.sha256(contents).hexdigest()

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".apk"
    ) as temp_file:

        temp_file.write(contents)

        temp_path = temp_file.name

    try:

        # =====================================
        # 1. APK STATIC ANALYSIS
        # =====================================

        apk_result = analyze_apk(
            temp_path
        )


        # =====================================
        # 2. APK → MH-100K FEATURE VECTOR
        # =====================================

        feature_vector, matched_features = (
            create_feature_vector(
                apk_result
            )
        )


        # =====================================
        # 2b. FEATURE COVERAGE
        # =====================================
        #
        # Computed BEFORE the prediction, so the
        # response can say how much of the model
        # was actually reachable from this APK.
        # =====================================

        coverage = compute_coverage(
            apk_result
        )


        # =====================================
        # 3. ML PREDICTION
        # =====================================

        ml_result = predict_apk(
            feature_vector
        )

        ml_result["coverage_reliable"] = coverage["reliable"]

        if not coverage["reliable"]:
            ml_result["warning"] = coverage["warning"]


        # =====================================
        # 4. CVE / NVD ANALYSIS
        # =====================================

        components = get_cve_search_components(
            apk_result
        )

        components_to_search = components[:10]

        # Returns a report dict. It never raises: a failed lookup is reported
        # as a status, so one NVD problem can no longer take down the scan.
        cve_report = search_multiple_components(
            components_to_search
        )

        cve_results = cve_report["results"]


        # =====================================
        # Extract CVSS scores
        # =====================================

        cvss_scores = []

        for cve in cve_results:

            score = cve.get(
                "cvss_score"
            )

            if score is not None:

                cvss_scores.append(
                    float(score)
                )


        # =====================================
        # 5. HIDS
        # =====================================
        #
        # Prototype runtime-event data.
        #
        # This represents the HIDS integration
        # while actual device runtime telemetry
        # is developed separately.
        # =====================================

        runtime_events = [
            "normal_file_access",
            "unexpected_sms",
            "unknown_network_connection"
        ]


        # Runtime behavior features:
        #
        # [network_connections,
        #  sms_activity,
        #  file_access,
        #  process_activity]

        runtime_data = np.array([

            [1, 0, 2, 1],

            [2, 0, 1, 1],

            [1, 0, 2, 2],

            [2, 1, 2, 1],

            [1, 0, 1, 1],

            [20, 15, 30, 25]

        ])


        hids_result = run_hids(
            runtime_events,
            runtime_data
        )


        hids_score = hids_result[
            "hids_score"
        ]


        # =====================================
        # 5b. PERMISSION-BASED RISK SCORE
        # =====================================
        #
        # Independent of the ML model and of the
        # weighted sum below. Adapted from
        # Ogwara et al. (2024), Future Internet
        # 16(8) 271. Weights fitted on the
        # training split only.
        #
        # This is deliberately NOT fed into
        # generate_risk_report(). It is reported
        # as its own separate analysis.
        # =====================================

        if PERMISSION_WEIGHTS is None:

            permission_result = {
                "score": None,
                "score_0_100": None,
                "status": "weights_unavailable",
                "error": PERMISSION_LOAD_ERROR,
                "explanation": (
                    "Permission risk weights could not be loaded. "
                    "No permission score was computed. This is not "
                    "a low-risk result."
                )
            }

        else:

            permission_result = compute_permission_score(
                apk_result.get("permissions", []),
                PERMISSION_WEIGHTS
            )


        # =====================================
        # 6. RISK ENGINE
        # =====================================

        risk_report = generate_risk_report(

            ml_probability=ml_result[
                "malware_probability"
            ],

            hids_score=hids_score,

            cvss_scores=cvss_scores
        )


        # =====================================
        # 7. FINAL MOSAIC-ML RESPONSE
        # =====================================

        report = {

            "filename": file.filename,

            "apk_sha256": apk_sha256,


            # ---------------------------------
            # APK ANALYSIS
            # ---------------------------------

            "apk_analysis": apk_result,


            # ---------------------------------
            # ML ANALYSIS
            # ---------------------------------

            "ml_analysis": {

                "matched_features":
                    len(matched_features),

                "prediction":
                    ml_result[
                        "prediction"
                    ],

                "label":
                    ml_result[
                        "label"
                    ],

                "malware_probability":
                    ml_result[
                        "malware_probability"
                    ],

                "benign_probability":
                    ml_result[
                        "benign_probability"
                    ],

                "model":
                    ml_result["model"]
            },


            # ---------------------------------
            # CVE / NVD ANALYSIS
            # ---------------------------------

            "cve_analysis": {

                "components_searched":
                    components_to_search,

                "cve_count":
                    len(cve_results),

                "cve_results":
                    cve_results
            },


            # ---------------------------------
            # HIDS ANALYSIS
            # ---------------------------------

            "hids_analysis": {

                "rule_score":
                    hids_result[
                        "rule_score"
                    ],

                "alerts":
                    hids_result[
                        "rule_alerts"
                    ],

                "hids_score":
                    hids_result[
                        "hids_score"
                    ]
            },


            # ---------------------------------
            # FEATURE COVERAGE
            #
            # How much of the model could
            # actually be populated from this
            # APK. Everything in ml_analysis
            # inherits its reliability from
            # this number.
            # ---------------------------------

            "feature_coverage": coverage,


            # ---------------------------------
            # CVE LOOKUP STATUS
            # ---------------------------------

            "cve_lookup": {

                "components_searched":
                    cve_report["components_searched"],

                "components_available":
                    cve_report["components_available"],

                "status_counts":
                    cve_report["status_counts"],

                "per_component":
                    cve_report["per_component"],

                "api_key_configured":
                    cve_report["api_key_configured"],

                "rate_limit":
                    cve_report["rate_limit"],

                "interpretation":
                    cve_report["interpretation"]
            },


            # ---------------------------------
            # ANALYSIS A - PERMISSION RISK
            #
            # Separate, independent evidence.
            # Not combined with anything below.
            # ---------------------------------

            "permission_risk": {

                "score":
                    permission_result["score"],

                "score_0_100":
                    permission_result["score_0_100"],

                "status":
                    permission_result["status"],

                "permissions_matched":
                    permission_result.get("k"),

                "selected_set_size":
                    permission_result.get(
                        "selected_set_size"
                    ),

                "matched_permissions":
                    permission_result.get(
                        "matched_permissions", []
                    ),

                "contributions":
                    permission_result.get(
                        "contributions", []
                    ),

                "explanation":
                    permission_result["explanation"],

                "method":
                    "r_i = sqrt(alpha_i * (1 - beta_i)); "
                    "R(a) = sum(lambda * r) / k, for k > 0",

                "source":
                    "Adapted from Ogwara et al. (2024), "
                    "Future Internet 16(8), 271",

                "weights_fitted_on":
                    PERMISSION_META.get(
                        "split_scheme",
                        "training split only"
                    ),

                "caveats": [
                    "Measured ROC-AUC 0.773 and PR-AUC 0.280 on the "
                    "held-out MH-100K test split. This is a weak "
                    "standalone discriminator.",
                    "Benign and malware score distributions overlap "
                    "heavily (means 0.646 vs 0.691).",
                    "This is NOT a probability of malware. The 0-100 "
                    "form is a display rescaling only.",
                    "A null score means insufficient permission "
                    "evidence, never low risk."
                ]
            },


            # ---------------------------------
            # ANALYSIS B - LEGACY WEIGHTED SUM
            #
            # DEPRECATED. Retained so existing
            # dashboard behaviour does not break.
            # ---------------------------------

            "risk_analysis": {

                "risk_score":
                    risk_report[
                        "risk_score"
                    ],

                "risk_category":
                    risk_report[
                        "risk_category"
                    ],

                "recommendation":
                    risk_report[
                        "recommendation"
                    ],

                "status": "DEPRECATED_PROTOTYPE",

                "formula":
                    "0.40 * ML + 0.40 * HIDS + 0.20 * CVSS",

                "caveats": [
                    "This weighted sum is a manually chosen prototype "
                    "formula, not an established standard, and its "
                    "weights have not been validated.",
                    "It combines quantities with different units: a "
                    "class probability, a synthetic event count and a "
                    "CVSS severity.",
                    "The HIDS input is SYNTHETIC telemetry hardcoded "
                    "in the API. It was not produced by the uploaded "
                    "APK.",
                    "CVSS is capped at 20% weight, so even a critical "
                    "vulnerability cannot raise the category beyond "
                    "MEDIUM.",
                    "Do not present this as a calibrated probability "
                    "of compromise."
                ]
            }

        }

        # Persist. A storage failure must not fail the scan, so the result is
        # reported as status rather than raised.
        report["storage"] = save_scan(report, apk_sha256=apk_sha256)

        return report

    finally:

        # Remove temporary APK
        os.remove(
            temp_path
        )


# =====================================
# DASHBOARD (single-container serving)
# =====================================
#
# When dashboard/dist exists - that is, the frontend has been built, which
# the Dockerfile does in its first stage - the API also serves it. One
# deployed URL then provides the whole application.
#
# This is mounted LAST so that every API route above takes precedence over
# the catch-all. In local development the Vite dev server serves the
# frontend instead and this block simply does nothing.

_DIST = PROJECT_ROOT / "dashboard" / "dist"

if _DIST.is_dir():

    app.mount(
        "/assets",
        StaticFiles(directory=str(_DIST / "assets")),
        name="assets"
    )

    @app.get("/", include_in_schema=False)
    def dashboard_root():
        return FileResponse(str(_DIST / "index.html"))

    @app.get("/{path:path}", include_in_schema=False)
    def dashboard_catchall(path: str):
        """Serve a real file when one exists, otherwise index.html.

        The fallback lets client-side routing work: a deep link that the
        server has no route for still loads the application shell.
        """
        candidate = _DIST / path
        if candidate.is_file():
            return FileResponse(str(candidate))
        return FileResponse(str(_DIST / "index.html"))
