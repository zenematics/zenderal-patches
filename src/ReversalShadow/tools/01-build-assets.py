"""Generate Reversal Shadow's black-and-silver meshes and texture into its MO2 mod.

Reversal Shadow is the Priest's Dueling Pistol (A Gentleman's Flintlock Armoury,
FlintlockPistol02.nif) recoloured: the black stock stays black, the steel goes
blackened, and every copper/green inlay turns silver. Nothing here is committed;
the inputs are the curator's installed mods:

  texture  <mods>/A Gentleman's Flintlock Armoury - Special Edition/
             textures/PowderMagePack/weapons/BattlestainedFP/FlintBlackBase_d.dds
  world    <same mod>/meshes/PowderMagePack/weapons/BattlestainedFP/FlintlockPistol02.nif
  held     <mods>/Zenderal - Loop Pistol Animations/
             meshes/Zenderal/LoopPistols/BattlestainedFP/FlintlockPistol02.nif
           (the rotated copy src/LoopPistolAnims/tools/02 makes; the FirstPersonModel
           static is the equipped model in third person too)

Outputs, into <mods>/Zenderal - Reversal Shadow/:
  textures/PowderMagePack/weapons/BattlestainedFP/FlintRevShadow_d.dds
  meshes/Zenderal/ReversalShadow/ReversalShadow.nif      (world / dropped model)
  meshes/Zenderal/ReversalShadow/ReversalShadow1st.nif   (equipped model)

The meshes are byte copies with ONE string changed: the diffuse path
'flintblackbase_d.dds' -> 'flintrevshadow_d.dds'. Same length, so no block size
or offset moves; the script asserts exactly one occurrence per mesh.

The texture is uncompressed 24-bit BGR with a full mip chain (as shipped); each
mip level is recoloured in place, so the header is reused verbatim.

Usage:  python 01-build-assets.py [<mods dir>] [--preview <png path>]   (default E:/Zenderal/mods)
"""
import os
import struct
import sys
import zlib

GENTLEMAN = "A Gentleman's Flintlock Armoury - Special Edition"
LOOP = 'Zenderal - Loop Pistol Animations'
MOD = 'Zenderal - Reversal Shadow'

TEX_DIR = 'textures/PowderMagePack/weapons/BattlestainedFP'
SRC_TEX = 'FlintBlackBase_d.dds'
DST_TEX = 'FlintRevShadow_d.dds'
OLD_PATH = b'flintblackbase_d.dds'
NEW_PATH = b'flintrevshadow_d.dds'
assert len(OLD_PATH) == len(NEW_PATH)

MESHES = [
    (os.path.join(GENTLEMAN, 'meshes/PowderMagePack/weapons/BattlestainedFP/FlintlockPistol02.nif'),
     'meshes/Zenderal/ReversalShadow/ReversalShadow.nif'),
    (os.path.join(LOOP, 'meshes/Zenderal/LoopPistols/BattlestainedFP/FlintlockPistol02.nif'),
     'meshes/Zenderal/ReversalShadow/ReversalShadow1st.nif'),
]


def smooth(e0, e1, x):
    t = (x - e0) / (e1 - e0)
    t = 0.0 if t < 0 else 1.0 if t > 1 else t
    return t * t * (3 - 2 * t)


def recolor(b, g, r):
    """BGR in, BGR out. Saturated bright pixels (copper, green, red inlays) -> silver;
    everything else (stock, steel) -> near-black, keeping its luminance detail."""
    mx = max(r, g, b)
    mn = min(r, g, b)
    sat = (mx - mn) / mx if mx else 0.0
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    w = smooth(0.22, 0.45, sat) * smooth(95, 140, mx)
    v = min(255.0, 60 + lum * 1.25)          # bright, slightly cool silver
    k = lum * 0.35                            # blackened steel / ebony
    ob = w * min(255.0, v + 6) + (1 - w) * (k + 2)
    og = w * v + (1 - w) * k
    orr = w * max(0.0, v - 4) + (1 - w) * k
    return int(ob + 0.5), int(og + 0.5), int(orr + 0.5)


def build_texture(src, dst):
    data = bytearray(open(src, 'rb').read())
    h, w = struct.unpack('<II', data[12:20])
    mips = struct.unpack('<I', data[28:32])[0] or 1
    fourcc = bytes(data[84:88])
    bits, rmask, gmask, bmask = struct.unpack('<4I', data[88:104])
    if fourcc != b'\0\0\0\0' or bits != 24 or (rmask, gmask, bmask) != (0xff0000, 0xff00, 0xff):
        raise SystemExit(f'{src}: expected uncompressed 24-bit BGR, got {fourcc} {bits} bits')
    cache = {}
    off = 128
    for _ in range(mips):
        n = w * h
        for i in range(off, off + n * 3, 3):
            key = bytes(data[i:i + 3])
            out = cache.get(key)
            if out is None:
                out = bytes(recolor(key[0], key[1], key[2]))
                cache[key] = out
            data[i:i + 3] = out
        off += n * 3
        w, h = max(1, w // 2), max(1, h // 2)
    if off != len(data):
        raise SystemExit(f'{src}: mip chain ends at {off}, file is {len(data)} bytes')
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, 'wb').write(data)
    return data


def write_preview(data, path, level=2):
    h, w = struct.unpack('<II', data[12:20])
    off = 128
    for _ in range(level):
        off += w * h * 3
        w, h = w // 2, h // 2
    rows = []
    for y in range(h):
        r = data[off + y * w * 3: off + (y + 1) * w * 3]
        rows.append(b'\0' + bytes(c for i in range(w) for c in (r[i * 3 + 2], r[i * 3 + 1], r[i * 3])))

    def chunk(t, d):
        c = t + d
        return struct.pack('>I', len(d)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)
    open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
                           + chunk(b'IDAT', zlib.compress(b''.join(rows), 6)) + chunk(b'IEND', b''))


def build_mesh(src, dst):
    data = open(src, 'rb').read()
    low = data.lower()
    hits = low.count(OLD_PATH)
    if hits != 1:
        raise SystemExit(f'{src}: expected 1 occurrence of {OLD_PATH!r}, found {hits}')
    i = low.index(OLD_PATH)
    out = data[:i] + NEW_PATH + data[i + len(OLD_PATH):]
    assert len(out) == len(data)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, 'wb').write(out)


def main(argv):
    preview = None
    if '--preview' in argv:
        k = argv.index('--preview')
        preview = argv[k + 1]
        del argv[k:k + 2]
    mods = argv[0] if argv else 'E:/Zenderal/mods'
    out_root = os.path.join(mods, MOD)
    tex = build_texture(os.path.join(mods, GENTLEMAN, TEX_DIR, SRC_TEX), os.path.join(out_root, TEX_DIR, DST_TEX))
    print('texture ->', os.path.join(out_root, TEX_DIR, DST_TEX))
    for src, dst in MESHES:
        build_mesh(os.path.join(mods, src), os.path.join(out_root, dst))
        print('mesh    ->', os.path.join(out_root, dst))
    if preview:
        write_preview(tex, preview)
        print('preview ->', preview)


if __name__ == '__main__':
    main(sys.argv[1:])
