import json,re,csv,collections,os,numpy as np,pandas as pd,statsmodels.api as sm
R='/home/user/beautiful-danish-data'
ps=json.load(open(f'{R}/data/papers.json')); res=json.load(open('res.json')); dl=json.load(open('dl.json'))
n=json.load(open(f'{R}/data/network.json')); sv=json.load(open(f'{R}/data/surveys.json'))
d=pd.read_csv(f'{R}/analysis/top5_regression_data.csv').set_index('id')
ra=collections.Counter(r['paper'] for r in csv.DictReader(open(f'{R}/analysis/ra_analysis.csv')))
inst=collections.defaultdict(set)
for x in n['nodes']:
    for p in x['papers']: inst[p]|=set(x['institutions'])
TOP=re.compile(r'Harvard|University of Chicago|Berkeley|Princeton|Massachusetts Institute|Stanford|London School of Economics|Yale|Northwestern|Columbia|New York University|University College London')
surv={pid for s in sv for pid in s.get('papers',[])}
def size(s):
    if not s: return np.nan
    best=np.nan
    for m in re.finditer(r'([\d][\d,\.]*)\s*(million|billion|thousand)?',s):
        try: v=float(m.group(1).replace(',','').rstrip('.'))
        except: continue
        v*={'million':1e6,'billion':1e9,'thousand':1e3,None:1}[m.group(2)]
        if 1800<=v<=2030 and not m.group(2): continue
        best=np.nanmax([best,v])
    return best
def span(s):
    y=[int(x) for x in re.findall(r'(?:19|20)\d\d',s or '')]
    return max(y)-min(y)+1 if y else np.nan
for p in ps:
    i=p['id']; r=res.get(i) or {}
    blob=json.dumps(r)+json.dumps(dl.get(i))+str(p.get('sample_source'))
    d.loc[i,'nber_wp']=int('nber.org' in blob or '10.3386' in blob)
    d.loc[i,'top_inst']=int(any(TOP.search(x) for x in inst[i]))
    d.loc[i,'ku']=int(any('University of Copenhagen' in x for x in inst[i]))
    d.loc[i,'aarhus']=int(any('Aarhus University' in x for x in inst[i]))
    d.loc[i,'log_n']=np.log10(size(p.get('sample_size')))
    d.loc[i,'span']=span(p.get('period'))
    d.loc[i,'n_data']=len(p.get('data') or [])
    d.loc[i,'dk_title']=int(bool(re.search(r'Denmark|Danish',p['title'])))
    d.loc[i,'survey']=int(i in surv)
    d.loc[i,'repl_pkg']=int(bool(p.get('replication_package')))
    d.loc[i,'n_ra']=ra[i]
print(d[['log_n','span']].isna().sum().to_dict())
for c in ['log_n','span']:
    d[c+'_miss']=d[c].isna().astype(int); d[c]=d[c].fillna(d[c].median())
d.reset_index().to_csv(f'{R}/analysis/top5_regression_data.csv',index=False)
new=['nber_wp','top_inst','ku','aarhus','log_n','span','n_data','dk_title','survey','repl_pkg','n_ra']
print(d.groupby('top5')[new].mean().T.round(2))
def fit(cols,dd,name):
    X=sm.add_constant(dd[cols].astype(float)); m=sm.Logit(dd.top5,X).fit(disp=0,maxiter=200)
    a=m.get_margeff().summary_frame()
    print(f'\n== {name}: N={len(dd)}, pseudo R2={m.prsquared:.3f}')
    print(pd.DataFrame({'AME':a['dy/dx'].round(3),'se':a['Std. Err.'].round(3),'p':a['Pr(>|z|)'].round(3)}).to_string())
base=['mixed','abroad_only','us_author','n_authors','year','firm']
th=[c for c in d if c.startswith('th_')]
full=base+['nber_wp','top_inst','ku','aarhus','log_n','log_n_miss','span','n_data','dk_title','survey','repl_pkg']
fit(full,d,'M5 all papers')
s=d[d.has_pdf==1]
fit(full+['has_ra'],s,'M6 + thanks RA')
fit(full+['has_ra']+th,s,'M7 + themes')
from sklearn.linear_model import LogisticRegression,LogisticRegressionCV
from sklearn.model_selection import cross_val_predict,StratifiedKFold
from sklearn.metrics import roc_auc_score,accuracy_score
from sklearn.pipeline import make_pipeline; from sklearn.preprocessing import StandardScaler
def cv(name,cols,dd,est):
    A=[];B=[]
    for seed in range(20):
        pr=cross_val_predict(make_pipeline(StandardScaler(),est()),dd[cols],dd.top5,cv=StratifiedKFold(5,shuffle=True,random_state=seed),method='predict_proba')[:,1]
        A.append(roc_auc_score(dd.top5,pr));B.append(accuracy_score(dd.top5,pr>.5))
    print(f'{name}: CV AUC {np.mean(A):.3f} acc {np.mean(B):.3f} (baseline {1-dd.top5.mean():.3f})')
plain=lambda:LogisticRegression(C=1e6,max_iter=5000)
lasso=lambda:LogisticRegression(penalty='l1',C=0.15,solver='liblinear')
cv('old M2',['us_author','mixed','abroad_only','n_authors','year','firm'],d,plain)
cv('M5',full,d,plain); cv('M6',full+['has_ra'],s,plain); cv('M7',full+['has_ra']+th,s,plain); cv('M7 lasso',full+['has_ra']+th,s,lasso)
cv('small: nber+has_ra+abroad_only',['nber_wp','has_ra','abroad_only'],s,plain)
k=['top_inst','log_n','log_n_miss','abroad_only','repl_pkg']
fit(k,d,'M8 compact'); cv('M8 compact',k,d,plain); cv('M8 + has_ra',k+['has_ra'],s,plain)
