"""Build the goblin limb meshes for `Zenderal - Goblins Dismembering`, and the plan 05/06 read. Run after 01.

Goblins are their own creature since 2026-10-21: `Zenderal - Goblins` (src/Goblins) adds ZEN_GoblinRace
(a copy of FalmerRace, so the same skeleton and the bones DF's Falmer templates name) with four skins
whose meshes are the `Goblins` mod's bodies at `meshes/Zenderal/Goblins/`. Arps are Arps again and keep
DF's own Falmer limbs; nothing here touches FalmerRace any more.

Same method as 04-build-minotaur-limbs.py: DF matches race -> skin -> sex, so every goblin NPC skin
(records from src/Goblins/GoblinsESP, regenerate with its tools/01 first) gets its own limbs, cut from
exactly the meshes that skin's ARMAs render (resolved through Ultra's MO2 mod order). Each shape of each
model is cut by dominant bone (the limb bone + all its descendants in the race skeleton), moved into the
RefNode bone's local space and added (shader, nine textures, alpha) to DF's naked male FALMER limb nif of
the same limb, whose own shapes are then detached. The Falmer base-data templates (RefNode `NPC L
Forearm` etc., BipedSlot, Translation) are reused; the actor-addon templates are ours (07's goblin caps).
Limbs with identical geometry are shared between skins.

Writes the meshes into the MO2 mod (generated from the user's install, never committed) and
`dismember-limbs.json` next to this script (committed; 06 builds the DF JSON and MiscItems from it).
Shared mesh helpers: src/LostOnesDismembering/tools/limbmesh.py.

Usage:  python 04-build-dismember-limbs.py <pynifly io_scene_nifly dir> [<modlist root>]
        (modlist root defaults to E:/Zenderal; mesh paths resolve through the Ultra profile's mod order)
"""
import glob
import hashlib
import importlib.util
import json
import os
import re
import sys
import tempfile


PYN = sys.argv[1]
ROOT = sys.argv[2] if len(sys.argv) > 2 else 'E:/Zenderal'
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, PYN)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', '..', 'LostOnesDismembering', 'tools'))   # limbmesh.py
from pyn.pynifly import NifFile  # noqa: E402
from limbmesh import build_nif, cut_shape, descendants  # noqa: E402

BS = chr(92)
MODS = os.path.join(ROOT, 'mods')
PROFILE = os.path.join(ROOT, 'profiles', 'Ultra', 'modlist.txt')
# a model no enabled mod ships loose comes from the game's archives
GAME_BSAS = [os.path.join(ROOT, 'Stock Game', 'Data', b) for b in ('E - Update.bsa', 'E - Meshes.bsa',
                                                                  'Skyrim - Meshes1.bsa', 'Skyrim - Meshes0.bsa')]
TMP = tempfile.mkdtemp(prefix='zen_goblin_')
OUT_MOD = os.path.join(MODS, 'Zenderal - Goblins Dismembering')
MESH_REL = BS.join(['DismemberingFramework', 'Zenderal', 'Goblins'])
PLAN = os.path.join(HERE, 'dismember-limbs.json')
# Plugins in load order; a later one wins a record (reference/, gitignored, spriggit-decompile-reference)
REFS = [os.path.join(HERE, '..', 'GoblinsESP')]
RACE = '000800:Zenderal - Goblins.esp'
RACE_EDID = 'ZEN_GoblinRace'
FIRST_FID = 0x800      # Zenderal - Goblins Dismembering.esp: limb items first, then 05's cap pairs

FALMER_DIR = os.path.join(MODS, 'DF - Official Creature Asset Pack', 'meshes', 'dismemberingframework',
                          'officialcreaturepack', 'falmer', 'male', 'limbs', 'naked')
DF_JSON = os.path.join(MODS, 'DF - Official Creature Asset Pack', 'SKSE', 'DismemberingFramework',
                       'OfficialCreaturePack_Falmer_BaseData_TEMPLATES.json')
# limb -> (RefNode bone, DATA node, container, base-data template, actor-addon template)
LIMBS = {
    'Calf_L': ('NPC L Calf', 'NPC L Calf', 'calf_l.nif',
               'Falmer - Male - Base data - L Calf', 'Falmer - Male - Actor addons data - L Calf'),
    'Calf_R': ('NPC R Calf', 'NPC R Calf', 'calf_r.nif',
               'Falmer - Male - Base data - R Calf', 'Falmer - Male - Actor addons data - R Calf'),
    'Forearm_L': ('NPC L Forearm', 'NPC L Forearm', 'forearm_l.nif',
                  'Falmer - Male - Base data - L Forearm', 'Falmer - Male - Actor addons data - L Forearm'),
    'Forearm_R': ('NPC R Forearm', 'NPC R Forearm', 'forearm_r.nif',
                  'Falmer - Male - Base data - R Forearm', 'Falmer - Male - Actor addons data - R Forearm'),
    'Head': ('NPC Head', 'NPC Neck', 'head.nif',
             'Falmer - Male - Base data - Head', 'Falmer - Male - Actor addons data - Head'),
}
MIN_TRIS = 20          # a limb with less geometry than this is left undismemberable for that skin
# Goblin body diffuse -> stump-cap variant (05-build-dismember-caps.py builds one cap nif per variant, 06 its
# ARMO/ARMA pairs and actor-addon templates). A skin without a goblin body would keep DF's Falmer caps.
BODY = 'Goblin_body'
CAP_VARIANTS = {'goblin.dds': 'Goblin', 'goblinwitch.dds': 'GoblinWitch'}


# ---------------------------------------------------------------------------------------------------
# records
def record_file(fk):
    fid, plugin = fk.split(':', 1)
    hits = []
    for ref in REFS:
        for folder in ('Armors', 'ArmorAddons'):
            hits += glob.glob(os.path.join(ref, folder, f'* - {fid}_{plugin}.yaml'))
    assert hits, fk
    return hits[-1]                    # REFS are in load order: the last hit wins


def field(text, name):
    m = re.search(r'^' + name + r': (.+?)\s*$', text, re.M)
    return m.group(1) if m else None


def block_list(text, name):
    m = re.search(r'^' + name + r':\s*\r?\n((?:- .*\r?\n?)+)', text, re.M)
    return [ln[2:].strip() for ln in m.group(1).splitlines()] if m else []


def male_model(text):
    m = re.search(r'^WorldModel:\s*\r?\n  Male:\s*\r?\n(?:    .*\r?\n)*?    File: (.+?)\s*$', text, re.M)
    return m.group(1) if m else None


def npcs():
    """{NPC FormKey: (EditorID, skin FormKey, female)} for every winning goblin NPC."""
    win = {}
    for ref in REFS:
        for f in os.listdir(os.path.join(ref, 'Npcs')):
            text = open(os.path.join(ref, 'Npcs', f), encoding='utf-8').read()
            fk = field(text, 'FormKey')
            if fk in win or field(text, 'Race') == RACE:
                win[fk] = text
    out = {}
    for fk, text in win.items():
        if field(text, 'Race') != RACE:
            continue
        cfg = re.search(r'^Configuration:\s*\r?\n((?:  .*\r?\n?)+)', text, re.M)
        female = bool(cfg and re.search(r'^  Flags:.*\bFemale\b', cfg.group(1), re.M))
        out[fk] = (field(text, 'EditorID'), field(text, 'WornArmor'), female)
    return out


def race_record():
    for ref in reversed(REFS):
        hits = glob.glob(os.path.join(ref, 'Races', f'* - {RACE.replace(":", "_")}.yaml'))
        if hits:
            return open(hits[0], encoding='utf-8').read()
    raise SystemExit(RACE)


# ---------------------------------------------------------------------------------------------------
# files
def enabled_mods():
    return [ln[1:].strip() for ln in open(PROFILE, encoding='utf-8') if ln.startswith('+')]


def resolve(rel, mods):
    """First enabled mod (MO2 priority order) with the loose file `meshes\\<rel>`."""
    parts = ['meshes'] + rel.replace(BS, '/').split('/')
    for m in mods:
        cur = os.path.join(MODS, m)
        for part in parts:                         # case-insensitive walk
            hit = [e for e in os.listdir(cur) if e.lower() == part.lower()] if os.path.isdir(cur) else []
            if not hit:
                cur = None
                break
            cur = os.path.join(cur, hit[0])
        if cur and os.path.isfile(cur):
            return cur
    spec = importlib.util.spec_from_file_location(
        'etr', os.path.join(REPO, 'src', 'EnderalTextureRestores', 'tools', '01-extract-enderal-textures.py'))
    etr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(etr)
    for bsa in GAME_BSAS:
        try:
            blob = etr.read_from_bsa(bsa, BS.join(parts).lower())
        except SystemExit:
            continue
        out = os.path.join(TMP, os.path.basename(bsa), *parts)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, 'wb') as fh:
            fh.write(blob)
        return out
    raise SystemExit(f'neither an enabled mod nor an Enderal BSA provides meshes{BS}{rel}')


def digest(path):
    with open(path, 'rb') as fh:
        return hashlib.sha1(fh.read()).hexdigest()


def source(path):
    """The MO2 mod (or Enderal BSA) a resolved file came from, for the log."""
    rel = os.path.relpath(path, TMP if path.startswith(TMP) else MODS)
    return rel.split(os.sep)[0]


# ---------------------------------------------------------------------------------------------------
def main():
    mods = enabled_mods()
    tpl = json.load(open(DF_JSON, encoding='utf-8'))
    race = race_record()
    m = re.search(r'^SkeletalModel:\s*\r?\n  Male:\s*\r?\n(?:    .*\r?\n)*?    File: (.+?)\s*$', race, re.M)
    skel = resolve(m.group(1), mods)
    print(f'{RACE_EDID} skeleton <- {source(skel)}')
    bone_sets = {limb: descendants(skel, spec[0]) for limb, spec in LIMBS.items()}

    actors = npcs()
    race_skin = field(race, 'Skin')
    by_skin = {}
    for fk, (edid, skin, female) in sorted(actors.items()):
        by_skin.setdefault(skin or race_skin, []).append((edid, female))
    print(f'{len(actors)} goblin NPCs on {len(by_skin)} skins; '
          f'{sum(f for _, _, f in actors.values())} female')

    out_dir = os.path.join(OUT_MOD, 'meshes', *MESH_REL.split(BS))
    if os.path.isdir(out_dir):
        for f in os.listdir(out_dir):
            os.remove(os.path.join(out_dir, f))
    os.makedirs(out_dir, exist_ok=True)

    plan, by_sig, fid = [], {}, FIRST_FID
    for skin, who in sorted(by_skin.items()):
        armo = open(record_file(skin), encoding='utf-8').read()
        models = []
        for arma in block_list(armo, 'Armature'):
            text = open(record_file(arma), encoding='utf-8').read()
            races = [field(text, 'Race')] + block_list(text, 'AdditionalRaces')
            if RACE in races:
                models.append(male_model(text))
        assert models, skin
        nifs = [(mdl, NifFile(resolve(mdl, mods))) for mdl in models]
        print(f'{field(armo, "EditorID")} {skin} ({len(who)} NPCs): '
              f'{", ".join(f"{mdl.split(BS)[-1]} <- {source(resolve(mdl, mods))}" for mdl in models)}')
        all_shapes = [s for _, nf in nifs for s in nf.shapes]
        bodies = {s.textures['Diffuse'].split(BS)[-1].lower() for s in all_shapes if s.name == BODY}
        assert len(bodies) <= 1 and bodies <= set(CAP_VARIANTS), (skin, bodies)
        cap = CAP_VARIANTS[bodies.pop()] if bodies else None
        print(f'    stump caps: {cap or "DF Falmer"}')
        for limb, (ref_bone, node, cont, base_t, addon_t) in LIMBS.items():
            if cap:
                addon_t = f'Zenderal - {cap} - Actor addons data - {base_t.split(" - ")[-1]}'
            pieces = []
            for mdl, nif in nifs:
                for shape in nif.shapes:
                    pc = cut_shape(nif, shape, ref_bone, bone_sets[limb], all_shapes)
                    if pc:
                        pc['model'] = mdl
                        pieces.append(pc)
            ntris = sum(len(p['tris']) for p in pieces)
            if ntris < MIN_TRIS:
                print(f'    {limb}: {ntris} tris - skipped')
                continue
            # keyed by file content: the Goblins mod ships falmer02 == falmer04 and falmer03 == falmer05
            sig = (limb, addon_t) + tuple(sorted((digest(resolve(p['model'], mods)), p['name'], len(p['tris']))
                                         for p in pieces))
            if sig not in by_sig:
                mesh = f'{"Goblin" if cap else "Falmer"}_{limb}_{fid:03X}.nif'
                translation = tuple(tpl[base_t]['Translation'][k] for k in 'xyz')
                build_nif(os.path.join(FALMER_DIR, cont), pieces, translation, os.path.join(out_dir, mesh))
                entry = dict(fid=f'{fid:06X}', limb=limb, mesh=MESH_REL + BS + mesh, node=node,
                             base_template=base_t, addon_template=addon_t, cap=cap, npcs=0, skins=[])
                by_sig[sig] = entry
                plan.append(entry)
                print(f'    {limb}: {ntris} tris from {", ".join(p["name"] for p in pieces)} -> {mesh}')
                fid += 1
            else:
                print(f'    {limb}: same as {by_sig[sig]["mesh"].split(BS)[-1]}')
            by_sig[sig]['skins'].append({'race': RACE_EDID, 'skin': skin})
            by_sig[sig]['npcs'] += len(who)
    assert fid <= 0xFFF, 'ESL range exhausted'
    with open(PLAN, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(plan, fh, indent=2)
        fh.write('\n')
    print(f'{len(plan)} goblin limb meshes -> {out_dir}; plan -> {PLAN}.')


if __name__ == '__main__':
    main()
