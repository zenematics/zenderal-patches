"""Write the Armor Balance overrides: each winning record verbatim from reference/mods, plus the fields below.

1. Fuse00's Adventurer set (_Fuse00_AdventurerArmor.esp, a Skyrim mod): 25/15/10/10 with recipes that have no
   conditions at all, and tagged ArmorHeavy + ArmorMaterialIron while light armor (EGO's heavy-armor spell-cost
   perk XionArmorHeavyPlayer applied to it, Vagrant's light-armor talents skipped it). Now Firm Leather's forged
   numbers 19.8/12.1/8.6/7.0, ArmorLight + ArmorMaterialLeather, and Smithing >= 20 on its 4 recipes (EGO's
   Firm Leather gate; there is no Enderal blueprint for it). Backpacks and tempering left alone.
2. Grievous Rose Multicolor: its craft book recipe 000813 has no items and no conditions, so the 30-armor dress
   could be made at once; the Enderal integration (Nexus Enderal 982) means the book to drop from Adila late in
   the main quest. The recipe gets Smithing >= 1000 (the DAR Rifles Recipes Off pattern).
3. Pretty Pyrean's Jakal's Soldier Cuirass 000810 (EditorID tier 19, lootable from the MQ07a soldiers): 34.8,
   above the best light cuirass (Aeterna 33.3). Now 26.6, a quarter of the way from Pyrean (tier 18, 25.9) to
   Assassin (tier 22, 28.8).

Input: tools/armor.json from 00-scan-armor.py, to check each source record still wins (before this plugin) and
still has the values edited here. Every FormKey written must belong to a declared master.

Run from the repo root: python -I src/ArmorBalance/tools/00-scan-armor.py, then this.
"""
import json
import os
import re
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
HERE = os.path.dirname(__file__)
REF = os.path.join(ROOT, 'reference', 'mods')
OUT = os.path.join(ROOT, 'src', 'ArmorBalance', 'ArmorBalanceESP')
ME = 'Zenderal - Armor Balance.esp'
FUSE = '_Fuse00_AdventurerArmor.esp'
ROSE = 'Grievous Rose Multicolor.esp'
PRETTY = 'Pretty Pyrean Armory.esp'
MASTERS = {'Skyrim.esm', 'Update.esm', 'Enderal - Forgotten Stories.esm', FUSE, ROSE, PRETTY}
SOURCES = {FUSE: 'Fuse00AdventurerArmor', ROSE: 'GrievousRoseMulticolor', PRETTY: os.path.join('Pretty', 'Pretty Pyrean Armory')}  # 2.1 serialization (2026-11-11)

ARMOR_HEAVY, ARMOR_LIGHT = '06BBD2:Skyrim.esm', '06BBD3:Skyrim.esm'
MATERIAL_IRON, MATERIAL_LEATHER = '06BBE3:Skyrim.esm', '06BBDB:Skyrim.esm'

# ARMO: FormKey -> (armor rating now, new armor rating, re-tag as light leather)
ARMORS = {
    '00080F:' + FUSE: (25, 19.8, True),      # Adventurer Armor    = Firm Leather Cuirass (forged)
    '00080B:' + FUSE: (15, 12.1, True),      # Adventurer Hood     = Firm Leather Helmet (forged)
    '000817:' + FUSE: (10, 8.6, True),       # Adventurer Gauntlets = Firm Leather Arm Protector (forged)
    '000813:' + FUSE: (10, 7.0, True),       # Adventurer Boots    = Firm Leather Shoes (forged)
    '000810:' + PRETTY: (34.8, 26.6, False),  # Jakal's Soldier Cuirass
}
# COBJ: FormKey -> Smithing needed
RECIPES = {
    '000811:' + FUSE: 20,      # _Fuse00_Adv_Body_Recipe
    '00080C:' + FUSE: 20,      # _Fuse00_Recipe_Adv_Hood
    '000819:' + FUSE: 20,      # _Fuse00_Adv_Gloves_Recipe
    '000815:' + FUSE: 20,      # _Fuse00_Adv_Boots_Recipe
    '000813:' + ROSE: 1000,    # 000_RecipeArmor_Book: hidden
}


def source_file(fk, folder):
    local, plugin = fk.split(':', 1)
    d = os.path.join(REF, SOURCES[plugin], folder)
    hits = [f for f in os.listdir(d) if f.endswith(' - %s_%s.yaml' % (local, plugin))]
    if len(hits) != 1:
        raise SystemExit('%s: expected one file in %s, found %r' % (fk, d, hits))
    return os.path.join(d, hits[0])


def winner_before_me(chain):
    rest = [p for p in chain if p != ME]
    return rest[-1]


def sub1(pattern, repl, text, what):
    new, n = re.subn(pattern, repl, text, flags=re.M)
    if n != 1:
        raise SystemExit('%s: expected 1 replacement, got %d' % (what, n))
    return new


def smithing(value, nl):
    return nl.join(['Conditions:', '- MutagenObjectType: ConditionFloat', '  CompareOperator: GreaterThanOrEqualTo',
                    '  Data:', '    MutagenObjectType: GetActorValueConditionData', '    RunOnType: Reference',
                    '    Reference: 000014:Skyrim.esm', '    ActorValue: Smithing', '  ComparisonValue: %d' % value, ''])


def retag(text, fk, nl):
    block = re.search(r'^Keywords:\r?\n((?:- .*\r?\n)+)', text, re.M)
    if not block:
        raise SystemExit('%s: no Keywords list' % fk)
    kws = re.findall(r'^- (\S+)', block.group(1), re.M)
    if kws.count(MATERIAL_IRON) != 1 or ARMOR_LIGHT in kws or MATERIAL_LEATHER in kws:
        raise SystemExit('%s: unexpected keywords %r' % (fk, kws))
    new = [k for k in kws if k != ARMOR_HEAVY]
    new = [MATERIAL_LEATHER if k == MATERIAL_IRON else k for k in new]
    new.insert(0, ARMOR_LIGHT)
    return text.replace(block.group(0), 'Keywords:' + nl + ''.join('- %s%s' % (k, nl) for k in new), 1)


def write(folder, src, text):
    for plugin in re.findall(r'\b[0-9A-F]{6}:([^\r\n]+?\.es[mpl])\b', text):
        if plugin not in MASTERS:
            raise SystemExit('%s: references undeclared master %s' % (src, plugin))
    d = os.path.join(OUT, folder)
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, os.path.basename(src)), 'wb').write(text.encode('utf-8'))


def main():
    live = json.load(open(os.path.join(HERE, 'armor.json'), encoding='utf-8'))
    for folder in ('Armors', 'ConstructibleObjects'):
        if os.path.isdir(os.path.join(OUT, folder)):
            shutil.rmtree(os.path.join(OUT, folder))

    for fk, (old, new, light_leather) in sorted(ARMORS.items()):
        rec = live['armor'].get(fk)
        if not rec or winner_before_me(rec['chain']) != fk.split(':', 1)[1]:
            raise SystemExit('%s: no longer won by its own plugin (%r) - rescan and review' % (fk, rec and rec['chain']))
        src = source_file(fk, 'Armors')
        text = open(src, 'rb').read().decode('utf-8')
        nl = '\r\n' if '\r\n' in text else '\n'
        text = sub1(r'^ArmorRating: %s(?=\r?$)' % re.escape('%g' % old), 'ArmorRating: %g' % new, text, fk + ' rating')
        if 'ArmorType:' in text:
            raise SystemExit('%s: not light armor' % fk)       # Mutagen omits ArmorType when it is LightArmor
        if light_leather:
            text = retag(text, fk, nl)
        write('Armors', src, text)

    for fk, value in sorted(RECIPES.items()):
        rec = live['recipes'].get(fk)
        if not rec or rec['winner'] != fk.split(':', 1)[1] and rec['winner'] != ME:
            raise SystemExit('%s: recipe won by %s - rescan and review' % (fk, rec and rec['winner']))
        src = source_file(fk, 'ConstructibleObjects')
        text = open(src, 'rb').read().decode('utf-8')
        nl = '\r\n' if '\r\n' in text else '\n'
        if re.search(r'^Conditions:', text, re.M):
            raise SystemExit('%s: already has conditions - merge instead of inserting' % fk)
        text = sub1(r'^(?=CreatedObject: )', smithing(value, nl), text, fk + ' conditions')
        write('ConstructibleObjects', src, text)

    print('%d armor + %d recipe overrides written' % (len(ARMORS), len(RECIPES)))


if __name__ == '__main__':
    sys.exit(main())
