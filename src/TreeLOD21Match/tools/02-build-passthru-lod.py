r"""Build `Zenderal - Tree LOD 3D` from the installed list -- never hand-edit its meshes.

Why: after `tools/01`, 83 tree types (8,590 placed trees in Vyn, 30% of the trees in LOD4) still had no 3D tree LOD
model, so DynDOLOD drew them as flat billboards (an X seen from above; the dark pines read as black). Nobody ships
3D LOD for them: Enderal Arboreal Revived and Seasonal Aspen Trees of Enderal (both installed) cover the rest.

How Arboreal made theirs (checked byte for byte, see the doc): a 3D tree LOD model is the full tree's **static**
shapes, unchanged (same vertices, same shader flags incl. Tree_Anim, same textures) under a plain root, with the
collision, BSXFlags, animation and skinning gone. Enderal's animated trees (BSTreeNode) carry a static copy of every
part next to the skinned one (Arboreal's Scots pine = exactly those static shapes), so no unskinning is needed.

For every TREE base record whose winning full model draws a billboard in the latest DynDOLOD Tree Report and has no
3D model in any other installed mod, this script takes the full model whose CRC32 DynDOLOD reported (the original,
not PG Patcher's copy), keeps each unskinned BSTriShape / NiTriShape (+ NiTriShapeData) with its
BSLightingShaderProperty (Default or Glow shader only), BSShaderTextureSet and NiAlphaProperty, puts them under a new
BSFadeNode root (intermediate node translation/scale folded into the shapes; rotated intermediates are refused), and
writes `<model>_<CRC32>passthru_lod.nif` (dyndolod.info *3D Tree LOD Model*). SSE input stays SSE, LE stays LE.

Every output is re-read and must keep the source's static shapes vertex for vertex. `--selftest` rebuilds Arboreal's
own Nehrimese aspen model from the 2.0 mesh and compares.

Brighter foliage for the trees whose LOD reads near-black (BRIGHTEN): their meshes carry ~0.5-0.7 vertex colours on
the leaves (baked shading the full tree's foliage lighting hides, LOD does not) on an already dark leaf texture -- Meadow
Ash `whispertree*` foliage 43 x 0.5 = ~23/255, King's tree 29 x 0.5 = ~14, red/pink/violet rhododendron wide bushes
~50 x 0.7 = ~35 (the Whispering trees, which look right, are 44 x 1.0). Their winning LOD model (Arboreal's, or our own) is written to this mod with the leaf shapes' (Tree_Anim)
vertex colour RGB x FOLIAGE_GAIN, capped at 1.0; trunks, geometry, textures and shaders untouched. This mod outranks
Arboreal in MO2, so its same-named copy wins; Arboreal's files stay as they are.

Re-run after an Enderal update, a tree mesh mod change or a DynDOLOD run, then rerun DynDOLOD.

Usage (repo root):  python src/TreeLOD21Match/tools/02-build-passthru-lod.py
                       [--modlist E:/Zenderal] [--profile Ultra] [--out "E:/Zenderal/mods/Zenderal - Tree LOD 3D"]
                       [--dry-run] [--selftest]
"""
import argparse
import collections
import importlib.util
import os
import re
import shutil
import struct
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
_spec = importlib.util.spec_from_file_location(
    'grassbounds', os.path.join(REPO, 'src', 'GrassBounds', 'tools', '01-build-grass-bounds.py'))
gb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gb)               # BsaIndex, enabled_mods, load_order, archives

BS = '\\'
LOD_DIR = ('meshes', 'dyndolod', 'lod', 'trees')
NODE_TYPES = {'NiNode', 'BSFadeNode', 'BSLeafAnimNode', 'BSTreeNode', 'BSMultiBoundNode', 'NiSwitchNode',
              'BSOrderedNode', 'NiBillboardNode', 'BSValueNode', 'NiLODNode'}
SHAPE_TYPES = {'BSTriShape', 'NiTriShape'}
OK_SHADER_TYPES = {0, 2}                   # Default, Glow (dyndolod.info: the engine supports these in LOD)
IDENT9 = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
# LOD models whose foliage reads near-black (curator, 2026-10-31, Riverville/Golden Mare Mill): Meadow Ash, King's trees,
# and the tree-sized rhododendron wide bushes (the maroon ones: red/pink/violet leaves at vertex colour ~0.7)
BRIGHTEN = re.compile(r'(?i)^(whispertree0[1-7](_2bone)?|kingstree0[13](_3bone)?|rhodbroad[a-z]+)_[0-9a-f]{8}passthru_lod\.nif$')
FOLIAGE_GAIN = 2.0


class Refuse(Exception):
    pass


# --- reading -------------------------------------------------------------------------------------------
class Nif:
    def __init__(self, d):
        self.d = d
        p = d.index(b'\n') + 1
        ver, = struct.unpack_from('<I', d, p)
        if ver != 0x14020007:
            raise Refuse('NIF version %x' % ver)
        p += 4 + 1
        self.user_at = p
        user, nblocks, self.bsver = struct.unpack_from('<III', d, p); p += 12
        if user != 12 or self.bsver not in (83, 100):
            raise Refuse('user %d bsver %d' % (user, self.bsver))
        q = p
        for _ in range(3):
            q += 1 + d[q]
        self.export_strings = d[p:q]       # author / process / export short strings
        p = q
        ntypes, = struct.unpack_from('<H', d, p); p += 2
        self.types = []
        for _ in range(ntypes):
            n, = struct.unpack_from('<I', d, p); self.types.append(d[p + 4:p + 4 + n].decode('latin1')); p += 4 + n
        tidx = struct.unpack_from('<%dH' % nblocks, d, p); p += 2 * nblocks
        sizes = struct.unpack_from('<%dI' % nblocks, d, p); p += 4 * nblocks
        s0 = p
        nstr, = struct.unpack_from('<I', d, p); p += 8
        self.strings = []
        for _ in range(nstr):
            n, = struct.unpack_from('<I', d, p); self.strings.append(d[p + 4:p + 4 + n].decode('latin1')); p += 4 + n
        self.strings_raw = d[s0:p]
        ng, = struct.unpack_from('<I', d, p)
        if ng:
            raise Refuse('NIF groups')
        p += 4
        self.blocks = []
        for i in range(nblocks):
            self.blocks.append((self.types[tidx[i] & 0x7FFF], p, sizes[i])); p += sizes[i]
        nroots, = struct.unpack_from('<I', d, p)
        self.roots = struct.unpack_from('<%di' % nroots, d, p + 4)

    def body(self, i):
        typ, p, sz = self.blocks[i]
        return self.d[p:p + sz]


def objnet(b, q):
    """NiObjectNET prefix: name idx, extra refs, controller. Returns (name, extras, controller, next offset)."""
    name, nx = struct.unpack_from('<iI', b, q); q += 8
    extras = struct.unpack_from('<%di' % nx, b, q); q += 4 * nx
    ctrl, = struct.unpack_from('<i', b, q); q += 4
    return name, extras, ctrl, q


def avobject(b):
    """NiAVObject prefix (bsver > 34: no properties list). Returns dict + offset after the collision ref."""
    name, extras, ctrl, q = objnet(b, 0)
    flags, = struct.unpack_from('<I', b, q); q += 4
    t = struct.unpack_from('<3f', b, q); q += 12
    R = struct.unpack_from('<9f', b, q); q += 36
    s, = struct.unpack_from('<f', b, q); q += 4
    coll, = struct.unpack_from('<i', b, q); q += 4
    return dict(name=name, extras=extras, ctrl=ctrl, flags=flags, t=t, R=R, s=s, coll=coll), q


def node_children(b):
    a, q = avobject(b)
    n, = struct.unpack_from('<I', b, q); q += 4
    return a, struct.unpack_from('<%di' % n, b, q)


def le_data_parse(b):
    """NiTriShapeData, Skyrim LE (20.2.0.7, bsver 83). Returns (vertex bytes, triangle bytes, additional data ref)."""
    q = 4
    nv, = struct.unpack_from('<H', b, q); q += 4
    hv = b[q]; q += 1
    verts = b[q:q + 12 * nv * hv]; q += 12 * nv * hv
    vf, = struct.unpack_from('<H', b, q); q += 2 + 4          # vector flags, material CRC
    hn = b[q]; q += 1; q += 12 * nv * hn
    if hn and vf & 0x1000:
        q += 24 * nv
    q += 16
    hc = b[q]; q += 1; q += 16 * nv * hc
    q += 8 * nv * (vf & 1)
    q += 2
    add, = struct.unpack_from('<i', b, q); q += 4
    ntri, = struct.unpack_from('<H', b, q); q += 2 + 4
    ht = b[q]; q += 1
    tris = b[q:q + 6 * ntri * ht]; q += 6 * ntri * ht
    nmg, = struct.unpack_from('<H', b, q); q += 2
    for _ in range(nmg):
        k, = struct.unpack_from('<H', b, q); q += 2 + 2 * k
    if q != len(b):
        raise Refuse('NiTriShapeData layout')
    return verts, tris, add


def shape_refs(nif, i):
    """(skin, shader, alpha, data, avobject, offset of the field after the collision ref)."""
    typ = nif.blocks[i][0]
    b = nif.body(i)
    a, q = avobject(b)
    if typ == 'BSTriShape':
        skin, shader, alpha = struct.unpack_from('<3i', b, q + 16)
        return skin, shader, alpha, None, a, q
    data, skin = struct.unpack_from('<2i', b, q)
    q2 = q + 8
    nmat, = struct.unpack_from('<I', b, q2); q2 += 4 + 8 * nmat + 4 + 1
    shader, alpha = struct.unpack_from('<2i', b, q2)
    return skin, shader, alpha, data, a, q


def geometry(nif):
    """Static shapes' (name, vertex positions, triangles) for the verification."""
    out = []
    for i, (typ, p, sz) in enumerate(nif.blocks):
        if typ not in SHAPE_TYPES:
            continue
        skin, shader, alpha, data, a, q = shape_refs(nif, i)
        if skin >= 0:
            continue
        b = nif.body(i)
        if typ == 'BSTriShape':
            q += 28
            desc, = struct.unpack_from('<Q', b, q); q += 8
            ntri, nvert = struct.unpack_from('<HH', b, q); q += 8
            vs = (desc & 0xF) * 4
            pos = b''.join(b[q + k * vs:q + k * vs + 12] for k in range(nvert))
            tris = b[q + vs * nvert:q + vs * nvert + 6 * ntri]
        else:
            pos, tris, _ = le_data_parse(nif.body(data))
        out.append((nif.strings[a['name']] if a['name'] >= 0 else '', pos, tris))
    return out


# --- writing -------------------------------------------------------------------------------------------
def build(nif):
    """The static shapes of `nif` under a new BSFadeNode root, as NIF bytes. Raises Refuse."""
    blocks = nif.blocks
    if blocks[nif.roots[0]][0] not in NODE_TYPES or len(nif.roots) != 1:
        raise Refuse('root %s' % blocks[nif.roots[0]][0])
    parent = {}
    for i, (typ, p, sz) in enumerate(blocks):
        if typ in NODE_TYPES:
            for c in node_children(nif.body(i))[1]:
                if c >= 0:
                    parent[c] = i
    root = nif.roots[0]
    root_av = avobject(nif.body(root))[0]

    keep = []                                       # (shape idx, folded translation, folded scale)
    for i, (typ, p, sz) in enumerate(blocks):
        if typ not in SHAPE_TYPES:
            continue
        skin, shader, alpha, data, a, q = shape_refs(nif, i)
        if skin >= 0:
            continue
        if shader < 0 or blocks[shader][0] != 'BSLightingShaderProperty':
            continue                                # effect-shader shapes have no place in tree LOD
        stype, = struct.unpack_from('<I', nif.body(shader), 0)
        if stype not in OK_SHADER_TYPES:
            raise Refuse('shader type %d on %s' % (stype, typ))
        # fold the nodes between the root and the shape
        t, s = [0.0, 0.0, 0.0], 1.0
        n, chain = parent.get(i), []
        while n is not None and n != root:
            chain.append(n); n = parent.get(n)
        if n != root:
            continue                                # not attached to the tree
        for n in reversed(chain):                   # outermost first
            na = avobject(nif.body(n))[0]
            if any(abs(x - y) > 1e-5 for x, y in zip(na['R'], IDENT9)):
                raise Refuse('rotated intermediate node')
            t = [t[k] + s * na['t'][k] for k in range(3)]
            s *= na['s']
        keep.append((i, t, s))
    if not keep:
        raise Refuse('no static shapes')

    # new block order: root, then per shape: shape, [data], shader, texture set, alpha (shared blocks once)
    order, newidx = [None], {}

    def add(old):
        if old not in newidx:
            newidx[old] = len(order); order.append(old)
        return newidx[old]

    for i, t, s in keep:
        skin, shader, alpha, data, a, q = shape_refs(nif, i)
        add(i)
        if data is not None:
            add(data)
        add(shader)
        tex = struct.unpack_from('<i', nif.body(shader), 4 + 8 + 4 * struct.unpack_from('<I', nif.body(shader), 8)[0] + 4 + 8 + 16)[0]
        if tex >= 0:
            if blocks[tex][0] != 'BSShaderTextureSet':
                raise Refuse('texture set block %s' % blocks[tex][0])
            add(tex)
        if alpha >= 0:
            if blocks[alpha][0] != 'NiAlphaProperty':
                raise Refuse('alpha block %s' % blocks[alpha][0])
            add(alpha)

    def ref(old):
        return -1 if old < 0 else newidx[old]

    out_blocks = []                                 # (type name, bytes)
    # root: a plain BSFadeNode with the root's own name, flags and transform
    rb = struct.pack('<iIiI', root_av['name'], 0, -1, root_av['flags']) + struct.pack('<3f', *root_av['t']) \
        + struct.pack('<9f', *root_av['R']) + struct.pack('<f', root_av['s']) + struct.pack('<i', -1)
    kids = [newidx[i] for i, t, s in keep]
    rb += struct.pack('<I', len(kids)) + struct.pack('<%di' % len(kids), *kids) + struct.pack('<I', 0)
    out_blocks.append(('BSFadeNode', rb))
    folded = {i: (t, s) for i, t, s in keep}
    for old in order[1:]:
        typ = blocks[old][0]
        b = nif.body(old)
        if typ in SHAPE_TYPES:
            skin, shader, alpha, data, a, q = shape_refs(nif, old)
            ft, fs = folded[old]
            tt = [ft[k] + fs * a['t'][k] for k in range(3)]
            head = struct.pack('<iIiI', a['name'], 0, -1, a['flags']) + struct.pack('<3f', *tt) \
                + struct.pack('<9f', *a['R']) + struct.pack('<f', fs * a['s']) + struct.pack('<i', -1)
            if typ == 'BSTriShape':
                body = head + b[q:q + 16] + struct.pack('<3i', -1, ref(shader), ref(alpha)) + b[q + 28:]
            else:
                q2 = q + 8
                nmat, = struct.unpack_from('<I', b, q2)
                mat_end = q2 + 4 + 8 * nmat + 4 + 1
                body = head + struct.pack('<2i', ref(data), -1) + b[q2:mat_end] \
                    + struct.pack('<2i', ref(shader), ref(alpha)) + b[mat_end + 8:]
        elif typ == 'NiTriShapeData':
            le_data_parse(b)                        # layout check; additional data must be -1
            if le_data_parse(b)[2] != -1:
                raise Refuse('NiTriShapeData additional data')
            body = b
        elif typ == 'BSLightingShaderProperty':
            stype, = struct.unpack_from('<I', b, 0)
            name, extras, ctrl, q = objnet(b, 4)
            q += 8 + 16                             # shader flags, uv offset + scale
            tex, = struct.unpack_from('<i', b, q)
            body = struct.pack('<IiIi', stype, name, 0, -1) + b[q - 24:q] + struct.pack('<i', ref(tex)) + b[q + 4:]
        elif typ == 'NiAlphaProperty':
            name, extras, ctrl, q = objnet(b, 0)
            body = struct.pack('<iIi', name, 0, -1) + b[q:]
        elif typ == 'BSShaderTextureSet':
            body = b
        else:
            raise Refuse('unexpected block %s' % typ)
        out_blocks.append((typ, body))

    tnames = []
    for typ, body in out_blocks:
        if typ not in tnames:
            tnames.append(typ)
    d = nif.d
    out = bytearray(d[:nif.user_at])
    out += struct.pack('<III', 12, len(out_blocks), nif.bsver) + nif.export_strings
    out += struct.pack('<H', len(tnames))
    for n in tnames:
        out += struct.pack('<I', len(n)) + n.encode('latin1')
    out += b''.join(struct.pack('<H', tnames.index(typ)) for typ, body in out_blocks)
    out += b''.join(struct.pack('<I', len(body)) for typ, body in out_blocks)
    out += nif.strings_raw + struct.pack('<I', 0)
    for typ, body in out_blocks:
        out += body
    out += struct.pack('<Ii', 1, 0)
    return bytes(out)


def brighten(d, gain):
    """Leaf shapes' (shader flag Tree_Anim) vertex colour RGB x gain, capped; same bytes otherwise. Returns (bytes, n)."""
    nif = Nif(d)
    buf = bytearray(d)
    n = 0
    for i, (typ, p, sz) in enumerate(nif.blocks):
        if typ not in SHAPE_TYPES:
            continue
        skin, shader, alpha, data, a, q = shape_refs(nif, i)
        if shader < 0 or nif.blocks[shader][0] != 'BSLightingShaderProperty':
            continue
        sb = nif.body(shader)
        q0 = objnet(sb, 4)[3]
        f2, = struct.unpack_from('<I', sb, q0 + 4)
        if not f2 >> 29 & 1:                        # SLSF2_Tree_Anim marks the foliage
            continue
        if typ == 'BSTriShape':
            q2 = q + 28
            desc, = struct.unpack_from('<Q', nif.body(i), q2)
            ntri, nvert = struct.unpack_from('<HH', nif.body(i), q2 + 8)
            if not (desc >> 44) & 0x20:             # no vertex colours
                continue
            vs, off = (desc & 0xF) * 4, ((desc >> 24) & 0xF) * 4
            base = p + q2 + 16
            for k in range(nvert):
                for c in range(3):
                    j = base + k * vs + off + c
                    buf[j] = min(255, int(round(buf[j] * gain)))
        else:
            dp = nif.blocks[data][1]
            db = nif.body(data)
            q3 = 4
            nv, = struct.unpack_from('<H', db, q3); q3 += 4
            hv = db[q3]; q3 += 1 + 12 * nv * hv
            vf, = struct.unpack_from('<H', db, q3); q3 += 6
            hn = db[q3]; q3 += 1 + 12 * nv * hn
            if hn and vf & 0x1000:
                q3 += 24 * nv
            q3 += 16
            if not db[q3]:
                continue
            q3 += 1
            for k in range(nv):
                at = dp + q3 + 16 * k
                r, g, b_, al = struct.unpack_from('<4f', buf, at)
                struct.pack_into('<4f', buf, at, min(1.0, r * gain), min(1.0, g * gain), min(1.0, b_ * gain), al)
        n += 1
    out = bytes(buf)
    if sorted(geometry(Nif(out))) != sorted(geometry(nif)):
        raise Refuse('brighten changed geometry')
    return out, n


def verify(src, out):
    """The output re-reads, has exactly the source's static shapes (by name, vertices, triangles), nothing else."""
    a, b = Nif(src), Nif(out)
    ga = [g for g in geometry(a)]
    gb_ = geometry(b)
    names_kept = {g[0] for g in gb_}
    want = [g for g in ga if g[0] in names_kept]
    if sorted(want) != sorted(gb_) or len(gb_) == 0:
        raise Refuse('verification: static shapes differ')
    if {t for t, p, s in b.blocks} - {'BSFadeNode', 'BSTriShape', 'NiTriShape', 'NiTriShapeData',
                                       'BSLightingShaderProperty', 'BSShaderTextureSet', 'NiAlphaProperty'}:
        raise Refuse('verification: stray block types')
    return len(gb_)


# --- the installed list --------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--modlist', default='E:/Zenderal')
    ap.add_argument('--profile', default='Ultra')
    ap.add_argument('--out', default='E:/Zenderal/mods/Zenderal - Tree LOD 3D')
    ap.add_argument('--old-data', default='E:/Zenderal-backups/2026-10-19-pre-AE-migration/Stock game/Data')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    root = a.modlist

    if a.selftest:
        old = gb.BsaIndex(os.path.join(a.old_data, 'E - Meshes.bsa'))
        src = old.read(r'meshes\enderal\landscape\trees\nico\nehrimeseaspen01.nif')
        arb = open(os.path.join(root, 'mods', 'Enderal Arboreal Revived - For Vanilla EnderalSE', *LOD_DIR,
                                'nehrimeseaspen01_C3408765passthru_lod.nif'), 'rb').read()
        out = build(Nif(src))
        n = verify(src, out)
        ours, theirs = geometry(Nif(out)), geometry(Nif(arb))
        same = sorted((nm, p) for nm, p, t in ours) == sorted((nm, p) for nm, p, t in theirs)
        print('selftest: %d static shapes kept; same shape names and vertices as Arboreal\'s model: %s' % (n, same))
        if not same:
            raise SystemExit(1)
        return

    out_name = os.path.basename(a.out.rstrip('/\\'))
    mods = [m for m in gb.enabled_mods(root, a.profile) if m != out_name]
    plugins = gb.load_order(root, a.profile)
    bsas = [gb.BsaIndex(p) for p in gb.archives(root, mods, a.profile, plugins)]

    have = set()                                    # name_crc of every installed 3D tree LOD model
    for m in mods:
        d = os.path.join(root, 'mods', m, *LOD_DIR)
        if os.path.isdir(d):
            for f in os.listdir(d):
                mm = re.match(r'(.+_[0-9a-f]{8})', f, re.I)
                if mm and f.lower().endswith('.nif'):
                    have.add(mm.group(1).lower())

    report = open(os.path.join(root, 'Tools', 'DynDOLOD', 'Logs', 'DynDOLOD_EnderalSE_Tree_Report.txt'),
                  encoding='utf-8', errors='replace').read()
    todo, seen = [], set()
    for m in re.finditer(r'\n(\S+)(?: "[^"\n]*")? \[TREE:([0-9A-F]{8})\] (\S.*?\.nif) \[(?:Original )?CRC32:([0-9A-F]{8})\]', report):
        ed, rel, crc = m.group(1), m.group(3), m.group(4).lower()
        block = report[m.end():report.find('Mask:', m.end())]
        if 'Billboard found' not in block:
            continue                                # no billboard today = no LOD today; not ours to add
        name = os.path.basename(rel.replace(BS, '/'))[:-4].lower()
        key = '%s_%s' % (name, crc)
        if key in have or key in seen:
            continue
        seen.add(key)
        todo.append((ed, rel, name, crc))

    made, refused = [], []
    for ed, rel, name, crc in todo:
        src = None
        for mo in mods:
            f = os.path.join(root, 'mods', mo, *rel.split(BS))
            if os.path.isfile(f):
                b = open(f, 'rb').read()
                if '%08x' % zlib.crc32(b) == crc:
                    src = b; break
        if src is None:
            for bsa in reversed(bsas):
                if rel.lower() in bsa.files:
                    x = bsa.read(rel.lower())
                    if '%08x' % zlib.crc32(x) == crc:
                        src = x; break
        if src is None:
            refused.append((ed, name, crc, 'no copy with that CRC32')); continue
        try:
            try:
                out = build(Nif(src))
                n = verify(src, out)
            except Refuse as e:
                # PG Patcher's duplicate (Meshes\_pgpatcher_dups\N\...) carries its parallax shaders; build from the
                # original path instead when its static shapes are identical. The name keeps the duplicate's CRC32.
                mm = re.match(r'(?i)meshes\\_pgpatcher_dups\\\d+\\(.+)$', rel)
                if not mm or 'shader type' not in str(e):
                    raise
                orig_rel = 'meshes' + BS + mm.group(1)
                orig = None
                for mo in mods:
                    f = os.path.join(root, 'mods', mo, *orig_rel.split(BS))
                    if os.path.isfile(f) and mo != 'PG Patcher Output':
                        orig = open(f, 'rb').read(); break
                if orig is None:
                    orig = next((bsa.read(orig_rel.lower()) for bsa in reversed(bsas) if orig_rel.lower() in bsa.files), None)
                if orig is None or sorted(geometry(Nif(orig))) != sorted(geometry(Nif(src))):
                    raise Refuse('%s; original %s missing or shaped differently' % (e, orig_rel))
                out = build(Nif(orig))
                n = verify(orig, out)
        except (Refuse, struct.error, ValueError) as e:
            refused.append((ed, name, crc, str(e))); continue
        made.append((ed, name, crc, n, out))

    for ed, name, crc, why in refused:
        print('refuse %-44s %s_%s  %s' % (ed, name, crc, why))
    print('%d 3D tree LOD models built (%d refused)' % (len(made), len(refused)))
    files = {'%s_%spassthru_lod.nif' % (name, crc.upper()): out for ed, name, crc, n, out in made}

    # brighter foliage: our own builds, and the winning copy of every installed model BRIGHTEN names
    winners = {}
    for m in mods:                                  # highest priority first: the first copy of a name wins
        d = os.path.join(root, 'mods', m, *LOD_DIR)
        if os.path.isdir(d):
            for f in os.listdir(d):
                winners.setdefault(f.lower(), (f, os.path.join(d, f)))
    for low, (f, path) in sorted(winners.items()):
        if BRIGHTEN.match(f) and not any(k.lower() == low for k in files):
            files[f] = open(path, 'rb').read()
    for f in sorted(files):
        if BRIGHTEN.match(f):
            files[f], n = brighten(files[f], FOLIAGE_GAIN)
            print('brighter foliage x%.1f: %-46s %d leaf shapes' % (FOLIAGE_GAIN, f, n))

    if a.dry_run:
        for ed, name, crc, n, out in made:
            print('  %-44s %s_%s  %d shapes, %d bytes' % (ed, name, crc.upper(), n, len(out)))
        return
    if os.path.isdir(os.path.join(a.out, 'meshes')):
        shutil.rmtree(os.path.join(a.out, 'meshes'))
    d = os.path.join(a.out, *LOD_DIR)
    os.makedirs(d, exist_ok=True)
    for f, out in files.items():
        open(os.path.join(d, f), 'wb').write(out)
    print('wrote %d files to %s' % (len(files), d))


if __name__ == '__main__':
    main()
