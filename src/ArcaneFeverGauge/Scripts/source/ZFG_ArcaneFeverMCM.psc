Scriptname ZFG_ArcaneFeverMCM extends MCM_ConfigBase
{Zenderal - Arcane Fever Gauge: its MCM page (MCM Helper). The page is MCM/Config/Zenderal - Arcane Fever Gauge/config.json,
the defaults settings.ini next to it. Every change is handed to the gauge's script, which reads the settings itself.}

ZFG_ArcaneFeverWidget Property Gauge Auto
{Quest 800, the gauge.}

Event OnSettingChange(String a_ID)
	Gauge.ApplySettings()
EndEvent

Event OnConfigClose()
	Gauge.ApplySettings()
EndEvent
