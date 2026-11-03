# BearRagdollFix

- **Source:** `src/BearRagdollFix/tools/01-build-rig.py` (generator; reuses SkeletonRagdollFix's XML reader).
- **Ships:** a generated loose `meshes/actors/bear/character assets/skeleton.hkx` (not committed), deployed as the MO2
  mod `Zenderal - Bear Ragdoll Fix`. It must win over XP32 Maximum Skeleton Special Extended, which ships its own loose
  copy. In the Ultra profile it sits at line 120, next to Zenderal - Skeleton Ragdoll Fix, far above XPMSE.
- **Status:** built 2026-11-01. Unverified in game.
- **Rerun** whenever XPMSE (or anything else shipping that file) updates. The output is a patch of the winning copy, and
  the tool refuses a rig that does not have the defect.

## The bug

Curator, 2026-11-01, testing Seismic Stomp on bears: ragdolled bears "flop and distort", like a hit impulse breaking
them. With Precision's hitstop on the target turned off, the distortion stayed, so it is the ragdoll itself.

## Cause [verified from the rig]

The bear rig (Bethesda's, in `Skyrim - Animations.bsa`, and XPMSE's copy, with the same joint data) has one bad joint:
the **right hind knee**, `Ragdoll_NPC RLeg02` (a limited hinge from RLeg02 to RLeg01).
- At bind pose it measures **−70°**, while its limits are **0..65°**. Its frame B is rotated 70° about the hinge axis
  against frame A.
- As soon as the bear ragdolls, the solver forces the knee more than 70° back into range, and the hind leg snaps and
  twists.
- Every other joint measures 0° at bind, including the left knee (−60..0°).

Both knees' hinge axes run along world +X (left (1, 0.07, 0), right (1, −0.07, 0)), so they bend the same way. The
right ankle and both elbows already use the same limits on both sides.

The rest of the rig is loose but not broken: zero friction everywhere, front-leg shoulder cones of 65°/76°, and elbows
that swing 125–130°. That was left as is.

## Fix

The winning file is patched in place, by SkeletonRagdollFix's method (an XML round trip loses physics precision).
- The right knee's frame B is rewritten so its world axes equal frame A's: bind = 0°.
- Its limits become the left knee's −60..0°, copied bit for bit from the file.
- Both copies of the joint are patched (physics system and ragdoll instance): 68 bytes in all.
- Each copy is identified through the packfile's fixups (the bear file needed a bounds-checked copy of
  `packfile_links`), and frame B's old rotation and translation are checked against the XML.
- After the patch, every joint in the file measures inside its limits at bind.

```
hkxconv "<XPMSE>/meshes/actors/bear/character assets/skeleton.hkx" skeleton.xml
python src/BearRagdollFix/tools/01-build-rig.py <that skeleton.hkx> skeleton.xml <out skeleton.hkx>
```

Applies to every race on the bear rig (`Actors\Bear\`): black, brown, snow and cave bears, including Bears of the North.
