"""Zenderal - High Poly Default Heads: the vanilla humanoid head parts become High Poly Head's.

Enderal's 17 male chargen presets (`_00E_CharacterTemplate_*`) and every playable race use the vanilla heads
(`MaleHeadNord`, `MaleHeadBreton`, ...: `Actors\\Character\\Character Assets\\MaleHead.nif`), while the list's beard
sets (High Poly Head's own, HPH SV Beards, The Art of Beard for HPH, Beards of Power HPH version) are fitted to
High Poly Head. On a vanilla head those beards sit wrong and the head pokes through their stubble shells (pale
patches on the chin and upper lip; RaceMenu's sculpt view showed the head through the facial-hair mesh).

High Poly Head's `00KLH_<name>` head part is the vanilla `<name>` record with only the mesh and the three .tri
paths moved to `KL\\High Poly Head\\` (same texture set, valid races, flags, type, part types). This copies each
vanilla record verbatim and swaps exactly those four paths for HPH's, asserting everything else matches, so every
preset, every existing character and any NPC without baked facegen gets the high-poly head. NPCs with facegen keep
theirs. The plugin needs no HPH master: it only names HPH's files.

Usage: python 01-build-high-poly-default-heads.py <serialized High Poly Head.esm folder>
       (reference/mods/HighPolyHead; vanilla records come from reference/base/Skyrim)
"""
import os
import re
import shutil
import sys

HPH = sys.argv[1] if len(sys.argv) > 1 else os.path.join("reference", "mods", "HighPolyHead")
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
VANILLA = os.path.join(REPO, "reference", "base", "Skyrim", "HeadParts")
OUT = os.path.join(HERE, "..", "HighPolyDefaultHeadsESP", "HeadParts")
RACES = ("Nord", "Breton", "Imperial", "Redguard", "HighElf", "WoodElf", "DarkElf", "Orc", "Elder")
HEADS = [f"{sex}Head{race}" for sex in ("Male", "Female") for race in RACES]
SAME = ("Flags", "Type", "TextureSet", "ValidRaces")


def load(folder, prefix=""):
    out = {}
    for f in os.listdir(folder):
        t = open(os.path.join(folder, f), encoding="utf-8").read()
        e = re.search(r"^EditorID: (\S+)", t, re.M).group(1)
        if e.startswith(prefix):
            out[e[len(prefix):]] = (f, t)
    return out


def block(t, key):
    """A top-level YAML key's value (inline or the indented lines under it)."""
    m = re.search(rf"^{key}:(.*)\n((?:[ -].*\n)*)", t + "\n", re.M)
    return (m.group(1) + "\n" + m.group(2)).strip() if m else None


def parts(t):
    return re.findall(r"- PartType: (\S+)\r?\n  FileName: (.+?)\r?$", t, re.M)


def model_file(t):
    return re.search(r"^Model:\r?\n  File: (.+?)\r?$", t, re.M).group(1)


van = load(VANILLA)
hph = load(os.path.join(HPH, "HeadParts"), "00KLH_")
if os.path.isdir(OUT):
    shutil.rmtree(OUT)
os.makedirs(OUT)
for name in HEADS:
    vf, vt = van[name]
    _, ht = hph[name]
    for key in SAME:
        if key == "TextureSet" and block(vt, key) is None:
            # Enderal's FemaleHeadNord has no texture set (HPH's names SkinHeadFemaleNord 03B522); keep Enderal's
            print(f"  {name}: no TextureSet in Enderal's record (HPH: {block(ht, key)}) - kept as Enderal has it")
            continue
        assert block(vt, key) == block(ht, key), (name, key, block(vt, key), block(ht, key))
    vp, hp = parts(vt), parts(ht)
    assert [p[0] for p in vp] == [p[0] for p in hp] and len(vp) == 3, (name, vp, hp)
    new = vt.replace(f"  File: {model_file(vt)}", f"  File: {model_file(ht)}", 1)
    for (typ, vfile), (_, hfile) in zip(vp, hp):
        a, b = f"  FileName: {vfile}", f"  FileName: {hfile}"
        assert new.count(a) == 1, (name, a)
        new = new.replace(a, b)
    assert model_file(new) == model_file(ht) and parts(new) == hp
    changed = [l for l, o in zip(new.splitlines(), vt.splitlines()) if l != o]
    assert len(changed) == 4 and len(new.splitlines()) == len(vt.splitlines()), (name, changed)
    # a non-localized plugin stores the (never displayed) head part name in English only: write it the way
    # Spriggit reads it back, so the source round-trips
    nl = "\r\n" if "\r\n" in new else "\n"
    new, n = re.subn(r"^Name:\r?\n  TargetLanguage: English\r?\n  Values:\r?\n(?:  [ -].*\r?\n)+",
                     f"Name:{nl}  TargetLanguage: English{nl}  Value: {name}{nl}", new, count=1, flags=re.M)
    assert n == 1, (name, "Name block")
    with open(os.path.join(OUT, vf), "w", encoding="utf-8", newline="") as f:
        f.write(new)
    print(f"  {name:18} -> {model_file(ht)}")
print(f"wrote {len(HEADS)} head part overrides")
