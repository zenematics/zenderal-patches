"""Rebuild the `Zenderal - Musket Aim Fix` MO2 mod: a first-person OAR submod that gives DAR Rifles'
bolt-action set (the one the _KID.ini puts on Ordo's 14 muskets, see 05-dar-rifles.py) a raise
(CrossBow_Aim) clip that ends on DAR's own aimed-hold pose.

First-person crossbow sequence (OAR animation log 2026-10-14): CrossBow_IdleHeld (hip, vanilla - DAR has
none in first person) -> CrossBow_Aim (the RAISE) -> CrossBow_IdleDrawn (the aimed HOLD, DAR 432101) ->
CrossBow_Release (DAR). DAR's first-person 432101/432102 ship no CrossBow_Aim, so vanilla's plays: a 0.2 s,
7-frame raise that ends with the right arm ~100 deg, the right hand ~150 deg and the Weapon bone 18 units
away from DAR's hold pose. The graph closes that gap in a quick blend at the moment the musket is ready -
the "jarring skip" (first person only; third-person 432101 has its own matching aim).
  v1 shipped the clips DAR parked in `432102/dlc01/New folder` - byte-identical to VANILLA crossbow_aim, so
     nothing changed.
  v2 used DAR's hold clip as the raise - the gap just moved into the state blend at the start.
  v3 synthesised a 0.5 s raise - in game it played slower, then still jumped: the first-person 1hm_behavior
     clip generator `CrossBow Aim` carries a TRIGGER (not an annotation) `bowDrawn` at absolute local time
     0.200 s, and CrossBowDrawing -> CrossBow_IdleDrawn fires on bowDrawn with fastBlendTransition. So the
     raise is cut at 0.2 s whatever its length, and its 0.2 s pose must already BE the hold pose.
  v4 (this): the same synthesis over exactly BOW_DRAWN_AT: vanilla's raise frame 0 (~ the vanilla hip pose)
     eased into DAR's hold frame 0, per bone (slerp rotations, lerp translation/scale, smoothstep), keeping
     vanilla's annotations (the aim sound). A slower raise needs a behaviour patch moving that trigger,
     which would also delay when every first-person crossbow can fire.

Inputs: vanilla clips from the user's `Skyrim - Animations.bsa`, DAR's hold clips from its install; HKX
read/write via PyNifly's anim_skyrim (`pynifly` in tools.json). Nothing third-party is committed.

Usage:  python -I 06-build-musket-aim-fix.py [<mods dir>]     (default <modlistRoot>/mods)
"""
import os, sys, json, math, shutil
import importlib.util

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
TOOLS = json.load(open(os.path.join(ROOT, '.claude', 'config', 'tools.json'), encoding='utf-8-sig'))
sys.path.insert(0, os.path.join(TOOLS['pynifly'], 'hkx'))
import anim_skyrim  # noqa: E402  (PyNifly, no Blender dependency)

_spec = importlib.util.spec_from_file_location(
    'restores', os.path.join(ROOT, 'src', 'EnderalTextureRestores', 'tools', '01-extract-enderal-textures.py'))
_restores = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_restores)
read_from_bsa = _restores.read_from_bsa

MOD = 'Zenderal - Musket Aim Fix'
DAR = ['DAR Rifles Standalone', 'meshes', 'actors', 'character', '_1stperson', 'animations',
       'DynamicAnimationReplacer', '_CustomConditions', '432101', 'dlc01']
VANILLA = 'meshes\\actors\\character\\_1stperson\\animations\\dlc01\\'
OAR = ['meshes', 'actors', 'character', '_1stperson', 'animations', 'OpenAnimationReplacer', MOD]
SUBMOD = 'Bolt-action aim 1st person'
# published raise clip -> DAR 2022 aimed-hold clip it must end on. The vanilla clip of the same name
# supplies the start pose and the annotations.
CLIPS = {
    'crossbow_aim.hkx': 'crossbow_idledrawn.hkx',
    'crossbow_aimdwarven.hkx': 'crossbow_idledrawndwarven.hkx',
    'sneakcrossbow_aim.hkx': 'sneakcrossbow_idledrawn.hkx',
    'sneakcrossbow_aimdwarven.hkx': 'sneakcrossbow_idledrawndwarven.hkx',
}
BOW_DRAWN_AT = 0.2  # 1st-person 1hm_behavior: `CrossBow Aim` (and Sneak/Dwarven) trigger bowDrawn@0.200
RAISE_SECONDS = BOW_DRAWN_AT  # longer is cut off at bowDrawn and snaps (v3)
FPS = 30
PRIORITY = 432200  # above DAR Rifles' 432101-432103

MOD_CONFIG = {
    'name': MOD,
    'author': 'Zenderal',
    'description': "First-person raise clips for DAR Rifles' bolt-action set that end on DAR's own aimed "
                   'hold, so muskets no longer snap between the raise and the hold.',
}
SUBMOD_CONFIG = {
    'name': SUBMOD,
    'description': "Right hand has WeapTypeRifleBoltAction: %.1f s raise easing into DAR Rifles' 2022 "
                   'aimed-hold pose.' % RAISE_SECONDS,
    'priority': PRIORITY,
    'conditions': [
        {'condition': 'IsEquippedHasKeyword', 'requiredVersion': '1.0.0.0',
         'Keyword': {'form': {'pluginName': 'DAR Rifles.esp', 'formID': '800'}}, 'Left hand': False},
    ],
}


def slerp(a, b, t):
    d = sum(x * y for x, y in zip(a, b))
    if d < 0:
        b, d = [-x for x in b], -d
    if d > 0.9995:
        q = [x + (y - x) * t for x, y in zip(a, b)]
    else:
        th = math.acos(d)
        s = math.sin(th)
        wa, wb = math.sin((1 - t) * th) / s, math.sin(t * th) / s
        q = [wa * x + wb * y for x, y in zip(a, b)]
    n = math.sqrt(sum(x * x for x in q))
    return [x / n for x in q]


def lerp(a, b, t):
    return [x + (y - x) * t for x, y in zip(a, b)]


def build_raise(start, end):
    """start: vanilla raise (frame 0 used), end: DAR hold (frame 0 used). Returns a new AnimationData."""
    if len(start.tracks) != len(end.tracks):
        sys.exit('track count mismatch %d vs %d' % (len(start.tracks), len(end.tracks)))
    n = int(round(RAISE_SECONDS * FPS)) + 1
    for i, (tr_s, tr_e) in enumerate(zip(start.tracks, end.tracks)):
        b = (tr_e.translations[0], tr_e.rotations[0], tr_e.scales[0])
        # PyNifly decodes one track of vanilla sneakcrossbow_aim (41) with NaN translation/scale: start
        # that component from the hold value instead.
        a = tuple(bv if any(math.isnan(x) for x in av) else av
                  for av, bv in zip((tr_s.translations[0], tr_s.rotations[0], tr_s.scales[0]), b))
        if a != (tr_s.translations[0], tr_s.rotations[0], tr_s.scales[0]):
            print('  track %d: NaN in the vanilla start pose, started from the hold value' % i)
        tr_s.translations, tr_s.rotations, tr_s.scales = [], [], []
        for f in range(n):
            u = f / (n - 1)
            w = u * u * (3 - 2 * u)  # smoothstep: no velocity jump at either end
            tr_s.translations.append(lerp(a[0], b[0], w))
            tr_s.rotations.append(slerp(a[1], b[1], w))
            tr_s.scales.append(lerp(a[2], b[2], w))
    start.duration = RAISE_SECONDS
    start.num_frames = n
    start.frame_duration = 1.0 / FPS
    start.num_blocks = 0
    start.block_duration = 0
    return start


def max_gap(a, fa, b, fb):
    return max(math.degrees(2 * math.acos(min(1.0, abs(sum(x * y for x, y in zip(ta.rotations[fa], tb.rotations[fb]))))))
               for ta, tb in zip(a.tracks, b.tracks))


def main():
    mods = sys.argv[1] if len(sys.argv) > 1 else os.path.join(TOOLS['modlistRoot'], 'mods')
    bsa = os.path.join(os.path.dirname(mods.rstrip('/\\')), 'Stock Game', 'Data', 'Skyrim - Animations.bsa')
    dar = os.path.join(mods, *DAR)
    mod_dir = os.path.join(mods, MOD, *OAR)
    sub = os.path.join(mod_dir, SUBMOD)
    if os.path.isdir(os.path.join(mods, MOD)):
        shutil.rmtree(os.path.join(mods, MOD))
    os.makedirs(os.path.join(sub, 'dlc01'))
    tmp = os.path.join(sub, 'dlc01', '_vanilla.tmp')
    for dest, hold_name in CLIPS.items():
        with open(tmp, 'wb') as fh:
            fh.write(read_from_bsa(bsa, VANILLA + dest))
        vanilla = anim_skyrim.load_skyrim_animation(tmp)
        os.remove(tmp)
        hold_path = os.path.join(dar, hold_name)
        if not os.path.isfile(hold_path):
            sys.exit('missing %s - DAR Rifles Standalone layout changed' % hold_path)
        hold = anim_skyrim.load_skyrim_animation(hold_path)
        start_gap = max_gap(anim_skyrim.load_skyrim_animation(hold_path), 0, vanilla, -1)
        out = os.path.join(sub, 'dlc01', dest)
        anim_skyrim.write_skyrim_animation(out, build_raise(vanilla, hold), ptr_size=8)
        check = anim_skyrim.load_skyrim_animation(out)
        end_gap = max_gap(check, -1, hold, 0)
        if end_gap > 2.0:
            sys.exit('%s: raise ends %.1f deg off the hold pose' % (dest, end_gap))
        print('%-30s %.2f s, %d frames; hand-off gap %.1f deg -> %.1f deg; %s'
              % (dest, check.duration, check.num_frames, start_gap, end_gap, [a.text for a in check.annotations]))
    with open(os.path.join(mod_dir, 'config.json'), 'w', encoding='utf-8') as fh:
        json.dump(MOD_CONFIG, fh, indent=4)
    with open(os.path.join(sub, 'config.json'), 'w', encoding='utf-8') as fh:
        json.dump(SUBMOD_CONFIG, fh, indent=4)
    n = len(os.listdir(os.path.join(sub, 'dlc01')))
    if n != len(CLIPS):
        sys.exit('expected %d clips, wrote %d' % (len(CLIPS), n))
    print('built %s: %d clips, priority %d' % (os.path.join(mods, MOD), n, PRIORITY))


if __name__ == '__main__':
    main()
