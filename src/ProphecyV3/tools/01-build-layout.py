"""Prophecy v3 - the constellation menu's data: src/ProphecyV3/data/SKSE/Plugins/ZenProphecyUI.json.

v3 is v1's plugin and scripts plus ZenProphecyUI.dll, an SKSE Menu Framework window that draws each tree as a
constellation (nodes + lines, like the website's talent trees) instead of B612's card menu. The DLL reads this file.

Everything per perk is read from the v1 build's menu quest (ZP_ProphecyInit 0x807, script ZP_ProphecyMenu), so the
window's node index IS the script's array index: Perks, Descriptions, Images, ParentA/ParentB and TreeStart are the
arrays the script learns with. Names come from the perk records, tree names from v1's TREES.

Layout (symmetrical, generated): a node's tier is its longest path from the tree's root; the root sits at the bottom
and the tree grows upward. Each tier is centred and its nodes spread evenly (spacing 1.0), ordered by the mean
position of their parents, so two-way branches mirror left and right.

Run after src/Prophecy/tools/01-build-trees.py:  python -I src/ProphecyV3/tools/01-build-layout.py
"""
import os, re, sys, json, glob, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
V1 = os.path.join(REPO, 'src', 'Prophecy')
ESP = os.path.join(V1, 'ProphecyESP')
OUT = os.path.join(REPO, 'src', 'ProphecyV3', 'data', 'SKSE', 'Plugins', 'ZenProphecyUI.json')
MOD = 'Zenderal - Prophecy.esp'
POINTS = '000802'            # ZP_ProphecyPoints

_spec = importlib.util.spec_from_file_location('v1', os.path.join(V1, 'tools', '01-build-trees.py'))
v1 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(v1)


def quest_arrays():
    t = open(glob.glob(os.path.join(ESP, 'Quests', '* - 000807_*'))[0], encoding='utf-8').read().replace('\r\n', '\n')
    t = t.split('  - Name: ZP_ProphecyMenu\n', 1)[1]
    def block(name):
        m = re.search(rf'^      Name: {name}\n      (?:Objects|Data):\n((?:      - .*\n(?:        .*\n)*)*)', t, re.M)
        assert m, f'quest property {name} not found'
        return m.group(1)
    def unq(v):
        v = v.strip()
        if v.startswith('"'):
            return json.loads(v)             # YAML double-quoted: same escapes as JSON for this text
        return v[1:-1].replace("''", "'") if v.startswith("'") else v
    perks = re.findall(r'^        Object: ([0-9A-F]{6}):', block('Perks'), re.M)
    strs = lambda n: [unq(x) for x in re.findall(r'^      - (.*)$', block(n), re.M)]
    ints = lambda n: [int(x) for x in re.findall(r'^      - (-?\d+)\s*$', block(n), re.M)]
    return (perks, strs('Descriptions'), strs('Images'), ints('ParentA'), ints('ParentB'), ints('TreeStart'),
            ints('LevelReq'))


def perk_name(local_id):
    p = glob.glob(os.path.join(ESP, 'Perks', f'* - {local_id}_*'))[0]
    t = open(p, encoding='utf-8').read().replace('\r\n', '\n')
    v = re.search(r'^Name:\n  TargetLanguage: English\n  Value: (.*)$', t, re.M).group(1).strip()
    return v[1:-1].replace("''", "'") if v.startswith("'") else v


# Hand-drawn constellation shapes (curator, 2026-10-25), in square units, y up. 'nodes' places each talent (by its
# TREES id); 'via' routes a prerequisite line through waypoints so it follows the figure; 'stars' and 'lines' are
# decoration only (faint, not clickable); empty since 2026-10-25 - the curator wanted the talents alone to form the figure. Trees not listed keep the generated layout.
SHAPES = {
    # 2026-10-25: eleven talents each (the six stat talents joined the figures). A merge talent's two children sit
    # level with it as a short bar; the capstone's line then runs on through the merge talent, as the shaft does.
    'Faith': {                                           # a patriarchal crucifix: long bar, short bar above
        'nodes': {'fst2': (0, -1.2), 'faith1': (0, 0), 'fst1': (0, 1.4),
                  'fst3': (-2.6, 2.8), 'faith2': (-1.3, 2.8), 'faith3': (1.3, 2.8), 'fst4': (2.6, 2.8),
                  'fst5': (-0.95, 4.0), 'faith5': (0, 4.0), 'fst6': (0.95, 4.0), 'faith4': (0, 5.2)},
        # 2026-10-25 rework: Templar (faith5) is the merge talent, Wrath of the Lightborn (faith4) the capstone
        'via': {('fst1', 'faith2'): [(0, 2.8)], ('fst1', 'faith3'): [(0, 2.8)],
                ('faith2', 'faith5'): [(0, 2.8)], ('faith3', 'faith5'): [(0, 2.8)], ('fst6', 'faith4'): [(0, 4.0)]},
        'stars': [], 'lines': [],
    },
    'Glory': {                                           # a Zweihaender, point up: pommel, grip, guard, hooks, blade
        'nodes': {'lst2': (0, -1.3), 'glo1': (0, -0.3), 'lst1': (0, 0.6),
                  'lst3': (-2.3, 1.0), 'glo2': (-1.2, 1.4), 'glo3': (1.2, 1.4), 'lst4': (2.3, 1.0),
                  'lst5': (-0.95, 2.5), 'glo5': (0, 2.5), 'lst6': (0.95, 2.5), 'glo4': (0, 5.0)},
        'via': {('lst1', 'glo2'): [(0, 1.4)], ('lst1', 'glo3'): [(0, 1.4)],
                ('glo2', 'glo5'): [(0, 1.4)], ('glo3', 'glo5'): [(0, 1.4)], ('lst6', 'glo4'): [(0, 2.5)]},
        'stars': [], 'lines': [],
    },
    'Sharpshooter': {                                    # a long musket, muzzle to the right
        'yscale': 1.4,                                   # a rifle is long and thin: give the stock room
        # one straight top line butt -> wrist -> lock -> breech -> barrel -> muzzle; hammer, trigger, butt plate
        # and ramrod are the short strokes off it
        'labels_above': ['gst3', 'gst6', 'gun5'],
        'nodes': {'gun1': (-4.0, 0.3), 'gst2': (-4.0, -0.75), 'gst1': (-2.6, 0.3),
                  'gun2': (-1.2, 0.4), 'gst3': (-1.55, 0.95), 'gun3': (-1.0, -0.4), 'gst4': (-0.75, -0.95),
                  'gun4': (0.3, 0.42), 'gst5': (2.3, 0.0), 'gst6': (2.0, 0.45), 'gun5': (4.0, 0.45)},
        'via': {},
        'stars': [], 'lines': [],
    },
    'Gadgets': {                                         # an open-end wrench holding a nut
        'nodes': {'dst2': (0, -1.4), 'gad1': (0, -0.2), 'dst1': (0, 1.0),
                  'gad2': (-1.1, 2.0), 'gad3': (1.1, 2.0), 'dst3': (-1.25, 3.7), 'dst4': (1.25, 3.7),
                  'gad4': (0, 2.3), 'dst6': (-0.5, 3.0), 'dst5': (0.5, 3.0), 'gad5': (0, 3.7)},
        'via': {},
        'stars': [], 'lines': [],
    },
    'Martial Arts': {                                    # a lotus on its stem
        'nodes': {'mst2': (0, -1.4), 'ma1': (0, -0.3), 'mst1': (0, 0.8),
                  'mst3': (-2.5, 1.5), 'ma2': (-1.3, 2.0), 'ma3': (1.3, 2.0), 'mst4': (2.5, 1.5),
                  'ma4': (0, 2.5), 'mst5': (-0.6, 3.4), 'mst6': (0.6, 3.4), 'ma5': (0, 4.4)},
        'via': {},
        'stars': [], 'lines': [],
    },
    'Arcane Archery': {                                  # a drawn bow, arrow pointing up
        'nodes': {'ast2': (0, -1.3), 'arc1': (0, -0.3), 'ast1': (0, 0.6),
                  'ast3': (-2.5, 0.6), 'arc2': (-1.9, 1.5), 'arc3': (1.9, 1.5), 'ast4': (2.5, 0.6),
                  'ast5': (-0.95, 2.3), 'arc4': (0, 2.3), 'ast6': (0.95, 2.3), 'arc5': (0, 4.0)},
        'via': {('ast6', 'arc5'): [(0, 2.3)]},
        'stars': [], 'lines': [],
    },
    'Necromancy': {                                      # a reaper's scythe: snath with two grips, blade to the left
        'nodes': {'nst2': (0, -1.5), 'nec1': (0, -0.4), 'nst1': (0, 0.8),
                  'nec2': (0.75, 1.0), 'nst3': (1.4, 1.15), 'nec3': (0, 2.1), 'nst4': (0.8, 2.35),
                  'nec4': (0, 3.4), 'nst5': (0.6, 3.75), 'nst6': (-1.3, 3.95), 'nec5': (-2.8, 3.1)},
        'via': {},
        'stars': [], 'lines': [],
    },
}


def shape_for(tname, nodes, start):
    s = SHAPES.get(tname)
    if not s:
        return None
    ids = [n[0] for n in nodes]
    assert set(s['nodes']) == set(ids), f'{tname}: shape places {sorted(s["nodes"])}, tree has {sorted(ids)}'
    for (a, b) in s['via']:
        assert a in ids and b in ids, f'{tname}: route {a}->{b} names an unknown node'
    idx = {nid: start + k for k, nid in enumerate(ids)}
    ys = s.get('yscale', 1.0)
    P = lambda p: [p[0], round(p[1] * ys, 4)]
    return {
        'nodes': {str(idx[nid]): P(p) for nid, p in s['nodes'].items()},
        'routes': [{'from': idx[a], 'to': idx[b], 'via': [P(p) for p in pts]} for (a, b), pts in s['via'].items()],
        'stars': [P(p) for p in s['stars']],
        'lines': [[P(a), P(b)] for a, b in s['lines']],
        'labelsAbove': [idx[nid] for nid in s.get('labels_above', [])],
    }


def layout(indices, parents):
    """{index: (x, tier)} - x centred per tier, spacing 1.0; tier 0 = root (bottom)."""
    tier = {}
    def depth(i):
        if i not in tier:
            ps = [p for p in parents[i] if p in indices]
            tier[i] = 0 if not ps else 1 + max(depth(p) for p in ps)
        return tier[i]
    for i in indices:
        depth(i)
    # Nodes that lead further up are centred; a dead end below the top tier (a side talent, e.g. Necromancy's Dark
    # Effigy - The Dead Don't Forget needs A Willing Sacrifice only) goes out to the side, so the spine stays straight
    # (curator, 2026-10-25: centring everything drew a slanted line and a branch that looked cut off).
    top = max(tier.values())
    has_child = {i: any(i in parents[j] for j in indices) for i in indices}
    pos = {}
    for t in range(top + 1):
        row = [i for i in indices if tier[i] == t]
        def key(i):
            ps = [pos[p][0] for p in parents[i] if p in pos]
            return (sum(ps) / len(ps) if ps else 0.0, indices.index(i))
        row.sort(key=key)
        cont = [i for i in row if has_child[i] or t == top]
        side = [i for i in row if i not in cont]
        if not cont:
            cont, side = row, []
        for k, i in enumerate(cont):
            pos[i] = ((k - (len(cont) - 1) / 2.0), t)
        edge = (len(cont) - 1) / 2.0
        for k, i in enumerate(side):          # alternate left, right, further out each pair
            out = edge + 1.0 + k // 2
            pos[i] = (-out if k % 2 == 0 else out, t)
    return pos


def main():
    perks, descs, images, pa, pb, starts, levelreq = quest_arrays()
    n = len(perks)
    assert len(descs) == len(images) == len(pa) == len(pb) == len(levelreq) == n, 'quest arrays disagree in length'
    assert starts[-1] == n and len(starts) == len(v1.TREES) + 1, 'TreeStart does not match TREES'
    parents = [[p for p in (pa[i], pb[i]) if p >= 0] for i in range(n)]
    trees = []
    for t, (tname, tdesc, nodes) in enumerate(v1.TREES):
        idx = list(range(starts[t], starts[t + 1]))
        assert len(idx) == len(nodes), f'{tname}: {len(idx)} perks in the quest, {len(nodes)} in TREES'
        pos = layout(idx, parents)
        bg = os.path.join(REPO, 'src', 'ProphecyV3', 'assets', 'interface', 'ProphecyBackgrounds', tname.replace(' ', '-') + '.dds')
        trees.append({
            'name': tname,
            'description': tdesc,
            'background': ('Data\\Interface\\ProphecyBackgrounds\\' + os.path.basename(bg)) if os.path.isfile(bg) else '',
            'shape': shape_for(tname, nodes, starts[t]),
            'nodes': [{
                'index': i,
                'perk': int(perks[i], 16),
                'name': perk_name(perks[i]),
                'description': descs[i],
                'image': 'Data\\Interface\\' + images[i].replace('/', '\\'),
                'parents': parents[i],
                'x': pos[i][0],
                'tier': pos[i][1],
                'minLevel': levelreq[i],     # capstones: level 30 (curator 2026-10-25)
            } for i in idx],
        })
    # the selection notes, in melody order (ZP_Prophecy_SelectNote_NN; the clips come from tools/03-split-piano.py)
    notes = []
    for p in sorted(glob.glob(os.path.join(ESP, 'SoundDescriptors', 'ZP_Prophecy_SelectNote_* - *.yaml'))):
        notes.append(int(re.search(r'^FormKey: ([0-9A-F]{6}):', open(p, encoding='utf-8').read(), re.M).group(1), 16))
    data = {'plugin': MOD, 'pointsGlobal': int(POINTS, 16), 'selectNotes': notes, 'trees': trees}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(data, fh, indent=1, ensure_ascii=False)
    for tr in trees:
        rows = {}
        for nd in tr['nodes']:
            rows.setdefault(nd['tier'], []).append(f"{nd['name']}({nd['x']:+.1f})")
        print(tr['name'], ' | '.join(' '.join(rows[k]) for k in sorted(rows)))
    print(f'{n} perks, {len(trees)} trees -> {OUT}')


if __name__ == '__main__':
    main()
