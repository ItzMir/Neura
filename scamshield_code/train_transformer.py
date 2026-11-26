"""Stage 2 (Kaggle GPU T4/P100): multi-task fine-tune of a multilingual encoder on synthetic + augmented sample data.
Heads: label(6) / techniques(6, sigmoid) / action(6).  Seeds fixed.  Outputs probs for test -> npz (blend with TF-IDF).
NOT executed in the authoring sandbox (no torch/GPU there): run a 2k-row smoke test first (N_SYN=2000, EPOCHS=1)."""
import os, random, numpy as np, pandas as pd, torch, torch.nn as nn
from transformers import AutoTokenizer, AutoModel, get_linear_schedule_with_warmup
from scamlib import *
SEED=42; random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)
MODEL=os.environ.get('MODEL','xlm-roberta-base')   # alt: intfloat/multilingual-e5-base, csebuetnlp/banglabert (check license/declare)
N_SYN=int(os.environ.get('N_SYN',60000)); EPOCHS=int(os.environ.get('EPOCHS',3)); MAXLEN=160; BS=32
U='/kaggle/input/neurahack-2026-preliminary-round/'   # adjust to your competition slug
smp=pd.read_csv(U+'sample.csv'); test=pd.read_csv(U+'test.csv'); rnd=random.Random(SEED)
syn=make_dataset(N_SYN,42)
aug=pd.concat([smp]+[smp.assign(text=[corrupt(t,rnd) for t in smp.text]) for _ in range(30)],ignore_index=True)
df=pd.concat([syn,aug],ignore_index=True).sample(frac=1,random_state=SEED).reset_index(drop=True)
def tm(s):
    M=np.zeros((len(s),6),dtype=np.float32)
    for i,t in enumerate(s):
        for c in str(t).split('|'):
            if c!='NONE': M[i,int(c[1:])-1]=1
    return M
tok=AutoTokenizer.from_pretrained(MODEL)
class Net(nn.Module):
    def __init__(s):
        super().__init__(); s.enc=AutoModel.from_pretrained(MODEL); h=s.enc.config.hidden_size; s.d=nn.Dropout(.1)
        s.a=nn.Linear(h,6); s.b=nn.Linear(h,6); s.c=nn.Linear(h,6)
    def forward(s,**k):
        o=s.enc(**k).last_hidden_state; m=k['attention_mask'].unsqueeze(-1).float(); x=s.d((o*m).sum(1)/m.sum(1))
        return s.a(x),s.b(x),s.c(x)
dev='cuda'; net=Net().to(dev)
Xtxt=[normalize(t) if rnd.random()<.5 else str(t) for t in df.text]   # see both raw and normalized forms
ya=torch.tensor(df.label.values); yb=torch.tensor(tm(df.techniques)); yc=torch.tensor(df.action.values)
opt=torch.optim.AdamW(net.parameters(),lr=3e-5,weight_decay=.01); steps=EPOCHS*(len(df)//BS)
sch=get_linear_schedule_with_warmup(opt,int(.06*steps),steps); scaler=torch.cuda.amp.GradScaler()
net.train()
for ep in range(EPOCHS):
    perm=np.random.permutation(len(df))
    for i in range(0,len(perm)-BS+1,BS):
        ix=perm[i:i+BS]; b=tok([Xtxt[j] for j in ix],truncation=True,max_length=MAXLEN,padding=True,return_tensors='pt').to(dev)
        with torch.autocast('cuda',dtype=torch.float16):
            la,lb,lc=net(**b)
            loss=nn.functional.cross_entropy(la,ya[ix].to(dev),label_smoothing=.05)+.5*nn.functional.binary_cross_entropy_with_logits(lb.float(),yb[ix].to(dev))+.5*nn.functional.cross_entropy(lc,yc[ix].to(dev))
        opt.zero_grad(); scaler.scale(loss).backward(); scaler.unscale_(opt); nn.utils.clip_grad_norm_(net.parameters(),1.); scaler.step(opt); scaler.update(); sch.step()
        if (i//BS)%200==0: print(ep,i//BS,float(loss),flush=True)
net.eval(); torch.save(net.state_dict(),'net.pt')
def infer(texts):
    order=np.argsort([len(t) for t in texts]); PA=np.zeros((len(texts),6),np.float32); PB=PA.copy(); PC=PA.copy()
    with torch.no_grad(), torch.autocast('cuda',dtype=torch.float16):
        for i in range(0,len(texts),512):
            ix=order[i:i+512]; b=tok([normalize(texts[j]) for j in ix],truncation=True,max_length=MAXLEN,padding=True,return_tensors='pt').to(dev)
            a,bb,c=net(**b); PA[ix]=a.float().softmax(-1).cpu().numpy(); PB[ix]=bb.float().sigmoid().cpu().numpy(); PC[ix]=c.float().softmax(-1).cpu().numpy()
    return PA,PB,PC
sa,sb,sc=infer(list(smp.text)); from sklearn.metrics import f1_score
print('sample (in training, sanity only) A F1',f1_score(smp.label,sa.argmax(1),average='macro'))
ta,tb,tc=infer(list(test.text)); np.savez_compressed('transformer_test_probs.npz',a=ta,b=tb,c=tc,ids=test.id.values)
