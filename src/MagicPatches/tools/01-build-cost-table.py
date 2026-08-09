#!/usr/bin/env python3
"""Build the Apocalypse -> EGO cost-ladder pricing table.

Reads the extracted magic dataset (arch-docs/magic/data) and maps every book-taught
Apocalypse player spell onto EGO's cost ladder with a per-(tier, castGroup) ratio:

    newCost = round( egoMedian[tier][group] * liveCost / apoMedian[tier][group] )

- liveCost is computedAutoCost: all 175 spells are auto-calc, so the engine prices them
  from effect data at runtime and the stored BaseCost is irrelevant.
- tier = the highest MinimumSkillLevel among the spell's winning magic effects,
  bucketed 0/25/50/75/100 (the CK's novice..master bands).
- castGroup separates Concentration (cost per second) from fire-and-forget; their
  ladders differ by ~4x and mixing them skews both.
- The per-tier ratio preserves the author's ordering inside each tier (CLAUDE.md:
  rescale by ratio, never flat), and tiers may overlap at the edges like Enderal's own.
- Floor of 5 so nothing becomes free.

Output: apocalypse-cost-table.json next to this script (committed), consumed by
02-apply-cost-table.ps1. Re-run after a modlist change alters either population.
"""
import json
import os
import statistics

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
DATA = os.path.join(ROOT, "arch-docs", "magic", "data")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "apocalypse-cost-table.json")

APO = "Apocalypse - Magic of Skyrim.esp"
EGO = "Enderal SE - Gameplay Overhaul.esp"
TIERS = (0, 25, 50, 75, 100)
FLOOR = 5


def main():
    spells = json.load(open(os.path.join(DATA, "spells.json"), encoding="utf-8"))["records"]
    mgef = {r["formKey"]: r for r in
            json.load(open(os.path.join(DATA, "magic-effects.json"), encoding="utf-8"))["records"]}

    def tier(r):
        lvl = 0
        for e in r.get("effects") or []:
            m = mgef.get((e.get("baseEffect") or {}).get("formKey"))
            if m:
                lvl = max(lvl, m.get("minimumSkillLevel") or 0)
        return 0 if lvl < 25 else 25 if lvl < 50 else 50 if lvl < 75 else 75 if lvl < 100 else 100

    def group(r):
        return "conc" if r.get("castType") == "Concentration" else "ff"

    def taught_player_spells(winner_prefix):
        return [r for r in spells
                if r["provenance"]["winner"].startswith(winner_prefix)
                and r.get("taughtBy") and r.get("type") == "Spell"
                and not (r.get("name") or "").startswith(">")
                and r.get("cost")]

    ego = taught_player_spells(EGO)
    apo = taught_player_spells(APO)
    if len(apo) == 0:
        raise SystemExit("no Apocalypse spells in the dataset - re-run /magic-extract first")

    def medians(pop, costof):
        out = {}
        for g in ("ff", "conc"):
            for t in TIERS:
                v = [costof(r) for r in pop if tier(r) == t and group(r) == g]
                if v:
                    out[(g, t)] = statistics.median(v)
        return out

    ego_med = medians(ego, lambda r: r["cost"]["baseCost"])            # manual-cost: stored = live
    apo_med = medians(apo, lambda r: r["cost"]["computedAutoCost"])    # auto-calc:  computed = live

    table = []
    for r in sorted(apo, key=lambda r: r["formKey"]):
        t, g = tier(r), group(r)
        live = r["cost"]["computedAutoCost"]
        if (g, t) not in ego_med or (g, t) not in apo_med:
            raise SystemExit(f"no median for ({g},{t}) - population changed, revisit the bucketing")
        new = max(FLOOR, round(ego_med[(g, t)] * live / apo_med[(g, t)]))
        table.append({
            "formKey": r["formKey"], "editorId": r["editorId"], "name": r.get("name"),
            "school": (r.get("school") or {}).get("displayName"),
            "tier": t, "castGroup": g,
            "liveCost": live, "storedBaseCost": r["cost"]["baseCost"], "newCost": new,
        })

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"generatedFrom": "arch-docs/magic/data (see manifest.json extractedAt)",
                   "egoMedians": {f"{g}:{t}": v for (g, t), v in sorted(ego_med.items())},
                   "apoMedians": {f"{g}:{t}": v for (g, t), v in sorted(apo_med.items())},
                   "spells": table}, f, indent=1)
    print(f"{len(table)} spells priced -> {OUT}")
    for t in TIERS:
        rows = [x for x in table if x["tier"] == t and x["castGroup"] == "ff"]
        if rows:
            print(f"  ff tier {t:3}: median {int(statistics.median([x['liveCost'] for x in rows]))} "
                  f"-> {int(statistics.median([x['newCost'] for x in rows]))}  (n={len(rows)})")


if __name__ == "__main__":
    main()
