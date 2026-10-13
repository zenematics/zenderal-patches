"""Rebuild the `Zenderal - Missing Parallax Heights` MO2 mod: flat height maps for parallax meshes whose `_p` is missing.

A parallax mesh (BSLightingShaderProperty shader type 3) reads its height from the texture set's slot 3. When that
file does not exist, the game substitutes white, and ENB complex parallax renders the surface "floating": the texture
slides across the mesh as the camera moves (Boris, ENB Parallax Occlusion Mapping page: "'Floating' texture without
any parallax usually means height map is missing, so game use white color instead of it"). Auto Parallax is meant to
disable parallax in that case, but under ENB it does not (seen 2026-10-11 on the curb of `_00E_Ark_1024WallGate02`,
SRP's `1024wallgate02.nif`, whose `blocks_p.dds` exists nowhere).

On 2026-10-11 the Alpha 0.5 profile had 1017 winning meshes referencing 289 missing height maps, almost all from SRP
Enderal's Architecture/Dungeons meshes. This script scans every winning loose mesh, resolves every parallax shader's
height path against the loose mods and the game BSAs, and writes a tiny mid-grey (128 = ENB's "flat, no shift")
height map at each missing path. It adds files only; nobody's mesh or texture is modified.

Usage:  python 01-flat-heights.py [--dry-run]
"""
import os, struct, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'HorseCloakFluffFix', 'tools'))
from nif import Nif, Reader  # noqa: E402

Z = 'E:/Zenderal'
PROFILE = 'Alpha 0.5'
MOD = 'Zenderal - Missing Parallax Heights'
EXPECTED = 289  # missing height maps in Alpha 0.5 on 2026-10-11; a change means re-check the list
FLAT = 128


def bsa_names(path):
    d = open(path, 'rb').read()
    magic, ver, fro, aflags, fcount, filecount, tfnl, tfil, ff = struct.unpack_from('<4sIIIIIIII', d, 0)
    assert magic == b'BSA\x00' and ver == 105, (path, magic, ver)
    p = fro
    counts = []
    for _ in range(fcount):
        counts.append(struct.unpack_from('<QIIQ', d, p)[1])
        p += 24
    folders = []
    for c in counts:
        ln = d[p]
        folders.append((d[p + 1:p + ln].rstrip(b'\0').decode('latin1'), c))
        p += 1 + ln + 16 * c
    names = d[p:p + tfil].split(b'\0')
    out, i = [], 0
    for name, c in folders:
        for _ in range(c):
            out.append((name + '/' + names[i].decode('latin1')).lower().replace('\\', '/'))
            i += 1
    return out


def flat_dds(size=4):
    """Uncompressed RGBA, full mip chain, every channel = FLAT."""
    mips, s = [], size
    while s >= 1:
        mips.append(bytes([FLAT]) * (s * s * 4))
        s //= 2
    hdr = struct.pack('<4sIIIIIII44sIIIIIIIIIIIII', b'DDS ', 124, 0x2100F, size, size, size * 4, 0, len(mips),
                      b'\0' * 44, 32, 0x41, 0, 32, 0x000000FF, 0x0000FF00, 0x00FF0000, 0xFF000000,
                      0x401008, 0, 0, 0, 0)
    return hdr + b''.join(mips)


def main():
    dry = '--dry-run' in sys.argv
    mods = [l[1:].strip() for l in open(f'{Z}/profiles/{PROFILE}/modlist.txt', encoding='utf-8')
            if l.startswith('+') and l[1:].strip() != MOD]
    avail = set()
    for f in os.listdir(f'{Z}/Stock Game/Data'):
        if f.lower().endswith('.bsa'):
            avail.update(bsa_names(f'{Z}/Stock Game/Data/{f}'))
    meshes = {}
    for m in mods:
        base = f'{Z}/mods/{m}'
        if not os.path.isdir(base):
            continue
        for dp, _, fns in os.walk(base):
            rel = os.path.relpath(dp, base).replace('\\', '/').lower()
            top = rel.split('/')[0]
            if top not in ('meshes', 'textures'):
                continue
            for f in fns:
                k = rel + '/' + f.lower()
                avail.add(k)
                if top == 'meshes' and k.endswith('.nif') and k not in meshes:
                    meshes[k] = os.path.join(dp, f)
    missing = {}
    for k, path in meshes.items():
        try:
            n = Nif(path)
        except Exception:
            continue  # non-SSE or unusual header; not something this reader handles
        for typ, p, _ in n.blocks:
            if typ != 'BSLightingShaderProperty':
                continue
            try:
                r = Reader(n.data, p)
                stype = r.take('I')
                r.take('i')
                r.skip(4 * r.take('I'))
                r.take('i')
                r.skip(8 + 16)
                ts = r.take('i')
                if stype != 3 or ts < 0:
                    continue
                tr = Reader(n.data, n.blocks[ts][1])
                tex = []
                for _ in range(tr.take('I')):
                    ln = tr.take('I')
                    tex.append(bytes(n.data[tr.p:tr.p + ln]).decode('latin1'))
                    tr.skip(ln)
            except Exception:
                continue
            h = tex[3].strip().lower().replace('\\', '/') if len(tex) > 3 else ''
            if not h:
                continue  # empty height slot: no file path to supply
            if not h.startswith('textures/'):
                h = 'textures/' + h
            if h not in avail:
                missing.setdefault(h, k)
    for h in sorted(missing):
        print(f'{h}   (e.g. {missing[h]})')
    print(f'{len(missing)} missing height maps')
    if len(missing) != EXPECTED:
        sys.exit(f'expected {EXPECTED}; the list changed - review the set above, then update EXPECTED')
    if dry:
        return
    data = flat_dds()
    for h in missing:
        dst = os.path.join(Z, 'mods', MOD, *h.split('/'))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, 'wb') as fh:
            fh.write(data)
    print(f'done: {len(missing)} flat height maps in mods/{MOD}')


if __name__ == '__main__':
    main()
