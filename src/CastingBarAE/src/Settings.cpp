#include "Settings.h"

using namespace SKSE;

void GetValue(CSimpleIniA& a_ini, int& a_value, const char* a_section,
	const char* a_key, const char* a_comment = nullptr)
{
	a_value = static_cast<int>(a_ini.GetLongValue(a_section, a_key, a_value));
	a_ini.SetLongValue(a_section, a_key, a_value, a_comment);
}

void GetValue(CSimpleIniA& a_ini, float& a_value, const char* a_section,
	const char* a_key, const char* a_comment = nullptr)
{
	a_value = static_cast<float>(a_ini.GetDoubleValue(a_section, a_key, a_value));
	a_ini.SetDoubleValue(a_section, a_key, a_value, a_comment);
}

void GetValue(CSimpleIniA& a_ini, bool& a_value, const char* a_section,
	const char* a_key, const char* a_comment = nullptr)
{
	a_value = a_ini.GetBoolValue(a_section, a_key, a_value);
	a_ini.SetBoolValue(a_section, a_key, a_value, a_comment);
};

void GetValue(CSimpleIniA& a_ini, std::string& a_value, const char* a_section,
	const char* a_key, const char* a_comment = nullptr)
{
	a_value = a_ini.GetValue(a_section, a_key, a_value.c_str());
	a_ini.SetValue(a_section, a_key, a_value.c_str(), a_comment);
};

namespace
{
	std::string IniPath()
	{
		auto plugin = PluginDeclaration::GetSingleton();
		return fmt::format("Data\\SKSE\\Plugins\\{}.ini", plugin->GetName());
	}

	void GetLayout(CSimpleIniA& a_ini, WidgetLayout& a_layout, const char* a_section, const char* a_name)
	{
		GetValue(a_ini, a_layout.PositionX, a_section, "PositionX", fmt::format(";The X Position for the {} widget", a_name).c_str());
		GetValue(a_ini, a_layout.PositionY, a_section, "PositionY", fmt::format(";The Y Position for the {} widget", a_name).c_str());
		GetValue(a_ini, a_layout.ScaleX, a_section, "ScaleX", fmt::format(";The X scale of the {} widget", a_name).c_str());
		GetValue(a_ini, a_layout.ScaleY, a_section, "ScaleY", fmt::format(";The Y scale of the {} widget", a_name).c_str());
	}

	void Apply(CSimpleIniA& a_ini)
	{
		GetValue(a_ini, Settings::EnableForSpell, "General", "EnableForSpell", ";Enable the widget for spell casting");
		GetValue(a_ini, Settings::EnableForShout, "General", "EnableForShout", ";Enable the widget for shouting");
		GetValue(a_ini, Settings::EnableForBow, "General", "EnableForBow", ";Enable the widget for bow drawing");
		GetValue(a_ini, Settings::HideWithHUD, "General", "HideWithHUD", ";Hide the widget while the HUD is hidden (Ultimate Immersion Toggle)");

		GetLayout(a_ini, Settings::Spell, "Spell", "spell");
		GetLayout(a_ini, Settings::Shout, "Shout", "shout");
		GetLayout(a_ini, Settings::Bow, "Bow", "bow");
	}
}

WidgetLayout& Settings::LayoutFor(std::string_view a_movie)
{
	if (a_movie.ends_with("_Shout")) {
		return Shout;
	}
	if (a_movie.ends_with("_Bow")) {
		return Bow;
	}
	return Spell;
}

void Settings::ReadSettings()
{
	logger::info("Reading settings...");

	auto path = IniPath();

	CSimpleIniA ini;
	ini.SetUnicode();
	ini.LoadFile(path.c_str());

	// 3.x's single [Position] section seeds all three widgets when they have no section of their own
	WidgetLayout legacy;
	legacy.PositionX = static_cast<float>(ini.GetDoubleValue("Position", "WidgetPositionX", legacy.PositionX));
	legacy.PositionY = static_cast<float>(ini.GetDoubleValue("Position", "WidgetPositionY", legacy.PositionY));
	legacy.ScaleX = static_cast<float>(ini.GetDoubleValue("Position", "WidgetScaleX", legacy.ScaleX));
	legacy.ScaleY = static_cast<float>(ini.GetDoubleValue("Position", "WidgetScaleY", legacy.ScaleY));
	Spell = Shout = Bow = legacy;

	Apply(ini);

	ini.SaveFile(path.c_str());
}

void Settings::SaveSettings()
{
	auto path = IniPath();

	CSimpleIniA ini;
	ini.SetUnicode();
	ini.LoadFile(path.c_str());

	ini.SetBoolValue("General", "EnableForSpell", EnableForSpell);
	ini.SetBoolValue("General", "EnableForShout", EnableForShout);
	ini.SetBoolValue("General", "EnableForBow", EnableForBow);
	ini.SetBoolValue("General", "HideWithHUD", HideWithHUD);

	for (auto [section, layout] : { std::pair{ "Spell", &Spell }, std::pair{ "Shout", &Shout }, std::pair{ "Bow", &Bow } }) {
		ini.SetDoubleValue(section, "PositionX", layout->PositionX);
		ini.SetDoubleValue(section, "PositionY", layout->PositionY);
		ini.SetDoubleValue(section, "ScaleX", layout->ScaleX);
		ini.SetDoubleValue(section, "ScaleY", layout->ScaleY);
	}

	ini.SaveFile(path.c_str());
	logger::info("Settings saved");
}
