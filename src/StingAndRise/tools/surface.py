"""Surfaces of placed furniture, for laying an item on it (the uniques' placement tools use this).

  mesh_triangles(nif)        every renderable triangle of a mesh in its root's space (the node chain's transforms
                             composed; collision, skinned shapes and particles left out)
  levels(T, box)             the heights of the upward-facing flat triangles inside an object-space XY box,
                             clustered: shelf boards, a table top, a coffin's floor
  top_z(T, x, y, below)      the highest surface at (x, y) under `below` (object space)
  winning_model(...)         a static's model path and the load order's winning copy of the mesh
  to_world / to_local        a ref's placement (position, Bethesda rotation in radians, scale)

Bethesda's reference rotation is extrinsic X, then Y, then Z, each clockwise seen down the axis (a +Z turn of t maps
local (x, y) to (x cos t + y sin t, -x sin t + y cos t)): R = Rz(-z) Ry(-y) Rx(-x) in right-handed terms."""
import os
import re
import struct

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
import nifse  # noqa: E402

NODE_TYPES = ('NiNode', 'BSFadeNode', 'BSMultiBoundNode', 'BSOrderedNode', 'BSLeafAnimNode', 'BSTreeNode',
              'BSValueNode', 'BSMasterParticleSystem', 'NiSwitchNode', 'NiLODNode', 'BSDamageStage', 'BSBlastNode',
              'BSDebrisNode', 'NiBillboardNode')
SHAPE_TYPES = ('BSTriShape', 'BSMeshLODTriShape', 'BSSubIndexTriShape')


def _rot(axis, a):
    c, s = np.cos(a), np.sin(a)
    if axis == 'x':
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    if axis == 'y':
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def ref_matrix(rot):
    """A reference's rotation (radians, as Spriggit prints Placement.Rotation) as a matrix acting on local columns."""
    rx, ry, rz = rot
    return _rot('z', -rz) @ _rot('y', -ry) @ _rot('x', -rx)


def to_world(p_local, pos, rot, scale=1.0):
    return np.asarray(pos, float) + scale * (np.atleast_2d(p_local) @ ref_matrix(rot).T)


def to_local(p_world, pos, rot, scale=1.0):
    return ((np.atleast_2d(p_world) - np.asarray(pos, float)) @ ref_matrix(rot)) / scale


def mesh_triangles(nif):
    """(V, T) of every unskinned shape in root space. A node's transform is (t, R, s): child -> parent = t + s R x."""
    V, T = [], []

    def walk(k, M, t, s):
        tp = nif.btype(k)
        if tp in SHAPE_TYPES:
            try:
                sh = nifse.read_trishape(nif.blocks[k])
            except Exception:
                return                                            # skinned / particle data: not a surface
            if sh.get('skin', -1) >= 0 or not len(sh['tris']):
                return
            if struct.unpack_from('<I', nif.blocks[k], nifse.av_fields(nif.blocks[k])['flags'])[0] & 1:
                return                                            # hidden (blood edges, a holder)
            lt, lR, ls = nifse.transform(nif.blocks[k])
            M2, t2, s2 = M @ lR, t + s * (M @ lt), s * ls
            V.append(t2 + s2 * (sh['pos'] @ M2.T))
            T.append(sh['tris'] + sum(len(v) for v in V[:-1]))
            return
        if tp in NODE_TYPES:
            lt, lR, ls = nifse.transform(nif.blocks[k])
            M2, t2, s2 = M @ lR, t + s * (M @ lt), s * ls
            _, kids = nifse.node_children(nif.blocks[k])
            for c in kids:
                if c >= 0:
                    walk(c, M2, t2, s2)

    for r in nif.roots:
        walk(r, np.eye(3), np.zeros(3), 1.0)
    if not V:
        return np.zeros((0, 3)), np.zeros((0, 3), int)
    return np.vstack(V), np.vstack(T)


def levels(V, T, box, min_area=1.0, up=0.95, tol=0.6):
    """Heights (object space) of the flat, upward-facing triangles whose centre lies in `box` = (x0, x1, y0, y1),
    clustered within `tol`, with the area each covers: [(z, area)], highest first."""
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    n = np.cross(b - a, c - a)
    area = np.linalg.norm(n, axis=1) / 2
    nz = n[:, 2] / np.maximum(np.linalg.norm(n, axis=1), 1e-12)
    cen = (a + b + c) / 3
    x0, x1, y0, y1 = box
    m = (nz > up) & (area > 1e-6) & (cen[:, 0] >= x0) & (cen[:, 0] <= x1) & (cen[:, 1] >= y0) & (cen[:, 1] <= y1)
    zs, ar = cen[m, 2], area[m]
    out = []
    for z, w in sorted(zip(zs, ar)):
        if out and abs(z - out[-1][0]) < tol:
            Z, W = out[-1]
            out[-1] = ((Z * W + z * w) / (W + w), W + w)
        else:
            out.append((z, w))
    return sorted([(round(float(z), 2), round(float(w), 1)) for z, w in out if w >= min_area], key=lambda zw: -zw[0])


def top_z(V, T, x, y, below=1e9):
    """The highest triangle surface over (x, y) under `below` (object space), or None."""
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    d = (b[:, 1] - c[:, 1]) * (a[:, 0] - c[:, 0]) + (c[:, 0] - b[:, 0]) * (a[:, 1] - c[:, 1])
    ok = np.abs(d) > 1e-9
    d = np.where(ok, d, 1.0)
    l0 = ((b[:, 1] - c[:, 1]) * (x - c[:, 0]) + (c[:, 0] - b[:, 0]) * (y - c[:, 1])) / d
    l1 = ((c[:, 1] - a[:, 1]) * (x - c[:, 0]) + (a[:, 0] - c[:, 0]) * (y - c[:, 1])) / d
    l2 = 1 - l0 - l1
    inside = ok & (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6)
    z = l0 * a[:, 2] + l1 * b[:, 2] + l2 * c[:, 2]
    z = z[inside & (z < below)]
    return float(z.max()) if len(z) else None


def raster(Vw, T, z0, z1, cell, origin, size):
    """World XY cells (cell units from `origin`, `size` cells) touched by triangles inside the z band [z0, z1]
    (each triangle sampled at about `cell` spacing, only its samples inside the band count)."""
    nx, ny = size
    occ = np.zeros((nx, ny), bool)
    a, b, c = Vw[T[:, 0]], Vw[T[:, 1]], Vw[T[:, 2]]
    zmin = np.minimum(np.minimum(a[:, 2], b[:, 2]), c[:, 2])
    zmax = np.maximum(np.maximum(a[:, 2], b[:, 2]), c[:, 2])
    for i in np.where((zmax >= z0) & (zmin <= z1))[0]:
        tri = np.array([a[i], b[i], c[i]])
        n = int(max(2, np.ceil(np.linalg.norm(tri[1] - tri[0]) / cell), np.ceil(np.linalg.norm(tri[2] - tri[0]) / cell)))
        u, v = np.meshgrid(np.linspace(0, 1, n + 1), np.linspace(0, 1, n + 1))
        m = u + v <= 1
        P = tri[0] + u[m][:, None] * (tri[1] - tri[0]) + v[m][:, None] * (tri[2] - tri[0])
        P = P[(P[:, 2] >= z0) & (P[:, 2] <= z1)]
        ix = np.floor((P[:, 0] - origin[0]) / cell).astype(int)
        iy = np.floor((P[:, 1] - origin[1]) / cell).astype(int)
        ok = (ix >= 0) & (ix < nx) & (iy >= 0) & (iy < ny)
        occ[ix[ok], iy[ok]] = True
    return occ


def dilate(occ, r):
    out = occ.copy()
    for dx in range(-r, r + 1):
        for dy in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                out |= np.roll(np.roll(occ, dx, 0), dy, 1)
    return out


def heading_offsets(t, w, l, step):
    """Sample points of a w x l rectangle (length along heading t: Bethesda's +Y turned by t, i.e. (sin t, cos t))."""
    ax = np.array([np.sin(t), np.cos(t)])
    px = np.array([np.cos(t), -np.sin(t)])
    U, W = np.meshgrid(np.arange(-l / 2, l / 2 + 1e-6, step), np.arange(-w / 2, w / 2 + 1e-6, step))
    return U.reshape(-1, 1) * ax + W.reshape(-1, 1) * px


def find_spot(surface_world, top, blockers_world, item_V, item_T, prefer, headings, cell=1.0, clearance=2, band=60.0):
    """Where an item lies flat (its local z up) on the surface at height `top`: every sample of its XY footprint on
    the surface's flat top (within 0.5 of `top`), `clearance` cells clear of everything else rising into the band
    [top + 0.5, top + band] (the surface's own walls and rails, and each blocker mesh), nearest `prefer`.
    surface_world / blockers_world: (V_world, T). Returns dict(position, rotation, centre, heading, bounds) for the
    REFR (position = the item's origin; rotation (0, 0, heading)), or None."""
    Sw, ST = surface_world
    used = item_V[np.unique(item_T)]
    lo_i, hi_i = used.min(0), used.max(0)
    w, l = hi_i[0] - lo_i[0], hi_i[1] - lo_i[1]
    cx, cy = (lo_i[0] + hi_i[0]) / 2, (lo_i[1] + hi_i[1]) / 2
    lo = np.array([Sw[:, 0].min() - 5, Sw[:, 1].min() - 5])
    hi = np.array([Sw[:, 0].max() + 5, Sw[:, 1].max() + 5])
    size = tuple(np.ceil((hi - lo) / cell).astype(int))
    top_ok = raster(Sw, ST, top - 0.5, top + 0.5, cell, lo, size)
    blocked = raster(Sw, ST, top + 0.5, top + band, cell, lo, size)
    for Bw, BT in blockers_world:                        # only what rises above the surface (a stack under it is fine)
        blocked |= raster(Bw, BT, top + 0.5, top + band, cell, lo, size)
    free = top_ok & ~dilate(blocked, clearance)
    nx, ny = free.shape
    best = None
    for t in headings:
        offs = heading_offsets(t, w, l, cell / 2)
        for i, j in zip(*np.where(free)):
            c = lo + (np.array([i, j]) + 0.5) * cell
            P = c + offs
            ix = np.floor((P[:, 0] - lo[0]) / cell).astype(int)
            iy = np.floor((P[:, 1] - lo[1]) / cell).astype(int)
            if (ix < 0).any() or (iy < 0).any() or (ix >= nx).any() or (iy >= ny).any() or not free[ix, iy].all():
                continue
            d = float(np.linalg.norm(c - prefer))
            if best is None or d < best[0]:
                best = (d, c, t)
    if best is None:
        return None
    _, c, t = best
    off = np.array([cx * np.cos(t) + cy * np.sin(t), -cx * np.sin(t) + cy * np.cos(t)])   # footprint centre, world
    return dict(position=(float(c[0] - off[0]), float(c[1] - off[1]), float(top - lo_i[2] + 0.1)),
                rotation=(0.0, 0.0, float(t)), centre=(float(c[0]), float(c[1])), heading=float(t),
                bounds=(lo_i, hi_i), distance=best[0])


def ref_mesh(sr, ref, base_text, box=None):
    """A placed ref's mesh in world space: (V_world, T). `box` = ((x0, y0, z0), (x1, y1, z1)) stands in for a model the
    reader cannot use (no unskinned shapes)."""
    V, T = np.zeros((0, 3)), np.zeros((0, 3), int)
    model = model_path(base_text)
    if model:
        _, nif = winning_model(sr, model)
        V, T = mesh_triangles(nif)
    if not len(T):
        assert box is not None, ('no readable shape and no stand-in box', model)
        (x0, y0, z0), (x1, y1, z1) = box
        V = np.array([[x, y, z] for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)], float)
        T = np.array([[0, 1, 3], [0, 3, 2], [4, 5, 7], [4, 7, 6], [0, 1, 5], [0, 5, 4], [2, 3, 7], [2, 7, 6],
                      [0, 2, 6], [0, 6, 4], [1, 3, 7], [1, 7, 5]])
    return to_world(V, ref['pos'], ref['rot'], ref['scale']), T


REFERENCE = os.path.normpath(os.path.join(HERE, '..', '..', '..', 'reference'))
SERIALIZATIONS = (('Skyrim.esm', os.path.join(REFERENCE, 'base', 'Skyrim')),
                  ('Enderal - Forgotten Stories.esm', os.path.join(REFERENCE, 'base', 'EnderalFS')),
                  ('Enderal SE - Gameplay Overhaul.esp', os.path.join(REFERENCE, 'mods', 'EGO - Enderal Gameplay Overhaul')))


def cell_dirs(eid):
    """[(plugin, cell folder)] of an interior cell in the serializations above, load order."""
    import glob
    out = []
    for plugin, root in SERIALIZATIONS:
        for d in glob.glob(os.path.join(root, 'Cells', '*', '*', eid + ' - *')):
            out.append((plugin, d))
    return out


def cell_refs(eid):
    """{ref FormKey: dict(base, pos, rot, scale, plugin)} of a cell, the serializations merged (later wins)."""
    refs = {}
    for plugin, d in cell_dirs(eid):
        t = open(os.path.join(d, 'RecordData.yaml'), encoding='utf-8').read()
        for block in re.split(r'^- MutagenObjectType: ', t, flags=re.M)[1:]:
            fk = re.search(r'^  FormKey: (.+?)\s*$', block, re.M)
            base = re.search(r'^  Base: (.+?)\s*$', block, re.M)
            if not (fk and base):
                continue
            pos = re.search(r'^    Position: (.*)$', block, re.M)
            rot = re.search(r'^    Rotation: (.*)$', block, re.M)
            sc = re.search(r'^  Scale: (\S+)', block, re.M)
            refs[fk.group(1)] = dict(base=base.group(1), plugin=plugin,
                                     pos=[float(v) for v in pos.group(1).split(',')] if pos else [0.0, 0.0, 0.0],
                                     rot=[float(v) for v in rot.group(1).split(',')] if rot else [0.0, 0.0, 0.0],
                                     scale=float(sc.group(1)) if sc else 1.0)
    return refs


def base_record(fk):
    """The YAML text of a base record (the last serialization that has it)."""
    import glob
    hexid, plugin = fk.split(':', 1)
    found = None
    for _, root in SERIALIZATIONS:
        hits = glob.glob(os.path.join(root, '*', '* - %s_%s.yaml' % (hexid, plugin)))
        if hits:
            found = hits[0]
    assert found, ('no base record', fk)
    return open(found, encoding='utf-8').read()


def check_winners(fks):
    """Each FormKey's last overrider in the live load order (Sting and Rise's master-aware scan): the placement reads
    the serializations above, so a winner outside them means re-serializing first."""
    import importlib.util
    spec = importlib.util.spec_from_file_location('sr_scan', os.path.join(HERE, '00-scan-overriders.py'))
    scan = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scan)
    chains = {fk: [] for fk in fks}
    for name, path in scan.plugin_paths():
        for fk in scan.scan(path, set(fks)):
            chains[fk].append(name)
    known = {p for p, _ in SERIALIZATIONS}
    for fk, chain in chains.items():
        assert chain and chain[-1] in known, (fk, 'is now won by', chain[-1:] or 'nothing', '- re-serialize it first')
    return {fk: c[-1] for fk, c in chains.items()}


def cell_override(eid, header_plugin, placed):
    """{relative path: text} for a plugin's Spriggit folder: the interior cell `eid` with `header_plugin`'s header
    (verbatim, cut before its navmeshes and refs; the name English only: a plugin that is not localized writes it
    so), our refs `placed` = [(FormKey, base FormKey, position, rotation)] lying still (Don't Havok Settle), and the
    block / sub-block group files. Spriggit's float text: float32, shortest."""
    dirs = dict(cell_dirs(eid))
    d = dirs[header_plugin]
    root = dict(SERIALIZATIONS)[header_plugin]
    rel = os.path.relpath(d, root).replace(os.sep, '/')
    text = open(os.path.join(d, 'RecordData.yaml'), encoding='utf-8').read().replace('\r\n', '\n')
    text = re.sub(r'^Name:\n  TargetLanguage: English\n  Values:\n  - Language: English\n    String: (.*)\n(?:  - .*\n    .*\n)*',
                  r'Name:\n  TargetLanguage: English\n  Value: \g<1>\n', text, count=1, flags=re.M)
    # top-level blocks (a key line and its indented / list lines): the navmeshes and refs out, ours in their place,
    # every other field kept where it was (EGO's header ends with MajorFlags after its refs)
    blocks, cur = [], None
    for line in text.rstrip('\n').split('\n'):
        if line and not line[0].isspace() and not line.startswith('- '):
            cur = [line]
            blocks.append(cur)
        else:
            cur.append(line)

    def f32(v):
        s = str(np.float32(v))
        s = s[:-2] if s.endswith('.0') else s
        return '0' if s == '-0' else s

    ours = ['Temporary:']
    for fk, base, pos, rot in placed:
        ours += ['- MutagenObjectType: PlacedObject', '  FormKey: ' + fk, '  MajorRecordFlagsRaw: 536870912',
                 '  SkyrimMajorRecordFlags:', '  - 0x20000000', '  Base: ' + base, '  Placement:',
                 '    Position: %s, %s, %s' % tuple(f32(v) for v in pos),
                 '    Rotation: %s, %s, %s' % tuple(f32(v) for v in rot)]
    out_lines, put = [], False
    for b in blocks:
        if b[0].split(':')[0] in ('NavigationMeshes', 'Persistent', 'Temporary'):
            if not put:
                out_lines += ours
                put = True
            continue
        out_lines += b
    if not put:
        out_lines += ours
    out = {rel + '/RecordData.yaml': '\n'.join(out_lines) + '\n'}
    b, sb = rel.split('/')[1:3]
    for g in ('Cells/%s/GroupRecordData.yaml' % b, 'Cells/%s/%s/GroupRecordData.yaml' % (b, sb)):
        out[g] = open(os.path.join(root, g), encoding='utf-8').read().replace('\r\n', '\n')
    out['Cells/GroupRecordData.yaml'] = '{}\n'
    return out


def place_unique(sr, cell, header_plugin, surface_ref, top_local, item_model, item_base, ref_fk, headings,
                 blockers=(), prefer=None, band=60.0, clearance=2, cell_size=1.0):
    """A unique lying flat on a placed surface (see find_spot), as a cell override (see cell_override).
    surface_ref: the furniture ref's FormKey; top_local: its surface height in the mesh (levels()); blockers:
    [(ref FormKey, stand-in box or None)] of things already on it; prefer: world XY (default the surface's origin).
    Checks every ref read is won by a serialization this module reads. Returns (files, spot)."""
    refs = cell_refs(cell)
    s = refs[surface_ref]
    assert abs(s['rot'][0]) < 1e-6 and abs(s['rot'][1]) < 1e-6, ('a tilted surface', surface_ref, s['rot'])
    check_winners([surface_ref] + [fk for fk, _ in blockers])
    _, snif = winning_model(sr, model_path(base_record(s['base'])))
    sV, sT = mesh_triangles(snif)
    lv = levels(sV, sT, (sV[:, 0].min(), sV[:, 0].max(), sV[:, 1].min(), sV[:, 1].max()))
    assert any(abs(z - top_local) < 0.05 for z, _ in lv), (surface_ref, 'has no flat surface at', top_local, lv[:6])
    top = s['pos'][2] + s['scale'] * top_local
    surf = ref_mesh(sr, s, base_record(s['base']))
    blk = [ref_mesh(sr, refs[fk], base_record(refs[fk]['base']), box) for fk, box in blockers]
    _, nif = winning_model(sr, item_model)
    iV, iT = mesh_triangles(nif)
    spot = find_spot(surf, top, blk, iV, iT, np.asarray(prefer if prefer is not None else s['pos'][:2], float),
                     headings, cell_size, clearance, band)
    assert spot, ('no free spot for', item_model, 'on', surface_ref)
    spot['top'] = top
    files = cell_override(cell, header_plugin, [(ref_fk, item_base, spot['position'], spot['rotation'])])
    return files, spot


def model_path(base_yaml_text):
    """A base record's world model: Model.File, else the first world-model File (an armour's male model)."""
    m = re.search(r'^Model:\n  File: (.*)$', base_yaml_text, re.M)
    if not m:
        m = re.search(r'^WorldModel:\n(?:  .*\n)*?\s+File: (.*)$', base_yaml_text, re.M)
    return m.group(1).strip() if m else None


def winning_model(sr, rel_model):
    """(source, Nif) of the load order's winning copy of meshes\\<rel_model>."""
    rel = 'meshes/' + rel_model.replace(chr(92), '/')
    src, raw = sr.winner(os.path.join(sr.MO2, 'mods'), sr.profile_mods(), rel)
    return src, nifse.Nif(raw)
