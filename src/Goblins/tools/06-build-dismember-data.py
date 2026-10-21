"""Build `Zenderal - Goblins Dismembering.esp` (records) and its Dismembering Framework JSON from the
plans of 04-build-dismember-limbs.py and 05-build-dismember-caps.py. Never hand-edit what this writes.

A separate plugin so `Zenderal - Goblins` stays usable without DF, and because the cap ARMAs must name
ZEN_GoblinRace: `Zenderal - Lost Ones Dismembering.esp` loads before `Zenderal - Goblins.esp` (it must
precede the Fluffworks DF patch), so it cannot master it. This one loads right after `Zenderal - Goblins.esp`.

Records (sources: reference/mods/DFOfficialCreaturePack, serialize `DF - Official Creature Pack.esp`
with the spriggit-decompile-reference skill):
  * one MiscItem per limb mesh (04's plan), DF's naked male Falmer limb item of the same limb copied
    (DFDefaultLimbRefScript + its globals, DF limb keyword) with a new EditorID and model;
  * per cap variant and limb (05's plan) DF's naked male Falmer body-cap ARMO (00083A-00083E) and ARMA
    (00083F-000843) copied as new records: goblin-skinned model, race ZEN_GoblinRace, ARMO -> new ARMA.
JSON (SKSE/DismemberingFramework/Zenderal_Goblins_*.json; DF parses every TEMPLATES, then LIMBS, then
DATA file, so these may name the pack's Falmer base-data templates):
  * TEMPLATES: one actor-addon template per cap (our ARMO + DF's Falmer blood art);
  * LIMBS: one limb per MiscItem, templates [DF - Base data, Falmer male base data, ours];
  * Mihail's goblins (04b): MiscItems from DF's naked male draugr limb items, LIMBS with DF's humanoid/draugr
    templates, DATA `ZEN_Mihail_mihailgoblinrace` -> each skin -> both sexes (first skin also `ANY`).
  * DATA: `ZEN_GoblinRace` -> each goblin skin -> both sexes -> its five limbs; the race skin
    (ZEN_SkinGoblinPlain) is also `ANY`.

Usage:  python 06-build-dismember-data.py [<mods dir>]      (default E:/Zenderal/mods)
"""
import json
import os
import re
import shutil
import sys

MODS = sys.argv[1] if len(sys.argv) > 1 else 'E:/Zenderal/mods'
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
REF = os.path.join(REPO, 'reference', 'mods', 'DFOfficialCreaturePack')
ESP = os.path.join(HERE, '..', 'GoblinsDismemberingESP')
JSON_DIR = os.path.join(HERE, '..', 'SKSE', 'DismemberingFramework')
MOD_KEY = 'Zenderal - Goblins Dismembering.esp'
DF_KEY = 'DF - Official Creature Pack.esp'
GOBLINS_KEY = 'Zenderal - Goblins.esp'
RACE = f'000800:{GOBLINS_KEY}'
RACE_EDID = 'ZEN_GoblinRace'
FALLBACK_SKIN = f'000805:{GOBLINS_KEY}'          # ZEN_SkinGoblinPlain, the race's own skin
PACK_DIR = os.path.join(MODS, 'DF - Official Creature Asset Pack', 'SKSE', 'DismemberingFramework')
LIMB_PLAN = os.path.join(HERE, 'dismember-limbs.json')
CAP_PLAN = os.path.join(HERE, 'dismember-caps.json')
MIHAIL_PLAN = os.path.join(HERE, 'mihail-dismember-limbs.json')     # 04b-build-mihail-limbs.py
MIHAIL_RACE_EDID = 'ZEN_Mihail_mihailgoblinrace'
MIHAIL_TEMPLATE_FILES = [
    os.path.join(MODS, 'DF - Official Humanoid Asset Pack', 'SKSE', 'DismemberingFramework', f'OfficialHumanoidPack_{n}_TEMPLATES.json')
    for n in ('BaseData', 'ActorAddonsData')] + [
    os.path.join(MODS, 'DF - Official Creature Asset Pack', 'SKSE', 'DismemberingFramework', f'OfficialCreaturePack_Draugr_{n}_TEMPLATES.json')
    for n in ('BaseData', 'ActorAddonsData')]
# DF naked male draugr limb item each Mihail goblin limb item is copied from (only the script + keyword matter)
DRAUGR_LIMB_ITEM = {'Calf_L': '000810', 'Calf_R': '000811', 'Forearm_L': '000812', 'Forearm_R': '000813',
                    'Head': '000814'}
# DF naked male Falmer limb item each goblin limb item is copied from
FALMER_LIMB_ITEM = {'Calf_L': '000844', 'Calf_R': '000845', 'Forearm_L': '000846', 'Forearm_R': '000847',
                    'Head': '000848'}
MASTERS = ['Skyrim.esm', 'Update.esm', 'Enderal - Forgotten Stories.esm', 'Dismembering Framework.esm',
           DF_KEY, GOBLINS_KEY]


def ref_file(folder, fid):
    hits = [f for f in os.listdir(os.path.join(REF, folder)) if f.endswith(f' - {fid}_{DF_KEY}.yaml')]
    assert len(hits) == 1, (folder, fid, hits)
    return os.path.join(REF, folder, hits[0])


def sub_once(pattern, repl, text, what):
    out, n = re.subn(pattern, lambda _: repl, text, flags=re.M)
    assert n == 1, (what, pattern, n)
    return out


def copy_record(folder, src_fid, fid, edid, subs=()):
    """DF record `src_fid` copied verbatim as `fid:MOD_KEY` with EditorID `edid`; `subs` = (pattern, repl)."""
    src = open(ref_file(folder, src_fid), encoding='utf-8').read()
    out = sub_once(r'^FormKey: \S+:' + re.escape(DF_KEY) + r'(?=\r?$)', f'FormKey: {fid}:{MOD_KEY}', src, 'formkey')
    out = sub_once(r'^EditorID: \S+(?=\r?$)', f'EditorID: {edid}', out, 'edid')
    for pattern, repl in subs:
        out = sub_once(pattern, repl, out, (folder, src_fid, pattern))
    os.makedirs(os.path.join(ESP, folder), exist_ok=True)
    with open(os.path.join(ESP, folder, f'{edid} - {fid}_{MOD_KEY}.yaml'), 'w', encoding='utf-8', newline='') as fh:
        fh.write(out)
    return src


def write_json(name, data):
    path = os.path.join(JSON_DIR, name)
    with open(path, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(data, fh, indent=2)
        fh.write('\n')
    return os.path.normpath(path)


def main():
    for folder in ('MiscItems', 'ArmorAddons', 'Armors'):
        shutil.rmtree(os.path.join(ESP, folder), ignore_errors=True)
    os.makedirs(JSON_DIR, exist_ok=True)
    limbs_plan = json.load(open(LIMB_PLAN, encoding='utf-8'))
    caps = json.load(open(CAP_PLAN, encoding='utf-8'))
    base_tpl = json.load(open(os.path.join(PACK_DIR, 'OfficialCreaturePack_Falmer_BaseData_TEMPLATES.json'),
                              encoding='utf-8'))
    race_line = r'^Race: 0131F4:Skyrim\.esm(?=\r?$)'

    # --- records ----------------------------------------------------------------------------------
    for e in limbs_plan:
        src = copy_record('MiscItems', FALMER_LIMB_ITEM[e['limb']], e['fid'], f'ZEN_Goblin_{e["limb"]}_{e["fid"][-3:]}_Limb',
                          [(r'^  File: .*(?=\r?$)', '  File: ' + e['mesh'])])
        assert 'DFDefaultLimbRefScript' in src and f'Falmer_Male_Naked_{e["limb"]}_Limb' in src, e['limb']
    for c in caps:
        copy_record('ArmorAddons', c['df_arma'], c['arma'], c['edid'] + '_AA',
                    [(r'^    File: .*(?=\r?$)', '    File: ' + c['mesh']), (race_line, f'Race: {RACE}')])
        copy_record('Armors', c['df_armo'], c['armo'], c['edid'] + '_AR',
                    [(r'^- ' + c['df_arma'] + ':' + re.escape(DF_KEY) + r'(?=\r?$)', f'- {c["arma"]}:{MOD_KEY}'),
                     (race_line, f'Race: {RACE}')])
    mihail = json.load(open(MIHAIL_PLAN, encoding='utf-8'))
    for e in mihail:                       # Mihail's goblins (04b): DF's naked draugr limb item, as the minotaurs
        src = copy_record('MiscItems', DRAUGR_LIMB_ITEM[e['limb']], e['fid'], f'ZEN_MihailGoblin_{e["limb"]}_{e["fid"][-3:]}_Limb',
                          [(r'^  File: .*(?=\r?$)', '  File: ' + e['mesh'])])
        assert 'DFDefaultLimbRefScript' in src and f'Draugr_Male_Naked_{e["limb"]}_Limb' in src, e['limb']
    fids = [int(e['fid'], 16) for e in limbs_plan + mihail] + [int(c[k], 16) for c in caps for k in ('armo', 'arma')]
    assert len(set(fids)) == len(fids) and min(fids) >= 0x800 and max(fids) <= 0xFFF, 'FormID clash/range'

    lines = ['SpriggitSource:', '  PackageName: Spriggit.Yaml.Skyrim', '  Version: 0.40', f'ModKey: {MOD_KEY}',
             'GameRelease: EnderalSE', 'ModHeader:', '  Flags:', '  - Small', '  Stats:', '    Version: 1.7',
             '  Author: Zenderal', '  Description: Dismembering Framework support for Zenderal - Goblins.',
             '  MasterReferences:']
    for m in MASTERS:
        lines += [f'  - Master: {m}', '    FileSize: 0']
    lines += ['  INTV: 1']
    with open(os.path.join(ESP, 'RecordData.yaml'), 'w', encoding='utf-8', newline='') as fh:
        fh.write('\r\n'.join(lines) + '\r\n')
    with open(os.path.join(ESP, 'spriggit-meta.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump({'PackageName': 'Spriggit.Yaml.Skyrim', 'Version': '0.40.0', 'Release': 'EnderalSE',
                   'ModKey': MOD_KEY}, fh, indent=2)
        fh.write('\n')

    # --- DF JSON ----------------------------------------------------------------------------------
    templates = {c['template']: {'ActorArmorAddon': f'{MOD_KEY}:0x{int(c["armo"], 16):X}', 'ActorArtObject': c['art']}
                 for c in caps}
    limbs, per_skin = {}, {}
    for e in limbs_plan:
        limb_id = f'Zenderal - Goblin - {e["limb"]} - {e["fid"][-3:]}'
        assert e['base_template'] in base_tpl and e['addon_template'] in templates, (e['base_template'], e['addon_template'])
        limbs[limb_id] = {'Templates': ['DF - Base data', e['base_template'], e['addon_template']],
                          'LimbFormID': f'{MOD_KEY}:0x{int(e["fid"], 16):X}'}
        for s in e['skins']:
            assert s['race'] == RACE_EDID, s
            per_skin.setdefault(s['skin'], {})[e['node']] = [{'IDLimb': limb_id}]
    race = {}
    for skin, nodes in sorted(per_skin.items()):
        assert len(nodes) == 5, (skin, sorted(nodes))
        fid, plugin = skin.split(':', 1)
        race[f'{plugin}:0x{int(fid, 16):X}'] = {'Male': nodes, 'Female': nodes}
        if skin == FALLBACK_SKIN:
            race['ANY'] = {'Male': nodes, 'Female': nodes}
    assert 'ANY' in race, 'race skin has no limbs'

    # Mihail's goblins: humanoid base-data + actor-addon templates (draugr for the head), per skin; the
    # first skin (Goblin/Archer, the commonest) is also ANY
    known = {}
    for path in MIHAIL_TEMPLATE_FILES:
        known.update(json.load(open(path, encoding='utf-8')))
    m_skin = {}
    for e in mihail:
        limb_id = f'Zenderal - Mihail Goblin - {e["limb"]} - {e["fid"][-3:]}'
        assert e['base_template'] in known and e['addon_template'] in known, (e['base_template'], e['addon_template'])
        limbs[limb_id] = {'Templates': ['DF - Base data', e['base_template'], e['addon_template']],
                          'LimbFormID': f'{MOD_KEY}:0x{int(e["fid"], 16):X}'}
        for s in e['skins']:
            assert s['race'] == MIHAIL_RACE_EDID, s
            m_skin.setdefault(s['skin'], {})[e['node']] = [{'IDLimb': limb_id}]
    m_race = {}
    for skin, nodes in sorted(m_skin.items()):
        assert len(nodes) == 5, (skin, sorted(nodes))
        fid, plugin = skin.split(':', 1)
        m_race[f'{plugin}:0x{int(fid, 16):X}'] = {'Male': nodes, 'Female': nodes}
    first = sorted(m_skin)[0]
    m_race['ANY'] = {'Male': m_skin[first], 'Female': m_skin[first]}

    print(write_json('Zenderal_Goblins_TEMPLATES.json', templates), f'({len(templates)} templates)')
    print(write_json('Zenderal_Goblins_LIMBS.json', limbs), f'({len(limbs)} limbs)')
    print(write_json('Zenderal_Goblins_DATA.json', {RACE_EDID: race, MIHAIL_RACE_EDID: m_race}),
          f'({len(per_skin)} + {len(m_skin)} skins, each race + ANY)')
    print(f'{len(limbs_plan)} + {len(mihail)} limb items + {len(caps)} cap ARMO/ARMA pairs -> {os.path.normpath(ESP)}')


if __name__ == '__main__':
    main()
