"""Index a serialized plugin tree and compute the record closure of a set of FormKeys (own-plugin refs only)."""
import os,re,glob,collections
FK=re.compile(r'\b([0-9A-F]{6}):([^\n:]*?\.es[pml])\b')
def index(root):
    recs={}
    for p in glob.glob(os.path.join(root,'*','*.yaml')):
        if os.path.basename(os.path.dirname(p)) in ('Cells','Worldspaces'): continue
        t=open(p,encoding='utf-8').read()
        m=re.search(r'^FormKey: (.+?)\s*$',t,re.M)
        if m: recs[m.group(1)]=(os.path.basename(os.path.dirname(p)),p,t)
    return recs
def closure(recs,seeds,plugin,stop=lambda fk,typ:False):
    seen=set(); q=list(seeds); ext=collections.Counter()
    while q:
        fk=q.pop()
        if fk in seen: continue
        if fk not in recs: ext[fk]+=1; continue
        seen.add(fk); typ,_,t=recs[fk]
        if stop(fk,typ) and fk not in seeds: continue
        for h,f in FK.findall(t):
            r=f'{h}:{f}'
            if f==plugin and r not in seen: q.append(r)
            elif f!=plugin: ext[r]+=1
    return seen,ext
