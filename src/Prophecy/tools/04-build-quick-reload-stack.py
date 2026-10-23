"""Build the `Zenderal - Quick Reload Stack` MO2 mod: Quick Reload (Prophecy, 000815) and Enderal's own Rapid
Shot (_00E_Class_Trickster_P05_B_RapidShot 069CD5:Skyrim.esm) stack on crossbow/musket reloads.

Why a clip mod (graph read 2026-10-22, see arch-docs/patches/Prophecy.md): both perks set the same graph flag,
bPerkQuickDraw, which picks the reload clip generator at playbackSpeed 1.3. One flag cannot count to two, so
holding both perks used to reload exactly as fast as holding one. The flag also picks the faster bow draw
and crossbow release, so it stays on both perks.

What this does: an OAR submod conditioned on HasPerk Quick Reload AND HasPerk Rapid Shot swaps in copies of
the reload clips that would otherwise play, retimed STACK_FACTOR shorter. The graph still plays them at its
1.3, so both perks give 1.3 * STACK_FACTOR; either perk alone is unchanged. Retiming scales duration, frame
and block durations and annotation times; poses are untouched. The graph's own triggers are safe: reloadStop
is relative to the end of the clip (-0.195 s) and Reload/ReloadFast fire at its start (1hm_behavior, 1st and
3rd person).

Sources, per slot: the clip that would win without us. Loose files in the active MO2 profile's mod order, then
Skyrim - Animations.bsa. First-person musket reloads come from DAR Rifles' 432101 folder (the set the _KID.ini
gives Ordo's muskets, keyword DAR Rifles.esp 0x800) when it has one, in a higher-priority submod that also
requires that keyword. OAR/DAR folders other than 432101 are never sources. Nothing third-party is committed:
the clips are written straight into the MO2 mods folder.

Usage:  python -I src/Prophecy/tools/04-build-quick-reload-stack.py [<modlist root>]   (default: tools.json)
"""
import importlib.util
import json
import math
import os
import re
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
TOOLS = json.load(open(os.path.join(ROOT, '.claude', 'config', 'tools.json'), encoding='utf-8-sig'))
sys.path.insert(0, os.path.join(TOOLS['pynifly'], 'hkx'))
import anim_skyrim  # noqa: E402  (PyNifly, no Blender dependency)

_spec = importlib.util.spec_from_file_location('_bsa', os.path.join(os.path.dirname(__file__), '_bsa.py'))
_bsa = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bsa)

STACK_FACTOR = 1.3  # extra speed when both perks are held (each alone: the graph's 1.3)
MOD = 'Zenderal - Quick Reload Stack'
PRIORITY_ALL = 432300     # above DAR Rifles' 432101-432103 and the Musket Aim Fix's 432200
PRIORITY_MUSKET = 432301
CLIPS = ['crossbow_reload.hkx', 'sneakcrossbow_reload.hkx',
         'crossbow_reloaddwarven.hkx', 'sneakcrossbow_reloaddwarven.hkx']
PERSONS = {  # person -> path under meshes/actors/character
    '3rd': ['animations'],
    '1st': ['_1stperson', 'animations'],
}
DAR_MUSKET = ['DynamicAnimationReplacer', '_CustomConditions', '432101', 'dlc01']
BOTH_PERKS = [
    {'condition': 'HasPerk', 'requiredVersion': '1.0.0.0',
     'Perk': {'pluginName': 'Zenderal - Prophecy.esp', 'formID': '815'}},       # ZP_Prophecy_QuickReload
    {'condition': 'HasPerk', 'requiredVersion': '1.0.0.0',
     'Perk': {'pluginName': 'Skyrim.esm', 'formID': '69CD5'}},                   # Rapid Shot
]
MUSKET = {'condition': 'IsEquippedHasKeyword', 'requiredVersion': '1.0.0.0',
          'Keyword': {'form': {'pluginName': 'DAR Rifles.esp', 'formID': '800'}}, 'Left hand': False}


def profile_mods(root):
    """Enabled mods, highest MO2 priority first (modlist.txt order), for the selected profile."""
    ini = open(os.path.join(root, 'ModOrganizer.ini'), encoding='utf-8', errors='replace').read()
    m = re.search(r'^selected_profile=@ByteArray\((.+)\)\s*$', ini, re.M)
    if not m:
        sys.exit('no selected_profile in ModOrganizer.ini')
    profile = m.group(1)
    lines = open(os.path.join(root, 'profiles', profile, 'modlist.txt'), encoding='utf-8').read().splitlines()
    return profile, [l[1:] for l in lines if l.startswith('+')]


def find_ci(base, parts):
    """Case-insensitive path walk (mods mix Meshes/meshes). Returns the real path or None."""
    cur = base
    for part in parts:
        if not os.path.isdir(cur):
            return None
        hit = [e for e in os.listdir(cur) if e.lower() == part.lower()]
        if not hit:
            return None
        cur = os.path.join(cur, hit[0])
    return cur


def winner(mods_dir, mods, bsa, rel_parts):
    """(label, bytes) of the loose file that wins rel_parts, else the BSA copy."""
    for mod in mods:
        p = find_ci(os.path.join(mods_dir, mod), rel_parts)
        if p and os.path.isfile(p):
            return mod, open(p, 'rb').read()
    key = '\\'.join(rel_parts).lower()
    data, listing = bsa
    if key not in listing:
        sys.exit('no source for %s' % key)
    return 'Skyrim - Animations.bsa', _bsa.read(data, listing[key])


def retime(src_bytes, tmp):
    with open(tmp, 'wb') as fh:
        fh.write(src_bytes)
    anim = anim_skyrim.load_skyrim_animation(tmp)
    before = (anim.duration, anim.num_frames, [(a.time, a.text) for a in anim.annotations])
    for tr in anim.tracks:
        for seq in (tr.translations, tr.rotations, tr.scales):
            if any(math.isnan(x) for v in seq for x in v):
                sys.exit('NaN in a source track - handle it before retiming')
    anim.duration /= STACK_FACTOR
    anim.frame_duration = anim.duration / max(1, anim.num_frames - 1)
    anim.num_blocks = 0
    anim.block_duration = 0
    for a in anim.annotations:
        a.time /= STACK_FACTOR
    return anim, before


def check(out, before, src_anim_path):
    got = anim_skyrim.load_skyrim_animation(out)
    src = anim_skyrim.load_skyrim_animation(src_anim_path)
    dur, frames, anns = before
    assert abs(got.duration - dur / STACK_FACTOR) < 1e-3, (got.duration, dur)
    assert got.num_frames == frames, (got.num_frames, frames)
    assert [a.text for a in got.annotations] == [t for _, t in anns], 'annotations changed'
    for a, (t, _) in zip(got.annotations, anns):
        assert abs(a.time - t / STACK_FACTOR) < 1e-3, (a.time, t)
    worst = 0.0
    for ta, tb in zip(got.tracks, src.tracks):
        for qa, qb in zip(ta.rotations, tb.rotations):
            dot = min(1.0, abs(sum(x * y for x, y in zip(qa, qb))))
            worst = max(worst, math.degrees(2 * math.acos(dot)))
    if worst > 1.0:
        sys.exit('%s: pose drift %.2f deg after re-encode' % (out, worst))
    return got, worst


def write_config(path, cfg):
    with open(os.path.join(path, 'config.json'), 'w', encoding='utf-8') as fh:
        json.dump(cfg, fh, indent=4)


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else TOOLS['modlistRoot']
    mods_dir = os.path.join(root, 'mods')
    profile, mods = profile_mods(root)
    bsa = _bsa.listing(os.path.join(root, 'Stock Game', 'Data', 'Skyrim - Animations.bsa'))
    if 'DAR Rifles Standalone' not in mods:
        sys.exit('DAR Rifles Standalone is not enabled in %s - the musket submod would be wrong' % profile)
    out_mod = os.path.join(mods_dir, MOD)
    if os.path.isdir(out_mod):
        shutil.rmtree(out_mod)
    tmp = os.path.join(os.environ.get('TEMP', '.'), '_qrs_src.hkx')
    written = 0
    for person, sub in PERSONS.items():
        anims = ['meshes', 'actors', 'character'] + sub
        oar = os.path.join(out_mod, *anims, 'OpenAnimationReplacer', MOD)
        submods = {'Both perks %s person' % person: (PRIORITY_ALL, BOTH_PERKS, {})}
        dar = find_ci(os.path.join(mods_dir, 'DAR Rifles Standalone'), anims + DAR_MUSKET)
        musket = {c: os.path.join(dar, c) for c in CLIPS if dar and os.path.isfile(os.path.join(dar, c))}
        if musket:
            submods['Both perks %s person, musket' % person] = (PRIORITY_MUSKET, BOTH_PERKS + [MUSKET], musket)
        for name, (prio, conds, override) in submods.items():
            sub_dir = os.path.join(oar, name)
            os.makedirs(os.path.join(sub_dir, 'dlc01'))
            sources = []
            for clip in CLIPS:
                if clip in override:
                    label, data = 'DAR Rifles 432101', open(override[clip], 'rb').read()
                else:
                    label, data = winner(mods_dir, mods, bsa, anims + ['dlc01', clip])
                anim, before = retime(data, tmp)
                out = os.path.join(sub_dir, 'dlc01', clip)
                anim_skyrim.write_skyrim_animation(out, anim, ptr_size=8)
                got, drift = check(out, before, tmp)
                os.remove(tmp)
                print('%-3s %-28s %-36s %.3f s -> %.3f s, %d frames, %d annotations, drift %.2f deg'
                      % (person, clip, label, before[0], got.duration, got.num_frames, len(got.annotations), drift))
                sources.append('%s <- %s' % (clip, label))
                written += 1
            write_config(sub_dir, {
                'name': name,
                'description': 'Quick Reload + Rapid Shot: reloads %.2fx shorter on top of the graph\'s 1.3. %s'
                               % (STACK_FACTOR, '; '.join(sources)),
                'priority': prio,
                'conditions': conds,
            })
        write_config(oar, {
            'name': MOD, 'author': 'Zenderal',
            'description': 'Quick Reload (Prophecy) and Rapid Shot stack on crossbow and musket reloads.',
        })
    print('built %s for profile %s: %d clips (factor %.2f; both perks %.2fx total)'
          % (out_mod, profile, written, STACK_FACTOR, 1.3 * STACK_FACTOR))


if __name__ == '__main__':
    main()
