"""Build `Zenderal - Bear Dismembering.esp` (records) and its Dismembering Framework JSON from 01's plan.
Never hand-edit what this writes.

Records (source: reference/mods/DFOfficialCreaturePack, serialize `DF - Official Creature Pack.esp` with the
spriggit-decompile-reference skill):
  * 0x800-0x804: one ArtObject per limb, DF's wolf stump blood art of that limb copied with the bear blood-fx
    model 01 wrote (its attach node renamed to the bear bone);
  * 0x805-: one MiscItem per limb mesh, DF's wolf Default limb item of that limb copied (DFDefaultLimbRefScript +
    its globals, DF limb keyword) with a new EditorID and model.

JSON (SKSE/DismemberingFramework/), all our own files (no other DF file defines a bear race):
  * Zenderal_Bears_TEMPLATES.json: per limb a base-data template (bear RefNode; DF's wolf flying-limb blood art
    0x8A4; the wolf Translation 01 kept; an explicit BipedSlot, see below) and an actor-addon template with only
    `ActorArtObject` (our bear stump blood).
      - No `ActorArmorAddon` (stump cap): DF's wolf caps are race-locked to wolves and render nothing on a bear,
        and equipping one is the suspect in the open 0FDDB2D crash (LostOnesDismembering, stump caps off).
      - BipedSlot: DF hides that body slot on a cut. A missing one defaults to slot 30, and every bear body ARMA
        is slot 30 (Head) only, so the whole bear would vanish (the spider lesson). 37 (legs) / 31 (head) are
        empty on a bear.
  * Zenderal_Bears_LIMBS.json: one limb per MiscItem, templates [DF - Base data, base data, actor addons].
  * Zenderal_Bears_DATA.json: each bear race -> its skin -> Male|Female -> node -> limb. No `ANY`, so FS's
    summonable panda (BearBlackRace with its own skin 02E3AE) gets nothing rather than cave-bear limbs.

Usage:  python 02-build-bear-data.py
"""
import json
import os
import re
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
REF = os.path.join(REPO, 'reference', 'mods', 'DFOfficialCreaturePack')
ESP = os.path.join(HERE, '..', 'BearDismemberingESP')
JSON_DIR = os.path.join(HERE, '..', 'SKSE', 'DismemberingFramework')
MOD_KEY = 'Zenderal - Bear Dismembering.esp'
DF_KEY = 'DF - Official Creature Pack.esp'
PLAN = os.path.join(HERE, 'bear-limbs.json')
MASTERS = ['Skyrim.esm', 'Update.esm', 'Enderal - Forgotten Stories.esm', 'Dismembering Framework.esm', DF_KEY]
# limb -> (DF wolf Default limb MiscItem, DF wolf stump blood ArtObject, display name in DF's naming, BipedSlot)
WOLF = {
    'Front_L_Leg': ('000878', '00087E', 'Front L Leg', 37),
    'Front_R_Leg': ('000879', '00087F', 'Front R Leg', 37),
    'Back_L_Leg': ('000876', '00087C', 'Back L Leg', 37),
    'Back_R_Leg': ('000877', '00087D', 'Back R Leg', 37),
    'Head': ('000867', '00087A', 'Head', 31),
}
LIMB_ART = f'{DF_KEY}:0x8A4'          # DF_Wolf_Default_ArtFX: the flying limb's own blood, attached to its BloodFX node


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


def write_json(name, data):
    path = os.path.join(JSON_DIR, name)
    with open(path, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(data, fh, indent=2)
        fh.write('\n')
    return os.path.normpath(path)


def main():
    for folder in ('MiscItems', 'ArtObjects'):
        shutil.rmtree(os.path.join(ESP, folder), ignore_errors=True)
    os.makedirs(JSON_DIR, exist_ok=True)
    plan = json.load(open(PLAN, encoding='utf-8'))

    # --- records ----------------------------------------------------------------------------------
    art_of = {}
    for a in plan['arts']:
        src = copy_record('ArtObjects', WOLF[a['limb']][1], a['fid'], f'ZEN_Bear_{a["limb"]}_ArtFX',
                          [(r'^  File: .*(?=\r?$)', '  File: ' + a['mesh'])])
        assert 'MagicCasting' in src and 'BloodFX_' in src, a
        art_of[a['limb']] = a['fid']
    for e in plan['limbs']:
        src = copy_record('MiscItems', WOLF[e['limb']][0], e['fid'], f'ZEN_Bear_{e["limb"]}_{e["fid"][-3:]}_Limb',
                          [(r'^  File: .*(?=\r?$)', '  File: ' + e['mesh'])])
        assert 'DFDefaultLimbRefScript' in src and '000802:Dismembering Framework.esm' in src, e['limb']
    fids = [int(x['fid'], 16) for x in plan['arts'] + plan['limbs']]
    assert len(set(fids)) == len(fids) and min(fids) >= 0x800 and max(fids) <= 0xFFF, 'FormID clash/range'

    lines = ['SpriggitSource:', '  PackageName: Spriggit.Yaml.Skyrim', '  Version: 0.40', f'ModKey: {MOD_KEY}',
             'GameRelease: EnderalSE', 'ModHeader:', '  Flags:', '  - Small', '  Stats:', '    Version: 1.7',
             '  Author: Zenderal',
             '  Description: Dismembering Framework limbs cut from the Bears of the North bodies.',
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
    templates, limbs, races = {}, {}, {}
    for e in plan['limbs']:
        _, _, name, slot = WOLF[e['limb']]
        base_t, addon_t = f'Zenderal - Bear - Base data - {name}', f'Zenderal - Bear - Actor addons data - {name}'
        templates[base_t] = {'RefNode': e['ref_node'], 'BipedSlot': slot, 'LimbArtObject': LIMB_ART,
                             'Translation': e['translation']}
        templates[addon_t] = {'ActorArtObject': f'{MOD_KEY}:0x{int(art_of[e["limb"]], 16):X}'}
        limb_id = f'Zenderal - Bear - {name} - {e["fid"][-3:]}'
        limbs[limb_id] = {'Templates': ['DF - Base data', base_t, addon_t],
                          'LimbFormID': f'{MOD_KEY}:0x{int(e["fid"], 16):X}'}
        for s in e['skins']:
            fid, plugin = s['skin'].split(':', 1)
            nodes = races.setdefault(s['race'], {}).setdefault(f'{plugin}:0x{int(fid, 16):X}', {'Male|Female': {}})
            nodes['Male|Female'][e['node']] = [{'IDLimb': limb_id}]
    for race, skins in races.items():
        for skin, sexes in skins.items():
            assert len(sexes['Male|Female']) == 5, (race, skin, sorted(sexes['Male|Female']))
    assert sorted(races) == ['BearBlackRace', 'BearBrownRace', 'BearBrownRaceHoher', 'BearSnowRace'], sorted(races)

    print(write_json('Zenderal_Bears_TEMPLATES.json', templates), f'({len(templates)} templates)')
    print(write_json('Zenderal_Bears_LIMBS.json', limbs), f'({len(limbs)} limbs)')
    print(write_json('Zenderal_Bears_DATA.json', races), f'({len(races)} races)')
    print(f'{len(plan["arts"])} art objects + {len(plan["limbs"])} limb items -> {os.path.normpath(ESP)}')


if __name__ == '__main__':
    main()
