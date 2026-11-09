"""Put the list's own logo into the main menu's `startmenu_logo.swf`. Run after 01 (01 wipes the mod folder).

The logo above the main-menu buttons is `Interface/deardiary_dm/startmenu/startmenu_logo.swf`, which Dear Diary's
start menu (Vel'dun UI) loads: one DefineBitsLossless2 bitmap (1536x1024 ARGB) drawn by one shape under a black
glow filter. Vel'dun's three Zenderal patches ship it with the old orb-and-ZENDERAL artwork, identical in all
three, so 01 copies it into this mod as a static file (the DLL never rewrites it).

This rebuilds that SWF with `assets/startmenu_logo.webp` (the curator's wordmark, 2026-11-06) fitted into the old
artwork's box - measured from the template bitmap's alpha, same width, centred - so the logo keeps its place on
screen. Everything else in the SWF (shape, matrices, glow) is kept byte for byte; the template is always the
Vel'dun patch's copy, never this mod's. Writes this mod's copy and, when present, the curator's `Zen's Ultrawide`
copy (which outranks this mod in Ultra).

Usage: python 03-build-startmenu-logo.py [<MO2 root>] [--preview <png>]      (default E:/Zenderal)
"""
import hashlib
import os
import struct
import sys
import zlib

import numpy as np
from PIL import Image

ARGV = sys.argv[1:]
PREVIEW = None
if "--preview" in ARGV:
    _k = ARGV.index("--preview")
    PREVIEW = ARGV[_k + 1]
    del ARGV[_k:_k + 2]
MO2 = ARGV[0] if ARGV else "E:/Zenderal"
HERE = os.path.dirname(os.path.abspath(__file__))
ASSET = os.path.join(HERE, "..", "assets", "startmenu_logo.webp")
REL = os.path.join("Interface", "deardiary_dm", "startmenu", "startmenu_logo.swf")
TEMPLATES = [os.path.join(MO2, "mods", f"Vel'dun Zenderal patches {k}", REL) for k in ("16x9", "21x9", "32x9")]
DESTS = [(os.path.join(MO2, "mods", "Zenderal - Aspect Layout", REL), True),
         (os.path.join(MO2, "mods", "Zen's Ultrawide - 3360x1440 - Do not use", REL), False)]  # (path, required)
ALPHA_MIN = 8  # a pixel counts as artwork above this alpha


def parse_swf(d):
    sig, ver = d[:3], d[3]
    if sig == b"CWS":
        body = zlib.decompress(d[8:])
    elif sig == b"FWS":
        body = d[8:]
    else:
        sys.exit(f"{sig!r} SWF (LZMA?) not handled")
    assert struct.unpack_from("<I", d, 4)[0] == 8 + len(body), "SWF header length does not match the body"
    return ver, body


def split_tags(body):
    """-> (movie header bytes, [(code, data bytes)])"""
    nbits = body[0] >> 3
    p = (5 + 4 * nbits + 7) // 8 + 4  # RECT + frame rate + frame count
    head, tags = body[:p], []
    while p < len(body):
        h = struct.unpack_from("<H", body, p)[0]
        code, ln = h >> 6, h & 0x3F
        p += 2
        if ln == 0x3F:
            ln = struct.unpack_from("<I", body, p)[0]
            p += 4
        tags.append((code, body[p:p + ln]))
        p += ln
    return head, tags


def tag_bytes(code, data):
    if len(data) < 0x3F:
        return struct.pack("<H", (code << 6) | len(data)) + data
    return struct.pack("<HI", (code << 6) | 0x3F, len(data)) + data


def decode_lossless2(data):
    """-> (character id, HxWx4 uint8 A,R,G,B with premultiplied colour)"""
    cid, fmt, w, h = struct.unpack_from("<HBHH", data, 0)
    assert fmt == 5, f"bitmap {cid}: format {fmt}, only 32-bit ARGB (5) handled"
    return cid, np.frombuffer(zlib.decompress(data[7:]), dtype=np.uint8).reshape(h, w, 4)


def encode_lossless2(cid, rgba):
    a = rgba[..., 3:4].astype(np.uint32)
    rgb = ((rgba[..., :3].astype(np.uint32) * a + 127) // 255).astype(np.uint8)  # premultiplied, as the format wants
    argb = np.concatenate([rgba[..., 3:4], rgb], axis=2)
    h, w = rgba.shape[:2]
    return struct.pack("<HBHH", cid, 5, w, h) + zlib.compress(argb.tobytes(), 9)


def bbox(alpha):
    ys, xs = np.where(alpha > ALPHA_MIN)
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def main():
    preview = PREVIEW
    tpl = [t for t in TEMPLATES if os.path.isfile(t)]
    assert tpl, "no Vel'dun Zenderal patch ships startmenu_logo.swf"
    assert len({hashlib.md5(open(t, "rb").read()).hexdigest() for t in tpl}) == 1, \
        "the Vel'dun Zenderal patches' startmenu_logo.swf differ: pick the template by hand"
    ver, body = parse_swf(open(tpl[0], "rb").read())
    head, tags = split_tags(body)
    codes = [c for c, _ in tags]
    assert codes.count(36) == 1 and not any(c in (6, 20, 21, 35, 90) for c in codes), f"expected one DefineBitsLossless2, tags {codes}"
    i = codes.index(36)
    cid, old = decode_lossless2(tags[i][1])
    H, W = old.shape[:2]
    x0, y0, x1, y1 = bbox(old[..., 0])
    bw, bh = x1 - x0, y1 - y0

    logo = np.asarray(Image.open(ASSET).convert("RGBA"))
    lx0, ly0, lx1, ly1 = bbox(logo[..., 3])
    logo = Image.fromarray(logo[ly0:ly1, lx0:lx1])
    scale = min(bw / logo.width, bh / logo.height)
    nw, nh = round(logo.width * scale), round(logo.height * scale)
    logo = logo.resize((nw, nh), Image.LANCZOS)
    px, py = x0 + (bw - nw) // 2, y0 + (bh - nh) // 2
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    canvas.paste(logo, (px, py))
    new = np.asarray(canvas)

    tags[i] = (36, encode_lossless2(cid, new))
    out_body = head + b"".join(tag_bytes(c, d) for c, d in tags)
    out = b"CWS" + bytes([ver]) + struct.pack("<I", 8 + len(out_body)) + zlib.compress(out_body, 9)

    # the result must re-parse to the template with only the bitmap's pixels changed
    ver2, body2 = parse_swf(out)
    head2, tags2 = split_tags(body2)
    assert ver2 == ver and head2 == head and [c for c, _ in tags2] == codes, "rebuilt SWF structure differs"
    assert all(tags2[j] == tags[j] for j in range(len(tags)) if j != i), "a tag other than the bitmap changed"
    cid2, back = decode_lossless2(tags2[i][1])
    assert cid2 == cid and back.shape == old.shape and np.array_equal(back[..., 0], new[..., 3]), "bitmap round trip failed"
    assert bbox(back[..., 0]) == (px, py, px + nw, py + nh), "the new artwork is not where it was placed"

    for dst, required in DESTS:
        if not os.path.isfile(dst):
            assert not required, f"{dst} missing: run 01-build-layout-sets.py first"
            print(f"skip (absent): {dst}")
            continue
        with open(dst, "wb") as f:
            f.write(out)
        print(f"wrote {dst} ({len(out)} bytes)")
    print(f"template {tpl[0]}: bitmap {cid} {W}x{H}, old artwork box x {x0}-{x1} y {y0}-{y1} ({bw}x{bh}); "
          f"new logo {logo.width}x{logo.height} at ({px}, {py}), scale {scale:.3f}")
    if preview:
        pair = Image.new("RGB", (W * 2 + 16, H), (40, 40, 40))
        pair.paste(Image.fromarray(np.ascontiguousarray(old[..., 1:4])), (0, 0))  # premultiplied colour = the old art over black
        pair.paste(canvas, (W + 16, 0), canvas)
        pair.save(preview)
        print(f"preview {preview}")


if __name__ == "__main__":
    main()
