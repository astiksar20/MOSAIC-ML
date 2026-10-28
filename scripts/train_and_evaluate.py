# SUPERSEDED by scripts/tune_models.py, which produced the shipped models.
# Running this overwrites ml/models/ and the results with the older,
# unweighted three-configuration run.
"""
MOSAIC-ML - train and evaluate the three selectable classifiers.

Replaces the previous ad-hoc training and the broken evaluation script.

Why this script exists
----------------------
The earlier `ml/evaluation_results.json` reported Random Forest at ROC-AUC
0.4354 with malware recall 0.0010 - worse than random guessing. The cause was
not the data: the matrix, the labels and the feature count were all verified
correct. The Random Forest artifact was serialised by scikit-learn 1.6.1 and
loaded under a different version, which produces a model that loads without
error but predicts incorrectly.

The fix is to train and evaluate every model inside one environment, and to
record the version used alongside the artifacts so the mismatch cannot recur
silently.

Protocol
--------
  * Rows with identical active-feature sets are collapsed before splitting, so
    copies of one application cannot straddle train and test.
  * Stratified 70 / 15 / 15 with a fixed seed.
  * Selection on validation using balanced accuracy, never accuracy: the class
    balance is roughly 9.4 : 1, so predicting the majority class alone scores
    about 0.90.
  * The test split is evaluated exactly once, after selection is final.
  * A single-feature control (count of active features only) is included to
    show how much the 24,833-dimensional representation actually contributes.

Usage:
    python scripts/train_and_evaluate.py
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import joblib
import numpy as np
import scipy.sparse as sp
import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score, f1_score, precision_score,
    recall_score, confusion_matrix, roc_auc_score, average_precision_score,
)

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"
MODEL_DIR = ROOT / "ml" / "models"
RESULTS = ROOT / "reports" / "results"
SEED = 42


def load_data():
    X = sp.load_npz(PROC / "mh100_csr.npz").tocsr()
    classes = PROC / "classes.npy"
    if classes.exists():
        y = np.load(classes).astype(int)
    else:
        z = np.load(ROOT / "data" / "mh100k" / "mh100.npz", allow_pickle=True)
        y = np.asarray(z["classes"]).astype(int)
    if X.shape[0] != y.shape[0]:
        raise ValueError(f"row mismatch: X has {X.shape[0]}, y has {y.shape[0]}")
    return X, y


def deduplicate(X, y):
    """Collapse rows with identical sets of active feature indices."""
    seen, keep, conflicts = {}, [], 0
    for i in range(X.shape[0]):
        lo, hi = X.indptr[i], X.indptr[i + 1]
        digest = hashlib.blake2b(
            X.indices[lo:hi].astype(np.int32).tobytes(), digest_size=16
        ).digest()
        if digest in seen:
            if y[seen[digest]] != y[i]:
                conflicts += 1
        else:
            seen[digest] = i
            keep.append(i)
    keep = np.array(keep)
    return X[keep], y[keep], len(keep), conflicts


def scores_of(model, X):
    if hasattr(model, "predict_proba"):
        return model.predict_proba(X)[:, 1]
    if hasattr(model, "decision_function"):
        return model.decision_function(X)
    return None


def measure(name, model, Xa, ya, Xb, yb, note=""):
    t0 = time.time()
    model.fit(Xa, ya)
    fit_s = time.time() - t0
    t1 = time.time()
    pred = model.predict(Xb)
    inf_s = time.time() - t1
    sc = scores_of(model, Xb)
    tn, fp, fn, tp = confusion_matrix(yb, pred, labels=[0, 1]).ravel()
    return {
        "model": name,
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
        "fit_seconds": round(fit_s, 2),
        "inference_seconds": round(inf_s, 3),
        "note": note,
    }


def main() -> int:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)

    print(f"scikit-learn {sklearn.__version__} | numpy {np.__version__}")
    print("loading...", flush=True)
    X, y = load_data()
    print(f"  {X.shape}, {int(y.sum()):,} malicious of {len(y):,}")

    print("deduplicating...", flush=True)
    X, y, n_unique, conflicts = deduplicate(X, y)
    print(f"  {n_unique:,} unique rows, {conflicts:,} conflicting-label duplicate pairs")
    print(f"  after dedup: {int((y==0).sum()):,} benign / {int((y==1).sum()):,} malicious")

    idx = np.arange(X.shape[0])
    i_tr, i_tmp = train_test_split(idx, test_size=0.30, random_state=SEED, stratify=y)
    i_va, i_te = train_test_split(i_tmp, test_size=0.50, random_state=SEED, stratify=y[i_tmp])
    X_tr, y_tr = X[i_tr], y[i_tr]
    X_va, y_va = X[i_va], y[i_va]
    X_te, y_te = X[i_te], y[i_te]
    print(f"  train {len(y_tr):,} | val {len(y_va):,} | test {len(y_te):,}")

    # The three selectable classifiers.
    specs = [
        ("Logistic Regression", lambda: LogisticRegression(max_iter=2000, random_state=SEED),
         "logistic_regression.joblib"),
        ("Linear SVM", lambda: LinearSVC(random_state=SEED, max_iter=3000),
         "linear_svm.joblib"),
        ("Random Forest (30 trees)",
         lambda: RandomForestClassifier(n_estimators=30, max_features="sqrt",
                                        random_state=SEED, n_jobs=-1),
         "random_forest.joblib"),
    ]

    val_rows, fitted = [], {}
    for name, make, fname in specs:
        print(f"\ntraining {name} ...", flush=True)
        model = make()
        row = measure(name, model, X_tr, y_tr, X_va, y_va)
        val_rows.append(row)
        fitted[name] = (model, fname)
        print(f"  acc={row['accuracy']} bal={row['balanced_accuracy']} "
              f"recall={row['malware_recall']} f1={row['malware_f1']} "
              f"auc={row['roc_auc']} ({row['fit_seconds']}s)")

    # Control: active-feature count only.
    print("\ntraining control (active-feature count only) ...", flush=True)
    cnt = lambda M: np.diff(M.indptr).astype(float).reshape(-1, 1)
    ctrl = measure("CONTROL: active-count only",
                   DecisionTreeClassifier(max_depth=3, random_state=SEED),
                   cnt(X_tr), y_tr, cnt(X_va), y_va,
                   "single input: number of active features")
    val_rows.append(ctrl)
    print(f"  acc={ctrl['accuracy']} bal={ctrl['balanced_accuracy']} "
          f"recall={ctrl['malware_recall']}")

    # Select on balanced accuracy, excluding the control.
    real = [r for r in val_rows if not r["model"].startswith("CONTROL")]
    best = max(real, key=lambda r: r["balanced_accuracy"])
    selected = best["model"]
    print(f"\nSELECTED on validation balanced accuracy: {selected}")

    # Refit the selected model on train + validation, then evaluate ONCE on test.
    X_fit = sp.vstack([X_tr, X_va], format="csr")
    y_fit = np.concatenate([y_tr, y_va])
    make = dict((n, m) for n, m, _ in specs)[selected]
    final = make()
    test_row = measure(selected, final, X_fit, y_fit, X_te, y_te,
                       "refit on train+validation; test evaluated once")
    print("\nFINAL TEST (evaluated once):")
    for k in ("accuracy", "balanced_accuracy", "malware_precision", "malware_recall",
              "malware_f1", "false_positive_rate", "roc_auc", "pr_auc"):
        print(f"  {k:22s} {test_row[k]}")
    print(f"  confusion [[TN,FP],[FN,TP]] {test_row['confusion_matrix']}")

    # Persist every model, each trained in THIS environment.
    print("\nsaving models...")
    for name, (model, fname) in fitted.items():
        path = MODEL_DIR / fname
        joblib.dump(model, path, compress=3)
        print(f"  {path.name:28s} {path.stat().st_size/1e6:7.2f} MB")
    final_path = MODEL_DIR / "selected_model.joblib"
    joblib.dump(final, final_path, compress=3)
    print(f"  {final_path.name:28s} {final_path.stat().st_size/1e6:7.2f} MB  <- used by the API")

    record = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sklearn_version": sklearn.__version__,
        "numpy_version": np.__version__,
        "scipy_version": sp.__name__ and __import__("scipy").__version__,
        "protocol": {
            "deduplicated": True,
            "unique_rows": int(n_unique),
            "conflicting_label_duplicate_pairs": int(conflicts),
            "split": "70/15/15 stratified",
            "seed": SEED,
            "n_train": int(len(y_tr)),
            "n_val": int(len(y_va)),
            "n_test": int(len(y_te)),
            "label_rule": "vt_detection >= 4",
            "selection_metric": "balanced_accuracy on validation",
            "test_evaluated_once": True,
        },
        "validation_results": val_rows,
        "selected_model": selected,
        "test_result": test_row,
        "caveats": [
            "Single split; no repeated runs or confidence intervals.",
            "No probability calibration was fitted; outputs are not calibrated probabilities.",
            "MH-100K spans 2010-2022; generalisation to current applications is untested.",
            "Compare every model against the active-count control before claiming the "
            "24,833-dimensional representation is doing the work.",
        ],
    }
    out = RESULTS / "model_evaluation.json"
    out.write_text(json.dumps(record, indent=2), encoding="utf-8")
    (ROOT / "ml" / "evaluation_results.json").write_text(
        json.dumps(record, indent=2), encoding="utf-8")
    print(f"\nwrote {out}")
    print("wrote ml/evaluation_results.json (replaces the earlier incorrect file)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
