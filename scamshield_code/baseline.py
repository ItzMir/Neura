import pandas as pd, numpy as np, time, sys
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.metrics import f1_score
from scamlib import *
U='/mnt/user-data/uploads/'
N=int(sys.argv[1]) if len(sys.argv)>1 else 30000
tr=make_dataset(N,42); s=pd.read_csv(U+'sample.csv')
print(tr.label.value_counts().sort_index().to_dict()); print(tr.sample(6,random_state=1).to_string()[:1500])
def prep(x): return [normalize(t) for t in x]
Xt=prep(tr.text); Xs=prep(s.text)
v1=TfidfVectorizer(analyzer='char_wb',ngram_range=(2,5),sublinear_tf=True,min_df=3,max_features=300000)
v2=TfidfVectorizer(analyzer='word',ngram_range=(1,2),sublinear_tf=True,min_df=2,token_pattern=r'\S+')
v3=TfidfVectorizer(analyzer='char',ngram_range=(3,5),sublinear_tf=True,min_df=3,max_features=200000)
sq=lambda X:[squash(t) for t in X]
t0=time.time()
M=hstack([v1.fit_transform(Xt),v2.fit_transform(Xt),v3.fit_transform(sq(Xt))]).tocsr()
H=lambda X:hstack([v1.transform(X),v2.transform(X),v3.transform(sq(X))]).tocsr()
clf=LogisticRegression(C=20,max_iter=300,n_jobs=1).fit(M,tr.label)
Ys=[ [int(c[1:]) for c in str(t).split('|') if c!='NONE'] for t in tr.techniques]
Tm=np.zeros((len(tr),6));
for i,l in enumerate(Ys):
    for k in l: Tm[i,k-1]=1
tcl=OneVsRestClassifier(LogisticRegression(C=20,max_iter=200)).fit(M,Tm)
acl=LogisticRegression(C=20,max_iter=300).fit(M,tr.action)
print('fit',time.time()-t0)
S=H(Xs); p=clf.predict_proba(S); pl=p.argmax(1)
print('A macroF1',f1_score(s.label,pl,average='macro'),'acc',(pl==s.label).mean())
print('C macroF1',f1_score(s.action,acl.predict(S),average='macro'))
ts=np.zeros((len(s),6))
for i,t in enumerate(s.techniques):
    for c in str(t).split('|'):
        if c!='NONE': ts[i,int(c[1:])-1]=1
print('B macroF1',f1_score(ts,(tcl.predict_proba(S)>.5).astype(int),average='macro',zero_division=0))
from sklearn.metrics import confusion_matrix; print(confusion_matrix(s.label,pl))
for i in np.where(pl!=s.label)[0]: print(s.label[i],pl[i],s.text[i][:110])
