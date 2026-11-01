"""Write the one-handed mace overrides: EGO's winning WEAP records verbatim, Speed 0.8 -> 0.9.

Input: tools/maces.json from 00-scan-maces.py (the live load order's maces and their winners).
Only records whose winner is EGO are emitted; the others (Pretty's unplayable Pyrean mace,
Apocalypse's conjured-Dremora weapons, Castle Bleakstar's 0.85 unique) are left alone.
Each source file is copied from reference/mods/EGO/Weapons and must contain exactly one
'  Speed: 0.8' line, which becomes '  Speed: 0.9'. Every FormKey in the output must belong to a
declared master.

Run from the repo root: python -I src/MaceSpeed/tools/01-build-mace-speed.py
"""
import json
import os
import re
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
HERE = os.path.dirname(__file__)
EGO_PLUGIN = 'Enderal SE - Gameplay Overhaul.esp'
EGO_WEAPONS = os.path.join(ROOT, 'reference', 'mods', 'EGO', 'Weapons')
OUT = os.path.join(ROOT, 'src', 'MaceSpeed', 'MaceSpeedESP', 'Weapons')
MASTERS = {'Skyrim.esm', 'Update.esm', 'Enderal - Forgotten Stories.esm', EGO_PLUGIN}
OLD, NEW = '0.8', '0.9'


def main():
    maces = json.load(open(os.path.join(HERE, 'maces.json'), encoding='utf-8'))
    wanted = sorted(fk for fk, r in maces.items() if r['chain'][-1] == EGO_PLUGIN)
    files = {}
    for f in os.listdir(EGO_WEAPONS):
        m = re.search(r' - ([0-9A-F]{6})_(.+)\.yaml$', f)
        if m:
            files['%s:%s' % (m.group(1), m.group(2))] = f
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    for fk in wanted:
        if maces[fk]['speed'] != float(OLD):
            raise SystemExit('%s: live speed %s, expected %s' % (fk, maces[fk]['speed'], OLD))
        src = files.get(fk)
        if not src:
            raise SystemExit('%s: not in %s' % (fk, EGO_WEAPONS))
        raw = open(os.path.join(EGO_WEAPONS, src), 'rb').read().decode('utf-8')
        new, n = re.subn(r'(?m)^  Speed: %s(?=\r?$)' % re.escape(OLD), '  Speed: ' + NEW, raw)
        if n != 1:
            raise SystemExit('%s: %d Speed lines replaced, expected 1' % (src, n))
        for ref in re.findall(r'\b[0-9A-F]{6}:([^\r\n]+?\.es[mp])\b', new):
            if ref not in MASTERS:
                raise SystemExit('%s: references undeclared master %s' % (src, ref))
        open(os.path.join(OUT, src), 'wb').write(new.encode('utf-8'))
    print('%d mace overrides written (Speed %s -> %s)' % (len(wanted), OLD, NEW))
    if len(wanted) != 22:
        raise SystemExit('expected 22 EGO maces, got %d - re-check the scan' % len(wanted))


if __name__ == '__main__':
    sys.exit(main())
