# CompanionHugFix

- **Source:** `src/CompanionHugFix/` (generated: `tools/01-build-companion-hug-fix.py`)
- **Ships:** `Zenderal - Companion Hug Fix.esp` (ESL, HEDR 1.7). Masters Skyrim, Update, FS and
  `ImmersiveInteractions.esp`. The live copy is in `Zenderal - Patch Collection`. Load after `ImmersiveInteractions.esp`.
- **FormID block:** none (one override)
- **Owns:** global `AR_hugspouse 04252B:ImmersiveInteractions.esp`
- **Status:** built and round-trip clean 2026-11-08, deployed. Unverified in game.

## Why

Player report (Junebug, 2026-11-08): holding E near a companion "randomly triggered a makeout animation"; hard to
reproduce.

- **The mod:** *Immersive Interactions - Animated Actions* (a Skyrim mod, with its Enderal patch). Its
  `AR_QuestScript.ffriend` runs when the player activates a follower or spouse. Sometimes it plays a hug instead of
  opening dialogue: `PlayerRef.PlayIdleWithTarget(pa_huga, friend)`.
  - relationship rank 3 (follower/ally): 1 in 15, when `AR_hugfollower` and `AR_hugspouse` are both 1;
  - rank 4 (lover): 4 in 15, when `AR_hugspouse` is 1.
  Both copies of `AR_Quest` (the mod's and its Enderal patch's) fill `pa_huga` with `pa_HugA 0F4699:Skyrim.esm`.
- **In Enderal that IDLE is a romance scene.** It sends `pa_HugB`, Enderal's own paired clip
  `enderal\paired_hugb.hkx`, one of the hug/kiss scenes [`EnderalPairedAnims`](EnderalPairedAnims.md) made playable
  under Pandora again. Before that patch the scene stood still; now the Skyrim "friendly hug" plays Enderal's kiss.
- The random rolls are why it was "pretty tricky to reproduce".

## The fix

`ImmersiveInteractions.esp`'s global `AR_hugspouse` verbatim with `Data` 1 → 0 (asserted). That is the MCM option
*Hug Spouses and Followers*, which gates both hug paths. Followers still salute (`AR_hugfollower` is untouched), and
activation goes straight to dialogue.

- The MCM toggle's own default is `True` in its script, so the menu shows the option on until the player clicks it.
  Clicking it twice sets the global to 1 again; that is the player's choice.
- A global keeps its plugin value in a save unless something changed it at runtime, so existing saves where nobody
  touched that MCM option should pick up 0. **[unverified]**

## Upkeep

After an Immersive Interactions update, re-serialize `ImmersiveInteractions.esp` into
`reference/mods/ImmersiveInteractions` and rerun `python -I src/CompanionHugFix/tools/01-build-companion-hug-fix.py`.

## To verify in game

Activate a companion 20+ times (third person, out of combat): no hug or kiss plays, and dialogue opens. In the console,
`help AR_hugspouse 3` shows the value 0.
