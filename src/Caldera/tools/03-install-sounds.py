"""Caldera's sound files (not committed: the curator's own files, installed from their copies). Each is converted to
16-bit / 44.1 kHz by Argent Verdict's converter (windowed-sinc resample, TPDF dither, never clipped; the game does not
play 24-bit PCM) and mixed to mono (the game places only mono sounds in 3D).

  sound/fx/Zenderal/Caldera/CalderaLavaLoop.wav   --lava: the lava river at the eruption, looping 7 s (SNDR 813;
                     curator 2026-11-16: "add this sound for the lava fissures", "flowing and bubbling lava
                     river-001.wav", 58 s): its first LAVA_SECONDS kept and made to loop without a seam (Whisper's
                     mono_loop: its last LOOP_FADE seconds faded, equal power, into its first)
  sound/fx/Zenderal/Caldera/CalderaEruption.wav   --eruption: the volcano bursting out of the ground (SNDR 814, the
                     volcano explosion's sound; curator: "and this one too", MA_MotionAudio_VolcanoErupting_01.wav)
  sound/fx/Zenderal/Caldera/CalderaCharged.wav    --charged: the hammer fully charged (SNDR 815 / SOUN 811; curator:
                     "add this sound when the hammer is charged", MA_Floraphonic_Swing_Whoosh_Metal_Hit_39.wav; was
                     vanilla's oil trap igniting)

Usage:  python src/Caldera/tools/03-install-sounds.py [--lava <flowing and bubbling lava river-001.wav>]
            [--eruption <MA_MotionAudio_VolcanoErupting_01.wav>]
            [--charged <MA_Floraphonic_Swing_Whoosh_Metal_Hit_39.wav>] [--out-root <dir>]
"""
import argparse
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
LAVA_OUT = 'sound/fx/Zenderal/Caldera/CalderaLavaLoop.wav'       # 02-build-records.py LAVA_FILE (checked there)
ERUPTION_OUT = 'sound/fx/Zenderal/Caldera/CalderaEruption.wav'   # 02-build-records.py ERUPTION_FILE (checked there)
CHARGED_OUT = 'sound/fx/Zenderal/Caldera/CalderaCharged.wav'     # 02-build-records.py CHARGED_FILE (checked there)
EXPECTED = {'lava': 'flowing and bubbling lava river-001.wav', 'eruption': 'MA_MotionAudio_VolcanoErupting_01.wav',
            'charged': 'MA_Floraphonic_Swing_Whoosh_Metal_Hit_39.wav'}
LAVA_SECONDS = 16.0       # of the 58 s river: it plays for the volcano's 6 s and one more
LOOP_FADE = 1.0           # Whisper's


def _module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    ap = argparse.ArgumentParser()
    for key, name in EXPECTED.items():
        ap.add_argument('--' + key, default=None, help="the curator's " + name)
    ap.add_argument('--out-root', default=None, help='default: the installed Zenderal - Patch Collection')
    args = ap.parse_args()
    if not any(getattr(args, k) for k in EXPECTED):
        sys.exit('nothing to install: pass --lava, --eruption and/or --charged')
    av = _module('av_assets', os.path.join(ROOT, 'src', 'ArgentVerdict', 'tools', '03-smite-assets.py'))
    ws = _module('w_sound', os.path.join(ROOT, 'src', 'Whisper', 'tools', '04-install-sound.py'))
    out_root = args.out_root
    if out_root is None:
        sr = _module('sr_assets', os.path.join(ROOT, 'src', 'StingAndRise', 'tools', '01-build-assets.py'))
        out_root = os.path.join(sr.MO2, 'mods', 'Zenderal - Patch Collection')
    for key, out in (('lava', LAVA_OUT), ('eruption', ERUPTION_OUT), ('charged', CHARGED_OUT)):
        src = getattr(args, key)
        if not src:
            continue
        if os.path.basename(src) != EXPECTED[key]:
            sys.exit('--%s: expected the curator\'s %s, got %s' % (key, EXPECTED[key], src))
        data, how = av.bell_sound(src)
        x, rate = ws.read16(data)
        if key == 'lava':
            x = x[:int((LAVA_SECONDS + LOOP_FADE) * rate)]
            ws.LOOP_FADE = LOOP_FADE
            data, more = ws.mono_loop(ws.write16(x, rate))
        else:
            data = ws.write16(x.mean(1)[:, None], rate)
            more = '%.2f s mono' % (len(x) / rate)
        p = os.path.join(out_root, *out.split('/'))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'wb') as f:
            f.write(data)
        print('%s: %s; %s -> %s (%d bytes)' % (key, how, more, p, len(data)))


if __name__ == '__main__':
    main()
