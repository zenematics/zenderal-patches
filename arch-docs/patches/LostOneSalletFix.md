# LostOneSalletFix

- **Source:** `src/LostOneSalletFix/`
- **Ships:** *(no plugin — one generated mesh, MO2 mod `Zenderal - Lost One Sallet Fix`)*
- **FormID block:** _(none)_

## What it does

**Plated Lost Ones no longer show a purple helmet and strap** (reported on Discord 2026-10-19, a
"Lost One" corpse with a purple head and forearm). Lost Ones Revised (Enderal SE Nexus 243, v2.0)
dresses its plated variant, `Meshes\Mihail Monsters and Animals\Human\Ancient Skeleton\mihailancientskeleton1.nif`,
in a Witcher 2 sallet and a strap. Both shapes are textured
`textures\armor\Plated Lost One\lavalette_guard__c1.dds` (+ `_n`, env mask `temeria_knight__b1_m.dds`),
and **the mod's archive never shipped that folder** **[verified 2026-10-19]**: the `.rar` holds only the
`.esp`, meshes and `textures\weapons\`, and no enabled mod or BSA in the Ultra profile provides the three
files. The mesh's other textures all resolve (the skeleton's from SMIM/Enderal, the five
`Ancient Skeleton\armor.dds` pieces from Mihail's Ancient Skeletons). The Nexus posts have no fix.

`src/LostOneSalletFix/tools/01-hide-plated-sallet.py` copies Lost Ones Revised's mesh and sets the
child refs to the `sallet` and `strap` shapes to `-1`. It asserts that each is detached exactly once.
The output differs from the source by 8 bytes, and the orphaned blocks stay in the file unreferenced.
The plated Lost One now shows a bare skull and keeps the rest of its armor. The mesh is not committed.
The mod must have **higher MO2 priority than Lost Ones Revised** (and Mihail's Ancient Skeletons, which
ships the same path), and CRDW must be rebuilt after generating. Generated and enabled in Ultra
2026-10-19. **Unverified in game.**

## The alternative not taken

The intended textures exist: `textures/armor/heavyknight/lavalette_guard__c1.dds`, `lavalette_guard__c1_n.dds`
and `temeria_knight__b1_m.dds` are loose files in Afro's Witcher 2 Armor Collection 1.3 (Skyrim LE
Nexus 78385, main file `Afro's WItcher 2 Armor Collection 1.3-78385-1-3.zip`, 234 MB), found through
Nexus's file-contents preview. Installing those three files renamed into
`textures\armor\Plated Lost One\` would show the helmet as the author intended. Wabbajack matches files
by hash, so the rename survives a compile. This was skipped to avoid a 234 MB download for one helmet.
If that route is taken later, retire this mod.
