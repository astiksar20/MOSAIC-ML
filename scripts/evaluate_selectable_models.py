from pathlib import Path
import json
import time

import joblib
import numpy as np
from scipy import sparse
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed"
MODEL_DIR = ROOT / "ml"

print("Loading dataset...", flush=True)
start = time.time()

X = sparse.load_npz(DATA / "mh100_csr.npz")
y = np.load(DATA / "classes.npy")

print(f"Dataset loaded: {X.shape}", flush=True)

_, X_test, _, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y,
)

models = [
    ("Logistic Regression", MODEL_DIR / "models" / "logistic_regression.joblib"),
    ("Linear SVM", MODEL_DIR / "models" / "linear_svm.joblib"),
    ("Random Forest (30 trees)", MODEL_DIR / "random_forest_model.joblib"),
]

results = []

for name, path in models:
    if not path.exists():
        print(f"\nSKIPPED {name}: file not found: {path}", flush=True)
        continue

    print(f"\nEvaluating {name}...", flush=True)
    model = joblib.load(path)
    predictions = model.predict(X_test)

    result = {
        "model": name,
        "accuracy": round(float(accuracy_score(y_test, predictions)), 4),
        "precision": round(float(precision_score(y_test, predictions, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, predictions, zero_division=0)), 4),
        "f1_score": round(float(f1_score(y_test, predictions, zero_division=0)), 4),
        "confusion_matrix_labels": ["0", "1"],
        "confusion_matrix": confusion_matrix(y_test, predictions, labels=[0, 1]).tolist(),
    }

    if hasattr(model, "predict_proba"):
        scores = model.predict_proba(X_test)[:, 1]
        result["roc_auc"] = round(float(roc_auc_score(y_test, scores)), 4)
    elif hasattr(model, "decision_function"):
        scores = model.decision_function(X_test)
        result["roc_auc"] = round(float(roc_auc_score(y_test, scores)), 4)

    results.append(result)
    print(json.dumps(result, indent=2), flush=True)

output = MODEL_DIR / "evaluation_results.json"
output.write_text(json.dumps(results, indent=2), encoding="utf-8")

print(f"\nResults saved to: {output}", flush=True)
print(f"Total time: {time.time() - start:.1f} seconds", flush=True)
