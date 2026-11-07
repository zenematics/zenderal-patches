"""Generate the Fog Wood worldspace into src/FogWood/FogWoodESP/ (Spriggit YAML): a fresh, flat, grassy,
dense pine woodland built from scratch, always dark and fog-filled, with a navmesh of its own.

The curator's brief (2026-11-05): a fresh area, flat woodland terrain, lots of trees, a large space, dense
forest but flat ground and grass, somewhere enemies can path through. (Two earlier builds copied Whisperwood
and then a Vyn pine patch, with SureAI's navmesh; the mushroom forest was the wrong look and the pine patch's
copied entry marker landed inside a rock. Their lessons are in arch-docs/patches/FogWood.md.)

What is generated, into a new worldspace ZFW_FogWood:

  * PATCH x PATCH cells of terrain (gently rolling, within ~+-50 units, so it reads as ground and not a plane),
    pine-forest floor with dense grass (LPineForest02DensityGrass) and blotches of field grass (LFieldGrass02);
    a ring of RING cells of the same terrain and trees around them, so the wood runs on into the fog;
  * a navmesh per patch cell: a 256-unit triangle lattice over the terrain, with a hole cut around every tree
    (trees stand on lattice vertices; the 6 triangles around that vertex go). Border edges link to the
    neighbouring cell's navmesh (EdgeLinks + EdgeLink_x_y flag), the navmesh grid (NVGD) is built the way
    SureAI's are (y-major cells, bounding-box overlap; checked against a reference navmesh at 96%), and a
    navmesh info map (NAVI) override holds only our entries, each merged to its neighbours;
  * trees: large pines (Skyrim's TreePineForest01/02/04, Enderal's ScotsPine01-03) on a jittered lattice at
    least TREE_MIN_GAP vertices apart (lanes stay at least two triangles wide), smaller pines between, and a
    floor of shrubs, ferns and clover (no collision). No rocks or logs: nothing with collision off the lattice;
  * a dark, fog-heavy copy of Enderal's Heartland fog (FS's SkyrimFog_HerzlandNebel 048085: night colours,
    night image space, night ambient and volumetric light at every hour, fog from FOG_NEAR to FOG_FAR), and a
    climate holding only it;
  * invisible walls (CollisionMarker 000021 planes, the shape Enderal and EVGAT use) WALL_INSET inside the
    patch edge; the entry marker at the middle (a lattice vertex kept free of trees) and SPAWN_COUNT spawn
    markers on a ring around it, every one on a free lattice vertex.

A FULL plugin, not ESL: as an ESL its new cells showed no terrain at all. FormIDs: 0x800 WRLD, 0x801 persistent
cell, 0x802 climate, 0x803 weather, 0x804-0x84F reserved for the arena quest, 0x850- cells, then landscapes,
navmeshes, walls + markers, and the trees from ID_REF up. The script asserts every budget.

Run from the repo root: python -I src/FogWood/tools/01-build-wood.py
"""
import math
import os
import random
import re
import shutil
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
REF = os.path.join(REPO, 'reference', 'base-2.1.4.4')
OUT = os.path.join(REPO, 'src', 'FogWood', 'FogWoodESP')
PLUGIN = 'Zenderal - Fog Wood.esp'
FS = 'Enderal - Forgotten Stories.esm'
SEED = 20261105

PATCH = 6                              # cells per side of the arena (navmeshed): -3..2
RING = 1                               # cells of scenery beyond it
CELL = 4096
VSTEP = 128                            # terrain vertex spacing
NSTEP = 256                            # navmesh lattice spacing (2 terrain vertices)
NV = CELL // NSTEP                     # lattice squares per cell side (16)
WALL_INSET = 512
FOG_NEAR, FOG_FAR = 0, 2500            # day; night is NIGHT_SCALE of these
NIGHT_SCALE = 0.9
WATER_HEIGHT = -30000
TREE_LATTICE = 3                       # big pines every 3 lattice vertices (768 units), jittered +-1
TREE_MIN_GAP = 2                       # never closer than 2 vertices (512 units): lanes >= 2 triangles
SMALL_PER_CELL = 10                    # small pines on free vertices (holes cut too)
FLOOR_PER_CELL = 110                   # shrubs, ferns, clover: no collision, anywhere
FLOOR_SINK = 14                        # units below the terrain geometry: the list's terrain parallax draws the
                                       # surface lower than the geometry, so plants on it read as hovering (6 was not enough)
ENTRY_CLEAR = 3                        # lattice vertices around the entry kept free of trees
SPAWN_COUNT, SPAWN_RADIUS = 12, 2300
CACHE_COUNT = 40                       # XMarkers for the Fogbound Caches: walkable vertices with no tree within a vertex
CACHE_RADIUS = 2700                    # ... within this of the entry (the first set, spread over the whole wood, was never seen in the fog)

ID_WRLD, ID_TOPCELL, ID_CLMT, ID_WTHR = 0x800, 0x801, 0x802, 0x803
ID_STONE, ID_EXIT_STONE, EXIT_STONE_Y = 0x805, 0x961, 320      # ACTI from tools/02; its ref in the persistent cell
ID_CELL, ID_LAND, ID_NAVM, ID_MARK, ID_REF = 0x850, 0x8B0, 0x910, 0x950, 0x1000
ID_LIMITS = {'cell': (0x850, 0x8AF), 'land': (0x8B0, 0x90F), 'navm': (0x910, 0x94F), 'mark': (0x950, 0x9FF),
             'ref': (0x1000, 0x7FFF)}

COLLISION_MARKER = '000021:Skyrim.esm'
XMARKER_HEADING = '000034:Skyrim.esm'
MUSIC = '097C29:Skyrim.esm'            # _00E_Music_Atmosphere_DeadForest
LTEX_BASE = '010B5D:Skyrim.esm'        # LPineForest02DensityGrass (2 grasses)
LTEX_GRASS = '01342A:Skyrim.esm'       # LFieldGrass02 (2 grasses)
BIG_TREES = ['01306D:Skyrim.esm', '018A02:Skyrim.esm', '04FBB0:Skyrim.esm',       # TreePineForest01/02/04
             '039013:Skyrim.esm', '0A707A:Skyrim.esm', '0A707B:Skyrim.esm']       # _00E_ScotsPine01-03
SMALL_TREES = ['04B016:Skyrim.esm', '051126:Skyrim.esm']                          # TreePineForest03/05
FLOOR = [('09DAA3:Skyrim.esm', 2), ('09DAA0:Skyrim.esm', 1), ('0B8A6E:Skyrim.esm', 4),   # PineShrub01/02, ReachFern01
         ('0B8A62:Skyrim.esm', 3), ('03905D:Skyrim.esm', 3)]                          # Clover01, vurt_fernfield
WEATHER_SRC = os.path.join(REF, 'EnderalFS', 'Weathers', 'SkyrimFog_HerzlandNebel - 048085_Skyrim.esm.yaml')
CLIMATE_SRC = os.path.join(REF, 'Skyrim', 'Climates', 'DefaultClimate - 00015F_Skyrim.esm.yaml')
REF_NAVMESH_CELL = os.path.join(REF, 'Skyrim', 'Worldspaces', 'Vyn - 001D3C_Skyrim.esm', '-1, 0', '-3, 1')
NVMI_UNKNOWN2 = -1511415748            # constant on every Enderal NAVI entry


def fk(local, plugin=PLUGIN):
    return '%06X:%s' % (local, plugin)


def nl_read(path):
    return open(path, 'rb').read().decode('utf-8').replace('\r\n', '\n')


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(text.replace('\n', '\r\n').encode('utf-8'))


def f2s(v):
    s = ('%.4f' % v).rstrip('0').rstrip('.')
    return s if s not in ('', '-0') else '0'


# ---------------------------------------------------------------- terrain
def height(x, y):
    """Gentle ground: a few long swells, quantised to the engine's 8-unit steps."""
    h = (40 * math.sin(x / 1900 + 0.7) * math.cos(y / 1700 - 0.3)
         + 22 * math.sin((x + y) / 950 + 1.1) + 14 * math.cos((x - 2 * y) / 700))
    return 8 * round(h / 8)


def noise(x, y):
    return 0.5 + 0.5 * math.sin(x / 530 + 0.4) * math.cos(y / 470 - 0.9) * math.cos((x + y) / 1300)


def land_yaml(gx, gy, land_fk):
    x0, y0 = gx * CELL, gy * CELL
    h = [[height(x0 + c * VSTEP, y0 + r * VSTEP) for c in range(33)] for r in range(33)]
    rows = []
    prev_row0 = h[0][0]
    for r in range(33):
        row = [0 if r == 0 else (h[r][0] - prev_row0) // 8]
        prev_row0 = h[r][0]
        for c in range(1, 33):
            row.append((h[r][c] - h[r][c - 1]) // 8)
        assert all(-128 <= v <= 127 for v in row)
        rows.append(row)
    normals = []
    for r in range(33):
        line = []
        for c in range(33):
            dx = (height(x0 + (c + 1) * VSTEP, y0 + r * VSTEP) - height(x0 + (c - 1) * VSTEP, y0 + r * VSTEP)) / (2 * VSTEP)
            dy = (height(x0 + c * VSTEP, y0 + (r + 1) * VSTEP) - height(x0 + c * VSTEP, y0 + (r - 1) * VSTEP)) / (2 * VSTEP)
            n = (-dx, -dy, 1.0)
            l = math.sqrt(n[0] ** 2 + n[1] ** 2 + 1)
            b = [int(round(127 * v / l)) & 0xFF for v in n]
            line.append("'%d, %d, %d'" % tuple(b))
        normals.append('  - [' + ', '.join(line) + ']')
    out = ['Landscape:', '  FormKey: ' + land_fk, '  Version2: 11', '  Flags:', '  - VertexNormalsHeightMap', '  - Layers',
           '  VertexNormals:'] + normals + ['  VertexHeightMap:', '    Offset: ' + f2s(h[0][0] / 8), '    HeightMap:']
    out += ['    - [' + ', '.join(str(v & 0xFF) for v in row) + ']' for row in rows]
    out.append('  Layers:')
    quads = [('BottomLeft', 0, 0), ('BottomRight', 16, 0), ('TopLeft', 0, 16), ('TopRight', 16, 16)]
    for name, qc, qr in quads:
        out += ['  - MutagenObjectType: BaseLayer', '    Header:', '      Texture: ' + LTEX_BASE]
        if name != 'BottomLeft':
            out.append('      Quadrant: ' + name)
        out.append('      LayerNumber: 65535')
    for name, qc, qr in quads:
        data = []
        for r in range(17):
            for c in range(17):
                v = noise(x0 + (qc + c) * VSTEP, y0 + (qr + r) * VSTEP)
                if v > 0.55:
                    data.append((r * 17 + c, min(1.0, (v - 0.55) * 3)))
        if not data:
            continue
        out += ['  - MutagenObjectType: AlphaLayer', '    Header:', '      Texture: ' + LTEX_GRASS]
        if name != 'BottomLeft':
            out.append('      Quadrant: ' + name)
        out.append('    AlphaLayerData:')
        for pos, op in data:
            out += ['    - Position: %d' % pos, '      Opacity: ' + f2s(op)]
    return out, h


# ---------------------------------------------------------------- navmesh
def reference_winding():
    """The sign of SureAI's triangle winding (z of (b-a)x(c-a)), read from a reference navmesh."""
    for cell in os.listdir(REF_NAVMESH_CELL):
        t = nl_read(os.path.join(REF_NAVMESH_CELL, cell, 'RecordData.yaml'))
        i = t.find('NavigationMeshes:')
        if i < 0:
            continue
        seg = t[i:]
        verts = [tuple(float(v) for v in m.groups()) for m in re.finditer(r'^    - (-?[\d.E+-]+), (-?[\d.E+-]+), (-?[\d.E+-]+)$', seg[:seg.find('    Triangles:')], re.M)]
        tris = [tuple(int(v) for v in m.groups()) for m in re.finditer(r'^    - Vertices: (\d+), (\d+), (\d+)$', seg, re.M)]
        signs = []
        for a, b, c in tris[:200]:
            if max(a, b, c) >= len(verts):
                break
            ax, ay = verts[a][0], verts[a][1]
            z = (verts[b][0] - ax) * (verts[c][1] - ay) - (verts[b][1] - ay) * (verts[c][0] - ax)
            if abs(z) > 1:
                signs.append(1 if z > 0 else -1)
        if len(signs) >= 50:
            s = sum(signs)
            assert abs(s) > 0.8 * len(signs), ('reference winding is mixed', s, len(signs))
            return 1 if s > 0 else -1
    raise SystemExit('no reference navmesh to read the winding from')


def build_navmeshes(patch_cells, trees, heights, nav_fk, wrld_fk, winding):
    """One navmesh per patch cell. Returns {cell: dict(verts, tris, links)} with cross-cell links resolved."""
    meshes = {}
    for (gx, gy) in patch_cells:
        x0, y0 = gx * CELL, gy * CELL
        h = heights[(gx, gy)]
        verts, vindex = [], {}
        for j in range(NV + 1):
            for i in range(NV + 1):
                vindex[(i, j)] = len(verts)
                verts.append((x0 + i * NSTEP, y0 + j * NSTEP, h[j * 2][i * 2]))
        blocked = {(i, j) for (i, j) in vindex if (gx * NV + i, gy * NV + j) in trees}
        tris = []
        for j in range(NV):
            for i in range(NV):
                for tri in (((i, j), (i + 1, j), (i + 1, j + 1)), ((i, j), (i + 1, j + 1), (i, j + 1))):
                    if any(v in blocked for v in tri):
                        continue
                    idxs = [vindex[v] for v in tri]
                    a, b, c = (verts[k] for k in idxs)
                    z = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
                    if (z > 0) != (winding > 0):
                        idxs = [idxs[0], idxs[2], idxs[1]]
                    tris.append(idxs)
        meshes[(gx, gy)] = dict(verts=verts, tris=tris, fk=nav_fk[(gx, gy)], links=[], edges={})
    # keep only the triangles the entry (the origin) can reach: tree holes seal off small pockets, and a creature
    # spawned in one could never get out
    pos_index = {}
    for cell, m in meshes.items():
        for ti, tri in enumerate(m['tris']):
            for e in range(3):
                a, b = m['verts'][tri[e]], m['verts'][tri[(e + 1) % 3]]
                pos_index.setdefault(frozenset([a[:2], b[:2]]), []).append((cell, ti))
    start = [(cell, ti) for cell, m in meshes.items() for ti, tri in enumerate(m['tris'])
             if any(m['verts'][k][:2] == (0.0, 0.0) or m['verts'][k][:2] == (0, 0) for k in tri)]
    assert start, 'no navmesh triangle at the entry'
    reach, stack = set(start), list(start)
    while stack:
        cell, ti = stack.pop()
        tri = meshes[cell]['tris'][ti]
        for e in range(3):
            a, b = meshes[cell]['verts'][tri[e]], meshes[cell]['verts'][tri[(e + 1) % 3]]
            for o in pos_index[frozenset([a[:2], b[:2]])]:
                if o not in reach:
                    reach.add(o)
                    stack.append(o)
    dropped = 0
    for cell, m in meshes.items():
        kept = [tri for ti, tri in enumerate(m['tris']) if (cell, ti) in reach]
        dropped += len(m['tris']) - len(kept)
        m['tris'] = kept
    meshes['_dropped'] = dropped
    # edges: internal neighbours, then cross-cell links by shared world positions
    pos_index = {}
    for cell, m in meshes.items():
        if cell == '_dropped':
            continue
        for ti, tri in enumerate(m['tris']):
            for e in range(3):
                a, b = m['verts'][tri[e]], m['verts'][tri[(e + 1) % 3]]
                pos_index.setdefault(frozenset([a[:2], b[:2]]), []).append((cell, ti, e))
    for cell, m in meshes.items():
        if cell == '_dropped':
            continue
        edges = {}
        for ti, tri in enumerate(m['tris']):
            for e in range(3):
                a, b = m['verts'][tri[e]], m['verts'][tri[(e + 1) % 3]]
                others = [o for o in pos_index[frozenset([a[:2], b[:2]])] if o != (cell, ti, e)]
                assert len(others) <= 1, ('edge shared by more than two triangles', cell, ti, e, others)
                if not others:
                    edges[(ti, e)] = ('none', -1)
                elif others[0][0] == cell:
                    edges[(ti, e)] = ('internal', others[0][1])
                else:
                    ocell, oti, oe = others[0]
                    m['links'].append((meshes[ocell]['fk'], oti))
                    edges[(ti, e)] = ('external', len(m['links']) - 1)
                    m.setdefault('merged', set()).add(meshes[ocell]['fk'])
        m['edges'] = edges
    return meshes


def navmesh_yaml(cell, m, wrld_fk, divisor=10):
    gx, gy = cell
    verts, tris = m['verts'], m['tris']
    out = ['- FormKey: ' + m['fk'], '  Version2: 1', '  Data:', '    Parent:',
           '      MutagenObjectType: WorldspaceNavmeshParent', '      Parent: ' + wrld_fk,
           '      Coordinates: %d, %d' % (gy, gx),             # Spriggit writes the cell as Y, X (checked: 3,001 of SureAI's)
           '    Vertices:']
    out += ['    - %s, %s, %s' % tuple(f2s(v) for v in p) for p in verts]
    out.append('    Triangles:')
    for ti, tri in enumerate(tris):
        out.append('    - Vertices: %d, %d, %d' % tuple(tri))
        flags = ['Found']
        for e, name in enumerate(('EdgeLink_0_1', 'EdgeLink_1_2', 'EdgeLink_2_0')):
            kind, val = m['edges'][(ti, e)]
            out.append('      %s: %d' % (name, val))
            if kind == 'external':
                flags.append(name)
        out.append('      Flags:')
        out += ['      - ' + f for f in flags]
    if m['links']:
        out.append('    EdgeLinks:')
        for mesh, ti in m['links']:
            out += ['    - Mesh: ' + mesh, '      TriangleIndex: %d' % ti]
    xs = [v[0] for v in verts]; ys = [v[1] for v in verts]; zs = [v[2] for v in verts]
    mn = (min(xs), min(ys), min(zs)); mx = (max(xs), max(ys), max(zs))
    cw, ch = (mx[0] - mn[0]) / divisor, (mx[1] - mn[1]) / divisor
    grid = b''
    for cy in range(divisor):
        for cx in range(divisor):
            x0, x1 = mn[0] + cx * cw, mn[0] + (cx + 1) * cw
            y0, y1 = mn[1] + cy * ch, mn[1] + (cy + 1) * ch
            hits = []
            for ti, tri in enumerate(tris):
                txs = [verts[k][0] for k in tri]; tys = [verts[k][1] for k in tri]
                if min(txs) <= x1 and max(txs) >= x0 and min(tys) <= y1 and max(tys) >= y0:
                    hits.append(ti)
            grid += struct.pack('<I', len(hits)) + struct.pack('<%dH' % len(hits), *hits)
    out += ['    NavmeshGridDivisor: %d' % divisor, '    MaxDistanceX: ' + f2s(cw), '    MaxDistanceY: ' + f2s(ch),
            '    Min: %s, %s, %s' % tuple(f2s(v) for v in mn), '    Max: %s, %s, %s' % tuple(f2s(v) for v in mx),
            '    NavmeshGrid: 0x' + grid.hex().upper()]
    return out


# ---------------------------------------------------------------- refs
def base_lift(base):
    """How far a base object's mesh floats above its own origin (ObjectBounds min z when positive, else 0):
    vurt_fernfield's lowest point is 19 units up, so at ground level it hovers."""
    local, plugin = base.split(':')
    for src in ('EnderalFS', 'Skyrim'):
        folder = os.path.join(REF, src, 'Trees')
        for f in os.listdir(folder):
            if f.endswith(' - %s_%s.yaml' % (local, plugin)):
                t = nl_read(os.path.join(folder, f))
                m = re.search(r'^ObjectBounds:\n  First: -?\d+, -?\d+, (-?\d+)$', t, re.M)
                return max(0, int(m.group(1))) if m else 0
    raise SystemExit('no base record for ' + base)


def placed(fkey, base, x, y, z, rot, scale=None):
    out = ['- MutagenObjectType: PlacedObject', '  FormKey: ' + fkey, '  Base: ' + base]
    if scale is not None and abs(scale - 1) > 1e-3:
        out.append('  Scale: ' + f2s(scale))
    out += ['  Placement:', '    Position: %s, %s, %s' % (f2s(x), f2s(y), f2s(z)), '    Rotation: 0, 0, ' + f2s(rot)]
    return out


def main():
    rng = random.Random(SEED)
    lo, hi = -PATCH // 2, PATCH - PATCH // 2            # cells lo..hi-1
    patch_cells = [(x, y) for x in range(lo, hi) for y in range(lo, hi)]
    all_cells = [(x, y) for x in range(lo - RING, hi + RING) for y in range(lo - RING, hi + RING)]
    ring_cells = [c for c in all_cells if c not in patch_cells]
    wrld_fk = fk(ID_WRLD)
    winding = reference_winding()

    for sub in ('Worldspaces', 'Weathers', 'Climates', 'NavigationMeshInfoMaps'):
        if os.path.isdir(os.path.join(OUT, sub)):
            shutil.rmtree(os.path.join(OUT, sub))

    # ---- ids
    cell_fk = {c: fk(ID_CELL + i) for i, c in enumerate(all_cells)}
    land_fk = {c: fk(ID_LAND + i) for i, c in enumerate(all_cells)}
    nav_fk = {c: fk(ID_NAVM + i) for i, c in enumerate(patch_cells)}
    assert ID_CELL + len(all_cells) - 1 <= ID_LIMITS['cell'][1] and ID_LAND + len(all_cells) - 1 <= ID_LIMITS['land'][1]
    assert ID_NAVM + len(patch_cells) - 1 <= ID_LIMITS['navm'][1]

    # ---- trees on the global lattice (vertex (gx*NV+i, gy*NV+j)); the entry at the lattice origin
    gmin, gmax = (lo - RING) * NV, (hi + RING) * NV
    entry = (0, 0)
    trees = {}                                           # lattice vertex -> (base, scale)
    cands = []
    for gj in range(gmin, gmax + 1, TREE_LATTICE):
        for gi in range(gmin, gmax + 1, TREE_LATTICE):
            cands.append((gi + rng.randint(-1, 1), gj + rng.randint(-1, 1)))
    rng.shuffle(cands)

    def free(v, gap):
        return (max(abs(v[0] - entry[0]), abs(v[1] - entry[1])) > ENTRY_CLEAR
                and all(max(abs(v[0] - t[0]), abs(v[1] - t[1])) >= gap for t in trees))
    for v in cands:
        if gmin <= v[0] <= gmax and gmin <= v[1] <= gmax and free(v, TREE_MIN_GAP):
            trees[v] = (rng.choice(BIG_TREES), rng.uniform(0.9, 1.25))
    small = 0
    for _ in range(SMALL_PER_CELL * len(all_cells) * 4):
        v = (rng.randint(gmin, gmax), rng.randint(gmin, gmax))
        if free(v, TREE_MIN_GAP):
            trees[v] = (rng.choice(SMALL_TREES), rng.uniform(0.8, 1.1))
            small += 1
            if small >= SMALL_PER_CELL * len(all_cells):
                break

    # ---- terrain + navmesh
    heights, land_lines = {}, {}
    for c in all_cells:
        land_lines[c], heights[c] = land_yaml(c[0], c[1], land_fk[c])
    meshes = build_navmeshes(patch_cells, trees, heights, nav_fk, wrld_fk, winding)
    dropped = meshes.pop('_dropped')
    walkable = set()                                     # lattice vertices with a kept triangle on them
    for m in meshes.values():
        for tri in m['tris']:
            for k in tri:
                v = m['verts'][k]
                walkable.add((int(round(v[0] / NSTEP)), int(round(v[1] / NSTEP))))
    assert entry in walkable, 'the entry is not on the navmesh'

    # ---- spawn markers: walkable lattice vertices nearest the ring points, no tree within a vertex
    spawns = []
    for k in range(SPAWN_COUNT):
        ang = 2 * math.pi * k / SPAWN_COUNT
        want = (SPAWN_RADIUS * math.cos(ang) / NSTEP, SPAWN_RADIUS * math.sin(ang) / NSTEP)
        best = min(((abs(i - want[0]) + abs(j - want[1])), (i, j))
                   for i in range(int(want[0]) - 3, int(want[0]) + 4) for j in range(int(want[1]) - 3, int(want[1]) + 4)
                   if (i, j) in walkable and all(max(abs(i - t[0]), abs(j - t[1])) >= 1 for t in trees))
        spawns.append(best[1])

    def ground(x, y):
        """Terrain height at (x, y): bilinear between the 128-unit vertices. The first build took the nearest
        vertex, and the small plants floated on the 8-unit steps between vertices (curator, 2026-11-05)."""
        c = (math.floor(x / CELL), math.floor(y / CELL))
        h = heights[c]
        fx, fy = (x - c[0] * CELL) / VSTEP, (y - c[1] * CELL) / VSTEP
        i, j = min(int(fx), 31), min(int(fy), 31)
        tx, ty = fx - i, fy - j
        return ((1 - tx) * (1 - ty) * h[j][i] + tx * (1 - ty) * h[j][i + 1]
                + (1 - tx) * ty * h[j + 1][i] + tx * ty * h[j + 1][i + 1])

    lift = {b: base_lift(b) for b in BIG_TREES + SMALL_TREES + [b for b, w in FLOOR]}
    # ---- refs per cell
    refs = {c: [] for c in all_cells}
    next_ref = ID_REF
    for (vi, vj), (base, scale) in sorted(trees.items()):
        x, y = vi * NSTEP, vj * NSTEP
        c = (math.floor(x / CELL), math.floor(y / CELL))
        if c not in refs:
            continue
        refs[c] += placed(fk(next_ref), base, x, y, ground(x, y) - 4 - lift[base] * scale, rng.uniform(0, 2 * math.pi), scale)
        next_ref += 1
    floor_bases = [b for b, w in FLOOR for _ in range(w)]
    for c in all_cells:
        for _ in range(FLOOR_PER_CELL):
            x, y = c[0] * CELL + rng.uniform(16, CELL - 16), c[1] * CELL + rng.uniform(16, CELL - 16)
            base, scale = rng.choice(floor_bases), rng.uniform(0.8, 1.3)
            refs[c] += placed(fk(next_ref), base, x, y, ground(x, y) - FLOOR_SINK - lift[base] * scale, rng.uniform(0, 2 * math.pi), scale)
            next_ref += 1
    assert next_ref - 1 <= ID_LIMITS['ref'][1], 'ref budget'

    # ---- walls and markers
    next_mark = ID_MARK
    pmin, pmax = lo * CELL + WALL_INSET, hi * CELL - WALL_INSET
    zs = [h for hh in heights.values() for row in hh for h in row]
    zmid, zspan = (max(zs) + min(zs)) / 2, (max(zs) - min(zs)) + 4000
    walls = [((pmin + pmax) / 2, pmin, pmax - pmin, 0.0), ((pmin + pmax) / 2, pmax, pmax - pmin, 0.0),
             (pmin, (pmin + pmax) / 2, pmax - pmin, math.pi / 2), (pmax, (pmin + pmax) / 2, pmax - pmin, math.pi / 2)]
    for wx, wy, length, rot in walls:
        c = (math.floor(wx / CELL), math.floor(wy / CELL))
        refs[c] += ['- MutagenObjectType: PlacedObject', '  FormKey: ' + fk(next_mark), '  Base: ' + COLLISION_MARKER,
                    '  Primitive:', '    Bounds: %s, 2, %s' % (f2s(length), f2s(zspan)), "    Color: '#00FFFF00'",
                    '    Unknown: 0.15', '    Type: PortalBox', '  Placement:',
                    '    Position: %s, %s, %s' % (f2s(wx), f2s(wy), f2s(zmid)), '    Rotation: 0, 0, ' + f2s(rot)]
        next_mark += 1
    persistent = []
    entry_fk = fk(next_mark)
    for name, (vi, vj) in [('entry', entry)] + [('spawn', s) for s in spawns]:
        x, y = vi * NSTEP, vj * NSTEP
        persistent += ['  - MutagenObjectType: PlacedObject', '    FormKey: ' + fk(next_mark), '    MajorRecordFlagsRaw: 1024',
                       '    SkyrimMajorRecordFlags:', '    - 0x400', '    Base: ' + XMARKER_HEADING, '    Placement:',
                       '      Position: %s, %s, %s' % (f2s(x), f2s(y), f2s(ground(x, y) + 16)),
                       '      Rotation: 0, 0, ' + f2s(math.atan2(-y, -x) if name == 'spawn' else 0)]
        next_mark += 1
    # the exit stone: the Fogbound Stone (ACTI 0x805 from tools/02) a few steps north of the entry, facing it
    assert next_mark == ID_EXIT_STONE, 'exit stone id moved: %X' % next_mark
    persistent += ['  - MutagenObjectType: PlacedObject', '    FormKey: ' + fk(ID_EXIT_STONE), '    MajorRecordFlagsRaw: 1024',
                   '    SkyrimMajorRecordFlags:', '    - 0x400', '    Base: ' + fk(ID_STONE), '    Placement:',
                   '      Position: 0, %d, %s' % (EXIT_STONE_Y, f2s(ground(0, EXIT_STONE_Y) - 8)),
                   '      Rotation: 0, 0, ' + f2s(math.pi)]
    next_mark += 1
    # cache markers (tools/02 reads them as CacheMarkers 0x962+): the arena script placed its chests at random
    # spots snapped to the nearest navmesh VERTEX, and the lattice keeps every tree's vertex (its triangles are
    # cut, the vertex stays), so one chest stood inside a trunk (curator, 2026-11-06). Now the chests go on these.
    assert next_mark == ID_EXIT_STONE + 1
    taken = set(spawns) | {entry}
    candidates = sorted(v for v in walkable
                        if v not in taken and max(abs(v[0] - entry[0]), abs(v[1] - entry[1])) > ENTRY_CLEAR
                        and math.hypot(v[0] - entry[0], v[1] - entry[1]) * NSTEP <= CACHE_RADIUS
                        and all(max(abs(v[0] - t[0]), abs(v[1] - t[1])) >= 1 for t in trees)
                        and all(max(abs(v[0] - s[0]), abs(v[1] - s[1])) >= 2 for s in spawns))
    caches = []
    while len(caches) < CACHE_COUNT and candidates:
        v = rng.choice(candidates)
        caches.append(v)
        candidates = [c for c in candidates if max(abs(c[0] - v[0]), abs(c[1] - v[1])) >= 2]   # at least 512 apart
    assert len(caches) == CACHE_COUNT, len(caches)
    for (vi, vj) in caches:
        x, y = vi * NSTEP, vj * NSTEP
        persistent += ['  - MutagenObjectType: PlacedObject', '    FormKey: ' + fk(next_mark), '    MajorRecordFlagsRaw: 1024',
                       '    SkyrimMajorRecordFlags:', '    - 0x400', '    Base: ' + XMARKER_HEADING, '    Placement:',
                       '      Position: %s, %s, %s' % (f2s(x), f2s(y), f2s(ground(x, y))),
                       '      Rotation: 0, 0, ' + f2s(rng.uniform(0, 2 * math.pi))]
        next_mark += 1
    assert next_mark - 1 <= ID_LIMITS['mark'][1]

    # ---- write
    wdir = os.path.join(OUT, 'Worldspaces', 'ZFW_FogWood - %06X_%s' % (ID_WRLD, PLUGIN))
    write(os.path.join(wdir, 'RecordData.yaml'), '\n'.join([
        'FormKey: ' + wrld_fk, 'EditorID: ZFW_FogWood', 'Name:', '  TargetLanguage: English', '  Value: The Fog Wood',
        'Climate: ' + fk(ID_CLMT), 'Water: 000018:Skyrim.esm', 'LodWater: 000018:Skyrim.esm',
        'LodWaterHeight: %d' % WATER_HEIGHT, 'LandDefaults:', '  DefaultLandHeight: -2048',
        '  DefaultWaterHeight: %d' % WATER_HEIGHT, 'MapData:', '  CameraMinHeight: 50000', '  CameraMaxHeight: 80000',
        '  CameraInitialPitch: 50', 'WorldMapOffsetScale: 1', 'DistantLodMultiplier: 1', 'Flags:', '- SmallWorld',
        '- CannotFastTravel', 'ObjectBoundsMin: %d, %d' % (lo - RING, lo - RING),
        'ObjectBoundsMax: %d, %d' % (hi + RING - 1, hi + RING - 1), 'Music: ' + MUSIC, 'TopCell:',
        '  FormKey: ' + fk(ID_TOPCELL), '  MajorRecordFlagsRaw: 1024', '  Version2: 3', '  SkyrimMajorRecordFlags:',
        '  - 0x400', '  Persistent:'] + persistent) + '\n')
    blocks = {}
    for g in all_cells:
        blocks.setdefault((g[0] // 32, g[1] // 32), set()).add((g[0] // 8, g[1] // 8))

    def group_yaml(x, y, kind):
        return '\n'.join(([('BlockNumberY: %d' % y)] if y else []) + ([('BlockNumberX: %d' % x)] if x else []) + ['GroupType: ' + kind]) + '\n'
    for b, subs in blocks.items():
        write(os.path.join(wdir, '%d, %d' % b, 'GroupRecordData.yaml'), group_yaml(b[0], b[1], 'ExteriorCellBlock'))
        for s in subs:
            write(os.path.join(wdir, '%d, %d' % b, '%d, %d' % s, 'GroupRecordData.yaml'), group_yaml(s[0], s[1], 'ExteriorCellSubBlock'))
    for g in all_cells:
        lines = ['FormKey: ' + cell_fk[g], 'Version2: 1', 'Grid:', '  Point: %d, %d' % g, 'WaterHeight: 3.4028235E+38'] + land_lines[g]
        if g in meshes:
            lines += ['NavigationMeshes:'] + navmesh_yaml(g, meshes[g], wrld_fk)
        if refs[g]:
            lines += ['Temporary:'] + refs[g]
        write(os.path.join(wdir, '%d, %d' % (g[0] // 32, g[1] // 32), '%d, %d' % (g[0] // 8, g[1] // 8),
                           '%s_%s' % (cell_fk[g].split(':')[0], PLUGIN), 'RecordData.yaml'), '\n'.join(lines) + '\n')

    navi = []
    for g in patch_cells:
        m = meshes[g]
        cx = sum(v[0] for v in m['verts']) / len(m['verts']); cy = sum(v[1] for v in m['verts']) / len(m['verts'])
        cz = sum(v[2] for v in m['verts']) / len(m['verts'])
        navi += ['- NavigationMesh: ' + m['fk'], '  Point: %s, %s, %s' % (f2s(cx), f2s(cy), f2s(cz))]
        if m.get('merged'):
            navi += ['  MergedTo:'] + ['  - ' + k for k in sorted(m['merged'])]
        navi += ['  Unknown2: %d' % NVMI_UNKNOWN2, '  Parent:', '    MutagenObjectType: NavigationMapInfoWorldParent',
                 '    ParentWorldspace: ' + wrld_fk,
                 '    ParentWorldspaceCoord: %d, %d' % (g[1], g[0])]   # Y, X here too (5,823 of SureAI's entries)
    write(os.path.join(OUT, 'NavigationMeshInfoMaps', '000802_%s.yaml' % FS),
          '\n'.join(['FormKey: 000802:' + FS, 'Version2: 1', 'NavMeshVersion: 12', 'MapInfos:'] + navi) + '\n')

    # ---- weather: Heartland fog at its night values for every hour, fog pulled in
    w = nl_read(WEATHER_SRC)
    src_fk = re.search(r'^FormKey: (.+)$', w, re.M).group(1)
    src_edid = re.search(r'^EditorID: (.+)$', w, re.M).group(1)
    w = w.replace('FormKey: ' + src_fk, 'FormKey: ' + fk(ID_WTHR), 1).replace('EditorID: ' + src_edid, 'EditorID: ZFW_FogWoodWeather', 1)
    slots = ('Sunrise', 'Day', 'Sunset', 'EarlySunrise', 'LateSunrise', 'EarlySunset', 'LateSunset')
    n = 0

    def night_all_day(m):
        nonlocal n
        block = m.group(0)
        night = re.search(r"^  Night: (.+)$", block, re.M)
        if not night:
            return block
        n += 1
        for slot in slots:
            block = re.sub(r'^  %s: .+$' % slot, '  %s: %s' % (slot, night.group(1)), block, flags=re.M)
        return block
    w = re.sub(r'^([A-Za-z]+Color|ImageSpaces|VolumetricLighting):\n(?:  .+\n)+', night_all_day, w, flags=re.M)
    assert n >= 14, ('colour/image-space blocks rewritten', n)

    def night_ambient(m):
        head, body = m.group(1), m.group(2)
        parts = [p for p in re.split(r'(?m)^(?=  [A-Za-z]+:\n)', body) if p.strip()]
        named = dict((re.match(r'  ([A-Za-z]+):', p).group(1), p) for p in parts)
        out = []
        for p in parts:
            slot = re.match(r'  ([A-Za-z]+):', p).group(1)
            out.append(p if slot not in slots else named['Night'].replace('  Night:', '  %s:' % slot, 1))
        return head + ''.join(out)
    w, k = re.subn(r'(?m)^(DirectionalAmbientLightingColors:\n)((?:  .+\n)+)', night_ambient, w)
    assert k == 1, 'ambient block'
    fog = {'FogDistanceDayNear': FOG_NEAR, 'FogDistanceDayFar': FOG_FAR,
           'FogDistanceNightNear': int(FOG_NEAR * NIGHT_SCALE), 'FogDistanceNightFar': int(FOG_FAR * NIGHT_SCALE),
           'FogDistanceDayMax': 1, 'FogDistanceNightMax': 1}
    for key, val in fog.items():
        w, k = re.subn(r'^%s: .+$' % key, '%s: %s' % (key, val), w, flags=re.M)
        if k == 0:
            w, k = re.subn(r'^(FogDistanceDayFar: )', '%s: %s\n\\1' % (key, val), w, count=1, flags=re.M)
        assert k == 1, key
    write(os.path.join(OUT, 'Weathers', 'ZFW_FogWoodWeather - %06X_%s.yaml' % (ID_WTHR, PLUGIN)), w)
    c = nl_read(CLIMATE_SRC)
    c = c.replace('FormKey: 00015F:Skyrim.esm', 'FormKey: ' + fk(ID_CLMT), 1).replace('EditorID: DefaultClimate', 'EditorID: ZFW_FogWoodClimate', 1)
    c, k = re.subn(r'^WeatherTypes:\n(?:- .+\n(?:  .+\n)*)+', 'WeatherTypes:\n- Weather: %s\n  Chance: 100\n' % fk(ID_WTHR), c, flags=re.M)
    assert k == 1, 'climate weather list'
    write(os.path.join(OUT, 'Climates', 'ZFW_FogWoodClimate - %06X_%s.yaml' % (ID_CLMT, PLUGIN)), c)

    ntri = sum(len(m['tris']) for m in meshes.values())
    nlink = sum(len(m['links']) for m in meshes.values())
    print('cells %d (patch %d + ring %d), trees %d (big %d, small %d), floor plants %d, refs up to 0x%X'
          % (len(all_cells), len(patch_cells), len(ring_cells), len(trees), len(trees) - small, small,
             FLOOR_PER_CELL * len(all_cells), next_ref - 1))
    print('navmeshes %d, triangles %d (%d in sealed pockets dropped), cross-cell links %d, winding %+d; entry %s at the '
          'origin, %d spawn markers' % (len(meshes), ntri, dropped, nlink, winding, entry_fk, len(spawns)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
