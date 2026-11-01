"""Build `Zenderal - ZarAh Texture Fix` from the installed Malphas' Blessing.

Malphas' Blessing bakes Zar'Ah's facegen (`0001F1B2.nif`, reused by the Phasmalist Warrior Tier 4 apparition
`00025312.nif`) with her hair and two scar overlays textured from `textures\\MB\\F\\mbZar'ah\\`, but the mod
ships that folder as `textures\\MB\\F\\mbZarah\\`. The engine finds nothing, so the hair vanishes and the
full-face scar overlays draw as an opaque dark-blue plate. This script copies the six textures to the
apostrophe path the facegen asks for. It reads every path from the facegen itself and asserts there are six.

The textures are the mod author's work, so they are copied from the user's own install, never committed.

Usage:  python 01-copy-zarah-textures.py [<mods dir>] [--dry-run]     (default E:/Zenderal/mods)
"""
import os
import re
import shutil
import sys

MOD = 'Zenderal - ZarAh Texture Fix'
SRC_MOD = "Malphas' Blessing"
FACEGEN = ['meshes', 'actors', 'character', 'facegendata', 'facegeom', 'Enderal - Forgotten Stories.esm']
NIFS = ('0001F1B2.nif', '00025312.nif')
WANT_DIR = "textures\\mb\\f\\mbzar'ah\\"
HAVE_DIR = os.path.join('textures', 'MB', 'F', 'mbZarah')
PAT = re.compile(rb"textures\x5cMB\x5cF\x5cmbZar'ah\x5c[\x20-\x7e]*?\.dds", re.I)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    dry = '--dry-run' in sys.argv
    mods = args[0] if args else 'E:/Zenderal/mods'
    src = os.path.join(mods, SRC_MOD)

    wanted = set()
    for n in NIFS:
        data = open(os.path.join(src, *FACEGEN, n), 'rb').read()
        found = {m.decode().lower() for m in PAT.findall(data)}
        assert found, n
        wanted |= found
    assert len(wanted) == 6, sorted(wanted)

    have = {f.lower(): f for f in os.listdir(os.path.join(src, HAVE_DIR))}
    for path in sorted(wanted):
        name = path[len(WANT_DIR):]
        assert name in have, (path, sorted(have))  # every texture the facegen wants exists under mbZarah
        dst = os.path.join(mods, MOD, 'textures', 'MB', 'F', "mbZar'ah", have[name])
        print(f'{HAVE_DIR}\\{have[name]} -> {dst}')
        if not dry:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(os.path.join(src, HAVE_DIR, have[name]), dst)


if __name__ == '__main__':
    main()
