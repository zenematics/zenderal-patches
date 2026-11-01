# CreatureRagdollFix

- **Source:** `src/CreatureRagdollFix/data/Pandora_Engine/mod/zragfix/` (Pandora-native patch, hand-written)
- **Ships:** MO2 mod `Zenderal - Creature Ragdoll Fix`. Needs a **Pandora run** with `zragfix` ticked.
- **Requires:** Pandora. The `0_master.xml` part completes MichelKI's *Death and Ragdoll Behavior Fix* (Nexus 171129,
  installed 2026-10-22); the creature part stands alone.
- **FormID block:** none (no plugin)
- **Status (final, 2026-10-22):** ships two edits. `0_master.xml`: the human `#0260` contact event → −1.
  `draugrbehavior.xml`: both get-up pose matchers start on `GetUpBegin`, which fixed skeletons getting up in a rigid
  A-pose (**verified in game**; built graph checked after the 22:16 Pandora run). The first creature version below
  (contact event + `TurnOnMatchingRagdoll` on draugr and spriggan) did **not** fix the mid-air freeze and was reverted.
  That freeze is [`AirborneGetUpFix`](AirborneGetUpFix.md); the rigid skeleton ragdoll is
  [`SkeletonRagdollFix`](SkeletonRagdollFix.md). Sections below are the history, in order.
- **Gotcha:** the first Pandora run that patches a graph not already in `Pandora Output - Zenderal` lands it in MO2's
  `overwrite` (`Meshes/Actors/spriggan/Behaviors/SprigganBehavior.hkx` did). It was moved into the output mod; later
  runs update it in place.

## The bug

An enemy ragdolled into the air (Seismic Stomp, but any knockdown) and **hit while airborne** went rigid and
never fell. Seen on skeletons and Wood Elementals (spriggans).

## Cause **[verified from the graphs]**

Every ragdoll-capable Skyrim behaviour graph has a `BSRagdollContactListenerModifier` named `CollisionListener` in its
ragdoll modifier list. Its `contactEvent` is **`Ragdoll`**, and the get-up and reanimate `hkbPoseMatchingGenerator`s
**start matching on `Ragdoll`**. So any contact with a live ragdoll, a weapon hit included, refires `Ragdoll` and
starts the get-up pose matcher. That drives the ragdoll towards an animation pose: rigid, held in the air.
MichelKI's mod fixes this for the human graph (`0_master`); creatures have the same wiring:

| Pandora template node | draugr (skeletons, `DraugrSkeletonProject` → `draugrbehavior`) | spriggan |
|---|---|---|
| `CollisionListener`, contact = `Ragdoll` | `#0156` (Ragdoll 245) | `#0133` (Ragdoll 62) |
| Get Up Pose Matcher, start = `Ragdoll` | `#0113` | `#0108` |
| Reanimate Pose Matcher, start = `Ragdoll` | `#0122` | `#0117` |
| `TurnOnMatchingRagdoll`, activate `GetUpBegin`, deactivate none | `#0143` (GetUpBegin 248) | `#0100` (GetUpBegin 67) |

Found by converting Pandora's templates (`hkxconv --meta`) and the live built graphs (`src/EnderalPairedAnims/tools/hkxconv`).

## Fix

The same three edits MichelKI's Nemesis patch makes to `0_master` (`#0260`, `#0217`/`#0226`, `#0243`), applied to
`draugrbehavior.xml` and `sprigganbehavior.xml`. The contact event becomes `-1`, both pose matchers start on
`GetUpBegin`, and `TurnOnMatchingRagdoll` deactivates on `Ragdoll` (numeric IDs from each template, see the table).

**Pandora-native `<replace>` syntax [verified 2026-10-22, Pandora source + two runs]:** an `<edit path>` must be
`#node/param[/...]` — a bare `#0113` fails with *"Invalid format (missing '/')"* in `Engine.log`. The child element
**replaces the element the path names**: `#0156/contactEvent/Element0` with a bare `<hkparam name="id">` built contact
event **0** (`moveStart` on draugr, `FootLeft` on humans), so it takes the whole `<hkobject>`; a scalar takes
`#0113/startMatchingEventId` + `<hkparam name="startMatchingEventId">`. There is no `$eventID[...]$` macro in the native
format — use the template's numeric index (Pandora appends new events, so template indices hold). Also: a patch only
loads if the MO2 mod is **enabled** — ticking it in Pandora alone does nothing. The human mod's
death-animation variables and triggers (`DeathAnimActive`, `IsRagdoll`, `IsRagdollGetUp`, the `DeathAnimA` trigger)
are not copied: they drive its death-animation system, which these creature graphs do not have.

`0_master.xml` carries the one human edit the mod page asks Pandora users to add by hand to Pandora's own
`pandora/patches/0_master.xml` (`#0260` contact event). Shipping it here leaves Pandora's file untouched. Its value
is `-1`, as in the Nemesis patch (the page's snippet says `0`).

## In-game result (2026-10-22): did NOT fix creatures, broke get-up

- Some enemies now fell, but got up and then **stood still** (or walked backwards on the spot), even without a mid-air hit.
- **Skeletons still froze mid-air**, alive, held rigid in what looks like the reference (A-)pose (Lost One on
  `mihailancientskeletonrace` → `DraugrSkeletonProject.hkx`, so our patched graph was loaded).
- **Wrong premise for creatures:** in `draugrbehavior` and `sprigganbehavior` the `CollisionListener` lives only in
  `AnimateToRagdoll` (entered on `DeathAnimation`), not in `FullyRagdoll`. A live knocked-down creature never runs it.
  Their death clips fire `Ragdoll` themselves (draugr `Special_DeathBackward` at 0.746 s, spriggan `Death` at
  0.867 s). The human analysis does not transfer.
- Creature get-up flow: `FullyRagdoll` (enter: `RemoveCharacterControllerFromWorld`) → engine `GetUpBegin` →
  `TurnOnMatchingRagdoll` (powered matching + 0.5 s timer → `GetUpStart`) → `GetUpFromRagdoll` → the clip's end
  triggers `GetUpEnd` + `AddCharacterControllerToWorld`. The only thing that gives the controller back is that clip-end
  trigger.
- Next step: capture the real graph event sequence on a frozen skeleton (runtime log), not more graph theory.
- **Reverted 2026-10-22:** `draugrbehavior.xml` and `sprigganbehavior.xml` removed from `zragfix`; only the human
  `0_master.xml` edit ships. The patched spriggan graph was deleted from `Pandora Output - Zenderal` (nothing else
  patches it; backup in `E:/Zenderal-backups/2026-10-22-zragfix-creature-revert`); the draugr graph is rebuilt
  unpatched by the next Pandora run. Runtime logger: [`ZenRagdollTrace.md`](ZenRagdollTrace.md).

## Cause found with ZenRagdollTrace (2026-10-22, 21:17 session) [verified from the runtime log]

Wood Elemental `0011C3B9` and Lost One `0011C3DF` (race `Draugr`), both thrown by Seismic Stomp:

| Real time (ms) | Wood Elemental | Lost One |
|---|---|---|
| `IN Ragdoll`, knock 2→1 (explode) | 78827, z 1276 | 187509, z 1590 |
| apex | ~80600, z 1590 | ~188300, z 1811 |
| **Precision hit on the flying ragdoll** | 82519 | 190012 |
| **`IN GetUpBegin` ~55 ms later, knock → 5 (queued), still airborne** | 82572, z 1509 | 190067, z 1754 |
| `OUT GetUpStart` (graph's 0.5 s timer), knock → 6, `ragdoll=false`, `animDriven=true` | 84450, z 1424 | 192052, z 1659 |
| afterwards | z frozen at 1332 for 15 s+, knock stays 6, **no `GetUpEnd` / `AddCharacterControllerToWorld` ever** | killed |

- **A hit on an airborne ragdoll makes the engine start the get-up mid-air.** Once `GetUpStart` turns the body
  animation-driven, it has no ragdoll and no character controller: no gravity, so it hangs rigid. The get-up never
  completes, so the knock state stays `kGetUp`: alive, stuck, unable to move.
- The slow arcs in real time are Seismic Stomp's SlowTime (world at 30% for 10 s), not damping. SlowTime stretches the
  airborne window in which a hit can land, which is why it shows up after Seismic Stomp.
- Fix direction: hold `GetUpBegin` while the ragdoll is still moving and send it once the body has settled.

## Draugr get-up pose matchers re-added (2026-10-22, late)

With the airborne freeze handled by [`AirborneGetUpFix`](AirborneGetUpFix.md), skeletons (Lost Ones on
`mihailancientskeletonrace`) still got up with **no visible get-up clip: a rigid A-pose rotated 90° upright**, even
from a plain ground knockdown. Not a missing clip: `Draugr_Skeleton.hkx` lists `GetUpFaceDown`/`GetUpFaceUp`, the
`.hkx` files are in `Skyrim - Animations.bsa`, no mod overrides them, and Pandora's `animationdatasinglefile.txt`
block for `DraugrSkeletonProject` is identical to vanilla (including both clips and their `GetUpEnd` /
`AddCharacterControllerToWorld` triggers).

The pose matchers `#0113`/`#0122` start matching on `Ragdoll`, the event that *enters* `FullyRagdoll`, so the matchers
(active only inside it) never receive it. With no match, they output the reference pose while `hkbGetUpModifier`
rotates the body upright. Only those two edits are back (`startMatchingEventId` → 248 `GetUpBegin`, MichelKI's human
change). The earlier "stands still after getting up" was a stagger interrupting the get-up, now refused by
AirborneGetUpFix 1.1.0, not this edit. Spriggans are left alone (their get-up looked right in game). Needs a Pandora run.

Verified after the 22:16 Pandora run: both draugr matchers start on `GetUpBegin`. The user confirmed the skeleton
get-up works.

## Open: skeletons ragdoll as a rigid A-pose (user report, 2026-10-22)

The user says skeleton models "don't have an actual ragdoll, they just A-pose". Ruled out so far:
- **Rig:** `Character Assets\SkeletonS.HKX` has a full ragdoll (`hkaRagdollInstance`, 20 rigid bodies, 36 constraints,
  19-bone ragdoll skeleton mapped onto the 84-bone animation skeleton), comparable to the draugr rig's 19/34.
- **Skeleton NIF:** `skeletons.nif` wins from XP32 Maximum Skeleton (no other mod ships it). Its physics are identical to
  vanilla's (`Skyrim - Meshes0.bsa`): 19 `bhkRigidBody`, 14 hinge + 4 ragdoll constraints, 18 capsules.
- **Mesh bones:** Mihail's `mihailancientskeleton0.nif` is skinned to the rig's bone names, except the left foot
  (`NPC L Foot [Lft ]` vs the rig's `[LLft ]`), which can only affect that foot.
- **Graph:** `FullyRagdoll` runs `PoweredRagdoll No Matching` with `maxForce 0` in draugr, spriggan and human graphs
  alike (matching motors at 200 only after `GetUpBegin`). Precision's `PreDriveToPose` returns early when every powered
  control has zero force.
**Cause found:** the user sees the A-pose in flight before any hit. The skeleton ragdoll rig welds every limb joint.
`meshes\actors\draugr\character assets\skeletons.hkx` (Enderal's copy in `E - Meshes.bsa`, which the game loads, and
Skyrim's in `Skyrim - Animations.bsa` alike):

| Joint | Skeleton (`skeletons.hkx`) | Draugr (`skeleton.hkx`) |
|---|---|---|
| Calf | hinge −1..+1° | hinge −110..0° |
| Foot | hinge −1..+1° | hinge −11..+45° |
| Forearm | hinge −1..+1° | hinge 0..+90° |
| Hand | hinge −1..+1° | hinge −25..+20° |
| Thigh | **hinge** −1..+1° | ragdoll joint, cone 34–45°, planes −59..+44° |
| Upper arm | **hinge** −1..+1° | ragdoll joint, cone 48–56°, planes −5..+90° |
| Head / jaw | hinge −1..+1° | ragdoll joint, cone 21° |
| Neck | ragdoll joint, cone 1°, twist ±1° | cone 5°, twist ±5° |
| Spine ×3 | cone 5°, planes ±30° | same |

So skeletons are rigid by Bethesda's design, not because of a mod. **Fixed by [`SkeletonRagdollFix`](SkeletonRagdollFix.md).** Correction: the winning copy is XPMSE's loose `skeletons.hkx`, not the BSA's; its joints are locked the same way, and the hinge axes run along the bones, so wider limits alone would not help. A fix would ship a loose `skeletons.hkx` rebuilt
from Enderal's copy with the limb limits opened up (draugr ranges for the hinges; thighs, upper arms and head would
also need the hinge axis or constraint type reconsidered), in a mod above everything that ships the BSA copy.

## Ruled out on the way (2026-10-22)

- **Precision** (`RemoveRagdollFromWorld` keyframing): patched, no effect, rolled back. See [`PrecisionFork.md`](PrecisionFork.md).
- **Dismembering Framework's stump-cap equip:** a test without skeleton stump caps was deployed, then undone
  once the graph cause was found. See [`LostOnesDismembering.md`](LostOnesDismembering.md).

## Extending

Other creatures that freeze the same way: convert their Pandora template, find the four nodes by name (as above), and
add a `<graph>.xml` with the same edits.
