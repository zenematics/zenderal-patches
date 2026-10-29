"""Prophecy's mixed sound files (curator 2026-10-28), each played by the engine, not by Shatterveil's DLL (its
DLL-played sounds are silent on 1.7.104, see ShatterveilAE.md). Each is clips mixed at start times:
- the Veil Wyrm shout (ZP_Prophecy_VeilWyrmGlassImpactSD 0xAE0): two Motion Array clips from the curator's Music
  folder - the glass impact, and the whale starting under its tail (straight after the impact's 5.25 s, whose last
  ~2 s are under -30 dB, it came too late); and, from 2026-10-29, the curator's Glass-002 with the impact ("add
  this sound to Sorcery's wyrm shout, as an addition") - a 96 kHz clip, downsampled to the mix's 48 kHz;
- Blink Step's swoosh (ZP_Prophecy_BlinkStepSwooshSound): one Motion Array clip, converted only;
Skyrim plays 16-bit PCM only; 24-bit clips are converted (top 16 bits, no dither). A clip at a whole multiple of the
first clip's rate is low-pass filtered (windowed sinc) and decimated to it. The .wavs are not committed (licensed
audio / another mod's); rerun this to rebuild them.

Usage: python 07-build-sounds.py [output mod dir]   (default: the Prophecy v3 MO2 mod)"""
import os, struct, sys
import numpy as np

MUSIC = os.path.join(os.path.expanduser('~'), 'Music')
# output (under the mod) -> [(clip, start in seconds)]. A clip without a folder is in the curator's Music folder.
# The impact is loud to ~3.0 s; the whale swells from ~0.6 s into its own clip
SOUNDS = {
    r'Sound\FX\ZenProphecy\ZP_VeilWyrmGlassImpact.wav': [('MA_GarnaVutka_Trailer_Glass_Impacts_09.wav', 0.0),
                                                        ('MA_SBProductions_WhaleCollection_Whale7.wav', 2.0),
                                                        ('Glass-002.wav', 0.0)],
    # Blink Step's swoosh (2026-10-29): one clip, only converted to 16-bit
    r'Sound\FX\ZenProphecy\ZP_BlinkStepSwoosh.wav': [('MA_Originals_FastSwooshTransitions_5.wav', 0.0)],
}
MOD = r'E:\Zenderal\mods\Zenderal - Prophecy v3 (Constellation)'


def read(path):
    d = open(path, 'rb').read()
    assert d[:4] == b'RIFF' and d[8:12] == b'WAVE', path
    i, fmt, data = 12, None, None
    while i < len(d) - 8:
        cid, sz = d[i:i + 4], struct.unpack_from('<I', d, i + 4)[0]
        if cid == b'fmt ':
            fmt = struct.unpack_from('<HHIIHH', d, i + 8)
        elif cid == b'data':
            data = d[i + 8:i + 8 + sz]
        i += 8 + sz + (sz & 1)
    tag, ch, sr, _, _, bits = fmt
    assert tag == 1 and bits in (16, 24), f'{path}: format {fmt}'
    if bits == 24:
        b = np.frombuffer(data[:len(data) // 3 * 3], dtype=np.uint8).reshape(-1, 3).astype(np.int32)
        s = b[:, 0] | (b[:, 1] << 8) | (b[:, 2] << 16)
        s = np.where(s & 0x800000, s - 0x1000000, s)
        s = np.clip(np.round(s / 256), -32768, 32767).astype(np.int16)
    else:
        s = np.frombuffer(data, dtype='<i2')
    return ch, sr, s


def decimate(ch, s, k):
    """Interleaved int16 at k x the rate -> float samples at the rate: 255-tap Hamming-windowed sinc low-pass at 0.45 of
    the new rate, then every k-th frame."""
    n = np.arange(255) - 127
    h = np.sinc(2 * 0.45 / k * n) * (2 * 0.45 / k) * np.hamming(255)
    h /= h.sum()
    x = s.reshape(-1, ch).astype(np.float64)
    y = np.stack([np.convolve(x[:, c], h, mode='same') for c in range(ch)], axis=1)[::k]
    return y.reshape(-1)


def build(out, clips):
    parts = [read(os.path.join(MUSIC, c)) for c, _ in clips]
    ch0, sr0 = parts[0][:2]
    for i, (ch, sr, s) in enumerate(parts):
        if ch == ch0 and sr != sr0 and sr % sr0 == 0:
            parts[i] = (ch, sr0, decimate(ch, s, sr // sr0))
            print(f'{clips[i][0]}: {sr} Hz -> {sr0} Hz')
    assert len({(ch, sr) for ch, sr, _ in parts}) == 1, 'clips differ in channels/rate'
    ch, sr = parts[0][:2]
    starts = [int(round(t0 * sr)) * ch for _, t0 in clips]
    mix = np.zeros(max(st + len(s) for st, (_, _, s) in zip(starts, parts)), dtype=np.float64)
    for st, (_, _, s) in zip(starts, parts):
        mix[st:st + len(s)] += s
    peak = np.abs(mix).max()
    if peak > 32767:                    # overlap clipped: scale the whole mix down to just under full scale
        mix *= 32767 / peak
        print(f'mix peak {peak:.0f} > 32767: scaled by {32767 / peak:.3f}')
    pcm = np.round(mix).astype('<i2').tobytes()
    os.makedirs(os.path.dirname(out), exist_ok=True)
    hdr = (b'RIFF' + struct.pack('<I', 36 + len(pcm)) + b'WAVE' + b'fmt ' +
           struct.pack('<IHHIIHH', 16, 1, ch, sr, sr * ch * 2, ch * 2, 16) + b'data' + struct.pack('<I', len(pcm)))
    open(out, 'wb').write(hdr + pcm)
    print(f'{out}: ' + ', '.join(f'{os.path.basename(c)} at {t0:.2f} s' for c, t0 in clips) +
          f' = {len(mix) / ch / sr:.2f} s, {ch} ch {sr} Hz 16-bit')


def main():
    mod = sys.argv[1] if len(sys.argv) > 1 else MOD
    for out, clips in SOUNDS.items():
        build(os.path.join(mod, out), clips)


if __name__ == '__main__':
    main()
