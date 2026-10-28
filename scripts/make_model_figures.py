"""
MOSAIC-ML - model figures from the verified tuning run.

Reads reports/results/model_evaluation.json (written by tune_models.py) and the
saved models in ml/models/. Rebuilds the exact same deduplicated split (seed 42)
so the curves are drawn on the same validation rows the numbers came from.

Figures
  fig04_model_comparison.png    validation metrics, best config per family + control
  fig05_confusion_matrices.png  validation (3 models) + final test (selected)
  fig06_roc_pr_curves.png       ROC and precision-recall, validation
  fig07_threshold_analysis.png  selected family: precision/recall/FPR vs threshold, validation
  fig08_tuning_grid.png         every configuration tried, validation balanced accuracy

Source data for every figure is written next to it as CSV.
Usage: python scripts/make_model_figures.py
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import (precision_recall_curve, roc_curve,
                             precision_score, recall_score, confusion_matrix)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from tune_models import dedup_split  # identical split, by construction

RES = ROOT / "reports" / "results"
FIG = ROOT / "reports" / "figures"
MOD = ROOT / "ml" / "models"
FIG.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({"font.size": 9, "figure.dpi": 200, "axes.spines.top": False,
                     "axes.spines.right": False})
COL = {"Logistic Regression": "#2E6FBA", "Linear SVM": "#E07B00",
       "Random Forest": "#2A9D5C", "Control": "#B0413E"}
FILES = {"Logistic Regression": "logistic_regression.joblib",
         "Linear SVM": "linear_svm.joblib", "Random Forest": "random_forest.joblib"}


def score(m, X):
    return m.predict_proba(X)[:, 1] if hasattr(m, "predict_proba") else m.decision_function(X)


def write_csv(path, header, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f); w.writerow(header); w.writerows(rows)


def main():
    rec = json.loads((RES / "model_evaluation.json").read_text())
    fam = rec["best_per_family"]
    ctrl = next(r for r in rec["validation_results"] if r["family"] == "Control")
    test = rec["test_result"]
    n_val = rec["protocol"]["n_val"]

    # ---------- Fig 4: metric comparison ----------
    names = list(fam) + ["Control (count only)"]
    rows = [fam[f] for f in fam] + [ctrl]
    colors = [COL[f] for f in fam] + [COL["Control"]]
    mets = [("accuracy", "Accuracy"), ("balanced_accuracy", "Balanced accuracy"),
            ("malware_recall", "Malware recall"), ("malware_precision", "Malware precision"),
            ("malware_f1", "Malware F1"), ("false_positive_rate", "False-positive rate (lower is better)")]
    fig, axes = plt.subplots(2, 3, figsize=(12, 6.2))
    for ax, (k, t) in zip(axes.ravel(), mets):
        v = [r[k] for r in rows]
        ax.bar(range(len(v)), v, color=colors, width=0.65)
        ax.set_xticks(range(len(v)))
        ax.set_xticklabels(["LR", "SVM", "RF", "Control"])
        ax.set_title(t, fontsize=10)
        lo = 0 if k == "false_positive_rate" else max(0, min(v) - 0.12)
        ax.set_ylim(lo, max(v) * (1.25 if k == "false_positive_rate" else 1.0) + 0.02)
        for i, x in enumerate(v):
            ax.text(i, x, f"{x:.4f}", ha="center", va="bottom", fontsize=7.5)
        ax.grid(axis="y", alpha=.25)
    fig.suptitle(f"Figure 4 - Validation metrics, best configuration per model (n = {n_val:,}). "
                 "Red = count-only shortcut control", fontsize=10.5)
    fig.tight_layout(); fig.savefig(FIG / "fig04_model_comparison.png", bbox_inches="tight"); plt.close(fig)
    write_csv(RES / "fig04_model_comparison.csv",
              ["model", "config"] + [k for k, _ in mets] + ["roc_auc", "pr_auc"],
              [[n, r["config"].strip()] + [r[k] for k, _ in mets] + [r["roc_auc"], r["pr_auc"]]
               for n, r in zip(names, rows)])

    # ---------- Fig 8: whole tuning grid ----------
    grid = [r for r in rec["validation_results"]]
    fig, ax = plt.subplots(figsize=(9, 4.6))
    y = np.arange(len(grid))
    ax.barh(y, [r["balanced_accuracy"] for r in grid], color=[COL[r["family"]] for r in grid])
    ax.set_yticks(y); ax.set_yticklabels([" ".join(r["config"].split()) for r in grid], fontsize=8)
    for i, r in enumerate(grid):
        tag = "  <- selected" if r["config"] == rec["selected_config"] else ""
        ax.text(r["balanced_accuracy"], i, f" {r['balanced_accuracy']:.4f}{tag}", va="center", fontsize=7.5)
    ax.set_xlim(min(r["balanced_accuracy"] for r in grid) - 0.03, 1.0)
    ax.invert_yaxis(); ax.grid(axis="x", alpha=.25)
    ax.set_xlabel("Validation balanced accuracy")
    ax.set_title("Figure 8 - Every configuration tried (validation only; test untouched)", fontsize=10.5)
    fig.tight_layout(); fig.savefig(FIG / "fig08_tuning_grid.png", bbox_inches="tight"); plt.close(fig)
    write_csv(RES / "fig08_tuning_grid.csv",
              ["config", "family", "accuracy", "balanced_accuracy", "malware_recall",
               "malware_precision", "false_positive_rate", "fit_seconds"],
              [[" ".join(r["config"].split()), r["family"], r["accuracy"], r["balanced_accuracy"],
                r["malware_recall"], r["malware_precision"], r["false_positive_rate"], r["fit_seconds"]]
               for r in grid])

    # ---------- curves need the actual models and validation rows ----------
    print("rebuilding split for curves...", flush=True)
    (X_tr, y_tr), (X_va, y_va), _, _ = dedup_split()
    models = {f: joblib.load(MOD / FILES[f]) for f in fam}
    scores = {f: score(m, X_va) for f, m in models.items()}

    # sanity: saved models must reproduce the recorded validation confusion matrices
    for f, m in models.items():
        cm = confusion_matrix(y_va, m.predict(X_va), labels=[0, 1]).tolist()
        assert cm == fam[f]["confusion_matrix"], f"{f}: {cm} != {fam[f]['confusion_matrix']}"
    print("  saved models reproduce recorded validation results: OK")

    # ---------- Fig 5: confusion matrices ----------
    panels = [(f"{f}\nvalidation", fam[f]["confusion_matrix"], COL[f]) for f in fam]
    panels.append((f"{test['family']} (selected)\nFINAL TEST, once", test["confusion_matrix"], "#333333"))
    fig, axes = plt.subplots(1, 4, figsize=(13, 3.4))
    for ax, (t, cm, c) in zip(axes, panels):
        cm = np.array(cm)
        norm = cm / cm.sum(axis=1, keepdims=True)
        ax.imshow(norm, cmap="Greys", vmin=0, vmax=1.4)
        for (i, j), v in np.ndenumerate(cm):
            ax.text(j, i, f"{v:,}\n({norm[i, j]*100:.1f}%)", ha="center", va="center", fontsize=8.5,
                    color="white" if norm[i, j] > .7 else "black")
        ax.set_xticks([0, 1]); ax.set_xticklabels(["pred benign", "pred malware"], fontsize=8)
        ax.set_yticks([0, 1]); ax.set_yticklabels(["benign", "malware"], fontsize=8)
        ax.set_title(t, fontsize=9, color=c)
    fig.suptitle("Figure 5 - Confusion matrices (counts; % of the true class)", fontsize=10.5)
    fig.tight_layout(); fig.savefig(FIG / "fig05_confusion_matrices.png", bbox_inches="tight"); plt.close(fig)
    write_csv(RES / "fig05_confusion_matrices.csv", ["panel", "TN", "FP", "FN", "TP"],
              [[t.replace("\n", " "), *np.array(cm).ravel().tolist()] for t, cm, _ in panels])

    # ---------- Fig 6: ROC + PR ----------
    prev = y_va.mean()
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.6))
    roc_rows, pr_rows = [], []
    for f, s in scores.items():
        fpr, tpr, _ = roc_curve(y_va, s)
        p, r, _ = precision_recall_curve(y_va, s)
        a1.plot(fpr, tpr, color=COL[f], lw=1.6, label=f"{f}  AUC {fam[f]['roc_auc']:.4f}")
        a2.plot(r, p, color=COL[f], lw=1.6, label=f"{f}  AP {fam[f]['pr_auc']:.4f}")
        idx = np.linspace(0, len(fpr) - 1, min(400, len(fpr))).astype(int)
        roc_rows += [[f, fpr[i], tpr[i]] for i in idx]
        idx = np.linspace(0, len(p) - 1, min(400, len(p))).astype(int)
        pr_rows += [[f, r[i], p[i]] for i in idx]
    a1.plot([0, 1], [0, 1], "k--", lw=.8, label="chance")
    a1.set_xlabel("False-positive rate"); a1.set_ylabel("True-positive rate (malware recall)")
    a1.set_title("ROC (validation)"); a1.legend(fontsize=8, loc="lower right")
    a2.axhline(prev, color="k", ls="--", lw=.8, label=f"chance = prevalence {prev:.3f}")
    a2.set_xlabel("Recall (malware)"); a2.set_ylabel("Precision (malware)")
    a2.set_title("Precision-recall (validation)"); a2.legend(fontsize=8, loc="lower left")
    for a in (a1, a2): a.grid(alpha=.25); a.set_xlim(0, 1); a.set_ylim(0, 1.01)
    fig.suptitle("Figure 6 - ROC and precision-recall curves. PR is the more informative view at "
                 f"{prev*100:.1f}% malware prevalence", fontsize=10.5)
    fig.tight_layout(); fig.savefig(FIG / "fig06_roc_pr_curves.png", bbox_inches="tight"); plt.close(fig)
    write_csv(RES / "fig06_roc_points.csv", ["model", "fpr", "tpr"], roc_rows)
    write_csv(RES / "fig06_pr_points.csv", ["model", "recall", "precision"], pr_rows)

    # ---------- Fig 7: threshold analysis for the selected family ----------
    sel = test["family"]
    s = scores[sel]
    proba = hasattr(models[sel], "predict_proba")
    ths = np.linspace(0.05, 0.95, 91) if proba else np.quantile(s, np.linspace(0.5, 0.995, 91))
    trows = []
    for t in ths:
        pr = (s >= t).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_va, pr, labels=[0, 1]).ravel()
        trows.append([float(t), precision_score(y_va, pr, zero_division=0),
                      recall_score(y_va, pr, zero_division=0), fp / (fp + tn),
                      0.5 * (tp / (tp + fn) + tn / (tn + fp))])
    T = np.array(trows)
    fig, ax = plt.subplots(figsize=(8.5, 4.4))
    ax.plot(T[:, 0], T[:, 1], color="#2E6FBA", label="malware precision")
    ax.plot(T[:, 0], T[:, 2], color="#2A9D5C", label="malware recall")
    ax.plot(T[:, 0], T[:, 3], color="#B0413E", label="false-positive rate")
    ax.plot(T[:, 0], T[:, 4], color="#333333", ls="--", label="balanced accuracy")
    if proba:
        ax.axvline(0.5, color="grey", ls=":", lw=1); ax.text(0.505, 0.03, "default 0.5", fontsize=7.5)
    ax.set_xlabel("Decision threshold on P(malware)" if proba else "Decision-function threshold")
    ax.set_ylim(0, 1.02); ax.grid(alpha=.25); ax.legend(fontsize=8, loc="center left")
    ax.set_title(f"Figure 7 - Threshold trade-off, {sel} (validation). "
                 "Threshold not tuned; model uses 0.5", fontsize=10)
    fig.tight_layout(); fig.savefig(FIG / "fig07_threshold_analysis.png", bbox_inches="tight"); plt.close(fig)
    write_csv(RES / "fig07_threshold_analysis.csv",
              ["threshold", "precision", "recall", "fpr", "balanced_accuracy"], trows)

    print("wrote fig04, fig05, fig06, fig07, fig08 + CSV source data")


if __name__ == "__main__":
    main()
