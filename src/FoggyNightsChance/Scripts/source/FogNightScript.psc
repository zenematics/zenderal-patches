Scriptname FogNightScript extends ReferenceAlias
; Fork of Foggy Nights for Enderal 1.0.3 (Nexus Enderal SE mod 487) by its author.
; Zenderal change ("; ZFN"): fog on about 30% of nights instead of every night.
; One roll per night, kept across loads; the hour decides night or morning,
; and the morning only releases the weather when it is this mod's fog.
; No Property added or removed.


Weather Property FoggyWeather  Auto
float morn_hour = 7.0
float night_hour = 20.0
float fog_chance = 0.3 ; ZFN
int rolled_night = -1 ; ZFN
bool fog_tonight = false ; ZFN


Event OnLoad()


	float hour = GetCurrentHourOfDay()
	float initialWait = 0.1

	if (hour >= morn_hour && hour < night_hour)
		float timeTillNight = GetHoursTillNight()
		RegisterForSingleUpdateGameTime(timeTillNight)

	else
		if Weather.GetCurrentWeather() != FoggyWeather
			RegisterForSingleUpdateGameTime(initialWait)
		else
			float timeTillDay = GetHoursTillDay()
			RegisterForSingleUpdateGameTime(timeTillDay)
		endif
	endIf

EndEvent


float Function GetCurrentHourOfDay()

	float time = Utility.GetCurrentGameTime()
	time -= Math.Floor(Time)
	time *= 24
	; Debug.Notification("time: " + time)
	Return time

EndFunction


float Function GetHoursTillDay()

	float hour = GetCurrentHourOfDay()
	float timeLeft = 0

	if (hour >= 0 && hour < morn_hour)
		timeLeft = morn_hour - hour
		return timeLeft

	elseIf (hour >= night_hour && hour < 24)

		timeLeft = 24 - hour + morn_hour
		return timeLeft
	else
		; Debug.Notification("Error: Daylight calculation")
	endIf

EndFunction


float Function GetHoursTillNight()

	float hour = GetCurrentHourOfDay()
	float time = night_hour - hour
	return time

EndFunction


; ZFN: the night that started at night_hour; the same number until morn_hour.
int Function GetNightID()
	return Math.Floor(Utility.GetCurrentGameTime() + (24.0 - night_hour) / 24.0)
EndFunction


Event OnInit()
	OnLoad()
EndEvent


Event OnUpdateGameTime()

	; ZFN: night or morning by the hour, not by the current weather
	float hour = GetCurrentHourOfDay()
	if (hour >= night_hour || hour < morn_hour)
		int night = GetNightID()
		if night != rolled_night
			rolled_night = night
			fog_tonight = Utility.RandomFloat(0.0, 1.0) < fog_chance
		endif
		if fog_tonight && Weather.GetCurrentWeather() != FoggyWeather
			FoggyWeather.setActive(true, false)
		endif
		float timeTillDay = GetHoursTillDay()
		if timeTillDay < 0.05
			timeTillDay = 0.05
		endif
		RegisterForSingleUpdateGameTime(timeTillDay)
	else
		if Weather.GetCurrentWeather() == FoggyWeather
			Weather.ReleaseOverride()
		endif
		float timeTillNight = GetHoursTillNight()
		if timeTillNight < 0.05
			timeTillNight = 0.05
		endif
		RegisterForSingleUpdateGameTime(timeTillNight)
	endif

EndEvent
