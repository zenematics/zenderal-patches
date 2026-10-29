"""Write the projectile overrides: the winning musket/rifle ball PROJ records verbatim, Gravity -> 0.

Hit Where You Aim (1.1.2) points the player's 3rd-person aiming pose with its ballistic solver,
fed the ammo projectile's speed and gravity. At these speeds with near-zero gravity its quartic
loses the flat root and only the high arc passes its speed check: the pose aims straight up.
Gravity exactly 0 takes its linear branch instead. Spriggit omits a zero Gravity line, so the
line is removed. Each source must contain exactly one 'Gravity:' line with the expected value.

Run from the repo root: python -I src/HWYAMusketFix/tools/01-build-hwya-musket-fix.py
"""
import os
import re
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
OUT = os.path.join(ROOT, 'src', 'HWYAMusketFix', 'HWYAMusketFixESP', 'Projectiles')
MASTERS = {'Skyrim.esm', 'Update.esm', 'Enderal - Forgotten Stories.esm',
           'DAR Rifles.esp', 'OrdoLegionisMuskets.esp'}
# (reference folder, file, expected gravity). OrdoEnderal = the winning 'Muskets of the Enderal' copy.
SOURCES = [
    ('OrdoEnderal', 'OLM_proj_ball - 002F9E_OrdoLegionisMuskets.esp.yaml', '0.001'),
    ('OrdoEnderal', 'OLM_proj_ballminie - 00F5DF_OrdoLegionisMuskets.esp.yaml', '0.001'),
    ('DARRifles', '0ProjBullet - 000808_DAR Rifles.esp.yaml', '2E-06'),
]


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    for folder, name, grav in SOURCES:
        path = os.path.join(ROOT, 'reference', 'mods', folder, 'Projectiles', name)
        raw = open(path, 'rb').read().decode('utf-8')
        if len(re.findall(r'(?m)^Gravity:', raw)) != 1:
            raise SystemExit('%s: expected one Gravity line' % name)
        new, n = re.subn(r'(?m)^Gravity: %s\r?\n' % re.escape(grav), '', raw)
        if n != 1:
            raise SystemExit('%s: Gravity %s not found' % (name, grav))
        for ref in re.findall(r'\b[0-9A-F]{6}:([^\r\n]+?\.es[mp])\b', new):
            if ref not in MASTERS:
                raise SystemExit('%s: references undeclared master %s' % (name, ref))
        open(os.path.join(OUT, name), 'wb').write(new.encode('utf-8'))
    print('%d projectile overrides written (Gravity -> 0)' % len(SOURCES))


if __name__ == '__main__':
    sys.exit(main())
