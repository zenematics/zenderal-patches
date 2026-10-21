# QyraIslandEditorIdFix

- **Source:** `src/QyraIslandEditorIdFix/` (generated: `tools/01-build-qyra-island-fix.py`)
- **Ships:** `Zenderal - Qyra Island EditorID Fix.esp` (ESL, HEDR 1.7)
- **FormID block:** none (overrides only)
- **Status:** built, round-trip clean, 0 unresolved FormKeys; enabled in Ultra 2026-10-21 (plugin after `Ships of the First Vassals - EPPI IPL Addon.esp`, the last overrider of `00A6A0`). DynDOLOD not yet re-run.

## Why

DynDOLOD stopped on 2026-10-21 with *"Worldspace Editor ID changed from FSNQ01QyraIsland to
FS_NQ01_Qyra_Island. Ships of the First Vassals.esp FS_NQ01_Qyra_Island "Strange Place" [WRLD:0700A6A0]"*.

Enderal 2.1 renamed Forgotten Stories' worldspace `00A6A0` (Qyra's island, "Strange Place") from
`FS_NQ01_Qyra_Island` (2.0) to `FSNQ01QyraIsland`. A three-way header diff shows the EditorID is SureAI's only
real change; the rest is string localisation. `Ships of the First Vassals.esp`, built on 2.0 and the worldspace's
only overrider, carries a full copy of the 2.0 header (it places refs inside), so it puts the old name back.
Its other differences from FS 2.0 are an English-only Name and `SubCellsUnknown`, so it changes nothing here
on purpose. DynDOLOD refuses a changed worldspace EditorID because LOD files are named by EditorID, and 2.1's
shipped LOD uses the new name.

A scan of every WRLD override in the `Ultra` load order found no other worldspace with a changed EditorID.

## The fix

Ships' header copied verbatim, with `EditorID: FSNQ01QyraIsland`. Header only: the worldspace's cells and refs
are untouched. The masters are Skyrim, Update, FS and `Ships of the First Vassals.esp` (to force load-after).
Load it anywhere after Ships and its EPPI addon.
