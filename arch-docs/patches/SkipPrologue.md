# SkipPrologue

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **Source:** `src/SkipPrologue/`
- **Ships:** `Zenderal - Skip The Prologue.esp`
- **FormID block:** `0x800–0x802`

## What it does

`800` Quest `ZP_SkipProlog`, `801` Activator `ZP_SkipProlog_StartTrigger`, `802` its placed trigger ref in Ark market cell `070793`. Overrides `MQ101 03372B` (alias 183 `StartMarkerRef` → `TeleportMarker_ArkMarket 0EAB74`) and forwards FS's `CapitalCityMarketArea 07072A` header — neither costs anything from the block. Lands the player awake at Jespar's camp with `MQ02` *"The Void"* running; see the note below the table for the mechanism

## How the skip works

> **To skip to a point in Enderal's main quest, find the SetStage that Enderal's own fragment
> already implements — do not re-author the transition.** **[verified 2026-08-09]**
> `Zenderal - Skip The Prologue` is one `SetStage` call, because `MQ01.SetStage(130)` fires
> `_00E_MQ01_Functions.CleanUp()`, which resets the timescale, opens the dam gate, unlocks the MQ01
> doors, calls `Self.CompleteQuest()`, then `MQ02.Start()` + `MQ02.SetStage(10)`. MQ02 stage 10
> (`MovePlayerAndJesparToStart`) teleports the player to `MQ02_D0_PlayersWakeUpmarker02 0C41D9` and
> Jespar to `MQ02_D0_JesparSpawnMarker 07321F`, skips to 05:30 and chains to stage 15
> (`WakeUpPlayer`) for the fade-in and the get-up idle. The earlier version of this patch walked
> MQ01→MQ02→MQ03→MQ04 by hand for the same reason and only needed the first line of it.
>
> Three things that follow, all of which are cheaper to read here than to rediscover:
> - **Quests can start themselves off dialogue.** `NQ41` *"Arcane Fever"* needs no property, no
>   `Start()` and no stage: `TIF__000C3FE4`, on Jespar's first camp topic (`MQ02_D0_4b 0C3FD6`),
>   calls `NQ41.SetStage(5)`. Likewise the class — MQ02's later Jespar topics (`146654`, `14664F`)
>   set `iPlayerClass` and call `GivePlayerSkillbook()`, so pre-setting it double-grants the
>   starting skillbooks. Grep the `TIF__*` fragments for the quest before writing any of it yourself.
> - **Arcane Fever is the actor value `LastFlattered`, negated.** MQ01's `BeginHeadache()` does
>   `ModAV("LastFlattered", -15)`, so 15 fever is what a natural arrival at MQ02 carries. The fever
>   *ability* is `_00E_MQP03_MagicFeverSpell 02506B`, added by `MQP03.StrandingCutscene()` and
>   removed by MQ04's `FinishUp()` — present or absent tells you which side of Lishari's ritual a
>   start point is on.
> - **A skipped stage's side effects stay skipped, and that is sometimes correct.** `KillFinn()`
>   never runs, so `_00E_MQ01_FinnREF 085998` stays alive at the dam camp. Do **not** "fix" that by
>   disabling him — `CleanUp()` has that exact line commented out with `; SE: Fixes "cannot disable
>   an object with an enable state parent"`. Carbos `08599A` is `InitiallyDisabled` and never
>   appears at all. Faking the prologue quests into the journal is likewise wrong: `MQP01` 40,
>   `MQP02` 75 and `MQP03` 70 all carry fragments, and `MQP03`'s is `FinishQuestAndStartMQ01`,
>   which would restart MQ01 at stage 5.
>
> The player still spawns at `TeleportMarker_ArkMarket 0EAB74` and the trigger still lives in the
> Ark market cell, because that is what keeps them out of `MQP01Home` — `MQP01` is started by a
> trigger inside that worldspace, not by `MQ101`, whose `Fragment_332` only does
> `MoveTo(StartMarkerRef)`. `BeginSkip()` then `MoveTo`s the camp marker before racemenu, so
> character creation happens at the camp with **no new cell override** — placing the trigger in
> Vyn's `01A3F5` instead would have added an exterior cell to our conflict surface for nothing.
