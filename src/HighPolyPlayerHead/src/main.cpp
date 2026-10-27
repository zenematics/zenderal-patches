#include "pch.h"

// Enderal's chargen presets and playable races use the vanilla face head parts (MaleHeadNord, ...:
// Character Assets\MaleHead.nif), while the list's beards are fitted to High Poly Head. High Poly Head.esm
// ships a twin of each vanilla face part, 00KLH_<name>: same texture set, races and flags, only the mesh and
// .tri paths differ.
//
// Repointing the shared vanilla records instead (Zenderal - High Poly Default Heads, 2026-10-25) hard-froze
// the game: NPCs with baked facegen keep their 898-vertex face mesh but take the head part's .tri morphs,
// HPH's are 3598-vertex. 1.0 swapped the player's face every frame from PlayerCharacter::Update, which does
// not tick while the race menu pauses the game: the swap landed the moment the menu closed, over Enderal's
// presets, whose slider values are tuned on the vanilla head (beta reports, 2026-10-27).
//
// 1.1 acts only inside the RaceSex menu (its AdvanceMovie, every frame while it is open), so HPH is the menu's
// default and nothing is forced afterwards:
//   - race/sex changed (or the menu opened on a new game) with a vanilla face -> the HPH twin with all 19
//     sliders at 0. Picking a race makes the engine apply one of its presets (the face goes onto the NPC
//     record and the sliders take the preset's values; log, 2026-10-27), and those values only look right
//     on the vanilla head, so the default becomes HPH's neutral face;
//   - a preset picked (the sliders now equal one of the race's preset NPCs) while wearing a twin this put
//     on -> back to the vanilla face, so the preset looks as SureAI tuned it;
//   - anything else (a head picked by hand, sliders moved, NPCs, every record) is left alone.

SKSEPluginInfo(
	.Version = REL::Version{ 1, 1, 2, 0 },
	.Name = "ZenHighPolyPlayerHead"sv,
	.Author = "Zenderal"sv,
	.StructCompatibility = SKSE::StructCompatibility::Independent,
	.RuntimeCompatibility = SKSE::VersionIndependence::AddressLibrary)

namespace
{
	constexpr auto kIniPath = "Data/SKSE/Plugins/ZenHighPolyPlayerHead.ini";
	constexpr auto kPrefix = "00KLH_"sv;

	bool g_enabled{ true };
	bool g_log{ true };

	std::unordered_map<RE::BGSHeadPart*, RE::BGSHeadPart*> g_twins;     // vanilla face part -> HPH twin
	std::unordered_map<RE::BGSHeadPart*, RE::BGSHeadPart*> g_vanillas;  // HPH twin -> vanilla face part

	// Menu state, reset whenever the RaceSex menu opens.
	bool                  g_menuFresh{ true };
	RE::TESRace*          g_lastRace{ nullptr };
	int                   g_lastSex{ -1 };
	std::array<float, 23> g_lastLook{};
	RE::BGSHeadPart*      g_ourTwin{ nullptr };  // the twin this put on, while the player still wears it
	RE::BGSHeadPart*      g_lastFace{ nullptr };
	bool                  g_newGame{ false };    // kNewGame until a save is loaded

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
			g_vanillas.emplace(twin, vanilla);
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

	// The 19 sliders and 4 nose/eyes/mouth picks; no face data = every slider at its default.
	std::array<float, 23> Look(const RE::TESNPC* a_npc)
	{
		std::array<float, 23> look{};
		if (const auto* face = a_npc->faceData) {
			for (std::size_t i = 0; i < RE::TESNPC::FaceData::Morphs::kTotal; ++i) {
				look[i] = face->morphs[i];
			}
			for (std::size_t i = 0; i < RE::TESNPC::FaceData::Parts::kTotal; ++i) {
				look[RE::TESNPC::FaceData::Morphs::kTotal + i] = static_cast<float>(face->parts[i]);
			}
		}
		return look;
	}

	bool SlidersAtDefault(const RE::TESNPC* a_npc)
	{
		const auto* face = a_npc->faceData;
		if (!face) {
			return true;
		}
		for (const auto morph : face->morphs) {
			if (std::fabs(morph) > 0.001f) {
				return false;
			}
		}
		return true;
	}

	// A preset NPC of the player's race and sex whose sliders the player now has. Presets with no slider
	// values look the same on either head and never count.
	RE::TESNPC* MatchingPreset(RE::TESNPC* a_npc, const std::array<float, 23>& a_look)
	{
		auto*      race = a_npc->GetRace();
		const auto sex = a_npc->GetSex();
		if (!race || sex > RE::SEX::kFemale || !race->faceRelatedData[sex] || !race->faceRelatedData[sex]->presetNPCs) {
			return nullptr;
		}
		for (auto* preset : *race->faceRelatedData[sex]->presetNPCs) {
			if (!preset || SlidersAtDefault(preset)) {
				continue;
			}
			const auto look = Look(preset);
			if (std::ranges::equal(look, a_look, [](float x, float y) { return std::fabs(x - y) < 0.001f; })) {
				return preset;
			}
		}
		return nullptr;
	}

	void SetFace(RE::PlayerCharacter* a_player, RE::TESNPC* a_npc, RE::BGSHeadPart* a_from, RE::BGSHeadPart* a_to, bool a_neutral, std::string_view a_why)
	{
		a_npc->ChangeHeadPart(a_to);
		if (a_neutral && a_npc->faceData) {
			for (auto& morph : a_npc->faceData->morphs) {
				morph = 0.0f;
			}
		}
		if (a_player->Get3D(false)) {
			if (a_neutral) {
				// The slider values only reach the head when it is rebuilt.
				a_player->DoReset3D(false);
			} else {
				a_player->ChangeHeadPart(a_from, a_to);
			}
		}
		if (g_log) {
			auto* race = a_npc->GetRace();
			SKSE::log::info("Player head {} -> {} (race {}){}: {}", a_from->GetFormEditorID(), a_to->GetFormEditorID(),
				race ? race->GetFormEditorID() : "?", a_neutral ? ", sliders reset to 0" : "", a_why);
		}
	}

	void CheckInMenu()
	{
		auto* player = RE::PlayerCharacter::GetSingleton();
		auto* npc = player ? player->GetActorBase() : nullptr;
		if (!npc || g_twins.empty()) {
			return;
		}
		auto*      face = CurrentFace(npc);
		auto*      race = npc->GetRace();
		const auto sex = static_cast<int>(npc->GetSex());
		const auto look = Look(npc);
		const bool raceChanged = race != g_lastRace || sex != g_lastSex;
		const bool lookChanged = look != g_lastLook;
		if (g_log && (g_menuFresh || raceChanged || face != g_lastFace)) {
			auto* explicitFace = npc->GetHeadPartByType(RE::BGSHeadPart::HeadPartType::kFace);
			auto* preset = MatchingPreset(npc, look);
			SKSE::log::info("Race menu: face {} ({}), race {}, sex {}, sliders {}{}", face ? face->GetFormEditorID() : "none",
				face && face == explicitFace ? "on the NPC record" : "race default", race ? race->GetFormEditorID() : "?", sex,
				SlidersAtDefault(npc) ? "at default" : "set", preset ? fmt::format(" = preset {}", preset->GetFormEditorID()) : "");
		}
		const bool fresh = std::exchange(g_menuFresh, false);
		// Only the first time the menu opens on a new game: Enderal opens it again later in the same game, and that
		// must not reset the face the player has just made.
		const bool firstOnNewGame = fresh && std::exchange(g_newGame, false);
		g_lastRace = race;
		g_lastSex = sex;
		g_lastLook = look;
		g_lastFace = face;
		if (g_ourTwin && face != g_ourTwin) {
			g_ourTwin = nullptr;  // the player picked another head
		}
		if (!face) {
			return;
		}

		// Opening the menu on an existing character (showracemenu) must not undo its sculpted face.
		if (firstOnNewGame || (!fresh && raceChanged)) {
			const auto it = g_twins.find(face);
			if (it == g_twins.end()) {
				return;
			}
			auto* twin = it->second;
			if (twin->validRaces && race && !twin->validRaces->HasForm(race)) {
				if (g_log) {
					SKSE::log::info("{} not valid for race {}", twin->GetFormEditorID(), race->GetFormEditorID());
				}
				return;
			}
			SetFace(player, npc, face, twin, true, fresh ? "menu opened on a new game" : "race or sex changed");
			g_ourTwin = twin;
			g_lastFace = twin;
			g_lastLook = Look(npc);
			return;
		}

		if (lookChanged && face == g_ourTwin) {
			if (auto* preset = MatchingPreset(npc, look)) {
				const auto it = g_vanillas.find(face);
				if (it != g_vanillas.end()) {
					SetFace(player, npc, face, it->second, false, preset->GetFormEditorID());
					g_ourTwin = nullptr;
					g_lastFace = it->second;
				}
			}
		}
	}

	// RaceSexMenu::AdvanceMovie (IMenu vfunc 0x05): every frame while the race menu is open.
	struct RaceMenuAdvance
	{
		static void thunk(RE::RaceSexMenu* a_this, float a_interval, std::uint32_t a_currentTime)
		{
			func(a_this, a_interval, a_currentTime);
			CheckInMenu();
		}
		static inline REL::Relocation<decltype(thunk)> func;
	};

	class MenuSink final : public RE::BSTEventSink<RE::MenuOpenCloseEvent>
	{
	public:
		RE::BSEventNotifyControl ProcessEvent(const RE::MenuOpenCloseEvent* a_event, RE::BSTEventSource<RE::MenuOpenCloseEvent>*) override
		{
			if (a_event && a_event->opening && a_event->menuName == RE::RaceSexMenu::MENU_NAME) {
				g_menuFresh = true;
				g_lastRace = nullptr;
				g_lastSex = -1;
				g_ourTwin = nullptr;
				g_lastFace = nullptr;
			}
			return RE::BSEventNotifyControl::kContinue;
		}
	};
	MenuSink g_menuSink;

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
	SKSE::log::info("ZenHighPolyPlayerHead 1.1.2 loading, runtime {}", REL::Module::get().version().string());
	g_enabled = ReadIniInt(kIniPath, "General"sv, "Enabled"sv, 1) != 0;
	g_log = ReadIniInt(kIniPath, "General"sv, "Log"sv, 1) != 0;
	SKSE::log::info("Enabled={} Log={}", g_enabled, g_log);
	if (!g_enabled) {
		return true;
	}

	SKSE::GetMessagingInterface()->RegisterListener([](SKSE::MessagingInterface::Message* a_msg) {
		switch (a_msg->type) {
		case SKSE::MessagingInterface::kDataLoaded:
			BuildTwins();
			RE::UI::GetSingleton()->AddEventSink<RE::MenuOpenCloseEvent>(&g_menuSink);
			break;
		case SKSE::MessagingInterface::kNewGame:
			g_newGame = true;
			break;
		case SKSE::MessagingInterface::kPreLoadGame:
			g_newGame = false;
			break;
		default:
			break;
		}
	});

	REL::Relocation<std::uintptr_t> vtbl{ RE::VTABLE_RaceSexMenu[0] };
	RaceMenuAdvance::func = vtbl.write_vfunc(0x05, RaceMenuAdvance::thunk);
	SKSE::log::info("RaceSexMenu::AdvanceMovie hooked");
	return true;
}
