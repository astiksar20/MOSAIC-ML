"""Standard-symbol flowcharts for the paper (column width).

Symbols: terminator (rounded capsule), input/output (parallelogram),
process (rectangle), decision (diamond), document (wavy base),
data store (cylinder). Every number shown is from the executed pipeline.
Outputs: reports/figures/paper/fig_flow_system.png, fig_flow_training.png
"""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Polygon, Ellipse, PathPatch
from matplotlib.path import Path as MPath
import numpy as np

OUT = Path(__file__).resolve().parent.parent / "reports" / "figures" / "paper"
OUT.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"font.family": "serif", "figure.dpi": 300})
FS = 5.6
EC, LW = "#222222", 0.7
FILL = {"term": "#D9D9D9", "io": "#DCE9F7", "proc": "#FFFFFF", "dec": "#FFF2CC", "doc": "#E2F0D9", "db": "#FCE4D6"}


class Chart:
    def __init__(self, w, h):
        self.fig, self.ax = plt.subplots(figsize=(w / 10, h / 10))
        self.ax.set_xlim(0, w); self.ax.set_ylim(0, h); self.ax.set_aspect("equal"); self.ax.axis("off")

    def text(self, x, y, t, fs=FS, **k):
        self.ax.text(x, y, t, ha="center", va="center", fontsize=fs, linespacing=1.15, zorder=5, **k)

    def term(self, x, y, w, h, t):
        self.ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle=f"round,pad=0,rounding_size={h/2}",
                                         fc=FILL["term"], ec=EC, lw=LW, zorder=3))
        self.text(x, y, t, weight="bold"); return (x, y, w, h)

    def proc(self, x, y, w, h, t, fc=None, dashed=False):
        self.ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fc=fc or FILL["proc"], ec=EC, lw=LW, zorder=3,
                                    ls="--" if dashed else "-"))
        self.text(x, y, t); return (x, y, w, h)

    def io(self, x, y, w, h, t):
        s = h * 0.35
        self.ax.add_patch(Polygon([(x - w / 2 + s, y + h / 2), (x + w / 2 + s, y + h / 2),
                                   (x + w / 2 - s, y - h / 2), (x - w / 2 - s, y - h / 2)],
                                  fc=FILL["io"], ec=EC, lw=LW, zorder=3))
        self.text(x, y, t); return (x, y, w, h)

    def dec(self, x, y, w, h, t):
        self.ax.add_patch(Polygon([(x, y + h / 2), (x + w / 2, y), (x, y - h / 2), (x - w / 2, y)],
                                  fc=FILL["dec"], ec=EC, lw=LW, zorder=3))
        self.text(x, y, t, fs=FS - 0.3); return (x, y, w, h)

    def doc(self, x, y, w, h, t):
        x0, x1, y0, y1 = x - w / 2, x + w / 2, y - h / 2 + h * 0.12, y + h / 2
        xs = np.linspace(x1, x0, 40); ys = y0 + h * 0.12 * np.sin((xs - x0) / w * 2 * np.pi)
        verts = [(x0, y1), (x1, y1)] + list(zip(xs, ys)) + [(x0, y1)]
        self.ax.add_patch(Polygon(verts, fc=FILL["doc"], ec=EC, lw=LW, zorder=3))
        self.text(x, y + h * 0.06, t); return (x, y, w, h)

    def db(self, x, y, w, h, t):
        e = h * 0.22
        self.ax.add_patch(Rectangle((x - w / 2, y - h / 2 + e / 2), w, h - e, fc=FILL["db"], ec="none", zorder=3))
        self.ax.add_patch(Ellipse((x, y - h / 2 + e / 2), w, e, fc=FILL["db"], ec=EC, lw=LW, zorder=3))
        self.ax.plot([x - w / 2, x - w / 2], [y - h / 2 + e / 2, y + h / 2 - e / 2], color=EC, lw=LW, zorder=4)
        self.ax.plot([x + w / 2, x + w / 2], [y - h / 2 + e / 2, y + h / 2 - e / 2], color=EC, lw=LW, zorder=4)
        self.ax.add_patch(Ellipse((x, y + h / 2 - e / 2), w, e, fc=FILL["db"], ec=EC, lw=LW, zorder=4))
        self.text(x, y - e * 0.25, t); return (x, y, w, h)

    def line(self, pts, arrow=True, label=None, lpos=None):
        xs, ys = zip(*pts)
        if arrow and len(pts) > 2:
            self.ax.plot(xs[:-1], ys[:-1], color=EC, lw=LW, zorder=2)
            pts = pts[-2:]
        if arrow:
            self.ax.annotate("", pts[-1], pts[0], zorder=2,
                             arrowprops=dict(arrowstyle="-|>,head_length=0.35,head_width=0.18", lw=LW, color=EC,
                                             shrinkA=0, shrinkB=0))
        else:
            self.ax.plot(xs, ys, color=EC, lw=LW, zorder=2)
        if label:
            self.ax.text(*lpos, label, fontsize=FS - 0.4, style="italic", ha="center", va="center", zorder=6,
                         bbox=dict(fc="white", ec="none", pad=0.3))

    def save(self, name):
        self.fig.savefig(OUT / name, bbox_inches="tight", pad_inches=0.02); plt.close(self.fig)


top = lambda n: (n[0], n[1] + n[3] / 2)
bot = lambda n: (n[0], n[1] - n[3] / 2)
rgt = lambda n: (n[0] + n[2] / 2, n[1])
lft = lambda n: (n[0] - n[2] / 2, n[1])

# ======================= Fig. 1: system / scan flowchart =======================
c = Chart(38, 66)
M = 15
U = 6  # vertical offset to make room for the final End
n_start = c.term(M, U + 57.5, 10, 3, "Start")
n_up = c.io(M, U + 52.3, 21, 3.6, "Input: APK uploaded to the dashboard")
n_val = c.dec(M, U + 44.6, 15, 7.2, "Valid package?\n.apk, ≤ 150 MB,\nZIP header")
n_rej = c.proc(32, U + 44.6, 9, 4.4, "Reject\n(HTTP 400\nwith reason)")
n_end2 = c.term(32, U + 37.6, 7, 3, "End")
n_ext = c.proc(M, U + 36.6, 21, 5.4, "Compute SHA-256; static extraction\n(Androguard): permissions,\nintents, API calls")
n_map = c.proc(M, U + 29.4, 21, 4.4, "Map to 24,833-feature vocabulary;\ncoverage = matched / 24,833")
n_cov = c.dec(M, U + 22.0, 12, 6.6, "Matched\nfeatures\n≥ 50?")
n_flag = c.proc(31.5, U + 22.0, 10, 4.4, "Mark ML output\nas low\nreliability")
xs = [4.9, 14.3, 23.7, 33.1]
labels = ["ML classifier\nP(malware)\n(weighted LR)", "Permission\nrisk R(a)\n(null if k = 0)", "CVE / NVD\nkeyword\nlookup", "HIDS rules\n(synthetic\nprototype)"]
boxes = [c.proc(x, U + 11.4, 8.6, 6.6, t, fc="#EEF3FA") for x, t in zip(xs, labels)]
n_doc = c.doc(12, U + 2.6, 18, 4.8, "Output: separated report,\none panel per signal")
n_db = c.db(31.5, U + 2.6, 10, 6.6, "Store\nsummary +\nSHA-256")
n_end = c.term(12, 1.6, 9, 3, "End")
# edges
c.line([bot(n_start), top(n_up)])
c.line([bot(n_up), top(n_val)])
c.line([rgt(n_val), lft(n_rej)], label="No", lpos=(25.0, U + 45.6))
c.line([bot(n_rej), top(n_end2)])
c.line([bot(n_val), top(n_ext)], label="Yes", lpos=(M + 1.6, U + 40.0))
c.line([bot(n_ext), top(n_map)])
c.line([bot(n_map), top(n_cov)])
c.line([rgt(n_cov), lft(n_flag)], label="No", lpos=(23.6, U + 23.0))
BUS = U + 16.6
c.line([bot(n_cov), (M, BUS)], arrow=False, label="Yes", lpos=(M + 1.6, U + 17.7))
c.line([bot(n_flag), (31.5, BUS)], arrow=False)
c.line([(xs[0], BUS), (xs[-1], BUS)], arrow=False)
for b in boxes:
    c.line([(b[0], BUS), top(b)])
JOIN = U + 7.0
for b in boxes:
    c.line([bot(b), (b[0], JOIN)], arrow=False)
c.line([(xs[0], JOIN), (xs[-1], JOIN)], arrow=False)
c.line([(12, JOIN), top(n_doc)])
c.line([(31.5, JOIN), top(n_db)])
c.line([bot(n_doc), top(n_end)])
c.save("fig_flow_system.png")

# ======================= Fig. 2: training / evaluation flowchart =======================
c = Chart(37, 62)
M = 13
n0 = c.term(M, 59.5, 10, 3, "Start")
n1 = c.io(M, 54.3, 21, 3.8, "Input: MH-100K .npz\n101,934 apps × 24,833 features")
n2 = c.proc(M, 47.7, 21, 4.4, "np.load (column-major aware)\n→ sparse CSR matrix")
n3 = c.dec(M, 39.6, 17, 8.0, "Integrity check:\nnnz = 185,917,518 and\nrow sizes vary?")
n3b = c.term(30, 39.6, 9, 4.0, "Stop:\nmatrix\ncorrupt")
n4 = c.proc(M, 31.4, 21, 4.4, "Label: vt_detection ≥ 4; remove\nduplicates → 58,576 unique apps")
n5 = c.proc(M, 25.0, 21, 4.4, "Stratified split 70/15/15 (seed 42)\n41,003 / 8,786 / 8,787")
n5b = c.proc(30, 18.6, 10, 5.4, "Fit permission\nweights\nr = √(α(1 − β))\non train only")
n6 = c.proc(M, 18.6, 21, 4.4, "Train 9 configurations (LR, SVM,\nRF ± class weights) + control")
n7 = c.proc(M, 12.4, 21, 4.4, "Score on validation; select max\nbalanced accuracy → weighted LR")
n8 = c.proc(M, 6.2, 21, 4.4, "Refit on train + validation;\nevaluate ONCE on test")
n9 = c.db(30, 6.2, 10, 6.6, "Save\nmodels,\nmetrics")
n10 = c.term(M, 1.5, 10, 3, "End")
c.line([bot(n0), top(n1)]); c.line([bot(n1), top(n2)]); c.line([bot(n2), top(n3)])
c.line([rgt(n3), lft(n3b)], label="No", lpos=(24.3, 40.6))
c.line([bot(n3), top(n4)], label="Yes", lpos=(M + 1.6, 34.6))
c.line([bot(n4), top(n5)]); c.line([bot(n5), top(n6)])
c.line([rgt(n5), (30, 25.0), top(n5b)])
c.line([bot(n6), top(n7)]); c.line([bot(n7), top(n8)])
c.line([rgt(n8), lft(n9)])
c.line([bot(n5b), top(n9)])
c.line([bot(n8), top(n10)])
c.save("fig_flow_training.png")
print("wrote fig_flow_system.png, fig_flow_training.png")
