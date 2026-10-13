# The schools and disciplines of magic

What Enderal's own books say magic is, and how that lore maps onto the records a patch touches.
Read this before renaming, re-schooling or writing descriptions for a ported spell. A Skyrim
school name in a string is a bug in Enderal (see [`porting-from-skyrim.md`](porting-from-skyrim.md)).

**Sources.** Nine in-game books, all by Baledor Dal'Goldenstein, read from
`reference/base/EnderalFS/Books/` (FS carries every one of them). No plugin in the Zenderal list
overrides any of them, so this is the text players read. **[verified]**

| Book | FormKey |
|---|---|
| *The Disciplines of Magic – Elementalism* | `044DEB:Skyrim.esm` |
| *The Disciplines of Magic – Entropy* | `04C9F0:Skyrim.esm` |
| *The Disciplines of Magic – Light Magic* | `0672AC:Skyrim.esm` |
| *The Disciplines of Magic – Mentalism* | `0672AD:Skyrim.esm` |
| *The Disciplines of Magic – Psionics* | `0709D2:Skyrim.esm` |
| *Encyclopedia Arcana – Magic, Part I–IV* | `020B44`, `020B46`, `020B4C`, `02A469:Skyrim.esm` |

## Three schools, five disciplines

Enderal has **schools** (the moral/legal grouping) containing **disciplines** (what the player
levels). The engine only knows the five disciplines. The schools exist in lore, and in the three
mage memory trees.

| School | Standing | Discipline | Engine skill (AVIF) | Memory tree |
|---|---|---|---|---|
| *(stands alone)* | prestigious, legal | **Elementalism** | `AVDestruction 00045A` | Elementalist (`ElementalismPerks`) |
| **Thaumaturgy** | respectable, legal | **Light Magic** | `AVRestoration 00045C` | Thaumaturge (`ManipulationPerks`) |
| | | **Mentalism** | `AVAlteration 000458` | |
| **Sinistra** | forbidden, capital offense | **Entropy** | `AVConjuration 000459` | Sinistrope (`LifeAndDeathPerks`) |
| | | **Psionics** | `AVMysticism 00045B` | |

Display names are the AVIF `Name` strings in Enderal's `Skyrim.esm` (the magic extractor's strings
canary checks them on every run). **[verified]** Note that the Illusion slot's EditorID is
`AVMysticism`, not `AVIllusion`. Search for it by FormKey.

The tree mapping holds in the perk names (`../perks/perks.json`): the Thaumaturge tree carries the
`Mental Apprentice…Master` line plus *Well of Life*, and the Sinistrope tree carries the
`… of the Dark Arts` line plus *Entropic Blood* and *Psionic Veil*. **[verified]**

Porting rule of thumb (Skyrim → Enderal): Destruction → Elementalism, Restoration → Light Magic,
Alteration → Mentalism, Conjuration → Entropy, Illusion → Psionics. The school *is* the skill AV
on the effect, so a ported spell's school is already correct; only its **strings** need renaming.
That mechanical mapping is only the starting point. Re-school a spell when lore **and** perks
disagree with it. Triumvirate's Warlock "Destruction" spells (raw/magic/poison damage + spirit
binding, with none of the fire/frost/shock keywords Elementalist perks need) are moved to
**Entropy** by `MagicPatches` (see [`../patches/MagicPatches.md`](../patches/MagicPatches.md)). Its
Conjuration and Illusion sets stay in Entropy and Psionics, and "Hurl Into Oblivion" was renamed
"Hurl Into Sinistra" by the conversion. The Shadow Mage's "Destruction" set (health/magicka drains,
raw magic damage) gets the same move. EGO's Sinistrope cost perks already call Entropy
"*Schattenzauber*" (shadow spells). Its Alteration set stays in Mentalism (dashes, pulls and portals
are the telekinetic "physical impulse" of the Mentalism book), and its Illusion set stays in
Psionics. Counter-precedent, kept on record: Enderal files its own *Life Absorption* under Light Magic.

## How magic works: the Sea of Eventualities

*Encyclopedia Arcana I* gives the theory every discipline book builds on:

- Vyn is one of countless parallel realities. Each alternative state is an **eventuality**, and the
  sum of them is the **Sea of Eventualities**.
- **Talent** is the ability to *perceive* nearby eventualities. **Power** is the trained ability to
  *bring one into our reality*. To set a tree alight, an elementalist finds a reality where it
  burst into flame by coincidence, then pulls that aspect across.
- Academic consensus on this model dates from about **6000 a. St.**. The god Saldrin pioneered the
  study, which is why many arcanists come from his realm, **Qyra**. Wild and Pathless peoples still
  treat magic as shamanic or supernatural.

So every spell description should be phrasable as "makes an eventuality true". None of the books
mention Oblivion, Aetherius, Magicka-as-a-substance or Daedra.

## The disciplines

### Elementalism

- **What:** fire, earth, water and air, which in game means fire, frost, lightning and earth.
- **Mechanism:** an eventuality where, for example, the air around the hand heats until it ignites.
  It draws **only on the environment, not on the mage's spirit**, so it is "relatively safe". Abuse
  causes exhaustion only.
- **Character:** the most widespread discipline, and very offensive.
- **Reputation:** prestigious, favored by soldiers and battle mages. It is the only magic the wild
  **Arazealeans** know, and they nearly deify their shamans. The **Skaraggs** consider manipulating
  earth unholy.

### Light Magic (School of Thaumaturgy)

- **What:** curing wounds and diseases, and temporarily raising stamina and strength to superhuman
  levels.
- **Mechanism:** the mage finds an eventuality with an intact body and transplants it, so bones knit
  and tissue regrows. Buffs need **unbroken concentration** for their whole duration, and few mages
  manage a permanent link.
- **Limits:** advanced diseases cannot be fully replaced (the **flesh-maggot plague** is the named
  example). Using it on the mind has ended in brain death or madness.
- **Reputation:** "perhaps the most prestigious" art, demanding self-sacrifice. **Erodan the
  Lightborn** is famed for it, and his shrines draw pilgrims. It is popular with common people.
- **Cost:** *Encyclopedia Arcana III* singles out Light Magic as **the** fever-raising discipline.
  This is the lore behind Enderal's healing spells carrying Arcane Fever effects (see below).

### Mentalism (School of Thaumaturgy)

- **What:** barriers made from thin air, telekinetic shockwaves, moving objects by thought.
- **Mechanism:** like Elementalism it acts on the surroundings, so it is relatively safe. A push is
  an eventuality where the object takes a random impulse. A shield is air that "hardens" in a
  sphere around the caster.
- **Why it is hard:** its effects are invisible and **not permanent**. The mage must hold the
  eventuality, unlike a fire that keeps burning on its own. So there are few truly capable
  Mentalists, but power grows steeply with mastery.
- **Reputation:** obscure in most lands but familiar to **Arazealean high priests**. Serious students
  study **Asha He Tis** or travel to **Silvercity**. The Psionics book calls Mentalism Psionics'
  "respectable counterpart".

### Entropy (School of Sinistra)

- **What:** manipulating life and death, conjuring creatures, necromancy.
- **Mechanism, three branches:**
  1. **Reanimation:** imbuing the dead with artificial life makes **Lost Ones**, undead puppets
     bound to the arcanist.
  2. **Conjuration:** "magical anomalies", from ethereal wolves, bears and trolls to elementals and
     otherworldly weapons. In game these are summons and bound weapons. They are anomalies, not
     Daedra.
  3. **Necromancy:** Death is an omnipresent force in every living being. Youth holds it off for
     about two decades, then it drains vitality. The Entropist pulls Death from other realities into
     ours as a storm of lightning and fire that sounds like the cries of the fallen.
- **Cost:** necromancy is the most destructive magic of all, but **it draws on the caster's own life
  force**, and Entropists commonly die of it.
- **Reputation:** forbidden to Path-abiding arcanists and a **capital offense**. Practiced by the
  **Skaragg bone readers**, who hold it holy, use bones as a focus and take narcotics to reach the
  dead, and who somehow bear its toll better than others. Rumor adds some mercenaries from
  **Melêe**. *Encyclopedia Arcana III* adds that the alternative rituals for suppressing Arcane Fever
  are Entropic, and dangerous to both ritualist and subject.

### Psionics (School of Sinistra)

- **What:** manipulating other people's thoughts and feelings.
- **Mechanism:** unlike Mentalism and Elementalism, which alter the physical world, Psionics forces
  a victim's eyes to accept an alternative reality, after which they cannot tell real from false and
  can be steered like a puppet.
  - *Frenzy:* the book's example plants the belief that a mercenary's comrades are monsters, so he
    turns on them.
  - *Invisibility:* enemies are shown a reality in which the caster is absent. In lore, invisibility
    is psionic, not Mentalism.
- **Reputation:** as notorious as Entropy and punishable in the civilized world. Many rulers have
  committed crimes under a Psionicist's spell.

## Arcane Fever and the Journey to the Water

From *Encyclopedia Arcana II–III*. This is the lore under Enderal's Arcane Fever mechanic; the
mechanic itself is covered in [`crafting-alchemy-economy.md`](crafting-alchemy-economy.md) and
[`../magic/README.md`](../magic/README.md).

- **Talent is inborn and probably inherited.** About 1 in 100 humans or Starlings has it, and about
  6 in 100 Aeterna. The apothecarii hypothesize it is carried in the blood. It may emerge gradually,
  suddenly, or never. Life-threatening or liminal experiences, including narcotic hallucinations,
  can trigger it.
- **Onset brings Arcane Fever:** the mind cannot cope with seeing many realities at once. It starts
  as weakness and headaches. After about three moons the mage cannot tell eventualities apart,
  then goes mad, and starts pulling eventualities into the world by accident.
- **One in five untreated cases** ends in the **Blue Death** within a year: the body deforms into an
  **Oorbâya**. Many wild mages owe their Pathlessness to the Fever.
- **The Journey to the Water** is a mandatory year at the **Holy Order** in Enderal, of study, daily
  meditation and prayer, and abstinence. Afterwards the mage is registered as an **arcanist** and
  returns to their Path. Refusing makes them a wild mage, a Pathless criminal.
- **Nobody becomes immune.** Taxing spells, *especially Light Magic*, and proximity to strongly
  magical sites or objects still raise the Fever. Meditation cannot lower this kind. The remedy is
  **ambrosia**, which mages should carry before heavy casting or remote travel.

**Patch implications.** In this list a heal that charges no fever reads as a lore break as well as a
balance break. That is why `MagicPatches` taxes ported self-heals. Mentalism and Elementalism being
"safe, environment-drawn" disciplines is the lore justification for leaving them untaxed. Entropy's
lore cost is the caster's life force, not fever.

## Cultural stance (*Encyclopedia Arcana IV*)

| Place | Stance |
|---|---|
| **Enderal** | Talent must be reported to the Holy Order and the Journey completed. Per the 101 Holy Verses, magic does not override one's Path: a farmer-mage stays a farmer. Arcanists, especially Order novitiates, are respected and also feared |
| **Nehrim, Arazeal** (civilized parts) | Much like Enderal |
| **Qyra, Kilé** | Few rules. **Mage circles** sell their services as mercenaries and researchers. The **Sbintoza** circle is known for unscrupulous research |
| **Wild lands** | Magic attributed to idols or the voices of the dead, practiced as shamanism |
| **Nehrim since Erodan's death** | *Librarian's note:* under Chancellor **Barateon**, only his guard may use magic. Wild mages, especially Aeterna, are hunted |

## Vocabulary for strings

Use these when writing or fixing spell, book and perk text:

| Use | Not (Skyrim) |
|---|---|
| arcanist, mage | wizard, Mages Guild member |
| Elementalism / Light Magic / Mentalism / Entropy / Psionics | Destruction / Restoration / Alteration / Conjuration / Illusion |
| Thaumaturgy, Sinistra (the schools) | Mysticism, "the College" |
| eventuality, Sea of Eventualities | Aetherius, Magicka as an energy source |
| magical anomaly, ethereal creature | Daedra, atronach summoned *from Oblivion* |
| Lost One | draugr (as a reanimated corpse) |
| Arcane Fever, ambrosia | — |
| Sinistra (as in the Triumvirate conversion's "Hurl Into Sinistra") | Oblivion |

The atronach, Daedra and Oblivion rows are inference, not an explicit rule: the books are silent on
them, and the Oblivion row follows the Triumvirate conversion's own renaming. In the books Sinistra
is a school, not a place. Base
Enderal's own records are the final word on any specific name, so check them before rewriting a
string.
