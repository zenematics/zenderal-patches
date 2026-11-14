Zenderal - Prologue Rope Fix
============================

Script-only fix for Enderal SE's prologue on the ship (quest MQP02, objective "Find a rope").

Using the rope hands the player to a scripted scene: the character walks to a crate, the Veiled
Woman appears, the player levitates, is thrown at the wall and knocked out. The player has no
control during all of it, and if one step never finishes they stay frozen for good.

This replaces SureAI's rope script (_00E_MQP02_RopeSC) with the same script plus a watchdog:
- if the walk to the crate has not arrived after 20 seconds, the player is moved onto it;
- if the levitation or the throw never finishes, SureAI's own next step is run.
Every step is written to the Papyrus log, lines starting with [ZP MQP02 rope].

Source included in Scripts/Source. Original script by SureAI.
