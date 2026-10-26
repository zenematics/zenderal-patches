"""Build `Zenderal - Arp Dismembering.esp` (records) and its Dismembering Framework JSON from 01's plan.
Never hand-edit what this writes.

Records (source: reference/mods/DFOfficialCreaturePack, serialize `DF - Official Creature Pack.esp` with the
spriggit-decompile-reference skill): one MiscItem per limb mesh, DF's naked male Falmer limb item of the same
limb copied (DFDefaultLimbRefScript + its globals, DF limb keyword) with a new EditorID and model.

JSON (SKSE/DismemberingFramework/):
  * Zenderal_Arps_LIMBS.json: one limb per MiscItem, templates [DF - Base data, DF's Falmer male base data,
    DF's Falmer male actor-addon data] (DF's stump caps);
  * OfficialCreaturePack_Falmer_DATA.json, at DF's own path: DF's file with `FalmerRace` rebuilt, each Arp
    skin -> its five limbs (both sexes), the race skin also `ANY`. DF's Dawnguard entries are kept, and the
    flesh construct (`_00E_SkinFleshconstruct 149709`, also FalmerRace, not an Arp body) keeps DF's own
    `ANY` limbs. A same-path copy, because two files defining FalmerRace would leave the result to DF's merge
    rules; the MO2 mod must outrank `DF - Official Creature Asset Pack`.

Usage:  python 02-build-arp-data.py [<mods dir>]      (default E:/Zenderal/mods)
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
ESP = os.path.join(HERE, '..', 'ArpDismemberingESP')
JSON_DIR = os.path.join(HERE, '..', 'SKSE', 'DismemberingFramework')
MOD_KEY = 'Zenderal - Arp Dismembering.esp'
DF_KEY = 'DF - Official Creature Pack.esp'
PACK_DIR = os.path.join(MODS, 'DF - Official Creature Asset Pack', 'SKSE', 'DismemberingFramework')
PLAN = os.path.join(HERE, 'arp-limbs.json')
RACE_SKIN = '016EE7:Skyrim.esm'
FLESH_CONSTRUCT = 'Skyrim.esm:0x149709'
FALMER_LIMB_ITEM = {'Calf_L': '000844', 'Calf_R': '000845', 'Forearm_L': '000846', 'Forearm_R': '000847',
                    'Head': '000848'}
MASTERS = ['Skyrim.esm', 'Update.esm', 'Enderal - Forgotten Stories.esm', 'Dismembering Framework.esm', DF_KEY]


def ref_file(folder, fid):
    hits = [f for f in os.listdir(os.path.join(REF, folder)) if f.endswith(f' - {fid}_{DF_KEY}.yaml')]
    assert len(hits) == 1, (folder, fid, hits)
    return os.path.join(REF, folder, hits[0])


def sub_once(pattern, repl, text, what):
    out, n = re.subn(pattern, lambda _: repl, text, flags=re.M)
    assert n == 1, (what, pattern, n)
    return out


def copy_record(folder, src_fid, fid, edid, subs=()):
    src = open(ref_file(folder, src_fid), encoding='utf-8').read()
    out = sub_once(r'^FormKey: \S+:' + re.escape(DF_KEY) + r'(?=\r?$)', f'FormKey: {fid}:{MOD_KEY}', src, 'formkey')
    out = sub_once(r'^EditorID: \S+(?=\r?$)', f'EditorID: {edid}', out, 'edid')
    for pattern, repl in subs:
        out = sub_once(pattern, repl, out, (folder, src_fid, pattern))
    os.makedirs(os.path.join(ESP, folder), exist_ok=True)
    with open(os.path.join(ESP, folder, f'{edid} - {fid}_{MOD_KEY}.yaml'), 'w', encoding='utf-8', newline='') as fh:
        fh.write(out)
    return src


def write_json(name, data, indent=2):
    path = os.path.join(JSON_DIR, name)
    with open(path, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(data, fh, indent=indent)
        fh.write('\n')
    return os.path.normpath(path)


def main():
    shutil.rmtree(os.path.join(ESP, 'MiscItems'), ignore_errors=True)
    os.makedirs(JSON_DIR, exist_ok=True)
    plan = json.load(open(PLAN, encoding='utf-8'))
    base_tpl = json.load(open(os.path.join(PACK_DIR, 'OfficialCreaturePack_Falmer_BaseData_TEMPLATES.json'), encoding='utf-8'))
    addon_tpl = json.load(open(os.path.join(PACK_DIR, 'OfficialCreaturePack_Falmer_ActorAddonsData_TEMPLATES.json'), encoding='utf-8'))

    # --- records ----------------------------------------------------------------------------------
    for e in plan:
        src = copy_record('MiscItems', FALMER_LIMB_ITEM[e['limb']], e['fid'], f'ZEN_Arp_{e["limb"]}_{e["fid"][-3:]}_Limb',
                          [(r'^  File: .*(?=\r?$)', '  File: ' + e['mesh'])])
        assert 'DFDefaultLimbRefScript' in src and f'Falmer_Male_Naked_{e["limb"]}_Limb' in src, e['limb']
    fids = [int(e['fid'], 16) for e in plan]
    assert len(set(fids)) == len(fids) and min(fids) >= 0x800 and max(fids) <= 0xFFF, 'FormID clash/range'

    lines = ['SpriggitSource:', '  PackageName: Spriggit.Yaml.Skyrim', '  Version: 0.40', f'ModKey: {MOD_KEY}',
             'GameRelease: EnderalSE', 'ModHeader:', '  Flags:', '  - Small', '  Stats:', '    Version: 1.7',
             '  Author: Zenderal', '  Description: Dismembering Framework limbs cut from the Enderal Arp bodies.',
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
    limbs, per_skin = {}, {}
    for e in plan:
        limb_id = f'Zenderal - Arp - {e["limb"]} - {e["fid"][-3:]}'
        assert e['base_template'] in base_tpl and e['addon_template'] in addon_tpl, e
        limbs[limb_id] = {'Templates': ['DF - Base data', e['base_template'], e['addon_template']],
                          'LimbFormID': f'{MOD_KEY}:0x{int(e["fid"], 16):X}'}
        for skin in e['skins']:
            per_skin.setdefault(skin, {})[e['node']] = [{'IDLimb': limb_id}]

    data = json.load(open(os.path.join(PACK_DIR, 'OfficialCreaturePack_Falmer_DATA.json'), encoding='utf-8'))
    df_race = data['FalmerRace']
    race = {}
    for skin, nodes in per_skin.items():
        assert len(nodes) == 5, (skin, sorted(nodes))
        fid, plugin = skin.split(':', 1)
        race[f'{plugin}:0x{int(fid, 16):X}'] = {'Male': nodes, 'Female': nodes}
    race[FLESH_CONSTRUCT] = df_race['ANY']                 # not an Arp body: DF's own limbs
    for key, value in df_race.items():
        if key.startswith('Dawnguard.esm'):
            race[key] = value
    race['ANY'] = {'Male': per_skin[RACE_SKIN], 'Female': per_skin[RACE_SKIN]}
    data['FalmerRace'] = race

    print(write_json('Zenderal_Arps_LIMBS.json', limbs), f'({len(limbs)} limbs)')
    print(write_json('OfficialCreaturePack_Falmer_DATA.json', data, indent=4), f'({len(per_skin)} Arp skins + ANY)')
    print(f'{len(plan)} limb items -> {os.path.normpath(ESP)}')


if __name__ == '__main__':
    main()
