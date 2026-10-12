#pragma once

#include "MCM.h"
#include "ScriptObject.h"
#include "Translator.h"

class Manager :
	public REX::Singleton<Manager>
{
private:
	enum ActorValue : std::int32_t
	{
		// Skills
		kOneHanded,
		kTwoHanded,
		kMarksman,
		kBlock,
		kHandicraft,
		kHeavyArmor,
		kLightArmor,
		kSlightOfHand,
		kLockpicking,
		kSneak,
		kAlchemy,
		kRhetoric,
		kMentalism,
		kEntropy,
		kElementalism,
		kPsionics,
		kLightMagic,
		kEnchanting,

		// Attributes
		kHealth,
		kMana,
		kStamina,
		kArcaneFever,

		// Total
		ActorValueTotal,
		SkillTotal = 18,
	};

	enum Affinity
	{
		kBattlemage,
		kCleric,
		kAssassin,
		kWayfarer,
		kBlackMage,
		kDarkKeeper,
		kFencer,
		kBladebreaker,
		kShadowdancer,
		kArcaneArcher,
		kWanderingMage,
		kSpectralist,
		kGhostBlade,
		kSpectralWarrior,
		kBrute,
		kDrifter,
		kDruid,
		kNightwolf,
		kRavager,
		kScourgeOfTheWilds,
		kSoulcaller,
		AffinityTotal,
	};

	enum Class
	{
		kNone,
		kBastion,
		kDerwish,
		kElementalist,
		kEspionage,
		kLifeAndDeath,
		kManipulation,
		kRage,
		kTrickery,
		kVagabond,
		kPhasmalist,
		kTheriantrophist,
		ClassTotal,
	};

	enum Index : std::int32_t
	{
		kVal,
		kMin,
		kMax,
		IndexTotal,
	};

	enum Level : std::int32_t
	{
		kApprentice,
		kAdept,
		kExpert,
		kMaster,
		LevelTotal,
	};

	enum Gender
	{
		kMale,
		kFemale,
		GenderTotal,
	};

	enum Global : std::int32_t
	{
		kExpMult,
		kExpMultSlope,
		kPlayerXP,
		kPlayerNeededXP,
		kPlayerLevel,
		kCraftingPoints,
		kLearningPoints,
		kTalentPoints,
		GlobalTotal,
	};

private:
	class HeroMessageBoxCallback :
		public RE::IMessageBoxCallback
	{
	public:
		inline static RE::BSTArray<RE::BSString> Buttons{ "$Yes", "$Cancel" };

	public:
		HeroMessageBoxCallback() = delete;
		HeroMessageBoxCallback(ActorValue a_av, std::int32_t a_cost) :
			m_actorValue(a_av),
			m_cost(a_cost)
		{
			Manager::GetSingleton()->SetOverrideMessage(true);
		}

		virtual void Run(std::uint8_t a_button) override
		{
			if (a_button == 0)
				Manager::GetSingleton()->IncreaseSkill(m_actorValue, m_cost);
			Manager::GetSingleton()->SetOverrideMessage(false);
		}

	private:
		ActorValue   m_actorValue{};
		std::int32_t m_cost{};
	};

public:
	void LoadForm()
	{
		Translator::GetSingleton()->Load();
		if (auto data = RE::TESDataHandler::GetSingleton())
		{
			LoadBookValues(data);
			LoadClassNames(data);
			LoadAffinityNames(data);
			LoadForms(data);
		}
	}

	void LoadSave()
	{
		UpdatePlayerInfo();
	}

	void UpdateCache()
	{
		UpdatePlayerInfo();
		UpdatePlayerGold();
		UpdateActorValues();
	}

public:
	bool QOverrideMessage() const
	{
		return overrideMessage;
	}

private:
	void SetOverrideMessage(bool a_value)
	{
		overrideMessage = a_value;
	}

private:
	auto ConvertActorValue(ActorValue a_av) const
	{
		switch (a_av)
		{
		case kOneHanded:
			return RE::ActorValue::kOneHanded;
		case kTwoHanded:
			return RE::ActorValue::kTwoHanded;
		case kMarksman:
			return RE::ActorValue::kArchery;
		case kBlock:
			return RE::ActorValue::kBlock;
		case kHandicraft:
			return RE::ActorValue::kSmithing;
		case kHeavyArmor:
			return RE::ActorValue::kHeavyArmor;
		case kLightArmor:
			return RE::ActorValue::kLightArmor;
		case kSlightOfHand:
			return RE::ActorValue::kPickpocket;
		case kLockpicking:
			return RE::ActorValue::kLockpicking;
		case kSneak:
			return RE::ActorValue::kSneak;
		case kAlchemy:
			return RE::ActorValue::kAlchemy;
		case kRhetoric:
			return RE::ActorValue::kSpeech;
		case kMentalism:
			return RE::ActorValue::kAlteration;
		case kEntropy:
			return RE::ActorValue::kConjuration;
		case kElementalism:
			return RE::ActorValue::kDestruction;
		case kPsionics:
			return RE::ActorValue::kIllusion;
		case kLightMagic:
			return RE::ActorValue::kRestoration;
		case kEnchanting:
			return RE::ActorValue::kEnchanting;
		case kHealth:
			return RE::ActorValue::kHealth;
		case kMana:
			return RE::ActorValue::kMagicka;
		case kStamina:
			return RE::ActorValue::kStamina;
		case kArcaneFever:
			return RE::ActorValue::kLastFlattered;
		default:
			return RE::ActorValue::kNone;
		}
	}

	auto ConvertActorValue(std::int32_t a_av) const
	{
		return ConvertActorValue(static_cast<ActorValue>(a_av));
	}

private:
	auto GetGlobalValue(Global a_global) const
	{
		switch (a_global)
		{
		case Global::kExpMult:
			return EXPMult ? EXPMult->value : 0.0f;
		case Global::kExpMultSlope:
			return EXPMultSlope ? EXPMultSlope->value : 0.0f;
		case Global::kPlayerXP:
			return PlayerXP ? PlayerXP->value : 0.0f;
		case Global::kPlayerNeededXP:
			return PlayerNeededXP ? PlayerNeededXP->value : 0.0f;
		case Global::kPlayerLevel:
			return PlayerLevel ? PlayerLevel->value : 0.0f;
		case Global::kCraftingPoints:
			return CraftingPoints ? CraftingPoints->value : 0.0f;
		case Global::kLearningPoints:
			return LearningPoints ? LearningPoints->value : 0.0f;
		case Global::kTalentPoints:
			return TalentPoints ? TalentPoints->value : 0.0f;
		default:
			return 0.0f;
		}
	}

private:
	auto GetActorValue(ActorValue a_av) const
	{
		return actorValue[a_av][kVal];
	}

	auto GetBaseActorValue(ActorValue a_av) const
	{
		return actorValue[a_av][kMin];
	}

	auto GetActorValueMod(ActorValue a_av) const
	{
		switch (a_av)
		{
		case kHealth:
		case kMana:
		case kStamina:
			return actorValue[a_av][kMax] - actorValue[a_av][kMin];
		default:
			return actorValue[a_av][kVal] - actorValue[a_av][kMin];
		}
	}

	void UpdateActorValue(ActorValue a_av)
	{
		if (auto player = RE::PlayerCharacter::GetSingleton())
		{
			auto av = ConvertActorValue(a_av);
			actorValue[a_av][kVal] = player->AsActorValueOwner()->GetActorValue(av);
			actorValue[a_av][kMin] = player->AsActorValueOwner()->GetBaseActorValue(av);
			if (a_av < kHealth)
				return;
			actorValue[a_av][kMax] = player->GetActorValueMax(av);
		}
	}

	void UpdateActorValues()
	{
		if (auto player = RE::PlayerCharacter::GetSingleton())
		{
			for (auto i = 0; i < ActorValueTotal; i++)
			{
				auto av = ConvertActorValue(i);
				actorValue[i][kVal] = player->AsActorValueOwner()->GetActorValue(av);
				actorValue[i][kMin] = player->AsActorValueOwner()->GetBaseActorValue(av);
				if (i < kHealth)
					continue;
				actorValue[i][kMax] = player->GetActorValueMax(av);
			}
		}
	}

private:
	std::string_view GetActorValueName(ActorValue a_av) const
	{
		return Translator::GetSingleton()->GetActorValueName(a_av);
	}

	std::string_view GetGoldName() const
	{
		return Translator::GetSingleton()->GetGoldName();
	}

	std::string_view GetPointName(bool a_craft) const
	{
		return Translator::GetSingleton()->GetPointName(a_craft);
	}

private:
	void UpdatePlayerGold()
	{
		if (auto player = RE::PlayerCharacter::GetSingleton();
			player && Gold001)
		{
			playerGold = player->GetItemCount(Gold001);
		}
	}

	void UpdatePlayerInfo()
	{
		if (auto player = RE::PlayerCharacter::GetSingleton())
		{
			playerName = player->GetName();
			if (auto base = player->GetActorBase())
				playerGender = base->GetSex();
			UpdatePlayerClassName();
		}
	}

private:
	void UpdateClassInfo()
	{
		if (AffinityQuest)
		{
			// ZP: Enderal 2.0.12 keeps these on _00E_Game_SkillmenuSC (Levelsystem 010AA2, alias "Player");
			// 2.1.x moved them to _00E_AffinityControl on a new FS quest that does not exist here.
			RE::BSReadLockGuard l{ AffinityQuest->aliasAccessLock };
			const RE::BGSBaseAlias* player = nullptr;
			for (auto alias : AffinityQuest->aliases)
			{
				if (alias && alias->aliasName == "Player"sv)
				{
					player = alias;
					break;
				}
			}
			if (player)
			{
				if (auto script = ScriptObject::FromAlias(player, "_00E_Game_SkillmenuSC"sv))
				{
					playerClassIndex = ScriptObject::GetSInt(*script, "iCurrentAffinityIndex"sv).value_or(playerClassIndex);
					playerClassMajor = ScriptObject::GetSInt(*script, "::MajorClassIndex_var"sv).value_or(playerClassMajor);
					playerClassMinor = ScriptObject::GetSInt(*script, "::MinorClassIndex_var"sv).value_or(playerClassMinor);
				}
			}
		}
	}

	void UpdatePlayerClassName()
	{
		UpdateClassInfo();
		if (playerClassIndex >= 0)
		{
			playerClass = affinityName[playerClassIndex][playerGender];
		}
		else
		{
			playerClass = className[playerClassMajor][playerGender];
			if (playerClassMinor > 0)
				playerClass.append(" / ").append(className[playerClassMinor][playerGender]);
		}
	}

private:
	std::int32_t CalculateGoldCost(std::int32_t a_cost)
	{
		auto mod{ 1.0f };
		if (auto player = RE::PlayerCharacter::GetSingleton())
		{
			auto min{ 1.3f }, max{ 3.3f }, bmi{ 1.05f }, bml{ 1.0f };
			if (auto gmst = RE::GameSettingCollection::GetSingleton())
			{
				if (auto setting = gmst->GetSetting("fBarterMin"))
					min = setting->GetFloat();
				if (auto setting = gmst->GetSetting("fBarterMax"))
					max = setting->GetFloat();
				if (auto setting = gmst->GetSetting("fBarterBuyMin"))
					bmi = setting->GetFloat();
				if (auto setting = gmst->GetSetting("fMinBuyMult"))
					bml = setting->GetFloat();
			}

			mod = std::max(bmi, max - (max - min) * (std::min(GetActorValue(kRhetoric), 100.0f) / 100.0f));
			RE::BGSEntryPoint::HandleEntryPoint(
				RE::BGSEntryPoint::ENTRY_POINT::kModBuyPrices,
				player,
				nullptr,
				&mod);

			if (MCM::GetSingleton()->QApplySeducerBonus())
			{
				if (Seducer && player->HasPerk(Seducer))
					mod *= 0.90f;
			}

			if (MCM::GetSingleton()->QApplyMesmerizeBonus())
			{
				if (Mesmerize03 && player->HasSpell(Mesmerize03))
					mod *= 1.0f + ((GetActorValue(kPsionics) / 6.0f) + 14.0f) / 100.0f;
				else if (Mesmerize02 && player->HasSpell(Mesmerize02))
					mod *= 1.0f + ((GetActorValue(kPsionics) / 6.0f) + 10.0f) / 100.0f;
				else if (Mesmerize01 && player->HasSpell(Mesmerize01))
					mod *= 1.0f + ((GetActorValue(kPsionics) / 6.0f) + 07.0f) / 100.0f;
			}

			mod = std::max(std::max(mod, bml), 1.0f);
		}

		return static_cast<std::int32_t>(roundf(a_cost * mod));
	}

	std::int32_t GetGoldCost(ActorValue a_av, Level a_idx)
	{
		return CalculateGoldCost(bookCost[a_av][a_idx]);
	}

	std::int32_t GetGoldCost(ActorValue a_av)
	{
		auto value = GetBaseActorValue(a_av);
		if (value < 25)
			return GetGoldCost(a_av, kApprentice);
		else if (value < 50)
			return GetGoldCost(a_av, kAdept);
		else if (value < 75)
			return GetGoldCost(a_av, kExpert);
		else
			return GetGoldCost(a_av, kMaster);
	}

private:
	void ModGold(std::int32_t a_cost)
	{
		if (auto player = RE::PlayerCharacter::GetSingleton();
			player && Gold001)
		{
			player->RemoveItem(Gold001, a_cost, RE::ITEM_REMOVE_REASON::kRemove, nullptr, nullptr);
		}
		UpdatePlayerGold();
	}

	void ModGlobal(RE::TESGlobal* a_global, float a_mod)
	{
		if (a_global)
			a_global->value -= a_mod;
	}

	void ModValue(ActorValue a_av, float a_mod)
	{
		if (auto player = RE::PlayerCharacter::GetSingleton())
			player->AsActorValueOwner()->ModBaseActorValue(ConvertActorValue(a_av), a_mod);
		UpdateActorValue(a_av);
	}

private:
	void IncreaseLearningSkill(ActorValue a_av, std::int32_t a_cost)
	{
		if (!MCM::GetSingleton()->QIgnoreLearningGold())
			ModGold(a_cost);
		if (!MCM::GetSingleton()->QIgnoreLearningPoints())
			ModGlobal(LearningPoints, 1.0f);
		ModValue(a_av, 1.0f);
		UpdateMenu();
	}

	void IncreaseCraftingSkill(ActorValue a_av, std::int32_t a_cost)
	{
		if (!MCM::GetSingleton()->QIgnoreCraftingGold())
			ModGold(a_cost);
		if (!MCM::GetSingleton()->QIgnoreCraftingPoints())
			ModGlobal(CraftingPoints, 1.0f);
		ModValue(a_av, 1.0f);
		UpdateMenu();
	}

public:
	void IncreaseSkill(ActorValue a_av, std::int32_t a_cost)
	{
		switch (a_av)
		{
		case kOneHanded:
		case kTwoHanded:
		case kMarksman:
		case kBlock:
		case kHeavyArmor:
		case kLightArmor:
		case kSneak:
		case kMentalism:
		case kEntropy:
		case kElementalism:
		case kPsionics:
		case kLightMagic:
			IncreaseLearningSkill(a_av, a_cost);
			break;
		case kHandicraft:
		case kSlightOfHand:
		case kLockpicking:
		case kAlchemy:
		case kRhetoric:
		case kEnchanting:
			IncreaseCraftingSkill(a_av, a_cost);
			break;
		}
	}

private:
	// clang-format off
	void RequestCallback(ActorValue a_av, std::int32_t a_cost, bool a_crafting)
	{
		// ZP: with no gold cost, leave the price and pennies out of the prompt
		const bool ignoreGold = a_crafting ? MCM::GetSingleton()->QIgnoreCraftingGold() : MCM::GetSingleton()->QIgnoreLearningGold();
		const auto points = a_crafting ? GetGlobalValue(kCraftingPoints) : GetGlobalValue(kLearningPoints);
		auto       text = ignoreGold ?
		                      std::format(
								  "Do you want to increase {0}?\n\nCost: 1 {1}\n\nCurrent {1}: {2}"sv,
								  GetActorValueName(a_av),
								  GetPointName(a_crafting),
								  points) :
		                      std::format(
								  "Do you want to increase {0}?\n\nPrice: {1}p, 1 {2}\n\nCurrent Pennies: {3}\n Current {2}: {4}"sv,
								  GetActorValueName(a_av),
								  a_cost,
								  GetPointName(a_crafting),
								  playerGold,
								  points);

		RE::BSString message{ text };
		RE::BSTSmartPointer<RE::IMessageBoxCallback> call{ new HeroMessageBoxCallback(a_av, a_cost) };
		RE::MessageBoxMenu::Create(message, call, 0, 25, 10, HeroMessageBoxCallback::Buttons);
	}
	// clang-format on

	void TryIncreaseLearningSkill(ActorValue a_av)
	{
		auto cost = GetGoldCost(a_av);
		if (!MCM::GetSingleton()->QIgnoreLearningGold() &&
			cost > playerGold)
		{
			auto message = std::format(
				"You do not have enough pennies to increase {0}! (Price: {1}p)"sv,
				GetActorValueName(a_av),
				cost);
			RE::SendHUDMessage::ShowHUDMessage(message.c_str());
			return;
		}

		if (!MCM::GetSingleton()->QIgnoreLearningPoints() &&
			!GetGlobalValue(kLearningPoints))
		{
			auto message = std::format(
				"You do not have enough {0} to increase {1}!"sv,
				GetPointName(false),
				GetActorValueName(a_av));
			RE::SendHUDMessage::ShowHUDMessage(message.c_str());
			return;
		}

		if (!MCM::GetSingleton()->QSkipCallback())
			RequestCallback(a_av, cost, false);
		else
			IncreaseLearningSkill(a_av, cost);
	}

	void TryIncreaseCraftingSkill(ActorValue a_av)
	{
		auto cost = GetGoldCost(a_av);
		if (!MCM::GetSingleton()->QIgnoreCraftingGold() &&
			cost > playerGold)
		{
			auto message = std::format(
				"You do not have enough pennies to increase {0}! (Price: {1}p)"sv,
				GetActorValueName(a_av),
				cost);
			RE::SendHUDMessage::ShowHUDMessage(message.c_str());
			return;
		}

		if (!MCM::GetSingleton()->QIgnoreCraftingPoints() &&
			!GetGlobalValue(kCraftingPoints))
		{
			auto message = std::format(
				"You do not have enough {0} to increase {1}!"sv,
				GetPointName(true),
				GetActorValueName(a_av));
			RE::SendHUDMessage::ShowHUDMessage(message.c_str());
			return;
		}

		if (!MCM::GetSingleton()->QSkipCallback())
			RequestCallback(a_av, cost, true);
		else
			IncreaseCraftingSkill(a_av, cost);
	}

public:
	void TryIncreaseSkill(ActorValue a_av)
	{
		if (MCM::GetSingleton()->QDisableOutsideCities())
		{
			if (auto player = RE::PlayerCharacter::GetSingleton())
			{
				if (auto location = player->GetCurrentLocation();
					location && !location->HasKeyword(NoTransformTown))
				{
					auto message = std::format("You cannot raise your skills in the wilderness."sv);
					RE::SendHUDMessage::ShowHUDMessage(message.c_str());
					return;
				}
			}
		}

		if (GetBaseActorValue(a_av) >= 100.0f)
		{
			auto message = std::format(
				"You cannot increase {0} further.",
				GetActorValueName(a_av));
			RE::SendHUDMessage::ShowHUDMessage(message.c_str());
			return;
		}

		switch (a_av)
		{
		case kOneHanded:
		case kTwoHanded:
		case kMarksman:
		case kBlock:
		case kHeavyArmor:
		case kLightArmor:
		case kSneak:
		case kMentalism:
		case kEntropy:
		case kElementalism:
		case kPsionics:
		case kLightMagic:
			TryIncreaseLearningSkill(a_av);
			break;
		case kHandicraft:
		case kSlightOfHand:
		case kLockpicking:
		case kAlchemy:
		case kRhetoric:
		case kEnchanting:
			TryIncreaseCraftingSkill(a_av);
			break;
		}
	}

	void TryIncreaseSkill(std::int32_t a_av)
	{
		TryIncreaseSkill(static_cast<ActorValue>(a_av));
	}

private:
	void UpdateMenuName()
	{
		if (!MCM::GetSingleton()->QShowPenniesInMenu())
			playerMenu = playerName;
		else
			playerMenu = std::format("{0} / {1}: {2}", playerName, GetGoldName(), playerGold);
	}

public:
	void UpdateMenuName(RE::GPtr<RE::GFxMovieView>& a_view)
	{
		UpdateMenuName();
		{
			RE::GFxValue args[2];
			args[0] = playerMenu;
			args[1] = playerClass;
			a_view->Invoke("heromenu_mc.SetStringValues", nullptr, args, 2);
		}
	}

private:
	auto CalculateNeededExpPoints(float a_level, float a_slope, float a_mult, float a_expAcc = 1.0f, float a_expAcc20 = 1.2f, float a_expAcc30 = 1.5f, float a_expAcc40 = 2.0f)
	{
		auto result = powf(std::min(a_level, 20.0f), a_slope) * a_mult * a_expAcc;
		if (a_level <= 20)
			return result;

		result += (powf(std::min(a_level, 30.0f), a_slope) - powf(20.0f, a_slope)) * a_mult * a_expAcc * a_expAcc20;
		if (a_level <= 30)
			return result;

		result += (powf(std::min(a_level, 40.0f), a_slope) - powf(30.0f, a_slope)) * a_mult * a_expAcc * a_expAcc30;
		if (a_level <= 40)
			return result;

		result += (powf(a_level, a_slope) - powf(40.0f, a_slope)) * a_mult * a_expAcc * a_expAcc40;
		return result;
	}

private:
	void UpdateMenu()
	{
		auto ui = RE::UI::GetSingleton();
		if (!ui)
			return;

		auto view = ui->GetMovieView(ZP::HeroMenuName);
		if (!view)
			return;

		// SetStringValues
		UpdateMenuName(view);

		// SetIntValues
		{
			RE::GFxValue args[33];

			auto expNeededForNextLevel = CalculateNeededExpPoints(GetGlobalValue(Global::kPlayerLevel), GetGlobalValue(Global::kExpMultSlope), GetGlobalValue(Global::kExpMult));
			auto expNeededForThisLevel = CalculateNeededExpPoints(GetGlobalValue(Global::kPlayerLevel) - 1, GetGlobalValue(Global::kExpMultSlope), GetGlobalValue(Global::kExpMult));

			// Health
			args[0] = GetBaseActorValue(kHealth);
			args[1] = GetActorValue(kHealth);

			// Mana
			args[2] = GetBaseActorValue(kMana);
			args[3] = GetActorValue(kMana);

			// Stamina
			args[4] = GetBaseActorValue(kStamina);
			args[5] = GetActorValue(kStamina);

			// Arcane Fever
			args[6] = -GetActorValue(kArcaneFever);

			// Globals
			args[7] = expNeededForNextLevel;
			args[8] = GetGlobalValue(kPlayerXP);
			args[9] = GetGlobalValue(kPlayerLevel);
			args[10] = GetGlobalValue(kLearningPoints);
			args[11] = GetGlobalValue(kCraftingPoints);
			args[12] = GetGlobalValue(kTalentPoints);

			// Skills
			args[13] = GetBaseActorValue(kPsionics);
			args[14] = GetBaseActorValue(kElementalism);
			args[15] = GetBaseActorValue(kMentalism);
			args[16] = GetBaseActorValue(kOneHanded);
			args[17] = GetBaseActorValue(kBlock);
			args[18] = GetBaseActorValue(kMarksman);
			args[19] = GetBaseActorValue(kEntropy);
			args[20] = GetBaseActorValue(kLightMagic);
			args[21] = GetBaseActorValue(kTwoHanded);
			args[22] = GetBaseActorValue(kLightArmor);
			args[23] = GetBaseActorValue(kHeavyArmor);
			args[24] = GetBaseActorValue(kSneak);
			args[25] = GetBaseActorValue(kAlchemy);
			args[26] = GetBaseActorValue(kSlightOfHand);
			args[27] = GetBaseActorValue(kLockpicking);
			args[28] = GetBaseActorValue(kEnchanting);
			args[29] = GetBaseActorValue(kHandicraft);
			args[30] = GetBaseActorValue(kRhetoric);

			// XP
			args[31] = GetGlobalValue(kPlayerXP) - expNeededForThisLevel;
			args[32] = expNeededForNextLevel - expNeededForThisLevel;
			view->Invoke("heromenu_mc.SetIntValues", nullptr, args, 33);
		}

		// SetModifier
		{
			RE::GFxValue args[21];
			// Attributes
			args[0] = GetActorValueMod(kHealth);
			args[1] = GetActorValueMod(kMana);
			args[2] = GetActorValueMod(kStamina);

			// Skills
			args[3] = GetActorValueMod(kPsionics);
			args[4] = GetActorValueMod(kElementalism);
			args[5] = GetActorValueMod(kMentalism);
			args[6] = GetActorValueMod(kOneHanded);
			args[7] = GetActorValueMod(kBlock);
			args[8] = GetActorValueMod(kMarksman);
			args[9] = GetActorValueMod(kEntropy);
			args[10] = GetActorValueMod(kLightMagic);
			args[11] = GetActorValueMod(kTwoHanded);
			args[12] = GetActorValueMod(kLightArmor);
			args[13] = GetActorValueMod(kHeavyArmor);
			args[14] = GetActorValueMod(kSneak);
			args[15] = GetActorValueMod(kAlchemy);
			args[16] = GetActorValueMod(kSlightOfHand);
			args[17] = GetActorValueMod(kLockpicking);
			args[18] = GetActorValueMod(kEnchanting);
			args[19] = GetActorValueMod(kHandicraft);
			args[20] = GetActorValueMod(kRhetoric);
			view->Invoke("heromenu_mc.SetModifier", nullptr, args, 21);
		}
	}

private:
	void LoadBookValues(RE::TESDataHandler* a_data)
	{
		for (auto i = 0; i < SkillTotal; i++)
		{
			for (auto j = 0; j < LevelTotal; j++)
			{
				auto& [formID, file] = bookForms[i][j];
				if (auto form = a_data->LookupForm(formID, file))
					bookCost[i][j] = form->GetGoldValue();
			}
		}
	}

private:
	void LoadAffinityNames(RE::TESDataHandler* a_data)
	{
		for (auto i = 0; i < AffinityTotal; i++)
		{
			for (auto j = 0; j < GenderTotal; j++)
			{
				auto& [formID, file] = affinityForms[i][j];
				if (auto form = a_data->LookupForm(formID, file))
					affinityName[i][j] = form->GetName();
			}
		}
	}

private:
	void LoadClassNames(RE::TESDataHandler* a_data)
	{
		for (auto i = 0; i < ClassTotal; i++)
		{
			for (auto j = 0; j < GenderTotal; j++)
			{
				auto& [formID, file] = classForms[i][j];
				if (auto form = a_data->LookupForm(formID, file))
					className[i][j] = form->GetName();
			}
		}
	}

private:
	// clang-format off
	void LoadForms(RE::TESDataHandler* a_data)
	{
		NoTransformTown = a_data->LookupForm<RE::BGSKeyword>(0x02EAA6, "Enderal - Forgotten Stories.esm"sv);
		Seducer         = a_data->LookupForm<RE::BGSPerk>(0x069D3D, "Skyrim.esm"sv);
		Mesmerize01     = a_data->LookupForm<RE::SpellItem>(0x01EFDA, "Enderal - Forgotten Stories.esm"sv);
		Mesmerize02     = a_data->LookupForm<RE::SpellItem>(0x01EFDD, "Enderal - Forgotten Stories.esm"sv);
		Mesmerize03     = a_data->LookupForm<RE::SpellItem>(0x01EFDE, "Enderal - Forgotten Stories.esm"sv);
		EXPMult         = a_data->LookupForm<RE::TESGlobal>(0x008D2B, "Skyrim.esm"sv);
		EXPMultSlope    = a_data->LookupForm<RE::TESGlobal>(0x0D0EDB, "Skyrim.esm"sv);
		PlayerXP        = a_data->LookupForm<RE::TESGlobal>(0x012596, "Skyrim.esm"sv);
		PlayerNeededXP  = a_data->LookupForm<RE::TESGlobal>(0x027CD1, "Skyrim.esm"sv);
		PlayerLevel     = a_data->LookupForm<RE::TESGlobal>(0x012595, "Skyrim.esm"sv);
		CraftingPoints  = a_data->LookupForm<RE::TESGlobal>(0x085A79, "Skyrim.esm"sv);
		LearningPoints  = a_data->LookupForm<RE::TESGlobal>(0x031ACB, "Skyrim.esm"sv);
		TalentPoints    = a_data->LookupForm<RE::TESGlobal>(0x05BCFA, "Skyrim.esm"sv);
		Gold001         = a_data->LookupForm<RE::TESObjectMISC>(0x00000F, "Skyrim.esm"sv);
		AffinityQuest   = a_data->LookupForm<RE::TESQuest>(0x010AA2, "Skyrim.esm"sv);  // ZP: Levelsystem (2.1.x: 01597B:FS)
	}
	// clang-format on

private:
	float        actorValue[ActorValueTotal][IndexTotal]{};
	std::string  className[ClassTotal][GenderTotal]{};
	std::string  affinityName[AffinityTotal][GenderTotal]{};
	std::int32_t bookCost[SkillTotal][LevelTotal]{};

private:
	std::string  playerName{};
	std::int32_t playerGender{};
	std::int32_t playerGold{};
	std::string  playerMenu{};
	std::string  playerClass{};
	std::int32_t playerClassIndex{ -1 };
	std::int32_t playerClassMajor{};
	std::int32_t playerClassMinor{};

private:
	bool overrideMessage{ false };

private:
	RE::BGSKeyword*    NoTransformTown{ nullptr };
	RE::BGSPerk*       Seducer{ nullptr };
	RE::SpellItem*     Mesmerize01{ nullptr };
	RE::SpellItem*     Mesmerize02{ nullptr };
	RE::SpellItem*     Mesmerize03{ nullptr };
	RE::TESGlobal*     EXPMult{ nullptr };
	RE::TESGlobal*     EXPMultSlope{ nullptr };
	RE::TESGlobal*     PlayerXP{ nullptr };
	RE::TESGlobal*     PlayerNeededXP{ nullptr };
	RE::TESGlobal*     PlayerLevel{ nullptr };
	RE::TESGlobal*     CraftingPoints{ nullptr };
	RE::TESGlobal*     LearningPoints{ nullptr };
	RE::TESGlobal*     TalentPoints{ nullptr };
	RE::TESObjectMISC* Gold001{ nullptr };
	RE::TESQuest*      AffinityQuest{ nullptr };

private:
	using FormID = std::pair<std::uint32_t, std::string_view>;

	static constexpr std::array<std::array<FormID, LevelTotal>, SkillTotal> bookForms{
		std::array<FormID, LevelTotal>{ std::make_pair(0x031ACC, "Skyrim.esm"sv), std::make_pair(0x031ACE, "Skyrim.esm"sv), std::make_pair(0x033A5F, "Skyrim.esm"sv), std::make_pair(0x039935, "Skyrim.esm"sv) }, // kOneHanded
		std::array<FormID, LevelTotal>{ std::make_pair(0x039936, "Skyrim.esm"sv), std::make_pair(0x039937, "Skyrim.esm"sv), std::make_pair(0x039938, "Skyrim.esm"sv), std::make_pair(0x039939, "Skyrim.esm"sv) }, // kTwoHanded
		std::array<FormID, LevelTotal>{ std::make_pair(0x085641, "Skyrim.esm"sv), std::make_pair(0x085643, "Skyrim.esm"sv), std::make_pair(0x085644, "Skyrim.esm"sv), std::make_pair(0x085642, "Skyrim.esm"sv) }, // kMarksman
		std::array<FormID, LevelTotal>{ std::make_pair(0x039941, "Skyrim.esm"sv), std::make_pair(0x039942, "Skyrim.esm"sv), std::make_pair(0x039943, "Skyrim.esm"sv), std::make_pair(0x039944, "Skyrim.esm"sv) }, // kBlock
		std::array<FormID, LevelTotal>{ std::make_pair(0x0E7632, "Skyrim.esm"sv), std::make_pair(0x0E7633, "Skyrim.esm"sv), std::make_pair(0x0E7634, "Skyrim.esm"sv), std::make_pair(0x0E7635, "Skyrim.esm"sv) }, // kHandicraft
		std::array<FormID, LevelTotal>{ std::make_pair(0x03F86A, "Skyrim.esm"sv), std::make_pair(0x03F86B, "Skyrim.esm"sv), std::make_pair(0x03F86C, "Skyrim.esm"sv), std::make_pair(0x03F86D, "Skyrim.esm"sv) }, // kHeavyArmor
		std::array<FormID, LevelTotal>{ std::make_pair(0x0E75F3, "Skyrim.esm"sv), std::make_pair(0x0E75F4, "Skyrim.esm"sv), std::make_pair(0x0E75F0, "Skyrim.esm"sv), std::make_pair(0x0E75F2, "Skyrim.esm"sv) }, // kLightArmor
		std::array<FormID, LevelTotal>{ std::make_pair(0x0E762E, "Skyrim.esm"sv), std::make_pair(0x0E762F, "Skyrim.esm"sv), std::make_pair(0x0E7630, "Skyrim.esm"sv), std::make_pair(0x0E7631, "Skyrim.esm"sv) }, // kSlightOfHand
		std::array<FormID, LevelTotal>{ std::make_pair(0x0E762A, "Skyrim.esm"sv), std::make_pair(0x0E762B, "Skyrim.esm"sv), std::make_pair(0x0E762C, "Skyrim.esm"sv), std::make_pair(0x0E762D, "Skyrim.esm"sv) }, // kLockpicking
		std::array<FormID, LevelTotal>{ std::make_pair(0x0E7636, "Skyrim.esm"sv), std::make_pair(0x0E7637, "Skyrim.esm"sv), std::make_pair(0x0E7638, "Skyrim.esm"sv), std::make_pair(0x0E7639, "Skyrim.esm"sv) }, // kSneak
		std::array<FormID, LevelTotal>{ std::make_pair(0x0E7622, "Skyrim.esm"sv), std::make_pair(0x0E7623, "Skyrim.esm"sv), std::make_pair(0x0E7624, "Skyrim.esm"sv), std::make_pair(0x0E7625, "Skyrim.esm"sv) }, // kAlchemy
		std::array<FormID, LevelTotal>{ std::make_pair(0x08591F, "Skyrim.esm"sv), std::make_pair(0x08591E, "Skyrim.esm"sv), std::make_pair(0x08591D, "Skyrim.esm"sv), std::make_pair(0x08591B, "Skyrim.esm"sv) }, // kRhetoric
		std::array<FormID, LevelTotal>{ std::make_pair(0x085618, "Skyrim.esm"sv), std::make_pair(0x085619, "Skyrim.esm"sv), std::make_pair(0x08561A, "Skyrim.esm"sv), std::make_pair(0x08561B, "Skyrim.esm"sv) }, // kMentalism
		std::array<FormID, LevelTotal>{ std::make_pair(0x085621, "Skyrim.esm"sv), std::make_pair(0x085622, "Skyrim.esm"sv), std::make_pair(0x085620, "Skyrim.esm"sv), std::make_pair(0x085623, "Skyrim.esm"sv) }, // kEntropy
		std::array<FormID, LevelTotal>{ std::make_pair(0x085614, "Skyrim.esm"sv), std::make_pair(0x085615, "Skyrim.esm"sv), std::make_pair(0x085616, "Skyrim.esm"sv), std::make_pair(0x085617, "Skyrim.esm"sv) }, // kElementalism
		std::array<FormID, LevelTotal>{ std::make_pair(0x08561C, "Skyrim.esm"sv), std::make_pair(0x08561D, "Skyrim.esm"sv), std::make_pair(0x08561E, "Skyrim.esm"sv), std::make_pair(0x08561F, "Skyrim.esm"sv) }, // kPsionics
		std::array<FormID, LevelTotal>{ std::make_pair(0x085624, "Skyrim.esm"sv), std::make_pair(0x085625, "Skyrim.esm"sv), std::make_pair(0x085626, "Skyrim.esm"sv), std::make_pair(0x085627, "Skyrim.esm"sv) }, // kLightMagic
		std::array<FormID, LevelTotal>{ std::make_pair(0x0E7626, "Skyrim.esm"sv), std::make_pair(0x0E7627, "Skyrim.esm"sv), std::make_pair(0x0E7628, "Skyrim.esm"sv), std::make_pair(0x0E7629, "Skyrim.esm"sv) }, // kEnchanting
	};

	static constexpr std::array<std::array<FormID, GenderTotal>, ClassTotal> classForms{
		std::array<FormID, GenderTotal>{ std::make_pair(0x042A8B, "Skyrim.esm"sv),                      std::make_pair(0x042A7A, "Skyrim.esm"sv)                      }, // kNone
		std::array<FormID, GenderTotal>{ std::make_pair(0x042A84, "Skyrim.esm"sv),                      std::make_pair(0x042A7B, "Skyrim.esm"sv)                      }, // kBastion
		std::array<FormID, GenderTotal>{ std::make_pair(0x042A85, "Skyrim.esm"sv),                      std::make_pair(0x042A7C, "Skyrim.esm"sv)                      }, // kDerwish
		std::array<FormID, GenderTotal>{ std::make_pair(0x042A86, "Skyrim.esm"sv),                      std::make_pair(0x042A7D, "Skyrim.esm"sv)                      }, // kElementalist
		std::array<FormID, GenderTotal>{ std::make_pair(0x042A87, "Skyrim.esm"sv),                      std::make_pair(0x042A7E, "Skyrim.esm"sv)                      }, // kEspionage
		std::array<FormID, GenderTotal>{ std::make_pair(0x042A89, "Skyrim.esm"sv),                      std::make_pair(0x042A7F, "Skyrim.esm"sv)                      }, // kLifeAndDeath
		std::array<FormID, GenderTotal>{ std::make_pair(0x042A8A, "Skyrim.esm"sv),                      std::make_pair(0x042A80, "Skyrim.esm"sv)                      }, // kManipulation
		std::array<FormID, GenderTotal>{ std::make_pair(0x042AA1, "Skyrim.esm"sv),                      std::make_pair(0x042A81, "Skyrim.esm"sv)                      }, // kRage
		std::array<FormID, GenderTotal>{ std::make_pair(0x042AA2, "Skyrim.esm"sv),                      std::make_pair(0x042A82, "Skyrim.esm"sv)                      }, // kTrickery
		std::array<FormID, GenderTotal>{ std::make_pair(0x042AA3, "Skyrim.esm"sv),                      std::make_pair(0x042A83, "Skyrim.esm"sv)                      }, // kVagabond
		std::array<FormID, GenderTotal>{ std::make_pair(0x044EEB, "Skyrim.esm"sv),                      std::make_pair(0x044EED, "Skyrim.esm"sv)                      }, // kPhasmalist
		std::array<FormID, GenderTotal>{ std::make_pair(0x02F188, "Enderal - Forgotten Stories.esm"sv), std::make_pair(0x02F189, "Enderal - Forgotten Stories.esm"sv) }, // kTheriantrophist
	};

	static constexpr std::array<std::array<FormID, GenderTotal>, AffinityTotal> affinityForms{
		std::array<FormID, GenderTotal>{ std::make_pair(0x042A8C, "Skyrim.esm"sv),                      std::make_pair(0x042A99, "Skyrim.esm"sv)                      }, // kBattlemage
		std::array<FormID, GenderTotal>{ std::make_pair(0x042A8D, "Skyrim.esm"sv),                      std::make_pair(0x042A9D, "Skyrim.esm"sv)                      }, // kCleric
		std::array<FormID, GenderTotal>{ std::make_pair(0x042A8E, "Skyrim.esm"sv),                      std::make_pair(0x042A98, "Skyrim.esm"sv)                      }, // kAssassin
		std::array<FormID, GenderTotal>{ std::make_pair(0x042A90, "Skyrim.esm"sv),                      std::make_pair(0x042AA0, "Skyrim.esm"sv)                      }, // kWayfarer
		std::array<FormID, GenderTotal>{ std::make_pair(0x042A91, "Skyrim.esm"sv),                      std::make_pair(0x042A9A, "Skyrim.esm"sv)                      }, // kBlackMage
		std::array<FormID, GenderTotal>{ std::make_pair(0x042A92, "Skyrim.esm"sv),                      std::make_pair(0x042A9E, "Skyrim.esm"sv)                      }, // kDarkKeeper
		std::array<FormID, GenderTotal>{ std::make_pair(0x042A93, "Skyrim.esm"sv),                      std::make_pair(0x042A9C, "Skyrim.esm"sv)                      }, // kFencer
		std::array<FormID, GenderTotal>{ std::make_pair(0x042A94, "Skyrim.esm"sv),                      std::make_pair(0x042A9B, "Skyrim.esm"sv)                      }, // kBladebreaker
		std::array<FormID, GenderTotal>{ std::make_pair(0x042A95, "Skyrim.esm"sv),                      std::make_pair(0x042A9F, "Skyrim.esm"sv)                      }, // kShadowdancer
		std::array<FormID, GenderTotal>{ std::make_pair(0x042A96, "Skyrim.esm"sv),                      std::make_pair(0x042A97, "Skyrim.esm"sv)                      }, // kArcaneArcher
		std::array<FormID, GenderTotal>{ std::make_pair(0x042A8B, "Skyrim.esm"sv),                      std::make_pair(0x042A7A, "Skyrim.esm"sv)                      }, // kWanderingMage
		std::array<FormID, GenderTotal>{ std::make_pair(0x029A35, "Enderal - Forgotten Stories.esm"sv), std::make_pair(0x044EEE, "Skyrim.esm"sv)                      }, // kSpectralist
		std::array<FormID, GenderTotal>{ std::make_pair(0x044EF3, "Skyrim.esm"sv),                      std::make_pair(0x029A34, "Enderal - Forgotten Stories.esm"sv) }, // kGhostBlade
		std::array<FormID, GenderTotal>{ std::make_pair(0x02F178, "Enderal - Forgotten Stories.esm"sv), std::make_pair(0x02F179, "Enderal - Forgotten Stories.esm"sv) }, // kSpectralWarrior
		std::array<FormID, GenderTotal>{ std::make_pair(0x02F17A, "Enderal - Forgotten Stories.esm"sv), std::make_pair(0x02F17B, "Enderal - Forgotten Stories.esm"sv) }, // kBrute
		std::array<FormID, GenderTotal>{ std::make_pair(0x02F17C, "Enderal - Forgotten Stories.esm"sv), std::make_pair(0x02F17D, "Enderal - Forgotten Stories.esm"sv) }, // kDrifter
		std::array<FormID, GenderTotal>{ std::make_pair(0x02F17E, "Enderal - Forgotten Stories.esm"sv), std::make_pair(0x02F17F, "Enderal - Forgotten Stories.esm"sv) }, // kDruid
		std::array<FormID, GenderTotal>{ std::make_pair(0x02F180, "Enderal - Forgotten Stories.esm"sv), std::make_pair(0x02F181, "Enderal - Forgotten Stories.esm"sv) }, // kNightwolf
		std::array<FormID, GenderTotal>{ std::make_pair(0x02F182, "Enderal - Forgotten Stories.esm"sv), std::make_pair(0x02F183, "Enderal - Forgotten Stories.esm"sv) }, // kRavager
		std::array<FormID, GenderTotal>{ std::make_pair(0x02F184, "Enderal - Forgotten Stories.esm"sv), std::make_pair(0x02F185, "Enderal - Forgotten Stories.esm"sv) }, // kScourgeOfTheWilds
		std::array<FormID, GenderTotal>{ std::make_pair(0x02F187, "Enderal - Forgotten Stories.esm"sv), std::make_pair(0x02F186, "Enderal - Forgotten Stories.esm"sv) }, // kSoulcaller
	};
};
