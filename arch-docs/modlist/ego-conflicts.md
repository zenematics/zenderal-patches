# EGO as a conflict source

Summary only; the full analysis is in [`../EGO/`](../EGO/), starting with [`patching-ego.md`](../EGO/patching-ego.md).

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

`Enderal SE - Gameplay Overhaul.esp` (v1.93.1.0, author *Ixion XVII*) overrides **6203** records and
adds **974**. **[verified 2026-08-04]** Zenderal patches load **after** it. Four facts that change
how you write a patch, all documented in [`arch-docs/EGO/`](../EGO/):

1. **EGO is not `Localized`.** Every string on every record it overrides collapses from a
   multi-language `Values:` list to a single English `Value:`. So `['Name', 'Description',
   'Version2']` is the **null diff** — filter it out — and copying the FS/Skyrim version of a record
   EGO also overrides re-adds the `Values:` block, which is the tell that you copied the wrong source.
2. **`Player 000007:Skyrim.esm` carries 42 EGO perks.** That record *is* EGO's player ruleset.
   Overriding it without forwarding them deletes the mod's combat, economy, alchemy and mana rules
   while everything else still looks installed.
3. **61 records are injected**, not overridden — FormIDs in `Skyrim.esm`'s space that `Skyrim.esm`
   does not define (`ChaurusChitin 03AD57`, `DeflectArrows 058F68`, the Dragon Priest masks, six
   `DeathItem*` lists…). Referencing one means declaring EGO as a master.
4. **EGO rewrites all three blueprint vendor lists** (`_00ETraderCraftingPlansA/B/C`) — the exact
   records a new craftable-weapon patch needs — plus 123 other leveled lists, 99 GMSTs and 18 GMSTs
   it creates outright.

Before touching a record, `grep` its FormKey in
[`arch-docs/EGO/conflict-index.md`](../EGO/conflict-index.md); if it is listed, build your
version from **EGO's** YAML file, not the master's.
