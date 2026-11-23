import json,re,collections,unicodedata,math,numpy as np,pandas as pd,statsmodels.api as sm,warnings; warnings.filterwarnings('ignore')
from scipy.stats import fisher_exact,mannwhitneyu
R='/home/user/beautiful-danish-data'
ps={p['id']:p for p in json.load(open(f'{R}/data/papers.json'))}; net=json.load(open(f'{R}/data/network.json'))
P=json.load(open('ack_parsed.json')); H=json.load(open('hidx.json')); ack=json.load(open('ack_text.json'))
def key(s): return re.sub(r'[^a-z ]','',''.join(ch for ch in unicodedata.normalize('NFD',s.lower().replace('ø','o').replace('æ','ae').replace('å','a')) if not unicodedata.combining(ch)))
kk=lambda n:(key(n).split()[0][0],key(n).split()[-1])
site={kk(x['name']):x for x in net['nodes']}
papers=[p for p,t in ack.items() if t]            # papers with an acknowledgment found
top=lambda p:ps[p]['group']=='top5'
nT=sum(top(p) for p in papers); nO=len(papers)-nT
cnt=collections.Counter(n for p in papers for n in P['thanks'].get(p,[]))
valid={n for n,c in cnt.items() if c>=2 or H.get(n)}       # drop unmatched one-off strings
valid.discard('Alexander Paul') if False else None
thanks={p:[n for n in P['thanks'].get(p,[]) if n in valid] for p in papers}
hof=lambda n:0 if n=='Alexander Paul' else ((H.get(n) or {}).get('h') or 0)
STAR=60
star={p:any(hof(n)>=STAR for n in thanks[p]) for p in papers}
cnt=collections.Counter(n for p in papers for n in thanks[p]); cT=collections.Counter(n for p in papers if top(p) for n in thanks[p])
# funders
FN=[]
order=collections.Counter(f for p in papers for f in P['fund'].get(p,[]))
for f,c in order.most_common():
    a=sum(1 for p in papers if top(p) and f in P['fund'][p]); b=c-a
    FN.append(dict(name=f,n=c,top5=a,other=b,share_top5=round(a/nT,3),share_other=round(b/nO,3),p=round(float(fisher_exact([[a,nT-a],[b,nO-b]])[1]),3)))
anyf=[bool(P['fund'].get(p)) for p in papers]
# thanks stats
nt=lambda g:[len(thanks[p]) for p in papers if top(p)==g]
sa=sum(star[p] for p in papers if top(p)); sb=sum(star[p] for p in papers if not top(p))
T=dict(n_people=len(cnt),n_mentions=sum(cnt.values()),mean=[round(float(np.mean(nt(False))),1),round(float(np.mean(nt(True))),1)],median=[float(np.median(nt(False))),float(np.median(nt(True)))],
       p_count=round(float(mannwhitneyu(nt(True),nt(False)).pvalue),4),star_h=STAR,n_star=sum(1 for n in cnt if hof(n)>=STAR),
       star=[sb,nO,sa,nT],p_star=round(float(fisher_exact([[sa,nT-sa],[sb,nO-sb]])[1]),4))
# regression: does thanking a highly cited person go with Top 5 once team and sample are held fixed
d=pd.read_csv(f'{R}/analysis/top5_regression_data.csv').set_index('id').loc[papers]
d['star']=[int(star[p]) for p in papers]; d['log_thanked']=[math.log1p(len(thanks[p])) for p in papers]
cols=['star','log_thanked','mixed','abroad_only','top_inst','log_n','log_n_miss','year']
m=sm.Logit(d.top5,sm.add_constant(d[cols].astype(float))).fit(disp=0); a=m.get_margeff().summary_frame()
T['reg']={c:dict(b=round(float(a.loc[c,'dy/dx']),3),se=round(float(a.loc[c,'Std. Err.']),3),p=round(float(a.loc[c,'Pr(>|z|)']),3)) for c in ['star','log_thanked']}; T['reg_n']=len(d)
print(T); 
def grp(n):
    x=site.get(kk(n)); 
    return None if not x else ('abroad' if x['group']=='Institutions abroad' else 'dk')
most=[dict(name=n,n=c,top5=cT[n],site=grp(n),h=hof(n) or None) for n,c in cnt.most_common(30)]
# network of people thanked in >=3 papers, linked when thanked together in >=2 papers
import networkx as nx
nodes=[n for n,c in cnt.items() if c>=3]
G=nx.Graph(); G.add_nodes_from(nodes)
pair=collections.Counter()
for p in papers:
    t=sorted(set(thanks[p])&set(nodes))
    for i in range(len(t)):
        for j in range(i+1,len(t)): pair[(t[i],t[j])]+=1
for (a_,b_),w in pair.items():
    if w>=2: G.add_edge(a_,b_,weight=w)
big=max(nx.connected_components(G),key=len); iso=[n for n in G if n not in big]; G.remove_nodes_from(iso)
pos=nx.kamada_kawai_layout(G,weight=None)
pos=nx.spring_layout(G,pos=pos,k=5.5/math.sqrt(len(G)),iterations=300,seed=4,weight=None)
xs=[v[0] for v in pos.values()]; ys=[v[1] for v in pos.values()]
nx_=lambda v,lo,hi:round((v-lo)/(hi-lo),4)
NET=dict(nodes=[dict(name=n,n=cnt[n],site=grp(n),x=nx_(pos[n][0],min(xs),max(xs)),y=nx_(pos[n][1],min(ys),max(ys))) for n in G],
         links=[dict(a=a_,b=b_,w=G[a_][b_]['weight']) for a_,b_ in G.edges()],isolated=len(iso))
print(len(G),G.number_of_edges(),len(iso))
out=dict(n_read=len(ack),n_ack=len(papers),n_top5=nT,n_other=nO,any_funder=[sum(1 for p,f in zip(papers,anyf) if f and not top(p)),sum(1 for p,f in zip(papers,anyf) if f and top(p))],funders=FN,thanks=T,most=most,net=NET)
json.dump(out,open(f'{R}/data/acknowledgments.json','w'),ensure_ascii=False,indent=1)
for f in FN: print(f)
print([(m_['name'],m_['n'],m_['top5'],m_['site']) for m_ in most])
