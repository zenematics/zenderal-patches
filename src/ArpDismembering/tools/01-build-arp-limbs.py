"""Cut Dismembering Framework limbs for the Arps from the bodies the list actually renders on them.

Arps are FalmerRace. DF's official Falmer limbs are Skyrim's pale, blind Falmer, but the list's `Enderal Arp`
mod (`Enderal - Arp.esp`) overrides all seven Falmer body ARMAs with Enderal's swamp-race meshes (dark skin,
red eyes, green dreadlocks), so a severed Arp head or arm looked like a different creature (seen in game
2026-10-26). Same method as src/Goblins/tools/04: per Arp skin, the meshes its ARMAs render are cut by
dominant bone (limb bone + descendants in the Falmer skeleton), moved into the RefNode bone's space and put
inside DF's naked male Falmer limb nif of that limb (its own shapes detached). DF's Falmer base-data and
actor-addon templates are reused (stump caps stay DF's Falmer caps).

Skins: the five Enderal Arp skins, Skyrim's SkinFalmer01 (five Arp NPCs wear it) and the race skin
SkinFalmer (DF's `ANY`). Body models are read from `Enderal - Arp.esp` (asserted: all seven ARMAs, and the
plugin is enabled); ARMO -> ARMA lists from reference/base/Skyrim (EGO and FS don't override them).

Writes the meshes into the MO2 mod `Zenderal - Arp Dismembering` (generated from the user's install, never
committed) and `arp-limbs.json` next to this script (committed; 02 builds the plugin and DF JSON from it).

Usage:  python 01-build-arp-limbs.py <pynifly io_scene_nifly dir> [<modlist root>]
        ($Tools.pynifly in .claude/config/tools.json; modlist root defaults to E:/Zenderal)
"""
import glob
import hashlib
import importlib.util
import json
import os
import re
import struct
import sys
import tempfile
import zlib

PYN = sys.argv[1]
ROOT = sys.argv[2] if len(sys.argv) > 2 else 'E:/Zenderal'
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, PYN)
sys.path.insert(0, os.path.join(REPO, 'src', 'LostOnesDismembering', 'tools'))   # limbmesh.py
from pyn.pynifly import NifFile  # noqa: E402
from limbmesh import build_nif, cut_shape, descendants  # noqa: E402

BS = chr(92)
MODS = os.path.join(ROOT, 'mods')
PROFILE = os.path.join(ROOT, 'profiles', 'Ultra')
GAME_BSAS = [os.path.join(ROOT, 'Stock Game', 'Data', b) for b in ('E - Update.bsa', 'E - Meshes.bsa',
                                                                  'Skyrim - Meshes1.bsa', 'Skyrim - Meshes0.bsa')]
TMP = tempfile.mkdtemp(prefix='zen_arp_')
OUT_MOD = os.path.join(MODS, 'Zenderal - Arp Dismembering')
MESH_REL = BS.join(['DismemberingFramework', 'Zenderal', 'Arps'])
PLAN = os.path.join(HERE, 'arp-limbs.json')
BASE = os.path.join(REPO, 'reference', 'base', 'Skyrim')
ARP_ESP = os.path.join(MODS, 'Enderal Arp', 'Enderal - Arp.esp')
SKELETON = BS.join(['Actors', 'Falmer', 'Character Assets', 'skeleton.nif'])
FIRST_FID = 0x800

# skin FormID (Skyrim.esm) -> EditorID; every skin a FalmerRace Arp wears, plus the race skin
SKINS = {
    '0B526C': '_00E_Arp1', '0B526D': '_00E_Arp2', '0B526E': '_00E_Arp3', '0B526F': '_00E_Arp4',
    '01848C': '_00E_SkinArpShaman', '050F30': 'SkinFalmer01', '016EE7': 'SkinFalmer',
}
RACE_SKIN = '016EE7'
FALMER_ARMAS = {'020E24', '050F2F', '050F31', '050F33', '050F35', '050F37', '050F39'}
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
MIN_TRIS = 20


# ---------------------------------------------------------------------------------------------------
def arp_models():
    """{ARMA FormID: male model} from Enderal - Arp.esp (it masters only Skyrim.esm)."""
    d = open(ARP_ESP, 'rb').read()

    def subs(data):
        i = 0
        while i + 6 <= len(data):
            t, n = data[i:i + 4], struct.unpack_from('<H', data, i + 4)[0]
            yield t, data[i + 6:i + 6 + n]
            i += 6 + n

    out = {}
    hsize = struct.unpack_from('<I', d, 4)[0]
    i = 24 + hsize
    while i < len(d):
        t, size = d[i:i + 4], struct.unpack_from('<I', d, i + 4)[0]
        if t == b'GRUP':
            i += 24
            continue
        flags, fid = struct.unpack_from('<II', d, i + 8)
        body = d[i + 24:i + 24 + size]
        if flags & 0x40000:
            body = zlib.decompress(body[4:])
        if t == b'ARMA':
            for st, sd in subs(body):
                if st == b'MOD2':
                    out[f'{fid & 0xFFFFFF:06X}'] = sd.rstrip(b'\0').decode('latin-1')
        i += 24 + size
    assert set(out) == FALMER_ARMAS, sorted(out)
    return out


def armo_armas(fid):
    hits = glob.glob(os.path.join(BASE, 'Armors', f'* - {fid}_Skyrim.esm.yaml'))
    assert len(hits) == 1, fid
    text = open(hits[0], encoding='utf-8').read()
    m = re.search(r'^Armature:\s*\r?\n((?:- .*\r?\n?)+)', text, re.M)
    return [ln[2:].strip().split(':')[0] for ln in m.group(1).splitlines()]


def enabled(profile_file, prefix):
    return [ln[1:].strip() for ln in open(os.path.join(PROFILE, profile_file), encoding='utf-8')
            if ln.startswith(prefix)]


def resolve(rel, mods):
    """First enabled mod (MO2 priority order) with the loose file `meshes\\<rel>`, else an Enderal BSA."""
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


def source(path):
    rel = os.path.relpath(path, TMP if path.startswith(TMP) else MODS)
    return rel.split(os.sep)[0]


def digest(path):
    with open(path, 'rb') as fh:
        return hashlib.sha1(fh.read()).hexdigest()


# ---------------------------------------------------------------------------------------------------
def main():
    mods = enabled('modlist.txt', '+')
    assert 'Enderal Arp' in mods and 'Enderal - Arp.esp' in enabled('plugins.txt', '*'), 'Enderal Arp not enabled'
    models = arp_models()
    tpl = json.load(open(DF_JSON, encoding='utf-8'))
    skel = resolve(SKELETON, mods)
    print(f'FalmerRace skeleton <- {source(skel)}')
    bone_sets = {limb: descendants(skel, spec[0]) for limb, spec in LIMBS.items()}

    out_dir = os.path.join(OUT_MOD, 'meshes', *MESH_REL.split(BS))
    if os.path.isdir(out_dir):
        for f in os.listdir(out_dir):
            os.remove(os.path.join(out_dir, f))
    os.makedirs(out_dir, exist_ok=True)

    plan, by_sig, fid = [], {}, FIRST_FID
    for skin, edid in SKINS.items():
        mdls = [models[a] for a in armo_armas(skin) if a in models]
        assert mdls, (skin, edid)
        nifs = [(m, NifFile(resolve(m, mods))) for m in mdls]
        print(f'{edid} {skin}: {", ".join(f"{m.split(BS)[-1]} <- {source(resolve(m, mods))}" for m in mdls)}')
        all_shapes = [s for _, nf in nifs for s in nf.shapes]
        for limb, (ref_bone, node, cont, base_t, addon_t) in LIMBS.items():
            pieces = []
            for mdl, nif in nifs:
                for shape in nif.shapes:
                    pc = cut_shape(nif, shape, ref_bone, bone_sets[limb], all_shapes)
                    if pc:
                        pc['model'] = mdl
                        pieces.append(pc)
            ntris = sum(len(p['tris']) for p in pieces)
            if ntris < MIN_TRIS:
                print(f'    {limb}: {ntris} tris - skipped (keeps DF Falmer limb)')
                continue
            sig = (limb,) + tuple(sorted((digest(resolve(p['model'], mods)), p['name'], len(p['tris']))
                                         for p in pieces))
            if sig not in by_sig:
                mesh = f'Arp_{limb}_{fid:03X}.nif'
                translation = tuple(tpl[base_t]['Translation'][k] for k in 'xyz')
                build_nif(os.path.join(FALMER_DIR, cont), pieces, translation, os.path.join(out_dir, mesh))
                entry = dict(fid=f'{fid:06X}', limb=limb, mesh=MESH_REL + BS + mesh, node=node,
                             base_template=base_t, addon_template=addon_t, skins=[])
                by_sig[sig] = entry
                plan.append(entry)
                print(f'    {limb}: {ntris} tris from {", ".join(p["name"] for p in pieces)} -> {mesh}')
                fid += 1
            else:
                print(f'    {limb}: same as {by_sig[sig]["mesh"].split(BS)[-1]}')
            by_sig[sig]['skins'].append(f'{skin}:Skyrim.esm')
    assert fid <= 0xFFF, 'ESL range exhausted'
    with open(PLAN, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(plan, fh, indent=2)
        fh.write('\n')
    print(f'{len(plan)} Arp limb meshes -> {out_dir}; plan -> {PLAN}.')


if __name__ == '__main__':
    main()
