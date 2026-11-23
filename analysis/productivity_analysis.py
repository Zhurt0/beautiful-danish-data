import json,collections,re,unicodedata
R='/home/user/beautiful-danish-data'
A=json.load(open('dk_econ_authors.json')); net=json.load(open(f'{R}/data/network.json')); ps={p['id']:p for p in json.load(open(f'{R}/data/papers.json'))}
def key(s): return re.sub(r'[^a-z ]','',''.join(ch for ch in unicodedata.normalize('NFD',s.lower().replace('ø','o').replace('æ','ae').replace('å','a').replace('‐','-').replace('-',' ')) if not unicodedata.combining(ch)))
econ=[x for x in A if x['econ_share']>=0.4 and x['recent']>0]
site_ids={x['id'] for x in net['nodes']}; site_names={key(x['name']) for x in net['nodes']}
site_fl={(key(x['name']).split()[0],key(x['name']).split()[-1]) for x in net['nodes']}
def is_site(x):
    k=key(x['name']).split()
    return x['id'] in site_ids or key(x['name']) in site_names or (len(k)>1 and (k[0],k[-1]) in site_fl)
INST=['University of Copenhagen','Aarhus University','Copenhagen Business School','University of Southern Denmark','Aalborg University','Danmarks Nationalbank','Technical University of Denmark','Roskilde University','VIVE - The Danish Center for Social Science Research','Rockwool Foundation']
rows=[]
def row(name,members,nodes):
    pp={p for x in nodes for p in x['papers']}
    return dict(name=name,econ=len(members),econ_site=sum(1 for x in members if is_site(x)),papers=len(pp),top5=sum(1 for p in pp if ps[p]['group']=='top5'),site_authors=len(nodes))
for i in INST:
    mem=[x for x in econ if any(n==i and c=='DK' for n,c in x['inst'])]
    nodes=[x for x in net['nodes'] if i in x['institutions']]
    rows.append(row(i,mem,nodes))
dk_nodes=[x for x in net['nodes'] if x['group']!='Institutions abroad']
tot=row('Denmark',econ,dk_nodes)
out=dict(rows=rows,total=tot,n_listed=len(A))
json.dump(out,open(f'{R}/data/productivity.json','w'),ensure_ascii=False,indent=1)
for r in rows+[tot]: print(r, round(100*r['papers']/r['econ'],1), round(100*r['econ_site']/r['econ'],1))
