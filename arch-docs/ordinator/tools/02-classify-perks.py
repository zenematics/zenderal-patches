import os,re,sys,glob,collections,json
root=sys.argv[1]; base=sys.argv[2]
def idx(folder,r=root):
    m={}
    for p in glob.glob(os.path.join(r,folder,'*.yaml')):
        t=open(p,encoding='utf-8').read()
        mm=re.search(r'^FormKey: (\S+)',t,re.M)
        if mm: m[mm.group(1)]=(p,t)
    return m
perks=idx('Perks'); spells=idx('Spells'); mgef=idx('MagicEffects')
def scripts(t): return re.findall(r'^\s+- Name: (\w+)\n',t.split('Effects:')[0] if False else t,re.M)
def vmad(t):
    if 'VirtualMachineAdapter' not in t: return []
    seg=t.split('VirtualMachineAdapter:')[1]
    return re.findall(r'^  - Name: (\S+)',seg,re.M)[:3]
nodes=[]
for p in sorted(glob.glob(os.path.join(root,'ActorValueInformation','*.yaml'))):
    t=open(p,encoding='utf-8').read()
    tree=re.search(r'EditorID: AV(\w+)',t).group(1)
    for fk in re.findall(r'- Perk: (\S+)',t):
        if fk not in perks: continue
        chain=[];cur=fk;seen=set()
        while cur in perks and cur not in seen:
            seen.add(cur);chain.append(perks[cur][1]);n=re.search(r'^NextPerk: (\S+)',perks[cur][1],re.M);cur=n.group(1) if n else ''
        cls=set(); scr=set()
        for x in chain:
            scr|=set(vmad(x))
            body=x.split('\nEffects:',1)[1] if '\nEffects:' in x else ''
            if re.search(r'PerkEntryPoint',body): cls.add('EP')
            for s in re.findall(r'^  (?:Spell|Ability): (\S+)',body,re.M):
                cls.add('ABIL')
                if s in spells:
                    st=spells[s][1]; scr|=set(vmad(st))
                    for e in re.findall(r'BaseEffect: (\S+)',st):
                        if e in mgef: scr|=set(vmad(mgef[e][1]))
            if re.search(r'ActivateChoice|PerkEntryPointAddActivateChoice|EntryPoint: Activate',body): cls.add('ACT')
        name=re.search(r'Name:\n  TargetLanguage: \w+\n  Value: (.*)',chain[0]).group(1)
        kind='script' if scr else ('ep-only' if cls<= {'EP'} else 'abil-noscript')
        nodes.append((tree,name,fk,kind,sorted(scr)))
c=collections.Counter(n[3] for n in nodes)
print('total',len(nodes),c)
for tree in sorted(set(n[0] for n in nodes)):
    cc=collections.Counter(n[3] for n in nodes if n[0]==tree); print(tree,dict(cc))
json.dump(nodes,open(sys.argv[3],'w'),indent=0)
# vanilla-suffixed overrides vs Enderal base
bp=idx('Perks',base)
sk=[n for n in nodes if n[2].endswith(':Skyrim.esm')]
print('\nskyrim-suffixed tree perks',len(sk))
allbase={}
for d in os.listdir(base):
    for p in glob.glob(os.path.join(base,d,'*.yaml')):
        allbase.setdefault(re.search(r' - (\w{6})_Skyrim\.esm\.yaml$',p).group(1) if re.search(r' - (\w{6})_Skyrim\.esm\.yaml$',p) else None,[]).append(d+'/'+os.path.basename(p))
for n in sk:
    h=n[2][:6]; print(n[0],n[1],h,'->',allbase.get(h,['ABSENT in Enderal Skyrim.esm'])[0][:90])
