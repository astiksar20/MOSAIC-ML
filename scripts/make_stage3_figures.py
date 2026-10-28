"""Figures 9 and 10 from real fitted weights and real scores."""
import json, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.metrics import roc_curve, precision_recall_curve, roc_auc_score, average_precision_score
FIG=Path('reports/figures'); RES=Path('reports/results')
plt.rcParams.update({'font.size':9,'figure.dpi':200})
d=json.load(open('risk/permission_weights.json'))
W=sorted(d['weights'], key=lambda w:-w['r'])
names=[w['permission'] for w in W]; alpha=[w['alpha'] for w in W]
beta=[w['beta'] for w in W]; r=[w['r'] for w in W]
yp=np.arange(len(names))

fig,(a1,a2)=plt.subplots(1,2,figsize=(12,5.4))
h=0.38
a1.barh(yp-h/2, alpha, h, label=r'$\alpha_i$  (malicious)', color='#C44E52')
a1.barh(yp+h/2, beta,  h, label=r'$\beta_i$  (benign)',    color='#4C72B0')
a1.set_yticks(yp); a1.set_yticklabels(names,fontsize=8); a1.invert_yaxis()
a1.set_xlabel('Within-class prevalence'); a1.legend(fontsize=8); a1.grid(axis='x',alpha=.3)
a1.set_title('Permission prevalence by class (TRAIN split only)',fontsize=10)
a2.barh(yp, r, color='#55A868')
a2.set_yticks(yp); a2.set_yticklabels(names,fontsize=8); a2.invert_yaxis()
a2.set_xlabel(r'$r_i=\sqrt{\alpha_i(1-\beta_i)}$'); a2.grid(axis='x',alpha=.3); a2.set_xlim(0,1)
a2.set_title('Derived permission risk weight',fontsize=10)
for i,v in enumerate(r): a2.text(v,i,f' {v:.3f}',va='center',fontsize=7)
fig.suptitle('Figure 9 - Dangerous-permission prevalence and derived weights\n'
             'Weights fitted on the training split only (n=41,003). Adapted from Ogwara et al. 2024.',fontsize=11)
fig.tight_layout(); fig.savefig(FIG/'fig09_permission_weights.png',bbox_inches='tight'); plt.close(fig)

sv=np.load(RES/'perm_scores_val.npy'); yv=np.load(RES/'perm_labels_val.npy')
st=np.load(RES/'perm_scores_test.npy'); yt=np.load(RES/'perm_labels_test.npy')
dv=~np.isnan(sv); dt=~np.isnan(st)
fig,ax=plt.subplots(1,3,figsize=(14,4.2))
ax[0].hist(sv[dv&(yv==0)],bins=45,alpha=.62,color='#4C72B0',density=True,label=f'Benign (n={int((dv&(yv==0)).sum()):,})')
ax[0].hist(sv[dv&(yv==1)],bins=45,alpha=.62,color='#C44E52',density=True,label=f'Malware (n={int((dv&(yv==1)).sum()):,})')
ax[0].axvline(np.nanmean(sv[dv&(yv==0)]),color='#4C72B0',ls='--',lw=1.2)
ax[0].axvline(np.nanmean(sv[dv&(yv==1)]),color='#C44E52',ls='--',lw=1.2)
ax[0].set_xlabel(r'$R_{perm}(a)$'); ax[0].set_ylabel('Density'); ax[0].legend(fontsize=8)
ax[0].set_title('Score distribution, validation\nHeavy overlap: means differ by only 0.045',fontsize=9)
fpr,tpr,_=roc_curve(yv[dv],sv[dv]); ax[1].plot(fpr,tpr,color='#55A868',lw=1.6,
    label=f'validation (AUC {roc_auc_score(yv[dv],sv[dv]):.3f})')
fpr,tpr,_=roc_curve(yt[dt],st[dt]); ax[1].plot(fpr,tpr,color='#8172B2',lw=1.6,ls='--',
    label=f'test (AUC {roc_auc_score(yt[dt],st[dt]):.3f})')
ax[1].plot([0,1],[0,1],'k:',lw=1,label='no skill'); ax[1].legend(fontsize=8); ax[1].grid(alpha=.3)
ax[1].set_xlabel('False positive rate'); ax[1].set_ylabel('True positive rate'); ax[1].set_title('ROC',fontsize=9)
pr,rc,_=precision_recall_curve(yv[dv],sv[dv]); ax[2].plot(rc,pr,color='#55A868',lw=1.6,
    label=f'validation (AP {average_precision_score(yv[dv],sv[dv]):.3f})')
pr,rc,_=precision_recall_curve(yt[dt],st[dt]); ax[2].plot(rc,pr,color='#8172B2',lw=1.6,ls='--',
    label=f'test (AP {average_precision_score(yt[dt],st[dt]):.3f})')
ax[2].axhline(yv[dv].mean(),color='k',ls=':',lw=1,label=f'no skill ({yv[dv].mean():.3f})')
ax[2].legend(fontsize=8); ax[2].grid(alpha=.3)
ax[2].set_xlabel('Recall'); ax[2].set_ylabel('Precision'); ax[2].set_title('Precision-Recall',fontsize=9)
fig.suptitle('Figure 10 - Permission-risk score: class distributions and discrimination\n'
             'A weak standalone discriminator. Not a probability of malware.',fontsize=11)
fig.tight_layout(); fig.savefig(FIG/'fig10_permission_score_eval.png',bbox_inches='tight'); plt.close(fig)
print('wrote fig09, fig10')
