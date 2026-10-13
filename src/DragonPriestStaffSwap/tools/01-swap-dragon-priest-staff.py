"""Rebuild the `Zenderal - Dragon Priest Staff Swap` MO2 mod from Pretty Mages Armory's BSA.

Pretty Mages Armory replaces the vanilla Dragon Priest staff meshes (by path, inside its BSA) with its
Maelstrom Staff design. Every staff that still uses that path gets it: Enderal's Fire Wrath (07C982,
07C9AD, 03990E), Frostbite (07C9B0), Grounding (07C980, 07C9B1), Lightning (07C9AA) and the Destruction
template (0BE11F), plus 19 Apocalypse and 7 Triumvirate staffs. This mod ships Pretty's own Staff of Chain
Lightning mesh LOOSE at both Dragon Priest paths instead; a loose file beats every BSA, so the mod only
needs to be enabled (sort it directly above Pretty Mages Armory for readability).

Pretty uses that single mesh for both the 3rd-person model and the 1st-person static of its Chain
Lightning staff, so one file serves both paths here too. Its textures resolve from Pretty's own BSA.

The mesh is Pretty's, so it is extracted from the user's own install, never committed.

Usage:  python 01-swap-dragon-priest-staff.py [<mods dir>]     (default E:/Zenderal/mods)
"""
import os, sys, hashlib
import importlib.util

_spec = importlib.util.spec_from_file_location(
    'restores', os.path.join(os.path.dirname(__file__), '..', '..', 'EnderalTextureRestores', 'tools',
                             '01-extract-enderal-textures.py'))
_restores = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_restores)
read_from_bsa = _restores.read_from_bsa

MOD = 'Zenderal - Dragon Priest Staff Swap'
SOURCE_MOD = 'Pretty Mages Armory'
SOURCE_BSA = 'Pretty Mages Armory.bsa'
SOURCE = 'meshes\\enderal\\weapons\\staves\\staffofchainlightning.nif'
TARGETS = [
    'meshes\\weapons\\dragonpriest\\dragonprieststaff3rd.nif',  # WEAP Model
    'meshes\\weapons\\dragonpriest\\dragonprieststaff.nif',     # 1st-person STAT 01C200
]


def main():
    mods = sys.argv[1] if len(sys.argv) > 1 else 'E:/Zenderal/mods'
    blob = read_from_bsa(os.path.join(mods, SOURCE_MOD, SOURCE_BSA), SOURCE)
    assert blob.startswith(b'Gamebryo File Format, Version 20.2.0.7'), 'not an SSE-era NIF'
    out_root = os.path.join(mods, MOD)
    for rel in TARGETS:
        out = os.path.join(out_root, *rel.split('\\'))
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, 'wb') as fh:
            fh.write(blob)
        print(f'{len(blob):>9}  {hashlib.sha1(blob).hexdigest()[:12]}  {rel}  <- {SOURCE}')
    print(f'{len(TARGETS)} files -> {out_root}')


if __name__ == '__main__':
    main()
