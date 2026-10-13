r"""Write Pretty Common Armory's NordHero arrow meshes LOOSE into the `Zenderal - Moonsteel Pretty Patch` MO2 mod.

Why: 01 points EGO's Silver Arrow (and its projectile) at Weapons\NordHero\NordHeroArrow*.nif, which
Pretty Common Armory replaces inside its BSA. But Enderal Remastered Armory Part 1 - Standard Armory
ships both files LOOSE, and a loose file beats every BSA regardless of MO2 priority, so its quiver would
win. Shipping Pretty's two files loose puts Pretty back on top. The mod must sort ABOVE Enderal
Remastered Armory Part 1 (lower in MO2's left pane). Side effect: base Enderal's Fine Steel Arrow uses
the same mesh, so it also gets Pretty's quiver instead of Enderal Remastered Armory's.

The meshes are Pretty's, so they are extracted from the user's own install and never committed.

Usage:  python 02-extract-pretty-arrow.py [<modlist root>]      (default E:/Zenderal)
"""
import os, sys, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    'pfmr', os.path.join(HERE, '..', '..', 'PrettyFemaleMeshRestores', 'tools', '01-extract-pretty-meshes.py'))
pfmr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pfmr)

MOD = 'Zenderal - Moonsteel Pretty Patch'
SOURCE = 'Pretty Common Armory/Pretty Common Armory.bsa'
WANT = {'meshes/weapons/nordhero/nordheroarrow.nif': 'meshes/Weapons/NordHero/NordHeroArrow.nif',
        'meshes/weapons/nordhero/nordheroarrowprojectile.nif': 'meshes/Weapons/NordHero/NordHeroArrowProjectile.nif'}


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else 'E:/Zenderal'
    mods = os.path.join(root, 'mods')
    found = 0
    for rel, read in pfmr.bsa_entries(os.path.join(mods, SOURCE)):
        if rel in WANT:
            dst = os.path.join(mods, MOD, WANT[rel])
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            data = read()
            assert data[:20] == b'Gamebryo File Format', rel
            with open(dst, 'wb') as fh:
                fh.write(data)
            print(f'{len(data):8d}  {dst}')
            found += 1
    assert found == len(WANT), f'expected {len(WANT)} files in {SOURCE}, found {found}'


if __name__ == '__main__':
    main()
