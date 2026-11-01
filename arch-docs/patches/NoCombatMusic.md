# NoCombatMusic

- **Source:** `src/NoCombatMusic/`
- **Ships:** `Zenderal - No Combat Music.esp` (ESL, HEDR 1.7, one override, masters only `Skyrim.esm`)
- **FormID block:** none
- **Pillar:** curator's taste

## What it does

Starting a fight no longer starts battle music. The area's exploration or dungeon music keeps playing
through the fight. Quest-scripted music is unchanged.

## How Enderal 2.1 starts combat music

2.1 changed the mechanism, so read 2.1's records and not `reference/base/` (2.0):

| | Enderal 2.0 (`reference/base/`) | Enderal 2.1.4.4 (`reference/base-2.1.4.4/`) |
|---|---|---|
| DOBJ `000031` key `BTMS` (Battle Music) | empty | `_00E_Music_Combat_Regular 0773F1` |
| `_00E_CombatSoundtrackScript` | on 1027 NPCs; `OnCombatStateChanged` called `_00E_PlayerFunctions.StartCombatMusic(_00E_Music_Combat_Regular)` (source in `papyrus-source/enderal/`) | **no `.pex` in any `E - *.bsa`**, not in `ScriptsEnderal.zip`, and 2.1's `_00E_PlayerFunctions` has no combat-music code at all |
| `0773F1` tracks | 7 | 10 (the regular battle tracks, plus the "epic" `Prophet` and "exotic/desert" tracks gated on `GetCombatTargetHasKeyword ActorEpicMusic 0493DA` and similar conditions) |

So in 2.1 the engine pushes `0773F1` onto the music stack whenever the player enters combat **[verified from records]**.
In 2.1, `0773F1` is referenced only by the DOBJ and by `_00E_MUS_AllCombatSoundtracks 0373CA`. That FormList is the
one `_00E_SoundControl.RemoveCombatSoundtracks()` walks to `.Remove()` types. No 2.1 script `.Add()`s `0773F1`.

Nine list plugins still put `_00E_CombatSoundtrackScript` on their NPCs: Enderal SE - Bug Fixes, EGO, EPPI, UCR EGO Patch,
mihailcrystalgolem, OrdoLegionisMuskets, Flintlock Overhaul, mihailudefryktereplacer and VicnReplacer. **No enabled mod ships
the `.pex`** (`tools/00` scan), so those attachments are dead. The Papyrus log line binding it to light-plugin forms
(`FE10FADE`/`FE10FCCC`) comes from these plugins, not from a music source.

Quest and boss-encounter music is separate. These MUSCs are added by quest scripts and are not touched:
`_00E_Music_Combat_*_NoCond`, `_00E_MQP02_CombatMusic`, `_00E_FS_NQR01_ArenaBattleMusic`, `_00E_Music_Special_*`, and
Castle Bleakstar's `_00E_Music_Combat_Epic_Phoenix`. They have priority 23–25 and keep winning.

## The override

The override is SureAI's 2.1 `0773F1` with three fields changed (`tools/01`, which asserts each edit):

- **Tracks** → only `_00E_SilentTrack 0963BB` (Type `SilentTrack`). This is SureAI's own silence shape: `_NONE 01BA72` and
  `_00E_SilenceTransitionLowPriority02 13C973` are a MUSC holding just that track.
- **Priority 65 → 100.** A lower number wins (`MUSSpecialDeath` = 1). Every exploration, dungeon and city type is 84–95, so the
  battle type now sits under the area's music on the stack instead of over it.
- **`AbruptTransition` and `DucksCurrentTrack` dropped**, so pushing it never cuts or ducks the playing track.

This approach was chosen over emptying DOBJ `BTMS`. A DOBJ override's merge semantics, and whether it accepts a null entry,
are engine behaviour this workspace has not verified. A plain MUSC field edit does not depend on them.

**Side effects:**

- Generic boss fights lose their music too. `ActorEpicMusic` targets used to get the `Prophet` theme from `0773F1`'s
  conditioned tracks.
- In a place with no music type at all, a fight is silent instead of scored.

## Load order

No enabled plugin overrides `0773F1`, and none overrides the DOBJ after `Update.esm` (`tools/00-scan-music.py`, Ultra,
2026-10-26). The plugin's position doesn't matter: it sits after `Zenderal - Pus Beetle Fixes.esp`. Re-run `tools/00` if a music
mod is added.

## Regenerating

```
python -I src/NoCombatMusic/tools/00-scan-music.py
python -I src/NoCombatMusic/tools/01-build-no-combat-music.py
```

## Status

Built with Spriggit 0.40.0 on 2026-10-26. Round trip is identical, ESL, HEDR 1.7. It is deployed as MO2 mod
`Zenderal - No Combat Music`, enabled in Ultra (profile backup in `E:/Zenderal-backups/ultra-profile-20261026-112625-no-combat-music`).
**Unverified in game.** To test, start a fight in the open world and in a dungeon. The exploration track should carry on, and
a quest fight such as the MQP02 or arena fights should still get its own music.
