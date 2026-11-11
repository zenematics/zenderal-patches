# FirstPersonUnarmedStances

- **Source:** `src/FirstPersonUnarmedStances/tools/`: `fpu_sources.py` (the source and stance table),
  `00-install-sources.py`, `01-build-overlays.py`, `02-verify.py`; `JellyFishUnarmedSoundsESP/` (Spriggit YAML) and
  `skse/ZenJFUnarmedSounds_BDI.json`.
- **Ships:** MO2 mod `Zenderal - 1P Unarmed Stance Overlays`: **134 OAR `user.json` files and nothing else**, over
  three first-person unarmed sets installed **untouched** from Nexus downloads; and MO2 mod
  `Zenderal - JellyFish Unarmed Sounds` (manifest release of the same name): `Zenderal - JellyFish Unarmed Sounds.esp`
  (ESL, HEDR 1.7, one SNDR) + its BDI file.
- **FormID block:** `0x800` in `Zenderal - JellyFish Unarmed Sounds.esp` (`JFsfxPunchRustle`)

## What it does

First-person fists get one set per stance, like the first-person weapons already do (every SIGMA weapon mod ships
four sets on the Stances perks: High `042518`, Mid `042519`, Low `04251A`, and none). Before this, fists had only
SIGMA - Fisting animations - 1st person in every stance. Third person is not touched (F2/F3 fists there are
[`StanceMovesets`](StanceMovesets.md)' Muay Thai / Kick Boxing, F1 and no stance are FHR).

| Stance | Set (Nexus, installed as its own MO2 mod) | Submods used |
|---|---|---|
| none | Sigerious, *SIGMA - Fisting animations - 1st person* 1.4 (179060), already in the list, **untouched** | all |
| High (F1) | JellyFishInLoop, *JellyFishFP (un)armed* 1.01 (180197, file 754110) | `JFFPU/unrmd` (attacks, power attacks), `JFFPU/unrmdm` (equip, block, idle, walk/run/sprint) |
| Mid (F2) | polar, *Comprehensive First Person Animation Overhaul - CFPAO* 1.5.1 (87169, file 584071) | `CFPAO/UnarmedDefault`, `UnarmedDefaultH`, `UnarmedDefaultHT` (its default unarmed set); the other 123 submods disabled |
| Low (F3) | modbom1, *First-Person Boxing Animation* 1.0 (179716, file 750996) | all: the base set (jabs, power punches, block, bash, sneak attacks) and its five random combos on the two-handed power punch |

SIGMA sits below all three (priorities 1000010–1000021), so in a stance it **fills in** every clip the stance's set
lacks: stagger, recoil, dodge, sneak roll, and (CFPAO, Boxing) everything when the left hand holds a spell, shield or
torch, because those two sets only apply with both hands empty. JellyFish's author recommends SIGMA alongside his set
for exactly that. The pairing of four sets with four stances follows HaikoHosuo's *First-Person Unarmed Stances for
Stances NG* (195256), which is built for the other Stances mod (`StancesNG.esp` effects) and so does nothing here; it
is not installed.

## Mechanism

`01` writes a `user.json` beside every submod's `config.json` (OAR then uses it in place of the config):

- used: the author's config with the stance perk put first. **First-Person Boxing ships with no conditions at all**,
  so raw it replaced `1hm_blockidle`/`1hm_blockbash` for every one-handed weapon in first person, not only fists;
  its submods also get right AND left hand unarmed. **CFPAO ships priority 1–4**, below SIGMA, so its three unarmed
  submods are raised by 1,000,100 (to 1000101/1000102).
- unused (CFPAO's 123 other submods: every weapon, magic, movement): `disabled` plus never-true conditions (player AND
  NOT player). Installed raw at priority 1–4, CFPAO would otherwise take over every first-person clip no other mod
  replaces.

Change a set's stance in `fpu_sources.SOURCES` (`'stance'`), then rerun 01 and 02.

`02-verify` reads the profile's whole first-person OAR tree (every enabled mod + overwrite, MO2's winner per file, a
`user.json` replacing its config) and checks: no submod of the three can play outside its stance or with a weapon in
the right hand (every stance × right-hand weapon × left-hand type); in each stance its set wins every clip it carries;
with no stance none of them is live. 2026-11-10: 0 problems. The one higher submod it cannot decide is Patch
Collection's *Righteous Path Shield 1st person* (priority 2100002000, perk `811`), a deliberate block replacement.

## JellyFish's punch sound (`Zenderal - JellyFish Unarmed Sounds.esp`)

The JellyFish file installed (754110) calls three sounds of its author's own by name: `SoundPlay.JFsfxPunchRustle`
on every punch and power punch, `JFsfxFingerCrack` on one of its two equip clips, `JFsfxBlockRustle` on a block
idle. They live in his *JellyFishInLoop Sound Reprisetory* (180207), which the curator chose not to install
(2026-11-10), and the attack submod takes its triggers from the clips only (`triggersFromAnnotationsOnly`), so the
vanilla clip's swing never plays either: F1 punches swung silently.

A `SoundPlay.<name>` annotation fires only if the actor graph knows the event (JellyFish's own BDI file registers
FingerCrack only; Behavior Data Injector's `"projectPath": "Actors"` reaches the first-person graph, as Precision's
`Collision_*` events show) and plays the sound descriptor with that EditorID. So the fix adds both:

- `ZenJFUnarmedSounds_BDI.json` registers `SoundPlay.JFsfxPunchRustle` in every actor graph;
- SNDR `000800` `JFsfxPunchRustle` = the list's winning `WPNSwingUnarmed 0C06D1` (Audio Overhaul Skyrim.esp's, read
  from the load order; Skyrim.esm's is the only other) **verbatim** but for its EditorID: the swing SIGMA's punches
  play. Checked byte for byte against Audio Overhaul's record: only the two master-index bytes of its own category
  and output model differ (index 5 there, 3 here; same forms). Masters Audio Overhaul for those two forms.

Finger crack and block rustle stay silent: vanilla first-person fists have no equip or block-idle sound (SIGMA's
clips have none either). No loaded plugin defined any `JFsfx*` EditorID before. If the Sound Reprisetory is ever
installed, its own records take over by load order; this plugin can then go.

## Boxing's combo markers (`CLIP_MARKERS`)

[`FirstPersonFistCombo`](FirstPersonFistCombo.md) chains fist hooks on left click from each punch's attack window.
Boxing's jabs had none that fires (see there), so `01` also writes **copies of Boxing's `h2h_attackright.hkx` and
`h2h_attackleft.hkx`** into the overlay mod, at the same path, each with one annotation added by
`hkx_annotate` (binary edit; the compressed animation is byte for byte the author's): `AttackWinStart` /
`AttackWinStartLeft` at 0.54 s. `01` refuses if the clip's length changed or it already has the marker. These two
files are the only derived animation assets here, so they need modbom1's permission, unlike the `user.json` overlays.
**Since 2026-11-11 they ship in Patch Collection** (`fpu_sources.CLIP_MARKERS_MOD`; PC outranks First-Person Boxing
in MO2), curator's call: shipped while permission is asked, **removed from Patch Collection if modbom1 declines**
(then Boxing still plays in F3, but its punches don't chain on left click). `01` writes only those two files into
Patch Collection; `FirstPersonFistCombo/tools/01-verify.py` reads them there.

## Alternatives to Boxing for F3 (searched 2026-11-11)

modbom1's page asks for permission before his files are modified, and he had not answered, so the two marked jab
copies cannot ship yet. Nexus has **no other complete first-person fist set**: the four in use are all there is.
*First Person Unarmed Animation* (87971) has idles, blocks and dodges but no punches; *First Person Unarmed Punches
Reposed* (179803) only re-poses the vanilla jabs (loose files, cannot be stance-gated); FPCAO 2.0 (45177), Modern
first-person animation overhaul (115525) and *Stances based animations for 1st person combat* (65309) are weapons
only. The one unused complete set is inside CFPAO: `CFPAO/UnarmedKhajiit` and `UnarmedArgonian` (gated to beast
races, which Enderal has none of), byte-identical but for the two-handed power punch. Its 1.17 s jabs pass the
vanilla `AttackWinStart` (0.70 s), so left-click combos chain with no clip edit, but the hands swing **open**:
fingertip-to-hand distance on the right jab is 0.83–0.90 of the bind pose, against 0.64–0.71 for JellyFish, CFPAO's
default set and Boxing (fists; SIGMA not measured). Without the marked copies Boxing
still plays untouched (overlays only); what is lost is the left-click chain, so every click is a fresh right jab.

## Known gaps / open

- First-Person Boxing's base clips carry no annotations (only its combos have `hitframe`s): hits come from the
  vanilla clip generators' own triggers, as the author built it. Not checked in game.
- FHR's first-person mechanics do not reach fists in any stance ([`FHRFirstPerson`](FHRFirstPerson.md) leaves
  unarmed out).
- Permissions not checked; the shape (originals untouched, our `user.json` only) is the shippable one. All three
  downloads have MO2 `.meta` files, so Wabbajack can source them. Ticked in Ultra, so the next compile includes them.
- **Unverified in game.**

## Install / regenerate

```
python src/FirstPersonUnarmedStances/tools/00-install-sources.py     # MO2 closed; --force to reinstall
python src/FirstPersonUnarmedStances/tools/01-build-overlays.py
python src/FirstPersonUnarmedStances/tools/02-verify.py
```

The sounds plugin is ordinary Spriggit YAML (manifest release `Zenderal - JellyFish Unarmed Sounds`); its plugin
loads after `Audio Overhaul - Enderal patch.esp` (any position after Audio Overhaul works: a new record only).
Rebuild it if Audio Overhaul changes `WPNSwingUnarmed`.

Rerun 01 + 02 after any of the three sets or SIGMA Fisting updates.
