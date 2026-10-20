#include "pch.h"

// Chocolate Poise - Reforged (ChocolatePoiseReforged.dll) looks up vanilla Skyrim's ForceFullBodyStagger
// faction by hardcoded FormID 0x10CED7. In Enderal that ID is a placed reference (cell QKerker), so the
// lookup's faction-type check discards it, the field stays null ("Failed to find ForceFullBodyStagger
// faction" in ChocolatePoiseReforged.log), and every poise break then runs
// a_target->AddToFaction(nullptr, 0) with no null check (src/PoiseAV.cpp). The null faction entry crashes
// the next faction-reaction lookup on that actor: on 1.7.104 SkyrimSE.exe+06C8FAD `mov ebx,[rcx+0x58]`
// with rcx = 0, seen 2026-10-20 the moment a Pit Rat's attack broke the player's poise.
//
// Fix: once data is loaded (main menu, then again on new game / save load), point that field at the
// ForceFullBodyStagger faction the Chocolate Poise Enderal patch already ships
// (ChocolatePoise - Enderal.esp, 0x800). That patch's PlayerStaggerRoot idle conditions on the same
// faction, so player full-body stagger works too. Only a null field is written, and only if the DLL's code
// bytes match the build this was derived from -- a CPR update makes this a logged no-op, not a bad write.
//
// This replaces the NetScriptFramework plugin in ../NetScriptPlugin (NSF only runs on SSE 1.5.97).
// Offsets re-derived 2026-10-20 from ChocolatePoiseReforged.dll (TimeDateStamp 0x6AB9B4F8,
// MD5 729b2b0e7b3facd389fcdee75436af31): RetrieveFullBodyStaggerFaction calls the PoiseAV getter
// (RVA 0x8710, a function-local static returned by `lea rax,[rip+...]` = RVA 0x139100), then
// `mov ecx,0x10CED7` at RVA 0x5B542, LookupByID, a kFaction (0x0B) form-type check, and
// `mov [rbx+8],rax` -- so the field is RVA 0x139108.

SKSEPluginInfo(
	.Version = REL::Version{ 2, 0, 0, 0 },
	.Name = "ZenCPRFactionFix"sv,
	.Author = "Zenderal"sv,
	.StructCompatibility = SKSE::StructCompatibility::Independent,
	.RuntimeCompatibility = SKSE::VersionIndependence::AddressLibrary)

namespace
{
	constexpr auto          kModule = L"ChocolatePoiseReforged.dll";
	constexpr std::uintptr_t kLookupSiteRva = 0x5B542;
	constexpr std::uint8_t  kLookupSiteBytes[] = { 0xB9, 0xD7, 0xCE, 0x10, 0x00 };  // mov ecx, 0x10CED7
	constexpr std::uintptr_t kFactionFieldRva = 0x139108;                             // PoiseAV singleton + 8
	constexpr auto          kFactionFile = "ChocolatePoise - Enderal.esp"sv;
	constexpr RE::FormID    kFactionId = 0x800;

	bool g_done{ false };

	void Patch(std::string_view a_when)
	{
		if (g_done) {
			return;
		}
		auto* const module = reinterpret_cast<std::uint8_t*>(::GetModuleHandleW(kModule));
		if (!module) {
			SKSE::log::info("[{}] ChocolatePoiseReforged.dll is not loaded; nothing to do", a_when);
			g_done = true;
			return;
		}
		if (std::memcmp(module + kLookupSiteRva, kLookupSiteBytes, sizeof(kLookupSiteBytes)) != 0) {
			SKSE::log::warn("[{}] ChocolatePoiseReforged.dll code at RVA {:#x} is not `mov ecx, 0x10CED7`: a different CPR "
							"build. Not patching -- re-derive the offsets (see main.cpp).",
				a_when, kLookupSiteRva);
			g_done = true;
			return;
		}
		auto** const field = reinterpret_cast<RE::TESFaction**>(module + kFactionFieldRva);
		if (*field) {
			SKSE::log::info("[{}] ForceFullBodyStagger already set ({:08X}); leaving it", a_when, (*field)->GetFormID());
			g_done = true;
			return;
		}
		auto* const handler = RE::TESDataHandler::GetSingleton();
		auto* const faction = handler ? handler->LookupForm<RE::TESFaction>(kFactionId, kFactionFile) : nullptr;
		if (!faction) {
			SKSE::log::warn("[{}] {} {:#x} (ForceFullBodyStagger) not found; CPR's field stays null", a_when, kFactionFile, kFactionId);
			return;  // try again later (new game / load) in case the plugin list was still loading
		}
		*field = faction;
		g_done = true;
		SKSE::log::info("[{}] Patched: ForceFullBodyStagger -> {} (form {:08X})", a_when, kFactionFile, faction->GetFormID());
	}

	class MenuSink final : public RE::BSTEventSink<RE::MenuOpenCloseEvent>
	{
	public:
		static MenuSink* GetSingleton()
		{
			static MenuSink singleton;
			return &singleton;
		}

		RE::BSEventNotifyControl ProcessEvent(const RE::MenuOpenCloseEvent* a_event, RE::BSTEventSource<RE::MenuOpenCloseEvent>*) override
		{
			if (a_event && a_event->opening && a_event->menuName == RE::MainMenu::MENU_NAME) {
				Patch("main menu"sv);
			}
			return RE::BSEventNotifyControl::kContinue;
		}
	};
}

SKSEPluginLoad(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	SKSE::log::info("ZenCPRFactionFix 2.0.0 loading, runtime {}", REL::Module::get().version().string());

	SKSE::GetMessagingInterface()->RegisterListener([](SKSE::MessagingInterface::Message* a_msg) {
		switch (a_msg->type) {
		case SKSE::MessagingInterface::kDataLoaded:
			if (auto* ui = RE::UI::GetSingleton()) {
				ui->AddEventSink<RE::MenuOpenCloseEvent>(MenuSink::GetSingleton());
				SKSE::log::info("Menu sink registered");
			}
			break;
		case SKSE::MessagingInterface::kNewGame:
			Patch("new game"sv);
			break;
		case SKSE::MessagingInterface::kPostLoadGame:
			Patch("load game"sv);
			break;
		default:
			break;
		}
	});
	return true;
}
