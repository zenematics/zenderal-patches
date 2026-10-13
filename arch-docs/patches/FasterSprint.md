# FasterSprint

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **Source:** `src/FasterSprint/`
- **Ships:** `Zenderal - Faster Sprint.esp`
- **FormID block:** none (overrides only)

## What it does

Global (player + NPC) sprint speed **+92.03%** on top of EGO's current values (five stacked bumps, each applied to the current live value: +20% shipped, then +15%, +10%, +15%, +10% — 1.2 × 1.15 × 1.10 × 1.15 × 1.10 = 1.92027× overall) — overrides `NPC_Sprinting_MT` (`034D9C:Skyrim.esm`, `ForwardWalk`/`ForwardRun` 440→**844.9188**) and `AIControlledNPC_Sprinting_MT` (`0F3469:Skyrim.esm`, 450→**864.1215**). `BackWalk`/`BackRun`/rotation fields left untouched. Plus a **sprint stamina drain -50%**: overrides GMST `fSprintStaminaDrainMult` (`02DD35:Skyrim.esm`, EGO's `4` → `2`; base Enderal was `7`, so this is 50% of EGO's *current* value, matching this patch's "on top of EGO" convention). Confirmed only EGO touches this GMST anywhere in the active load order (grepped every `.esp`/`.esm` in the modlist for the string), so no other patch's value is being reverted. `fSprintStaminaWeightMult`/`fSprintStaminaWeightBase` left untouched — halving the leading `DrainMult` factor already scales total drain by 50% uniformly regardless of carry weight, no need to touch the weight-scaling GMSTs too. Master: `Skyrim.esm` only (no EGO FormKey is referenced, only its record is overridden — but this plugin **must load after both** `Enderal SE - Gameplay Overhaul.esp` **and** `Dynamic Sprint.esp` in-game to win the conflict on both — see below; declaring either as a master isn't required since no FormLink to either exists). See `arch-docs/zenderal-curation.md`. **Note:** `RecordData.yaml`'s `ModHeader.Description` says "by 80%" — that's stale/wrong, the actual sprint-speed ratio everywhere is 1.92027× (+92.03%); not corrected, flag if touching that file next. This value is now within one further +10% stack of doubling the original shipped speed — worth confirming with the user whether more increments are actually wanted or whether this has drifted past a comfortable gameplay pace; each increment so far has been a direct explicit request, not an assumption.

## Dynamic Sprint was reverting it

> **THE ACTUAL ROOT CAUSE of "sprint speed changes don't show up in-game," found 2026-08-12 after an
> extensive false-trail investigation: a THIRD mod, `Dynamic Sprint.esp`, overrides the exact same two
> records** (`NPC_Sprinting_MT` `034D9C` and `AIControlledNPC_Sprinting_MT` `0F3469`) and was loading
> **after** `Zenderal - Faster Sprint.esp` in the user's list — silently reverting this patch's boost
> back to `Dynamic Sprint`'s own values every time, regardless of what number this patch shipped. This
> is guardrail 5 (forward, don't author) played out from the *other* side: it wasn't our override
> failing to forward something, it was a *later-loading* mod we didn't know existed reverting *us*.
>
> This single conflict explains every "no effect" result logged in the entries below it — the
> `NPC_1HM_MT`/`NPC_2HM_MT`/`NPC_Bow_MT` experiment, the stale-deploy-file rounds, the SSMT_Fix
> back-and-forth, and three further stacked speed increments (+15%, +10%, then a 3× diagnostic jump)
> that all "did nothing" even once every other variable (file staleness, launch method, SSMT_Fix
> config) had been independently verified correct. The 3× diagnostic value (1320/1350) that finally
> "worked" only did so because the user reordered `Dynamic Sprint.esp` to load *before*
> `Zenderal - Faster Sprint.esp` at the same time — not because 3× was special. Confirmed by dialing
> back down to the intended 1.518× value (667.92/683.1) with the corrected load order and having it
> still take effect.
>
> **Consequence: add `Dynamic Sprint.esp` to the same "must load after" requirement as EGO.** There is
> no FormKey link to enforce this (same reasoning as the EGO note above — nothing to master), so a
> Zenderal install that has `Dynamic Sprint` enabled and mis-ordered will silently keep its own sprint
> values with zero error, exactly as happened here. Worth a load-order note in the FOMOD/mod-page
> description if this patch ships standalone. `Dynamic Sprint.esp` was *disabled* for most of this
> session (hence not caught earlier by the "grep every enabled esp" checks, which only searched
> `E:/Zenderal/mods/` file contents, not enabled state) and only got re-enabled partway through —
> **grep-for-conflicts checks must be re-run any time a mod's enabled state changes**, not just once
> at the start of a debugging session.

## Armed sprint, SSMT_Fix and the stale deploy

> **RESOLVED 2026-08-12: armed sprint was never a records problem — it was a stale-deploy bug plus
> an external mod's fix shipping disabled.** The trail below (`NPC_1HM_MT`/`NPC_2HM_MT`/`NPC_Bow_MT`)
> was a wrong turn investigated before the real cause surfaced; kept for the record since the
> negative results (nothing references those three FormKeys) are still true and might save someone
> re-deriving them. But **do not trust its "disproven" conclusion as strongly as it reads below** —
> it was tested manually-deployed, and a manually-deployed `.esp` in this workspace turned out to be
> silently stuck three days stale for several rounds of testing afterward (see the deploy-hygiene
> note at the end of this entry). It was never re-verified with a confirmed-fresh deploy.
>
> **The actual mechanism:** `NPC_Sprinting_MT` (`034D9C`) and `AIControlledNPC_Sprinting_MT`
> (`0F3469`) — the two records `FasterSprint` has overridden from the start — DO govern armed sprint
> correctly, but only once a real vanilla engine bug is worked around: while a weapon is drawn, the
> behavior graph can resolve to `NPC_Default_MT` (`03580D`) instead of `NPC_Sprinting_MT` even during
> an actual stamina-draining sprint. This is independently documented by a third-party mod already in
> this list's modlist — **`Sprint Sneak Movement Speed Fix`** (SKSE plugin, `SSMT_Fix.dll`) — whose
> own description names the exact symptom: *"NPC_Sprinting_MT should be set while sprinting, instead
> NPC_Default_MT is applied when a weapon is drawn... due to mistakes in behavior graphs."* Its fix
> for this is gated by an ini flag that **ships disabled by default**:
> ```
> <mod>/SKSE/Plugins/SSMT_Fix.ini
> WieldingMovementTypeFixes=false   ← must be true for FasterSprint's armed-sprint boost to apply
> ApplyToNPC=false                  ← player-only; leave as-is, matches this patch's scope
> ```
> Confirmed in-game 2026-08-12 with a verified-fresh deploy and a deliberately absurd 3x test value
> (`ForwardRun` 1320/1350): with `WieldingMovementTypeFixes=true`, **both** sheathed and armed sprint
> scaled up dramatically. Dialed back to the shipped 1.2× (528/540) afterward.
>
> **Consequence: `FasterSprint`'s armed-sprint effect has an undeclared soft dependency** on
> `Sprint Sneak Movement Speed Fix` being installed with `WieldingMovementTypeFixes=true`. There is
> no FormKey link (nothing to master), so Spriggit/the build can't enforce or even detect this — a
> Zenderal install without that mod (or with the setting left at its shipped default) will still get
> the full boost while sheathed but silently keep vanilla/EGO armed-sprint speed, with no error
> anywhere. Worth a line in the FOMOD/mod-page description if this patch is ever released standalone
> outside a curated modlist that already carries the dependency.
>
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
