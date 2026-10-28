"""Fit permission-risk weights on the TRAINING SPLIT ONLY, then evaluate."""
import sys, json, hashlib
sys.path.insert(0,'.')
import numpy as np, scipy.sparse as sp
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, average_precision_score
from risk.permission_risk import (fit_permission_weights, score_matrix, save_weights,
                                  PERMISSION_SET_OGWARA15)

SEED=42; RES=Path('reports/results'); RES.mkdir(parents=True,exist_ok=True)
z=np.load('data/mh100k/mh100.npz',allow_pickle=True)
vocab=[str(v) for v in z['column_names']]; y_all=np.asarray(z['classes']).astype(int)
X_all=sp.load_npz('data/processed/mh100_csr.npz').tocsr()

# Same dedup + split as Stage 2 so results are comparable.
seen={}; keep=[]
for i in range(X_all.shape[0]):
    lo,hi=X_all.indptr[i],X_all.indptr[i+1]
    d=hashlib.blake2b(X_all.indices[lo:hi].astype(np.int32).tobytes(),digest_size=16).digest()
    if d not in seen: seen[d]=i; keep.append(i)
keep=np.array(keep); X,y=X_all[keep],y_all[keep]
idx=np.arange(X.shape[0])
itr,itmp=train_test_split(idx,test_size=.30,random_state=SEED,stratify=y)
iva,ite=train_test_split(itmp,test_size=.50,random_state=SEED,stratify=y[itmp])
X_tr,y_tr=X[itr],y[itr]; X_va,y_va=X[iva],y[iva]; X_te,y_te=X[ite],y[ite]
print(f'train {len(y_tr):,} | val {len(y_va):,} | test {len(y_te):,}')
print(f'train malicious {int(y_tr.sum()):,} benign {int((y_tr==0).sum()):,}\n')

W = fit_permission_weights(X_tr, y_tr, vocab, PERMISSION_SET_OGWARA15)
print(f'{"permission":<28}{"alpha":>8}{"beta":>8}{"r":>8}')
print('-'*52)
for w in sorted(W, key=lambda w:-w.r):
    print(f'{w.permission:<28}{w.alpha:8.4f}{w.beta:8.4f}{w.r:8.4f}')

meta={'dataset':'MH-100K','label_rule':'vt_detection >= 4','split_seed':SEED,
      'split_scheme':'70/15/15 stratified, deduplicated','n_train':int(len(y_tr)),
      'n_train_malicious':int(y_tr.sum()),'n_train_benign':int((y_tr==0).sum()),
      'permission_set':'Ogwara et al. 2024 Table 1, P1-P15','n_features':int(X.shape[1])}
save_weights('risk/permission_weights.json', W, meta)
print('\nsaved risk/permission_weights.json')

out={}
for nm,Xs,ys in [('train',X_tr,y_tr),('validation',X_va,y_va),('test',X_te,y_te)]:
    s,k = score_matrix(Xs, vocab, W)
    defined = ~np.isnan(s)
    row={'n':int(len(ys)),'n_defined':int(defined.sum()),
         'n_insufficient_evidence':int((~defined).sum()),
         'pct_insufficient':round(100*(~defined).mean(),3),
         'mean_k':round(float(k.mean()),3)}
    if defined.sum()>0 and len(np.unique(ys[defined]))>1:
        row['roc_auc']=round(float(roc_auc_score(ys[defined],s[defined])),4)
        row['pr_auc']=round(float(average_precision_score(ys[defined],s[defined])),4)
        row['mean_score_benign']=round(float(np.nanmean(s[defined&(ys==0)])),4)
        row['mean_score_malware']=round(float(np.nanmean(s[defined&(ys==1)])),4)
        row['median_score_benign']=round(float(np.nanmedian(s[defined&(ys==0)])),4)
        row['median_score_malware']=round(float(np.nanmedian(s[defined&(ys==1)])),4)
    # insufficient-evidence breakdown by class
    row['insufficient_benign']=int(((~defined)&(ys==0)).sum())
    row['insufficient_malware']=int(((~defined)&(ys==1)).sum())
    out[nm]=row
    print(f'\n--- {nm} ---')
    for kk,vv in row.items(): print(f'  {kk:26s}: {vv}')
    if nm=='validation': np.save(RES/'perm_scores_val.npy',s); np.save(RES/'perm_labels_val.npy',ys)
    if nm=='test': np.save(RES/'perm_scores_test.npy',s); np.save(RES/'perm_labels_test.npy',ys)

json.dump({'metadata':meta,'weights':[w.__dict__ for w in W],'evaluation':out},
          open(RES/'permission_risk_evaluation.json','w'), indent=2)
print('\nsaved reports/results/permission_risk_evaluation.json')
