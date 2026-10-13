import os,re,sys,glob,collections
root=sys.argv[1]; out=sys.argv[2]
def idx(folder):
    m={}
    for p in glob.glob(os.path.join(root,folder,'*.yaml')):
        t=open(p,encoding='utf-8').read()
        fk=re.search(r'^FormKey: (\S+)',t,re.M).group(1)
        m[fk]=t
    return m
perks=idx('Perks'); spells=idx('Spells'); mgef=idx('MagicEffects')
def f(t,k):
    m=re.search(r'^'+k+r':\n  TargetLanguage: \w+\n  Value: (.*)',t,re.M)
    if m: return m.group(1).strip()
    m=re.search(r'^'+k+r': (.*)',t,re.M); return m.group(1).strip() if m else ''
def req(t):
    head=t.split('\nEffects:')[0]
    m=re.findall(r'ActorValue: (\w+)\n  ComparisonValue: ([\d.]+)',head)
    return ', '.join(f'{a} {v}' for a,v in m)
def kinds(t):
    body=t.split('\nEffects:',1)[1] if '\nEffects:' in t else ''
    c=collections.Counter(re.findall(r'^- MutagenObjectType: (Perk\w+)',body,re.M))
    eps=sorted(set(re.findall(r'EntryPoint: (\w+)',body)))
    sp=re.findall(r'^  (?:Spell|Ability): (\S+)',body,re.M)
    return eps,sp
L=[]
for p in sorted(glob.glob(os.path.join(root,'ActorValueInformation','*.yaml'))):
    t=open(p,encoding='utf-8').read()
    name=f(t,'Name'); L.append(f'\n## {name} ({f(t,"EditorID")})\n')
    nodes=re.findall(r'- Perk: (\S+)',t)
    for fk in nodes:
        pt=perks.get(fk)
        if not pt: L.append(f'- `{fk}` (not in plugin)'); continue
        chain=[]; cur=fk; seen=set()
        while cur and cur in perks and cur not in seen:
            seen.add(cur); x=perks[cur]
            chain.append(x); n=re.search(r'^NextPerk: (\S+)',x,re.M); cur=n.group(1) if n else None
        first=chain[0]
        L.append(f'- **{f(first,"Name")}** — `{f(first,"EditorID")}` `{fk}` — ranks {len(chain)}')
        for i,x in enumerate(chain):
            eps,sp=kinds(x)
            sps=[f(spells[s],'EditorID') if s in spells else s for s in sp]
            L.append(f'  - R{i+1} [{req(x)}] {f(x,"Description")}')
            L.append(f'    - mech: EP={",".join(eps) or "-"} | abilities={",".join(sps) or "-"}')
open(out,'w',encoding='utf-8').write('\n'.join(L))
