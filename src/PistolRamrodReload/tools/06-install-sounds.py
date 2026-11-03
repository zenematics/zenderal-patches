"""Install the pistol reload's loading sounds into `Zenderal - Pistol Ramrod Reload`: tools/01's SOUNDS, in order.

The curator's picks (2026-11-02) are Motion Array SFX, "MA_Amenteramco_Loading_Gun_5.wav" and "..._9.wav" (24-bit / 48 kHz
stereo). They are licensed, so neither they nor the output are committed. Each is written to the path its SNDR names
(tools/02, SOUND_PATH) as 16-bit / 44.1 kHz mono PCM: the SNDRs copy vanilla's bow nock (a positional output model), and
the clips play them on the actor. The conversion is src/BloodyCritSound/tools/01's (windowed-sinc resample, TPDF dither,
no gain change unless it would clip), the channels averaged first.

Run before tools/02 (which checks the files are there).
Usage:  python src/PistolRamrodReload/tools/06-install-sounds.py <Loading_Gun_5.wav> <Loading_Gun_9.wav> [<modlist root>]
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


PR = _load('pistol_reload', os.path.join(HERE, '01-build-pistol-reload.py'))
CRIT = _load('crit_sound', os.path.join(ROOT, 'src', 'BloodyCritSound', 'tools', '01-build-crit-sound.py'))
OUT_RATE = 44100
SOUND_DIR = ['sound', 'fx', 'zenderal', 'pistolreload']     # tools/02 SOUND_PATH, lower case on disk


def main():
    args = sys.argv[1:]
    if len(args) < len(PR.SOUNDS):
        sys.exit(__doc__)
    root = args[len(PR.SOUNDS)] if len(args) > len(PR.SOUNDS) else PR.ADS.TOOLS['modlistRoot']
    for (edid, _), src in zip(PR.SOUNDS, args):
        ch, rate, chans = CRIT.read_pcm(src)
        mono = [sum(v) / ch for v in zip(*chans)]
        mono = CRIT.resample(mono, rate, OUT_RATE)
        peak = max(abs(v) for v in mono)
        gain = 0.98 / peak if peak > 0.98 else 1.0
        rnd = random.Random(0)
        frames = bytearray()
        for v in mono:
            frames += struct.pack('<h', max(-32768, min(32767, int(round(v * gain * 32767 + rnd.random() - rnd.random())))))
        out = os.path.join(root, 'mods', PR.DEPLOY, *SOUND_DIR, edid.lower() + '.wav')
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with wave.open(out, 'wb') as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(OUT_RATE)
            w.writeframes(bytes(frames))
        print('%s <- %s: mono, 16-bit, %d Hz, %.2f s, peak %.1f dBFS, gain %.1f dB'
              % (out, os.path.basename(src), OUT_RATE, len(mono) / OUT_RATE, 20 * math.log10(max(peak, 1e-9)),
                 20 * math.log10(gain)))


if __name__ == '__main__':
    main()
