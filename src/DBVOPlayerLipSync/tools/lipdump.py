"""Decode the .lip track inside a Skyrim/Enderal .fuz (or a bare .lip) and print its frames.

Format, reverse-engineered 2026-10-17 from the Nehrimese DBVO pack (all 3551 files agree):

  .fuz  = "FUZE" | u32 version (1) | u32 lipSize | lip bytes | xWMA RIFF audio
  .lip  = u32 version (1) | u32 decodedSize | u32 13 | body
  body  = zero-run compressed: byte 0x00 + u16 n -> n zero bytes; any other byte is a literal.
          Decodes to: u32 frameCount | i32 (unknown, -12..0) | u32 16 | frameCount x 33 float32
          and decodedSize == len(decoded) + 16 for every file.
  frame = 16 phoneme weights (Aah BigAah BMP ChJSh DST Eee Eh FV I K N Oh OohQ R Th W)
          + 17 modifiers (BlinkL BlinkR BrowDownL/R BrowInL/R BrowUpL/R LookDown/Left/Right/Up
          SquintL/R HeadPitch HeadRoll HeadYaw); blinks/brows/look are 0..1, head is signed.

Frames run at ~30 fps: frameCount = 30.56 * audioSeconds + 10 across the pack.

Usage: python -I lipdump.py <file.fuz|file.lip> [--frames]
"""
import struct
import sys

PHONEMES = ["Aah", "BigAah", "BMP", "ChJSh", "DST", "Eee", "Eh", "FV",
            "I", "K", "N", "Oh", "OohQ", "R", "Th", "W"]


def lip_bytes(data):
    if data[:4] == b"FUZE":
        size = struct.unpack_from("<I", data, 8)[0]
        return data[12:12 + size]
    return data


def decode(lip):
    version, decoded_size, magic = struct.unpack_from("<III", lip, 0)
    if version != 1 or magic != 13:
        raise ValueError(f"unexpected header version={version} magic={magic}")
    out = bytearray()
    i = 12
    while i < len(lip):
        if lip[i] == 0:
            out += bytes(struct.unpack_from("<H", lip, i + 1)[0])
            i += 3
        else:
            out.append(lip[i])
            i += 1
    frames, unk, tracks = struct.unpack_from("<IiI", out, 0)
    if len(out) != 12 + frames * 132 or decoded_size != len(out) + 16:
        raise ValueError(f"size mismatch: decoded {len(out)}, frames {frames}, header {decoded_size}")
    return [struct.unpack_from("<33f", out, 12 + 132 * k) for k in range(frames)], unk, tracks


def main():
    path = sys.argv[1]
    frames, unk, tracks = decode(lip_bytes(open(path, "rb").read()))
    print(f"{path}: {len(frames)} frames (~{len(frames) / 30:.2f}s at 30 fps), unk={unk}, tracks={tracks}")
    if "--frames" in sys.argv:
        for k, f in enumerate(frames):
            lit = " ".join(f"{PHONEMES[j]}={f[j]:.2f}" for j in range(16) if f[j] > 0.01)
            print(f"{k / 30:6.2f}s  {lit}")


if __name__ == "__main__":
    main()
