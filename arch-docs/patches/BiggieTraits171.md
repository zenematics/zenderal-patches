# BiggieTraits171

- **Source:** `src/BiggieTraits171/tools/01-build-biggie-171.py` (generator only; its output is third-party content
  and is never committed)
- **Ships:** nothing. It builds a same-name `Biggie Traits.esp` at HEDR 1.71 into the MO2 mod
  *Biggie Traits - HEDR 1.71 (Zenderal)*.
- **Status:** built and installed 2026-10-23, on the curator's request. Unverified in game and in DynDOLOD.

## Why

DynDOLOD Alpha-208 stopped on *"Record [STAT:00000064] in file Skyrim.esm is being overridden by record
[KYWD:00000064] in file Biggie Traits.esp. Biggie Traits.esp is of version 1.7 which does not support form IDs <
0x800."* The Enderal conversion of Biggie Traits is a HEDR 1.70 light plugin whose 148 records sit below object ID
`0x800`. xEdit reads every sub-`0x800` ID in a pre-1.71 plugin as a Skyrim.esm form, so 47 of them collide with
base Enderal records of another type (`Traits_SelectionSpell 000004` → `PrisonMarker`, `Traits_AbilityList 000002` →
`TravelMarker`, …).

**In game they were never broken.** `player.addspell FE115004` gave the player Biggie's Select Traits spell under
Biggie's own index. The trait menu also offered Zenderal - Traits' traits, which only that plugin's override of
`000002` carries. So this fix only makes the header say what the records already are. 1.71 is the form version that
lets a light plugin own IDs below `0x800`.

## The fix

- `Biggie Traits.esp`, same filename, is the original **byte for byte except the HEDR version float** (file offset
  30, 1.70 → 1.71; 3 bytes change). The generator asserts the source is 1.70 and light-flagged, and that nothing
  outside those 4 bytes differs.
- It goes in a new mod folder placed **directly above** the original in `modlist.txt` (the line before it, so
  higher priority), so its `.esp` wins the file conflict. The original stays enabled for its scripts, interface
  files and meshes. `plugins.txt` is unchanged (same filename). This is the IronGolemClean pattern.
- **Every plugin that masters Biggie must be 1.71 too.** A pre-1.71 plugin's reference to a 1.71 light plugin's
  sub-`0x800` form resolves to Skyrim.esm (the FHR Parry Poise failure in CLAUDE.md). A live scan of the Ultra
  profile on 2026-10-23 found two:
  - `Zen Traits.esp` (Patch Collection) is already 1.71.
  - [`Zenderal - Traits.esp`](TraitsRework.md) was rebuilt at 1.71 the same day. Its only sub-`0x800`
    references are Skyrim.esm forms and the `000002` override.
- Not affected: Zen Traits' `_FLM.ini` names forms by EditorID. Biggie's only script `GetFormFromFile` on itself
  uses `0x84A` (above `0x800`), and no ini/json in the mods folder names `Biggie Traits.esp`.
- Backups (the old `Zenderal - Traits.esp` and `modlist.txt`): `E:/Zenderal-backups/2026-10-23-biggie-171/`.

## To verify

- DynDOLOD no longer stops on Biggie Traits.
- In game: the trait menu still lists Zenderal's traits, and `help "Select Traits" 4` still finds Biggie's spell.

## Regenerating

After any Biggie Traits update: `python src/BiggieTraits171/tools/01-build-biggie-171.py`. Re-scan for plugins that
master Biggie whenever one is added, since each of them must be 1.71 as well.
