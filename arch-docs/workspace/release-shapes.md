# Release shapes

What a Zenderal release can be, and the rules each shape carries. The build side is `build/manifest.json` + `build/build.ps1`; `/mod-new-plugin` scaffolds a new one.

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

> **Two shapes of release exist.** Most are **patches**: a small plugin of overrides that masters the
> mod it fixes — everything in this repo is one. A few mods must instead be **replacements**: the
> third-party plugin itself, rebuilt with our changes and shipped under its *original filename* so
> its BSAs keep loading, with `src/<Name>/<Name>ESP/` holding *all* of the author's records rather
> than just our edits, because that is what the build deserializes. A replacement is only legitimate
> when the author's permissions allow modification and re-upload, and it must ship credit in the
> plugin header and on the mod page. It also needs a `tools/` folder of generators that can rebuild
> the tree against a new upstream version — without those, an update means redoing the analysis from
> scratch.
>
> **Replacements are not built here.** The [form-version ceiling](testing-and-debugging.md#the-form-version-ceiling-hedr-171-and-bees) forces some Enderal ports into
> that shape, and those live in the
> [`enderal-mods`](https://github.com/whisperdealer/enderal-mods) repo, which holds Enderal SE mods
> in general rather than this list's patches. `Apocalypse - Magic of Skyrim` is the worked example and
> the source of most of what the ceiling section below records.

> **A third shape: the SCRIPT-ONLY release — no plugin at all.** **[verified 2026-08-08]** When a
> third-party mod's misbehaviour lives entirely in a *loose* `.pex` and not in its records, the patch
> is one recompiled script and nothing else. `build/manifest.json` supports it directly: set
> `"plugins": []` alongside `"fomod": false` and a `"scripts": { "from": …, "to": "Scripts" }` block.
> `build.ps1` handles that without changes — the `foreach ($p in $rel.plugins)` loop simply runs zero
> times, and the release contributes an archive but no row to the build report's Plugins table.
>
> Four rules, learned building `Zenderal - No Kata Debug Prompt` (that release was later absorbed
> into `Zenderal - Kata Fixes`, which ships the recompiled script *alongside* a plugin — a release
> may mix both; the rules below apply to its `scripts` block unchanged):
> 1. **Start from the author's own `.psc`, copied verbatim**, and change the fewest lines possible
>    (guardrail 4). Most mods that ship loose scripts ship their `source/` next to them.
> 2. **Never add or remove a `Property` declaration.** The host plugin's quest record stores the
>    property *values* in its `VMAD` and binds them **by name** at load. Drop a declaration and
>    Papyrus logs an unresolved property every load; rename one and its value silently never arrives.
>    Read the values out of the serialized record and diff the property set against your script before
>    compiling — `rg -a -o '<names>' both.pex | sort -u` on the two `.pex` is the cheap confirmation.
> 3. **It only wins if it sorts ABOVE the mod it overrides in `modlist.txt`** — MO2 writes that file
>    highest-priority-first (the list's `EGO SE - *` patches sit ~20 lines above the `KataPUMB *` mods
>    they patch). Getting this backwards is invisible: the game runs and the original script wins.
> 4. **A `.pex` override only bites where the script re-runs.** An `OnInit()` fix reaches new games
>    and saves that never had the mod; a save where `OnInit` already fired is untouched.
>
> This shape carries an obligation the others don't: it redistributes a **modified copy of someone
> else's script**, so check the author's permissions and credit them in the source header.

> **A fourth shape: the SPID CONFIG release — no plugin, no script, one `.ini`.** **[verified
> 2026-08-13]** *Spell Perk Item Distributor* 7.3.2 is in the list, and a fix that only needs to hand
> a spell/perk/keyword/outfit to a set of NPCs is a text file, not a plugin. `build/manifest.json`
> carries it with `"plugins": []`, `"fomod": false` and a **`"files"`** block:
>
> ```json
> "files": [ { "from": "src/<PatchName>/spid/Zenderal - <Name>_DISTR.ini", "to": "" } ]
> ```
>
> `"to": ""` is the **archive root** and it has to be, because SPID scans the Data folder with a
> *non-recursive* `directory_iterator` — a config one folder down is never seen and nothing warns.
> Three rules:
> 1. **Prefix the shipped filename `Zenderal - `.** Two mods shipping the same `_DISTR.ini` name are
>    an ordinary MO2 file conflict and only the winner deploys, silently. This list already has one:
>    10 `_DISTR.ini` on disk, `9 matching inis found` in the log.
> 2. **Write it pre-sanitised** — `~` not ` - `, no spaces around `|` or `,`, `0x` FormIDs with no
>    leading zeros. SPID rewrites any config it has to normalise, in place, inside the deployed mod
>    folder, so the committed and deployed copies otherwise drift.
> 3. **Verify with `Registered X/Y` in `po3_SpellPerkItemDistributor.log`, not by launching.** Every
>    unresolvable filter is skipped per entry and logged, never surfaced in game — Enderal currently
>    registers **198/318** of the list's keyword entries.
>
> Full detail in [`arch-docs/tools/spid.md`](../tools/spid.md) and
> [`spid-in-enderal.md`](../tools/spid-in-enderal.md). Read the second one before porting a
> Skyrim config: faction, NPC and location filters almost never survive, and `NordRace` resolves in
> Enderal to **Half Arazealean**.

`src/` is the only place patch content goes, and it holds as many patches as the list needs. Each
gets its own `src/<PatchName>/` folder and its own `build/manifest.json` release entry; the
`/mod-new-plugin` skill sets both up.

## Two mutually exclusive upstream builds

> **When a mod has two mutually exclusive upstream builds, ship two ARCHIVES of ONE ModKey — not
> two plugins.** **[verified 2026-08-06]** johnskyrim's Relentless Sword exists as a free Nexus
> build (6 swords) and a Patreon "ZEN" build (the same 6 plus a Zen-design pair). The user owns one
> or the other, never both — the ZEN download is a rebuild of the whole mod, not an add-on.
>
> Two shapes were tried. **An add-on plugin mastering the base patch was wrong**, and its failure
> mode is the generalisable part: the base patch overrides `FlusshaimTemple 015282` (to place the
> blueprint) and `_00ETraderCraftingPlansC 148ABE` (to stock it), so *any* second plugin of ours
> touching either would win on load order and **silently delete the first patch's entry** —
> guardrail 5, turned against our own repo.
>
> The shape that works: **two releases, both emitting `Zenderal - Relentless Sword.esp`**, one with
> 33 records and one with 43. Same filename ⇒ they physically cannot both be enabled, no conflict
> is possible, and because the Zen tree copies the base records **byte-identically** and allocates
> its additions **above** them at `0x828+`, a user swapping builds keeps every FormID — swords
> already in a save survive. `manifest.json` allows this directly: two releases may share a `dest`.
>
> The cost is a duplicated YAML tree, which the build requires (it deserializes a folder), plus a
> generator to keep the two from drifting (`build-zen-tree.ps1`, which rebuilt the Zen tree from the
> base one and asserted file counts, blueprint gating and the absence of dead Skyforge refs).
>
> **This repo no longer ships that pair.** On 2026-08-16 the six-blade release and its generator
> were removed and the Zen tree was renamed `src/RelentlessSwordPatreon/`, leaving one release that
> requires the Patreon build. The note stays because the *shape* is the reusable part — and note the
> two things the retirement had to preserve: the **plugin filename** (renaming it would strand every
> sword in an existing save) and the `0x828+` allocation above the retired block.
>
> Verified on the built plugin: `MAST Skyrim.esm` + `MAST Enderal - Forgotten Stories.esm` (no
> third master), HEDR 1.7, ESL flag intact, `nextObjectId 0x832`, and all 244 FormKey references
> resolving. **That is a verified BUILD, not a verified RUN** (guardrail 8).

## FOMOD images that actually render in MO2

- **FOMOD images that actually render in MO2** — a config can build clean, pass
  `build.ps1 -CheckFomod`, open its wizard normally, and still show *no image at all*. Nothing
  warns you. This recipe is confirmed working in MO2; copy its shape rather than re-deriving:
  1. `path=` is relative to the **archive root**, so an image at `fomod/images/foo.jpg` is
     referenced as `path="fomod\images\foo.jpg"` — *including* the `fomod` prefix.
  2. Use **backslashes** in `path=`.
  3. Declare an `<installSteps>` block, even for a patch with no real choices (one
     `SelectExactlyOne` group holding a single `Recommended` plugin). A config with only
     `<requiredInstallFiles>` gives MO2 no wizard page to draw the banner on.
  4. Use a **baseline** JPEG or a PNG, not a progressive JPEG. Check with
     `od -A d -t x1 -v img.jpg | grep -oE 'ff c[0-9a-f]'`: `ff c0` is baseline (fine), `ff c2` is
     progressive. Re-encode progressive files via `System.Drawing` before shipping.

  These four were fixed **together** after several one-at-a-time attempts each failed, so which is
  individually decisive is unverified — treat the set as the known-good recipe, and do not drop one
  on the assumption it does not matter.

  `build/build.ps1 -CheckFomod` enforces points 1, 2 and 4: an unresolvable `path=` or a
  progressive JPEG **fails** the check (with a "did you mean `fomod\…`?" hint for the missing
  prefix), and forward slashes warn. It cannot check point 3 — whether an `<installSteps>` block
  exists at all — because a config legitimately may not want one.

## No starter plugin

**There is deliberately no starter plugin.** `build/manifest.json` ships with `"releases": []`, and
the build reports "nothing to build" and exits 0 in that state — the repo is green from the first
commit and stays green until there is a real patch to ship.
