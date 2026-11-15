"""Clockwork Thunder's own reload sounds (curator 2026-11-15: "add these to the reload, decide how they're paced
based on the animation movement"): the curator's licensed Motion Array MA_Designed_SciFiWeaponsReload_1/_2.wav.

The rifle shares OL_Musket_Rifle's ramrod reload (src/FlintlockOverhaul tools/09-12, MO2 mod Zenderal - Musket
Ramrod Reload; tools/03 here added Clockwork Thunder to its conditions). Its reload clip carries, per Zodd's
movement (normal speed, 4.43 s): handling click 0.17, ball drawn 0.84, ball into the muzzle 1.71 (the ball's
AnimObjectUnequip, with SoundPlay.ZEN_MusketLoad7), ramrod drawn 2.22, rod stowed 2.96 (the last AnimObjectUnequip;
ZEN_MusketLoad1 at 2.91), back on aim 4.43. The two sounds are short two-hit designed reloads (Reload_1 0.8 s, hits
at 0.15/0.35 s; Reload_2 0.6 s, hits at 0.10/0.25 s), so:

  ZP_CTReload1 (80D)  its first hit on the ball going into the muzzle - the loading action
  ZP_CTReload2 (80E)  its first hit on the ramrod being stowed - the closing action
  (asserted: Reload_1 has died away before Reload_2 starts, in every clip)

For this gun only, the rifle's reload submods are copied (third person standard/sneak, the *both reload perks*
faster copies, first person and its faster copy), reload clips only, each keyed on IsEquipped(Clockwork Thunder)
alone at the original priority + PRIORITY_UP, into Patch Collection. In the copies the two musket loading-sound
annotations are edited in place (no size changes): text -> SoundPlay.ZP_CTReload1/2 (shorter, NUL-padded), time ->
the beat minus the sound's first hit (the faster copies scale the beats, not the sounds). Zodd's own
SoundPlay.WPNCrossbowReload handling clicks stay. The wavs (16-bit mono, 48 kHz) go to
sound/fx/Zenderal/ClockworkThunder/ZP_CTReload1/2.wav; not committed.

Usage:  python src/ClockworkThunder/tools/05-build-reload-sounds.py <Reload_1.wav> <Reload_2.wav>
"""
import argparse
import array
import importlib.util
import json
import os
import shutil
import struct

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
TOOLS = json.load(open(os.path.join(ROOT, '.claude', 'config', 'tools.json'), encoding='utf-8-sig'))
MODS = os.path.join(TOOLS['modlistRoot'], 'mods')
RAMROD = os.path.join(MODS, 'Zenderal - Musket Ramrod Reload')
TARGET = os.path.join(MODS, 'Zenderal - Patch Collection')
OAR_MOD = 'Zenderal - Clockwork Thunder Reload'
SUBMODS = [('animations', 'Ramrod ol_musket_rifle'), ('animations', 'Ramrod ol_musket_rifle, both reload perks'),
           ('_1stperson/animations', 'Ramrod 1P ol_musket_rifle'),
           ('_1stperson/animations', 'Ramrod 1P ol_musket_rifle, both reload perks')]
CLIPS = ('crossbow_reload.hkx', 'crossbow_reloaddwarven.hkx', 'sneakcrossbow_reload.hkx',
         'sneakcrossbow_reloaddwarven.hkx')
GUN = {'pluginName': 'Zenderal - Clockwork Thunder.esp', 'formID': '800'}
PRIORITY_UP = 200000
SOUNDS = [('ZP_CTReload1', 'SoundPlay.ZEN_MusketLoad7', 'ball'), ('ZP_CTReload2', 'SoundPlay.ZEN_MusketLoad1', 'rod')]
WAV_DIR = 'sound/fx/Zenderal/ClockworkThunder'
RATE = 48000
GAIN = 0.85    # curator 2026-11-15: "lower the reload sounds by 15%" (amplitude x0.85, about -1.4 dB)

_s = importlib.util.spec_from_file_location('_ha', os.path.join(ROOT, 'src', 'FHRFirstPerson', 'tools', 'hkx_annotate.py'))
ha = importlib.util.module_from_spec(_s)
_s.loader.exec_module(ha)
_s = importlib.util.spec_from_file_location('_rs', os.path.join(ROOT, 'src', 'ReversalShadow', 'tools', '01-build-assets.py'))
rs = importlib.util.module_from_spec(_s)
_s.loader.exec_module(rs)


def install_wav(src, dst, gain=GAIN):
    """16-bit mono at RATE (a positional sound); returns (seconds, first-hit seconds, audible seconds)."""
    fmt, x = rs.read_pcm(src)
    ch, rate = fmt[1], fmt[2]
    mono = array.array('h', (int(sum(x[i:i + ch]) / ch) for i in range(0, len(x) - len(x) % ch, ch)))
    mono = rs.resample(mono, 1, rate, RATE)
    peak = max(1, max(abs(v) for v in mono))
    scale = min(1.0, 32000 / peak) * gain
    mono = array.array('h', (int(round(v * scale)) for v in mono))
    data = mono.tobytes()
    head = (b'RIFF' + struct.pack('<I', 36 + len(data)) + b'WAVE' + b'fmt ' +
            struct.pack('<IHHIIHH', 16, 1, 1, RATE, RATE * 2, 2, 16) + b'data' + struct.pack('<I', len(data)))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, 'wb').write(head + data)
    # loudness per 50 ms: the first window within 6 dB of the loudest = the first hit; audible = within 30 dB
    win = RATE // 20
    env = [max(1e-9, (sum(v * v for v in mono[i:i + win]) / win) ** 0.5) for i in range(0, len(mono) - win, win)]
    top = max(env)
    first = next(i for i, e in enumerate(env) if e >= top / 2) * 0.05
    audible = (max(i for i, e in enumerate(env) if e >= top / 31.6) + 1) * 0.05
    return len(mono) / RATE, first, audible


def retime(src, dst, edits):
    """edits: {old text: (new text, new time)}; in place, no sizes change."""
    with open(src, 'rb') as fh:
        pf = ha.Packfile(fh.read())
    done = set()
    for track, items in pf.tracks():
        arr = pf._ptr(track + 8)
        for a, (t, text) in enumerate(items):
            if text in edits:
                new, time = edits[text]
                entry = arr + a * ha.ANNOTATION_SIZE
                s = pf._ptr(entry + 8)
                old_len = len(text.encode())
                assert len(new.encode()) <= old_len, (new, text)
                pf.data[s:s + old_len] = new.encode().ljust(old_len, b'\0')
                struct.pack_into('<f', pf.data, entry, time)
                done.add(text)
    assert done == set(edits), (src, set(edits) - done)
    out = pf.save()
    check = ha.Packfile(out)
    have = check.annotations()
    for new, time in edits.values():
        assert any(x == new and abs(t - time) < 1e-5 for t, x in have), (dst, new, time)
    ha.check_string_alignment(check, dst)
    with open(dst, 'wb') as fh:
        fh.write(out)
    return have


def only_gun(conds):
    """The conditions with every IsEquipped (Ordo musket or ours) reduced to ours alone."""
    out = []
    for c in conds:
        c = json.loads(json.dumps(c))
        if isinstance(c.get('Conditions'), list):
            c['Conditions'] = only_gun(c['Conditions'])
            if not c['Conditions']:
                continue
        if c.get('condition') == 'IsEquipped' and c.get('Form', {}) != GUN:
            continue
        out.append(c)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('reload1')
    ap.add_argument('reload2')
    ap.add_argument('--gain', type=float, default=GAIN, help='volume after peak-normalising (1 = full)')
    args = ap.parse_args()
    info = {}
    for (name, _, _), src in zip(SOUNDS, (args.reload1, args.reload2)):
        info[name] = install_wav(src, os.path.join(TARGET, *WAV_DIR.split('/'), name + '.wav'), args.gain)
        print('sound %s: %.2f s, first hit %.2f s, audible %.2f s' % ((name,) + info[name]))
    char = os.path.join('meshes', 'actors', 'character')
    for base, sub in SUBMODS:
        src_dir = os.path.join(RAMROD, char, *base.split('/'), 'OpenAnimationReplacer', 'Zenderal - Musket Ramrod Reload', sub)
        dst_mod = os.path.join(TARGET, char, *base.split('/'), 'OpenAnimationReplacer', OAR_MOD)
        dst_dir = os.path.join(dst_mod, 'Clockwork Thunder ' + sub)
        shutil.rmtree(dst_dir, ignore_errors=True)
        os.makedirs(os.path.join(dst_dir, 'dlc01'))
        cfg = json.load(open(os.path.join(src_dir, 'config.json'), encoding='utf-8'))
        assert GUN['pluginName'] in json.dumps(cfg['conditions']), (sub, 'run tools/03 first: no Clockwork Thunder')
        cfg['name'] = 'Clockwork Thunder ' + sub
        cfg['description'] = ('Clockwork Thunder only: ' + sub + "'s reload clips with the curator's sci-fi reload "
                              'sounds (src/ClockworkThunder tools/05). ' + cfg.get('description', ''))
        cfg['priority'] = cfg['priority'] + PRIORITY_UP
        cfg['conditions'] = only_gun(cfg['conditions'])
        json.dump(cfg, open(os.path.join(dst_dir, 'config.json'), 'w', encoding='utf-8'), indent=4)
        if not os.path.isfile(os.path.join(dst_mod, 'config.json')):
            json.dump({'name': OAR_MOD, 'author': 'Zenderal',
                       'description': "Clockwork Thunder's reload with the curator's sci-fi reload sounds."},
                      open(os.path.join(dst_mod, 'config.json'), 'w', encoding='utf-8'), indent=4)
        for clip in CLIPS:
            p = os.path.join(src_dir, 'dlc01', clip)
            if not os.path.isfile(p):
                continue
            dur, ann = ha.read(p)
            ball = [t for t, x in ann if x == 'SoundPlay.ZEN_MusketLoad7']
            unequips = sorted(t for t, x in ann if x == 'AnimObjectUnequip')
            assert len(ball) == 1 and unequips, (p, ann)
            beats = {'ball': ball[0], 'rod': unequips[-1]}
            edits, starts = {}, {}
            for name, old, beat in SOUNDS:
                starts[name] = max(0.0, beats[beat] - info[name][1])
                edits[old] = ('SoundPlay.' + name, starts[name])
            # Reload_1 must have died away before Reload_2 starts
            assert starts['ZP_CTReload1'] + info['ZP_CTReload1'][2] <= starts['ZP_CTReload2'] + 1e-6, (p, starts)
            retime(p, os.path.join(dst_dir, 'dlc01', clip), edits)
            print('%s / %s: %.2f s clip; ball %.2f -> Reload1 at %.2f; rod stowed %.2f -> Reload2 at %.2f'
                  % (sub, clip, dur, beats['ball'], starts['ZP_CTReload1'], beats['rod'], starts['ZP_CTReload2']))


if __name__ == '__main__':
    main()
