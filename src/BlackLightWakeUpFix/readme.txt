Zenderal - Black Light Wake Up Fix
==================================

One recompiled script. No plugin, no records, no ESP.

  Scripts\_00E_MQ12c_Functions.pex   (+ Scripts\Source\ .psc)

  Base: SureAI's script (ScriptsEnderal.zip, Enderal 2.1.4.4), verbatim.
  Change: a wake-up watchdog, every line marked "; ZP".

Credit: SureAI (original script).

THE BUG
-------
Black Light, Part III: after the dream in the Temple quarters the screen stays
black, the player cannot move, and Jespar/Calia never come to wake you.

After the dream, scene MQ12c_SC04_WakeUp keeps the screen black and makes the
player walk to the bed MQ12c_SC2_Bed (0A6F3A) and lie down. Its first phase
ends - and only then fades the screen back in - when the player is lying in
that bed. If the player never gets into it, nothing ever ends the phase.
"player.setscale 1" does not help.

THE FIX
-------
When the wake-up scene starts, a watchdog starts with it:

  - after 15 s, if the player is not in (or getting into) any furniture, it
    puts them in the bed through the bed's own script (at this stage that
    lies them down without the sleep menu);
  - after 15 s more, if the screen still has not faded in, it fades it in,
    gives the controls back and unblocks the bed, so the player can lie down
    themselves; that ends the phase and the scene carries on (the companion
    walks in).

When the scene works normally, the watchdog does nothing.

Saves already stuck on the black screen started the scene with the old script;
use the console recovery from the Zenderal Discord for those.
