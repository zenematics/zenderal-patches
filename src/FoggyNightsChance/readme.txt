Zenderal - Foggy Nights Chance
==============================

One recompiled script. No plugin, no records, no ESP.

  Scripts\FogNightScript.pex    (+ Scripts\Source\ .psc)

  Base: Foggy Nights for Enderal 1.0.3's own FogNightScript.psc (Nexus
  Enderal SE mod 487), verbatim. Changes marked "; ZFN".

Credit: the author of Foggy Nights for Enderal.


WHAT IT CHANGES
---------------
Foggy Nights makes every night foggy: its quest's player alias runs
FogNightScript, which at 20:00 forces its NightThickFog weather with
Weather.SetActive(true, false) and at 07:00 calls Weather.ReleaseOverride().

This fork rolls once per night (30%, the fog_chance variable). On the other
70% of nights the regions' own weather plays on. The roll is remembered for the
rest of that night, so reloading or changing cells does not roll again. The
script now decides night or morning by the hour, not by whether the fog is
showing (the original treated a fog-free morning as night and re-applied it).
The morning only releases the override when the current weather is this mod's
fog. The FoggyWeather property is unchanged.

Install: sort ABOVE "Foggy Nights for Enderal" in MO2's modlist.txt (higher
priority, so this .pex wins). Keep Foggy Nights - Enderal.esp enabled.
Existing saves pick it up at the next scheduled 20:00 or 07:00 update.
