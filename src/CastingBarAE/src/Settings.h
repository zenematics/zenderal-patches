#pragma once

struct WidgetLayout
{
	float PositionX = 961.0f;
	float PositionY = 1040.0f;
	float ScaleX = 75.0f;
	float ScaleY = 75.0f;
};

struct Settings
{
	static void ReadSettings();
	static void SaveSettings();

	// Layout for a movie name (CastingBar_Spell / _Shout / _Bow)
	static WidgetLayout& LayoutFor(std::string_view a_movie);

	// General
	static inline bool EnableForSpell = true;
	static inline bool EnableForShout = true;
	static inline bool EnableForBow = false;

	// Zenderal: hide while the HUD Menu's _root._alpha is 0 (Ultimate Immersion Toggle)
	static inline bool HideWithHUD = true;

	// Per widget, as in the SKSE Menu Framework edition; defaults come from 3.x's single [Position] section
	static inline WidgetLayout Spell;
	static inline WidgetLayout Shout;
	static inline WidgetLayout Bow;
};
