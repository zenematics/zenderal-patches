"""Build the records of `Zenderal - Lost Ones Dismembering.esp` from DF's own records.

Sources (gitignored; regenerate with the spriggit-decompile-reference skill):
  reference/mods/DFOfficialCreaturePack  <- DF - Official Creature Pack.esp
  reference/mods/DFXtudoCanidae          <- DF - Xtudo Creature Pack - Canidae - A Wolf Replacer.esp
Never hand-edit the YAML this writes.

1. Five skeleton limb MiscItems (0x800-0x804). Each is DF's naked male draugr limb item copied verbatim
   (DFDefaultLimbRefScript + its five global properties, the DF limb keyword) with a new EditorID and
   its model pointed at the skeleton limb mesh 03-build-skeleton-limbs.py generates.
2. DF's five draugr body-cap ARMAs (000805-000809) overridden to add UCR's LostOneTemplateRace as an
   additional race. The ARMAs are race-locked to DraugrRace, so before this the Lost Ones that
   01-build-lost-ones-data.py maps onto the draugr limbs lost a limb with no stump cap on the body.
   The skeleton races are deliberately NOT added: the caps are draugr flesh, and a bare skeleton
   needs none (equipped, a race-locked ARMA simply renders nothing).
3. DF's 18 wolf body-cap ARMAs (Default 000868/86F-872/874, Black 000880-883, Red 000884-88B) forwarded
   from their winner, the Xtudo Canidae plugin (Canidae meshes), with Enderal's own wolf races
   WolfRaceLarge/WolfRaceSmall (FS) and WolfHoheRace added; they are race-locked to WolfRace.
   In a profile with `Fluffworks - Dismembering Framework Patch.esp` this plugin must load BEFORE it:
   Fluffworks overrides 000880 (alternate fur textures) and routes the black/red caps through its own
   ARMAs, which do not get the extra races.
4. One MiscItem per minotaur limb mesh in minotaur-limbs.json (04-build-minotaur-limbs.py; 0x805 up),
   each DF's naked draugr limb item of the same limb copied with a new EditorID and model.
5. One MiscItem per spider leg in spider-limbs.json (05-build-spider-limbs.py; 0x833 up), same pattern.
   Shelved: only when SPIDERS is True.

Usage:  python 02-build-records.py
"""
import json
import os
import re
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
REF = os.path.join(ROOT, 'reference', 'mods', 'DFOfficialCreaturePack')
REF_WOLF = os.path.join(ROOT, 'reference', 'mods', 'DFXtudoCanidae')
ESP = os.path.join(HERE, '..', 'LostOnesDismemberingESP')
MOD_KEY = 'Zenderal - Lost Ones Dismembering.esp'
DF_KEY = 'DF - Official Creature Pack.esp'
LOST_ONE_RACE = '00398C:Undead Creatures Replacer.esp'
WOLF_RACES = ['0133E3:Enderal - Forgotten Stories.esm', '0133EF:Enderal - Forgotten Stories.esm',
              '117FCC:Skyrim.esm']
WOLF_ARMAS = ['000868', '00086F', '000870', '000871', '000872', '000874'] + [f'{i:06X}' for i in range(0x880, 0x88C)]
BS = chr(92)
MESH_DIR = BS.join(['DismemberingFramework', 'Zenderal', 'LostOnesSkeleton'])

MINOTAUR_PLAN = os.path.join(HERE, 'minotaur-limbs.json')
SPIDER_PLAN = os.path.join(HERE, 'spider-limbs.json')
# Spiders are SHELVED (2026-10-19): every leg cut made DF rebuild the corpse's 3D and Spider SE's 25.8 MB
# body blinked out for ~8 s (see arch-docs/patches/LostOnesDismembering.md). 05-build-spider-limbs.py and
# limbmesh's hull fitting are kept; set True to ship the spider legs again.
SPIDERS = False
# DF naked male draugr limb item each minotaur limb item is copied from (only the script + keyword matter)
DRAUGR_LIMB_ITEM = {'Calf_L': '000810', 'Calf_R': '000811', 'Forearm_L': '000812', 'Forearm_R': '000813',
                    'Head': '000814'}

# (new FormID, limb name, DF source limb MiscItem, DF body-cap ARMA)
LIMBS = [
    ('000800', 'Calf_L', '000810', '000805'),
    ('000801', 'Calf_R', '000811', '000806'),
    ('000802', 'Forearm_L', '000812', '000807'),
    ('000803', 'Forearm_R', '000813', '000808'),
    ('000804', 'Head', '000814', '000809'),
]


def ref_file(folder, fid, ref=REF):
    hits = [f for f in os.listdir(os.path.join(ref, folder)) if f.endswith(f' - {fid}_{DF_KEY}.yaml')]
    assert len(hits) == 1, (folder, fid, hits)
    return os.path.join(ref, folder, hits[0])


def sub_once(pattern, repl, text, what):
    out, n = re.subn(pattern, lambda _: repl, text, flags=re.M)
    assert n == 1, (what, pattern, n)
    return out


def add_races(path, race, races):
    """Copy an ARMA verbatim with an AdditionalRaces list appended; asserts its main race."""
    src = open(path, encoding='utf-8').read()
    assert 'AdditionalRaces' not in src, path
    assert re.search(r'^Race: ' + re.escape(race) + r'(?=\r?$)', src, re.M), (path, race)
    nl = '\r\n' if '\r\n' in src else '\n'
    out = src.rstrip('\r\n') + nl + 'AdditionalRaces:' + nl + ''.join('- ' + r + nl for r in races)
    with open(os.path.join(ESP, 'ArmorAddons', os.path.basename(path)), 'w', encoding='utf-8', newline='') as fh:
        fh.write(out)


def main():
    for folder in ('MiscItems', 'ArmorAddons'):
        shutil.rmtree(os.path.join(ESP, folder), ignore_errors=True)
        os.makedirs(os.path.join(ESP, folder))

    for fid, limb, src_misc, src_arma in LIMBS:
        # --- skeleton limb item -------------------------------------------------------------
        src = open(ref_file('MiscItems', src_misc), encoding='utf-8').read()
        assert 'DFDefaultLimbRefScript' in src and f'Naked_{limb}_Limb' in src, src_misc
        edid = f'ZEN_LostOnes_Skeleton_{limb}_Limb'
        out = sub_once(r'^FormKey: \S+:' + re.escape(DF_KEY) + r'(?=\r?$)', f'FormKey: {fid}:{MOD_KEY}', src, 'formkey')
        out = sub_once(r'^EditorID: \S+(?=\r?$)', f'EditorID: {edid}', out, 'edid')
        out = sub_once(r'^  File: .*(?=\r?$)', '  File: ' + MESH_DIR + BS + limb + '.nif', out, 'model')
        with open(os.path.join(ESP, 'MiscItems', f'{edid} - {fid}_{MOD_KEY}.yaml'), 'w', encoding='utf-8', newline='') as fh:
            fh.write(out)

        # --- draugr body-cap ARMA override ----------------------------------------------------
        add_races(ref_file('ArmorAddons', src_arma), '000D53:Skyrim.esm', [LOST_ONE_RACE])
        print(f'{fid} {edid}  +  ARMA {src_arma} += LostOneTemplateRace')

    # --- minotaur limb items (plan from 04-build-minotaur-limbs.py) ---------------------------
    plan = json.load(open(MINOTAUR_PLAN, encoding='utf-8'))
    for e in plan:
        src = open(ref_file('MiscItems', DRAUGR_LIMB_ITEM[e['limb']]), encoding='utf-8').read()
        edid = f'ZEN_Minotaur_{e["limb"]}_{e["fid"][-3:]}_Limb'
        out = sub_once(r'^FormKey: \S+:' + re.escape(DF_KEY) + r'(?=\r?$)', f'FormKey: {e["fid"]}:{MOD_KEY}', src, 'formkey')
        out = sub_once(r'^EditorID: \S+(?=\r?$)', f'EditorID: {edid}', out, 'edid')
        out = sub_once(r'^  File: .*(?=\r?$)', '  File: ' + e['mesh'], out, 'model')
        with open(os.path.join(ESP, 'MiscItems', f'{edid} - {e["fid"]}_{MOD_KEY}.yaml'), 'w', encoding='utf-8', newline='') as fh:
            fh.write(out)
    print(f'{len(plan)} minotaur limb items {plan[0]["fid"]}-{plan[-1]["fid"]}')

    if SPIDERS:
        # --- spider leg items (plan from 05-build-spider-limbs.py) --------------------------------
        plan = json.load(open(SPIDER_PLAN, encoding='utf-8'))
        for e in plan:
            src = open(ref_file('MiscItems', DRAUGR_LIMB_ITEM[e['item_limb']]), encoding='utf-8').read()
            edid = f'ZEN_Spider_{e["limb"]}_Limb'
            out = sub_once(r'^FormKey: \S+:' + re.escape(DF_KEY) + r'(?=\r?$)', f'FormKey: {e["fid"]}:{MOD_KEY}', src, 'formkey')
            out = sub_once(r'^EditorID: \S+(?=\r?$)', f'EditorID: {edid}', out, 'edid')
            out = sub_once(r'^  File: .*(?=\r?$)', '  File: ' + e['mesh'], out, 'model')
            with open(os.path.join(ESP, 'MiscItems', f'{edid} - {e["fid"]}_{MOD_KEY}.yaml'), 'w', encoding='utf-8', newline='') as fh:
                fh.write(out)
        print(f'{len(plan)} spider leg items {plan[0]["fid"]}-{plan[-1]["fid"]}')

    # --- wolf body-cap ARMAs, forwarded from the Xtudo Canidae winner -------------------------
    assert len(os.listdir(os.path.join(REF_WOLF, 'ArmorAddons'))) == len(WOLF_ARMAS), 'Xtudo Canidae changed'
    for fid in WOLF_ARMAS:
        add_races(ref_file('ArmorAddons', fid, REF_WOLF), '01320A:Skyrim.esm', WOLF_RACES)
    print(f'{len(WOLF_ARMAS)} wolf ARMAs (Xtudo Canidae versions) += WolfRaceLarge, WolfRaceSmall, WolfHoheRace')


if __name__ == '__main__':
    main()
