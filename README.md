# MOSAIC-ML

## Android Vulnerability and Intrusion Risk Analysis Using CVE/NVD and Machine Learning

MOSAIC-ML is an academic prototype for analyzing Android applications using static APK analysis, machine learning, CVE/NVD vulnerability intelligence, and host-based intrusion detection concepts.

The system combines multiple security signals into an explainable prototype risk score to support Android application security analysis.

---

## System Architecture

```text
                         MOSAIC-ML
                            │
                       ANDROID APK
                            │
                            ▼
                  ┌──────────────────┐
                  │ STATIC ANALYSIS  │
                  └────────┬─────────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
       APK FEATURES              CVE / NVD ANALYSIS
              │                         │
              │                 ┌───────┴────────┐
              │                 │ CVE identifiers│
              │                 │ CVSS severity  │
              │                 │ CWE             │
              │                 │ Components     │
              │                 └───────┬────────┘
              │                         │
              └────────────┬────────────┘
                           ▼
                   FEATURE ENGINEERING
                           │
                           ▼
                    ML DATA PIPELINE
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
       SUPERVISED ML              RUNTIME MONITOR
       Random Forest                    │
       Logistic Regression              ▼
                                      HIDS
                                ┌──────┴──────┐
                                ▼             ▼
                              Rules    Isolation Forest
                                │             │
                                └──────┬──────┘
                                       ▼
                                 Anomaly Score
              │
              └───────────────┬───────────────┘
                              ▼
                        RISK ENGINE
                              │
                              ▼
                    EXPLAINABLE 0–100
                         RISK SCORE
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
              Risk Category        Recommendation
              LOW/MEDIUM/HIGH      Monitor/Restrict
                    │
                    ▼
                 DASHBOARD
