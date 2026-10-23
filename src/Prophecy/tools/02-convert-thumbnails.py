"""Prophecy card thumbnails: the curator's PNG art -> the DDS the B612 card menu shows.

Input:  one PNG per perk named <perk EditorID>.png (e.g. ZP_Prophecy_Tripwire.png), default folder
        outputs/trait-icons/ (gitignored scratch where the art is generated).
Output: src/Prophecy/assets/interface/ProphecyPics/<EditorID>.dds - the path ZP_ProphecyMenu passes to B612
        ("ProphecyPics/<EditorID>.dds" under Interface/).
Format: 932 x 760, BC1/DXT1, one mip - identical to the list's Zenderal - Traits TraitPics (354,288 bytes each).
The square art is centre-cropped to 932:760 first (not stretched), then texconv (DirectXTex, shipped with xEdit)
resizes and compresses.

Usage: python -I src/Prophecy/tools/02-convert-thumbnails.py [art folder]
"""
import os, sys, re, glob, json, struct, zlib, shutil, subprocess, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, 'outputs', 'trait-icons')
OUT = os.path.join(REPO, 'src', 'Prophecy', 'assets', 'interface', 'ProphecyPics')
W, H = 932, 760


def texconv():
    tools = json.load(open(os.path.join(REPO, '.claude', 'config', 'tools.json'), encoding='utf-8-sig'))
    xedit = tools.get('xedit', '')
    p = os.path.join(os.path.dirname(xedit), 'Edit Scripts', 'Texconvx64.exe')
    assert os.path.isfile(p), f'texconv not found next to tools.json xedit: {p}'
    return p


def read_png(path):
    d = open(path, 'rb').read()
    assert d[:8] == b'\x89PNG\r\n\x1a\n', path
    i, idat, w = 8, b'', None
    while i < len(d):
        n, typ = struct.unpack('>I4s', d[i:i + 8]); body = d[i + 8:i + 8 + n]; i += 12 + n
        if typ == b'IHDR':
            w, h, bd, ct, _, _, il = struct.unpack('>IIBBBBB', body)
            assert bd == 8 and ct in (2, 6) and il == 0, f'{path}: need 8-bit RGB/RGBA non-interlaced'
            bpp = 3 if ct == 2 else 4
        elif typ == b'IDAT':
            idat += body
    raw = zlib.decompress(idat); stride = w * bpp; rows = []; prev = bytearray(stride); p = 0
    for _ in range(h):
        f = raw[p]; line = bytearray(raw[p + 1:p + 1 + stride]); p += 1 + stride
        for x in range(stride):
            a = line[x - bpp] if x >= bpp else 0; b = prev[x]; c = prev[x - bpp] if x >= bpp else 0
            if f == 1: line[x] = (line[x] + a) & 255
            elif f == 2: line[x] = (line[x] + b) & 255
            elif f == 3: line[x] = (line[x] + ((a + b) >> 1)) & 255
            elif f == 4:
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append(line); prev = line
    return w, h, bpp, rows


def write_png(path, w, h, bpp, rows):
    raw = b''.join(b'\0' + bytes(r) for r in rows)
    ch = lambda t, b: struct.pack('>I', len(b)) + t + b + struct.pack('>I', zlib.crc32(t + b) & 0xffffffff)
    ct = 2 if bpp == 3 else 6
    open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, ct, 0, 0, 0)) +
                           ch(b'IDAT', zlib.compress(raw, 6)) + ch(b'IEND', b''))


def main():
    tc = texconv()
    pngs = sorted(glob.glob(os.path.join(SRC, 'ZP_Prophecy_*.png')))
    assert pngs, f'no ZP_Prophecy_*.png in {SRC}'
    os.makedirs(OUT, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix='prophecypics_')
    try:
        for p in pngs:
            w, h, bpp, rows = read_png(p)
            # centre-crop to the target aspect
            if w / h > W / H:
                cw, ch_ = round(h * W / H), h
            else:
                cw, ch_ = w, round(w * H / W)
            x0, y0 = (w - cw) // 2, (h - ch_) // 2
            crop = [r[x0 * bpp:(x0 + cw) * bpp] for r in rows[y0:y0 + ch_]]
            name = os.path.splitext(os.path.basename(p))[0]
            cp = os.path.join(tmp, name + '.png')
            write_png(cp, cw, ch_, bpp, crop)
            r = subprocess.run([tc, '-nologo', '-y', '-f', 'BC1_UNORM', '-m', '1', '-w', str(W), '-h', str(H),
                                '-o', OUT, cp], capture_output=True, text=True)
            out = os.path.join(OUT, name + '.dds')
            for f in os.listdir(OUT):   # texconv writes .DDS; keep the extension the menu script asks for
                if f.lower() == name.lower() + '.dds' and f != name + '.dds':
                    os.rename(os.path.join(OUT, f), out)
            assert r.returncode == 0 and os.path.isfile(out), f'texconv failed on {name}: {r.stdout}{r.stderr}'
            d = open(out, 'rb').read(128)
            hh, ww = struct.unpack_from('<II', d, 12)
            assert (ww, hh) == (W, H) and d[84:88] == b'DXT1', f'{name}: got {ww}x{hh} {d[84:88]}'
            print(f'{name}: {w}x{h} -> crop {cw}x{ch_} -> {W}x{H} DXT1')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f'{len(pngs)} thumbnails -> {OUT}')


if __name__ == '__main__':
    main()
