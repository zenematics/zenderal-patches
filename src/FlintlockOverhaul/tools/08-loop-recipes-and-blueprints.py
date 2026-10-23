"""Zenderal - Flintlock Overhaul: Loop's gun recipes + pistol blueprints at traders. GENERATED - never
hand-edit the ConstructibleObjects/*_Pistol animation by Loop.esp overrides or
LeveledItems/_00ETraderCraftingPlans 137A06; re-run this instead.

1. Loop's "Simple Pistol Shooting Animation" (Pistol animation by Loop.esp) ships 8 example guns as staves on soul
   gems, each with a forge recipe the player can always use (it needs DwarvenSmithing 0CB40E, which the Player
   record starts with). Curator 2026-10-22: every pistol runs on Flintlock Bullets, and the soul-gem crossbows go.
   - the 4 Hunter Pistol recipes stay; 01-build-damage.py converts the pistols themselves;
   - the 4 Hunter Crossbow recipes are hidden with Smithing >= 1000 (the DAR Rifles Recipes Off pattern).
   Every recipe also loses its HearthFires.esm component: the DLC ESMs are empty stubs in Enderal, so the entry
   never resolved (Zenderal - Unresolved References Cleanup used to drop it; with this plugin's records winning
   there is nothing left for it to clean).

2. The flintlock pack's 5 blueprints (PMCraftingPlan*, keyword BlueprintDONOTUSE 02A3D6, so Enderal's blueprint
   folio takes them and the pack's recipes - GetItemCount on the folio 02A3DB - then work) were only in three quest
   containers. Enderal sells blueprints from _00ETraderCraftingPlans 137A06, which ~20 merchant chests and four of
   the chest-loot lists (01E/02E BeuteGross/Mittel/Gering, already owned here) draw from, so one list puts them at
   traders and in the world. Live winner (2026-10-22 scan): Enderal SE - Crossbows, a base-Enderal copy + its
   crossbow plan 000832, which reverted EGO's version (ChanceNone 0.05, all levels 1, 5 more plans). Rule: EGO's
   record verbatim + Crossbows' addition + the 5 pistol blueprints at level 1. This plugin then OWNS 137A06.

Run from the repo root: python -I src/FlintlockOverhaul/tools/08-loop-recipes-and-blueprints.py
"""
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
OUT = os.path.join(ROOT, 'src', 'FlintlockOverhaul', 'FlintlockOverhaulESP')
LOOP_SRC = os.path.join(ROOT, 'reference', 'mods', 'LoopPistol', 'ConstructibleObjects')
EGO_LIST = os.path.join(ROOT, 'reference', 'mods', 'EGO', 'LeveledItems', '_00ETraderCraftingPlansA - 137A06_Skyrim.esm.yaml')
XBOW_LIST = os.path.join(ROOT, 'reference', 'mods', 'EnderalCrossbows', 'LeveledItems', '_00ETraderCraftingPlans - 137A06_Skyrim.esm.yaml')
LOOP = 'Pistol animation by Loop.esp'
FP = 'AdventurerFlintlockPack.esp'
XBOW = 'Enderal SE - Crossbows.esp'
CROSSBOWS = {'000C24', '000C2A', '000C2B', '000824'}   # Hunter Crossbow, +1, +2, +3
PISTOLS = {'000802', '00080B', '00080C', '00080D'}     # Hunter Pistol, +1, +2, +3
XBOW_ADDS = ['000832:' + XBOW]
BLUEPRINTS = ['000800:' + FP, '000825:' + FP, '000826:' + FP, '000827:' + FP, '000828:' + FP]
DLC_STUBS = ('HearthFires.esm', 'Dawnguard.esm', 'Dragonborn.esm')
NL = '\r\n'
HIDE = ('- MutagenObjectType: ConditionFloat' + NL + '  CompareOperator: GreaterThanOrEqualTo' + NL + '  Data:' + NL +
        '    MutagenObjectType: GetActorValueConditionData' + NL + '    RunOnType: Reference' + NL +
        '    Reference: 000014:Skyrim.esm' + NL + '    ActorValue: Smithing' + NL + '  ComparisonValue: 1000' + NL)


def read(path):
    with open(path, encoding='utf-8', newline='') as f:
        return f.read().replace('\r\n', '\n').replace('\n', NL)


def write(folder, name, text):
    d = os.path.join(OUT, folder)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, name), 'w', encoding='utf-8', newline='') as f:
        f.write(text)


# ---------------------------------------------------------------- 1. Loop's recipes
d = os.path.join(OUT, 'ConstructibleObjects')
for f in os.listdir(d):
    if f.endswith('_%s.yaml' % LOOP):
        os.remove(os.path.join(d, f))
done = {'pistol': 0, 'crossbow': 0}
for f in sorted(os.listdir(LOOP_SRC)):
    t = read(os.path.join(LOOP_SRC, f))
    made = re.search(r'^CreatedObject: (\w{6}):(.+)$', t, re.M)
    if not made or made.group(2).strip() != LOOP:
        sys.exit('%s: unexpected CreatedObject' % f)
    kind = 'pistol' if made.group(1) in PISTOLS else 'crossbow' if made.group(1) in CROSSBOWS else None
    if not kind:
        sys.exit('%s: creates %s, neither a Hunter Pistol nor a Hunter Crossbow' % (f, made.group(1)))
    # drop each Items entry whose item is in a DLC stub
    items = re.search(r'^Items:' + NL + r'((?:[- ] .*' + NL + r')+)', t, re.M)
    blocks = re.split(r'(?=^- Item:' + NL + ')', items.group(1), flags=re.M)
    keep = [b for b in blocks if b and not any(':' + s in b for s in DLC_STUBS)]
    dropped = len([b for b in blocks if b]) - len(keep)
    if dropped != 1:
        sys.exit('%s: expected one DLC-stub component, found %d' % (f, dropped))
    t = t.replace(items.group(0), ('Items:' + NL + ''.join(keep)) if keep else '')
    if kind == 'crossbow':
        if '\nConditions:' + NL not in t:
            sys.exit('%s: no Conditions block to extend' % f)
        t = t.replace('Conditions:' + NL, 'Conditions:' + NL + HIDE, 1)
    write('ConstructibleObjects', f, t)
    done[kind] += 1
if done != {'pistol': 4, 'crossbow': 4}:
    sys.exit('expected 4 pistol + 4 crossbow recipes, got %r' % done)

# ---------------------------------------------------------------- 2. trader blueprint list
ego = read(EGO_LIST)
xbow = read(XBOW_LIST)
for ref in XBOW_ADDS:
    if ref not in xbow:
        sys.exit('Crossbows no longer adds %s - rescan its 137A06' % ref)
    if ref in ego:
        sys.exit('EGO already has %s' % ref)
for ref in BLUEPRINTS:
    if ref in ego:
        sys.exit('EGO already has %s' % ref)
add = ''
for ref in XBOW_ADDS:
    m = re.search(r'^- Data:' + NL + r'    Level: (\d+)' + NL + '    Reference: ' + re.escape(ref) + NL + r'    Count: (\d+)' + NL, xbow, re.M)
    if not m:
        sys.exit('could not read Crossbows entry %s' % ref)
    add += m.group(0)
for ref in BLUEPRINTS:
    add += '- Data:' + NL + '    Level: 1' + NL + '    Reference: ' + ref + NL + '    Count: 1' + NL
n_before = ego.count(NL + '- Data:' + NL)
if not ego.endswith(NL) or not re.search(r'^Entries:' + NL, ego, re.M):
    sys.exit('EGO 137A06: unexpected layout')
# Entries is the last key in EGO's record: append there
if re.search(r'^\w', ego.split('Entries:' + NL, 1)[1], re.M):
    sys.exit('EGO 137A06: Entries is not the last key')
out = ego + add
if out.count(NL + '- Data:' + NL) != n_before + len(XBOW_ADDS) + len(BLUEPRINTS):
    sys.exit('entry count check failed')
d = os.path.join(OUT, 'LeveledItems')
for f in os.listdir(d):
    if ' - 137A06_' in f:
        os.remove(os.path.join(d, f))
write('LeveledItems', os.path.basename(EGO_LIST), out)
print('Loop recipes: 4 pistol kept, 4 crossbow hidden; 137A06: %d EGO + %d Crossbows + %d blueprints = %d entries'
      % (n_before, len(XBOW_ADDS), len(BLUEPRINTS), n_before + len(XBOW_ADDS) + len(BLUEPRINTS)))
