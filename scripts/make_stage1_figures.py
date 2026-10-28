"""Generate Figures 2 and 3 from real MH-100K data. No mock values."""
import numpy as np, scipy.sparse as sp, csv, json
from pathlib import Path
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

FIG = Path('reports/figures'); RES = Path('reports/results')
FIG.mkdir(parents=True, exist_ok=True); RES.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({'font.size': 10, 'figure.dpi': 200})

z = np.load('data/mh100k/mh100.npz', allow_pickle=True)
y = np.asarray(z['classes']).astype(int)
X = sp.load_npz('data/processed/mh100_csr.npz').tocsr()
nnz = np.diff(X.indptr)

# ---- Figure 2: class distribution ----
counts = [int((y==0).sum()), int((y==1).sum())]
pct = [100*c/len(y) for c in counts]
labels = ['Benign\n(VT < 4)', 'Malware\n(VT >= 4)']
fig, ax = plt.subplots(1, 2, figsize=(9, 3.6))
b = ax[0].bar(labels, counts, color=['#4C72B0', '#C44E52'], width=.6)
ax[0].set_ylabel('Number of samples'); ax[0].set_title('MH-100K class counts (n = %d)' % len(y))
for r, c in zip(b, counts): ax[0].text(r.get_x()+r.get_width()/2, c, f'{c:,}', ha='center', va='bottom', fontsize=9)
ax[0].set_ylim(0, max(counts)*1.15)
b2 = ax[1].bar(labels, pct, color=['#4C72B0', '#C44E52'], width=.6)
ax[1].set_ylabel('Percentage of samples (%)'); ax[1].set_title('Class proportions (imbalance 9.40 : 1)')
for r, p in zip(b2, pct): ax[1].text(r.get_x()+r.get_width()/2, p, f'{p:.2f}%', ha='center', va='bottom', fontsize=9)
ax[1].set_ylim(0, 100)
fig.suptitle('Figure 2 - MH-100K class distribution (labels: vt_detection >= 4)', y=1.02, fontsize=11)
fig.tight_layout(); fig.savefig(FIG/'fig02_class_distribution.png', bbox_inches='tight'); plt.close(fig)
with open(RES/'fig02_class_distribution.csv','w',newline='',encoding='utf-8') as f:
    w=csv.writer(f); w.writerow(['class','label_rule','count','percent'])
    w.writerow([0,'vt_detection < 4',counts[0],round(pct[0],4)])
    w.writerow([1,'vt_detection >= 4',counts[1],round(pct[1],4)])

# ---- Figure 3: sparsity / non-zero features per app ----
fig, ax = plt.subplots(1, 2, figsize=(9.5, 3.6))
ax[0].hist(nnz, bins=80, color='#55A868', edgecolor='white', linewidth=.3)
ax[0].set_xlabel('Active (non-zero) features per app'); ax[0].set_ylabel('Number of apps')
ax[0].set_title('Distribution of active features\n(mean %.0f, median %.0f of 24,833)' % (nnz.mean(), np.median(nnz)))
ax[0].axvline(nnz.mean(), color='#C44E52', ls='--', lw=1.2, label='mean %.0f'%nnz.mean())
ax[0].axvline(5, color='#8172B2', ls=':', lw=1.6, label='test APK = 5')
ax[0].legend(fontsize=8)
for cls, col, nm in [(0,'#4C72B0','Benign'),(1,'#C44E52','Malware')]:
    ax[1].hist(nnz[y==cls], bins=70, alpha=.6, color=col, label=f'{nm} (median {np.median(nnz[y==cls]):.0f})', density=True)
ax[1].set_xlabel('Active (non-zero) features per app'); ax[1].set_ylabel('Density')
ax[1].set_title('Active features by class\nOverall matrix density 7.34%')
ax[1].legend(fontsize=8)
fig.suptitle('Figure 3 - MH-100K feature sparsity and active-feature distribution', y=1.02, fontsize=11)
fig.tight_layout(); fig.savefig(FIG/'fig03_sparsity.png', bbox_inches='tight'); plt.close(fig)

stats = {
    'n_samples': int(len(y)), 'n_features': int(X.shape[1]),
    'stored_nonzeros': int(X.nnz), 'density': float(X.nnz/(X.shape[0]*X.shape[1])),
    'active_features_per_app': {
        'min': int(nnz.min()), 'p5': float(np.percentile(nnz,5)), 'p25': float(np.percentile(nnz,25)),
        'median': float(np.median(nnz)), 'mean': float(nnz.mean()),
        'p75': float(np.percentile(nnz,75)), 'p99': float(np.percentile(nnz,99)), 'max': int(nnz.max())},
    'by_class': {str(c): {'median': float(np.median(nnz[y==c])), 'mean': float(nnz[y==c].mean())} for c in (0,1)},
    'test_apk_active_features': 5,
    'training_apps_with_le_5_active': int((nnz<=5).sum()),
}
(RES/'fig03_sparsity_stats.json').write_text(json.dumps(stats, indent=2))
print('Figures written:'); print(' ', FIG/'fig02_class_distribution.png'); print(' ', FIG/'fig03_sparsity.png')
print('Source data written to reports/results/')
