Zenderal - Fever Death Latch Fix
================================

One recompiled script. No plugin, no records, no ESP.

  Scripts\_00E_EPUpdateFunctions.pex   (+ Scripts\Source\ .psc)

  Base: Leveling Redone's copy of the script (Ixion XVII), verbatim - itself
        SureAI's script with Leveling Redone's 4/3 points per level.
  Change: one guard added, marked "; ZP".

Credit: SureAI (original script), Ixion XVII (Leveling Redone).

THE BUG
-------
When Arcane Fever reaches 100, the player script sets a private flag, isdead,
then calls Player.Kill(). Nothing ever sets isdead back to False. That is fine
if the player dies and reloads an earlier save - but if Kill() does not take
(god mode, an essential player, a scene), the player lives on with isdead =
True, and it is written into every later save.

isdead gates the level-up loop and the Arcane Fever 40%/70% effects, so the
character can never level again: XP keeps rising past the bar, and
"prid player" + "sv" shows "iLevelUpsNeeded = N" next to "IsDead = True".

THE FIX
-------
Each update tick (every 3.5 s), if isdead is set, the player is NOT actually
dead and fever is below 100, the flag is cleared. A real fever death is
unchanged: the player is dead, so the flag stays until reload.

On an affected save, the owed level-ups fire a few seconds after loading.

INSTALL
-------
Must win the loose-script conflict with "Leveling Redone (No Skillbooks)":
sort this mod BELOW it in MO2's left pane.
