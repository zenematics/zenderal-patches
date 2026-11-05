# ZenTraitsFixes

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **Source:** `src/ZenTraitsFixes/`
- **Ships:** *(no plugin — two recompiled scripts; the live copies are in `Zenderal - Patch Collection`)*
- **FormID block:** _(none)_

> **Another Zen Traits fork lives elsewhere:** Aeterna Veins' `ZenTraits_AeternaVeinsScript` (a −20% max Health cut kept
> current every 5 s, no full heal) ships in *Zenderal - Traits*, next to the cut ability it uses. See
> [`TraitsRework.md`](TraitsRework.md).

## What it does

Forks **Zen Traits'** `_00e_ambrosiaeffect` (shazdeh, MIT, upstream `1ae67a8`), which already replaces SureAI's copy. Upstream read Ambrosia's magnitude from the `Variable08` AV, which nothing ever writes, so Ambrosia reduced Arcane Fever by **0** while still playing its flash/sound/notification. One `; ZP` line restores `Self.GetMagnitude()` (the ALCH effect item: `0FEC69` → `1037EC`, 20 base / 15 under EGO). Upstream issue [shazdeh/Zen-Traits#2](https://github.com/shazdeh/Zen-Traits/issues/2). Compile needs `<modlistRoot>/mods/Zen Traits/Source/Scripts` on `-i` (for `ArcaneFever.psc`). **Must sort above `Zen Traits`** to win the loose-script conflict; retire once upstream ships the fix

## Potion fever counted twice (2026-11-05)

NickyBoy (0.9.2): a health potion said Arcane Fever had lessened while the number rose by an odd amount (not the 2%
shown). **Cause:** Enderal 2.1 changed `_00E_AlchIncreaseArcaneFever 02F21D` (FS, no overrider) from `Type: Script`
(2.0) to a value modifier on `LastFlattered`; SureAI's 2.1 `_00E_ArkanistenfieberBlitzheilungSCN` only shows the
message. Zen Traits' replacement of that script is from 2.0 and calls `ArcaneFever.ModFever(-GetMagnitude())`, so on
2.1 the fever is changed twice: by the engine and by the script (with its own sign, Mental Expert and trait
multipliers, and its "lessened" message when the sign comes out positive). Not new in 0.9.2: the Patch Collection
merge (2026-11-03) left Zen Traits' files byte-identical; the 2.1 update (2026-10-21) is what broke it.

The same script also runs on effects where it must still apply the fever: EGO overrides `11A4B6` to `Type: Script`
and adds `0083D0`/`001E51`/`0083D2`, and EGO's `AlchFeverHealth/Mana/Stamina` (`001FD3`/`D4`/`D6`) modify
Health/Mana/Stamina. **Fork** (`; ZP`): at effect start, `PO3_SKSEFunctions.GetPrimaryActorValue(GetBaseObject())`;
on `LastFlattered` the engine's amount stands and only Zen Traits' trait multipliers are added on top (Mental
Expert divided back out: 2.1 handles it with its own effect `0493DF`), then Zen Traits' "increased" message; on
any other effect, Zen Traits' code unchanged. Same two properties as Zen Traits' script. **Compile with
`src/ZenTraitsFixes/Scripts/source` FIRST on `-i`**: Enderal's tree has a same-named source and is first-wins
otherwise (the first build compiled SureAI's). Imports Zen Traits' sources from `Zenderal - Patch Collection/Source/Scripts`.
Old copy in `E:/Zenderal-backups/2026-11-05-zentraits-potion-fever/`. Unverified in game: drink a health potion and
check the fever goes up by the potion's stated amount with an "increased" message.
