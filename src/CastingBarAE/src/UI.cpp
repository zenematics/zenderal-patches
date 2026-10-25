#include "UI.h"

#include "CastingBar.h"
#include "Settings.h"

namespace
{
	struct ImVec2
	{
		float x = 0.0f;
		float y = 0.0f;
	};

	using RenderFunction = void(__stdcall*)();

	HMODULE Framework()
	{
		static HMODULE module = GetModuleHandleW(L"SKSEMenuFramework");
		return module;
	}

	template <class T>
	T Get(const char* a_name)
	{
		return reinterpret_cast<T>(GetProcAddress(Framework(), a_name));
	}

	bool Checkbox(const char* a_label, bool* a_value)
	{
		static auto func = Get<bool (*)(const char*, bool*)>("igCheckbox");
		return func && func(a_label, a_value);
	}

	bool SliderFloat(const char* a_label, float* a_value, float a_min, float a_max)
	{
		static auto func = Get<bool (*)(const char*, float*, float, float, const char*, int)>("igSliderFloat");
		return func && func(a_label, a_value, a_min, a_max, "%.0f", 0);
	}

	bool Button(const char* a_label)
	{
		static auto func = Get<bool (*)(const char*, const ImVec2)>("igButton");
		return func && func(a_label, ImVec2{});
	}

	void SeparatorText(const char* a_label)
	{
		static auto func = Get<void (*)(const char*)>("igSeparatorText");
		if (func) {
			func(a_label);
		}
	}

	void TextWrapped(const char* a_text)
	{
		static auto func = Get<void (*)(const char*, ...)>("igTextWrapped");
		if (func) {
			func("%s", a_text);
		}
	}

	void SameLine()
	{
		static auto func = Get<void (*)(float, float)>("igSameLine");
		if (func) {
			func(0.0f, -1.0f);
		}
	}

	bool LayoutSliders(const char* a_id, WidgetLayout& a_layout)
	{
		bool changed = false;
		changed |= SliderFloat(fmt::format("Position X##{}", a_id).c_str(), &a_layout.PositionX, 0.0f, 3840.0f);
		changed |= SliderFloat(fmt::format("Position Y##{}", a_id).c_str(), &a_layout.PositionY, 0.0f, 2160.0f);
		changed |= SliderFloat(fmt::format("Scale X##{}", a_id).c_str(), &a_layout.ScaleX, 10.0f, 300.0f);
		changed |= SliderFloat(fmt::format("Scale Y##{}", a_id).c_str(), &a_layout.ScaleY, 10.0f, 300.0f);
		return changed;
	}

	void WidgetSection(const char* a_title, const char* a_movie, WidgetLayout& a_layout)
	{
		SeparatorText(a_title);

		bool previewing = CastingBar::PreviewMovie.load() == a_movie;
		if (Checkbox(fmt::format("Show for positioning##{}", a_movie).c_str(), &previewing)) {
			CastingBar::PreviewMovie = previewing ? a_movie : nullptr;
			CastingBar::LayoutDirty = true;
		}
		if (LayoutSliders(a_movie, a_layout)) {
			CastingBar::LayoutDirty = true;
		}
	}

	void __stdcall Render()
	{
		SeparatorText("General");
		Checkbox("Spell casting", &Settings::EnableForSpell);
		Checkbox("Shouting", &Settings::EnableForShout);
		Checkbox("Bow drawing", &Settings::EnableForBow);
		Checkbox("Hide with the HUD (Ultimate Immersion Toggle)", &Settings::HideWithHUD);

		WidgetSection("Spell widget", "CastingBar_Spell", Settings::Spell);
		WidgetSection("Shout widget", "CastingBar_Shout", Settings::Shout);
		WidgetSection("Bow widget", "CastingBar_Bow", Settings::Bow);

		SeparatorText("");
		if (Button("Save")) {
			Settings::SaveSettings();
		}
		SameLine();
		if (Button("Reload from ini")) {
			Settings::ReadSettings();
			CastingBar::LayoutDirty = true;
		}
		TextWrapped("Changes apply at once; Save writes them to SKSE/Plugins/CastingBar.ini.");
	}
}

void UI::Register()
{
	if (!Framework()) {
		logger::info("SKSE Menu Framework not loaded - UI registration skipped");
		return;
	}

	auto addSectionItem = Get<void (*)(const char*, RenderFunction)>("AddSectionItem");
	if (!addSectionItem) {
		logger::warn("SKSEMenuFramework.dll has no AddSectionItem export - UI registration skipped");
		return;
	}

	addSectionItem("Casting Bar/Settings", Render);
	logger::info("SKSE Menu Framework UI registered");
}
