"""Build the frostbite spider leg meshes for `Zenderal - Lost Ones Dismembering`, and the plan 01/02 read.

DF has no spider data. Enderal's spiders are the four vanilla FrostbiteSpider races (normal, Large, Hoher
on SkinFrostbiteSpider 03636F; Giant on 02C180). Both skins render
`Actors\\FrostbiteSpider\\Character Assets\\FrostbiteSpider.nif` (Spider SE's replacement in this list); the
winning skeleton (Creature Collision Fix) has the same leg chains as Spider SE's.
Each of the eight legs is a chain `Leg_<L|R>[n0]..[n4]` (n = 0..3, plus toes on some). A leg is cut at
`[n2]`, like DF's wolf legs at `Leg2`: the triangles dominated by `[n2]` and its descendants, moved into
`[n2]`'s bone space (limbmesh.cut_shape), go into DF's wolf front-leg nif (collision kept, wolf shapes
detached) skinned rigidly to `Root` with Translation 0, so Root IS the `[n2]` bone frame. The template
this writes into the plan therefore has Translation 0 and RefNode `Leg_<side>[n2]`.

Usage:  python 05-build-spider-limbs.py <pynifly io_scene_nifly dir> [<modlist root>]
"""
import importlib.util
import json
import os
import sys

PYN = sys.argv[1]
ROOT = sys.argv[2] if len(sys.argv) > 2 else 'E:/Zenderal'
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PYN)
sys.path.insert(0, HERE)
from pyn.pynifly import NifFile  # noqa: E402
from limbmesh import build_nif, cut_shape, descendants  # noqa: E402

spec = importlib.util.spec_from_file_location('m04', os.path.join(HERE, '04-build-minotaur-limbs.py'))
m04 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m04)             # for resolve()/enabled_mods(): mesh lookup through the MO2 mod order

BS = chr(92)
MODS = os.path.join(ROOT, 'mods')
OUT_MOD = os.path.join(MODS, 'Zenderal - Lost Ones Dismembering')
MESH_REL = BS.join(['DismemberingFramework', 'Zenderal', 'Spiders'])
PLAN = os.path.join(HERE, 'spider-limbs.json')
BODY = BS.join(['Actors', 'FrostbiteSpider', 'Character Assets', 'FrostbiteSpider.nif'])
SKELETON = BS.join(['Actors', 'FrostbiteSpider', 'Character Assets', 'skeleton.nif'])
RACES = ['FrostbiteSpiderRace', 'FrostbiteSpiderRaceLarge', 'FrostbiteSpiderRaceGiant', 'FrostbiteSpiderRaceHoher']
WOLF_DIR = os.path.join(MODS, 'DF - Official Creature Asset Pack', 'meshes', 'dismemberingframework',
                        'officialcreaturepack', 'wolf', 'limbs')
# DF wolf blood art object for the severed leg, and its front-leg actor-addon templates (body cap ARMO in
# slot 58, race-locked to the wolf races, so nothing renders on a spider; the spider skin is slots 30/32)
LIMB_ART = 'DF - Official Creature Pack.esp:0x8A4'
# Actor addons: the spider's own templates, written by 01 with ONLY the wolf front-leg blood art on the actor
# and NO ActorArmorAddon. Equipping DF's body-cap armor rebuilds the actor's 3D, and Spider SE's 25.8 MB
# body takes seconds to reload: the corpse vanished and reappeared (in game 2026-10-19). The cap would be
# invisible on a spider anyway (race-locked to wolves).
ADDON = {'L': 'Zenderal - Spider - Actor addons data - L', 'R': 'Zenderal - Spider - Actor addons data - R'}
ADDON_ART = {'L': 'DF - Official Creature Pack.esp:0x87E', 'R': 'DF - Official Creature Pack.esp:0x87F'}
# BipedSlot = the actor's body slot DF hides when the limb is cut (its own templates: 33 forearm gloves,
# 37 calf boots, 31 head). Left out (as in DF's wolf templates) it hid slot 30, and the spider's single
# body ARMA NakedFrostbiteSpiderAA covers Head(30)+Body(32): every dismembered spider vanished whole
# (reported in game 2026-10-19). 37 is free on a spider; DF's draugr calves already share one slot.
LEG_SLOT = 37
# Cut segment per leg pair. A 2026-10-19 experiment (pairs cut at [n2]/[n3]/[n4]/[n2]+CollisionNode)
# ruled out the bone collapse: the corpse blinked out for a few seconds and came back on every variant.
CUT = {n: (2, False) for n in range(4)}
FIRST_FID = 0x833      # after the minotaur limbs (0x805-0x832)
MIN_TRIS = 200


def main():
    mods = m04.enabled_mods()
    body_path = m04.resolve(BODY, mods)
    skel_path = m04.resolve(SKELETON, mods)
    print(f'body {body_path}\nskeleton {skel_path}')
    nif = NifFile(body_path)
    shapes = list(nif.shapes)

    out_dir = os.path.join(OUT_MOD, 'meshes', *MESH_REL.split(BS))
    if os.path.isdir(out_dir):
        for f in os.listdir(out_dir):
            os.remove(os.path.join(out_dir, f))
    os.makedirs(out_dir, exist_ok=True)

    plan, fid = [], FIRST_FID
    for side in ('L', 'R'):
        for n in range(4):
            seg, coll_node = CUT[n]
            bone = f'Leg_{side}[{n}{seg}]'
            bones = descendants(skel_path, bone)
            pieces = [pc for pc in (cut_shape(nif, s, bone, bones, shapes) for s in shapes) if pc]
            ntris = sum(len(p['tris']) for p in pieces)
            assert ntris >= MIN_TRIS, (bone, ntris)
            limb = f'Leg_{side}{n}'
            mesh = f'Spider_{limb}.nif'
            # fit_hull: the wolf leg's hull runs along Z across the joint; a spider leg runs ~72 units
            # along X, so the borrowed hull overlapped the body and Havok flung the corpse away.
            build_nif(os.path.join(WOLF_DIR, f'front_{side.lower()}_leg.nif'), pieces, (0.0, 0.0, 0.0),
                      os.path.join(out_dir, mesh), fit_hull=True)
            base_t = f'Zenderal - Spider - Base data - {limb}'
            plan.append(dict(fid=f'{fid:06X}', limb=limb, mesh=MESH_REL + BS + mesh, node=bone,
                             item_limb='Forearm_L' if side == 'L' else 'Forearm_R',
                             base_template=base_t,
                             base_data={'RefNode': bone, 'BipedSlot': LEG_SLOT, 'LimbArtObject': LIMB_ART,
                                        'Translation': {'x': 0.0, 'y': 0.0, 'z': 0.0},
                                        **({'CollisionNode': bone} if coll_node else {})},
                             addon_template=ADDON[side],
                             addon_data={'ActorArtObject': ADDON_ART[side]},
                             skins=[{'race': r, 'skin': 'ANY'} for r in RACES]))
            print(f'  {limb}: {ntris} tris from {len(pieces)} shapes ({sorted(bones)}) -> {mesh}')
            fid += 1
    with open(PLAN, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(plan, fh, indent=2)
        fh.write('\n')
    print(f'{len(plan)} spider legs -> {out_dir}; plan -> {PLAN}. Rebuild CRDW before testing.')


if __name__ == '__main__':
    main()
