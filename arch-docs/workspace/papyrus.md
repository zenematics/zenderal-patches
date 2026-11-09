# Papyrus toolchain

Extract → decompile → edit → compile → package. Use the matching skills; the `papyrus-script-engineer` subagent handles decompiled-source cleanup and compile-error fixing.

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

**Tool paths:** all resolved from `.claude/config/tools.json` — do not hardcode.

| Step | Tool | Config key |
|------|------|------------|
| Extract `.bsa` | `bsab.exe`, or `BSArch64.exe` (see below) | `$Tools.bsab` / `$Tools.bsarch` |
| Decompile `.pex`→`.psc` | `Champollion.exe` | `$Tools.champollion` |
| Disassemble `.pex` (no Champollion) | `python tools/pexdis.py <file.pex>`: properties, variables, every function's instructions with names resolved | none |
| Compile `.psc`→`.pex` | `PapyrusCompiler.exe` (from Skyrim SE) | `$Tools.papyrusCompiler` |
| Open Creation Kit | `CreationKit.exe` (from Skyrim SE) | `$Tools.creationKit` |

> **`bae.exe` has no usable CLI — do not reach for it.** **[verified]** It rejects `-e`,
> `--extract` and even `--help` ("Unknown option"); the `extract` string in the binary is a Qt slot
> name, not a command-line option. It is GUI/drag-and-drop only. When `bsab` is not installed, use
> **`BSArch64.exe unpack "<archive.bsa>" "<outdir>" -mt`** (bundled in xEdit's folder,
> `$Tools.bsarch`) — it is the reliable headless extractor here. Note it **requires the output
> directory to already exist** and fails with "Folder does not exist" otherwise.

## The import path is first-wins, and Enderal must be first

There are **three** Papyrus source trees in an Enderal setup, and **55 script names exist in both
Enderal's and Skyrim's** — `critter.psc`, `dgintimidateplayerscript.psc`, `dragonactorscript.psc`,
the `default*` handlers, and so on. Compile against the wrong copy and you get code built on vanilla
signatures that fails at runtime, not at compile time.

**All 55 differ from vanilla — not one is an accidental identical duplicate.** **[verified]** by
byte-comparing `reference/base/EnderalScripts` against `reference/base/VanillaScripts`. Two of them
are explicit `; DUMMY, DO NOTHING` stubs: `dgintimidateplayerscript.psc` and
`dgintimidatealiasscript.psc`, where Enderal has gutted the vanilla brawl/intimidate system down to
4 lines from 59. **[verified]** That is the concrete cost of getting the order wrong: compile
against vanilla's copy and you link in brawl logic Enderal deliberately deleted.

**The Papyrus compiler's `-i` path is FIRST-WINS. [verified]** — tested directly on this machine's
`PapyrusCompiler.exe` by putting a deliberately broken copy of a script in the first import dir and
a good copy in the second: with `-i="broken;good"` the compile **failed** on the broken copy; with
`-i="good;broken"` it **succeeded**. So the correct order is:

```
-i="<papyrusSource.enderal>;<papyrusSource.skse>;<papyrusSource.vanilla>;<importDirs...>"
```

> SureAI's own `How to modify Enderal scripts.txt` (inside `ScriptsEnderal.zip`) states the sources
> "must be loaded in the following order: Creation Kit scripts (Scripts.zip), SKSE scripts, Enderal
> scripts (ScriptsEnderal.zip)". That is **precedence** order — last one wins — describing the CK's
> source-folder list. It is the **reverse** of the `-i` order above. Both say the same thing:
> *Enderal's copy is the one that must be used.* Don't paste that readme's order into `-i`.

**Where the three trees come from** (unpack once; `papyrus-source/` is gitignored):

| Tree | Source | `tools.json` key |
|---|---|---|
| Enderal (~5000 `.psc`) | `<gameDataDir>/ScriptsEnderal.zip` → its `source/scripts/` | `papyrusSource.enderal` |
| SKSE (74 `.psc`) | `<gameDataDir>/Source/Scripts` — already loose in an Enderal install | `papyrusSource.skse` |
| Vanilla (~14300 `.psc`) | `<skyrimSeRoot>/Data/Scripts.zip` → its `Source/Scripts/` | `papyrusSource.vanilla` |

**Flags file.** `TESV_Papyrus_Flags.flg` ships only in the **vanilla** `Scripts.zip` — neither
Enderal tree contains one. **[verified]** It resolves off the `-i` path, so having vanilla on the
path is what makes `-f=TESV_Papyrus_Flags.flg` work.

**Enderal's own scripts are prefixed `_00E_`** (1257 of them). **[verified]** A script name starting
`_00E_` is Enderal's; treat it as third-party source you read but do not edit in place — patch by
adding your own script, not by shipping a modified `_00E_` file, unless overriding it *is* the fix
and you have said so in the patch's notes.

**Per-project import dirs** — persist in `tools.json`'s `importDirs` array (the `papyrus-compile`
skill appends them to `-i` after the three trees). Record each one here as you discover it:

| API / framework | Source `.psc` dir |
|-----------------|-------------------|
| powerofthree's Papyrus Extender (`PO3_SKSEFunctions`, used by `ZEN_SettingsApplier`) | `<modlistRoot>/mods/powerofthree's Papyrus Extender/Source/scripts` |
| JContainers (`JValue`, `JMap`, `JContainers`, used by `ZEN_SettingsApplier`) | `<modlistRoot>/mods/JContainers SE/scripts/source` |
| Zen Traits (`ZenTraits_ArcaneFeverScript`, `ArcaneFever`: the list's fever API, used by Prophecy's `ZP_LegionEffect`) | `<modlistRoot>/mods/Zenderal - Patch Collection/Source/Scripts`. Put it **last**: it also holds Zen Traits' copies of two `_00E_` fever scripts |
| B612 (`b612_TraitsMenu`: Prophecy's v1 card menu, `ZP_ProphecyMenu`) | `<modlistRoot>/mods/B612 - my little asteroid of useful UI components/Source/Scripts` |
| _(more)_ | Add SkyUI/MCM, PapyrusUtil, etc. here when a patch's script needs them. |

## Creation Kit against Enderal

The CK is only needed for asset work and for the compiler binary — **all record editing here happens
in the Spriggit YAML**, so most sessions never open it. If you do:

- Use the **Skyrim SE** CK (`$Tools.creationKit`), pointed at Enderal's `Data`.
- `bAllowMultipleMasterLoads=1` must be set in `CreationKit.ini` (already set on this machine
  **[verified]**) — without it the CK refuses to load an ESP on top of an ESM chain.
- The CK's `sResourceArchiveList` lists the *Skyrim* BSAs; it does not know about `E - *.bsa`, so
  Enderal assets will be missing in the render window unless you add them.

## Gotchas

- **A missing `-i` folder makes the compile fail with no error. [verified 2026-10-24]** The compiler prints
  `Cannot use import folder "…" - Could not find a part of the path`, then `No output generated for X.psc,
  compilation failed` with **0 error lines** — even for a script that never imports anything from that
  folder. Every `-i` entry must exist. On 2026-10-24 two `tools.json` paths had gone stale (`papyrusSource.vanilla`
  → a removed Nemesis folder, now `papyrus-source/vanilla-stubs`; PapyrusUtil's mod folder renamed to
  `PapyrusUtil AE SE`). No vanilla `Scripts.zip` is installed on this machine; Enderal's tree carries every base
  type and the flags file, so nothing needs the vanilla tree.

- **Compiling against vanilla signatures.** If a script compiles clean and then misbehaves on an
  Enderal type, check the `-i` order — Enderal's tree must be first. 55 names collide.

- **Decompiled `.psc` is a reconstruction** (Champollion): auto-named vars, reconstructed control
  flow, lost comments/flags. Enderal ships real source for its own scripts in `ScriptsEnderal.zip` —
  **read that instead of decompiling** whenever the script is Enderal's.
- **Missing-type compile errors** → the referenced API's source isn't on the import path; add its
  `Source\Scripts` dir to `importDirs` in `tools.json` and record it in the imports table above.
- **A property added to a script whose instance is already running in a save stays `None` there.** This bites
  abilities, perk-granted effects and running quests: the plugin's new VMAD value does not reach the old instance.
  Verified in game 2026-10-23 with Prophecy's Ice Shot watcher (`Remaining` read as 0, so `Cannot call GetValue()
  on a None object`). For a new property on such a script, add a fallback (`If !Prop: Prop =
  Game.GetFormFromFile(<id>, "<plugin>")`), or have the player re-add the perk or spell.
- **Never call `UnequipAll` (or other inventory calls) on an actor from `OnDying`.** **[verified 2026-10-23]**
  The game crashed in `UnequipAllVisitor` (Crash Logger: `SkyrimSE.exe+0164668`, an inventory entry pointer of `0x63`).
  It was Prophecy's Legion skeleton ability calling `UnequipAll` in `OnDying`, on an archer that A Willing Sacrifice
  was disintegrating (`SetCriticalStage`, `SetAlpha`, `AttachAshPile`), with FEC's death effects also on it. Strip
  gear while the actor is alive, or just `Disable`/`Delete` the corpse, which takes its inventory with it.
- **PO3's `MoveToNearestNavmeshLocation` moves a ref to the nearest navmesh *vertex*, not the nearest point on the
  navmesh.** **[verified 2026-10-23 from `po3_PapyrusExtender.pdb`: the function's lambdas work on
  `BSTArray<BSNavmeshVertex>`]** On open ground, where navmesh triangles are large, that can be meters away. A thrown
  Utility Droid visibly landed off its throw. Use it only to rescue something placed inside geometry, never to
  "tidy" a position that is already right.
- **A `VisualEffect` property needs a Visual Effect (RFCT) record, not an Art Object (ARTO).** Pointing it at an
  ARTO logs `cannot be bound because (…) is not the right type`, and the property stays `None`. The RFCT wraps the
  art: `DA07SummonTargetFX 107D96` is the summon portal `SummonTargetFX 03F811`. Search `VisualEffects/` for an
  existing RFCT by `EffectArt:` before making one.
- **A line break for a UI string: build it in Papyrus with `"\n"`, not in a plugin string.** **[verified 2026-10-24]**
  Spriggit/Mutagen 0.40 stores every line break in a script string property as CRLF, even a lone `\r` from the YAML.
  B612's plain-text card description showed a stored `\n\n` as a huge gap. A Papyrus `"\n"` literal compiles to a lone
  LF (check the `.pex` string table). Prophecy's card header is built this way in `ZP_ProphecyMenu`.

## A script's events run concurrently: guard a long tick (2026-11-09)

Every event (and every external call) runs on its own thread, and the same script can run several at once;
nothing serialises them. A loop that re-arms `RegisterForSingleUpdate` at the top of `OnUpdate` so that an error
cannot kill it therefore gets a second `OnUpdate` running while a long first one (a 30-actor `PlaceAtMe` loop) is
still going: the Fog Wood spawned two themes at once. Re-arm first, then run the body under a `Bool InTick` flag
with a timeout (an aborted tick never clears its flag), as `ZFW_ArenaQuest.OnUpdate` does
([`patches/FogWood.md`](../patches/FogWood.md)).

## Never compare an array to None (2026-11-06)

`If myArray == None` compiles but is a **fatal runtime error** (`Error: Cannot cast from None to Actor[]` in the
Papyrus log) that aborts the whole function at that line; everything after it silently never runs. Test arrays as
booleans instead: `If !myArray` is true for a None array and for an empty one, `If myArray` for one with elements.
Found in the Fog Wood arena, whose load handler died before it could move the entry stone
([`patches/FogWood.md`](../patches/FogWood.md)).

## Quest script property values live in the save (2026-11-06)

A property's value is read from the plugin only when the script instance is created; from then on the save holds
it, and a rebuilt plugin with a new value changes nothing for an existing save. Anything a later build must be able
to change (a position, a FormID, a version number) belongs in an `AutoReadOnly` property, which the compiler bakes
into the `.pex` as a literal, and a form looked up by `Game.GetFormFromFile`. New properties (absent from the save)
do initialise from the plugin. Found when the Fog Wood stone would not move
([`patches/FogWood.md`](../patches/FogWood.md)).

## `<Global=...>` in objective text needs `UpdateCurrentInstanceGlobal` (2026-11-06)

The tag reads the quest instance's snapshot of the global, not its live value; call
`UpdateCurrentInstanceGlobal(theGlobal)` on the quest after changing it and before `SetObjectiveDisplayed`
(37 Enderal scripts do). A tag the engine does not replace reaches the HUD as `<Global=...>`, and the HUD's
Scaleform text field treats it as HTML: the tag and everything after it vanish, so "Wave <Global=X> cleared"
shows as "Wave ". Found by the Fog Wood banner ([`patches/FogWood.md`](../patches/FogWood.md)).

## `<Global=...>` needs the quest's Text Display Globals, captured at quest start (2026-11-06)

Correction to the entry above: `UpdateCurrentInstanceGlobal` refreshes only globals the quest record lists in its
**Text Display Globals** (QTGL; Spriggit `TextDisplayGlobals:`), which the quest instance captures when it starts.
A global missing from QTGL is never replaced, and a quest that started (in a save) before QTGL named the global
never captures it: the quest must be stopped and started again once. The Fog Wood does that from the Fogbound
Stone's own script (outside the quest), after the quest parks what must survive in a FormList
([`patches/FogWood.md`](../patches/FogWood.md)). The same restart is what makes a rebuilt plugin's new or changed
script property values reach an old save.
