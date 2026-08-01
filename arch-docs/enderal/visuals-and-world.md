# Visuals and the world

Reference for the **modern visuals** pillar. Enderal's lighting is not Skyrim's with different
numbers — it is a wholly separate set of records, and this is the pillar where naive porting fails
most visibly.

## SureAI's own warning

From `enderal readme.txt`, shipped with the game **[verified]**:

> "since Enderal changes all light settings, no ENB preset made for Skyrim would produce adequate
> lighting in Enderal. Furthermore, ENB mods may deactivate fadeouts in cutscenes, leading to visual
> bugs."

Two separate claims, both actionable. The second is the one people forget: **cutscene fades are a
known ENB casualty**, and Enderal is full of scripted cutscenes. A broken fade reads to the player as
a hang, not as a visual bug.

## The scale of the replacement

**[verified]** counts:

| Record type | base Enderal | Forgotten Stories |
|---|---:|---:|
| Lights | **1195** | 122 |
| ImageSpaces | **339** | 28 |
| ImageSpaceAdapters | **328** | 29 |
| Weathers | **147** | 57 |
| Regions | **100** | 14 |
| LightingTemplates | **60** | 6 |
| VolumetricLightings | 0 | 42 |
| Climates | **4** | 0 |
| EffectShaders | — | 14 |
| TextureSets | — | 27 |

339 imagespaces and 147 weathers is a complete weather/lighting system. A Skyrim weather mod that
edits vanilla weather records edits records that **do not exist here**.

Note **VolumetricLightings are FS-only (42 records)** — base Enderal has none. If you are patching
volumetric lighting, you are patching Forgotten Stories content.

## Climates

Only four, and they are Enderal's **[verified]**:

| Climate | FormKey |
|---|---|
| `DefaultClimate` | `00015F:Skyrim.esm` |
| `SkyrimClimate` | `000812:Skyrim.esm` |
| `SternenstadtClimate` | `003ED6:Skyrim.esm` |
| `UnderwaterClimate` | `07284F:Skyrim.esm` |

`SkyrimClimate` retains the vanilla EditorID but sits inside Enderal's `Skyrim.esm` — assume it has
been retuned, do not assume it matches Bethesda's. *Sternenstadt* is Star City.

## Worldspaces

**23 worldspaces in base Enderal.** **[verified]** The main one is **`Vyn`** — there is no Tamriel.

```
Vyn                          <- the overworld
Akropolis                    CapitalCityCastleWorld       CapitalCityLowerCity
CapitalCityMarketArea        CapitalCityStrangerArea      CapitalCityUpperCity
CapitalCityUpperTemple       IsleOfKorCaveWorldspace      MaxKingsPass
MQ07aDreamRealm              MQ09Isle                     MQ11cTempleWorldspace
MQ13aStarshipWorldspace      MQ13cNexusbridge             MQ13StarcityNexus
MQKristalltempelEingang      MQP01Home                    MQP02Ship
MQP03Temple                  PiratenversteckSonnenkueste  PresentationDungeon
StarCityNewHarbour
```

The `MQ*` worldspaces are main-quest set pieces; `MQP*` are the prologue. The Capital City is split
across six worldspaces.

> **Look up Enderal's worldspace FormKey; never reuse Tamriel's `00003C`.** Map markers, weather
> regions and cell edits all need the right worldspace. Grep
> `reference/base/Skyrim/Worldspaces/` for the name.

## Interior cells

**524 cell records in base Enderal, 291 more in FS.** **[verified]** These are Enderal's interiors
with Enderal's lighting templates applied — a Skyrim interior-lighting mod has nothing to attach to.

## What this means for the visuals pillar

1. **Weather/lighting mods need porting, not installing.** The records they edit don't exist. Budget
   for an Enderal-specific pass rather than assuming a load-order fix.
2. **Prefer mods that don't touch records at all.** Texture and mesh replacers, parallax, grass, and
   shader-level effects (ENB/Community Shaders) carry over far better than anything editing WTHR,
   IMGS, LGTM or LIGH — because they attach to assets, not to Enderal's record set.
3. **Test cutscene fades.** Run at least one story cutscene before signing off any ENB or
   post-processing change. This is the regression SureAI specifically warns about.
4. **Check `E - Update.bsa` first** when an asset doesn't look like the one you extracted. It loads
   last and overrides the earlier Enderal archives. **[verified]**
5. **Imagespace modifiers are used for gameplay feedback**, not just ambience — e.g.
   `_00E_ArkanistenfieberIMOD` fires when Arcane Fever increases. **[verified]** A blanket
   imagespace override can silently remove a mechanic's only visual signal.

## Assets

Enderal's assets live in its own archives **[verified]**:

| Archive | Holds |
|---|---|
| `E - Meshes.bsa`, `E - Textures1.bsa`, `E - Textures2.bsa` | meshes / textures |
| `E - Misc.bsa` | interface, scripts, misc |
| `E - Sounds.bsa`, `L - Voices.bsa` | audio, voiced dialogue |
| `E - Update.bsa` | **later-patch overrides — loads last, wins** |

The vanilla `Skyrim - *.bsa` are also present, because Enderal still uses a lot of Bethesda's raw
assets even though its records are its own.

Use the `bsa-extract` skill; extract to `reference/` (gitignored), never into `src/`.

## Checklist for a visuals patch

- [ ] Does it edit WTHR / IMGS / IMAD / LGTM / LIGH / CLMT records? Those are Enderal's — port, don't
      install.
- [ ] Have you run a story cutscene to check fades?
- [ ] If it's volumetric lighting, are you aware that's FS-only content?
- [ ] Does it assume the Tamriel worldspace or vanilla region records?
- [ ] Did you check `E - Update.bsa` for the live version of any asset you replaced?
- [ ] Does a blanket imagespace change wipe out a gameplay signal (Arcane Fever, etc.)?
