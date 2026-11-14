"""Write the stealth setting overrides: EGO's GMST records verbatim with the new values.

Input: tools/gmsts.json from 00-scan-stealth-gmsts.py (the live load order's stealth settings).
Each setting in CHANGES must be set only by the plugins in KNOWN, EGO's value must still be the one
this patch was tuned against, and nothing may load after this patch with that setting. The record
is copied from reference/mods/EGO/GameSettings and must contain exactly one 'Data:' line holding
EGO's value.

Run from the repo root: python -I src/StealthTuning/tools/01-build-stealth-gmsts.py
"""
import json
import os
import re
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
HERE = os.path.dirname(__file__)
SELF = 'Zenderal - Stealth Tuning.esp'
EGO_PLUGIN = 'Enderal SE - Gameplay Overhaul.esp'
EGO_GMSTS = os.path.join(ROOT, 'reference', 'mods', 'EGO', 'GameSettings')
OUT = os.path.join(ROOT, 'src', 'StealthTuning', 'StealthTuningESP', 'GameSettings')
KNOWN = {'Skyrim.esm', 'Enderal SE - Bug Fixes.esp', EGO_PLUGIN, 'Enderal SE - Stealth Overhaul.esp', SELF}

# EditorID: (EGO's value, new value)
CHANGES = {
    # Flat term in every detection check, not reduced by distance. Enderal -19, EGO -13; halfway back,
    # for the early game where the player starts at Sneak 5 (EGO's Player record; Enderal 15).
    'fSneakBaseValue': (-13, -16),
    # How fast a searching NPC finds a hidden player (Enderal 3) and how long it keeps searching after
    # being attacked (Enderal 15 s) or after a detection event (Enderal 10 s): still 2x / 4x / 3x
    # Enderal, so a slip still costs a long search, but backing into shadow can break contact.
    'fCombatStealthPointDrainMult': (12, 6),
    'fCombatStealthPointRegenAttackedWaitTime': (120, 60),
    'fCombatStealthPointRegenDetectedEventWaitTime': (60, 30),
    # EGO's own value, forwarded: Stealth Overhaul loads later with -0.15.
    'fSneakSleepBonus': (-0.2, -0.2),
    # Weight of the player's light level, standing still (Enderal 0.3), and its extra factor outdoors
    # (Enderal 0.5). A tester with every Sneak bonus stacked was still seen up close until level 8:
    # skill does not offset the light term, and up close the distance falloff does not shrink it.
    # 0.6 / 0.6 keeps light the biggest factor (indoors 2x Enderal, outdoors 0.36 vs 0.15).
    'fSneakLightMult': (1, 0.6),
    'fSneakLightExteriorMult': (1, 0.6),
}


def fmt(v):
    return ('%g' % v) if v != int(v) else str(int(v))


def main():
    live = json.load(open(os.path.join(HERE, 'gmsts.json'), encoding='utf-8'))
    files = {}
    for f in os.listdir(EGO_GMSTS):
        m = re.match(r'(\w+) - [0-9A-F]{6}_.+\.yaml$', f)
        if m:
            files[m.group(1)] = f
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    for edid, (ego, new) in sorted(CHANGES.items()):
        chain = live.get(edid, {}).get('chain')
        if not chain:
            raise SystemExit('%s: not in the live load order scan' % edid)
        names = [n for n, _, _ in chain]
        unknown = [n for n in names if n not in KNOWN]
        if unknown:
            raise SystemExit('%s: also set by %s - review before overriding' % (edid, unknown))
        ego_live = [v for n, _, v in chain if n == EGO_PLUGIN]
        if ego_live != [ego]:
            raise SystemExit('%s: EGO sets %s, this patch was tuned against %s' % (edid, ego_live, ego))
        if SELF in names and names[-1] != SELF:
            raise SystemExit('%s: %s loads after %s and reverts it' % (edid, names[-1], SELF))
        src = files.get(edid)
        if not src:
            raise SystemExit('%s: not in %s' % (edid, EGO_GMSTS))
        raw = open(os.path.join(EGO_GMSTS, src), 'rb').read().decode('utf-8')
        out, n = re.subn(r'(?m)^Data: %s(?=\r?$)' % re.escape(fmt(ego)), 'Data: ' + fmt(new), raw)
        if n != 1:
            raise SystemExit('%s: %d Data lines replaced, expected 1' % (src, n))
        for ref in re.findall(r'\b[0-9A-F]{6}:([^\r\n]+?\.es[mp])\b', out):
            if ref != 'Skyrim.esm':
                raise SystemExit('%s: references %s, expected only Skyrim.esm' % (src, ref))
        open(os.path.join(OUT, src), 'wb').write(out.encode('utf-8'))
        print('%-46s %s -> %s   (live: %s)' % (edid, fmt(ego), fmt(new), ' > '.join('%s %s' % (n, v) for n, _, v in chain)))
    print('%d settings written' % len(CHANGES))


if __name__ == '__main__':
    sys.exit(main())
