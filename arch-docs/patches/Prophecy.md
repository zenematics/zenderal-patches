# Prophecy

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **Source:** `src/Prophecy/`
- **Ships:** `Zenderal - Prophecy.esp` + 2 scripts + `NetScriptFramework/Plugins/CustomSkill.Prophecy.config.txt`
- **FormID block:** `0x800–0x807`

## What it does

**PROTOTYPE — not an ESL yet, on purpose.** A separate perk tree for Ordinator-derived perks (see [`arch-docs/ordinator/`](../ordinator/)), opened by the **Prophecy** power and drawn by **Custom Skills Framework** on the engine's vanilla StatsMenu. `800` `ZP_ProphecyLevel`, `801` `ZP_ProphecyRatio`, `802` `ZP_ProphecyPoints` (the tree's own currency; CSF spends it), `803` `ZP_ProphecyShowMenu`, `804` test perk *First Omen*, `805` power `ZP_ProphecyPower`, `806` its script MGEF, `807` StartGameEnabled+RunOnce quest that `AddSpell`s the power. The power just sets `ZP_ProphecyShowMenu` to 1 — CSF polls that global every frame and opens the tree, so no CSF Papyrus native is needed and it works with either CSF build. Config is the CSF v2 / meh321 INI format (`Data/NetScriptFramework/Plugins/CustomSkill.<id>.config.txt`). **Needs a 1.5.97 CSF**: current Exit-9B CSF (3.x) is AE-only (address IDs like `410201`); the candidates are meh321's original NetScriptFramework CSF (NSF is already in the list) or CSF v2.0.2's SE build from Nexus 41780 old files. CSF v2 renders through the beast-skill (vampire) path and defaults to `DLC01/Interface/INTVampirePerkSkydome.nif`, which Enderal ships in `Skyrim - Meshes0.bsa`. Kept non-ESL until CSF is proven to resolve FormIDs in a light plugin (one variable per test). Built 2026-10-08, round-trips identically; **not run in game**.
