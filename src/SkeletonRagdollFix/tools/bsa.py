"""Minimal SSE BSA (v105) lister/extractor. usage: bsa.py ARCHIVE PATTERN [OUTDIR]"""
import fnmatch
import os
import struct
import sys

BS = chr(92)


def read(path):
    f = open(path, "rb")
    magic, ver, off, flags, nfold, nfile, lfold, lfile = struct.unpack("<4sIIIIIII", f.read(32))
    assert magic == b"BSA\0", magic
    compressed_default = bool(flags & 0x4)
    embed = bool(flags & 0x100)
    f.seek(off)
    counts = []
    for _ in range(nfold):
        _h, cnt, _pad, _o = struct.unpack("<QIIQ", f.read(24))
        counts.append(cnt)
    files = []
    for cnt in counts:
        n = f.read(1)[0]
        folder = f.read(n)[:-1].decode("cp1252")
        for _ in range(cnt):
            _h, size, o = struct.unpack("<QII", f.read(16))
            files.append((folder, size, o))
    names = f.read(lfile).split(b"\0")
    out = [(folder + BS + fn.decode("cp1252"), size, o) for (folder, size, o), fn in zip(files, names)]
    return f, out, compressed_default, embed


def main():
    path, pat = sys.argv[1], sys.argv[2]
    outdir = sys.argv[3] if len(sys.argv) > 3 else None
    f, files, cdef, embed = read(path)
    for name, size, o in files:
        if not fnmatch.fnmatch(name.lower(), pat.lower()):
            continue
        comp = cdef ^ bool(size & 0x40000000)
        size &= 0x3FFFFFFF
        print(name, size, "compressed" if comp else "")
        if outdir:
            f.seek(o)
            data = f.read(size)
            if embed:
                data = data[1 + data[0]:]
            if comp:
                import lz4.frame
                data = lz4.frame.decompress(data[4:])
            p = os.path.join(outdir, *name.split(BS))
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "wb").write(data)


main()
