"""Merge CBBE's shipped body morphs with a BodySlide build of CBBE NeverNude into one femalebody.tri.

CBBE's FOMOD (Slim + NeverNude + RaceMenu Morphs) ships femalebody.tri with morphs for the CBBE body shape
only, so RaceMenu body sliders move the body but not the NeverNude Bra/Panty shapes (the bra sinks into the
breasts). BodySlide's "CBBE NeverNude" build with Build Morphs adds Bra and Panty morphs, but its CBBE morph
set lacks 6 of the shipped ones. Output: every shipped CBBE morph, the build's CBBE morphs the shipped file
lacks, and the build's Bra and Panty morphs. Morph records are copied byte for byte; the trailing UV-morph
section must be identical in both inputs. CBBE's meshes are not touched.

Usage:  python 01-merge-tri.py <CBBE mod's femalebody.tri> <BodySlide build's femalebody.tri> <output .tri>
"""
import struct
import sys


def parse(path):
    data = open(path, 'rb').read()
    assert data[:4] == b'PIRT', path
    i = 4
    count, = struct.unpack_from('<H', data, i)
    i += 2
    shapes = {}
    for _ in range(count):
        n = data[i]
        name = data[i + 1:i + 1 + n].decode()
        i += 1 + n
        mcount, = struct.unpack_from('<H', data, i)
        i += 2
        morphs = {}
        for _ in range(mcount):
            start = i
            n = data[i]
            mname = data[i + 1:i + 1 + n].decode()
            i += 1 + n
            _, vcount = struct.unpack_from('<fH', data, i)
            i += 6 + 8 * vcount
            morphs[mname] = data[start:i]
        shapes[name] = morphs
    return shapes, data[i:]


def main(shipped_path, built_path, out_path):
    shipped, shipped_tail = parse(shipped_path)
    built, built_tail = parse(built_path)
    assert list(shipped) == ['CBBE'], list(shipped)
    assert set(built) == {'CBBE', 'Bra', 'Panty'}, list(built)
    assert shipped_tail == built_tail, 'UV-morph sections differ'

    body = dict(shipped['CBBE'])
    added = [m for m in built['CBBE'] if m not in body]
    for m in added:
        body[m] = built['CBBE'][m]
    merged = {'Bra': built['Bra'], 'CBBE': body, 'Panty': built['Panty']}

    out = bytearray(b'PIRT' + struct.pack('<H', len(merged)))
    for name, morphs in merged.items():
        out += bytes([len(name)]) + name.encode() + struct.pack('<H', len(morphs))
        for record in morphs.values():
            out += record
    out += shipped_tail
    open(out_path, 'wb').write(out)

    check, _ = parse(out_path)
    assert {k: len(v) for k, v in check.items()} == {k: len(v) for k, v in merged.items()}
    print(f"CBBE: {len(shipped['CBBE'])} shipped + {len(added)} from the build = {len(body)}; "
          f"Bra {len(built['Bra'])}; Panty {len(built['Panty'])}; {len(out)} bytes -> {out_path}")


if __name__ == '__main__':
    main(*sys.argv[1:4])
