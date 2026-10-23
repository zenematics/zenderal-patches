"""Rebuild the `Zenderal - Bloody Crit Sound` MO2 mod from a user-supplied .wav.

The critical-hit sound is `UISneakAttack 0C06CE:Skyrim.esm`, a single-file SNDR. `Zenderal - Bloody Crit
Sound.esp` points it at this mod's own file, `Sound\\FX\\Zenderal\\ZEN_CritBloodyCut_01.wav`, so it does not
care what Impactful Crits (which replaces the stock `UI_SneakAttack_01.wav`) does or where it sorts.

The source is a Motion Array SFX the curator picked (`MA_Asak SFX_SwordKnifeBloodyCut_sword_hard_bloody.wav`,
24-bit / 48 kHz stereo). It is licensed, so neither it nor the output is committed. This script converts
it to 16-bit / 44.1 kHz PCM (the format of Impactful Crits' and the game's own UI sounds): windowed-sinc
resample, TPDF dither. Pure Python, no numpy.

Usage:  python 01-build-crit-sound.py <source.wav> [<mods dir>]     (default E:/Zenderal/mods)
"""
import math, os, random, struct, sys, wave

MOD = 'Zenderal - Bloody Crit Sound'
REL = ['sound', 'fx', 'zenderal', 'zen_critbloodycut_01.wav']  # must match the SNDR's SoundFiles
OUT_RATE = 44100
TAPS = 32  # half-width of the sinc kernel, in input samples


def read_pcm(path):
    with wave.open(path) as w:
        ch, width, rate, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        raw = w.readframes(n)
    assert width in (2, 3), f'{path}: {width * 8}-bit PCM not handled'
    full = float(1 << (width * 8 - 1))
    vals = []
    for i in range(0, len(raw), width):
        b = raw[i:i + width]
        if width == 3:
            b = b + (b'\xff' if b[2] & 0x80 else b'\x00')
        vals.append(struct.unpack('<i' if width == 3 else '<h', b)[0] / full)
    return ch, rate, [vals[c::ch] for c in range(ch)]


def resample(x, src, dst):
    if src == dst:
        return list(x)
    ratio = dst / src
    cutoff = min(1.0, ratio) * 0.95
    n_out = int(len(x) * ratio)
    out = []
    for j in range(n_out):
        t = j / ratio
        c = int(t)
        acc = 0.0
        for k in range(c - TAPS + 1, c + TAPS + 1):
            if 0 <= k < len(x):
                d = t - k
                s = cutoff if d == 0 else math.sin(math.pi * cutoff * d) / (math.pi * d)
                win = 0.5 + 0.5 * math.cos(math.pi * d / TAPS) if abs(d) < TAPS else 0.0
                acc += x[k] * s * win
        out.append(acc)
    return out


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    src = sys.argv[1]
    mods = sys.argv[2] if len(sys.argv) > 2 else 'E:/Zenderal/mods'
    ch, rate, chans = read_pcm(src)
    chans = [resample(c, rate, OUT_RATE) for c in chans]
    peak = max(abs(v) for c in chans for v in c)
    gain = 0.98 / peak if peak > 0.98 else 1.0  # never clip
    rnd = random.Random(0)
    frames = bytearray()
    for i in range(len(chans[0])):
        for c in chans:
            v = c[i] * gain * 32767 + rnd.random() - rnd.random()
            frames += struct.pack('<h', max(-32768, min(32767, int(round(v)))))
    out = os.path.join(mods, MOD, *REL)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with wave.open(out, 'wb') as w:
        w.setnchannels(ch); w.setsampwidth(2); w.setframerate(OUT_RATE)
        w.writeframes(bytes(frames))
    print(f'{out}: {ch} ch, 16-bit, {OUT_RATE} Hz, {len(chans[0]) / OUT_RATE:.2f} s, '
          f'source peak {20 * math.log10(peak):.1f} dBFS, gain {20 * math.log10(gain):.1f} dB')


if __name__ == '__main__':
    main()
