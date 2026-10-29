#include "pch.h"

#include <atomic>
#include <chrono>
#include <thread>

// Testing tool, not part of the list. In Prophecy's Force of Nature the player turns into Triumvirate's Horned Lord
// race (TVR_Verdant_Race_ForceOfNature 000837) and has no body at all - no shadow - while an NPC set to the same race
// shows it (curator, 2026-10-28). Guesses (mesh format, armour, skeleton, sex) all failed, so this reads what the game
// actually built. Every 2 s, on the main thread, while the player is that race it logs (twice per change: on seeing
// it and 3 s later):
//   - the race's skin and skeleton path for the player's sex, the actor base's own skin;
//   - every biped slot with an item: the item, the addon and whether its part was attached (partClone);
//   - the third- and first-person 3D trees: each node's type, name, hidden (AppCulled) flag, local scale.
// Log: My Games/Skyrim Special Edition/SKSE/ZenPlayer3DTrace.log

SKSEPluginInfo(
	.Version = REL::Version{ 1, 0, 0, 0 },
	.Name = "ZenPlayer3DTrace"sv,
	.Author = "Zenderal"sv,
	.StructCompatibility = SKSE::StructCompatibility::Independent,
	.RuntimeCompatibility = SKSE::VersionIndependence::AddressLibrary)

namespace
{
	constexpr int kMaxLines = 600;

	std::atomic<bool> g_busy{ false };
	RE::TESRace*      g_target{ nullptr };
	RE::TESRace*      g_lastRace{ nullptr };
	int               g_dumpsForThisRace{ 0 };
	std::int64_t      g_seenAt{ 0 };
	int               g_lines{ 0 };

	std::int64_t NowMs()
	{
		static const auto start = std::chrono::steady_clock::now();
		return std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - start).count();
	}

	std::string FormStr(const RE::TESForm* a_form)
	{
		if (!a_form) {
			return "none";
		}
		const char* name = a_form->GetName();
		return std::format("{:08X} '{}'", a_form->GetFormID(), name ? name : "");
	}

	void Walk(RE::NiAVObject* a_obj, int a_depth)
	{
		if (!a_obj || g_lines >= kMaxLines) {
			return;
		}
		++g_lines;
		const auto* rtti = a_obj->GetRTTI();
		const auto  name = a_obj->name.c_str();
		SKSE::log::info("{:{}}{} '{}'{} scale {:.3f}{}", "", a_depth * 2, rtti ? rtti->GetName() : "?", name ? name : "",
			a_obj->GetAppCulled() ? " HIDDEN" : "", a_obj->local.scale, a_obj->AsGeometry() ? " GEOMETRY" : "");
		if (auto* node = a_obj->AsNode()) {
			for (auto& child : node->GetChildren()) {
				Walk(child.get(), a_depth + 1);
			}
		}
	}

	void Dump(RE::PlayerCharacter* a_player, const char* a_why)
	{
		g_lines = 0;
		auto*      base = a_player->GetActorBase();
		auto*      race = a_player->GetRace();
		const auto sex = base ? base->GetSex() : RE::SEX::kMale;
		SKSE::log::info("==== {} ms: {} ====", NowMs(), a_why);
		SKSE::log::info("race {} sex {} skin(race) {} skin(actor base) {} skeleton '{}'", FormStr(race),
			static_cast<int>(sex), FormStr(race ? race->skin : nullptr), FormStr(base ? base->skin : nullptr),
			race && sex <= RE::SEX::kFemale ? race->skeletonModels[sex].GetModel() : "?");
		for (const bool first : { false, true }) {
			const auto& biped = a_player->GetBiped(first);
			if (!biped) {
				SKSE::log::info("{} biped: none", first ? "1st" : "3rd");
				continue;
			}
			for (int i = 0; i < RE::BIPED_OBJECTS::kTotal; ++i) {
				const auto& o = biped->objects[i];
				if (o.item || o.addon) {
					SKSE::log::info("{} slot {:2}: item {} addon {} model '{}' attached {}", first ? "1st" : "3rd", i,
						FormStr(o.item), FormStr(o.addon), o.part ? o.part->GetModel() : "", o.partClone ? "yes" : "NO");
				}
			}
		}
		for (const bool first : { false, true }) {
			auto* root = a_player->Get3D(first);
			SKSE::log::info("--- {}-person 3D: {}", first ? "first" : "third", root ? "" : "NONE");
			Walk(root, 1);
		}
		if (g_lines >= kMaxLines) {
			SKSE::log::info("(tree cut at {} lines)", kMaxLines);
		}
	}

	void Check()
	{
		auto* player = RE::PlayerCharacter::GetSingleton();
		if (!player || !g_target) {
			return;
		}
		auto* race = player->GetRace();
		if (race != g_lastRace) {
			SKSE::log::info("{} ms: player race now {}", NowMs(), FormStr(race));
			g_lastRace = race;
			g_dumpsForThisRace = 0;
			g_seenAt = NowMs();
		}
		if (race != g_target) {
			return;
		}
		if (g_dumpsForThisRace == 0) {
			Dump(player, "Horned Lord race seen");
			g_dumpsForThisRace = 1;
		} else if (g_dumpsForThisRace == 1 && NowMs() - g_seenAt >= 3000) {
			Dump(player, "3 s later");
			g_dumpsForThisRace = 2;
		}
	}

	void Loop()
	{
		for (;;) {
			std::this_thread::sleep_for(std::chrono::seconds(2));
			if (g_busy.exchange(true)) {
				continue;
			}
			SKSE::GetTaskInterface()->AddTask([] {
				Check();
				g_busy = false;
			});
		}
	}
}

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	SKSE::log::info("ZenPlayer3DTrace 1.0.0 loading, runtime {}", REL::Module::get().version().string());
	SKSE::GetMessagingInterface()->RegisterListener([](SKSE::MessagingInterface::Message* a_msg) {
		if (a_msg->type == SKSE::MessagingInterface::kDataLoaded) {
			g_target = RE::TESDataHandler::GetSingleton()->LookupForm<RE::TESRace>(0x837, "Triumvirate - Mage Archetypes.esp");
			SKSE::log::info("Horned Lord race: {}", FormStr(g_target));
			std::thread(Loop).detach();
		}
	});
	return true;
}
