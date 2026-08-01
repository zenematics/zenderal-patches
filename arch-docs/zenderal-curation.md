# Zenderal — curation

What is in the list, why it is in the list, and what it cost. This is the human-facing companion to
`enderal-record-patterns.md`: that file is about *how* to write a patch, this one is about *why a
patch exists at all*.

> **Status: skeleton.** The structure, constraints and decision rules below are settled and verified.
> The **roster tables are empty on purpose** — fill them in as mods are actually chosen. An invented
> roster would be worse than none, because the first person to read it would trust it.

## The list in one paragraph

Zenderal is an Enderal: Forgotten Stories (Special Edition) modlist with three goals — **bug fixes**,
**modern combat**, and **modern visuals** — and one non-goal: it is not a total overhaul. Enderal is
a finished, authored game with its own balance, art direction and progression. Zenderal's job is to
remove the things that get in the way of playing it in 2026, not to turn it into a different game.
Every entry below has to answer *"which pillar, and what did it break?"*

## Hard constraints

These are properties of Enderal itself, verified against the install (see CLAUDE.md → "Enderal
ground truth"). They rule mods out before taste does.

| Constraint | Consequence for mod selection |
|---|---|
| Enderal SE is pinned to **SSE 1.5.97** (ships `skse64_1_5_97.dll`) | Every SKSE `.dll` plugin must be a **1.5.97 / pre-AE** build. AE (1.6.x) builds do not load. This eliminates a large share of modern Skyrim combat and UI mods outright, or restricts them to their legacy versions. **Check this first — it is the cheapest possible rejection.** |
| Enderal masters **only** `Skyrim.esm` + `Update.esm` | Any mod mastering `Dawnguard.esm`/`HearthFires.esm`/`Dragonborn.esm` needs its masters changed or is out. |
| **SkyUI is built into Enderal** | Never install SkyUI separately. UI mods that assume a stock SkyUI install need checking against Enderal's copy. |
| Enderal replaces **all light settings** (SureAI's own readme) | Skyrim ENB/weather presets are starting points, not drop-ins. Cutscene fades are the canonical regression. |
| Progression is **talents (3-tier perks + WordOfPower)** in a custom menu | Mods that add to vanilla perk trees are invisible to the player. See `enderal-record-patterns.md` §0.2. |
| Enderal overrides **55 vanilla script names** | Any mod shipping a `.pex` with one of those names will clobber Enderal's version. Check the filename against Enderal's script list before installing, not after. |

## Decision rules

1. **Pillar or out.** If a mod doesn't serve bug fixes, combat, or visuals, it doesn't go in — however
   good it is.
2. **Prefer the smallest mod that does the job.** A list's patch burden scales with how much each mod
   touches. A weapon-timing tweak that edits ten records is worth more than an overhaul that edits
   ten thousand and needs a patch against everything.
3. **Prefer mods already converted for Enderal.** An existing Enderal port has already paid the
   master/keyword/script-collision tax. Search Enderal's Nexus category before Skyrim's.
4. **Record the conversion cost.** If a mod needed a patch in this repo, its roster row must name the
   patch. A mod with an unexplained patch is a mod nobody can safely remove later.
5. **Balance is Enderal's, not yours.** Combat mods get tuned toward Enderal's numbers, not the other
   way round. Enderal's difficulty curve is authored around its talent system and its economy.

## Roster

One row per mod. `Patch` names the `src/<PatchName>/` folder in this repo that makes it work, or `—`
if it needed none.

### Bug fixes

| Mod | Version | Why | Patch | Notes |
|---|---|---|---|---|
| _(none recorded yet)_ | | | | |

### Modern combat

| Mod | Version | Why | Patch | Notes |
|---|---|---|---|---|
| _(none recorded yet)_ | | | | |

### Modern visuals

| Mod | Version | Why | Patch | Notes |
|---|---|---|---|---|
| _(none recorded yet)_ | | | | |

### Rejected

Worth keeping — it stops the same mod being re-evaluated every few months.

| Mod | Pillar | Why not |
|---|---|---|
| _(none recorded yet)_ | | |

## Load order

Enderal's stock order is two lines:

```
*Enderal - Forgotten Stories.esm
*SkyUI_SE.esp
```

Everything else is Zenderal. Record the intended ordering **and its reasons** here as it settles —
"why does this sit below that" is the part that is expensive to re-derive, and the part LOOT cannot
tell you.

| Position | Plugin | Must load after | Because |
|---|---|---|---|
| _(none recorded yet)_ | | | |

**Patches from this repo load last**, after everything they forward, or they are not forwarding
anything. See `enderal-record-patterns.md` §0.1.

## Known conversion hazards

Running list of things that have bitten a Skyrim→Enderal conversion. Add to it as they come up; each
entry saves someone a test cycle.

| Hazard | Symptom | Check |
|---|---|---|
| AE-only SKSE plugin | SKSE fails to load, or the game closes at the splash | Mod's file page lists a 1.5.97/SE build |
| Mod masters a DLC | Plugin doesn't load; changes simply absent | `MasterReferences` in xEdit (`-EnderalSE`) |
| Ships a `.pex` colliding with one of Enderal's 55 overridden vanilla scripts | Enderal behaviour subtly regresses elsewhere | Compare the mod's `Scripts/*.pex` names against Enderal's |
| Second copy of SkyUI | UI breakage, MCM oddities | Enderal already ships `SkyUI_SE.esp` |
| Skyrim ENB/weather preset | Washed-out lighting; **broken cutscene fades** | Run one story cutscene before signing off |
| Perks added to vanilla trees | Mod appears to do nothing | Enderal draws its own talent menu |

## Release process

Patches are built and released from this repo, not from the modlist. `main` produces rolling
pre-release archives on every push; a `vX.Y.Z` tag cuts a named release. See README →
"CI build & release" and the `/github-release` skill.

When the list ships a new version, note **which patch release it pins** — a modlist referencing
"latest" is a modlist that breaks when this repo moves.

| List version | Patch release | Date | Notes |
|---|---|---|---|
| _(none yet)_ | | | |
