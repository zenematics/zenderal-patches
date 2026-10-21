"""Plan where `Zenderal - Goblins` places its goblin packs in Vyn. Writes `goblin-packs.json` (committed;
03-build-packs.py turns it into placed refs). Deterministic: the same inputs give the same plan.

Curator's brief (2026-10-21): large packs of weak goblins scattered over Vyn's forests and mountains
"anywhere it makes sense", around Riverville and Ark's surroundings too, never in the Crystal Forest,
and IN ADDITION to every existing creature (nothing is removed, moved or replaced).

Inputs, in load order (a later source wins a record):
  reference/base/Skyrim, reference/base/EnderalFS   base Enderal + Forgotten Stories (spriggit-decompile-reference)
  <all>/<plugin>/                                   every enabled Ultra plugin, serialized by
                                                    src/UnresolvedRefsCleanup/tools/00a-serialize-all.py
From them: every Vyn cell's winning header (regions, water), the winning version of every navmesh,
every placed NPC/object (last override wins; deleted ones dropped) and the map markers.

How a site is chosen:
  * candidates are navmesh triangles: walkable by construction and at the right height, so a goblin
    never stands inside a rock or a house. Not Water/Door/Preferred (= roads), slope normal z >= 0.9,
    above the cell's water;
  * "makes sense" = near wild animals Enderal itself placed (wolves, deer, foxes, bears, sabre cats,
    trolls, spiders, hares, goats...), 1200-4000 units from such an anchor, but >= 1500 from any placed
    NPC so a pack is its own camp and does not merge with the animals;
  * away from people: >= 3500 units from any human/elf NPC, >= 2500 from farm animals, and clear of map
    markers of settlements (City 7000, Town/Settlement 5000, Farm/mills/stable/docks/lighthouse/fort/
    camp/stronghold 3000, Shack/Shrine/Altar 2000);
  * >= 700 from road triangles, >= 350 from any object a MOD added (its navmesh may not know it);
  * off river banks and waterfall edges (a pack stood on the lip of a waterfall, 2026-10-21): site/member
    >= 600/250 from navmesh Water triangles and >= 1200/600 from placed objects whose base EditorID says
    waterfall/river/rapids/stream/cascade/splash/creek/wet (Statics, MoveableStatics, Activators and
    SoundMarkers such as AMBWaterfallLarge2DLP, of every source). The Dual Towers river in cell -15,-3 had
    no Water navmesh triangles and only FXSplash/FXCreek/wet rocks/waterfall sound markers nearby;
  * excluded regions: Crystal Forest (KristallwaldRegion, plus one cell of margin), the deserts, Isle of
    Kor, the tropical idyll, the intro/temple/star-city regions, Ark (CapitalCity*) and Fogville (Nebelhaim);
  * sites >= 7000 units apart, at most TARGET sites; pack of 5-8 goblins on triangles within 450 units, >= 90
    apart, mixing our goblins and Mihail's (01b-build-mihail.py; 75% Mihail's), plus 0-2 Tamed Durzogs (50/30/20%).

Usage:  python 02-plan-packs.py <all dir> [<cache.pickle>]
"""
import collections
import glob
import json
import math
import os
import pickle
import random
import re
import sys

ALL = sys.argv[1]
CACHE = sys.argv[2] if len(sys.argv) > 2 else None
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
WS = 'Vyn - 001D3C_Skyrim.esm'
PLUGINS = os.path.join('E:/Zenderal', 'profiles', 'Ultra', 'plugins.txt')
OUT = os.path.join(HERE, 'goblin-packs.json')
OWN = 'Zenderal - Goblins.esp'

TARGET = 80
SEED = 20261021
PACK = (5, 8)                     # goblins per pack
DURZOGS = ((0, 0.5), (1, 0.3), (2, 0.2))   # extra Tamed Durzogs per pack: count, chance
MIHAIL_SHARE = 0.75                # curator 2026-10-21: more of Mihail's goblins in the mix
SITE_SPACING = 7000
ANCHOR_RANGE = (1200, 4000)
CLEAR_NPC = 1500
CLEAR_HUMAN = 3500
CLEAR_FARM = 2500
CLEAR_ROAD = 700
CLEAR_WATER = (600, 250)          # site, member: from navmesh Water triangles (rivers, lakes, coast)
CLEAR_FALLS = (1200, 600)         # site, member: from placed waterfall/river/rapids objects
NAME = re.compile(r'^(.+) - ([0-9A-F]{6})_(.+)\.yaml$')
FALLS = re.compile(r'waterfall|wasserfall|river|fluss|rapid|stream|cascade|fxwater|wfall|splash|creek|wet', re.I)
CLEAR_MOD_OBJECT = 350
PACK_RADIUS = 450
MEMBER_SPACING = 90
FLAT = 0.9
MEMBER_FLAT = 0.75
MARKER_CLEAR = {'City': 7000, 'Town': 5000, 'Settlement': 5000, 'WhiterunCapitol': 7000, 'WindhelmCastle': 7000,
                'Farm': 3000, 'WheatMill': 3000, 'WoodMill': 3000, 'Stable': 3000, 'Docks': 3000,
                'Lighthouse': 3000, 'Fort': 3000, 'Camp': 3000, 'OrcStronghold': 3000,
                'Shack': 2000, 'Shrine': 2000, 'Altar': 2000}
CRYSTAL = '12ECF1:Skyrim.esm'
EXCLUDED_REGIONS = {
    CRYSTAL: 'Crystal Forest',
    '139C4D:Skyrim.esm': 'desert', '09A9BF:Skyrim.esm': 'desert sandstorm', '043C5D:Skyrim.esm': 'desert',
    '069550:Skyrim.esm': 'Isle of Kor', '075801:Skyrim.esm': 'Isle of Kor',
    '0AEB92:Skyrim.esm': 'tropical idyll', '01B860:Skyrim.esm': 'intro region',
    '0CE136:Skyrim.esm': 'temple region', '137F94:Skyrim.esm': 'star city', '003ED7:Skyrim.esm': 'star city',
    '10A876:Skyrim.esm': 'Ark', '139A24:Skyrim.esm': 'Ark', '06E2BA:Skyrim.esm': 'Ark',
    '139A22:Skyrim.esm': 'Ark', '139A20:Skyrim.esm': 'Ark', '139A23:Skyrim.esm': 'Ark',
    '10A875:Skyrim.esm': 'Fogville',
}
WILD = {'WolfRace', 'WolfRaceLarge', 'WolfRaceSmall', 'WolfHoheRace', 'DeerRace', 'DeerRaceSmall', 'ElkRace',
        'FoxRace', 'HareRace', 'SabreCatRace', 'SabreCatSnowyRace', 'BearBrownRace', 'BearBlackRace',
        'BearSnowRace', 'TrollRace', 'TrollFrostRace', 'FrostbiteSpiderRace', 'FrostbiteSpiderRaceLarge',
        'FrostbiteSpiderRaceGiant', 'GoatRace', 'SkeeverRace', 'SkeeverRaceLarge', 'SprigganRace'}
HUMAN = {'NordRace', 'ImperialRace', 'BretonRace', 'RedguardRace', 'HighElfRace', 'WoodElfRace', 'DarkElfRace',
         'OrcRace', 'KhajiitRace', 'ArgonianRace', 'ElderRace', 'NordRaceChild', 'ImperialRaceChild',
         'BretonRaceChild', 'RedguardRaceChild', 'HighElfRaceChild', 'WoodElfRaceChild', 'DarkElfRaceChild'}
FARM = {'ChickenRace', 'ChickenRaceLarge', 'CowRace', 'GoatDomesticsRace', 'PigRace', 'HorseRace', 'DogRace'}


# ---------------------------------------------------------------------------------------------------
# reading
def sources():
    plugins = [ln[1:].strip() for ln in open(PLUGINS, encoding='utf-8') if ln.startswith('*')]
    out = [('Skyrim.esm', os.path.join(REPO, 'reference', 'base', 'Skyrim')),
           ('Enderal - Forgotten Stories.esm', os.path.join(REPO, 'reference', 'base', 'EnderalFS'))]
    for p in plugins:
        if p == OWN:
            continue
        d = os.path.join(ALL, re.sub(r'[^A-Za-z0-9]', '', p))
        if os.path.isdir(d):
            out.append((p, d))
    return out


ITEM = re.compile(r'^(\s*)- MutagenObjectType: (PlacedNpc|PlacedObject)\s*$')


def parse_refs(lines, cell, plugin, refs):
    """Every placed NPC/object block: FormKey, Base, Position, deleted, map marker name/type."""
    i = 0
    n = len(lines)
    while i < n:
        m = ITEM.match(lines[i])
        if not m:
            i += 1
            continue
        ind = len(m.group(1)) + 2
        kind = m.group(2)
        j = i + 1
        d = {'kind': kind, 'cell': cell, 'plugin': plugin}
        while j < n and (lines[j].startswith(' ' * ind) or not lines[j].strip()):
            s = lines[j][ind:]
            if s.startswith('FormKey: '):
                d['fk'] = s[9:].strip()
            elif s.startswith('Base: '):
                d['base'] = s[6:].strip()
            elif s.startswith('  Position: ') and 'pos' not in d:
                d['pos'] = tuple(float(x) for x in s[12:].split(','))
            elif s.startswith('MajorRecordFlagsRaw: '):
                d['deleted'] = bool(int(s[21:]) & 0x20)
            elif s == 'MapMarker:':
                d['marker'] = True
            elif d.get('marker') and s.startswith('    - Language: English') and 'marker_name' not in d:
                d['marker_name'] = lines[j + 1].split('String: ', 1)[1].strip()
            elif d.get('marker') and s.startswith('    Value: ') and 'marker_name' not in d:
                d['marker_name'] = s[11:].strip()            # non-localized plugin
            elif s.startswith('  Type: ') and 'marker_name' in d:
                d['marker_type'] = s[8:].strip()
            j += 1
        if 'fk' in d:
            refs[d['fk']] = d
        i = j


def parse_navmeshes(lines, cell, navs):
    i = 0
    n = len(lines)
    while i < n:
        if lines[i] != 'NavigationMeshes:':
            i += 1
            continue
        i += 1
        cur = None
        while i < n and (lines[i].startswith(' ') or lines[i].startswith('- ')):
            s = lines[i]
            if s.startswith('- FormKey: '):
                cur = {'fk': s[11:].strip(), 'cell': cell, 'verts': [], 'tris': [], 'deleted': False}
                navs[cur['fk']] = cur
            elif cur is not None and s.startswith('  MajorRecordFlagsRaw: '):
                cur['deleted'] = bool(int(s[23:]) & 0x20)
            elif cur is not None and s == '    Vertices:':
                i += 1
                while i < n and lines[i].startswith('    - ') and 'Vertices' not in lines[i]:
                    cur['verts'].append(tuple(float(x) for x in lines[i][6:].split(',')))
                    i += 1
                continue
            elif cur is not None and s.startswith('    - Vertices: '):
                tri = [tuple(int(x) for x in s[16:].split(',')), set()]
                i += 1
                while i < n and lines[i].startswith('      '):
                    if lines[i].startswith('      - '):
                        tri[1].add(lines[i][8:].strip())
                    i += 1
                cur['tris'].append(tri)
                continue
            i += 1
        return


def header(lines):
    h = {'regions': [], 'water': None, 'grid': None}
    i = 0
    while i < len(lines):
        s = lines[i]
        if re.match(r'^(Temporary|Persistent|NavigationMeshes|Landscape|MajorFlags):', s):
            break
        if s.startswith('  Point: '):
            h['grid'] = tuple(int(x) for x in s[9:].split(','))
        elif s.startswith('WaterHeight: '):
            h['water'] = float(s[13:])
        elif s == 'Regions:':
            i += 1
            while i < len(lines) and lines[i].startswith('- '):
                h['regions'].append(lines[i][2:].strip())
                i += 1
            continue
        i += 1
    if h['grid'] is None and 'Grid:' in lines[:12]:
        h['grid'] = (0, 0)
    return h


def read_all():
    cells, refs, navs, npc_race, races, edids = {}, {}, {}, {}, {}, {}
    for plugin, root in sources():
        for d in ('Statics', 'MoveableStatics', 'Activators', 'SoundMarkers'):
            for f in glob.glob(os.path.join(root, d, '*.yaml')):
                m = NAME.match(os.path.basename(f))     # '<EditorID> - <hex>_<plugin>.yaml'
                if m:
                    edids[f'{m.group(2)}:{m.group(3)}'] = m.group(1)
        for d in ('Races',):
            for f in glob.glob(os.path.join(root, d, '*.yaml')):
                t = open(f, encoding='utf-8').read()
                races[re.search(r'^FormKey: (\S+)', t, re.M).group(1)] = re.search(r'^EditorID: (\S+)', t, re.M).group(1)
        for f in glob.glob(os.path.join(root, 'Npcs', '*.yaml')):
            t = open(f, encoding='utf-8').read()
            m = re.search(r'^Race: (\S+)', t, re.M)
            npc_race[re.search(r'^FormKey: (\S+)', t, re.M).group(1)] = m.group(1) if m else None
        wsd = os.path.join(root, 'Worldspaces', WS)
        if not os.path.isdir(wsd):
            continue
        n = 0
        for dirpath, _, files in os.walk(wsd):
            if 'RecordData.yaml' not in files:
                continue
            lines = open(os.path.join(dirpath, 'RecordData.yaml'), encoding='utf-8').read().splitlines()
            if dirpath == wsd:
                parse_refs(lines, 'TopCell', plugin, refs)
                continue
            fk = lines[0].split('FormKey: ', 1)[1].strip()
            h = header(lines)
            h.update(plugin=plugin, path=dirpath, fk=fk)
            cells[fk] = h if h['grid'] is not None else {**cells.get(fk, {}), **{k: v for k, v in h.items() if v}}
            parse_refs(lines, fk, plugin, refs)
            parse_navmeshes(lines, fk, navs)
            n += 1
        print(f'  {n:6} cells  {plugin}', flush=True)
    return cells, refs, navs, npc_race, races, edids


# ---------------------------------------------------------------------------------------------------
# geometry
class Grid:
    """Points bucketed by 4096-unit squares for radius queries."""

    def __init__(self, pts):
        self.b = collections.defaultdict(list)
        for p in pts:
            self.b[(int(p[0] // 4096), int(p[1] // 4096))].append(p)

    def near(self, x, y, r):
        k = int(math.ceil(r / 4096))
        cx, cy = int(x // 4096), int(y // 4096)
        r2 = r * r
        for i in range(cx - k, cx + k + 1):
            for j in range(cy - k, cy + k + 1):
                for p in self.b.get((i, j), ()):
                    if (p[0] - x) ** 2 + (p[1] - y) ** 2 < r2:
                        return p
        return None


def tri_info(verts, idx):
    a, b, c = (verts[i] for i in idx)
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    ln = math.sqrt(nx * nx + ny * ny + nz * nz) or 1
    cen = ((a[0] + b[0] + c[0]) / 3, (a[1] + b[1] + c[1]) / 3, (a[2] + b[2] + c[2]) / 3)
    return cen, abs(nz) / ln, ln / 2


def cell_of(x, y):
    return int(x // 4096), int(y // 4096)


# ---------------------------------------------------------------------------------------------------
def main():
    if CACHE and os.path.isfile(CACHE):
        cells, refs, navs, npc_race, races, edids = pickle.load(open(CACHE, 'rb'))
    else:
        cells, refs, navs, npc_race, races, edids = read_all()
        if CACHE:
            pickle.dump((cells, refs, navs, npc_race, races, edids), open(CACHE, 'wb'))
    live = [r for r in refs.values() if not r.get('deleted') and 'pos' in r]
    by_grid = {c['grid']: c for c in cells.values() if c.get('grid') is not None}
    print(f'{len(cells)} cells, {len(live)} live refs, {len(navs)} navmeshes')

    def race_of(r):
        return races.get(npc_race.get(r.get('base')), '')

    npcs = [r for r in live if r['kind'] == 'PlacedNpc']
    anchors = [r for r in npcs if race_of(r) in WILD]
    humans = Grid([r['pos'] for r in npcs if race_of(r) in HUMAN])
    farm = Grid([r['pos'] for r in npcs if race_of(r) in FARM])
    any_npc = Grid([r['pos'] for r in npcs])
    base_plugins = {'Skyrim.esm', 'Enderal - Forgotten Stories.esm'}
    mod_objs = Grid([r['pos'] for r in live if r['kind'] == 'PlacedObject' and r['plugin'] not in base_plugins
                     and not r['fk'].endswith(OWN)])
    markers = [r for r in live if r.get('base') == '000010:Skyrim.esm' and r.get('marker_name')]
    falls = [r['pos'] for r in live if FALLS.search(edids.get(r.get('base'), ''))]
    falls = Grid(falls)
    print(f'{sum(len(v) for v in falls.b.values())} waterfall/river objects')
    print(f'{len(anchors)} wild-animal anchors, {len(markers)} map markers')

    crystal = {c['grid'] for c in cells.values() if c.get('grid') is not None and CRYSTAL in c['regions']}
    crystal_margin = {(x + i, y + j) for x, y in crystal for i in (-1, 0, 1) for j in (-1, 0, 1)}

    def cell_ok(g):
        c = by_grid.get(g)
        if c is None or g in crystal_margin:
            return False
        return not any(r in EXCLUDED_REGIONS for r in c['regions'])

    def water_z(g):
        c = by_grid.get(g)
        w = c.get('water') if c else None
        return 0.0 if w is None or w > 1e30 else w

    # walkable triangles of the winning navmeshes
    tris = []
    roads = []
    water = []
    for nv in navs.values():
        if nv['deleted'] or not nv['verts']:
            continue
        for idx, flags in nv['tris']:
            cen, flat, area = tri_info(nv['verts'], idx)
            if 'Preferred' in flags:
                roads.append(cen)
                continue
            if 'Water' in flags:
                water.append(cen)
                continue
            if 'Door' in flags:
                continue
            tris.append((cen, flat, nv['fk']))
    roads = Grid(roads)
    water = Grid(water)
    tri_grid = collections.defaultdict(list)
    for t in tris:
        tri_grid[(int(t[0][0] // 512), int(t[0][1] // 512))].append(t)
    print(f'{len(tris)} walkable navmesh triangles')

    def members_around(c, want):
        out = []
        cand = []
        for i in range(-1, 2):
            for j in range(-1, 2):
                cand += tri_grid.get((int(c[0] // 512) + i, int(c[1] // 512) + j), [])
        cand.sort(key=lambda t: (t[0][0] - c[0]) ** 2 + (t[0][1] - c[1]) ** 2)
        for cen, flat, _ in cand:
            if flat < MEMBER_FLAT or math.dist(cen[:2], c[:2]) > PACK_RADIUS or abs(cen[2] - c[2]) > 180:
                continue
            if cen[2] < water_z(cell_of(*cen[:2])) + 40 or roads.near(cen[0], cen[1], 300):
                continue
            if water.near(cen[0], cen[1], CLEAR_WATER[1]) or falls.near(cen[0], cen[1], CLEAR_FALLS[1]):
                continue
            if mod_objs.near(cen[0], cen[1], 200):
                continue
            if all(math.dist(cen[:2], o[:2]) >= MEMBER_SPACING for o in out):
                out.append(cen)
            if len(out) == want:
                return out
        return None

    def marker_clear(x, y):
        for m in markers:
            r = MARKER_CLEAR.get(m.get('marker_type'))
            if r and (m['pos'][0] - x) ** 2 + (m['pos'][1] - y) ** 2 < r * r:
                return False
        return True

    rng = random.Random(SEED)
    order = sorted(anchors, key=lambda r: r['fk'])
    rng.shuffle(order)
    sites = []
    site_grid = Grid([])
    for a in order:
        if len(sites) >= TARGET:
            break
        ax, ay, _ = a['pos']
        if not cell_ok(cell_of(ax, ay)) or site_grid.near(ax, ay, SITE_SPACING):
            continue
        cand = []
        r = ANCHOR_RANGE[1]
        for i in range(int((ax - r) // 512), int((ax + r) // 512) + 1):
            for j in range(int((ay - r) // 512), int((ay + r) // 512) + 1):
                cand += tri_grid.get((i, j), [])
        rng.shuffle(cand)
        for cen, flat, nav in cand:
            x, y, z = cen
            d = math.dist((x, y), (ax, ay))
            if not ANCHOR_RANGE[0] <= d <= ANCHOR_RANGE[1] or flat < FLAT:
                continue
            g = cell_of(x, y)
            if not cell_ok(g) or z < water_z(g) + 100:
                continue
            if any_npc.near(x, y, CLEAR_NPC) or humans.near(x, y, CLEAR_HUMAN) or farm.near(x, y, CLEAR_FARM):
                continue
            if roads.near(x, y, CLEAR_ROAD) or mod_objs.near(x, y, CLEAR_MOD_OBJECT) or site_grid.near(x, y, SITE_SPACING):
                continue
            if water.near(x, y, CLEAR_WATER[0]) or falls.near(x, y, CLEAR_FALLS[0]):
                continue
            if not marker_clear(x, y):
                continue
            size = rng.randint(*PACK)
            pts = members_around(cen, size + max(d for d, _ in DURZOGS))   # room for the durzogs
            if not pts:
                continue
            near = min(markers, key=lambda m: math.dist(m['pos'][:2], (x, y)))
            sites.append(dict(center=[round(v, 1) for v in cen], cell=list(g), cell_fk=by_grid[g]['fk'],
                              anchor=a['fk'], anchor_race=race_of(a),
                              near=near['marker_name'], near_type=near.get('marker_type'),
                              near_dist=round(math.dist(near['pos'][:2], (x, y))),
                              size=size,
                              members=[[round(v, 1) for v in p] + [round(rng.uniform(0, 2 * math.pi), 4)] for p in pts]))
            site_grid.b[(int(x // 4096), int(y // 4096))].append(cen)
            break
    rng2 = random.Random(SEED + 1)
    for s in sites:                         # pack composition: ours and Mihail's (01b) mixed, plus durzogs
        n = s.pop('size')
        def pick(ours, mihails):            # Mihail's types win MIHAIL_SHARE of every draw
            return rng2.choice(mihails) if rng2.random() < MIHAIL_SHARE else rng2.choice(ours)
        roles = [pick(['Archer'], ['MArcher']) for _ in range(rng2.randint(1, 2))]
        if rng2.random() < 0.35:
            roles.append(pick(['Shaman'], ['MShaman']))
        if n >= 7:
            roles.append(pick(['Chief'], ['MWarlord']))
        while len(roles) < n:
            roles.append(pick(['Goblin', 'Scout'], ['MGoblin', 'MSkirmisher', 'MBerserker']))
        rng2.shuffle(roles)
        r, acc = rng2.random(), 0.0
        for d, p in DURZOGS:
            acc += p
            if r < acc:
                break
        s['roles'] = roles[:n] + ['Durzog'] * d
        s['members'] = s['members'][:len(s['roles'])]
    total = sum(len(s['members']) for s in sites)
    print('roles: ' + ', '.join(f'{k} {v}' for k, v in collections.Counter(r for s in sites for r in s['roles']).most_common()))
    with open(OUT, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(sites, fh, indent=1)
        fh.write('\n')
    print(f'{len(sites)} sites, {total} goblins -> {OUT}')
    for s in sorted(sites, key=lambda s: s['near']):
        print(f'  {len(s["members"])}  {s["near"]} ({s["near_type"]}, {s["near_dist"]} units)  cell {s["cell"]}  near {s["anchor_race"]}')


if __name__ == '__main__':
    main()
