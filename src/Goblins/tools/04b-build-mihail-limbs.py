"""Build the limb meshes for Mihail's goblins (`Zenderal - Goblins Dismembering`), and the plan 06 reads.
Run after 01b and 05 (its FormIDs follow 05's cap pairs).

Mihail's goblin race (ZEN_Mihail_mihailgoblinrace 0x830, copied by 01b) is a humanoid: skeleton
`Mihail Monsters and Animals\\Human\\Goblins\\skeletongoblin.nif` with the standard `NPC ... [xxx]` bones,
DefaultMale.hkx. Its three skins cover only the Body slot, and the goblin's head is part of the body mesh
(2,921 head-weighted vertices in each `mihailgoblin*.nif`). DF keys its humanoid data by race EditorID, so
these goblins were never dismembered.

Same method as src/LostOnesDismembering/tools/04-build-minotaur-limbs.py (minotaurs, verified in game
2026-10-19), whose helpers this copies. For every Mihail skin worn by a goblin NPC and every limb, each
shape of the skin's male model is cut by dominant bone (the limb bone + all its descendants in the race
skeleton) and moved into the RefNode bone's space, keeping shader, textures and alpha. Forearms and calves
go into DF's humanoid naked male limb nifs (`DF - Official Humanoid Pack.bsa`) with the humanoid male
templates; the head goes into DF's draugr naked male head with the draugr head template (the humanoid head
is `Method: Decapitate`, not a mesh). The templates' BipedSlots (33/37/31) are free on this race (rule from
the spider work: never a slot the race's skins cover). No body caps: DF's humanoid caps are race-locked to
the playable races and render nothing here, as on the minotaurs.

Writes meshes into the MO2 mod `Zenderal - Goblins Dismembering` (generated, never committed) and
`mihail-dismember-limbs.json` (committed; 06 builds the MiscItems and DF JSON from it).

Usage:  python 04b-build-mihail-limbs.py <pynifly io_scene_nifly dir> [<modlist root>]
"""
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
OUT_MOD = os.path.join(MODS, 'Zenderal - Goblins Dismembering')
MESH_REL = BS.join(['DismemberingFramework', 'Zenderal', 'MihailGoblins'])
PLAN = os.path.join(HERE, 'mihail-dismember-limbs.json')
CAP_PLAN = os.path.join(HERE, 'dismember-caps.json')
REFS = [os.path.join(HERE, '..', 'GoblinsESP')]
RACES = {'000830:Zenderal - Goblins.esp': 'ZEN_Mihail_mihailgoblinrace'}

HUMANOID_BSA = os.path.join(MODS, 'DF - Official Humanoid Asset Pack', 'DF - Official Humanoid Pack.bsa')
HUMANOID_DIR = BS.join(['meshes', 'dismemberingframework', 'officialhumanoidpack', 'limbs', 'naked'])
DRAUGR_HEAD = os.path.join(MODS, 'DF - Official Creature Asset Pack', 'meshes', 'dismemberingframework',
                           'officialcreaturepack', 'draugr', 'male', 'limbs', 'naked', 'head.nif')
DF_JSON = {
    'humanoid': os.path.join(MODS, 'DF - Official Humanoid Asset Pack', 'SKSE', 'DismemberingFramework',
                             'OfficialHumanoidPack_BaseData_TEMPLATES.json'),
    'draugr': os.path.join(MODS, 'DF - Official Creature Asset Pack', 'SKSE', 'DismemberingFramework',
                           'OfficialCreaturePack_Draugr_BaseData_TEMPLATES.json'),
}
# limb -> (RefNode bone, DATA node, container, base-data template, actor-addon template)   (= minotaurs)
LIMBS = {
    'Calf_L': ('NPC L Calf [LClf]', 'NPC L Calf [LClf]', 'male_calf_l.nif',
               'Humanoid - Male - Base data - L Calf', 'Humanoid - Male - Actor addons data - L Calf'),
    'Calf_R': ('NPC R Calf [RClf]', 'NPC R Calf [RClf]', 'male_calf_r.nif',
               'Humanoid - Male - Base data - R Calf', 'Humanoid - Male - Actor addons data - R Calf'),
    'Forearm_L': ('NPC L Forearm [LLar]', 'NPC L Forearm [LLar]', 'male_forearm_l.nif',
                  'Humanoid - Male - Base data - L Forearm', 'Humanoid - Male - Actor addons data - L Forearm'),
    'Forearm_R': ('NPC R Forearm [RLar]', 'NPC R Forearm [RLar]', 'male_forearm_r.nif',
                  'Humanoid - Male - Base data - R Forearm', 'Humanoid - Male - Actor addons data - R Forearm'),
    'Head': ('NPC Head [Head]', 'NPC Neck [Neck]', 'draugr_head',
             'Draugr - Male - Base data - Head', 'Draugr - Male - Actor addons data - Head'),
}
MIN_TRIS = 20


# --- records (as 04-build-minotaur-limbs.py) ---------------------------------------------------------
def load_records():
    rec = {}
    for ref in REFS:
        for folder in ('Npcs', 'Armors', 'ArmorAddons', 'Races'):
            d = os.path.join(ref, folder)
            for f in os.listdir(d):
                text = open(os.path.join(d, f), encoding='utf-8').read()
                fk = re.search(r'^FormKey: (.+?)\s*$', text, re.M).group(1)
                rec[fk] = (folder, text)
    return rec


def field(text, name):
    m = re.search(r'^' + name + r': (.+?)\s*$', text, re.M)
    return m.group(1) if m else None


def block_list(text, name):
    m = re.search(r'^' + name + r':\s*\n((?:- .*\n?)+)', text, re.M)
    return [ln[2:].strip() for ln in m.group(1).splitlines()] if m else []


def male_model(text):
    m = re.search(r'^WorldModel:\s*\n  Male:\s*\n(?:    .*\n)*?    File: (.+?)\s*$', text, re.M)
    return m.group(1) if m else None


def skins(rec):
    out = set()
    for fk, (folder, text) in rec.items():
        if folder == 'Npcs' and field(text, 'Race') in RACES:
            race = field(text, 'Race')
            out.add((RACES[race], field(text, 'WornArmor') or field(rec[race][1], 'Skin')))
    return sorted(out)


def enabled_mods():
    return [ln[1:].strip() for ln in open(PROFILE, encoding='utf-8') if ln.startswith('+')]


def resolve(rel, mods):
    parts = ['meshes'] + rel.replace(BS, '/').split('/')
    for m in mods:
        cur = os.path.join(MODS, m)
        for part in parts:
            hit = [e for e in os.listdir(cur) if e.lower() == part.lower()] if os.path.isdir(cur) else []
            if not hit:
                cur = None
                break
            cur = os.path.join(cur, hit[0])
        if cur and os.path.isfile(cur):
            return cur
    raise SystemExit(f'no enabled mod provides meshes{BS}{rel}')


def humanoid_container(name, tmp):
    spec = importlib.util.spec_from_file_location(
        'etr', os.path.join(REPO, 'src', 'EnderalTextureRestores', 'tools', '01-extract-enderal-textures.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    out = os.path.join(tmp, name)
    with open(out, 'wb') as fh:
        fh.write(m.read_from_bsa(HUMANOID_BSA, (HUMANOID_DIR + BS + name).lower()))
    return out


# -----------------------------------------------------------------------------------------------------
def main():
    rec = load_records()
    mods = enabled_mods()
    tpl = {k: json.load(open(p, encoding='utf-8')) for k, p in DF_JSON.items()}
    tpl = {**tpl['humanoid'], **tpl['draugr']}
    race_skel = {}
    for fk, edid in RACES.items():
        m = re.search(r'^SkeletalModel:\s*\n  Male:\s*\n(?:    .*\n)*?    File: (.+?)\s*$', rec[fk][1], re.M)
        race_skel[edid] = resolve(m.group(1), mods)
    bone_sets = {(race, limb): descendants(race_skel[race], spec[0])
                 for race in race_skel for limb, spec in LIMBS.items()}

    out_dir = os.path.join(OUT_MOD, 'meshes', *MESH_REL.split(BS))
    if os.path.isdir(out_dir):
        for f in os.listdir(out_dir):
            os.remove(os.path.join(out_dir, f))
    os.makedirs(out_dir, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix='zen_mihail_')
    containers = {spec[2]: (DRAUGR_HEAD if spec[2] == 'draugr_head' else humanoid_container(spec[2], tmp))
                  for spec in LIMBS.values()}

    caps = json.load(open(CAP_PLAN, encoding='utf-8'))
    fid = max(int(c[k], 16) for c in caps for k in ('armo', 'arma')) + 1
    plan, by_sig = [], {}
    for race, skin in skins(rec):
        models = []
        for arma in block_list(rec[skin][1], 'Armature'):
            text = rec[arma][1]
            if field(text, 'Race') in RACES or any(r in RACES for r in block_list(text, 'AdditionalRaces')):
                models.append(male_model(text))
        assert models, (race, skin)
        nifs = [(m, NifFile(resolve(m, mods))) for m in models]
        print(f'{race} {skin}: {", ".join(m.split(BS)[-1] for m in models)}')
        all_shapes = [s for _, nf in nifs for s in nf.shapes]
        for limb, (ref_bone, node, cont, base_t, addon_t) in LIMBS.items():
            pieces = []
            for model, nif in nifs:
                for shape in nif.shapes:
                    pc = cut_shape(nif, shape, ref_bone, bone_sets[(race, limb)], all_shapes)
                    if pc:
                        pc['model'] = model
                        pieces.append(pc)
            ntris = sum(len(p['tris']) for p in pieces)
            if ntris < MIN_TRIS:
                print(f'    {limb}: {ntris} tris - skipped')
                continue
            sig = (limb,) + tuple(sorted((p['model'].lower(), p['name'], len(p['tris'])) for p in pieces))
            if sig not in by_sig:
                mesh = f'MihailGoblin_{limb}_{fid:03X}.nif'
                translation = tuple(tpl[base_t]['Translation'][k] for k in 'xyz')
                build_nif(containers[cont], pieces, translation, os.path.join(out_dir, mesh))
                entry = dict(fid=f'{fid:06X}', limb=limb, mesh=MESH_REL + BS + mesh, node=node,
                             base_template=base_t, addon_template=addon_t, skins=[])
                by_sig[sig] = entry
                plan.append(entry)
                print(f'    {limb}: {ntris} tris from {len(pieces)} shapes -> {mesh}')
                fid += 1
            else:
                print(f'    {limb}: same as {by_sig[sig]["mesh"].split(BS)[-1]}')
            by_sig[sig]['skins'].append({'race': race, 'skin': skin})
    assert fid <= 0xFFF, 'ESL range exhausted'
    with open(PLAN, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(plan, fh, indent=2)
        fh.write('\n')
    print(f'{len(plan)} Mihail goblin limb meshes -> {out_dir}; plan -> {PLAN}')


if __name__ == '__main__':
    main()
