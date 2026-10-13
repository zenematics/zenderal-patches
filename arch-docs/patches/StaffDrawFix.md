# StaffDrawFix

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **Source:** `src/StaffDrawFix/`
- **Ships:** *(no plugin — OAR submod, MO2 mod `Zenderal - Staff Draw Fix`)*
- **FormID block:** _(none)_

## What it does

**The third-person staff draw never showed — the staff popped into the hand.** OAR's animation log showed `StaffRight_Equip` activating (original), then `MRh_and_MLh_Equip` + `MLh_Equip` activating right after, both `[Replaced]` by Smooth Magic Casting Animation 4.2's legacy DAR folder `_CustomConditions/996`, whose condition is always true (`IsActorBase(Player) OR NOT IsActorBase(Player)`), so its magic equip plays over the staff draw. Dynamic Random Spell Idle replaces the same clips but every equip submod excludes a right-hand staff (`IsEquippedType 8`, negated) — the intended pattern. Fix: one OAR submod, `IsEquippedType 8` right hand, priority 8300000, carrying the VANILLA `mlh_equip`/`mrh_and_mlh_equip`/`mlh_unequip`/`mrh_and_mlh_unequip` extracted from `Skyrim - Animations.bsa` by `src/StaffDrawFix/tools/01-build-staff-draw-fix.py` (not committed — Bethesda's clips). First person is unaffected (IC-VanillaAnims, priority 99999999). Built 2026-10-13, not yet verified in game.
