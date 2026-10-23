"""Read Enderal's meditation worldspace (Akropolis 0A7FB9) from reference/base: every placed ref with base, position,
rotation, scale and linked refs. Shared by the ProphecyV2 generators."""
import os, re, glob
REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
AKRO = os.path.join(REPO, 'reference', 'base', 'Skyrim', 'Worldspaces', 'Akropolis - 0A7FB9_Skyrim.esm')
STAR, LINE, LINESMALL = '05BD42:Skyrim.esm', '0A8263:Skyrim.esm', None

def refs():
    out = {}
    for p in glob.glob(os.path.join(AKRO, '**', 'RecordData.yaml'), recursive=True):
        t = open(p, encoding='utf-8').read().replace('\r\n', '\n')
        for blk in re.split(r'\n(?= *- MutagenObjectType: PlacedObject\n)', t):
            fk = re.search(r'^ *FormKey: (.+?)\s*$', blk, re.M)
            b = re.search(r'^ *Base: (.+?)\s*$', blk, re.M)
            if not (fk and b and 'PlacedObject' in blk.split('\n')[0]): continue
            pos = re.search(r'Position: (\S+), (\S+), (\S+)', blk)
            rot = re.search(r'Rotation: (\S+), (\S+), (\S+)', blk)
            sc = re.search(r'^ *Scale: (\S+)', blk, re.M)
            links = re.findall(r'(?:KeywordOrReference: (\S+)\n *)?Reference: (\S+:\S+?\.es[mp])', blk.split('Placement:')[0])
            out[fk.group(1)] = dict(base=b.group(1), pos=tuple(map(float, pos.groups())) if pos else (0, 0, 0),
                                    rot=tuple(map(float, rot.groups())) if rot else (0, 0, 0),
                                    scale=float(sc.group(1)) if sc else 1.0, links=links, text=blk,
                                    persistent='Persistent' in p or os.path.dirname(p) == AKRO,
                                    file=p)
    return out
