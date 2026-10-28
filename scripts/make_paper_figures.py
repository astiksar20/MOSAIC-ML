"""Column-width figures for the IEEE paper, drawn only from saved results.

Inputs : reports/results/fig06_pr_points.csv, fig04_model_comparison.csv,
         model_evaluation.json, two_analyses_comparison.json
Outputs: reports/figures/paper/fig_p1_pipeline.png ... fig_p3_two_analyses.png
"""
import csv, json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "reports" / "results"
OUT = ROOT / "reports" / "figures" / "paper"
OUT.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"font.family": "serif", "font.size": 8, "figure.dpi": 300,
                     "axes.spines.top": False, "axes.spines.right": False})
COL = {"Logistic Regression": "#2E6FBA", "Linear SVM": "#E07B00", "Random Forest": "#2A9D5C"}

# ---- Fig 1: pipeline ----
fig, ax = plt.subplots(figsize=(3.4, 3.0)); ax.axis("off"); ax.set_xlim(0, 10); ax.set_ylim(0, 10)
def box(x, y, w, h, t, fc="#F2F2F2"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05,rounding_size=0.15",
                                fc=fc, ec="#333", lw=0.6))
    ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=5.6)
def arrow(x1, y1, x2, y2):
    ax.annotate("", (x2, y2), (x1, y1), arrowprops=dict(arrowstyle="-|>", lw=0.6, color="#333"))
box(0.3, 8.9, 9.4, 0.8, "APK upload: extension, size and ZIP-header checks; SHA-256")
box(0.3, 7.6, 9.4, 0.8, "Static extraction (Androguard): permissions, intents, API calls")
box(0.3, 6.3, 9.4, 0.8, "Map to the 24,833-feature vocabulary; compute coverage cov(a)")
for y in (8.9, 7.6): arrow(5, y, 5, y - 0.5)
xs = [0.1, 2.6, 5.1, 7.6]
labs = ["ML classifier\n(LR, class-\nweighted)", "Permission\nrisk R(a)\n(Ogwara)", "CVE / NVD\nkeyword\nlookup", "HIDS rules\n(synthetic\nprototype)"]
for x, t in zip(xs, labs):
    box(x, 3.6, 2.3, 1.6, t, fc="#E6EEF8"); arrow(5, 6.3, x + 1.15, 5.2)
box(0.3, 1.6, 9.4, 1.0, "Separated report: each signal with its own reliability\nstatement; scan summary stored (SQLite / PostgreSQL)", fc="#FFF1E6")
for x in xs: arrow(x + 1.15, 3.6, 5, 2.6)
ax.text(5, 0.7, "Prototype 40/40/20 aggregate: retained, labelled deprecated", ha="center", fontsize=6, style="italic", color="#555")
fig.savefig(OUT / "fig_p1_pipeline.png", bbox_inches="tight"); plt.close(fig)

# ---- Fig 2: precision-recall, validation ----
pts = {}
with open(RES / "fig06_pr_points.csv") as f:
    for r in csv.DictReader(f):
        pts.setdefault(r["model"], ([], []))
        pts[r["model"]][0].append(float(r["recall"])); pts[r["model"]][1].append(float(r["precision"]))
ap = {}
with open(RES / "fig04_model_comparison.csv") as f:
    for r in csv.DictReader(f): ap[r["model"]] = float(r["pr_auc"])
rec = json.loads((RES / "model_evaluation.json").read_text())
prev = sum(rec["best_per_family"]["Logistic Regression"]["confusion_matrix"][1]) / rec["protocol"]["n_val"]
fig, ax = plt.subplots(figsize=(3.4, 2.3))
for m, (r, p) in pts.items():
    ax.plot(r, p, color=COL[m], lw=1.1, label=f"{m} (AP {ap[m]:.3f})")
ax.axhline(prev, color="k", ls="--", lw=0.6, label=f"Chance (prevalence {prev:.3f})")
ax.set_xlabel("Malware recall"); ax.set_ylabel("Malware precision")
ax.set_xlim(0, 1); ax.set_ylim(0, 1.02); ax.grid(alpha=.25); ax.legend(fontsize=6, loc="lower left")
fig.savefig(OUT / "fig_p2_pr_curves.png", bbox_inches="tight"); plt.close(fig)

# ---- Fig 3: two analyses ----
t = json.loads((RES / "two_analyses_comparison.json").read_text())["agreement"]
keys = [("both", "Both\nflag"), ("ml_only", "ML\nonly"), ("permission_only", "Permission\nonly"), ("neither", "Neither")]
fig, ax = plt.subplots(figsize=(3.4, 2.1))
v = [t[k]["pct_malware"] for k, _ in keys]
b = ax.bar(range(4), v, color=["#B0413E", "#E07B00", "#2E6FBA", "#8C8C8C"], width=0.6)
for i, (k, _) in enumerate(keys):
    ax.text(i, v[i] + 2, f"{v[i]:.1f}%\nn={t[k]['n']:,}", ha="center", fontsize=6.5)
ax.set_xticks(range(4)); ax.set_xticklabels([l for _, l in keys], fontsize=7)
ax.set_ylabel("Actually malware (%)"); ax.set_ylim(0, 112); ax.grid(axis="y", alpha=.25)
fig.savefig(OUT / "fig_p3_two_analyses.png", bbox_inches="tight"); plt.close(fig)
print("wrote", sorted(p.name for p in OUT.iterdir()))
