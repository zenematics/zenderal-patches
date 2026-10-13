# Testing and debugging

Deploying, loading in xEdit, reading crash logs, and the load-time failure modes that produce no error.

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

## Testing in MO2 and xEdit

MO2 instances under `$Tools.modlistsRoot`, or the Zenderal instance at `$Tools.modlistRoot`.
Use the `mod-deploy` skill rather than copying by hand.

**xEdit must run in Enderal mode:** use a copy named `EnderalSEEdit.exe` or pass **`-EnderalSE`**.
**[upstream]** Plain SSEEdit mode reads the Skyrim game folder and INI and will not see Enderal's
plugins at all. Pass the switch yourself — there is no skill that does it for you.

> **xEdit lives inside the instance now, and the release archive contains no `EnderalSEEdit.exe` —
> you make it yourself.** **[verified 2026-08-27]** xEdit **4.1.5f** is installed at
> `<modlistRoot>/Tools/EnderalSEEdit 4.1.5f/`, which is the exact path the Zenderal
> `ModOrganizer.ini` "EnderalSEEdit" entry already expected (it also passes
> `-D:"<Stock game\Data>" -enderalse`). The `.7z` from
> [TES5Edit releases](https://github.com/TES5Edit/TES5Edit/releases) ships **only** the generic
> per-family binaries — `xTESEdit64.exe`, `xFOEdit64.exe`, `xSFEdit64.exe`, plus `BSArch64.exe` and
> `Edit Scripts/`. **xEdit selects its game mode from the executable's NAME**, so
> `EnderalSEEdit.exe` and `EnderalSEEditQuickAutoClean.exe` here are plain copies of
> `xTESEdit64.exe`. Confirmed working: the running process's window title reads
> `EnderalSEEdit 4.1.5f x64`, and the binary carries `EnderalSE` as a recognised mode string.
>
> Before this, **every** `xedit`/`bsarch` path in `tools.json` pointed into
> `C:/modding/mod-projects/claudemoddev/modlist/tools/`, **which no longer exists** — that whole
> shared tools folder is gone. `tools.json` now points at the in-instance install. **`champollion`
> was in that same dead folder and is still NOT installed**; its key is blanked so `Assert-Tool`
> fails loudly. Reinstall from
> [Orvid/Champollion releases](https://github.com/Orvid/Champollion/releases) if you need to
> decompile a third-party `.pex` — Enderal's own scripts need no decompiler, `ScriptsEnderal.zip`
> is real source.

## Crash logs are written to the SKYRIM SE folder, not Enderal's

**[verified]** Crash Logger SSE (and the other SKSE plugin logs — `skse64.log`, `EnderalSE.log`,
`po3_*.log`) land in:

```
C:\Users\<you>\Documents\My Games\Skyrim Special Edition\SKSE\crash-<timestamp>.log
```

**not** `…\My Games\Enderal Special Edition\SKSE\`, which holds only the INIs and saves. Looking in
the Enderal folder and finding nothing is what makes a crash look like it produced no log at all —
it did. Read the newest `crash-*.log` by mtime and check `Working Directory:` says Enderal before
trusting it.

Two fields to read first, before the call stack:

| Field | Means |
|---|---|
| `PLUGINS: Total: 0` | crashed **during** file loading — the data handler never populated. Suspect the plugin header/masters, not records |
| `PLUGINS: Total: <n>` with a full list | plugins loaded fine; it is a content or runtime problem |

The plugin list in a `.ess` save is a second, independent source for what the engine actually
loaded — useful when the game will not start at all.

---

## Standalone xEdit reads its own game path

- **Standalone xEdit reads its OWN configured game path, not `tools.json`'s `gameDataDir`.**
  **[verified]** On this machine `tools.json.gameDataDir` is `E:/Zenderal/Stock Game/Data` (the MO2
  instance's self-contained copy), but launching `EnderalSEEditQuickAutoClean.exe`/`EnderalSEEdit.exe`
  directly (bypassing MO2) reads `EnderalSEEdit_log.txt`'s own `Using Enderal Special Edition Data
  Path:` line — which pointed at a completely different, genuinely separate Steam install,
  `E:\Steam\SteamApps\common\Enderal Special Edition\Data\`, apparently configured the one time
  someone ran the tool standalone in the past. Staging a built plugin into `$Tools.gameDataDir` and
  then running xEdit standalone silently does nothing — the QuickAutoClean process reports exit 0
  but never touches the file, because it never looked in that folder. **Check the tool's own log file
  in its install folder for the actual `Using ... Data Path:` line before staging anything**, don't
  trust `tools.json` alone for this specific step. Both paths share the same
  `C:\Users\frien\AppData\Local\Enderal Special Edition\Plugins.txt` load order, confirming the Steam
  folder is the real live target MO2's USVFS overlays onto when launched normally.
  **The reliable defence is to stop relying on the tool's remembered path at all: pass
  `-D:"<data dir>"` on the command line every time**, which is what the instance's MO2 entry does
  (`-D:"…\Stock game\Data" -enderalse`). The paths above are from an older machine state and the
  fresh 4.1.5f install has no remembered path yet — so set it explicitly rather than discovering
  which folder it picked. **[verified 2026-08-27]**

## The form-version ceiling (HEDR 1.71) and BEES

> ### THE FORM-VERSION CEILING: Enderal will not load a plugin whose `HEDR` version is 1.71
>
> **[verified in-game 2026-08-02. Read this before porting any Skyrim mod.]**
>
> Enderal SE runs SSE **1.5.97**, and that engine **silently refuses any plugin written at `HEDR`
> form version 1.71**. No warning, no log entry, no missing-master dialog — the plugin is simply
> absent from the game. `HEDR` 1.70 is the ceiling; 1.71 is what the 1.6/AE-era Creation Kit and
> newer tools emit.
>
> **BUT: the Zenderal modlist lifts this ceiling with BEES.** **[verified in-game 2026-08-08]**
> The list ships **Backported Extended ESL Support** (Nukem, Nexus 106441, v1.2.0.0 — SKSE plugin,
> `mods\Backported Extended ESL Support\`), which replicates SSE 1.6.1130's plugin-loading code on
> 1.5.97 so 1.71 plugins load normally. Proof from a live run:
> `Documents\My Games\Skyrim Special Edition\SKSE\BackportedESLSupport.log` logs
> `Emulated old header version for <plugin>` for **exactly the 68 plugins** an independent HEDR
> scan of the profile found at 1.71 (`DynDOLOD.esp`, the `Pretty * Armory` set, `ForHonorBFCO.esp`,
> `Smart_NPC_Potions.esp`, …). BEES was added to the list on 2026-08-08 — *after* the 2026-08-02
> ceiling verification; both observations were correct when made.
>
> Consequences: (a) everything below still applies verbatim to a BEES-less Enderal install, to
> plugins WE author (keep writing `Version: 1.7` — do not make Zenderal patches depend on BEES),
> and to debugging reports from users who dropped BEES; (b) inside *this* list, a 1.71 third-party
> plugin is **not** inert — the "five inert `thepath` plugins" note below describes a list without
> BEES, so audit any Enderal list for 1.71 **or** for BEES; (c) BEES
> is now load-bearing — removing it silently disables 68 plugins. `arch-docs/magic/` datasets mark
> every record whose winner needs it (`winnerNeedsBees`), and the `magic-extract` tool hard-fails
> if 1.71 plugins are present without BEES.
>
> **Proof:** `Apocalypse - Magic of Skyrim.esp` is 1.71. With it enabled, `help wither 4` in the
> console finds nothing, though the mod defines a spell whose EditorID and name both contain
> "Wither". Change **four bytes** — the `HEDR` version float at file offset 30 — from 1.71 to 1.70,
> leave every other byte identical, and the spell appears. Single variable, both directions.
>
> **How this presents, and why it is so hard to spot:**
>
> - The mod appears installed and enabled. MO2 is happy. The game launches.
> - Nothing it adds exists. `help <anything> 4` finds none of its records.
> - **A patch that masters it crashes the game**, because the patch loads, tries to bind to a master
>   the engine skipped, and dereferences null during data load:
>   ```
>   EXCEPTION_ACCESS_VIOLATION  SkyrimSE.exe+05E1F22   mov rdx, [rax+0x158]   rax = 0
>   PROBABLE CALL STACK: ... InitTESThread
>   PLUGINS: Light: 0  Regular: 0  Total: 0      <-- data handler never finished
>   ```
> - Setting the *patch* to 1.71 makes the crash disappear — because the patch is now skipped too.
>   **That is a false fix and it was shipped once.** A crash that vanishes because both plugins
>   became invisible looks exactly like a crash that was fixed.
>
> **Check `HEDR` before you plan anything.** Read the float at offset 30 of the `.esp`
> (`enderal-mods`' `src/Apocalypse/tools/verify-plugin-structure.ps1` prints it, or read the four
> bytes directly). If it is 1.71:
>
> - a patch plugin **cannot** work — the only route is to rebuild the mod's own plugin at 1.70,
>   which means shipping a modified copy under the same filename (keeps its BSAs loading). Check the
>   author's permissions first.
> - when authoring with Spriggit, set `ModHeader.Stats.Version: 1.7` **explicitly**. Mutagen's
>   default is **1.71**, so a plugin that never mentions the field builds itself invisible.
>
> **This is not rare.** Five other plugins in the `thepath` modlist are 1.71 and therefore inert:
> `CS Light.esp`, `DynDOLOD.esp`, `Enderal Weather - HDR.esp`, `standard_lighting_templates.esp`,
> `TerrainHelper.esp` — most of a visuals layer, loading nothing, with no error anywhere. Audit any
> Enderal list for this.

## Debugging a load crash

> ### Debugging a load crash: bisect the PLUGIN, not the records
>
> **[verified — learned the expensive way on the Apocalypse patch.]** When a patch crashes the game
> at load, the instinct is to suspect the records. Six record-level hypotheses were tested and all
> six were wrong, because the cause was in the 24-byte header. **Run the cheap controls first, in
> this order** — each is one launch and each halves the search space:
>
> 1. **Empty plugin.** Hand-write a valid TES4 with no masters and no records under the same
>    filename. If that crashes, nothing you authored is involved.
> 2. **Masters only, no records.** Add the real master list, still zero records. This separates
>    "header/masters" from "content" in one launch.
> 3. **Bisect the master list**, then the header fields (`HEDR` version, flags), then records.
>
> `scratchpad/make-masters.ps1`-style hand-built plugins are better than toolchain output here
> precisely because they remove the toolchain as a variable. Also: **isolate one variable per
> launch** — an early run changed the ESL flag and the record set together and proved nothing.

## Deploy hygiene: check the deployed file's timestamp

Worked example in [`patches/FasterSprint.md`](../patches/FasterSprint.md); the rule:

> **Deploy-hygiene lesson, the expensive part:** a manually-installed (non-`mod-deploy`-skill)
> `.esp` sat stuck at its original `2026-08-09` timestamp through the `NPC_1HM_MT` experiment, a
> +40% rebuild, an ini-flag test, and a +40%-with-ini-flag retest — **four rounds of "no effect"
> in-game results that were actually testing zero code changes at all**, because the file in the
> live MO2 mod folder was never being overwritten by the rebuilds happening in this repo's `dist/`.
> Every one of those "disproven" results had to be discarded once the file's actual `Date modified`
> was checked directly in the mod folder and found to predate every rebuild in question. **Before
> trusting *any* in-game "no change" result on a manually-deployed patch, check the deployed file's
> timestamp against the rebuild's** — this is exactly what the `mod-deploy` skill exists to make
> impossible (it copies from `dist/` and verifies the destination), so prefer it over manual install
> for anything under active iteration.

## Which plugin actually won? Ask the console

From the Ark Myrad postmortem ([`patches/ArkMyradPlatformFix.md`](../patches/ArkMyradPlatformFix.md)):

> **How this was finally caught:** the in-game console's own reference-info panel names the winning
> plugin directly — `prid <formid>` in-game shows `Ref last changed by: <plugin>` — and it said
> `Enderal - Forgotten Stories.esm`, not `Skyrim.esm`. That single field ended a session's worth of
> guessing. **Read that field before trusting any FormKey lookup against `reference/base/Skyrim/` for
> a record FS is known to touch** (recall: 28.7% of FS's own records override base Enderal — see
> "Master order" above) — grep `reference/base/EnderalFS/` for the same FormKey FIRST, or at minimum
> in parallel, never only the base layer, whenever a record's edits aren't taking visible effect and
> the record belongs to an NPC, quest alias, or anything else FS is likely to have touched.
>

## Tooling traps

- **Never rewrite a UTF-8 doc with PowerShell 5.1's `Set-Content -Encoding utf8`.** **[verified
  2026-08-03]** It reads the file as the system ANSI codepage and writes it back as UTF-8 **with a
  BOM**, double-encoding every non-ASCII character — every `—` in this file became `â€"` in one
  pass, and `git diff` then reports the whole file as changed. It happened here while resolving a
  rebase conflict in `CLAUDE.md`. Use the Edit tool for surgical text changes, or `git checkout` the
  file and redo them; if you must script it, read and write with an explicit
  `[System.Text.UTF8Encoding]::new($false)` rather than the `-Encoding utf8` shorthand.

## PowerShell 5.1 and bulk-edit traps (guardrails 10 and 11 in full)

10. **PowerShell 5.1 is the target** for build scripts and skills: `Set-StrictMode` is on, there is
    no `&&`/`||`, no ternary, no null-coalescing, and no built-in YAML parser. Write `-Encoding utf8`
    explicitly when a file will be read by other tools. Two further traps when bulk-editing YAML:
    - **The Spriggit YAML is CRLF, so `$` in a multiline regex does not match.** `'(?m)^Foo: bar$'`
      silently fails on `Foo: bar\r\n` because `$` anchors before `\n` and the `\r` is in the way.
      Use `(?=\r?$)` or drop the anchor. **[verified]** — this cost a full pass on the Apocalypse
      recipes and it fails *silently*, so always assert the replacement count and throw on zero.
    - `Join-Path` takes **two** arguments in 5.1; `Join-Path $a $b $c` is a parameter-binding error.
      Nest the calls.
11. **Bulk record edits should be scripted, verified by count, and re-validated after.** When a patch
    touches dozens of records, generate them from `reference/` with a script that *asserts* what it
    changed (entry counts before/after, every intended replacement matched at least once) and fails
    loudly otherwise. Then re-resolve every FormKey the patch emits against the serialized masters —
    that catches the dangling references xEdit would, without needing the mod installed. Note
    `000014:Skyrim.esm` (PlayerRef) is **absent from `reference/base/Skyrim/`** despite being valid
    and used by 77 of Enderal's own recipes, so allow-list it rather than chasing it. **[verified]**
