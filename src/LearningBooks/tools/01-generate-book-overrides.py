#!/usr/bin/env python3
"""Generate the 72 book overrides for Zenderal - Learning Books Grant Learning Points.esp.

Every Enderal learning book (48x _00E_Lehrbuch<Skill>To{25,50,75,100}) and crafting book
(24x _00E_Handwerksbuch<Skill>To{25,50,75,99}) is an ALCH whose consume effect spends a
point (Lernpunkte 031ACB / Handwerkspunkte 085A79) and raises a skill. This patch inverts
that: each book GRANTS 1 point of its currency instead - EGO SE - Leveling Redone provides
the skill-raising path.

Method (guardrails 4/5/11): the winner of all 72 records is EGO (Enderal SE - Gameplay
Overhaul.esp), which reprices them and swaps 8 of the learning books' keyword to its own
LehrbuchForbidden 001FB7 (all four tiers of Conjuration/Entropy and Illusion/Psionics).
So each override is EGO's serialized YAML copied BYTE-VERBATIM with exactly one change:
the single "- BaseEffect:" line is repointed from the per-book spend-script MGEF to this
plugin's grant MGEF (learning -> 000800, crafting -> 000801). Prices, names, keywords,
ObjectBounds and effect Data ride through untouched.

Deliberately NOT matched (the To-tier filename pattern excludes them): the Plus2 grant
books (_00E_Lehrbuch_Plus2* and EGO's _Gaboff pair - they already grant), the memory
book _00E_Erinnerungsbuch (+1 MEMORY point - a separate currency this patch must never
touch), _00E_KnowledgeBook, and the FS Apotheosis books.

Inputs (regenerate with /spriggit-decompile-reference):
  reference/mods/EGO/esp/Ingestibles        (the 72 winning ALCH records)
  reference/base/Skyrim/MagicEffects        (to prove each detached MGEF is a spend-script one)

Output: src/LearningBooks/LearningBooksESP/Ingestibles/*_Skyrim.esm.yaml (wiped and
rewritten each run - NEVER hand-edit that folder). Asserts every count and fails loudly
on any EGO drift: file counts, the 8-file 001FB7 keyword set, one BaseEffect per file,
the old MGEF's script prefix, localization shape, and the FoodItem/NoAutoCalc/ConsumeSound
invariants.
"""
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
SRC = os.path.join(ROOT, "reference", "mods", "EGO", "esp", "Ingestibles")
MGEF_REF = os.path.join(ROOT, "reference", "base", "Skyrim", "MagicEffects")
OUT = os.path.join(ROOT, "src", "LearningBooks", "LearningBooksESP", "Ingestibles")

OWN_ESP = "Zenderal - Learning Books Grant Learning Points.esp"
LEARNING_MGEF = b"000800:" + OWN_ESP.encode("ascii")
CRAFTING_MGEF = b"000801:" + OWN_ESP.encode("ascii")

LEARNING_RE = re.compile(r"^_00E_Lehrbuch[A-Za-z]+To(25|50|75|100) - ([0-9A-F]{6})_Skyrim\.esm\.yaml$")
CRAFTING_RE = re.compile(r"^_00E_Handwerksbuch[A-Za-z]+To(25|50|75|99) - ([0-9A-F]{6})_Skyrim\.esm\.yaml$")

BASEEFFECT_RE = re.compile(rb"^- BaseEffect: ([0-9A-F]{6}):Skyrim\.esm\r?$", re.M)
KEYWORD_RE = re.compile(rb"^- (031ACD:Skyrim\.esm|001FB7:Enderal SE - Gameplay Overhaul\.esp)\r?$", re.M)

# EGO's deliberate keyword swap: these 8 (and ONLY these) carry LehrbuchForbidden 001FB7.
FORBIDDEN_BOOKS = {
    "_00E_LehrbuchConjurationTo25", "_00E_LehrbuchConjurationTo50",
    "_00E_LehrbuchConjurationTo75", "_00E_LehrbuchConjurationTo100",
    "_00E_LehrbuchIllusionTo25", "_00E_LehrbuchIllusionTo50",
    "_00E_LehrbuchIllusionTo75", "_00E_LehrbuchIllusionTo100",
}

fail_count = 0


def fail(msg):
    global fail_count
    fail_count += 1
    print("FAIL: %s" % msg)


def check_old_mgef(old_hex, want_prefixes, fname):
    """The detached MGEF must exist in base Enderal and carry a spend-script VMAD."""
    matches = [f for f in os.listdir(MGEF_REF) if f.endswith(" - %s_Skyrim.esm.yaml" % old_hex)]
    if len(matches) != 1:
        fail("%s: old BaseEffect %s -> %d matches in %s" % (fname, old_hex, len(matches), MGEF_REF))
        return
    with open(os.path.join(MGEF_REF, matches[0]), "rb") as f:
        mgef = f.read()
    m = re.search(rb"^  - Name: (\S+)\r?$", mgef, re.M)
    if not m or not m.group(1).decode("ascii").startswith(want_prefixes):
        fail("%s: old MGEF %s VMAD script %r does not start with %s - refusing to detach it"
             % (fname, matches[0], m and m.group(1), want_prefixes))


def main():
    for d in (SRC, MGEF_REF):
        if not os.path.isdir(d):
            sys.exit("Missing reference tree: %s (regenerate with /spriggit-decompile-reference)" % d)

    names = sorted(os.listdir(SRC))
    learning = [n for n in names if LEARNING_RE.match(n)]
    crafting = [n for n in names if CRAFTING_RE.match(n)]
    if len(learning) != 48:
        fail("expected 48 learning books in EGO tree, found %d" % len(learning))
    if len(crafting) != 24:
        fail("expected 24 crafting books in EGO tree, found %d" % len(crafting))

    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    for f in os.listdir(OUT):
        if f.endswith("_Skyrim.esm.yaml"):
            os.remove(os.path.join(OUT, f))

    forbidden_seen = set()

    for fname, is_learning in [(n, True) for n in learning] + [(n, False) for n in crafting]:
        editor_id = fname.split(" - ")[0]
        form_hex = (LEARNING_RE if is_learning else CRAFTING_RE).match(fname).group(2)
        with open(os.path.join(SRC, fname), "rb") as f:
            data = f.read()

        if (b"FormKey: %s:Skyrim.esm" % form_hex.encode("ascii")) not in data:
            fail("%s: FormKey does not match filename" % fname)
        if b"  Values:" in data:
            fail("%s: localized Values block - EGO is not Localized, wrong source tree?" % fname)
        for needle in (b"- NoAutoCalc", b"- FoodItem", b"ConsumeSound: 07EA3A:Skyrim.esm"):
            if needle not in data:
                fail("%s: missing expected %r" % (fname, needle))

        kws = KEYWORD_RE.findall(data)
        if len(kws) != 1:
            fail("%s: expected exactly one Lehrbuch(Forbidden) keyword, found %d" % (fname, len(kws)))
        elif kws[0].startswith(b"001FB7"):
            forbidden_seen.add(editor_id)

        effects = BASEEFFECT_RE.findall(data)
        if len(effects) != 1:
            fail("%s: expected exactly one '- BaseEffect: XXXXXX:Skyrim.esm' line, found %d"
                 % (fname, len(effects)))
            continue
        old_hex = effects[0].decode("ascii")
        # "_00E_Lehrboch" is SureAI's own typo on the four Block book scripts
        # (_00E_LehrbochBlock25/50/75/100 - verified real ReadPrimarySkillBook spend scripts).
        check_old_mgef(old_hex,
                       ("_00E_Lehrbuch", "_00E_Lehrboch") if is_learning else ("_00E_Handwerksbuch",),
                       fname)

        new_mgef = LEARNING_MGEF if is_learning else CRAFTING_MGEF
        out_data, n = BASEEFFECT_RE.subn(
            lambda m: b"- BaseEffect: " + new_mgef + (b"\r" if m.group(0).endswith(b"\r") else b""),
            data)
        if n != 1:
            fail("%s: BaseEffect rewrite count %d != 1" % (fname, n))
        with open(os.path.join(OUT, fname), "wb") as f:
            f.write(out_data)

    if forbidden_seen != FORBIDDEN_BOOKS:
        fail("LehrbuchForbidden 001FB7 set drifted from the known 8: +%s -%s"
             % (sorted(forbidden_seen - FORBIDDEN_BOOKS), sorted(FORBIDDEN_BOOKS - forbidden_seen)))

    # Post-pass over the output tree.
    out_files = [f for f in os.listdir(OUT) if f.endswith("_Skyrim.esm.yaml")]
    n_learn = n_craft = 0
    for fname in out_files:
        with open(os.path.join(OUT, fname), "rb") as f:
            data = f.read()
        if LEARNING_MGEF in data:
            n_learn += 1
        if CRAFTING_MGEF in data:
            n_craft += 1
        if BASEEFFECT_RE.search(data):
            fail("%s: an old Skyrim.esm BaseEffect survived the rewrite" % fname)
    if (len(out_files), n_learn, n_craft) != (72, 48, 24):
        fail("output tree: %d files, %d learning, %d crafting (want 72/48/24)"
             % (len(out_files), n_learn, n_craft))

    if fail_count:
        sys.exit("%d check(s) FAILED - EGO tree drifted or output is wrong; fix before building." % fail_count)
    print("OK: 72 overrides written (48 learning -> 000800, 24 crafting -> 000801); "
          "8 forbidden-keyword books confirmed; all detached MGEFs were spend-script ones.")


if __name__ == "__main__":
    main()
