# DFSlowTimeGuard

- **Source:** `src/DFSlowTimeGuard/` (SKSE plugin, CommonLibSSE-NG, Address Library; `build.cmd`)
- **Ships:** `SKSE/Plugins/ZenDFSlowTimeGuard.dll`, deployed as the MO2 mod `Zenderal - DF SlowTime Guard`
- **Log:** `Documents/My Games/Skyrim Special Edition/SKSE/ZenDFSlowTimeGuard.log` (this machine: under `OneDrive/Documents`)
- **Status:** built 2026-10-22. **Unverified in game.**

## The bug

A dismember during Seismic Stomp's slow motion (Zenderal - Prophecy: SlowTime, world at 30% for 10 s) snapped the
game back to normal speed (user report: "the two cancel each other out").

## Cause [verified from DF's source and script strings]

Dismembering Framework's player slow-mo is `dfplayerdismembereffectscript`, which calls its Papyrus native
`DismemberingFramework.SetGlobalTimeMultiplier` with the slow factor, `Wait`s, then calls it with 1.0. DF's native
(`src/Papyrus.hpp`, Seb263's GitHub source) skips values **below 1.0** while the player has a SlowTime-archetype
effect. It always lets the **reset to 1.0** through, so DF's slow-mo ending reset time mid-Stomp. Seismic Stomp's
`ZP_Prophecy_SeismicStomp_SlowTimeEffect 000938` is archetype `SlowTime`.

## Fix

At `kDataLoaded` (after every plugin's Papyrus registration, so it replaces DF's binding) the plugin re-registers
`DismemberingFramework.SetGlobalTimeMultiplier`. While the player has a SlowTime-archetype effect, any value is ignored
(and logged). Otherwise it calls `BSTimer::SetGlobalTimeMultiplier(value, false)`, exactly as DF does. DF itself is
not edited; its slow-mo still plays whenever no SlowTime effect is running.

## Verify

The log should show `DismemberingFramework.SetGlobalTimeMultiplier re-registered` at load. Dismembering during Seismic
Stomp should log `DF time multiplier 1.00 ignored`, and the slow motion should last its full 10 s. If no `ignored`
line ever appears while DF slow-mo still cancels Stomp, the re-registration did not replace DF's binding.
