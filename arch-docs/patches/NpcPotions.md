# NpcPotions

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **Source:** `src/NpcPotions/`
- **Ships:** `Zenderal - NPC Potions_DISTR.ini`
- **FormID block:** _(none — SPID config, no plugin)_

## What it does

**The repo's first worked example of the fourth release shape** (`"plugins": []` + a `files` block, `"to": ""`). 16 `Item =` lines distributing Enderal's three restore-consumable lines plus Ambrosia to `ActorTypeNPC` humanoids, level-banded `1/9`, `10/17`, `18/27`, `28/37`, `38` — the same 10/18/28/38 ladder as `_00ETraderPotion10/20/30`. Health `_NNE_Genesungstrank` (`0028C8`, `0028C5`, `0028C6`, `0028C7`, `0028C9` — **non-monotonic, do not sort**) at chance 55; mana `_NNE_Manatrank` (`0028DB`, `019E3B`, `090892`, `09B6CB`, `1037F7`) and stamina `_NNE_Morgenlufttrank` (`0028DE`, `085668`, `09B6CA`, `1037F5`, `1037F6`) at 45; **all count `1`** — cut from `1-2` once NUP's corpse-stripping was turned off, since nothing trims the piles any more. Ambrosia `_00E_Ambrosia 0FEC69` is a **`DeathItem =`**, count 1, chance 10 — see the NUP note below for why it is not an `Item =`. Traits `-S/-C/-D` exclude summons, children and StartsDead props. For the `Item =` lines, **chance is rolled per BASE NPC record, not per corpse, and it is all-or-nothing** — win and every instance of that base carries the item, lose and none ever do. A single low-chance line therefore reads as "never drops": Ambrosia at 12 hit 22 of 182 bases exactly as configured, but ~16 of those were townsfolk, leaving a typical fight (5–10 distinct enemy bases) a ~36% chance of yielding none. **[verified in-game 2026-08-13]** Budget per-base, not per-kill, and remember `ActorTypeNPC` is mostly civilians. **`DeathItem =` rolls per CORPSE instead**, which is the fix for that whole class of problem whenever the item is meant as loot rather than as something the NPC uses **`Morgenlufttrank` is the restore-stamina line** — `_NNE_Ausdauertrank` is *fortify* stamina and has only 2 tiers in base Enderal (a 3rd is EGO's new `0008C0`), so it is the wrong record. **Supersedes `Zenderal - Enemy Potions.esp`** — an untracked mod at MO2 priority 24 with no source in this repo, which banded the same three lines into the `_00E_MOB_Bandit` / `DeathItemDraugr` / `_00E_FS_DeathItem_Human` death-item lists; disable it or those NPCs draw from both. Unlike death items, SPID puts these in the base NPC's *live* container, so they can be drunk by an NPC-potion AI that uses inventory — `NPCs Use Potions` did, but **NUP is disabled since 2026-10-07** and Smart NPC Potions conjures its own, so these are currently **loot only**. If NUP is ever re-enabled: it STRIPS EVERY CORPSE and will silently eat a distributed item — see the section below; this release depends on its `RemoveItemsOnDeath` being off

## NPCs Use Potions strips every corpse

> ### `NPCs Use Potions` STRIPS EVERY CORPSE — it will silently eat anything you distribute
>
> **2026-10-06: the list now ships `RemoveItemsOnDeath = false`, `GlobalItemCooldown = 15000` and
> `OnlyAllowFoodAtCombatStart = true`** (in the `Zenderal - Settings` MO2 mod) — corpses keep their potions,
> NPCs drink at most once per 15 s and never eat mid-fight. Smart NPC Potions was removed the same day
> (it conjures potions with `EquipItem`, no inventory needed, which read as enemies auto-healing) and
> **re-added on 2026-10-07 (Alpha 0.5), tuned down instead**: use chance 40→**10%**, max potions per
> fight 4→**1**, corpse drop chance 15→**50%**. Its MCM is save-based, so those values ship in
> `Zenderal - Settings Applier`, not as files. The history below is why NUP's removal must stay off.
>
> **2026-10-07: NPCs Use Potions itself is now DISABLED in Alpha 0.5.** Smart NPC Potions is the only
> NPC-potion AI left. Nothing strips corpses any more, and nothing makes NPCs drink from their own
> inventory, because Smart NPC Potions conjures its own potions. `Zenderal - Settings` still ships
> `SKSE/Plugins/NPCsUsePotions.ini`, which is inert while NUP is off. Everything below applies only if
> NUP is re-enabled.
>
> **[verified in-game 2026-08-14]** The list runs *NPCs Use Potions* (SKSE DLL + `*_NUP_DIST.ini`
> rules), and its live settings in `zenderal/overwrite/SKSE/Plugins/NPCsUsePotions.ini` ship as:
>
> ```ini
> [Removal]
> RemoveItemsOnDeath = true
> ChanceToRemoveItem = 90
> MaxItemsLeftAfterRemoval = 2
> ```
>
> Every dying NPC has its alchemy items culled — each item faces a **90% removal roll**, and at most
> **2 survive**. NUP does this on a **worker thread** (`Started RemoveItemsHandler`,
> `[TESDeathEvent] Removed item {}`), so it runs *after* anything else hooked to `TESDeathEvent`.
>
> **This cost a full diagnosis cycle on Ambrosia.** A single-count item cannot win that lottery
> against the ~6 potions the same config distributes: at SPID chance **100**, on **every humanoid
> base in the game**, Ambrosia reached **zero** corpses. The SPID log was clean and correct
> throughout — `Registered 17/17 Items`, then `[📦] _00E_Ambrosia [ALCH:000FEC69]` on base after
> base. Switching to `DeathItem =` did not help either: the log showed `[💀][📦]` delivering to all
> four test corpses and the loot was still empty, because NUP's thread strips it afterwards. Only
> `RemoveItemsOnDeath = false` made it appear, on every corpse, immediately.
>
> Generalise the *diagnosis*, not just the fix:
> - **A clean SPID log does not mean the item reached the player.** SPID reports what it distributed,
>   not what survived. Prove delivery *and* survival separately.
> - **Test at chance 100 before tuning a chance.** It converts "is it rare?" into "does it work?" in
>   one launch. Zero hits at 100% is proof of removal, not of bad luck.
> - **A rare item competing with common ones is the worst case**, because the cull keeps a fixed
>   *count*. The commons crowd out the rare even when the rare survives its own roll.
> - NUP also has `DistributePotions = true`, and Enderal's potions live in a plugin literally named
>   `Skyrim.esm` — which NUP's whitelist covers. So NUP is probably already handing out Enderal's
>   restore potions on its own, which would make our three potion lines largely redundant.
>   **Unverified** — NUP's `EnableLogging` is off; one run with it on would settle it.
