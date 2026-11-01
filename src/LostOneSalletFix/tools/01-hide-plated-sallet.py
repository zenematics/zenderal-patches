"""Build the plated Lost One mesh for `Zenderal - Lost One Sallet Fix` from the installed Lost Ones Revised.

Lost Ones Revised's `mihailancientskeleton1.nif` (the plated Lost One variant) dresses the skeleton in a
Witcher 2 sallet helmet and a strap, both textured `textures\\armor\\Plated Lost One\\lavalette_guard__c1.dds`
(+ `_n`, and `temeria_knight__b1_m.dds` as the env mask). The mod's Nexus archive (Enderal SE 243, v2.0)
never shipped that folder, so both shapes render purple. This script detaches exactly those two shapes
(their parent's child ref -> -1); the skeleton and its five `Ancient Skeleton\\armor.dds` pieces are kept.
Orphaned blocks stay in the file unreferenced, so the output differs from the source by 8 bytes.

The mesh is the mod authors' work, so it is generated from the user's own install, never committed.

Usage:  python 01-hide-plated-sallet.py [<mods dir>] [--dry-run]     (default E:/Zenderal/mods)
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'HorseCloakFluffFix', 'tools'))
from nif import Nif, Reader  # noqa: E402

MOD = 'Zenderal - Lost One Sallet Fix'
SRC_MOD = 'Lost Ones Revised'
MESH = os.path.join('Meshes', 'Mihail Monsters and Animals', 'Human', 'Ancient Skeleton',
                    'mihailancientskeleton1.nif')
HIDE = {'sallet', 'strap'}
NODE_TYPES = ('NiNode', 'BSFadeNode', 'BSLeafAnimNode', 'NiSwitchNode')


def child_slots(nif, i):
    """(byte offset, child ref) for every child slot of node block i."""
    _, p, _ = nif.blocks[i]
    r = Reader(nif.data, p)
    r.skip(4)                                   # name
    r.skip(4 * r.take('I'))                     # extra data refs
    r.skip(4 + 4 + 12 + 36 + 4 + 4)             # controller, flags, translation, rotation, scale, collision
    count = r.take('I')
    return [(r.p + 4 * k, struct.unpack_from('<i', nif.data, r.p + 4 * k)[0]) for k in range(count)]


def strip(src, dst, dry):
    nif = Nif(src)
    names = {sh['block']: sh['name'] for sh in nif.shapes()}
    dropped = []
    for i, (typ, _, _) in enumerate(nif.blocks):
        if typ not in NODE_TYPES:
            continue
        for at, ref in child_slots(nif, i):
            if names.get(ref) in HIDE:
                struct.pack_into('<i', nif.data, at, -1)
                dropped.append(names[ref])
    assert sorted(dropped) == sorted(HIDE), (src, dropped)  # each shape detached exactly once
    print(f'{os.path.basename(src)}: detached {sorted(dropped)}')
    if not dry:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, 'wb') as f:
            f.write(nif.data)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    dry = '--dry-run' in sys.argv
    mods = args[0] if args else 'E:/Zenderal/mods'
    strip(os.path.join(mods, SRC_MOD, MESH), os.path.join(mods, MOD, MESH), dry)


if __name__ == '__main__':
    main()
