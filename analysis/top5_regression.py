import json,re,csv,collections,os,numpy as np,pandas as pd,statsmodels.api as sm
R='/home/user/beautiful-danish-data'
ps=json.load(open(f'{R}/data/papers.json')); cat=json.load(open('author_cat.json')); res=json.load(open('res.json'))
ra=collections.Counter(r['paper'] for r in csv.DictReader(open(f'{R}/analysis/ra_analysis.csv')))
n=json.load(open(f'{R}/data/network.json'))
US=re.compile(r'Harvard|Chicago|Berkeley|Northwestern|New York Univ|Columbia|Yale|Princeton|Stanford|Massachusetts|Pennsylvania|California|Wisconsin|Cornell|Purdue|Maryland|Colorado|Georgia State|Federal Reserve|Texas|Notre Dame|Clemson|Grinnell|Michigan|Duke|Boston|Brown|Dartmouth|Minnesota|Arizona|Virginia|Rochester|Illinois|Carnegie|Johns Hopkins|Rice|Vanderbilt|Washington|Ohio|Indiana|Iowa|Oregon|Utah|Florida|Syracuse|Georgetown|Amazon')
usnet=collections.defaultdict(bool)
for x in n['nodes']:
    if x['group']=='Institutions abroad' and any(US.search(i) for i in x['primary']):
        for p in x['papers']: usnet[p]=True
rows=[]
for p in ps:
    r=res.get(p['id']); us=None
    if r:
        for w in ([r['pub']] if r['pub'] else [])+[r['any']]:
            cc=[set(a.get('countries') or []) for a in w['authorships']]
            if cc and all(cc): us=any('US' in c for c in cc); break
    if us is None: us=usnet[p['id']]
    rows.append(dict(id=p['id'],top5=int(p['group']=='top5'),mixed=int(cat[p['id']]=='Mixed'),abroad_only=int(cat[p['id']]=='Abroad only'),
        us_author=int(us),n_authors=len(re.split(r',? and |, ',p['authors'])),year=p['year']-2015,
        firm=int(p['level'] in('firm','both')),has_ra=int(ra[p['id']]>0),has_pdf=int(os.path.exists(f"{R}/pdfs/{p['id']}.pdf")),
        **{'th_'+t:int(t in p['themes']) for t in ['taxation','household-finance','labor','health','family','firms','children']}))
d=pd.DataFrame(rows); d.to_csv(f'{R}/analysis/top5_regression_data.csv',index=False)
print(d.drop(columns='id').groupby('top5').mean().T.round(2)); print(collections.Counter(t for p in ps for t in p['themes']))
def fit(cols,dd,name):
    X=sm.add_constant(dd[cols].astype(float)); m=sm.Logit(dd.top5,X).fit(disp=0)
    ame=m.get_margeff().summary_frame()
    print(f'\n== {name}: N={len(dd)}, pseudo R2={m.prsquared:.3f}')
    print(pd.DataFrame({'AME':ame['dy/dx'].round(3),'se':ame['Std. Err.'].round(3),'p':ame['Pr(>|z|)'].round(3),'odds ratio':np.exp(m.params[1:]).round(2)}))
    return m
b=['mixed','abroad_only','n_authors','year','firm']
fit(b,d,'M1 author mix')
fit(['us_author']+b,d,'M2 + US-based author')
s=d[d.has_pdf==1]
fit(['has_ra','us_author']+b,s,'M3 + thanks RAs (papers with PDF)')
th=[c for c in d if c.startswith('th_')]
m=fit(['has_ra','us_author']+b+th,s,'M4 + themes')
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_predict,StratifiedKFold
from sklearn.metrics import roc_auc_score,accuracy_score
from sklearn.pipeline import make_pipeline; from sklearn.preprocessing import StandardScaler
for name,cols,dd in [('M2',['us_author']+b,d),('M3',['has_ra','us_author']+b,s),('M4',['has_ra','us_author']+b+th,s)]:
    aucs=[];accs=[]
    for seed in range(20):
        pr=cross_val_predict(make_pipeline(StandardScaler(),LogisticRegression(C=1e6,max_iter=2000)),dd[cols],dd.top5,cv=StratifiedKFold(5,shuffle=True,random_state=seed),method='predict_proba')[:,1]
        aucs.append(roc_auc_score(dd.top5,pr));accs.append(accuracy_score(dd.top5,pr>.5))
    print(name,'CV AUC %.3f  accuracy %.3f  (baseline always non-top5 %.3f)'%(np.mean(aucs),np.mean(accs),1-dd.top5.mean()))
