#pragma once

class Translator :
	public REX::Singleton<Translator>
{
public:
	void Load()
	{
		LoadTranslations();
	}

	std::string_view GetActorValueName(std::int32_t a_av) const
	{
		return actorValue[a_av];
	}

	std::string_view GetGoldName() const
	{
		return gold;
	}

	std::string_view GetPointName(bool a_craft) const
	{
		return point[a_craft];
	}

private:
	void LoadTranslation(RE::BSScaleformTranslator* a_trns, const wchar_t* a_key, std::string& a_output)
	{
		RE::GFxTranslator::TranslateInfo info;
		RE::GFxWStringBuffer             buffer;

		info.key = a_key;
		info.result = std::addressof(buffer);
		a_trns->Translate(std::addressof(info));

		a_output.resize(512);
		sprintf_s(a_output.data(), 512, "%ws", buffer.c_str());
		a_output.resize(buffer.size() - 1);
	}

	void LoadTranslations()
	{
		if (auto manager = RE::BSScaleformManager::GetSingleton();
			manager && manager->loader)
		{
			if (auto translator = manager->loader->GetState<RE::BSScaleformTranslator>(RE::GFxState::StateType::kTranslator))
			{
				// ActorValues
				LoadTranslation(translator.get(), L"$00E_EINHANDDESCRTITEL", actorValue[0]);           // OneHanded
				LoadTranslation(translator.get(), L"$00E_ZWEIHANDDESCRTITEL", actorValue[1]);          // TwoHanded
				LoadTranslation(translator.get(), L"$00E_BOGENKUNSTDESCRTITEL", actorValue[2]);        // Archery
				LoadTranslation(translator.get(), L"$00E_PARADEDESCRTITEL", actorValue[3]);            // Block
				LoadTranslation(translator.get(), L"$00E_SCHMIEDENDESCRTITEL", actorValue[4]);         // Smithing
				LoadTranslation(translator.get(), L"$00E_SCHWERERUESTUNGDESCRTITEL", actorValue[5]);   // HeavyArmor
				LoadTranslation(translator.get(), L"$00E_LEICHTERUESTUNGDESCRTITEL", actorValue[6]);   // LightArmor
				LoadTranslation(translator.get(), L"$00E_TASCHENDIEBSTAHLDESCRTITEL", actorValue[7]);  // Pickpocket
				LoadTranslation(translator.get(), L"$00E_SCHLOSSKNACKENDESCRTITEL", actorValue[8]);    // Lockpicking
				LoadTranslation(translator.get(), L"$00E_SCHLEICHENDESCRTITEL", actorValue[9]);        // Sneak
				LoadTranslation(translator.get(), L"$00E_ALCHIMIEDESCRTITEL", actorValue[10]);         // Alchemy
				LoadTranslation(translator.get(), L"$00E_RETHORIKDESCRTITEL", actorValue[11]);         // Speech
				LoadTranslation(translator.get(), L"$00E_MENTALISMUSDESCRTITEL", actorValue[12]);      // Alteration
				LoadTranslation(translator.get(), L"$00E_ENTROPIEDESCRTITEL", actorValue[13]);         // Conjuration
				LoadTranslation(translator.get(), L"$00E_ELEMENTARISMUSDESCRTITEL", actorValue[14]);   // Destruction
				LoadTranslation(translator.get(), L"$00E_PSIONIKDESCRTITEL", actorValue[15]);          // Illusion
				LoadTranslation(translator.get(), L"$00E_LICHTMAGIEDESCRTITEL", actorValue[16]);       // Restoration
				LoadTranslation(translator.get(), L"$00E_VERZAUBERUNGDESCRTITEL", actorValue[17]);     // Enchanting

				// Gold
				LoadTranslation(translator.get(), L"$Gold", gold);

				// Points
				LoadTranslation(translator.get(), L"$00E_LERNPUNKTEDESCRTITEL", point[0]);       // Learning Points
				LoadTranslation(translator.get(), L"$00E_HANDWERKSPUNKTEDESCRTITEL", point[1]);  // Crafting Points
			}
		}
	}

private:
	std::string actorValue[18]{};
	std::string gold{};
	std::string point[2]{};
};
