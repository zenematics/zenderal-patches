"""Zenderal - Flintlock Overhaul: Wheeler icons for the flintlock pistols and Ordo Legionis muskets.
GENERATED - never hand-edit wheeler/icons_custom/; re-run this instead.

Wheeler (the list's wheeler-enderal-fix DLL) loads per-item icons from
Data/SKSE/Plugins/wheeler/resources/icons_custom/FID_<plugin>_0X<local FormID>.svg, the same scheme
Dragonborn - Wheeler Reskin uses for its 211 FID_ icons (e.g. FID_AdamantBard.esp_0X804.svg). One copy
of the curator's art per weapon: wheeler/source/flintlock.svg for all 8 pistols, musket.svg for all 14
muskets. Weapon lists are read from the serialized plugins so a mod update fails loudly here.

Run from the repo root: python -I src/FlintlockOverhaul/tools/03-wheeler-icons.py
"""
import os
import re
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
SRC = os.path.join(ROOT, 'src', 'FlintlockOverhaul', 'wheeler', 'source')
OUT = os.path.join(ROOT, 'src', 'FlintlockOverhaul', 'wheeler', 'icons_custom')
SETS = [  # (serialized plugin tree, plugin filename, icon, expected weapon count)
    ('FlintlockPack', 'AdventurerFlintlockPack.esp', 'flintlock.svg', 8),
    ('OrdoLegionis', 'OrdoLegionisMuskets.esp', 'musket.svg', 14),
]

os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    os.remove(os.path.join(OUT, f))
for tree, plugin, icon, expected in SETS:
    wdir = os.path.join(ROOT, 'reference', 'mods', tree, 'Weapons')
    ids = []
    for f in sorted(os.listdir(wdir)):
        m = re.search(r' - ([0-9A-F]{6})_%s\.yaml$' % re.escape(plugin), f)
        if m:
            ids.append(int(m.group(1), 16))
    if len(ids) != expected:
        sys.exit('%s: expected %d weapons, found %d' % (plugin, expected, len(ids)))
    for i in ids:
        name = 'FID_%s_0X%X.svg' % (plugin, i)
        shutil.copyfile(os.path.join(SRC, icon), os.path.join(OUT, name))
        print(name, '<-', icon)
