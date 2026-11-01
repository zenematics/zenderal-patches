"""Build the Minotaur limb meshes for `Zenderal - Lost Ones Dismembering`, and the plan 01/02 read.

Minotaurs SE (`1Minotaurs.esp`, Enderal build from 4thUnknown's "Minotaurs In Enderal") and
`MinotaursInEnderal.esp` (loads after it; overrides the NPCs/ARMAs and adds Celtic/Forsworn/Ancient
skins) put minotaurs on two races DF has no data for:
  * MinotaurRace (00A81E): human-style skeleton `1mino\\1minotaur\\skeleton.nif`. Its race skin is
    human SkinNaked, so a minotaur is drawn ENTIRELY from its NPC skin (`WornArmor`), and that ARMO is a
    whole outfit: body ("cuirass" incl. the fur), gauntlets, boots and the bull-head "helmet".
  * FeralMinotaurRace (00A810): one `wildmino.nif` body on `1mino\\1wildminotaur\\skeleton.nif`.
Both skeletons use the standard `NPC ...` bone names DF's templates hook.

DF matches race -> skin -> sex, so every minotaur skin gets its own limbs, cut from exactly the meshes
that skin renders. For each skin and limb, every shape of every ARMA model is cut by dominant bone
(the limb bone + all its descendants in the race skeleton, so horns/jaw/fingers come along), moved into
the RefNode bone's local space with the shape's own skin-to-bone transform, and added (shader, the
nine textures and any alpha property kept) to a DF container nif whose own shapes are then detached:
  forearms/calves -> DF humanoid naked male limbs (from `DF - Official Humanoid Pack.bsa`) with the
                     humanoid male base-data templates;
  head            -> DF draugr naked male head with the draugr male head template.
Each new shape is skinned rigidly to `Root` with skin-to-bone = (identity, template Translation): see
limbmesh.py for the convention. Limbs with identical geometry are shared between skins.

Writes the meshes into the MO2 mod (generated from the user's install, never committed) and
`minotaur-limbs.json` next to this script (committed; 01 and 02 build the DF JSON and MiscItems from it).

Usage:  python 04-build-minotaur-limbs.py <pynifly io_scene_nifly dir> [<modlist root>]
        (modlist root defaults to E:/Zenderal; mesh paths resolve through the Ultra profile's mod order)
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
from pyn.pynifly import NifFile  # noqa: E402
from limbmesh import build_nif, cut_shape, descendants  # noqa: E402

BS = chr(92)
MODS = os.path.join(ROOT, 'mods')
PROFILE = os.path.join(ROOT, 'profiles', 'Ultra', 'modlist.txt')
OUT_MOD = os.path.join(MODS, 'Zenderal - Lost Ones Dismembering')
MESH_REL = BS.join(['DismemberingFramework', 'Zenderal', 'Minotaurs'])
PLAN = os.path.join(HERE, 'minotaur-limbs.json')
# Plugins in load order; a later one wins a record (reference/mods, gitignored, spriggit-decompile-reference)
REFS = [os.path.join(REPO, 'reference', 'mods', d) for d in ('MinotaursEnderal', 'MinotaursInEnderal')]
RACES = {'00A81E:1Minotaurs.esp': 'MinotaurRace', '00A810:1Minotaurs.esp': 'FeralMinotaurRace'}
FIRST_FID = 0x805      # 0x800-0x804 are the skeleton limbs

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
# limb -> (RefNode bone, DATA node, container, base-data template, actor-addon template)
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
MIN_TRIS = 20          # a limb with less geometry than this is left undismemberable for that skin


# ---------------------------------------------------------------------------------------------------
# records
def load_records():
    rec = {}
    for ref in REFS:
        assert os.path.isdir(ref), ref
        for folder in ('Npcs', 'Armors', 'ArmorAddons', 'Races'):
            d = os.path.join(ref, folder)
            if not os.path.isdir(d):
                continue
            for f in os.listdir(d):
                text = open(os.path.join(d, f), encoding='utf-8').read()
                fk = re.search(r'^FormKey: (\S+)', text, re.M).group(1)
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
    """(race edid, skin FormKey) for every minotaur NPC skin in the winning records."""
    out = set()
    for fk, (folder, text) in rec.items():
        if folder != 'Npcs':
            continue
        race = field(text, 'Race')
        if race in RACES:
            skin = field(text, 'WornArmor') or field(rec[race][1], 'Skin')
            out.add((RACES[race], skin))
    return sorted(out)


# ---------------------------------------------------------------------------------------------------
# files
def enabled_mods():
    return [ln[1:].strip() for ln in open(PROFILE, encoding='utf-8') if ln.startswith('+')]


def resolve(rel, mods):
    """First enabled mod (MO2 priority order) with the loose file `meshes\\<rel>`."""
    parts = ['meshes'] + rel.replace(BS, '/').split('/')
    for m in mods:
        p = os.path.join(MODS, m, *parts)
        if os.path.isfile(p):
            return p
        # case-insensitive fallback for mixed-case folder names
        cur = os.path.join(MODS, m)
        for part in parts:
            hit = [e for e in os.listdir(cur)] if os.path.isdir(cur) else []
            match = [e for e in hit if e.lower() == part.lower()]
            if not match:
                cur = None
                break
            cur = os.path.join(cur, match[0])
        if cur and os.path.isfile(cur):
            return cur
    raise SystemExit(f'no enabled mod provides meshes{BS}{rel}')


def humanoid_container(name, tmp):
    spec = importlib.util.spec_from_file_location(
        'etr', os.path.join(REPO, 'src', 'EnderalTextureRestores', 'tools', '01-extract-enderal-textures.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    blob = m.read_from_bsa(HUMANOID_BSA, (HUMANOID_DIR + BS + name).lower())
    out = os.path.join(tmp, name)
    with open(out, 'wb') as fh:
        fh.write(blob)
    return out


# ---------------------------------------------------------------------------------------------------
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

    tmp = tempfile.mkdtemp(prefix='zen_minotaur_')
    containers = {spec[2]: (DRAUGR_HEAD if spec[2] == 'draugr_head' else humanoid_container(spec[2], tmp))
                  for spec in LIMBS.values()}

    plan, by_sig, fid = [], {}, FIRST_FID
    for race, skin in skins(rec):
        armo = rec[skin][1]
        models = []
        for arma in block_list(armo, 'Armature'):
            text = rec[arma][1]
            races = [field(text, 'Race')] + block_list(text, 'AdditionalRaces')
            if not any(r in RACES and RACES[r] == race for r in races):
                continue
            models.append(male_model(text))
        assert models, (race, skin)
        nifs = [(m, NifFile(resolve(m, mods))) for m in models]
        print(f'{race} {skin}: {", ".join(m.split(BS)[-1] for m in models)}')
        for limb, (ref_bone, node, cont, base_t, addon_t) in LIMBS.items():
            pieces = []
            all_shapes = [s for _, nf in nifs for s in nf.shapes]
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
                mesh = f'Minotaur_{limb}_{fid:03X}.nif'
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
    print(f'{len(plan)} minotaur limb meshes -> {out_dir}; plan -> {PLAN}. Rebuild CRDW before testing.')


if __name__ == '__main__':
    main()
