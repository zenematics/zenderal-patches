---
name: magic-extract
description: Regenerate arch-docs/magic/ — every magic record in the installed Zenderal modlist (SPEL/MGEF/ENCH/SCRL/ALCH/SHOU/LVSP/GMST) with load-order-WINNING values as JSON/CSV/Markdown. Use after any modlist change, or when the user asks what a spell's actual in-game values are, wants the magic dataset refreshed, or is rebalancing magic.
---

# Magic extract — load-order-winning magic values

Runs `arch-docs/magic/tools/MagicExtract` (C#, Mutagen 0.54.4, **read-only**) against the MO2
instance and regenerates the committed dataset under `arch-docs/magic/`. Read
[`arch-docs/magic/README.md`](../../../arch-docs/magic/README.md) for the schema and limits.

## Preconditions

- `.claude/config/tools.json` has `modlistRoot`, `modlistProfile`, `gameDataDir` (already standard).
- .NET 9 SDK on PATH (`dotnet --list-sdks`).
- The modlist is installed at `modlistRoot`. No game launch needed.

## Run

```powershell
powershell -NoProfile -File arch-docs/magic/tools/Run-MagicExtract.ps1
```

Exit 0 = all self-checks passed (strings canary, BEES canary, cost-formula validation, raw GRUP
cross-check, 12 golden fixtures). **Nonzero = do not commit the outputs**; the console says which
check failed.

Optional deeper verification (needs the Spriggit trees in `reference/`):

```powershell
python arch-docs/magic/tools/verify_against_yaml.py
```

## Failure triage

| Failure | Meaning / fix |
|---|---|
| `FATAL: canary AVIF …` | String delocalization broke — a nameless dataset was refused. Check `Stock game/Data/Strings/` exists; see README fallbacks |
| `FATAL: … would NOT load without BEES` | 1.71 plugins present but *Backported Extended ESL Support* missing/disabled in the modlist — fix the modlist, not the tool |
| `COST MODEL DISABLED` | Formula validation fell below 97% on base Enderal — a Mutagen or data regression; `computedAutoCost` ships null |
| `FIXTURE FAIL` | A golden fixture regressed — usually a modlist change altered a fixture record; verify in xEdit (`-EnderalSE`), then update `golden.json` **only if the new value is genuinely correct** |
| `raw GRUP cross-check … mismatch` | Mutagen and the raw scanner disagree on record counts — investigate before trusting anything |

## Guardrails

- **Never use MagicExtract or its Mutagen 0.54.4 to WRITE a plugin.** Authoring goes exclusively
  through pinned Spriggit 0.40.0 (CLAUDE.md). The version pin `[0.54.4]` + `packages.lock.json`
  must stay (NuGet lists broken ancient versions after it).
- Commit `arch-docs/magic/data/*.json`, `spells.csv` and the generated `.md` together —
  they are one snapshot. `.provenance.json`, `bin/`, `obj/` stay gitignored.
- The dataset is per-profile (`modlistProfile`). After changing the modlist, re-run and read
  `git diff` on `data/` — deterministic ordering makes the diff the change report.
