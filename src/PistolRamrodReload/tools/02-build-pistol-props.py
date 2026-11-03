"""Build the ball and ramrod props of `Zenderal - Pistol Ramrod Reload`: their meshes and the ANIO records tools/01's
clips ask for (`AnimObjLoad.<EditorID>` / `AnimObjDraw.<EditorID>`, unloaded by `AnimObjectUnequip`).

The musket reload's props, made the same way (src/FlintlockOverhaul/tools/11, whose mesh writer this reuses), but hung
on the ramming hand's AnimObject node, whose track tools/01 animates: `AnimObjectR` for a left-hand pistol, and a copy of
each on `AnimObjectL` (BALL_EDID_L, ROD_EDID_L) for a right-hand one (the mesh's Prn string picks the node, so a prop
cannot serve both hands):
  - ball: a dark steel sphere of tools/01's BALL_RADIUS, shaded like the musket's (the vanilla steel dagger's blade);
  - ramrod, one per pistol barrel (ROD_EDID % label): a rod up +Y from its top end at 0 down to -length (tools/01's
    rod_length: as long as the barrel allows, at most ROD_MAX), with a wider ramming head at the far end, shaded like
    that pistol's barrel (its shader, one texel near the muzzle).
Textures are referenced, not copied: the Gentleman's Flintlock Armoury stays installed (the pistols need it anyway).

Records: `ZEN_PistolBall` 0x800, the rods 0x801 up in tools/01's group order; the quest 0x806; the AnimObjectL copies
`ZEN_PistolBallL` 0x807, the rods 0x808 up; the loading sounds' SNDRs 0x80D up (tools/01 SOUNDS; run tools/06 first for
their .wavs); plugin `Zenderal - Pistol Ramrod Reload.esp`, ESL, HEDR 1.7, YAML in src/PistolRamrodReload/PistolRamrodReloadESP (generated, never hand-edited), built
with the pinned Spriggit CLI into the MO2 mod.

Run order: 01 -> 02 (01 rebuilds the OAR folder only; this rebuilds the meshes and the plugin).
Usage:  python src/PistolRamrodReload/tools/02-build-pistol-props.py [<modlist root>]   (needs numpy)
"""
import glob
import importlib.util
import os
import shutil
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


PR = _load('pistol_reload', os.path.join(HERE, '01-build-pistol-reload.py'))
PROPS = _load('ramrod_props', os.path.join(ROOT, 'src', 'FlintlockOverhaul', 'tools', '11-build-ramrod-props.py'))
ADS = PR.ADS
NifFile = PROPS.NifFile

OUT = os.path.join(ROOT, 'src', 'PistolRamrodReload', 'PistolRamrodReloadESP')
MESH_DIR = 'Zenderal\\PistolRamrod'
PRN = 'AnimObjectR'            # left-hand pistol: the right hand rams
PRN_L = 'AnimObjectL'          # right-hand pistol: the left hand rams
L_BASE = 0x807                 # the AnimObjectL copies' FormIDs start here (after the quest)
ROD_RADIUS = PR.ROD_RADIUS     # tools/01 lays the stowed rod this far out
HEAD_RADIUS = 0.4              # the ramming head ...
HEAD_LENGTH = 1.2              # ... this long at the rod's far end
CRLF = '\r\n'
QUEST_ID, QUEST_EDID = 0x806, 'ZP_PistolReloadArmQuest'   # after the AnimObjectR ANIO block (0x800-0x805)
SCRIPT = 'ZP_PistolReloadArmScript'                       # hands the right arm to the clip for a reload (see its source)
PEX = os.path.join(ROOT, 'src', 'PistolRamrodReload', 'Scripts', 'compiled', SCRIPT + '.pex')
# the loading sounds' SNDRs (tools/01 SOUNDS, in order, 2026-11-02): vanilla's bow nock (WPNBowNockSD, weapon category,
# positional output) copied with one file each, the .wavs tools/06 writes
SOUND_ID = 0x80D
SOUND_TEMPLATE = os.path.join(ROOT, 'reference', 'base', 'Skyrim', 'SoundDescriptors',
                              'WPNBowNockSD - 03E7B4_Skyrim.esm.yaml')
SOUND_PATH = 'Data\\Sound\\FX\\Zenderal\\PistolReload\\%s.wav'
# "Your item has insufficient charge." (2026-11-02, curator: remove it from the pistols): the empty gun's reload is a cast
# with no charge, so the engine said it at every reload. Vanilla's GMST verbatim with its text a single space (no mod
# overrides it; an empty string may not be written at all). There is one setting for every staff, so staves stay quiet
# too.
CHARGE_GMST = os.path.join(ROOT, 'reference', 'base', 'Skyrim', 'GameSettings',
                           'sMagicCastInsufficientItemCharge - 0D4BD8_Skyrim.esm.yaml')


def yaml_record(edid, local_id, mesh):
    return CRLF.join(['FormKey: %06X:%s' % (local_id, PR.PROP_PLUGIN), 'EditorID: ' + edid, 'Model:',
                      '  File: ' + mesh, 'UnloadEvent: ' + PR.UNEQUIP, ''])


def sound_record(edid, local_id):
    """SOUND_TEMPLATE verbatim but for its FormKey, EditorID and SoundFiles (one: SOUND_PATH)."""
    if not os.path.isfile(SOUND_TEMPLATE):
        sys.exit('%s is missing: serialize Skyrim.esm into reference/base (spriggit-decompile-reference)' % SOUND_TEMPLATE)
    out, files = [], False
    for line in open(SOUND_TEMPLATE, encoding='utf-8').read().splitlines():
        if files and line.startswith('- '):
            continue
        files = False
        if line.startswith('FormKey:'):
            line = 'FormKey: %06X:%s' % (local_id, PR.PROP_PLUGIN)
        elif line.startswith('EditorID:'):
            line = 'EditorID: ' + edid
        elif line.startswith('SoundFiles:'):
            out += [line, '- ' + SOUND_PATH % edid]
            files = True
            continue
        out.append(line)
    if sum(x.startswith(('FormKey:', 'EditorID:', 'SoundFiles:')) for x in out) != 3:
        sys.exit('%s: no FormKey / EditorID / SoundFiles to replace' % SOUND_TEMPLATE)
    return CRLF.join(out + [''])


def charge_message_record():
    """CHARGE_GMST verbatim but its text: one English string, a single space."""
    if not os.path.isfile(CHARGE_GMST):
        sys.exit('%s is missing: serialize Skyrim.esm into reference/base (spriggit-decompile-reference)' % CHARGE_GMST)
    out = []
    for line in open(CHARGE_GMST, encoding='utf-8').read().splitlines():
        out.append(line)
        if line.strip() == 'Values:':
            break
    if out[-1].strip() != 'Values:' or not any(x.startswith('EditorID: sMagicCastInsufficientItemCharge') for x in out):
        sys.exit('%s: not the GMST tools/02 expects' % CHARGE_GMST)
    return CRLF.join(out + ['  - Language: English', "    String: ' '", ''])


def quest_record():
    """ZP_PistolReloadArmQuest: start-game-enabled, its player alias runs ZP_PistolReloadArmScript (the Flintlock
    Overhaul's ammo quest's shape)."""
    fk = '%06X:%s' % (QUEST_ID, PR.PROP_PLUGIN)
    return CRLF.join([
        'FormKey: ' + fk, 'EditorID: ' + QUEST_EDID, 'VirtualMachineAdapter:', "  FileName: ''", '  Aliases:',
        '  - Property:', "      Name: ''", '      Object: ' + fk, '      Alias: 0', '    Scripts:',
        '    - Name: ' + SCRIPT, '      Properties:', '      - MutagenObjectType: ScriptObjectProperty',
        '        Name: PlayerRef', '        Object: 000014:Skyrim.esm', 'Flags:', '- StartGameEnabled', '- RunOnce',
        'NextAliasID: 1', 'Aliases:', '- Name: PlayerAlias', '  Flags: []', '  ForcedReference: 000014:Skyrim.esm',
        '  VoiceTypes: Null', ''])


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else ADS.TOOLS['modlistRoot']
    mods_dir = os.path.join(root, 'mods')
    _, mods = ADS.QRS.profile_mods(root)
    out_mod = os.path.join(mods_dir, PR.DEPLOY)
    if not os.path.isdir(os.path.join(out_mod, *PR.OAR)):
        sys.exit('run tools/01 first: %s has no clips' % out_mod)
    meshes = os.path.join(out_mod, 'meshes', *MESH_DIR.split('\\'))
    if os.path.isdir(meshes):
        shutil.rmtree(meshes)
    records = []

    ball_path = os.path.join(os.environ.get('TEMP', '.'), '_pistol_ball_source.nif')
    for bsa_path in sorted(glob.glob(os.path.join(root, 'Stock Game', 'Data', '*.bsa'))):
        data, listing = ADS._bsa.listing(bsa_path)
        if PROPS.BALL_SOURCE[0] in listing:
            with open(ball_path, 'wb') as fh:
                fh.write(ADS._bsa.read(data, listing[PROPS.BALL_SOURCE[0]]))
            break
    else:
        sys.exit('%s is in no archive under Stock Game/Data' % PROPS.BALL_SOURCE[0])
    ball_nif = NifFile(ball_path)
    ball_src = [s for s in ball_nif.shapes if s.name == PROPS.BALL_SOURCE[1]]
    if len(ball_src) != 1:
        sys.exit('%s has no shape %s' % (PROPS.BALL_SOURCE[0], PROPS.BALL_SOURCE[1]))
    v, n, t = PROPS.sphere(PR.BALL_RADIUS, PROPS.SEGMENTS, 8)
    for edid, local_id, prn, stem in ((PR.BALL_EDID, 0x800, PRN, 'ZenPistolBall'),
                                      (PR.BALL_EDID_L, L_BASE, PRN_L, 'ZenPistolBallL')):
        PROPS.write_prop(os.path.join(meshes, stem + '.nif'), stem, v, n, t, np.array(PROPS.BALL_UV), ball_nif,
                         ball_src[0], PROPS.BALL_CUBEMAP, prn=prn)
        records.append((edid, local_id, MESH_DIR + '\\' + stem + '.nif'))
    print('ball: radius %.2f, %d triangles, shaded like %s with %s'
          % (PR.BALL_RADIUS, len(t), PROPS.BALL_SOURCE[1], PROPS.BALL_CUBEMAP))

    for i, (label, path, weapons, (c, axis, radius), _) in enumerate(PR.pistol_groups(mods_dir, mods)):
        nif = NifFile(path)
        src, uv = PROPS.barrel_shape(nif)
        lengths = []
        # the right hand's pistol shows at PR.RIGHT_GUN_SCALE (Loop's right-hand set; 1.0 since mirror_hkx moves scales)
        for edid, local_id, prn, stem, scale in (
                (PR.ROD_EDID % label, 0x801 + i, PRN, 'ZenPistolRod_' + label, 1.0),
                (PR.ROD_EDID_L % label, L_BASE + 1 + i, PRN_L, 'ZenPistolRodL_' + label, PR.RIGHT_GUN_SCALE)):
            length = PR.rod_length(c, scale)
            v, n, t = PROPS.lathe([(0.0, ROD_RADIUS), (-(length - HEAD_LENGTH - 0.3), ROD_RADIUS),
                                   (-(length - HEAD_LENGTH), HEAD_RADIUS), (-length, HEAD_RADIUS)], PROPS.SEGMENTS)
            rel = '%s\\%s.nif' % (MESH_DIR, stem)
            PROPS.write_prop(os.path.join(out_mod, 'meshes', *rel.split('\\')), stem, v, n, t, uv, nif, src, prn=prn)
            records.append((edid, local_id, rel))
            lengths.append(length)
        print('%-20s rods %.1f / %.1f units (left / right hand), shaded like %s (uv %.3f, %.3f): %s'
              % (label, lengths[0], lengths[1], src.name, uv[0], uv[1], ', '.join('%s %s' % w for w in weapons)))

    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, 'AnimatedObjects'))
    with open(os.path.join(OUT, 'RecordData.yaml'), 'w', encoding='utf-8', newline='') as fh:
        fh.write(CRLF.join([
            'SpriggitSource:', '  PackageName: Spriggit.Yaml.Skyrim', '  Version: 0.40', 'ModKey: ' + PR.PROP_PLUGIN,
            'GameRelease: EnderalSE', 'ModHeader:', '  Flags:', '  - Small', '  Stats:', '    Version: 1.7',
            '  Author: Zenderal',
            '  Description: Ball and ramrod props for the flintlock pistols\' ramrod reload (Zenderal).',
            '  MasterReferences:', '  - Master: Skyrim.esm', '    FileSize: 0', '  - Master: Update.esm',
            '    FileSize: 0', '  - Master: Enderal - Forgotten Stories.esm', '    FileSize: 0', '  INTV: 1', '']))
    with open(os.path.join(OUT, 'spriggit-meta.json'), 'w', encoding='utf-8', newline='') as fh:
        fh.write('{' + CRLF + '  "PackageName": "Spriggit.Yaml.Skyrim",' + CRLF + '  "Version": "0.40.0",' + CRLF +
                 '  "Release": "EnderalSE",' + CRLF + '  "ModKey": "' + PR.PROP_PLUGIN + '"' + CRLF + '}')
    for edid, local_id, mesh in records:
        with open(os.path.join(OUT, 'AnimatedObjects', '%s - %06X_%s.yaml' % (edid, local_id, PR.PROP_PLUGIN)),
                  'w', encoding='utf-8', newline='') as fh:
            fh.write(yaml_record(edid, local_id, mesh))
    sounds = [(edid, SOUND_ID + i) for i, (edid, _) in enumerate(PR.SOUNDS)]
    ids = [i for _, i, _ in records] + [i for _, i in sounds]
    if QUEST_ID in ids or len(set(ids)) != len(ids) or max(ids) > 0xFFF:
        sys.exit('ANIO / SNDR FormIDs collide with each other or the quest\'s %03X: %s'
                 % (QUEST_ID, sorted('%03X' % i for i in ids)))
    os.makedirs(os.path.join(OUT, 'GameSettings'))
    with open(os.path.join(OUT, 'GameSettings', 'sMagicCastInsufficientItemCharge - 0D4BD8_Skyrim.esm.yaml'), 'w',
              encoding='utf-8', newline='') as fh:
        fh.write(charge_message_record())
    os.makedirs(os.path.join(OUT, 'SoundDescriptors'))
    for edid, local_id in sounds:
        wav = os.path.join(out_mod, *(SOUND_PATH % edid).split('\\')[1:])
        if not os.path.isfile(wav):
            sys.exit('%s is missing: run tools/06 with the loading sounds' % wav)
        with open(os.path.join(OUT, 'SoundDescriptors', '%s - %06X_%s.yaml' % (edid, local_id, PR.PROP_PLUGIN)), 'w',
                  encoding='utf-8', newline='') as fh:
            fh.write(sound_record(edid, local_id))
    os.makedirs(os.path.join(OUT, 'Quests'))
    with open(os.path.join(OUT, 'Quests', '%s - %06X_%s.yaml' % (QUEST_EDID, QUEST_ID, PR.PROP_PLUGIN)), 'w',
              encoding='utf-8', newline='') as fh:
        fh.write(quest_record())
    if not os.path.isfile(PEX):
        sys.exit('%s is not compiled (Scripts/source -> Scripts/compiled, papyrus-compile)' % PEX)
    os.makedirs(os.path.join(out_mod, 'Scripts'), exist_ok=True)
    shutil.copyfile(PEX, os.path.join(out_mod, 'Scripts', SCRIPT + '.pex'))
    esp = os.path.join(out_mod, PR.PROP_PLUGIN)
    run = subprocess.run([ADS.TOOLS['spriggitCli'], 'deserialize', '--InputPath', OUT, '--OutputPath', esp],
                         capture_output=True, text=True)
    if run.returncode != 0 or not os.path.isfile(esp):
        sys.exit('Spriggit deserialize failed:\n%s\n%s' % (run.stdout, run.stderr))
    data = open(esp, 'rb').read()
    found = [e for e, _, _ in records if e.encode() + b'\0' in data]
    if len(found) != len(records) or data.count(b'ANIO') < len(records):
        sys.exit('%s: expected %d ANIO records, found %d EditorIDs' % (esp, len(records), len(found)))
    if QUEST_EDID.encode() + b'\0' not in data or SCRIPT.encode() not in data:
        sys.exit('%s: the quest %s or its script is missing' % (esp, QUEST_EDID))
    if any(e.encode() + b'\0' not in data for e, _ in sounds) or data.count(b'SNDR') < len(sounds):
        sys.exit('%s: a loading sound\'s SNDR is missing' % esp)
    if b'sMagicCastInsufficientItemCharge\0' not in data or b'DATA\x02\x00 \x00' not in data:
        sys.exit('%s: the charge message GMST is missing or not a single space' % esp)
    # every rod the clips ask for has its record
    asked = set()
    oar_1p = ADS.ANIMS_1P + ['OpenAnimationReplacer', PR.MOD]       # tools/04's first-person set
    for clip in (glob.glob(os.path.join(out_mod, *PR.OAR, '*', PR.CLIP)) +
                 glob.glob(os.path.join(out_mod, *PR.OAR, '*', PR.CLIP_RIGHT)) +
                 glob.glob(os.path.join(out_mod, *oar_1p, '*', PR.CLIP))):
        for a in PR.anim_skyrim.load_skyrim_animation(clip).annotations:
            if a.text.startswith('AnimObjLoad.'):
                asked.add(a.text.split('.', 1)[1])
    missing = asked - {e for e, _, _ in records}
    if missing:
        sys.exit('clips ask for props with no record: %s' % sorted(missing))
    print('built %s: %d ANIO records (%s), %d meshes; clips ask for %d of them; SNDR %s'
          % (esp, len(records), ' '.join('%03X' % i for _, i, _ in sorted(records, key=lambda r: r[1])), len(records),
             len(asked), ', '.join('%s %03X' % s for s in sounds)))


if __name__ == '__main__':
    main()
