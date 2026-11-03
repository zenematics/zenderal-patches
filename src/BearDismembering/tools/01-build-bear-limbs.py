"""Cut Dismembering Framework limbs for Enderal's bears from the Bears of the North bodies the list renders.

DF's creature data has no bear at all (its packs cover draugr, falmer, trolls and wolves), and no DF bear patch
exists on Nexus (searched 2026-10-11). Enderal's bears are the four vanilla bear races and wear their race skins
(no bear NPC has WornArmor except FS's summonable panda, which is deliberately left out):

    BearBrownRace       0131E7  SkinBearBrown      0868FD  -> ARMA 0868FB  (EGO SE - Bears of the North wins)
    BearBrownRaceHoher  0EAA5A  SkinBearBrownHoher 0EAA5B  -> ARMA 0868FB  (EGO BotN adds the race)
    BearBlackRace       0131E8  SkinBearCave       0187FE  -> ARMA 018800  (Bears of the North wins)
    BearSnowRace        0131E9  SkinBearWhite      0187FD  -> ARMA 0187FF  (Bears of the North wins;
                                                              0868FB is also listed but is not for this race)

Winners from a master-aware scan of the Ultra load order (2026-11-01); the models are read from the winners'
serialized records (reference/mods/BearsOfTheNorth, reference/mods/EGOBearsOfTheNorth) and asserted.

Same method as src/ArpDismembering/tools/01: each body (base shape + its five fur shells) is cut by dominant
bone (the limb bone and its descendants in the bear skeleton), moved into the RefNode bone's space and put
inside DF's wolf limb nif of the matching limb (its own shapes detached, collision hull re-fitted to the bear
geometry, because the bear bones do not lie along the canine axes). The wolf template's Translation is kept,
so the container's `Origin` node still marks the joint.

DF's wolf stump blood (ActorArtObject) attaches to a node named after the canine bone, which a bear does not
have, so each wolf `BloodFX_<limb>.nif` is copied with that one node name renamed to the bear bone.

Writes the meshes into the MO2 mod `Zenderal - Bear Dismembering` (generated from the user's install, never
committed) and `bear-limbs.json` next to this script (committed; 02 builds the plugin and DF JSON from it).

Usage:  python 01-build-bear-limbs.py <pynifly io_scene_nifly dir> [<modlist root>]
        ($Tools.pynifly in .claude/config/tools.json; modlist root defaults to E:/Zenderal)
"""
import hashlib
import importlib.util
import json
import os
import re
import struct
import sys

PYN = sys.argv[1]
ROOT = sys.argv[2] if len(sys.argv) > 2 else 'E:/Zenderal'
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, PYN)
sys.path.insert(0, os.path.join(REPO, 'src', 'LostOnesDismembering', 'tools'))   # limbmesh.py
from pyn.pynifly import NifFile  # noqa: E402
from limbmesh import build_nif, cut_loops, cut_shape, descendants, gore_caps  # noqa: E402
import numpy as np  # noqa: E402
from nif import Nif, Reader  # noqa: E402  (limbmesh put HorseCloakFluffFix/tools on sys.path)

# the Arp generator's MO2 resolver (loose file by mod priority, else an Enderal BSA)
_spec = importlib.util.spec_from_file_location('arp01', os.path.join(REPO, 'src', 'ArpDismembering', 'tools',
                                                                     '01-build-arp-limbs.py'))
arp = importlib.util.module_from_spec(_spec)
_argv = sys.argv
sys.argv = [_argv[0], PYN, ROOT]
_spec.loader.exec_module(arp)
sys.argv = _argv

BS = chr(92)
MODS = os.path.join(ROOT, 'mods')
OUT_MOD = os.path.join(MODS, 'Zenderal - Bear Dismembering')
MESH_REL = BS.join(['DismemberingFramework', 'Zenderal', 'Bears'])
PLAN = os.path.join(HERE, 'bear-limbs.json')
REF = os.path.join(REPO, 'reference', 'mods')
SKELETON = BS.join(['Actors', 'Bear', 'Character Assets', 'skeleton.nif'])
WOLF = os.path.join(MODS, 'DF - Official Creature Asset Pack', 'meshes', 'dismemberingframework',
                    'officialcreaturepack', 'wolf')
WOLF_TPL = os.path.join(MODS, 'DF - Official Creature Asset Pack', 'SKSE', 'DismemberingFramework',
                        'OfficialCreaturePack_Wolf_BaseData_TEMPLATES.json')
FIRST_ART, FIRST_LIMB = 0x800, 0x805

# skin FormID -> (EditorID, race EditorID, race FormID, ARMA FormID, winning plugin's reference tree)
SKINS = {
    '0868FD': ('SkinBearBrown', 'BearBrownRace', '0131E7', '0868FB', 'EGOBearsOfTheNorth'),
    '0EAA5B': ('SkinBearBrownHoher', 'BearBrownRaceHoher', '0EAA5A', '0868FB', 'EGOBearsOfTheNorth'),
    '0187FE': ('SkinBearCave', 'BearBlackRace', '0131E8', '018800', 'BearsOfTheNorth'),
    '0187FD': ('SkinBearWhite', 'BearSnowRace', '0131E9', '0187FF', 'BearsOfTheNorth'),
}
# limb -> (RefNode bone, DATA node = cut bone set root, wolf container, wolf blood fx, canine node in it,
#          wolf base-data template whose Translation is kept)
LIMBS = {
    'Front_L_Leg': ('NPC LArm2', 'NPC LArm2', 'front_l_leg.nif', 'bloodfx_front_l_leg.nif', 'Canine_LFrontLeg2',
                    'Wolf - Base data - Front L Leg'),
    'Front_R_Leg': ('NPC RArm2', 'NPC RArm2', 'front_r_leg.nif', 'bloodfx_front_r_leg.nif', 'Canine_RFrontLeg2',
                    'Wolf - Base data - Front R Leg'),
    'Back_L_Leg': ('NPC LLeg2', 'NPC LLeg2', 'back_l_leg.nif', 'bloodfx_back_l_leg.nif', 'Canine_LBackLeg2',
                   'Wolf - Base data - Back L Leg'),
    'Back_R_Leg': ('NPC RLeg2', 'NPC RLeg2', 'back_r_leg.nif', 'bloodfx_back_r_leg.nif', 'Canine_RBackLeg2',
                   'Wolf - Base data - Back R Leg'),
    'Head': ('NPC Head', 'NPC Neck2', 'head.nif', 'bloodfx_head.nif', 'Canine_Neck2', 'Wolf - Base data - Head'),
}
MIN_TRIS = 200


def arma_model(arma, tree, race):
    hits = [f for f in os.listdir(os.path.join(REF, tree, 'ArmorAddons')) if f' - {arma}_Skyrim.esm' in f]
    assert len(hits) == 1, (arma, tree, hits)
    text = open(os.path.join(REF, tree, 'ArmorAddons', hits[0]), encoding='utf-8').read()
    races = re.findall(r'^Race: (\w+):', text, re.M)
    extra = re.search(r'^AdditionalRaces:\s*\r?\n((?:- .*\r?\n?)+)', text, re.M)
    if extra:
        races += re.findall(r'^- (\w+):', extra.group(1), re.M)
    assert race in races, (arma, race, races)
    m = re.search(r'^WorldModel:\s*\r?\n  Male:\s*\r?\n(?:    .*\r?\n)*?    File: (.+?)\r?$', text, re.M)
    assert m and 'botn_' in m.group(1).lower(), (arma, m and m.group(1))
    return m.group(1)


def rename_node(src, dst, old, new):
    """Copy a wolf blood-fx nif with its art attach node renamed. The name is the one string of the nif's
    NiStringsExtraData block, `NamedNode&<bone>` (u32 count, then u32 length + bytes per string), so only that
    block grows; its entry in the header's block-size table is updated (same table walk as limbmesh.rewrite_hull)."""
    n = Nif(src)
    hits = [i for i, (t, _, _) in enumerate(n.blocks) if t == 'NiStringsExtraData']
    assert len(hits) == 1, (src, hits)
    i = hits[0]
    _, pos, size = n.blocks[i]
    blk = bytes(n.data[pos:pos + size])
    want = b'NamedNode&' + old.encode()
    assert struct.unpack_from('<I', blk, 4)[0] == 1 and blk[12:] == want and struct.unpack_from('<I', blk, 8)[0] == len(want), (src, blk)
    s = b'NamedNode&' + new.encode()
    nb = blk[:8] + struct.pack('<I', len(s)) + s
    r = Reader(n.data, n.data.index(b'\n') + 1)
    r.skip(4 + 1 + 4)
    nblocks = r.take('I')
    r.skip(4)
    for _ in range(3):
        r.skip(r.take('B'))
    for _ in range(r.take('H')):
        r.skip(r.take('I'))
    sizes_at = r.p + 2 * nblocks
    assert struct.unpack_from('<I', n.data, sizes_at + 4 * i)[0] == size, src
    d = bytearray(bytes(n.data[:pos]) + nb + bytes(n.data[pos + size:]))
    struct.pack_into('<I', d, sizes_at + 4 * i, len(nb))
    with open(dst, 'wb') as fh:
        fh.write(d)
    check = Nif(dst)
    assert len(check.blocks) == len(n.blocks) and s in bytes(check.data) and want not in bytes(check.data), dst


def digest(path):
    with open(path, 'rb') as fh:
        return hashlib.sha1(fh.read()).hexdigest()


def main():
    mods = arp.enabled('modlist.txt', '+')
    plugins = arp.enabled('plugins.txt', '*')
    for need in ('Bears of the North.esp', 'EGO SE - Bears of the North.esp', 'DF - Official Creature Pack.esp'):
        assert need in plugins, f'{need} not enabled'
    tpl = json.load(open(WOLF_TPL, encoding='utf-8'))
    skel = arp.resolve(SKELETON, mods)
    print(f'bear skeleton <- {arp.source(skel)}')
    bone_sets = {limb: descendants(skel, spec[1]) for limb, spec in LIMBS.items()}

    out_dir = os.path.join(OUT_MOD, 'meshes', *MESH_REL.split(BS))
    if os.path.isdir(out_dir):
        for f in os.listdir(out_dir):
            os.remove(os.path.join(out_dir, f))
    os.makedirs(out_dir, exist_ok=True)

    arts = []
    for k, (limb, (_, node, _, fx, canine, _)) in enumerate(LIMBS.items()):
        mesh = f'BloodFX_{limb}.nif'
        rename_node(os.path.join(WOLF, 'effects', fx), os.path.join(out_dir, mesh), canine, node)
        arts.append(dict(fid=f'{FIRST_ART + k:06X}', limb=limb, mesh=MESH_REL + BS + mesh, node=node))
    assert FIRST_ART + len(arts) <= FIRST_LIMB

    limbs, by_sig, fid = [], {}, FIRST_LIMB
    for skin, (edid, race_edid, race, arma, tree) in SKINS.items():
        mdl = arma_model(arma, tree, race)
        path = arp.resolve(mdl, mods)
        nif = NifFile(path)
        print(f'{edid} {skin} ({race_edid}): {mdl.split(BS)[-1]} <- {arp.source(path)}')
        for limb, (ref_bone, node, cont, _, _, base_t) in LIMBS.items():
            pieces = [pc for pc in (cut_shape(nif, s, ref_bone, bone_sets[limb], nif.shapes) for s in nif.shapes) if pc]
            # the meat layer: close the cut on the skin shape (not the fur shells), or the limb shows its hollow inside
            body = [pc for pc in pieces if not pc['name'].lower().startswith('shell')]
            assert len(body) == 1, [pc['name'] for pc in pieces]
            loops = cut_loops(body[0]['shape'], bone_sets[limb])
            assert len(loops) == 1, (edid, limb, 'expected one closed cut ring', [len(x) for x in loops])
            cont_nif = NifFile(os.path.join(WOLF, 'limbs', cont))
            pieces.append(gore_caps(body[0], loops, cont_nif, np.vstack([pc['verts'] for pc in pieces])))
            ntris = sum(len(p['tris']) for p in pieces)
            assert ntris >= MIN_TRIS, (edid, limb, ntris)
            sig = (limb, digest(path))
            if sig not in by_sig:
                mesh = f'Bear_{limb}_{fid:03X}.nif'
                translation = tuple(tpl[base_t]['Translation'][k] for k in 'xyz')
                build_nif(os.path.join(WOLF, 'limbs', cont), pieces, translation, os.path.join(out_dir, mesh),
                          fit_hull=True)
                entry = dict(fid=f'{fid:06X}', limb=limb, mesh=MESH_REL + BS + mesh, ref_node=ref_bone, node=node,
                             translation=dict(zip('xyz', translation)), skins=[])
                by_sig[sig] = entry
                limbs.append(entry)
                print(f'    {limb}: {ntris} tris from {len(pieces) - 1} shapes + cap over {len(loops)} loop(s) of {[len(x) for x in loops]} -> {mesh}')
                fid += 1
            else:
                print(f'    {limb}: same as {by_sig[sig]["mesh"].split(BS)[-1]}')
            by_sig[sig]['skins'].append(dict(skin=f'{skin}:Skyrim.esm', race=race_edid))
    assert fid <= 0xFFF, 'ESL range exhausted'
    with open(PLAN, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(dict(arts=arts, limbs=limbs), fh, indent=2)
        fh.write('\n')
    print(f'{len(limbs)} bear limb meshes + {len(arts)} blood fx -> {out_dir}; plan -> {PLAN}.')


if __name__ == '__main__':
    main()
