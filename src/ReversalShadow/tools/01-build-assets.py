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

Shot sound (curator 2026-10-18): --shot <wav>, repeatable, mixes the curator's own sound files into
  sound/fx/Zenderal/ReversalShadow/ReversalShadowShot.wav
which SNDR ZP_ReversalShadowShotSD 808 plays (tools/02). The layers all start at 0 and are summed;
if the sum would clip, the whole mix is scaled down to a 32000 peak. Inputs must be uncompressed 16- or
24-bit PCM with the same channel count; 24-bit is cut to 16-bit and other rates are resampled (linear) to
the first layer's rate. The files are the curator's, not
committed. Without --shot an existing copy is kept. Current mix:
  --shot "Lazer Gun Shot 3.wav" --shot "Breathing Echo 2.wav" --shot "MA_CMDSOUND_Gun_Sound_03.wav"

Usage:  python 01-build-assets.py [<mods dir>] [--preview <png path>] [--shot <wav> ...]   (default E:/Zenderal/mods)
"""
import array
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


SHOT_DST = 'sound/fx/Zenderal/ReversalShadow/ReversalShadowShot.wav'


def read_pcm(src):
    d = open(src, 'rb').read()
    if d[:4] != b'RIFF' or d[8:12] != b'WAVE':
        raise SystemExit(f'{src}: not a RIFF WAVE file')
    p = 12
    fmt = data = None
    while p + 8 <= len(d):
        cid, size = d[p:p + 4], struct.unpack_from('<I', d, p + 4)[0]
        if cid == b'fmt ':
            fmt = struct.unpack_from('<HHIIHH', d, p + 8)
        elif cid == b'data':
            data = d[p + 8:p + 8 + size]
        p += 8 + size + (size & 1)
    if not fmt or fmt[0] != 1 or fmt[5] not in (16, 24) or data is None:
        raise SystemExit(f'{src}: need uncompressed 16- or 24-bit PCM, got {fmt}')
    if fmt[5] == 16:
        samples = array.array('h')
        samples.frombytes(data[:len(data) - len(data) % 2])
    else:   # 24-bit little-endian -> 16-bit (keep the top two bytes)
        samples = array.array('h', (int.from_bytes(data[i + 1:i + 3], 'little', signed=True)
                                    for i in range(0, len(data) - len(data) % 3, 3)))
    return fmt, samples


def resample(samples, ch, src_rate, dst_rate):
    """Linear interpolation, per channel."""
    if src_rate == dst_rate:
        return samples
    frames = len(samples) // ch
    out_frames = int(frames * dst_rate / src_rate)
    out = array.array('h', bytes(2 * out_frames * ch))
    step = src_rate / dst_rate
    for j in range(out_frames):
        pos = j * step
        i = int(pos)
        f = pos - i
        i2 = min(i + 1, frames - 1)
        for c in range(ch):
            a = samples[i * ch + c]
            b = samples[i2 * ch + c]
            out[j * ch + c] = int(round(a + (b - a) * f))
    return out


def mix_shot(srcs, dst):
    layers = [read_pcm(s) for s in srcs]
    fmt = layers[0][0]
    for k, (s, (f, x)) in enumerate(zip(srcs, layers)):
        if f[1] != fmt[1]:
            raise SystemExit(f'{s}: {f[1]} channels, first layer has {fmt[1]}')
        if f[2] != fmt[2]:   # resample to the first layer's rate
            layers[k] = (f, resample(x, f[1], f[2], fmt[2]))
    n = max(len(x) for _, x in layers)
    n -= n % fmt[1]
    total = [0] * n
    for _, x in layers:
        for i, v in enumerate(x[:n]):
            total[i] += v
    peak = max(1, max(abs(v) for v in total))
    scale = min(1.0, 32000 / peak)
    out = array.array('h', (int(round(v * scale)) for v in total))
    data = out.tobytes()
    ch, rate = fmt[1], fmt[2]
    header = (b'RIFF' + struct.pack('<I', 36 + len(data)) + b'WAVE'
              + b'fmt ' + struct.pack('<IHHIIHH', 16, 1, ch, rate, rate * ch * 2, ch * 2, 16)
              + b'data' + struct.pack('<I', len(data)))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, 'wb').write(header + data)
    print(f'sound   -> {dst}  ({len(srcs)} layers, {ch} ch, {rate} Hz, {n / ch / rate:.2f} s, '
          f'peak {peak}, scale {scale:.3f})')


def main(argv):
    shots = []
    while '--shot' in argv:
        k = argv.index('--shot')
        shots.append(argv[k + 1])
        del argv[k:k + 2]
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
    if shots:
        mix_shot(shots, os.path.join(out_root, SHOT_DST))
    if preview:
        write_preview(tex, preview)
        print('preview ->', preview)


if __name__ == '__main__':
    main(sys.argv[1:])
