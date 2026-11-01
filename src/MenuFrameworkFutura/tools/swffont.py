"""Read the fonts out of a Scaleform/Flash .swf (DefineFont2 / DefineFont3 tags) - glyph outlines, code table, layout.

SWF glyph shapes are quadratic Bezier paths (straight and curved edges), the same curve type TrueType uses, so the
outlines convert exactly. Spec: SWF File Format Specification v19, DefineFont2/DefineFont3 and SHAPE.
DefineFont3 coordinates are in 1/20 of an em unit on a 1024-unit em square (DefineFont2: 1024 units, no 20x).
"""
import struct, zlib


class Bits:
    def __init__(self, data, pos=0):
        self.d = data
        self.pos = pos * 8           # bit position

    def ub(self, n):
        v = 0
        for _ in range(n):
            byte = self.d[self.pos >> 3]
            v = (v << 1) | ((byte >> (7 - (self.pos & 7))) & 1)
            self.pos += 1
        return v

    def sb(self, n):
        if n == 0:
            return 0
        v = self.ub(n)
        return v - (1 << n) if v & (1 << (n - 1)) else v

    def align(self):
        self.pos = (self.pos + 7) & ~7

    @property
    def byte(self):
        return self.pos >> 3


def tags(path):
    raw = open(path, 'rb').read()
    sig = raw[:3]
    if sig == b'CWS':
        body = raw[:8] + zlib.decompress(raw[8:])
    elif sig == b'FWS':
        body = raw
    else:
        raise ValueError(f'{path}: unsupported SWF signature {sig!r}')
    b = Bits(body, 8)
    nbits = b.ub(5)
    b.ub(4 * nbits)
    b.align()
    p = b.byte + 4                   # frame rate, frame count
    while p < len(body):
        code_len = struct.unpack_from('<H', body, p)[0]; p += 2
        code, length = code_len >> 6, code_len & 0x3F
        if length == 0x3F:
            length = struct.unpack_from('<I', body, p)[0]; p += 4
        yield code, body[p:p + length]
        p += length
        if code == 0:
            break


def parse_shape(data, start, scale):
    """Glyph SHAPE -> list of contours; each contour is a list of (x, y, on_curve) in em units, y up."""
    b = Bits(data, start)
    nfill = b.ub(4)
    nline = b.ub(4)
    contours, cur = [], None
    x = y = 0
    while True:
        if b.ub(1) == 0:                         # style change / end
            new_styles, line_s, fill1, fill0, move = b.ub(1), b.ub(1), b.ub(1), b.ub(1), b.ub(1)
            if not (new_styles or line_s or fill1 or fill0 or move):
                break
            if move:
                mb = b.ub(5)
                x, y = b.sb(mb), b.sb(mb)
                if cur:
                    contours.append(cur)
                cur = [(x, y, True)]
            if fill0:
                b.ub(nfill)
            if fill1:
                b.ub(nfill)
            if line_s:
                b.ub(nline)
            if new_styles:
                raise ValueError('glyph shape with new styles')
        else:
            if cur is None:
                cur = [(x, y, True)]
            if b.ub(1):                          # straight
                nb = b.ub(4) + 2
                if b.ub(1):
                    x += b.sb(nb); y += b.sb(nb)
                elif b.ub(1):
                    y += b.sb(nb)
                else:
                    x += b.sb(nb)
                cur.append((x, y, True))
            else:                                # curved
                nb = b.ub(4) + 2
                cx, cy = x + b.sb(nb), y + b.sb(nb)
                x, y = cx + b.sb(nb), cy + b.sb(nb)
                cur.append((cx, cy, False))
                cur.append((x, y, True))
    if cur:
        contours.append(cur)
    out = []
    for c in contours:
        pts = [(px / scale, -py / scale, on) for px, py, on in c]    # SWF y grows down
        if len(pts) > 1 and pts[0][:2] == pts[-1][:2] and pts[-1][2]:
            pts.pop()                                                # closing point repeats the start
        if len(pts) >= 2:
            out.append(pts)
    return out


def read_fonts(path):
    fonts = []
    for code, t in tags(path):
        if code not in (48, 75):                 # DefineFont2, DefineFont3
            continue
        scale = 20.0 if code == 75 else 1.0
        p = 2
        flags = t[p]; p += 1
        has_layout, wide_offsets, wide_codes = flags & 0x80, flags & 0x08, flags & 0x04
        italic, bold = bool(flags & 0x02), bool(flags & 0x01)
        p += 1                                   # language
        nlen = t[p]; p += 1
        name = t[p:p + nlen].rstrip(b'\0').decode('latin1'); p += nlen
        n = struct.unpack_from('<H', t, p)[0]; p += 2
        base = p
        ofmt, osz = ('<I', 4) if wide_offsets else ('<H', 2)
        offsets = [struct.unpack_from(ofmt, t, base + i * osz)[0] for i in range(n)]
        code_off = struct.unpack_from(ofmt, t, base + n * osz)[0]
        glyphs = [parse_shape(t, base + o, scale) for o in offsets]
        cp = base + code_off
        cfmt, csz = ('<H', 2) if (wide_codes or code == 75) else ('<B', 1)
        codes = [struct.unpack_from(cfmt, t, cp + i * csz)[0] for i in range(n)]
        p = cp + n * csz
        font = dict(name=name, italic=italic, bold=bold, glyphs=glyphs, codes=codes, scale=scale)
        if has_layout:
            asc, desc, lead = struct.unpack_from('<HHh', t, p); p += 6
            adv = [struct.unpack_from('<h', t, p + 2 * i)[0] for i in range(n)]; p += 2 * n
            font.update(ascent=asc / scale, descent=desc / scale, leading=lead / scale,
                        advances=[a / scale for a in adv])
        fonts.append(font)
    return fonts
