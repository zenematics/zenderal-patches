"""Measure where each drinking clip closes the right hand, in the potion prop's frame (AnimObjectR).

tools/01 lifts every bottle so its body sits in the fist; the fist's height (GRIP_TOP there) comes from this. For each
clip: the skeleton's world matrices per frame, then the right hand's finger and thumb joints in AnimObjectR's frame,
over the middle 60% of the clip (the hold). Prints the median height (prop Z) of the finger joints with their 10th-90th
percentile spread, the thumb's median height, and the joints' median distance from the prop axis.

Clips: JellyFish Ultimate Animated Potions NG (OAR, priority 1, no conditions: it replaces UAPNG's standing and sneak
clips in both views) and UAPNG's own. Skeletons from Skyrim - Animations.bsa: JellyFish's third-person clips carry
156 tracks, and their first 99 are the vanilla skeleton's bones in order (bind translations match), so they are
measured on it.

Measured 2026-11-12: JellyFish fingers 10.2-10.8 (spread 7.5-13.1), thumb 12.1-12.3, in all four clips.
UAPNG's own: 1st person 4.3, 3rd-person walk/run -0.9 (never matched each other; JellyFish ships no walk/run clip).
Usage: python src/AnimatedPotionBottles/tools/00-measure-grip.py   (needs numpy)
"""
import importlib.util
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
TOOLS = json.load(open(os.path.join(ROOT, '.claude', 'config', 'tools.json'), encoding='utf-8-sig'))
sys.path.insert(0, os.path.join(TOOLS['pynifly'], 'hkx'))
sys.path.insert(0, TOOLS['pynifly'])
import anim_skyrim  # noqa: E402  (PyNifly, no Blender dependency)


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ADS = _load('ads', os.path.join(ROOT, 'src', 'FlintlockOverhaul', 'tools', '06-build-musket-aim-fix.py'))
ML = TOOLS['modlistRoot']
MODS = os.path.join(ML, 'mods')
SKELETONS = {'1p': 'meshes\\actors\\character\\_1stperson\\characterassets\\skeletonfirst.hkx',
             '3p': 'meshes\\actors\\character\\character assets\\skeleton.hkx'}
JF = 'JellyFish Ultimate Animated Potions NG/meshes/OpenAnimationReplacer/JFP/'
UAP = 'Ultimate Animated Potions NG/meshes/actors/character/'
CLIPS = [
    ('JellyFish 1P', '1p', JF + 'Base/actors/character/_1stperson/animations/NickNak/DrinkPotion_1st.hkx'),
    ('JellyFish 1P sneak', '1p', JF + 'Base/actors/character/_1stperson/animations/NickNak/DrinkPotion_1st_Sneak.hkx'),
    ('JellyFish 3P', '3p', JF + 'Base/actors/character/animations/NickNak/DrinkPotion.hkx'),
    ('JellyFish 3P sneak', '3p', JF + 'Sneak/actors/character/animations/NickNak/DrinkPotion.hkx'),
    ('UAPNG 1P', '1p', UAP + '_1stperson/animations/NickNak/DrinkPotion_1st.hkx'),
    ('UAPNG 3P', '3p', UAP + 'animations/NickNak/DrinkPotion.hkx'),
    ('UAPNG 3P walk', '3p', UAP + 'animations/NickNak/DrinkPotion_Walk.hkx'),
    ('UAPNG 3P run', '3p', UAP + 'animations/NickNak/DrinkPotion_Run.hkx'),
]
FINGERS = ['NPC R Finger%d%d' % (a, b) for a in range(1, 5) for b in range(3)]
THUMB = ['NPC R Finger0%d' % b for b in range(3)]


def bone(skel, name):
    for i, n in enumerate(skel.bones):
        if n == name or n.startswith(name + ' '):
            return i
    sys.exit('no bone %s' % name)


def world(skel, anim, f):
    out = [None] * len(skel.parents)
    for i, p in enumerate(skel.parents):
        t = anim.tracks[i]
        local = ADS.trs(t.translations[f], t.rotations[f], t.scales[f][0])
        out[i] = local if p < 0 else out[p] @ local
    return out


def main():
    bsa = ADS._bsa.listing(os.path.join(ML, 'Stock Game', 'Data', 'Skyrim - Animations.bsa'))
    tmp = os.path.join(os.environ.get('TEMP', '.'), '_potion_grip_skeleton.hkx')
    skels = {}
    for kind, key in SKELETONS.items():
        with open(tmp, 'wb') as fh:
            fh.write(ADS._bsa.read(bsa[0], bsa[1][key]))
        skels[kind] = anim_skyrim.load_skyrim_skeleton(tmp)
    os.remove(tmp)
    for label, kind, rel in CLIPS:
        path = os.path.join(MODS, *rel.split('/'))
        if not os.path.isfile(path):
            print('%-18s not installed' % label)
            continue
        skel = skels[kind]
        anim = anim_skyrim.load_skyrim_animation(path)
        if len(anim.tracks) < len(skel.parents):
            sys.exit('%s: %d tracks, skeleton %d bones' % (label, len(anim.tracks), len(skel.parents)))
        if len(anim.tracks) > len(skel.parents):
            # extra tracks after the vanilla bones: check the vanilla ones really are in vanilla order
            fing = [bone(skel, n) for n in FINGERS]
            err = max(np.linalg.norm(np.array(anim.tracks[i].translations[0]) - np.array(skel.reference_pose[i].translation))
                      for i in fing)
            if err > 0.05:   # Havok's quantised tracks: up to ~0.03 off the bind pose; a wrong bone order is units off
                sys.exit('%s: %d tracks do not follow the vanilla skeleton (finger offset %.3f)' % (label, len(anim.tracks), err))
        ao = bone(skel, 'AnimObjectR')
        fi = [bone(skel, n) for n in FINGERS]
        th = [bone(skel, n) for n in THUMB]
        n = len(anim.tracks[0].translations)
        pts, tps = [], []
        for f in range(int(n * 0.2), int(n * 0.8)):
            w = world(skel, anim, f)
            inv = np.linalg.inv(w[ao])
            pts += [(inv @ w[i])[:3, 3] for i in fi]
            tps += [(inv @ w[i])[:3, 3] for i in th]
        pts, tps = np.array(pts), np.array(tps)
        print('%-18s fingers z %6.2f (%.2f..%.2f), %.2f from the axis | thumb z %6.2f' % (
            label, np.median(pts[:, 2]), np.percentile(pts[:, 2], 10), np.percentile(pts[:, 2], 90),
            np.median(np.hypot(pts[:, 0], pts[:, 1])), np.median(tps[:, 2])))


if __name__ == '__main__':
    main()
