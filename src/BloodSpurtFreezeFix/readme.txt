Zenderal - Blood Spurt Freeze Fix
=================================

Script-only fix for a rare game freeze in big fights (seen in the Fog Wood arena).

Enhanced Blood Textures plays its blood spurts with an aiming direction of (0, 0, 0). The game
turns that into a ray with no length, so these spurts almost never show anything at all, but now
and then the engine's ray walk runs away with one and the game locks up for good (no crash log).

This is the DF - Enhanced Blood Textures Patch's zbloodnpc script with those 12 spurt calls
commented out. Nothing else changed: every other blood effect, splatter, pool and drip still plays.

Must win over DF - Enhanced Blood Textures Patch and Enhanced Blood Textures (sort it above them
in MO2's left pane).

Source included in Scripts/Source. Original script: Enhanced Blood Textures (Enderal SE port) and
its Dismembering Framework patch.
