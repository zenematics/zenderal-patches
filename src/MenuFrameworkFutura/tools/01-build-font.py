"""SKSE Menu Framework in regular (non-condensed) Futura: build MainFont.ttf from Vel'dun UI's Futura Book BT.

SKSE Menu Framework draws every window (its control panel, Local Map Upgrade, Prophecy v3) in `PrimaryFont`. The
list's SKSEMenuFramework.ini (Zenderal - Input Defaults / Personal Keybinds) already asks for `MainFont.ttf`, which
SMF loads from Data/SKSE/Plugins/Fonts/; nothing provided it, so SMF fell back to the game's Futura Condensed
(its log: "Primary font 'MainFont.ttf' failed to load"). Vel'dun UI (Enderal Default) maps the game's menus to
regular Futura Book BT from its Interface/fonts_futura.swf, but SMF's SWF font reader loads 0 faces from that file.

This converts that SWF font (DefineFont3: quadratic outlines on a 1024 em, so exact) into a TrueType file at
<MO2 mods>/Zenderal - Menu Framework Futura/SKSE/Plugins/Fonts/MainFont.ttf. NOT committed: Futura Book BT is a
Bitstream font that Vel'dun distributes; this only re-wraps it for the same list. No kerning is carried over.

Usage: python -I src/MenuFrameworkFutura/tools/01-build-font.py [<MO2 mods dir>]
"""
import os, sys, struct

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import swffont  # noqa: E402

MOD = 'Zenderal - Menu Framework Futura'
SRC = os.path.join("Vel'dun UI Enderal Default", 'Interface', 'fonts_futura.swf')
EM = 1024
FAMILY, STYLE = 'Futura Book BT', 'Regular'


def checksum(data):
    data += b'\0' * (-len(data) % 4)
    return sum(struct.unpack(f'>{len(data) // 4}I', data)) & 0xFFFFFFFF


def glyph_record(contours):
    """TrueType simple glyph: on-curve flag only, every coordinate as a 16-bit delta."""
    if not contours:
        return b'', (0, 0, 0, 0), 0, 0
    pts = [(round(x), round(y), on) for c in contours for x, y, on in c]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    bbox = (min(xs), min(ys), max(xs), max(ys))
    ends, k = [], 0
    for c in contours:
        k += len(c); ends.append(k - 1)
    out = struct.pack('>hhhhh', len(contours), *bbox)
    out += struct.pack(f'>{len(ends)}H', *ends) + struct.pack('>H', 0)
    out += bytes(1 if on else 0 for _, _, on in pts)
    px = py = 0
    xd, yd = [], []
    for x, y, _ in pts:
        xd.append(x - px); yd.append(y - py); px, py = x, y
    out += struct.pack(f'>{len(xd)}h', *xd) + struct.pack(f'>{len(yd)}h', *yd)
    return out, bbox, len(pts), len(contours)


def cmap_table(mapping):
    """format 4, one segment per character (idDelta), plus the 0xFFFF terminator."""
    codes = sorted(c for c in mapping if c <= 0xFFFE)
    segs = [(c, c, (mapping[c] - c) & 0xFFFF) for c in codes] + [(0xFFFF, 0xFFFF, 1)]
    n = len(segs)
    sr = 2 * (1 << (n.bit_length() - 1))
    es = (n.bit_length() - 1)
    sub = struct.pack('>HHHHHHH', 4, 0, 0, 2 * n, sr, es, 2 * n - sr)
    sub += struct.pack(f'>{n}H', *[s[1] for s in segs]) + b'\0\0'
    sub += struct.pack(f'>{n}H', *[s[0] for s in segs])
    sub += struct.pack(f'>{n}H', *[s[2] for s in segs])
    sub += struct.pack(f'>{n}H', *([0] * n))
    sub = sub[:2] + struct.pack('>H', len(sub)) + sub[4:]
    return struct.pack('>HHHHI', 0, 1, 3, 1, 12) + sub


def name_table():
    recs = [(1, FAMILY), (2, STYLE), (3, f'{FAMILY} {STYLE} (Zenderal SMF)'), (4, f'{FAMILY}'),
            (5, 'Version 1.0'), (6, FAMILY.replace(' ', '') + '-' + STYLE)]
    strings, entries, off = b'', [], 0
    for nid, s in recs:
        data = s.encode('utf-16-be')
        entries.append(struct.pack('>HHHHHH', 3, 1, 0x409, nid, len(data), off))
        strings += data; off += len(data)
    return struct.pack('>HHH', 0, len(recs), 6 + 12 * len(recs)) + b''.join(entries) + strings


def build(font):
    codes, glyphs, adv = font['codes'], font['glyphs'], font['advances']
    order = [None] + list(range(len(glyphs)))           # glyph 0 = .notdef (empty)
    glyf, loca, metrics = b'', [], []
    gbox = [32767, 32767, -32768, -32768]
    max_pts = max_cont = 0
    for gi in order:
        loca.append(len(glyf))
        if gi is None:
            rec, bbox, npt, nct = b'', (0, 0, 0, 0), 0, 0
            aw = round(EM * 0.5)
        else:
            rec, bbox, npt, nct = glyph_record(glyphs[gi])
            aw = max(0, round(adv[gi]))
        glyf += rec + b'\0' * (-len(rec) % 4)
        lsb = bbox[0] if rec else 0
        metrics.append((aw, lsb, bbox if rec else None))
        if rec:
            gbox = [min(gbox[0], bbox[0]), min(gbox[1], bbox[1]), max(gbox[2], bbox[2]), max(gbox[3], bbox[3])]
        max_pts, max_cont = max(max_pts, npt), max(max_cont, nct)
    loca.append(len(glyf))
    num = len(order)
    mapping = {c: i + 1 for i, c in enumerate(codes)}

    ascent, descent, leading = round(font['ascent']), round(font['descent']), round(font['leading'])
    adv_max = max(m[0] for m in metrics)
    lsbs = [m[1] for m in metrics if m[2]]
    rsbs = [m[0] - m[2][2] for m in metrics if m[2]]
    xext = [m[1] + (m[2][2] - m[2][0]) for m in metrics if m[2]]
    def box(ch):
        i = mapping.get(ord(ch))
        return metrics[i][2] if i is not None and metrics[i][2] else (0, 0, 0, 0)

    tables = {}
    tables['head'] = struct.pack('>IIIIHHqqhhhhHHhhh', 0x00010000, 0x00010000, 0, 0x5F0F3CF5, 0x000B, EM, 0, 0,
                                 *gbox, 0, 8, 2, 1, 0)
    tables['hhea'] = struct.pack('>IhhhHhhhhhhhhhhhH', 0x00010000, ascent, -descent, leading, adv_max,
                                 min(lsbs), min(rsbs), max(xext), 1, 0, 0, 0, 0, 0, 0, 0, num)
    tables['maxp'] = struct.pack('>IHHHHHHHHHHHHHH', 0x00010000, num, max_pts, max_cont, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0)
    widths = [m[0] for m in metrics[1:] if m[0] > 0]
    cps = sorted(mapping)
    tables['OS/2'] = struct.pack('>HhHHHhhhhhhhhhhh10s4I4sHHHhhhHHII hhHHH'.replace(' ', ''),
                                 4, round(sum(widths) / len(widths)), 400, 5, 0,
                                 650, 600, 0, 75, 650, 600, 0, 350, 50, 260, 0,
                                 b'\x02\x0b\x05\x02\x02\x02\x04\x02\x02\x04', 0x00000003, 0, 0, 0, b'ZEN ',
                                 0x0040, max(0x20, cps[0]), min(0xFFFF, cps[-1]), ascent, -descent, leading,
                                 ascent, descent, 0x00000001, 0,
                                 box('x')[3], box('H')[3], 0, 0x20, 1)
    tables['hmtx'] = b''.join(struct.pack('>Hh', aw, lsb) for aw, lsb, _ in metrics)
    tables['cmap'] = cmap_table(mapping)
    tables['loca'] = struct.pack(f'>{len(loca)}I', *loca)
    tables['glyf'] = glyf
    tables['name'] = name_table()
    tables['post'] = struct.pack('>IIhhIIIII', 0x00030000, 0, -100, 50, 0, 0, 0, 0, 0)

    tags = sorted(tables)
    n = len(tags)
    sr = 16 * (1 << (n.bit_length() - 1))
    header = struct.pack('>IHHHH', 0x00010000, n, sr, n.bit_length() - 1, n * 16 - sr)
    off = 12 + 16 * n
    directory, body = b'', b''
    for tag in tags:
        data = tables[tag]
        directory += struct.pack('>4sIII', tag.encode('latin1'), checksum(data), off + len(body), len(data))
        body += data + b'\0' * (-len(data) % 4)
    ttf = bytearray(header + directory + body)
    head_off = off + sum(len(tables[t]) + (-len(tables[t]) % 4) for t in tags[:tags.index('head')])
    struct.pack_into('>I', ttf, head_off + 8, (0xB1B0AFBA - checksum(bytes(ttf))) & 0xFFFFFFFF)
    return bytes(ttf), num, len(mapping)


def main():
    mods = sys.argv[1] if len(sys.argv) > 1 else r'E:\Zenderal\mods'
    fonts = swffont.read_fonts(os.path.join(mods, SRC))
    font = next(f for f in fonts if f['name'] == FAMILY)
    assert 'advances' in font, 'the SWF font has no layout table'
    ttf, nglyphs, ncodes = build(font)
    out = os.path.join(mods, MOD, 'SKSE', 'Plugins', 'Fonts', 'MainFont.ttf')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'wb').write(ttf)
    print(f'{FAMILY}: {nglyphs} glyphs, {ncodes} characters, {len(ttf)} bytes -> {out}')


if __name__ == '__main__':
    main()
