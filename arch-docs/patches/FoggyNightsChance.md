# FoggyNightsChance

- **Source:** `src/FoggyNightsChance/`
- **Ships:** *(no plugin — one recompiled script)* `Scripts/FogNightScript.pex`
- **MO2 mod:** `Zenderal - Foggy Nights Chance`, sorted **above** `Foggy Nights for Enderal` in `modlist.txt`
- **FormID block:** _(none)_
- **Status:** built and deployed 2026-10-29. **Unverified in game.**

## What it does

Curator's taste: fog on about 30% of nights instead of every night.

## How Foggy Nights does it (read 2026-10-29)

Foggy Nights for Enderal 1.0.3 (Nexus Enderal SE mod 487) uses **no region weather lists, no ini and
no SKSE plugin**. Serialized to `reference/mods/FoggyNights/`, its plugin (ESL, HEDR 1.7) holds two
records:

- `NightThickFog 000800` — the fog WTHR. No region or climate lists it.
- `FoggyNightsQuest 000D61` — start-game-enabled, alias `PlayerRef` (forced `000014:Skyrim.esm`) running
  `FogNightScript` with one property, `FoggyWeather` = `000800`. (The same script is also on the quest
  itself, where a `ReferenceAlias` script can't bind; harmless.)

`FogNightScript` (its shipped `.psc`) is a game-time timer: at 20:00 it calls
`FoggyWeather.SetActive(true, false)` (a weather **override**), at 07:00 `Weather.ReleaseOverride()`.
It tells night from morning by whether the current weather is the fog, so a fog-free morning was
treated as night and fog was forced again.

Because the fog is forced from a script, a region-chance patch could do nothing here; the fork is the
simplest route. Rule 5 (other region editors) does not come into it: no region record is touched.

## The fork (`; ZFN` lines)

- One roll per night: `Utility.RandomFloat(0, 1) < fog_chance` (0.3). The result is kept with the night
  number (`Floor(GameTime + (24 − 20)/24)`, the same from 20:00 to 07:00), so a reload or `OnLoad`
  at night re-applies a rolled fog but never rolls again.
- Night or morning by the hour; the morning releases the override only when the current weather is
  `FoggyWeather` (no other mod's override is released).
- Timer waits floored at 0.05 h, so an update landing a hair before a boundary can't loop.
- New script variables only; the `FoggyWeather` property is unchanged (release-shapes rule 2, checked
  with `grep -a` on both `.pex`).

Existing saves: the registered game-time update runs the new code at the next 20:00 or 07:00. A save
that is foggy right now keeps that night's fog until 07:00.

To change the chance, edit `fog_chance` in the `.psc` and recompile. Once a save has been made with
this script, it stores `fog_chance`, and the stored value wins over a new default. So a later change
only reaches new games or saves that never had this fork, unless the variable is renamed.

## Steamin ENB

[`SteaminTWoEWeatherList`](SteaminTWoEWeatherList.md) already maps `NightThickFog 0x800` to
`!_FoggyWeather_E.ini`. Nothing there changes: the weather is the same, it just plays less often.

## Shipping

This redistributes a modified copy of the Foggy Nights author's script; their Nexus page states no
permissions. Ask before shipping it outside the list's own install.
