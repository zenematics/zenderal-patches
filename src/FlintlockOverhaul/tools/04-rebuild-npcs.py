"""Zenderal - Flintlock Overhaul: rebuild every NPC the gun mods override. GENERATED - never hand-edit
Npcs/ or the ZP_DeathItem* LeveledItems; re-run this instead (after 00-scan-overriders.py).

Why: Ordo Legionis (Muskets of the Enderal) overrides 95 NPCs and A Gentleman's Flintlock Armoury 17,
both with copies of BASE Enderal/FS records, loading after EGO (82 + 10 of them), our UCR patch (2) and
EGO's Kata package (1) - so they silently revert those NPCs' levels, skills, perks, AI and outfits.
Enderal SE - Crossbows (8 of the same NPCs, also a base copy) loads after Ordo and reverts Ordo's
muskets on those 8 in turn.

Rule, per NPC (chain = tools/overriders.json, a load-order scan of every active plugin):
  record = the last NON-gun plugin's record, verbatim (de-localised: this plugin is not Localized)
  + each gun plugin's INVENTORY delta vs the record it copied (FS if FS defines it, else Skyrim):
    added counts are added, removed counts are removed where the winner still has them
  - entries pointing at pistols the flintlock porter deleted (812-815, 81E-820) are dropped
  then:
  * HOSTILE musket NPCs (EditorID has Bandit / Nehrimes / Soeldner), sorted by EditorID, every
    second one swaps its Ordo musket + Ordo ammo for a low-tier pistol + Flintlock Bullets
    (curator, 2026-10-12: "50/50 ... make sure ammo is also included for both").
    Pistol by the EditorID's level prefix: <= 10 alternates Flintlock Pistol / Ancient Dueling
    Pistol, otherwise Priest's Dueling Pistol - the three lowest-damage pistols, the only ones NPCs get.
  * NON-HUMAN flintlock carriers (curator: only human enemies have guns) lose the pistol from
    their inventory; it goes into a new UseAll death list (0x80E+) = old DeathItem + the pistol,
    so it still drops as boss loot but is never wielded. Blueprints stay (they are not guns).
  The orphan 02DE35:FS "Gravewarden" (no such record in FS - never placed) is skipped.

Run from the repo root: python -I src/FlintlockOverhaul/tools/04-rebuild-npcs.py
"""
import collections
import glob
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
REF = os.path.join(ROOT, 'reference')
OUTD = os.path.join(ROOT, 'src', 'FlintlockOverhaul', 'FlintlockOverhaulESP')
ME = 'Zenderal - Flintlock Overhaul.esp'
FP = 'AdventurerFlintlockPack.esp'
ORDO = 'OrdoLegionisMuskets.esp'
CROSS = 'Enderal SE - Crossbows.esp'
GUN = {ORDO: 'mods/OrdoEnderal', FP: 'mods/FlintlockPack', CROSS: 'mods/EnderalCrossbows'}
TREES = {
    'Skyrim.esm': 'base/Skyrim',
    'Enderal - Forgotten Stories.esm': 'base/EnderalFS',
    'Enderal SE - Gameplay Overhaul.esp': 'mods/EGO',
    'EGO - KataPUMB Spell Package.esp': 'mods/EGOKataPUMB',
    'Zenderal - Undead Creatures Replacer EGO Patch.esp':
        '../src/UndeadCreaturesReplacerEGO/UndeadCreaturesReplacerEGOESP',
}
SKIP = {'02DE35:Enderal - Forgotten Stories.esm'}
DEAD = {'%06X:%s' % (i, FP) for i in (0x812, 0x813, 0x814, 0x815, 0x81E, 0x81F, 0x820)}
PISTOLS = {'%06X:%s' % (i, FP) for i in (0x816, 0x817, 0x818, 0x819, 0x834, 0x838, 0x839, 0x83A)}
FLINTLOCK, ANCIENT, PRIESTS = '000838:' + FP, '000816:' + FP, '000817:' + FP
BULLET = '000800:' + ME
ORDO_AMMO = {'002F9D:' + ORDO, '00F5E1:' + ORDO, '00F5BE:' + ORDO}
HOSTILE = re.compile(r'Bandit|Nehrimes|Soeldner')
NONHUMAN = {'SkeletonRace', 'DraugrRace', 'DwarvenCenturionRace', 'GiantRace', 'DragonPriestRace',
            'WispShadeRaceFire', '_00E_StoneGolemRaceBig'}
DEATH_BASE = 0x80E


def read(path):
    with open(path, encoding='utf-8') as f:
        return f.read().replace('\r\n', '\n')


def find(tree, fk):
    h, plugin = fk.split(':', 1)
    g = glob.glob(os.path.join(REF, tree, 'Npcs', '* - %s_%s.yaml' % (h, plugin)))
    return g[0] if g else None


def races():
    out = {}
    for d in ('base/Skyrim', 'base/EnderalFS', 'mods/EGO'):
        for f in glob.glob(os.path.join(REF, d, 'Races', '*.yaml')):
            t = read(f)
            out[re.search(r'FormKey: (.+)', t).group(1)] = re.search(r'EditorID: (\S+)', t).group(1)
    return out


def blocks(text):
    out = collections.OrderedDict()
    cur = None
    for line in text.split('\n'):
        if not line:
            continue
        if line[0] not in ' -':
            cur = line.split(':', 1)[0]
            out[cur] = [line]
        else:
            out[cur].append(line)
    return out


def delocalize(lines):
    out, i = [], 0
    while i < len(lines):
        m = re.match(r'^(\s*)Values:$', lines[i])
        if m:
            ind = m.group(1)
            j, eng = i + 1, None
            while j < len(lines) and (lines[j].startswith(ind + '- ') or lines[j].startswith(ind + '  ')):
                s = re.match(r'^\s+String: (.*)$', lines[j])
                if s and re.match(r'^\s*- Language: English$', lines[j - 1]):
                    eng = s.group(1)
                j += 1
            if eng is None:
                sys.exit('no English string in Values block: %r' % lines[i - 1:i + 3])
            out.append('%sValue: %s' % (ind, eng))
            i = j
            continue
        out.append(lines[i])
        i += 1
    return out


def items(blk):
    """Items block -> ordered {FormKey: [count, extra lines]} (extra = ownership etc., kept verbatim)."""
    out = collections.OrderedDict()
    if not blk:
        return out
    cur = None
    for line in blk[1:]:
        if line == '- Item:':
            cur = None
            continue
        m = re.match(r'^    Item: (.+)$', line)
        if m:
            cur = m.group(1)
            out[cur] = [0, []]
            continue
        m = re.match(r'^    Count: (-?\d+)$', line)
        if m and cur:
            out[cur][0] = int(m.group(1))
            continue
        if cur:
            out[cur][1].append(line)
    return out


def items_block(d):
    if not d:
        return []
    lines = ['Items:']
    for fk, (count, extra) in d.items():
        if count <= 0:
            continue
        lines += ['- Item:', '    Item: ' + fk, '    Count: %d' % count] + extra
    return lines if len(lines) > 1 else []


def main():
    chains = json.load(open(os.path.join(os.path.dirname(__file__), 'overriders.json'), encoding='utf-8'))
    race_ed = races()
    for sub in ('Npcs',):
        d = os.path.join(OUTD, sub)
        os.makedirs(d, exist_ok=True)
        for f in os.listdir(d):
            os.remove(os.path.join(d, f))
    ldir = os.path.join(OUTD, 'LeveledItems')
    os.makedirs(ldir, exist_ok=True)
    for f in os.listdir(ldir):
        if f.startswith('ZP_DeathItem'):
            os.remove(os.path.join(ldir, f))

    built = {}      # fk -> (edid, blocks, item dict)
    stats = collections.Counter()
    warn = []
    for fk, chain in sorted(chains.items()):
        if fk in SKIP:
            stats['skipped orphan'] += 1
            continue
        prev = [p for p in chain if p not in GUN]
        if not prev or prev[-1] not in TREES:
            sys.exit('%s: no serialized tree for previous winner %r (chain %r)' % (fk, prev[-1:], chain))
        winner = prev[-1]
        path = find(TREES[winner], fk)
        if not path:
            sys.exit('%s: not found in %s' % (fk, TREES[winner]))
        b = blocks(read(path))
        for k in list(b):
            b[k] = delocalize(b[k])
        inv = items(b.get('Items'))
        src = find('base/EnderalFS', fk) or find('base/Skyrim', fk)
        base_inv = items(blocks(read(src)).get('Items')) if src else collections.OrderedDict()
        for g in [p for p in chain if p in GUN]:
            if g == ORDO and CROSS in chain:
                # Crossbows loads after Ordo and won these in game (crossbow, no musket): keep that
                stats['Ordo skipped, Crossbows wins'] += 1
                continue
            gi = items(blocks(read(find(GUN[g], fk))).get('Items'))
            for k in set(gi) | set(base_inv):
                delta = gi.get(k, [0])[0] - base_inv.get(k, [0])[0]
                if delta > 0:
                    if k in DEAD:
                        stats['dead pistol entries dropped'] += 1
                        continue
                    if k in inv:
                        inv[k][0] += delta
                    else:
                        inv[k] = [delta, gi[k][1]]
                elif delta < 0:
                    if k in inv and inv[k][0] > 0:
                        inv[k][0] = max(0, inv[k][0] + delta)
                    else:
                        warn.append('%s: %s removes %s, which the winner (%s) no longer has' % (fk, g, k, winner))
        edid = b['EditorID'][0].split(': ', 1)[1]
        built[fk] = (edid, b, inv, winner, chain)
        stats['winner ' + winner] += 1

    # --- 50/50 musket -> pistol on hostile musket NPCs
    musketeers = sorted((v[0], fk) for fk, v in built.items()
                        if HOSTILE.search(v[0]) and any(k.endswith(':' + ORDO) and k not in ORDO_AMMO
                                                        for k, (c, _) in v[2].items() if c > 0))
    low = 0
    swapped = []
    for n, (edid, fk) in enumerate(musketeers):
        if n % 2 == 0:
            continue
        inv = built[fk][2]
        ammo = sum(inv[k][0] for k in ORDO_AMMO if k in inv)
        for k in list(inv):
            if k.endswith(':' + ORDO):
                del inv[k]
        m = re.match(r'_(\d\d)E_', edid)
        level = int(m.group(1)) if m else 99
        if level <= 10:
            pistol = (FLINTLOCK, ANCIENT)[low % 2]
            low += 1
        else:
            pistol = PRIESTS
        inv[pistol] = [1, []]
        inv[BULLET] = [max(5, min(10, ammo)), []]
        swapped.append((edid, pistol.split(':')[0]))

    # --- non-human flintlock carriers: pistol -> death list
    death = []
    for fk, (edid, b, inv, winner, chain) in sorted(built.items(), key=lambda x: x[1][0]):
        race = race_ed.get(b.get('Race', ['Race: ?'])[0].split(': ', 1)[1], '?')
        guns = [k for k in inv if k in PISTOLS and inv[k][0] > 0]
        if not guns or race not in NONHUMAN:
            continue
        lid = '%06X' % (DEATH_BASE + len(death))
        old = b.get('DeathItem', [None])[0]
        entries = []
        if old:
            entries.append(old.split(': ', 1)[1])
        entries += guns
        for g in guns:
            del inv[g]
        ledid = 'ZP_DeathItem_' + edid.lstrip('_')
        lines = ['FormKey: %s:%s' % (lid, ME), 'EditorID: ' + ledid, 'Flags:', '- UseAll', 'Entries:']
        for e in entries:
            lines += ['- Data:', '    Level: 1', '    Reference: ' + e, '    Count: 1']
        with open(os.path.join(ldir, '%s - %s_%s.yaml' % (ledid, lid, ME)), 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(lines) + '\n')
        new = 'DeathItem: %s:%s' % (lid, ME)
        if 'DeathItem' in b:
            b['DeathItem'] = [new]
        else:   # insert before Race, where Spriggit writes DeathItem
            nb = collections.OrderedDict()
            for k, v in b.items():
                if k == 'Race':
                    nb['DeathItem'] = [new]
                nb[k] = v
            b.clear()
            b.update(nb)
        death.append((edid, race, [g.split(':')[0] for g in guns], old))

    # --- write
    for fk, (edid, b, inv, winner, chain) in built.items():
        blk = items_block(inv)
        if blk:
            if 'Items' in b:
                b['Items'] = blk
            else:   # place it where the gun mod's own copy has it: before the next key that exists here
                order = list(blocks(read(find(GUN[[g for g in chain if g in GUN][-1]], fk))))
                after = [k for k in order[order.index('Items') + 1:] if k in b]
                if not after:
                    sys.exit('%s: cannot place an Items block' % edid)
                nb = collections.OrderedDict()
                for k, v in b.items():
                    if k == after[0]:
                        nb['Items'] = blk
                    nb[k] = v
                b.clear()
                b.update(nb)
                stats['Items block inserted'] += 1
        elif 'Items' in b:
            del b['Items']
        text = '\n'.join(line for v in b.values() for line in v) + '\n'
        h, plugin = fk.split(':', 1)
        with open(os.path.join(OUTD, 'Npcs', '%s - %s_%s.yaml' % (edid, h, plugin)), 'w',
                  encoding='utf-8', newline='\n') as f:
            f.write(text)

    for k, v in sorted(stats.items()):
        print('%-50s %d' % (k, v))
    print('hostile musket NPCs: %d, swapped to pistols: %d' % (len(musketeers), len(swapped)))
    for e, p in swapped:
        print('   pistol %s  %s' % (p, e))
    print('non-human pistol carriers moved to death lists: %d' % len(death))
    for d in death:
        print('   %s (%s): %s, old DeathItem %s' % d)
    print('warnings: %d' % len(warn))
    for w in warn:
        print('   ' + w)
    if len(built) != 111:
        sys.exit('expected 111 NPCs, built %d' % len(built))
    if len(death) + DEATH_BASE > 0x830:
        sys.exit('death lists ran past the allocated block')


if __name__ == '__main__':
    main()
