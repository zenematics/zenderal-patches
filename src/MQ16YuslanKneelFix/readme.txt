Zenderal - MQ16 Yuslan Kneel Fix
================================

Script-only fix for Enderal SE's main quest "The Shards of Order, Part II" (MQ16), in the City of a
Thousand Floods.

When the party finds the corpses, Calia wonders why they have not decayed and Yuslan answers "Good
question." The scene then waits for Yuslan to kneel by one of the corpses. If he never kneels, the
quest stops there; a console disable/enable of Yuslan was the only way on.

This replaces SureAI's quest script (_00E_MQ16_Functions) with the same script plus a watchdog for
that one wait. If Yuslan has not knelt after a few seconds it nudges him, one step at a time:
re-evaluating his package, resetting his animation state, then the disable/enable that worked, then
placing him on the kneeling spot. Every step is written to the Papyrus log, lines starting with
[ZP MQ16 kneel].

Stuck in an existing save? Open the console, click Yuslan (or type: prid 102DED), then type
disable, then enable.

Source included in Scripts/Source. Original script by SureAI.
