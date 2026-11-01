#include "pch.h"

#include <filesystem>

// DBVO 2.0.2.2 keeps its settings per save (SKSE co-save record 'DBVO'/'STNG') and gives a new game
// whatever is in Data/SKSE/Plugins/DBVO2/default_options.json: its revert callback reads that file on
// every new game and before every load. It has no idea of the player's sex, and in Enderal the sex is
// chosen in the RaceSex menu well after the new game has started.
//
// So at the start of a new game this copies silent.json (male.json at volume 0: the prologue is played
// before the player has a character, and a voice there would be the wrong one half the time), and when
// the RaceSex menu closes it copies male.json or female.json (all next to this DLL) over
// default_options.json and calls DBVO's own "load default_options.json" routine, which revert
// uses. The settings are then in memory and go into the character's first save; from there on DBVO's
// save record rules, so anything the player changes in DBVO's menu sticks. A save made before character
// creation holds the silent settings; the RaceSex menu closing still switches it, because
// default_options.json then still holds silent.json.
//
// DBVO.dll 2.0.2.2 (TimeDateStamp 0x6AB06DCE), read with capstone 2026-10-18:
//   0x6FB0  registers the serialization callbacks: save 0x8830, load 0x80F0, revert 0x6FF0
//   0x6FF0  revert: ... call 0x2AC20 (load defaults), call 0x2AEF0 (read always_use_default_options)
//   0x2AC20 void(): builds the path (0x234E0), opens the file, parses it into the live settings (0x2BAD0)
// Any other DBVO build: the file is still written (so the NEXT new game starts right) but nothing is
// called, and the log says so.

SKSEPluginInfo(
	.Version = REL::Version{ 1, 2, 0, 0 },
	.Name = "ZenDBVOSexDefaults"sv,
	.Author = "Zenderal"sv,
	.StructCompatibility = SKSE::StructCompatibility::Independent,
	.RuntimeCompatibility = SKSE::VersionIndependence::AddressLibrary)

namespace
{
	constexpr auto kDefaultsPath = "Data/SKSE/Plugins/DBVO2/default_options.json";
	constexpr auto kMalePath = "Data/SKSE/Plugins/ZenDBVOSexDefaults/male.json";
	constexpr auto kFemalePath = "Data/SKSE/Plugins/ZenDBVOSexDefaults/female.json";
	constexpr auto kSilentPath = "Data/SKSE/Plugins/ZenDBVOSexDefaults/silent.json";

	constexpr std::uint32_t kDbvoTimeDateStamp = 0x6AB06DCE;
	constexpr std::uintptr_t kLoadDefaultsRva = 0x2AC20;
	constexpr std::array<std::uint8_t, 18> kLoadDefaultsPrologue{
		0x55, 0x56, 0x57, 0x48, 0x81, 0xEC, 0xA0, 0x01, 0x00, 0x00, 0x48, 0x8D, 0xAC, 0x24, 0x80, 0x00, 0x00, 0x00
	};

	using LoadDefaults_t = void (*)();
	LoadDefaults_t g_loadDefaults{ nullptr };

	bool g_freshGame{ false };          // set by kNewGame, cleared by any save load
	int  g_appliedSex{ -1 };            // sex applied during this fresh game (-1 = none yet, or silent)

	std::optional<std::string> ReadFile(const char* a_path)
	{
		std::ifstream in(a_path, std::ios::binary);
		if (!in) {
			return std::nullopt;
		}
		return std::string(std::istreambuf_iterator<char>(in), {});
	}

	void FindDbvo()
	{
		const auto module = ::GetModuleHandleW(L"DBVO.dll");
		if (!module) {
			SKSE::log::warn("DBVO.dll is not loaded; nothing to do");
			return;
		}
		const auto base = reinterpret_cast<std::uintptr_t>(module);
		const auto dos = reinterpret_cast<const IMAGE_DOS_HEADER*>(base);
		const auto nt = reinterpret_cast<const IMAGE_NT_HEADERS64*>(base + dos->e_lfanew);
		const auto stamp = nt->FileHeader.TimeDateStamp;
		const auto fn = reinterpret_cast<const std::uint8_t*>(base + kLoadDefaultsRva);
		const bool bytesMatch = stamp == kDbvoTimeDateStamp && kLoadDefaultsRva + kLoadDefaultsPrologue.size() < nt->OptionalHeader.SizeOfImage &&
		                        std::memcmp(fn, kLoadDefaultsPrologue.data(), kLoadDefaultsPrologue.size()) == 0;
		if (!bytesMatch) {
			SKSE::log::warn("DBVO.dll is not the 2.0.2.2 build this was made for (TimeDateStamp {:08X}); the defaults file will be written, "
							"but a new character only gets it from the next new game",
				stamp);
			return;
		}
		g_loadDefaults = reinterpret_cast<LoadDefaults_t>(base + kLoadDefaultsRva);
		SKSE::log::info("DBVO.dll 2.0.2.2 found at {:X}; defaults loader at +{:X}", base, kLoadDefaultsRva);
	}

	// Writes a_profilePath over default_options.json and has DBVO reload it. False if nothing was applied.
	bool ApplyProfile(const char* a_profilePath, const char* a_label)
	{
		const auto profilePath = a_profilePath;
		const auto profile = ReadFile(profilePath);
		if (!profile || profile->empty()) {
			SKSE::log::error("{} is missing or empty; DBVO keeps its current settings", profilePath);
			return false;
		}
		if (ReadFile(kDefaultsPath) != profile) {
			std::ofstream out(kDefaultsPath, std::ios::binary | std::ios::trunc);
			out << *profile;
			out.close();
			if (!out) {
				SKSE::log::error("could not write {}", kDefaultsPath);
				return false;
			}
			SKSE::log::info("wrote {} into {}", profilePath, kDefaultsPath);
		} else {
			SKSE::log::info("{} already holds {}", kDefaultsPath, profilePath);
		}
		if (g_loadDefaults) {
			g_loadDefaults();
			SKSE::log::info("DBVO reloaded its defaults: {} profile is live", a_label);
		}
		return true;
	}

	void ApplyForSex(RE::SEX a_sex)
	{
		const bool female = a_sex == RE::SEX::kFemale;
		if (ApplyProfile(female ? kFemalePath : kMalePath, female ? "female" : "male")) {
			g_appliedSex = static_cast<int>(a_sex);
		}
	}

	// default_options.json still holding silent.json means the voice was never switched on for this
	// character: a save made before character creation, loaded later.
	bool DefaultsAreSilent()
	{
		const auto silent = ReadFile(kSilentPath);
		return silent && !silent->empty() && ReadFile(kDefaultsPath) == silent;
	}

	// Queued on the main thread: by then DBVO's revert for this new game has run, so our reload wins.
	void ApplyForCurrentPlayer(const char* a_when)
	{
		SKSE::GetTaskInterface()->AddTask([a_when] {
			const auto player = RE::PlayerCharacter::GetSingleton();
			const auto base = player ? player->GetActorBase() : nullptr;
			if (!base) {
				SKSE::log::warn("{}: no player base yet; DBVO keeps its current settings", a_when);
				return;
			}
			const auto sex = base->GetSex();
			if (static_cast<int>(sex) == g_appliedSex) {
				SKSE::log::info("{}: player is still {}, leaving DBVO alone", a_when, sex == RE::SEX::kFemale ? "female" : "male");
				return;
			}
			SKSE::log::info("{}: player is {}", a_when, sex == RE::SEX::kFemale ? "female" : "male");
			ApplyForSex(sex);
		});
	}

	class MenuSink final : public RE::BSTEventSink<RE::MenuOpenCloseEvent>
	{
	public:
		RE::BSEventNotifyControl ProcessEvent(const RE::MenuOpenCloseEvent* a_event, RE::BSTEventSource<RE::MenuOpenCloseEvent>*) override
		{
			if (!a_event || a_event->opening || a_event->menuName != RE::RaceSexMenu::MENU_NAME) {
				return RE::BSEventNotifyControl::kContinue;
			}
			if (g_freshGame) {
				ApplyForCurrentPlayer("RaceSex menu closed on a new game");
			} else if (DefaultsAreSilent()) {
				g_appliedSex = -1;
				ApplyForCurrentPlayer("RaceSex menu closed on a save made before character creation");
			}
			return RE::BSEventNotifyControl::kContinue;
		}
	};
	MenuSink g_menuSink;
}

SKSEPluginLoad(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	SKSE::log::info("ZenDBVOSexDefaults 1.2.0 loading, runtime {}", REL::Module::get().version().string());

	SKSE::GetMessagingInterface()->RegisterListener([](SKSE::MessagingInterface::Message* a_msg) {
		switch (a_msg->type) {
		case SKSE::MessagingInterface::kDataLoaded:
			FindDbvo();
			RE::UI::GetSingleton()->AddEventSink<RE::MenuOpenCloseEvent>(&g_menuSink);
			break;
		case SKSE::MessagingInterface::kNewGame:
			// Enderal's prologue is played before character creation, as the default (male) player. Keep the
			// player voice silent until the RaceSex menu closes and the character's sex is known.
			g_freshGame = true;
			g_appliedSex = -1;
			SKSE::GetTaskInterface()->AddTask([] {
				SKSE::log::info("new game: player voice silent until character creation");
				ApplyProfile(kSilentPath, "silent");
			});
			break;
		case SKSE::MessagingInterface::kPreLoadGame:
			g_freshGame = false;
			break;
		default:
			break;
		}
	});
	return true;
}
