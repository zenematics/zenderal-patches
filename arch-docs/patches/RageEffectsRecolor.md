# RageEffectsRecolor: Rage's effects in red and orange

**Ships:** generated meshes and textures, not committed. MO2 mod *Zenderal - Rage Effects Recolor*, built from the
user's install by `src/RageEffectsRecolor/tools/01-build-rage-recolor.py`. Curator's taste (2026-10-27).

Prophecy's Rage casts A Dark Warrior's Tale's class actions ([`Prophecy`](Prophecy.md), Rage). Their meshes,
`KittyClass_DarkWarrior\*.nif` in the pack's BSA (9 of them), take their colour from greyscale textures looked up in
shared gradient palettes, `…\effects\gradients\grad*.dds`. The violet, blue and purple ones (summon burst, reanimate,
purple enchantment, shadow shield, telekinesis) made the actions pink and purple. The meshes' effect-shader base colours
are white, and the pack's two effect shaders are grey and dark red, so the palettes are all the colour there is.

The palettes are shared with vanilla spells, so they are not recoloured in place:

- **The meshes:** every `\gradients\` path is repointed to `\gradientz\`, the same length. The NIF stores paths as
  length-prefixed strings, so the file keeps its size and differs only in those letters; the tool checks this.
- **The palettes:** each one is copied from the winning copy (a loose file by MO2 priority, then Enderal's and Skyrim's
  texture BSAs) to the same path under `\gradientz\`, recoloured. Every coloured pixel's hue goes from red (dark) to (curator, 2026-10-27: 0–32° was too light, now 0–20°)
  orange (bright); saturation, brightness and alpha are kept.
  - 23 palettes. In this list all come from Glorious Gradients.
  - Vanilla's are in `Skyrim - Textures5`; Dawnguard's shadow-shield palettes are under `textures\dlc01\`.

**Second pass (curator: clouds still black/pink/purple):** 11 effect shaders carry a cool base colour, (0.75, 0.25,
1.0). Several have no palette at all, so that tint is their whole colour. The tool now warms those in place (fixed-size
floats, same red-to-orange rule). Surveyed and clean: particle emitters' starting colours, colour-controller keys, and
the cloud/smoke textures themselves (greyscale). One small bluish flash texture (`fxbrightfash01`) is left.

**Clouds removed (curator, same day):** every shape or particle system whose effect shader uses a cloud, smoke,
steam, vapour or swirl texture (`CLOUD_TEXTURES`: `cloud2`, `cloudtile`, `fxcloudroundtilenew`, `fxsmoke*`,
`fxsteamthickanim`, `darkswirls*`, `vaportile02`) is detached from its parent node: child ref → −1, as
[`IchorGooNoGlow`](IchorGooNoGlow.md) does. 27 across 8 meshes. Each mesh keeps its size and still parses; the orphaned
blocks stay in the file unreferenced. The beams, slashes, pillars, sparks and embers are kept.

**The side-attack cloud (curator's screenshot):** not a mesh. It is the pack's hit shader `_CDW_DarknessDamageFXS 00151E`,
played on targets by Shadow Carve, Shadowbringer, Bloodletter and Soulrender. Its particles (`SmokeInky01` through the vanilla
palette `GradDisguiseShader02`, scale up to 96, birth ratio 100) are the magenta cloud. `tools/02` writes
`Zenderal - Rage Effects.esp` (ESL, masters `KittyClass_DarkWarrior.esp`; YAML in `RageEffectsRecolorESP`): the record
verbatim with `ParticleFullBirthRatio` 0 (the only changed line). The membrane glow stays. **Load it after
`KittyClass_DarkWarrior.esp`.**

**Dark Deluge's beam restored:** keeping `vaportile02` shapes alone did not bring it back (curator), so both Dark Deluge
meshes (`KEEP_SHAPES`: `DarkWarriorPierceHazard`, `…CastProj`) now keep every shape; only their colours change.

**The absorb screen tint:** Bloodletter/Soulrender's `magicAbsorbFXScript` plays `_CDW_AbsorbImod 000890` (its `TrapImod`),
with magenta (`BF007F`) and purple (`8000FF`) tint/fade keys. `tools/02` adds it to `Zenderal - Rage Effects.esp` with
every cool `#AARRGGBB` key warmed (6 keys; alpha and times kept).

**The drain's absorb visuals emptied (curator: the side attack's purple cloud survived the hit-shader fix, plugin active):**
Bloodletter/Soulrender's `magicAbsorbFXScript` plays the pack's VisualEffects `001523`/`001525` (red) and `00151D`/
`001522` (blue). The cast ones carry a vanilla absorb mesh plus a vanilla particle shader (`AbsorbHealthFXS` /
`AbsorbBlueFXS`: `MagicCaustic01` particles); the target ones carry a mesh only. Vanilla Absorb spells share those, so
`tools/02` overrides the pack's four VFX records with their `EffectArt`/`Shader` removed: the drain plays no absorb cloud.

**The side attack's purple cloud, found:** after the hit shader and absorb visuals were ruled out in game (plugin active, log
showing Bloodletter + Soulrender fired), it was in both side-attack meshes (`DarkWarriorSlashProj`, `DarkWarriorFlashProj`):
particle system `Vapor01`, textured `magicicewisps.dds`. That texture is coloured by itself (Arctic Frost Effects Redux,
bluish-violet), and its base colour is white, so no palette or tint warms it. Its dark `Darkness01` glow too. The cloud
detach now also matches shape names (`CLOUD_NAMES`: vapor, darkness, smoke, cloud, mist, fog prefixes); Shadowbringer's
pillar `ShadowVapor` is not a prefix match and stays.

**Then the restores' shaders:** the cloud was still reported after `Vapor01` was gone, so `tools/02` also overrides the
"fake absorb" restore effects `001587` (Health) and `001588` (Mana) without their `HitShader`. Those shaders are vanilla
`AbsorbHealthFXS` and `AbsorbBlueFXS` (blue `MagicCaustic01` particles on the player). The restore itself is unchanged.
The plugin now holds 8 records.

**Then the membrane (curator's screenshot: a magenta sheet over a corpse after a side power attack):** with
`00151E`'s particles already off, its membrane remained: `ShockTile01` through Dawnguard's `GradVampireTrans01` palette
(Glorious Gradients colours it). `tools/02` now overrides all 11 pack effects that apply `00151E` (Shadowbringer, Shadow
Carve, Bloodletter, Soulrender, the spikes, and their aiming-fix twins) without `HitShader`. Damage and drain unchanged.

**The actual purple cloud: the particles' own tints (2026-10-27).** Making the class ability inert changed nothing. The
side power attack fires Bloodletter + Soulrender, whose projectiles `DarkWarriorSlashProj.nif`/`DarkWarriorFlashProj.nif`
tint their particles with `BSPSysSimpleColorModifier` (3 RGBA colours over a particle's life). Sparkle01 fades dark blue
(241 deg) -> red -> dark blue, which blends through magenta and violet; Sparkle01B goes blue -> purple. tools/01 now warms
those colours with the palette rule too (`particle_colours`); no cool tint is left in any of the 9 meshes.
Recoloured, the curator still wanted the cloud gone: Sparkle01 (64-unit wisp puffs, `fxmagicwisps01.dds`) is detached
from both side-attack projectiles by exact name (`CLOUD_SHAPES`); their small Sparkle01B sparks and BCut ripples stay.

**The real source: the pack's own class system, active on the character.** A clip (2026-10-27 20:28) showed the cloud on a
side power attack where ZenProphecyRage logged no hit and no action. The pack's class ability `_CDW_ClassMGEF 00080B`
("assumes the mantle of the Dark Warrior") was on the player. It applies class perk `000892`, whose `ApplyCombatHitSpell`
entries fire the pack's wrapper spells: `_CDW_ClassProgression` defaults to 1, the in-place Soulrender, and MCO reports
every power attack as standing. Its `_CDW_ClassAbMonitorScript` casts more on hits taken, and it carries its own hit shader
`00088A` and art `00089F`. `tools/02` overrides it inert (no script, perk, shader or art), so only Rage drives the actions.
The plugin holds 20 records.

**A boot crash right after the plugin was enabled (2026-10-27 19:17) was not the plugin.** It was in Community Shaders'
shader compiler (`ShaderCache::GetCompletedShader`, a grass shader, 24 s in), the same as a crash at 12:17 before
the plugin existed. The plugin has two records, which nothing reads at boot.

Loose files win over the pack's BSA, so the mod's place in the list does not matter. Rerun after Glorious Gradients or
the pack changes. Unverified in game.
