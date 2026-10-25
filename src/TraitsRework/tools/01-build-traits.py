"""Generate the TraitsRework plugin's records: one ability SPEL + perk-carrier MGEF + PERK per trait,
shared value-modifier MGEFs for stat changes, and the Traits_AbilityList override.

Archetype copied from Zen Traits (ZenTraits_LightbornAb 00081C -> MGEF 00081A with PerkToApply ->
PERK 00081B) and Biggie's stat effects (Traits_MarathonRunnerPos1 00005C, Traits_BulwarkNeg1 00025:
positive magnitude, Detrimental flag for penalties). Entry-point tab counts follow the base/EGO records.

Run from the repo root:  python src/TraitsRework/tools/01-build-traits.py
Rewrites Spells/, MagicEffects/, Perks/ and FormLists/ under TraitsReworkESP/ -- never hand-edit them.
"""
import os
import shutil
import sys

PLUGIN = "Zenderal - Traits.esp"
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "TraitsReworkESP")
GENERATED_DIRS = ["Spells", "MagicEffects", "Perks", "FormLists", "LeveledItems"]

# --- Enderal forms (see arch-docs/patches/TraitsRework.md for where each was verified) ---
GAME_HOUR = "000038:Skyrim.esm"
ARK = "0A1A12:Skyrim.esm"              # CapitalCityLocation, LocTypeCity, 54 child locations
RIVERVILLE = "032706:Skyrim.esm"       # FlusshaimLocation, no keywords, 4 child locations
KW_FIRE, KW_FROST, KW_SHOCK = "01CEAD:Skyrim.esm", "01CEAE:Skyrim.esm", "01CEAF:Skyrim.esm"
KW_SUMMON_FAMILIAR = "1091CF:Skyrim.esm"
KW_SUMMON_UNDEAD = "02482B:Skyrim.esm"
KW_SUMMON_FIRE = "024823:Skyrim.esm"
KW_UNDEAD = "013796:Skyrim.esm"        # ActorTypeUndead
KW_ANIMAL = "013798:Skyrim.esm"        # ActorTypeAnimal
KW_BOW = "01E715:Skyrim.esm"           # WeapTypeBow: bows, crossbows and the OrdoLegionis muskets
KW_LEHRBUCH = "031ACD:Skyrim.esm"      # Lehrbuch: every handbook ALCH
PLAYER_REF = "000014:Skyrim.esm"
# Flintlock Overhaul's pistols are STAVES firing a spell; every pistol shot enchantment carries this keyword, and the
# overhaul's own scaling perk (ZP_FlintlockArcheryScaling 00080D) multiplies ModSpellMagnitude on it the same way.
KW_FLINTLOCK_SHOT = "00080C:Zenderal - Flintlock Overhaul.esp"
FLINTLOCK_BULLET = "000800:Zenderal - Flintlock Overhaul.esp"   # ZP_FlintlockBullet, the pistols' ammo (MISC)
ABILITY_LIST = "000002:Biggie Traits.esp"
EQUIP_TYPE = "013F44:Skyrim.esm"       # as on every Zen Traits ability
FALMER_RACE = "0131F4:Skyrim.esm"      # Arps (Zenderal - Goblins gave goblins their own races)
GOBLIN_RACE = "000800:Zenderal - Goblins.esp"         # ZEN_GoblinRace
MIHAIL_GOBLIN_RACE = "000830:Zenderal - Goblins.esp"  # ZEN_Mihail_mihailgoblinrace (75% of every pack)
GOBLIN_SLAYER_RACES = [GOBLIN_RACE, MIHAIL_GOBLIN_RACE, FALMER_RACE]
LVLI_GOLD_SMALL = "0028E4:Skyrim.esm"  # 01E_Gold: 60% nothing, else 3-5 gold
# Enderal's own tiered loot lists, referenced (never overridden)
LVLI_GOLD_LARGE = "0030A8:Skyrim.esm"  # 01E_GoldGross: one roll = 4-9 gold
LVLI_GEMS_1 = "085669:Skyrim.esm"      # 02E_Edelsteine
LVLI_GEMS_2 = "085676:Skyrim.esm"      # 03E_Edelsteine
LVLI_JEWELRY_1 = "04C981:Skyrim.esm"   # 01E_Schmuckstck
LVLI_JEWELRY_2 = "0E1222:Skyrim.esm"   # 02E_Schmuckstck

BLOCK_START = 0x800   # trait n uses BLOCK_START + 4n .. +2 (SPEL, MGEF, PERK); +3 spare (a Pool trait's cut ability)
ZEN_POOL_START = 0x86C  # cut abilities for Zen Traits' own traits (0x86C-0x86F), counting down from 0x86F
STAT_START = 0x870    # shared stat MGEFs
LOOT_START = 0x880    # leveled lists (0x880-0x88F)


def num(v):
    return str(int(v)) if float(v).is_integer() else repr(float(v))


def fk(n):
    return f"{n:06X}:{PLUGIN}"


# ---------- conditions ----------
class C:
    def __init__(self, fn, fields=None, op="EqualTo", value=0, or_=False):
        self.fn, self.fields, self.op, self.value, self.or_ = fn, fields or {}, op, value, or_

    def lines(self, indent):
        p = " " * indent
        out = [f"{p}- MutagenObjectType: ConditionFloat"]
        if self.op != "EqualTo":
            out.append(f"{p}  CompareOperator: {self.op}")
        if self.or_:
            out += [f"{p}  Flags:", f"{p}  - OR"]
        out += [f"{p}  Data:", f"{p}    MutagenObjectType: {self.fn}ConditionData"]
        for k, v in self.fields.items():
            out.append(f"{p}    {k}: {v}")
        if self.value:
            out.append(f"{p}  ComparisonValue: {num(self.value)}")
        return out


def is_spell():
    return C("GetIsObjectType", {"FormType": "Spell"}, value=1)


def school(av, or_=False):
    return C("EPMagic_SpellHasSkill", {"ActorValue": av}, value=1, or_=or_)


def spell_kw(kw, value=1, or_=False):
    return C("EPMagic_SpellHasKeyword", {"Keyword": kw}, value=value, or_=or_)


def has_kw(kw, or_=False):
    return C("HasKeyword", {"Keyword": kw}, value=1, or_=or_)


def in_loc(loc, value=1, or_=False):
    return C("GetInCurrentLoc", {"Location": loc}, value=value, or_=or_)


def health_pct(op, value):
    return C("GetActorValuePercent", {"ActorValue": "Health"}, op=op, value=value)


def goblin(match=True):
    """Any Goblin Slayer race (OR chain), or none of them (AND chain)."""
    if match:
        races = [C("GetIsRace", {"Race": r}, value=1, or_=True) for r in GOBLIN_SLAYER_RACES]
        races[-1].or_ = False
        return races
    return [C("GetIsRace", {"Race": r}) for r in GOBLIN_SLAYER_RACES]


def night():
    return [C("GetGlobalValue", {"Global": GAME_HOUR}, op="GreaterThanOrEqualTo", value=20, or_=True),
            C("GetGlobalValue", {"Global": GAME_HOUR}, op="LessThan", value=5)]


def day():
    return [C("GetGlobalValue", {"Global": GAME_HOUR}, op="GreaterThanOrEqualTo", value=5),
            C("GetGlobalValue", {"Global": GAME_HOUR}, op="LessThan", value=20)]


TAB_COUNT = {
    "ModSpellMagnitude": 3, "ModSpellCost": 2, "ModSpellDuration": 3, "ModIncomingSpellMagnitude": 2,
    "ModAttackDamage": 3, "ModIncomingDamage": 3, "ModPowerAttackDamage": 3, "ModPowerAttackStamina": 2,
    "ModPercentBlocked": 1, "ModBuyPrices": 2, "ModSellPrices": 2, "ModPickpocketChance": 3,
    "ModLockpickSweetSpot": 2, "ModDetectionSneakSkill": 2, "ModAlchemyEffectiveness": 1,
}


class EP:
    """One perk entry point. tabs = {tab_index: [C, ...]}"""

    def __init__(self, entry, value, tabs=None, mod="Multiply"):
        assert entry in TAB_COUNT, entry
        self.entry, self.value, self.tabs, self.mod = entry, value, tabs or {}, mod
        assert all(t < TAB_COUNT[entry] for t in self.tabs), (entry, self.tabs)

    def lines(self):
        out = ["- MutagenObjectType: PerkEntryPointModifyValue"]
        if self.tabs:
            out.append("  Conditions:")
            for t in sorted(self.tabs):
                if t == 0:
                    out.append("  - Conditions:")
                else:
                    out += [f"  - RunOnTabIndex: {t}", "    Conditions:"]
                for c in self.tabs[t]:
                    out += c.lines(4)
        out += [f"  EntryPoint: {self.entry}", f"  PerkConditionTabCount: {TAB_COUNT[self.entry]}",
                f"  Modification: {self.mod}", f"  Value: {num(self.value)}"]
        return out


class LootOnDeath:
    """AddLeveledListOnDeath: the leveled list goes into a victim matching tab 1 (the dead actor).
    Shape copied from FS's _00E_SE_ShadowDancerAddToken 01596A."""

    def __init__(self, lvli, victim_conds):
        self.lvli, self.victim_conds = lvli, victim_conds

    def lines(self):
        out = ["- MutagenObjectType: PerkEntryPointAddLeveledItem", "  Conditions:",
               "  - RunOnTabIndex: 1", "    Conditions:"]
        for c in self.victim_conds:
            out += c.lines(4)
        return out + ["  EntryPoint: AddLeveledListOnDeath", "  PerkConditionTabCount: 2", f"  Item: {self.lvli}"]


# ---------- leveled lists ----------
LOOT_GOBLIN = fk(LOOT_START)          # always: three large-gold + one small-gold roll + one rare roll
LOOT_GOBLIN_RARE = fk(LOOT_START + 1)  # 76% nothing, else a gem or jewelry roll
LOOT_GUNSLINGER = fk(LOOT_START + 2)   # 50% nothing, else 3 or 5 Flintlock Bullets
LEVELED_LISTS = [
    # FormKey, EditorID, ChanceNone (0-1), flags, [(level, reference, count)]
    # 2026-10-22: +60% on both (curator): rare 15% -> 24%; gold ~13 -> ~21 per kill
    (LOOT_GOBLIN_RARE, "ZEN_TR_GoblinSlayerLootRare", 0.76,
     ["CalculateFromAllLevelsLessThanOrEqualPlayer"],
     [(1, LVLI_GEMS_1, 1), (1, LVLI_JEWELRY_1, 1), (10, LVLI_JEWELRY_2, 1), (20, LVLI_GEMS_2, 1)]),
    (LOOT_GOBLIN, "ZEN_TR_GoblinSlayerLoot", 0,
     ["UseAll"],
     [(1, LVLI_GOLD_LARGE, 1), (1, LVLI_GOLD_LARGE, 1), (1, LVLI_GOLD_LARGE, 1), (1, LVLI_GOLD_SMALL, 1),
      (1, LOOT_GOBLIN_RARE, 1)]),
    # Gunslinger (curator 2026-10-23): 50% chance of pistol ammo on any slain enemy
    (LOOT_GUNSLINGER, "ZEN_TR_GunslingerLoot", 0.5,
     ["CalculateFromAllLevelsLessThanOrEqualPlayer"],
     [(1, FLINTLOCK_BULLET, 3), (1, FLINTLOCK_BULLET, 5)]),
]


def lvli_lines(formkey, edid, chance_none, flags, entries):
    out = [f"FormKey: {formkey}", f"EditorID: {edid}"]
    if chance_none:
        out.append(f"ChanceNone: {num(chance_none)}")
    out += ["Flags:"] + [f"- {f}" for f in flags] + ["Entries:"]
    for level, ref, count in entries:
        out += ["- Data:", f"    Level: {level}", f"    Reference: {ref}", f"    Count: {count}"]
    return out


# ---------- shared stat MGEFs (value modifiers on the ability) ----------
STATS = [  # key, EditorID suffix, ActorValue, detrimental
    ("health_neg", "HealthNeg", "Health", True),
    ("stamina_neg", "StaminaNeg", "Stamina", True),
    ("frost_res", "ResistFrost", "ResistFrost", False),
    ("fire_weak", "ResistFireNeg", "ResistFire", True),
    ("healrate_neg", "HealRateNeg", "HealRateMult", True),
    ("magickarate", "MagickaRate", "MagickaRateMult", False),
    ("staminarate_neg", "StaminaRateNeg", "StaminaRateMult", True),
    ("speed", "SpeedMult", "SpeedMult", False),
    ("carry_neg", "CarryWeightNeg", "CarryWeight", True),
]
STAT_FK = {key: fk(STAT_START + i) for i, (key, *_rest) in enumerate(STATS)}


class Stat:
    def __init__(self, key, magnitude, conds=None):
        assert key in STAT_FK, key
        assert magnitude > 0, "penalties use a Detrimental MGEF with a positive magnitude"
        self.key, self.magnitude, self.conds = key, magnitude, conds or []


# Zen Traits traits whose cut is ours (formkey, stem, menu name, stat key). Their scripts are Zen Traits' own, forked
# in Scripts/source: a script-only replacement keeps its properties, so it finds the ability by FormID.
ZEN_POOLS = [(fk(0x86F), "AeternaVeins", "Aeterna Veins", "health_neg")]


class Pool:
    """A percentage cut to a maximum pool that follows every change to it (curator 2026-10-25; these were flat cuts,
    because a plain ability can't scale a max). The trait's perk-carrier MGEF also runs ZEN_TR_PoolPenaltyEffect,
    which keeps the trait's own cut ability (its spare slot, +3: one Detrimental stat effect, magnitude set at runtime)
    at `fraction` of the pool's uncut maximum. Zen Traits' Aeterna Veins is the archetype (a cut ability re-added on
    level-up); this re-checks every 5 s, so gear and buffs count too."""
    def __init__(self, key, av, fraction):
        assert key in STAT_FK and 0 < fraction < 1, (key, fraction)
        self.key, self.av, self.fraction = key, av, fraction


# ---------- the traits ----------
# (EditorID stem, menu name, description, [EP...], [Stat...])
TRAITS = [
    ("Overcharged", "Overcharged",
     "Elementalism spells deal 20% more damage.\n\nYour maximum Health is 15% lower.",
     [EP("ModSpellMagnitude", 1.2, {1: [is_spell(), school("Destruction")]})],
     [Pool("health_neg", "Health", 0.15)]),

    ("Stormcaller", "Stormcaller",
     "Shock spells deal 25% more damage and cost 10% less.\n\nFire and frost spells deal 15% less damage.",
     [EP("ModSpellMagnitude", 1.25, {1: [is_spell(), school("Destruction"), spell_kw(KW_SHOCK)]}),
      EP("ModSpellCost", 0.9, {1: [is_spell(), school("Destruction"), spell_kw(KW_SHOCK)]}),
      # school check keeps the 26 holy-fire Light Magic effects out of the penalty
      EP("ModSpellMagnitude", 0.85, {1: [is_spell(), school("Destruction"),
                                         spell_kw(KW_FIRE, or_=True), spell_kw(KW_FROST)]})],
     []),

    ("EntropicPact", "Entropic Pact",
     "Entropy spells cost 20% less, and Entropy spells other than summons last 25% longer.\n\n"
     "Light Magic costs 25% more.",
     [EP("ModSpellCost", 0.8, {1: [is_spell(), school("Conjuration")]}),
      EP("ModSpellDuration", 1.25, {1: [is_spell(), school("Conjuration"),
                                        spell_kw(KW_SUMMON_FAMILIAR, 0), spell_kw(KW_SUMMON_UNDEAD, 0),
                                        spell_kw(KW_SUMMON_FIRE, 0)]}),
      EP("ModSpellCost", 1.25, {1: [is_spell(), school("Restoration")]})],
     []),

    ("Gravecaller", "Gravecaller",
     "Your summons and revived dead last 50% longer.\n\nThe dead are drawn to you: undead deal 15% more damage to you.",
     [EP("ModSpellDuration", 1.5, {1: [is_spell(), spell_kw(KW_SUMMON_FAMILIAR, or_=True),
                                       spell_kw(KW_SUMMON_UNDEAD, or_=True), spell_kw(KW_SUMMON_FIRE)]}),
      EP("ModIncomingDamage", 1.15, {1: [has_kw(KW_UNDEAD)]})],
     []),

    ("IronWill", "Iron Will",
     "Psionic spells cast on you are 50% weaker.\n\nYou never back down: blocking absorbs 15% less damage.",
     [EP("ModIncomingSpellMagnitude", 0.5, {1: [school("Illusion")]}),
      EP("ModPercentBlocked", 0.85)],
     []),

    ("CorneredWolf", "Cornered Wolf",
     "Below 30% Health, your weapons deal 25% more damage and you take 10% less damage.\n\n"
     "Above 75% Health, your weapons deal 10% less damage.",
     [EP("ModAttackDamage", 1.25, {0: [health_pct("LessThan", 0.3)]}),
      EP("ModIncomingDamage", 0.9, {0: [health_pct("LessThan", 0.3)]}),
      EP("ModAttackDamage", 0.9, {0: [health_pct("GreaterThan", 0.75)]})],
     []),

    ("HeavyHand", "Heavy Hand",
     "Power attacks deal 30% more damage.\n\nNormal attacks deal 10% less damage, and power attacks cost 20% more Stamina.",
     [EP("ModPowerAttackDamage", 1.3, {0: [C("IsPowerAttacking", value=1)]}),
      EP("ModAttackDamage", 0.9, {0: [C("IsPowerAttacking")]}),
      EP("ModPowerAttackStamina", 1.2)],
     []),

    ("SteadyBreath", "Steady Breath",
     "Bow, crossbow and musket shots deal 20% more damage while you stand still.\n\n"
     "Shots fired on the move deal 15% less damage.",
     [EP("ModAttackDamage", 1.2, {0: [C("IsMoving")], 1: [has_kw(KW_BOW)]}),
      EP("ModAttackDamage", 0.85, {0: [C("IsMoving", value=1)], 1: [has_kw(KW_BOW)]})],
     []),

    ("Nightwalker", "Nightwalker",
     "From 20:00 to 05:00 you sneak better (+20) and regenerate Mana 25% faster.\n\n"
     "During the day your Stamina regenerates 10% slower.",
     [EP("ModDetectionSneakSkill", 20, {0: night()}, mod="Add")],
     [Stat("magickarate", 25, night()), Stat("staminarate_neg", 10, day())]),

    ("ColdHardened", "Cold-Hardened",
     "You resist frost by 30%.\n\nYou take 20% more fire damage.",
     [],
     [Stat("frost_res", 30), Stat("fire_weak", 20)]),

    ("Wildling", "Wildling",
     "You deal 15% more damage to animals and take 15% less from them.\n\n"
     "Townsfolk find you uncouth: prices are 15% worse.",
     [EP("ModAttackDamage", 1.15, {2: [has_kw(KW_ANIMAL)]}),
      EP("ModIncomingDamage", 0.85, {1: [has_kw(KW_ANIMAL)]}),
      EP("ModBuyPrices", 1.15),
      EP("ModSellPrices", 0.85)],
     []),

    ("Pathfinder", "Pathfinder",
     "Outdoors and out of combat you move 15% faster.\n\nYou can carry 50 less.",
     [],
     [Stat("speed", 15, [C("IsInCombat"), C("IsInInterior")]), Stat("carry_neg", 50)]),

    ("ArkBorn", "Ark-Born",
     "Prices are 15% better in Ark and Riverville.\n\nIn the wilderness your Health regenerates 25% slower.",
     [EP("ModBuyPrices", 0.85, {0: [in_loc(ARK, or_=True), in_loc(RIVERVILLE)]}),
      EP("ModSellPrices", 1.15, {0: [in_loc(ARK, or_=True), in_loc(RIVERVILLE)]})],
     [Stat("healrate_neg", 25, [in_loc(ARK, 0), in_loc(RIVERVILLE, 0), C("IsInInterior")])]),

    ("BackAlleyBorn", "Back-Alley Born",
     "Pickpocketing and lockpicking are easier, and in Ark and Riverville you sneak better (+15).\n\n"
     "Merchants don't trust you: buying costs 10% more everywhere.",
     [EP("ModPickpocketChance", 20, mod="Add"),
      EP("ModLockpickSweetSpot", 1.2),
      EP("ModDetectionSneakSkill", 15, {0: [in_loc(ARK, or_=True), in_loc(RIVERVILLE)]}, mod="Add"),
      EP("ModBuyPrices", 1.1)],
     []),

    ("InkStained", "Ink-Stained",
     "Handbooks cost 25% less.\n\nYour maximum Stamina is 15% lower.",
     [EP("ModBuyPrices", 0.75, {1: [has_kw(KW_LEHRBUCH)]})],
     [Pool("stamina_neg", "Stamina", 0.15)]),

    ("BrewersLungs", "Brewer's Lungs",
     "Potions you brew are 20% stronger.\n\nYears of fumes: your maximum Health is 10% lower.",
     [EP("ModAlchemyEffectiveness", 1.2)],
     [Pool("health_neg", "Health", 0.10)]),

    ("GoblinSlayer", "Goblin Slayer",
     "Your weapons deal 25% more damage to goblins and Arps, and they deal 15% less damage to you. "
     "Goblins and Arps you kill carry extra gold, and often a gem or piece of jewelry.\n\n"
     "Your weapons deal 10% less damage to everything else.",
     [EP("ModAttackDamage", 1.25, {2: goblin()}),
      EP("ModIncomingDamage", 0.85, {1: goblin()}),
      EP("ModAttackDamage", 0.9, {2: goblin(match=False)}),
      LootOnDeath(LOOT_GOBLIN, goblin())],
     []),

    # Gunslinger (curator 2026-10-23). Pistols are staves firing a spell, so their bonus is spell magnitude on the
    # Flintlock shot keyword; ModAttackDamage never touches them. Melee = any weapon attack without WeapTypeBow
    # (bows, crossbows and muskets all carry it), fists included.
    ("Gunslinger", "Gunslinger",
     "Flintlock pistols deal 35% more damage, and enemies you kill have a 50% chance to carry Flintlock Bullets.\n\n"
     "Your melee attacks deal 25% less damage.",
     [EP("ModSpellMagnitude", 1.35, {1: [spell_kw(KW_FLINTLOCK_SHOT)]}),
      EP("ModAttackDamage", 0.75, {1: [C("HasKeyword", {"Keyword": KW_BOW})]}),
      # any enemy: FS's own Shadow Dancer token perk (01596A) checks its victim the same way
      LootOnDeath(LOOT_GUNSLINGER, [C("IsHostileToActor", {"TargetNpc": PLAYER_REF}, value=1)])],
     []),
]


def yaml_block(s, indent):
    p = " " * indent
    if "\n" not in s and "'" not in s and ":" not in s:
        return [f"{p}Value: {s}"]
    out = [f"{p}Value: >-"]
    for para in s.split("\n\n"):
        out += [f"{p}  {para}", ""]
    return out[:-1]


def write(folder, edid, formkey, lines):
    d = os.path.join(ROOT, folder)
    os.makedirs(d, exist_ok=True)
    name = f"{edid} - {formkey.replace(':', '_')}.yaml"
    with open(os.path.join(d, name), "w", encoding="utf-8", newline="\r\n") as f:
        f.write("\n".join(lines) + "\n")


def stat_mgef(i, key, suffix, av, detrimental):
    edid = f"ZEN_TR_Stat{suffix}"
    flags = ["Recover"] + (["Detrimental"] if detrimental else []) + ["NoDuration", "NoArea", "HideInUI"]
    lines = [f"FormKey: {STAT_FK[key]}", f"EditorID: {edid}", "Name:", "  TargetLanguage: English",
             f"  Value: 'Trait: {suffix}'", "Flags:"] + [f"- {x}" for x in flags] + [
             "Archetype:", "  MutagenObjectType: MagicEffectArchetype", f"  ActorValue: {av}",
             "DualCastScale: 1", "CastingSoundLevel: Normal", "Sounds: []", "Description:",
             "  TargetLanguage: English", "  Value: ''"]
    write("MagicEffects", edid, STAT_FK[key], lines)


def main():
    for d in GENERATED_DIRS:
        shutil.rmtree(os.path.join(ROOT, d), ignore_errors=True)

    for i, (key, suffix, av, det) in enumerate(STATS):
        stat_mgef(i, key, suffix, av, det)

    ability_fks = []
    counts = {"SPEL": 0, "MGEF": len(STATS), "PERK": 0, "EP": 0}
    for n, (stem, name, desc, eps, stats) in enumerate(TRAITS):
        base = BLOCK_START + 4 * n
        assert base + 3 < ZEN_POOL_START, "trait block overflows into the Zen Traits cut abilities"
        spel, mgef, perk = fk(base), fk(base + 1), fk(base + 2)
        pools = [s for s in stats if isinstance(s, Pool)]
        stats = [s for s in stats if not isinstance(s, Pool)]
        assert len(pools) <= 1 and (not pools or eps), f"{stem}: one Pool, on a trait whose perk MGEF can carry it"
        vmad = []
        if pools:
            pool, penalty = pools[0], fk(base + 3)
            vmad = ["VirtualMachineAdapter:", "  Scripts:", "  - Name: ZEN_TR_PoolPenaltyEffect", "    Properties:",
                    "    - MutagenObjectType: ScriptObjectProperty", "      Name: Penalty", f"      Object: {penalty}",
                    "    - MutagenObjectType: ScriptStringProperty", "      Name: PoolName", f"      Data: {pool.av}",
                    "    - MutagenObjectType: ScriptFloatProperty", "      Name: Fraction",
                    f"      Data: {num(pool.fraction)}"]
            write("Spells", f"ZEN_TR_{stem}PenaltyAb", penalty, [
                f"FormKey: {penalty}", f"EditorID: ZEN_TR_{stem}PenaltyAb", "Name:", "  TargetLanguage: English",
                f"  Value: {name}", f"EquipmentType: {EQUIP_TYPE}", "Description:", "  TargetLanguage: English",
                "  Value: ''", "Type: Ability", "Effects:",
                f"- BaseEffect: {STAT_FK[pool.key]}", "  Data:", "    Magnitude: 1"])   # the script sets it
            counts["SPEL"] += 1
        effects = []
        if eps:
            plines = [f"FormKey: {perk}", f"EditorID: ZEN_TR_{stem}PERK", "Description:",
                      "  TargetLanguage: English", "  Value: ''", "NumRanks: 1", "Playable: True", "Effects:"]
            for ep in eps:
                plines += ep.lines()
            write("Perks", f"ZEN_TR_{stem}PERK", perk, plines)
            write("MagicEffects", f"ZEN_TR_{stem}MGEF", mgef, [
                f"FormKey: {mgef}", f"EditorID: ZEN_TR_{stem}MGEF"] + vmad + ["Name:", "  TargetLanguage: English",
                f"  Value: {name}",
                "Flags:", "- Recover", "- NoDuration", "- NoMagnitude", "- NoArea",
                "Archetype:", "  MutagenObjectType: MagicEffectArchetype", "  Type: Script",
                "DualCastScale: 1", f"PerkToApply: {perk}", "CastingSoundLevel: Normal", "Sounds: []",
                "Description:", "  TargetLanguage: English", "  Value: ''"])
            effects += [f"- BaseEffect: {mgef}", "  Data: {}"]
            counts["PERK"] += 1
            counts["MGEF"] += 1
            counts["EP"] += len(eps)
        for st in stats:
            effects += [f"- BaseEffect: {STAT_FK[st.key]}", "  Data:", f"    Magnitude: {num(st.magnitude)}"]
            if st.conds:
                effects.append("  Conditions:")
                for c in st.conds:
                    effects += c.lines(2)
        assert effects, stem
        slines = [f"FormKey: {spel}", f"EditorID: ZEN_TR_{stem}Ab", "Name:", "  TargetLanguage: English",
                  f"  Value: {name}", f"EquipmentType: {EQUIP_TYPE}", "Description:",
                  "  TargetLanguage: English"] + yaml_block(desc, 2) + ["Type: Ability", "Effects:"] + effects
        write("Spells", f"ZEN_TR_{stem}Ab", spel, slines)
        ability_fks.append(spel)
        counts["SPEL"] += 1

    # Zen Traits' Aeterna Veins (curator 2026-10-25): its cut is this ability, kept at 20% of the uncut max Health by
    # the forked ZenTraits_AeternaVeinsScript in Scripts/source (which looks it up by this FormID; see its header)
    for formkey, stem, name, key in ZEN_POOLS:
        write("Spells", f"ZEN_TR_{stem}PenaltyAb", formkey, [
            f"FormKey: {formkey}", f"EditorID: ZEN_TR_{stem}PenaltyAb", "Name:", "  TargetLanguage: English",
            f"  Value: {name}", f"EquipmentType: {EQUIP_TYPE}", "Description:", "  TargetLanguage: English",
            "  Value: ''", "Type: Ability", "Effects:",
            f"- BaseEffect: {STAT_FK[key]}", "  Data:", "    Magnitude: 1"])   # the script sets it
        counts["SPEL"] += 1

    for formkey, edid, chance_none, flags, entries in LEVELED_LISTS:
        assert LOOT_START <= int(formkey[:6], 16) <= 0x88F, formkey
        write("LeveledItems", edid, formkey, lvli_lines(formkey, edid, chance_none, flags, entries))

    # Option (a): replace Biggie's list with ours. Zen Traits' 9 are added back at runtime by its _FLM.ini.
    write("FormLists", "Traits_AbilityList", ABILITY_LIST,
          [f"FormKey: {ABILITY_LIST}", "EditorID: Traits_AbilityList", "Items:"] + [f"- {x}" for x in ability_fks])

    assert len(TRAITS) == 18 and counts["SPEL"] == 18 + 3 + len(ZEN_POOLS), counts   # 18th: Gunslinger (2026-10-23); + cut abilities
    print(f"traits={counts['SPEL']} perks={counts['PERK']} entry_points={counts['EP']} mgefs={counts['MGEF']} "
          f"leveled_lists={len(LEVELED_LISTS)}")


if __name__ == "__main__":
    sys.exit(main())
