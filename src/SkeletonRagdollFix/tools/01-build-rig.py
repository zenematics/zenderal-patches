"""Build a skeletons.hkx whose ragdoll actually bends.

Enderal's (and Skyrim's) skeleton ragdoll rig, meshes/actors/draugr/character assets/skeletons.hkx, locks every limb:
14 hkpLimitedHingeConstraints at +-1 degree, and their hinge axes run ALONG each bone, so even a wider limit would only
spin the bone around its own length. The neck ragdoll joint is 1 degree. Skeletons therefore fly as a rigid A-pose.
See arch-docs/patches/SkeletonRagdollFix.md.

The skeleton's bind pose matches the draugr rig's (skeleton.hkx) almost exactly, and the draugr's knees, ankles, elbows
and wrists are proper hinges. So each skeleton hinge gets:
  * calf / foot / forearm / hand: the draugr hinge's world axis and range, same side;
  * thigh / upper arm / head / jaw (free ragdoll joints on draugr): a forward/back swing hinge about world X;
  * neck ragdoll joint: the draugr's twist +-5, cone 5, planes +-30.
Each hinge's frame A and frame B rotations are rewritten from the same world axes (axis, perp, axis x perp) mapped into
each body's bind-pose frame, so the bind pose still measures 0 degrees. Pivots (frame translations) are untouched.

The file is PATCHED IN PLACE, not rebuilt: an XML round trip through hkxconv/HKX2 loses physics precision (8885 bytes
differ; FLT_MAX and sub-1e-6 values change). Only these floats change: each hinge's frame rotation x/y/z and its angle
limits, and the neck's limits. Both copies of every joint in the file are patched.

Convention (verified on the draugr rig, asserted below): a constraint's entities are (A, B); frame rotations are
column-major (axis, perp, perp2) in the body's local frame; +angle rotates A about the world axis (right hand). The
draugr calf's range -110..0 is knee flexion because +angle swings its foot forward.

Inputs - always the WINNING copies. In Zenderal that is XP32 Maximum Skeleton Special Extended's loose
meshes/actors/draugr/character assets/skeletons.hkx and skeleton.hkx (they beat Enderal's E - Meshes.bsa copies,
which tools/bsa.py can extract). Convert with src/EnderalPairedAnims/tools/hkxconv in plain mode:
  skeletons.hkx  - the winning skeleton rig (binary, the one patched)
  skeletons.xml  - the same file as XML (bind-pose body frames, constraint frames)
  draugr.xml     - the winning skeleton.hkx (draugr rig) as XML

usage: python 01-build-rig.py skeletons.hkx skeletons.xml draugr.xml <out skeletons.hkx>
"""
import math
import re
import struct
import sys
import xml.etree.ElementTree as ET

SWING_X = (1.0, 0.0, 0.0)
# skeleton joint -> ("draugr", draugr constraint name) | ("swing", (min, max) degrees, +angle meaning)
JOINTS = {
    "Ragdoll_NPC L Calf [LClf]01": ("draugr", "Ragdoll_NPC L Calf [LClf]"),
    "Ragdoll_NPC R Calf [RClf]01": ("draugr", "Ragdoll_NPC R Calf [RClf]"),
    "Ragdoll_NPC L Foot [LLft ]01": ("draugr", "Ragdoll_NPC L Foot [Lft ]"),
    "Ragdoll_NPC R Foot [Rft ]01": ("draugr", "Ragdoll_NPC R Foot [Rft ]"),
    "Ragdoll_NPC L Forearm [LLar]01": ("draugr", "Ragdoll_NPC L Forearm [LLar]"),
    "Ragdoll_NPC R Forearm [RLar]01": ("draugr", "Ragdoll_NPC R Forearm [RLar]"),
    "Ragdoll_NPC L Hand [LHnd]01": ("draugr", "Ragdoll_NPC L Hand [LHnd]"),
    "Ragdoll_NPC R Hand [RHnd]01": ("draugr", "Ragdoll_NPC R Hand [RHnd]"),
    "Ragdoll_NPC L Thigh [LThg]01": ("swing", (-25.0, 60.0)),      # + swings the leg forward (hip flexion)
    "Ragdoll_NPC R Thigh [RThg]01": ("swing", (-25.0, 60.0)),
    "Ragdoll_NPC L UpperArm [LUar]01": ("swing", (-40.0, 70.0)),   # + swings the arm forward
    "Ragdoll_NPC R UpperArm [RUar]01": ("swing", (-40.0, 70.0)),
    "Ragdoll_NPC Head [Head]01": ("swing", (-30.0, 20.0)),         # - nods the head forward
    "Ragdoll_NPC Head [Jaw]01": ("swing", (-15.0, 0.0)),           # - opens the jaw
}
NECK = "Ragdoll_NPC Neck [Neck]01"
NECK_LIMITS = {"twist": (-5.0, 5.0), "cone": 5.0, "planes": (-30.0, 30.0)}
LOCKED = 0.017453  # the +-1 degree the vanilla rig uses
KNOWN_MISALIGNED = {"Ragdoll_NPC R Foot [Rft ]01"}


def vecs(txt):
    return [tuple(map(float, g.split())) for g in re.findall(r"\(([^)]*)\)", txt)]


def sub(a, b): return tuple(x - y for x, y in zip(a, b))
def dot(a, b): return sum(x * y for x, y in zip(a, b))
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def norm(a):
    n = math.sqrt(dot(a, a))
    return tuple(x / n for x in a)
def mat_vec(cols, v): return tuple(sum(cols[c][r] * v[c] for c in range(3)) for r in range(3))   # R @ v
def mat_t_vec(cols, v): return tuple(dot(cols[r], v) for r in range(3))                         # R^T @ v


def load(path):
    root = ET.parse(path)
    objs = {o.get("name"): o for o in root.iter("hkobject") if o.get("name")}
    bodies = {}
    for key, o in objs.items():
        if o.get("class") == "hkpRigidBody":
            tr = vecs(o.find(".//hkparam[@name='motionState']").find(".//hkparam[@name='transform']").text)
            bodies[key] = (o.find("hkparam[@name='name']").text, [tr[0], tr[1], tr[2]], tr[3])
    cons = {}
    for o in objs.values():
        if o.get("class") != "hkpConstraintInstance":
            continue
        data = objs[o.find("hkparam[@name='data']").text]
        a, b = o.find("hkparam[@name='entities']").text.split()
        ta = vecs(data.find(".//hkparam[@name='transformA']").text)
        tb = vecs(data.find(".//hkparam[@name='transformB']").text)
        lim = data.find(".//hkparam[@name='angLimit']")
        cons[o.find("hkparam[@name='name']").text] = {
            "class": data.get("class"), "A": bodies[a], "B": bodies[b], "ta": ta, "tb": tb,
            "lim": None if lim is None else tuple(math.degrees(float(lim.find(f".//hkparam[@name='{n}']").text)) for n in ("minAngle", "maxAngle")),
        }
    return cons


def packfile_links(data):
    """Map every constraint-data object in an hk_2010 packfile to the names of the hkpConstraintInstances using it.
    Section header: name[20], absStart, local/global/virtual fixups, exports, imports, end (offsets in the section)."""
    secs = []
    for k in range(struct.unpack_from("<i", data, 20)[0]):
        o = 0x40 + k * 0x30
        secs.append((data[o:o + 20].split(b"\0")[0].decode(), struct.unpack_from("<7I", data, o + 20)))
    cls_start = secs[0][1][0]
    start, loc, glob, virt, exp, _, _ = secs[2][1]
    objects = []  # (offset in data section, class name)
    for o in range(start + virt, start + exp, 12):
        obj, _, name_off = struct.unpack_from("<3i", data, o)
        if obj == -1:
            continue
        name = data[cls_start + name_off:].split(b"\0")[0].decode()
        objects.append((obj, name))
    objects.sort()
    ends = {obj: (objects[i + 1][0] if i + 1 < len(objects) else loc) for i, (obj, _) in enumerate(objects)}
    local = {}
    for o in range(start + loc, start + glob, 8):
        src, dst = struct.unpack_from("<2i", data, o)
        if src != -1:
            local[src] = dst
    links = {}
    for o in range(start + glob, start + virt, 12):
        src, sec, dst = struct.unpack_from("<3i", data, o)
        if src == -1:
            continue
        owner = max((obj for obj, _ in objects if obj <= src), default=None)
        if owner is None or dict(objects)[owner] != "hkpConstraintInstance" or dict(objects).get(dst) is None:
            continue
        if not dict(objects)[dst].endswith("ConstraintData"):
            continue
        names = [data[start + local[s]:].split(b"\0")[0].decode() for s in local if owner <= s < ends[owner]
                 and data[start + local[s]:start + local[s] + 8].startswith(b"Ragdoll_")]
        assert len(names) == 1, (owner, names)
        links.setdefault(start + dst, set()).add(names[0])   # absolute file offset of the data object
    return links


def world_axis(c):
    return norm(mat_vec(c["A"][1], c["ta"][0]))


def frames(c, axis):
    """(axis, perp, perp2) in world, then in A's and B's local frames (columns)."""
    _, ra, xa = c["A"]
    pivot = tuple(p + x for p, x in zip(mat_vec(ra, c["ta"][3]), xa))
    along = sub(xa, pivot) if dot(sub(xa, pivot), sub(xa, pivot)) > 1.0 else (0.0, 0.0, -1.0)
    perp = cross(axis, norm(along))
    if dot(perp, perp) < 0.04:  # axis ~ parallel to the bone: any perpendicular will do
        perp = cross(axis, (0.0, 1.0, 0.0))
    perp = norm(perp)
    world = (axis, perp, cross(axis, perp))
    local_a = [mat_t_vec(ra, w) for w in world]
    local_b = [mat_t_vec(c["B"][1], w) for w in world]
    return world, local_a, local_b


def main(in_hkx, sk_xml, dr_xml, out_hkx):
    sk, dr = load(sk_xml), load(dr_xml)
    # Convention check: on every original hinge both frames' axes coincide in world space - except the skeleton's
    # right foot, whose vanilla frames disagree by ~67 degrees (Bethesda's data; the rewrite below rebuilds both).
    for name, c in list(sk.items()) + list(dr.items()):
        if c["class"].endswith("LimitedHingeConstraintData"):
            wa, wb = world_axis(c), norm(mat_vec(c["B"][1], c["tb"][0]))
            if name in KNOWN_MISALIGNED:
                print(f"note: {name} frames disagree at bind pose (dot {dot(wa, wb):.3f}), rebuilt")
                continue
            assert dot(wa, wb) > 0.999, f"frame convention broken on {name}: {wa} vs {wb}"
    # Sign check on the draugr calf: +angle must swing the foot forward (+Y), so -110..0 is flexion.
    calf = dr["Ragdoll_NPC L Calf [LClf]"]
    assert calf["lim"][0] < -100 and abs(calf["lim"][1]) < 1, calf["lim"]
    # The calf body's origin sits on the knee pivot, so use the bone's direction (down, -Z) as the lever.
    assert cross(world_axis(calf), (0.0, 0.0, -1.0))[1] > 0.5, "draugr calf +angle does not swing the foot forward"

    data = bytearray(open(in_hkx, "rb").read())
    hinge_hits, neck_hits = [], []
    for off in range(0, len(data) - 12, 4):
        lo, hi, tau = struct.unpack_from("<3f", data, off)
        if abs(lo + LOCKED) < 1e-5 and abs(hi - LOCKED) < 1e-5:
            (hinge_hits if abs(tau - 1.0) < 1e-6 else neck_hits).append(off)
    assert len(hinge_hits) == 28 and len(neck_hits) == 2, (len(hinge_hits), len(neck_hits))

    # Left and right forearms/hands have byte-identical constraint data, so a block is named through the packfile's
    # fixups: the hkpConstraintInstance whose `data` pointer targets it.
    links = packfile_links(data)

    def owner(off):
        blocks = [d for d in links if d <= off and off - d < 512]
        assert len(blocks) >= 1, off
        names = links[max(blocks)]
        assert len(names) == 1, (off, names)
        name = next(iter(names))
        # Cross-check with the XML: frame B's translation (72 bytes before the limits) must match that joint's.
        tb = struct.unpack_from("<3f", data, off - 72)
        assert all(abs(x - y) < 2e-5 for x, y in zip(tb, sk[name]["tb"][3])), (off, name, tb)
        return name

    done = {}
    for off in hinge_hits:
        name = owner(off)
        c = sk[name]
        kind, arg = JOINTS[name]
        if kind == "draugr":
            ref = dr[arg]
            axis, (lo, hi) = world_axis(ref), ref["lim"]
        else:
            axis, (lo, hi) = SWING_X, arg
        _, local_a, local_b = frames(c, axis)
        for i in range(3):
            struct.pack_into("<3f", data, off - 184 + 16 * i, *local_a[i])
            struct.pack_into("<3f", data, off - 120 + 16 * i, *local_b[i])
        struct.pack_into("<2f", data, off, math.radians(lo), math.radians(hi))
        done[name] = done.get(name, 0) + 1
        print(f"{off:6d} {name:34s} axis {tuple(round(v, 2) for v in axis)} range {lo:+.0f}..{hi:+.0f}")
    assert set(done) == set(JOINTS) and all(v == 2 for v in done.values()), done

    for off in neck_hits:
        assert abs(struct.unpack_from("<f", data, off + 24)[0] - LOCKED) < 1e-5      # cone max
        assert abs(struct.unpack_from("<f", data, off + 48)[0] - 0.8) < 1e-6         # planes tau
        struct.pack_into("<2f", data, off, *map(math.radians, NECK_LIMITS["twist"]))
        struct.pack_into("<f", data, off + 24, math.radians(NECK_LIMITS["cone"]))
        struct.pack_into("<2f", data, off + 40, *map(math.radians, NECK_LIMITS["planes"]))
        print(f"{off:6d} {NECK:34s} twist +-5, cone 5, planes +-30")

    open(out_hkx, "wb").write(data)
    print(f"wrote {out_hkx}")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    main(*sys.argv[1:])
