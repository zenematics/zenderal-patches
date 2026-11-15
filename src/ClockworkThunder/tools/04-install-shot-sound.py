"""Install Clockwork Thunder's shot sound (curator 2026-11-15: "add this noise to when it's fired", then "add this
sound effect to the fire", then "turn up the newer shot sounds, they're a little quiet").

The curator's own files are not committed. Each given wav is a layer, cut to just before its own attack (its first
frame at ONSET_LEVEL of its peak; the files open on different lead-ins, which staggered the bangs), and summed (the
first layer's channels and rate; later layers resampled to it, with Reversal Shadow's reader/resampler,
src/ReversalShadow/tools/01-build-assets.py), into

  <mods>/<target>/sound/fx/Zenderal/ClockworkThunder/ClockworkThunderShot.wav   (16-bit PCM)

which SNDR ZP_ClockworkThunderShotSD 80C plays (tools/02), the rifle's AttackSound and AttackSound2D.

Loudness: the plain mix already peaked at 0.96 of full scale with its loudest 50 ms at -9.7 dB RMS, so it could not
simply be turned up. --drive k runs it through a soft limiter, y = tanh(k x) / tanh(k) on the peak-normalised mix,
which rounds the peaks off and raises everything else (k 2.5: about +5 to +6 dB RMS); the result is scaled to
peak 32000. The script prints the loudest-50-ms RMS before and after.

The shipped shot (2026-11-15), in this order, --drive 2.5:
  MA_SoundsByGFXSounds_Sci-FiLaserGunShot_1.wav   (licensed Motion Array; 24-bit 48 kHz stereo)
  "Blaster Rifle Shot V03.wav"                     (16-bit 44.1 kHz stereo, resampled)
  MA_SoundsByGFXSounds_SniperRifleShot_4.wav       (licensed Motion Array; 24-bit 48 kHz stereo)
  MA_MotionAudio_Sci-FiBlasterShot_04.wav          (licensed Motion Array)

Usage:  python src/ClockworkThunder/tools/04-install-shot-sound.py <wav> [<wav> ...] [--drive K] [--mods <dir>]
        [--target <mod>]
"""
import argparse
import importlib.util
import json
import math
import os
import struct
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
TOOLS = json.load(open(os.path.join(ROOT, '.claude', 'config', 'tools.json'), encoding='utf-8-sig'))
DST = 'sound/fx/Zenderal/ClockworkThunder/ClockworkThunderShot.wav'
DRIVE = 2.5
ONSET_LEVEL = 0.1      # a layer's attack: the first frame at 10% (-20 dB) of its peak
ONSET_LEAD = 0.002     # keep this much before it

_spec = importlib.util.spec_from_file_location(
    '_rs', os.path.join(ROOT, 'src', 'ReversalShadow', 'tools', '01-build-assets.py'))
_rs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_rs)


def loudest_rms_db(x, ch, rate):
    m = x.reshape(-1, ch).mean(1)
    win = rate // 20
    env = [math.sqrt(float((m[i:i + win] ** 2).mean())) for i in range(0, len(m) - win, win)]
    return 20 * math.log10(max(env) + 1e-12)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('wav', nargs='+')
    ap.add_argument('--drive', type=float, default=DRIVE, help='soft-limiter drive (0 = plain peak-normalised mix)')
    ap.add_argument('--mods', default=os.path.join(TOOLS['modlistRoot'], 'mods'))
    ap.add_argument('--target', default='Zenderal - Patch Collection')
    args = ap.parse_args()
    root = os.path.join(args.mods, args.target)
    assert os.path.isdir(root), root
    dst = os.path.join(root, *DST.split('/'))

    layers = [_rs.read_pcm(p) for p in args.wav]
    ch, rate = layers[0][0][1], layers[0][0][2]
    arrs = []
    for p, (fmt, x) in zip(args.wav, layers):
        assert fmt[1] == ch, (p, fmt[1], 'channels differ from the first layer')
        if fmt[2] != rate:
            x = _rs.resample(x, ch, fmt[2], rate)
        a = np.array(x, np.float64) / 32768.0
        # line the layers up on their attacks, not their file starts (curator: "fired at the same time, not
        # staggered"): each is cut to ONSET_LEAD before the first frame reaching ONSET_LEVEL of its own peak
        frames = np.abs(a.reshape(-1, ch)).max(1)
        onset = int(np.argmax(frames >= ONSET_LEVEL * frames.max()))
        start = max(0, onset - int(ONSET_LEAD * rate))
        print('layer %s: attack at %.3f s, cut %.3f s' % (os.path.basename(p), onset / rate, start / rate))
        arrs.append(a[start * ch:])
    n = max(len(a) for a in arrs)
    n -= n % ch
    mix = np.zeros(n)
    for a in arrs:
        mix[:min(n, len(a))] += a[:n]
    mix /= np.abs(mix).max()
    before = loudest_rms_db(mix, ch, rate)
    if args.drive > 0:
        mix = np.tanh(args.drive * mix) / math.tanh(args.drive)
    out = np.round(mix / np.abs(mix).max() * 32000).astype('<i2')
    after = loudest_rms_db(out / 32768.0, ch, rate)
    data = out.tobytes()
    head = (b'RIFF' + struct.pack('<I', 36 + len(data)) + b'WAVE' + b'fmt ' +
            struct.pack('<IHHIIHH', 16, 1, ch, rate, rate * ch * 2, ch * 2, 16) + b'data' + struct.pack('<I', len(data)))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, 'wb').write(head + data)
    w = wave.open(dst)                                  # read it back: 16-bit PCM the engine plays
    assert w.getsampwidth() == 2 and w.getnframes() > 0, (w.getsampwidth(), w.getnframes())
    print('installed %s (%d layers, %d ch, %d Hz, %.2f s, 16-bit); loudest 50 ms %.1f dB -> %.1f dB RMS (drive %.1f)'
          % (dst, len(arrs), ch, rate, w.getnframes() / rate, before, after, args.drive))


if __name__ == '__main__':
    main()
