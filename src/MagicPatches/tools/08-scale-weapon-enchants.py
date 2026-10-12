#!/usr/bin/env python3
"""Double the strength of Enderal's weapon enchantments for Zenderal - Magic Patches.esp.

Why: weapon enchantments are weak in base Enderal (Boneripper's Absorb Health is 3 per
hit on a 14-damage sword), and EGO cuts most damage/absorb ones further (Boneripper -> 2).
Nothing scales them in play: EGO's XionEnchantmentBuff / XionEnchantDouble perks touch
ModEnchantmentPower, which only applies to player-crafted enchantments, and its x1.2
XionMagicDamage perk explicitly skips weapon enchantments (XionWeaponEnch keyword).

Rule: every damage/absorb effect (SCALED_MGEFS) on an enchantment that a weapon actually
carries gets  magnitude = FACTOR x max(base Enderal's value, live value)  - i.e. double
base Enderal, undoing EGO's cuts, except where EGO RAISED a value (Winter's Edge 6 -> 13),
which is doubled from EGO's instead so nothing ends up weaker than today. Effects and
whole enchantments EGO added (no base value) double EGO's. Riders (slow, turn undead,
paralysis, fear, crit dummies) are untouched.

Charge: these records are auto-calc, so the engine would reprice them from the new
magnitudes and every weapon would empty its charge ~2.1x faster. Each override that is
auto-calc therefore gets NoAutoCalc + the cost it has TODAY (CK formula, same as
arch-docs/magic/tools/MagicExtract/CostCalculator.cs, at the live magnitudes and the
winning MGEF BaseCost) - hits per charge stay exactly as they are. Base Enderal already
ships NoAutoCalc weapon enchantments (EnchWeaponFrostDamage04, the ambush daggers).

Source record per override = the live winner (EGO's YAML when EGO wins, else base
Enderal's), so every other field EGO changed is forwarded. Base-sourced names are
collapsed to EGO's single-English-Value shape (this plugin is not Localized).

Inputs:
  reference/base/{Skyrim,EnderalFS}/ObjectEffects + Weapons
  reference/mods/EGO/ObjectEffects + Weapons
  arch-docs/magic/data/enchantments.json, magic-effects.json  (winners + BaseCost)
Output: src/MagicPatches/MagicPatchesESP/ObjectEffects/*.yaml (folder is regenerated)
"""
import glob
import json
import math
import os
import re
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
BASE = os.path.join(ROOT, "reference", "base")
EGO = os.path.join(ROOT, "reference", "mods", "EGO")
DATA = os.path.join(ROOT, "arch-docs", "magic", "data")
OUT = os.path.join(ROOT, "src", "MagicPatches", "MagicPatchesESP", "ObjectEffects")

FACTOR = 2.0
EGO_PLUGIN = "Enderal SE - Gameplay Overhaul.esp"

# damage / absorb effects that get scaled, by EditorID of the winning MGEF
SCALED_MGEFS = {
    "EnchAbsorbHealthFFContact", "EnchAbsorbMagickaFFContact", "EnchAbsorbStaminaFFContact",
    "DA08EnchAbsorbHealthFFContact",
    "EnchFireDamageFFContact", "EnchFrostDamageFFContact", "EnchShockDamageFFContact",
    "EnchFrostDamageFFContactNoShader",  # EGO's 001E8E, replaces Selna's base frost effect
    "EnchMagickaDamageFFContact", "EnchStaminaDamageFFContact",
    "XionLightbringer",                  # EGO-added light damage vs undead
}
EXPECTED_RECORDS = 30

EFFECT_RE = re.compile(r"^- BaseEffect: ([^\r\n]+)\r?\n((?:  [^\r\n]*\r?\n?)*)", re.M)
MAG_RE = re.compile(r"^    Magnitude: ([\d.]+)", re.M)
DUR_RE = re.compile(r"^    Duration: (\d+)", re.M)


def load(name):
    d = json.load(open(os.path.join(DATA, name), encoding="utf-8"))
    return d if isinstance(d, list) else d["records"]


def index_tree(folder):
    out = {}
    for f in glob.glob(os.path.join(folder, "*.yaml")):
        t = open(f, encoding="utf-8", newline="").read()
        m = re.search(r"^FormKey: ([^\r\n]+)", t, re.M)
        if m:
            out[m.group(1)] = (f, t)
    return out


def effects(text):
    """[(baseEffect, magnitude, duration)] in record order."""
    body = text[text.index("\nEffects:"):]
    res = []
    for m in EFFECT_RE.finditer(body):
        mag = MAG_RE.search(m.group(2))
        dur = DUR_RE.search(m.group(2))
        res.append((m.group(1), float(mag.group(1)) if mag else 0.0, int(dur.group(1)) if dur else 0))
    return res


def effect_cost(mgef, mag, dur):
    mag = max(mag, 1.0)
    durf = 1.0 if mgef["castType"] == "Concentration" else (10.0 if dur == 0 else dur) / 10.0
    return math.floor(mgef["baseCost"] * mag ** 1.1 * durf ** 1.1)


def fmt(x):
    return str(int(x)) if float(x).is_integer() else repr(round(x, 4))


def main():
    winners = {r["formKey"]: r for r in load("enchantments.json")}
    mgefs = {r["formKey"]: r for r in load("magic-effects.json")}

    base = index_tree(os.path.join(BASE, "Skyrim", "ObjectEffects"))
    base.update(index_tree(os.path.join(BASE, "EnderalFS", "ObjectEffects")))  # FS overrides
    ego = index_tree(os.path.join(EGO, "ObjectEffects"))

    on_weapon = set()
    for f in glob.glob(os.path.join(BASE, "*", "Weapons", "*.yaml")) + glob.glob(os.path.join(EGO, "Weapons", "*.yaml")):
        m = re.search(r"^ObjectEffect: ([^\r\n]+)", open(f, encoding="utf-8").read(), re.M)
        if m:
            on_weapon.add(m.group(1))

    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)

    written = []
    for fk in sorted(on_weapon):
        w = winners.get(fk)
        if not w or w["enchantType"] != "Enchantment":
            continue
        if not any(e["baseEffect"]["editorId"] in SCALED_MGEFS for e in w["effects"]):
            continue
        winner = w["provenance"]["winner"]
        if winner == EGO_PLUGIN:
            path, text = ego[fk]
        elif winner in ("Skyrim.esm", "Enderal - Forgotten Stories.esm", "Update.esm"):
            path, text = base[fk]
        else:
            sys.exit(f"{fk}: winner {winner} is not EGO or base - extend this script deliberately")

        live = effects(text)
        orig = effects(base[fk][1]) if fk in base else []  # EGO-new enchantment: no base values
        if [round(m, 4) for _, m, _ in live] != [round(e["magnitude"], 4) for e in w["effects"]]:
            sys.exit(f"{fk}: YAML magnitudes {live} disagree with the dataset winner - regenerate reference/ or the dataset")

        # cost the engine charges today, before we touch magnitudes
        # no EnchantmentCost at all = an uncharged blade (Petrified Saber, the Ebony Blade
        # analogue) - nothing to pin
        auto = "NoAutoCalc" not in text and re.search(r"^EnchantmentCost:", text, re.M) is not None
        cost_now = sum(effect_cost(mgefs[be], m, d) for be, m, d in live)

        changes = []
        lines_out = text
        offset = text.index("\nEffects:")
        head, body = lines_out[:offset], lines_out[offset:]
        new_body, pos = [], 0
        for i, m in enumerate(EFFECT_RE.finditer(body)):
            be = m.group(1)
            block = m.group(0)
            if mgefs[be]["editorId"] in SCALED_MGEFS:
                # base Enderal's value at this slot (0 when EGO added the effect/record)
                # (paired by slot; EGO swapped Selna's frost MGEF, so match on role, not FormKey)
                base_mag = 0.0
                if i < len(orig) and mgefs.get(orig[i][0], {}).get("editorId") in SCALED_MGEFS:
                    base_mag = orig[i][1]
                src = max(base_mag, live[i][1])
                target = FACTOR * src
                block, n = MAG_RE.subn(f"    Magnitude: {fmt(target)}", block)
                if n != 1:
                    sys.exit(f"{fk}: effect {i} has no Magnitude line")
                changes.append(f"{mgefs[be]['editorId']} {fmt(live[i][1])}->{fmt(target)}")
            new_body.append(body[pos:m.start()] + block)
            pos = m.end()
        new_body.append(body[pos:])
        body = "".join(new_body)

        if auto:
            # join an existing Flags list (Souleater's Mace has ExtendDurationOnRecast) rather
            # than writing a second Flags key
            head, n = re.subn(r"^EnchantmentCost: \d+(\r?\n)(Flags:\r?\n)?",
                              lambda mm: f"EnchantmentCost: {cost_now}{mm.group(1)}Flags:{mm.group(1)}- NoAutoCalc{mm.group(1)}",
                              head, count=1, flags=re.M)
            if n != 1:
                sys.exit(f"{fk}: no EnchantmentCost line")
            if len(re.findall(r"^Flags:", head, re.M)) != 1:
                sys.exit(f"{fk}: expected exactly one Flags key after pinning the cost")

        # non-localized plugin: collapse a multi-language Name to EGO's single-Value shape
        head = re.sub(r"^Name:\r?\n  TargetLanguage: English\r?\n  Values:\r?\n(?:  - [^\r\n]*\r?\n(?:    [^\r\n]*\r?\n)*)+",
                      lambda mm: "Name:\r\n  TargetLanguage: English\r\n  Value: "
                      + re.search(r"Language: English\r?\n    String: ([^\r\n]*)", mm.group(0)).group(1) + "\r\n",
                      head, count=1, flags=re.M)
        if "  Values:" in head:
            sys.exit(f"{fk}: Name collapse failed")

        out = re.sub(r"\r?\n", "\n", head + body)  # repo YAML is LF (.gitattributes eol=lf)
        with open(os.path.join(OUT, os.path.basename(path)), "w", encoding="utf-8", newline="") as fh:
            fh.write(out)
        written.append(f"{w['editorId']:<40} {'cost ' + str(cost_now) + ' pinned' if auto else 'manual cost kept':<18} {'; '.join(changes)}")

    for line in written:
        print(line)
    if len(written) != EXPECTED_RECORDS:
        sys.exit(f"expected {EXPECTED_RECORDS} overrides, wrote {len(written)} - review before updating EXPECTED_RECORDS")
    print(f"OK: {len(written)} weapon enchantments scaled x{fmt(FACTOR)}")


if __name__ == "__main__":
    main()
