"""Snowveil's sounds (curator 2026-11-17), the curator's licensed files converted to 16-bit / 48 kHz stereo PCM into
Zenderal - Patch Collection (neither the sources nor the wavs are committed). ZP_OwlBowQuiverEffect plays them.

  sound/fx/Zenderal/OwlBow/SnowveilReleaseHoot.wav <- "Owl in Forest 02.wav", its SECOND hoot only, over the bow's
        own shot ("part of the shot sound ... subtle"); since 2026-11-17 only on every 5th shot, the guaranteed crit. Measured (40 ms frames): hoot 1 at 0.04-0.29 s
        (~1100 Hz), hoot 2 from 0.30 s, falling 1025 -> 800 Hz, loudest 0.6-0.8 s, gone by ~2 s. Cut at OWL_SKIP
        (20 ms fade in), OWL_GAIN_DB quieter.
  sound/fx/Zenderal/OwlBow/SnowveilDrawAir1..3.wav <- "MA_CineTransitions_DeepLongAirTransition4_001..003.wav", one per
        draw in turn ("alternate between these 3, don't play them at the same time"). Each is a long air swell (peak
        3.0 / 2.0 / 1.9 s in, 100 ms RMS; 7.6-8.6 s long). Started on arrowAttach and cut so its peak lands DRAW_TIME
        later, when the bow is fully drawn (BowDrawn); kept to AIR_AFTER s past the peak, the last AIR_FADE s faded.
        Timing from the 2026-11-17 Papyrus log (5 draws): BowDraw -> arrowAttach 0.18 s, arrowAttach -> BowDrawn
        0.91 s, -> arrowRelease 1.06-1.33 s.

  sound/fx/Zenderal/OwlBow/SnowveilShotFlap1..N.wav <- "MA_MotionAudio_BigBirdFlappingWings_02.wav" (24-bit / 48 kHz,
        12 s): its single wing beats, split at the digital silence between them (FLAP_SILENCE_DB), each started
        FLAP_LEAD s before it first comes within FLAP_RISE_DB of its own peak (so the whump lands on the release),
        20 ms fade in. One descriptor lists them all: the game picks one at random each shot (curator: "add the
        single flap noises ... as different bow shots"); played on the shots that are not the 5th.

Retired the same day: the whoosh + lightsaber draw sounds ("doesn't work well": they peaked at +0.5 s, before full
draw); their wavs are deleted from Patch Collection here.

Usage:  python src/OwlBow/tools/03-install-sounds.py --owl <Owl in Forest 02.wav>
            --air <..._001.wav> <..._002.wav> <..._003.wav> --flaps <MA_MotionAudio_BigBirdFlappingWings_02.wav>
"""
import argparse
import os
import subprocess
import wave

import imageio_ffmpeg
import numpy as np

MODS = 'E:/Zenderal/mods'
TARGET = 'Zenderal - Patch Collection'
OUT_DIR = 'sound/fx/Zenderal/OwlBow'
OWL_OUT, OWL_SKIP, OWL_GAIN_DB = 'SnowveilReleaseHoot.wav', 0.29, -12.0
AIR_OUT = 'SnowveilDrawAir%d.wav'
DRAW_TIME = 0.91            # s from arrowAttach to BowDrawn (fully drawn), measured
AIR_AFTER, AIR_FADE = 2.5, 1.2
FLAP_OUT = 'SnowveilShotFlap%d.wav'
FLAP_SILENCE_DB, FLAP_RISE_DB, FLAP_LEAD = -100.0, 20.0, 0.06
RETIRED = ('SnowveilDrawWhoosh.wav', 'SnowveilDrawSaber.wav')


def ffmpeg(args):
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-y', '-v', 'error'] + args, check=True)


def check(dst):
    w = wave.open(dst)
    assert (w.getnchannels(), w.getsampwidth(), w.getframerate()) == (2, 2, 48000)
    return w.getnframes() / 48000.0


def peak_time(src):
    """The loudest 100 ms window of the file (mono), in seconds."""
    tmp = os.path.join(os.environ.get('TEMP', '.'), 'snowveil_peak.wav')
    ffmpeg(['-i', src, '-ac', '1', '-ar', '48000', '-c:a', 'pcm_s16le', tmp])
    w = wave.open(tmp)
    x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float)
    w.close()
    os.remove(tmp)
    hop = 4800
    rms = [np.sqrt(np.mean(x[i:i + hop] ** 2)) for i in range(0, len(x) - hop, hop // 4)]
    return int(np.argmax(rms)) * (hop // 4) / 48000.0 + 0.05


def mono(src):
    tmp = os.path.join(os.environ.get('TEMP', '.'), 'snowveil_mono.wav')
    ffmpeg(['-i', src, '-ac', '1', '-ar', '48000', '-c:a', 'pcm_s16le', tmp])
    w = wave.open(tmp)
    x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768
    w.close()
    os.remove(tmp)
    return x


def flap_segments(src):
    """(start, end) seconds of each wing beat: runs of 10 ms frames above FLAP_SILENCE_DB, at least 0.4 s long; start
    moved to FLAP_LEAD before the beat first comes within FLAP_RISE_DB of its own peak."""
    x = mono(src)
    hop = 480
    db = np.array([20 * np.log10(np.sqrt(np.mean(x[i:i + hop] ** 2)) + 1e-6) for i in range(0, len(x) - hop, hop)])
    loud = db > FLAP_SILENCE_DB
    segs, i = [], 0
    while i < len(loud):
        if loud[i]:
            j = i
            while j < len(loud) and loud[j]:
                j += 1
            if (j - i) * 0.01 >= 0.4:
                pk = db[i:j].max()
                first = i + int(np.argmax(db[i:j] > pk - FLAP_RISE_DB))
                segs.append((max(i * 0.01, first * 0.01 - FLAP_LEAD), j * 0.01))
            i = j
        else:
            i += 1
    return segs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--owl', required=True)
    ap.add_argument('--air', nargs=3, required=True)
    ap.add_argument('--flaps', required=True)
    args = ap.parse_args()
    out = os.path.join(MODS, TARGET, *OUT_DIR.split('/'))
    os.makedirs(out, exist_ok=True)
    for f in RETIRED:
        if os.path.exists(os.path.join(out, f)):
            os.remove(os.path.join(out, f))
            print('removed retired', f)
    dst = os.path.join(out, OWL_OUT)
    ffmpeg(['-ss', '%.3f' % OWL_SKIP, '-i', args.owl, '-af', 'afade=t=in:d=0.02,volume=%.1fdB' % OWL_GAIN_DB,
            '-ar', '48000', '-ac', '2', '-c:a', 'pcm_s16le', dst])
    print('release hoot: %s (%.2f s, %.0f dB)' % (OWL_OUT, check(dst), OWL_GAIN_DB))
    for old in os.listdir(out):
        if old.startswith('SnowveilShotFlap'):
            os.remove(os.path.join(out, old))
    segs = flap_segments(args.flaps)
    assert 4 <= len(segs) <= 16, segs
    for i, (a, b) in enumerate(segs, 1):
        dst = os.path.join(out, FLAP_OUT % i)
        ffmpeg(['-ss', '%.3f' % a, '-t', '%.3f' % (b - a), '-i', args.flaps, '-af', 'afade=t=in:d=0.02',
                '-ar', '48000', '-ac', '2', '-c:a', 'pcm_s16le', dst])
        print('shot flap %d: %.2f-%.2f s, %.2f s long' % (i, a, b, check(dst)))
    print('FLAPS = %d' % len(segs))
    for i, src in enumerate(args.air, 1):
        pk = peak_time(src)
        skip = pk - DRAW_TIME
        assert skip > 0, (src, pk)
        length = DRAW_TIME + AIR_AFTER
        dst = os.path.join(out, AIR_OUT % i)
        ffmpeg(['-ss', '%.3f' % skip, '-t', '%.3f' % length, '-i', src, '-af',
                'afade=t=in:d=0.08,afade=t=out:st=%.3f:d=%.3f' % (length - AIR_FADE, AIR_FADE),
                '-ar', '48000', '-ac', '2', '-c:a', 'pcm_s16le', dst])
        print('draw air %d: peak %.2f s in the source, cut from %.2f s -> peak at +%.2f s, %.2f s long'
              % (i, pk, skip, DRAW_TIME, check(dst)))


if __name__ == '__main__':
    main()
