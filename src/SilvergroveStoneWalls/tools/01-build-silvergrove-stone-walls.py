"""Build `Zenderal - Silvergrove Stone Walls`: Skyrim 202X's farmhouse cobbles, warmed and tiled, on Enderal's
Silvergrove stone walls (`wall01-03.nif`: `_00E_Tropical_ClayHouseWall*`, Old Ishmorlep / Duneville / the desert).

Those three meshes are the only ones in the list that use `silvergrove\\brickwall01` (scan of every winning mesh,
loose and in the mesh BSAs). Each is a baked unwrap into one quarter of that 2048 texture, about 2.5 texels per
game unit, so the stones read as smeared blobs; SRP and ETATU only upscaled the same 2014 art. This:

  * copies SRP's three meshes (the winners under PG Patcher Output, which only re-points them at SPR PBR's copy
    of the same art) and gives every triangle a box projection picked by which way the FACE points in the wall's
    own frame (long axis L, thickness axis W, up Z): out of the wall -> (L, Z), along it (ends and the jagged
    stone flanks) -> (W, Z), up/down (cap) -> (L, W). One texture repeat per TILE units. A vertex shared by faces
    of different classes is duplicated, one copy per class (position, normal and vertex colour copied), so no
    triangle ever spans two projections; that is what stretched one texture column across the flanks in v1;
  * recomputes every vertex's tangent and bitangent from the new UVs. Which stored vector is dP/du and which is
    dP/dv, and their signs, are learned from the ORIGINAL mesh (recomputing them from the original UVs must
    reproduce the stored ones), so the normal map lights the right way;
  * rewrites the BSTriShape block (new vertex count, vertex buffer, triangles, data size) and the header's
    block-size entry for it; every other block keeps its bytes;
  * writes 202X's `stonewall01` diffuse colour-matched (mean/std per CIELAB channel, computed here in numpy) to
    Enderal's brickwall01, so the meshes' own vertex colours tint it the warm red-brown they tinted the old one;
    202X's normal and height map are copied unchanged. All three go to the brickwall01 paths, which nothing
    else uses. (v1 used Pillow's LAB mode, whose a/b bytes are SIGNED: green moss wrapped round to magenta.)

Every file is derived from the user's own install (SRP, Skyrim 202X, Enderal), so nothing here is committed.

Usage:  python 01-build-silvergrove-stone-walls.py [<MO2 root>] [--tile N] [--dry-run]     (default E:/Zenderal)
"""
import os
import shutil
import struct
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'HorseCloakFluffFix', 'tools'))
from nif import Nif, Reader  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('--')]
MO2 = args[0] if args else 'E:/Zenderal'
DRY = '--dry-run' in sys.argv
TILE = float(sys.argv[sys.argv.index('--tile') + 1]) if '--tile' in sys.argv else 160.0

MOD = 'Zenderal - Silvergrove Stone Walls'
MESH_SRC = 'SRP Enderal - Architecture (2K)'
TEX_SRC = '-Skyrim 202X 10.0.1 - Architecture PART 1'
MESH_DIR = 'meshes/enderal/architecture/silvergrove'
TEX_DIR = 'textures/enderal/architecture/silvergrove'
# (mesh, texture its stone shape uses, projection frame). 'wall' = PCA long axis / thickness / up; 'world' = X/Y/Z
# box projection for the round well (`_00E_Tropical_ClayHouseWell 08A241`, the only user of well.dds). Shapes on
# any other texture (the well's wood and black shapes) are left byte-identical.
TARGETS = (
    ('wall01.nif', 'brickwall01', 'wall'),
    ('wall02.nif', 'brickwall01', 'wall'),
    ('wall03.nif', 'brickwall01', 'wall'),
    ('well.nif', 'well', 'world'),
)
X_DIR = 'textures/architecture/farmhouse'
REF_DIFFUSE = os.path.join(MO2, 'mods', MESH_SRC, TEX_DIR, 'brickwall01.dds')    # colour target (SureAI's art)
TEXCONV = os.path.join(MO2, 'Tools', 'DynDOLOD', 'Edit Scripts', 'Texconvx64.exe')
DIFFUSE_SIZE = 4096                                   # 202X ships 8192; 4096 matches its normal map

# Vertex layout every one of the three meshes must have (asserted): 32 bytes, position + bitangent X float,
# half-float UV, normal + bitangent Y bytes, tangent + bitangent Z bytes, vertex colour.
FLAGS = 0x3B
OFFSETS = dict(uv=16, normal=20, tangent=24, color=28)
VSIZE = 32


# --- vertex buffer helpers -------------------------------------------------------------------------------
def vbuf(nif, sh):
    base, vs, n = sh['vdata'], sh['vsize'], sh['nvert']
    return np.frombuffer(bytes(nif.data[base:base + vs * n]), np.uint8).reshape(n, vs).copy()


def unbyte(b):
    return b.astype(np.float64) / 255.0 * 2.0 - 1.0


def tobyte(v):
    return np.clip(np.round((v + 1.0) / 2.0 * 255.0), 0, 255).astype(np.uint8)


def read_frame(buf):
    """Stored normal, the two stored tangent-space vectors (as the file names them), UVs."""
    n = unbyte(buf[:, 20:23])
    t = unbyte(buf[:, 24:27])
    b = np.stack([buf[:, 12:16].copy().view('<f4')[:, 0].astype(np.float64),
                  unbyte(buf[:, 23]), unbyte(buf[:, 27])], 1)
    uv = buf[:, 16:20].copy().view('<f2').astype(np.float64).reshape(-1, 2)
    return n, t, b, uv


def derivs(pos, tris, uv, normal):
    """Per-vertex dP/du and dP/dv (summed over faces), orthogonalised against the vertex normal."""
    du = np.zeros_like(pos)
    dv = np.zeros_like(pos)
    p0, p1, p2 = pos[tris[:, 0]], pos[tris[:, 1]], pos[tris[:, 2]]
    u0, u1, u2 = uv[tris[:, 0]], uv[tris[:, 1]], uv[tris[:, 2]]
    e1, e2 = p1 - p0, p2 - p0
    d1, d2 = u1 - u0, u2 - u0
    det = d1[:, 0] * d2[:, 1] - d2[:, 0] * d1[:, 1]
    ok = np.abs(det) > 1e-12
    r = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)[:, None]
    fu = (e1 * d2[:, 1:2] - e2 * d1[:, 1:2]) * r
    fv = (e2 * d1[:, 0:1] - e1 * d2[:, 0:1]) * r
    for k in range(3):
        np.add.at(du, tris[:, k], fu)
        np.add.at(dv, tris[:, k], fv)
    out = []
    for d in (du, dv):
        d = d - normal * (d * normal).sum(1, keepdims=True)
        ln = np.linalg.norm(d, axis=1, keepdims=True)
        out.append(np.where(ln > 1e-9, d / np.where(ln > 1e-9, ln, 1.0), 0.0))
    return out


def learn_mapping(t, b, du, dv):
    """Which recomputed derivative (and sign) reproduces each stored vector; returns (src for t, src for b, scores)."""
    cands = {'du': du, '-du': -du, 'dv': dv, '-dv': -dv}

    def best(stored):
        unit = stored / np.maximum(np.linalg.norm(stored, axis=1, keepdims=True), 1e-9)
        score = {k: float(np.mean((unit * c).sum(1))) for k, c in cands.items()}
        k = max(score, key=score.get)
        return k, score[k]
    kt, st = best(t)
    kb, sb = best(b)
    return kt, kb, st, sb


def pick(name, du, dv):
    return {'du': du, '-du': -du, 'dv': dv, '-dv': -dv}[name]


def wall_frame(pos, mode='wall'):
    """Unit long axis L and thickness axis W in the horizontal plane (PCA), plus Z; world X/Y/Z for 'world'."""
    if mode == 'world':
        return np.array([1.0, 0.0, 0.0]), np.array([0.0, 1.0, 0.0]), np.array([0.0, 0.0, 1.0])
    xy = pos[:, :2] - pos[:, :2].mean(0)
    _, vecs = np.linalg.eigh(np.cov(xy.T))
    L = np.array([vecs[0, 1], vecs[1, 1], 0.0])
    W = np.array([vecs[0, 0], vecs[1, 0], 0.0])
    return L, W, np.array([0.0, 0.0, 1.0])


def split_by_projection(pos, tris, mode='wall'):
    """Per-face projection class (0: faces out of the wall, 1: along it, 2: up/down) and the split mesh:
    returns (old-vertex index for each new vertex, class of each new vertex, new triangles, per-class counts)."""
    L, W, Z = wall_frame(pos, mode)
    fn = np.cross(pos[tris[:, 1]] - pos[tris[:, 0]], pos[tris[:, 2]] - pos[tris[:, 0]])
    comp = np.abs(np.stack([fn @ W, fn @ L, fn @ Z], 1))
    cls = comp.argmax(1)
    key = {}
    src, vcls = [], []
    new_tris = np.empty_like(tris)
    for f in range(len(tris)):
        for k in range(3):
            kk = (int(tris[f, k]), int(cls[f]))
            if kk not in key:
                key[kk] = len(src)
                src.append(kk[0])
                vcls.append(kk[1])
            new_tris[f, k] = key[kk]
    return np.array(src), np.array(vcls), new_tris, np.bincount(cls, minlength=3), (L, W, Z)


def project(pos, vcls, frame):
    L, W, Z = frame
    c = pos - pos.mean(0)
    l, w, z = c @ L, c @ W, c @ Z
    u = np.select([vcls == 0, vcls == 1, vcls == 2], [l, w, l])
    v = np.select([vcls == 0, vcls == 1, vcls == 2], [-z, -z, w])
    uv = np.stack([u, v], 1) / TILE
    return uv - np.floor(uv.min(0))


def sizes_table_offset(data):
    """Byte offset of the header's per-block size table (same walk as nif.Nif.__init__)."""
    r = Reader(data, data.index(b'\n') + 1)
    r.skip(4 + 1 + 4)
    nblocks = r.take('I')
    r.skip(4)
    for _ in range(3):
        r.skip(r.take('B'))
    ntypes = r.take('H')
    for _ in range(ntypes):
        r.skip(r.take('I'))
    r.skip(2 * nblocks)
    return r.p


def diffuse_of(nif, shader_block):
    """First (diffuse) path of a BSLightingShaderProperty's BSShaderTextureSet, lower-case."""
    r = Reader(nif.data, nif.blocks[shader_block][1])
    r.skip(4 + 4)                                        # skyrim shader type, name
    r.skip(4 * r.take('I'))                              # extra data refs
    r.skip(4 + 8 + 16)                                   # controller, shader flags 1+2, uv offset + scale
    ts = r.take('i')
    assert nif.blocks[ts][0] == 'BSShaderTextureSet'
    rr = Reader(nif.data, nif.blocks[ts][1])
    rr.skip(4)                                           # texture count
    n = rr.take('I')
    return bytes(nif.data[rr.p:rr.p + n]).decode('latin1').lower()


def rebuild_mesh(src, dst, texture, mode):
    nif = Nif(src)
    want = f'{TEX_DIR}/{texture}.dds'.replace('/', '\\')
    shapes = [s for s in nif.shapes() if diffuse_of(nif, s['shader']) == want]
    assert len(shapes) == 1, (src, want, [diffuse_of(nif, s['shader']) for s in nif.shapes()])
    sh = shapes[0]
    flags = sh['desc'] >> 44
    offs = {k: ((sh['desc'] >> (4 * i)) & 0xF) * 4 for k, i in (('uv', 2), ('normal', 4), ('tangent', 5), ('color', 6))}
    assert flags == FLAGS and sh['vsize'] == VSIZE and offs == OFFSETS, (src, hex(flags), sh['vsize'], offs)
    assert sh['dsize'] == sh['nvert'] * VSIZE + sh['ntri'] * 6, 'data size must be vertices + triangles'
    buf = vbuf(nif, sh)
    pos = nif.positions(sh)
    tris = sh['tris'].astype(np.int64)
    n, t, b, uv0 = read_frame(buf)

    du0, dv0 = derivs(pos, tris, uv0, n)
    kt, kb, st, sb = learn_mapping(t, b, du0, dv0)
    assert {kt.strip('-'), kb.strip('-')} == {'du', 'dv'} and st > 0.85 and sb > 0.85, (src, kt, kb, st, sb)

    srcv, vcls, tris1, counts, frame = split_by_projection(pos, tris, mode)
    assert len(srcv) < 65536
    pos1, n1 = pos[srcv], n[srcv]
    uv1 = project(pos1, vcls, frame)
    assert np.abs(uv1).max() < 2000, 'UV out of half-float precision range'
    du1, dv1 = derivs(pos1, tris1, uv1, n1)
    t1, b1 = pick(kt, du1, dv1), pick(kb, du1, dv1)

    out = buf[srcv].copy()                                 # position, normal, colour carried from the source vertex
    out[:, 16:20] = uv1.astype('<f2').view(np.uint8).reshape(-1, 4)
    out[:, 24:27] = tobyte(t1)
    out[:, 12:16] = b1[:, 0].astype('<f4').view(np.uint8).reshape(-1, 4)
    out[:, 23] = tobyte(b1[:, 1])
    out[:, 27] = tobyte(b1[:, 2])
    for a, z in ((0, 12), (20, 23), (28, 32)):
        assert (out[:, a:z] == buf[srcv, a:z]).all()

    # rewrite the BSTriShape block: header fields up to ntri/nvert, new vertex + triangle data, old tail
    _, bpos, bsize = nif.blocks[sh['block']]
    head_end = sh['vdata'] - 8                             # ntri(H) nvert(H) dsize(I) sit right before the data
    old_end = sh['vdata'] + sh['nvert'] * VSIZE + sh['ntri'] * 6
    nv, nt = len(out), len(tris1)
    block = (bytes(nif.data[bpos:head_end]) + struct.pack('<HHI', nt, nv, nv * VSIZE + nt * 6)
             + out.tobytes() + tris1.astype('<u2').tobytes() + bytes(nif.data[old_end:bpos + bsize]))
    data = bytearray(nif.data[:bpos]) + block + nif.data[bpos + bsize:]
    so = sizes_table_offset(data)
    assert struct.unpack_from('<I', data, so + 4 * sh['block'])[0] == bsize
    struct.pack_into('<I', data, so + 4 * sh['block'], len(block))

    # parse the result back and check it holds exactly what was written
    tmp = dst + '.check' if not DRY else os.path.join(tempfile.gettempdir(), os.path.basename(src) + '.check')
    os.makedirs(os.path.dirname(tmp), exist_ok=True)
    open(tmp, 'wb').write(data)
    chk = Nif(tmp)
    csh = next(s for s in chk.shapes() if s['block'] == sh['block'])
    assert (csh['nvert'], csh['ntri']) == (nv, nt) and np.allclose(chk.positions(csh), pos1)
    assert [x[0] for x in chk.blocks] == [x[0] for x in nif.blocks]
    for i, (typ, p0, s0) in enumerate(nif.blocks):          # every other block byte-identical
        if i != sh['block']:
            _, p1, s1 = chk.blocks[i]
            assert bytes(nif.data[p0:p0 + s0]) == bytes(chk.data[p1:p1 + s1]), (src, i, typ)
    if DRY:
        os.remove(tmp)
    else:
        os.replace(tmp, dst)
    reps = np.ptp(uv1, 0)
    print(f'  {os.path.basename(src)}: {sh["nvert"]} -> {nv} verts ({nt} tris; faces out/along/up {counts.tolist()}); '
          f'tangent=stored<-{kt} ({st:.2f}), bitangent=stored<-{kb} ({sb:.2f}); UV {reps[0]:.1f} x {reps[1]:.1f} repeats')


# --- textures ------------------------------------------------------------------------------------------
def texconv(src, outdir, *extra):
    r = subprocess.run([TEXCONV, '-nologo', '-y', '-o', outdir, *extra, src], capture_output=True, text=True)
    assert r.returncode == 0 and 'FAILED' not in r.stdout, r.stdout + r.stderr


_M = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])
_WHITE = np.array([0.95047, 1.0, 1.08883])


def srgb_to_lab(rgb):
    c = rgb / 255.0
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    xyz = lin @ _M.T / _WHITE
    f = np.where(xyz > (6 / 29) ** 3, np.cbrt(xyz), xyz / (3 * (6 / 29) ** 2) + 4 / 29)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def lab_to_srgb(lab):
    fy = (lab[..., 0] + 16) / 116
    f = np.stack([fy + lab[..., 1] / 500, fy, fy - lab[..., 2] / 200], -1)
    xyz = np.where(f > 6 / 29, f ** 3, 3 * (6 / 29) ** 2 * (f - 4 / 29)) * _WHITE
    lin = np.clip(xyz @ np.linalg.inv(_M).T, 0, 1)
    c = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055)
    return np.clip(np.round(c * 255), 0, 255).astype(np.uint8)


def recolour(src_png, ref_png, dst_png):
    src = np.asarray(Image.open(src_png).convert('RGB')).astype(np.float64)
    ref = np.asarray(Image.open(ref_png).convert('RGB')).astype(np.float64)
    a, r = srgb_to_lab(src), srgb_to_lab(ref)
    for c in range(3):
        a[..., c] = (a[..., c] - a[..., c].mean()) * (r[..., c].std() / max(a[..., c].std(), 1e-6)) + r[..., c].mean()
    out = lab_to_srgb(a)
    Image.fromarray(out, 'RGB').save(dst_png)
    m = lambda im: [round(float(x)) for x in im.reshape(-1, 3).mean(0)]
    # the old magenta bug showed as a > 40 in a texture whose reference has none
    print(f'  diffuse: 202X mean RGB {m(src)} -> {m(out.astype(np.float64))} (Enderal brickwall01 {m(ref)}); '
          f'texels with a* > 30: {float((srgb_to_lab(out.astype(np.float64))[..., 1] > 30).mean()):.4%} '
          f'(reference {float((r[..., 1] > 30).mean()):.4%})')


def build_textures(out_tex):
    xdir = os.path.join(MO2, 'mods', TEX_SRC, X_DIR)
    for f in ('stonewall01.dds', 'stonewall01_n.dds', 'stonewall01_p.dds'):
        assert os.path.isfile(os.path.join(xdir, f)), f
    assert os.path.isfile(REF_DIFFUSE), REF_DIFFUSE
    if DRY:
        print('  (dry run: textures not written)')
        return
    os.makedirs(out_tex, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        texconv(os.path.join(xdir, 'stonewall01.dds'), tmp, '-ft', 'png', '-w', str(DIFFUSE_SIZE), '-h', str(DIFFUSE_SIZE), '-m', '1')
        shutil.copy(REF_DIFFUSE, os.path.join(tmp, 'ref.dds'))
        texconv(os.path.join(tmp, 'ref.dds'), tmp, '-ft', 'png', '-m', '1')
        recolour(os.path.join(tmp, 'stonewall01.png'), os.path.join(tmp, 'ref.png'), os.path.join(tmp, 'brickwall01.png'))
        texconv(os.path.join(tmp, 'brickwall01.png'), out_tex, '-f', 'BC7_UNORM', '-m', '0')
    shutil.copy(os.path.join(xdir, 'stonewall01_n.dds'), os.path.join(out_tex, 'brickwall01_n.dds'))
    shutil.copy(os.path.join(xdir, 'stonewall01_p.dds'), os.path.join(out_tex, 'brickwall01_p.dds'))
    for f in ('brickwall01.dds', 'brickwall01_n.dds', 'brickwall01_p.dds'):
        print(f'  {f}: {os.path.getsize(os.path.join(out_tex, f)):,} bytes')


def main():
    out = os.path.join(MO2, 'mods', MOD)
    print(f'{MOD}: tile {TILE:g} units{" (dry run)" if DRY else ""}')
    for m, texture, mode in TARGETS:
        src = os.path.join(MO2, 'mods', MESH_SRC, MESH_DIR, m)
        assert os.path.isfile(src), src
        dst = os.path.join(out, MESH_DIR, m)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        rebuild_mesh(src, dst, texture, mode)
    tex = os.path.join(out, TEX_DIR)
    build_textures(tex)
    if not DRY:
        # the well's stones get the same material (only well.nif uses well*.dds)
        for suffix in ('', '_n', '_p'):
            shutil.copy(os.path.join(tex, f'brickwall01{suffix}.dds'), os.path.join(tex, f'well{suffix}.dds'))
        meta = os.path.join(out, 'meta.ini')
        with open(meta, 'w', encoding='utf-8', newline='\r\n') as f:
            f.write('[General]\ngameName=EnderalSE\nmodid=0\nversion=1.2.0\n'
                    'comments=Generated by zenderal-patches src/SilvergroveStoneWalls/tools/01. '
                    'Its 4 meshes are in PGPatcher\'s blocklist; sort ABOVE PG Patcher Output.\n')


if __name__ == '__main__':
    main()
