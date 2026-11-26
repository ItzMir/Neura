"""Stage 1 (CPU, no torch): synthetic data -> TF-IDF + LR for all tasks -> submission.csv. SEED=42."""
import pandas as pd, numpy as np, time, random, sys, os
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.metrics import f1_score
from scamlib import *
U='/mnt/user-data/uploads/'; OUT=sys.argv[2] if len(sys.argv)>2 else 'out'; os.makedirs(OUT,exist_ok=True)
N=int(sys.argv[1]) if len(sys.argv)>1 else 40000
rnd=random.Random(7)
syn=make_dataset(N,42); smp=pd.read_csv(U+'sample.csv')
# augment sample.csv (allowed): 8 corrupted copies + original
aug=[smp]+[smp.assign(text=[corrupt(t,rnd) for t in smp.text]) for _ in range(8)]
def tm(ser):
    M=np.zeros((len(ser),6))
    for i,t in enumerate(ser):
        for c in str(t).split('|'):
            if c!='NONE': M[i,int(c[1:])-1]=1
    return M
sq=lambda X:[squash(t) for t in X]
class Feat:
    def fit(s,X):
        s.v=[TfidfVectorizer(analyzer='char_wb',ngram_range=(2,5),sublinear_tf=True,min_df=3,max_features=300000),
             TfidfVectorizer(analyzer='word',ngram_range=(1,2),sublinear_tf=True,min_df=2,token_pattern=r'\S+'),
             TfidfVectorizer(analyzer='char',ngram_range=(3,5),sublinear_tf=True,min_df=3,max_features=200000)]
        return hstack([s.v[0].fit_transform(X),s.v[1].fit_transform(X),s.v[2].fit_transform(sq(X))]).tocsr()
    def tr(s,X): return hstack([s.v[0].transform(X),s.v[1].transform(X),s.v[2].transform(sq(X))]).tocsr()
def fit_all(df):
    X=[normalize(t) for t in df.text]; F=Feat(); M=F.fit(X)
    return F,LogisticRegression(C=20,max_iter=300).fit(M,df.label),OneVsRestClassifier(LogisticRegression(C=20,max_iter=200)).fit(M,tm(df.techniques)),LogisticRegression(C=20,max_iter=300).fit(M,df.action)
# ---- stage A: synthetic only -> fit temperature on the real sample (honest, template-disjoint)
F,c,_,_=fit_all(syn); P=c.predict_proba(F.tr([normalize(t) for t in smp.text]))
y=smp.label.values; best=(9,1)
for T in np.arange(.5,6,.25):
    q=P**(1/T); q/=q.sum(1,keepdims=True); br=np.mean((q.max(1)-(q.argmax(1)==y))**2); best=min(best,(br,T))
T=best[1]; print('A macroF1 (synthetic-only, real sample):',f1_score(y,P.argmax(1),average='macro'),'temp',T,'brier',best[0])
# ---- final model: synthetic + augmented sample (sample upweighted by repetition x3)
full=pd.concat([syn]+aug*3,ignore_index=True); F,clf,tcl,acl=fit_all(full)
ALLOW={1:[1,2],2:[1,2,3,4,5],3:[2,4,5,1],4:[2,3,5,1]}; MUST={1:'T2',2:'T4',3:'T6',4:'T1'}
test=pd.read_csv(U+'test.csv'); res=[]; t0=time.time()
for i in range(0,len(test),20000):
    ch=test.iloc[i:i+20000]; X=F.tr([normalize(t) for t in ch.text])
    p=clf.predict_proba(X); lab=p.argmax(1); q=p**(1/T); q/=q.sum(1,keepdims=True); conf=np.clip(q.max(1),.05,.99)
    tp=tcl.predict_proba(X); ap=acl.predict_proba(X)
    for j,l in enumerate(lab):
        if l in (0,5): res.append((ch.id.iloc[j],l,'NONE',0,conf[j])); continue
        ts={f'T{k+1}' for k in range(6) if tp[j,k]>.4}|{MUST[l]}
        a=max(ALLOW[l],key=lambda k:ap[j,k]); res.append((ch.id.iloc[j],l,'|'.join(sorted(ts)),a,conf[j]))
    print(i,time.time()-t0,flush=True)
sub=pd.DataFrame(res,columns=['id','label','techniques','action','confidence']); sub['confidence']=sub.confidence.round(4)
sub.to_csv(f'{OUT}/submission.csv',index=False); print(sub.label.value_counts(normalize=True).sort_index().round(3).to_dict()); print(sub.head())
