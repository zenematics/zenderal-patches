"""Plan where `Zenderal - Enemy Density` places its enemy groups in Vyn. Writes `enemy-groups.json` (committed;
02-build-groups.py turns it into placed refs). Deterministic: the same inputs give the same plan.

Curator's brief (2026-10-24): more enemies where it makes sense, to give the player more combat while exploring,
keeping Enderal's themes; IN ADDITION to every existing creature (nothing is removed, moved or replaced):
  * Fogville: goblins and Arps, drastically more;
  * Whisperwood: hordes of weak undead, drastically more, away from quest spots;
  * Powder Desert, Crystal Forest, Frostcliff Mountains, Thalgard, Goldenforst, Western Cliff: groups built
    from the creatures Enderal itself places there, at that region's level band.
Every group is made of base NPCs Enderal already places in that region (or Zenderal - Goblins' goblins), so
nothing new is invented: the EditorID's `_NNE_` prefix is the creature's level.
No Mihail skeletons (02-build-groups.py refuses any base on mihailancientskeletons.esp's race or won by that
plugin): the first two builds crashed twice in the Whisperwood hordes, both times on a Mihail-race skeleton while
IED attached its weapon (2026-10-24). The hordes are also smaller and more spread out (5-8 instead of 8-14), so
fewer actors load together. arch-docs/patches/EnemyDensity.md has the crash logs.

Reading, navmesh and clearance rules are Zenderal - Goblins' (src/Goblins/tools/02-plan-packs.py, imported);
what differs:
  * a site is any walkable navmesh triangle in a cell whose header lists the region (no wild-animal anchor);
  * quest spots: no site within QUEST_CLEAR of any placed ref whose base EditorID names a quest (MQ/NQ/FS..),
    a trigger box or a scene trigger, or of any persistent placed NPC (quest aliases need persistent refs);
  * no site within GOBLIN_CLEAR of a Zenderal - Goblins pack (goblin-packs.json);
  * each region has its own site spacing, target and group table.

Usage:  python 01-plan-groups.py <all dir> [<cache.pickle>]
"""
import collections
import importlib.util
import json
import math
import os
import pickle
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
_spec = importlib.util.spec_from_file_location('goblins_plan', os.path.join(REPO, 'src', 'Goblins', 'tools', '02-plan-packs.py'))
G = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(G)                      # reads sys.argv[1] (<all dir>) like this script

CACHE = sys.argv[2] if len(sys.argv) > 2 else None
OUT = os.path.join(HERE, 'enemy-groups.json')
GOBLIN_PLAN = os.path.join(REPO, 'src', 'Goblins', 'tools', 'goblin-packs.json')
OWN = 'Zenderal - Enemy Density.esp'
SEED = 20261024

QUEST_CLEAR = 3000
GOBLIN_CLEAR = 3500
OTHER_SITE_CLEAR = 3000          # between sites of different regions
CLEAR_NPC = 1200                 # an existing creature: our group must not merge into it
QUEST_EDID = re.compile(r'(^|_)(MQ|NQ|FS_?NQ|FS_?MQ|FSNQ|SQ|CQ)\d|Trigger|TGBX|TravelBox|Scene|Quest', re.I)
HARD_EXCLUDE = {                 # never, whatever the target region (Goblins' list minus the regions we target)
    '069550:Skyrim.esm': 'Isle of Kor', '075801:Skyrim.esm': 'Isle of Kor',
    '0AEB92:Skyrim.esm': 'tropical idyll', '01B860:Skyrim.esm': 'intro region',
    '0CE136:Skyrim.esm': 'temple region', '137F94:Skyrim.esm': 'star city', '003ED7:Skyrim.esm': 'star city',
    '10A876:Skyrim.esm': 'Ark', '139A24:Skyrim.esm': 'Ark', '06E2BA:Skyrim.esm': 'Ark',
    '139A22:Skyrim.esm': 'Ark', '139A20:Skyrim.esm': 'Ark', '139A23:Skyrim.esm': 'Ark',
}

# Group tables. A slot is (EditorIDs to draw from, (min, max) count); 'fill' tops the group up to its size.
# 'GOB' is Zenderal - Goblins' pack recipe (its NPCs carry the 3-day respawn script).
ARP = (['_17E_Arp01_Range1500', '_17E_Arp02_Range1500', '_17E_Arp03_Range1500', '_17E_Arp03SteelSword_Range2000'])
REGIONS = [
    dict(name='Fogville', regions=['10A875:Skyrim.esm'], target=34, spacing=3500, groups=[
        dict(kind='goblin pack', weight=6, size=(5, 8), radius=450, recipe='GOB'),
        dict(kind='Arp camp', weight=4, size=(5, 7), radius=450, slots=[
            (['_17E_Arp03Scheutze_Range1500', '_17E_Arp03Scheutze_Range2000'], (1, 2)),
            (['_18E_ArpSchamane_Aggressive'], (0, 1))], fill=ARP),
    ]),
    dict(name='Whisperwood', regions=['00703D:Skyrim.esm'], target=34, spacing=2800, groups=[
        dict(kind='undead horde', weight=1, size=(5, 8), radius=550, spacing=110, slots=[
            (['_20E_LostOne01Bow_Range1200', '_20E_LostOne01Bow_Range1500'], (1, 2)),
            (['_14E_LostOneMage_Range1200'], (0, 1))],
            fill=['_08E_LostOne_Range1200', '_14E_LostOne_Range1200', '_16E_LostOneBlackVer1_Range1200',
                  '_08E_LostOne_Range1200', '_20E_Skelett_Range1500']),
    ]),
    dict(name='Powder Desert', regions=['139C4D:Skyrim.esm', '09A9BF:Skyrim.esm', '043C5D:Skyrim.esm'],
         target=30, spacing=5500, groups=[
        dict(kind='marauder camp', weight=3, size=(4, 6), radius=450, slots=[
            (['_30E_BanditDessert02Ranged_Aggressive', '_30E_BanditDessert07Ranged_Aggressive'], (1, 2))],
            fill=['_30E_BanditDessert01_Aggressive', '_30E_BanditDessert03_Aggressive']),
        dict(kind='Sere Lost Ones', weight=3, size=(6, 10), radius=600, spacing=100, slots=[
            (['_30E_LostOneMageDesert_Range1200'], (0, 1))],
            fill=['_30E_LostOneDesert01', '_30E_LostOneDesert04', '_30E_LostOneDesert05', '_30E_LostOneDesert06',
                  '_30E_LostOneDesert02_Range1200', '_30E_LostOneDesert03_Range1200']),
        dict(kind='lion pride', weight=2, size=(3, 4), radius=450, slots=[(['_31E_Lion'], (1, 1))],
             fill=['_25E_Lioness']),
        dict(kind='pus beetle swarm', weight=2, size=(4, 6), radius=400, fill=['_31E_Pusbug', '_31E_PusbugSmall']),
        dict(kind='panthers', weight=1, size=(2, 3), radius=400, fill=['_27E_Panther']),
    ]),
    dict(name='Crystal Forest', regions=['12ECF1:Skyrim.esm'], target=14, spacing=4000, groups=[
        dict(kind='crystal specters', weight=3, size=(3, 5), radius=450, slots=[
            (['_30E_AnomalitaetGrouped'], (1, 2))], fill=['_20E_Kristallgeist', '_30E_Kristallgeist']),
        dict(kind='elemental wolves', weight=2, size=(3, 4), radius=400, fill=['_26E_ElementalWolf', '_30E_ElementalWolf']),
        dict(kind='crystal elementals', weight=1, size=(2, 2), radius=400, fill=['_20E_CrystallElemental']),
    ]),
    dict(name='Frostcliff Mountains', regions=['0823E4:Skyrim.esm'], target=40, spacing=6000, groups=[
        dict(kind='snow wolf pack', weight=4, size=(4, 6), radius=450, slots=[(['_23E_Schneewolf'], (0, 2))],
             fill=['_35E_Schneewolf']),
        dict(kind='Lost One patrol', weight=3, size=(4, 6), radius=500, slots=[
            (['_25E_SkelettBogen_Range1500', '_28E_LostOne01Bow_Range1500'], (1, 2)),
            (['_26E_LostOne01_Range1200'], (0, 1))],
            fill=['_25E_Skelett02_Aggressive', '_25E_Skelett03_Aggressive', '_26E_LostOne01_Range1200']),
        dict(kind='ice bears', weight=2, size=(1, 2), radius=400, fill=['_45E_Eisbaer', '_29E_Eisbaer']),
        dict(kind='glacier hounds', weight=1, size=(2, 2), radius=400, fill=['_55E_Gletscherhund']),
    ]),
    dict(name='Thalgard', regions=['0022AB:Skyrim.esm'], target=16, spacing=5000, groups=[
        dict(kind='Sunborn patrol', weight=3, size=(3, 5), radius=450, slots=[
            (['_45E_Sunborn01Mage'], (1, 1)), (['_45E_SunbornSchuetze01', '_45E_SunbornSchuetze02'], (1, 1))],
            fill=['_45E_Sunborn02', '_45E_Sunborn03', '_45E_Sunborn04']),
        dict(kind='restless spirits', weight=2, size=(3, 4), radius=450, slots=[(['_43E_ElementGhost_Undead'], (0, 1))],
             fill=['_40E_MoenchGeist01', '_40E_MoenchGeist02']),
    ]),
    dict(name='Goldenforst', regions=['035CCA:Skyrim.esm'], target=14, spacing=5000, groups=[
        dict(kind='Vatyr warband', weight=1, size=(4, 6), radius=500, fill=['_30E_Vatyr01', '_30E_Vatyr02', '_30E_Vatyr03']),
    ]),
    dict(name='Western Cliff', regions=['048089:Skyrim.esm'], target=16, spacing=5000, groups=[
        dict(kind='Lost One graves', weight=3, size=(4, 6), radius=450, slots=[(['_20E_LostOne01Bow_Range1200'], (1, 2))],
             fill=['_08E_LostOne_Range1200', '_14E_LostOne_Range1200', '_16E_LostOneBlackVer1_Range1200']),
        dict(kind='moss crawler nest', weight=2, size=(3, 4), radius=400, slots=[(['_08E_Mooskrabbler'], (1, 1))],
             fill=['_05E_Mooskrabbler', '_03E_JungerMooskrabbler']),
    ]),
]


def goblin_roles(rng, n):
    """Zenderal - Goblins' pack recipe (02-plan-packs.py): ours and Mihail's mixed, plus 0-2 Tamed Durzogs."""
    def pick(ours, mihails):
        return rng.choice(mihails) if rng.random() < G.MIHAIL_SHARE else rng.choice(ours)
    roles = [pick(['Archer'], ['MArcher']) for _ in range(rng.randint(1, 2))]
    if rng.random() < 0.35:
        roles.append(pick(['Shaman'], ['MShaman']))
    if n >= 7:
        roles.append(pick(['Chief'], ['MWarlord']))
    while len(roles) < n:
        roles.append(pick(['Goblin', 'Scout'], ['MGoblin', 'MSkirmisher', 'MBerserker']))
    rng.shuffle(roles)
    r, acc = rng.random(), 0.0
    for d, p in G.DURZOGS:
        acc += p
        if r < acc:
            break
    return ['GOB:' + x for x in roles[:n] + ['Durzog'] * d]


def roles_for(rng, g, n):
    if g.get('recipe') == 'GOB':
        return goblin_roles(rng, n)
    roles = []
    for edids, (lo, hi) in g.get('slots', []):
        roles += [rng.choice(edids) for _ in range(rng.randint(lo, hi))]
    while len(roles) < n:
        roles.append(rng.choice(g['fill']))
    rng.shuffle(roles)
    return roles[:max(n, len(roles))]


def main():
    if CACHE and os.path.isfile(CACHE):
        cells, refs, navs, npc_race, races, edids = pickle.load(open(CACHE, 'rb'))
    else:
        cells, refs, navs, npc_race, races, edids = G.read_all()
        if CACHE:
            pickle.dump((cells, refs, navs, npc_race, races, edids), open(CACHE, 'wb'))
    live = [r for r in refs.values() if not r.get('deleted') and 'pos' in r and not r['fk'].endswith(OWN)]
    by_grid = {c['grid']: c for c in cells.values() if c.get('grid') is not None}
    print(f'{len(cells)} cells, {len(live)} live refs, {len(navs)} navmeshes')

    # NPC/any base EditorIDs, from file names: '<EditorID> - <hex>_<plugin>.yaml'
    base_edid = dict(edids)
    for _, root in G.sources():
        for d in ('Npcs', 'Activators', 'Statics', 'MoveableStatics', 'Furniture', 'Containers'):
            p = os.path.join(root, d)
            if os.path.isdir(p):
                for f in os.listdir(p):
                    m = G.NAME.match(f)
                    if m:
                        base_edid[f'{m.group(2)}:{m.group(3)}'] = m.group(1)

    def race_of(r):
        return races.get(npc_race.get(r.get('base')), '')

    npcs = [r for r in live if r['kind'] == 'PlacedNpc']
    humans = G.Grid([r['pos'] for r in npcs if race_of(r) in G.HUMAN])
    farm = G.Grid([r['pos'] for r in npcs if race_of(r) in G.FARM])
    any_npc = G.Grid([r['pos'] for r in npcs if 'SkelettDead' not in base_edid.get(r.get('base'), '')])
    base_plugins = {'Skyrim.esm', 'Enderal - Forgotten Stories.esm'}
    mod_objs = G.Grid([r['pos'] for r in live if r['kind'] == 'PlacedObject' and r['plugin'] not in base_plugins])
    markers = [r for r in live if r.get('base') == '000010:Skyrim.esm' and r.get('marker_name')]
    falls = G.Grid([r['pos'] for r in live if G.FALLS.search(edids.get(r.get('base'), ''))])
    quest = [r for r in live if QUEST_EDID.search(base_edid.get(r.get('base'), ''))
             or (r['kind'] == 'PlacedNpc' and r['cell'] == 'TopCell')]
    quest_grid = G.Grid([r['pos'] for r in quest])
    goblins = json.load(open(GOBLIN_PLAN, encoding='utf-8'))
    goblin_grid = G.Grid([m[:3] for s in goblins for m in s['members']])
    pos = {r['fk']: r['pos'] for r in live}
    mq01 = [(pos[fk], radius) for fk, (_, radius) in G.QUEST_CLEAR.items()]
    print(f'{len(quest)} quest/trigger/persistent-NPC refs kept clear ({QUEST_CLEAR}), {len(goblins)} goblin packs')

    def water_z(g):
        c = by_grid.get(g)
        w = c.get('water') if c else None
        return 0.0 if w is None or w > 1e30 else w

    tris, roads, water = [], [], []
    for nv in navs.values():
        if nv['deleted'] or not nv['verts']:
            continue
        for idx, flags in nv['tris']:
            cen, flat, _ = G.tri_info(nv['verts'], idx)
            if 'Preferred' in flags:
                roads.append(cen)
            elif 'Water' in flags:
                water.append(cen)
            elif 'Door' not in flags:
                tris.append((cen, flat))
    roads, water = G.Grid(roads), G.Grid(water)
    tri_grid = collections.defaultdict(list)
    for t in tris:
        tri_grid[(int(t[0][0] // 512), int(t[0][1] // 512))].append(t)

    def members_around(c, want, radius, spacing):
        out, cand = [], []
        k = int(math.ceil(radius / 512))
        for i in range(-k, k + 1):
            for j in range(-k, k + 1):
                cand += tri_grid.get((int(c[0] // 512) + i, int(c[1] // 512) + j), [])
        cand.sort(key=lambda t: (t[0][0] - c[0]) ** 2 + (t[0][1] - c[1]) ** 2)
        for cen, flat in cand:
            if flat < G.MEMBER_FLAT or math.dist(cen[:2], c[:2]) > radius or abs(cen[2] - c[2]) > 200:
                continue
            if cen[2] < water_z(G.cell_of(*cen[:2])) + 40 or roads.near(cen[0], cen[1], 300):
                continue
            if water.near(cen[0], cen[1], G.CLEAR_WATER[1]) or falls.near(cen[0], cen[1], G.CLEAR_FALLS[1]):
                continue
            if mod_objs.near(cen[0], cen[1], 200):
                continue
            if all(math.dist(cen[:2], o[:2]) >= spacing for o in out):
                out.append(cen)
            if len(out) == want:
                return out
        return None

    def marker_clear(x, y):
        for m in markers:
            r = G.MARKER_CLEAR.get(m.get('marker_type'))
            if r and (m['pos'][0] - x) ** 2 + (m['pos'][1] - y) ** 2 < r * r:
                return False
        return True

    rng = random.Random(SEED)
    sites, all_sites = [], G.Grid([])
    for reg in REGIONS:
        want = set(reg['regions'])
        grids = {g for g, c in by_grid.items() if want & set(c['regions']) and not set(c['regions']) & set(HARD_EXCLUDE)}
        cand = [t for g in grids for i in range(8) for j in range(8)
                for t in tri_grid.get((g[0] * 8 + i, g[1] * 8 + j), [])]
        cand.sort(key=lambda t: t[0])
        rng.shuffle(cand)
        own = G.Grid([])
        got = 0
        weights = [g['weight'] for g in reg['groups']]
        for cen, flat in cand:
            if got >= reg['target']:
                break
            x, y, z = cen
            g = G.cell_of(x, y)
            if flat < G.FLAT or z < water_z(g) + 100:
                continue
            if own.near(x, y, reg['spacing']) or all_sites.near(x, y, OTHER_SITE_CLEAR):
                continue
            if any_npc.near(x, y, CLEAR_NPC) or humans.near(x, y, G.CLEAR_HUMAN) or farm.near(x, y, G.CLEAR_FARM):
                continue
            if roads.near(x, y, G.CLEAR_ROAD) or mod_objs.near(x, y, G.CLEAR_MOD_OBJECT):
                continue
            if water.near(x, y, G.CLEAR_WATER[0]) or falls.near(x, y, G.CLEAR_FALLS[0]):
                continue
            if quest_grid.near(x, y, QUEST_CLEAR) or goblin_grid.near(x, y, GOBLIN_CLEAR):
                continue
            if any(math.dist((x, y), p[:2]) < r for p, r in mq01) or not marker_clear(x, y):
                continue
            grp = rng.choices(reg['groups'], weights)[0]
            n = rng.randint(*grp['size'])
            roles = roles_for(rng, grp, n)
            pts = members_around(cen, len(roles), grp['radius'], grp.get('spacing', G.MEMBER_SPACING))
            if not pts:
                continue
            near = min(markers, key=lambda m: math.dist(m['pos'][:2], (x, y)))
            sites.append(dict(region=reg['name'], kind=grp['kind'], center=[round(v, 1) for v in cen], cell=list(g),
                              cell_fk=by_grid[g]['fk'], near=near['marker_name'],
                              near_dist=round(math.dist(near['pos'][:2], (x, y))), roles=roles,
                              members=[[round(v, 1) for v in p] + [round(rng.uniform(0, 2 * math.pi), 4)] for p in pts]))
            own.b[(int(x // 4096), int(y // 4096))].append(cen)
            all_sites.b[(int(x // 4096), int(y // 4096))].append(cen)
            got += 1
        n = sum(len(s['members']) for s in sites if s['region'] == reg['name'])
        print(f"{reg['name']:22} {got:3}/{reg['target']} groups, {n:4} enemies, {len(grids)} cells")
    # carry the ref FormIDs 02 gave each surviving site, so enemies in existing saves keep their refs
    if os.path.isfile(OUT):
        old = {tuple(s['center']): s.get('refs', []) for s in json.load(open(OUT, encoding='utf-8'))}
        for s in sites:
            r = old.get(tuple(s['center']), [])
            if len(r) == len(s['members']):
                s['refs'] = r
    with open(OUT, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(sites, fh, indent=1)
        fh.write('\n')
    print(f'{len(sites)} groups, {sum(len(s["members"]) for s in sites)} enemies -> {OUT}')
    for k, v in collections.Counter((s['region'], s['kind']) for s in sites).most_common():
        print(f'  {v:3}  {k[0]}: {k[1]}')


if __name__ == '__main__':
    main()
