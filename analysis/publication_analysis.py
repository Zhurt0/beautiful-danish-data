import json,numpy as np,pandas as pd,statsmodels.api as sm,warnings; warnings.filterwarnings('ignore')
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_predict,StratifiedKFold
from sklearn.metrics import roc_auc_score,accuracy_score
from sklearn.pipeline import make_pipeline; from sklearn.preprocessing import StandardScaler
R='/home/user/beautiful-danish-data'
d=pd.read_csv(f'{R}/analysis/top5_regression_data.csv').set_index('id')
d=d[[c for c in d if c not in('log_cites','cites_miss','sen_max','sen_min','sen_miss')]]
n=json.load(open(f'{R}/data/network.json')); st=json.load(open('career_start.json')); ci=json.load(open('cites.json'))
ps={p['id']:p for p in json.load(open(f'{R}/data/papers.json'))}
by={}
for x in n['nodes']:
    for p in x['papers']: by.setdefault(p,[]).append(st.get(x['name']))
for i in d.index:
    s=[max(0,ps[i]['year']-y) for y in by.get(i,[]) if y]
    d.loc[i,'sen_max']=max(s) if s else np.nan; d.loc[i,'sen_min']=min(s) if s else np.nan
    c=ci.get(i); d.loc[i,'cites']=c['mx'] if c else np.nan
d['cites_miss']=d.cites.isna().astype(int); d['log_cites']=np.log1p(d.cites.fillna(d.cites.median()))
for c in['sen_max','sen_min']: d[c]=d[c].fillna(d[c].median())
d.drop(columns='cites').reset_index().to_csv(f'{R}/analysis/top5_regression_data.csv',index=False)
print(d.groupby('top5')[['sen_max','sen_min','log_cites','cites']].agg(['mean','median']).round(2).T, d.cites_miss.sum())
A=['mixed','abroad_only','n_authors','year','firm']
B=['us_author','top_inst','ku','aarhus']
C=['log_n','log_n_miss','span','n_data','dk_title','survey','repl_pkg']
D=['sen_max','sen_min']; E=['log_cites','cites_miss']; F=['has_ra']; TH=[c for c in d if c.startswith('th_')]
s=d[d.has_pdf==1]
specs=[('(1)','Author mix',A,d),('(2)','+ Institutions',A+B,d),('(3)','+ Paper traits',A+B+C,d),('(4)','+ Seniority',A+B+C+D,d),
       ('(5)','+ Citations',A+B+C+D+E,d),('(6)','+ RA, themes',A+B+C+D+E+F+TH,s)]
out=dict(n_papers=len(d),n_top5=int(d.top5.sum()),models=[])
for num,label,cols,dd in specs:
    m=sm.Logit(dd.top5,sm.add_constant(dd[cols].astype(float))).fit(disp=0,maxiter=500)
    a=m.get_margeff().summary_frame()
    aucs=[];accs=[]
    for seed in range(20):
        pr=cross_val_predict(make_pipeline(StandardScaler(),LogisticRegression(C=1e6,max_iter=5000)),dd[cols],dd.top5,cv=StratifiedKFold(5,shuffle=True,random_state=seed),method='predict_proba')[:,1]
        aucs.append(roc_auc_score(dd.top5,pr));accs.append(accuracy_score(dd.top5,pr>.5))
    out['models'].append(dict(num=num,label=label,n=len(dd),top5=int(dd.top5.sum()),r2=round(m.prsquared,3),auc=round(float(np.mean(aucs)),3),acc=round(float(np.mean(accs)),3),base=round(1-dd.top5.mean(),3),
        coef={c:dict(b=round(float(a.loc[c,'dy/dx']),3),se=round(float(a.loc[c,'Std. Err.']),3),p=round(float(a.loc[c,'Pr(>|z|)']),4)) for c in cols}))
    print(num,len(dd),round(m.prsquared,3),round(np.mean(aucs),3),round(np.mean(accs),3))
means={c:[round(float(d[d.top5==0][c].mean()),2),round(float(d[d.top5==1][c].mean()),2)] for c in A+B+C+D+E+TH}
means['has_ra']=[round(float(s[s.top5==0].has_ra.mean()),2),round(float(s[s.top5==1].has_ra.mean()),2)]
out['means']=means; out['median_cites']=[float(d[d.top5==0].cites.median()),float(d[d.top5==1].cites.median())]
json.dump(out,open(f'{R}/data/publication.json','w'),indent=1)
pd.set_option('display.width',200)
print(pd.DataFrame({m['num']:{c:f"{v['b']:+.3f} ({v['p']:.2f})" for c,v in m['coef'].items()} for m in out['models']}).fillna('').to_string())
