"""Zenderal - Flintlock Overhaul: gun ammo in random chest loot. GENERATED - never hand-edit
LeveledItems/ZP_LootGunAmmo or the 0?E_Beute* / 0?E_Kampfitems overrides; re-run this instead.

Enderal's chest loot is tiered (01E..04E) lists of small/medium/large loot (BeuteGering/Klein,
BeuteMittel, BeuteGross/Gro) plus combat items (Kampfitems); they are where its arrows live, so gun
ammo goes in beside them. The live winner of all 13 Beute lists and 01E_Kampfitems is EGO
(tools/../reference scan 2026-10-15). 02E_Kampfitems is won by Ordo Legionis (Muskets of the Enderal)
with a base-Enderal copy + Musket Balls x10/x15 + Old Flintlock Musket, which reverted EGO's version
(ChanceNone 0.15, extra arrows, 4 items); Enderal SE - Crossbows' copy is unchanged base.

Rule, per list: EGO's record verbatim, + Ordo's three additions on 02E_Kampfitems,
+ one entry of ZP_LootGunAmmo (0x814, pick-one: Musket Balls x10/x15, Flintlock Bullets x5/x10).
This plugin then OWNS these 14 lists - no other Zenderal plugin may override them.

Run from the repo root: python -I src/FlintlockOverhaul/tools/07-loot-ammo.py
"""
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
EGO = os.path.join(ROOT, 'reference', 'mods', 'EGO', 'LeveledItems')
OUT = os.path.join(ROOT, 'src', 'FlintlockOverhaul', 'FlintlockOverhaulESP', 'LeveledItems')
PLUGIN = 'Zenderal - Flintlock Overhaul.esp'
LIST_FK = '000814:' + PLUGIN
LISTS = ['0028E1', '0028E0', '0028E2', '0028E6',          # 01E Gering/Mittel/Gross/Kampfitems
         '085664', '085666', '085665', '085667',          # 02E
         '11A4BF', '0F76D4', '11A4BE',                    # 03E Klein/Mittel/Gro
         '12E3CF', '12E3CE', '12E3CD']                    # 04E Gering/Mittel/Gro
ORDO_ADDS = {'085667': [('002F9D:OrdoLegionisMuskets.esp', 10), ('002F9D:OrdoLegionisMuskets.esp', 15),
                        ('00F5E9:OrdoLegionisMuskets.esp', 1)]}
AMMO = [('002F9D:OrdoLegionisMuskets.esp', 10), ('002F9D:OrdoLegionisMuskets.esp', 15),
        ('000800:' + PLUGIN, 5), ('000800:' + PLUGIN, 10)]
NL = '\r\n'


def entry(ref, count):
    return '- Data:' + NL + '    Level: 1' + NL + '    Reference: ' + ref + NL + '    Count: %d' % count + NL


def main():
    os.makedirs(OUT, exist_ok=True)
    body = ('FormKey: ' + LIST_FK + NL + 'EditorID: ZP_LootGunAmmo' + NL + 'Entries:' + NL
            + ''.join(entry(r, c) for r, c in AMMO))
    with open(os.path.join(OUT, 'ZP_LootGunAmmo - 000814_' + PLUGIN + '.yaml'), 'w', encoding='utf-8', newline='') as f:
        f.write(body)
    files = os.listdir(EGO)
    for fid in LISTS:
        src = [f for f in files if f.endswith(' - %s_Skyrim.esm.yaml' % fid)]
        if len(src) != 1:
            raise SystemExit('expected one EGO file for %s, got %r' % (fid, src))
        text = open(os.path.join(EGO, src[0]), encoding='utf-8', newline='').read()
        keys = re.findall(r'^([A-Za-z0-9]+):', text, re.M)
        if keys[-1] != 'Entries':
            raise SystemExit('%s: Entries is not the last key (%r)' % (src[0], keys))
        before = text.count('Reference: ')
        if not text.endswith(('\n',)):
            text += NL
        adds = ORDO_ADDS.get(fid, []) + [(LIST_FK, 1)]
        text += ''.join(entry(r, c) for r, c in adds)
        if text.count('Reference: ') != before + len(adds):
            raise SystemExit('%s: entry count mismatch' % src[0])
        with open(os.path.join(OUT, src[0]), 'w', encoding='utf-8', newline='') as f:
            f.write(text)
        print('%-45s %3d -> %3d entries' % (src[0][:-5], before, before + len(adds)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
