"""Derived metrics and worked examples for the paper, computed from saved
artifacts only. Writes reports/results/paper_examples.json.

- Test metrics derived from the recorded confusion matrix (specificity, MCC,
  Cohen's kappa, NPV) - pure arithmetic on recorded counts.
- Inference timing of the shipped selected model on the test split.
- Worked examples: one malicious and one benign test-split app, chosen as the
  first of each class in split order (no cherry-picking by score).
"""
import hashlib, json, math, time
from pathlib import Path
import joblib, numpy as np, scipy.sparse as sp
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "reports" / "results"
rec = json.loads((RES / "model_evaluation.json").read_text())
(tn, fp), (fn, tp) = rec["test_result"]["confusion_matrix"]
n = tn + fp + fn + tp
po = (tp + tn) / n
pe = ((tp + fp) * (tp + fn) + (tn + fn) * (tn + fp)) / n ** 2
derived = {
    "specificity": tn / (tn + fp), "npv": tn / (tn + fn),
    "mcc": (tp * tn - fp * fn) / math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)),
    "cohen_kappa": (po - pe) / (1 - pe), "n_test": n,
}

# rebuild the identical deduplicated split, keeping original row indices
X = sp.load_npz(ROOT / "data/processed/mh100_csr.npz").tocsr()
y = np.load(ROOT / "data/processed/classes.npy").astype(int)
sha = np.load(ROOT / "data/processed/sha256.npy", allow_pickle=True)
vocab = [str(v) for v in np.load(ROOT / "data/processed/column_names.npy", allow_pickle=True)]
seen, keep = set(), []
for i in range(X.shape[0]):
    d = hashlib.blake2b(X.indices[X.indptr[i]:X.indptr[i + 1]].astype(np.int32).tobytes(), digest_size=16).digest()
    if d not in seen:
        seen.add(d); keep.append(i)
keep = np.array(keep); Xd, yd = X[keep], y[keep]
idx = np.arange(len(keep))
i_tr, i_tmp = train_test_split(idx, test_size=0.30, random_state=42, stratify=yd)
i_va, i_te = train_test_split(i_tmp, test_size=0.50, random_state=42, stratify=yd[i_tmp])

model = joblib.load(ROOT / "ml/models/selected_model.joblib")
Xte = Xd[i_te]
t0 = time.perf_counter(); proba = model.predict_proba(Xte)[:, 1]; dt = time.perf_counter() - t0
pred = (proba >= 0.5).astype(int)
assert int(((pred == 1) & (yd[i_te] == 1)).sum()) == tp, "model does not reproduce recorded TP"
timing = {"test_rows": int(len(i_te)), "batch_seconds": dt, "ms_per_app": 1000 * dt / len(i_te)}

W = {w["permission"]: w["r"] for w in json.loads((ROOT / "risk/permission_weights.json").read_text())["weights"]}
def example(k):
    row = Xte[k]; feats = [vocab[j] for j in row.indices]
    perms = sorted(f.split("::", 1)[1].split(".")[-1] for f in feats if f.startswith("Permission::"))
    matched = {p: round(W[p], 4) for p in perms if p in W}
    R = round(sum(matched.values()) / len(matched), 4) if matched else None
    return {"sha256_prefix": str(sha[keep[i_te[k]]])[:16], "true_label": "MALWARE" if yd[i_te[k]] else "BENIGN",
            "active_features": int(row.nnz),
            "by_block": {b: sum(f.startswith(b + "::") for f in feats) for b in ("Permission", "Intent", "APICall")},
            "ml_probability": round(float(proba[k]), 4), "ml_label": "MALWARE" if pred[k] else "BENIGN",
            "permissions_in_weighted_set": matched, "R": R}
first_mal = int(np.where(yd[i_te] == 1)[0][0]); first_ben = int(np.where(yd[i_te] == 0)[0][0])
out = {"derived_test_metrics": derived, "inference_timing": timing,
       "example_malicious": example(first_mal), "example_benign": example(first_ben)}
(RES / "paper_examples.json").write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=2))
