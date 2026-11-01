"""Path-preserving SE BSA (v105) reader, built on the SettingsApplier capture reader's LZ4 decoder."""
import os, re, struct, importlib.util

_here = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    'capbsa', os.path.join(_here, '..', '..', 'SettingsApplier', 'tools', 'capture', 'bsa.py'))
_cap = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_cap)


def listing(path):
    """Return {lowercase 'dir\\file': (size, offset, compressed)} for an SE BSA."""
    d = open(path, 'rb').read()
    magic, ver, fro, aflags, fcount, filecount, tfnl, tfil, ff = struct.unpack_from('<4sIIIIIIII', d, 0)
    assert magic == b'BSA\x00' and ver == 105, (magic, ver)
    p = fro; counts = []
    for _ in range(fcount):
        h, c, pad, off = struct.unpack_from('<QIIQ', d, p); p += 24; counts.append(c)
    files = []
    for c in counts:
        ln = d[p]; name = d[p + 1:p + ln].rstrip(b'\0').decode('latin1'); p += 1 + ln
        for _ in range(c):
            h, size, off = struct.unpack_from('<QII', d, p); p += 16; files.append([name, size, off])
    names = d[p:p + tfil].split(b'\0')
    out = {}
    for f, n in zip(files, names):
        full = (f[0] + '\\' + n.decode('latin1')).lower()
        size = f[1]; comp = bool(aflags & 4) ^ bool(size & 0x40000000)
        out[full] = (size & 0x3FFFFFFF, f[2], comp, bool(aflags & 0x100))
    return d, out


def read(d, entry):
    size, off, comp, embed = entry
    q = off
    if embed:
        ln = d[q]; q += 1 + ln; size -= 1 + ln
    blob = d[q:q + size]
    return _cap.lz4_frame(blob[4:]) if comp else blob
