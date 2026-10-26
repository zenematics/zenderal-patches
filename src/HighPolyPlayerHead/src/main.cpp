#include "pch.h"

// Enderal's chargen presets and playable races use the vanilla face head parts (MaleHeadNord, ...:
// Character Assets\MaleHead.nif), while the list's beards are fitted to High Poly Head, so on a new
// character the head pokes through their stubble shells. High Poly Head.esm ships a twin of each
// vanilla face part, 00KLH_<name>: same texture set, races and flags, only the mesh and .tri paths differ.
//
// Repointing the shared vanilla records instead (Zenderal - High Poly Default Heads, 2026-10-25) hard-froze
// the game: NPCs with baked facegen keep their 898-vertex face mesh but take the head part's .tri morphs,
// HPH's are 3598-vertex, and the MQP03 temple corpse's head lock was left held mid-render. So this touches
// only the player: whenever the player's face part (explicit, or the race default it falls back to) has
// an HPH twin, the player's own NPC record and 3D switch to the twin. Checked once per frame from
// PlayerCharacter::Update, so it also catches chargen race/preset changes and scripted race swaps.

SKSEPluginInfo(
	.Version = REL::Version{ 1, 0, 1, 0 },
	.Name = "ZenHighPolyPlayerHead"sv,
	.Author = "Zenderal"sv,
	.StructCompatibility = SKSE::StructCompatibility::Independent,
	.RuntimeCompatibility = SKSE::VersionIndependence::AddressLibrary)

namespace
{
	constexpr auto kIniPath = "Data/SKSE/Plugins/ZenHighPolyPlayerHead.ini";
	constexpr auto kPrefix = "00KLH_"sv;

	// After a swap, wait this long before the next one, so a menu that keeps re-applying the vanilla
	// head can't make us rebuild the face every frame.
	constexpr std::uint64_t kCooldownMs = 1000;

	bool g_enabled{ true };
	bool g_log{ true };

	std::unordered_map<RE::BGSHeadPart*, RE::BGSHeadPart*> g_twins;  // vanilla face part -> HPH twin
	std::uint64_t                                         g_nextSwapMs{ 0 };
	bool                                                  g_seenUpdate{ false };
	RE::BGSHeadPart*                                      g_lastFace{ nullptr };
	RE::BGSHeadPart*                                      g_lastRefused{ nullptr };

	std::uint64_t NowMs() { return ::GetTickCount64(); }

	void BuildTwins()
	{
		auto* data = RE::TESDataHandler::GetSingleton();
		if (!data) {
			return;
		}
		std::unordered_map<std::string, RE::BGSHeadPart*> byName;
		std::vector<RE::BGSHeadPart*>                     hph;
		for (auto* part : data->GetFormArray<RE::BGSHeadPart>()) {
			if (!part || part->type != RE::BGSHeadPart::HeadPartType::kFace) {
				continue;
			}
			const std::string_view id{ part->GetFormEditorID() };
			if (id.starts_with(kPrefix)) {
				hph.push_back(part);
			} else if (!id.empty()) {
				byName.emplace(std::string{ id }, part);
			}
		}
		for (auto* twin : hph) {
			const std::string_view id{ twin->GetFormEditorID() };
			const auto             it = byName.find(std::string{ id.substr(kPrefix.size()) });
			if (it == byName.end()) {
				continue;
			}
			auto* vanilla = it->second;
			// Enderal's FemaleHeadNord has no texture set where HPH names SkinHeadFemaleNord; the head keeps
			// the look Enderal gave it.
			if (twin->textureSet != vanilla->textureSet) {
				SKSE::log::info("{}: texture set {:08X} -> {:08X} (Enderal's {})", id,
					twin->textureSet ? twin->textureSet->GetFormID() : 0, vanilla->textureSet ? vanilla->textureSet->GetFormID() : 0,
					vanilla->GetFormEditorID());
				twin->textureSet = vanilla->textureSet;
			}
			g_twins.emplace(vanilla, twin);
		}
		SKSE::log::info("{} vanilla face parts have a High Poly Head twin", g_twins.size());
	}

	// The face part the player is wearing: an explicit one on the NPC record, else the race's default.
	RE::BGSHeadPart* CurrentFace(RE::TESNPC* a_npc)
	{
		if (auto* face = a_npc->GetCurrentHeadPartByType(RE::BGSHeadPart::HeadPartType::kFace)) {
			return face;
		}
		auto* race = a_npc->GetRace();
		const auto sex = a_npc->GetSex();
		if (!race || sex > RE::SEX::kFemale || !race->faceRelatedData[sex] || !race->faceRelatedData[sex]->headParts) {
			return nullptr;
		}
		for (auto* part : *race->faceRelatedData[sex]->headParts) {
			if (part && part->type == RE::BGSHeadPart::HeadPartType::kFace) {
				return part;
			}
		}
		return nullptr;
	}

	void Check(RE::PlayerCharacter* a_player)
	{
		if (g_twins.empty()) {
			return;
		}
		auto* npc = a_player->GetActorBase();
		if (!npc) {
			return;
		}
		auto* face = CurrentFace(npc);
		if (g_log && (!std::exchange(g_seenUpdate, true) || face != g_lastFace)) {
			auto* explicitFace = npc->GetHeadPartByType(RE::BGSHeadPart::HeadPartType::kFace);
			auto* race = npc->GetRace();
			SKSE::log::info("Player face part: {} {:08X} ({}; overlays {}), race {}, {} twin", face ? face->GetFormEditorID() : "none",
				face ? face->GetFormID() : 0, face == explicitFace ? "on the NPC record" : "race default or overlay", npc->HasOverlays(),
				race ? race->GetFormEditorID() : "?", face && g_twins.contains(face) ? "has a" : "no");
		}
		g_lastFace = face;
		const auto it = face ? g_twins.find(face) : g_twins.end();
		if (it == g_twins.end()) {
			return;
		}
		auto* twin = it->second;
		auto* race = npc->GetRace();
		if (twin->validRaces && race && !twin->validRaces->HasForm(race)) {
			if (g_log && face != g_lastRefused) {
				SKSE::log::info("{} not valid for race {}", twin->GetFormEditorID(), race->GetFormEditorID());
			}
			g_lastRefused = face;
			return;
		}
		const auto now = NowMs();
		if (now < g_nextSwapMs) {
			return;
		}
		g_nextSwapMs = now + kCooldownMs;
		npc->ChangeHeadPart(twin);
		if (a_player->Get3D(false)) {
			a_player->ChangeHeadPart(face, twin);
		}
		if (g_log) {
			SKSE::log::info("Player head {} -> {} (race {})", face->GetFormEditorID(), twin->GetFormEditorID(),
				race ? race->GetFormEditorID() : "?");
		}
	}

	// Actor::Update (vfunc 0xAD) on the player's vtable: once per frame while the game runs.
	struct PlayerUpdate
	{
		static void thunk(RE::PlayerCharacter* a_this, float a_delta)
		{
			Check(a_this);
			func(a_this, a_delta);
		}
		static inline REL::Relocation<decltype(thunk)> func;
	};

	// GetPrivateProfileInt can't be used: a relative path is looked up in the Windows directory, and a
	// UTF-8 BOM glues itself to the first section header (ZenBlockReleaseFix 1.0.0). Parse it ourselves.
	std::uint32_t ReadIniInt(const char* a_path, std::string_view a_section, std::string_view a_key, std::uint32_t a_default)
	{
		std::ifstream file{ a_path };
		if (!file) {
			return a_default;
		}
		const auto trim = [](std::string_view s) {
			const auto b = s.find_first_not_of(" \t\r");
			const auto e = s.find_last_not_of(" \t\r");
			return b == std::string_view::npos ? std::string_view{} : s.substr(b, e - b + 1);
		};
		const auto iequals = [](std::string_view a, std::string_view b) {
			return std::ranges::equal(a, b, [](char x, char y) { return std::tolower(static_cast<unsigned char>(x)) == std::tolower(static_cast<unsigned char>(y)); });
		};
		std::string line;
		bool        inSection = false;
		bool        first = true;
		while (std::getline(file, line)) {
			std::string_view view{ line };
			if (first && view.starts_with("\xEF\xBB\xBF"sv)) {
				view.remove_prefix(3);
			}
			first = false;
			view = trim(view);
			if (view.empty() || view.front() == ';' || view.front() == '#') {
				continue;
			}
			if (view.front() == '[') {
				const auto end = view.find(']');
				inSection = end != std::string_view::npos && iequals(trim(view.substr(1, end - 1)), a_section);
				continue;
			}
			const auto eq = view.find('=');
			if (!inSection || eq == std::string_view::npos || !iequals(trim(view.substr(0, eq)), a_key)) {
				continue;
			}
			const auto value = trim(view.substr(eq + 1));
			std::uint32_t result{};
			if (std::from_chars(value.data(), value.data() + value.size(), result).ec == std::errc{}) {
				return result;
			}
			return a_default;
		}
		return a_default;
	}
}

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	SKSE::log::info("ZenHighPolyPlayerHead 1.0.1 loading, runtime {}", REL::Module::get().version().string());
	g_enabled = ReadIniInt(kIniPath, "General"sv, "Enabled"sv, 1) != 0;
	g_log = ReadIniInt(kIniPath, "General"sv, "Log"sv, 1) != 0;
	SKSE::log::info("Enabled={} Log={}", g_enabled, g_log);
	if (!g_enabled) {
		return true;
	}

	SKSE::GetMessagingInterface()->RegisterListener([](SKSE::MessagingInterface::Message* a_msg) {
		if (a_msg->type == SKSE::MessagingInterface::kDataLoaded) {
			BuildTwins();
		}
	});

	REL::Relocation<std::uintptr_t> vtbl{ RE::VTABLE_PlayerCharacter[0] };
	PlayerUpdate::func = vtbl.write_vfunc(0xAD, PlayerUpdate::thunk);
	SKSE::log::info("PlayerCharacter::Update hooked");
	return true;
}
