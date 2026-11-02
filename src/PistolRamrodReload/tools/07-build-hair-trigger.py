"""Hair Trigger's reloads: a faster twin of every reload submod, third and first person.

Prophecy's Hair Trigger (`ZP_Prophecy_HairTrigger` 0xB12) says "You reload pistols in 1.2 seconds instead of 2". Until
2026-11-02 the Flintlock script skipped the reload animation for it and loaded the gun by a 1.2 s timer, so with the
pistol branch (Hair Trigger is its root) a gun refilled itself after every shot (curator: "all reloading requires were
removed and I could spam shots"). Now the reload stays on the fire button and animated, at SPEED: the one-gun reload
(2.11 s) in 1.2 s, the two-pistol and melee ones (3.40 s) in 1.94 s. Fan the Hammer's power keeps reloading at once
while it lasts (its text; the Flintlock script's timer).

Each submod `Reload ...` (tools/01's third-person ones, tools/04's first-person ones) gets a twin `Reload ... (hair
trigger)`: the same conditions with the negated Hair Trigger perk turned round, the priority + PRIORITY_STEP, the other
files copied, and the reload clip played faster: frame duration and annotations / SPEED, except the loading sounds after
the first, which keep their gap to it (tools/01 SOUNDS: a sound is no shorter when the clip is). The pose data and the
float tracks are the source clip's. ZP_PistolReloadArmScript hands the arms back SPEED times sooner with the perk.

tools/01 and tools/04 rebuild their folders from scratch: run this after them (06 -> 01 -> 04 -> 07 -> 02).
Usage:  python src/PistolRamrodReload/tools/07-build-hair-trigger.py [<modlist root>]
"""
import importlib.util
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


PR = _load('pistol_reload', os.path.join(HERE, '01-build-pistol-reload.py'))
P1 = _load('pistol_reload_1p', os.path.join(HERE, '04-build-pistol-reload-1p.py'))
ADS, anim_skyrim = PR.ADS, PR.anim_skyrim
SPEED = 1.75                 # ZP_PistolReloadArmScript.HAIR_TRIGGER_SPEED: the 2.11 s reload in 1.2 s
SUFFIX = ' (hair trigger)'
PRIORITY_STEP = 500          # inside each family's block of 1000 (tools/01 PRIORITY_*: + group index)
CLIPS = (PR.CLIP, PR.CLIP_RIGHT)


def flip_perk(conditions):
    """The conditions with the negated Hair Trigger perk required instead; exactly one such condition."""
    out, found = [], 0
    for c in conditions:
        c = dict(c)
        perk = c.get('Perk') or {}
        if c.get('condition') == 'HasPerk' and perk.get('pluginName') == PR.PROPHECY_ESP and \
                perk.get('formID') == PR.HAIR_TRIGGER and c.get('negated'):
            del c['negated']
            found += 1
        out.append(c)
    if found != 1:
        sys.exit('%d negated Hair Trigger conditions, expected 1' % found)
    return out


def faster(src, dst):
    """The reload clip `src` written to `dst` SPEED times faster; returns (old, new duration)."""
    floats = PR.HF.read_file(src)
    anim = anim_skyrim.load_skyrim_animation(src)
    old = anim.duration
    anim.frame_duration /= SPEED
    anim.duration = (anim.num_frames - 1) * anim.frame_duration
    sounds = ['SoundPlay.' + e for e, _ in PR.SOUNDS]
    first = min((a.time for a in anim.annotations if a.text == sounds[0]), default=None)
    for a in anim.annotations:
        t = a.time / SPEED
        if a.text in sounds[1:] and first is not None:
            t = first / SPEED + (a.time - first)
        if t > anim.duration + 1e-4:
            sys.exit('%s: %s at %.3f s is past the faster clip\'s end (%.3f s)' % (src, a.text, t, anim.duration))
        a.time = round(t, 4)
    PR.write_clip(dst, ADS.havok_blocks(anim), floats, reference=True)
    ADS.check_blocks(dst)
    got = anim_skyrim.load_skyrim_animation(dst)
    if abs(got.duration - anim.duration) > 1e-3 or got.num_frames != anim.num_frames:
        sys.exit('%s: wrote %.3f s / %d frames, meant %.3f / %d' % (dst, got.duration, got.num_frames, anim.duration,
                                                                    anim.num_frames))
    return old, got.duration


def twin(oar, name):
    src = os.path.join(oar, name)
    dst = os.path.join(oar, name + SUFFIX)
    os.makedirs(dst)
    cfg = json.load(open(os.path.join(src, 'config.json'), encoding='utf-8'))
    cfg['name'] = name + SUFFIX
    cfg['description'] = 'With Prophecy\'s Hair Trigger, %.2fx faster (tools/07). %s' % (SPEED, cfg['description'])
    cfg['priority'] = cfg['priority'] + PRIORITY_STEP
    cfg['conditions'] = flip_perk(cfg['conditions'])
    done = None
    for f in sorted(os.listdir(src)):
        if f == 'config.json':
            continue
        if f.lower() in CLIPS:
            done = faster(os.path.join(src, f), os.path.join(dst, f))
        else:
            shutil.copyfile(os.path.join(src, f), os.path.join(dst, f))
    if not done:
        sys.exit('%s has no reload clip (%s)' % (src, ' / '.join(CLIPS)))
    ADS.write_config(dst, cfg)
    return done


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else ADS.TOOLS['modlistRoot']
    mod = os.path.join(root, 'mods', PR.MOD)
    for view, parts in (('third person', PR.OAR), ('first person', P1.OAR_1P)):
        oar = os.path.join(mod, *parts)
        if not os.path.isdir(oar):
            sys.exit('%s is missing: run tools/01 and tools/04 first' % oar)
        for d in os.listdir(oar):
            if d.endswith(SUFFIX):
                shutil.rmtree(os.path.join(oar, d))
        subs = sorted(d for d in os.listdir(oar) if d.startswith('Reload ') and os.path.isdir(os.path.join(oar, d)))
        lengths = {}
        for name in subs:
            old, new = twin(oar, name)
            lengths.setdefault((round(old, 2), round(new, 2)), []).append(name)
        print('%s: %d Hair Trigger twins in %s' % (view, len(subs), oar))
        for (old, new), names in sorted(lengths.items()):
            print('   %.2f s -> %.2f s: %d clips' % (old, new, len(names)))


if __name__ == '__main__':
    main()
