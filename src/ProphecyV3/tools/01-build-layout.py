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
import os, re, sys, json, glob, math, importlib.util

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
    'Firearms': {                                    # a long musket, muzzle to the right
        'yscale': 1.4,                                   # a rifle is long and thin: give the stock room
        # one straight top line butt -> wrist -> lock -> breech -> barrel -> muzzle; hammer, trigger, butt plate
        # and ramrod are the short strokes off it
        'labels_above': ['gst3', 'gst6', 'gun5'],
        'nodes': {'gun1': (-4.0, 0.3), 'gst2': (-4.0, -0.75), 'gst1': (-2.6, 0.3),
                  'gun2': (-1.2, 0.4), 'gst3': (-1.75, 1.15), 'gun3': (-1.0, -0.4), 'gst4': (-0.5, -1.15),
                  'gun4': (0.3, 0.42), 'gst5': (2.6, -0.25), 'gst6': (2.0, 0.45), 'gun5': (4.0, 0.45),   # opened up 2026-10-27
                  'gun6': (-2.6, -0.75)},                # Ricochet Rounds (2026-10-29), under Steady Aim
        'via': {},
        'stars': [], 'lines': [],
    },
    'Gadgets': {                                         # an open-end wrench holding a nut
        'nodes': {'dst2': (0, -1.4), 'gad1': (0, -0.2), 'dst1': (0, 1.0),          # nut opened up 2026-10-27
                  'gad2': (-1.2, 2.0), 'gad3': (1.2, 2.0), 'dst3': (-1.35, 4.0), 'dst4': (1.35, 4.0),
                  'gad4': (0, 2.3), 'dst6': (-0.65, 3.15), 'dst5': (0.65, 3.15), 'gad5': (0, 4.0),
                  'gad6': (-2.35, 2.0)},                 # Chaff (2026-10-26): a spur off Smokescreen
        'via': {},
        'stars': [], 'lines': [],
    },
    'Shadow': {                                          # a dagger, point up, through an upturned crescent moon
        'nodes': {'sst2': (0, -1.3), 'shd1': (0, -0.3), 'sst1': (0, 0.7),
                  'shd2': (-1.3, 1.3), 'shd3': (1.3, 1.3), 'sst3': (-2.3, 2.9), 'sst4': (2.3, 2.9),
                  'sst5': (-0.95, 2.4), 'shd4': (0, 2.4), 'sst6': (0.95, 2.4), 'shd5': (0, 4.6),
                  'shd6': (0, 1.55), 'shd7': (0, 2.0)},  # Shade Veil, Darkness (2026-10-28): down the blade
        'via': {('sst6', 'shd5'): [(0, 2.4)]},
        'stars': [], 'lines': [],
    },
    'Martial Arts': {                                    # a lotus on its stem
        'nodes': {'mst2': (0, -1.4), 'ma1': (0, -0.3), 'mst1': (0, 0.8),
                  'mst3': (-2.5, 1.5), 'ma2': (-1.3, 2.0), 'ma3': (1.3, 2.0), 'mst4': (2.5, 1.5),
                  'ma6': (-2.3, 2.6),                    # Dragon's Breath (2026-10-28), beside Hissing Dragon
                  'ma4': (0, 2.5), 'mst5': (-0.6, 3.4), 'mst6': (0.6, 3.4), 'ma5': (0, 4.4)},
        'via': {},
        'stars': [], 'lines': [],
    },
    'Rage': {                                            # a double-headed axe: Heavenfall's head left, Shadowbringer's right
        'nodes': {'yst2': (0, -1.3), 'rge1': (0, -0.3), 'yst1': (0, 0.7),
                  'rge2': (-1.1, 1.6), 'yst3': (-2.1, 1.1), 'rge3': (-2.1, 2.4), 'rge4': (-1.2, 2.9),
                  'rge5': (1.1, 1.6), 'yst4': (2.1, 1.1), 'rge6': (2.1, 2.4), 'yst5': (2.1, 3.5), 'rge7': (1.2, 2.9),
                  'rge8': (0, 3.4), 'yst6': (0, 4.5), 'rge9': (0, 5.7)},
        'via': {},
        'stars': [], 'lines': [],
    },
    'Druidic': {                                           # an oak: roots, trunk, a round crown (growths left, totems right)
        'nodes': {'vst2': (0, -1.3), 'dru1': (0, -0.3), 'vst1': (0, 0.7),
                  'dru2': (-1.3, 1.6), 'vst3': (-2.3, 2.2), 'dru3': (-1.3, 3.2),
                  'dru4': (1.2, 1.4), 'vst4': (2.3, 1.0), 'dru5': (2.5, 2.6), 'vst5': (2.4, 3.5), 'dru6': (1.3, 3.4),
                  'vst6': (0, 4.2), 'dru7': (0, 5.4),
                  'dru8': (0, 2.2),                      # Twister (2026-10-27): up the trunk, a dead end
                  'dru9': (-2.5, 1.2), 'dru10': (3.4, 2.4)},   # Wolf Pack, Nature's Way (2026-10-29)
        'via': {},
        'stars': [], 'lines': [],
    },
    'Sorcery': {                                        # a star: elements to the left, the stars to the right, meeting in Falling Star
        'nodes': {'cst2': (0, -1.3), 'sor1': (0, -0.3), 'cst1': (0, 0.8),
                  'sor2': (-1.1, 1.8), 'cst3': (-2.0, 1.3), 'sor4': (-2.1, 2.8), 'sor3': (-1.1, 3.5),
                  'cst4': (-2.0, 4.2), 'sor10': (-1.1, 5.0),
                  'sor5': (1.1, 1.8), 'cst5': (2.0, 1.3), 'sor7': (2.1, 2.8), 'sor6': (1.1, 3.5),
                  'sor8': (0, 4.3), 'cst6': (0, 5.5), 'sor9': (0, 6.8)},
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
        'nodes': {'nst2': (0, -1.7), 'nec1': (0, -0.5), 'nst1': (0, 0.8),          # opened up 2026-10-27
                  'nec2': (1.0, 1.2), 'nst3': (2.0, 1.45), 'nec3': (0, 2.3), 'nst4': (1.1, 2.65),
                  'nec4': (0, 3.8), 'nst5': (0.95, 4.3), 'nst6': (-1.5, 4.45), 'nec5': (-3.2, 3.6)},
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


# The radial map (curator 2026-10-27, "like Path of Exile"): every tree on one canvas, a Prophecy start point at the
# centre, each tree's figure turned so its root -> capstone axis points straight out along its own spoke, clockwise
# from Faith at the top - the order of the background art's wedges (Prophecy-Radial.png). Map units, y up, centre 0,0.
RADIAL_ROOT = float(os.environ.get('ZP_RADIAL_ROOT', 3.5))     # the least a tree's root sits out from the centre
RADIAL_SPREAD = float(os.environ.get('ZP_RADIAL_SPREAD', 2.0)) # each figure scaled by this on the map (2026-10-27: 1.2 bunched the talents under their names, 2.0)
RADIAL_LABEL_GAP = 1.9         # tree name: this far beyond its furthest talent
RADIAL_FILL = float(os.environ.get('ZP_RADIAL_FILL', 0.6))      # share of its half-slice a figure may use (0.75: Arcane Archery touched Glory)
RADIAL_LENGTH = float(os.environ.get('ZP_RADIAL_LENGTH', 0.0))  # every figure this long (0 = RADIAL_SPREAD)
RADIAL_MIN_CENTRE = 2.0        # nothing behind a root comes closer to the centre than this
# each tree's share of the circle (default 1). Glory and Rage wider (curator 2026-10-27: Druid and Arcane Archery moved
# further clockwise to give them room); the others give up a little. Faith stays at the top.
RADIAL_WEIGHT = {'Glory': 1.35, 'Rage': 1.35}
RADIAL_SCALE = {'Necromancy': 0.65}   # a figure drawn smaller without changing its slice (curator 2026-10-27: Necromancy stuck out)
RADIAL_BG = 'Data\\Interface\\ProphecyBackgrounds\\Radial.dds'
TREE_COLOR = {'Faith': (232, 196, 110), 'Firearms': (205, 140, 80), 'Gadgets': (190, 165, 105),
              'Martial Arts': (110, 190, 175), 'Glory': (215, 90, 75), 'Arcane Archery': (110, 155, 230),
              'Necromancy': (165, 110, 210), 'Shadow': (130, 140, 170),
              'Druidic': (115, 180, 95), 'Sorcery': (90, 200, 230), 'Rage': (240, 120, 30)}


def place_radial(trees):
    """Adds mx/my to every node, and color/labelPos/mapRoutes/angle to every tree. Returns the map's own settings.

    The roots form a perfect circle (curator 2026-10-29, "equally spaced like on the website"): every slice is the
    same width, so the roots are 360/n degrees apart, and every root sits at one shared radius - the largest any figure
    needs to stay inside its slice (first pass). RADIAL_WEIGHT now only draws Glory and Rage larger."""
    n = len(trees)
    weights = [RADIAL_WEIGHT.get(t['name'], 1.0) for t in trees]
    far_all = 0.0
    shared = None
    for pass_ in ('measure', 'place'):
        needs = []
        for k, t in enumerate(trees):
            r = _place_tree(t, k, n, weights[k], shared)
            needs.append(r[0])
            if pass_ == 'place':
                far_all = max(far_all, r[1])
        shared = max(needs)
    print(f'roots on a circle of radius {shared:.2f}, {360 / n:.2f} degrees apart (each tree alone: '
          + ', '.join(f"{t['name']} {nd:.2f}" for t, nd in zip(trees, needs)) + ')')
    bg = os.path.join(REPO, 'src', 'ProphecyV3', 'assets', 'interface', 'ProphecyBackgrounds', 'Radial.dds')
    return {'rootRadius': round(shared, 4), 'extent': round(far_all + 0.8, 3),
            'background': RADIAL_BG if os.path.isfile(bg) else ''}


def _place_tree(t, k, n, weight, root_r_shared):
    """One tree on spoke k of n: returns (the root radius its figure needs, its furthest reach incl. the name).
    With root_r_shared it is placed at that radius instead."""
    if True:
        s = t['shape']
        assert s, f"{t['name']}: the radial map needs every tree shaped"
        pos = {int(i): tuple(p) for i, p in s['nodes'].items()}
        root = next(nd['index'] for nd in t['nodes'] if not nd['parents'])
        cap = next(nd['index'] for nd in t['nodes'] if nd['minLevel'])
        rx, ry = pos[root]
        ang_fig = math.atan2(pos[cap][1] - ry, pos[cap][0] - rx)
        # balanced trees (2026-10-27): each figure scaled so it reaches RADIAL_LENGTH from its root - the long rifle and
        # sword no longer set the map's size while the compact figures stay cramped
        span = max(math.hypot(p[0] - rx, p[1] - ry) for p in pos.values())
        spread = (RADIAL_LENGTH / span if RADIAL_LENGTH > 0 else RADIAL_SPREAD) * weight * RADIAL_SCALE.get(t['name'], 1.0)   # Glory and Rage drawn larger
        # the slice's centre, clockwise from Faith's at the top; every slice 360/n degrees
        ang = math.pi / 2 - 2 * math.pi * k / n
        rot = ang - ang_fig
        cs, sn = math.cos(rot), math.sin(rot)

        # each tree starts as far out as it needs for its whole figure (stars and line waypoints) to stay inside its
        # own slice of the circle: |across| <= tan(half slice * RADIAL_FILL) * (root + along). One shared root radius
        # let the wide figures (Faith's crossbar, Glory's guard) reach into their neighbours (curator 2026-10-27).
        def local(p):
            x, y = (p[0] - rx) * spread, (p[1] - ry) * spread
            xr, yr = x * cs - y * sn, x * sn + y * cs
            return xr * math.cos(ang) + yr * math.sin(ang), -xr * math.sin(ang) + yr * math.cos(ang)
        pts = [pos[i] for i in pos] + [tuple(v) for r in s['routes'] for v in r['via']]
        tan_half = math.tan(math.pi / n * RADIAL_FILL)
        need = RADIAL_ROOT
        for p in pts:
            along, across = local(p)
            need = max(need, abs(across) / tan_half - along, RADIAL_MIN_CENTRE - along)
        if root_r_shared is None:
            return need, 0.0
        root_r = root_r_shared

        def T(p, root_r=root_r):
            x, y = (p[0] - rx) * spread, (p[1] - ry) * spread
            return [round(math.cos(ang) * root_r + x * cs - y * sn, 4),
                    round(math.sin(ang) * root_r + x * sn + y * cs, 4)]
        far = 0.0
        for nd in t['nodes']:
            nd['mx'], nd['my'] = T(pos[nd['index']])
            far = max(far, math.hypot(nd['mx'], nd['my']))
        t['mapRoutes'] = [{'from': r['from'], 'to': r['to'], 'via': [T(v) for v in r['via']]} for r in s['routes']]
        t['angle'] = round(math.degrees(ang), 3)
        t['color'] = list(TREE_COLOR.get(t['name'], (200, 196, 186)))
        # the name well past the furthest talent, so it never sits on the capstone's own label (curator 2026-10-27)
        t['labelPos'] = [round(math.cos(ang) * (far + RADIAL_LABEL_GAP), 4), round(math.sin(ang) * (far + RADIAL_LABEL_GAP), 4)]
        return need, far + RADIAL_LABEL_GAP


# Label sides (curator 2026-10-27: names overlapped at the whole-map view). Each talent's name goes below, above, right
# or left of its star - whichever collides least with stars, tree names and the labels placed before it - judged at
# the default view of a reference canvas (the curator's 16:9 window). Mirrors DrawMap's sizes. Pillow is not available
# under -I, so text widths come from a per-character table for Futura Book.
REF_CANVAS = (1784, 1130)
REF_FONT = 20.0
SIDES = ('below', 'above', 'right', 'left')


def text_w(s, size):
    w = 0.0
    for ch in s:
        if ch in "iljtf'.,:;!| ": w += 0.28
        elif ch in 'mwMW': w += 0.86
        elif ch.isupper(): w += 0.66
        else: w += 0.52
    return w * size


def label_boxes(x, y, r, w, h):
    return {'below': (x - w / 2, y + r + 4, x + w / 2, y + r + 4 + h),
            'above': (x - w / 2, y - r - 4 - h, x + w / 2, y - r - 4),
            'right': (x + r + 5, y - h / 2, x + r + 5 + w, y + h / 2),
            'left': (x - r - 5 - w, y - h / 2, x - r - 5, y + h / 2)}


def place_labels(trees, extent):
    cw, ch = REF_CANVAS
    sc = min(cw, ch) / (2 * extent)
    z = max(0.7, min(2.4, sc / 45.0))
    ls = REF_FONT * max(0.8, min(1.5, z * 0.9))
    tfs = REF_FONT * max(1.15, min(2.2, z * 1.35))
    P = lambda p: (cw / 2 + p[0] * sc, ch / 2 - p[1] * sc)
    hit = lambda a, b: a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]
    # a tree's name steps outward until it clears its own stars (Arcane Archery's sat on Arcane Echo) and the room
    # their names may take on any side (2026-10-27: on eight trees "Gadgets" sat on Clockwork Turret's name)
    def zone(n):
        x, y = P((n['mx'], n['my']))
        if n['minor']: return (x - 14 * z, y - 14 * z, x + 14 * z, y + 14 * z)
        w = text_w(n['name'], ls) / 2 + 14 * z
        return (x - w, y - ls - 14 * z, x + w, y + ls + 14 * z)
    for t in trees:
        for _ in range(30):
            x, y = P(t['labelPos'])
            w = text_w(t['name'], tfs)
            box = (x - w / 2, y - tfs / 2, x + w / 2, y + tfs / 2)
            if not any(hit(box, zone(n)) for n in t['nodes']):
                break
            d = math.hypot(*t['labelPos'])
            t['labelPos'] = [round(t['labelPos'][0] * (d + 0.3) / d, 4), round(t['labelPos'][1] * (d + 0.3) / d, 4)]
    obstacles = []
    for t in trees:
        for n in t['nodes']:
            x, y = P((n['mx'], n['my']))
            r = (12 if n['minLevel'] else 6 if n['minor'] else 8.5) * z + 2
            obstacles.append((n['index'], (x - r, y - r, x + r, y + r)))
        x, y = P(t['labelPos'])
        w = text_w(t['name'], tfs)
        obstacles.append((-1, (x - w / 2, y - tfs / 2, x + w / 2, y + tfs / 2)))
    placed, bad = [], 0
    nodes = [n for t in trees for n in t['nodes']]
    nodes.sort(key=lambda n: (not n['minLevel'], n['minor']))      # capstones first, stat talents last
    for n in nodes:
        x, y = P((n['mx'], n['my']))
        r = (12 if n['minLevel'] else 6 if n['minor'] else 8.5) * z
        boxes = label_boxes(x, y, r, text_w(n['name'], ls), ls)
        def cost(side):
            b = boxes[side]
            c = sum(1 for i, o in obstacles if i != n['index'] and hit(b, o)) + sum(1 for o in placed if hit(b, o))
            c += 4 * (b[0] < 0 or b[2] > cw or b[1] < 0 or b[3] > ch)
            return c
        side = min(SIDES, key=lambda s: (cost(s), SIDES.index(s)))
        n['labelSide'] = SIDES.index(side)
        bad += cost(side) > 0
        if not n['minor']:               # stat talents' names only show zoomed in: they do not block the others
            placed.append(boxes[side])
    return bad


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
                'minor': nodes[k][0] in v1.STAT,     # a stat talent: the map hides its label when zoomed out
            } for k, i in enumerate(idx)],
        })
    radial = place_radial(trees)
    crowded = place_labels(trees, radial['extent'])
    # a tree name stepped outward still fits the whole-map view
    radial['extent'] = round(max(radial['extent'], max(math.hypot(*t['labelPos']) for t in trees) + 0.8), 3)
    print(f'labels: {crowded} still crowded at the whole-map view')
    # the selection notes, in melody order (ZP_Prophecy_SelectNote_NN; the clips come from tools/03-split-piano.py)
    notes = []
    for p in sorted(glob.glob(os.path.join(ESP, 'SoundDescriptors', 'ZP_Prophecy_SelectNote_* - *.yaml'))):
        notes.append(int(re.search(r'^FormKey: ([0-9A-F]{6}):', open(p, encoding='utf-8').read(), re.M).group(1), 16))
    data = {'plugin': MOD, 'pointsGlobal': int(POINTS, 16), 'selectNotes': notes, 'radial': radial, 'trees': trees}
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
