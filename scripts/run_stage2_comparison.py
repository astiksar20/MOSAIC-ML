"""Stage 2 model comparison - same logic as the Colab notebook, run locally."""
import numpy as np, scipy.sparse as sp, hashlib, time, json, sys, platform, sklearn
from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import BernoulliNB
from sklearn.metrics import (accuracy_score, balanced_accuracy_score, f1_score,
                             precision_score, recall_score, confusion_matrix,
                             roc_auc_score, average_precision_score)
SEED=42; RES=Path('reports/results'); RES.mkdir(parents=True,exist_ok=True)
z=np.load('data/mh100k/mh100.npz',allow_pickle=True)
y_all=np.asarray(z['classes']).astype(int)
X_all=sp.load_npz('data/processed/mh100_csr.npz').tocsr()

seen={}; keep=[]; conflicts=0
for i in range(X_all.shape[0]):
    lo,hi=X_all.indptr[i],X_all.indptr[i+1]
    d=hashlib.blake2b(X_all.indices[lo:hi].astype(np.int32).tobytes(),digest_size=16).digest()
    if d in seen:
        if y_all[seen[d]]!=y_all[i]: conflicts+=1
    else: seen[d]=i; keep.append(i)
keep=np.array(keep)
print(f'unique rows {len(keep):,} of {X_all.shape[0]:,}  (conflicting-label dup pairs: {conflicts})')
X,y=X_all[keep],y_all[keep]
print(f'after dedup: benign {int((y==0).sum()):,}  malware {int((y==1).sum()):,}  ({100*(y==1).mean():.2f}% malware)')

idx=np.arange(X.shape[0])
itr,itmp=train_test_split(idx,test_size=.30,random_state=SEED,stratify=y)
iva,ite=train_test_split(itmp,test_size=.50,random_state=SEED,stratify=y[itmp])
X_tr,y_tr=X[itr],y[itr]; X_va,y_va=X[iva],y[iva]; X_te,y_te=X[ite],y[ite]
print(f'train {len(y_tr):,}  val {len(y_va):,}  test {len(y_te):,}')

MODELS={
 'Random Forest (100)': RandomForestClassifier(n_estimators=100,max_features='sqrt',random_state=SEED,n_jobs=-1),
 'Random Forest (30)':  RandomForestClassifier(n_estimators=30,max_features='sqrt',random_state=SEED,n_jobs=-1),
 'Logistic Regression': LogisticRegression(max_iter=2000,random_state=SEED),
 'Decision Tree':       DecisionTreeClassifier(random_state=SEED),
 'Linear SVM':          LinearSVC(random_state=SEED,max_iter=3000),
 'Bernoulli NB':        BernoulliNB(),
}
def scores_from(m,Xs):
    if hasattr(m,'predict_proba'): return m.predict_proba(Xs)[:,1]
    if hasattr(m,'decision_function'): return m.decision_function(Xs)
    return None
def ev(name,m,Xa,ya,Xb,yb,note=''):
    t=time.time(); m.fit(Xa,ya); fs=time.time()-t
    t=time.time(); p=m.predict(Xb); isec=time.time()-t
    sc=scores_from(m,Xb); tn,fp,fn,tp=confusion_matrix(yb,p,labels=[0,1]).ravel()
    return {'model':name,'accuracy':accuracy_score(yb,p),'balanced_accuracy':balanced_accuracy_score(yb,p),
      'macro_f1':f1_score(yb,p,average='macro'),'malware_precision':precision_score(yb,p,zero_division=0),
      'malware_recall':recall_score(yb,p,zero_division=0),'malware_f1':f1_score(yb,p,zero_division=0),
      'false_positive_rate':fp/(fp+tn),'false_negative_rate':fn/(fn+tp),
      'TN':int(tn),'FP':int(fp),'FN':int(fn),'TP':int(tp),
      'roc_auc':roc_auc_score(yb,sc) if sc is not None else np.nan,
      'pr_auc':average_precision_score(yb,sc) if sc is not None else np.nan,
      'fit_seconds':round(fs,2),'inference_seconds':round(isec,3),'note':note},m,sc
rows={}; fitted={}; vsc={}
for n,m in MODELS.items():
    print(f'  training {n} ...',flush=True)
    try:
        r,mm,sc=ev(n,m,X_tr,y_tr,X_va,y_va); rows[n]=r; fitted[n]=mm; vsc[n]=sc
        print(f'    acc={r["accuracy"]:.4f} bal={r["balanced_accuracy"]:.4f} malF1={r["malware_f1"]:.4f} ({r["fit_seconds"]}s)')
    except Exception as e:
        print(f'    FAILED {type(e).__name__}: {e}'); rows[n]={'model':n,'note':f'FAILED {type(e).__name__}'}
cnt=lambda M: np.diff(M.indptr).astype(float).reshape(-1,1)
r,mm,sc=ev('CONTROL: active-count only',DecisionTreeClassifier(max_depth=3,random_state=SEED),
           cnt(X_tr),y_tr,cnt(X_va),y_va,'1 feature: count of active features')
rows['CONTROL: active-count only']=r; vsc['CONTROL: active-count only']=sc
print(f'  CONTROL acc={r["accuracy"]:.4f} bal={r["balanced_accuracy"]:.4f} malF1={r["malware_f1"]:.4f}')

df=pd.DataFrame(list(rows.values())).set_index('model')
df.to_csv(RES/'model_comparison_validation.csv')
real=df.drop(index='CONTROL: active-count only').dropna(subset=['balanced_accuracy'])
best=real['balanced_accuracy'].idxmax()
print(f'\nSELECTED on validation balanced accuracy: {best}')
fm=MODELS[best]; t=time.time(); fm.fit(X_tr,y_tr); fs=time.time()-t
p=fm.predict(X_te); sc=scores_from(fm,X_te)
tn,fp,fn,tp=confusion_matrix(y_te,p,labels=[0,1]).ravel()
test={'model':best,'split':'TEST (once)','accuracy':accuracy_score(y_te,p),
 'balanced_accuracy':balanced_accuracy_score(y_te,p),'macro_f1':f1_score(y_te,p,average='macro'),
 'malware_precision':precision_score(y_te,p,zero_division=0),'malware_recall':recall_score(y_te,p,zero_division=0),
 'malware_f1':f1_score(y_te,p,zero_division=0),'false_positive_rate':fp/(fp+tn),'false_negative_rate':fn/(fn+tp),
 'TN':int(tn),'FP':int(fp),'FN':int(fn),'TP':int(tp),
 'roc_auc':roc_auc_score(y_te,sc) if sc is not None else np.nan,
 'pr_auc':average_precision_score(y_te,sc) if sc is not None else np.nan,'fit_seconds':round(fs,2)}
pd.DataFrame([test]).to_csv(RES/'final_test_result.csv',index=False)
json.dump({'split':{'seed':SEED,'scheme':'70/15/15 stratified','deduplicated':True,
   'n_train':len(y_tr),'n_val':len(y_va),'n_test':len(y_te)},
   'label_rule':'vt_detection >= 4','selected_model':best,
   'selection_metric':'balanced_accuracy on validation','test_evaluated_once':True,
   'versions':{'python':sys.version.split()[0],'numpy':np.__version__,'sklearn':sklearn.__version__},
   'validation_results':df.reset_index().to_dict(orient='records'),'test_result':test},
   open(RES/'stage2_run_record.json','w'),indent=2,default=str)
print('\n=== VALIDATION TABLE ===')
cols=['accuracy','balanced_accuracy','macro_f1','malware_recall','malware_f1','false_positive_rate','roc_auc','fit_seconds']
print(df[cols].round(4).sort_values('balanced_accuracy',ascending=False).to_string())
print('\n=== FINAL TEST (evaluated once) ===')
for k,v in test.items(): print(f'  {k:20s}: {v}')
ctrl=df.loc['CONTROL: active-count only']
print('\n=== GAIN OVER SHORTCUT CONTROL ===')
for mname in ['accuracy','balanced_accuracy','malware_f1','malware_recall']:
    print(f'  {mname:18s}: best {real.loc[best,mname]:.4f}  control {ctrl[mname]:.4f}  gain {real.loc[best,mname]-ctrl[mname]:+.4f}')
