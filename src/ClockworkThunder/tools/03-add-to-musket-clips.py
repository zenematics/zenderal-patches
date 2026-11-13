"""Give Clockwork Thunder the Nehrimese rifle's per-mesh musket clips: first-person aim down sights and the
ramrod reload (third and first person, with the ball and ramrod props).

Those OAR submods are generated per Ordo mesh by src/FlintlockOverhaul/tools/06 (ADS, now shipped inside
Zenderal - Patch Collection) and 09/10 (MO2 mod Zenderal - Musket Ramrod Reload), each keyed on an OR of
IsEquipped(<Ordo musket>, right hand). Clockwork Thunder's mesh is OL_Musket_Rifle's with cogs and a cog-shaped
trigger guard: same barrel, sights, grip and muzzle, so the rifle's clips fit it as they are.

tools/06's EXTRA_MUSKETS puts it into the rifle's group for any future rerun of 06 -> 09 -> 10 -> 11 -> 12. This
script makes the same change to the configs installed now, without rerunning that chain (06's standalone output
mod no longer exists, and 12 needs the curator's licensed .wav files): next to every
IsEquipped(OrdoLegionisMuskets.esp | 2F9B) it adds IsEquipped(Zenderal - Clockwork Thunder.esp | 800), same
shape. Idempotent; refuses to run unless it finds exactly EXPECTED configs.

Usage:  python src/ClockworkThunder/tools/03-add-to-musket-clips.py [--dry-run]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
TOOLS = json.load(open(os.path.join(ROOT, '.claude', 'config', 'tools.json'), encoding='utf-8-sig'))
MODS = os.path.join(TOOLS['modlistRoot'], 'mods')
SEARCH = ['Zenderal - Patch Collection', 'Zenderal - Musket Ramrod Reload']
RIFLE = ('OrdoLegionisMuskets.esp', '2F9B')
GUN = ('Zenderal - Clockwork Thunder.esp', '800')
EXPECTED = 7     # ADS x2 (Patch Collection), ramrod 3P x3 + 1P x2 (2026-11-13)


def is_equipped(c, plugin, fid):
    f = c.get('Form', {})
    return c.get('condition') == 'IsEquipped' and f.get('pluginName') == plugin and f.get('formID') == fid


def patch(conds):
    """Walk a condition list; in each list holding the rifle, add the gun right after it. Returns (rifle, added)."""
    found = added = 0
    for i in range(len(conds) - 1, -1, -1):
        c = conds[i]
        if isinstance(c.get('Conditions'), list):
            f, a = patch(c['Conditions'])
            found += f
            added += a
        if is_equipped(c, *RIFLE):
            found += 1
            if not any(is_equipped(x, *GUN) for x in conds):
                new = json.loads(json.dumps(c))
                new['Form'] = {'pluginName': GUN[0], 'formID': GUN[1]}
                conds.insert(i + 1, new)
                added += 1
    return found, added


def main():
    dry = '--dry-run' in sys.argv
    hits = []
    for mod in SEARCH:
        for dirpath, _, files in os.walk(os.path.join(MODS, mod)):
            if 'config.json' in files:
                p = os.path.join(dirpath, 'config.json')
                text = open(p, encoding='utf-8').read()
                if '"%s"' % RIFLE[1] in text and RIFLE[0] in text:
                    hits.append(p)
    if len(hits) != EXPECTED:
        sys.exit('expected %d configs naming the rifle, found %d:\n  %s' % (EXPECTED, len(hits), '\n  '.join(hits)))
    for p in hits:
        cfg = json.load(open(p, encoding='utf-8'))
        found, added = patch(cfg['conditions'])
        assert found >= 1, p
        print('%s %s (rifle x%d)' % ('add ' if added else 'have', os.path.relpath(p, MODS), found))
        if added and not dry:
            with open(p, 'w', encoding='utf-8') as fh:
                json.dump(cfg, fh, indent=4)


if __name__ == '__main__':
    main()
