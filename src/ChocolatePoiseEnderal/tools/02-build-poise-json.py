#!/usr/bin/env python3
"""Give Enderal's Vatyr races their own poise pool in Chocolate Poise - Reforged.

Why: CPR sizes an actor's poise pool as BaseHealth (100) x a per-race weight it looks up by
race EditorID in ChocolatePoise.json "Races"; an unlisted race falls back to the race's
BaseMass AV (PoiseAV::GetBaseActorValue, BlessingS91/Chocolate-Poise-Reforged). None of
Enderal's three Vatyr races is listed and EGO gives all three BaseMass 1.5, so every Vatyr -
the alphas and the level-55 one included - had a 150 pool: an early sword hit deals ~27
poise (MinPoise 25), so a stagger every 4-6 hits. EGO's Vatyr damage/power-attack nerf is
deliberately left alone; only the stagger resistance changes.

  VatyrRace       0133E4  every ordinary Vatyr (_06E_ "Young Vatyr" .. _45E_) + summonable
  VatyrRaceLarge  0133E6  the VaBoss alphas, Vadim, Sechshuf
  VatyrRaceGiant  0133ED  _55E_VatyrVaBoss_Aggressive only

The weight sets only the pool. Health damage on a poise break still reads the race's real
BaseMass (ApplyCreatureStaggerDamage), so that is unchanged.

CPR reads exactly one file, Data/SKSE/Plugins/ChocolatePoise.json, so this ships the
author's file verbatim with the entries appended to "Races"; the MO2 mod must sort above
"Chocolate Poise - Reforged". Re-run after any CPR update.

Input: <modlistRoot>/mods/Chocolate Poise - Reforged/skse/plugins/ChocolatePoise.json
Output: src/ChocolatePoiseEnderal/skse/ChocolatePoise.json (regenerated)
"""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
OUT = os.path.join(ROOT, "src", "ChocolatePoiseEnderal", "skse", "ChocolatePoise.json")

# Sabre cat is 2.2 and troll 3.0 in the author's table.
RACES = {
    "VatyrRace": 2.5,
    "VatyrRaceLarge": 3.0,
    "VatyrRaceGiant": 3.5,
}


def main():
    tools = json.load(open(os.path.join(ROOT, ".claude", "config", "tools.json"), encoding="utf-8-sig"))
    src = os.path.join(tools["modlistRoot"], "mods", "Chocolate Poise - Reforged", "skse", "plugins",
                       "ChocolatePoise.json")
    if not os.path.isfile(src):
        sys.exit(f"CPR json not found: {src}")
    text = open(src, encoding="utf-8", newline="").read()
    races = json.loads(text)["Races"]
    for name in RACES:
        if name in races:
            sys.exit(f"{name} is already in the author's table ({races[name]}) - review before overriding")

    # Insert after the last "Races" entry, keeping every other byte of the author's file.
    last = list(races)[-1]
    anchor = f'"{last}": {json.dumps(races[last])}'
    if text.count(anchor) != 1:
        sys.exit(f"anchor {anchor!r} matched {text.count(anchor)} times, expected 1")
    nl = "\r\n" if "\r\n" in text else "\n"
    indent = text[text.rfind("\n", 0, text.index(anchor)) + 1:text.index(anchor)]
    added = "".join(f",{nl}{indent}{json.dumps(k)}: {v}" for k, v in RACES.items())
    out = text.replace(anchor, anchor + added)

    parsed = json.loads(out)["Races"]
    assert len(parsed) == len(races) + len(RACES), "entry count"
    assert all(parsed[k] == v for k, v in RACES.items()), "new values"
    assert all(parsed[k] == v for k, v in races.items()), "author's values changed"

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        fh.write(out)
    print(f"{len(races)} author races + {len(RACES)} added -> {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
