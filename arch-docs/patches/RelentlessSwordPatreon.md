# RelentlessSwordPatreon

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **Source:** `src/RelentlessSwordPatreon/`
- **Ships:** `Zenderal - Relentless Sword.esp`
- **FormID block:** `0x800–0x831`

The two-build history and the one-ModKey/two-archives shape are in [`../workspace/release-shapes.md`](../workspace/release-shapes.md#two-mutually-exclusive-upstream-builds).

## What it does

`800–806` statics (1st-person models), `809–80F` weapons, `811–81F` forge + temper recipes (johnskyrim's original offsets, preserved for traceability), `820–825` dismantle recipes (new, this repo's), `826` crafting blueprint, `827` its placed reference in Riverville Temple — those 33 records were the free six-blade Nexus release. Then `828–829` statics, `82A–82B` weapons, `82C–82D` forge recipes, `82E–82F` tempers, `830–831` dismantle recipes for johnskyrim's Patreon "Zen" blade, allocated **above** the first block so a user coming from the six-blade build keeps every FormID. **The six-blade release was removed on 2026-08-16** (`src/RelentlessSword/`, plus `build-zen-tree.ps1`, which derived this tree from it and had no input left) — this folder is now hand-edited source of truth, and its assertions (42 record files, 8 blueprint-gated recipes, no `0F46CE`/`0F46D1` Skyforge refs) went with it. The **plugin filename was deliberately NOT renamed with the release**, for the same FormID reason
