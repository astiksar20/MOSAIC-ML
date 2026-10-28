import pandas as pd, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from pathlib import Path
RES=Path('reports/results'); FIG=Path('reports/figures'); FIG.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.size':9,'figure.dpi':200})
df=pd.read_csv(RES/'model_comparison_validation.csv').set_index('model')
mets=[('balanced_accuracy','Balanced accuracy'),('malware_recall','Malware recall'),
      ('malware_f1','Malware F1'),('false_positive_rate','False positive rate (lower better)')]
fig,axes=plt.subplots(2,2,figsize=(11.5,6.5))
order=df['balanced_accuracy'].sort_values().index
for ax,(m,t) in zip(axes.ravel(),mets):
    v=df.loc[order,m]
    cols=['#C44E52' if 'CONTROL' in str(i) else '#4C72B0' for i in order]
    ax.barh(range(len(v)),v.values,color=cols)
    ax.set_yticks(range(len(v))); ax.set_yticklabels(order,fontsize=8)
    ax.set_title(t,fontsize=10); ax.grid(axis='x',alpha=.3)
    for i,val in enumerate(v.values): ax.text(val,i,f' {val:.3f}',va='center',fontsize=7)
    ax.set_xlim(0,max(v.values)*1.18)
fig.suptitle('Figure 4 - Model comparison, VALIDATION split (deduplicated, n=58,576 unique rows)\n'
             'Red = active-count shortcut control',fontsize=11)
fig.tight_layout(); fig.savefig(FIG/'fig04_model_comparison.png',bbox_inches='tight'); plt.close(fig)
# Fig 5 confusion matrices
valid=[i for i in df.index if not pd.isna(df.loc[i,'accuracy'])]
nc=4; nr=int(np.ceil(len(valid)/nc))
fig,axes=plt.subplots(nr,nc,figsize=(3.3*nc,2.9*nr))
for ax,n in zip(np.ravel(axes),valid):
    r=df.loc[n]; cm=np.array([[r['TN'],r['FP']],[r['FN'],r['TP']]],dtype=int)
    ax.imshow(cm,cmap='Blues')
    for (i,j),val in np.ndenumerate(cm):
        ax.text(j,i,f'{val:,}',ha='center',va='center',fontsize=8,
                color='white' if val>cm.max()/2 else 'black')
    ax.set_xticks([0,1]); ax.set_xticklabels(['pred ben','pred mal'],fontsize=7)
    ax.set_yticks([0,1]); ax.set_yticklabels(['true ben','true mal'],fontsize=7)
    ax.set_title(n,fontsize=8)
for ax in np.ravel(axes)[len(valid):]: ax.axis('off')
fig.suptitle('Figure 5 - Confusion matrices (validation split, raw counts)',fontsize=11)
fig.tight_layout(); fig.savefig(FIG/'fig05_confusion_matrices.png',bbox_inches='tight'); plt.close(fig)
print('wrote fig04, fig05')
