# FrostSpiderMotherFix

- **Source:** `src/FrostSpiderMotherFix/`
- **Ships:** `Zenderal - Frost Spider Mother Fix.esp` (ESL, masters `Skyrim.esm` only)
- **FormID block:** _(none; one override)_

## What it does

**The Frostkrabblermutter (`_26E_Frostkrabblermutter` `0E430A`) is visible again.** Reported 2026-10-19:
`player.placeatme 0E430A` spawned an invisible spider. **[verified 2026-10-19]** Not a spider-replacer gap:
Spider SE ships both `FrostbiteSpider.nif` and `FrostbiteSpiderCold.nif`.

- Base Enderal puts the NPC on `FrostbiteSpiderRaceGiant` `04E507` with skin
  `SkinFrostbiteSpiderGiantCold` `02C181`.
- EGO (`Enderal SE - Gameplay Overhaul.esp`) moves it to `FrostbiteSpiderRaceLarge` `053477` and keeps the skin.
- That skin's only body ARMA, `NakedFrostbiteSpiderGiantColdAA` `02C17F`
  (`FrostbiteSpiderCold.nif`), is race-locked to Giant with no additional races. Its other ARMA,
  `01FDBD`, is a draugr body for `DraugrRace`. So nothing renders on a Large spider.

The override is Skyrim.esm's `02C17F` verbatim plus `AdditionalRaces: 053477`, which keeps EGO's race
(size/stats) change. A live binary scan of the Ultra load order found no other plugin with `02C17F`, and
EGO as the only override of `0E430A`. The other giant-skin spiders (`06A2E0`, `15024A`, `1003C5`) are
still on the Giant race and were never affected.

Built 2026-10-19; the Spriggit round trip is identical. Enabled in Alpha 0.6; Ultra must be ticked in
MO2. **Unverified in game.**
