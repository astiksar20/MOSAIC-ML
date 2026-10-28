"""
MOSAIC-ML - hyperparameter search for the three selectable classifiers.

Honest protocol
---------------
Every configuration below is scored on the VALIDATION split only. The test
split is touched exactly once, at the end, by the single winning
configuration. Nothing here looks at test data while choosing.

Selection is on balanced accuracy, not accuracy. After deduplication malware is
13.1% of rows, so predicting "benign" for everything scores 0.869 accuracy;
accuracy rewards a model for neglecting the minority class - the one that matters.

Usage:
    python scripts/tune_models.py
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import joblib
import numpy as np
import scipy
import scipy.sparse as sp
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.svm import LinearSVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import (
    accuracy_score, average_precision_score, balanced_accuracy_score,
    confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score,
)

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"
MODEL_DIR = ROOT / "ml" / "models"
RESULTS = ROOT / "reports" / "results"
SEED = 42


def dedup_split():
    X = sp.load_npz(PROC / "mh100_csr.npz").tocsr()
    y = np.load(PROC / "classes.npy").astype(int)

    seen, keep = {}, []
    for i in range(X.shape[0]):
        lo, hi = X.indptr[i], X.indptr[i + 1]
        d = hashlib.blake2b(
            X.indices[lo:hi].astype(np.int32).tobytes(), digest_size=16
        ).digest()
        if d not in seen:
            seen[d] = i
            keep.append(i)
    keep = np.array(keep)
    X, y = X[keep], y[keep]

    idx = np.arange(X.shape[0])
    i_tr, i_tmp = train_test_split(idx, test_size=0.30, random_state=SEED, stratify=y)
    i_va, i_te = train_test_split(i_tmp, test_size=0.50, random_state=SEED, stratify=y[i_tmp])
    return (X[i_tr], y[i_tr]), (X[i_va], y[i_va]), (X[i_te], y[i_te]), len(keep)


def scores_of(m, X):
    if hasattr(m, "predict_proba"):
        return m.predict_proba(X)[:, 1]
    if hasattr(m, "decision_function"):
        return m.decision_function(X)
    return None


def evaluate(name, model, Xa, ya, Xb, yb, note=""):
    t0 = time.time()
    model.fit(Xa, ya)
    fit_s = time.time() - t0
    pred = model.predict(Xb)
    sc = scores_of(model, Xb)
    tn, fp, fn, tp = confusion_matrix(yb, pred, labels=[0, 1]).ravel()
    return {
        "config": name,
        "accuracy": round(float(accuracy_score(yb, pred)), 4),
        "balanced_accuracy": round(float(balanced_accuracy_score(yb, pred)), 4),
        "macro_f1": round(float(f1_score(yb, pred, average="macro")), 4),
        "malware_precision": round(float(precision_score(yb, pred, zero_division=0)), 4),
        "malware_recall": round(float(recall_score(yb, pred, zero_division=0)), 4),
        "malware_f1": round(float(f1_score(yb, pred, zero_division=0)), 4),
        "false_positive_rate": round(float(fp / (fp + tn)), 4),
        "false_negative_rate": round(float(fn / (fn + tp)), 4),
        "confusion_matrix": [[int(tn), int(fp)], [int(fn), int(tp)]],
        "roc_auc": round(float(roc_auc_score(yb, sc)), 4) if sc is not None else None,
        "pr_auc": round(float(average_precision_score(yb, sc)), 4) if sc is not None else None,
        "fit_seconds": round(fit_s, 1),
        "note": note,
    }


# Each entry: (label, factory, family). Class weighting is the main lever for
# an imbalanced problem - it makes the loss care about the minority class
# instead of letting it be drowned out.
GRID = [
    ("LR  C=1    (baseline)",   lambda: LogisticRegression(max_iter=2000, random_state=SEED), "Logistic Regression"),
    ("LR  C=1    balanced",     lambda: LogisticRegression(max_iter=2000, class_weight="balanced", random_state=SEED), "Logistic Regression"),
    ("LR  C=0.1  balanced",     lambda: LogisticRegression(C=0.1, max_iter=2000, class_weight="balanced", random_state=SEED), "Logistic Regression"),
    ("LR  C=10   balanced",     lambda: LogisticRegression(C=10, max_iter=3000, class_weight="balanced", random_state=SEED), "Logistic Regression"),

    ("SVM C=1    (baseline)",   lambda: LinearSVC(random_state=SEED, max_iter=3000), "Linear SVM"),
    ("SVM C=1    balanced",     lambda: LinearSVC(class_weight="balanced", random_state=SEED, max_iter=3000), "Linear SVM"),
    ("SVM C=0.1  balanced",     lambda: LinearSVC(C=0.1, class_weight="balanced", random_state=SEED, max_iter=3000), "Linear SVM"),

    ("RF  30     (baseline)",   lambda: RandomForestClassifier(n_estimators=30, max_features="sqrt", random_state=SEED, n_jobs=-1), "Random Forest"),
    ("RF  30     balanced",     lambda: RandomForestClassifier(n_estimators=30, max_features="sqrt", class_weight="balanced", random_state=SEED, n_jobs=-1), "Random Forest"),
    # Random Forest is fixed at 30 trees by the project specification.
]


def main() -> int:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)

    print(f"scikit-learn {sklearn.__version__} | numpy {np.__version__} | scipy {scipy.__version__}")
    print("loading and splitting...", flush=True)
    (X_tr, y_tr), (X_va, y_va), (X_te, y_te), n_unique = dedup_split()
    print(f"  {n_unique:,} unique rows | train {len(y_tr):,} val {len(y_va):,} test {len(y_te):,}")
    print(f"  train malicious {int(y_tr.sum()):,} / benign {int((y_tr==0).sum()):,}\n")

    rows = []
    for label, make, family in GRID:
        print(f"  {label:26s}", end=" ", flush=True)
        try:
            r = evaluate(label, make(), X_tr, y_tr, X_va, y_va)
            r["family"] = family
            rows.append(r)
            print(f"bal={r['balanced_accuracy']:.4f} rec={r['malware_recall']:.4f} "
                  f"f1={r['malware_f1']:.4f} fpr={r['false_positive_rate']:.4f} "
                  f"({r['fit_seconds']}s)")
        except Exception as exc:
            print(f"FAILED {type(exc).__name__}: {exc}")

    # Control, for reference.
    cnt = lambda M: np.diff(M.indptr).astype(float).reshape(-1, 1)
    ctrl = evaluate("CONTROL active-count", DecisionTreeClassifier(max_depth=3, random_state=SEED),
                    cnt(X_tr), y_tr, cnt(X_va), y_va, "single input: count of active features")
    ctrl["family"] = "Control"
    rows.append(ctrl)
    print(f"  {'CONTROL active-count':26s} bal={ctrl['balanced_accuracy']:.4f} "
          f"rec={ctrl['malware_recall']:.4f}")

    real = [r for r in rows if r["family"] != "Control"]
    best = max(real, key=lambda r: r["balanced_accuracy"])
    print(f"\nBEST on validation balanced accuracy: {best['config']} "
          f"({best['balanced_accuracy']:.4f})")

    # Best per family, so the paper can report all three fairly.
    per_family = {}
    for fam in ("Logistic Regression", "Linear SVM", "Random Forest"):
        cands = [r for r in real if r["family"] == fam]
        if cands:
            per_family[fam] = max(cands, key=lambda r: r["balanced_accuracy"])
    print("\nBest per family:")
    for fam, r in per_family.items():
        print(f"  {fam:22s} {r['config']:26s} bal={r['balanced_accuracy']:.4f} "
              f"rec={r['malware_recall']:.4f}")

    # Refit the winner on train+validation, evaluate ONCE on test.
    make = dict((l, m) for l, m, _ in GRID)[best["config"]]
    X_fit = sp.vstack([X_tr, X_va], format="csr")
    y_fit = np.concatenate([y_tr, y_va])
    print(f"\nrefitting {best['config']} on train+validation ({X_fit.shape[0]:,} rows)...", flush=True)
    final = make()
    test_row = evaluate(best["config"], final, X_fit, y_fit, X_te, y_te,
                        "refit on train+validation; test evaluated once")
    test_row["family"] = best["family"]
    print("\nFINAL TEST (once):")
    for k in ("accuracy", "balanced_accuracy", "macro_f1", "malware_precision",
              "malware_recall", "malware_f1", "false_positive_rate",
              "false_negative_rate", "roc_auc", "pr_auc"):
        print(f"  {k:22s} {test_row[k]}")
    print(f"  confusion              {test_row['confusion_matrix']}")

    # Save one artifact per family plus the winner.
    print("\nsaving models...")
    fname = {"Logistic Regression": "logistic_regression.joblib",
             "Linear SVM": "linear_svm.joblib",
             "Random Forest": "random_forest.joblib"}
    for fam, r in per_family.items():
        mk = dict((l, m) for l, m, _ in GRID)[r["config"]]
        m = mk()
        m.fit(X_tr, y_tr)
        joblib.dump(m, MODEL_DIR / fname[fam], compress=3)
        print(f"  {fname[fam]:28s} {(MODEL_DIR/fname[fam]).stat().st_size/1e6:6.2f} MB  ({r['config']})")
    joblib.dump(final, MODEL_DIR / "selected_model.joblib", compress=3)
    print(f"  {'selected_model.joblib':28s} "
          f"{(MODEL_DIR/'selected_model.joblib').stat().st_size/1e6:6.2f} MB  <- API uses this")

    record = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sklearn_version": sklearn.__version__,
        "numpy_version": np.__version__,
        "scipy_version": scipy.__version__,
        "protocol": {
            "deduplicated": True, "unique_rows": int(n_unique),
            "split": "70/15/15 stratified", "seed": SEED,
            "n_train": int(len(y_tr)), "n_val": int(len(y_va)), "n_test": int(len(y_te)),
            "label_rule": "vt_detection >= 4",
            "selection_metric": "balanced_accuracy on validation",
            "configurations_tried": len(GRID),
            "test_evaluated_once": True,
        },
        "validation_results": rows,
        "best_per_family": per_family,
        "selected_config": best["config"],
        "test_result": test_row,
        "caveats": [
            "All configurations were scored on validation; the test split was "
            "used once, by the winning configuration only.",
            "Single split; no repeated runs or confidence intervals.",
            "No probability calibration was fitted.",
            "Accuracy is not a safe selection metric here: the count-only "
            "control reaches high accuracy without using which features are set.",
        ],
    }
    (RESULTS / "model_evaluation.json").write_text(json.dumps(record, indent=2))
    (ROOT / "ml" / "evaluation_results.json").write_text(json.dumps(record, indent=2))
    print(f"\nwrote {RESULTS/'model_evaluation.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
