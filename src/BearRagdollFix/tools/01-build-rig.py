"""Fix the bear ragdoll's right knee (meshes/actors/bear/character assets/skeleton.hkx).

Bethesda's bear rig (Skyrim - Animations.bsa, and XPMSE's copy, which wins in Zenderal) has one bad joint: the right
hind knee, Ragdoll_NPC RLeg02 (hkpLimitedHingeConstraintData, entities RLeg02 -> RLeg01). Its frame B is rotated 70
degrees about the hinge axis against frame A, so at bind pose the knee measures -70 degrees while its limits are
0..65. The moment the bear ragdolls, the solver snaps the knee 70+ degrees back into range: the hind leg flops and
twists (curator, 2026-11-01). Every other joint measures 0 at bind. The left knee (LLeg02) is clean: bind 0, -60..0.

Both knees' hinge axes point along world +X (left (1, 0.07, 0), right (1, -0.07, 0): mirror images with the same
sense of rotation), and the right ankle and elbow use the left's limits unchanged - so the right knee bends the same
way as the left. Fix: frame B is rewritten so its world axes equal frame A's (bind = 0 degrees), and the limits become
the left knee's -60..0, copied from the file. Frame A, pivots and every other joint are untouched.

The file is PATCHED IN PLACE (SkeletonRagdollFix's method: an XML round trip loses physics precision); both copies of
the joint (physics system + ragdoll instance) are patched. See arch-docs/patches/BearRagdollFix.md.

Inputs - the WINNING copy (XP32 Maximum Skeleton Special Extended's loose file), plus the same file as XML from
src/EnderalPairedAnims/tools/hkxconv (plain mode).

usage: python 01-build-rig.py skeleton.hkx skeleton.xml <out skeleton.hkx>
"""
import importlib.util
import math
import os
import struct
import sys

_spec = importlib.util.spec_from_file_location(
    "rig", os.path.join(os.path.dirname(__file__), "..", "..", "SkeletonRagdollFix", "tools", "01-build-rig.py"))
rig = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rig)

RIGHT = "Ragdoll_NPC RLeg02"
LEFT = "Ragdoll_NPC LLeg02"


def packfile_links(data):
    """SkeletonRagdollFix's packfile_links, bounds-checked: the bear file's virtual-fixup table runs to the end of the
    file (its last 12-byte step would read past EOF)."""
    secs = []
    for k in range(struct.unpack_from("<i", data, 20)[0]):
        o = 0x40 + k * 0x30
        secs.append((data[o:o + 20].split(b"\0")[0].decode(), struct.unpack_from("<7I", data, o + 20)))
    cls_start = secs[0][1][0]
    start, loc, glob, virt, exp, _, _ = secs[2][1]
    end = len(data)
    objects = []
    for o in range(start + virt, min(start + exp, end - 11), 12):
        obj, _, name_off = struct.unpack_from("<3i", data, o)
        if obj == -1:
            continue
        objects.append((obj, data[cls_start + name_off:].split(b"\0")[0].decode()))
    objects.sort()
    kinds = dict(objects)
    ends = {obj: (objects[i + 1][0] if i + 1 < len(objects) else loc) for i, (obj, _) in enumerate(objects)}
    local = {}
    for o in range(start + loc, min(start + glob, end - 7), 8):
        src, dst = struct.unpack_from("<2i", data, o)
        if src != -1:
            local[src] = dst
    links = {}
    for o in range(start + glob, min(start + virt, end - 11), 12):
        src, _sec, dst = struct.unpack_from("<3i", data, o)
        if src == -1:
            continue
        owner = max((obj for obj, _ in objects if obj <= src), default=None)
        if owner is None or kinds[owner] != "hkpConstraintInstance" or not kinds.get(dst, "").endswith("ConstraintData"):
            continue
        names = [data[start + local[s]:].split(b"\0")[0].decode() for s in local if owner <= s < ends[owner]
                 and data[start + local[s]:start + local[s] + 8].startswith(b"Ragdoll_")]
        assert len(names) == 1, (owner, names)
        links.setdefault(start + dst, set()).add(names[0])
    return links


def bind_angle(c):
    wa = [rig.norm(rig.mat_vec(c["A"][1], c["ta"][k])) for k in range(2)]
    wb = [rig.norm(rig.mat_vec(c["B"][1], c["tb"][k])) for k in range(2)]
    return math.degrees(math.atan2(rig.dot(rig.cross(wa[1], wb[1]), wa[0]), rig.dot(wa[1], wb[1])))


def limit_hits(data, lo, hi):
    hits = []
    for off in range(0, len(data) - 12, 4):
        a, b, tau = struct.unpack_from("<3f", data, off)
        if abs(a - lo) < 1e-6 and abs(b - hi) < 1e-6 and abs(tau - 1.0) < 1e-6:
            hits.append(off)
    return hits


def main(in_hkx, xml, out_hkx):
    cons = rig.load(xml)
    right, left = cons[RIGHT], cons[LEFT]
    # the defect, as measured; refuse to touch a file that does not have it (a fixed or different rig)
    assert abs(bind_angle(right) + 70.0) < 1.0, f"right knee bind angle {bind_angle(right):.1f}, expected -70"
    assert abs(bind_angle(left)) < 0.5, f"left knee bind angle {bind_angle(left):.1f}, expected 0"
    assert abs(right["lim"][0]) < 0.01 and abs(right["lim"][1] - 65.0) < 0.01, right["lim"]
    # same sense of rotation: both axes along +X
    for c in (right, left):
        assert rig.norm(rig.mat_vec(c["A"][1], c["ta"][0]))[0] > 0.99

    data = bytearray(open(in_hkx, "rb").read())
    left_hits = limit_hits(data, *map(math.radians, left["lim"]))
    right_hits = limit_hits(data, *map(math.radians, right["lim"]))
    assert len(right_hits) == 2, f"{len(right_hits)} right-knee limit blocks, expected 2"
    links = packfile_links(data)

    def owner(off):
        blocks = [d for d in links if d <= off and off - d < 512]
        names = links[max(blocks)]
        assert len(names) == 1, (off, names)
        return next(iter(names))

    assert left_hits and all(owner(o) == LEFT for o in left_hits), [owner(o) for o in left_hits]
    left_lo, left_hi = struct.unpack_from("<2f", data, left_hits[0])   # the left knee's own floats, bit for bit

    # frame B (in body B's local frame) = frame A's world axes mapped into B
    RA, RB = right["A"][1], right["B"][1]
    world = [rig.norm(rig.mat_vec(RA, right["ta"][k])) for k in range(3)]
    local_b = [rig.mat_t_vec(RB, w) for w in world]
    for off in right_hits:
        assert owner(off) == RIGHT, (off, owner(off))
        # layout as in SkeletonRagdollFix: frame B rotation at -120, its translation at -72 (cross-checked with the XML)
        tb = struct.unpack_from("<3f", data, off - 72)
        assert all(abs(x - y) < 2e-5 for x, y in zip(tb, right["tb"][3])), (off, tb)
        for i in range(3):
            old = struct.unpack_from("<3f", data, off - 120 + 16 * i)
            assert all(abs(x - y) < 2e-5 for x, y in zip(old, right["tb"][i])), (off, i, old)
            struct.pack_into("<3f", data, off - 120 + 16 * i, *local_b[i])
        struct.pack_into("<2f", data, off, left_lo, left_hi)
        print(f"{off:6d} {RIGHT}: frame B rotated onto frame A (bind 0), limits {math.degrees(left_lo):+.0f}..{math.degrees(left_hi):+.0f}")

    open(out_hkx, "wb").write(data)
    print(f"wrote {out_hkx}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
