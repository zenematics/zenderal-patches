"""Install the musket ramrod reload's loading sounds into `Zenderal - Musket Ramrod Reload`: tools/09's SOUNDS, in order.

The curator's picks (2026-11-02) are Motion Array SFX, "MA_BBRealSound_Weapon_Gun_Reload_And_Load_7.wav" and "..._1.wav"
(24-bit / 48 kHz stereo). They are licensed, so neither they nor the output are committed. Each is written to the path
its SNDR names (tools/11, SOUND_PATH) as 16-bit / 44.1 kHz mono PCM, as Pistol Ramrod Reload's tools/06 does (the SNDRs
copy vanilla's positional bow nock; the clips play them on the actor). The conversion is src/BloodyCritSound/tools/01's
(windowed-sinc resample, TPDF dither, no gain change unless it would clip), the channels averaged first. Both files
open and close on digital silence (0.62 s and 0.33 s before the first sound), which is cut down to TRIM_PAD so each
sound starts on its clip event; no audible sample is touched.

Checks that each sound has died away (within 30 dB of its loudest 50 ms) before the next one's event (SOUNDS' gaps).
Run after tools/09 (which rebuilds the mod folder), e.g. with tools/11.
Usage:  python src/FlintlockOverhaul/tools/12-install-ramrod-sounds.py <..._Load_7.wav> <..._Load_1.wav> [<modlist root>]
"""
import importlib.util
import math
import os
import random
import struct
import sys
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


R3P = _load('ramrod3p', os.path.join(HERE, '09-build-ramrod-reload.py'))
CRIT = _load('crit_sound', os.path.join(ROOT, 'src', 'BloodyCritSound', 'tools', '01-build-crit-sound.py'))
OUT_RATE = 44100
SOUND_DIR = ['sound', 'fx', 'zenderal', 'musketreload']    # tools/11 SOUND_PATH, lower case on disk
SILENCE = 10 ** (-100 / 20.0)   # below this a sample counts as silence (the files' silence is under -140 dBFS RMS)
TRIM_PAD = 0.002                # seconds kept before the first and after the last audible sample
WINDOW = 0.05                   # loudness windows for the died-away check
DIED_AWAY_DB = 30.0


def trim(mono, rate):
    loud = [i for i, v in enumerate(mono) if abs(v) > SILENCE]
    if not loud:
        sys.exit('the sound is silent')
    pad = int(round(TRIM_PAD * rate))
    return mono[max(0, loud[0] - pad):loud[-1] + pad + 1], loud[0] / rate


def audible(mono, rate):
    """Seconds until the end of the last WINDOW within DIED_AWAY_DB of the loudest one."""
    n = int(WINDOW * rate)
    rms = [math.sqrt(sum(v * v for v in mono[i:i + n]) / n) for i in range(0, len(mono) - n + 1, n)]
    top = max(rms)
    last = max(i for i, r in enumerate(rms) if r > 0 and 20 * math.log10(r / top) > -DIED_AWAY_DB)
    return (last + 1) * WINDOW


def main():
    args = sys.argv[1:]
    if len(args) < len(R3P.SOUNDS):
        sys.exit(__doc__)
    root = args[len(R3P.SOUNDS)] if len(args) > len(R3P.SOUNDS) else R3P.ADS.TOOLS['modlistRoot']
    mod = os.path.join(root, 'mods', R3P.MOD)
    if not os.path.isdir(mod):
        sys.exit('run tools/09 first: %s is missing' % mod)
    lengths = []
    for (edid, _), src in zip(R3P.SOUNDS, args):
        ch, rate, chans = CRIT.read_pcm(src)
        mono, cut = trim([sum(v) / ch for v in zip(*chans)], rate)
        lengths.append(audible(mono, rate))
        mono = CRIT.resample(mono, rate, OUT_RATE)
        peak = max(abs(v) for v in mono)
        gain = 0.98 / peak if peak > 0.98 else 1.0
        rnd = random.Random(0)
        frames = bytearray()
        for v in mono:
            frames += struct.pack('<h', max(-32768, min(32767, int(round(v * gain * 32767 + rnd.random() - rnd.random())))))
        out = os.path.join(mod, *SOUND_DIR, edid.lower() + '.wav')
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with wave.open(out, 'wb') as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(OUT_RATE)
            w.writeframes(bytes(frames))
        print('%s <- %s: mono, 16-bit, %d Hz, %.2f s (%.2f s of leading silence cut), audible %.2f s, peak %.1f dBFS, '
              'gain %.1f dB' % (out, os.path.basename(src), OUT_RATE, len(mono) / OUT_RATE, cut, lengths[-1],
                                20 * math.log10(max(peak, 1e-9)), 20 * math.log10(gain)))
    for (edid, at), (_, nxt), length in zip(R3P.SOUNDS, R3P.SOUNDS[1:], lengths):
        if nxt - at < length - WINDOW:
            sys.exit('%s is audible for %.2f s but the next sound starts %.2f s after it: change tools/09 SOUNDS and '
                     'rerun 09 -> 10 -> 11' % (edid, length, nxt - at))


if __name__ == '__main__':
    main()
