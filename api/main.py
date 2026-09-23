from fastapi import FastAPI, UploadFile, File
import tempfile
import os
import numpy as np

from analyzer.apk_analyzer import (
    analyze_apk,
    get_cve_search_components
)

from cve.nvd_client import search_multiple_components

from feature_engineering.apk_feature_mapper import (
    create_feature_vector
)

from ml.predict import predict_apk

from hids.hids_engine import run_hids

from risk.risk_engine import (
    generate_risk_report
)


app = FastAPI(
    title="MOSAIC-ML API",
    description="Android vulnerability and intrusion risk analysis API",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "project": "MOSAIC-ML",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/analyze-apk")
async def analyze_uploaded_apk(
    file: UploadFile = File(...)
):

    # =====================================
    # Save uploaded APK temporarily
    # =====================================

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".apk"
    ) as temp_file:

        contents = await file.read()

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
        # 3. ML PREDICTION
        # =====================================

        ml_result = predict_apk(
            feature_vector
        )


        # =====================================
        # 4. CVE / NVD ANALYSIS
        # =====================================

        components = get_cve_search_components(
            apk_result
        )

        components_to_search = components[:10]

        cve_results = search_multiple_components(
            components_to_search
        )


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

        return {

            "filename": file.filename,


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
                    ]
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
            # RISK ANALYSIS
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
                    ]
            }

        }

    finally:

        # Remove temporary APK
        os.remove(
            temp_path
        )