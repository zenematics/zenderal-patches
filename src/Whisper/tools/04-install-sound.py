"""Whisper's sound files (not committed: the curator's licensed files, installed from their own copies). Each is
converted to 16-bit / 44.1 kHz by Argent Verdict's converter (windowed-sinc resample, TPDF dither, never clipped; the
game does not play 24-bit PCM).

  sound/fx/Zenderal/Whisper/WhisperCharged.wav   --charged: the axe fully charged (SNDR 80E / SOUN 80F; curator
                     2026-11-15: "add this sound when its fully charged", MA_MotionAudio_SpookyBreath_02.wav)
  sound/fx/Zenderal/Whisper/WhisperWispLoop.wav  --wisp: the Soul Wisp's whisper, looping while it is out (SNDR 820 /
                     SOUN 821; curator: "add this whisper sound effect looped for when the Wisp is active",
                     MA_MotionAudio_GhostWhispering_03.wav): mixed to mono (the game places only mono sounds in 3D) and
                     made to loop without a seam: its last LOOP_FADE seconds faded (equal power) into its first, so the
                     end runs straight into the start; the level otherwise untouched
  sound/fx/Zenderal/Whisper/WhisperPoof.wav      --poof: Soul Cleave's release (SNDR 822 / SOUN 823; curator: "add this
                     to the special power attack wave on trigger", 02. Cartoon Poof SFX.wav), stereo kept

Usage:  python src/Whisper/tools/04-install-sound.py [--charged <MA_MotionAudio_SpookyBreath_02.wav>]
            [--wisp <MA_MotionAudio_GhostWhispering_03.wav>] [--poof <02. Cartoon Poof SFX.wav>] [--out-root <dir>]
"""
import argparse
import importlib.util
import io
import os
import sys
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
CHARGED_OUT = 'sound/fx/Zenderal/Whisper/WhisperCharged.wav'      # 03-build-records.py CHARGED_FILE (checked there)
WISP_OUT = 'sound/fx/Zenderal/Whisper/WhisperWispLoop.wav'        # 03-build-records.py WISP_LOOP_FILE (checked there)
POOF_OUT = 'sound/fx/Zenderal/Whisper/WhisperPoof.wav'            # 03-build-records.py POOF_FILE (checked there)
EXPECTED = {'charged': 'MA_MotionAudio_SpookyBreath_02.wav', 'wisp': 'MA_MotionAudio_GhostWhispering_03.wav',
            'poof': '02. Cartoon Poof SFX.wav'}
LOOP_FADE = 1.0           # seconds of the end faded into the start


def _module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def read16(data):
    w = wave.open(io.BytesIO(data))
    assert w.getsampwidth() == 2
    x = np.frombuffer(w.readframes(w.getnframes()), '<i2').astype(np.float64) / 32768.0
    return x.reshape(-1, w.getnchannels()), w.getframerate()


def write16(x, rate):
    peak = float(np.abs(x).max())
    if peak > 0.98:
        x = x * (0.98 / peak)
    out = io.BytesIO()
    o = wave.open(out, 'wb')
    o.setnchannels(x.shape[1])
    o.setsampwidth(2)
    o.setframerate(rate)
    o.writeframes(np.clip(np.round(x * 32767), -32768, 32767).astype('<i2').tobytes())
    o.close()
    return out.getvalue()


def mono_loop(data):
    """Mono, and the last LOOP_FADE seconds faded (equal power) into the first, the tail dropped: the end of the result
    is where the original's tail fade began, which runs on seamlessly into its start."""
    x, rate = read16(data)
    m = x.mean(1)
    n = int(LOOP_FADE * rate)
    assert len(m) > 4 * n, 'too short to loop'
    t = np.linspace(0.0, 1.0, n)
    head, tail = m[:n], m[-n:]
    m = m[:-n].copy()
    m[:n] = head * np.sin(t * np.pi / 2) + tail * np.cos(t * np.pi / 2)
    return write16(m[:, None], rate), '%.2f s mono, looping (%.1f s cross-fade)' % (len(m) / rate, LOOP_FADE)


def main():
    ap = argparse.ArgumentParser()
    for key, name in EXPECTED.items():
        ap.add_argument('--' + key, default=None, help="the curator's " + name)
    ap.add_argument('--out-root', default=None, help='default: the installed Zenderal - Patch Collection')
    args = ap.parse_args()
    if not any(getattr(args, k) for k in EXPECTED):
        sys.exit('nothing to install: pass --charged, --wisp and/or --poof')
    av = _module('av_assets', os.path.join(ROOT, 'src', 'ArgentVerdict', 'tools', '03-smite-assets.py'))
    out_root = args.out_root
    if out_root is None:
        sr = _module('sr_assets', os.path.join(ROOT, 'src', 'StingAndRise', 'tools', '01-build-assets.py'))
        out_root = os.path.join(sr.MO2, 'mods', 'Zenderal - Patch Collection')
    for key, out in (('charged', CHARGED_OUT), ('wisp', WISP_OUT), ('poof', POOF_OUT)):
        src = getattr(args, key)
        if not src:
            continue
        if os.path.basename(src) != EXPECTED[key]:
            sys.exit('--%s: expected the curator\'s %s, got %s' % (key, EXPECTED[key], src))
        data, how = av.bell_sound(src)
        if key == 'wisp':
            data, more = mono_loop(data)
            how += '; ' + more
        dst = os.path.join(out_root, *out.split('/'))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, 'wb') as f:
            f.write(data)
        print('%s: %s (%d bytes) from %s' % (dst, how, len(data), src))


if __name__ == '__main__':
    main()
