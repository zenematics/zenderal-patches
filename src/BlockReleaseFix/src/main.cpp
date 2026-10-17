#include "pch.h"

// Dual Wield Parrying SKSE 1.7.0 (src/InputEventHandler.cpp) blocks on its ParryKey like this:
//
//     if (paused || menu open || !fighting controls || !attackBlockHandler->inputEventHandlingEnabled ||
//         weapon not drawn || sitting || knockState != normal || flying || in killmove ||
//         !GetGraphVariableBool("IsBlocking", isBlocking))
//         return;                                       // the key-up is never seen
//     if (held)      { wantBlocking = 1; if (!isBlocking) NotifyAnimationGraph("blockStart"); }
//     else if (up)   { wantBlocking = 0; if (isBlocking)  NotifyAnimationGraph("blockStop"); }
//
// Nothing re-checks later, so a key-up that lands while any gate fails, or while IsBlocking briefly
// reads false (block-hit / timed-block / counter clips), leaves the player blocking until the key is
// tapped again. This plugin tracks the block keys itself (DWP's ParryKey/ParryKey2 plus the vanilla
// Left/Right Attack/Block controls on every device) and, once none has been held for GraceMs, ends
// any player block that is still on - the same wantBlocking = 0 + blockStop DWP would have sent.

SKSEPluginInfo(
	.Version = REL::Version{ 1, 0, 2, 0 },
	.Name = "ZenBlockReleaseFix"sv,
	.Author = "Zenderal"sv,
	.StructCompatibility = SKSE::StructCompatibility::Independent,
	.RuntimeCompatibility = SKSE::VersionIndependence::AddressLibrary)

namespace
{
	constexpr auto kIniPath = "Data/SKSE/Plugins/ZenBlockReleaseFix.ini";
	constexpr auto kDwpIniPath = "Data/SKSE/Plugins/DualWieldParryingSKSE.ini";
	constexpr std::uint32_t kNoKey = 1000000;  // DWP's own "unbound" value

	// DWP's key codes: keyboard = DX scan code, mouse = button + 257 (upstream InputEventHandler.cpp:61,
	// verified in this list: right click = 258, Mouse 5 = 261).
	constexpr std::uint32_t kMouseOffset = 257;
	constexpr std::uint32_t kRetryMs = 500;

	// Gamepad codes follow SKSE's numbering (266 = D-pad up ... 280 = LT, 281 = RT); the list's DWP
	// ParryKey2 = 280 blocks on LT. The engine reports XInput button masks, and the triggers as 0x9/0xA.
	std::uint32_t GamepadKeyCode(std::uint32_t a_idCode)
	{
		switch (a_idCode) {
		case 0x0001: return 266;  // D-pad up
		case 0x0002: return 267;  // D-pad down
		case 0x0004: return 268;  // D-pad left
		case 0x0008: return 269;  // D-pad right
		case 0x0010: return 270;  // Start
		case 0x0020: return 271;  // Back
		case 0x0040: return 272;  // Left thumb
		case 0x0080: return 273;  // Right thumb
		case 0x0100: return 274;  // LB
		case 0x0200: return 275;  // RB
		case 0x1000: return 276;  // A
		case 0x2000: return 277;  // B
		case 0x4000: return 278;  // X
		case 0x8000: return 279;  // Y
		case 0x0009: return 280;  // LT
		case 0x000A: return 281;  // RT
		default:     return kNoKey;
		}
	}

	std::uint32_t g_graceMs{ 200 };
	bool          g_log{ true };
	bool          g_enabled{ true };
	std::uint32_t g_dwpKeys[2]{ kNoKey, kNoKey };

	// Currently held block keys, as (device << 32 | idCode).
	std::vector<std::uint64_t> g_held;
	std::uint64_t              g_lastReleaseMs{ 0 };
	std::uint64_t              g_lastFixMs{ 0 };

	std::uint64_t NowMs() { return ::GetTickCount64(); }

	bool IsBlockKey(const RE::ButtonEvent* a_button)
	{
		const auto& userEvent = a_button->QUserEvent();
		if (const auto* strings = RE::UserEvents::GetSingleton()) {
			if (userEvent == strings->leftAttack || userEvent == strings->rightAttack) {
				return true;
			}
		}

		std::uint32_t code = a_button->GetIDCode();
		switch (a_button->GetDevice()) {
		case RE::INPUT_DEVICE::kKeyboard:
			break;
		case RE::INPUT_DEVICE::kMouse:
			code += kMouseOffset;
			break;
		case RE::INPUT_DEVICE::kGamepad:
			code = GamepadKeyCode(code);
			break;
		default:
			return false;
		}
		return code == g_dwpKeys[0] || code == g_dwpKeys[1];
	}

	class InputSink final : public RE::BSTEventSink<RE::InputEvent*>
	{
	public:
		static InputSink* GetSingleton()
		{
			static InputSink singleton;
			return &singleton;
		}

		RE::BSEventNotifyControl ProcessEvent(RE::InputEvent* const* a_event, RE::BSTEventSource<RE::InputEvent*>*) override
		{
			for (auto* event = a_event ? *a_event : nullptr; event; event = event->next) {
				if (event->GetEventType() != RE::INPUT_EVENT_TYPE::kButton) {
					continue;
				}
				const auto* button = event->AsButtonEvent();
				if (!button || !IsBlockKey(button)) {
					continue;
				}
				const auto key = (static_cast<std::uint64_t>(button->GetDevice()) << 32) | button->GetIDCode();
				const auto it = std::ranges::find(g_held, key);
				if (button->IsPressed()) {
					if (it == g_held.end()) {
						g_held.push_back(key);
					}
				} else if (it != g_held.end()) {
					g_held.erase(it);
					g_lastReleaseMs = NowMs();
				}
			}
			return RE::BSEventNotifyControl::kContinue;
		}
	};

	void CheckStuckBlock(RE::PlayerCharacter* a_player)
	{
		if (!g_enabled || !g_held.empty()) {
			return;
		}
		const auto now = NowMs();
		if (now - g_lastReleaseMs < g_graceMs || now - g_lastFixMs < kRetryMs) {
			return;
		}

		auto* state = a_player->AsActorState();
		if (!state) {
			return;
		}
		bool isBlocking = false;
		a_player->GetGraphVariableBool("IsBlocking"sv, isBlocking);
		const bool wantBlocking = state->actorState2.wantBlocking != 0;
		if (!isBlocking && !wantBlocking) {
			return;
		}

		g_lastFixMs = now;
		state->actorState2.wantBlocking = 0;
		if (isBlocking) {
			a_player->NotifyAnimationGraph("blockStop"sv);
		}
		if (g_log) {
			SKSE::log::info("Ended stuck block (IsBlocking={} wantBlocking={} weaponState={} knockState={} {} ms after last block key-up)",
				isBlocking, wantBlocking,
				static_cast<std::uint32_t>(state->GetWeaponState()),
				static_cast<std::uint32_t>(state->GetKnockState()),
				now - g_lastReleaseMs);
		}
	}

	// Actor::Update (vfunc 0xAD) on the player's vtable: once per frame while the game runs.
	struct PlayerUpdate
	{
		static void thunk(RE::PlayerCharacter* a_this, float a_delta)
		{
			func(a_this, a_delta);
			CheckStuckBlock(a_this);
		}
		static inline REL::Relocation<decltype(thunk)> func;
	};

	// GetPrivateProfileInt can't be used: DWP's shipped ini starts with a UTF-8 BOM, which glues itself
	// to the first section header so "[DualWieldParrying]" is never found and every key reads as default.
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

	void LoadSettings()
	{
		g_graceMs = ReadIniInt(kIniPath, "General"sv, "GraceMs"sv, 200);
		g_log = ReadIniInt(kIniPath, "General"sv, "Log"sv, 1) != 0;
		g_dwpKeys[0] = ReadIniInt(kDwpIniPath, "DualWieldParrying"sv, "ParryKey"sv, kNoKey);
		g_dwpKeys[1] = ReadIniInt(kDwpIniPath, "DualWieldParrying"sv, "ParryKey2"sv, kNoKey);
		SKSE::log::info("GraceMs={} Log={} DWP ParryKey={} ParryKey2={}", g_graceMs, g_log, g_dwpKeys[0], g_dwpKeys[1]);

		// Without DWP's key we can't tell a held DWP block from a stuck one; ending blocks then would
		// cancel every one the player is holding. Stay inert instead.
		if (g_dwpKeys[0] == kNoKey) {
			g_enabled = false;
			SKSE::log::warn("Could not read DWP's ParryKey from {} - fix DISABLED", kDwpIniPath);
		}
	}

	void MessageHandler(SKSE::MessagingInterface::Message* a_msg)
	{
		switch (a_msg->type) {
		case SKSE::MessagingInterface::kInputLoaded:
			if (auto* input = RE::BSInputDeviceManager::GetSingleton()) {
				input->AddEventSink(InputSink::GetSingleton());
				SKSE::log::info("Input sink registered");
			}
			break;
		case SKSE::MessagingInterface::kPreLoadGame:
		case SKSE::MessagingInterface::kNewGame:
			g_held.clear();
			g_lastReleaseMs = NowMs();
			break;
		default:
			break;
		}
	}
}

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	SKSE::log::info("ZenBlockReleaseFix 1.0.2 loading, runtime {}", REL::Module::get().version().string());
	LoadSettings();

	REL::Relocation<std::uintptr_t> vtbl{ RE::VTABLE_PlayerCharacter[0] };
	PlayerUpdate::func = vtbl.write_vfunc(0xAD, PlayerUpdate::thunk);
	SKSE::log::info("PlayerCharacter::Update hooked");

	SKSE::GetMessagingInterface()->RegisterListener(MessageHandler);
	return true;
}
