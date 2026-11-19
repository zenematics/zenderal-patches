"""Generate the Kata elemental shield no-stack overrides -- never hand-edit their MagicEffects/ files.

Player report (GreaseLord, 2026-11-17): Fire Shield (Rank I) and Fire Shield (Rank III) both active.

KataPUMB_SpellPackage.esp ships Fire/Frost/Shock Shield in five ranks, each rank its own MGEF with the
PeakValueModifier archetype (ResistFire/Frost/Shock). The engine keeps only the strongest of the
PeakValueModifier effects that share an Association keyword; without one, every effect counts. Kata made
one keyword per element (Kata_FireShield 0098C5, Kata_FrostShield 0098C6, Kata_ShockShield 0098C7) and
put it on each Rank I's Keywords, but set it as the Association on Fire Shield I alone. So all fifteen
ranks stacked (all five Fire ranks = 8+14+20+35+50 = 127% fire resistance). No list plugin overrides
these MGEFs, and nothing else references the three keywords.

Each override = Kata's record verbatim + its element's keyword in Keywords (as Kata's Rank I has) and as
the archetype's Association. Only the strongest rank of each element counts; the three elements still
stack with each other, as Kata's keywords are per element.

Writes and deletes only *_KataPUMB_SpellPackage.esp.yaml files in MagicEffects/, so it is independent
of the other steps' order. Needs KataPUMB_SpellPackage.esp as a master (RecordData.yaml).
"""
import glob
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "reference", "mods", "KataPUMBSpellPackage", "MagicEffects")
OUT = os.path.join(ROOT, "src", "MagicPatches", "MagicPatchesESP", "MagicEffects")
SUFFIX = "_KataPUMB_SpellPackage.esp.yaml"
KEYWORDS = {
    "Fire": ("ResistFire", "0098C5:KataPUMB_SpellPackage.esp"),
    "Frost": ("ResistFrost", "0098C6:KataPUMB_SpellPackage.esp"),
    "Shock": ("ResistShock", "0098C7:KataPUMB_SpellPackage.esp"),
}
RANKS = ("I", "II", "III", "IV", "V")
CRLF = "\r\n"


def patch(text, av, kw):
    nl = CRLF if CRLF in text else "\n"
    lines = text.split(nl)
    # Keywords: add the element keyword after the existing entries if missing.
    i = lines.index("Keywords:")
    j = i + 1
    while j < len(lines) and lines[j].startswith("- "):
        j += 1
    if "- " + kw not in lines[i + 1:j]:
        lines.insert(j, "- " + kw)
    # Archetype: Association right after its ActorValue.
    a = lines.index("Archetype:")
    assert lines[a + 1] == "  MutagenObjectType: MagicEffectPeakValueModArchetype", lines[a + 1]
    assert lines[a + 2] == "  ActorValue: " + av, lines[a + 2]
    if lines[a + 3].startswith("  Association:"):
        assert lines[a + 3] == "  Association: " + kw, lines[a + 3]
    else:
        assert not lines[a + 3].startswith("  "), lines[a + 3]
        lines.insert(a + 3, "  Association: " + kw)
    return nl.join(lines)


def main():
    for old in glob.glob(os.path.join(OUT, "*" + SUFFIX)):
        os.remove(old)
    written = 0
    for elem, (av, kw) in KEYWORDS.items():
        for rank in RANKS:
            hits = glob.glob(os.path.join(SRC, "Kata_%sShield_%s - *%s" % (elem, rank, SUFFIX)))
            assert len(hits) == 1, (elem, rank, hits)
            with open(hits[0], "r", encoding="utf-8", newline="") as f:
                text = f.read()
            new = patch(text, av, kw)
            assert new.count(kw) == 2, (hits[0], new.count(kw))
            assert new != text or (elem == "Fire" and rank == "I"), hits[0]
            with open(os.path.join(OUT, os.path.basename(hits[0])), "w", encoding="utf-8", newline="") as f:
                f.write(new)
            written += 1
    assert written == 15, written
    print("wrote %d shield MGEF overrides" % written)


if __name__ == "__main__":
    main()
