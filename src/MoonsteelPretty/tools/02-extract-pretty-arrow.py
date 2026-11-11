r"""Write Pretty Common Armory's NordHero arrow meshes LOOSE into the `Zenderal - Moonsteel Pretty Patch` MO2 mod.

Why: 01 points EGO's Silver Arrow (and its projectile) at Weapons\NordHero\NordHeroArrow*.nif, which
Pretty Common Armory replaces (inside its BSA up to 2.0, loose since 2.1). But Enderal Remastered Armory Part 1 - Standard Armory
ships both files LOOSE, and a loose file beats every BSA regardless of MO2 priority, so its quiver would
win (since Pretty 2.1 ships loose too, it still wins: ERA outranks Pretty Common Armory in MO2).
Shipping Pretty's two files in a mod above ERA puts Pretty back on top. The mod must sort ABOVE Enderal
Remastered Armory Part 1 (lower in MO2's left pane). Side effect: base Enderal's Fine Steel Arrow uses
the same mesh, so it also gets Pretty's quiver instead of Enderal Remastered Armory's.

The meshes are Pretty's, so they are extracted from the user's own install and never committed.

Usage:  python 02-extract-pretty-arrow.py [<modlist root>] [<target MO2 mod>]
        (defaults E:/Zenderal and 'Zenderal - Moonsteel Pretty Patch'; the live copy is in 'Zenderal - Patch Collection')

2026-11-11: Pretty Enderal Armory 2.1 ships loose files and no BSA, so this copies the two loose meshes.
"""
import os, sys, shutil

MOD = 'Zenderal - Moonsteel Pretty Patch'
SOURCE = 'Pretty Common Armory'
WANT = {'meshes/weapons/nordhero/nordheroarrow.nif': 'meshes/Weapons/NordHero/NordHeroArrow.nif',
        'meshes/weapons/nordhero/nordheroarrowprojectile.nif': 'meshes/Weapons/NordHero/NordHeroArrowProjectile.nif'}


def find_ci(base, rel):
    """Resolve rel under base case-insensitively (MO2 mods keep whatever case the author shipped)."""
    cur = base
    for part in rel.split('/'):
        hits = [n for n in os.listdir(cur) if n.lower() == part.lower()]
        if len(hits) != 1:
            raise SystemExit(f'{rel}: expected one "{part}" in {cur}, found {hits}')
        cur = os.path.join(cur, hits[0])
    return cur


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else 'E:/Zenderal'
    target = sys.argv[2] if len(sys.argv) > 2 else MOD
    mods = os.path.join(root, 'mods')
    for rel, out in WANT.items():
        src = find_ci(os.path.join(mods, SOURCE), rel)
        with open(src, 'rb') as fh:
            assert fh.read(20) == b'Gamebryo File Format', src
        dst = os.path.join(mods, target, out)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)
        print(f'{os.path.getsize(dst):8d}  {dst}')


if __name__ == '__main__':
    main()
