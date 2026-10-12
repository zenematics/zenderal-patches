Zenderal - Zen Traits Fixes
===========================

One recompiled script. No plugin, no records, no ESP.

  Scripts\_00e_ambrosiaeffect.pex    (+ Scripts\Source\ .psc)

  Base: Shazdeh's Zen Traits source, verbatim (upstream main @ 1ae67a8).
  Change: one line, marked "; ZP".

Credit: Shazdeh (Zen Traits, MIT licence) and SureAI (the Enderal script that
Zen Traits itself replaces).


THE BUG
-------
Zen Traits ships a loose _00e_ambrosiaeffect.pex that replaces Enderal's copy
in E - Misc.bsa. Its version reads the reduction amount from the Variable08
actor value. Nothing in Enderal or in this list ever writes Variable08, so the
value is always 0, and drinking Ambrosia reduced Arcane Fever by 0. It still
plays the flash, the sound and the "reduced by" notification, so it looks as
though it worked.

The amount actually lives on the potion's effect item: _00E_Ambrosia (0FEC69)
-> _00E_AlchReduceArcaneFever (1037EC), magnitude 20 in base Enderal and 15
under EGO. SureAI's own script reads it with GetMagnitude(), and this fix does
the same. Zen Traits' Purified Blood multiplier (GetAmbrosiaMod) and its
clamp at 0 fever (ModFever) are unchanged and get a real number again.

Upstream report: https://github.com/shazdeh/Zen-Traits/issues/2


INSTALL ORDER
-------------
This mod must sort ABOVE "Zen Traits" in MO2's left pane (higher priority) to
win the loose-script file conflict. If it sorts below, the game runs normally
and Ambrosia stays broken.

Drop this mod once Zen Traits ships the fix itself.
