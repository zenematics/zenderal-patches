# ArkMyradPlatformFix

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **Source:** `src/ArkMyradPlatformFix/`
- **Ships:** `Zenderal - Ark Myrad Platform Fix.esp`
- **FormID block:** none (overrides only)

## What it does

Fixes the Ark Myrad boarding sequence dropping the player off the platform edge before the mount animation completes. Single override: reference `02F0B5:Enderal - Forgotten Stories.esm` (a plain XMarker), repositioned toward the platform's east edge so the Myrad's westward-facing neck (rotation `270°` exactly) has room before running off the platform's short axis. Verified against the cell's real navmesh (point-in-triangle, not just vertex proximity), and confirmed by matching an in-game `getangle z` reading of `270.00°` to this record's exact vanilla rotation (`4.7124` rad). Master: `Skyrim.esm` + `Enderal - Forgotten Stories.esm` (the marker's defining master). See the FS-override postmortem below — read it before touching any Myrad-adjacent record again.

## Postmortem: the winning override lived in FS

> **POSTMORTEM, 2026-08-31: an entire debugging session was spent editing the wrong record because
> the winning override lived in `Enderal - Forgotten Stories.esm`, not the `Skyrim.esm` layer this
> repo's own reference docs pointed at first.** The Ark Myrad NPC reference (`Ark_MyradRef`,
> `09C522:Skyrim.esm`) has TWO separate FormKey definitions in `reference/base/`: one in
> `reference/base/Skyrim/Worldspaces/...` (the base layer) and a completely different one in
> `reference/base/EnderalFS/Worldspaces/...` (FS's override) — different `LinkedReferences`,
> different `Placement`. Every edit this session made to the base-layer version's fields (Position,
> Rotation — six separate attempts, three different records) produced **zero** in-game effect,
> because the live game was reading FS's override the whole time, which links to a *different*
> reference entirely (`02F0B5:Enderal - Forgotten Stories.esm`, reached via a keyword,
> `_00E_FS_MyradTakeOffMarker` `02F0B6`, that only exists on the FS-layer copy of the record).
>
> **How this was finally caught:** the in-game console's own reference-info panel names the winning
> plugin directly — `prid <formid>` in-game shows `Ref last changed by: <plugin>` — and it said
> `Enderal - Forgotten Stories.esm`, not `Skyrim.esm`. That single field ended a session's worth of
> guessing. **Read that field before trusting any FormKey lookup against `reference/base/Skyrim/` for
> a record FS is known to touch** (recall: 28.7% of FS's own records override base Enderal — see
> "Master order" above) — grep `reference/base/EnderalFS/` for the same FormKey FIRST, or at minimum
> in parallel, never only the base layer, whenever a record's edits aren't taking visible effect and
> the record belongs to an NPC, quest alias, or anything else FS is likely to have touched.
>
> **Two further mechanism notes, in case a similar animation-adjacent bug shows up elsewhere:**
> 1. An actor's *own* placed Position/Rotation can be entirely irrelevant to where it actually
>    appears if a linked marker (found via `GetLinkedRef(keyword)`) drives the behavior instead —
>    console `getpos`/`getangle` on the actor itself will keep reporting the marker's values
>    regardless of what the actor's own record says, which looks exactly like "my edit did nothing"
>    but is actually "I edited the wrong record." Don't conclude a lever is broken until you've
>    confirmed via console which record's values are actually live.
> 2. A creature's `ObjectBounds` (on its base NPC/creature record) can legitimately exceed a small
>    platform's own footprint — the Myrad's ~5m nose-to-tail half-length is longer than this
>    platform's forward clearance in every direction. The fix isn't finding a position where the
>    *whole body* fits (impossible here), it's biasing the pivot so the *mount point* (near the
>    front, not the full length) lands on solid ground and letting the tail hang off the back, where
>    nothing needs footing.
