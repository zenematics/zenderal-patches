# Enderal SE record patterns — known-good archetypes and the traps

A field guide to record shapes that **actually work in-game**, and the plausible-looking ones that
silently don't. Every entry here cost someone a build-deploy-launch-test cycle to discover.

**Why this file exists.** An Enderal plugin can be perfectly valid — Spriggit deserializes it, xEdit
reports no errors, the Creation Kit opens it — and still do nothing at all when you play. The engine
has a large set of unwritten rules about which field combinations are live and which are inert. None
of them produce an error message. The only feedback is "I pressed the button and nothing happened,"
twenty minutes after you started the game.

Enderal runs the **SkyrimSE engine**, so every engine-level rule below is inherited from Skyrim and
holds unchanged. What does *not* carry over is Enderal's **design**: progression, crafting, lighting
and the character UI are SureAI's own. §0 covers the Enderal-specific traps; §1 onward is the engine.

**How to use it:**

- **Before authoring a patch**, find the closest archetype below and copy its shape. Prefer a proven
  pattern over an invented one — the failure mode for invented mechanics is silence, not an error,
  so you pay for the experiment in full test cycles.
- **Before shipping**, run the checklist at the bottom, or ask the `spriggit-formkey-auditor`
  subagent to scan for these anti-patterns.
- **When something doesn't fire in-game**, read the anti-pattern column first. It is usually there.

Confidence is marked per entry:
**[verified]** — observed on this machine's Enderal install, or observed failing and then fixed in a
real playthrough in this project's lineage.
**[community]** — long-established Skyrim-engine modding knowledge, not independently re-tested here.

---

## 0. Enderal-specific — read this before the engine sections

### 0.1 A patch is a forwarding problem, not an authoring problem

Most records this repo touches already exist and are already overridden by somebody. The override
you write **replaces the whole record**, not the field you changed. Every field you did not
deliberately set is silently reverted to whatever your copy happened to contain.

> **Anti-pattern: overriding a record copied from the wrong source.** Copy an Enderal record from
> `Enderal - Forgotten Stories.esm` when the list's winning version comes from a combat overhaul,
> and your bugfix patch quietly undoes the entire overhaul for that record. It builds clean, xEdit
> is happy, and the regression shows up as "the combat mod stopped working on wolves".
> **Fix:** copy from the **winning** plugin in the list's load order, then apply your delta. Load the
> whole list in xEdit (`-EnderalSE`) and read the conflict column before you copy anything.

**Rule:** a patch's master list is a design statement. If your `RecordData.yaml` doesn't master the
mod whose change you are forwarding, you are not forwarding it.

### 0.2 Vanilla perk trees are invisible in Enderal **[verified]**

Enderal's character sheet is a custom menu (`_00E_Game_SkillmenuSC`, a ReferenceAlias script
registered for `"Journal Menu"`), and its *talents* are three-tier **Perks** paired with
**WordOfPower** unlocks, read back through `_00E_TalentLibrary`:

```papyrus
int Function GetPlayerTalentLevel(Perk Perk01, Perk Perk02, Perk Perk03) Global
    if Player.HasPerk(Perk03)
        return 3
    ...
```

> **Anti-pattern [verified]: adding a perk to a vanilla Skyrim perk tree.** The perk exists, the
> entry points work if something grants it — but there is no UI in which the player can ever see or
> buy it, because Enderal never draws the vanilla tree. The mod appears to do nothing.
> **Fix:** attach new combat behaviour to an existing Enderal talent perk, to a keyword on the
> weapon/armor, or to a spell/ability you grant directly. Do not build progression UI.

### 0.3 Skyrim lighting/weather mods are not drop-ins **[verified]**

SureAI, in Enderal's own readme: *"since Enderal changes all light settings, no ENB preset made for
Skyrim would produce adequate lighting in Enderal. Furthermore, ENB mods may deactivate fadeouts in
cutscenes, leading to visual bugs."*

> **Consequence for the visuals pillar:** an imported weather/lighting mod needs an Enderal-specific
> reconciliation pass, and **cutscene fades are the regression to test for** — Enderal is full of
> scripted cutscenes and a broken fade reads as a hang, not as a visual bug.

### 0.4 Check `E - Update.bsa` before believing an asset **[verified]**

Enderal's archives load in order and `E - Update.bsa` is last, so it **overrides** the earlier
`E - Meshes.bsa` / `E - Textures*.bsa`. A mesh or texture you extracted from the wrong archive is a
mesh the game is not using.

### 0.5 Never master a DLC **[verified]**

`Dawnguard.esm`, `HearthFires.esm` and `Dragonborn.esm` are present in Enderal's `Data/` but are not
in `plugins.txt` and are not mastered by Enderal's ESM. Mutagen's implicit base-master list for
`EnderalSE` *does* include them, so **Spriggit will not warn you**. The game will simply not load a
plugin that masters one. See CLAUDE.md → "Masters".

---

## 1. Spells and Magic Effects

### Delivery and casting type must match how the effect reaches its target

| Intent | Casting Type | Delivery | Notes |
|---|---|---|---|
| Passive always-on bonus (an "ability") | `ConstantEffect` | `Self` | The standard boon/perk-carrier shape. Duration 0. Added with `AddSpell`. |
| Player-activated, once per day | `FireAndForget` | `Self` | A **Greater Power**. `Spell.Type = Power`. |
| Player-activated, unlimited uses | `FireAndForget` | `Self` | A **Lesser Power**. `Spell.Type = LesserPower`. |
| Effect applied to another actor at range | `FireAndForget` | `Aimed` | **Requires a Projectile on the MGEF.** |
| Effect applied to whoever you touch | `FireAndForget` | `Touch` | No projectile needed. |
| Radius effect around the caster | `ConstantEffect` | `Self` + Cloak archetype | See §1.2. |

> **Anti-pattern [verified]: an `Aimed` spell with no projectile.**
> The spell casts, the animation plays, magicka is spent — and nothing ever arrives at the target,
> because `Aimed` delivery is implemented by firing a projectile and there isn't one. This is
> especially insidious for effects like *force the target to flee*, where you stand there watching an
> enemy calmly not fleeing with no indication why.
> **Fix:** either attach a Projectile to the MGEF, or restructure so the *victim* self-casts the
> effect (script: `victim.DoCombatSpellApply(fleeSpell, victim)` or `victim.AddSpell(...)`), which is
> usually what you actually wanted for a debuff.

> **Anti-pattern [verified]: using a Greater Power where you meant scaling or repeatable use.**
> `Spell.Type = Power` is hard-gated to once per game day by the engine. If the design says "costs a
> resource" or "usable whenever the condition is met," you want `LesserPower` plus your own gating
> condition — otherwise the mechanic appears broken the second time the player tries it.

### 1.2 Cloak effects always need a cooldown gate

The cloak pattern is: an ability (`ConstantEffect`/`Self`) whose MGEF uses
`MagicEffectCloakArchetype` and points at a **proc spell**; the engine re-applies that proc spell to
every actor in the radius **on a repeating tick**, not once on entry.

```
<Ability Spell>  ConstantEffect / Self, magnitude = radius
  └── <Cloak MGEF>  MagicEffectCloakArchetype, Association -> <Proc Spell>
        └── <Proc Spell>  FireAndForget / Contact (or Self, cast on the victim)
              ├── <Real Effect MGEF>   conditions: cooldown marker ABSENT (+ any filters)
              └── <Cooldown Marker MGEF>  Script archetype, no script, duration = cooldown
```

> **Anti-pattern [verified]: a cloak proc with no cooldown marker.**
> The real effect re-fires on every cloak tick. A "heal a nearby ally" boon becomes an infinite heal;
> a "chance to frighten" becomes a permanent stunlock; a counter becomes a rapidly incrementing one.
> It reads as a wildly overpowered bug rather than a subtle one.
> **Fix:** add a second MGEF to the proc spell that does nothing but exist for `duration` seconds,
> and put `HasMagicEffect(<marker>) == 0` in the real effect's conditions. The marker's *only* job is
> to answer "have I fired recently?"

Enderal uses this shape itself — `_00E_A1_OnslaughtCloakSC` and its dummy/impact companions are a
worked example in `ScriptsEnderal.zip` worth reading before you build one. **[verified]**

### 1.3 A Script-archetype MGEF with no script attached is decoration

`MagicEffectArchetype: Script` tells the engine "the behaviour lives in an attached Papyrus script."
If `VirtualMachineAdapter` is empty, the effect has **no behaviour at all** — it only contributes its
name, description and duration to the active-effects UI.

This is a legitimate and common technique — it is how you show a status or a cooldown marker in the
UI — but it is a trap when someone reads the description text and assumes the mechanic is
implemented. **[verified]** in this project's lineage, an entire set of "tenets" was cosmetic for a
long time because the enforcement actually lived, hardcoded by index, inside a third-party mod's
compiled `.pex`.

**Rule:** if a MGEF's description promises a mechanic, either attach a script that implements it, or
record in this repo's notes that it is display-only and where the real logic lives.

---

## 2. Perks and entry points

> **Anti-pattern [verified]: `MultiplyOnePlusAVMult` on a value-modifying perk entry point.**
> The multiplier is applied to the underlying value, so the mechanic *works* — but the **inventory
> card never updates**. A player looking at their weapon's damage number sees no change and concludes
> the change is broken, then reports it as a bug.
> **Fix:** use a flat `Multiply: <ratio>` entry point instead. The displayed number then tracks the
> real value.

**[community]** Other perk-entry-point notes worth knowing:

- Perk entry points are evaluated by the engine at specific moments; a perk added mid-combat may not
  affect an already-swung attack.
- A perk attached via `PerkToApply` on a MGEF is added/removed with the effect. A perk added by
  script via `AddPerk` persists until you `RemovePerk` it — including across the effect ending.
  Mixing the two mechanisms for the same perk leaves orphaned copies in the save.
- **In Enderal, also check §0.2** — a perk the player cannot reach through the talent UI is only
  useful if something else grants it.

---

## 3. Activators and scripted objects

> **[verified] Property names are matched by string.** A `ScriptObjectProperty`'s `Name:` must equal
> the Papyrus property name exactly, including case. A typo doesn't fail the build — the property is
> simply `None` at runtime, and the script silently no-ops or throws into the Papyrus log where
> nobody looks.

```yaml
VirtualMachineAdapter:
  Scripts:
  - Name: <ExactScriptName>
    Properties:
    - MutagenObjectType: ScriptObjectProperty
      Name: <ExactPropertyName>     # must match the .psc, case included
      Object: <FormKey>
```

> **[verified]** Prefer a **clickable activator** over an effect that tries to detect a player
> action. Detecting an action is fragile; an activator the player walks up to and presses E on is
> unambiguous, discoverable, and trivially debuggable.

---

## 4. Placed objects, map markers and cell edits

Map markers are **two** PlacedObject records in the target worldspace's **persistent** cell:

```yaml
- MutagenObjectType: PlacedObject
  FormKey: <markerKey>:<YourPatch>.esp
  MajorRecordFlagsRaw: 1024                 # 0x400 = Persistent — required
  SkyrimMajorRecordFlags: [0x400]
  Base: 000010:Skyrim.esm                   # MapMarker base
  LocationRefTypes: [10F63C:Skyrim.esm]     # MapMarkerRef — REQUIRED for discoverability
  LinkedReferences:
  - Reference: <linkKey>:<YourPatch>.esp    # the XMarker you fast-travel to
  MapMarker:
    Name: { TargetLanguage: English, Value: <Marker Name> }
    Type: <Shrine|Town|Cave|...>
  Placement:
    Position: <X>, <Y>, <Z>
- MutagenObjectType: PlacedObject
  FormKey: <linkKey>:<YourPatch>.esp
  MajorRecordFlagsRaw: 1024
  SkyrimMajorRecordFlags: [0x400]
  Base: 000034:Skyrim.esm                   # XMarker base
  Placement:
    Position: <X+300>, <Y>, <Z>
    Rotation: 0, 0, 0
```

The worldspace FormKey is **Enderal's**, not `00003C:Skyrim.esm` — look it up in a serialized copy
of `Enderal - Forgotten Stories.esm` rather than reusing Tamriel's.

> **Anti-pattern [verified]: a map marker with no `LocationRefTypes`.**
> It renders on the map but does not behave as a discoverable location — no discovery notification,
> no fast-travel entry. Add `10F63C:Skyrim.esm`.

> **Anti-pattern [verified]: reading placement coordinates off the in-game console.**
> Console coordinates are the *player's* position, not the object's origin, and mesh geometry is
> frequently offset from the reference origin. Read the canonical `Position` from the existing
> PlacedObject record in the serialized worldspace instead. (Concretely, in this project's lineage a
> shrine `.nif` sat **55 units above** its reference origin, so every one placed from console
> coordinates floated.)

> **[community] Never delete a reference** in a cell you're patching. A deleted reference (UDR) that
> another mod or a save still points at causes crashes. Set it *Initially Disabled* and move it far
> below the world instead. `xedit-audit`'s QuickAutoClean pass catches deleted refs and ITMs.

---

## 5. Quests, aliases and script attachment

**Start-game-enabled setup quest** — the standard way to run code once when a patch first loads, and
the standard way to attach a script to the player:

- `Quest.Flags` includes `StartGameEnabled` (and `RunOnce` if it is genuinely one-shot).
- Put persistent per-player behaviour on a **ReferenceAlias pointing at PlayerRef**
  (`000014:Skyrim.esm`), not on the quest itself — alias scripts receive `OnObjectEquipped`,
  `OnHit`, `OnPlayerLoadGame` and friends; a bare quest script does not. This is the shape Enderal
  itself uses for `_00E_Game_SkillmenuSC`. **[verified]**

> **Anti-pattern [community]: relying on `RunOnce` for something that must survive a list update.**
> A `RunOnce` quest that has already run will not re-run for players updating from a previous
> version of the list. Version your setup with a global or a script property and re-run on version
> bump — for a modlist patch this matters far more than for a standalone mod, because players update
> mid-playthrough.

> **[verified] Index-based logic in a third-party compiled script does not extend to your records.**
> If you are appending to arrays inside another mod's quest, any behaviour keyed off `if index == 4`
> inside their compiled `.pex` applies only to *their* indices. Your new entries inherit the
> data-driven parts and none of the hardcoded parts. Verify which is which by reading their
> decompiled source before you promise the mechanic works. For Enderal's own scripts, read the real
> source in `ScriptsEnderal.zip` instead of decompiling.

---

## 6. Globals, gating and persistence

**[community]** `GlobalVariable.SetValue` from Papyrus persists in the save. The standard daily-gate
pattern is to store `GameDaysPassed` (`000039:Skyrim.esm`) at use time and compare on the next
attempt:

```papyrus
If (GameDaysPassed.GetValue() as Int) > (LastUsedDay.GetValue() as Int)
    LastUsedDay.SetValue(GameDaysPassed.GetValue())
    ; ... do the thing
Else
    Debug.Notification("You must wait until tomorrow.")
EndIf
```

Prefer this over a Greater Power's built-in once-per-day when you need the cooldown to be visible,
adjustable, or conditional.

---

## 7. Plugin-level shapes

- **ESL / `Small`-flagged plugins are limited to FormIDs `0x800–0xFFF`** for *new* records — 2048 of
  them. Overrides consume none of that budget, so an ESL patch can override thousands of records.
  Allocate a contiguous block per feature and grep the whole workspace before assigning a hex ID;
  the `formkey-check` skill does this.
- **New records** take your patch's ModKey as the FormKey suffix (`000801:YourPatch.esp`).
  **Overrides keep the defining master's suffix** (`0099B0:Enderal - Forgotten Stories.esm`) — that
  is how you tell at a glance which records you invented and which you are modifying.
- **Set a sane `Stats.Version` in `RecordData.yaml`.** SSE Wrye Bash rejects `0.85`-style versions;
  use `1.7` (which is what Enderal's own ESM carries **[verified]**).
- **Every master you reference must be declared** in `RecordData.yaml`'s `MasterReferences`, in load
  order: `Skyrim.esm`, `Update.esm`, `Enderal - Forgotten Stories.esm`, then third-party plugins.
  A FormKey pointing at an undeclared master resolves to garbage at runtime.
- **`GameRelease: EnderalSE`** in `RecordData.yaml` and `spriggit-meta.json`, matching `.spriggit`.

---

## Pre-ship checklist

Run through this before packaging. The `spriggit-formkey-auditor` subagent can check most of it.

| # | Check | Failure mode if skipped |
|---|---|---|
| 1 | Every override was copied from the **winning** plugin in the list, not from Enderal's ESM by default | Silently reverts another mod's change |
| 2 | `GameRelease` is `EnderalSE` everywhere; no DLC in `MasterReferences` | Plugin fails to load in Enderal |
| 3 | No duplicate FormIDs within the plugin | Spriggit or the game picks one arbitrarily |
| 4 | ESL-flagged → all **new** FormIDs in `0x800–0xFFF` | Records silently dropped or remapped |
| 5 | Every referenced FormKey resolves; every master declared in load order | Dangling ref, garbage at runtime |
| 6 | Filename `<EditorID> - <FormID>_<Master>.esp.yaml` matches the `EditorID:`/`FormKey:` inside | Confusing diffs; usually a copy-paste bug with a real wrong-record behind it |
| 7 | No new perks placed in vanilla perk trees | Player can never see or buy them |
| 8 | No `Aimed` spell without a projectile | Spell casts, nothing happens |
| 9 | Every cloak proc gated by a cooldown-marker MGEF | Effect fires every tick |
| 10 | No value-modifying perk entry point using `MultiplyOnePlusAVMult` | Works, but inventory card never updates |
| 11 | Every map marker has `LocationRefTypes: [10F63C:Skyrim.esm]` and a linked XMarker | Not discoverable, no fast travel |
| 12 | Every Script-archetype MGEF either has a script or is documented as display-only | Description promises a mechanic that doesn't exist |
| 13 | Every `ScriptObjectProperty.Name` matches the `.psc` property exactly | Property is `None`; script silently no-ops |
| 14 | Scripts compiled with Enderal's source **first** on `-i` | Built against vanilla signatures; fails at runtime, not compile time |
| 15 | Every `.psc` changed → recompiled **and the `.pex` committed** | Ships stale scripts; CI cannot detect this |
| 16 | Parallel arrays / linked record sets are the same length | Silent per-index failure |
| 17 | No deleted references in patched cells | Crashes for anyone whose save references them |

**And the rule that supersedes all of the above:** a clean deserialize, a clean xEdit report, and a
clean Papyrus compile prove the patch *builds*. They prove nothing about whether it *runs*. Deploy
to a real Zenderal profile and look at it with your own eyes before you call it done.
