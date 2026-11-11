"""Rebuild `Zenderal - 1P Unarmed Stance Overlays`: OAR user.json files only, over the three UNTOUCHED first-person
unarmed sets that 00-install-sources.py installed (fpu_sources.SOURCES), plus the few clip copies in
fpu_sources.CLIP_MARKERS (First-Person Boxing's two jabs with one combo-window annotation each, so
src/FirstPersonFistCombo's left-click chain reaches F3), which go into Patch Collection (fpu_sources.CLIP_MARKERS_MOD).
Nothing else is copied or changed.

An OAR user.json beside a submod's config.json replaces its settings. Every submod folder of every set gets one:
  - used (fpu_sources 'use'): the author's config with the set's stance perk (and, for First-Person Boxing, which
    ships with no conditions, both hands unarmed) put in front of the author's own conditions; priority raised by
    'priority_add' where the set would otherwise lose to SIGMA (CFPAO ships priority 1-4);
  - not used (all of CFPAO but its three unarmed submods): disabled, with conditions that can never be true as a
    second lock. So CFPAO changes nothing else in first person.

SIGMA - Fisting animations - 1st person stays untouched as the no-stance set; it is below all three, so in a stance it
fills in every clip the stance's set lacks.

Usage:  python 01-build-overlays.py [<modlist root>] [<profile>]
"""
import copy
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'FHRFirstPerson', 'tools'))
import fpu_sources as fs  # noqa: E402
import hkx_annotate  # noqa: E402


def write_clip_markers(out_mod, report):
    """fpu_sources.CLIP_MARKERS: copies of the source clips with annotations added (hkx_annotate edits the binary;
    the compressed animation is untouched), at the same path in fs.CLIP_MARKERS_MOD (Patch Collection), which
    outranks the sources. Only these files are written there; nothing else in that mod is touched."""
    for key, rel, duration, new in fs.CLIP_MARKERS:
        src_oar = fs.find_ci(os.path.join(fs.MODS, fs.SOURCES[key]['mod']), fs.OAR_1P)
        src = fs.find_ci(src_oar, rel.split('/')) if src_oar else None
        if src is None:
            raise SystemExit(f'{fs.SOURCES[key]["mod"]}: {rel} not found')
        dur, have = hkx_annotate.read(src)
        if abs(dur - duration) > 0.01:
            raise SystemExit(f'{rel}: {dur:.3f} s, expected {duration} s (the author changed it? recheck the markers)')
        for t, text in new:
            if any(x.lower() == text.lower() for _t, x in have):
                raise SystemExit(f'{rel} already has {text}: drop the marker')
            if not 0 < t < dur:
                raise SystemExit(f'{rel}: marker {text} at {t} s outside the clip')
        dst = os.path.join(out_mod, *fs.OAR_1P, *os.path.relpath(src, src_oar).split(os.sep))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        hkx_annotate.annotate(src, dst, new)
        report.append(f'marked copy: {rel} + ' + ', '.join(f'{x} @{t}' for t, x in new))


def main():
    out_mod = os.path.join(fs.MODS, fs.OVERLAY_MOD)
    if os.path.isdir(out_mod):
        shutil.rmtree(out_mod)
    report, written = [], 0
    for key, src in fs.SOURCES.items():
        oar = fs.find_ci(os.path.join(fs.MODS, src['mod']), fs.OAR_1P)
        if oar is None:
            raise SystemExit(f'{src["mod"]} is not installed (run 00-install-sources.py)')
        subs = fs.submods(oar)
        by_lower = {rel.lower(): rel for rel in subs}
        used = []
        for want in src['use']:
            if want.lower() not in by_lower:
                raise SystemExit(f'{src["mod"]}: submod {want} not found (author changed the layout?)')
            used.append(by_lower[want.lower()])
        for rel, (_dp, cfg) in sorted(subs.items()):
            user = copy.deepcopy(cfg)
            if rel in used:
                conds = [fs.has_perk(src['stance'])] + (copy.deepcopy(fs.FISTS) if src['fists'] else [])
                user.update({'priority': cfg['priority'] + src['priority_add'], 'disabled': False,
                             'conditions': conds + cfg.get('conditions', [])})
            else:
                user.update({'disabled': True, 'conditions': copy.deepcopy(fs.NEVER)})
            path = os.path.join(out_mod, *fs.OAR_1P, *rel.split('/'), 'user.json')
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8', newline='\n') as fh:
                json.dump(user, fh, indent=4)
                fh.write('\n')
            written += 1
        report.append(f'{src["stance"]:<4} (perk {fs.PERKS[src["stance"]]}): {src["mod"]} - on: '
                      + ', '.join(f'{r} (priority {subs[r][1]["priority"] + src["priority_add"]})' for r in used)
                      + f'; disabled: {len(subs) - len(used)}')
    write_clip_markers(os.path.join(fs.MODS, fs.CLIP_MARKERS_MOD), report)
    with open(os.path.join(out_mod, 'meta.ini'), 'w', encoding='utf-8', newline='\r\n') as fh:
        fh.write('[General]\ngameName=SkyrimSE\nversion=1.0\nnotes=Generated by src/FirstPersonUnarmedStances/tools/'
                 '01-build-overlays.py: OAR user.json overlays only\n')
    print('\n'.join(report))
    print(f'{written} user.json files -> {out_mod}')


if __name__ == '__main__':
    main()
