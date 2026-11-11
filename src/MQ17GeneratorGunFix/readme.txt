Zenderal - MQ17 Generator Gun Fix
=================================

One recompiled script. No plugin, no records, no ESP.

  Scripts\_00E_MQ17_BossFight_GeneratorSC.pex   (+ Scripts\Source\ .psc)

  Base: SureAI's script (ScriptsEnderal.zip, Enderal 2.1.4.4), verbatim.
  Change: every added line is marked "; ZP".

Credit: SureAI (original script).

THE BUG
-------
Final boss (spoilers): the two generators took no damage from muskets or
pistols; only melee and bashing worked.

SureAI counts damage only through two invisible hit boxes around the
generators (MQ17_Generator_Left/Right_Hitbox, script
_00E_MQ17_GeneratorHitBoxSC). The generator actor's own OnHit is empty. The
list's guns (Ordo's 60000-speed exploding musket ball, the flintlock pack's
missile shot) evidently miss the box and reach the generator, where the hit
was dropped.

THE FIX
-------
The generator's OnHit now passes the player's hits to SureAI's own
CheckForDamage, under the hit box's rules (player only, MQ17 stage 75+,
generator alive). One shot that hits both is counted once: the same source
within 0.3 s is ignored. SureAI's damage formula is unchanged.

Every hit is logged in the Papyrus log as "[ZP MQ17 generator] ...", with
"hit box" or "generator" telling which path counted it.
