"""Build the four Prophecy perk trees (Faith, Sharpshooter, Gadgets, Martial Arts).

Regenerates, from the serialized source mods in reference/mods/:
  ProphecyESP/{Perks,Spells,MagicEffects,...}/   every record a picked perk needs, renumbered into
                                                  Zenderal - Prophecy.esp (block 0x810+)
  Scripts/compiled/*.pex                          the source mods' compiled scripts those records use
  assets/                                         meshes/textures those records use (from the BSAs)
  csf/Prophecy.json                               the Custom Skills Framework menu: 4 trees, 5 nodes each

Sources (both allow modification/redistribution with credit; see arch-docs/ordinator/README.md):
  Ordinator - Perks of Skyrim (Enai Siaion)  reference/mods/Ordinator, raw BSA in reference/mods/_raw/Ordinator
  Subclasses of Skyrim 2 (Darenii)            reference/mods/SubclassesOfSkyrim, raw in reference/mods/_raw/SubclassesOfSkyrim

Rules the copy follows (asserted, the script fails loudly otherwise):
  * a reference to a copied record is repointed to its new FormKey;
  * a reference to a source PERK we did not pick is repointed to ZP_Prophecy_Never (never owned), so every
    "has perk X" condition on an unpicked perk evaluates exactly as it would for a player who lacks it;
  * any other reference into a source plugin, or to a base-game form Enderal does not define, is an error.
Never hand-edit what this script writes - edit the SPEC below and re-run, then 02 (fever tax) is folded in here.
"""
import os, re, sys, json, glob, shutil, struct, collections

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE)
from _closure import index, FK
import _bsa

PATCH = os.path.join(REPO, 'src', 'Prophecy')
ESP = os.path.join(PATCH, 'ProphecyESP')
MOD = 'Zenderal - Prophecy.esp'
ORD = 'Ordinator - Perks of Skyrim.esp'
SOS = 'SubclassesOfSkyrim.esp'
REF = os.path.join(REPO, 'reference')
SRC = {ORD: os.path.join(REF, 'mods', 'Ordinator'), SOS: os.path.join(REF, 'mods', 'SubclassesOfSkyrim')}
RAW = {ORD: os.path.join(REF, 'mods', '_raw', 'Ordinator'), SOS: os.path.join(REF, 'mods', '_raw', 'SubclassesOfSkyrim')}
BSAS = {ORD: ['Ordinator - Perks of Skyrim.bsa', 'Ordinator - Perks of Skyrim - Textures.bsa'], SOS: ['SubclassesOfSkyrim.bsa']}

FIRST_ID = 0x810                   # 0x800-0x807 are the prototype's hand-written records
NEVER = f'000808:{MOD}'            # ZP_Prophecy_Never            # ZP_Prophecy_Never, written below
FEVER = '11A4B6:Skyrim.esm'        # _00E_IncreaseArcaneFeverFFSelf - Enderal's healing-magic tax
WEAPTYPEBOW = '01E715:Skyrim.esm'  # muskets carry it (arch-docs/patches/MusketHandling.md)
FIRE_ENCH = '04605A:Skyrim.esm'    # EnchFireDamageFFContact

o = lambda h: f'{h}:{ORD}'
s = lambda h: f'{h}:{SOS}'

# Smokescreen also turns the player invisible on cast (curator 2026-10-23). Enderal's plain InvisibillityFFSelf
# 01EA6A (no script; attacking or activating ends it), not Spectral Veil's _00E_A1_InvisibilityME 067239, whose
# script SETS base Sneak +75 and writes the old value back: overlapping the player's own Spectral Veil could leave
# Sneak permanently changed. 10 s = Spectral Veil's first rank.
SMOKE_INVISIBLE = '01EA6A:Skyrim.esm'
SMOKE_INVISIBLE_SECONDS = 10

# Arcane Archery's numbers (curator 2026-10-23; Ice Shot first followed Flame Shot's middle tier: 14 s, 110 s recovery;
# after play: no time limit (IceSeconds = a day: the arrows stay until fired), no cooldown, a 50 Magicka cost;
# No Distractions casts the list's own Spell Ward (Rank II) - SPELL_WARD_RANK2)
# Ice Shot is a talent (a shout) with Flame Shot's cooldown since 2026-10-28 (curator): IceCooldown = EGO's Fire Arrow
# RecoveryTime (110, all ranks), and no Magicka cost - the 50 Magicka replaced the first build's cooldown on 2026-10-23
ARC = {'ElementDamage': 10, 'IceArrows': 3, 'IceSeconds': 1, 'IceMagicka': 0, 'IceCooldown': 110, 'IceDamage': 25,
       'FreezeSeconds': 8, 'OwlDrain': 10, 'OwlRegen': 2}
# Necromancy's numbers (curator's design 2026-10-23; the balance is ours). A Willing Sacrifice deals half the summon's
# base Health - SureAI's own Corpse Explosion rule (_00E_FS_Entropy_CorpseExplosionSC) - to each enemy within
# 300 units (14 ft; Enderal's Fireball is 12 ft), with a 15 s cooldown so it cannot be chained with Revive.
# Legion: 5 minutes, 80 + 8 Health per player level. Dark Effigy prices like Triumvirate's Create Earth Totem (76, 60 s).
NEC = {'FeverStep': 25, 'EffigyCost': 100, 'EffigySeconds': 60, 'EffigyHeal': 2, 'EffigyArmor': 250, 'EffigyRadius': 512,
       'SacrificeRadius': 300, 'SacrificeFraction': 0.5, 'SacrificeCooldown': 15, 'DeadMagicka': 50,
       'LegionFever': 50, 'LegionSeconds': 300, 'LegionHealth': 80, 'LegionHealthPerLevel': 8}
# Rage (curator 2026-10-27). Seconds are wall-clock seconds of unpaused game, counted by ZenProphecyRage.dll.
RAGE = {'Max': 10, 'MaxUntempered': 15, 'DamagePerStack': 2, 'FadeAfter': 6, 'FadeEvery': 3, 'CombatGrace': 3,
        'SprintGrace': 1.0, 'HitDedupe': 0.25, 'SwingWindow': 0.5, 'VehemenceSeconds': 15,
        # the meter (Oxygen Meter 2's movie, our menu): where the casting bar sits, between the compass and the health bar
        # (curator 2026-10-27) - Casting Bar 4.0's CenterSlot fPositionY 90.7 and fScale 56 (Aspect Layout's CastingBar.ini);
        # X 50 is the screen's centre line in Oxygen Meter's movie. Bold orange-red (curator)
        'Meter': {'x': 50.0, 'y': 90.7, 'rotation': 0.0, 'xscale': 56.0, 'yscale': 56.0,
                  'barColour': 'E8400C', 'flashColour': 'FF2A00',
                  'followCastingBar': True,
                  # the health bar's width and centre (curator's screenshot 2026-10-27: the bar was 215 of the
                  # health bar's 265 px, centred 18 px left): xscale 56 -> 69, centre +0.9% of the stage width
                  'width': 63.0, 'xOffset': 0.1},   # in game (curator's screenshots): 69 too wide, 63 matches; +0.9 and 0.55 sat right of it   # the DLL reads Casting Bar's live CastingBar.ini (centre slot, spell scale) - x/y above are the fallback
        # costs doubled-ish (curator 2026-10-28: "so you can't just spam them"; was 5/3/3/5/3/3): a full 10-stack bar
        # buys one big action (sprint/standing) or one small one with a few stacks left
        'Cost': {'Heavenfall': 8, 'Shadow Carve': 6, 'Dark Deluge': 6, 'Shadowbringer': 8, 'Bloodletter': 6, 'Soulrender': 6}}
# Shadow's Darkness (curator 2026-10-28): a meter that fills in darkness and pays for the Shadow talents' spells instead
# of Mana (ZenProphecyDarkness.dll, src/Prophecy/darkness). Fill steps use Gather Shadows' own light thresholds
# (TVR_Shadows_Global_GatherShadows_Threshold_1-3: 60/40/20, the light level behind the sneak eye): darker fills faster.
# Above the last step it drains. Nightfall costs the full meter ('full').
# 2026-10-28 (curator): daytime shade outdoors filled nothing at 60, so a fourth, slower step up to 90 (the log showed
# 137 in open light); the DLL logs the light level every 5 s for the next tuning.
DARKNESS = {'Max': 10, 'Fill': [(20, 1.0), (40, 1.5), (60, 2.0), (90, 3.0)], 'VeilMult': 2.0, 'DrainEvery': 4.0,
            'Cost': {'shd1': 3, 'shd2': 4, 'shd3': 4, 'shd4': 3, 'shd5': 'full', 'shd7': 2},
            # the meter: Rage's (Oxygen Meter 2's movie, our own menu), dark navy / purple (curator 2026-10-28; bar #4E5180, was 2A1A5E). Rage
            # follows the casting bar's slot (90.7% in Vel'dun's bottom HUD); this sits just below the Stamina / Mana
            # bars (curator's screenshots: -2.5 sat on the compass, 2.8 on the Stamina / Mana bars, 4.0 a little high and wide)
            'Meter': {'x': 50.0, 'y': 90.7, 'rotation': 0.0, 'xscale': 56.0, 'yscale': 56.0,
                      'barColour': '4E5180', 'flashColour': '6B48C8', 'followCastingBar': True,
                      'width': 60.0, 'xOffset': 0.1, 'yOffset': 4.8}}
# Nightblade on Darkness (curator 2026-10-28: "scale its damage on the Darkness meter instead of Mana"). Triumvirate's
# proc (TVR_Shadow_Spell_Nightblade_Proc 335B4F, cast by TVR_BlinkStrikes_Script on each power attack) deals a flat 45
# and its 335B52 effect takes 50% of the CASTER's current Magicka (TVR_PercentageDamage_Script: akCaster) - the "50% of
# your Magicka into damage" of its text, though the damage never read it. With Gather Shadows the Mana drain is off and
# the DLL spends Fraction of the Darkness (rounded up) on each proc hit, adding PerPoint magic damage per point spent.
NIGHTBLADE = {'Fraction': 0.5, 'PerPoint': 15}
# Dragon's Breath (curator 2026-10-28): every Every-th unarmed hit, ZenProphecyRage.dll casts one of three elemental
# cones at the target - Hissing Dragon's fire/frost/shock procs, reaching Range units (~5 m) instead of 128
DRAGONS_BREATH = {'Every': 5, 'Damage': 60}
SHADE_VEIL_DETECT = 50   # Shade Veil: ModDetectionSneakSkill Add, SureAI's "percent" (Infiltrator: Devious 15)
NIGHTFALL_FEVER = 50     # Shadow's capstone power: Arcane Fever per use; refused at this much or more (as Wrath)
# Druid's numbers (curator 2026-10-27). Force of Nature's 60 s are Triumvirate's own (its spell 28E6EB); the familiars
# last FamiliarSeconds unless the form ends first.
TWISTER_COST = 97       # Abyssal Wind's Twister (tier 75, FireAndForget) on EGO's ladder: 409 Mana on Skyrim's scale
# Drowning Orb (Water Globe) drains OrbDrain Mana per second from each enemy inside it into the caster, and restores
# OrbRegen per second to the player standing in it. Mana Burn (the capstone power of 2026-10-27, replaced by
# Shatterveil's Veil Wyrm shout on 2026-10-28) lives on as the shout's buff (curator, same day): every word casts its
# marker (spells x CostMult Mana, the blue-flame aura) and the RegenPerSecond restore, both BurnSeconds; no fever
# BurnSeconds 60 -> 20 and the shout's recovery doubled (WYRM_COOLDOWN_MULT; curator 2026-10-28)
# Blink Step is a lesser power (curator 2026-10-28): a power spends no Mana, so the spell gets a second effect that
# takes BLINK_MANA (blinkme), and both effects need that much Mana first - the blink is listed first, so it is checked
# before the Mana comes off
BLINK_MANA = 35
# ...and, as a power plays no hand-casting sounds, it plays the spell's own cast sound - its effect's Release sound,
# vanilla MAGIllusionReleaseSelfSD 07BBAE - through sound_records: a third effect that plays it (Explosive Tripwire's
# pattern). As a Release sound on the power it did not play, and a mix of Shatterveil's glass shatter + re-form added a
# bell the original never had (curator, in game, 2026-10-28; 'blinksnd' 0xAE3 retired)
BLINK_CAST_SOUND = '07BBAE:Skyrim.esm'
# ...plus the curator's swoosh (2026-10-29, "add this sound to the Sorcery blink step"): Motion Array's
# MA_Originals_FastSwooshTransitions_5 (24-bit, converted to 16-bit by tools/07-build-sounds.py, not committed),
# played by a fourth effect the same way
BLINK_SWOOSH_RECORDS = ('swooshsnd', 'swooshmarker', 'swooshplay')
BLINK_SWOOSH_FILE = r'Data\Sound\FX\ZenProphecy\ZP_BlinkStepSwoosh.wav'
# Gravity Well (Celestial Vortex) drains GW_ABSORB Health from each enemy it catches into the caster (curator
# 2026-10-28). Its hazard re-casts _K01_CelestialVortexHazardEffect 000826 on everyone inside every 0.3 s for 3.1 s, and
# that spell's first effects include a 9 s marker (000810, "cooldown"): the absorb is listed first and needs the marker
# not yet on the target, so it lands once per enemy per well. Enemies only (IsHostileToActor player)
GW_ABSORB = 20
GW_HAZARD_SPELL = '000826:KittySpellPack01.esl'
GW_COOLDOWN_MGEF = '000810:KittySpellPack01.esl'
WYRM_COOLDOWN_MULT = 2   # the Veil Wyrm's word recovery times (Shatterveil's 20/35/50 s) x this
# Balance pass (curator 2026-10-29: "match up with similar tiered spells in EGO"). Every Sorcery spell sits on EGO's
# 97-Mana rung (Expert); EGO's damage at that rung, base magnitudes from arch-docs/magic: single target Blazing Spark VI
# 78.5 (85 Mana), Firebolt VI 62 (68); area Fireball III 63 (90, area 12), Chain Lightning III 75 (107, area 20),
# Frostwind III 53 + slow (78); per second Flame Bite III 19.2, Grounding III 23.85 (concentration). The packs' own:
# Frost Spires 80 per spire up to four, Wildfire 80 on impact plus a homing hazard of 32 every 0.6 s for 10 s,
# Starlance 120 (its sub-spell _SS_CelestialRaysDamageSpell), Drowning Orb 30 Stamina + Mana per hazard tick (60/s).
# Falling Star (60, area 18 - Fireball III's) and Gravity Well (20 + 20 absorbed) already sit on the ladder.
SORC_MAG = {'Spires': 30, 'WildfireHit': 40, 'WildfireBurn': 12, 'Starlance': 80, 'OrbSap': 15, 'OrbSapPerSecond': 30}
# record -> [(effect, nth occurrence, magnitude)]: the packs' spells (and sub-spells) at Enderal's ladder
SORC_TUNE = {'000825:KittySpellPack02.esl': [('000817:KittySpellPack02.esl', 0, SORC_MAG['Spires'])],     # Frost Spires
             '000829:KittySpellPack02.esl': [('00081E:KittySpellPack02.esl', 0, SORC_MAG['WildfireHit'])],  # Wildfire
             '000827:KittySpellPack02.esl': [('000819:KittySpellPack02.esl', 0, SORC_MAG['WildfireBurn'])],  # its hazard
             '000814:Supernova.esl': [('000809:Supernova.esl', 0, SORC_MAG['Starlance'])],                   # Starlance (shown)
             '000816:Supernova.esl': [('00080C:Supernova.esl', 0, SORC_MAG['Starlance'])],                   # its beam
             '000828:KittySpellPack01.esl': [('000813:KittySpellPack01.esl', 0, SORC_MAG['OrbSap'])]}        # Drowning Orb
EFFIGY_EVERY = 6.0   # Twin Effigies' chain lightning (curator 2026-10-29 "balance"): 3 s was 2 x 40 every 3 s for 30-60 s
SORC = {'OrbDrain': 10, 'OrbRegen': 10, 'BurnSeconds': 20, 'CostMult': 0.5, 'RegenPerSecond': 10}
# Ricochet Rounds (2026-10-29): chance per pistol hit, the second target's search radius (units, ~feet)
RICOCHET = {'Chance': 25, 'Range': 960, 'Feet': 45, 'Cooldown': 1.0}
# The Hunt (2026-10-29): Goodberries spent per call; the wolves' summon lasts HUNT['Seconds'] - "until killed"
HUNT = {'Berries': 5, 'Seconds': 100000}
DRUID = {'CraftBerries': 1, 'CraftHeal': 20, 'FormFever': 50, 'FormSeconds': 60, 'FamiliarSeconds': 65, 'ExtraSummons': 4}

# id, name, description, source seed, perks folded INTO this node (their FormKeys alias to it), parents
TREES = [
  # Faith reworked 2026-10-25 around Kittytails' Holy Templar Magic (curator's design). The node ids, seeds and so the
  # FormIDs stay (0x810-0x814): faith1-faith4's old perks (Descending Light, Respite, Edgewalker, Healing Presence) are
  # rewritten in place (FAITH_NEW), so their seed closures - and every ID after them - are unchanged, and a save that
  # owned one owns its successor in the same place. faith4 is now the capstone and faith5 (Templar) the merge talent:
  # FAITH_CAPSTONE tells weave_stats.
  ('Faith', 'Holy light, sacred wards and smiting.', [
    ('faith1', 'Consecrate Dead', 'Grants the "Consecrate Dead" spell: cast it on a corpse to burn it to ash with holy light and restore 30 Health, Mana and Stamina. Undead it strikes take 15 damage and stagger.', o('01435F'), [], []),
    ('faith2', 'Righteous Path', 'While you block with a spell or nothing in your left hand, a ward of sunlight surrounds you: you gain 25% resistance to magic and immunity to disease, and each attacker you block is struck by a beam of light that leaps between enemies for 20 damage, for 10 Mana (with less, you simply block).', '0581F9:Skyrim.esm', [], ['faith1']),
    ('faith3', 'Smite', 'Your hits with silver weapons have a 15% chance to call down a pillar of holy light on the target: 40 damage, while beams of light strike the enemies around it for 10 each. Undead take double damage.', '0581F8:Skyrim.esm', [], ['faith1']),
    ('faith4', 'Wrath of the Lightborn', 'Grants the "Wrath of the Lightborn" spell (no Mana, 50% Arcane Fever): for 60 seconds, bolts of sunlight strike enemies within 20 feet of you for 40 damage each. Undead take double damage. It cannot be cast at 50% Arcane Fever or more.', s('000820'), [], ['faith5']),
    ('faith5', 'Templar', 'Once every 90 seconds, dropping below 25% Health makes you immune to damage for 6 seconds, then heals you for 100 Health.', s('000849'), [], ['faith2', 'faith3']),
  ]),
  ('Firearms', 'Muskets, powder and lead.', [
    ('gun1', 'Quick Reload', 'You reload muskets 30% faster.', '105F19:Skyrim.esm', [], []),
    ('gun2', 'Elemental Rounds', 'Your musket hits deal 10 extra fire damage.', None, [], ['gun1']),
    ('gun3', 'Bleeding Shot', 'Your musket hits make living targets bleed for 50 damage over 5 seconds.', None, [], ['gun1']),
    # Ricochet Rounds (curator 2026-10-29): pistols, off Steady Aim (the root's stat talent), allocated last
    # (FIREARMS_LATE_NODES). ZenProphecyRage.dll does the bounce (write_rage's 'ricochet')
    ('gun6', 'Ricochet Rounds', f"Your pistol shots have a {RICOCHET['Chance']}% chance to ricochet off their target into another enemy up to {RICOCHET['Feet']} feet away, hitting it with the same shot.", None, [], ['gst1']),
    ('gun4', 'Run and Gun', 'You move at full speed while aiming a musket.', '058F63:Skyrim.esm', [], ['gun2', 'gun3']),
    ('gun5', 'Deadeye', "A musket shot at a target you haven't shot in the last 10 seconds is a critical strike that deals triple critical damage, and its weapon enchantments are twice as strong.", o('0064C0'), [], ['gun4']),
  ]),
  ('Gadgets', 'Traps, smoke and clockwork.', [
    ('gad1', 'Explosive Tripwire', 'Grants the "Explosive Tripwire" power: at will, set a tripwire in front of you that lasts 120 seconds. When tripped, it snaps and knocks everyone it hits to the ground, and an enemy who trips it sets off an explosion that deals 40 damage.', o('0379AA'), [], []),
    ('gad2', 'Smokescreen', f'Grants the "Smokescreen" power: once a day, create a 35-foot cloud of smoke for 180 seconds and turn invisible for {SMOKE_INVISIBLE_SECONDS} seconds. Those inside the cloud are blinded and cannot see sneaking targets, and your sneak attacks against them deal 50% more damage.', o('037419'), [], ['gad1']),
    # Chaff (curator 2026-10-26): a side talent off Smokescreen. No effect of its own - fix_smoke_blind lets the cloud's
    # blindness take automatons when the player has it. Allocated last (LATE_NODES), so no older ID moved.
    ('gad6', 'Chaff', 'Your Smokescreen cloud also blinds automatons: mechanical spiders, spheres and centurions inside it can no longer see you.', None, [], ['gad2']),
    # gad3 was Bear Traps (Ordinator 0306CB + Lockjaw 030C45). Utility Droid replaced it 2026-10-23; the seed and the
    # folded perk stay so the copy closure, and every ID after it, is unchanged. The perk itself is rewritten (DROID_NODE).
    ('gad3', 'Utility Droid', 'Grants the "Utility Droid" power: throw out a mechanical spider that follows you, heals you and staggers enemies around it. It lasts until destroyed, and using the power again calls it back to you. Your first droid is free; each new one costs 10 Spare Parts.', o('0306CB'), [o('030C45')], ['gad1']),
    ('gad4', 'Clockwork Turret', 'You can build Clockwork Turrets at a forge, and you receive one when you learn this. The "Clockwork Turret" power deploys it for 30 seconds: it turns and fires at your target, or the nearest enemy in combat, dealing damage equal to 30% of your Handicraft skill.', o('056C92'), [], ['gad2', 'gad3']),
    ('gad5', 'Overclock', 'Your Clockwork Turret power deploys two turrets side by side, and they fire 2% faster with every shot, up to 200%.', None, [o('056C9F'), o('056CA7')], ['gad4']),
  ]),
  # Shadow (2026-10-27, curator's design): Triumvirate's Shadow Mage spells, granted by the menu (SHADOW_GRANTS; Magic
  # Patches prices them), and Nightfall as a fever-priced power (write_shadow). Allocated after every older block
  # (SHADOW_FIRST_ID), so sitting between Gadgets and Martial Arts renumbered nothing.
  ('Shadow', 'Darkness, stealth and stolen strength.', [
    ('shd1', 'Gather Shadows', f'Darkness gathers in you while you stand in shadow, up to {DARKNESS["Max"]}: the darker it is, the faster. In light it slowly fades. Your Shadow talents spend Darkness instead of Mana. Grants the "Gather Shadows" spell ({DARKNESS["Cost"]["shd1"]} Darkness): for 60 seconds, your melee attacks and Shadow spells are up to 50% stronger in darkness.', None, [], []),
    ('shd2', 'Draining Shroud', f'Grants the "Draining Shroud" spell ({DARKNESS["Cost"]["shd2"]} Darkness): for 60 seconds, you absorb 10 Health and Mana per second from nearby enemies.', None, [], ['shd1']),
    ('shd3', 'Nightblade', f'Grants the "Nightblade" spell ({DARKNESS["Cost"]["shd3"]} Darkness): for 60 seconds, your power attacks can reach targets up to 50 feet away, dashing you to them for 45 magic damage. Each dash spends half your Darkness, dealing {NIGHTBLADE["PerPoint"]} more magic damage per point spent.', None, [], ['shd1']),
    # Shade Veil (2026-10-28): off Silent Step, a dead end; added after the tree's first build, so allocated last
    # (SHADOW_LATE_NODES). The menu holds two parents at most, so it does not join the merge below
    ('shd6', 'Shade Veil', f'While you sneak, your body is wrapped in black and grey mist, you are {SHADE_VEIL_DETECT}% harder to detect, and Darkness gathers twice as fast.', None, [], ['sst1']),
    # Darkness (2026-10-28): after Shade Veil, allocated after the Darkness meter's records (SHADOW_LATE_NODES_2)
    ('shd7', 'Darkness', f'Grants the "Darkness" spell ({DARKNESS["Cost"]["shd7"]} Darkness): a bolt that leaves a pool of black mist and darkness where it strikes for 30 seconds.', None, [], ['shd6']),
    ('shd4', 'Pull Through Shadows', f'Grants the "Pull Through Shadows" spell ({DARKNESS["Cost"]["shd4"]} Darkness): pull a target up to 150 feet away to you, lowering its armor by 100 for 10 seconds.', None, [], ['shd2', 'shd3']),
    ('shd5', 'Nightfall', f'Grants the "Nightfall" power (a full Darkness meter): for 60 seconds, a pool of darkness follows you and every Shadow spell you know is cast on you at once.', None, [], ['shd4']),
  ]),
  ('Martial Arts', 'Fists, footwork and timing.', [
    ('ma1', 'Iron Fist', 'Your unarmed attacks deal extra damage equal to 15% of your current Stamina. Requires both hands to be empty.', '058F6E:Skyrim.esm', [], []),
    ('ma2', 'Hissing Dragon', 'Choose a damage type (fire, frost, shock, poison, disease or sun): your unarmed attacks unleash a shockwave that deals it to everyone in front of you. Requires both hands to be empty, and does not trigger while sneaking.', o('04D4E3'), [], ['ma1']),
    # Dragon's Breath (2026-10-28): beside Hissing Dragon, off Conditioning (the root's stat talent), allocated after
    # Nightblade's records (MARTIAL_LATE_NODES)
    # renamed Invoker (curator 2026-10-29); its records keep their DragonsBreath EditorIDs
    ('ma6', 'Invoker',f"Every {DRAGONS_BREATH['Every']}th unarmed hit unleashes fire, frost or lightning on the enemy, at random: a fireball explosion, a freeze that holds it for 4 seconds, or chain lightning that leaps to nearby enemies. Each deals {DRAGONS_BREATH['Damage']} damage.", None, [], ['mst1']),
    ('ma3', 'Stunning Blows', 'Your unarmed attacks have a 15% chance to stagger enemies, and deal 25% more damage to staggered enemies.', s('000851'), [], ['ma1']),
    ('ma4', 'Breaking Waves', 'Your unarmed attacks have a 15% chance to land a critical strike that deals damage equal to 40% of your current Stamina. Requires both hands to be empty.', o('04D4DA'), [], ['ma2', 'ma3']),
    ('ma5', 'Flow State', 'Dodging in combat briefly slows time to a crawl (once every 8 seconds) and releases a Shock Nova that deals 40 shock damage to nearby enemies and sends chain lightning into your foe (once every 8 seconds).', None, [], ['ma4']),
  ]),
  # Glory (2026-10-21, curator's design): all hand-built - see write_glory. Its records sit AFTER every other
  # block (GLORY_FIRST_ID) so adding it did not renumber the four older trees in existing saves.
  ('Glory', 'Charges, banners and hard-won grit.', [
    ('glo1', 'Seismic Stomp', 'Grants the "Seismic Stomp" power: stomp the ground to send out a shockwave that hurls every enemy within 19 feet into the air and makes them bleed for 50 damage over 5 seconds, while time briefly slows. Usable once every 30 seconds.', None, [], []),
    ('glo2', 'Second Wind', 'While you are at or below half Health, every hit you take restores 20 Stamina.', None, [], ['glo1']),
    ('glo3', 'Dragon Scale', 'You gain 25% resistance to fire, frost and lightning.', None, [], ['glo1']),
    ('glo5', 'Surrounded', 'While 3 or more enemies are near you, you regenerate 2 Stamina per second.', None, [], ['glo2', 'glo3']),
    ('glo4', 'War Banner', 'Grants the "War Banner" power: plant a banner for 15 seconds. While you stand near it, you heal 20 Health per second, and enemies who come close are bound in chains, as by a Stave of Binding. Usable once every 5 minutes.', None, [], ['glo5']),   # capstone after Surrounded (curator 2026-10-24)
  ]),
  # Rage (2026-10-27, curator's design): A Dark Warrior's Tale's class actions (Kittytails; installed, cleaned by
  # src/KittytailsPacksClean), driven by Rage stacks. ZenProphecyRage.dll counts the stacks from hit events (no
  # ApplyCombatHitSpell: one per hit, and EGO's XionPowerStagger and Enderal's class talents already use it), fires
  # each talent's action by power-attack direction and runs Vehemence; its config is generated (write_rage_json).
  # The talents' perks are markers the DLL reads; Bloodied Fury's damage bonus and Vehemence's free power attacks
  # are perk entries on the ZP_Rage global / the Vehemence effect. Shaped by hand (HAND_STATS); after Sorcerer.
  ('Rage', 'Fury, blood and the strength of the fallen.', [
    ('rge1', 'Bloodied Fury', f'Rage builds as you fight: every melee hit you land and every hit you take adds a stack, up to {RAGE["Max"]}. Each stack makes your attacks {RAGE["DamagePerStack"]}% stronger. After {RAGE["FadeAfter"]} seconds without a hit, Rage fades by one stack every {RAGE["FadeEvery"]} seconds, and it is gone when combat ends.', None, [], []),
    ('yst1', 'Blood Oath', None, None, [], ['rge1']),
    ('yst2', 'Iron Lungs', None, None, [], ['rge1']),
    ('rge2', 'Heavenfall', f'Your sprinting power attacks with at least {RAGE["Cost"]["Heavenfall"]} Rage tear a burning line through the ground: 80 damage to everyone in it, 4 more per second for 10 seconds, and a stagger. Spends {RAGE["Cost"]["Heavenfall"]} Rage.', None, [], ['yst1']),
    ('yst3', 'Tempered Steel', None, None, [], ['rge2']),
    ('rge3', 'Shadow Carve', f'Your forward power attacks with at least {RAGE["Cost"]["Shadow Carve"]} Rage send a wave of darkness in a straight line: 40 damage, and 20 more to targets further away. Spends {RAGE["Cost"]["Shadow Carve"]} Rage.', None, [], ['rge2']),
    ('rge4', 'Dark Deluge', f'Your backward power attacks with at least {RAGE["Cost"]["Dark Deluge"]} Rage pierce the target for 40 damage and lower its magic resistance by 25% for 30 seconds. Spends {RAGE["Cost"]["Dark Deluge"]} Rage.', None, [], ['rge2']),
    ('rge5', 'Shadowbringer', f'Your standing power attacks with at least {RAGE["Cost"]["Shadowbringer"]} Rage raise a pillar of dark fire: 60 damage, knocking down everyone it strikes. Spends {RAGE["Cost"]["Shadowbringer"]} Rage.', None, [], ['yst1']),
    ('yst4', 'Scarred Hide', None, None, [], ['rge5']),
    ('rge6', 'Bloodletter', f'Your sideways power attacks with at least {RAGE["Cost"]["Bloodletter"]} Rage drain 40 Health from the target into you. Spends {RAGE["Cost"]["Bloodletter"]} Rage.', None, [], ['rge5']),
    ('yst5', 'Bloodthirst', None, None, [], ['rge6']),
    ('rge7', 'Soulrender', f'Your sideways power attacks with at least {RAGE["Cost"]["Soulrender"]} Rage drain 40 Mana and 40 Stamina from the target into you. With Bloodletter, one hit does both for one cost. Spends {RAGE["Cost"]["Soulrender"]} Rage.', None, [], ['rge5']),
    ('rge8', 'Untempered', f'Your Rage can reach {RAGE["MaxUntempered"]} stacks, and fades half as fast.', None, [], ['rge3', 'rge6']),
    ('yst6', 'Unending Fury', None, None, [], ['rge8']),
    ('rge9', 'Vehemence', f'When your Rage reaches its peak you enter Vehemence for {RAGE["VehemenceSeconds"]} seconds: your power attacks cost no Stamina, and their Rage actions spend no Rage. When it ends, your Rage is spent.', None, [], ['yst6']),
  ]),
  # Druid (2026-10-27, curator's design): Triumvirate's Druid and Shaman spells, granted by the menu (DRUID_GRANTS),
  # Druidcraft as our copy with a heal, Force of Nature a fever-priced power that also brings the familiars
  # (write_druid). Its shape is not weave_stats' - three branches, the totems a three-talent chain - so its stat
  # talents are written here and filled in from HAND_STATS. Allocated after every older block (DRUID_FIRST_ID).
  # Abyssal Wind (the third branch) waits for its spell pack; it will be appended last.
  ('Druidic', 'Roots, totems and the wild.', [
    ('dru1', 'Druidcraft', f'Grants the "Druidcraft" spell: cast it on a corpse and nature reclaims it, growing a plant you can harvest, and you heal {DRUID["CraftHeal"]} Health and gather a Goodberry.', None, [], []),
    ('vst1', 'Green Wellspring', None, None, [], ['dru1']),
    ('vst2', 'Barkskin', None, None, [], ['dru1']),
    # The Hunt (curator 2026-10-29) replaced Parasitic Growth on dru2 (its perk ID stays; a save that bought dru2 keeps
    # the spell it was given then): a power that spends Goodberries to call Triumvirate's Gray Wolf (write_hunt)
    ('dru2', 'The Hunt', f'Grants "The Hunt" power: spend {HUNT["Berries"]} Goodberries to call a Gray Wolf to your side. It stays until it is killed.', None, [], ['vst1']),
    # Wolf Pack (2026-10-29): a branch off The Hunt, allocated last (DRUID_LATE_NODES_2)
    ('dru9', 'Wolf Pack', 'The Hunt calls two Gray Wolves instead of one.', None, [], ['dru2']),
    ('vst3', 'Sap of Life', None, None, [], ['dru2']),
    ('dru3', 'Bramble Growth', 'Grants the "Bramble Growth" spell: a bed of brambles that deals 10 bleed and poison damage for 15 seconds. A target that dies on it sprouts a Goodberry.', None, [], ['dru2']),
    # Twister (2026-10-27): the third branch, Abyssal Wind Magic's spell (Aero.esl, which Prophecy masters). Added after
    # the tree's first build, so allocated last (DRUID_LATE_NODES). A dead end: the menu holds two parents at most.
    ('dru8', 'Twister', f'Grants the "Twister" spell ({TWISTER_COST} Mana): a column of deadly wind that deals 40 damage per second for 10 seconds and staggers those caught in it.', None, [], ['vst1']),
    ('dru4', 'Water Totem', 'Grants the "Create Water Totem" spell: a totem stands for 60 seconds, heals 5 Health and Mana per second and cures disease. An Elementalism spell.', None, [], ['vst1']),
    ('vst4', 'Deep Roots', None, None, [], ['dru4']),
    ('dru5', 'Tree Totem', 'Grants the "Create Tree Totem" spell: a totem stands for 60 seconds and deals 10 poison damage per second to nearby enemies in combat. An Elementalism spell.', None, [], ['dru4']),
    ('vst5', 'Thornhide', None, None, [], ['dru5']),
    # Nature's Way (2026-10-29): a branch off the totems, allocated last (DRUID_LATE_NODES_2)
    ('dru10', "Nature's Way", 'You can have one more totem standing at a time.', None, [], ['dru5']),
    ('dru6', 'Earth Totem', 'Grants the "Create Earth Totem" spell: a totem stands for 60 seconds and casts tremors that deal 120 damage every 7 seconds in combat. An Elementalism spell.', None, [], ['dru5']),
    ('vst6', 'Heart of the Grove', None, None, [], ['dru3', 'dru6']),
    ('dru7', 'Force of Nature', f'Grants the "Force of Nature" power (no Mana, {DRUID["FormFever"]}% Arcane Fever): for {DRUID["FormSeconds"]} seconds you take the form of a Horned Lord, whose power attacks steal Mana, and a raven, a snow leopard and two rattlesnakes fight at your side until they are killed or the form ends. It cannot be used when the fever would reach 100%.', None, [], ['vst6']),
  ]),
  # Arcane Archery (2026-10-23, curator's design): hand-built but Lion's Arrow (Ordinator's, its own description).
  # Every record of this tree - its perks, write_arcane's records and Lion's Arrow's copied closure - is allocated
  # AFTER all older blocks (ARCANE), so adding it renumbered nothing in existing saves.
  ('Arcane Archery', 'Arrows, wards and spellcraft.', [
    ('arc1', 'Arcane Arsenal', f'Grants the "Arcane Arsenal" power: choose Fire, Frost or Lightning, and your bow hits deal {ARC["ElementDamage"]} extra damage of that element.', None, [], []),
    ('arc2', 'No Distractions', 'While you aim a bow, a Spell Ward (Rank II) surrounds you. It fades when you fire or lower the bow.', None, [], ['arc1']),
    ('arc3', 'Ice Shot', f'Grants the "Ice Shot" talent ({ARC["IceCooldown"]} seconds cooldown): with a bow equipped, add {ARC["IceArrows"]} ice arrows to your quiver. They deal {ARC["IceDamage"]} frost damage and freeze a weak target - no higher level than you, never a unique foe - solid for {ARC["FreezeSeconds"]} seconds, and your next arrow shatters it.', None, [], ['arc1']),
    ('arc4', "Andrasta's Owl", f'Your bow hits send a barn owl to attack the target. It fights at your side until it is killed, each later hit sends it after that target, and each of its strikes drains {ARC["OwlDrain"]} Magicka from its target and gives it to you. While it is out, you regenerate {ARC["OwlRegen"]} Magicka per second. Only one owl can be out at a time.', None, [], ['arc2', 'arc3']),
    ('arc5', 'Arcane Echo', 'Grants the "Arcane Echo" power: use it while dual casting a spell to store that spell. Your fully drawn bow shots in combat then also release the stored spell toward your crosshair. Only works with spells cast at others.', o('010258'), [], ['arc4']),  # Ordinator's Lion's Arrow, renamed (curator 2026-10-23)
  ]),
  # Necromancy (2026-10-23, curator's design): all hand-built - see write_necro. Allocated after every older block
  # (NECRO), so adding it renumbered nothing. The Dead Don't Forget improves A Willing Sacrifice, so only it unlocks it.
  ('Necromancy', 'Summons, sacrifice and the restless dead.', [
    ('nec1', 'Corpse Fever', f'You can command one more summon for every {NEC["FeverStep"]}% Arcane Fever you have.', None, [], []),
    ('nec2', 'Dark Effigy', f'Grants the "Dark Effigy" spell ({NEC["EffigyCost"]} Magicka): raise a dark totem for {NEC["EffigySeconds"]} seconds. You and your undead summons near it heal {NEC["EffigyHeal"]} Health per second, and you and your allies near it gain {NEC["EffigyArmor"]} armor.', None, [], ['nec1']),
    ('nec3', 'A Willing Sacrifice', f'Grants the "A Willing Sacrifice" power: every summon you command explodes, dealing damage equal to half its maximum Health to each enemy within 14 feet of it. Usable once every {NEC["SacrificeCooldown"]} seconds.', None, [], ['nec1']),
    ('nec4', "The Dead Don't Forget", f'A Willing Sacrifice restores {NEC["DeadMagicka"]} Magicka for every enemy it hits.', None, [], ['nec3']),
    ('nec5', 'Legion of the Damned', f'Grants the "Legion of the Damned" power: at the cost of {NEC["LegionFever"]}% Arcane Fever, raise six skeletons (two warriors, two archers and two mages) that fight at your side for {NEC["LegionSeconds"] // 60} minutes. They do not count against your summon limit, and A Willing Sacrifice can explode them. A new Legion replaces the old one.', None, [], ['nec4']),
  ]),
  # Sorcerer (2026-10-27, curator's design): Kittytails' Obscure Magic, Elemental Mastery Magic and Constellation Magic,
  # installed and mastered (src/KittytailsPacksClean), their spells granted by the menu and renamed for Enderal
  # (SORC_SPELLS, write_sorcerer). Since 2026-10-28 four nodes are Shatterveil's (installed and mastered): Bursting
  # Effigy (sor1, was Arcane Brand) climbs its tiers with Psionics (SHVL_TIERS), Orbit Ward (sor2, was Rimefire, then
  # Twin Effigies) rises while the player casts (ORBIT_WARD), Blink Step (sor6, was Star Prison) and the Veil Wyrm
  # shout as the capstone (sor9, was Mana Burn). Shaped by
  # hand (HAND_STATS); allocated after Druid (SORC_FIRST_ID). Between Necromancy and Faith on the map.
  ('Sorcery', 'Elements, stars and raw arcane might.', [
    ('sor1', 'Blink Step', f'Grants the "Blink Step" lesser power ({BLINK_MANA} Mana): you shatter like glass and re-form up to 33 feet ahead.', None, [], []),
    ('cst1', 'Arcane Study', None, None, [], ['sor1']),
    ('cst2', 'Mana Font', None, None, [], ['sor1']),
    ('sor2', 'Orbit Ward', 'While you cast a spell, five glass wards orbit you. Each absorbs one whole weapon, arrow or claw hit, then breaks. They fall away when you stop casting.', None, [], ['cst1']),
    ('cst3', 'Ember Ward', None, None, [], ['sor2']),
    ('sor3', 'Frost Spires', f'Grants the "Frost Spires" spell: spires of ice burst from the ground, dealing {SORC_MAG['Spires']} damage to Health and Stamina - up to four times that the more spires strike - and staggering.', None, [], ['sor2']),
    ('cst4', 'Rime Ward', None, None, [], ['sor3']),
    ('sor10', 'Drowning Orb', f'Grants the "Drowning Orb" spell: a 15-foot sphere of water slows everyone inside it and drains {SORC_MAG['OrbSapPerSecond']} Stamina and Mana per second. Each enemy inside it gives you {SORC["OrbDrain"]} of its Mana per second, and you restore {SORC["OrbRegen"]} Mana per second while you stand in it. An Elementalism spell: water is frost, so Elementalist talents strengthen it.', None, [], ['sor3']),
    ('sor4', 'Wildfire', f'Grants the "Wildfire" spell: a bolt of flame strikes for {SORC_MAG["WildfireHit"]} damage and leaves a fire that chases your targets for 10 seconds, burning {SORC_MAG["WildfireBurn"]} damage each time it catches them.', None, [], ['sor2']),
    ('sor5', 'Starlance', f'Grants the "Starlance" spell: beams of pure Mana fall from the night sky on a single target for {SORC_MAG["Starlance"]} damage.', None, [], ['cst1']),
    ('cst5', 'Storm Ward', None, None, [], ['sor5']),
    ('sor6', 'Twin Effigies', f'Grants the "Twin Effigies" spell: two copies of you, one on each side, draw your enemies\' attacks for 30 seconds and hurl chain lightning at them every {EFFIGY_EVERY:g} seconds, 40 damage a bolt. Each shatters after taking a third of your Health in damage. They grow with your Psionics: at 50 they last 40 seconds and take almost half your Health, at 75 50 seconds and two thirds, at 100 a full minute and more than your whole Health.', None, [], ['sor5']),
    ('sor7', 'Gravity Well', f'Grants the "Gravity Well" spell: a well of gravity pulls nearby enemies into it and staggers them, and drains {GW_ABSORB} Health from each into you.', None, [], ['sor5']),
    ('sor8', 'Falling Star', 'Grants the "Falling Star" spell: a falling star strikes for 60 damage and staggers; a target with more Mana than Health also loses Mana.', None, [], ['sor3', 'sor6']),
    ('cst6', 'Arcane Tide', None, None, [], ['sor8']),
    ('sor9', 'Veil Wyrm', f'Grants the "Veil Wyrm" shout, all three words: a wyrm of glass forms over your shoulder and roars. Its shockwaves cut and stagger every enemy around you and slow time; two words bring a Veilblade - a copy of you with your weapons - out of the burst to fight for you, three words two of them and throw your enemies back, and you vanish in the shards for 10 seconds. Then blue flames of Mana burn around you for {SORC["BurnSeconds"]} seconds: your spells cost half as much Mana and you restore {SORC["RegenPerSecond"]} Mana per second. One word recovers in {20 * WYRM_COOLDOWN_MULT} seconds, two in {35 * WYRM_COOLDOWN_MULT}, three in {50 * WYRM_COOLDOWN_MULT}.', None, [], ['cst6']),
  ]),
]

# Stat talents (curator 2026-10-25, after Subclasses of Skyrim 2's stat nodes): six per tree, each one constant ability.
# W1 sits between the root and both branches (they now need it), W2 between the last talent and the capstone, and
# the four side talents hang off one talent each. Woven into TREES below, so the menu arrays list them in place;
# their FormIDs are allocated after every other block (STAT_FIRST_ID), so nothing older is renumbered.
# kind -> (effects, description). '@' = one of our two regen MGEFs (STAT_RATE_MGEFS). Regen magnitudes follow SureAI's
# convention: points on the 100-scale *RateMult read as "percent" (Mental Master: MagickaRateMult +10 = "10 percent
# faster") although the player's Health/Mana mults sit at 1/10 (_00E_Game_AbHealRateDamageFull 01DA25 on Player).
STAT_FX = {
    'health': (['0A1A3F'], 'Your maximum Health is increased by {m}.'),               # AbFortifyHealth
    'mana': (['0CDA4B'], 'Your maximum Mana is increased by {m}.'),                     # AbFortifyMagickaHighElf
    'stamina': (['091F77'], 'Your maximum Stamina is increased by {m}.'),               # AbFortifyStamina
    'staminarate': (['105F21'], 'Your Stamina regenerates {m} percent faster.'),       # AbFortifyStaminaRate
    'healrate': (['@healrate'], 'Your Health regenerates {m} percent faster.'),
    'manarate': (['@manarate'], 'Your Mana regenerates {m} percent faster.'),
    'armor': (['0CAB90'], 'Your armor rating is increased by {m}.'),                    # AbResistDamage
    'resmagic': (['053124'], 'You gain {m}% resistance to magic.'),                     # AbResistMagic
    'resfrost': (['024315'], 'You gain {m}% resistance to frost.'),                     # AbResistFrost
    'resshock': (['024318'], 'You gain {m}% resistance to lightning.'),                 # AbResistShock
    'respoison': (['0AA024'], 'You gain {m}% resistance to poison.'),                   # AbResistPoison
    'carry': (['10CED9'], 'Your carry weight is increased by {m}.'),                    # AbFortifyCarryWeight
    'unarmed': (['0424E2'], 'Your unarmed attacks deal {m} more damage.'),              # AbFortifyUnarmedDamage
    'melee': (['023166', '023167'], 'Your One-handed and Two-handed skills are increased by {m}.'),
    'light': (['023162'], 'Your Light Magic skill is increased by {m}.'),
    'archery': (['023163'], 'Your Marksman skill is increased by {m}.'),
    'handicraft': (['0438F4'], 'Your Handicraft skill is increased by {m}.'),
    'block': (['03E15B'], 'Your Blocking skill is increased by {m}.'),
    'entropy': (['023165'], 'Your Entropy skill is increased by {m}.'),
    'sneak': (['02E1C6'], 'Your Sneak skill is increased by {m}.'),                     # AbFortifySneak
    'psionics': (['02E1C5'], 'Your Psionics skill is increased by {m}.'),               # AbFortifyIllusion
    'elementalism': (['02E1C4'], 'Your Elementalism skill is increased by {m}.'),       # AbFortifyDestruction
    'resfire': (['024314'], 'You gain {m}% resistance to fire.'),                       # AbResistFire
    'onehanded': (['023166'], 'Your One-handed skill is increased by {m}.'),            # AbFortifyOneHanded
}
# (key, EditorID, name, actor value) - copies of AbFortifyStaminaRate 105F21 on the other two rate multipliers
STAT_RATE_MGEFS = [('healrate', 'ZP_Prophecy_FortifyHealRate', 'Fortify Health Regeneration', 'HealRateMult'),
                   ('manarate', 'ZP_Prophecy_FortifyManaRate', 'Fortify Mana Regeneration', 'MagickaRateMult')]
# tree -> (W1, [side talents with their parent], W2); a talent = (id, name, kind, magnitude[, parent])
STAT_NODES = {
    'Faith': (('fst1', 'Devotion', 'light', 10),
              [('fst2', 'Inner Light', 'mana', 25, 'faith1'), ('fst3', 'Blessed Vigour', 'health', 25, 'faith2'),
               ('fst4', 'Mending Grace', 'healrate', 25, 'faith3'), ('fst5', 'Serenity', 'manarate', 10, 'faith5')],
              ('fst6', 'Warding Faith', 'resmagic', 10)),
    'Firearms': (('gst1', 'Steady Aim', 'archery', 10),
              [('gst2', 'Powder Lungs', 'stamina', 25, 'gun1'), ('gst3', 'Quick Breath', 'staminarate', 25, 'gun2'),
               ('gst4', 'Leather Duster', 'armor', 40, 'gun3'), ('gst5', 'Bandolier', 'carry', 25, 'gun4')],
              ('gst6', 'Hardened Nerves', 'health', 25)),
    'Gadgets': (('dst1', 'Tinkerer', 'handicraft', 10),
              [('dst2', 'Toolbelt', 'carry', 30, 'gad1'), ('dst3', 'Fume Mask', 'respoison', 15, 'gad2'),
               ('dst4', 'Riveted Plating', 'armor', 40, 'gad3'), ('dst5', 'Insulated Gloves', 'resshock', 15, 'gad4')],
              ('dst6', 'Steady Hands', 'stamina', 25)),
    # Shadow's (2026-10-27): Mana and stealth (curator)
    'Shadow': (('sst1', 'Silent Step', 'sneak', 10),
              [('sst2', 'Dark Reservoir', 'mana', 25, 'shd1'), ('sst3', 'Soul Siphon', 'manarate', 10, 'shd2'),
               ('sst4', 'Umbral Edge', 'onehanded', 10, 'shd3'), ('sst5', 'Whispering Mind', 'psionics', 10, 'shd4')],
              ('sst6', 'Unseen', 'sneak', 10)),
    'Martial Arts': (('mst1', 'Conditioning', 'stamina', 25),
              [('mst2', 'Iron Knuckles', 'unarmed', 5, 'ma1'), ('mst3', 'Breath Control', 'staminarate', 25, 'ma2'),
               ('mst4', 'Toughened Body', 'armor', 40, 'ma3'), ('mst5', 'Unbroken', 'health', 25, 'ma4')],
              ('mst6', 'Inner Calm', 'resmagic', 10)),
    'Glory': (('lst1', 'Battle-Hardened', 'health', 25),
              [('lst2', 'Shield Discipline', 'block', 10, 'glo1'), ('lst3', 'Thick Hide', 'armor', 60, 'glo2'),
               ('lst4', 'War Cry', 'stamina', 25, 'glo3'), ('lst5', 'Veteran', 'melee', 10, 'glo5')],
              ('lst6', 'Iron Constitution', 'healrate', 25)),
    'Arcane Archery': (('ast1', 'Arcane Focus', 'mana', 25),
              [('ast2', "Fletcher's Eye", 'archery', 10, 'arc1'), ('ast3', 'Mana Spring', 'manarate', 10, 'arc2'),
               ('ast4', 'Frostbound', 'resfrost', 15, 'arc3'), ('ast5', "Owl's Vigil", 'stamina', 25, 'arc4')],
              ('ast6', 'Spellward', 'resmagic', 10)),
    'Necromancy': (('nst1', 'Dark Studies', 'entropy', 10),
              [('nst2', 'Grave Pact', 'mana', 25, 'nec1'), ('nst3', 'Corpse Ward', 'respoison', 15, 'nec2'),
               ('nst4', "Death's Patience", 'manarate', 10, 'nec3'), ('nst5', 'Cold Blood', 'resfrost', 15, 'nec4')],
              ('nst6', 'Bone Armour', 'armor', 40)),
}
# Stat talents placed by hand in TREES (a tree whose shape weave_stats cannot make): id -> (kind, magnitude); the
# tree's W2 (the one before its capstone) is listed in HAND_W2. Druid's (2026-10-27): Mana, armor and regeneration.
HAND_STATS = {'Druidic': {'vst1': ('manarate', 10), 'vst2': ('armor', 40), 'vst3': ('healrate', 25),
                        'vst4': ('mana', 25), 'vst5': ('armor', 40), 'vst6': ('mana', 25)},
              'Sorcery': {'cst1': ('elementalism', 10), 'cst2': ('mana', 75), 'cst3': ('resfire', 15),   # Mana Font 25 -> 75 (curator 2026-10-28)
                           'cst4': ('resfrost', 15), 'cst5': ('resshock', 15), 'cst6': ('manarate', 10)},
              'Rage': {'yst1': ('health', 25), 'yst2': ('stamina', 25), 'yst3': ('melee', 10),
                       'yst4': ('armor', 40), 'yst5': ('healrate', 25), 'yst6': ('staminarate', 25)}}
HAND_W2 = {'vst6', 'cst6', 'yst6'}
STAT_FIRST_ID = 0x9C4
FAITH_CAPSTONE = {'Faith': 'faith4'}     # the 2026-10-25 rework: Templar (faith5) is the merge talent now
CAPSTONE_LEVEL = 30
SHADOW_LATE_NODES = ('shd6',)            # Shade Veil (2026-10-28): allocated after Shatterveil's records
SHADOW_LATE_NODES_2 = ('shd7',)          # Darkness (2026-10-28): allocated after the Darkness meter's records
SHADOW_LATE = SHADOW_LATE_NODES + SHADOW_LATE_NODES_2
MARTIAL_LATE_NODES = ('ma6',)
FIREARMS_LATE_NODES = ('gun6',)          # Ricochet Rounds (2026-10-29): allocated after The Hunt's records            # Dragon's Breath (2026-10-28): allocated after Nightblade's records
LATE_NODES = ('gad6',)                   # talents added after the stat talents: allocated after the Faith records                      # every capstone needs this player level (curator 2026-10-25; ZP_ProphecyMenu.LevelReq)
STAT = {}                          # node id -> (kind, magnitude)


def weave_stats():
    """Insert STAT_NODES into TREES: W1 after the root (the root's children now need W1), W2 before the capstone
    (the last node; it now needs W2, which needs what the capstone needed), each side talent after its parent."""
    for k, (tree, desc, ns) in enumerate(TREES):
        if tree in HAND_STATS:                       # already in place: only their descriptions to fill in
            hs = HAND_STATS[tree]
            assert {n[0] for n in ns if n[2] is None} == set(hs), (tree, 'hand stat talents')
            TREES[k] = (tree, desc, [(n[0], n[1], STAT_FX[hs[n[0]][0]][1].format(m=hs[n[0]][1]), *n[3:])
                                     if n[0] in hs else n for n in ns])
            STAT.update(hs)
            continue
        (w1, sides, w2) = STAT_NODES[tree]
        ns = list(ns)
        root, capid = ns[0][0], FAITH_CAPSTONE.get(tree, ns[-1][0])
        stat = lambda s, parents: (s[0], s[1], STAT_FX[s[2]][1].format(m=s[3]), None, [], parents)
        kids = [i for i, n in enumerate(ns) if n[5] == [root]]
        assert len(kids) == 2, (tree, 'root should have two children', kids)
        for i in kids: ns[i] = ns[i][:5] + ([w1[0]],)
        ns.insert(1, stat(w1, [root]))
        ci = next(i for i, n in enumerate(ns) if n[0] == capid)
        cap = ns[ci]
        ns[ci] = cap[:5] + ([w2[0]],)
        ns.insert(ci, stat(w2, list(cap[5])))
        for s in sides:
            after = w1[0] if s[4] == root else s[4]          # a side talent off the root reads after W1
            at = next(i for i, n in enumerate(ns) if n[0] == after)
            ns.insert(at + 1, stat(s, [s[4]]))
        for s in [w1, w2] + sides: STAT[s[0]] = (s[2], s[3])
        assert len(ns) == 11 + sum(1 for n in ns if n[0] in LATE_NODES + SHADOW_LATE + MARTIAL_LATE_NODES + FIREARMS_LATE_NODES), (tree, len(ns))
        TREES[k] = (tree, desc, ns)


weave_stats()



# ------------------------------------------------------------------------------------------------ Holy Templar Magic
# Kittytails' Holy Templar Magic (Lightpower.esl; the curator has her permission to convert the spells, 2026-10-25).
# Its six player spells and their 73-record closure are copied in from reference/mods/HolyTemplarMagic and allocated
# after everything else (HOLY_FIRST_ID). Left out: the 6 tomes and both injector quests (their 6 vanilla leveled lists
# do not exist in Enderal), the author's test cell (Dawnguard 001DBA) and the NPC/SPID variants (their factions do not
# exist). Loose assets come from reference/mods/_raw/HolyTemplarMagic (a copy of the mod folder). Triage and balance:
# arch-docs/patches/Prophecy.md, "Holy Templar Magic".
HTM = 'Lightpower.esl'
HTM_DIR = os.path.join(REF, 'mods', 'HolyTemplarMagic')
HTM_RAW = os.path.join(REF, 'mods', '_raw', 'HolyTemplarMagic')
HOLY_WARD_1ST = 'HolyShield_1st.nif'     # Righteous Path's first-person ward model (copy_holy_assets)
# the flat shapes left out of it: the white disc, then (2026-10-26, "a smaller strip in the middle") the glow-spot disc,
# both a thin bright sheet edge-on at first person's close angle; only the particles stay in first person
HOLY_WARD_1ST_DROP = ('HolyShield:0', 'HolyShield:1')
htm = lambda x: f'{x}:{HTM}'
HOLY_SEEDS = [htm('000826'), htm('000824'), htm('000820'), htm('000822'), htm('000825'), htm('000829')]
HOLY_FIRST_ID = 0xA1A
# Dawnguard/Dragonborn forms (empty stubs in Enderal) -> the list's holy look (Kata's Holy Cross: MAGINVTurnUndead,
# TurnUnFXShader) and Enderal's Restoration hand art/sounds; None drops the line (ISMs: no screen flashes; DLC races
# on the shield's ARMA)
HOLY_SUBST = {
    '00F64A:Dawnguard.esm': '01C859:Skyrim.esm',   # casting art -> Heal01HandEffects
    '018F02:Dawnguard.esm': '1097CA:Skyrim.esm',   # menu display object -> MAGINVTurnUndead
    '019C9D:Dawnguard.esm': '04C6D8:Skyrim.esm',   # hit shaders -> TurnUnFXShader
    '00A3BB:Dawnguard.esm': '04C6D8:Skyrim.esm',
    '019C9E:Dawnguard.esm': '04C6D8:Skyrim.esm',   # magiceffectshaderapply's EffectShaderFX
    '00D9AE:Dawnguard.esm': '01C2AF:Skyrim.esm',   # impact data set -> MAGFirebolt01ImpactSet
    '00D94A:Dawnguard.esm': '056622:Skyrim.esm',   # charge sound -> MAGRestorationChargeSD
    '019956:Dawnguard.esm': '02518F:Skyrim.esm',   # far sky-bolt boom -> MAGDestructionFireballExplosionDistant
    '00A3BE:Dawnguard.esm': None, '00AE9D:Dawnguard.esm': None,
    '00E88A:Dawnguard.esm': None, '00377D:Dawnguard.esm': None, '03CA97:Dragonborn.esm': None,
}
# Prices on the list's cost ladder (EGO's medians, src/MagicPatches/tools/*-cost-table.json: FF 30/53.5/76.5/97/124
# by tier, Concentration 7/16/28/37/43 per second); Wrath of the Heavens is a 60 s buff, priced between the master
# rung and Holy Aura (Rank III), 258 for its 60 s cloak.
HOLY_COST = {htm('000826'): 30, htm('000824'): 18, htm('000820'): 76, htm('000822'): 97, htm('000825'): 124,
             htm('000829'): 0}     # Wrath of the Lightborn: Arcane Fever only, no Mana (curator 2026-10-25)
# (spell, effect, field, old, new). Damage sits next to Enderal's own holy line at the same tier (Holy Ray, Holy
# Cross, Holy Sun Burst; arch-docs/magic/data/spells.json); the mod's "undead take double damage" is kept.
HOLY_EDITS = [
    ('000826', '000816', 'Magnitude', '60', '30'),    # Consecrate Dead: restores 30 Health/Mana/Stamina (was 60)
    ('000826', '000817', 'Magnitude', '8', '15'),     # ... and undead in it take 15
    ('000827', '000818', 'Magnitude', '60', '30'),    # Blessing, the heal it casts
    ('000827', '000819', 'Magnitude', '60', '30'),
    ('000824', '000810', 'Magnitude', '20', '12'),    # Sun Shards 12/s (Holy Ray III at skill 25: 11.3)
    ('000824', '000811', 'Magnitude', '20', '12'),
    ('000820', '000804', 'Magnitude', '10', '20'),    # Sunlight Targe: its beam's damage (description)
    ('000863', '000860', 'Magnitude', '8', '20'),     # ... the Reflector Beam itself
    ('000822', '000814', 'Magnitude', '80', '40'),    # Hallowed Flare (description)
    ('000823', '000812', 'Magnitude', '80', '40'),    # each sky-bolt's centre, shared with Wrath of the Heavens
    ('000823', '000813', 'Magnitude', '80', '40'),
    ('00081F', '000802', 'Magnitude', '40', '10'),    # each scattered beam (9 per Flare bolt, 6 per Wrath bolt)
    ('00081F', '000803', 'Magnitude', '40', '10'),
    ('000821', '000805', 'Magnitude', '8', '6'),      # Sanctuary's rising damage per second, x0.75
    ('000821', '000806', 'Magnitude', '12', '9'),
    ('000821', '000807', 'Magnitude', '16', '12'),
    ('000821', '000808', 'Magnitude', '20', '15'),
    ('000821', '000809', 'Magnitude', '24', '18'),
    ('000821', '00080A', 'Magnitude', '8', '6'),
    ('000821', '00080B', 'Magnitude', '16', '12'),
    ('000821', '00080C', 'Magnitude', '24', '18'),
    ('000829', '00081A', 'Magnitude', '80', '40'),    # Wrath of the Heavens (description): 60 s, not 120
    ('000829', '00081A', 'Duration', '120', '60'),
    ('000829', '00081B', 'Duration', '120', '60'),
    ('000829', '00081B', 'Magnitude', '45', '20'),    # its cloak's reach in feet (no sniping across the map)
]
# The Faith rework's names (curator 2026-10-25), on every display string of the copied records
HOLY_RENAME = [('Hallowed Flare', 'Smite'), ('Sunlight Targe', 'Righteous Path'),
               ('Wrath of the Heavens', 'Wrath of the Lightborn')]
HOLY_WRATH_FEVER = 50     # Arcane Fever per cast; refused at this much fever or more (100% kills)


def holy_closure(hidx):
    """The six player spells and everything of Lightpower.esl they reach, in source-ID order."""
    seen, q = set(), list(HOLY_SEEDS)
    while q:
        fk = q.pop()
        if fk in seen: continue
        assert fk in hidx, f'Holy Templar record {fk} missing from {HTM_DIR}'
        seen.add(fk)
        for a, b in FK.findall(hidx[fk][2]):
            if b == HTM: q.append(f'{a}:{b}')
    assert not any(hidx[fk][0] in ('Books', 'Quests', 'Cells') for fk in seen), 'Holy closure reached tomes/quests'
    return sorted(seen)


GLORY = 'Glory'
ARCANE = 'Arcane Archery'
NECRO = 'Necromancy'
GLORY_FIRST_ID = 0x916
# Glory nodes added after the Glory block was laid out get IDs at the END (after GLORY_RECORDS_5), so nothing that
# existing saves point at moves. glo5 (2026-10-22) = 0x93A: first Death or Glory (power attacks stronger below 75%
# Health), replaced the same day by Surrounded on the same perk, so a save that took one now has the other.
GLORY_LATE_NODES = ('glo5',)
# Surrounded (curator, 2026-10-22): an ability whose script restores Stamina once a second while enough living hostile
# actors stand close. Radius 400 = Seismic Stomp's.
SURROUNDED = {'Radius': 400.0, 'MinEnemies': 3, 'StaminaPerSecond': 2.0}
# Records copied for hand-built nodes (their closures come along)
EXTRA_SEEDS = [s('00084F'),          # Monk - its bleed spell/MGEF become Bleeding Shot's
               o('07B101')]          # ORD_Bck_QuickReflexes_Spell_Self - the slow-time spell Flow State casts
# Plain numeric edits on copied perk effects: (node, EntryPoint, old value, new value)
VALUE_EDITS = [('ma1', 'ModAttackDamage', '0.05', '0.15')]
# Skyrim forms a copied record names that Enderal lacks (or has at that ID as something else). A target
# of None removes the YAML list entry/line carrying the reference; the DUMMY_* are inert records of ours.
DUMMY_QUEST, DUMMY_LOC, DUMMY_SPELL = f'00080A:{MOD}', f'00080B:{MOD}', f'00080C:{MOD}'
SUBST = {
    '0BC0BD:Skyrim.esm': DUMMY_QUEST,          # C00JorrvaskrFight (Iron Fist/Descending Light: "not brawling");
                                               #   in Enderal 0BC0BD is a placed ref
    '01F877:Skyrim.esm': DUMMY_LOC,            # WhiterunJorrvaskrLocation
    '047AE6:Skyrim.esm': '11A493:Skyrim.esm',  # DGIntimidateQuest -> Enderal's own brawl quest
    '064D68:Skyrim.esm': DUMMY_SPELL,          # VoiceMakeEthereal (no shouts in Enderal)
    '01397D:Skyrim.esm': '0800E4:Skyrim.esm',  # Bear Trap recipe's 20x (vanilla-only item) -> Leather Strips
    '09E0C9:Skyrim.esm': None,                 # Hunt Together wolf's faction (wolf never spawns: perk unpicked)
    '0A85C7:Skyrim.esm': None,                 # ... and its InheritsSoundsFrom
    # Lion's Arrow's exclusion list (spells it will not store): four vanilla spells Enderal does not have
    '0211EC:Skyrim.esm': None, '0211ED:Skyrim.esm': None, '0C96A0:Skyrim.esm': None, '0F9615:Skyrim.esm': None,
}
# A node renamed after release keeps its EditorID (the thumbnail file and the menu's Images path follow it).
EDITORID = {'gad1': 'ZP_Prophecy_Tripwire', 'glo5': 'ZP_Prophecy_DeathorGlory', 'arc4': 'ZP_Prophecy_SendaRaven',
            'arc5': 'ZP_Prophecy_LionsArrow',   # gad3 follows its name: ZP_Prophecy_UtilityDroid
            # the curator's thumbnail names
            'nec3': 'ZP_Prophecy_WillingSacrifice', 'nec4': 'ZP_Prophecy_DeadDontForget', 'nec5': 'ZP_Prophecy_LegionDamned'}
# Exact display strings renamed on the copied records (the power, its effect, the wire, its quest).
RENAME = {'Tripwire': 'Explosive Tripwire'}


def perk_edid(node):
    return EDITORID.get(node[0], 'ZP_Prophecy_' + re.sub(r'\W', '', node[1]))


LORE = [('Dwemer Autocannon', 'Clockwork Turret'), ('Dwarven Autocannon', 'Clockwork Turret'),
        ('Dwemer', 'Clockwork'), ('Dwarven', 'Clockwork'), ('Skyrim', 'Vyn'), ('Light Armor experience', 'nothing'),
        ("Lion's Arrow", 'Arcane Echo')]   # Arcane Archery 5 (curator 2026-10-23): the perk, its power and effects


def ed(t):
    m = re.search(r'^EditorID: (.+?)\s*$', t, re.M); return m.group(1) if m else None


def enderal_formkeys():
    have = {f'000014:Skyrim.esm', '000007:Skyrim.esm'}
    for d, mk in [('base/Skyrim', 'Skyrim.esm'), ('base/Update', 'Update.esm'), ('base/EnderalFS', None), ('mods/EGO', None)]:
        for root, _, fs in os.walk(os.path.join(REF, d)):
            for f in fs:
                m = re.search(r' - ([0-9A-F]{6})_(.+?\.es[mp])\.yaml$', f)
                if m: have.add(f'{m.group(1)}:{m.group(2)}')
    return have


def main():
    idx = {p: index(SRC[p]) for p in SRC}
    rec = {}
    for p in idx: rec.update(idx[p])           # FormKey -> (type, path, text); vanilla-ID Ordinator records included
    def owner(fk):
        for p in idx:
            if fk in idx[p]: return p
    # --- closure over source records (stop at perks: perks are only copied when picked)
    nodes = {n[0]: n for _, _, ns in TREES for n in ns}
    arc_nids = [n[0] for t, _, ns in TREES if t == ARCANE for n in ns if n[0] not in STAT]
    nec_nids = [n[0] for t, _, ns in TREES if t == NECRO for n in ns if n[0] not in STAT]
    shadow_all = [n[0] for t, _, ns in TREES if t == SHADOW for n in ns if n[0] not in SHADOW_LATE]   # its stat talents too: its own block
    druid_all = [n[0] for t, _, ns in TREES if t == DRUID_TREE for n in ns if n[0] not in DRUID_LATE_NODES + DRUID_LATE_NODES_2]   # likewise
    sorc_all = [n[0] for t, _, ns in TREES if t == SORC_TREE for n in ns]
    rage_all = [n[0] for t, _, ns in TREES if t == RAGE_TREE for n in ns]
    picked = {n[3]: n[0] for n in nodes.values() if n[3]}
    alias = {a: nid for nid, n in nodes.items() for a in n[4]}
    # the older trees close over exactly the seeds they always had (same order, same IDs); Arcane Archery's own
    # closure is a second pass below, allocated last
    old_picked = {fk: nid for fk, nid in picked.items() if nid not in arc_nids}
    seeds = list(old_picked) + list(alias) + EXTRA_SEEDS
    copy, q = [], list(seeds)
    while q:
        fk = q.pop()
        if fk in copy: continue
        assert fk in rec, f'seed/ref {fk} not in any source tree'
        copy.append(fk)
        ty, _, t = rec[fk]
        for h, f in FK.findall(t):
            r = f'{h}:{f}'
            if r in rec and r not in copy and (rec[r][0] != 'Perks' or r in old_picked or r in alias):
                q.append(r)
    # COBJ recipes that unlock on a picked perk (Bear Traps, the turret) - reverse refs
    for fk, (ty, _, t) in rec.items():
        if ty == 'ConstructibleObjects' and any(p in t for p in seeds) and fk not in copy:
            copy.append(fk); q = [fk]
            while q:
                x = q.pop()
                for h, f in FK.findall(rec[x][2]):
                    r = f'{h}:{f}'
                    if r in rec and r not in copy and rec[r][0] != 'Perks': copy.append(r); q.append(r)
    copy = [fk for fk in copy if fk not in alias]          # folded perks contribute effects, not records
    # Scenes that belong to a copied quest, and what they use (Tripwire's kneel: scene 0379A9 runs package 0379A7).
    # Only quest -> scene is a reverse ref, so the forward closure missed them until 2026-10-21 (no placing
    # animation). Allocated after the Glory block, so adding them renumbered nothing.
    late = []
    for fk, (ty, _, t) in rec.items():
        qm = re.search(r'^Quest: (.+?)\s*$', t, re.M)
        if ty == 'Scenes' and qm and qm.group(1) in copy and fk not in copy:
            q = [fk]
            while q:
                x = q.pop()
                if x in copy or x in late: continue
                late.append(x)
                for h, f in FK.findall(rec[x][2]):
                    r = f'{h}:{f}'
                    if r in rec and rec[r][0] != 'Perks': q.append(r)
    # Arcane Archery's closure (Lion's Arrow + the Mage Ward art): only what the older trees did not already copy
    arc_copy = []
    q = [fk for fk, nid in picked.items() if nid in arc_nids] + ARC_SEEDS
    while q:
        fk = q.pop()
        if fk in copy or fk in late or fk in arc_copy: continue
        assert fk in rec, f'seed/ref {fk} not in any source tree'
        arc_copy.append(fk)
        for h, f in FK.findall(rec[fk][2]):
            r = f'{h}:{f}'
            if r in rec and (rec[r][0] != 'Perks' or r in picked or r in alias):
                q.append(r)
    assert not any(rec[fk][0] in ('Scenes', 'ConstructibleObjects') for fk in arc_copy), 'Arcane closure needs scenes/recipes'
    # --- allocate
    newid, nxt = {}, FIRST_ID
    nodeperk = {}
    glory_all = [n[0] for t, _, ns in TREES if t == GLORY for n in ns if n[0] not in STAT]
    glory_nodes = [nid for nid in glory_all if nid not in GLORY_LATE_NODES]
    for nid, n in nodes.items():                         # perks first, in tree order, for readable IDs
        if nid in glory_all or nid in arc_nids or nid in nec_nids or nid in STAT or nid in LATE_NODES or nid in shadow_all or nid in druid_all or nid in DRUID_LATE_NODES or nid in DRUID_LATE_NODES_2 or nid in sorc_all or nid in rage_all or nid in SHADOW_LATE or nid in MARTIAL_LATE_NODES or nid in FIREARMS_LATE_NODES: continue
        if n[3]: newid[n[3]] = f'{nxt:06X}:{MOD}'
        nodeperk[nid] = f'{nxt:06X}:{MOD}'; nxt += 1
    for a, nid in alias.items(): newid[a] = nodeperk[nid]
    for fk in copy:
        if fk not in newid: newid[fk] = f'{nxt:06X}:{MOD}'; nxt += 1
    gunhit = f'{nxt:06X}:{MOD}'; nxt += 1
    flowab, flowme = f'{nxt:06X}:{MOD}', f'{nxt+1:06X}:{MOD}'; nxt += 2
    blast = {k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(('exp', 'mgef', 'glob'))}; nxt += 3
    assert nxt <= GLORY_FIRST_ID, f'older trees grew into the Glory block (next 0x{nxt:03X})'
    nxt = GLORY_FIRST_ID
    for nid in glory_nodes:
        nodeperk[nid] = f'{nxt:06X}:{MOD}'; nxt += 1
    glory = {k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(GLORY_RECORDS)}; nxt += len(GLORY_RECORDS)
    for fk in late:
        newid[fk] = f'{nxt:06X}:{MOD}'; nxt += 1
    copy += late
    glory.update({k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(GLORY_RECORDS_2)}); nxt += len(GLORY_RECORDS_2)
    psound = {}
    for key, *_ in POWER_SOUNDS:                          # 3 records each, in table order (append new ones last)
        psound[key] = {k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(('sound', 'marker', 'mgef'))}; nxt += 3
    glory.update({k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(GLORY_RECORDS_3)}); nxt += len(GLORY_RECORDS_3)
    glory.update({k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(GLORY_RECORDS_4)}); nxt += len(GLORY_RECORDS_4)
    glory.update({k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(GLORY_RECORDS_5)}); nxt += len(GLORY_RECORDS_5)
    for nid in GLORY_LATE_NODES:                          # in order; append new late nodes last
        nodeperk[nid] = f'{nxt:06X}:{MOD}'; nxt += 1
    assert nodeperk['glo5'] == f'00093A:{MOD}', nodeperk['glo5']
    glory.update({k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(GLORY_RECORDS_6)}); nxt += len(GLORY_RECORDS_6)
    nova = {k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(FLOW_NOVA_RECORDS)}; nxt += len(FLOW_NOVA_RECORDS)
    droid = {k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(DROID_RECORDS)}; nxt += len(DROID_RECORDS)
    deadeye = {k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(('sound', 'marker', 'mgef'))}; nxt += 3
    bleedsnd = {k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(('sound', 'marker', 'mgef'))}; nxt += 3
    # Arcane Archery (2026-10-23): its perks, its hand-built records, then Lion's Arrow's copied closure
    for nid in arc_nids:
        nodeperk[nid] = f'{nxt:06X}:{MOD}'; nxt += 1
    for fk, nid in picked.items():
        if nid in arc_nids: newid[fk] = nodeperk[nid]
    assert nodeperk['arc1'] == f'00094E:{MOD}', nodeperk['arc1']
    arc = {k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(ARC_RECORDS)}; nxt += len(ARC_RECORDS)
    for fk in arc_copy:
        if fk not in newid: newid[fk] = f'{nxt:06X}:{MOD}'; nxt += 1
    copy += arc_copy
    sharp = {k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(SHARP_RECORDS)}; nxt += len(SHARP_RECORDS)   # 2026-10-23
    # Necromancy (2026-10-23): its perks, then its hand-built records
    assert nxt == 0x992, f'Necromancy would not start at 0x992 (0x{nxt:03X})'
    for nid in nec_nids:
        nodeperk[nid] = f'{nxt:06X}:{MOD}'; nxt += 1
    nec = {k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(NEC_RECORDS)}; nxt += len(NEC_RECORDS)
    # the thrown Utility Droid (2026-10-23)
    assert nxt == 0x9AA, f'Utility Droid throw would not start at 0x9AA (0x{nxt:03X})'
    droid.update({k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(DROID_THROW_RECORDS)}); nxt += len(DROID_THROW_RECORDS)
    droid.update({k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(DROID_HEAL_RECORDS)}); nxt += len(DROID_HEAL_RECORDS)
    assert droid['healspell'] == f'0009AF:{MOD}', droid['healspell']     # ZP_UtilityDroidEffect looks it up by this ID
    glory['quickreflexes_me'] = newid[f'07B100:{ORD}']     # ORD_Bck_QuickReflexes_Effect_Self
    # the sound when a Prophecy point is gained (2026-10-25)
    assert nxt == 0x9B0, f'point sound would not start at 0x9B0 (0x{nxt:03X})'
    pointsnd = {k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(('sound', 'marker'))}; nxt += 2
    assert pointsnd['marker'] == f'0009B1:{MOD}', pointsnd['marker']   # ZP_ProphecyMenu looks it up by this ID
    # Prophecy v3's selection notes (2026-10-25): one SNDR per note of the curator's piano melody, played in order
    notes = [f'{nxt + i:06X}:{MOD}' for i in range(SELECT_NOTES)]; nxt += SELECT_NOTES
    # the stat talents (2026-10-25): their perks in tree order, then one ability each, then the two regen MGEFs
    assert nxt == STAT_FIRST_ID, f'stat talents would not start at 0x{STAT_FIRST_ID:03X} (0x{nxt:03X})'
    stat_ids = [nid for nid in nodes if nid in STAT and nid not in shadow_all and nid not in druid_all and nid not in sorc_all and nid not in rage_all]
    for nid in stat_ids:
        nodeperk[nid] = f'{nxt:06X}:{MOD}'; nxt += 1
    statab = {}
    for nid in stat_ids:
        statab[nid] = f'{nxt:06X}:{MOD}'; nxt += 1
    ratemgef = {key: f'{nxt + i:06X}:{MOD}' for i, (key, *_) in enumerate(STAT_RATE_MGEFS)}; nxt += len(STAT_RATE_MGEFS)
    # Holy Templar Magic (2026-10-25): its copied closure, in source-ID order
    assert nxt == HOLY_FIRST_ID, f'Holy Templar records would not start at 0x{HOLY_FIRST_ID:03X} (0x{nxt:03X})'
    hidx = index(HTM_DIR)
    hcopy = holy_closure(hidx)
    SUBST.update(HOLY_SUBST)
    for fk in hcopy:
        newid[fk] = f'{nxt:06X}:{MOD}'; nxt += 1
    # the Faith rework (2026-10-25): Righteous Path's ability + its effects, Smite's hit spell + effect
    assert nxt == 0xA63, f'Faith rework records would not start at 0xA63 (0x{nxt:03X})'
    faith = {k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(FAITH_RECORDS)}; nxt += len(FAITH_RECORDS)
    # talents added late (2026-10-26: Chaff), in LATE_NODES order - append new ones last
    assert nxt == 0xA6D, f'late talents would not start at 0xA6D (0x{nxt:03X})'
    for nid in LATE_NODES:
        nodeperk[nid] = f'{nxt:06X}:{MOD}'; nxt += 1
    # Shadow (2026-10-27): its perks in tree order, its stat abilities, then Nightfall's records
    assert nxt == SHADOW_FIRST_ID, f'Shadow would not start at 0x{SHADOW_FIRST_ID:03X} (0x{nxt:03X})'
    for nid in shadow_all:
        nodeperk[nid] = f'{nxt:06X}:{MOD}'; nxt += 1
    for nid in shadow_all:
        if nid in STAT: statab[nid] = f'{nxt:06X}:{MOD}'; nxt += 1
    shadow = {k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(SHADOW_RECORDS)}; nxt += len(SHADOW_RECORDS)
    # Druid (2026-10-27): the same layout
    assert nxt == DRUID_FIRST_ID, f'Druid would not start at 0x{DRUID_FIRST_ID:03X} (0x{nxt:03X})'
    for nid in druid_all:
        nodeperk[nid] = f'{nxt:06X}:{MOD}'; nxt += 1
    for nid in druid_all:
        if nid in STAT: statab[nid] = f'{nxt:06X}:{MOD}'; nxt += 1
    druid = {k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(DRUID_RECORDS)}; nxt += len(DRUID_RECORDS)
    for nid in DRUID_LATE_NODES:                          # talents added to Druid later, in order; append new ones last
        nodeperk[nid] = f'{nxt:06X}:{MOD}'; nxt += 1
    # Sorcerer (2026-10-27): the same layout
    assert nxt == SORC_FIRST_ID, f'Sorcerer would not start at 0x{SORC_FIRST_ID:03X} (0x{nxt:03X})'
    for nid in sorc_all:
        nodeperk[nid] = f'{nxt:06X}:{MOD}'; nxt += 1
    for nid in sorc_all:
        if nid in STAT: statab[nid] = f'{nxt:06X}:{MOD}'; nxt += 1
    sorc = {k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(SORC_RECORDS)}; nxt += len(SORC_RECORDS)
    # Rage (2026-10-27): the same layout
    assert nxt == RAGE_FIRST_ID, f'Rage would not start at 0x{RAGE_FIRST_ID:03X} (0x{nxt:03X})'
    for nid in rage_all:
        nodeperk[nid] = f'{nxt:06X}:{MOD}'; nxt += 1
    for nid in rage_all:
        if nid in STAT: statab[nid] = f'{nxt:06X}:{MOD}'; nxt += 1
    rage = {k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(RAGE_RECORDS)}; nxt += len(RAGE_RECORDS)
    # Sorcery, later (2026-10-27): Mana Burn's and Drowning Orb's Mana restore, and the orb's drain. Append new ones LAST
    assert nxt == SORC_LATE_FIRST_ID, f'Sorcery late records would not start at 0x{SORC_LATE_FIRST_ID:03X} (0x{nxt:03X})'
    sorc.update({k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(SORC_LATE_RECORDS)}); nxt += len(SORC_LATE_RECORDS)
    # Arcane Archery, later (2026-10-28): Ice Shot's shout and word. Append new ones LAST
    arc.update({k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(ICE_LATE_RECORDS)}); nxt += len(ICE_LATE_RECORDS)
    # Sorcery, later (2026-10-28): Shatterveil's tier abilities. Append new ones LAST
    sorc.update({k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(SHVL_LATE_RECORDS)}); nxt += len(SHVL_LATE_RECORDS)
    # Shadow, later (2026-10-28): Shade Veil's perk, then its records. Append new ones LAST
    assert nxt == 0xAE6, f'Shade Veil would not start at 0xAE6 (0x{nxt:03X})'
    for nid in SHADOW_LATE_NODES:
        nodeperk[nid] = f'{nxt:06X}:{MOD}'; nxt += 1
    shadow.update({k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(SHADE_VEIL_RECORDS)}); nxt += len(SHADE_VEIL_RECORDS)
    shadow.update({k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(DARKNESS_RECORDS)}); nxt += len(DARKNESS_RECORDS)
    for nid in SHADOW_LATE_NODES_2:
        nodeperk[nid] = f'{nxt:06X}:{MOD}'; nxt += 1
    shadow.update({k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(DARK_SPELL_RECORDS)}); nxt += len(DARK_SPELL_RECORDS)
    shadow.update({k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(NIGHTBLADE_RECORDS)}); nxt += len(NIGHTBLADE_RECORDS)
    # Martial Arts, later (2026-10-28): Dragon's Breath's perk, then its records. Append new ones LAST
    assert nxt == 0xAF5, f"Dragon's Breath would not start at 0xAF5 (0x{nxt:03X})"
    for nid in MARTIAL_LATE_NODES:
        nodeperk[nid] = f'{nxt:06X}:{MOD}'; nxt += 1
    dragon = {k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(DRAGON_RECORDS)}; nxt += len(DRAGON_RECORDS)
    # Flow State's chain lightning (2026-10-29): one spell on Dragon's Breath's chain lightning effect. Append LAST
    assert nxt == 0xB02, f"Flow State's chain lightning would not start at 0xB02 (0x{nxt:03X})"
    flowchain = f'{nxt:06X}:{MOD}'; nxt += 1
    # Blink Step's swoosh (2026-10-29): its sound, marker and play effect. Append LAST
    sorc.update({k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(BLINK_SWOOSH_RECORDS)}); nxt += len(BLINK_SWOOSH_RECORDS)
    # Druid, later (2026-10-29): Wolf Pack's and Nature's Way's perks, then The Hunt's records. Append LAST
    assert nxt == 0xB06, f"Wolf Pack would not start at 0xB06 (0x{nxt:03X})"
    for nid in DRUID_LATE_NODES_2:
        nodeperk[nid] = f'{nxt:06X}:{MOD}'; nxt += 1
    druid.update({k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(HUNT_RECORDS)}); nxt += len(HUNT_RECORDS)
    # Firearms, later (2026-10-29): Ricochet Rounds' perk (the DLL does the rest). Append LAST
    assert nxt == 0xB0E, f"Ricochet Rounds would not start at 0xB0E (0x{nxt:03X})"
    for nid in FIREARMS_LATE_NODES:
        nodeperk[nid] = f'{nxt:06X}:{MOD}'; nxt += 1
    # The Hunt's howl (2026-10-29): its sound and marker. Append LAST
    assert nxt == 0xB0F, f"The Hunt's howl would not start at 0xB0F (0x{nxt:03X})"
    druid.update({k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(HUNT_HOWL_RECORDS)}); nxt += len(HUNT_HOWL_RECORDS)
    # The Hunt's invisible summon art (2026-10-29). Append LAST
    assert nxt == 0xB11, f"The Hunt's summon art would not start at 0xB11 (0x{nxt:03X})"
    druid.update({k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(HUNT_PORTAL_RECORDS)}); nxt += len(HUNT_PORTAL_RECORDS)

    assert nxt <= 0xFFF, 'out of ESL range'
    have = enderal_formkeys()
    bad = collections.Counter()

    def remap(t, where, vanilla_ok=False):
        def sub(m):
            r = f'{m.group(1)}:{m.group(2)}'
            if r in newid: return newid[r]
            if m.group(2) in (ORD, SOS) or (r in rec and not vanilla_ok):   # vanilla_ok: a base form Ordinator also overrides
                if r in rec and rec[r][0] == 'Perks': return NEVER
                bad[f'{r} (source record not copied) in {where}'] += 1; return r
            if m.group(2) == MOD: return r
            if r in SUBST: return SUBST[r] or '@@DROP@@'
            if r not in have: bad[f'{r} (not in Enderal) in {where}'] += 1
            return r
        t = FK.sub(sub, t)
        # drop whole YAML list items / lines that referenced a SUBST None
        t = re.sub(r'^- [A-Za-z]+: @@DROP@@\n(?:  .*\n)*', '', t, flags=re.M)
        t = re.sub(r'^.*@@DROP@@.*\n', '', t, flags=re.M)
        t = re.sub(r'^\w+:\n(?=[A-Za-z]|\Z)', '', t, flags=re.M)     # a list emptied by the drop
        return t

    # --- wipe generated folders (keep the prototype's hand-written 0x800-0x807 files)
    keep = {f'{i:06X}' for i in range(0x800, 0x808)} | {'000809', '00080D', '00080E'}     # + 809 PointsEarned, 80D ZP_ProphecyMenu, 80E ZP_ProphecyLevelWatch (hand-written quest)
    for p in glob.glob(os.path.join(ESP, '*', '*.yaml')):
        m = re.search(r' - ([0-9A-F]{6})_', os.path.basename(p))
        if m and m.group(1) not in keep: os.remove(p)
    for p in glob.glob(os.path.join(ESP, '*', '*ZP_Prophecy_TestPerk*')): os.remove(p)

    def write(ty, t):
        t = marksman(t)
        fk = re.search(r'^FormKey: (.+?)\s*$', t, re.M).group(1)
        h = fk.split(':')[0]
        os.makedirs(os.path.join(ESP, ty), exist_ok=True)
        open(os.path.join(ESP, ty, f'{ed(t)} - {h}_{fk.split(":", 1)[1]}.yaml'), 'w', encoding='utf-8', newline='\r\n').write(t)

    def setstr(t, key, val):
        val = val.replace("'", "''")
        block = f"{key}:\n  TargetLanguage: English\n  Value: '{val}'\n"
        pat = re.compile(rf'^{key}:\n(?:  .*\n)+', re.M)
        if pat.search(t): return pat.sub(lambda m: block, t, count=1)
        return t.replace('\nEditorID: ', f'\nEditorID: ', 1).replace(f'EditorID: {ed(t)}\n', f'EditorID: {ed(t)}\n{block}', 1)

    def lore(t):
        # display strings only ("Value:"/"String:" lines) - never FormKeys or EditorIDs
        def fix(m):
            line = m.group(0)
            for a, b in LORE: line = line.replace(a, b)
            return line
        return re.sub(r'^\s*(?:Value|String): .*$', fix, t, flags=re.M)

    def prereq(parents):
        if not parents: return ''
        out = 'Conditions:\n'
        for i, pnode in enumerate(parents):
            flag = '  Flags:\n  - OR\n' if i < len(parents) - 1 else ''
            out += ('- MutagenObjectType: ConditionFloat\n' + flag +
                    '  Data:\n    MutagenObjectType: HasPerkConditionData\n'
                    f'    Perk: {nodeperk[pnode]}\n  ComparisonValue: 1\n')
        return out

    models, scripts = set(), set()
    # --- copied records
    for fk in copy:
        ty, _, t = rec[fk]
        t = t.replace('\r\n', '\n')
        for f in re.findall(r'^\s+File: (.+?)\s*$', t, re.M): models.add((owner(fk), f.strip("'\"").lower()))
        for n in re.findall(r'^\s+- Name: (\S+)\s*$', t, re.M): scripts.add((owner(fk), n.lower()))
        if ty == 'Perks': continue                       # perks are written per node below
        t = remap(t, ed(t))
        t = re.sub(r'^EditorID: (?:ZP_)?', 'EditorID: ZP_', t, count=1, flags=re.M)
        t = lore(t)
        for old, new in RENAME.items():
            t = re.sub(rf'^(\s*Value: ){re.escape(old)}\s*$', lambda m: m.group(1) + new, t, flags=re.M)
        if ty == 'ConstructibleObjects':
            # Bear Traps' forge recipes stay copied (IDs) but can no longer unlock: Utility Droid owns that perk now
            t = t.replace(nodeperk[DROID_NODE], NEVER)
        if '- Name: ORD_DwarvenAutocannon_Script\n' in t:
            # Clockwork Turret aims itself (curator 2026-10-23): our rebuild of Ordinator's script, same properties
            # (both turrets: the main effect and Overclock's Firing Line one)
            t = t.replace('- Name: ORD_DwarvenAutocannon_Script\n', '- Name: ZP_ClockworkTurretEffect\n')
            t = t.replace('It tracks your line of sight for <dur> seconds', 'It shoots the nearest enemy for <dur> seconds')
        write(ty, t)

    # --- perks, one per node
    for nid, n in nodes.items():
        _, name, desc, seed, folded, parents = n
        if seed:
            t = rec[seed][2].replace('\r\n', '\n')
            # effects of folded perks are appended to this node's
            for a in folded:
                ft = rec[a][2].replace('\r\n', '\n')
                m = re.search(r'^Effects:\n((?:[- ].*\n)*)', ft, re.M)
                if m:
                    if re.search(r'^Effects:\n', t, re.M):
                        t = re.sub(r'^(Effects:\n(?:[- ].*\n)*)', lambda mm: mm.group(1) + m.group(1), t, count=1, flags=re.M)
                    else:
                        t += 'Effects:\n' + m.group(1)
            t = remap(t, name)
        else:
            t = f'FormKey: {nodeperk[nid]}\nEditorID: x\nNumRanks: 1\nPlayable: True\n'
        t = re.sub(r'^FormKey: .*$', f'FormKey: {nodeperk[nid]}', t, count=1, flags=re.M)
        t = re.sub(r'^EditorID: .*$', 'EditorID: ' + perk_edid(n), t, count=1, flags=re.M)
        t = re.sub(r'^NextPerk: .*\n', '', t, flags=re.M)
        t = re.sub(r'^Conditions:\n(?:[- ].*\n)*', '', t, count=1, flags=re.M)
        t = re.sub(r'^(NumRanks: .*\n)', lambda m: prereq(parents) + m.group(1), t, count=1, flags=re.M) if 'NumRanks:' in t else t + prereq(parents)
        t = setstr(t, 'Name', name)
        if desc: t = setstr(t, 'Description', desc)
        elif 'Description:' in t: t = lore(t)
        for vn, ep, old, new in VALUE_EDITS:
            if vn == nid:
                t2 = re.sub(rf'(EntryPoint: {ep}\n(?:  .*\n)*?  Value: ){re.escape(old)}\n', lambda m: m.group(1) + new + '\n', t, count=1)
                assert t2 != t, (nid, ep); t = t2
        if nid == 'ma3':     # Stunning Blows: Saboteur restricted to unarmed (right hand item type 0)
            t = add_unarmed(t)
        if nid in ('gun2', 'gun3'):
            t = t.rstrip('\n') + '\n' + gun_hit_effect(gunhit)
        if nid == 'ma5':
            t = t.rstrip('\n') + '\nEffects:\n- MutagenObjectType: PerkAbilityEffect\n  Ability: ' + flowab + '\n'
        # Sharpshooter, muskets only (curator 2026-10-23): item type 12 on the owner tab
        if nid == 'gun1':   # Quick Reload: its own copy of PerkAbQuickShot (crossbow-type effect only) + the flag gated
            t, n = re.subn(r'  Ability: 106642:Skyrim\.esm\n', f"  Ability: {sharp['qrab']}\n", t)
            assert n == 1, 'Quick Reload ability'
            t, n = re.subn(r'(- MutagenObjectType: PerkEntryPointSelectText\n)(  EntryPoint: SetBooleanGraphVariable\n)',
                           lambda m: m.group(1) + '  Conditions:\n  - Conditions:\n' + MUSKET_TAB_COND + m.group(2), t)
            assert n == 1, 'Quick Reload graph flag'
        if nid == 'gun4':   # Run and Gun: next to its IsSneaking check
            sneak = '        MutagenObjectType: IsSneakingConditionData\n'
            assert t.count(sneak) == 1, 'Run and Gun condition'
            t = t.replace(sneak, sneak + MUSKET_TAB_COND)
        if nid == 'gun5':   # Deadeye: crit/damage entries gated; the enchantment entries lose their "or a bow"
            vats = '  - Conditions:\n    - MutagenObjectType: ConditionFloat\n      Data:\n        MutagenObjectType: GetVATSModeConditionData\n'
            assert t.count(vats) == 3, ('Deadeye tab-0 entries', t.count(vats))
            t = t.replace(vats, vats + MUSKET_TAB_COND)
            bow_or = ('    - MutagenObjectType: ConditionFloat\n      Flags:\n      - OR\n      Data:\n'
                      '        MutagenObjectType: GetEquippedItemTypeConditionData\n      ComparisonValue: 7\n')
            assert t.count(bow_or) == 2, ('Deadeye bow-or entries', t.count(bow_or))
            t = t.replace(bow_or, '')
        # Arcane Archery: the hit-spell perks point at the shared gun hit spell (one ApplyCombatHitSpell per hit)
        if nid in ('arc1', 'arc3', 'arc4'):
            t = t.rstrip('\n') + '\n' + gun_hit_effect(gunhit)
        if nid in ARC_ABILITY:
            if 'Effects:' not in t: t = t.rstrip('\n') + '\nEffects:\n'
            t = t.rstrip('\n') + '\n- MutagenObjectType: PerkAbilityEffect\n  Ability: ' + arc[ARC_ABILITY[nid]] + '\n'
        if nid == 'arc3':   # Ice Shot's watcher (records ice shots, puts the old ammo back) - always on with the perk
            t = t.rstrip('\n') + '\n- MutagenObjectType: PerkAbilityEffect\n  Ability: ' + sharp['icewatchab'] + '\n'
        if nid == 'nec1':   # Corpse Fever: +1 to the summon limit at each FeverStep of Arcane Fever (LastFlattered, negated)
            t = t.rstrip('\n') + '\nEffects:\n' + ''.join(
                '- MutagenObjectType: PerkEntryPointModifyValue\n  Priority: 100\n  Conditions:\n  - Conditions:\n'
                '    - MutagenObjectType: ConditionFloat\n      CompareOperator: LessThanOrEqualTo\n      Data:\n'
                '        MutagenObjectType: GetActorValueConditionData\n        ActorValue: LastFlattered\n'
                f'      ComparisonValue: {-step}\n  EntryPoint: ModCommandedActorLimit\n  PerkConditionTabCount: 2\n'
                '  Modification: Add\n  Value: 1\n' for step in range(NEC['FeverStep'], 101, NEC['FeverStep']))
        if nid in NEC_ABILITY:   # the two powers (Dark Effigy is a spell: write_menu grants it)
            t = t.rstrip('\n') + '\nEffects:\n- MutagenObjectType: PerkAbilityEffect\n  Ability: ' + nec[NEC_ABILITY[nid]] + '\n'
        if nid in FAITH_NEW:      # the 2026-10-25 Faith rework: the old talent's entry points and script out
            t = re.sub(r'^Effects:\n(?:[- ].*\n)*', '', t, count=1, flags=re.M)
            t = re.sub(r'^VirtualMachineAdapter:\n(?:  .*\n)*', '', t, count=1, flags=re.M)
            assert 'Effects:' not in t and 'VirtualMachineAdapter' not in t, f'{nid}: old perk body left'
            t = t.rstrip('\n') + '\n' + FAITH_NEW[nid](faith)
        if nid == DROID_NODE:      # Bear Traps' (and Lockjaw's) entry points out, the Utility Droid power in
            t, n_eff = re.subn(r'^Effects:\n(?:[- ].*\n)*', '', t, count=1, flags=re.M)
            assert n_eff == 1 and 'Effects:' not in t, 'Bear Traps perk effects not where expected'
            # ...and its perk-script fragment (the "pick up a bear trap" activate entry it hooked is gone)
            t, n_vm = re.subn(r'^VirtualMachineAdapter:\n(?:  .*\n)*', '', t, count=1, flags=re.M)
            assert n_vm == 1 and 'PRKF_ORD' not in t, 'Bear Traps perk script not where expected'
            t = t.rstrip('\n') + '\nEffects:\n- MutagenObjectType: PerkAbilityEffect\n  Ability: ' + droid['power'] + '\n'
        if nid == 'shd6':      # Shade Veil: the mist while sneaking, and harder to detect (Enderal's own entry point)
            t = t.rstrip('\n') + ('\nEffects:\n- MutagenObjectType: PerkAbilityEffect\n  Ability: ' + shadow['veilab'] +
                                  '\n- MutagenObjectType: PerkEntryPointModifyValue\n  EntryPoint: ModDetectionSneakSkill\n'
                                  f'  PerkConditionTabCount: 2\n  Modification: Add\n  Value: {SHADE_VEIL_DETECT}\n')
        if nid == 'shd1':      # Gather Shadows: the Darkness ability (the DLL writes the count into its magnitude)
            t = t.rstrip('\n') + '\nEffects:\n- MutagenObjectType: PerkAbilityEffect\n  Ability: ' + shadow['darkab'] + '\n'
        if nid == 'shd5':      # Nightfall: the power (the four spells are granted by the menu, SHADOW_GRANTS)
            t = t.rstrip('\n') + '\nEffects:\n- MutagenObjectType: PerkAbilityEffect\n  Ability: ' + shadow['power'] + '\n'
        if nid == 'dru2':      # The Hunt: the power (the menu AddSpells perk powers)
            t = t.rstrip('\n') + '\nEffects:\n- MutagenObjectType: PerkAbilityEffect\n  Ability: ' + druid['huntpower'] + '\n'
        if nid == 'dru9':      # Wolf Pack: room for the second wolf while the first is out (The Hunt's script calls it)
            t = t.rstrip('\n') + '\n' + summon_room('HasMagicEffectConditionData', 'MagicEffect', druid['wolfme1'])
        if nid == 'dru10':     # Nature's Way: one more summon while a totem stands (totems are summons)
            t = t.rstrip('\n') + '\n' + summon_room('HasMagicEffectKeywordConditionData', 'Keyword', TOTEM_KEYWORD)
        if nid == 'dru7':      # Force of Nature: the power, and room for the familiars while the form lasts
            t = t.rstrip('\n') + '\n' + druid_perk(druid)
        if nid == 'sor10':     # Drowning Orb: the ability that restores the player's Mana inside the orb
            t = t.rstrip('\n') + '\nEffects:\n- MutagenObjectType: PerkAbilityEffect\n  Ability: ' + sorc['orbwatch'] + '\n'
        if nid == 'sor9':      # Veil Wyrm: Mana Burn's half-cost spells while the shout's marker is on
            t = t.rstrip('\n') + '\n' + sorc_perk(sorc)
        if nid == 'sor2':      # Orbit Ward: the ability that raises it while casting
            t = t.rstrip('\n') + '\nEffects:\n- MutagenObjectType: PerkAbilityEffect\n  Ability: ' + sorc['orbitab'] + '\n'
        if nid in SHVL_TIERS:  # Bursting Effigy: the ability that gives the Psionics tier
            t = t.rstrip('\n') + '\nEffects:\n- MutagenObjectType: PerkAbilityEffect\n  Ability: ' + sorc[SHVL_TIERS[nid][0]] + '\n'
        if nid in ('rge1', 'rge9'):      # Rage: the stack damage bonus / Vehemence's free power attacks
            t = t.rstrip('\n') + '\n' + rage_perk(nid, rage)
        if nid in GLORY_ABILITY:
            t = t.rstrip('\n') + '\nEffects:\n- MutagenObjectType: PerkAbilityEffect\n  Ability: ' + glory[GLORY_ABILITY[nid]] + '\n'
        if nid in STAT:
            t = t.rstrip('\n') + '\nEffects:\n- MutagenObjectType: PerkAbilityEffect\n  Ability: ' + statab[nid] + '\n'
        if nid == 'glo1':      # the player keeps full speed in Seismic Stomp's slow time (as Ordinator's Quick Reflexes)
            t += ('- MutagenObjectType: PerkEntryPointModifyValue\n  Conditions:\n  - RunOnTabIndex: 1\n    Conditions:\n'
                  '    - MutagenObjectType: ConditionFloat\n      Data:\n        MutagenObjectType: EPMagic_SpellHasKeywordConditionData\n'
                  f"        Keyword: {glory['slowkw']}\n      ComparisonValue: 1\n  EntryPoint: ModPlayerMagicSlowdown\n"
                  '  PerkConditionTabCount: 2\n  Value: 1\n')
        write('Perks', t)

    # --- hand-built records
    write_gunhit(gunhit, newid, nodeperk, write, deadeye, bleedsnd, arc, sharp)
    write_flow(flowab, flowme, newid, write, nova, flowchain, dragon['Shockme'])
    write_droid(droid, write)
    write_never(write)
    write_dummies(write)
    # add_fever(newid, write, rec) - off since 2026-10-25 (curator): Faith's free heals no longer raise Arcane Fever
    add_tripwire_blast(newid, write, blast)
    write_glory(glory, write)
    write_arcane(arc, newid, write, sharp)
    write_necro(nec, nodeperk, write)
    # Quick Reload's own weapon-speed ability: PerkAbQuickShot 106642 (Enderal SE - Crossbows' winning copy, shared with
    # Enderal's Rapid Shot) minus its bow half - Sharpshooter is muskets only
    write('Spells', f"FormKey: {sharp['qrab']}\nEditorID: ZP_Prophecy_QuickReload_Ability\nName:\n  TargetLanguage: English\n"
                    "  Value: Quick Reload\nEquipmentType: 013F44:Skyrim.esm\nDescription:\n  TargetLanguage: English\n  Value: ''\n"
                    "Type: Ability\nCastType: ConstantEffect\nEffects:\n- BaseEffect: 105F17:Skyrim.esm\n  Data:\n    Magnitude: 1.3\n"
                    "  Conditions:\n  - MutagenObjectType: ConditionFloat\n    Data:\n      MutagenObjectType: GetEquippedItemTypeConditionData\n"
                    "      ItemSource: Right\n    ComparisonValue: 12\n")
    write('SoundDescriptors', f"""FormKey: {pointsnd['sound']}
EditorID: ZP_Prophecy_PointGainedSound
Type: Standard
Category: 01A0BD:Skyrim.esm
SoundFiles:
- {POINT_SOUND}
OutputModel: 0B6463:Skyrim.esm
LoopAndRumble: {{}}
Priority: 128
""")
    write('SoundMarkers', f"FormKey: {pointsnd['marker']}\nEditorID: ZP_Prophecy_PointGainedMarker\nSoundDescriptor: {pointsnd['sound']}\n")
    for k, fk in enumerate(notes, 1):     # UI category + 2D output: heard while the menu pauses the game
        write('SoundDescriptors', f"""FormKey: {fk}
EditorID: ZP_Prophecy_SelectNote_{k:02d}
Type: Standard
Category: 064451:Skyrim.esm
SoundFiles:
- Data\\Sound\\FX\\Zenderal\\Prophecy\\ZEN_ProphecyNote_{k:02d}.wav
OutputModel: 0B75FB:Skyrim.esm
LoopAndRumble: {{}}
Priority: 128
""")
    for key, spell_src, name, wav in POWER_SOUNDS:
        add_power_sound(newid, write, psound[key], key, spell_src, name, wav)
    add_smoke_invisibility(newid)
    fix_smoke_blind(nodeperk['gad6'])
    write_stats(nodes, statab, ratemgef, write)
    write_holy(hidx, hcopy, remap, write, faith)
    write_faith(faith, newid, write)
    write_shadow(shadow, write, nodeperk)
    write_druid(druid, write)
    write_hunt(druid, write, nodeperk)
    write_sorcerer(sorc, write)
    write_unsold_tomes(write)
    write_dragons_breath(dragon, write, sharp, arc)
    write_rage(rage, nodeperk, write, dragon, flowchain)

    if bad:
        for k, v in sorted(bad.items()): print('UNRESOLVED', v, k)
        sys.exit('unresolved references - fix SPEC or the source trees')
    copy_assets(models, scripts)
    copy_holy_assets(hidx, hcopy)
    write_menu(nodes, nodeperk, write, {'nec2': nec['effspell'],      # spells: AddPerk would not teach them
                                        'faith1': newid[htm('000826')], 'faith4': newid[htm('000829')],
                                        **SHADOW_GRANTS, 'shd7': shadow['dspell'], **DRUID_GRANTS, 'dru1': druid['craftspell'],
                                        **{nid: s[1] for nid, s in SORC_SPELLS.items()},
                                        'arc3': arc['iceshout'],                # a shout: the menu teaches its word
                                        'sor9': WYRM_SHOUT})                    # Veil Wyrm: all three words
    print(f'records copied {len(copy)}, perks {len(nodes)}, next free ID 0x{nxt:03X}, models {len(models)}, scripts {len(scripts)}')


def write_stats(nodes, statab, ratemgef, write):
    """One constant ability per stat talent, plus the Health/Mana regen MGEFs (AbFortifyStaminaRate's copies)."""
    src = open(os.path.join(REF, 'base', 'Skyrim', 'MagicEffects', 'AbFortifyStaminaRate - 105F21_Skyrim.esm.yaml'),
               encoding='utf-8').read().replace('\r\n', '\n')
    for key, edid, name, av in STAT_RATE_MGEFS:
        t = re.sub(r'^FormKey: .*$', f'FormKey: {ratemgef[key]}', src, count=1, flags=re.M)
        t = re.sub(r'^EditorID: .*$', f'EditorID: {edid}', t, count=1, flags=re.M)
        t = re.sub(r'^Name:\n(?:  .*\n)+', f'Name:\n  TargetLanguage: English\n  Value: {name}\n', t, count=1, flags=re.M)
        t = re.sub(r'^Description:\n(?:  .*\n)+', "Description:\n  TargetLanguage: English\n  Value: ''\n", t, count=1, flags=re.M)
        t, n = re.subn(r'^  ActorValue: StaminaRateMult$', f'  ActorValue: {av}', t, flags=re.M)
        assert n == 1, edid
        write('MagicEffects', t)
    for nid, ab in statab.items():
        kind, mag = STAT[nid]
        name = nodes[nid][1].replace("'", "''")
        effs = ''.join(f'- BaseEffect: {ratemgef[e[1:]] if e.startswith("@") else e + ":Skyrim.esm"}\n  Data:\n    Magnitude: {mag}\n'
                       for e in STAT_FX[kind][0])
        write('Spells', f"FormKey: {ab}\nEditorID: {perk_edid(nodes[nid])}_Ability\nName:\n  TargetLanguage: English\n"
                        f"  Value: '{name}'\nEquipmentType: 013F44:Skyrim.esm\nDescription:\n  TargetLanguage: English\n  Value: ''\n"
                        f"Type: Ability\nCastType: ConstantEffect\nEffects:\n{effs}")


# ------------------------------------------------------------------------------------------------ Faith rework
# (curator 2026-10-25) Allocated after the Holy Templar block, 0xA63+. Append new ones LAST.
FAITH_RECORDS = ('rpab', 'rpme', 'rpvis', 'smitespell', 'smiteme',
                 'rparmo', 'rparma',     # Righteous Path's visible ward (curator 2026-10-25)
                 'wrathgate', 'wrathcloak', 'wrathfever')   # Wrath of the Lightborn's cast-time fever gate (wrath_split)
WEAPMATERIALSILVER = '10AA1A:Skyrim.esm'
SMITE_CHANCE = 15
# Righteous Path's conditions: blocking, with a spell or nothing in the left hand (Dual Wield Parrying blocks that way)
RP_BLOCKING = ('  Conditions:\n'
               '  - MutagenObjectType: ConditionFloat\n    Flags:\n    - OR\n    Data:\n'
               '      MutagenObjectType: GetEquippedItemTypeConditionData\n      ItemSource: Left\n    ComparisonValue: 0\n'
               '  - MutagenObjectType: ConditionFloat\n    Data:\n'
               '      MutagenObjectType: GetEquippedItemTypeConditionData\n      ItemSource: Left\n    ComparisonValue: 9\n'
               '  - MutagenObjectType: ConditionFloat\n    Data:\n      MutagenObjectType: IsBlockingConditionData\n'
               '    ComparisonValue: 1\n')
FAITH_NEW = {
    'faith1': lambda f: '',      # Consecrate Dead: the spell is granted by the menu (write_menu grants)
    'faith2': lambda f: f"Effects:\n- MutagenObjectType: PerkAbilityEffect\n  Ability: {f['rpab']}\n",
    # Smite: its own combat hit spell, on melee hits only (bows and muskets keep the shared gun hit spell: one
    # ApplyCombatHitSpell per hit)
    'faith3': lambda f: ('Effects:\n- MutagenObjectType: PerkEntryPointSelectSpell\n  Conditions:\n  - RunOnTabIndex: 1\n'
                         '    Conditions:\n    - MutagenObjectType: ConditionFloat\n      Data:\n'
                         f'        MutagenObjectType: HasKeywordConditionData\n        Keyword: {WEAPMATERIALSILVER}\n'
                         '      ComparisonValue: 1\n    - MutagenObjectType: ConditionFloat\n      Data:\n'
                         f'        MutagenObjectType: HasKeywordConditionData\n        Keyword: {WEAPTYPEBOW}\n'
                         '      ComparisonValue: 0\n  EntryPoint: ApplyCombatHitSpell\n  PerkConditionTabCount: 3\n'
                         f"  Spell: {f['smitespell']}\n"),
    'faith4': lambda f: '',      # Wrath of the Lightborn: granted by the menu
}


def write_faith(f, newid, write):
    """Righteous Path (Kittytails' Sunlight Targe as a passive block ward, without the summoned shield: equipping it
    would push a spell out of the left hand) and Smite (Hallowed Flare's sky-bolt on a silver hit)."""
    def mgef(fk, edid, name, desc, extra, cast='ConstantEffect', target='', shader=''):
        write('MagicEffects', f"""FormKey: {fk}
EditorID: {edid}
{extra}Name:
  TargetLanguage: English
  Value: {name}
Flags:
- NoMagnitude
- NoArea
- NoDuration
- Painless
{'' if desc else '- HideInUI' + chr(10)}{shader}Archetype:
  MutagenObjectType: MagicEffectArchetype
  Type: Script
CastType: {cast}
{target}DualCastScale: 1
CastingSoundLevel: Silent
Sounds: []
Description:
  TargetLanguage: English
  Value: '{desc}'
""")
    mgef(f['rpme'], 'ZP_Prophecy_RighteousPath_Effect', 'Righteous Path',
         'While you block with a spell or nothing in your left hand, each attacker you block is struck by a beam of light, for 10 Mana.',
         'VirtualMachineAdapter:\n  Scripts:\n  - Name: ZP_RighteousPathEffect\n    Properties:\n'
         f"    - MutagenObjectType: ScriptObjectProperty\n      Name: CounterSpell\n      Object: {newid[htm('000863')]}\n"
         f"    - MutagenObjectType: ScriptObjectProperty\n      Name: HitSFX\n      Object: {newid[htm('00085D')]}\n"
         f"    - MutagenObjectType: ScriptObjectProperty\n      Name: ExplosionArtEffect\n      Object: {newid[htm('00085E')]}\n"
         f"    - MutagenObjectType: ScriptObjectProperty\n      Name: WardShield\n      Object: {f['rparmo']}\n")
    # The ward's trigger (2026-10-25; was the first version's body glow): condition-gated on the ability like the
    # resistances, so the engine starts it for any block - Dual Wield Parrying's forced block raises no block events.
    mgef(f['rpvis'], 'ZP_Prophecy_RighteousPath_WardEffect', 'Righteous Path', '',
         'VirtualMachineAdapter:\n  Scripts:\n  - Name: ZP_RighteousPathWard\n    Properties:\n'
         f"    - MutagenObjectType: ScriptObjectProperty\n      Name: WardShield\n      Object: {f['rparmo']}\n")
    # The ward you see: Kittytails' Sunlight Targe shield (its mesh carries Prn = SHIELD, so it sits on the left
    # forearm), copied into the FX01 slot (61) so wearing it leaves the left hand - and a spell in it - alone.
    # ZP_RighteousPathEffect puts it on while the ward is up. No enchantment, rating, shield flag or block keyword.
    path = lambda ty, fk: glob.glob(os.path.join(ESP, ty, f"* - {fk.split(':')[0]}_*"))[0]
    def sub1(t, pat, rep, what):
        t, n = re.subn(pat, rep, t, count=1, flags=re.M)
        assert n == 1, f'Righteous Path ward: {what}'
        return t
    a = open(path('ArmorAddons', newid[htm('000846')]), encoding='utf-8').read().replace('\r\n', '\n')
    a = sub1(a, r'^FormKey: .*$', f"FormKey: {f['rparma']}", 'ARMA FormKey')
    a = sub1(a, r'^EditorID: .*$', 'EditorID: ZP_Prophecy_RighteousPath_WardAA', 'ARMA EditorID')
    a = sub1(a, r'^  - Shield$', '  - FX01', 'ARMA slot')
    fp1 = f'    File: Lightpower\\{HOLY_WARD_1ST}\n    Data: 0x020000000000000000000000\n'
    a = sub1(a, r'^(WorldModel:\n(?:  .*\n)*)', lambda m: m.group(1) + 'FirstPersonModel:\n  Male:\n' + fp1 + '  Female:\n' + fp1,
             'ARMA first-person model')
    write('ArmorAddons', a)
    o = open(path('Armors', newid[htm('00082D')]), encoding='utf-8').read().replace('\r\n', '\n')
    o = sub1(o, r'^FormKey: .*$', f"FormKey: {f['rparmo']}", 'ARMO FormKey')
    o = sub1(o, r'^EditorID: .*$', 'EditorID: ZP_Prophecy_RighteousPath_Ward', 'ARMO EditorID')
    o = sub1(o, r'^VirtualMachineAdapter:\n(?:  .*\n)*', '', 'ARMO script')
    o = sub1(o, r'^ObjectEffect: .*\n', '', 'ARMO enchantment')
    o = sub1(o, r'^  - Shield$', '  - FX01', 'ARMO slot')
    o = sub1(o, r'^EquipmentType: .*\n', '', 'ARMO equip type')
    o = sub1(o, r'^Keywords:\n- 0965B2:Skyrim\.esm\n', '', 'ARMO shield keyword')
    o = sub1(o, r'^Armature:\n- .*$', f"Armature:\n- {f['rparma']}", 'ARMO armature')
    o = sub1(o, r'^ArmorRating: .*$', 'ArmorRating: 0', 'ARMO rating')
    o = sub1(o, r'^- Shield\n', '', 'ARMO shield flag')
    write('Armors', o)
    write('Spells', f"""FormKey: {f['rpab']}
EditorID: ZP_Prophecy_RighteousPath_Ability
Name:
  TargetLanguage: English
  Value: Righteous Path
EquipmentType: 013F44:Skyrim.esm
Description:
  TargetLanguage: English
  Value: ''
Type: Ability
CastType: ConstantEffect
Effects:
- BaseEffect: {f['rpme']}
  Data: {{}}
- BaseEffect: 053124:Skyrim.esm
  Data:
    Magnitude: 25
""" + RP_BLOCKING + """- BaseEffect: 0E40D3:Skyrim.esm
  Data:
    Magnitude: 100
""" + RP_BLOCKING + f"""- BaseEffect: {f['rpvis']}
  Data: {{}}
""" + RP_BLOCKING)
    # Smite: the hit places Hallowed Flare's own explosion on the target, which drops the player's sky-bolt there
    mgef(f['smiteme'], 'ZP_Prophecy_Smite_Effect', 'Smite', '',
         'VirtualMachineAdapter:\n  Scripts:\n  - Name: ZP_HolyPlaceExplosion\n    Properties:\n'
         f"    - MutagenObjectType: ScriptObjectProperty\n      Name: ExplosionRef\n      Object: {newid[htm('000841')]}\n",
         cast='FireAndForget', target='TargetType: Touch\n')
    write('Spells', f"""FormKey: {f['smitespell']}
EditorID: ZP_Prophecy_Smite_HitSpell
Name:
  TargetLanguage: English
  Value: Smite
MenuDisplayObject: 0435A5:Skyrim.esm
EquipmentType: 013F44:Skyrim.esm
Description:
  TargetLanguage: English
  Value: ''
Flags:
- ManualCostCalc
CastType: FireAndForget
TargetType: Touch
Effects:
- BaseEffect: {f['smiteme']}
  Data: {{}}
  Conditions:
  - MutagenObjectType: ConditionFloat
    CompareOperator: LessThan
    Data:
      MutagenObjectType: GetRandomPercentConditionData
    ComparisonValue: {SMITE_CHANCE}
""")


def wrath_split(t, ty, faith, write):
    """Wrath of the Lightborn (fixed 2026-10-25). Its first version carried "Arcane Fever below 50%" as a condition on
    every effect - but the engine re-checks an active effect's conditions, and the cast's own +50% fever then failed
    them, so the cloak stopped after one volley. Now the learned spell (this record, 0xA43, no Mana) holds only the gate
    effect: ZP_WrathGate checks the fever ONCE, at cast, then casts the real cloak (wrathcloak, no conditions, runs its
    full 60 s) and the fever spell (wrathfever, Enderal's 11A4B6 at HOLY_WRATH_FEVER). Returns the gate spell's text."""
    cloak = re.sub(r'^FormKey: .*$', f"FormKey: {faith['wrathcloak']}", t, count=1, flags=re.M)
    cloak = re.sub(r'^EditorID: .*$', 'EditorID: ZP_Holy_WrathoftheLightborn_Cloak', cloak, count=1, flags=re.M)
    assert 'Conditions:' not in cloak, 'Wrath cloak must carry no conditions'
    write(ty, cloak)
    write('Spells', f"""FormKey: {faith['wrathfever']}
EditorID: ZP_Holy_WrathoftheLightborn_Fever
Name:
  TargetLanguage: English
  Value: Wrath of the Lightborn
EquipmentType: 013F44:Skyrim.esm
Description:
  TargetLanguage: English
  Value: ''
Flags:
- ManualCostCalc
CastType: FireAndForget
Effects:
- BaseEffect: {FEVER}
  Data:
    Magnitude: {HOLY_WRATH_FEVER}
    Duration: 1
""")
    write('MagicEffects', f"""FormKey: {faith['wrathgate']}
EditorID: ZP_Holy_WrathoftheLightborn_Gate
VirtualMachineAdapter:
  Scripts:
  - Name: ZP_WrathGate
    Properties:
    - MutagenObjectType: ScriptObjectProperty
      Name: CloakSpell
      Object: {faith['wrathcloak']}
    - MutagenObjectType: ScriptObjectProperty
      Name: FeverSpell
      Object: {faith['wrathfever']}
    - MutagenObjectType: ScriptFloatProperty
      Name: MaxFever
      Data: {float(HOLY_WRATH_FEVER)}
Name:
  TargetLanguage: English
  Value: Wrath of the Lightborn
MenuDisplayObject: 1097CA:Skyrim.esm
Flags:
- NoMagnitude
- NoArea
- NoDuration
- Painless
MagicSkill: Restoration
Archetype:
  MutagenObjectType: MagicEffectArchetype
  Type: Script
CastType: FireAndForget
CastingArt: 01C859:Skyrim.esm
DualCastScale: 1
Sounds: []
Description:
  TargetLanguage: English
  Value: 'For 60 seconds, bolts of sunlight strike enemies within 20 feet of you for 40 damage each. Undead take double damage. Costs {HOLY_WRATH_FEVER}% Arcane Fever; cannot be cast at {HOLY_WRATH_FEVER}% or more.'
""")
    t, n = re.subn(r'^Effects:\n(?:[- ].*\n)*', f"Effects:\n- BaseEffect: {faith['wrathgate']}\n  Data: {{}}\n", t,
                   count=1, flags=re.M)
    assert n == 1, 'Wrath effects block'
    return t


def write_holy(hidx, hcopy, remap, write, faith):
    """Holy Templar Magic's records, rebalanced (HOLY_COST/HOLY_EDITS) and repointed at Enderal forms."""
    hits = collections.Counter()
    for fk in hcopy:
        ty, _, t = hidx[fk]
        t = t.replace('\r\n', '\n')
        for sp, eff, field, old, new in HOLY_EDITS:
            if fk == htm(sp):
                pat = rf'(- BaseEffect: {eff}:{re.escape(HTM)}\n  Data:\n(?:    .*\n)*?    {field}: ){re.escape(old)}\n'
                t, n = re.subn(pat, lambda m: m.group(1) + new + '\n', t)
                assert n == 1, ('Holy edit', sp, eff, field, old)
                hits['edit'] += 1
        if fk in HOLY_COST:
            t, n = re.subn(r'^BaseCost: .*$', f'BaseCost: {HOLY_COST[fk]}', t, count=1, flags=re.M)
            assert n == 1 and 'ManualCostCalc' in t, ('Holy cost', fk)
            hits['cost'] += 1
        # magicPlaceExplosionScript / MagicPlaceHazard are vanilla scripts Enderal does not ship (triage 2026-10-25):
        # the first is re-written as ZP_HolyPlaceExplosion; Sanctuary's hazard already comes from its SpawnHazard
        # archetype (as Enderal's own Circle of Protection), so its MagicPlaceHazard goes. AshPileObject named a
        # Dragonborn form: without it the script's AttachAshPile uses the default pile.
        t, n = re.subn(r'^  - Name: magicPlaceExplosionScript$', '  - Name: ZP_HolyPlaceExplosion', t, flags=re.M)
        hits['explosion script'] += n
        t, n = re.subn(r'^  - Name: MagicPlaceHazard\n    Properties:\n(?:    .*\n)*', '', t, flags=re.M)
        hits['hazard script'] += n
        t, n = re.subn(r'^    - MutagenObjectType: ScriptObjectProperty\n      Name: AshPileObject\n      Object: .*\n', '', t, flags=re.M)
        hits['ash pile'] += n
        t = remap(t, ed(t), vanilla_ok=True)
        t = re.sub(r'^EditorID: _LIP_', 'EditorID: ZP_Holy_', t, count=1, flags=re.M)
        def rename(m):
            line = m.group(0)
            for a, b in HOLY_RENAME: line = line.replace(a, b)
            return line
        t = re.sub(r'^\s*(?:Value|String): .*$', rename, t, flags=re.M)
        if fk == htm('000829'):
            t = wrath_split(t, ty, faith, write)
            hits['wrath'] += 1
        write(ty, t)
    assert hits == {'edit': len(HOLY_EDITS), 'cost': len(HOLY_COST), 'explosion script': 4, 'hazard script': 1,
                    'ash pile': 1, 'wrath': 1}, hits


def copy_holy_assets(hidx, hcopy):
    """The mod's loose meshes, sound and scripts that the copied records name (vanilla paths stay in Enderal's BSAs)."""
    assets = os.path.join(PATCH, 'assets')
    shutil.rmtree(os.path.join(assets, 'sound'), ignore_errors=True)
    n = 0
    for fk in hcopy:
        t = hidx[fk][2]
        for f in re.findall(r'^\s+File: (.+?\.nif)\s*$', t, re.M | re.I):
            src = os.path.join(HTM_RAW, 'meshes', f.strip("'\"").replace('\\', os.sep))
            if os.path.isfile(src):
                dst = os.path.join(assets, 'meshes', f.strip("'\"").lower().replace('\\', os.sep))
                os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copyfile(src, dst); n += 1
        for f in re.findall(r'^- (data\\sound\\.+?\.wav)\s*$', t, re.M | re.I):
            src = os.path.join(HTM_RAW, f[5:].replace('\\', os.sep))
            if os.path.isfile(src):
                dst = os.path.join(assets, f[5:].lower().replace('\\', os.sep))
                os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copyfile(src, dst); n += 1
        for s in re.findall(r'^  - Name: (_LIP_\w+)\s*$', t, re.M | re.I):
            src = os.path.join(HTM_RAW, 'scripts', s.lower() + '.pex')
            assert os.path.isfile(src), f'Holy Templar script {s} not in {HTM_RAW}'
            shutil.copyfile(src, os.path.join(PATCH, 'Scripts', 'compiled', s.lower() + '.pex')); n += 1
    # Righteous Path's ward in first person (curator 2026-10-25: "a white mesh in the effect"): HolyShield:0 is a disc
    # drawn with textures\white.dds that the effect shader softens by view angle - a glow from the third-person camera,
    # a white sheet at first person's close, grazing angle. The first-person model is the same mesh with that shape
    # DETACHED: its entry in its parent's child list set to -1 (rewritten in place, file size unchanged). The first
    # version only set the shape's hidden flag and it still drew in game (2026-10-26) - attaching armor 3D can re-show
    # culled shapes. The glow spot (HolyShield:1) and particles stay.
    sys.path.insert(0, os.path.join(REPO, 'src', 'HorseCloakFluffFix', 'tools'))
    import nif
    src = os.path.join(assets, 'meshes', 'lightpower', 'holyshield.nif')
    m = nif.Nif(src)
    disc = [i for i, (typ, p, _) in enumerate(m.blocks)
            if typ == 'BSTriShape' and m.string(struct.unpack_from('<i', m.data, p)[0]) in HOLY_WARD_1ST_DROP]
    assert len(disc) == len(HOLY_WARD_1ST_DROP), f'{HOLY_WARD_1ST_DROP} not all found once in holyshield.nif'
    hit = 0
    for typ, p, _ in m.blocks:
        if typ not in ('NiNode', 'BSFadeNode'):
            continue
        q = p + 8 + 4 * struct.unpack_from('<I', m.data, p + 4)[0] + 4 + 4 + 12 + 36 + 4 + 4   # NiAVObject -> children
        for k in range(struct.unpack_from('<I', m.data, q)[0]):
            if struct.unpack_from('<i', m.data, q + 4 + 4 * k)[0] in disc:
                struct.pack_into('<i', m.data, q + 4 + 4 * k, -1)
                hit += 1
    assert hit == len(disc), f'{hit} parent entries for {len(disc)} shapes'
    open(os.path.join(assets, 'meshes', 'lightpower', HOLY_WARD_1ST.lower()), 'wb').write(bytes(m.data))
    print(f'  Holy Templar Magic: {len(hcopy)} records, {n} asset copies, + {HOLY_WARD_1ST} (first-person ward)')


def add_unarmed(t):
    cond = ('  Conditions:\n  - Conditions:\n    - MutagenObjectType: ConditionFloat\n      Data:\n'
            '        MutagenObjectType: GetEquippedItemTypeConditionData\n        ItemSource: Right\n'
            '      ComparisonValue: 0\n')
    out, n = re.subn(r'(- MutagenObjectType: PerkEntryPointSelectSpell\n)(  EntryPoint: ApplyCombatHitSpell\n)',
                     lambda m: m.group(1) + cond + m.group(2), t)
    assert n == 1, 'Saboteur hit-spell entry not found'
    # the damage bonus vs staggered enemies: the same unarmed condition on its owner tab (tab 0)
    tab0 = ('  - Conditions:\n    - MutagenObjectType: ConditionFloat\n      Data:\n'
            '        MutagenObjectType: GetEquippedItemTypeConditionData\n        ItemSource: Right\n'
            '      ComparisonValue: 0\n')
    out, n = re.subn(r'(- MutagenObjectType: PerkEntryPointModifyValue\n  Conditions:\n)(  - RunOnTabIndex: 2\n)',
                     lambda m: m.group(1) + tab0 + m.group(2), out, count=1)
    assert n == 1, 'Saboteur damage entry not found'
    return out


def gun_hit_effect(spell):
    return ('Effects:\n- MutagenObjectType: PerkEntryPointSelectSpell\n  Conditions:\n  - RunOnTabIndex: 1\n'
            '    Conditions:\n    - MutagenObjectType: ConditionFloat\n      Data:\n'
            f'        MutagenObjectType: HasKeywordConditionData\n        Keyword: {WEAPTYPEBOW}\n'
            '      ComparisonValue: 1\n  EntryPoint: ApplyCombatHitSpell\n  PerkConditionTabCount: 3\n'
            f'  Spell: {spell}\n')


def write_gunhit(gunhit, newid, nodeperk, write, deadeye, bleedsnd, arc, late):
    """One hit spell for both gun perks (ApplyCombatHitSpell applies a single spell per hit): Monk's bleed
    effect gated on Bleeding Shot, Enderal's weapon fire-enchant effect gated on Elemental Rounds."""
    monk_spell = newid[f'000879:{SOS}']
    t = open(glob.glob(os.path.join(ESP, 'Spells', f'* - {monk_spell.split(":")[0]}_*'))[0], encoding='utf-8').read().replace('\r\n', '\n')
    bleed = re.search(r'^  - BaseEffect: (.+?)\s*$|^- BaseEffect: (.+?)\s*$', t, re.M)
    be = (bleed.group(1) or bleed.group(2))
    t = re.sub(r'^FormKey: .*$', f'FormKey: {gunhit}', t, count=1, flags=re.M)
    t = re.sub(r'^EditorID: .*$', 'EditorID: ZP_Prophecy_GunHitSpell', t, count=1, flags=re.M)
    t = re.sub(r'^(Name:\n  TargetLanguage: English\n  Value: ).*$', r'\1Firearms', t, count=1, flags=re.M)
    def gate(perk):
        # MutagenObjectType must be the first key under Data or Spriggit fails to read it
        return ('  Conditions:\n  - MutagenObjectType: ConditionFloat\n    Data:\n      MutagenObjectType: HasPerkConditionData\n'
                '      RunOnType: Reference\n      Reference: 000014:Skyrim.esm\n'
                f'      Perk: {perk}\n    ComparisonValue: 1\n')
    eff = re.search(r'^Effects:\n((?:[- ].*\n)*)', t, re.M)
    assert eff, 'Monk spell has no Effects'
    body = eff.group(1)
    body = re.sub(r'(- BaseEffect: .*\n(?:  Data:\n(?:    .*\n)*)?)', lambda m: m.group(1) + gate(nodeperk['gun3']) + MUSKET_IN_HAND, body, count=1)
    body += (f'- BaseEffect: {FIRE_ENCH}\n  Data:\n    Magnitude: 10\n    Duration: 0\n' + gate(nodeperk['gun2']) + MUSKET_IN_HAND)
    # Deadeye shares this spell (2026-10-23). ApplyCombatHitSpell applies one spell per hit and owning Deadeye means
    # owning both gun perks, so Ordinator's own Deadeye hit spell competed with this one. Its other 11 effects are all
    # gated on ZP_Prophecy_Never; only Snipe Blocker + Snipe (in Ordinator's order) carry over.
    by_edid = lambda ty, e: [x for x in glob.glob(os.path.join(ESP, ty, '*.yaml')) if os.path.basename(x).startswith(e + ' - ')]
    fk_of = lambda x: re.search(r'^FormKey: (.+?)\s*$', open(x, encoding='utf-8').read(), re.M).group(1)
    snipe = fk_of(by_edid('MagicEffects', 'ZP_ORD_Arc_ArcheryOnHit_Effect_Snipe')[0])
    blocker = fk_of(by_edid('MagicEffects', 'ZP_ORD_Arc_ArcheryOnHit_Effect_Snipe_Blocker')[0])
    ord_path = by_edid('Spells', 'ZP_ORD_Arc_ArcheryOnHit_Spell')[0]
    ot = open(ord_path, encoding='utf-8').read().replace('\r\n', '\n')
    blocks = re.findall(r'^- BaseEffect: .*\n(?:  .*\n)*', ot, re.M)
    keep = [b for b in blocks if b.split('\n')[0].split(': ')[1] in (blocker, snipe)]
    assert [b.split('\n')[0].split(': ')[1] for b in keep] == [blocker, snipe], 'Snipe effects missing or reordered'
    # the curator's rocket-launcher blast when Deadeye triggers: a target without Snipe takes the triple crit
    # (Ordinator's Blocker only lands when Snipe is already on). First in the list, so Snipe is not on it yet.
    sound_records(write, deadeye, 'DeadeyeShot', 'Deadeye', DEADEYE_WAV, on_caster=True)
    lacks = lambda me: ('  - MutagenObjectType: ConditionFloat\n    Data:\n      MutagenObjectType: HasMagicEffectConditionData\n'
                        f'      MagicEffect: {me}\n')
    # Bleeding Shot's proc (curator's file, 2026-10-23): a bloody knife on the victim when a bleed starts - the
    # bleed's own GetDead == 0, and not while one runs (it is NoRecast). Before the bleed in the list.
    sound_records(write, bleedsnd, 'BleedingShot', 'Bleeding Shot', BLEED_WAV, touch=True)
    # Sharpshooter is muskets only (MUSKET_IN_HAND), Snipe's markers included, so a bow hit cannot spend Deadeye
    keep = [b + '  Conditions:\n' + MUSKET_IN_HAND for b in keep]
    assert all(b.count('Conditions:') == 1 for b in keep), 'Snipe effect gained its own conditions - merge them'
    body = (f"- BaseEffect: {deadeye['mgef']}\n  Data: {{}}\n" + gate(nodeperk['gun5']) + lacks(snipe) + MUSKET_IN_HAND
            + f"- BaseEffect: {bleedsnd['mgef']}\n  Data: {{}}\n" + gate(nodeperk['gun3'])
            + '  - MutagenObjectType: ConditionFloat\n    Data:\n      MutagenObjectType: GetDeadConditionData\n'
            + lacks(be) + MUSKET_IN_HAND
            + body + arcane_hits(arc, late, nodeperk, gate, lacks) + ''.join(keep))
    t = t[:eff.start(1)] + body + t[eff.end(1):]
    write('Spells', t)
    pp = glob.glob(os.path.join(ESP, 'Perks', f"* - {nodeperk['gun5'].split(':')[0]}_*"))[0]
    pt = open(pp, encoding='utf-8').read().replace('\r\n', '\n')
    ord_fk = fk_of(ord_path)
    assert pt.count(f'  Spell: {ord_fk}\n') == 1, 'Deadeye hit-spell entry not found'
    open(pp, 'w', encoding='utf-8', newline='\r\n').write(pt.replace(f'  Spell: {ord_fk}\n', f'  Spell: {gunhit}\n'))


def write_flow(ab, me, newid, write, nova, chain, chainme):
    slow = newid[f'07B101:{ORD}']
    write('Spells', f"""FormKey: {ab}
EditorID: ZP_Prophecy_FlowStateAbility
Name:
  TargetLanguage: English
  Value: Flow State
EquipmentType: 013F44:Skyrim.esm
Description:
  TargetLanguage: English
  Value: ''
Type: Ability
CastType: ConstantEffect
Effects:
- BaseEffect: {me}
  Data: {{}}
""")
    write('MagicEffects', f"""FormKey: {me}
EditorID: ZP_Prophecy_FlowStateEffect
VirtualMachineAdapter:
  Scripts:
  - Name: ZP_FlowStateEffect
    Properties:
    - MutagenObjectType: ScriptObjectProperty
      Name: SlowTime
      Object: {slow}
    - MutagenObjectType: ScriptObjectProperty
      Name: Nova
      Object: {nova['novaexp']}
    - MutagenObjectType: ScriptFloatProperty
      Name: NovaEvery
      Data: {FLOW_NOVA['Cooldown']}
    - MutagenObjectType: ScriptFloatProperty
      Name: SlowEvery
      Data: {FLOW_NOVA['SlowCooldown']}
    - MutagenObjectType: ScriptObjectProperty
      Name: ChainLightning
      Object: {chain}
Name:
  TargetLanguage: English
  Value: Flow State
Flags:
- HideInUI
- NoMagnitude
- NoArea
- NoDuration
- Painless
Archetype:
  MutagenObjectType: MagicEffectArchetype
  Type: Script
CastType: ConstantEffect
DualCastScale: 1
CastingSoundLevel: Silent
Sounds: []
Description:
  TargetLanguage: English
  Value: ''
""")
    # Shock Nova (curator, 2026-10-23): Enderal's shock-mass blast at the player's feet on a combat dodge, own cooldown.
    # The explosion drops its full-screen ISM (the list strips screen flashes) and gets a wider radius; its damage is a
    # copy of the weapon shock enchantment (shared, so not edited in place) at FLOW_NOVA['Damage'], gated to actors
    # hostile to the player so the player and followers standing in the blast are spared.
    t = open(SHOCK_MASS_EXP, encoding='utf-8').read().replace('\r\n', '\n')
    t = re.sub(r'^FormKey: .*$', f"FormKey: {nova['novaexp']}", t, count=1, flags=re.M)
    t = re.sub(r'^EditorID: .*$', 'EditorID: ZP_Prophecy_FlowStateNova', t, count=1, flags=re.M)
    t = re.sub(r'^Version2: .*\n', '', t, flags=re.M)
    t, n = re.subn(r'^(?:ImageSpaceModifier|ISRadius): .*\n', '', t, flags=re.M)
    assert n == 2, 'shock-mass explosion ISM lines not where expected'
    t, n1 = re.subn(r'^ObjectEffect: .*$', f"ObjectEffect: {nova['novaench']}", t, count=1, flags=re.M)
    t, n2 = re.subn(r'^Radius: .*$', f"Radius: {FLOW_NOVA['Radius']}", t, count=1, flags=re.M)
    assert n1 == n2 == 1, 'shock-mass explosion fields not where expected'
    write('Explosions', t)
    t = open(SHOCK_DAMAGE_ENCH, encoding='utf-8').read().replace('\r\n', '\n')
    t = re.sub(r'^FormKey: .*$', f"FormKey: {nova['novaench']}", t, count=1, flags=re.M)
    t = re.sub(r'^EditorID: .*$', 'EditorID: ZP_Prophecy_FlowStateNovaEnch', t, count=1, flags=re.M)
    t = re.sub(r'^Version2: .*\n', '', t, flags=re.M)
    t, n1 = re.subn(r'^Name:\n(?:  .*\n)+', 'Name:\n  TargetLanguage: English\n  Value: Shock Nova\n', t, count=1, flags=re.M)
    t, n2 = re.subn(r'^(    Magnitude: )20$', lambda m: m.group(1) + str(FLOW_NOVA['Damage']), t, count=1, flags=re.M)
    assert n1 == n2 == 1 and t.count('- BaseEffect:') == 1, 'shock enchantment not as expected'
    t = t.rstrip('\n') + ('\n  Conditions:\n  - MutagenObjectType: ConditionFloat\n    Data:\n'
                          '      MutagenObjectType: IsHostileToActorConditionData\n      TargetNpc: 000014:Skyrim.esm\n'
                          '    ComparisonValue: 1\n')
    write('ObjectEffects', t)
    # the nova's chain lightning (curator 2026-10-29: "add a chain lightning to the Shock Nova"): vanilla Chain
    # Lightning on Dragon's Breath's copy of its effect (no screen flash), at the nova's damage and Chain Lightning's
    # 13 ft; the script casts it from the player at their combat target as the nova goes off
    write('Spells', f"""FormKey: {chain}
EditorID: ZP_Prophecy_FlowStateChainLightning
Name:
  TargetLanguage: English
  Value: Shock Nova
EquipmentType: 013F44:Skyrim.esm
Description:
  TargetLanguage: English
  Value: ''
Flags:
- ManualCostCalc
- NoAbsorbOrReflect
CastType: FireAndForget
TargetType: Aimed
Effects:
- BaseEffect: {chainme}
  Data:
    Magnitude: {FLOW_NOVA['Damage']}
    Area: 13
""")


def write_droid(d, write):
    """Utility Droid (Gadgets node 3, curator 2026-10-23; replaced Bear Traps). A lesser power deploys a mechanical
    spider - Enderal's own Starling Spider (the friendly Starship-cave spider, DwarvenSpiderRace) - that follows the
    player on SureAI's _DefaultFollowPlayer package, heals them and staggers enemies around it, until it is destroyed.
    The first droid is free (once per save, flag d['free']); each later one costs DROID['Cost'] Spare Parts. One droid
    at a time: casting while it lives calls it back. The live droid is remembered in FormList d['list']."""
    # --- the droid: the Starling Spider record, re-purposed
    t = open(DROID_BASE_NPC, encoding='utf-8').read().replace('\r\n', '\n')
    t = re.sub(r'^FormKey: .*$', f"FormKey: {d['npc']}", t, count=1, flags=re.M)
    t = re.sub(r'^EditorID: .*$', 'EditorID: ZP_Prophecy_UtilityDroid', t, count=1, flags=re.M)
    for pat, rep in [
            (r'^Factions:\n(?:- .*\n(?:  .*\n)*)', f'Factions:\n- Faction: {PLAYER_FACTION}\n  Fluff: 0x000000\n'),
            (r'^DeathItem: .*\n', ''),                                   # no farmable loot
            (r'^AIData:\n(?:  .*\n)*', 'AIData:\n  Aggression: Aggressive\n  Confidence: Brave\n  EnergyLevel: 50\n'
                                       '  Responsibility: NoCrime\n  Assistance: HelpsFriendsAndAllies\n'),
            (r'^Packages:\n(?:- .*\n)*', f'Packages:\n- {FOLLOW_PLAYER}\n'),
            (r'^Name:\n(?:  .*\n)*', 'Name:\n  TargetLanguage: English\n  Value: Utility Droid\n')]:
        t, n = re.subn(pat, rep, t, count=1, flags=re.M)
        assert n == 1, f'Starling Spider record changed: {pat}'
    t = re.sub(r'^(Race: .*\n)', lambda m: m.group(1) + f"ActorEffect:\n- {d['ab']}\n", t, count=1, flags=re.M)
    assert 'ActorEffect:' in t and t.count('ActorEffect:') == 1
    write('Npcs', t)

    # --- its ability: heal the player, stagger nearby enemies (script on the droid)
    write('Spells', f"""FormKey: {d['ab']}
EditorID: ZP_Prophecy_UtilityDroid_Ability
Name:
  TargetLanguage: English
  Value: Utility Droid
EquipmentType: 013F44:Skyrim.esm
Description:
  TargetLanguage: English
  Value: ''
Type: Ability
CastType: ConstantEffect
Effects:
- BaseEffect: {d['abme']}
  Data: {{}}
""")
    write('MagicEffects', f"""FormKey: {d['abme']}
EditorID: ZP_Prophecy_UtilityDroid_Effect
VirtualMachineAdapter:
  Scripts:
  - Name: ZP_UtilityDroidEffect
    Properties:
    - MutagenObjectType: ScriptObjectProperty
      Name: StaggerSpell
      Object: {d['stg']}
    - MutagenObjectType: ScriptObjectProperty
      Name: HealSpell
      Object: {d['healspell']}
    - MutagenObjectType: ScriptFloatProperty
      Name: HealAmount
      Data: {DROID['HealAmount']}
    - MutagenObjectType: ScriptIntProperty
      Name: HealInterval
      Data: {DROID['HealInterval']}
    - MutagenObjectType: ScriptFloatProperty
      Name: HealRadius
      Data: {DROID['HealRadius']}
    - MutagenObjectType: ScriptIntProperty
      Name: StaggerInterval
      Data: {DROID['StaggerInterval']}
    - MutagenObjectType: ScriptFloatProperty
      Name: StaggerRadius
      Data: {DROID['StaggerRadius']}
Name:
  TargetLanguage: English
  Value: Utility Droid
Flags:
- HideInUI
- NoMagnitude
- NoArea
- NoDuration
- Painless
Archetype:
  MutagenObjectType: MagicEffectArchetype
  Type: Script
CastType: ConstantEffect
DualCastScale: 1
CastingSoundLevel: Silent
Sounds: []
Description:
  TargetLanguage: English
  Value: ''
""")

    # --- the stagger it casts: Enderal's contact stagger (StaggerAttackFFContact 07809B) as a target-actor effect,
    # so a script can apply it to each enemy (Seismic Stomp's bleed pattern). Magnitude 0.5 (Stunning Blows uses 0.25).
    t = open(STAGGER_CONTACT_MGEF, encoding='utf-8').read().replace('\r\n', '\n')
    t = re.sub(r'^FormKey: .*$', f"FormKey: {d['stgme']}", t, count=1, flags=re.M)
    t = re.sub(r'^EditorID: .*$', 'EditorID: ZP_Prophecy_UtilityDroid_StaggerEffect', t, count=1, flags=re.M)
    t = re.sub(r'^Version2: .*\n', '', t, flags=re.M)
    t, n1 = re.subn(r'^Name:\n(?:  .*\n)*', 'Name:\n  TargetLanguage: English\n  Value: Utility Droid\n', t, count=1, flags=re.M)
    t, n2 = re.subn(r'^TargetType: Touch$', 'TargetType: TargetActor', t, count=1, flags=re.M)
    t = re.sub(r'^Description:\n(?:  .*\n)*', "Description:\n  TargetLanguage: English\n  Value: ''\n", t, count=1, flags=re.M)
    assert n1 == n2 == 1 and 'Type: Stagger' in t, 'StaggerAttackFFContact not as expected'
    write('MagicEffects', t)
    write('Spells', f"""FormKey: {d['stg']}
EditorID: ZP_Prophecy_UtilityDroid_Stagger
Name:
  TargetLanguage: English
  Value: Utility Droid
MenuDisplayObject: 0435A5:Skyrim.esm
EquipmentType: 013F44:Skyrim.esm
Description:
  TargetLanguage: English
  Value: ''
Flags:
- NoAbsorbOrReflect
CastType: FireAndForget
TargetType: TargetActor
Effects:
- BaseEffect: {d['stgme']}
  Data:
    Magnitude: {DROID['StaggerMagnitude']}
""")

    # --- the power: deploy (free once, then Spare Parts) or call the living droid back
    write('Spells', f"""FormKey: {d['power']}
EditorID: ZP_Prophecy_UtilityDroid_Power
Name:
  TargetLanguage: English
  Value: Utility Droid
MenuDisplayObject: 0435A5:Skyrim.esm
EquipmentType: 025BEE:Skyrim.esm
Description:
  TargetLanguage: English
  Value: ''
Flags:
- IgnoreResistance
- NoAbsorbOrReflect
Type: LesserPower
CastType: FireAndForget
Effects:
- BaseEffect: {d['powerme']}
  Data:
    Duration: 1
""")
    write('MagicEffects', f"""FormKey: {d['powerme']}
EditorID: ZP_Prophecy_UtilityDroid_PowerEffect
VirtualMachineAdapter:
  Scripts:
  - Name: ZP_UtilityDroidPowerEffect
    Properties:
    - MutagenObjectType: ScriptObjectProperty
      Name: ThrowSpell
      Object: {d['throwspell']}
    - MutagenObjectType: ScriptObjectProperty
      Name: SwingSound
      Object: 07BB93:Skyrim.esm
    - MutagenObjectType: ScriptObjectProperty
      Name: SpareParts
      Object: {SPARE_PARTS}
    - MutagenObjectType: ScriptObjectProperty
      Name: DroidList
      Object: {d['list']}
    - MutagenObjectType: ScriptObjectProperty
      Name: FreeUsed
      Object: {d['free']}
    - MutagenObjectType: ScriptIntProperty
      Name: Cost
      Data: {DROID['Cost']}
Name:
  TargetLanguage: English
  Value: Utility Droid
Flags:
- NoMagnitude
- NoArea
- HideInUI
- Painless
Archetype:
  MutagenObjectType: MagicEffectArchetype
  Type: Script
CastType: FireAndForget
DualCastScale: 1
CastingSoundLevel: Silent
Sounds: []
Description:
  TargetLanguage: English
  Value: ''
""")
    write('FormLists', f"FormKey: {d['list']}\nEditorID: ZP_Prophecy_UtilityDroid_Current\n")
    write('Globals', f"MutagenObjectType: GlobalShort\nFormKey: {d['free']}\nEditorID: ZP_Prophecy_UtilityDroid_FreeUsed\nData: 0\n")

    # --- the throw (curator 2026-10-23): Enderal's Starling Dummy talent chain, copied. Its aimed spell's lobbed
    # projectile (the curled-up Starling spider, gravity 0.7) bursts on landing; the burst places an invisible activator
    # whose script places the droid (ZP_UtilityDroidPlacerScript). Each record is SureAI's with its links re-pointed.
    def sub1(t, pat, rep, what):
        t2, k = re.subn(pat, rep, t, count=1, flags=re.M)
        assert k == 1, f'{what}: {pat}'
        return t2
    names = {'throwspell': 'ZP_Prophecy_UtilityDroid_ThrowSpell', 'throwme': 'ZP_Prophecy_UtilityDroid_ThrowEffect',
             'throwproj': 'ZP_Prophecy_UtilityDroid_ThrowProjectile', 'throwexp': 'ZP_Prophecy_UtilityDroid_ThrowExplosion',
             'placer': 'ZP_Prophecy_UtilityDroid_Placer'}
    folder = {'throwspell': 'Spells', 'throwme': 'MagicEffects', 'throwproj': 'Projectiles', 'throwexp': 'Explosions',
              'placer': 'Activators'}
    for key, src in STARLING_DUMMY.items():
        t = open(src, encoding='utf-8').read().replace('\r\n', '\n')
        t = sub1(t, r'^FormKey: .*$', f'FormKey: {d[key]}', key)
        t = sub1(t, r'^EditorID: .*$', f'EditorID: {names[key]}', key)
        for block in ('Name', 'Description'):          # SureAI's localized strings -> one English line
            t = re.sub(rf'^{block}:\n(?:  .*\n)*', f"{block}:\n  TargetLanguage: English\n  Value: {'Utility Droid' if block == 'Name' else chr(39) * 2}\n",
                       t, count=1, flags=re.M)
        if key == 'throwspell':
            t = sub1(t, r'^- BaseEffect: 0F64A6:Skyrim\.esm$', f"- BaseEffect: {d['throwme']}", key)
        elif key == 'throwme':
            t = sub1(t, r'^Projectile: 0697F1:Skyrim\.esm$', f"Projectile: {d['throwproj']}", key)
        elif key == 'throwproj':
            t = sub1(t, r'^Explosion: 069836:Skyrim\.esm$', f"Explosion: {d['throwexp']}", key)
        elif key == 'throwexp':
            t = sub1(t, r'^PlacedObject: 06983E:Skyrim\.esm$', f"PlacedObject: {d['placer']}", key)
            t = sub1(t, r'^ImageSpaceModifier: .*\n', '', key)        # MAGShockExpImod's flash (curator: no screen effects)
        elif key == 'placer':
            t = sub1(t, r'^VirtualMachineAdapter:\n(?:  .*\n)*',
                     'VirtualMachineAdapter:\n  Scripts:\n  - Name: ZP_UtilityDroidPlacerScript\n    Properties:\n'
                     f"    - MutagenObjectType: ScriptObjectProperty\n      Name: Droid\n      Object: {d['npc']}\n"
                     f"    - MutagenObjectType: ScriptObjectProperty\n      Name: DroidList\n      Object: {d['list']}\n"
                     '    - MutagenObjectType: ScriptObjectProperty\n      Name: DustExplosion\n      Object: 0EEFB1:Skyrim.esm\n'
                     f"    - MutagenObjectType: ScriptFloatProperty\n      Name: BaseHealth\n      Data: {DROID['BaseHealth']}\n"
                     f"    - MutagenObjectType: ScriptFloatProperty\n      Name: HealthPerLevel\n      Data: {DROID['HealthPerLevel']}\n", key)
            t = sub1(t, r'^Destructible:\n(?:  .*\n)*', '', key)    # SureAI's self-destroying placer; ours deletes itself
        assert not re.search(r'0F64A6|0697F1|069836|06983E|_00E_A2_', t), f'{key} still links SureAI\'s chain'
        write(folder[key], t)

    # --- the heal's look (curator 2026-10-23: "an effect for when the droid heals me"): the droid casts this at the
    # player instead of restoring Health silently. Enderal's own heal-other effect RestoreHealthFFActor 01CEA7 (as in
    # HealOther 012FD2): the healing shimmer (HitShader 012FD9 + HitEffectArt 03F1B4), no Arcane Fever.
    write('Spells', f"""FormKey: {d['healspell']}
EditorID: ZP_Prophecy_UtilityDroid_Heal
Name:
  TargetLanguage: English
  Value: Utility Droid
MenuDisplayObject: 0435A5:Skyrim.esm
EquipmentType: 013F44:Skyrim.esm
Description:
  TargetLanguage: English
  Value: ''
Flags:
- NoAbsorbOrReflect
CastType: FireAndForget
TargetType: TargetActor
Effects:
- BaseEffect: 01CEA7:Skyrim.esm
  Data:
    Magnitude: {DROID['HealAmount']}
""")


def write_dummies(write):
    write('Quests', f"FormKey: {DUMMY_QUEST}\nEditorID: ZP_Prophecy_DummyQuest\nNextAliasID: 0\n")
    write('Locations', f"FormKey: {DUMMY_LOC}\nEditorID: ZP_Prophecy_DummyLocation\n")
    write('Spells', f"FormKey: {DUMMY_SPELL}\nEditorID: ZP_Prophecy_DummySpell\nEquipmentType: 013F44:Skyrim.esm\nType: Ability\nCastType: ConstantEffect\n")


def write_never(write):
    write('Perks', f"""FormKey: {NEVER}
EditorID: ZP_Prophecy_Never
Name:
  TargetLanguage: English
  Value: ''
NumRanks: 1
Hidden: True
""")


TRIPWIRE_PROC = f'0379A1:{ORD}'      # ORD_Sne_Tripwire_Spell_Proc - Ordinator's script remote-casts it on whoever trips
FIREBALL_EXP = os.path.join(REF, 'base', 'Skyrim', 'Explosions', 'FireBallExp01 - 0439C0_Skyrim.esm.yaml')
TRIPWIRE_DAMAGE = 40
# Flow State's Shock Nova (curator, 2026-10-23): Enderal's shock-mass blast + its weapon shock-damage enchantment, copied
SHOCK_MASS_EXP = os.path.join(REF, 'base', 'Skyrim', 'Explosions', 'ExplosionShockMass01ShockDamage - 03BC85_Skyrim.esm.yaml')
SHOCK_DAMAGE_ENCH = os.path.join(REF, 'base', 'Skyrim', 'ObjectEffects', 'EnchWeaponShockDamage06 - 045F9E_Skyrim.esm.yaml')
FLOW_NOVA = {'Damage': 40, 'Radius': 300, 'Cooldown': 8.0, 'SlowCooldown': 8.0}   # both 8 s (curator 2026-10-29)


def add_tripwire_blast(newid, write, blast):
    """Tripwire (Gadgets): a snap by an enemy also sets off a fireball explosion at their feet (curator's request
    2026-10-21). Enderal's FireBallExp01 copied with Damage set and its full-screen flash (ISM 0439C1) removed - the
    list strips screen flashes (NoScreenFlashes). Placed by ZP_TripwireBlastEffect, an extra effect on Tripwire Snap
    gated to actors hostile to the player; Ordinator's own tripwire script is untouched."""
    t = open(FIREBALL_EXP, encoding='utf-8').read().replace('\r\n', '\n')
    t = re.sub(r'^FormKey: .*$', f'FormKey: {blast["exp"]}', t, count=1, flags=re.M)
    t = re.sub(r'^EditorID: .*$', 'EditorID: ZP_Prophecy_TripwireBlast', t, count=1, flags=re.M)
    t = re.sub(r'^Version2: .*\n', '', t, flags=re.M)
    t = re.sub(r'^(?:ImageSpaceModifier|ISRadius): .*\n', '', t, flags=re.M)
    t2 = re.sub(r'^(Force: .*\n)', lambda m: m.group(1) + f'Damage: {TRIPWIRE_DAMAGE}\n', t, count=1, flags=re.M)
    assert t2 != t, 'FireBallExp01 has no Force line'
    write('Explosions', t2)
    write('Globals', f'MutagenObjectType: GlobalFloat\nFormKey: {blast["glob"]}\nEditorID: ZP_Prophecy_TripwireBlastTime\nData: 0\n')
    write('MagicEffects', f"""FormKey: {blast['mgef']}
EditorID: ZP_Prophecy_TripwireBlastEffect
VirtualMachineAdapter:
  Scripts:
  - Name: ZP_TripwireBlastEffect
    Properties:
    - MutagenObjectType: ScriptObjectProperty
      Name: Blast
      Object: {blast['exp']}
    - MutagenObjectType: ScriptObjectProperty
      Name: LastBlast
      Object: {blast['glob']}
Name:
  TargetLanguage: English
  Value: Tripwire Blast
Flags:
- Hostile
- Detrimental
- NoMagnitude
- NoDuration
- HideInUI
- Painless
Archetype:
  MutagenObjectType: MagicEffectArchetype
  Type: Script
CastType: FireAndForget
DualCastScale: 1
CastingSoundLevel: Silent
Sounds: []
Description:
  TargetLanguage: English
  Value: ''
Conditions:
- MutagenObjectType: ConditionFloat
  Data:
    MutagenObjectType: IsHostileToActorConditionData
    TargetNpc: 000014:Skyrim.esm
  ComparisonValue: 1
""")
    h = newid[TRIPWIRE_PROC].split(':')[0]
    p = glob.glob(os.path.join(ESP, 'Spells', f'* - {h}_*'))[0]
    t = open(p, encoding='utf-8').read().replace('\r\n', '\n')
    assert blast['mgef'] not in t
    t = t.rstrip('\n') + f"\n- BaseEffect: {blast['mgef']}\n  Data:\n    Area: 8\n"
    assert re.search(r'^Effects:\n(?:[- ].*\n)+- BaseEffect: ' + re.escape(blast['mgef']), t + '\n', re.M), 'Effects is not the last block'
    open(p, 'w', encoding='utf-8', newline='\r\n').write(t)


# Sounds on using a power that ships silent (curator's files, 2026-10-22): (key, source power, display name, file).
# The .wav files are loose and not committed - tools/03-install-sounds.py. Append new entries LAST (IDs follow order).
# Deadeye's trigger sound (curator's file, 2026-10-23), carried by the gun hit spell - see write_gunhit
DEADEYE_WAV = r'Data\Sound\FX\Zenderal\ZEN_DeadeyeShot_01.wav'
BLEED_WAV = r'Data\Sound\FX\Zenderal\ZEN_BleedingShot_01.wav'     # Bleeding Shot's proc, same spell

SELECT_NOTES = 18     # v3: notes of the curator's piano melody (src/ProphecyV3/tools/03-split-piano.py; not committed)
POINT_SOUND = r'Data\Sound\FX\Zenderal\ZEN_ProphecyPoint_01.wav'   # a Prophecy point is gained; not committed: tools/03
POWER_SOUNDS = [
    ('Tripwire_Ratchet', f'0379A4:{ORD}', 'Explosive Tripwire', r'Data\Sound\FX\Zenderal\ZEN_TripwireRatchet_01.wav'),
    ('Smokescreen_Burst', f'036EB3:{ORD}', 'Smokescreen', r'Data\Sound\FX\Zenderal\ZEN_SmokescreenBurst_01.wav'),
]


def add_power_sound(newid, write, r, key, spell_src, name, wav):
    """A sound when a power is used (Explosive Tripwire's ratchet as the player kneels, Smokescreen's burst; both
    ship silent from Ordinator). An extra effect on the power whose script plays one sound - Ordinator's own scripts
    stay untouched."""
    sound_records(write, r, key, name, wav)
    h = newid[spell_src].split(':')[0]
    p = glob.glob(os.path.join(ESP, 'Spells', f'* - {h}_*'))[0]
    t = open(p, encoding='utf-8').read().replace('\r\n', '\n')
    assert r['mgef'] not in t
    t = t.rstrip('\n') + f"\n- BaseEffect: {r['mgef']}\n  Data: {{}}\n"
    assert re.search(r'^Effects:\n(?:[- ].*\n)+- BaseEffect: ' + re.escape(r['mgef']), t + '\n', re.M), 'Effects is not the last block'
    open(p, 'w', encoding='utf-8', newline='\r\n').write(t)


def add_smoke_invisibility(newid):
    """Smokescreen's power also turns the player invisible (SMOKE_INVISIBLE, curator 2026-10-23): one more effect on
    the power spell, after the burst sound, so Ordinator's cloud script stays untouched."""
    h = newid[f'036EB3:{ORD}'].split(':')[0]                 # ORD_Sne_SmokeCurtain_Spell
    p = glob.glob(os.path.join(ESP, 'Spells', f'* - {h}_*'))[0]
    t = open(p, encoding='utf-8').read().replace('\r\n', '\n')
    assert SMOKE_INVISIBLE not in t and 'Type: Power' in t
    t = t.rstrip('\n') + f'\n- BaseEffect: {SMOKE_INVISIBLE}\n  Data:\n    Duration: {SMOKE_INVISIBLE_SECONDS}\n'
    assert re.search(r'^Effects:\n(?:[- ].*\n)+- BaseEffect: ' + re.escape(SMOKE_INVISIBLE), t + '\n', re.M), 'Effects is not the last block'
    open(p, 'w', encoding='utf-8', newline='\r\n').write(t)


def fix_smoke_blind(chaff):
    """Smokescreen blinds Enderal's enemies (curator 2026-10-26: "still detected immediately with maxed stealth").
    Every 0.5 s Ordinator's cloud script RemoteCasts Smoke Curtain from the cloud: Blindness 100 for 2 s (an engine AV
    that works here - Enderal's own Arps carry AbBlind 052FF3 via AbFalmer) plus ORD_Alert_Script, SetAlert(True) on
    every hostile inside. Two changes: (1) the blindness also takes undead - Ordinator skipped ActorTypeUndead/IsUndead,
    which in Enderal is most enemies (Lost Ones, skeletons); automatons (ActorTypeDwarven) stay immune; (2) the alert
    effect comes off the pulse - it put everyone in the cloud on alert twice a second, sharpening their hearing.
    Blind enemies still HEAR (armour, running), as Arps do."""
    by = lambda ty, e: [x for x in glob.glob(os.path.join(ESP, ty, '*.yaml')) if os.path.basename(x).startswith(e + ' - ')]
    p = by('MagicEffects', 'ZP_ORD_Sne_SmokeCurtain_Effect_Ping')[0]
    t = open(p, encoding='utf-8').read().replace('\r\n', '\n')
    undead = ['- MutagenObjectType: ConditionFloat\n  Data:\n    MutagenObjectType: HasKeywordConditionData\n'
              '    Keyword: 013796:Skyrim.esm\n',
              '- MutagenObjectType: ConditionFloat\n  Data:\n    MutagenObjectType: IsUndeadConditionData\n']
    for c in undead:
        assert t.count(c) == 1, ('Smoke Curtain blindness: undead condition not found once', c[:80])
        t = t.replace(c, '')
    # Chaff (2026-10-26): automatons too when the player has it - "not ActorTypeDwarven OR the player has Chaff"
    dwarven = ('- MutagenObjectType: ConditionFloat\n  Data:\n    MutagenObjectType: HasKeywordConditionData\n'
               '    Keyword: 01397A:Skyrim.esm\n')
    assert t.count(dwarven) == 1, 'Smoke Curtain blindness: automaton condition not found once'
    t = t.replace(dwarven, '- MutagenObjectType: ConditionFloat\n  Flags:\n  - OR\n' + dwarven[len('- MutagenObjectType: ConditionFloat\n'):] +
                  '- MutagenObjectType: ConditionFloat\n  Data:\n    MutagenObjectType: HasPerkConditionData\n'
                  '    RunOnType: Reference\n    Reference: 000014:Skyrim.esm\n'
                  f'    Perk: {chaff}\n  ComparisonValue: 1\n')
    open(p, 'w', encoding='utf-8', newline='\r\n').write(t)
    alert = re.search(r'^FormKey: (.+?)\s*$', open(by('MagicEffects', 'ZP_ORD_Sne_SmokeCurtain_Effect_PingScript')[0],
                                                   encoding='utf-8').read(), re.M).group(1)
    p = by('Spells', 'ZP_ORD_Sne_SmokeCurtain_Spell_Ping')[0]
    t = open(p, encoding='utf-8').read().replace('\r\n', '\n')
    t, n = re.subn(rf'^- BaseEffect: {re.escape(alert)}\n(?:  .*\n)*', '', t, flags=re.M)
    assert n == 1 and 'BaseEffect:' in t, 'Smoke Curtain pulse: alert effect not removed once'
    open(p, 'w', encoding='utf-8', newline='\r\n').write(t)


def sound_records(write, r, key, name, wav, on_caster=False, touch=False, descriptor=None):
    """SoundDescriptor + marker + a hidden Script effect (ZP_PlaySoundEffect) that plays it once. touch: the effect
    rides a Touch hit spell (target = the enemy); on_caster (implies touch) plays the sound on the shooter instead.
    descriptor: an existing SoundDescriptor for the marker instead of a new one from wav (r['sound'] unused)"""
    caster = ('    - MutagenObjectType: ScriptBoolProperty\n      Name: PlayOnCaster\n      Data: True\n'
              if on_caster else '')
    touch = 'TargetType: Touch\n' if on_caster or touch else ''
    if descriptor is None:
        write('SoundDescriptors', f"""FormKey: {r['sound']}
EditorID: ZP_Prophecy_{key}Sound
Type: Standard
Category: 01A0BD:Skyrim.esm
SoundFiles:
- {wav}
OutputModel: 0B6463:Skyrim.esm
LoopAndRumble: {{}}
Priority: 128
""")
    write('SoundMarkers', f"FormKey: {r['marker']}\nEditorID: ZP_Prophecy_{key}Marker\n"
                          f"SoundDescriptor: {descriptor or r['sound']}\n")
    write('MagicEffects', f"""FormKey: {r['mgef']}
EditorID: ZP_Prophecy_{key}Effect
VirtualMachineAdapter:
  Scripts:
  - Name: ZP_PlaySoundEffect
    Properties:
    - MutagenObjectType: ScriptObjectProperty
      Name: SoundToPlay
      Object: {r['marker']}
{caster}Name:
  TargetLanguage: English
  Value: {name}
Flags:
- NoMagnitude
- NoArea
- NoDuration
- HideInUI
- Painless
Archetype:
  MutagenObjectType: MagicEffectArchetype
  Type: Script
CastType: FireAndForget
{touch}DualCastScale: 1
CastingSoundLevel: Silent
Sounds: []
Description:
  TargetLanguage: English
  Value: ''
""")


def add_fever(newid, write, rec):
    """Arcane Fever on the two free heals (Enderal's rule: ~26 HP per fever point)."""
    for spell_src, mag in [(f'000E0F:{SOS}', 1), (f'000E37:{SOS}', 4)]:   # Healing Presence / Templar heals
        h = newid[spell_src].split(':')[0]
        p = glob.glob(os.path.join(ESP, 'Spells', f'* - {h}_*'))[0]
        t = open(p, encoding='utf-8').read().replace('\r\n', '\n')
        assert 'TargetType:' not in t, 'heal spell is not self-delivered'
        assert FEVER not in t
        t = t.rstrip('\n') + f'\n- BaseEffect: {FEVER}\n  Data:\n    Magnitude: {mag}\n    Duration: 1\n'
        assert re.search(r'^Effects:\n(?:[- ].*\n)+- BaseEffect: ' + re.escape(FEVER), t + '\n', re.M), 'Effects is not the last block'
        open(p, 'w', encoding='utf-8', newline='\r\n').write(t)


def copy_assets(models, scripts):
    import struct
    comp = os.path.join(PATCH, 'Scripts', 'compiled')
    for f in glob.glob(os.path.join(comp, '*.pex')):
        if not os.path.basename(f).lower().startswith('zp_'): os.remove(f)
    assets = os.path.join(PATCH, 'assets')
    for sub in ('meshes', 'textures'):   # interface/ProphecyPics comes from 02-convert-thumbnails.py - keep it
        shutil.rmtree(os.path.join(assets, sub), ignore_errors=True)
    for plugin, bsas in BSAS.items():
        lst = {}
        for b in bsas:
            d, l = _bsa.listing(os.path.join(RAW[plugin], b))
            for k, v in l.items(): lst[k] = (d, v)
        want_pex = {n for p, n in scripts if p == plugin}
        # script dependencies: any other script of this mod named in a pex string table
        allpex = {k.split('\\')[-1][:-4]: k for k in lst if k.endswith('.pex')}
        todo = [n for n in want_pex if n in allpex]; done = set()
        while todo:
            n = todo.pop()
            if n in done: continue
            done.add(n); data = _bsa.read(*lst[allpex[n]])
            for other in allpex:
                if other not in done and other.encode() in data.lower(): todo.append(other)
        for n in done:
            open(os.path.join(comp, n + '.pex'), 'wb').write(_bsa.read(*lst[allpex[n]]))
        missing = [n for n in want_pex if n not in allpex and not n.startswith('zp_')]
        if missing: print(f'  scripts not in {plugin} BSA (engine/base scripts?):', sorted(missing))
        # meshes + every texture they name
        todo = ['meshes\\' + m.replace('/', '\\') for p, m in models if p == plugin]
        for k in todo:
            if k not in lst: continue
            data = _bsa.read(*lst[k])
            out = os.path.join(assets, k.replace('\\', os.sep)); os.makedirs(os.path.dirname(out), exist_ok=True)
            open(out, 'wb').write(data)
            for tex in set(re.findall(rb'[\w\\/ .-]+?\.dds', data, re.I)):
                tk = tex.decode('latin1').lower().replace('/', '\\').lstrip('\\')
                if not tk.startswith('textures\\'): tk = 'textures\\' + tk
                if tk in lst:
                    o2 = os.path.join(assets, tk.replace('\\', os.sep)); os.makedirs(os.path.dirname(o2), exist_ok=True)
                    open(o2, 'wb').write(_bsa.read(*lst[tk]))


# ------------------------------------------------------------------------------------------------ Glory
# 'shout', 'word', 'dashspell', 'dashme' (0x91A-0x91D) were Gap Closer's; retired 2026-10-22 for Seismic Stomp and
# kept as unused names so the later Glory records keep their IDs. Never reuse them: older saves still point at them.
GLORY_RECORDS = ('shout', 'word', 'dashspell', 'dashme', 'swab', 'swme', 'dsab', 'banner', 'bannerme', 'cdspell', 'cdme')
GLORY_RECORDS_2 = ('hornsound', 'hornmarker')     # added 2026-10-22, after the Tripwire scene block
GLORY_RECORDS_3 = ('stompspell', 'stompme', 'stompexp', 'stompsound', 'bleedspell', 'bleedme', 'stompcd', 'stompcdme')
GLORY_RECORDS_4 = ('slowspell', 'slowme')     # Seismic Stomp's slow time, added 2026-10-22
STOMP_SLOW = (0.3, 10)                         # world speed, seconds
GLORY_RECORDS_5 = ('slowkw',)                  # the stomp slow time's own keyword, added 2026-10-22
GLORY_RECORDS_6 = ('surab', 'surme')           # Surrounded's ability + effect, after the late glo5 perk (0x93B-0x93C)
FLOW_NOVA_RECORDS = ('novaexp', 'novaench')     # Flow State's Shock Nova explosion + enchantment (0x93D-0x93E), 2026-10-23
# Utility Droid (Gadgets node 3, curator 2026-10-23), 0x93F-0x947: the droid NPC, its heal/stagger ability, the stagger
# spell it casts, the power and its effect, the one-droid list and the free-first-droid flag.
DROID_NODE = 'gad3'
DROID_RECORDS = ('npc', 'ab', 'abme', 'stgme', 'stg', 'power', 'powerme', 'list', 'free')
# the throw (2026-10-23), allocated after Necromancy: Enderal's Starling Dummy talent chain, copied (write_droid)
DROID_THROW_RECORDS = ('throwspell', 'throwme', 'throwproj', 'throwexp', 'placer')
DROID_HEAL_RECORDS = ('healspell',)    # the heal as a spell, for Enderal's heal look (2026-10-23)
STARLING_DUMMY = {k: os.path.join(REF, 'base', 'Skyrim', d, f) for k, d, f in [
    ('throwspell', 'Spells', '_00E_A2_StarlingdummyProjSP - 0F64A7_Skyrim.esm.yaml'),
    ('throwme', 'MagicEffects', '_00E_A2_StarlingdummyProjME - 0F64A6_Skyrim.esm.yaml'),
    ('throwproj', 'Projectiles', '_00E_A2_StarlingdummyProjectile - 0697F1_Skyrim.esm.yaml'),
    ('throwexp', 'Explosions', '_00E_A2_StarlingdummyExp - 069836_Skyrim.esm.yaml'),
    ('placer', 'Activators', '_00E_A2_StarlingdummyPlacer - 06983E_Skyrim.esm.yaml')]}
DROID = {'Cost': 10, 'HealAmount': 15.0, 'HealInterval': 4, 'HealRadius': 640.0, 'StaggerInterval': 6,
         'StaggerRadius': 300.0, 'StaggerMagnitude': 0.5, 'BaseHealth': 100.0, 'HealthPerLevel': 10.0}
DROID_BASE_NPC = os.path.join(REF, 'mods', 'EGO - Enderal Gameplay Overhaul', 'Npcs',
                              '_00E_StarshipCaveHelpfulSpiderPatrol01 - 130AE8_Skyrim.esm.yaml')   # Starling Spider
STAGGER_CONTACT_MGEF = os.path.join(REF, 'base', 'Skyrim', 'MagicEffects', 'StaggerAttackFFContact - 07809B_Skyrim.esm.yaml')
SPARE_PARTS = '0773ED:Skyrim.esm'           # _00E_CraftingPieces, "Spare Parts"
FOLLOW_PLAYER = '04B037:Skyrim.esm'         # _DefaultFollowPlayer (Follow template, target PlayerRef; SureAI's scenes)
PLAYER_FACTION = '000DB1:Skyrim.esm'
STOMP_SOUND = r'Data\Sound\FX\Zenderal\ZEN_SeismicStomp_01.wav'    # loose, not committed: tools/03-install-sounds.py
SHOCKWAVE = os.path.join(REF, 'mods', 'Apocalypse - Magic of Skyrim', 'Explosions',
                         'WB_AlterationEarth_Explosion_ThrummingStone_Shockwave - 07FE7C_Apocalypse - Magic of Skyrim.esp.yaml')
WARHORN = r'Data\Sound\FX\Zenderal\ZEN_WarBannerHorn_01.wav'    # loose, not committed: tools/03-install-sounds.py
GLORY_ABILITY = {'glo1': 'stompspell', 'glo2': 'swab', 'glo3': 'dsab', 'glo4': 'banner', 'glo5': 'surab'}     # perk -> record its PerkAbilityEffect grants
TRIUMVIRATE = 'Triumvirate - Mage Archetypes.esp'


ARC_RECORDS = ('arspell', 'arme', 'armsg', 'arglob',                       # Arcane Arsenal
               'ndab', 'ndme', 'wardab', 'wardme', 'armorme',             # No Distractions
               'icepower', 'iceme', 'icecd', 'icecdme', 'icearrow', 'iceproj', 'iceball', 'iceballproj',
               'iceexp', 'iceench', 'freezeme',                           # Ice Shot (iceball*: reserved, bows only)
               'ravenme', 'ravenlist')                                    # Send a Raven
ARC_ABILITY = {'arc1': 'arspell', 'arc2': 'ndab'}   # node -> what its perk grants (Ice Shot's shout: the menu, grants)
ICE_LATE_RECORDS = ('iceshout', 'iceword')       # Ice Shot as a talent (2026-10-28), allocated after Sorcery's late records
# Arcane Archery is bows only (curator 2026-10-23): the player's right-hand item type is 7 (crossbows/muskets: 12).
# As a condition on a hit-spell effect (subject = the target) it runs on PlayerRef.
# Sharpshooter is muskets only (curator 2026-10-23): crossbow-type weapons, item type 12 - Ordo's muskets, and the
# list's 4 Xion crossbows, which only Enderal SE - Crossbows' own keyword 00081B tells apart (Prophecy masters
# Skyrim.esm alone). Hit-spell form (on PlayerRef) and perk-tab form.
MUSKET_IN_HAND = ('  - MutagenObjectType: ConditionFloat\n    Data:\n      MutagenObjectType: GetEquippedItemTypeConditionData\n'
                  '      RunOnType: Reference\n      Reference: 000014:Skyrim.esm\n      ItemSource: Right\n    ComparisonValue: 12\n')
MUSKET_TAB_COND = ('    - MutagenObjectType: ConditionFloat\n      Data:\n        MutagenObjectType: GetEquippedItemTypeConditionData\n'
                   '        ItemSource: Right\n      ComparisonValue: 12\n')
# Records added after Arcane Archery's block (2026-10-23), in order - append new ones LAST: Quick Reload's own ability
# (Sharpshooter, muskets only), then the raven's own ability + its effect (Send a Raven stays until killed)
SHARP_RECORDS = ('qrab', 'ravenab', 'ravenabme', 'ravennpc', 'cawsound', 'cawmarker',
                 'owlarmo', 'owlarma', 'owlperk', 'owlhit', 'owlhitme',
                 # Ice Shot delivered by the hit, not the explosion (bears, 2026-10-23)
                 'icewatchab', 'icewatchme', 'icetrig', 'icefrz', 'icefrost', 'icelast', 'icepending', 'iceold',
                 # the shatter's two explosions without their screen blur (curator 2026-10-23)
                 'iceshat1', 'iceshat2',
                 # ice shots left from the last cast (the watcher cleans up at zero)
                 'iceremain')
# Andrasta's Owl's bird: Triumvirate's Call Raven creature as Triumvirate - Enderal Patch wins it (serialized into
# reference/mods/TriumvirateEnderalPatch) - its chaurus-flyer skeleton and graph move and fight in Enderal - minus its
# looping "conscious" crow call, wearing Mihail's Barn Owl mesh owl1go.nif (the one rigged to that skeleton; owl1.nif
# is a baked flight path). Mihail's Barn Owls itself is only ambient scenery (an animated Activator).
TVR = 'Triumvirate - Mage Archetypes.esp'
_TVR_REF = os.path.join(REF, 'mods', 'TriumvirateEnderalPatch')
RAVEN_SRC = os.path.join(_TVR_REF, 'Npcs', f'TVR_Primal_Actor_CallRaven - 14F4E2_{TVR}.yaml')
RAVEN_ARMO_SRC = os.path.join(_TVR_REF, 'Armors', f'TVR_Primal_Armor_CallRaven - 000851_{TVR}.yaml')
RAVEN_ARMA_SRC = os.path.join(_TVR_REF, 'ArmorAddons', f'TVR_Primal_Addon_CallRaven - 000850_{TVR}.yaml')
OWL_MODEL = r'Zenderal\Prophecy\BarnOwl.nif'   # owl1go.nif re-rigged onto the raven skeleton - tools/05-build-owl-mesh.py
OWL_SPAWN_WAV = r'Data\Sound\FX\Zenderal\ZEN_OwlSpawn_01.wav'      # the curator's file - tools/03-install-sounds.py
BOW_IN_HAND = ('  - MutagenObjectType: ConditionFloat\n    Data:\n      MutagenObjectType: GetEquippedItemTypeConditionData\n'
               '      RunOnType: Reference\n      Reference: 000014:Skyrim.esm\n      ItemSource: Right\n    ComparisonValue: 7\n')
SPELL_WARD_RANK2 = '085654:Skyrim.esm'   # _10E_SpellSpellWard; Levin's Spell Ward Rework's shell version wins in the list
ARC_SEEDS = [o('014E7B')]          # ORD_Res_MageWard_Art - the first No Distractions build's shell; unused, kept so Lion's Arrow's IDs stay put
FROST_ENCH = '04605B:Skyrim.esm'   # EnchFrostDamageFFContact
SHOCK_ENCH = '04605C:Skyrim.esm'   # EnchShockDamageFFContact
ICE_EXPLOSION_SRC = os.path.join(REF, 'base', 'Skyrim', 'Explosions', 'MAGIceSpikeVolleyExplosion - 0D6C63_Skyrim.esm.yaml')
# Ice Shot's frost damage: EnchFrostDamageFFContact 04605B (base Enderal's copy: Skyrim.esm references only), made
# target-delivered for the freeze spell the hit trigger casts
FROST_DAMAGE_SRC = os.path.join(REF, 'base', 'Skyrim', 'MagicEffects', 'EnchFrostDamageFFContact - 04605B_Skyrim.esm.yaml')
# SureAI's shatter explosions (ShatterEnemy), as they win: Forgotten Stories overrides 066897, 066895 is base Enderal's.
# Both carry ImageSpaceModifier 04408A at ISRadius 1024 - the blur on a shatter; Ice Shot uses copies without it.
SHATTER_SRC = [('iceshat1', os.path.join(REF, 'base', 'EnderalFS', 'Explosions', '_00E_FrostShatteringExplosion - 066897_Skyrim.esm.yaml')),
               ('iceshat2', os.path.join(REF, 'base', 'Skyrim', 'Explosions', '_00E_FrostShatteringExplosion02 - 066895_Skyrim.esm.yaml'))]


def friendly_immune(entry_point):
    """A perk entry on the owl: x0 incoming damage / spell strength when the attacker (tab 1: the attacker for
    ModIncomingDamage, the caster for ModIncomingSpellMagnitude) is the player, a teammate or a PlayerFaction member
    (curator 2026-10-23: "immune to all friendly fire"). Same shape as Triumvirate's TVR_Primal_Perk_ExtraDamageTaken
    181F3A, which sat on this very creature."""
    cond = lambda fn, extra, last=False: ('    - MutagenObjectType: ConditionFloat\n' + ('' if last else '      Flags:\n      - OR\n')
                                          + f'      Data:\n        MutagenObjectType: {fn}ConditionData\n' + extra
                                          + '      ComparisonValue: 1\n')
    return (f'- MutagenObjectType: PerkEntryPointModifyValue\n  Conditions:\n  - RunOnTabIndex: 1\n    Conditions:\n'
            + cond('GetIsID', '        Object: 000007:Skyrim.esm\n')
            + cond('GetPlayerTeammate', '')
            + cond('GetInFaction', f'        Faction: {PLAYER_FACTION}\n', last=True)
            + f'  EntryPoint: {entry_point}\n  PerkConditionTabCount: 3\n  Modification: Multiply\n  Value: 0\n')


def arcane_hits(a, late, nodeperk, gate, lacks):
    """Arcane Archery's effects on the gun hit spell: Arcane Arsenal's element (one contact-damage effect per element,
    gated on the perk and its global) and Send a Raven (living target, no raven of ours on it yet). Bows only (curator
    2026-10-23): the player's right-hand item type must be 7 - crossbows and Ordo's muskets are 12, and they carry
    WeapTypeBow too, so the perk entries' keyword check lets them through."""
    out = ''
    for value, me in ((1, FIRE_ENCH), (2, FROST_ENCH), (3, SHOCK_ENCH)):
        out += (f"- BaseEffect: {me}\n  Data:\n    Magnitude: {ARC['ElementDamage']}\n    Duration: 0\n" + gate(nodeperk['arc1'])
                + '  - MutagenObjectType: ConditionFloat\n    Data:\n      MutagenObjectType: GetGlobalValueConditionData\n'
                + f"      Global: {a['arglob']}\n    ComparisonValue: {value}\n" + BOW_IN_HAND)
    # Send a Raven: a 1 s spawn/redirect effect. No "not already on the target" condition: a hit-spell effect's
    # conditions are re-checked while it runs, and that one ended the first build's effect - and raven - after 2 s.
    out += (f"- BaseEffect: {a['ravenme']}\n  Data:\n    Duration: 1\n" + gate(nodeperk['arc4'])
            + '  - MutagenObjectType: ConditionFloat\n    Data:\n      MutagenObjectType: GetDeadConditionData\n'
            + BOW_IN_HAND)
    # Ice Shot: a 1 s trigger; its script decides whether this hit was an ice arrow (the watcher's record) and casts
    # the freeze spell on the target - the explosion's enchantment missed big creatures (bears, 2026-10-23)
    out += (f"- BaseEffect: {late['icetrig']}\n  Data:\n    Duration: 1\n" + gate(nodeperk['arc3']) + BOW_IN_HAND)
    return out


def write_arcane(a, newid, write, late):
    """Arcane Archery's hand-built records (curator's design, 2026-10-23). Values in ARC.
    - Arcane Arsenal: a lesser power whose message box sets a global (0 none, 1 fire, 2 frost, 3 lightning); the gun
      hit spell carries the three contact-damage effects, each gated on the perk and the global (write_gunhit).
    - No Distractions: an ability whose script adds the ward on Bow Draw and removes it on release/sheathe. The ward is
      Spell Ward (Rank II)'s 55 ward + 55 armor as plain value modifiers (Ordinator's Mage Ward shape) with Ordinator's
      Mage Ward art - a concentration ward only works while cast, and Enderal's ward art sits in the casting hands.
    - Ice Shot: Flame Shot's pattern (lesser power -> ammo handed out and equipped, old ammo back after) with ice
      arrows, bows only, whose explosion (Enderal's ice-spike burst, no image space) carries frost damage and a
      GetRandomPercent-gated freeze; the freeze is Arctic Wind's frozen ability, the shatter SureAI's (see the script).
    - Send a Raven: a script effect on the gun hit spell; the raven is Triumvirate's, read at runtime."""
    def mgef(fk, edid, name, desc, flags, archetype, cast='FireAndForget', vmad='', extra='', after=''):
        return (f'FormKey: {fk}\nEditorID: {edid}\n' + vmad +
                f"Name:\n  TargetLanguage: English\n  Value: {name}\n" + extra +
                'Flags:\n' + ''.join(f'- {x}\n' for x in flags) +
                f'Archetype:\n  MutagenObjectType: MagicEffectArchetype\n{archetype}' + after +
                f'CastType: {cast}\nDualCastScale: 1\nCastingSoundLevel: Silent\nSounds: []\n'
                f"Description:\n  TargetLanguage: English\n  Value: '{desc}'\n")
    def touch(t):
        return t.replace('CastType: FireAndForget\n', 'CastType: FireAndForget\nTargetType: Touch\n', 1)
    def script(name, props):
        out = f'VirtualMachineAdapter:\n  Scripts:\n  - Name: {name}\n    Properties:\n'
        for pn, kind, val in props:
            key = 'Object' if kind == 'Object' else 'Data'
            out += f'    - MutagenObjectType: Script{kind}Property\n      Name: {pn}\n      {key}: {val}\n'
        return out
    def spell(fk, edid, name, typ, cast, effects, equip='013F44:Skyrim.esm', extra=''):
        t = (f'FormKey: {fk}\nEditorID: {edid}\nName:\n  TargetLanguage: English\n  Value: {name}\n'
             f'MenuDisplayObject: 0435A5:Skyrim.esm\nEquipmentType: {equip}\n'
             "Description:\n  TargetLanguage: English\n  Value: ''\n" + extra)
        if typ: t += f'Type: {typ}\n'
        return t + f'CastType: {cast}\nEffects:\n' + effects
    hidden = ['NoMagnitude', 'NoArea', 'NoDuration', 'HideInUI', 'Painless']

    # --- Arcane Arsenal
    write('Spells', spell(a['arspell'], 'ZP_Prophecy_ArcaneArsenal_Power', 'Arcane Arsenal', 'LesserPower', 'FireAndForget',
                          f"- BaseEffect: {a['arme']}\n  Data: {{}}\n", equip='025BEE:Skyrim.esm',
                          extra='Flags:\n- IgnoreResistance\n- NoAbsorbOrReflect\n'))
    write('MagicEffects', mgef(a['arme'], 'ZP_Prophecy_ArcaneArsenal_Effect', 'Arcane Arsenal', '', hidden, '  Type: Script\n',
                               vmad=script('ZP_ArcaneArsenalEffect', [('Menu', 'Object', a['armsg']), ('Element', 'Object', a['arglob'])])))
    btn = lambda s: f'- Text:\n    TargetLanguage: English\n    Value: {s}\n'
    write('Messages', f"FormKey: {a['armsg']}\nEditorID: ZP_Prophecy_ArcaneArsenal_Menu\nDescription:\n  TargetLanguage: English\n"
                      '  Value: Which element will your arrows carry?\nINAM: 0x00000000\nFlags:\n- MessageBox\nMenuButtons:\n' +
                      btn('Fire') + btn('Frost') + btn('Lightning') + btn('None'))
    write('Globals', f"MutagenObjectType: GlobalShort\nFormKey: {a['arglob']}\nEditorID: ZP_Prophecy_ArcaneArsenal_Element\nData: 0\n")

    # --- No Distractions
    write('Spells', spell(a['ndab'], 'ZP_Prophecy_NoDistractions_Ability', 'No Distractions', 'Ability', 'ConstantEffect',
                          f"- BaseEffect: {a['ndme']}\n  Data: {{}}\n"))
    write('MagicEffects', mgef(a['ndme'], 'ZP_Prophecy_NoDistractions_Effect', 'No Distractions', '', hidden, '  Type: Script\n',
                               cast='ConstantEffect', vmad=script('ZP_NoDistractionsEffect', [('Ward', 'Object', SPELL_WARD_RANK2),
                                                                        ('MagicWard', 'Object', '01EA69:Skyrim.esm')])))
    # The ward is the list's own Spell Ward (Rank II), cast by the script - Levin's Enderal Spell Ward Rework makes it a
    # fire-and-forget shell ward (curator 2026-10-23: 'use the spell ward'). 'wardab'/'wardme'/'armorme' (the first
    # build's hand-made value-modifier ward) stay reserved and unwritten; a save that has the old ability drops it.

    # --- Ice Shot: a talent like Flame Shot (curator 2026-10-28): the spell is a Voice spell, the shout's one word
    # carries the cooldown (ARC['IceCooldown'], Fire Arrow's EGO RecoveryTime), shaped like _00E_A1_Firearrow 05C233 /
    # _00E_A1_FirearrowWord01 05C274. The menu grants the shout (TeachWord + UnlockWord + AddShout) and takes back the
    # spell a 2026-10-23..27 save got as a lesser power. 'icecd'/'icecdme' (the first build's cooldown) stay unwritten.
    write('Spells', spell(a['icepower'], 'ZP_Prophecy_IceShot_Power', 'Ice Shot', 'Voice', 'FireAndForget',
                          f"- BaseEffect: {a['iceme']}\n  Data:\n    Duration: {ARC['IceSeconds']}\n", equip='013F44:Skyrim.esm',
                          extra='Flags:\n- IgnoreResistance\n- NoAbsorbOrReflect\n'))
    write('WordsOfPower', f"FormKey: {a['iceword']}\nEditorID: ZP_Prophecy_IceShot_Word\nName:\n  TargetLanguage: English\n"
                          "  Value: Ice Shot\nTranslation:\n  TargetLanguage: English\n  Value: Ice Shot\n")
    write('Shouts', f"FormKey: {a['iceshout']}\nEditorID: ZP_Prophecy_IceShot\nName:\n  TargetLanguage: English\n  Value: Ice Shot\n"
                    "MenuDisplayObject: 04E264:Skyrim.esm\nDescription:\n  TargetLanguage: English\n"
                    f"  Value: 'Adds {ARC['IceArrows']} ice arrows to your quiver: {ARC['IceDamage']} frost damage, and the target freezes"
                    f" for {ARC['FreezeSeconds']} seconds until your next arrow shatters it.'\n"
                    f"WordsOfPower:\n- Word: {a['iceword']}\n  Spell: {a['icepower']}\n  RecoveryTime: {ARC['IceCooldown']}\n")
    write('MagicEffects', mgef(a['iceme'], 'ZP_Prophecy_IceShot_Effect', 'Ice Shot', '', ['NoMagnitude', 'NoArea', 'HideInUI', 'Painless'],
                               '  Type: Script\n', vmad=script('ZP_IceShotEffect', [
                                   ('IceArrow', 'Object', a['icearrow']),
                                   ('AmmoList', 'Object', '13E955:Skyrim.esm'),          # _00E_A1_FirearrowAmmoFormlist
                                   ('OldAmmo', 'Object', late['iceold']),
                                   ('Remaining', 'Object', late['iceremain']),
                                   ('ArrowCount', 'Int', ARC['IceArrows']),
                                   ('MagickaCost', 'Float', ARC['IceMagicka'])])))
    # --- the ammo: an arrow (the fire arrow's shape) and a musket ball (Flame Shot's cleaned copy of Ordo's)
    write('Ammunitions', f"""FormKey: {a['icearrow']}
EditorID: ZP_Prophecy_IceArrow
Name:
  TargetLanguage: English
  Value: Ice Arrow
Model:
  File: Weapons\\Steel\\SteelArrow.nif
  Data: 0x020000000000000000000000
PickUpSound: 03E7B7:Skyrim.esm
PutDownSound: 03E877:Skyrim.esm
Description:
  TargetLanguage: English
  Value: ''
Keywords:
- 01CEAD:Skyrim.esm
Projectile: {a['iceproj']}
Flags:
- NonBolt
Damage: 7
Weight: 0.1
""")
    # an exploding ARROW (Flame Shot ranks 2/3's _00E_A1_FireArrow_ProjectileL02 0670DA shape): the hit is a real weapon
    # hit, which the hit trigger needs. The first build copied rank 1's Missile type, whose hits never reach
    # ApplyCombatHitSpell (in game 2026-10-23: no freeze once the trigger replaced the explosion's enchantment)
    write('Projectiles', f"""FormKey: {a['iceproj']}
EditorID: ZP_Prophecy_IceArrowProjectile
Model:
  File: Weapons\\Steel\\SteelArrowFlight.nif
  Data: 0x020000000000000000000000
Flags:
- Explosion
- DisableCombatAimCorrection
Type: Arrow
Gravity: 0.35
Speed: 3600
Range: 60000
Light: 020BF4:Skyrim.esm
Explosion: {a['iceexp']}
Sound: 03F2B4:Skyrim.esm
FadeDuration: 5
ImpactForce: 1
CollisionRadius: 0.5
RelaunchInterval: 0.25
MuzzleFlashModel: ''
SoundLevel: 1
""")
    # 'iceball'/'iceballproj' stay reserved and unwritten: Ice Shot is bows only (curator 2026-10-23)
    # --- the burst: Enderal's ice-spike volley explosion, visuals only (no physical damage, no enchantment). It carried
    # the frost + freeze enchantment until 2026-10-23; that missed big creatures (bears), so the hit delivers them now
    t = open(ICE_EXPLOSION_SRC, encoding='utf-8').read().replace('\r\n', '\n')
    t = re.sub(r'^Name:\n(?:  .*\n)*', '', t, count=1, flags=re.M)
    for pat, rep in [(r'^FormKey: .*$', f"FormKey: {a['iceexp']}"), (r'^EditorID: .*$', 'EditorID: ZP_Prophecy_IceShot_Explosion'),
                     (r'^Damage: .*$', 'Damage: 0'), (r'^Force: .*$', 'Force: 10')]:
        t, n = re.subn(pat, rep, t, count=1, flags=re.M); assert n == 1, pat
    assert 'ImageSpaceModifier' not in t and 'ObjectEffect' not in t
    t = re.sub(r'^Version2: .*\n', '', t, flags=re.M)
    write('Explosions', t)
    # 'iceench' (the explosion's enchantment) stays reserved and unwritten
    # --- the freeze, cast on the arrow's target by ZP_IceShotTriggerEffect: frost damage + the freeze, target-delivered
    write('Spells', spell(late['icefrz'], 'ZP_Prophecy_IceShot_FreezeSpell', 'Ice Shot', None, 'FireAndForget',
                          f"- BaseEffect: {late['icefrost']}\n  Data:\n    Magnitude: {ARC['IceDamage']}\n"
                          f"- BaseEffect: {a['freezeme']}\n  Data:\n    Duration: {ARC['FreezeSeconds']}\n",
                          extra='Flags:\n- NoAbsorbOrReflect\n').replace('CastType: FireAndForget\n', 'CastType: FireAndForget\nTargetType: TargetActor\n'))
    t = open(FROST_DAMAGE_SRC, encoding='utf-8').read().replace('\r\n', '\n')
    for pat, rep in [(r'^FormKey: .*$', f"FormKey: {late['icefrost']}"), (r'^EditorID: .*$', 'EditorID: ZP_Prophecy_IceShot_FrostDamage'),
                     (r'^TargetType: Touch$', 'TargetType: TargetActor')]:
        t, n = re.subn(pat, rep, t, count=1, flags=re.M); assert n == 1, pat
    t = re.sub(r'^Version2: .*\n', '', t, flags=re.M)
    assert re.search(r':(?!Skyrim\.esm)[^\s:]+\.es[mp]', t) is None, 'frost damage copy names another plugin'
    write('MagicEffects', t)
    write('MagicEffects', mgef(a['freezeme'], 'ZP_Prophecy_IceShot_FreezeEffect', 'Frozen', '',
                               ['Hostile', 'Detrimental', 'NoMagnitude', 'NoArea', 'HideInUI'], '  Type: Script\n',
                               vmad=script('ZP_IceShotFreezeEffect', [
                                   ('MagicNoFreeze', 'Object', '0EEE66:Skyrim.esm'),
                                   ('IceShader', 'Object', '0DC20E:Skyrim.esm'),         # FrostIceFormFXShader02 (_00E_Frozen_ME's)
                                   ('FreezeSound', 'Object', '10A6A0:Skyrim.esm'),       # _00E_A1_ArcticWindFreezeM
                                   ('ActorTypeNPC', 'Object', '013794:Skyrim.esm'),
                                   ('DraugrRace', 'Object', '000D53:Skyrim.esm'),
                                   ('ShatterExplosion', 'Object', late['iceshat1']),
                                   ('ShatterExplosion02', 'Object', late['iceshat2']),
                                   ('IceGoreExplosion', 'Object', '033468:Skyrim.esm'),
                                   ('ShatteredPile', 'Object', '0671F3:Skyrim.esm'),
                                   ('ImpactIce', 'Object', '02398B:Skyrim.esm')])).replace(
                                       'CastType: FireAndForget\n', 'CastType: FireAndForget\nTargetType: TargetActor\n'))
    for key, src in SHATTER_SRC:   # SureAI's shatter explosions minus their screen blur (04408A, ISRadius 1024)
        t = open(src, encoding='utf-8').read().replace('\r\n', '\n')
        edid = re.search(r'^EditorID: (.+?)\s*$', t, re.M).group(1)
        for pat, rep in [(r'^FormKey: .*$', f"FormKey: {late[key]}"), (r'^EditorID: .*$', f'EditorID: ZP_Prophecy_IceShot{edid[4:]}')]:
            t, n = re.subn(pat, rep, t, count=1, flags=re.M); assert n == 1, pat
        t, n = re.subn(r'^(?:ImageSpaceModifier|ISRadius): .*\n', '', t, flags=re.M)
        assert n == 2, (src, 'image space lines', n)
        if key == 'iceshat2':   # the one the shatter still places: no push, so nearby clutter (logs) stays put
            t, n = re.subn(r'^Force: .*$', 'Force: 0', t, count=1, flags=re.M)
            assert n == 1, 'shatter burst force'
        t = re.sub(r'^Version2: .*\n', '', t, flags=re.M)
        t = re.sub(r'^Name:\n(?:  .*\n)*', '', t, count=1, flags=re.M)
        write('Explosions', t)
    # --- the hit trigger (on the gun hit spell, arcane_hits) and the watcher ability (from the perk) that records ice shots
    globals_ = [('icelast', 'ZP_Prophecy_IceShot_LastShot'), ('icepending', 'ZP_Prophecy_IceShot_Pending'),
                ('iceremain', 'ZP_Prophecy_IceShot_Remaining')]
    for k, edid in globals_:
        write('Globals', f"MutagenObjectType: GlobalFloat\nFormKey: {late[k]}\nEditorID: {edid}\nData: 0\n")
    write('FormLists', f"FormKey: {late['iceold']}\nEditorID: ZP_Prophecy_IceShot_OldAmmo\n")
    write('MagicEffects', touch(mgef(late['icetrig'], 'ZP_Prophecy_IceShot_HitTrigger', 'Ice Shot', '',
                               ['NoMagnitude', 'NoArea', 'HideInUI', 'Painless'], '  Type: Script\n',
                               vmad=script('ZP_IceShotTriggerEffect', [
                                   ('Freeze', 'Object', late['icefrz']), ('FreezeEffect', 'Object', a['freezeme']),
                                   ('LastShot', 'Object', late['icelast']), ('Pending', 'Object', late['icepending']),
                                   ('IceArrow', 'Object', a['icearrow'])]))))   # strips ice arrows off the target
    write('Spells', spell(late['icewatchab'], 'ZP_Prophecy_IceShot_Watcher', 'Ice Shot', 'Ability', 'ConstantEffect',
                          f"- BaseEffect: {late['icewatchme']}\n  Data: {{}}\n"))
    write('MagicEffects', mgef(late['icewatchme'], 'ZP_Prophecy_IceShot_WatcherEffect', 'Ice Shot', '', hidden,
                               '  Type: Script\n', cast='ConstantEffect',
                               vmad=script('ZP_IceShotWatcherEffect', [
                                   ('IceArrow', 'Object', a['icearrow']), ('OldAmmo', 'Object', late['iceold']),
                                   ('LastShot', 'Object', late['icelast']), ('Pending', 'Object', late['icepending']),
                                   ('Remaining', 'Object', late['iceremain'])])))

    # --- Andrasta's Owl (was Send a Raven; curator 2026-10-23): the hit effect only spawns or redirects; the bird's own
    # ability (RavenBrain) flies it and cleans up when it dies - it stays until killed. The bird is Triumvirate's Call
    # Raven creature (chaurus-flyer skeleton + graph, which move and fight in Enderal) wearing Mihail's owl1go.nif,
    # with no sound types; its strikes drain Magicka to the player.
    write('MagicEffects', touch(mgef(a['ravenme'], 'ZP_Prophecy_SendRaven_Effect', "Andrasta's Owl", '',
                               ['NoMagnitude', 'NoArea', 'HideInUI', 'Painless'], '  Type: Script\n',
                               vmad=script('ZP_SendRavenEffect', [('Ravens', 'Object', a['ravenlist']),
                                                                  ('PlayerFaction', 'Object', PLAYER_FACTION),
                                                                  ('RavenBrain', 'Object', late['ravenab']),
                                                                  ('BirdBase', 'Object', late['ravennpc']),
                                                                  ('SpawnSound', 'Object', late['cawmarker'])]))))
    # the owl: Triumvirate's raven record (its winning copy) with no sound types - its only one was the looping crow
    # call TVR_Primal_Descriptor_Crow_Conscious 000853 - named Barn Owl, wearing the owl skin, with the owl's
    # Magicka-drain perk in place of Triumvirate's TVR_Primal_Perk_ExtraDamageTaken 181F3A
    t = open(RAVEN_SRC, encoding='utf-8').read().replace('\r\n', '\n')
    for pat, rep in [(r'^FormKey: .*$', f"FormKey: {late['ravennpc']}"), (r'^EditorID: .*$', 'EditorID: ZP_Prophecy_SendOwl_Owl'),
                     (r'^WornArmor: .*$', f"WornArmor: {late['owlarmo']}"),
                     (r'^Perks:\n(?:- .*\n(?:  .*\n)*)', f"Perks:\n- Perk: {late['owlperk']}\n  Rank: 1\n  Fluff: 0x000000\n"),
                     (r'^(Name:\n(?:  TargetLanguage: English\n)?  Value: ).*$', r'\1Barn Owl')]:
        t, n = re.subn(pat, rep, t, count=1, flags=re.M); assert n == 1, pat
    t, n = re.subn(r'^Sound:\n(?:  .*\n)*', '', t, count=1, flags=re.M)
    assert n == 1 and f'000853:{TVR}' not in t and f'181F3A:{TVR}' not in t, "raven's sound block / perk not where expected"
    t = re.sub(r'^(?:IsCompressed|MajorRecordFlagsRaw): .*\n', '', t, flags=re.M)
    t = re.sub(r'^SkyrimMajorRecordFlags:\n- Compressed\n', '', t, flags=re.M)
    write('Npcs', t)
    # the owl skin: Triumvirate's crow skin (armor + addon on the raven race) with Mihail's owl1go.nif as its model
    for src, key, edid, extra in [(RAVEN_ARMA_SRC, 'owlarma', 'ZP_Prophecy_SendOwl_SkinAddon', []),
                                  (RAVEN_ARMO_SRC, 'owlarmo', 'ZP_Prophecy_SendOwl_Skin',
                                   [(r'^(Name:\n(?:  TargetLanguage: English\n)?  Value: ).*$', r'\1Barn Owl'),
                                    (r'^Armature:\n- .*$', f"Armature:\n- {late['owlarma']}")])]:
        t = open(src, encoding='utf-8').read().replace('\r\n', '\n')
        for pat, rep in [(r'^FormKey: .*$', f"FormKey: {late[key]}"), (r'^EditorID: .*$', f'EditorID: {edid}')] + extra:
            t, n = re.subn(pat, rep, t, count=1, flags=re.M); assert n == 1, (edid, pat)
        if key == 'owlarma':
            t, n = re.subn(r'^(    File: ).*basecrow\.nif\s*$', lambda m: m.group(1) + OWL_MODEL, t, count=1, flags=re.M | re.I)
            assert n == 1, 'crow skin model not where expected'
        write('ArmorAddons' if key == 'owlarma' else 'Armors', t)
    # its strikes: a perk on the owl applies the drain as a combat-hit spell
    write('Perks', f"FormKey: {late['owlperk']}\nEditorID: ZP_Prophecy_SendOwl_StrikePerk\nName:\n  TargetLanguage: English\n"
                   "  Value: Andrasta's Owl\nNumRanks: 1\nEffects:\n- MutagenObjectType: PerkEntryPointSelectSpell\n"
                   f"  EntryPoint: ApplyCombatHitSpell\n  PerkConditionTabCount: 3\n  Spell: {late['owlhit']}\n"
                   + ''.join(friendly_immune(ep) for ep in ('ModIncomingDamage', 'ModIncomingSpellMagnitude')))
    write('Spells', spell(late['owlhit'], 'ZP_Prophecy_SendOwl_StrikeSpell', "Andrasta's Owl", None, 'FireAndForget',
                          f"- BaseEffect: {late['owlhitme']}\n  Data: {{}}\n",
                          extra='Flags:\n- NoAbsorbOrReflect\n').replace('CastType: FireAndForget\n', 'CastType: FireAndForget\nTargetType: Touch\n'))
    write('MagicEffects', touch(mgef(late['owlhitme'], 'ZP_Prophecy_SendOwl_StrikeEffect', 'Magicka Drain', '',
                               ['Hostile', 'Detrimental', 'NoMagnitude', 'NoArea', 'NoDuration', 'HideInUI'], '  Type: Script\n',
                               vmad=script('ZP_OwlAbsorbEffect', [('Amount', 'Float', ARC['OwlDrain'])]),
                               after='HitShader: 057C67:Skyrim.esm\n')))       # AbsorbMagickaConstant's shader
    # the spawn sound (the curator's file), played once; the bird is silent after it
    write('SoundDescriptors', f"""FormKey: {late['cawsound']}
EditorID: ZP_Prophecy_SendOwl_SpawnSound
Type: Standard
Category: 01A0BD:Skyrim.esm
SoundFiles:
- {OWL_SPAWN_WAV}
OutputModel: 0B6463:Skyrim.esm
LoopAndRumble: {{}}
Priority: 128
""")
    write('SoundMarkers', f"FormKey: {late['cawmarker']}\nEditorID: ZP_Prophecy_SendOwl_SpawnMarker\nSoundDescriptor: {late['cawsound']}\n")
    write('FormLists', f"FormKey: {a['ravenlist']}\nEditorID: ZP_Prophecy_SendRaven_Current\n")
    write('Spells', spell(late['ravenab'], 'ZP_Prophecy_SendRaven_RavenAbility', "Andrasta's Owl", 'Ability', 'ConstantEffect',
                          f"- BaseEffect: {late['ravenabme']}\n  Data: {{}}\n"))
    write('MagicEffects', mgef(late['ravenabme'], 'ZP_Prophecy_SendRaven_RavenEffect', "Andrasta's Owl", '',
                               hidden + ['NoDeathDispel'], '  Type: Script\n', cast='ConstantEffect',
                               vmad=script('ZP_RavenBrainEffect', [('Ravens', 'Object', a['ravenlist']),
                                                                   ('PlayerMagickaPerSecond', 'Float', ARC['OwlRegen'])])))

    # --- Lion's Arrow, bows only: its in-combat effect (ORD_LionsArrow_Script, OnPlayerBowShot) only with a bow
    p = [x for x in glob.glob(os.path.join(ESP, 'Spells', '*.yaml')) if os.path.basename(x).startswith('ZP_ORD_Arc_LionsArrow_Spell_Ab - ')]
    assert len(p) == 1, "Lion's Arrow ability moved"
    t = open(p[0], encoding='utf-8').read().replace('\r\n', '\n')
    incombat = '      MutagenObjectType: IsInCombatConditionData\n    ComparisonValue: 1\n'
    assert t.count(incombat) == 1, "Lion's Arrow in-combat condition not where expected"
    t = t.replace(incombat, incombat + '  - MutagenObjectType: ConditionFloat\n    Data:\n'
                  '      MutagenObjectType: GetEquippedItemTypeConditionData\n      ItemSource: Right\n    ComparisonValue: 7\n')
    open(p[0], 'w', encoding='utf-8', newline='\r\n').write(t)


def write_glory(g, write):
    """Glory's records (curator's design, 2026-10-21; Gap Closer became Seismic Stomp 2026-10-22).
    Seismic Stomp follows Enderal's own stomp beat (_00E_MQ15_Functions.TealorBreakWall: PlayIdle _00E_IdleStomp,
    wait 0.5 s, PlaceAtMe a shockwave, ShakeCamera) - the idle is Enderal's FNIS basic idle "Stomp" (stomp.hkx in
    FNIS_Enderal_Behavior, which Pandora's 0_Master links) and Enderal plays it on the player too (Theriantrophist).
    The shockwave is Apocalypse's Thrumming Stone shockwave explosion copied with its model (Apocalypse's BSA mesh),
    without its ISM, with the curator's stomp sound and Enderal's FXDragonTailstompImpactSet. Knockback is the script's
    PushActorAway on every hostile in range; the bleed is a target-delivered copy of Bleeding Shot's (Monk) bleed.
    War Banner is a lesser power with Templar's cooldown pattern (a script-less effect checked by HasMagicEffect).
    Its chains are Triumvirate's Stave of Binding proc (TVR_Shaman_Spell_StaveBinding_Proc 423DA8), read at runtime
    with GetFormFromFile, so the plugin does not master Triumvirate."""
    def mgef(fk, edid, name, desc, flags, archetype, cast='FireAndForget', vmad='', extra=''):
        return (f'FormKey: {fk}\nEditorID: {edid}\n' + vmad +
                f"Name:\n  TargetLanguage: English\n  Value: {name}\n" + extra +
                'Flags:\n' + ''.join(f'- {x}\n' for x in flags) +
                f'Archetype:\n  MutagenObjectType: MagicEffectArchetype\n{archetype}'
                f'CastType: {cast}\nDualCastScale: 1\nCastingSoundLevel: Silent\nSounds: []\n'
                f"Description:\n  TargetLanguage: English\n  Value: '{desc}'\n")
    def script(name, props):
        out = f'VirtualMachineAdapter:\n  Scripts:\n  - Name: {name}\n    Properties:\n'
        for pn, kind, val in props:
            key = 'Object' if kind == 'Object' else 'Data'
            out += f'    - MutagenObjectType: Script{kind}Property\n      Name: {pn}\n      {key}: {val}\n'
        return out
    def spell(fk, edid, name, typ, cast, effects, equip='013F44:Skyrim.esm', extra=''):
        t = (f'FormKey: {fk}\nEditorID: {edid}\nName:\n  TargetLanguage: English\n  Value: {name}\n'
             f'MenuDisplayObject: 0435A5:Skyrim.esm\nEquipmentType: {equip}\n'
             "Description:\n  TargetLanguage: English\n  Value: ''\n" + extra)
        if typ: t += f'Type: {typ}\n'
        return t + f'CastType: {cast}\nEffects:\n' + effects

    # --- Seismic Stomp: lesser power -> scripted stomp (idle, shockwave, knockback, bleed); 60 s cooldown effect
    write('Spells', spell(g['stompspell'], 'ZP_Prophecy_SeismicStomp_Power', 'Seismic Stomp', 'LesserPower', 'FireAndForget',
                          f'- BaseEffect: {g["stompme"]}\n  Data:\n    Duration: 6\n', equip='025BEE:Skyrim.esm',   # outlasts the script's waits, even slowed
                          extra='Flags:\n- IgnoreResistance\n- NoAbsorbOrReflect\n'))
    write('MagicEffects', mgef(g['stompme'], 'ZP_Prophecy_SeismicStomp_Effect', 'Seismic Stomp', '',
                               ['NoMagnitude', 'NoArea', 'HideInUI', 'Painless'], '  Type: Script\n',
                               vmad=script('ZP_SeismicStompEffect', [
                                   ('StompIdle', 'Object', '146675:Skyrim.esm'),        # _00E_IdleStomp
                                   ('Shockwave', 'Object', g['stompexp']),
                                   ('Bleed', 'Object', g['bleedspell']),
                                   ('SlowTime', 'Object', g['slowspell']),
                                   ('Cooldown', 'Object', g['stompcd']),
                                   ('CooldownEffect', 'Object', g['stompcdme'])])))
    t = open(SHOCKWAVE, encoding='utf-8').read().replace('\r\n', '\n')
    t = re.sub(r'^FormKey: .*$', f'FormKey: {g["stompexp"]}', t, count=1, flags=re.M)
    t = re.sub(r'^EditorID: .*$', 'EditorID: ZP_Prophecy_SeismicStomp_Explosion', t, count=1, flags=re.M)
    t = re.sub(r'^(?:ImageSpaceModifier|ISRadius): .*\n', '', t, flags=re.M)
    t = re.sub(r'^Sound1: .*$', f'Sound1: {g["stompsound"]}', t, count=1, flags=re.M)
    t = re.sub(r'^ImpactDataSet: .*$', 'ImpactDataSet: 03F819:Skyrim.esm', t, count=1, flags=re.M)   # FXDragonTailstompImpactSet
    assert 'Apocalypse' not in t and 'AlterationEarth_Explosion_Massive.nif' in t, 'shockwave copy still names Apocalypse'
    write('Explosions', t)
    write('SoundDescriptors', f"""FormKey: {g['stompsound']}
EditorID: ZP_Prophecy_SeismicStomp_Sound
Type: Standard
Category: 01A0BD:Skyrim.esm
SoundFiles:
- {STOMP_SOUND}
OutputModel: 0B6463:Skyrim.esm
LoopAndRumble: {{}}
Priority: 128
""")
    bleed_src = glob.glob(os.path.join(ESP, 'MagicEffects', '* - 000829_*'))
    assert len(bleed_src) == 1 and 'Monk' in os.path.basename(bleed_src[0]), "Bleeding Shot's bleed MGEF moved"
    t = open(bleed_src[0], encoding='utf-8').read().replace('\r\n', '\n')
    t = re.sub(r'^FormKey: .*$', f'FormKey: {g["bleedme"]}', t, count=1, flags=re.M)
    t = re.sub(r'^EditorID: .*$', 'EditorID: ZP_Prophecy_SeismicStomp_BleedEffect', t, count=1, flags=re.M)
    t2 = re.sub(r'^TargetType: Touch$', 'TargetType: TargetActor', t, count=1, flags=re.M)
    assert t2 != t, 'bleed MGEF is no longer Touch'
    write('MagicEffects', t2)
    write('Spells', spell(g['bleedspell'], 'ZP_Prophecy_SeismicStomp_Bleed', 'Seismic Stomp', None, 'FireAndForget',
                          f'- BaseEffect: {g["bleedme"]}\n  Data:\n    Magnitude: 10\n    Duration: 5\n',
                          extra='Flags:\n- NoAbsorbOrReflect\n') .replace('CastType: FireAndForget\n', 'CastType: FireAndForget\nTargetType: TargetActor\n'))
    # slow time: Quick Reflexes' self effect (Flow State's) copied, its dispel-after-delay script set to STOMP_SLOW[1]
    src = glob.glob(os.path.join(ESP, 'MagicEffects', f"* - {g['quickreflexes_me'].split(':')[0]}_*"))
    assert len(src) == 1 and 'QuickReflexes_Effect_Self' in os.path.basename(src[0]), 'Quick Reflexes self effect moved'
    t = open(src[0], encoding='utf-8').read().replace('\r\n', '\n')
    t = t.replace(g['quickreflexes_me'], g['slowme'])                 # FormKey + its own no-recast condition
    t = re.sub(r'^EditorID: .*$', 'EditorID: ZP_Prophecy_SeismicStomp_SlowTimeEffect', t, count=1, flags=re.M)
    # its own keyword, not PerkQuickReflexesKeyword 046BB3: Enderal's Keeper perks (Fast Reflexes, Steadfast) set
    # the player's slowdown to 0.5 for anything carrying 046BB3, and Flow State keeps 046BB3 for itself
    assert t.count('- 046BB3:Skyrim.esm\n') == 1, 'Quick Reflexes keyword not where expected'
    t = t.replace('- 046BB3:Skyrim.esm\n', f"- {g['slowkw']}\n")
    # no screen blur (curator, 2026-10-22): drop Quick Reflexes' MagicImodBasicScript, which applies QuickReflexesImod
    # 10C761 (radial blur, double vision, depth of field) for the whole effect. Flow State keeps it.
    t, n = re.subn(r'^  - Name: MagicImodBasicScript\n    Properties:\n(?:    .*\n)+?(?=  - Name: )', '', t, count=1, flags=re.M)
    assert n == 1 and '10C761' not in t, 'Quick Reflexes blur script not found on the slow-time copy'
    t2 = re.sub(r'(Name: ORD_DelayUntilDispel\n      Data: )\S+', lambda m: m.group(1) + str(STOMP_SLOW[1]), t, count=1)
    assert t2 != t and t2.count(g['slowme']) == 2, 'slow-time copy not as expected'
    write('MagicEffects', t2)
    write('Keywords', f"FormKey: {g['slowkw']}\nEditorID: ZP_Prophecy_SeismicStompSlowKeyword\nColor: '#00000000'\n")
    write('Spells', spell(g['slowspell'], 'ZP_Prophecy_SeismicStomp_SlowTime', 'Seismic Stomp', None, 'FireAndForget',
                          f'- BaseEffect: {g["slowme"]}\n  Data:\n    Magnitude: {STOMP_SLOW[0]}\n    Duration: {STOMP_SLOW[1]}\n',
                          extra='Flags:\n- NoAbsorbOrReflect\n'))
    write('Spells', spell(g['stompcd'], 'ZP_Prophecy_SeismicStomp_Cooldown', 'Seismic Stomp', None, 'FireAndForget',
                          f'- BaseEffect: {g["stompcdme"]}\n  Data:\n    Duration: 30\n', extra='Flags:\n- NoAbsorbOrReflect\n'))
    write('MagicEffects', mgef(g['stompcdme'], 'ZP_Prophecy_SeismicStomp_CooldownEffect', 'Seismic Stomp',
                               'Seismic Stomp can be used again in <dur> seconds.', ['Recover'], '  Type: Script\n'))

    # --- Second Wind: an ability whose script restores Stamina on hits taken at half Health or less
    write('Spells', spell(g['swab'], 'ZP_Prophecy_SecondWind_Ability', 'Second Wind', 'Ability', 'ConstantEffect',
                          f'- BaseEffect: {g["swme"]}\n  Data: {{}}\n'))
    write('MagicEffects', mgef(g['swme'], 'ZP_Prophecy_SecondWind_Effect', 'Second Wind',
                               'While at or below half Health, every hit you take restores 20 Stamina.',
                               ['NoMagnitude', 'NoArea', 'NoDuration', 'Painless'], '  Type: Script\n', cast='ConstantEffect',
                               vmad=script('ZP_SecondWindEffect', [('Stamina', 'Float', 20), ('HealthThreshold', 'Float', 0.5)])))

    # --- Surrounded: an ability whose script restores Stamina each second while enough enemies are close
    write('Spells', spell(g['surab'], 'ZP_Prophecy_Surrounded_Ability', 'Surrounded', 'Ability', 'ConstantEffect',
                          f'- BaseEffect: {g["surme"]}\n  Data: {{}}\n'))
    write('MagicEffects', mgef(g['surme'], 'ZP_Prophecy_Surrounded_Effect', 'Surrounded',
                               'While 3 or more enemies are close to you, your Stamina regenerates 2 points per second.',
                               ['NoMagnitude', 'NoArea', 'NoDuration', 'Painless'], '  Type: Script\n', cast='ConstantEffect',
                               vmad=script('ZP_SurroundedEffect', [('Radius', 'Float', SURROUNDED['Radius']),
                                                                   ('MinEnemies', 'Int', SURROUNDED['MinEnemies']),
                                                                   ('StaminaPerSecond', 'Float', SURROUNDED['StaminaPerSecond'])])))

    # --- Dragon Scale: Enderal's own resist abilities' effects at 25
    write('Spells', spell(g['dsab'], 'ZP_Prophecy_DragonScale_Ability', 'Dragon Scale', 'Ability', 'ConstantEffect',
                          ''.join(f'- BaseEffect: {fx}\n  Data:\n    Magnitude: 25\n'
                                  for fx in ('024314:Skyrim.esm', '024315:Skyrim.esm', '024318:Skyrim.esm'))))  # AbResistFire/Frost/Shock

    # --- War Banner: lesser power -> 15 s scripted banner; 300 s cooldown effect
    write('Spells', spell(g['banner'], 'ZP_Prophecy_WarBanner_Power', 'War Banner', 'LesserPower', 'FireAndForget',
                          f'- BaseEffect: {g["bannerme"]}\n  Data:\n    Duration: 15\n', equip='025BEE:Skyrim.esm',
                          extra='Flags:\n- IgnoreResistance\n- NoAbsorbOrReflect\n'))
    write('MagicEffects', mgef(g['bannerme'], 'ZP_Prophecy_WarBanner_Effect', 'War Banner',
                               'Near your banner you heal 20 Health per second; enemies who come close are bound in chains.',
                               ['NoMagnitude', 'NoArea', 'Painless'], '  Type: Script\n',
                               vmad=script('ZP_WarBannerEffect', [
                                   ('Banner', 'Object', '060165:Skyrim.esm'),          # CivilWarBanner02: Enderal's camp banner frame (no cloth)
                                   ('Cloth', 'Object', '0EAC23:Skyrim.esm'),           # _00E_BannerNehrimesian, hung from the frame's crossbar
                                   ('HornSound', 'Object', g['hornmarker']),
                                   ('Cooldown', 'Object', g['cdspell']),
                                   ('CooldownEffect', 'Object', g['cdme']),
                                   ('Radius', 'Float', 400), ('HealPerSecond', 'Float', 20)])))
    write('SoundDescriptors', f"""FormKey: {g['hornsound']}
EditorID: ZP_Prophecy_WarBanner_HornSound
Type: Standard
Category: 01A0BD:Skyrim.esm
SoundFiles:
- {WARHORN}
OutputModel: 0B6463:Skyrim.esm
LoopAndRumble: {{}}
Priority: 128
""")
    write('SoundMarkers', f"FormKey: {g['hornmarker']}\nEditorID: ZP_Prophecy_WarBanner_HornMarker\nSoundDescriptor: {g['hornsound']}\n")
    write('Spells', spell(g['cdspell'], 'ZP_Prophecy_WarBanner_Cooldown', 'War Banner', None, 'FireAndForget',
                          f'- BaseEffect: {g["cdme"]}\n  Data:\n    Duration: 300\n',
                          extra='Flags:\n- NoAbsorbOrReflect\n'))
    write('MagicEffects', mgef(g['cdme'], 'ZP_Prophecy_WarBanner_CooldownEffect', 'War Banner',
                               'War Banner can be raised again in <dur> seconds.', ['Recover'], '  Type: Script\n'))


# Necromancy's records (2026-10-23), in order - append new ones LAST
NEC_RECORDS = ('effspell', 'effme', 'armorspell', 'armorme',                                     # Dark Effigy
               'wspower', 'wsme', 'wsblast', 'wsblastme', 'wsvisual', 'wscd', 'wscdme',          # A Willing Sacrifice
               'legpower', 'legme', 'legwar', 'legarch', 'legmage', 'legab', 'legabme', 'leglist')   # Legion of the Damned
NEC_ABILITY = {'nec3': 'wspower', 'nec5': 'legpower'}   # node -> the power its perk grants
# Base Enderal's player skeleton summon ("Fleshless Lost One"). EGO's winning copy adds FS/EGO forms (a health-bar
# script, perks) the plugin does not master, so the Legion is built from Skyrim.esm's.
SKELETON_SRC = os.path.join(REF, 'base', 'Skyrim', 'Npcs', '_07E_SummonableSkeleton_Player - 11C391_Skyrim.esm.yaml')
SUMMON_SPELL_SRC = os.path.join(REF, 'mods', 'EGO', 'Spells', '_07E_SpellSummonSkeleton - 11C383_Skyrim.esm.yaml')
CORPSE_EXP_SRC = os.path.join(REF, 'base', 'EnderalFS', 'Explosions',
                              '_00E_FS_Entropy_CorpseExplosionEXP - 02F27D_Enderal - Forgotten Stories.esm.yaml')


def write_necro(n, nodeperk, write):
    """Necromancy's hand-built records (curator's design, 2026-10-23). Values in NEC.
    - Corpse Fever: entry points on the perk itself (main()).
    - Dark Effigy: an Entropy spell (Summon Ancestor's casting look, copied) whose script plants a hagraven goat pole
      and once a second gives allies near it ArmorSpell and heals the player's undead summons (ZP_DarkEffigyEffect).
    - A Willing Sacrifice: a lesser power whose script explodes every commanded actor and Legion skeleton (Forgotten
      Stories' Corpse Explosion look and damage rule); The Dead Don't Forget is a perk that script checks.
    - Legion of the Damned: a lesser power that adds Arcane Fever and places six skeleton copies of base Enderal's
      player summon, with their own lifetime ability."""
    def mgef(fk, edid, name, desc, flags, archetype, cast='FireAndForget', vmad='', extra='', after=''):
        return (f'FormKey: {fk}\nEditorID: {edid}\n' + vmad +
                f"Name:\n  TargetLanguage: English\n  Value: {name}\n" + extra +
                'Flags:\n' + ''.join(f'- {x}\n' for x in flags) +
                f'Archetype:\n  MutagenObjectType: MagicEffectArchetype\n{archetype}' + after +
                f'CastType: {cast}\nDualCastScale: 1\nCastingSoundLevel: Silent\nSounds: []\n'
                f"Description:\n  TargetLanguage: English\n  Value: '{desc}'\n")
    def script(name, props):
        out = f'VirtualMachineAdapter:\n  Scripts:\n  - Name: {name}\n    Properties:\n'
        for pn, kind, val in props:
            key = 'Object' if kind == 'Object' else 'Data'
            out += f'    - MutagenObjectType: Script{kind}Property\n      Name: {pn}\n      {key}: {val}\n'
        return out
    def spell(fk, edid, name, typ, cast, effects, equip='013F44:Skyrim.esm', extra=''):
        t = (f'FormKey: {fk}\nEditorID: {edid}\nName:\n  TargetLanguage: English\n  Value: {name}\n'
             f'MenuDisplayObject: 0435A5:Skyrim.esm\nEquipmentType: {equip}\n'
             "Description:\n  TargetLanguage: English\n  Value: ''\n" + extra)
        if typ: t += f'Type: {typ}\n'
        return t + f'CastType: {cast}\nEffects:\n' + effects
    def target_actor(t):
        return t.replace('CastType: FireAndForget\n', 'CastType: FireAndForget\nTargetType: TargetActor\n', 1)
    hidden = ['NoMagnitude', 'NoArea', 'NoDuration', 'HideInUI', 'Painless']
    def sub1(t, pat, rep, what):
        t2, k = re.subn(pat, rep, t, count=1, flags=re.M)
        assert k == 1, f'{what}: {pat}'
        return t2

    # --- Dark Effigy: Summon Ancestor's spell (EGO's winning copy) re-aimed at the caster
    t = open(SUMMON_SPELL_SRC, encoding='utf-8').read().replace('\r\n', '\n')
    t = sub1(t, r'^FormKey: .*$', f"FormKey: {n['effspell']}", 'effigy spell')
    t = sub1(t, r'^EditorID: .*$', 'EditorID: ZP_Prophecy_DarkEffigy_Spell', 'effigy spell')
    t = sub1(t, r'^Name:\n(?:  .*\n)*', 'Name:\n  TargetLanguage: English\n  Value: Dark Effigy\n', 'effigy spell')
    t = sub1(t, r'^EquipmentType: .*$', 'EquipmentType: 013F44:Skyrim.esm', 'effigy spell')     # either hand
    t = sub1(t, r'^BaseCost: .*$', f"BaseCost: {NEC['EffigyCost']}", 'effigy spell')
    t = sub1(t, r'^ChargeTime: .*$', 'ChargeTime: 1.5', 'effigy spell')
    t = sub1(t, r'^TargetType: TargetLocation\n', 'TargetType: Self\n', 'effigy spell')
    t = sub1(t, r'^Range: .*\n', '', 'effigy spell')
    t = sub1(t, r'^Effects:\n(?:[- ].*\n)*', f"Effects:\n- BaseEffect: {n['effme']}\n  Data:\n    Duration: {NEC['EffigySeconds']}\n", 'effigy spell')
    assert '14181F' not in t and 'Skyrim.esm' in t
    write('Spells', t)
    # its effect: Summon Ancestor's (14181F) casting art, light and sounds and skill; a script instead of the summon
    write('MagicEffects', f"""FormKey: {n['effme']}
EditorID: ZP_Prophecy_DarkEffigy_Effect
{script('ZP_DarkEffigyEffect', [
        ('Totem', 'Object', '0ACAFD:Skyrim.esm'),              # HagravenDeadGoatPole01
        ('PlantVisual', 'Object', n['wsvisual']),
        ('ArmorSpell', 'Object', n['armorspell']),
        ('ActorTypeUndead', 'Object', '013796:Skyrim.esm'),
        ('MagicSummonUndead', 'Object', '02482B:Skyrim.esm'),  # on every reanimate effect: a raised corpse carries it
        ('LegionList', 'Object', n['leglist']),
        ('Radius', 'Float', NEC['EffigyRadius']),
        ('HealPerSecond', 'Float', NEC['EffigyHeal'])])}Name:
  TargetLanguage: English
  Value: Dark Effigy
Keywords:
- 1076F4:Skyrim.esm
Flags:
- NoMagnitude
- NoArea
- PowerAffectsDuration
- NoHitEffect
BaseCost: 15
MagicSkill: Conjuration
CastingLight: 03BA90:Skyrim.esm
SpellmakingCastingTime: 0.5
Archetype:
  MutagenObjectType: MagicEffectArchetype
  Type: Script
CastType: FireAndForget
TargetType: Self
CastingArt: 03CDFC:Skyrim.esm
SkillUsageMultiplier: 0.6
DualCastScale: 1
Sounds:
- Sound: 03F269:Skyrim.esm
- Type: Charge
  Sound: 03C8F9:Skyrim.esm
- Type: Ready
  Sound: 03C8FA:Skyrim.esm
- Type: Release
  Sound: 03F2B1:Skyrim.esm
Description:
  TargetLanguage: English
  Value: A dark totem stands for <dur> seconds. You and your undead summons near it heal {NEC['EffigyHeal']} Health per second, and you and your allies near it gain {NEC['EffigyArmor']} armor.
""")
    write('Spells', target_actor(spell(n['armorspell'], 'ZP_Prophecy_DarkEffigy_Armor', 'Dark Effigy', None, 'FireAndForget',
                                       f"- BaseEffect: {n['armorme']}\n  Data:\n    Magnitude: {NEC['EffigyArmor']}\n    Duration: 2\n",
                                       extra='Flags:\n- NoAbsorbOrReflect\n')))
    write('MagicEffects', target_actor(mgef(n['armorme'], 'ZP_Prophecy_DarkEffigy_ArmorEffect', 'Dark Effigy',
                                            'Armor rating increased by <mag>.', ['Recover', 'NoArea'], '  ActorValue: DamageResist\n')))

    # --- A Willing Sacrifice
    write('Spells', spell(n['wspower'], 'ZP_Prophecy_WillingSacrifice_Power', 'A Willing Sacrifice', 'LesserPower', 'FireAndForget',
                          f"- BaseEffect: {n['wsme']}\n  Data:\n    Duration: 30\n", equip='025BEE:Skyrim.esm',   # outlasts the chain of blasts
                          extra='Flags:\n- IgnoreResistance\n- NoAbsorbOrReflect\n'))
    write('MagicEffects', mgef(n['wsme'], 'ZP_Prophecy_WillingSacrifice_Effect', 'A Willing Sacrifice', '',
                               ['NoMagnitude', 'NoArea', 'HideInUI', 'Painless'], '  Type: Script\n',
                               vmad=script('ZP_WillingSacrificeEffect', [
                                   ('Blast', 'Object', n['wsblast']),
                                   ('BlastVisual', 'Object', n['wsvisual']),
                                   ('LegionList', 'Object', n['leglist']),
                                   ('DeadDontForget', 'Object', nodeperk['nec4']),
                                   ('Cooldown', 'Object', n['wscd']),
                                   ('CooldownEffect', 'Object', n['wscdme']),
                                   ('Radius', 'Float', NEC['SacrificeRadius']),
                                   ('HealthFraction', 'Float', NEC['SacrificeFraction']),
                                   ('MagickaPerEnemy', 'Float', NEC['DeadMagicka'])])))
    # the blast: plain damage to Health (its magnitude set per summon by the script), blamed on the player - Enderal's
    # BlameSpellKeyword so a kill pays EP (_00E_EPOnDeath) - with Corpse Explosion's eldritch hit shader
    write('Spells', target_actor(spell(n['wsblast'], 'ZP_Prophecy_WillingSacrifice_Blast', 'A Willing Sacrifice', None, 'FireAndForget',
                                       f"- BaseEffect: {n['wsblastme']}\n  Data:\n    Magnitude: 1\n",
                                       extra='Flags:\n- NoAbsorbOrReflect\n')))
    write('MagicEffects', target_actor(mgef(n['wsblastme'], 'ZP_Prophecy_WillingSacrifice_BlastEffect', 'A Willing Sacrifice', '',
                                            ['Hostile', 'Detrimental', 'NoArea', 'NoDuration'], '  ActorValue: Health\n',
                                            extra='MenuDisplayObject: 0435A5:Skyrim.esm\nKeywords:\n- 05BD16:Skyrim.esm\n- 1076F4:Skyrim.esm\n')
                                       .replace('Archetype:\n', 'HitShader: 06A07B:Skyrim.esm\nArchetype:\n', 1)))
    # its burst: Corpse Explosion's eldritch explosion, without its damage enchantment, screen effect or push
    t = open(CORPSE_EXP_SRC, encoding='utf-8').read().replace('\r\n', '\n')
    t = sub1(t, r'^FormKey: .*$', f"FormKey: {n['wsvisual']}", 'corpse explosion')
    t = sub1(t, r'^EditorID: .*$', 'EditorID: ZP_Prophecy_WillingSacrifice_Explosion', 'corpse explosion')
    t = sub1(t, r'^Name:\n(?:  .*\n)*', 'Name:\n  TargetLanguage: English\n  Value: A Willing Sacrifice\n', 'corpse explosion')
    for line in ('ObjectEffect', 'ImageSpaceModifier', 'ISRadius'):
        t = sub1(t, rf'^{line}: .*\n', '', 'corpse explosion')
    t = sub1(t, r'^Force: .*$', 'Force: 0', 'corpse explosion')
    t = sub1(t, r'^Radius: .*$', f"Radius: {NEC['SacrificeRadius']}", 'corpse explosion')
    assert 'Forgotten Stories.esm' not in t and 'EldritchShockExplosion.nif' in t, 'corpse explosion copy still names FS'
    write('Explosions', t)
    write('Spells', spell(n['wscd'], 'ZP_Prophecy_WillingSacrifice_Cooldown', 'A Willing Sacrifice', None, 'FireAndForget',
                          f"- BaseEffect: {n['wscdme']}\n  Data:\n    Duration: {NEC['SacrificeCooldown']}\n",
                          extra='Flags:\n- NoAbsorbOrReflect\n'))
    write('MagicEffects', mgef(n['wscdme'], 'ZP_Prophecy_WillingSacrifice_CooldownEffect', 'A Willing Sacrifice',
                               'A Willing Sacrifice can be used again in <dur> seconds.', ['Recover'], '  Type: Script\n'))

    # --- Legion of the Damned
    write('Spells', spell(n['legpower'], 'ZP_Prophecy_LegionDamned_Power', 'Legion of the Damned', 'LesserPower', 'FireAndForget',
                          f"- BaseEffect: {n['legme']}\n  Data:\n    Duration: 6\n", equip='025BEE:Skyrim.esm',
                          extra='Flags:\n- IgnoreResistance\n- NoAbsorbOrReflect\n'))
    write('MagicEffects', mgef(n['legme'], 'ZP_Prophecy_LegionDamned_Effect', 'Legion of the Damned', '',
                               ['NoMagnitude', 'NoArea', 'HideInUI', 'Painless'], '  Type: Script\n',
                               vmad=script('ZP_LegionEffect', [
                                   ('Warrior', 'Object', n['legwar']),
                                   ('Archer', 'Object', n['legarch']),
                                   ('Mage', 'Object', n['legmage']),
                                   ('FeverMessage', 'Object', '036F95:Skyrim.esm'),     # _00E_Player_sArcaneFeverIncreased
                                   ('FeverImod', 'Object', '103755:Skyrim.esm'),        # _00E_ArkanistenfieberIMOD
                                   ('MentalExpert', 'Object', '069D07:Skyrim.esm'),     # _00E_Class_Thaumaturge_P07_MentalExpert
                                   ('LegionList', 'Object', n['leglist']),
                                   ('SummonArt', 'Object', '107D96:Skyrim.esm'),        # DA07SummonTargetFX (RFCT of art SummonTargetFX 03F811;
                                                                                         # an ARTO does not bind to VisualEffect)
                                   ('RaiseSound', 'Object', '14C018:Skyrim.esm'),       # MAGConjurePortalOpenM
                                   ('FeverCost', 'Float', NEC['LegionFever']),
                                   ('BaseHealth', 'Float', NEC['LegionHealth']),
                                   ('HealthPerLevel', 'Float', NEC['LegionHealthPerLevel'])])))
    write('Spells', spell(n['legab'], 'ZP_Prophecy_LegionDamned_Ability', 'Legion of the Damned', 'Ability', 'ConstantEffect',
                          f"- BaseEffect: {n['legabme']}\n  Data: {{}}\n"))
    write('MagicEffects', mgef(n['legabme'], 'ZP_Prophecy_LegionDamned_SkeletonEffect', 'Legion of the Damned', '', hidden,
                               '  Type: Script\n', cast='ConstantEffect',
                               vmad=script('ZP_LegionSkeletonEffect', [('LegionList', 'Object', n['leglist']),
                                                                       ('LifeSeconds', 'Float', NEC['LegionSeconds'])])))
    write('FormLists', f"FormKey: {n['leglist']}\nEditorID: ZP_Prophecy_LegionDamned_Current\n")
    # the skeletons: base Enderal's player summon, levelled with the player, in the player's faction, following,
    # no loot (no bone meal; their gear is removed when they die)
    weapon = '- Item:\n    Item: 0672D9:Skyrim.esm\n    Count: 1\n'                        # 01E_MOB_SkelettWeapon01
    kinds = [('legwar', 'ZP_Prophecy_LegionDamned_Warrior', 'Legion Warrior', weapon, '000D0D:Skyrim.esm', [], 0),
             ('legarch', 'ZP_Prophecy_LegionDamned_Archer', 'Legion Archer',
              '- Item:\n    Item: 07C97F:Skyrim.esm\n    Count: 1\n- Item:\n    Item: 08659D:Skyrim.esm\n    Count: 99\n',  # Oak Bow, Old Rune Arrows
              '038A23:Skyrim.esm', [], 0),                                                     # csDraugrMissile (LostOneArcherAmmo's fixes)
             ('legmage', 'ZP_Prophecy_LegionDamned_Mage', 'Legion Mage', weapon,
              '038A24:Skyrim.esm', ['048006:Skyrim.esm'], 200)]                                # csDraugrMagic + the Lost Mage's fire bolt
    for key, edid, name, items, combat, spells, magicka in kinds:
        t = open(SKELETON_SRC, encoding='utf-8').read().replace('\r\n', '\n')
        t = sub1(t, r'^FormKey: .*$', f'FormKey: {n[key]}', edid)
        t = sub1(t, r'^EditorID: .*$', f'EditorID: {edid}', edid)
        t = sub1(t, r'^  Flags:\n  - Summonable\n', '', edid)                      # placed actors, not summons
        t = sub1(t, r'^  Level:\n    MutagenObjectType: NpcLevel\n    Level: 7\n',
                 ('  MagickaOffset: %d\n' % magicka if magicka else '') +
                 '  Level:\n    MutagenObjectType: PcLevelMult\n    LevelMult: 1\n  CalcMinLevel: 1\n  CalcMaxLevel: 100\n', edid)
        t = sub1(t, r'^Factions:\n(?:- .*\n(?:  .*\n)*)', f'Factions:\n- Faction: {PLAYER_FACTION}\n  Fluff: 0x000000\n', edid)
        t = sub1(t, r'^(Race: .*\n)', lambda m: m.group(1) + 'ActorEffect:\n' + ''.join(f'- {x}\n' for x in [n['legab']] + spells), edid)
        t = sub1(t, r'^Items:\n(?:- .*\n(?:  .*\n)*)*', 'Items:\n' + items, edid)
        t = sub1(t, r'^AIData:\n(?:  .*\n)*', 'AIData:\n  Aggression: Aggressive\n  Confidence: Foolhardy\n  EnergyLevel: 50\n'
                                             '  Responsibility: NoCrime\n  Assistance: HelpsFriendsAndAllies\n'
                                             f'Packages:\n- {FOLLOW_PLAYER}\n', edid)
        t = sub1(t, r'^Name:\n(?:  .*\n)*', f'Name:\n  TargetLanguage: English\n  Value: {name}\n', edid)
        t = sub1(t, r'^CombatStyle: .*$', f'CombatStyle: {combat}', edid)
        assert t.count('ActorEffect:') == 1 and t.count('Packages:') == 1 and '034CDD' not in t
        write('Npcs', t)


# ------------------------------------------------------------------------------------------------ Shadow
# (curator 2026-10-27) Triumvirate's Shadow Mage spells, used as they are (Prophecy masters Triumvirate; Magic Patches
# prices them for Enderal): the menu teaches four of them (SHADOW_GRANTS). Nightfall is a lesser power instead of its
# 1245-Mana master spell: the power's gate effect (ZP_WrathGate, as Wrath of the Lightborn) checks Arcane Fever once,
# then casts Triumvirate's Nightfall and the fever cost. A scripted cast is free and ignores the spell's skill level.
# Nightfall's own script (TVR_CastAllTheThings_Script) casts each Shadow buff the caster HasSpell - so the talents'
# spells, plus Shadow Stride/Shadow Dance if bought from a tome. Allocated after every older block. Append new ones LAST.
SHADOW = 'Shadow'
SHADOW_FIRST_ID = 0xA6E
SHADOW_RECORDS = ('power', 'gate', 'fever')
SHADE_VEIL_RECORDS = ('veilab', 'veilme', 'veilfxs')     # Shade Veil (2026-10-28), after Shatterveil's records
DARKNESS_RECORDS = ('darkglobal', 'darkab', 'darkabme')   # Darkness (2026-10-28): the count, shown as the ability's magnitude
# the Darkness talent's spell (2026-10-28): our copy of Triumvirate's Darkness 3727C3 (Magic Patches' winning record)
# down to its hazard, whose model is vanilla's dark low mist - FXMistLowSwirls01Dark, about 900 units across, the
# size of the darkness light's 426-unit radius. Triumvirate's own records stay as they are (its tome still sells them)
DARK_SPELL_RECORDS = ('dspell', 'dme', 'dimpset', 'dimpact', 'dhazard')
NIGHTBLADE_RECORDS = ('nbspell', 'nbme')   # Nightblade's Darkness damage (2026-10-28), cast by the DLL
NIGHTBLADE_PROC = '335B4F'                 # TVR_Shadow_Spell_Nightblade_Proc: owned by Prophecy (no other plugin of ours)
NIGHTBLADE_DRAIN = '335B52'                # its TVR_Shadow_Rift_Effect_Nightblade_Debuff_SelfDamage (the Mana drain)
NIGHTBLADE_DAMAGE = '335B51'               # its 45 magic damage effect: the look and resist our damage copies
DARK_SPELL_SRC = {'dspell': os.path.join(REPO, 'src', 'MagicPatches', 'MagicPatchesESP', 'Spells',
                                         'TVR_Shadow_I025_Spell_Darkness - 3727C3_Triumvirate - Mage Archetypes.esp.yaml'),
                  'dme': ('MagicEffects', '395F16'), 'dimpset': ('ImpactDataSets', '395F14'),
                  'dimpact': ('Impacts', '395F15'), 'dhazard': ('Hazards', '38BD03')}
DARK_SPELL_FK = {'dspell': '3727C3', 'dme': '395F16', 'dimpset': '395F14', 'dimpact': '395F15', 'dhazard': '38BD03'}
DARK_MIST_MODEL = r'ZenProphecy\DarknessMist.nif'   # vanilla's FXMistLowSwirls01Dark tinted black (tools/08; drew light grey)
DARK_MIST_SECONDS = 30                                # the spell's duration: the mist impact lasts as long
DARKNESS_JSON = os.path.join(PATCH, 'data', 'SKSE', 'Plugins', 'ZenProphecyDarkness.json')
# Shade Veil's mist: Enderal's DA02ArmorShadow (the vanilla Ebony Armor's black and grey smoke: inky particles, dark
# membrane; its textures ship in Skyrim - Textures4/5) minus its ambient sound, which would sound on every crouch
SHADE_VEIL_FXS = os.path.join(REF, 'base', 'Skyrim', 'EffectShaders', 'DA02ArmorShadow - 081180_Skyrim.esm.yaml')
SHADOW_GRANTS = {'shd1': f'3727BF:{TRIUMVIRATE}',    # TVR_Shadow_I000_Spell_GatherShadows
                 'shd2': f'31C5C1:{TRIUMVIRATE}',    # TVR_Shadow_D075_Spell_DrainingShroud
                 'shd3': f'330A43:{TRIUMVIRATE}',    # TVR_Shadow_D050_Spell_Nightblade
                 'shd4': f'30D2A4:{TRIUMVIRATE}'}    # TVR_Shadow_A075_Spell_PullThroughShadows
NIGHTFALL_SPELL = f'31C5B8:{TRIUMVIRATE}'            # TVR_Shadow_I100_Spell_Nightfall
SHADOW_ICON = f'381AEB:{TRIUMVIRATE}'                # Triumvirate's Shadow menu art and hand art
SHADOW_CAST_ART = f'381AEC:{TRIUMVIRATE}'


def write_dark_spell(sh, write):
    """The Darkness talent's spell: Triumvirate's records copied (the Triumvirate Enderal patch's where it has them),
    each pointing at the next copy; the hazard keeps its own model, the impact adds the black mist."""
    tvr = lambda h: f'{h}:{TRIUMVIRATE}'
    swap = {tvr(DARK_SPELL_FK[k]): sh[k] for k in DARK_SPELL_RECORDS}
    names = {'dspell': 'ZP_Prophecy_Darkness_Spell', 'dme': 'ZP_Prophecy_Darkness_SpellEffect',
             'dimpset': 'ZP_Prophecy_Darkness_ImpactSet', 'dimpact': 'ZP_Prophecy_Darkness_Impact',
             'dhazard': 'ZP_Prophecy_Darkness_MistHazard'}
    for k in DARK_SPELL_RECORDS:
        src = DARK_SPELL_SRC[k]
        if isinstance(src, tuple):
            folder, h = src
            hits = [f for d in ('TriumvirateEnderalPatch', 'Triumvirate')
                    for f in glob.glob(os.path.join(REF, 'mods', d, folder, f'* - {h}_*.yaml'))]
            assert hits, f'Darkness spell: {folder} {h} not found'
            src = hits[0]
        y = open(src, encoding='utf-8').read().replace('\r\n', '\n')
        for a, b in swap.items():
            y = y.replace(a, b)
        y, n = re.subn(r'^EditorID: .*$', f'EditorID: {names[k]}', y, count=1, flags=re.M)
        assert n == 1, k
        if k == 'dhazard':
            # the hazard keeps Triumvirate's own Blacklight model (curator 2026-10-28: "the original Darkness spell's
            # effect additional to the black smoke"); it is an LE nif, so the two can't be merged into one mesh
            y = y.replace('  Value: Blacklight Hazard', '  Value: Darkness')
        if k == 'dimpact':
            # the black mist rides the impact instead, its effect lasting the spell's 30 seconds (vanilla impacts
            # last 0.1-2 s: that a 30 s one holds its model that long is unverified in game)
            y, n = re.subn(r'^(EditorID: .*\n)', lambda m: m.group(1) + f'Model:\n  File: {DARK_MIST_MODEL}\n', y,
                           count=1, flags=re.M)
            assert n == 1, 'Darkness impact model'
            y, n = re.subn(r'^Duration: .*$', f'Duration: {DARK_MIST_SECONDS}', y, count=1, flags=re.M)
            assert n == 1, 'Darkness impact duration'
        if k == 'dme':
            y = y.replace('Creates a <10> foot source of darkness that sticks where it strikes for <dur> seconds.',
                          'Leaves a pool of black mist and darkness where it strikes for <dur> seconds.')
        assert sh[k] in y, k
        ty = {'dspell': 'Spells', 'dme': 'MagicEffects', 'dimpset': 'ImpactDataSets', 'dimpact': 'Impacts',
              'dhazard': 'Hazards'}[k]
        write(ty, y)


def tvr_record(folder, h):
    """A Triumvirate record as the list loads it: the Triumvirate Enderal patch's copy where it has one."""
    hits = [f for d in ('TriumvirateEnderalPatch', 'Triumvirate')
            for f in glob.glob(os.path.join(REF, 'mods', d, folder, f'* - {h}_*.yaml'))]
    assert hits, f'{folder} {h} not found'
    return open(hits[0], encoding='utf-8').read().replace('\r\n', '\n')


def write_nightblade(sh, write, nodeperk):
    # the proc without its Mana drain while the player has Gather Shadows (the drain's subject is the target; the
    # player is named by reference). Tome users without the tree keep Triumvirate's Nightblade as it was
    y = tvr_record('Spells', NIGHTBLADE_PROC)
    entry = f'- BaseEffect: {NIGHTBLADE_DRAIN}:{TRIUMVIRATE}\n  Data: {{}}\n'
    assert y.count(entry) == 1, 'Nightblade proc: drain entry'
    y = y.replace(entry, entry + '  Conditions:\n  - MutagenObjectType: ConditionFloat\n    Data:\n'
                  '      MutagenObjectType: HasPerkConditionData\n      RunOnType: Reference\n'
                  f"      Reference: 000014:Skyrim.esm\n      Perk: {nodeperk['shd1']}\n    ComparisonValue: 0\n")
    write('Spells', y)
    # the Darkness damage: Triumvirate's damage effect (its hit shader, resist, look) without the dash-keyword
    # condition, in a spell the DLL casts from the player with the magnitude it computes
    me = tvr_record('MagicEffects', NIGHTBLADE_DAMAGE)
    me = re.sub(r'^FormKey: .*$', f"FormKey: {sh['nbme']}", me, count=1, flags=re.M)
    me = re.sub(r'^EditorID: .*$', 'EditorID: ZP_Prophecy_Nightblade_DarknessDamage', me, count=1, flags=re.M)
    me, n = re.subn(r'^Conditions:\n(?:[- ].*\n)*', '', me, count=1, flags=re.M)
    assert n == 1, 'Nightblade damage: conditions'
    me = me.replace('  Value: <mag> magic damage and pulls the caster to the target.', '  Value: <mag> magic damage from Darkness.')
    me = me.replace('  Value: Magic Damage\n', '  Value: Nightblade\n', 1)
    write('MagicEffects', me)
    write('Spells', f"""FormKey: {sh['nbspell']}
EditorID: ZP_Prophecy_Nightblade_DarknessDamage
Name:
  TargetLanguage: English
  Value: Nightblade
EquipmentType: 013F44:Skyrim.esm
Description:
  TargetLanguage: English
  Value: ''
Flags:
- ManualCostCalc
- NoAbsorbOrReflect
CastType: FireAndForget
TargetType: TargetActor
Effects:
- BaseEffect: {sh['nbme']}
  Data:
    Magnitude: 1
    Duration: 1
""")


def write_shadow(sh, write, nodeperk):
    # Darkness: the global (saved with the game), the ability that shows the count, and the DLL's config
    write('Globals', f"MutagenObjectType: GlobalShort\nFormKey: {sh['darkglobal']}\nEditorID: ZP_Darkness\nData: 0\n")
    write('Spells', f"FormKey: {sh['darkab']}\nEditorID: ZP_Prophecy_Darkness_Ability\nName:\n  TargetLanguage: English\n"
                    "  Value: Darkness\nEquipmentType: 013F44:Skyrim.esm\nDescription:\n  TargetLanguage: English\n  Value: ''\n"
                    f"Type: Ability\nCastType: ConstantEffect\nEffects:\n- BaseEffect: {sh['darkabme']}\n  Data: {{}}\n")
    write('MagicEffects', f"""FormKey: {sh['darkabme']}
EditorID: ZP_Prophecy_Darkness_Effect
Name:
  TargetLanguage: English
  Value: Darkness
Flags:
- Recover
- NoDuration
- NoArea
Archetype:
  MutagenObjectType: MagicEffectArchetype
  Type: Script
CastType: ConstantEffect
DualCastScale: 1
Sounds: []
Description:
  TargetLanguage: English
  Value: You have <mag> Darkness.
""")
    write_dark_spell(sh, write)
    write_nightblade(sh, write, nodeperk)
    hexid = lambda fk: fk.split(':')[0]
    spells = ([(nid, SHADOW_GRANTS[nid]) for nid in ('shd1', 'shd2', 'shd3', 'shd4')] + [('shd5', sh['power'])] +
              [('shd7', sh['dspell'])])
    cfg = {
        '$comment': 'Generated by src/Prophecy/tools/01-build-trees.py (write_shadow) - never hand-edit. FormIDs are '
                    'local to their plugin (hex). See arch-docs/patches/Prophecy.md, Darkness.',
        'plugin': MOD, 'darknessGlobal': hexid(sh['darkglobal']), 'darknessEffect': hexid(sh['darkabme']),
        'veilEffect': hexid(sh['veilme']), 'perks': {'root': hexid(nodeperk['shd1'])},
        'max': DARKNESS['Max'], 'fill': [{'lightAtMost': l, 'secondsPerPoint': s} for l, s in DARKNESS['Fill']],
        'veilMult': DARKNESS['VeilMult'], 'drainEvery': DARKNESS['DrainEvery'],
        'refusal': 'Not enough Darkness.',
        'spells': [{'name': next(n[1] for _, _, ns in TREES for n in ns if n[0] == nid), 'plugin': fk.split(':', 1)[1],
                    'id': hexid(fk), 'cost': DARKNESS['Cost'][nid]} for nid, fk in spells],
        'meter': DARKNESS['Meter'],
        'nightblade': {'procPlugin': TRIUMVIRATE, 'procId': NIGHTBLADE_PROC, 'damageSpell': hexid(sh['nbspell']),
                       'fraction': NIGHTBLADE['Fraction'], 'perPoint': NIGHTBLADE['PerPoint']},
    }
    os.makedirs(os.path.dirname(DARKNESS_JSON), exist_ok=True)
    with open(DARKNESS_JSON, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(cfg, fh, indent=1)
    fx = open(SHADE_VEIL_FXS, encoding='utf-8').read().replace('\r\n', '\n')
    for a, b in ((r'^FormKey: .*$', f"FormKey: {sh['veilfxs']}"),
                 (r'^EditorID: .*$', 'EditorID: ZP_Prophecy_ShadeVeil_FXS'),
                 (r'^AmbientSound: .*\n', '')):
        fx, n = re.subn(a, b, fx, count=1, flags=re.M)
        assert n == 1, f'Shade Veil shader: {a}'
    write('EffectShaders', fx)
    write('Spells', f"""FormKey: {sh['veilab']}
EditorID: ZP_Prophecy_ShadeVeil_Ability
Name:
  TargetLanguage: English
  Value: Shade Veil
EquipmentType: 013F44:Skyrim.esm
Description:
  TargetLanguage: English
  Value: ''
Type: Ability
CastType: ConstantEffect
Effects:
- BaseEffect: {sh['veilme']}
  Data: {{}}
  Conditions:
  - MutagenObjectType: ConditionFloat
    Data:
      MutagenObjectType: IsSneakingConditionData
    ComparisonValue: 1
""")
    # the mist is played by the effect's script (a HitShader on this conditioned effect did not show in game)
    write('MagicEffects', f"""FormKey: {sh['veilme']}
EditorID: ZP_Prophecy_ShadeVeil_Effect
VirtualMachineAdapter:
  Scripts:
  - Name: ZP_ShaderWhileActiveEffect
    Properties:
    - MutagenObjectType: ScriptObjectProperty
      Name: Shader
      Object: {sh['veilfxs']}
Name:
  TargetLanguage: English
  Value: Shade Veil
Flags:
- NoMagnitude
- NoArea
- NoDuration
- Painless
Archetype:
  MutagenObjectType: MagicEffectArchetype
  Type: Script
CastType: ConstantEffect
TargetType: Self
DualCastScale: 1
Sounds: []
Description:
  TargetLanguage: English
  Value: 'You are {SHADE_VEIL_DETECT}% harder to detect while sneaking.'
""")
    write('Spells', f"""FormKey: {sh['power']}
EditorID: ZP_Prophecy_Nightfall_Power
Name:
  TargetLanguage: English
  Value: Nightfall
MenuDisplayObject: {SHADOW_ICON}
EquipmentType: 025BEE:Skyrim.esm
Description:
  TargetLanguage: English
  Value: ''
Flags:
- IgnoreResistance
- NoAbsorbOrReflect
Type: LesserPower
CastType: FireAndForget
Effects:
- BaseEffect: {sh['gate']}
  Data: {{}}
""")
    write('MagicEffects', f"""FormKey: {sh['gate']}
EditorID: ZP_Prophecy_Nightfall_Gate
VirtualMachineAdapter:
  Scripts:
  - Name: ZP_WrathGate
    Properties:
    - MutagenObjectType: ScriptObjectProperty
      Name: CloakSpell
      Object: {NIGHTFALL_SPELL}
    - MutagenObjectType: ScriptFloatProperty
      Name: MaxFever
      Data: 1000.0
    - MutagenObjectType: ScriptStringProperty
      Name: Refusal
      Data: Your Arcane Fever is too high to call down Nightfall.
Name:
  TargetLanguage: English
  Value: Nightfall
MenuDisplayObject: {SHADOW_ICON}
Flags:
- NoMagnitude
- NoArea
- NoDuration
- Painless
MagicSkill: Illusion
Archetype:
  MutagenObjectType: MagicEffectArchetype
  Type: Script
CastType: FireAndForget
CastingArt: {SHADOW_CAST_ART}
DualCastScale: 1
Sounds: []
Description:
  TargetLanguage: English
  Value: 'For 60 seconds, a pool of darkness follows you and every Shadow spell you know is cast on you at once. Costs a full Darkness meter.'
""")
    write('Spells', f"""FormKey: {sh['fever']}
EditorID: ZP_Prophecy_Nightfall_Fever
Name:
  TargetLanguage: English
  Value: Nightfall
EquipmentType: 013F44:Skyrim.esm
Description:
  TargetLanguage: English
  Value: ''
Flags:
- ManualCostCalc
CastType: FireAndForget
Effects:
- BaseEffect: {FEVER}
  Data:
    Magnitude: {NIGHTFALL_FEVER}
    Duration: 1
""")


# ------------------------------------------------------------------------------------------------ Druid
# (curator 2026-10-27) Triumvirate's Druid and Shaman spells, used as they are (Magic Patches prices them): the menu
# teaches Parasitic Growth, Bramble Growth and the three totems (DRUID_GRANTS) and our Druidcraft - Triumvirate's
# spell (Magic Patches' price) plus a heal on a dead target. Force of Nature is a lesser power, not the 105-Mana spell:
# ZP_ForceOfNatureEffect takes the fever as Legion of the Damned does, casts Triumvirate's Force of Nature (the player
# becomes its Horned Lord race 000837 through TVR_Wildshape_Script) and then the familiars: our FireAndForget copies
# of Triumvirate's Call Raven / Snow Leopard / Rattlesnakes summon effects without TVR_SummonCost_Script (the Mana
# drain that ends them with the concentration). The perk raises the summon limit by ExtraSummons while the form is
# on, and the script dispels the familiars when the form ends early. Allocated after Shadow. Append new ones LAST.
DRUID_TREE = 'Druidic'
DRUID_FIRST_ID = 0xA82
DRUID_RECORDS = ('craftspell', 'crafthealme', 'power', 'powerme', 'familiars', 'raven', 'leopard', 'snake1', 'snake2')
DRUID_LATE_NODES = ('dru8',)
DRUID_LATE_NODES_2 = ('dru9', 'dru10')       # Wolf Pack, Nature's Way (2026-10-29): after Blink Step's swoosh
HUNT_RECORDS = ('huntpower', 'huntme', 'wolfspell1', 'wolfme1', 'wolfspell2', 'wolfme2')
# The Hunt's howl (curator 2026-10-29, "that wolf sound to the Gray Wolves as they spawn in"): Motion Array's wolf howl
# (tools/07, converted only), played by ZP_TheHuntEffect on the player once the wolf is called. Allocated after
# Ricochet Rounds' perk
HUNT_HOWL_RECORDS = ('howlsnd', 'howlmarker')
# The wolves' summon art (2026-10-29): the effect needs a HitEffectArt or the summon is created but never shown nor
# commanded until a reload; Triumvirate's portal still looked like conjuration, so a copy of it with vanilla's empty
# effect model (Effects\FXEmptyObject.nif, also used by Enderal's own placers). Allocated after the howl
HUNT_PORTAL_RECORDS = ('huntportal',)
HUNT_PORTAL_SRC = os.path.join(REF, 'mods', 'Triumvirate', 'ArtObjects', 'TVR_Primal_Portal - 11F22F_Triumvirate - Mage Archetypes.esp.yaml')
HUNT_HOWL_FILE = r'Data\Sound\FX\ZenProphecy\ZP_TheHuntHowl.wav'
GOODBERRY = f'2844D3:{TRIUMVIRATE}'                  # TVR_Healing_Potion_Goodberry
WOLF_EFFECT = 'TVR_Druid_Primal_Effect_CallWolf - 16391F'   # Triumvirate's Enderal patch's copy
WOLF_ICON = f'14F4DC:{TRIUMVIRATE}'
TOTEM_KEYWORD = f'3E706A:{TRIUMVIRATE}'              # TVR_Totem_Keyword_LevelScaling: on all three totem effects
AERO = 'Aero.esl'                                    # Abyssal Wind Magic (Kittytails), installed with src/KittytailsPacksClean
TWISTER = f'00086F:{AERO}'                           # _AV_PLAYER_WindBallSpawnTornado_75
DRUID_GRANTS = {'dru8': TWISTER,
                'dru3': f'27F3B4:{TRIUMVIRATE}',     # TVR_Druid_R075_Spell_BrambleGrowth
                'dru4': f'3BE79F:{TRIUMVIRATE}',     # TVR_Shaman_C000_Spell_CreateWaterTotem
                'dru5': f'3C38C5:{TRIUMVIRATE}',     # TVR_Shaman_C025_Spell_CreateTreeTotem
                'dru6': f'35E36E:{TRIUMVIRATE}'}     # TVR_Shaman_C075_Spell_CreateEarthTotem
TOTEM_EFFECTS = ('3BE79E', '3C89CF', '35E36C')   # the three totem spells' effects: Elementalism, not Conjuration
DRUIDCRAFT_EFFECT = f'2ACD21:{TRIUMVIRATE}'          # TVR_Druid_Verdant_Effect_Druidcraft
DRUIDCRAFT_ICON = f'191249:{TRIUMVIRATE}'
FON_SPELL = f'28E6EB:{TRIUMVIRATE}'                  # TVR_Druid_A025_Spell_ForceOfNature
DRUIDCRAFT_SPELL = f'28E6E9:{TRIUMVIRATE}'           # TVR_Druid_A000_Spell_Druidcraft (our copy is the talent's)
FON_EFFECT = f'191250:{TRIUMVIRATE}'                 # TVR_Druid_Verdant_Effect_ForceOfNature (TVR_Wildshape_Script)
# the Horned Lord race's skin: the player's actor base wears it during the form (its own SkinNaked 000D64 wins over
# the race's, which left the player with no body; ZP_ForceOfNatureEffect.FormSkin, 2026-10-28)
FON_SKIN = f'000839:{TRIUMVIRATE}'                   # TVR_Verdant_Armor_ForceOfNature
_TVR_PATCH_MGEF = os.path.join(REF, 'mods', 'TriumvirateEnderalPatch', 'MagicEffects')
FAMILIARS = [('raven', 'TVR_Druid_Primal_Effect_CallRaven - 15460C', 'Raven'),          # Triumvirate's Enderal patch's copies
             ('leopard', 'TVR_Druid_Primal_Effect_CallSnowLeopard - 168A21', 'Snow Leopard'),
             ('snake1', 'TVR_Druid_Primal_Effect_CallSnakes - 02A226', 'Rattlesnake'),
             ('snake2', 'TVR_Druid_Primal_Effect_CallSnakes - 02A226', 'Rattlesnake')]


def summon_room(cond_type, field, form):
    """+1 to the summon limit while the player has the given effect / an effect with the keyword."""
    return ('Effects:\n- MutagenObjectType: PerkEntryPointModifyValue\n  Priority: 100\n  Conditions:\n  - Conditions:\n'
            f'    - MutagenObjectType: ConditionFloat\n      Data:\n        MutagenObjectType: {cond_type}\n'
            f'        {field}: {form}\n      ComparisonValue: 1\n  EntryPoint: ModCommandedActorLimit\n'
            '  PerkConditionTabCount: 2\n  Modification: Add\n  Value: 1\n')


def write_hunt(d, write, nodeperk):
    """The Hunt (curator 2026-10-29): a lesser power that summons Triumvirate's Gray Wolf (and, with Wolf Pack, a second)
    for HUNT['Berries'] Goodberries. Each wolf effect is one copy of Triumvirate's Call Gray Wolf summon effect, made
    FireAndForget and without TVR_SummonCost_Script (Force of Nature's familiars' shape), lasting HUNT['Seconds'].
    The summons sit on the power itself (the player's cast, so the engine applies the summon limit; summons cast from
    a script ignore it - 6 wolves in game), each conditioned on carrying the Goodberries; ZP_TheHuntEffect only takes
    the berries and plays the howl. The scripted entrance (hidden wolves leaping in from behind) was reverted the same
    day: Papyrus took 5-7 s in the list ("too janky and heavy"). Its empty summon art 'huntportal' 0xB11 and the two
    wolf spells 'wolfspell1/2' are retired and unwritten - never reuse."""
    # the howl (2026-10-29): sound + marker, played from the script (Sound.Play) once the wolf is called
    write('SoundDescriptors', f"""FormKey: {d['howlsnd']}
EditorID: ZP_Prophecy_TheHuntHowlSound
Type: Standard
Category: 01A0BD:Skyrim.esm
SoundFiles:
- {HUNT_HOWL_FILE}
OutputModel: 0B6463:Skyrim.esm
LoopAndRumble: {{}}
Priority: 128
""")
    write('SoundMarkers', f"FormKey: {d['howlmarker']}\nEditorID: ZP_Prophecy_TheHuntHowlMarker\n"
                          f"SoundDescriptor: {d['howlsnd']}\n")
    write('Spells', f"""FormKey: {d['huntpower']}
EditorID: ZP_Prophecy_TheHunt_Power
Name:
  TargetLanguage: English
  Value: The Hunt
MenuDisplayObject: {WOLF_ICON}
EquipmentType: 025BEE:Skyrim.esm
Description:
  TargetLanguage: English
  Value: ''
Flags:
- IgnoreResistance
- NoAbsorbOrReflect
Type: LesserPower
CastType: FireAndForget
Effects:
- BaseEffect: {d['huntme']}
  Data:
    Duration: 1
- BaseEffect: {d['wolfme1']}
  Data:
    Duration: {HUNT['Seconds']}
  Conditions:
  - MutagenObjectType: ConditionFloat
    CompareOperator: GreaterThanOrEqualTo
    Data:
      MutagenObjectType: GetItemCountConditionData
      ItemOrList: {GOODBERRY}
    ComparisonValue: {HUNT['Berries']}
- BaseEffect: {d['wolfme2']}
  Data:
    Duration: {HUNT['Seconds']}
  Conditions:
  - MutagenObjectType: ConditionFloat
    CompareOperator: GreaterThanOrEqualTo
    Data:
      MutagenObjectType: GetItemCountConditionData
      ItemOrList: {GOODBERRY}
    ComparisonValue: {HUNT['Berries']}
  - MutagenObjectType: ConditionFloat
    Data:
      MutagenObjectType: HasPerkConditionData
      Perk: {nodeperk['dru9']}
    ComparisonValue: 1
""")
    write('MagicEffects', f"""FormKey: {d['huntme']}
EditorID: ZP_Prophecy_TheHunt_Effect
VirtualMachineAdapter:
  Scripts:
  - Name: ZP_TheHuntEffect
    Properties:
    - MutagenObjectType: ScriptObjectProperty
      Name: Goodberry
      Object: {GOODBERRY}
    - MutagenObjectType: ScriptIntProperty
      Name: Cost
      Data: {HUNT['Berries']}
    - MutagenObjectType: ScriptObjectProperty
      Name: Howl
      Object: {d['howlmarker']}
    - MutagenObjectType: ScriptObjectProperty
      Name: WolfBase
      Object: 17CE35:Triumvirate - Mage Archetypes.esp
Name:
  TargetLanguage: English
  Value: The Hunt
MenuDisplayObject: {WOLF_ICON}
Flags:
- NoMagnitude
- NoArea
- HideInUI
- Painless
Archetype:
  MutagenObjectType: MagicEffectArchetype
  Type: Script
CastType: FireAndForget
DualCastScale: 1
Sounds: []
Description:
  TargetLanguage: English
  Value: ''
""")
    p = glob.glob(os.path.join(_TVR_PATCH_MGEF, f'{WOLF_EFFECT}_*.yaml'))
    assert len(p) == 1, WOLF_EFFECT
    src = open(p[0], encoding='utf-8').read().replace('\r\n', '\n')
    for i in (1, 2):
        me = d[f'wolfme{i}']
        t = re.sub(r'^FormKey: .*$', f'FormKey: {me}', src, count=1, flags=re.M)
        t = re.sub(r'^EditorID: .*$', f'EditorID: ZP_Prophecy_TheHunt_Wolf{i}', t, count=1, flags=re.M)
        t, n = re.subn(r'^VirtualMachineAdapter:\n(?:  .*\n)*', '', t, count=1, flags=re.M)
        assert n == 1 and 'TVR_SummonCost_Script' not in t, 'wolf: summon cost script'
        t = re.sub(r'^Name:\n(?:  .*\n)+', 'Name:\n  TargetLanguage: English\n  Value: Gray Wolf\n', t, count=1, flags=re.M)
        t = re.sub(r'^Description:\n(?:  .*\n)+', "Description:\n  TargetLanguage: English\n  Value: ''\n", t, count=1, flags=re.M)
        t, n = re.subn(r'^CastType: Concentration$', 'CastType: FireAndForget', t, flags=re.M)
        assert n == 1, 'wolf: cast type'
        t = re.sub(r'^- Type: ConcentrationCastLoop\n  Sound: .*\n', '', t, flags=re.M)
        t = re.sub(r'^MinimumSkillLevel: .*\n', '', t, flags=re.M)
        t = re.sub(r'^Conditions:\n(?:[- ].*\n)*', '', t, count=1, flags=re.M)
        assert 'MagicEffectSummonCreatureArchetype' in t
        write('MagicEffects', t)


def druid_perk(d):
    return ('Effects:\n- MutagenObjectType: PerkAbilityEffect\n  Ability: ' + d['power'] + '\n'
            '- MutagenObjectType: PerkEntryPointModifyValue\n  Priority: 100\n  Conditions:\n  - Conditions:\n'
            '    - MutagenObjectType: ConditionFloat\n      Data:\n        MutagenObjectType: HasMagicEffectConditionData\n'
            f'        MagicEffect: {FON_EFFECT}\n      ComparisonValue: 1\n  EntryPoint: ModCommandedActorLimit\n'
            f"  PerkConditionTabCount: 2\n  Modification: Add\n  Value: {DRUID['ExtraSummons']}\n")


def write_druid(d, write):
    # Force of Nature's Horned Lord race, male skeleton: Triumvirate gives men Mihail's skeletonoldgod.nif, an LE file
    # with LE Havok ragdoll data, and the male player got no body at all (no shadow; a plain player.setrace too) while
    # a female NPC - XPMSE's SE skeletonBeast_female.nif - showed the form (curator, 2026-10-28). XPMSE's male
    # skeletonBeast.nif carries all 21 bones the body mesh is skinned to. The winning record (Triumvirate - Enderal
    # Patch's copy of the .esp) verbatim, only that path changed.
    src = glob.glob(os.path.join(REF, 'mods', 'TriumvirateEnderalPatch', 'Races', '* - 000837_Triumvirate - Mage Archetypes.esp.yaml'))
    assert len(src) == 1, 'serialize Triumvirate - Enderal Patch into reference/mods/TriumvirateEnderalPatch'
    t = open(src[0], encoding='utf-8').read().replace('\r\n', '\n')
    t, n = re.subn(r'(?i)^    File: mihail monsters and animals\\dwarven centurion\\old god\\skeletonoldgod\.nif$',
                   lambda m: r'    File: Actors\Character\Character Assets\skeletonBeast.nif', t, flags=re.M)
    assert n == 1, 'Horned Lord race: male skeleton path'
    write('Races', t)
    # The three totems are Elementalism (curator, 2026-10-28): Triumvirate makes them Conjuration (Enderal's Entropy).
    # The school sits on each spell's effect; Magic Patches owns the spells (prices), so Prophecy overrides only the
    # effects - the winning records (Triumvirate - Enderal Patch's), verbatim but for MagicSkill. Their
    # MagicSummonFamiliar keyword stays (Sinistrope's Mystical Call reads it).
    for eid in TOTEM_EFFECTS:
        src = glob.glob(os.path.join(REF, 'mods', 'TriumvirateEnderalPatch', 'MagicEffects', f'* - {eid}_Triumvirate - Mage Archetypes.esp.yaml'))
        assert len(src) == 1, eid
        t = open(src[0], encoding='utf-8').read().replace('\r\n', '\n')
        t, n = re.subn(r'^MagicSkill: Conjuration$', 'MagicSkill: Destruction', t, flags=re.M)
        assert n == 1, f'{eid}: school'
        write('MagicEffects', t)
    # Twister priced for Enderal (an override of Aero.esl's record: Prophecy is its only patcher), and without its
    # Dragonborn menu art (Dragonborn.esm is an empty stub in Enderal)
    src = glob.glob(os.path.join(REF, 'mods', 'AbyssalWindMagic', 'Spells', '* - 00086F_Aero.esl.yaml'))
    assert len(src) == 1, 'reference/mods/AbyssalWindMagic: serialize the cleaned Aero.esl there'
    t = open(src[0], encoding='utf-8').read().replace('\r\n', '\n')
    t, n = re.subn(r'^BaseCost: 409$', f'BaseCost: {TWISTER_COST}', t, flags=re.M)
    assert n == 1 and '- ManualCostCalc' in t, 'Twister cost'
    t, n = re.subn(r'^MenuDisplayObject: .*:Dragonborn\.esm\n', '', t, flags=re.M)
    assert n == 1, 'Twister menu art'
    write('Spells', t)
    # Druidcraft: Magic Patches' winning spell (its price) with the heal added
    src = glob.glob(os.path.join(REPO, 'src', 'MagicPatches', '*', 'Spells', '* - 28E6E9_*.yaml'))
    assert len(src) == 1, 'Magic Patches Druidcraft'
    t = open(src[0], encoding='utf-8').read().replace('\r\n', '\n')
    t = re.sub(r'^FormKey: .*$', f"FormKey: {d['craftspell']}", t, count=1, flags=re.M)
    t = re.sub(r'^EditorID: .*$', 'EditorID: ZP_Prophecy_Druidcraft_Spell', t, count=1, flags=re.M)
    t, n = re.subn(r'^(Effects:\n- BaseEffect: ' + re.escape(DRUIDCRAFT_EFFECT) + r'\n  Data: \{\}\n)',
                   lambda m: m.group(1) + f"- BaseEffect: {d['crafthealme']}\n  Data:\n    Magnitude: {DRUID['CraftHeal']}\n",
                   t, flags=re.M)
    assert n == 1, 'Druidcraft effects'
    write('Spells', t)
    write('MagicEffects', f"""FormKey: {d['crafthealme']}
EditorID: ZP_Prophecy_Druidcraft_Heal
VirtualMachineAdapter:
  Scripts:
  - Name: ZP_DruidcraftHealEffect
    Properties:
    - MutagenObjectType: ScriptObjectProperty
      Name: Goodberry
      Object: {GOODBERRY}
    - MutagenObjectType: ScriptIntProperty
      Name: Berries
      Data: {DRUID['CraftBerries']}
Name:
  TargetLanguage: English
  Value: Druidcraft
MenuDisplayObject: {DRUIDCRAFT_ICON}
Flags:
- NoDuration
- NoArea
- HideInUI
- NoHitEffect
- NoDeathDispel
- Painless
Archetype:
  MutagenObjectType: MagicEffectArchetype
  Type: Script
CastType: FireAndForget
TargetType: TargetActor
DualCastScale: 1
Sounds: []
Description:
  TargetLanguage: English
  Value: ''
""")
    # Force of Nature: the power and its effect
    write('Spells', f"""FormKey: {d['power']}
EditorID: ZP_Prophecy_ForceOfNature_Power
Name:
  TargetLanguage: English
  Value: Force of Nature
MenuDisplayObject: {DRUIDCRAFT_ICON}
EquipmentType: 025BEE:Skyrim.esm
Description:
  TargetLanguage: English
  Value: ''
Flags:
- IgnoreResistance
- NoAbsorbOrReflect
Type: LesserPower
CastType: FireAndForget
Effects:
- BaseEffect: {d['powerme']}
  Data:
    Duration: {DRUID['FamiliarSeconds'] + 10}
""")
    write('MagicEffects', f"""FormKey: {d['powerme']}
EditorID: ZP_Prophecy_ForceOfNature_Effect
VirtualMachineAdapter:
  Scripts:
  - Name: ZP_ForceOfNatureEffect
    Properties:
    - MutagenObjectType: ScriptObjectProperty
      Name: FormSpell
      Object: {FON_SPELL}
    - MutagenObjectType: ScriptObjectProperty
      Name: FormEffect
      Object: {FON_EFFECT}
    - MutagenObjectType: ScriptObjectProperty
      Name: Familiars
      Object: {d['familiars']}
    - MutagenObjectType: ScriptObjectProperty
      Name: FeverMessage
      Object: 036F95:Skyrim.esm
    - MutagenObjectType: ScriptObjectProperty
      Name: FeverImod
      Object: 103755:Skyrim.esm
    - MutagenObjectType: ScriptObjectProperty
      Name: MentalExpert
      Object: 069D07:Skyrim.esm
    - MutagenObjectType: ScriptFloatProperty
      Name: FeverCost
      Data: {float(DRUID['FormFever'])}
    - MutagenObjectType: ScriptBoolProperty
      Name: StripArmor
      Data: True
    - MutagenObjectType: ScriptObjectProperty
      Name: FormSkin
      Object: {FON_SKIN}
    - MutagenObjectType: ScriptFloatProperty
      Name: PollSeconds
      Data: 0.25
Name:
  TargetLanguage: English
  Value: Force of Nature
MenuDisplayObject: {DRUIDCRAFT_ICON}
Flags:
- NoMagnitude
- NoArea
- HideInUI
- Painless
Archetype:
  MutagenObjectType: MagicEffectArchetype
  Type: Script
CastType: FireAndForget
DualCastScale: 1
Sounds: []
Description:
  TargetLanguage: English
  Value: ''
""")
    # the familiars: one spell, four summon effects
    write('Spells', f"FormKey: {d['familiars']}\nEditorID: ZP_Prophecy_ForceOfNature_Familiars\nName:\n  TargetLanguage: English\n"
                    "  Value: Force of Nature\nEquipmentType: 013F44:Skyrim.esm\nDescription:\n  TargetLanguage: English\n  Value: ''\n"
                    "Flags:\n- ManualCostCalc\n- IgnoreResistance\n- NoAbsorbOrReflect\nCastType: FireAndForget\nEffects:\n" +
                    ''.join(f"- BaseEffect: {d[k]}\n  Data:\n    Duration: {DRUID['FamiliarSeconds']}\n" for k, _, _ in FAMILIARS))
    for k, base, name in FAMILIARS:
        p = glob.glob(os.path.join(_TVR_PATCH_MGEF, f'{base}_*.yaml'))
        assert len(p) == 1, base
        t = open(p[0], encoding='utf-8').read().replace('\r\n', '\n')
        t = re.sub(r'^FormKey: .*$', f'FormKey: {d[k]}', t, count=1, flags=re.M)
        t = re.sub(r'^EditorID: .*$', f'EditorID: ZP_Prophecy_ForceOfNature_{k.capitalize()}', t, count=1, flags=re.M)
        t, n = re.subn(r'^VirtualMachineAdapter:\n(?:  .*\n)*', '', t, count=1, flags=re.M)
        assert n == 1 and 'TVR_SummonCost_Script' not in t, f'{base}: summon cost script'
        t = re.sub(r'^Name:\n(?:  .*\n)+', f'Name:\n  TargetLanguage: English\n  Value: {name}\n', t, count=1, flags=re.M)
        t = re.sub(r'^Description:\n(?:  .*\n)+', "Description:\n  TargetLanguage: English\n  Value: ''\n", t, count=1, flags=re.M)
        t, n = re.subn(r'^CastType: Concentration$', 'CastType: FireAndForget', t, flags=re.M)
        assert n == 1, f'{base}: cast type'
        t = re.sub(r'^- Type: ConcentrationCastLoop\n  Sound: .*\n', '', t, flags=re.M)
        t = re.sub(r'^MinimumSkillLevel: .*\n', '', t, flags=re.M)
        t = re.sub(r'^Conditions:\n(?:[- ].*\n)*', '', t, count=1, flags=re.M)     # Twin Souls / dual-cast gates
        assert 'MagicEffectSummonCreatureArchetype' in t, base
        write('MagicEffects', t)


# ------------------------------------------------------------------------------------------------ Sorcerer
# (curator 2026-10-27) Kittytails' Obscure Magic (KittySpellPack01.esl), Elemental Mastery Magic (KittySpellPack02.esl)
# and Constellation Magic (Supernova.esl), installed and mastered, cleaned by src/KittytailsPacksClean. The menu grants
# six of their spells; Prophecy overrides each (it is their only patcher) with an Enderal name (the curator: lore
# friendly - no Aetherius, Psijics; Magicka is Mana in Enderal's text) and a price on EGO's FireAndForget ladder
# (tier 50: 77, tier 75: 97; the packs use Skyrim's scale), and renames the effects the player sees. Damage is the
# packs'. Shatterveil (2026-10-28, installed and mastered; its DLL runs the effigies, the dash and the wyrm) gives
# Blink Step, the two tiered effigy lines (SHVL_TIERS) and the capstone shout - its SkyPatcher tome list is not
# installed, and its ini has the wyrm's songs off. Drowning Orb: its hazard re-casts the pack's "Wade" spell
# 000828 on everyone inside every 0.2 s; Prophecy's override adds an Absorb Mana (enemies only). The hazard never
# applies its spell to its own caster (a player-only restore added there did nothing in game, 2026-10-27), so the
# player's restore inside the orb is the Drowning Orb talent's ability, ZP_DrowningOrbWatch: after an orb cast it
# looks for the hazard within 320 units twice a second. Allocated after Druid. Append LAST.
SORC_TREE = 'Sorcery'
SORC_FIRST_ID = 0xA9F
SORC_RECORDS = ('marker', 'markerme', 'power', 'powerme')   # Mana Burn's; marker/power retired 2026-10-28, never reuse
SORC_LATE_FIRST_ID = 0xAD3
SORC_LATE_RECORDS = ('regen', 'orbdrain', 'orbwatch', 'orbwatchme', 'burnfxs')   # regen, burnfxs: Mana Burn's
ORB_WADE = '000828:KittySpellPack01.esl'           # _K01_PsijicWaterGlobeHazardEffect, the orb's hazard spell
ORB_HAZARD = '000853:KittySpellPack01.esl'         # _K01_PsijicWaterGlobeHazard
# Drowning Orb is water: its effects move from Mentalism (Alteration) to Elementalism (Destruction) - the skill lowers
# its cost and gains from it - and carry MagicDamageFrost, the keyword Enderal's Elementalist talents boost (Arcane
# Might 069D0B, Elemental Frenzy 069D0E: ModSpellMagnitude on spells with fire/frost/shock keywords). Curator 2026-10-27
ORB_EFFECTS = ('000812:KittySpellPack01.esl', '000811:KittySpellPack01.esl', '000813:KittySpellPack01.esl')
FROST_KW = '01CEAE:Skyrim.esm'                      # MagicDamageFrost
K01, K02, SNV, SHVL = 'KittySpellPack01.esl', 'KittySpellPack02.esl', 'Supernova.esl', 'Shatterveil.esp'
SORC_REF = {K01: 'ObscureMagic', K02: 'ElementalMasteryMagic', SNV: 'ConstellationMagic',
            SHVL: 'Shatterveil'}   # reference/mods/, serialized
# node -> (pack's player spell, Enderal name, Mana cost). Shatterveil's costs on EGO's FireAndForget ladder
# (30/53/76/97/124 by tier; the mod's own run 45-1300)
SORC_SPELLS = {'sor3': ('Diamond Splash', f'000825:{K02}', 'Frost Spires', 97),
               'sor10': ('Water Globe', f'000829:{K01}', 'Drowning Orb', 39),      # half the tier-50 price (curator)
               'sor4': ('Flare Storm', f'000829:{K02}', 'Wildfire', 97),
               'sor5': ('Celestial Rays', f'000814:{SNV}', 'Starlance', 97),
               'sor1': ('Blink Step', f'000E52:{SHVL}', 'Blink Step', 20),        # the root since 2026-10-28 (was sor6)
               'sor7': ('Celestial Vortex', f'000827:{K01}', 'Gravity Well', 97),
               'sor8': ('Stardust', f'000815:{SNV}', 'Falling Star', 97)}
# Shatterveil's tiered lines (curator 2026-10-28): the talent's ability (ZP_SpellTierWatch) gives the tier the player's
# Psionics (Illusion) reaches and takes back the lower ones - the apprentice tier from the start, the mod's own
# MinimumSkillLevel for the others. The menu grants nothing for these nodes. node -> (record key, [(spell, cost, skill)])
SHVL_TIERS = {'sor6': ('tiertwin', [(f'000F10:{SHVL}', 53, 0), (f'000F11:{SHVL}', 76, 50),
                                    (f'000F12:{SHVL}', 97, 75), (f'000F13:{SHVL}', 124, 100)])}
# tierburst/tierburstme: Bursting Effigy's tier ability (sor1 on 2026-10-28), retired - never reuse. tiertwin/tiertwinme
# are Twin Effigies' again (sor2 first, then sor6, both 2026-10-28)
SHVL_LATE_RECORDS = ('tierburst', 'tierburstme', 'tiertwin', 'tiertwinme', 'orbitab', 'orbitme',   # after Ice Shot's
                     'wyrmsnd', 'blinkme', 'gwabsorb', 'blinksnd', 'blinkmarker', 'blinkplay')
# Orbit Ward (sor2, curator 2026-10-28: "an effect while casting spells that drops afterward, like Arcane Archery's
# ward"): the talent's ability runs ZP_CastWardEffect, which casts Shatterveil's own Orbit Ward spell on the player at
# BeginCastRight/Left (no Mana: Spell.Cast) and dispels it when the cast ends. The DLL starts the orbiting wards on the
# effect's apply event; whether a dispel also takes them away is the DLL's (unverified)
ORBIT_WARD = f'000E55:{SHVL}'      # shvl_PrismWardSpell
WYRM_SHOUT = f'000E6A:{SHVL}'      # shvl_GlassWyrmShout, Sorcery's capstone (sor9); the menu teaches all three words
# The shout's slow time is Shatterveil's spell shvl_VeilWyrmSlowTime, whose effect is vanilla VoiceSlowTime 048ACD -
# not in Enderal, so the engine dropped it (0 effects in game, 2026-10-28 probe) and the DLL skipped slow time. Prophecy
# overrides the spell onto Enderal's own SlowTime effect (_00E_Game_SlowTimeME, its slow-time ability's); the DLL sets
# the magnitude from fShoutSlowTime itself
WYRM_SLOW = (f'000F26:{SHVL}', '048ACD:Skyrim.esm', '13FB41:Skyrim.esm')
# The shout's own sound (curator 2026-10-28): Shatterveil's wyrm sounds all report "playing" at the player and are
# silent on 1.7.104 (cause open, see ShatterveilAE.md), so the curator's Motion Array glass impact (converted to 16-bit
# PCM, loose, not committed; tools/07-build-sounds.py mixes it with a whale clip) plays as the Release sound of the three word effects - the engine's own spell sound, no
# DLL involved. Stereo output (SOMStereo) so it is never attenuated.
WYRM_WORD_MGEFS = (f'000E6E:{SHVL}', f'000E6F:{SHVL}', f'000E70:{SHVL}')
WYRM_WORD_SPELLS = (f'000E6B:{SHVL}', f'000E6C:{SHVL}', f'000E6D:{SHVL}')   # each word's Voice spell: + Mana Burn's buff
BURN_NAME = 'Mana Burn'
# Mana Burn's look: Enderal's Onslaught talent cloak shader (flames thrown off the body, a glowing edge), copied and
# turned Mana-blue through a palette, with the vanilla shock cloak's arcs around the player
ONSLAUGHT_FXS = os.path.join(REF, 'base', 'Skyrim', 'EffectShaders', '_00E_A1_OnslaughtCloakFXS - 033478_Skyrim.esm.yaml')
BURN_ART = '05B1BC:Skyrim.esm'                      # FXShockCloak01
WYRM_SOUND_FILE = r'Data\Sound\FX\ZenProphecy\ZP_VeilWyrmGlassImpact.wav'
SORC_LORE = [('Magicka', 'Mana'), ('from the Aetherius', 'from the night sky'), ('mystic water', 'water'),
             ('meteorite', 'falling star')]


def sorc_perk(s):
    return ('Effects:\n- MutagenObjectType: PerkEntryPointModifyValue\n  Priority: 100\n  Conditions:\n  - Conditions:\n'
            '    - MutagenObjectType: ConditionFloat\n      Data:\n        MutagenObjectType: HasMagicEffectConditionData\n'
            f"        MagicEffect: {s['markerme']}\n      ComparisonValue: 1\n  EntryPoint: ModSpellCost\n"
            f"  PerkConditionTabCount: 2\n  Modification: Multiply\n  Value: {SORC['CostMult']}\n")


def blink_power(t, s):
    """Blink Step as a lesser power that costs BLINK_MANA (see BLINK_MANA)"""
    t, n = re.subn(r'^EquipmentType: .*$', 'EquipmentType: 025BEE:Skyrim.esm', t, count=1, flags=re.M)
    assert n == 1, 'Blink Step: equip type'
    t, n = re.subn(r'^CastType: FireAndForget$', 'Type: LesserPower\nCastType: FireAndForget', t, count=1, flags=re.M)
    assert n == 1 and t.count('Type: LesserPower') == 1, 'Blink Step: type'
    t = re.sub(r'^HalfCostPerk: .*\n', '', t, flags=re.M)
    cond = ('  Conditions:\n  - MutagenObjectType: ConditionFloat\n    CompareOperator: GreaterThanOrEqualTo\n'
            '    Data:\n      MutagenObjectType: GetActorValueConditionData\n      ActorValue: Magicka\n'
            f'    ComparisonValue: {BLINK_MANA}\n')
    t, n = re.subn(r'^(- BaseEffect: 000E51:Shatterveil\.esp\n  Data: \{\}\n)', lambda m: m.group(1) + cond, t, flags=re.M)
    assert n == 1, 'Blink Step: effect'
    return (t.rstrip('\n') + f"\n- BaseEffect: {s['blinkme']}\n  Data:\n    Magnitude: {BLINK_MANA}\n" + cond +
            f"- BaseEffect: {s['blinkplay']}\n  Data: {{}}\n" + cond +
            f"- BaseEffect: {s['swooshplay']}\n  Data: {{}}\n" + cond)


def sorc_record(fk):
    hexid, plugin = fk.split(':')
    p = glob.glob(os.path.join(REF, 'mods', SORC_REF[plugin], '*', f'* - {hexid}_{plugin}.yaml'))
    assert len(p) == 1, f'{fk} not in reference/mods/{SORC_REF[plugin]}: serialize the cleaned pack there'
    return os.path.basename(os.path.dirname(p[0])), open(p[0], encoding='utf-8').read().replace('\r\n', '\n')


MARKSMAN_ENUM_LINE = re.compile(r'^\s*(?:- )?(?:Key|Skill|ActorValue|SecondActorValue|Teaches|MagicSkill|ResistValue|'
                                r'CastingSkill|AssociatedItem|EditorID|Name|Object)\s*:\s*\S*Archery')


def marksman(t):
    """The skill is "Marksman" in Enderal's own interface (translate_english.txt: $Archery = Marksman), so every
    shown "Archery" that names the skill becomes Marksman (curator 2026-10-29). Not the tree "Arcane Archery", not
    actor-value keys (Key/Skill/ActorValue: Archery), EditorIDs or script property names."""
    out = []
    for line in t.split('\n'):
        if not MARKSMAN_ENUM_LINE.match(line):
            line = re.sub(r'(?<!Arcane )\bArchery\b', 'Marksman', line)
        out.append(line)
    return '\n'.join(out)


def sorc_tune(fk, t):
    """SORC_TUNE's magnitudes on one record's text (each change asserted)"""
    for eff, nth, mag in SORC_TUNE.get(fk, []):
        blocks = [m for m in re.finditer(rf'^- BaseEffect: {re.escape(eff)}\n  Data:\n(?:    (?!Magnitude).*\n)*    Magnitude: ([\d.]+)$',
                                         t, re.M)]
        assert len(blocks) > nth, f'{fk}: effect {eff} #{nth} has no Magnitude'
        m = blocks[nth]
        t = t[:m.start(1)] + f'{mag:g}' + t[m.end(1):]
    return t


def write_sorcerer(s, write):
    def rename(t, name, what):
        t, n = re.subn(r'^Name:\n  TargetLanguage: English\n  Value: .*\n',
                       f"Name:\n  TargetLanguage: English\n  Value: '{name}'\n", t, count=1, flags=re.M)
        assert n == 1, f'{what}: name'
        return t

    def lore(t, desc=None):
        def fix(m):
            v = m.group(2)
            if desc is not None and v.strip("'") != '': v = "'" + desc.replace("'", "''") + "'"
            for a, b in SORC_LORE: v = v.replace(a, b)
            return m.group(1) + v
        return re.sub(r'^(Description:\n  TargetLanguage: English\n  Value: )(.*)$', fix, t, count=1, flags=re.M)

    def no_dlc(t, what):
        # a field naming a Dawnguard/Dragonborn form (empty stubs in Enderal: the pack's own record already resolves to
        # nothing there) is dropped, so Prophecy needs no DLC master - Constellation's ImpactData 01A3FB:Dawnguard.esm
        t = re.sub(r'^[A-Za-z]+: [0-9A-F]{6}:(?:Dawnguard|Dragonborn)\.esm\n', '', t, flags=re.M)
        assert not re.search(r':(?:Dawnguard|Dragonborn)\.esm', t), f'{what}: a DLC form left in a list'
        return t

    def elementalism(t, what):
        """Drowning Orb's effects: Elementalism (Destruction) and the frost keyword (ORB_EFFECTS)"""
        t, n = re.subn(r'^MagicSkill: Alteration$', 'MagicSkill: Destruction', t, flags=re.M)
        assert n == 1, f'{what}: school'
        if re.search(r'^Keywords:$', t, re.M):
            t, n = re.subn(r'^(Keywords:\n(?:- .*\n)*)', lambda m: m.group(1) + f'- {FROST_KW}\n', t, count=1, flags=re.M)
        else:
            t, n = re.subn(r'^Flags:$', f'Keywords:\n- {FROST_KW}\nFlags:', t, count=1, flags=re.M)
        assert n == 1, f'{what}: keyword'
        return t

    def effects(spell_text, plugin, name, desc=None):
        """the spell's own visible effects: the spell's Enderal name, lore-fixed text"""
        for e in re.findall(r'^- BaseEffect: (\S+)$', spell_text, re.M):
            if not e.endswith(':' + plugin): continue
            ty, t = sorc_record(e)
            if re.search(r'^- HideInUI$', t, re.M): continue
            t = no_dlc(lore(rename(t, name, e), desc), e)
            write(ty, elementalism(t, e) if e in ORB_EFFECTS else t)

    for nid, (old, fk, name, cost) in SORC_SPELLS.items():
        ty, t = sorc_record(fk)
        assert re.search(rf"^  Value: {re.escape(old)}$", t, re.M), f'{fk} is not {old}'
        t = rename(t, name, fk)
        t, n = re.subn(r'^BaseCost: \d+$', f'BaseCost: {cost}', t, flags=re.M)
        assert n == 1 and '- ManualCostCalc' in t, f'{fk}: cost'
        if nid == 'sor1':
            t = blink_power(t, s)
        t = sorc_tune(fk, t)
        write(ty, no_dlc(t, fk))
        effects(t, fk.split(':')[1], name)
    # Drowning Orb: the hazard's Wade spell, plus the Mana drain from enemies. The player's restore inside the orb is
    # ZP_DrowningOrbWatch's: a restore added here never reached the player (the hazard skips its own caster; in game)
    ty, t = sorc_record(ORB_WADE)
    assert t.rstrip('\n').endswith('Magnitude: 30'), f'{ORB_WADE}: Effects is not the last block'
    t = sorc_tune(ORB_WADE, t)
    write(ty, t.rstrip('\n') + f"""
- BaseEffect: {s['orbdrain']}
  Data:
    Magnitude: {SORC['OrbDrain']}
    Duration: 1
  Conditions:
  - MutagenObjectType: ConditionFloat
    Data:
      MutagenObjectType: IsHostileToActorConditionData
      TargetNpc: 000014:Skyrim.esm
    ComparisonValue: 1
""")
    for e in ORB_EFFECTS[1:]:
        ty, et = sorc_record(e)
        write(ty, elementalism(et, e))
    # the sub-spells that carry the damage (balance pass 2026-10-29): Wildfire's homing fire, Starlance's beam
    for fk in ('000827:KittySpellPack02.esl', '000816:Supernova.esl'):
        ty, t = sorc_record(fk)
        write(ty, no_dlc(sorc_tune(fk, t), fk))
    write('MagicEffects', f"""FormKey: {s['orbdrain']}
EditorID: ZP_Prophecy_DrowningOrb_AbsorbMana
Name:
  TargetLanguage: English
  Value: Drowning Orb
MenuDisplayObject: 0435A5:Skyrim.esm
Keywords:
- {FROST_KW}
Flags:
- Hostile
- Detrimental
- NoArea
- FXPersist
- NoDeathDispel
- Painless
MagicSkill: Destruction
ResistValue: ResistMagic
Archetype:
  MutagenObjectType: MagicEffectArchetype
  ActorValue: Magicka
  Type: Absorb
CastType: FireAndForget
TargetType: Touch
DualCastScale: 1
Sounds: []
Description:
  TargetLanguage: English
  Value: Absorbs <mag> Mana per second.
""")
    write('Spells', f"""FormKey: {s['orbwatch']}
EditorID: ZP_Prophecy_DrowningOrb_Watch
Name:
  TargetLanguage: English
  Value: Drowning Orb
EquipmentType: 013F44:Skyrim.esm
Description:
  TargetLanguage: English
  Value: ''
Flags:
- ManualCostCalc
- IgnoreResistance
- NoAbsorbOrReflect
Type: Ability
CastType: ConstantEffect
Effects:
- BaseEffect: {s['orbwatchme']}
  Data: {{}}
""")
    write('MagicEffects', f"""FormKey: {s['orbwatchme']}
EditorID: ZP_Prophecy_DrowningOrb_WatchEffect
VirtualMachineAdapter:
  Scripts:
  - Name: ZP_DrowningOrbWatch
    Properties:
    - MutagenObjectType: ScriptObjectProperty
      Name: OrbSpell
      Object: {SORC_SPELLS['sor10'][1]}
    - MutagenObjectType: ScriptObjectProperty
      Name: OrbHazard
      Object: {ORB_HAZARD}
    - MutagenObjectType: ScriptFloatProperty
      Name: RestorePerSecond
      Data: {float(SORC['OrbRegen'])}
Name:
  TargetLanguage: English
  Value: Drowning Orb
Flags:
- HideInUI
- NoMagnitude
- NoArea
- NoDuration
- Painless
Archetype:
  MutagenObjectType: MagicEffectArchetype
  Type: Script
CastType: ConstantEffect
TargetType: Self
DualCastScale: 1
Sounds: []
Description:
  TargetLanguage: English
  Value: ''
""")
    # Shatterveil's tiered lines: each spell on EGO's ladder, and the talent's ability that gives the tier
    for nid, (key, tiers) in SHVL_TIERS.items():
        for fk, cost, _ in tiers:
            ty, st = sorc_record(fk)
            st, n = re.subn(r'^BaseCost: \d+$', f'BaseCost: {cost}', st, flags=re.M)
            assert n == 1 and '- ManualCostCalc' in st, f'{fk}: cost'
            write(ty, st)
        name = re.search(r'^  Value: (.+)$', sorc_record(tiers[0][0])[1], re.M).group(1)
        write('Spells', f"""FormKey: {s[key]}
EditorID: ZP_Prophecy_{name.replace(' ', '')}_Tiers
Name:
  TargetLanguage: English
  Value: {name}
EquipmentType: 013F44:Skyrim.esm
Description:
  TargetLanguage: English
  Value: ''
Flags:
- ManualCostCalc
- IgnoreResistance
- NoAbsorbOrReflect
Type: Ability
CastType: ConstantEffect
Effects:
- BaseEffect: {s[key + 'me']}
  Data: {{}}
""")
        write('MagicEffects', f"""FormKey: {s[key + 'me']}
EditorID: ZP_Prophecy_{name.replace(' ', '')}_TiersEffect
VirtualMachineAdapter:
  Scripts:
  - Name: ZP_SpellTierWatch
    Properties:
    - MutagenObjectType: ScriptObjectListProperty
      Name: Tiers
      Objects:
""" + ''.join(f'      - Object: {fk}\n' for fk, _, _ in tiers) + """    - MutagenObjectType: ScriptIntListProperty
      Name: MinSkill
      Data:
""" + ''.join(f'      - {sk}\n' for _, _, sk in tiers) + f"""Name:
  TargetLanguage: English
  Value: {name}
Flags:
- HideInUI
- NoMagnitude
- NoArea
- NoDuration
- Painless
Archetype:
  MutagenObjectType: MagicEffectArchetype
  Type: Script
CastType: ConstantEffect
TargetType: Self
DualCastScale: 1
Sounds: []
Description:
  TargetLanguage: English
  Value: ''
""")


    # the Veil Wyrm's slow time on Enderal's SlowTime effect (WYRM_SLOW)
    ty, st = sorc_record(WYRM_SLOW[0])
    st, n = re.subn(rf'^- BaseEffect: {WYRM_SLOW[1]}$', f'- BaseEffect: {WYRM_SLOW[2]}', st, flags=re.M)
    assert n == 1, 'Veil Wyrm slow time: effect'
    write(ty, st)
    # Mana Burn on the shout: its restore, its aura shader and marker effect, added to each word's Voice spell
    write('MagicEffects', f"""FormKey: {s['regen']}
EditorID: ZP_Prophecy_ManaBurn_Regen
Name:
  TargetLanguage: English
  Value: {BURN_NAME}
MenuDisplayObject: 0435A5:Skyrim.esm
Flags:
- NoArea
- NoDeathDispel
- Painless
Archetype:
  MutagenObjectType: MagicEffectArchetype
  ActorValue: Magicka
CastType: FireAndForget
TargetType: Self
DualCastScale: 1
Sounds: []
Description:
  TargetLanguage: English
  Value: Restores <mag> Mana per second.
""")
    fx = open(ONSLAUGHT_FXS, encoding='utf-8').read().replace('\r\n', '\n')
    for a, b in ((r'^FormKey: .*$', f"FormKey: {s['burnfxs']}"),
                 (r'^EditorID: .*$', 'EditorID: ZP_Prophecy_ManaBurn_FXS'),
                 (r"^ParticlePaletteTexture: ''$", r'ParticlePaletteTexture: Effects\Gradients\GradBlueBright.dds'),
                 (r"^EdgeEffectColor: .*$", "EdgeEffectColor: '#002A6CFF'"),
                 (r"^FillColorKey1: .*$", "FillColorKey1: '#00050A1E'"),
                 (r'^MembraneSourceBlendMode:', 'Flags:\n- ParticleGrayscaleColor\nMembraneSourceBlendMode:')):
        fx, n = re.subn(a, lambda m, b=b: b, fx, count=1, flags=re.M)
        assert n == 1, f'Mana Burn shader: {a}'
    assert '\nFlags:' in fx and fx.count('Flags:') == 1, 'Mana Burn shader: Flags'
    write('EffectShaders', fx)
    write('MagicEffects', f"""FormKey: {s['markerme']}
EditorID: ZP_Prophecy_ManaBurn_MarkerEffect
Name:
  TargetLanguage: English
  Value: {BURN_NAME}
Flags:
- NoMagnitude
- NoArea
- Recover
- FXPersist
HitShader: {s['burnfxs']}
HitEffectArt: {BURN_ART}
Archetype:
  MutagenObjectType: MagicEffectArchetype
  Type: Script
CastType: FireAndForget
TargetType: Self
DualCastScale: 1
Sounds: []
Description:
  TargetLanguage: English
  Value: Your spells cost half as much Mana for <dur> seconds.
""")
    for fk in WYRM_WORD_SPELLS:
        ty, wt = sorc_record(fk)
        assert wt.rstrip('\n').endswith('  Data: {}'), f'{fk}: Effects is not the last block'
        write(ty, wt.rstrip('\n') + f"""
- BaseEffect: {s['markerme']}
  Data:
    Duration: {SORC['BurnSeconds']}
- BaseEffect: {s['regen']}
  Data:
    Magnitude: {SORC['RegenPerSecond']}
    Duration: {SORC['BurnSeconds']}
""")
    # Gravity Well's Health drain (GW_ABSORB)
    write('MagicEffects', f"""FormKey: {s['gwabsorb']}
EditorID: ZP_Prophecy_GravityWell_AbsorbHealth
Name:
  TargetLanguage: English
  Value: Gravity Well
MenuDisplayObject: 0435A5:Skyrim.esm
Flags:
- Hostile
- Detrimental
- NoArea
- NoDuration
- NoDeathDispel
MagicSkill: Alteration
ResistValue: ResistMagic
Archetype:
  MutagenObjectType: MagicEffectArchetype
  ActorValue: Health
  Type: Absorb
CastType: FireAndForget
TargetType: Touch
DualCastScale: 1
Sounds: []
Description:
  TargetLanguage: English
  Value: Absorbs <mag> Health.
""")
    ty, gt = sorc_record(GW_HAZARD_SPELL)
    absorb = (f"- BaseEffect: {s['gwabsorb']}\n  Data:\n    Magnitude: {GW_ABSORB}\n  Conditions:\n"
              "  - MutagenObjectType: ConditionFloat\n    Data:\n      MutagenObjectType: HasMagicEffectConditionData\n"
              f"      MagicEffect: {GW_COOLDOWN_MGEF}\n    ComparisonValue: 0\n"
              "  - MutagenObjectType: ConditionFloat\n    Data:\n      MutagenObjectType: IsHostileToActorConditionData\n"
              "      TargetNpc: 000014:Skyrim.esm\n    ComparisonValue: 1\n")
    gt, n = re.subn(r'^Effects:\n', 'Effects:\n' + absorb, gt, count=1, flags=re.M)
    assert n == 1 and gt.index(s['gwabsorb']) < gt.index(GW_COOLDOWN_MGEF), 'Gravity Well: absorb first'
    write(ty, gt)
    # Blink Step's cast sound (BLINK_CAST_SOUND): a marker + a script effect, the spell's third effect
    sound_records(write, {'sound': s['blinksnd'], 'marker': s['blinkmarker'], 'mgef': s['blinkplay']}, 'BlinkStep',
                  'Blink Step', None, descriptor=BLINK_CAST_SOUND)
    sound_records(write, {'sound': s['swooshsnd'], 'marker': s['swooshmarker'], 'mgef': s['swooshplay']},
                  'BlinkStepSwoosh', 'Blink Step', BLINK_SWOOSH_FILE)
    # Blink Step's Mana price (blink_power)
    write('MagicEffects', f"""FormKey: {s['blinkme']}
EditorID: ZP_Prophecy_BlinkStep_ManaCost
Name:
  TargetLanguage: English
  Value: Blink Step
Flags:
- Detrimental
- NoArea
- NoDuration
- HideInUI
- Painless
Archetype:
  MutagenObjectType: MagicEffectArchetype
  ActorValue: Magicka
CastType: FireAndForget
TargetType: Self
DualCastScale: 1
Sounds: []
Description:
  TargetLanguage: English
  Value: ''
""")
    # the shout's recovery times x WYRM_COOLDOWN_MULT
    ty, sh = sorc_record(WYRM_SHOUT)
    olds = [int(x) for x in re.findall(r'^  RecoveryTime: (\d+)$', sh, re.M)]
    assert olds == [20, 35, 50], f'Veil Wyrm recovery times {olds}'
    sh = re.sub(r'^  RecoveryTime: (\d+)$', lambda m: f'  RecoveryTime: {int(m.group(1)) * WYRM_COOLDOWN_MULT}', sh, flags=re.M)
    write(ty, sh)
    # the shout's glass impact (WYRM_SOUND_FILE) as each word effect's Release sound
    write('SoundDescriptors', f"""FormKey: {s['wyrmsnd']}
EditorID: ZP_Prophecy_VeilWyrmGlassImpactSD
Type: Standard
Category: 0172A1:Skyrim.esm
SoundFiles:
- {WYRM_SOUND_FILE}
OutputModel: 07EDCA:Skyrim.esm
LoopAndRumble: {{}}
Priority: 128
""")
    for fk in WYRM_WORD_MGEFS:
        ty, mt = sorc_record(fk)
        mt, n = re.subn(r'^Sounds: \[\]$', f"Sounds:\n- Type: Release\n  Sound: {s['wyrmsnd']}", mt, flags=re.M)
        assert n == 1, f'{fk}: Sounds'
        write(ty, mt)
    # Orbit Ward while casting
    write('Spells', f"""FormKey: {s['orbitab']}
EditorID: ZP_Prophecy_OrbitWard_Ability
Name:
  TargetLanguage: English
  Value: Orbit Ward
EquipmentType: 013F44:Skyrim.esm
Description:
  TargetLanguage: English
  Value: ''
Flags:
- ManualCostCalc
- IgnoreResistance
- NoAbsorbOrReflect
Type: Ability
CastType: ConstantEffect
Effects:
- BaseEffect: {s['orbitme']}
  Data: {{}}
""")
    write('MagicEffects', f"""FormKey: {s['orbitme']}
EditorID: ZP_Prophecy_OrbitWard_Effect
VirtualMachineAdapter:
  Scripts:
  - Name: ZP_CastWardEffect
    Properties:
    - MutagenObjectType: ScriptObjectProperty
      Name: Ward
      Object: {ORBIT_WARD}
Name:
  TargetLanguage: English
  Value: Orbit Ward
Flags:
- HideInUI
- NoMagnitude
- NoArea
- NoDuration
- Painless
Archetype:
  MutagenObjectType: MagicEffectArchetype
  Type: Script
CastType: ConstantEffect
TargetType: Self
DualCastScale: 1
Sounds: []
Description:
  TargetLanguage: English
  Value: ''
""")


# ------------------------------------------------------------------------------------------------ Unsold tomes
# (curator, 2026-10-28) A spell Prophecy grants is not for sale. Only Triumvirate's tomes reach shops: Triumvirate -
# Enderal Patch puts its TVR_Tomes_Litem_* bundles into three merchant lists (BibliothekarMarius 0302D2, Undercity
# fence 030307, Undercity wild mage 0302F0) and does no runtime distribution (its TVR_PopulateSpellBooks_Script says
# so). Kittytails' packs inject into vanilla tome lists Enderal does not have (0FDE79, 0A272F, ...) and Aero into a
# Dragonborn stub list, so theirs never sell. Prophecy overrides every bundle holding a granted spell's tome (the
# winning record, the Enderal patch's) minus those entries; merchant lists stay untouched.
def write_unsold_tomes(write):
    granted = set(SHADOW_GRANTS.values()) | set(DRUID_GRANTS.values())
    # + the two Druid talents that grant our own versions of Triumvirate spells (curator 2026-10-29: "remove any spells
    # unlocked via this talent tree from vendors"): Druidcraft's and Force of Nature's tomes teach Triumvirate's originals
    granted |= {DRUIDCRAFT_SPELL, FON_SPELL}
    granted = {g for g in granted if g.endswith(':' + TRIUMVIRATE)}
    tomes = set()
    for f in glob.glob(os.path.join(REF, 'mods', 'Triumvirate', 'Books', '*.yaml')):
        b = open(f, encoding='utf-8').read().replace('\r\n', '\n')
        sp = re.search(r'^  Spell: (.+)$', b, re.M)
        if sp and sp.group(1) in granted:
            tomes.add(re.search(r'^FormKey: (.+)$', b, re.M).group(1))
    assert len(tomes) == len(granted), f'{len(tomes)} tomes for {len(granted)} granted Triumvirate spells'
    lists = 0
    for f in sorted(glob.glob(os.path.join(REF, 'mods', 'TriumvirateEnderalPatch', 'LeveledItems', 'TVR_Tomes_Litem_*.yaml'))):
        t = open(f, encoding='utf-8').read().replace('\r\n', '\n')
        if not any(tm in t for tm in tomes):
            continue
        before = t.count('    Reference: ')
        t, n = re.subn(r'^- Data:\n(?:    .*\n)*?    Reference: (?:' + '|'.join(map(re.escape, tomes)) + r')\n(?:    .*\n)*',
                       '', t, flags=re.M)
        assert n >= 1 and t.count('    Reference: ') == before - n and not any(tm in t for tm in tomes), f
        if t.count('    Reference: ') == 0:
            t = re.sub(r'^Entries:\n', '', t, flags=re.M)
        write('LeveledItems', t)
        lists += 1
    print(f'unsold tomes: {len(tomes)} tomes taken out of {lists} Triumvirate tome lists')


# ------------------------------------------------------------------------------------------------ Rage
# (curator 2026-10-27) See the tree's comment. ZenProphecyRage.dll (src/Prophecy/rage) reads
# Data/SKSE/Plugins/ZenProphecyRage.json, written here: Prophecy's IDs plus A Dark Warrior's Tale's action spells
# (KittyClass_DarkWarrior.esp, by local ID; the DLL resolves them at load, so Prophecy needs no master for them - if the
# pack is missing, the actions are skipped and logged). Each action casts the pack's damage spell and its visual on the
# target from the player, as the pack's _CDW_MagicCastMultipleSpellsScript did - never its "rebound" Health cost
# (_CDW_ClassReboundDmg2/6, 2-6 Health per second on the player: the class's price; Rage is ours).
# Allocated after Sorcerer. Append new ones LAST.
RAGE_TREE = 'Rage'
RAGE_FIRST_ID = 0xAB9
RAGE_RECORDS = ('global', 'vehspell', 'vehme', 'rageab', 'rageabme')   # rageab: the stack count, shown as its magnitude
DW = 'KittyClass_DarkWarrior.esp'
RAGE_JSON = os.path.join(PATCH, 'data', 'SKSE', 'Plugins', 'ZenProphecyRage.json')
# node -> (trigger, [the pack's spells cast on the target]); triggers are the DLL's: sprint = a power attack while
# sprinting or within a second of it; the rest by the attack's PowerAttackType keyword (0914E5-0914E8)
RAGE_ACTIONS = {'rge2': ('sprint', ['000835', '00083D']),                # Heavenfall: _CDW_DarkWarriorBeamSlash_Upgraded + VFX
                'rge3': ('forward', ['000834', '00083C']),               # Shadow Carve: _CDW_DarkWarriorBeamSlash + VFX
                'rge4': ('back', ['000853', '000857']),                  # Dark Deluge: _CDW_DarkWarriorPierce + VFX
                'rge5': ('standing', ['000FAB', '000FAC']),              # Shadowbringer: _CDW_DarkWarriorBeamSlash2 + VFX
                'rge6': ('side', ['000832', '00083F', '00158A']),        # Bloodletter: _CDW_DarkWarriorSlash + VFX + FakeAbsorbRestoreHealth
                'rge7': ('side', ['000833', '00083E', '00158B'])}        # Soulrender: _CDW_DarkWarriorFlash + VFX + FakeAbsorbRestoreMagickaStamina
POWER_ATTACK_TYPES = {'standing': '0914E5', 'forward': '0914E6', 'side': '0914E7', 'back': '0914E8'}


def rage_perk(nid, r):
    if nid == 'rge1':    # the Rage ability (the DLL writes the stack count into its magnitude) and, per stack,
                         # attacks x(1 + DamagePerStack%), stacking (ZP_Rage >= k)
        return 'Effects:\n- MutagenObjectType: PerkAbilityEffect\n  Ability: ' + r['rageab'] + '\n' + ''.join(
            '- MutagenObjectType: PerkEntryPointModifyValue\n  Priority: 100\n  Conditions:\n  - Conditions:\n'
            '    - MutagenObjectType: ConditionFloat\n      CompareOperator: GreaterThanOrEqualTo\n      Data:\n'
            f"        MutagenObjectType: GetGlobalValueConditionData\n        Global: {r['global']}\n      ComparisonValue: {k}\n"
            '  EntryPoint: ModAttackDamage\n  PerkConditionTabCount: 3\n  Modification: Multiply\n'
            f"  Value: {1 + RAGE['DamagePerStack'] / 100}\n" for k in range(1, RAGE['MaxUntempered'] + 1))
    if nid == 'rge9':    # Vehemence: power attacks cost no Stamina while it is on
        return ('Effects:\n- MutagenObjectType: PerkEntryPointModifyValue\n  Priority: 100\n  Conditions:\n  - Conditions:\n'
                '    - MutagenObjectType: ConditionFloat\n      Data:\n        MutagenObjectType: HasMagicEffectConditionData\n'
                f"        MagicEffect: {r['vehme']}\n      ComparisonValue: 1\n  EntryPoint: ModPowerAttackStamina\n"
                '  PerkConditionTabCount: 2\n  Modification: Multiply\n  Value: 0\n')
    return ''


# Twin Effigies cast the player's spells (curator 2026-10-29: "the Effigies need to be able to cast the spells I have
# equipped at the time of casting it" - Shatterveil copies weapons only, so a caster's effigies punched). Shatterveil's
# records: shvl_TwinDecoys{Apprentice,Adept,Expert,Master}Spell, shvl_DecoyFaction, shvl_DecoyBase.
# Then (curator 2026-10-29): "not cast our own spells but just chain lightning - infinitely casting any spell was terrible
# for balance": each effigy casts Flow State's Chain Lightning (flowchain, 40 Shock) every CastEvery s, nothing else
EFFIGY_CAST = {'Spells': ('000F10', '000F11', '000F12', '000F13'), 'Faction': '000800', 'Base': '000F01',
               'CastEvery': EFFIGY_EVERY, 'Range': 2048.0, 'SpawnWindow': 3.0}
DRAGON_ELEMENTS = ('Fire', 'Frost', 'Shock')
DRAGON_RECORDS = (tuple(f'{e}{k}' for e in DRAGON_ELEMENTS for k in ('spell', 'me', 'proj')) +
                  tuple(f'{e}expl' for e in DRAGON_ELEMENTS))   # the blasts' look (2026-10-28): appended last
# each element's spell (curator 2026-10-29: "Fire = Explosion, Frost = Freeze, Lightning = Chain lightning spell
# triggers on enemy"), cast by the DLL from the player at the punched enemy. Earlier builds (cones from Hissing Dragon
# / the breath shouts, bursts at the fist) are gone; their IDs stay allocated, unwritten:
# - Fire: vanilla's fireball - a copy of FireDamageFFAimedArea 01CEA1 (fireball missile 10FBED, kept) whose
#   explosion is a copy of FireBallExp01 0439C0 without its image-space flash
# - Frost: vanilla Ice Spike's frost damage (a copy of FrostDamageFFAimed 01CEA2, its spike 02F774) plus Ice Shot's
#   freeze (ZP_IceShotFreezeEffect: AI off, paralysed, iced over) in an Aimed copy, DRAGON_FREEZE_SECONDS. The first
#   build cast Ice Shot's TargetActor freeze spell and nothing froze in game (2026-10-29) while the two Aimed spells
#   worked, so frost is a projectile spell too. Its records use the Frost 'me' (damage) and 'proj' (freeze) IDs
# - Lightning: vanilla's Chain Lightning - a copy of ShockDamageFFAimedArea 05DBAE (bolt 0A9D92, kept) whose explosion
#   is a copy of ChainLightningExplosion 05DBAD (the Chain flag makes it leap), both without the image-space flash
DRAGON_SPELL_SRC = {'Fire': ('FireDamageFFAimedArea - 01CEA1_Skyrim.esm.yaml', 'FireBallExp01 - 0439C0_Skyrim.esm.yaml'),
                    'Shock': ('ShockDamageFFAimedArea - 05DBAE_Skyrim.esm.yaml',
                              'ChainLightningExplosion - 05DBAD_Skyrim.esm.yaml')}
DRAGON_AREA = {'Fire': 12, 'Shock': 13}       # feet: vanilla Fireball's and Chain Lightning's NPC spell's
DRAGON_FREEZE_SECONDS = 4


def write_dragons_breath(d, write, sharp, arc):
    """Dragon's Breath's three spells (see DRAGON_SPELL_SRC)."""
    def sub1(y, pat, new, what):
        y, n = re.subn(pat, new, y, count=1, flags=re.M)
        assert n == 1, what
        return y

    def base(folder, name):
        return open(os.path.join(REF, 'base', 'Skyrim', folder, name), encoding='utf-8').read().replace('\r\n', '\n')

    name = "Name:\n  TargetLanguage: English\n  Value: Invoker\n"

    def spell(fk, e, target, effects):
        return (f"FormKey: {fk}\nEditorID: ZP_Prophecy_DragonsBreath_Spell_{e}\n{name}EquipmentType: 013F44:Skyrim.esm\n"
                "Description:\n  TargetLanguage: English\n  Value: ''\nFlags:\n- ManualCostCalc\n- NoAbsorbOrReflect\n"
                f"CastType: FireAndForget\nTargetType: {target}\nEffects:\n{effects}")

    for e, (me_src, expl_src) in DRAGON_SPELL_SRC.items():
        me, expl = d[f'{e}me'], d[f'{e}expl']
        y = base('Explosions', expl_src)
        y = sub1(y, r'^FormKey: .*$', f'FormKey: {expl}', 'expl fk')
        y = sub1(y, r'^EditorID: .*$', f'EditorID: ZP_Prophecy_DragonsBreath_Blast_{e}', 'expl edid')
        y = re.sub(r'^Name:\n(?:  .*\n)*', '', y, flags=re.M)
        y = re.sub(r'^(?:ImageSpaceModifier|ISRadius|Version2): .*\n', '', y, flags=re.M)
        write('Explosions', y)
        y = base('MagicEffects', me_src)
        y = sub1(y, r'^FormKey: .*$', f'FormKey: {me}', 'me fk')
        y = sub1(y, r'^EditorID: .*$', f'EditorID: ZP_Prophecy_DragonsBreath_Effect_{e}', 'me edid')
        y = sub1(y, r'^Name:\n(?:  .*\n)*', name, 'me name')
        y = sub1(y, r'^Explosion: .*$', f'Explosion: {expl}', 'me explosion')
        y = re.sub(r'^(?:ImageSpaceModifier|Version2): .*\n', '', y, flags=re.M)
        y = re.sub(r'^Description:\n(?:  .*\n)*', '', y, flags=re.M)
        y = y.rstrip('\n') + "\nDescription:\n  TargetLanguage: English\n  Value: Invoker deals <mag> damage.\n"
        assert 'ImageSpaceModifier' not in y
        write('MagicEffects', y)
        write('Spells', spell(d[f'{e}spell'], e, 'Aimed', f"- BaseEffect: {me}\n  Data:\n"
                              f"    Magnitude: {DRAGONS_BREATH['Damage']}\n    Area: {DRAGON_AREA[e]}\n"))
    y = base('MagicEffects', 'FrostDamageFFAimed - 01CEA2_Skyrim.esm.yaml')
    y = sub1(y, r'^FormKey: .*$', f"FormKey: {d['Frostme']}", 'frost fk')
    y = sub1(y, r'^EditorID: .*$', 'EditorID: ZP_Prophecy_DragonsBreath_Effect_Frost', 'frost edid')
    y = sub1(y, r'^Name:\n(?:  .*\n)*', name, 'frost name')
    y = re.sub(r'^(?:ImageSpaceModifier|Version2): .*\n', '', y, flags=re.M)
    y = re.sub(r'^Description:\n(?:  .*\n)*', '', y, flags=re.M)
    y = y.rstrip('\n') + "\nDescription:\n  TargetLanguage: English\n  Value: Invoker deals <mag> frost damage.\n"
    write('MagicEffects', y)
    # Ice Shot's freeze effect, delivered by the spike: the record as write_arcane wrote it, made Aimed
    hits = glob.glob(os.path.join(ESP, 'MagicEffects', f"* - {arc['freezeme'].split(':')[0]}_*.yaml"))
    assert len(hits) == 1, hits
    y = open(hits[0], encoding='utf-8').read().replace('\r\n', '\n')
    y = sub1(y, r'^FormKey: .*$', f"FormKey: {d['Frostproj']}", 'freeze fk')
    y = sub1(y, r'^EditorID: .*$', 'EditorID: ZP_Prophecy_DragonsBreath_FreezeEffect', 'freeze edid')
    y = sub1(y, r'^TargetType: TargetActor$', 'TargetType: Aimed', 'freeze delivery')
    write('MagicEffects', y)
    write('Spells', spell(d['Frostspell'], 'Frost', 'Aimed',
                          f"- BaseEffect: {d['Frostme']}\n  Data:\n    Magnitude: {DRAGONS_BREATH['Damage']}\n"
                          f"- BaseEffect: {d['Frostproj']}\n  Data:\n    Duration: {DRAGON_FREEZE_SECONDS}\n"))


def write_rage(r, nodeperk, write, dragon, flowchain):
    write('Globals', f"MutagenObjectType: GlobalShort\nFormKey: {r['global']}\nEditorID: ZP_Rage\nData: 0\n")
    write('Spells', f"FormKey: {r['vehspell']}\nEditorID: ZP_Prophecy_Vehemence_Spell\nName:\n  TargetLanguage: English\n"
                    "  Value: Vehemence\nEquipmentType: 013F44:Skyrim.esm\nDescription:\n  TargetLanguage: English\n  Value: ''\n"
                    "Flags:\n- ManualCostCalc\n- IgnoreResistance\n- NoAbsorbOrReflect\nCastType: FireAndForget\n"
                    f"Effects:\n- BaseEffect: {r['vehme']}\n  Data:\n    Duration: {RAGE['VehemenceSeconds']}\n")
    write('MagicEffects', f"""FormKey: {r['vehme']}
EditorID: ZP_Prophecy_Vehemence_Effect
Name:
  TargetLanguage: English
  Value: Vehemence
Flags:
- NoMagnitude
- NoArea
- Recover
Archetype:
  MutagenObjectType: MagicEffectArchetype
  Type: Script
CastType: FireAndForget
DualCastScale: 1
Sounds: []
Description:
  TargetLanguage: English
  Value: Your power attacks cost no Stamina and their Rage actions spend no Rage for <dur> seconds.
""")
    write('Spells', f"FormKey: {r['rageab']}\nEditorID: ZP_Prophecy_Rage_Ability\nName:\n  TargetLanguage: English\n"
                    "  Value: Rage\nEquipmentType: 013F44:Skyrim.esm\nDescription:\n  TargetLanguage: English\n  Value: ''\n"
                    f"Type: Ability\nCastType: ConstantEffect\nEffects:\n- BaseEffect: {r['rageabme']}\n  Data: {{}}\n")
    write('MagicEffects', f"""FormKey: {r['rageabme']}
EditorID: ZP_Prophecy_Rage_Effect
Name:
  TargetLanguage: English
  Value: Rage
Flags:
- Recover
- NoDuration
- NoArea
Archetype:
  MutagenObjectType: MagicEffectArchetype
  Type: Script
CastType: ConstantEffect
DualCastScale: 1
Sounds: []
Description:
  TargetLanguage: English
  Value: You have <mag> stacks of Rage.
""")
    hexid = lambda fk: fk.split(':')[0]
    cfg = {
        '$comment': 'Generated by src/Prophecy/tools/01-build-trees.py (write_rage) - never hand-edit. FormIDs are local '
                    'to their plugin (hex). See arch-docs/patches/Prophecy.md, Rage.',
        'plugin': MOD, 'actionPlugin': DW,
        'rageGlobal': hexid(r['global']), 'vehemenceSpell': hexid(r['vehspell']), 'vehemenceEffect': hexid(r['vehme']),
        'rageEffect': hexid(r['rageabme']),
        'perks': {'root': hexid(nodeperk['rge1']), 'untempered': hexid(nodeperk['rge8']), 'vehemence': hexid(nodeperk['rge9'])},
        'max': RAGE['Max'], 'maxUntempered': RAGE['MaxUntempered'],
        'fadeAfter': RAGE['FadeAfter'], 'fadeEvery': RAGE['FadeEvery'], 'combatGrace': RAGE['CombatGrace'],
        'sprintGrace': RAGE['SprintGrace'], 'hitDedupe': RAGE['HitDedupe'], 'swingWindow': RAGE['SwingWindow'],
        'powerAttackTypes': POWER_ATTACK_TYPES, 'meter': RAGE['Meter'],
        # Dragon's Breath (Martial Arts, 2026-10-28): counted here with the other hit events, Rage or not
        'dragonsBreath': {'perk': hexid(nodeperk['ma6']), 'every': DRAGONS_BREATH['Every'],
                          'spells': [hexid(dragon[f'{e}spell']) for e in DRAGON_ELEMENTS]},   # no fist bursts
        # Ricochet Rounds (Firearms, 2026-10-29): a pistol hit - the Flintlock Overhaul's shot enchantments all carry
        # PMPistolShot, tagged ZP_FlintlockShot - re-casts the same shot from the target at the next enemy
        'ricochet': {'perk': hexid(nodeperk['gun6']), 'chance': RICOCHET['Chance'], 'range': RICOCHET['Range'],
                     'cooldown': RICOCHET['Cooldown'], 'keywordPlugin': 'Zenderal - Flintlock Overhaul.esp',
                     'keyword': '00080C'},
        # Twin Effigies (Sorcery, 2026-10-29): Shatterveil's effigies cast the spells the player held when casting it
        'effigies': {'plugin': SHVL, 'spells': list(EFFIGY_CAST['Spells']), 'faction': EFFIGY_CAST['Faction'],
                     'base': EFFIGY_CAST['Base'], 'castEvery': EFFIGY_CAST['CastEvery'], 'range': EFFIGY_CAST['Range'],
                     'spawnWindow': EFFIGY_CAST['SpawnWindow'], 'castSpell': hexid(flowchain)},
        'actions': [{'name': nodes_name, 'perk': hexid(nodeperk[nid]), 'trigger': trig,
                     'cost': RAGE['Cost'][nodes_name], 'spells': spells}
                    for nid, (trig, spells) in RAGE_ACTIONS.items()
                    for nodes_name in [next(n[1] for _, _, ns in TREES for n in ns if n[0] == nid)]],
    }
    os.makedirs(os.path.dirname(RAGE_JSON), exist_ok=True)
    with open(RAGE_JSON, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(cfg, fh, indent=1)


def perk_powers(esp, perk_fks):
    """(perk index, spell FormKey) for every perk whose PerkAbilityEffect is a Power/LesserPower. AddPerk from a
    script does not hand out power-type abilities (Explosive Tripwire, 2026-10-21), so the menu AddSpells them."""
    idx, spells = [], []
    for k, fk in enumerate(perk_fks):
        t = open(glob.glob(os.path.join(esp, 'Perks', f'* - {fk.split(":")[0]}_*'))[0], encoding='utf-8').read()
        for ab in re.findall(r'MutagenObjectType: PerkAbilityEffect\r?\n(?:  .*\r?\n)*?  Ability: ([^\r\n]+)', t):
            sp = glob.glob(os.path.join(esp, 'Spells', f'* - {ab.split(":")[0]}_*')) if ab.endswith(MOD) else []
            if sp and re.search(r'^Type: (Power|LesserPower|Voice)\s*$', open(sp[0], encoding='utf-8').read(), re.M):
                idx.append(k); spells.append(ab)
    assert len(idx) == len(set(idx)), 'a perk grants more than one power'
    return idx, spells


# Items handed out ONCE per save when a perk is owned (2026-10-22, curator: the turret power was useless until a
# turret was crafted from rare scrap). (perk node, item EditorID); the forge recipe stays for replacements.
GIFTS = [('gad4', 'ZP_ORD_Smh_DwarvenAutocannon_Misc')]


def gift_props(esp, perk_index):
    """(GiftPerk ints, GiftItem FormKeys) for the menu quest; items found by EditorID so v2 can call it too."""
    idx, items = [], []
    for nid, edid in GIFTS:
        hit = [p for p in glob.glob(os.path.join(esp, 'MiscItems', '*.yaml')) if os.path.basename(p).startswith(edid + ' - ')]
        assert len(hit) == 1, f'gift item {edid} not found'
        idx.append(perk_index[nid])
        items.append(re.search(r'^FormKey: (.+?)\s*$', open(hit[0], encoding='utf-8').read(), re.M).group(1))
    return idx, items


def write_menu(nodes, nodeperk, write, grants):
    """The perk menu is Enderal's UIExtensions list menu, run by ZP_ProphecyMenu on quest ZP_ProphecyInit 0x807.
    Custom Skills Framework was dropped 2026-10-21: the Skyrim perk screen it draws on does not work in Enderal 2.1
    (four in-game tests, see arch-docs/patches/Prophecy.md). Writes one description box per perk, the quest's
    script properties, and points the power's effect at the quest.
    2026-10-21: the menu is B612's traits card menu (the one Biggie Traits uses) - one card per perk with a
    thumbnail at Interface/ProphecyPics/<perk EditorID>.dds (art: see arch-docs/patches/Prophecy.md)."""
    order = [n[0] for _, _, ns in TREES for n in ns]
    descs, images = [], []
    for nid in order:
        p = glob.glob(os.path.join(ESP, 'Perks', f'* - {nodeperk[nid].split(":")[0]}_*'))[0]
        t = open(p, encoding='utf-8').read().replace('\r\n', '\n')
        val = lambda key: re.search(rf'^{key}:\n  TargetLanguage: English\n  Value: (.*)$', t, re.M).group(1)
        def unq(v):
            if v.startswith("'"): return v[1:-1].replace("''", "'")
            if v.startswith('"'): return json.loads(v)     # Spriggit's double-quoted scalars: Arcane Echo's showed \" (2026-10-24)
            return v
        # the talent's name heads its description (curator 2026-10-24). B612's card menu shows the description as plain
        # text (b612_traitsmenut.swf updateDetails sets ItemText_tf.text, not htmlText), so a line of its own, no markup.
        # The talent's name heads its description (curator 2026-10-24), added by ZP_ProphecyMenu at runtime with a
        # Papyrus "\n": Mutagen stores every line break here as CRLF (even a lone CR), and B612's plain-text field
        # breaks on CR and LF alike, so a stored "\n\n" showed a huge gap. The array holds the bare description.
        descs.append(unq(val('Description')))
        images.append(f'ProphecyPics/{ed(t)}.dds')
    strs = lambda xs: ''.join("      - '" + x.replace("'", "''") + "'\n" for x in xs)
    # double-quoted YAML, so the header's line break survives (a single-quoted scalar folds a newline into a space)
    dqstrs = lambda xs: ''.join('      - "' + x.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r') + '"\n' for x in xs)
    pos = {nid: k for k, nid in enumerate(order)}
    # capstones need level 30 (curator 2026-10-25): the talent after each tree's W2 stat talent
    caps = {n for n in order if nodes[n][5] and nodes[n][5][0] in {w2[0] for _, _, w2 in STAT_NODES.values()} | HAND_W2}
    assert len(caps) == len(TREES), ('capstones', sorted(caps))
    levelreq = [CAPSTONE_LEVEL if n in caps else 0 for n in order]
    pa = [pos[nodes[n][5][0]] if nodes[n][5] else -1 for n in order]
    pb = [pos[nodes[n][5][1]] if len(nodes[n][5]) > 1 else -1 for n in order]
    objs = lambda fks: ''.join(f"      - Name: ''\n        Object: {fk}\n" for fk in fks)
    ints = lambda xs: ''.join(f'      - {x}\n' for x in xs)
    prop = lambda name, fk: (f'    - MutagenObjectType: ScriptObjectProperty\n      Name: {name}\n      Object: {fk}\n')
    # points already handed out (AwardPoints pays level/5 minus this). Written here: it was once lost from the YAML,
    # the property resolved to None and every open paid the full level/5 again.
    for p in glob.glob(os.path.join(ESP, 'Globals', '* - 000809_*')): os.remove(p)
    write('Globals', f'MutagenObjectType: GlobalShort\nFormKey: 000809:{MOD}\nEditorID: ZP_ProphecyPointsEarned\nData: 0\n')
    pw_i, pw_s = perk_powers(ESP, [nodeperk[n] for n in order])
    for nid, form in grants.items():             # extra forms granted like the powers (a Shout needs this; none today)
        pw_i.append(pos[nid]); pw_s.append(form)
    print('powers granted by the menu:', pw_s)
    gift_i, gift_s = gift_props(ESP, pos)
    # tree choice box + where each tree starts in the tree-major arrays (last entry = total)
    starts, k = [], 0
    for _, _, ns in TREES:
        starts.append(k); k += len(ns)
    starts.append(k)
    btn = lambda s: f'- Text:\n    TargetLanguage: English\n    Value: {s}\n'
    for p in glob.glob(os.path.join(ESP, 'Messages', '* - 00080D_*')): os.remove(p)
    write('Messages', f'FormKey: 00080D:{MOD}\nEditorID: ZP_ProphecyMenu\nDescription:\n  TargetLanguage: English\n'
                      '  Value: Which prophecy will you read?\nINAM: 0x00000000\nFlags:\n- MessageBox\nMenuButtons:\n' +
                      ''.join(btn(t) for t, _, _ in TREES) + btn('Cancel'))
    # The menu arrays go on the quest (what a new save starts with) AND on the power's effect, whose instance is
    # created from the plugin on every cast and passed to ZP_ProphecyMenu.Refresh: a running quest keeps its old
    # property values in the save, so without this new perks never reached existing saves (2026-10-22).
    arrays = ('    - MutagenObjectType: ScriptObjectListProperty\n      Name: Perks\n      Objects:\n' + objs(nodeperk[n] for n in order) +
              '    - MutagenObjectType: ScriptStringListProperty\n      Name: Descriptions\n      Data:\n' + dqstrs(descs) +
              '    - MutagenObjectType: ScriptStringListProperty\n      Name: Images\n      Data:\n' + strs(images) +
              '    - MutagenObjectType: ScriptIntListProperty\n      Name: ParentA\n      Data:\n' + ints(pa) +
              '    - MutagenObjectType: ScriptIntListProperty\n      Name: ParentB\n      Data:\n' + ints(pb) +
              '    - MutagenObjectType: ScriptIntListProperty\n      Name: PowerPerk\n      Data:\n' + ints(pw_i) +
              '    - MutagenObjectType: ScriptObjectListProperty\n      Name: PowerSpell\n      Objects:\n' + objs(pw_s) +
              '    - MutagenObjectType: ScriptIntListProperty\n      Name: TreeStart\n      Data:\n' + ints(starts) +
              '    - MutagenObjectType: ScriptIntListProperty\n      Name: GiftPerk\n      Data:\n' + ints(gift_i) +
              '    - MutagenObjectType: ScriptObjectListProperty\n      Name: GiftItem\n      Objects:\n' + objs(gift_s) +
              '    - MutagenObjectType: ScriptIntListProperty\n      Name: LevelReq\n      Data:\n' + ints(levelreq))
    write('Quests',
          f'FormKey: 000807:{MOD}\nEditorID: ZP_ProphecyInit\nVirtualMachineAdapter:\n  Scripts:\n'
          '  - Name: ZP_ProphecyInit\n    Properties:\n' + prop('ZP_ProphecyPower', f'000805:{MOD}') +
          '  - Name: ZP_ProphecyMenu\n    Properties:\n' +
          prop('ZP_ProphecyMenuMsg', f'00080D:{MOD}') + prop('ZP_ProphecyPoints', f'000802:{MOD}') +
          prop('ZP_ProphecyPointsEarned', f'000809:{MOD}') + arrays +
          "  FileName: ''\nFlags:\n- StartGameEnabled\n- RunOnce\nNextAliasID: 0\n")
    p = glob.glob(os.path.join(ESP, 'MagicEffects', '* - 000806_*'))[0]
    t = open(p, encoding='utf-8').read().replace('\r\n', '\n')
    t2 = re.sub(r'(  - Name: ZP_ProphecyPowerEffect\n    Properties:\n)(?:    - .*\n(?:      .*\n)*)+',
                lambda m: m.group(1) + prop('MenuQuest', f'000807:{MOD}') + arrays, t, count=1)
    assert t2 != t or 'Name: MenuQuest' in t, 'power effect VMAD not rewritten'
    open(p, 'w', encoding='utf-8', newline='\r\n').write(t2)
    csf = os.path.join(PATCH, 'csf')
    if os.path.isdir(csf): shutil.rmtree(csf)


if __name__ == '__main__':
    main()
