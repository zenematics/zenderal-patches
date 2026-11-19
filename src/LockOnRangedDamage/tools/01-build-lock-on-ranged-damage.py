r"""Generate the Lock-On Ranged Damage plugin YAML -- never hand-edit what this writes.

Curator's request (2026-11-16): shooting a bow, crossbow, musket or pistol while locked on with True Directional
Movement does 60% of the damage; aiming by hand does full damage. The list's TDM aims a locked shot for the player
(uTargetLockArrowAimType / uTargetLockMissileAimType = 1, predictive aim, TDM's default; Zenderal - Settings does not
change it).

How TDM tells us it is locked: while a target lock is active, TDM puts its ability TDM_TargetLockSpell
000805:TrueDirectionalMovement.esp on the player (its DLL looks the spell up by 0x805 at load: lea of the string
"TrueDirectionalMovement.esp", mov edx 0x805, LookupForm), and that ability carries the dummy effect
TDM_TargetLock 000804 (documented on TDM's page for DAR conditions).

Mechanism: TDM's effect 000804 verbatim plus PerkToApply = our hidden perk. A perk applied through an effect is added
and removed with the effect (Zen Traits, Kata's book perks, Reforged Directional Combat and base Enderal's
_00E_Frozen_ME all use PerkToApply), so the perk sits on the player exactly while the lock is on, no script, no
quest. No plugin in the list masters TrueDirectionalMovement.esp (scan of profiles/Ultra, 2026-11-16), so this is
the only override of 000804.

The perk (all entries Multiply LOCKED_DAMAGE):
  - ModAttackDamage, weapon (tab 1) has WeapTypeBow 01E715: bows, crossbows and the Ordo muskets all carry it
    (TraitsRework's Gunslinger relies on the same fact). Also hits a bash made with one of them while locked.
  - CalculateMyCriticalHitDamage, same condition: the crit part of the hit.
  - ModSpellMagnitude, spell (tab 1) has ZP_FlintlockShot 00080C: the pistols are staves whose damage is the shot
    enchantment's magnitude (the condition the Flintlock Overhaul's own scaling perk 00080D uses). Reversal Shadow's
    shot keeps the keyword, so its Witch Bolt is scaled too, as the Flintlock scaling already does.
Not scaled: talent procs riding a hit (Deadeye's bleed, Arcane Arsenal's element, Ice Shot), explosions from ammo,
anything not on those three entry points.

Order: the list's flat Add entries on bow hits (Enderal's Master of the Bowstring +1, EGO's silver arrows +5 vs
undead) are priority 0 like these; whether they land before or after the x0.6 is not established, a difference of
at most 2 points a hit.

Rerun after a TDM update (re-serialize TrueDirectionalMovement.esp into reference/mods/TDM first).
"""
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
PATCH = "Zenderal - Lock-On Ranged Damage.esp"
ESP_DIR = os.path.join(ROOT, "src", "LockOnRangedDamage", "LockOnRangedDamageESP")

LOCKED_DAMAGE = 0.6

TDM_MGEF = "TDM_TargetLock - 000804_TrueDirectionalMovement.esp.yaml"
TDM_SRC = os.path.join(ROOT, "reference", "mods", "TDM", "MagicEffects", TDM_MGEF)

PERK_ID = f"000800:{PATCH}"
WEAP_TYPE_BOW = "01E715:Skyrim.esm"
FLINTLOCK_SHOT = "00080C:Zenderal - Flintlock Overhaul.esp"

RECORD_DATA = f"""SpriggitSource:
  PackageName: Spriggit.Yaml.Skyrim
  Version: 0.40
ModKey: {PATCH}
GameRelease: EnderalSE
ModHeader:
  Flags:
  - Small
  Stats:
    Version: 1.7
  Author: Zenderal
  Description: Bows, crossbows, muskets and pistols do 60% damage while locked on with True Directional Movement; manual aim does full damage. TDM's lock-on effect applies a hidden perk.
  MasterReferences:
  - Master: Skyrim.esm
    FileSize: 0
  - Master: Update.esm
    FileSize: 0
  - Master: Enderal - Forgotten Stories.esm
    FileSize: 0
  - Master: TrueDirectionalMovement.esp
    FileSize: 0
  - Master: Zenderal - Flintlock Overhaul.esp
    FileSize: 0
  INTV: 1
"""

META = f"""{{
  "PackageName": "Spriggit.Yaml.Skyrim",
  "Version": "0.40.0",
  "Release": "EnderalSE",
  "ModKey": "{PATCH}"
}}"""


def entry(entry_point, keyword):
    return f"""- MutagenObjectType: PerkEntryPointModifyValue
  Conditions:
  - RunOnTabIndex: 1
    Conditions:
    - MutagenObjectType: ConditionFloat
      Data:
        MutagenObjectType: {'EPMagic_SpellHasKeywordConditionData' if entry_point == 'ModSpellMagnitude' else 'HasKeywordConditionData'}
        Keyword: {keyword}
      ComparisonValue: 1
  EntryPoint: {entry_point}
  PerkConditionTabCount: 3
  Modification: Multiply
  Value: {LOCKED_DAMAGE}
"""


PERK = f"""FormKey: {PERK_ID}
EditorID: ZP_LockOnRangedDamage
Name:
  TargetLanguage: English
  Value: Lock-On Aim
Description:
  TargetLanguage: English
  Value: ''
NumRanks: 1
Playable: True
Hidden: True
Effects:
{entry('ModAttackDamage', WEAP_TYPE_BOW)}{entry('CalculateMyCriticalHitDamage', WEAP_TYPE_BOW)}{entry('ModSpellMagnitude', FLINTLOCK_SHOT)}"""


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8", newline="\r\n").write(text)
    print("wrote", os.path.relpath(path, ROOT))


def main():
    mgef = open(TDM_SRC, encoding="utf-8").read().replace("\r\n", "\n")
    if "PerkToApply:" in mgef:
        raise SystemExit(f"{TDM_SRC}: TDM's effect already applies a perk (TDM updated?): merge by hand")
    anchor = "DualCastScale: 1\n"
    if mgef.count(anchor) != 1:
        raise SystemExit(f"{TDM_SRC}: expected exactly one '{anchor.strip()}'")
    new = mgef.replace(anchor, anchor + f"PerkToApply: {PERK_ID}\n")
    added = [l for l in new.split("\n") if l not in mgef.split("\n")]
    assert added == [f"PerkToApply: {PERK_ID}"], added
    assert "FormKey: 000804:TrueDirectionalMovement.esp" in new

    write(os.path.join(ESP_DIR, "MagicEffects", TDM_MGEF), new)
    write(os.path.join(ESP_DIR, "Perks", f"ZP_LockOnRangedDamage - 000800_{PATCH}.yaml"), PERK)
    write(os.path.join(ESP_DIR, "RecordData.yaml"), RECORD_DATA)
    write(os.path.join(ESP_DIR, "spriggit-meta.json"), META)
    assert PERK.count(f"Value: {LOCKED_DAMAGE}") == 3


if __name__ == "__main__":
    main()
