"""Column-width performance graphs for the paper, from saved results only."""
import csv, json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "reports" / "results"
OUT = ROOT / "reports" / "figures" / "paper"
plt.rcParams.update({"font.family": "serif", "font.size": 7, "figure.dpi": 300,
                     "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False})
COL = {"Logistic Regression": "#2E6FBA", "Linear SVM": "#E07B00", "Random Forest": "#2A9D5C", "Control": "#B0413E"}
SHORT = {"Logistic Regression": "LR", "Linear SVM": "Linear SVM", "Random Forest": "RF (30)", "Control": "Control"}
rec = json.loads((RES / "model_evaluation.json").read_text())
fam = rec["best_per_family"]
ctrl = next(r for r in rec["validation_results"] if r["family"] == "Control")
rows = {**fam, "Control": ctrl}

# ---- metrics grouped bars (validation) ----
mets = [("accuracy", "Accuracy"), ("balanced_accuracy", "Balanced\naccuracy"), ("malware_recall", "Malware\nrecall"),
        ("malware_precision", "Malware\nprecision"), ("malware_f1", "Malware\nF1")]
fig, ax = plt.subplots(figsize=(3.45, 1.95))
w = 0.2
for i, (m, r) in enumerate(rows.items()):
    v = [r[k] for k, _ in mets]
    ax.bar(np.arange(len(mets)) + (i - 1.5) * w, v, w, color=COL[m], label=SHORT[m])
ax.set_xticks(range(len(mets))); ax.set_xticklabels([l for _, l in mets], fontsize=6.3)
ax.set_ylim(0.75, 1.0); ax.set_ylabel("Score (validation)"); ax.grid(axis="y", alpha=.3)
ax.legend(ncol=4, fontsize=6, loc="upper center", bbox_to_anchor=(0.5, 1.16))
fig.savefig(OUT / "fig_g_metrics.png", bbox_inches="tight"); plt.close(fig)

# ---- ROC + PR (validation) ----
def load(fn, a, b):
    d = {}
    with open(RES / fn) as f:
        for r in csv.DictReader(f):
            d.setdefault(r["model"], ([], []))
            d[r["model"]][0].append(float(r[a])); d[r["model"]][1].append(float(r[b]))
    return d
roc, pr = load("fig06_roc_points.csv", "fpr", "tpr"), load("fig06_pr_points.csv", "recall", "precision")
fig, (a1, a2) = plt.subplots(1, 2, figsize=(3.45, 1.75))
for m in fam:
    a1.plot(*roc[m], color=COL[m], lw=1, label=f"{SHORT[m]} {fam[m]['roc_auc']:.3f}")
    a2.plot(*pr[m], color=COL[m], lw=1, label=f"{SHORT[m]} {fam[m]['pr_auc']:.3f}")
a1.plot([0, 1], [0, 1], "k--", lw=.5)
prev = sum(fam["Logistic Regression"]["confusion_matrix"][1]) / rec["protocol"]["n_val"]
a2.axhline(prev, color="k", ls="--", lw=.5)
a1.set_xlabel("False-positive rate"); a1.set_ylabel("Malware recall"); a1.set_title("(a) ROC, AUC", fontsize=7)
a2.set_xlabel("Malware recall"); a2.set_ylabel("Precision"); a2.set_title("(b) Precision–recall, AP", fontsize=7)
for a in (a1, a2):
    a.set_xlim(0, 1); a.set_ylim(0, 1.02); a.grid(alpha=.25); a.legend(fontsize=5.2, loc="lower right" if a is a1 else "lower left")
fig.tight_layout(w_pad=1.0); fig.savefig(OUT / "fig_g_roc_pr.png", bbox_inches="tight"); plt.close(fig)

# ---- test confusion matrix ----
cm = np.array(rec["test_result"]["confusion_matrix"]); norm = cm / cm.sum(1, keepdims=True)
fig, ax = plt.subplots(figsize=(2.1, 1.75))
ax.imshow(norm, cmap="Blues", vmin=0, vmax=1.15)
for (i, j), v in np.ndenumerate(cm):
    ax.text(j, i, f"{v:,}\n({norm[i, j]*100:.1f}%)", ha="center", va="center", fontsize=7,
            color="white" if norm[i, j] > .6 else "black")
ax.set_xticks([0, 1]); ax.set_xticklabels(["Benign", "Malware"]); ax.set_yticks([0, 1]); ax.set_yticklabels(["Benign", "Malware"])
ax.set_xlabel("Predicted"); ax.set_ylabel("Actual")
for s in ax.spines.values(): s.set_visible(False)
fig.savefig(OUT / "fig_g_confusion.png", bbox_inches="tight"); plt.close(fig)

# ---- active-feature shortcut ----
n, lab = [], []
with open(RES / "nonzero_features_per_app.csv") as f:
    for r in csv.DictReader(f):
        n.append(int(r["nonzero_features"])); lab.append(int(r["label"]))
n, lab = np.array(n), np.array(lab)
bins = np.logspace(0, np.log10(n.max() + 1), 45)
fig, ax = plt.subplots(figsize=(3.45, 1.55))
ax.hist(n[lab == 0], bins=bins, color=COL["Logistic Regression"], alpha=.65, label=f"Benign (median {int(np.median(n[lab==0])):,})", weights=np.full((lab==0).sum(), 100/(lab==0).sum()))
ax.hist(n[lab == 1], bins=bins, color=COL["Control"], alpha=.65, label=f"Malware (median {int(np.median(n[lab==1])):,})", weights=np.full((lab==1).sum(), 100/(lab==1).sum()))
ax.axvline(100, color="k", ls=":", lw=.6)
ax.set_xscale("log"); ax.set_xlabel("Active features per app (log scale)"); ax.set_ylabel("% of class"); ax.legend(fontsize=6, loc="upper left")
fig.savefig(OUT / "fig_g_shortcut.png", bbox_inches="tight"); plt.close(fig)

# ---- permission weights ----
W = sorted(json.loads((ROOT / "risk/permission_weights.json").read_text())["weights"], key=lambda w: w["r"])
fig, ax = plt.subplots(figsize=(3.45, 2.1))
y = np.arange(len(W))
ax.barh(y, [w["r"] for w in W], color="#E07B00", height=.65)
ax.set_yticks(y); ax.set_yticklabels([w["permission"] for w in W], fontsize=5.6)
for i, w in enumerate(W):
    ax.text(w["r"] + .01, i, f"{w['r']:.3f}  (α {w['alpha']:.2f}, β {w['beta']:.2f})", va="center", fontsize=5)
ax.set_xlim(0, 1.18); ax.set_xlabel("Weight r = √(α(1 − β)), fitted on the training split")
fig.savefig(OUT / "fig_g_perm_weights.png", bbox_inches="tight"); plt.close(fig)
print("wrote", sorted(p.name for p in OUT.glob("fig_g_*.png")))
print("check: shortcut medians", int(np.median(n[lab == 0])), int(np.median(n[lab == 1])), "rows", len(n))
