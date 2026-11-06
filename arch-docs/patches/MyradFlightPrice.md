# MyradFlightPrice

- **Source:** `src/MyradFlightPrice/` (generated: `tools/01-build-myrad-flight-price.py`)
- **Ships:** `Zenderal - Myrad Flight Price.esp` (ESL, HEDR 1.7, masters Skyrim/Update/FS only). The live copy is in
  `Zenderal - Patch Collection`. **Must load after `EGO SE - Gameplay Overhaul.esp` and `DBVO_EnderalPatch.esp`.**
- **FormID block:** none (overrides only)
- **Owns:** topic `MyradDialogue_StartTopic_T1Topic01 12E0EC` (DBVO's header, verbatim) and its responses `12E110`,
  `12E111`, `14CB50`, `14CB51` (EGO's, gold gate changed)
- **Status:** built and round-trip clean 2026-11-06, deployed. Unverified in game.

## Why

Player report (GreaseLord, 2026-11-06): the Myrad keeper in Ark offers a flight "(25 pennies)" but needs 50.

Enderal 2.1 prices a flight at 25 everywhere: the topic text, the four responses' gold gates (`GetItemCount` gold
`00000F` ≥ 25 to fly on `12E110`/`14CB50`, < 25 to be refused on `12E111`/`14CB51`) and the charge (2.1's
`_00E_MyradSystem02.PortPlayer` removes `MyradTripPrice` gold, global `0493E1` = 25).

EGO is a 2.0-era plugin and charged 50:
- its copies of the four responses gate at 50;
- its quest record `0D9B17` gives the script an int `Price` = 50. 2.1's script no longer reads it, and the record
  leaves `MyradTripPrice` unfilled, so the charge is unreliable as well.

`DBVO_EnderalPatch.esp` (mod *Ciri - Enderal Dialogue Fixes*) wins the topic itself and keeps 2.1's "(25 pennies)"
text. So the menu said 25 while the gate wanted 50. The curator chose 25.

## The fix

- This plugin: DBVO's topic header verbatim (an INFO override needs its DIAL), plus EGO's four responses verbatim,
  with only the gold condition's `ComparisonValue` 50 → 25. The generator asserts one gold `GetItemCount` per
  response at 50, and that DBVO's text still says 25.
- The charge: [`Levelsystem21Cleanup`](Levelsystem21Cleanup.md) owns quest `0D9B17` and now fills `MyradTripPrice`.

## Upkeep

After an EGO or Ciri - Enderal Dialogue Fixes update, re-serialize EGO into `reference/mods/EGO` and
`DBVO_EnderalPatch.esp` into `reference/mods/DBVOEnderalPatch`, then rerun
`python -I src/MyradFlightPrice/tools/01-build-myrad-flight-price.py`.

## To verify in game

At a Myrad keeper (Ark), carrying 25–49 gold:
- "I need a flight. (25 pennies)" leads to the destination choice, not the refusal.
- A flight takes exactly 25 gold.
- With fewer than 25 gold, you get the refusal.
