import json,re,collections,unicodedata
R='/home/user/beautiful-danish-data'
T=json.load(open('dk_topics.json')); net=json.load(open(f'{R}/data/network.json'))
RULES=[('Health',r'health|pharmaceut|medical|care\b|hospital|disease|covid|mental|cancer|patient|clinical|nursing|aging|obesity|alcohol|smoking'),
 ('Household finance and pensions',r'financial literacy|pension|household|consumer|saving|microfinance|retirement'),
 ('Labour',r'labor|labour|wage|employment|unemploy|migration|gender|job|work\b|workplace|human capital|occupation'),
 ('Education, family and inequality',r'education|school|intergenerational|family|child|inequality|poverty|fertility|demograph|marriage|youth|student'),
 ('Public finance and political economy',r'\btax|fiscal|welfare|social policy|local government|public administration|political|electoral|voting|public policy|corruption|governance and reform|european union policy'),
 ('Finance',r'financial|finance|investment|banking|credit|risk|volatility|stochastic|portfolio|insurance|asset|fintech|auditing|corporate|equity|bond|stock|venture|accounting|earnings'),
 ('Macro and monetary',r'monetary|economic growth|productivity|crisis|business cycle|inflation|macro|economic theory and policy|economic and fiscal'),
 ('Trade and international',r'trade|international business|fdi|globali|exchange rate|development and aid|economic zones'),
 ('Environment, energy and agriculture',r'climate|environment|energy|agricultur|resource|forest|fisher|food|conservation|transport|sustainab|water|land use|carbon|electricity|marine'),
 ('Behavioural and experimental',r'experimental|behavioral|behavioural|decision-making|game theory|psycholog'),
 ('Firms, innovation and competition',r'innovation|firm|merger|competition|entrepreneur|ict\b|industrial|auction|market dynamics|digital|technology|patent|supply chain|platform|r&d'),
 ('Urban, housing and regional',r'housing|urban|agglomeration|regional|spatial|city|cities'),
 ('Economic history',r'histor'),
 ('Theory and econometrics',r'economic theor|theories and models|statistical|econometric|time series|probability|bayesian|mathematical|optimization|forecast')]
def fld(t):
    t=t.lower()
    for n,rx in RULES:
        if re.search(rx,t): return n
    return 'Other'
def key(s): return re.sub(r'[^a-z ]','',''.join(ch for ch in unicodedata.normalize('NFD',s.lower().replace('ø','o').replace('æ','ae').replace('å','a').replace('‐','-').replace('-',' ')) if not unicodedata.combining(ch)))
site_ids={x['id'] for x in net['nodes']}; site_names={key(x['name']) for x in net['nodes']}
site_fl={(key(x['name']).split()[0],key(x['name']).split()[-1]) for x in net['nodes']}
def is_site(i,n):
    k=key(n).split(); return i in site_ids or key(n) in site_names or (len(k)>1 and (k[0],k[-1]) in site_fl)
tot=collections.Counter(); here=collections.Counter(); unm=collections.Counter(); ex=collections.defaultdict(list)
for i,v in T.items():
    w=collections.Counter()
    for name,c,sub,f in v['topics']:
        g=fld(name); w[g]+=c
        if g=='Other': unm[name]+=c
    best=[g for g,_ in w.most_common() if g!='Other']
    g=best[0] if best and w[best[0]]>=w['Other']*0.5 else 'Other'
    tot[g]+=1
    if is_site(i,v['name']): here[g]+=1; ex[g].append(v['name'])
rows=[dict(field=g,people=n,here=here[g]) for g,n in tot.most_common()]
json.dump(dict(rows=rows,n=sum(tot.values()),n_here=sum(here.values())),open('fields.json','w'),indent=1)
for r in sorted(rows,key=lambda r:-r['here']/r['people']): print(f"{r['field']:38}{r['people']:4}{r['here']:4} {100*r['here']/r['people']:3.0f}%  {ex[r['field']][:6]}")
print(sum(tot.values()),sum(here.values())); print(unm.most_common(25))
