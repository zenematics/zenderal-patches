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

Built and deployed 2026-10-25 (MO2 mod `Zenderal - High Poly Default Heads`). Round-trip identical. Unverified in
game. Vanilla-fitted beards (Enderal's `HumanBeard*`) will now be the ones that sit slightly off; pick HPH beards.
