"""Build `Zenderal - Pretty Righteous Path SMP` from the installed Pretty Righteous Path Armory.

Pretty's Righteous Path cuirass (Enderal's ebony armor paths, `meshes\\armor\\ebony\\{f,m}\\cuirass_{0,1}.nif`)
has a front and a rear tabard flap, the shape `SkirtB`, already skinned to XPMSE's skirt bones
(`SkirtFBone02/03`, `SkirtBBone02/03`) but with nothing simulating them, so they stay glued to the pelvis.

The Cuirass of the Righteous Keeper (`0365C7`) is the same model with black `_alt` textures: Pretty Semi-Unique
Armory points it at its own ARMA `000817` -> `armor\\ebony\\alt\\{f,m}\\cuirass_{0,1}.nif`, packed in that mod's BSA.

This copies the eight meshes and appends one `NiStringExtraData` "HDT Skinned Mesh Physics Object" to each scene
root, pointing at `ZenRighteousPathFlaps.xml` (committed in `../assets/`, copied alongside). Every other byte of
the mesh is kept: the new block goes last, so no block reference shifts. It asserts first that each mesh has the
flap shape on exactly those four bones and no physics hook yet.

The meshes are the mod author's work, so they are generated from the user's own install, never committed.

Usage:  python 01-build-smp-meshes.py [<mods dir>] [--dry-run]     (default E:/Zenderal/mods)
"""
import os
import shutil
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'HorseCloakFluffFix', 'tools'))
from nif import Reader  # noqa: E402
sys.path.insert(0, HERE)
from bsa import Bsa  # noqa: E402

MOD = 'Zenderal - Pretty Righteous Path SMP'
DIR = os.path.join('meshes', 'armor', 'ebony')
# (source mod, BSA inside it or None for loose files, subfolder under armor\ebony)
SOURCES = [
    ('Pretty Righteous Path Armory', None, ''),                                   # Path, Forged (red)
    ('Pretty Semi-Unique Armory', 'Pretty Semi-Unique Armory.bsa', 'alt'),        # Keeper (black)
]
MESHES = [os.path.join(s, f'cuirass_{w}.nif') for s in ('f', 'm') for w in (0, 1)]
XML = 'ZenRighteousPathFlaps.xml'
SMP_KEY = 'HDT Skinned Mesh Physics Object'
SMP_VALUE = 'Meshes\\armor\\ebony\\' + XML
FLAP_SHAPE = 'SkirtB'
FLAP_BONES = {'SkirtFBone02', 'SkirtFBone03', 'SkirtBBone02', 'SkirtBBone03'}


def parse(data):
    """Split an SSE NIF into its header fields, raw block bytes and footer."""
    r = Reader(data)
    r.p = data.index(b'\n') + 1
    h = {'magic': bytes(data[:r.p])}
    assert r.take('I') == 0x14020007
    h['endian'] = r.take('B')
    assert r.take('I') == 12
    nblocks = r.take('I')
    assert r.take('I') == 100                   # SSE only
    start = r.p
    for _ in range(3):                          # author / process / export short strings
        r.skip(r.take('B'))
    h['bsstrings'] = bytes(data[start:r.p])
    types = []
    for _ in range(r.take('H')):
        n = r.take('I')
        types.append(bytes(data[r.p:r.p + n]))
        r.skip(n)
    tidx = [r.take('H') for _ in range(nblocks)]
    sizes = [r.take('I') for _ in range(nblocks)]
    strings = []
    nstr = r.take('I')
    r.skip(4)                                   # max string length, recomputed on write
    for _ in range(nstr):
        n = r.take('I')
        strings.append(bytes(data[r.p:r.p + n]))
        r.skip(n)
    ngroups = r.take('I')
    groups = [r.take('I') for _ in range(ngroups)]
    blocks = []
    for s in sizes:
        blocks.append(bytearray(data[r.p:r.p + s]))
        r.skip(s)
    nroots = r.take('I')
    roots = [r.take('i') for _ in range(nroots)]
    assert r.p == len(data), (r.p, len(data))
    return h, types, tidx, strings, groups, blocks, roots


def write(h, types, tidx, strings, groups, blocks, roots):
    out = bytearray(h['magic'])
    out += struct.pack('<IBII', 0x14020007, h['endian'], 12, len(blocks))
    out += struct.pack('<I', 100) + h['bsstrings']
    out += struct.pack('<H', len(types))
    for t in types:
        out += struct.pack('<I', len(t)) + t
    out += struct.pack(f'<{len(tidx)}H', *tidx)
    out += struct.pack(f'<{len(blocks)}I', *(len(b) for b in blocks))
    out += struct.pack('<II', len(strings), max(len(s) for s in strings))
    for s in strings:
        out += struct.pack('<I', len(s)) + s
    out += struct.pack('<I', len(groups)) + struct.pack(f'<{len(groups)}I', *groups)
    for b in blocks:
        out += b
    out += struct.pack('<I', len(roots)) + struct.pack(f'<{len(roots)}i', *roots)
    return out


def check_flaps(data, label):
    """The flap shape must exist and be skinned to exactly the four bones the XML simulates."""
    sys.path.insert(0, 'E:/Zen Tools/PyNifly V29.1.0/io_scene_nifly')
    import tempfile
    from pyn.pynifly import NifFile
    fd, tmp = tempfile.mkstemp(suffix='.nif')
    with os.fdopen(fd, 'wb') as f:
        f.write(data)
    try:
        shapes = {s.name: s for s in NifFile(tmp).shapes}
        assert FLAP_SHAPE in shapes and 'Greaves' in shapes, (label, list(shapes))
        bones = set(shapes[FLAP_SHAPE].bone_names)
        assert bones == FLAP_BONES, (label, bones)
    finally:
        os.remove(tmp)


def add_smp(data, src, dst, dry):
    check_flaps(data, src)
    data = bytearray(data)
    h, types, tidx, strings, groups, blocks, roots = parse(data)
    assert SMP_KEY.encode() not in strings, f'{src} already has an SMP hook'
    root = roots[0]
    assert types[tidx[root] & 0x7FFF] in (b'NiNode', b'BSFadeNode'), types[tidx[root]]
    if b'NiStringExtraData' not in types:
        types.append(b'NiStringExtraData')
    t = types.index(b'NiStringExtraData')
    strings += [SMP_KEY.encode(), SMP_VALUE.encode()]
    new = len(blocks)
    blocks.append(bytearray(struct.pack('<ii', len(strings) - 2, len(strings) - 1)))   # name, data
    tidx.append(t)
    # Root NiObjectNET: name, extra data count + refs, ... -> append our ref to the list.
    rb = blocks[root]
    count = struct.unpack_from('<I', rb, 4)[0]
    at = 8 + 4 * count
    blocks[root] = rb[:4] + struct.pack('<I', count + 1) + rb[8:at] + struct.pack('<i', new) + rb[at:]
    out = write(h, types, tidx, strings, groups, blocks, roots)
    assert parse(out)[5][:new] == blocks[:new]
    print(f'{src}: +NiStringExtraData block {new} -> {SMP_VALUE} ({len(data)} -> {len(out)} bytes)')
    if not dry:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, 'wb') as f:
            f.write(out)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    dry = '--dry-run' in sys.argv
    mods = args[0] if args else 'E:/Zenderal/mods'
    for src_mod, archive, sub in SOURCES:
        bsa = Bsa(os.path.join(mods, src_mod, archive)) if archive else None
        for m in MESHES:
            rel = os.path.join(DIR, sub, m)
            if bsa:
                data = bsa.read(rel)
            else:
                with open(os.path.join(mods, src_mod, rel), 'rb') as f:
                    data = f.read()
            add_smp(data, f'{src_mod}: {rel}', os.path.join(mods, MOD, rel), dry)
    if not dry:
        shutil.copyfile(os.path.join(HERE, '..', 'assets', XML), os.path.join(mods, MOD, DIR, XML))
        print(f'copied {XML}')


if __name__ == '__main__':
    main()
