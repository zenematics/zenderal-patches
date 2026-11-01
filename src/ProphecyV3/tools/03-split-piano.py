"""Prophecy v3 - the selection notes: split the curator's piano melody into one clip per note.

Input:  the curator's Piano-003.wav (24-bit / 96 kHz stereo, ~105 s): a slow C-minor melody, 18 notes (C3 D3 Eb2 Bb2
        Ab2 G2 ...), each left to ring until the next, 2-8 s apart.
Output: <MO2 mods>/Zenderal - Prophecy v3 (Constellation)/Sound/FX/Zenderal/Prophecy/ZEN_ProphecyNote_NN.wav, NN = 01-18
        in melody order: 16-bit / 44.1 kHz stereo, cut 20 ms before each onset, at most 3.5 s, last 0.8 s faded out.
        NOT committed (the curator's audio, as with the other Prophecy sounds).
The window plays the next note each time a learnable star is clicked, so choosing talents plays the melody in order
(ZP_Prophecy_SelectNote_NN 0x9B2-0x9C3, AudioCategoryUI + SOMUIDefault so they sound while the menu pauses the game).

Onsets are detected (10 ms energy envelope: a rise of 1.5x over the previous window (1.3-1.6 all find the same 18; 1.8 misses the soft Ab2 at 28.4 s, which starts under a ringing Bb2), above 10% of the peak and 3x the
running floor, at least 150 ms apart); the script stops unless it finds exactly 18.
Usage (numpy is not available under -I):  python src/ProphecyV3/tools/03-split-piano.py "<Piano-003.wav>" [<MO2 mods dir>]
"""
import os, sys, wave
import numpy as np

NOTES = 18
OUT_RATE = 44100
MAX_LEN, FADE, PRE = 3.5, 0.8, 0.02
MOD = 'Zenderal - Prophecy v3 (Constellation)'


def read(path):
    w = wave.open(path)
    ch, sw, rate, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
    raw = np.frombuffer(w.readframes(n), dtype=np.uint8)
    if sw == 3:
        b = raw.reshape(-1, 3).astype(np.int32)
        v = b[:, 0] | (b[:, 1] << 8) | (b[:, 2] << 16)
        v = np.where(v & 0x800000, v - 0x1000000, v) / 8388608.0
    elif sw == 2:
        v = raw.view('<i2') / 32768.0
    else:
        raise SystemExit(f'{sw * 8}-bit PCM not handled')
    return rate, v.reshape(-1, ch)


def onsets(x, rate):
    mono = np.abs(x).mean(axis=1)
    hop = rate // 100
    env = mono[:len(mono) // hop * hop].reshape(-1, hop).mean(axis=1)
    peak, floor, found = env.max(), env[0], []
    for i in range(1, len(env)):
        if env[i] > max(0.1 * peak, 3 * floor) and env[i] > env[i - 1] * 1.5 and (not found or i - found[-1] > 15):
            found.append(i)
        floor = 0.95 * floor + 0.05 * env[i]
    return [i / 100.0 for i in found]


def resample(x, src, dst):
    """FFT resample per channel (clips are a few seconds long)."""
    n_out = int(round(len(x) * dst / src))
    out = np.empty((n_out, x.shape[1]))
    for c in range(x.shape[1]):
        spec = np.fft.rfft(x[:, c])
        keep = n_out // 2 + 1
        spec = spec[:keep] if len(spec) >= keep else np.pad(spec, (0, keep - len(spec)))
        out[:, c] = np.fft.irfft(spec, n_out) * (n_out / len(x))
    return out


def main():
    src = sys.argv[1]
    mods = sys.argv[2] if len(sys.argv) > 2 else r'E:\Zenderal\mods'
    rate, x = read(src)
    t = onsets(x, rate)
    # a note that starts within 0.3 s of the previous one is the same strike (the detector's double hit)
    merged = [s for k, s in enumerate(t) if k == 0 or s - t[k - 1] > 0.3]
    if len(merged) != NOTES:
        sys.exit(f'expected {NOTES} notes, found {len(merged)}: {merged}')
    out_dir = os.path.join(mods, MOD, 'Sound', 'FX', 'Zenderal', 'Prophecy')
    os.makedirs(out_dir, exist_ok=True)
    total = len(x) / rate
    for k, s in enumerate(merged):
        end = min(merged[k + 1] if k + 1 < len(merged) else total, s + MAX_LEN)
        a, b = int(max(0.0, s - PRE) * rate), int(end * rate)
        clip = resample(x[a:b], rate, OUT_RATE)
        fade = min(int(FADE * OUT_RATE), len(clip))
        clip[-fade:] *= np.linspace(1.0, 0.0, fade)[:, None]
        clip[: int(0.005 * OUT_RATE)] *= np.linspace(0.0, 1.0, int(0.005 * OUT_RATE))[:, None]
        peak = np.abs(clip).max()
        if peak > 0.98:
            clip *= 0.98 / peak
        pcm = np.clip(np.round(clip * 32767), -32768, 32767).astype('<i2')
        path = os.path.join(out_dir, f'ZEN_ProphecyNote_{k + 1:02d}.wav')
        with wave.open(path, 'wb') as w:
            w.setnchannels(pcm.shape[1]); w.setsampwidth(2); w.setframerate(OUT_RATE)
            w.writeframes(pcm.tobytes())
        print(f'{k + 1:02d}: {s:6.2f}s, {len(clip) / OUT_RATE:.2f}s -> {path}')


if __name__ == '__main__':
    main()
