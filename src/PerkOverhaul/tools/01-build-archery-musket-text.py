"""Trickster (archery) Hero Menu texts name muskets alongside bows.

Every archery perk already applies to Ordo's muskets (crossbow-type WEAP carrying WeapTypeBow 01E715):
keyword-gated entry points match them, and EGO / Enderal SE - Crossbows widened the
GetEquippedItemType == 7 checks to 12. Only the text said "bow". This copies each MESG's winning
record (EGO's, else base Enderal's) into PerkOverhaulESP/Messages/ and rewrites the English
description. Each replacement must match exactly once or the script fails.

Replica 069D72 also gains its ammo-recovery line (ZEN_PO_ReplicaAmmoRecoverySC). Not touched: Flame
Shot 069D6E (owned by src/FlameShot, already mentions muskets). Live overriders: python -I src/PerkOverhaul/tools/00-scan-overriders.py <ids>

Run from the repo root: python -I src/PerkOverhaul/tools/01-build-archery-musket-text.py
"""
import glob
import os
import sys

EGO = 'reference/mods/EGO/Messages'
BASE = 'reference/base/Skyrim/Messages'
OUT = 'src/PerkOverhaul/PerkOverhaulESP/Messages'

# FormID -> [(old, new), ...] applied to the record's English description.
# Wording (curator, 2026-10-26): every node that works with both says "muskets or bows" ("musket balls or arrows"
# for the ammo), musket first.
EDITS = {
    '066858': [  # Strong Bowstring (EGO)
        ('effective use of a bow with lockpicking', 'effective use of muskets or bows with lockpicking'),
        ('Tier I: Bows do 15%%', 'Tier I: Muskets or bows do 15%%'),
        ('Tier II: Bows do another', 'Tier II: Muskets or bows do another'),
    ],
    '066856': [  # Skilled Hands (EGO)
        ('while you have a bow equipped', 'while you have a musket or bow equipped'),
    ],
    '066857': [  # Eagle Eye (base)
        ('Pressing Block while aiming will', 'Pressing Block while aiming a musket or bow will'),
    ],
    '069D6F': [  # Concentration (EGO)
        ('Bows do 18%%', 'Muskets or bows do 18%%'),
    ],
    '05BD2E': [  # Thief Apprentice (EGO)
        ('while you have a bow equipped', 'while you have a musket or bow equipped'),
    ],
    '069D70': [  # Ranger (base)
        ('with a drawn bow.', 'with a drawn musket or bow.'),
    ],
    '069D71': [  # Rapid Shot (EGO)
        ('You can draw a bow 20%% faster.', 'You can reload muskets or draw bows 20%% faster.'),
    ],
    '069D72': [  # Replica (base) - not musket wording: the perk's new ammo recovery
        ("Automatically gives you a copy of a picked lock's key.",
         "Automatically gives you a copy of a picked lock's key. Musket balls or arrows that hit an "
         "enemy have an additional 30%% chance to be recoverable from their body."),
    ],
    '069D73': [  # Expert Locksmith (EGO)
        ('Bows penetrate 25%%', 'Muskets or bows penetrate 25%%'),
    ],
    '069D74': [  # Fatal Shot (EGO)
        ('critical hit chance with bows.', 'critical hit chance with muskets or bows.'),
    ],
    '069D75': [  # Master of the Bowstring (base)
        ('Zooming in with a bow now', 'Zooming in with a musket or bow now'),
        ('All arrows do 1 more point', 'All musket balls or arrows do 1 more point'),
    ],
    '069D76': [  # Eye of the Storm (EGO)
        ('if your equipped weapon is a bow.', 'if your equipped weapon is a musket or bow.'),
    ],
    '069D77': [  # Shadow Player (EGO)
        ('sneak attack damage with bows', 'sneak attack damage with muskets or bows'),
    ],
    '069D78': [  # Master Thief (EGO)
        ('your arrows often stagger', 'your musket balls or arrows often stagger'),
    ],
}


def winner(fid):
    for d in (EGO, BASE):
        hits = glob.glob(os.path.join(d, f'* - {fid}_Skyrim.esm.yaml'))
        if hits:
            return hits[0]
    sys.exit(f'{fid}: no source record')


def main():
    os.makedirs(OUT, exist_ok=True)
    for fid, pairs in EDITS.items():
        src = winner(fid)
        text = open(src, encoding='utf-8', newline='').read()
        head, sep, rest = text.partition('\nName:')
        if not sep or 'Description:' not in head:
            sys.exit(f'{fid}: Description block not found')
        for old, new in pairs:
            n = head.count(old)
            if n != 1:
                sys.exit(f'{fid}: {old!r} matched {n}x in {src}')
            head = head.replace(old, new)
        dest = os.path.join(OUT, os.path.basename(src))
        open(dest, 'w', encoding='utf-8', newline='').write(head + sep + rest)
        print(f'{fid} <- {src.split("/")[1]}/{src.split("/")[2]}: {len(pairs)} edit(s)')
    print(f'{len(EDITS)} messages written')


if __name__ == '__main__':
    main()
