# DynamicDodgeShotFix

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **Source:** `src/DynamicDodgeShotFix/`
- **Ships:** `Zenderal - Dynamic Dodge Shot Fix.esp`
- **FormID block:** none (overrides only)

## What it does

Dynamic Dodge Shot (Nexus 114101) never triggered. Its mechanism: right-click/left-hand while a bow is drawn runs the left-hand idle tree; DDS restricts vanilla `BowZoom 0A7033` to `GetMovementDirection` 0/1 and adds `BowDodge 000802` (left/right/back, plays `IdleReadElderScrollLonger`, which its OAR submods replace with the dodge). But it parents `BowDodge` beside `BowLeftAttack 09753B` under `NonMountedCombatLeft 00098E:Update.esm` with prev-sibling `Null` — a first-child slot also claimed by `AttackLeftHandForwardSprinting` (Update) and Attack_MCO's `DW_Block`/`H2H_Block` — and it lost: a strafing right-click entered `BowLeftAttack` (bow equipped), `BowZoom` refused, nothing played (OAR animation log showed no DDS clip at all). Fix: `BowDodge` re-parented INTO `BowLeftAttack` as first child, `BowZoom` chained after it (`BowBash` unchanged after `BowZoom`); records otherwise verbatim from DDS. **Verified in game 2026-10-05.** Two things that look like this bug but aren't: **the bow zoom requires Enderal's Trickster talent Eagle Eye** (`_00E_Class_Trickster_P03_A_EagleEye 066867`, `ModBowZoom`) — without it the block press while aiming is ignored and NO left-hand bow idle can fire; and **Bow Charge Plus's MCM "Dodge Shot"** (script + DAR on its global `0x827`) answers the same button with a different dodge — turn it off. Masters: Skyrim + `Dynamic Dodge Shot.esp`.
