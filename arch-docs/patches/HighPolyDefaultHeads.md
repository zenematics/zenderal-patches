# HighPolyDefaultHeads

- **Source:** `src/HighPolyDefaultHeads/` (generated: `tools/01-build-high-poly-default-heads.py`, from
  `reference/mods/HighPolyHead` = Spriggit serialize of `High Poly Head.esm`)
- **Ships:** `Zenderal - High Poly Default Heads.esp` (ESL, HEDR 1.7, masters `Skyrim.esm` only)
- **FormID block:** none (18 overrides)

## Why

Reported 2026-10-24 with screenshots: on every default preset, pale hard-edged patches on the chin and beside the
mouth; "lots of beards also don't sit right"; seen in the alpha too. RaceMenu's sculpt wireframe showed the
**head mesh poking through the facial-hair mesh** (tan head through the magenta stubble shell on the chin).
**[verified 2026-10-25]**

- All 17 of Enderal's male chargen presets (`_00E_CharacterTemplate_*`) use **vanilla heads**
  (`MaleHeadNord/Breton/HighElf/Redguard` → `Actors\Character\Character Assets\MaleHead.nif`).
- The list's beard sets are fitted to **High Poly Head**: HPH's own 45 facial hairs, HPH SV Beards (1764),
  The Art of Beard for HPH, Beards of Power (HPH version, whose 28 vanilla-path `_1bit` beards are HPH-fitted).
  On a vanilla head they sit wrong and the head shows through their stubble shells.
- Ruled out on the way: head/mouth mesh vs .tri vertex counts (vanilla 898, HPH 3598, mouth 141 — all match,
  EFA/EFM/Enderal/HPH copies); Tempered Skins diffuse/normal/specular and every male tint mask (no hard edges);
  plugin overrides of the presets' head/beard parts (none); Face Discoloration Fix 1.0.4 on 1.7.104 (its 7
  NOP/jump patch sites still land on the intended instructions); disabling Expressive Facegen Morphs (user test:
  still clipped).

## What it does

High Poly Head's `00KLH_<name>` head part is Enderal's `<name>` record with only the mesh and its three .tri
paths under `KL\High Poly Head\`; texture set, valid races, flags and type are identical. The generator copies
each of the 18 humanoid heads (male + female Nord, Breton, Imperial, Redguard, HighElf, WoodElf, DarkElf, Orc,
Elder) verbatim and swaps exactly those four paths, asserting the rest matches. The one difference allowed:
Enderal's `FemaleHeadNord` has no texture set (HPH's names `SkinHeadFemaleNord 03B522`), and keeps none. The
display name is written in English only (a non-localized plugin can't hold the base file's other languages).
Beast, Dremora, Astrid, Afflicted, child, mannequin and the Ryneus/Sullevan quest heads are untouched.

Effect: every chargen preset, every existing character on those heads, and any NPC without baked facegen uses the
high-poly head. NPCs with facegen (`FaceGeom/*.nif`) keep their baked heads. Nothing else in the list defines
these 18 records (scan 2026-10-25), so load position doesn't matter; it sits after The Art of Beard for HPH.

## Status

Built and deployed 2026-10-25 (MO2 mod `Zenderal - High Poly Default Heads`). Round-trip identical.
**DISABLED 2026-10-25 (plugin hidden as `.esp.mohidden`): it hard-freezes the game. Do not re-enable as built.** With it hidden, the MQP03 temple scene plays through
without freezing (user replay, 2026-10-25) **[verified]**.
Vanilla-fitted beards (Enderal's `HumanBeard*`) would be the ones that sit slightly off; pick HPH beards.

## Postmortem: the prologue temple freeze (2026-10-25)

"NPCs with facegen keep their baked heads" above was only half true. They keep the baked **mesh**, but the
engine still takes the **.tri morphs from the head part record**, so every facegen NPC on these 18 heads got
HPH's 3598-vertex morphs on an 898-vertex face mesh.

Symptom: a consistent hard freeze in the MQP03 temple vision, just after "The corpses and the light... they are gone."
Evidence, from a full hang dump (`rundll32 comsvcs.dll, MiniDump`) **[verified]**:

- The main thread spins forever in BSSpinLock acquire (ID 13663), called from ID 70950 (lock `this+0x168`,
  return `this+0x160`: BSDynamicTriShape's dynamic-data lock) inside the BSBatchRenderer draw.
- The object is a `BSDynamicTriShape` named `MaleHeadImperial` under `BSFaceGenNiNodeSkinned`. Its owner is
  ref `0007AF9E`, base `0007AF9D`: the StartsDead corpse in `MQP03TempleBeacon`, which ragdolls at that moment.
  The shape's vertex count is 898 (u16 at +0x15A; dynamic data size 0x3820 = 898 × 16).
- The lock (owner u32 at +0x168, count at +0x16C) is held by game worker thread 42736 with count **2**. That
  thread is back in its idle job wait (ID 69344), so the lock leaked.
- `MaleHead.tri` / `MaleHeadRaces.tri` from HPH: FRTRI003, 3598 vertices.

How the mismatch turns into a leaked lock is not proven. The morph update runs as the face-morph task (ID 26999
→ 26988), and Better Facial Animations 4.3.2 hooks that call (`BetterFacialAnimations.dll+0x18100`), so the
code that leaked could be either. BFA's log shows no playback on that head. Removing this plugin removes the
mismatch either way.

Replaced by [`HighPolyPlayerHead`](HighPolyPlayerHead.md), an SKSE plugin that swaps only the player's face part.

Lesson: an HDPT's .tri paths are part of every facegen NPC's head, so swapping vanilla head parts for a
different topology needs regenerated facegen for every NPC on them. To fix the chargen beard clipping, give the
player an HPH head (e.g. the presets' own head parts, or HPH's `00KLH_*` records in RaceMenu) instead.
