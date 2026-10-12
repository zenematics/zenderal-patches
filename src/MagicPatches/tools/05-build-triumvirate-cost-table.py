#!/usr/bin/env python3
"""Build the Triumvirate -> EGO cost-ladder pricing table.

Same mechanism as 01-build-cost-table.py (Apocalypse): reads the extracted magic dataset
(arch-docs/magic/data) and maps every book-taught Triumvirate player spell onto EGO's cost
ladder with a per-(tier, castGroup) ratio:

    newCost = round( egoMedian[tier][group] * liveCost / tvrMedian[tier][group] )

Measured 2026-08-27 against the v2026.08.27 Triumvirate - Enderal Conversion: the 75 spells
are all auto-calc on Enai's vanilla-Skyrim effect economy, so their live costs run far above
EGO's ladder - ff tier medians 46/82/168/356/1207 vs EGO's 30/53/76/97/124 (master ~10x).

Differences from 01, both deliberate:
  - Population filter is provenance.definedIn (not winner), so the table can be REBUILT after
    Zenderal - Magic Patches ships its overrides and becomes the dataset winner. liveCost is
    computedAutoCost, which the extractor computes from the winning record's effect data - the
    overrides carry the effects verbatim, so it stays the upstream live cost. (Caveat: the
    three fever-taxed heals gain a fever effect, which nudges their computedAutoCost by a few
    points on a re-run - same class as King's Heart's 635 vs 636 in the Apocalypse table.
    Accept the drift; the table in git is the authority until upstream changes.)
  - tier comes from Enai's own EditorID encoding TVR_<Archetype>_<School><Tier>_Spell_<Name>
    (A/C/D/I/R + 000/025/050/075/100), which is also what tiers the tome and picks the vendor.
    The MGEF MinimumSkillLevel cross-check agrees on 74/75; the known exception is
    TVR_Cleric_R025_Spell_Aura_1, which shares a skill-75 proc effect with Aura_3 - its tome
    tier (25) is the one the player shops by, so the EditorID wins. Asserted below so a new
    upstream version that moves tiers fails loudly instead of mispricing.

Output: triumvirate-cost-table.json next to this script (committed), consumed by
06-apply-triumvirate-cost-table.ps1.
"""
import json
import os
import re
import statistics

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
DATA = os.path.join(ROOT, "arch-docs", "magic", "data")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "triumvirate-cost-table.json")

TVR = "Triumvirate - Mage Archetypes.esp"
EGO = "Enderal SE - Gameplay Overhaul.esp"
OURS = "Zenderal - Magic Patches.esp"
TIERS = (0, 25, 50, 75, 100)
FLOOR = 5
TIER_RE = re.compile(r"_(?P<school>[ACDIR])(?P<tier>000|025|050|075|100)_")
# EditorID tier != max MGEF MinimumSkillLevel, verified by hand (shared proc effects):
KNOWN_TIER_OUTLIERS = {"TVR_Cleric_R025_Spell_Aura_1"}


def main():
    spells = json.load(open(os.path.join(DATA, "spells.json"), encoding="utf-8"))["records"]
    mgef = {r["formKey"]: r for r in
            json.load(open(os.path.join(DATA, "magic-effects.json"), encoding="utf-8"))["records"]}

    def mgef_tier(r):
        lvl = 0
        for e in r.get("effects") or []:
            m = mgef.get((e.get("baseEffect") or {}).get("formKey"))
            if m:
                lvl = max(lvl, m.get("minimumSkillLevel") or 0)
        return 0 if lvl < 25 else 25 if lvl < 50 else 50 if lvl < 75 else 75 if lvl < 100 else 100

    def group(r):
        return "conc" if r.get("castType") == "Concentration" else "ff"

    ego = [r for r in spells
           if r["provenance"]["winner"].startswith(EGO)
           and r.get("taughtBy") and r.get("type") == "Spell"
           and not (r.get("name") or "").startswith(">")
           and r.get("cost")]
    tvr = [r for r in spells
           if r["provenance"]["definedIn"] == TVR
           and r["provenance"]["winner"] in (TVR, OURS)
           and r.get("taughtBy") and r.get("type") == "Spell"
           and not (r.get("name") or "").startswith(">")
           and r.get("cost")]
    if len(tvr) != 75:
        raise SystemExit(f"expected 75 taught Triumvirate player spells, found {len(tvr)}"
                         " - re-run /magic-extract, or upstream changed: revisit this script")

    def tvr_tier(r):
        m = TIER_RE.search(r["editorId"])
        if not m:
            raise SystemExit(f"{r['editorId']}: no <School><Tier> in EditorID - naming drifted")
        t = int(m.group("tier"))
        if t != mgef_tier(r) and r["editorId"] not in KNOWN_TIER_OUTLIERS:
            raise SystemExit(f"{r['editorId']}: EditorID tier {t} != MGEF tier {mgef_tier(r)}"
                             " and not a known outlier - upstream moved tiers, re-verify")
        return t

    for r in tvr:
        if "ManualCostCalc" in (r.get("flags") or []) and r["provenance"]["winner"] == TVR:
            raise SystemExit(f"{r['editorId']}: upstream is ManualCostCalc - model changed")
        if r["cost"].get("computedAutoCost") is None:
            raise SystemExit(f"{r['editorId']}: no computedAutoCost - cost model disabled?")

    def medians(pop, costof, tierof):
        out = {}
        for g in ("ff", "conc"):
            for t in TIERS:
                v = [costof(r) for r in pop if tierof(r) == t and group(r) == g]
                if v:
                    out[(g, t)] = statistics.median(v)
        return out

    ego_med = medians(ego, lambda r: r["cost"]["baseCost"], mgef_tier)   # manual-cost: stored = live
    tvr_med = medians(tvr, lambda r: r["cost"]["computedAutoCost"], tvr_tier)

    table = []
    for r in sorted(tvr, key=lambda r: r["formKey"]):
        t, g = tvr_tier(r), group(r)
        live = r["cost"]["computedAutoCost"]
        if (g, t) not in ego_med or (g, t) not in tvr_med:
            raise SystemExit(f"no median for ({g},{t}) - population changed, revisit the bucketing")
        new = max(FLOOR, round(ego_med[(g, t)] * live / tvr_med[(g, t)]))
        table.append({
            "formKey": r["formKey"], "editorId": r["editorId"], "name": r.get("name"),
            "school": (r.get("school") or {}).get("displayName"),
            "tier": t, "castGroup": g,
            "liveCost": live, "storedBaseCost": r["cost"]["baseCost"], "newCost": new,
        })

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"generatedFrom": "arch-docs/magic/data (see manifest.json extractedAt)",
                   "egoMedians": {f"{g}:{t}": v for (g, t), v in sorted(ego_med.items())},
                   "tvrMedians": {f"{g}:{t}": v for (g, t), v in sorted(tvr_med.items())},
                   "spells": table}, f, indent=1)
    print(f"{len(table)} spells priced -> {OUT}")
    for g in ("ff", "conc"):
        for t in TIERS:
            rows = [x for x in table if x["tier"] == t and x["castGroup"] == g]
            if rows:
                print(f"  {g} tier {t:3}: median {int(statistics.median([x['liveCost'] for x in rows]))} "
                      f"-> {int(statistics.median([x['newCost'] for x in rows]))}  (n={len(rows)})")


if __name__ == "__main__":
    main()
