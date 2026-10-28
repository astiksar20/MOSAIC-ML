"""Unit tests for the permission-risk mechanism."""
import sys, math, json, tempfile, os
sys.path.insert(0,'.')
import numpy as np, scipy.sparse as sp
from risk.permission_risk import (fit_permission_weights, compute_permission_score,
    canonical_permission, save_weights, load_weights, score_matrix,
    PermissionWeight, INSUFFICIENT, OK)

P=0; F=0
def check(name, cond, detail=''):
    global P,F
    if cond: P+=1; print(f'  PASS  {name}')
    else: F+=1; print(f'  FAIL  {name}  {detail}')

print('1. canonical_permission')
check('android.permission prefix', canonical_permission('android.permission.SEND_SMS')=='SEND_SMS')
check('Permission:: prefix', canonical_permission('Permission::SEND_SMS')=='SEND_SMS')
check('bare name', canonical_permission('SEND_SMS')=='SEND_SMS')
check('lowercase upcased', canonical_permission('send_sms')=='SEND_SMS')

print('\n2. formula correctness on a hand-built dataset')
# 4 apps x 3 perms. y = [1,1,0,0]
vocab=['Permission::A','Permission::B','Permission::C']
X=sp.csr_matrix(np.array([[1,1,0],[1,0,0],[0,1,0],[0,0,1]],dtype=np.int8))
y=np.array([1,1,0,0])
W=fit_permission_weights(X,y,vocab,['A','B','C'])
w={x.permission:x for x in W}
# A: malicious 2/2=1.0 ; benign 0/2=0.0 -> r=sqrt(1*1)=1.0
check('alpha_A', abs(w['A'].alpha-1.0)<1e-9, f"got {w['A'].alpha}")
check('beta_A',  abs(w['A'].beta-0.0)<1e-9,  f"got {w['A'].beta}")
check('r_A=1.0', abs(w['A'].r-1.0)<1e-9,     f"got {w['A'].r}")
# B: malicious 1/2=0.5 ; benign 1/2=0.5 -> r=sqrt(0.5*0.5)=0.5
check('r_B=0.5', abs(w['B'].r-0.5)<1e-9, f"got {w['B'].r}")
# C: malicious 0/2=0 ; benign 1/2=0.5 -> r=sqrt(0*0.5)=0
check('r_C=0.0', abs(w['C'].r-0.0)<1e-9, f"got {w['C'].r}")
check('r in [0,1] for all', all(0.0<=x.r<=1.0 for x in W))

print('\n3. R_perm(a) averaging')
r=compute_permission_score(['A'],W)
check('single perm -> r_A', abs(r['score']-1.0)<1e-9 and r['k']==1)
r=compute_permission_score(['A','B'],W)
check('two perms -> mean', abs(r['score']-0.75)<1e-9, f"got {r['score']}")
r=compute_permission_score(['A','B','C'],W)
check('three perms -> mean', abs(r['score']-0.5)<1e-9, f"got {r['score']}")
check('score in [0,1]', 0.0<=r['score']<=1.0)
check('0-100 is rescale', abs(r['score_0_100']-50.0)<1e-6, f"got {r['score_0_100']}")

print('\n4. k(a)=0 -> insufficient evidence, NOT zero')
r=compute_permission_score([],W)
check('score is None', r['score'] is None, f"got {r['score']}")
check('score is NOT 0.0', r['score']!=0.0)
check('status flag', r['status']==INSUFFICIENT)
check('k==0', r['k']==0)
r2=compute_permission_score(['UNRELATED_PERM','android.permission.INTERNET'],W)
check('unselected perms only -> None', r2['score'] is None)
check('status flag (unselected)', r2['status']==INSUFFICIENT)

print('\n5. absent / unknown permissions ignored')
r=compute_permission_score(['A','TOTALLY_MADE_UP'],W)
check('unknown ignored, k=1', r['k']==1 and abs(r['score']-1.0)<1e-9)
check('denominator counts only matched', r['matched_permissions']==['A'])

print('\n6. no leakage - weights depend only on data passed in')
Xa=sp.csr_matrix(np.array([[1,0,0],[0,1,0]],dtype=np.int8)); ya=np.array([1,0])
Wa=fit_permission_weights(Xa,ya,vocab,['A','B','C'])
Wb=fit_permission_weights(X,y,vocab,['A','B','C'])
check('different splits -> different weights',
      any(abs(p.r-q.r)>1e-9 for p,q in zip(sorted(Wa,key=lambda z:z.permission),
                                            sorted(Wb,key=lambda z:z.permission))))

print('\n7. serialization round-trip')
with tempfile.TemporaryDirectory() as d:
    p=os.path.join(d,'w.json'); save_weights(p,W,{'test':True})
    W2,meta=load_weights(p)
    check('round-trip preserves r', all(abs(a.r-b.r)<1e-12 for a,b in
          zip(sorted(W,key=lambda z:z.permission), sorted(W2,key=lambda z:z.permission))))
    check('metadata preserved', meta.get('test') is True)
    s1=compute_permission_score(['A','B'],W); s2=compute_permission_score(['A','B'],W2)
    check('stable scores after reload', s1['score']==s2['score'])

print('\n8. vectorised scorer agrees with per-APK scorer')
s,k=score_matrix(X,vocab,W)
expect=[compute_permission_score([p for p,v in zip(['A','B','C'],X[i].toarray().ravel()) if v],W)
        for i in range(X.shape[0])]
ok=True
for i,e in enumerate(expect):
    if e['score'] is None: ok &= bool(np.isnan(s[i]))
    else: ok &= abs(s[i]-e['score'])<1e-9
check('vectorised == per-APK', ok)
check('k vector matches', list(k)==[e['k'] for e in expect])

print('\n9. guards')
try:
    fit_permission_weights(X,np.array([1,1,1,1]),vocab,['A']); check('single-class rejected',False)
except ValueError: check('single-class rejected',True)
try:
    fit_permission_weights(X,y,vocab,['NOT_IN_VOCAB']); check('missing perm rejected',False)
except KeyError: check('missing perm rejected',True)
try:
    fit_permission_weights(X,np.array([1,0]),vocab,['A']); check('row mismatch rejected',False)
except ValueError: check('row mismatch rejected',True)

print(f'\n{"="*52}\nPASSED {P}   FAILED {F}')
sys.exit(1 if F else 0)
