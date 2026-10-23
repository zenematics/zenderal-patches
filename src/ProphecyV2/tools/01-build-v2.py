"""Prophecy v2 - the physical sanctum. Builds src/ProphecyV2/ from the v1 build (src/Prophecy/) plus a walk-in
constellation space made of Enderal's own meditation (Akropolis) pieces.

v1 and v2 ship as two archives of ONE plugin, Zenderal - Prophecy.esp: every shared record (perks, spells, effects,
globals, the power) keeps its v1 FormID, so a save can switch between them. v2's own records use 0xC00+, out of v1's way.

Run src/Prophecy/tools/01-build-trees.py FIRST - this copies its output. Then compile src/ProphecyV2/Scripts/source.

What the sanctum is (all derived from reference/base/Skyrim/Worldspaces/Akropolis, measured 2026-10-21):
  * the environment = every Akropolis reference except Enderal's own stars, lines, perk nodes, roots, triggers and
    markers (213 refs: platforms, dome, pillars, levitating ruins, candles, plants, the three themed lights),
    copied at their own coordinates into one interior cell;
  * a star = _00E_Class_MemoryStar 05BD42 (AkropolisPerk.nif, unlock event "PlayAnim02");
  * a line = _00E_Class_PerkLine 0A8263 (vanilla interface/intperkline01.nif, "Unlock"/"Unlocked"). Fitted against
    all 243 of Enderal's lines: it runs along the ref's local +Y, rotation matrix = Rx(-rx)*Ry(-ry)*Rz(-rz),
    origin 4.1 units past the start star, scale = star-to-star distance / 81.3, ribbon normal (local Z) = wall normal;
  * a node = an invisible collision box (Enderal's invisiblecollision_perks.nif) on the star, script ZP_ProphecyNode;
  * our four 5-star trees hang where four of Enderal's class constellations hang (same wall, same star rotation):
      Faith -> Thaumaturge, Gunslinger -> Trickster, Gadgets -> Infiltrator, Martial Arts -> Vandal.
"""
import os, re, sys, glob, math, shutil, statistics, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE)
from _akropolis import refs, STAR, LINE

V1 = os.path.join(REPO, 'src', 'Prophecy')
V2 = os.path.join(REPO, 'src', 'ProphecyV2')
ESP = os.path.join(V2, 'ProphecyESP')
MOD = 'Zenderal - Prophecy.esp'
BASE = os.path.join(REPO, 'reference', 'base')

_spec = importlib.util.spec_from_file_location('v1', os.path.join(V1, 'tools', '01-build-trees.py'))
v1 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(v1)
TREES = v1.TREES

WALLS = {'Faith': 'Thaumaturge', 'Gunslinger': 'Trickster', 'Gadgets': 'Infiltrator', 'Martial Arts': 'Vandal',
         'Glory': 'BladeDancer'}
# (across, up) per tree slot, by tree size: root -> two branches -> merge (-> capstone). Edges come from the perks' parents.
LAYOUTS = {5: [(0, 0), (-1, 1), (1, 1), (0, 2), (0, 3)], 4: [(0, 0), (-1, 1), (1, 1), (0, 2)]}
HALF_WIDTH = 40.0
LINE_START, LINE_UNITS = 4.1, 81.3
SPAWN = (2005.3868, 1998.438, 150.18788)                  # Enderal's _00E_ClassMenuOrigin 0AC813
SPAWN_ROT = (0, 0, 0.025003282)
NODE_BASE_SRC = '_00E_Class_Acti_Vandal_P01_Barbarian - 06A016_Skyrim.esm.yaml'
LIGHTING_SRC = 'MQP03TempleInnerVision - 1503AA_Skyrim.esm'  # Enderal's own vision void
# Enderal forms the unlock / teleport sequences use (same as _00E_Class_PerkScript / _00E_Class_OpenClassMenuScript)
F = dict(TeleportIMOD='05BCFF:Skyrim.esm', TeleportSound='05C23E:Skyrim.esm', CantEnterInCombat='042AF9:Skyrim.esm',
         UnlockSound='03A1E7:Skyrim.esm', AbsorbVFX='02E6AD:Skyrim.esm', AbsorbFXS='0ACDC5:Skyrim.esm',
         UnlockIMOD='03C692:Skyrim.esm', XMarkerHeading='000034:Skyrim.esm')
SKIP_BASES = ('_00E_Class_', '_00E_Game_CalculateClassTGBX', '_00E_MQP03_AkropolisTriggerbox',
              '_00E_DirectiononalMarkerArrow', 'COCMarkerHeading', 'XMarkerHeading', 'WaterCurrentMarker', 'Water1024')

nid = [0xC00]
def alloc():
    fk = f'{nid[0]:06X}:{MOD}'; nid[0] += 1; assert nid[0] <= 0xFFF, 'out of ESL range'; return fk


# ------------------------------------------------------------------------------------------------ geometry
def rx(a): c, s = math.cos(a), math.sin(a); return [[1, 0, 0], [0, c, -s], [0, s, c]]
def ry(a): c, s = math.cos(a), math.sin(a); return [[c, 0, s], [0, 1, 0], [-s, 0, c]]
def rz(a): c, s = math.cos(a), math.sin(a); return [[c, -s, 0], [s, c, 0], [0, 0, 1]]
def mul(A, B): return [[sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def mat(rot): return mul(mul(rx(-rot[0]), ry(-rot[1])), rz(-rot[2]))
def unit(v): n = math.sqrt(sum(x * x for x in v)); return [x / n for x in v]
def cross(a, b): return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]
def dot(a, b): return sum(x * y for x, y in zip(a, b))

def rot_from(xa, ya, za):
    """Euler (rx, ry, rz) whose mat() has columns xa, ya, za."""
    M = [[xa[i], ya[i], za[i]] for i in range(3)]
    b = math.asin(max(-1, min(1, M[0][2]))); a = math.atan2(-M[1][2], M[2][2]); g = math.atan2(-M[0][1], M[0][0])
    rot = (-a, -b, -g)
    chk = mat(rot)
    assert all(abs(chk[i][j] - M[i][j]) < 1e-4 for i in range(3) for j in range(3)), 'euler round trip'
    return rot

def line_ref(p, q, normal):
    d = unit([q[i] - p[i] for i in range(3)]); dist = math.dist(p, q)
    z = unit([normal[i] - dot(normal, d) * d[i] for i in range(3)]); x = cross(d, z)
    return [p[i] + d[i] * LINE_START for i in range(3)], rot_from(x, d, z), dist / LINE_UNITS

def fmt(v): return ', '.join(f'{x:.6g}' if abs(x) > 1e-9 else '0' for x in v)


# ------------------------------------------------------------------------------------------------ build
def main():
    assert os.path.isdir(os.path.join(V1, 'ProphecyESP', 'Perks')), 'run src/Prophecy/tools/01-build-trees.py first'
    shutil.rmtree(ESP, ignore_errors=True)
    shutil.copytree(os.path.join(V1, 'ProphecyESP'), ESP)
    for s in ('ZP_ProphecyInit.psc', 'ZP_FlowStateEffect.psc', 'ZP_TripwireBlastEffect.psc', 'ZP_SeismicStompEffect.psc',
              'ZP_SecondWindEffect.psc', 'ZP_WarBannerEffect.psc', 'ZP_PlaySoundEffect.psc'):
        shutil.copy(os.path.join(V1, 'Scripts', 'source', s), os.path.join(V2, 'Scripts', 'source', s))
    # the source mods' compiled scripts ship unchanged in both builds; ZP_ scripts are compiled per build
    comp = os.path.join(V2, 'Scripts', 'compiled'); os.makedirs(comp, exist_ok=True)
    for f in glob.glob(os.path.join(comp, '*.pex')):
        if not os.path.basename(f).lower().startswith('zp_'): os.remove(f)
    for f in glob.glob(os.path.join(V1, 'Scripts', 'compiled', '*.pex')):
        if not os.path.basename(f).lower().startswith('zp_'): shutil.copy(f, comp)

    R = refs()
    names = {}
    for d in ('Skyrim', 'EnderalFS'):
        for p in glob.glob(os.path.join(BASE, d, '*', '*.yaml')):
            m = re.search(r'^(.*) - ([0-9A-F]{6})_(.+)\.yaml$', os.path.basename(p))
            if m: names[f'{m.group(2)}:{m.group(3)}'] = m.group(1)

    # Enderal's class walls: their stars (via each node's linked star)
    walls = {}
    for v in R.values():
        n = names.get(v['base'], '')
        if n.startswith('_00E_Class_Acti_'):
            st = [r for kw, r in v['links'] if r in R and R[r]['base'] == STAR]
            if st: walls.setdefault(n.split('_')[4], []).append((R[st[0]], v))

    perks = {}
    for p in glob.glob(os.path.join(ESP, 'Perks', '*.yaml')):
        t = open(p, encoding='utf-8').read()
        perks[re.search(r'^EditorID: (.+?)\s*$', t, re.M).group(1)] = re.search(r'^FormKey: (.+?)\s*$', t, re.M).group(1)
    order = [n for _, _, ns in TREES for n in ns]
    perkfk = [perks[v1.perk_edid(n)] for n in order]

    cell_fk, node_base = alloc(), alloc()
    info = [alloc() for _ in order]
    origin_fk, realworld_fk = alloc(), alloc()

    persistent, temporary = [], []
    def placed(fk, base, pos, rot, scale=None, vmad=''):
        s = f'- MutagenObjectType: PlacedObject\n  FormKey: {fk}\n' + vmad + f'  Base: {base}\n'
        if scale and abs(scale - 1) > 1e-6: s += f'  Scale: {scale:.6g}\n'
        return s + f'  Placement:\n    Position: {fmt(pos)}\n    Rotation: {fmt(rot)}\n'

    persistent.append(placed(origin_fk, F['XMarkerHeading'], SPAWN, SPAWN_ROT))
    persistent.append(placed(realworld_fk, F['XMarkerHeading'], SPAWN, (0, 0, 0)))

    star_fk, line_fk, line_from, line_to = [], [], [], []
    base = 0
    for t_i, (tree, _, ns) in enumerate(TREES):
        LAYOUT = LAYOUTS[len(ns)]
        slot = {n[0]: k for k, n in enumerate(ns)}
        edges = [(slot[par], k) for k, n in enumerate(ns) for par in n[5]]
        pairs = walls[WALLS[tree]]
        pts = [s['pos'] for s, _ in pairs]
        cx = [statistics.mean(p[i] for p in pts) for i in range(3)]
        dx = [p[0] - cx[0] for p in pts]; dy = [p[1] - cx[1] for p in pts]
        ang = 0.5 * math.atan2(2 * sum(a * b for a, b in zip(dx, dy)), sum(a * a for a in dx) - sum(b * b for b in dy))
        normal = [-math.sin(ang), math.cos(ang), 0.0]
        if dot(normal, [SPAWN[i] - cx[i] for i in range(3)]) < 0: normal = [-x for x in normal]
        right = cross([0, 0, 1], normal)
        zmin = min(p[2] for p in pts); zmax = max(p[2] for p in pts); step = (zmax - zmin) / max(w for _, w in LAYOUT)
        star_rot = pairs[0][0]['rot']
        node_scale = statistics.median(v['scale'] for _, v in pairs)
        pos = []
        for (u, w) in LAYOUT:
            pos.append([cx[0] + right[0] * u * HALF_WIDTH, cx[1] + right[1] * u * HALF_WIDTH, zmin + w * step])
        for k in range(len(ns)):
            idx = base + k
            sfk = alloc(); star_fk.append(sfk)
            persistent.append(placed(sfk, STAR, pos[k], star_rot))
            vm = ('  VirtualMachineAdapter:\n    Scripts:\n    - Name: ZP_ProphecyNode\n      Properties:\n'
                  '      - MutagenObjectType: ScriptIntProperty\n        Name: Index\n'
                  f'        Data: {idx}\n'
                  '      - MutagenObjectType: ScriptObjectProperty\n        Name: Sanctum\n'
                  f'        Object: 000807:{MOD}\n')
            persistent.append(placed(alloc(), node_base, pos[k], star_rot, node_scale, vm))
        for a, b in edges:
            lp, lr, ls = line_ref(pos[a], pos[b], normal)
            lfk = alloc(); line_fk.append(lfk); line_from.append(base + a); line_to.append(base + b)
            persistent.append(placed(lfk, LINE, lp, lr, ls))
        base += len(ns)

    # environment: Enderal's Akropolis minus its own trees/markers, at the same coordinates
    akro_refs = set(R)
    env = [(k, v) for k, v in R.items() if not names.get(v['base'], '').startswith(SKIP_BASES)]
    remap = {k: alloc() for k, _ in env}
    for k, v in env:
        blk = v['text'].rstrip('\n') + '\n'
        lines = blk.split('\n')
        indent = len(lines[0]) - len(lines[0].lstrip(' '))
        blk = '\n'.join(l[indent:] for l in lines)
        blk = re.sub(r'^  FormKey: .*$', f'  FormKey: {remap[k]}', blk, count=1, flags=re.M)
        blk = re.sub(r'^  (?:MajorRecordFlagsRaw|Version2): .*\n', '', blk, flags=re.M)
        blk = re.sub(r'^  SkyrimMajorRecordFlags:\n(?:  - .*\n)*', '', blk, flags=re.M)
        blk = re.sub(r'^  (?:LinkedReferences|EnableParent):\n(?:    .*\n|  - .*\n)*', '', blk, flags=re.M)
        for r in set(re.findall(r'[0-9A-F]{6}:[^\n:]*?\.es[mp]', blk)):
            if r in akro_refs and r != k:
                assert r in remap, f'env ref {k} points at Akropolis ref {r} that is not copied'
                blk = blk.replace(r, remap[r])
        temporary.append(blk)

    # --- records
    def write(folder, name, text):
        os.makedirs(os.path.join(ESP, folder), exist_ok=True)
        fk = re.search(r'^FormKey: (.+?)\s*$', text, re.M).group(1).split(':')[0]
        open(os.path.join(ESP, folder, f'{name} - {fk}_{MOD}.yaml'), 'w', encoding='utf-8', newline='\r\n').write(text)

    src = open(os.path.join(BASE, 'Skyrim', 'Activators', NODE_BASE_SRC), encoding='utf-8').read().replace('\r\n', '\n')
    t = re.sub(r'^FormKey: .*$', f'FormKey: {node_base}', src, count=1, flags=re.M)
    t = re.sub(r'^EditorID: .*$', 'EditorID: ZP_ProphecyNodeActi', t, count=1, flags=re.M)
    t = re.sub(r'^Version2: .*\n', '', t, flags=re.M)
    t = re.sub(r'^VirtualMachineAdapter:\n(?:  .*\n)*', 'VirtualMachineAdapter:\n  Scripts:\n  - Name: ZP_ProphecyNode\n', t, count=1, flags=re.M)
    t = re.sub(r'^Name:\n(?:  .*\n)*', 'Name:\n  TargetLanguage: English\n  Value: Prophecy\n', t, count=1, flags=re.M)
    assert 'invisiblecollision_perks.nif' in t
    write('Activators', 'ZP_ProphecyNodeActi', t)

    for k, n in enumerate(order):
        p = glob.glob(os.path.join(ESP, 'Perks', f'* - {perkfk[k].split(":")[0]}_*'))[0]
        pt = open(p, encoding='utf-8').read().replace('\r\n', '\n')
        val = lambda key: re.search(rf'^{key}:\n  TargetLanguage: English\n  Value: (.*)$', pt, re.M).group(1)
        unq = lambda v: v[1:-1].replace("''", "'") if v.startswith("'") else v
        text = (unq(val('Name')) + ': ' + unq(val('Description'))).replace("'", "''")
        write('Messages', 'ZP_Prophecy_Info_' + v1.perk_edid(n)[len('ZP_Prophecy_'):],
              f"FormKey: {info[k]}\nEditorID: ZP_Prophecy_Info_{v1.perk_edid(n)[len('ZP_Prophecy_'):]}\n"
              f"Description:\n  TargetLanguage: English\n  Value: '{text}'\nINAM: 0x00000000\nFlags:\n- MessageBox\n"
              "MenuButtons:\n- Text:\n    TargetLanguage: English\n    Value: Learn (1 Prophecy point)\n"
              "- Text:\n    TargetLanguage: English\n    Value: Back\n")

    lp = open(glob.glob(os.path.join(BASE, 'Skyrim', 'Cells', '*', '*', LIGHTING_SRC, 'RecordData.yaml'))[0], encoding='utf-8').read().replace('\r\n', '\n')
    lighting = re.search(r'^Lighting:\n(?:  .*\n)*', lp, re.M).group(0)
    lighting = re.sub(r'^  Inherits:\n(?:  - .*\n)*', '', lighting, flags=re.M)
    cid = int(cell_fk.split(':')[0], 16)
    cdir = os.path.join(ESP, 'Cells', str(cid % 10), str(cid // 10 % 10), f'ZP_ProphecySanctum - {cell_fk.split(":")[0]}_{MOD}')
    os.makedirs(cdir, exist_ok=True)
    cell = (f'FormKey: {cell_fk}\nEditorID: ZP_ProphecySanctum\nName:\n  TargetLanguage: English\n  Value: Prophecy\n'
            'Flags:\n- IsInteriorCell\n' + lighting +
            'Persistent:\n' + ''.join(persistent) + 'Temporary:\n' + ''.join(temporary))
    open(os.path.join(cdir, 'RecordData.yaml'), 'w', encoding='utf-8', newline='\r\n').write(cell)

    # quest 0x807: v2 scripts and properties
    objs = lambda fks: ''.join(f"      - Name: ''\n        Object: {fk}\n" for fk in fks)
    ints = lambda xs: ''.join(f'      - {x}\n' for x in xs)
    prop = lambda n, fk: f'    - MutagenObjectType: ScriptObjectProperty\n      Name: {n}\n      Object: {fk}\n'
    olist = lambda n, fks: f'    - MutagenObjectType: ScriptObjectListProperty\n      Name: {n}\n      Objects:\n' + objs(fks)
    ilist = lambda n, xs: f'    - MutagenObjectType: ScriptIntListProperty\n      Name: {n}\n      Data:\n' + ints(xs)
    pos = {n[0]: k for k, n in enumerate(order)}
    pw_i, pw_s = v1.perk_powers(ESP, perkfk)
    gift_i, gift_s = v1.gift_props(ESP, {n[0]: k for k, n in enumerate(order)})
    nodes = {n[0]: n for n in order}
    pa = [pos[n[5][0]] if n[5] else -1 for n in order]
    pb = [pos[n[5][1]] if len(n[5]) > 1 else -1 for n in order]
    q = (f'FormKey: 000807:{MOD}\nEditorID: ZP_ProphecyInit\nVirtualMachineAdapter:\n  Scripts:\n'
         '  - Name: ZP_ProphecyInit\n    Properties:\n' + prop('ZP_ProphecyPower', f'000805:{MOD}') +
         '  - Name: ZP_ProphecySanctum\n    Properties:\n' +
         prop('PlayerRef', '000014:Skyrim.esm') + prop('SanctumOrigin', origin_fk) + prop('RealWorldOrigin', realworld_fk) +
         ''.join(prop(k, F[k]) for k in ('TeleportIMOD', 'TeleportSound', 'CantEnterInCombat', 'UnlockSound', 'AbsorbVFX', 'AbsorbFXS', 'UnlockIMOD')) +
         prop('ZP_ProphecyPoints', f'000802:{MOD}') + prop('ZP_ProphecyPointsEarned', f'000809:{MOD}') +
         olist('Perks', perkfk) + olist('PerkInfo', info) + ilist('ParentA', pa) + ilist('ParentB', pb) +
         ilist('PowerPerk', pw_i) + olist('PowerSpell', pw_s) + ilist('GiftPerk', gift_i) + olist('GiftItem', gift_s) +
         olist('Stars', star_fk) + olist('Lines', line_fk) + ilist('LineFrom', line_from) + ilist('LineTo', line_to) +
         "  FileName: ''\nFlags:\n- StartGameEnabled\n- RunOnce\nNextAliasID: 0\n")
    for p in glob.glob(os.path.join(ESP, 'Quests', '* - 000807_*')): os.remove(p)
    write('Quests', 'ZP_ProphecyInit', q)
    print(f'v2: {len(persistent)} persistent + {len(temporary)} temporary refs in ZP_ProphecySanctum, '
          f'{len(star_fk)} stars, {len(line_fk)} lines, next free 0x{nid[0]:03X}')


if __name__ == '__main__':
    main()
