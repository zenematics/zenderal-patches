#pragma once

#include "ScriptObject.h"

class MCM :
	public REX::Singleton<MCM>
{
public:
	void LoadForm()
	{
		if (auto data = RE::TESDataHandler::GetSingleton())
			MCMQuest = data->LookupForm(0x000800, "BakaHeroMenu.esp"sv);
	}

	// clang-format off
	void LoadSettings()
	{
		if (auto mcm = ScriptObject::FromForm(MCMQuest, "BakaHeroMenuMCMScript"sv))
		{
			ApplySeducerBonus    = ScriptObject::GetBool(*mcm, "bApplySeducerBonus"sv).value_or(ApplySeducerBonus);
			ApplyMesmerizeBonus  = ScriptObject::GetBool(*mcm, "bApplyMesmerizeBonus"sv).value_or(ApplyMesmerizeBonus);
			DisableOutsideCities = ScriptObject::GetBool(*mcm, "bDisableOutsideCities"sv).value_or(DisableOutsideCities);
			IgnoreLearningGold   = ScriptObject::GetBool(*mcm, "bIgnoreLearningGold"sv).value_or(IgnoreLearningGold);
			IgnoreLearningPoints = ScriptObject::GetBool(*mcm, "bIgnoreLearningPoints"sv).value_or(IgnoreLearningPoints);
			IgnoreCraftingGold   = ScriptObject::GetBool(*mcm, "bIgnoreCraftingGold"sv).value_or(IgnoreCraftingGold);
			IgnoreCraftingPoints = ScriptObject::GetBool(*mcm, "bIgnoreCraftingPoints"sv).value_or(IgnoreCraftingPoints);
			ShowPenniesInMenu    = ScriptObject::GetBool(*mcm, "bShowPenniesInMenu"sv).value_or(ShowPenniesInMenu);
			SkipCallback         = ScriptObject::GetBool(*mcm, "bSkipCallback"sv).value_or(SkipCallback);
		}
	}
	// clang-format on

public:
	bool QApplySeducerBonus() const { return ApplySeducerBonus; }
	bool QApplyMesmerizeBonus() const { return ApplyMesmerizeBonus; }
	bool QDisableOutsideCities() const { return DisableOutsideCities; }
	bool QIgnoreLearningGold() const { return IgnoreLearningGold; }
	bool QIgnoreLearningPoints() const { return IgnoreLearningPoints; }
	bool QIgnoreCraftingGold() const { return IgnoreCraftingGold; }
	bool QIgnoreCraftingPoints() const { return IgnoreCraftingPoints; }
	bool QShowPenniesInMenu() const { return ShowPenniesInMenu; }
	bool QSkipCallback() const { return SkipCallback; }

private:
	RE::TESForm* MCMQuest{ nullptr };

private:
	bool ApplySeducerBonus{ false };
	bool ApplyMesmerizeBonus{ false };
	bool DisableOutsideCities{ false };
	bool IgnoreLearningGold{ true };    // ZP: Zenderal default - skills cost points only, no gold
	bool IgnoreLearningPoints{ false };
	bool IgnoreCraftingGold{ true };    // ZP: Zenderal default - skills cost points only, no gold
	bool IgnoreCraftingPoints{ false };
	bool ShowPenniesInMenu{ false };    // ZP: no gold cost, so no gold readout
	bool SkipCallback{ false };
};
