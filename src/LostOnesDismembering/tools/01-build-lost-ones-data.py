"""Build the Dismembering Framework JSON for `Zenderal - Lost Ones Dismembering`.

DF picks severed-limb meshes by the actor's race EDITORID (then skin, then sex). Its Official Creature
Asset Pack covers `DraugrRace` only, so no Lost One outside that race was ever dismembered:

* `LostOneTemplateRace` (00398C:Undead Creatures Replacer.esp; ~72 NPCs after the Lost Ones Revised EGO
  patch) is a draugr in all but name: same `Actors\\Draugr\\Character Assets\\Skeleton.nif`,
  `DraugrProject.hkx` and body part data `048C13`, bodies textured with vanilla
  `textures\\actors\\draugr\\draugr.dds`. It gets the pack's `DraugrRace` -> `ANY` entries verbatim (the
  naked draugr limbs and heads), so a DF or pack update carries over on the next run.
* `mihailancientskeletonrace` (Lost Ones Revised, 37 NPCs) and `SkeletonRace` (0B7998, 11) are bare
  skeletons on `SkeletonS.nif`. They get the five skeleton limbs of `Zenderal - Lost Ones Dismembering.esp`
  (0x800-0x804, meshes from 03-build-skeleton-limbs.py) on both sexes. Each limb reuses the pack's MALE
  draugr base-data and actor-addon templates: the meshes are built inside the male draugr limb nifs, so
  their RefNode, slot and Translation fit. The draugr body-cap ARMAs those templates equip are
  race-locked to DraugrRace (+ LostOneTemplateRace, 02-build-records.py), so on a skeleton they render
  nothing, which is what a bare skeleton needs.

DF parses every TEMPLATES file, then every LIMBS file, then every DATA file, so these files may
reference the pack's templates and limb IDs.

Usage:  python 01-build-lost-ones-data.py [<mods dir>]     (default E:/Zenderal/mods)
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, '..', 'SKSE', 'DismemberingFramework')
PACK = 'DF - Official Creature Asset Pack'
PACK_DIR = os.path.join('SKSE', 'DismemberingFramework')
PLUGIN = 'Zenderal - Lost Ones Dismembering.esp'
DRAUGR_RACES = ['LostOneTemplateRace']
SKELETON_RACES = ['mihailancientskeletonrace', 'SkeletonRace']
# Enderal's own wolf races (FS WolfRaceLarge/WolfRaceSmall, WolfHoheRace) share WolfRace's skeleton and
# skin; most early wolves (_10E_Wolf, the Coastprawlers) are on them, and DF only knows WolfRace.
WOLF_RACES = ['WolfRaceLarge', 'WolfRaceSmall', 'WolfHoheRace']
# Minotaur limbs per NPC skin come from 04-build-minotaur-limbs.py; a skin it never saw falls back to:
MINOTAUR_PLAN = os.path.join(HERE, 'minotaur-limbs.json')
SPIDER_PLAN = os.path.join(HERE, 'spider-limbs.json')        # 05-build-spider-limbs.py
# Spiders are SHELVED (2026-10-19): every leg cut made DF rebuild the corpse's 3D and Spider SE's 25.8 MB
# body blinked out for ~8 s (see arch-docs/patches/LostOnesDismembering.md). 05-build-spider-limbs.py and
# limbmesh's hull fitting are kept; set True to ship the spider legs again.
SPIDERS = False
MINOTAUR_FALLBACK = {'MinotaurRace': '00A818:1Minotaurs.esp',          # ArmorMinotaurCuirass1
                     'FeralMinotaurRace': '00A811:1Minotaurs.esp'}     # SkinFeralMinotaur
# limb ID -> (DATA node, pack template suffix, FormID in PLUGIN); must match 02-build-records.py
SKELETON_LIMBS = {
    'Zenderal - Skeleton - L Calf': ('NPC L Calf [LClf]', 'L Calf', 0x800),
    'Zenderal - Skeleton - R Calf': ('NPC R Calf [RClf]', 'R Calf', 0x801),
    'Zenderal - Skeleton - L Forearm': ('NPC L Forearm [LLar]', 'L Forearm', 0x802),
    'Zenderal - Skeleton - R Forearm': ('NPC R Forearm [RLar]', 'R Forearm', 0x803),
    'Zenderal - Skeleton - Head': ('NPC Neck [Neck]', 'Head', 0x804),
}


def load(mods, name):
    with open(os.path.join(mods, PACK, PACK_DIR, name), encoding='utf-8') as fh:
        return json.load(fh)


def write(name, data):
    path = os.path.join(OUT_DIR, name)
    with open(path, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(data, fh, indent=2)
        fh.write('\n')
    return os.path.normpath(path)


def main():
    mods = sys.argv[1] if len(sys.argv) > 1 else 'E:/Zenderal/mods'
    any_skin = load(mods, 'OfficialCreaturePack_Draugr_DATA.json')['DraugrRace']['ANY']
    assert set(any_skin) == {'Male', 'Female'}, any_skin.keys()
    for sex in ('Male', 'Female'):        # forearms, calves and the neck/head on both sexes
        assert len(any_skin[sex]) == 5, (sex, sorted(any_skin[sex]))
    base = load(mods, 'OfficialCreaturePack_Draugr_BaseData_TEMPLATES.json')
    with open(os.path.join(mods, 'DF - Official Humanoid Asset Pack', PACK_DIR,
                           'OfficialHumanoidPack_BaseData_TEMPLATES.json'), encoding='utf-8') as fh:
        humanoid_base = json.load(fh)
    addons = load(mods, 'OfficialCreaturePack_Draugr_ActorAddonsData_TEMPLATES.json')
    draugr_nodes = set(any_skin['Male'])

    limbs = {}
    skeleton_nodes = {}
    for limb_id, (node, part, fid) in SKELETON_LIMBS.items():
        b = f'Draugr - Male - Base data - {part}'
        a = f'Draugr - Male - Actor addons data - {part}'
        assert b in base and a in addons, (b, a)
        assert node in draugr_nodes, node
        limbs[limb_id] = {'Templates': ['DF - Base data', b, a], 'LimbFormID': f'{PLUGIN}:0x{fid:X}'}
        skeleton_nodes[node] = [{'IDLimb': limb_id}]
    assert set(skeleton_nodes) == draugr_nodes, sorted(draugr_nodes ^ set(skeleton_nodes))

    wolf = load(mods, 'OfficialCreaturePack_Wolf_DATA.json')
    assert list(wolf) == ['WolfRace'], list(wolf)
    assert 'ANY' in wolf['WolfRace'], list(wolf['WolfRace'])

    data = {
        '|'.join(DRAUGR_RACES): {'ANY': any_skin},
        '|'.join(SKELETON_RACES): {'ANY': {'Male': skeleton_nodes, 'Female': skeleton_nodes}},
        '|'.join(WOLF_RACES): wolf['WolfRace'],
    }

    # Minotaurs: one limb set per NPC skin, from 04-build-minotaur-limbs.py's plan
    plan = json.load(open(MINOTAUR_PLAN, encoding='utf-8'))
    per_skin = {}
    for e in plan:
        limb_id = f'Zenderal - Minotaur - {e["limb"]} - {e["fid"][-3:]}'
        b, a = e['base_template'], e['addon_template']
        assert b in base or b in humanoid_base, b
        limbs[limb_id] = {'Templates': ['DF - Base data', b, a], 'LimbFormID': f'{PLUGIN}:0x{int(e["fid"], 16):X}'}
        for s in e['skins']:
            per_skin.setdefault((s['race'], s['skin']), {})[e['node']] = [{'IDLimb': limb_id}]
    for (race, skin), nodes in sorted(per_skin.items()):
        fid, plugin = skin.split(':', 1)
        entry = data.setdefault(race, {})
        entry[f'{plugin}:0x{int(fid, 16):X}'] = {'Male': nodes, 'Female': nodes}
        if skin == MINOTAUR_FALLBACK.get(race):
            entry['ANY'] = {'Male': nodes, 'Female': nodes}
    for race in MINOTAUR_FALLBACK:
        assert 'ANY' in data.get(race, {}), race

    templates = {}
    if SPIDERS:
        # Spiders: eight legs on every frostbite spider race, own base-data templates (05-build-spider-limbs.py)
        spider = json.load(open(SPIDER_PLAN, encoding='utf-8'))
        spider_nodes, spider_races = {}, set()
        for e in spider:
            limb_id = f'Zenderal - Spider - {e["limb"]}'
            templates[e['base_template']] = e['base_data']
            templates[e['addon_template']] = e['addon_data']    # blood art only, no body-cap armor (see 05)
            limbs[limb_id] = {'Templates': ['DF - Base data', e['base_template'], e['addon_template']],
                              'LimbFormID': f'{PLUGIN}:0x{int(e["fid"], 16):X}'}
            spider_nodes[e['node']] = [{'IDLimb': limb_id}]
            spider_races |= {s['race'] for s in e['skins']}
            assert all(s['skin'] == 'ANY' for s in e['skins']), e['limb']
        assert len(spider_nodes) == 8, sorted(spider_nodes)
        data['|'.join(sorted(spider_races))] = {'ANY': {'Male': spider_nodes, 'Female': spider_nodes}}

    os.makedirs(OUT_DIR, exist_ok=True)
    tpl_path = os.path.join(OUT_DIR, 'Zenderal_LostOnes_TEMPLATES.json')
    if templates:
        print(write('Zenderal_LostOnes_TEMPLATES.json', templates), f'({len(templates)} templates)')
    elif os.path.exists(tpl_path):
        os.remove(tpl_path)                                  # only the spider legs used own templates
    print(write('Zenderal_LostOnes_LIMBS.json', limbs), f'({len(limbs)} limbs)')
    print(write('Zenderal_LostOnes_DATA.json', data))
    n = sum(len(v) for sex in any_skin.values() for v in sex.values())
    print(f'  {"|".join(DRAUGR_RACES)}: pack draugr limbs ({n} entries)')
    print(f'  {"|".join(SKELETON_RACES)}: {len(skeleton_nodes)} skeleton limbs per sex')
    print(f'  {"|".join(WOLF_RACES)}: pack WolfRace entries for skins {list(wolf["WolfRace"])}')


if __name__ == '__main__':
    main()
