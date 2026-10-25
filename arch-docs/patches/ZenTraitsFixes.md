# ZenTraitsFixes

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **Source:** `src/ZenTraitsFixes/`
- **Ships:** *(no plugin — one recompiled script)*
- **FormID block:** _(none)_

> **Another Zen Traits fork lives elsewhere:** Aeterna Veins' `ZenTraits_AeternaVeinsScript` (a −20% max Health cut kept
> current every 5 s, no full heal) ships in *Zenderal - Traits*, next to the cut ability it uses. See
> [`TraitsRework.md`](TraitsRework.md).

## What it does

Forks **Zen Traits'** `_00e_ambrosiaeffect` (shazdeh, MIT, upstream `1ae67a8`), which already replaces SureAI's copy. Upstream read Ambrosia's magnitude from the `Variable08` AV, which nothing ever writes, so Ambrosia reduced Arcane Fever by **0** while still playing its flash/sound/notification. One `; ZP` line restores `Self.GetMagnitude()` (the ALCH effect item: `0FEC69` → `1037EC`, 20 base / 15 under EGO). Upstream issue [shazdeh/Zen-Traits#2](https://github.com/shazdeh/Zen-Traits/issues/2). Compile needs `<modlistRoot>/mods/Zen Traits/Source/Scripts` on `-i` (for `ArcaneFever.psc`). **Must sort above `Zen Traits`** to win the loose-script conflict; retire once upstream ships the fix
