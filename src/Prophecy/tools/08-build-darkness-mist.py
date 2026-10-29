"""The Darkness talent's mist mesh (curator 2026-10-28: "it's a grey/white colour, let's make it black").

The Darkness spell's hazard wore vanilla's Effects\\Ambient\\FXMistLowSwirls01Dark.nif. Its swirl shape (block 7,
BSEffectShaderProperty: DarkSwirls.dds through the GradAmbFog01 palette) is alpha-blended (SrcAlpha / InvSrcAlpha -
the plain FXMistLowSwirls01 adds instead), but its base colour is white, so it drew light grey. This copies it out of
Skyrim - Meshes0.bsa and sets that base colour to black; the alpha (the swirls' shape and fade) is untouched. The
other effect shape (block 5) has no texture and is left alone. Asserts the block layout before writing.

Vanilla's mesh is Bethesda's, so it is generated from the user's own install, never committed.

Usage:  python 08-build-darkness-mist.py [<output mod dir>]   (default: the Prophecy v3 MO2 mod)
"""
import os
import struct
import sys

import lz4.frame

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'HorseCloakFluffFix', 'tools'))
from nif import Nif  # noqa: E402

BSA = r'E:\Zenderal\Stock Game\Data\Skyrim - Meshes0.bsa'
SRC = ('meshes\\effects\\ambient', 'fxmistlowswirls01dark.nif')
OUT = os.path.join('meshes', 'ZenProphecy', 'DarknessMist.nif')     # DARK_MIST_MODEL in 01-build-trees.py
MOD = r'E:\Zenderal\mods\Zenderal - Prophecy v3 (Constellation)'
# black, at double opacity (the base colour's alpha multiplies the swirls' own; curator 2026-10-28: "isn't noticeable
# enough"), and no edge-on fade: the shader's falloff took a flat ground mist seen from standing height to 0
BLACK = (0.0, 0.0, 0.0, 2.0)
FALLOFF_STOP_OPACITY = 1.0


def extract(bsa, folder, name):
    d = open(bsa, 'rb').read()
    _, _, off, flags, nfold, _, _, lfile = struct.unpack_from('<4sIIIIIII', d, 0)
    comp, embed = bool(flags & 4), bool(flags & 0x100)
    pos, counts = off, []
    for _ in range(nfold):
        counts.append(struct.unpack_from('<QIIQ', d, pos)[1]); pos += 24
    recs = []
    for c in counts:
        n = d[pos]; fold = d[pos + 1:pos + n].rstrip(b'\0').decode(); pos += 1 + n
        for _ in range(c):
            recs.append((fold,) + struct.unpack_from('<QII', d, pos)[1:]); pos += 16
    names = d[pos:pos + lfile].split(b'\0')
    for (fold, size, at), fn in zip(recs, names):
        if fold == folder and fn.decode().lower() == name:
            packed = comp ^ bool(size & 0x40000000)
            b = d[at:at + (size & 0x3FFFFFFF)]
            if embed:
                b = b[1 + b[0]:]
            return lz4.frame.decompress(b[4:]) if packed else b
    sys.exit(f'{folder}\\{name} not in {bsa}')


def base_colour_offset(data, block):
    """Byte offset of a BSEffectShaderProperty's base colour (SSE layout)."""
    p = block + 4                                                    # name
    p += 4 + 4 * struct.unpack_from('<I', data, p)[0]                # extra data list
    p += 4 + 8 + 16                                                  # controller, flags 1/2, UV offset + scale
    p += 4 + struct.unpack_from('<I', data, p)[0]                    # source texture
    p += 4 + 16                                                      # clamp/lighting/LOD bytes, falloff
    return p


def falloff_offset(data, block):
    """Byte offset of a BSEffectShaderProperty's falloff (start angle, stop angle, start opacity, stop opacity)."""
    return base_colour_offset(data, block) - 16


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else MOD
    raw = extract(BSA, *SRC)
    tmp = os.path.join(out_dir, OUT)
    os.makedirs(os.path.dirname(tmp), exist_ok=True)
    open(tmp, 'wb').write(raw)
    nif = Nif(tmp)
    kinds = [t for t, _, _ in nif.blocks]
    assert kinds[7] == 'BSEffectShaderProperty' and kinds[14] == 'NiAlphaProperty', kinds
    data = bytearray(nif.data)
    at = base_colour_offset(data, nif.blocks[7][1])
    assert struct.unpack_from('<4f', data, at) == (1.0, 1.0, 1.0, 1.0), struct.unpack_from('<4f', data, at)
    # alpha-blended (SrcAlpha 6 / InvSrcAlpha 7), so black darkens instead of vanishing as it would if additive
    a = nif.blocks[14][1] + 4
    a += 4 + 4 * struct.unpack_from('<I', data, a)[0] + 4
    flags = struct.unpack_from('<H', data, a)[0]
    assert (flags >> 1) & 15 == 6 and (flags >> 5) & 15 == 7, hex(flags)
    struct.pack_into('<4f', data, at, *BLACK)
    fo = falloff_offset(data, nif.blocks[7][1])
    fall = struct.unpack_from('<4f', data, fo)
    assert abs(fall[2] - 1.0) < 1e-6 and fall[3] == 0.0, fall
    struct.pack_into('<f', data, fo + 12, FALLOFF_STOP_OPACITY)
    open(tmp, 'wb').write(data)
    print(f'{tmp}: swirl base colour white -> black at alpha {BLACK[3]}, edge-on fade off ({len(data)} bytes)')


if __name__ == '__main__':
    main()
