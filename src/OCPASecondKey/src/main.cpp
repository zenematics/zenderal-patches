#include "pch.h"

// One Click Power Attack NG reads a single power-attack key ([General] iKeycode in Data/MCM/Settings/OCPA.ini), so the
// list could have Mouse 4 or the gamepad's RT, not both, without swapping the MCM setting. This plugin adds a second key
// next to OCPA's, without touching OCPA: on that key's press it applies OCPA's own rules (read from the same OCPA.ini)
// and fires the same actions OCPA does (NG 1.12.3 for 1.7.104, src/Main.cpp, PowerAttack / PerformAction):
//
//   jumping or blocking -> ActionRightAttack, then ActionRightPowerAttack 200 ms later (jump attack / Vanguard)
//   otherwise           -> ActionRightPowerAttack
//
// An action the game refuses is retried for OCPA's queue window (bQueuePowerAttack / fQueueExpire), checked once per
// frame. OCPA retries only on MCO_PowerWinOpen/Close; the action still only succeeds when the game allows it.
// Key codes are OCPA's: keyboard = DX scan code, mouse = 256 + button, gamepad = 266-281 (281 = RT).

SKSEPluginInfo(
	.Version = REL::Version{ 1, 0, 0, 0 },
	.Name = "ZenOCPASecondKey"sv,
	.Author = "Zenderal"sv,
	.StructCompatibility = SKSE::StructCompatibility::Independent,
	.RuntimeCompatibility = SKSE::VersionIndependence::AddressLibrary)

namespace
{
	constexpr auto kIniPath = "Data/SKSE/Plugins/ZenOCPASecondKey.ini";
	constexpr auto kOcpaUserIni = "Data/MCM/Settings/OCPA.ini";
	constexpr auto kOcpaDefaultIni = "Data/MCM/Config/OCPA/settings.ini";
	constexpr int  kUnbound = -1;

	constexpr RE::FormID kActionRightAttack = 0x13005;
	constexpr RE::FormID kActionRightPowerAttack = 0x13383;

	// Settings: ours, then OCPA's.
	int   g_key = 281;
	bool  g_log = true;
	int   g_ocpaKey = kUnbound;
	int   g_modifierKey = kUnbound;
	bool  g_onlyDuringAttack = false;
	bool  g_onlyFirstAttack = false;
	bool  g_allowZeroStamina = true;
	bool  g_queue = true;
	float g_queueExpire = 0.2f;

	bool                 g_modifierHeld = false;
	RE::BGSAction*       g_queued = nullptr;
	std::uint64_t        g_queuedAtMs = 0;
	std::uint64_t        g_altAttackDueMs = 0;

	std::uint64_t NowMs() { return ::GetTickCount64(); }

	// OCPA's key numbering (SKSE's macro codes): keyboard 0-255, mouse 256+, gamepad 266-281.
	int KeyCode(const RE::ButtonEvent* a_button)
	{
		const auto id = a_button->GetIDCode();
		switch (a_button->GetDevice()) {
		case RE::INPUT_DEVICE::kKeyboard:
			return static_cast<int>(id);
		case RE::INPUT_DEVICE::kMouse:
			return 256 + static_cast<int>(id);
		case RE::INPUT_DEVICE::kGamepad:
			{
				using Key = RE::BSWin32GamepadDevice::Key;
				switch (static_cast<Key>(id)) {
				case Key::kUp:            return 266;
				case Key::kDown:          return 267;
				case Key::kLeft:          return 268;
				case Key::kRight:         return 269;
				case Key::kStart:         return 270;
				case Key::kBack:          return 271;
				case Key::kLeftThumb:     return 272;
				case Key::kRightThumb:    return 273;
				case Key::kLeftShoulder:  return 274;
				case Key::kRightShoulder: return 275;
				case Key::kA:             return 276;
				case Key::kB:             return 277;
				case Key::kX:             return 278;
				case Key::kY:             return 279;
				case Key::kLeftTrigger:   return 280;
				case Key::kRightTrigger:  return 281;
				default:                  return kUnbound;
				}
			}
		default:
			return kUnbound;
		}
	}

	// Same entry point OCPA uses to make the player perform a BGSAction.
	bool PerformAction(RE::BGSAction* a_action, RE::Actor* a_actor)
	{
		std::unique_ptr<RE::TESActionData> data(RE::TESActionData::Create());
		if (!data) {
			return false;
		}
		data->source = RE::NiPointer<RE::TESObjectREFR>(a_actor);
		data->action = a_action;
		using func_t = bool(RE::TESActionData*);
		static REL::Relocation<func_t> func{ RELOCATION_ID(40551, 41557) };
		return func(data.get());
	}

	void TryAction(RE::FormID a_id)
	{
		auto* player = RE::PlayerCharacter::GetSingleton();
		auto* action = RE::TESForm::LookupByID<RE::BGSAction>(a_id);
		if (!player || !action) {
			return;
		}
		if (PerformAction(action, player)) {
			if (g_queued == action) {
				g_queued = nullptr;
			}
		} else if (g_queue && a_id == kActionRightPowerAttack) {
			g_queued = action;
			g_queuedAtMs = NowMs();
		}
	}

	bool IsAttacking(RE::PlayerCharacter* a_player)
	{
		const auto state = a_player->AsActorState()->actorState1.meleeAttackState;
		return state >= RE::ATTACK_STATE_ENUM::kDraw && state <= RE::ATTACK_STATE_ENUM::kBash;
	}

	// OCPA's canProcessPowerAttack().
	bool CanPowerAttack(RE::PlayerCharacter* a_player)
	{
		auto* ui = RE::UI::GetSingleton();
		if (!ui || ui->GameIsPaused() || ui->IsMenuOpen(RE::DialogueMenu::MENU_NAME)) {
			return false;
		}
		if (a_player->IsOnMount() || a_player->IsInKillMove()) {
			return false;
		}
		if (a_player->AsActorState()->actorState1.sitSleepState != RE::SIT_SLEEP_STATE::kNormal) {
			return false;
		}
		return g_allowZeroStamina || a_player->AsActorValueOwner()->GetActorValue(RE::ActorValue::kStamina) > 0;
	}

	// OCPA's PowerAttack().
	void PowerAttack(RE::PlayerCharacter* a_player)
	{
		bool jumping = false;
		bool blocking = false;
		a_player->GetGraphVariableBool("bInJumpState"sv, jumping);
		a_player->GetGraphVariableBool("IsBlocking"sv, blocking);
		if (jumping || blocking) {
			SKSE::GetTaskInterface()->AddTask([] { TryAction(kActionRightAttack); });
			g_altAttackDueMs = NowMs() + 200;
		} else {
			SKSE::GetTaskInterface()->AddTask([] { TryAction(kActionRightPowerAttack); });
		}
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
			auto* player = RE::PlayerCharacter::GetSingleton();
			if (!player || g_key == kUnbound || g_key == g_ocpaKey) {
				return RE::BSEventNotifyControl::kContinue;
			}
			for (auto* event = a_event ? *a_event : nullptr; event; event = event->next) {
				if (event->GetEventType() != RE::INPUT_EVENT_TYPE::kButton) {
					continue;
				}
				const auto* button = event->AsButtonEvent();
				const int   code = button ? KeyCode(button) : kUnbound;
				if (code == kUnbound) {
					continue;
				}
				if (code == g_modifierKey) {
					if (button->IsDown()) {
						g_modifierHeld = true;
					} else if (button->IsUp()) {
						g_modifierHeld = false;
					}
				}
				if (code != g_key || !button->IsDown() || !CanPowerAttack(player)) {
					continue;
				}
				// OCPA's modifier / attack-only rules (iModifierKey < 2 means no modifier).
				const bool attacking = IsAttacking(player);
				bool       want = !g_onlyDuringAttack || attacking;
				if (want && g_modifierKey >= 2) {
					want = g_onlyFirstAttack ? (attacking || g_modifierHeld) : g_modifierHeld;
				}
				if (g_log) {
					SKSE::log::info("Second key {} pressed (attacking {}, modifier held {}) -> {}", code, attacking, g_modifierHeld,
						want ? "power attack" : "ignored");
				}
				if (want) {
					PowerAttack(player);
				}
			}
			return RE::BSEventNotifyControl::kContinue;
		}
	};

	// Actor::Update (vfunc 0xAD) on the player's vtable: once per frame while the game runs.
	struct PlayerUpdate
	{
		static void thunk(RE::PlayerCharacter* a_this, float a_delta)
		{
			func(a_this, a_delta);
			const auto now = NowMs();
			if (g_altAttackDueMs && now >= g_altAttackDueMs) {
				g_altAttackDueMs = 0;
				TryAction(kActionRightPowerAttack);
			}
			if (g_queued) {
				if (now - g_queuedAtMs > static_cast<std::uint64_t>(g_queueExpire * 1000.0f)) {
					g_queued = nullptr;
				} else if (PerformAction(g_queued, a_this)) {
					g_queued = nullptr;
				}
			}
		}
		static inline REL::Relocation<decltype(thunk)> func;
	};

	// MCM Helper writes OCPA.ini with a UTF-8 BOM, so parse it ourselves (as ZenBlockReleaseFix does for DWP).
	std::optional<std::string> ReadIni(const char* a_path, std::string_view a_section, std::string_view a_key)
	{
		std::ifstream file{ a_path };
		if (!file) {
			return std::nullopt;
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
			if (inSection && eq != std::string_view::npos && iequals(trim(view.substr(0, eq)), a_key)) {
				return std::string{ trim(view.substr(eq + 1)) };
			}
		}
		return std::nullopt;
	}

	// User MCM settings first, then OCPA's shipped defaults, then OCPA's hard-coded default.
	std::string OcpaValue(std::string_view a_section, std::string_view a_key, std::string_view a_default)
	{
		if (auto v = ReadIni(kOcpaUserIni, a_section, a_key)) {
			return *v;
		}
		if (auto v = ReadIni(kOcpaDefaultIni, a_section, a_key)) {
			return *v;
		}
		return std::string{ a_default };
	}

	int ToInt(const std::string& a_value, int a_default)
	{
		int result{};
		const auto* end = a_value.data() + a_value.size();
		return std::from_chars(a_value.data(), end, result).ec == std::errc{} ? result : a_default;
	}

	float ToFloat(const std::string& a_value, float a_default)
	{
		float result{};
		const auto* end = a_value.data() + a_value.size();
		return std::from_chars(a_value.data(), end, result).ec == std::errc{} ? result : a_default;
	}

	void LoadSettings()
	{
		g_key = ToInt(ReadIni(kIniPath, "General"sv, "iKeycode"sv).value_or("281"), 281);
		g_log = ToInt(ReadIni(kIniPath, "General"sv, "bLog"sv).value_or("1"), 1) != 0;

		g_ocpaKey = ToInt(OcpaValue("General"sv, "iKeycode"sv, "257"), 257);
		g_modifierKey = ToInt(OcpaValue("General"sv, "iModifierKey"sv, "-1"), kUnbound);
		g_onlyDuringAttack = ToInt(OcpaValue("General"sv, "bOnlyDuringAttack"sv, "1"), 1) > 0;
		g_onlyFirstAttack = ToInt(OcpaValue("General"sv, "bSkipModifierDuringCombo"sv, "0"), 0) > 0;
		g_allowZeroStamina = ToInt(OcpaValue("General"sv, "bAllowZeroStamina"sv, "1"), 1) > 0;
		g_queue = ToInt(OcpaValue("MCO"sv, "bQueuePowerAttack"sv, "1"), 1) > 0;
		g_queueExpire = std::clamp(ToFloat(OcpaValue("MCO"sv, "fQueueExpire"sv, "0.2"), 0.2f), 0.0f, 10.0f);

		SKSE::log::info("Second key {}; OCPA key {} modifier {} onlyDuringAttack {} skipModifierDuringCombo {} allowZeroStamina {} queue {} ({} s)",
			g_key, g_ocpaKey, g_modifierKey, g_onlyDuringAttack, g_onlyFirstAttack, g_allowZeroStamina, g_queue, g_queueExpire);
		if (g_key == g_ocpaKey) {
			SKSE::log::warn("Second key is OCPA's own key - nothing to add, staying idle");
		}
	}

	// OCPA re-reads its ini when a save loads and when the Journal (MCM) closes; follow it.
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
			if (a_event && !a_event->opening && a_event->menuName == RE::JournalMenu::MENU_NAME) {
				LoadSettings();
			}
			return RE::BSEventNotifyControl::kContinue;
		}
	};

	void MessageHandler(SKSE::MessagingInterface::Message* a_msg)
	{
		switch (a_msg->type) {
		case SKSE::MessagingInterface::kInputLoaded:
			if (auto* input = RE::BSInputDeviceManager::GetSingleton()) {
				input->AddEventSink(InputSink::GetSingleton());
				SKSE::log::info("Input sink registered");
			}
			break;
		case SKSE::MessagingInterface::kDataLoaded:
			if (auto* ui = RE::UI::GetSingleton()) {
				ui->AddEventSink<RE::MenuOpenCloseEvent>(MenuSink::GetSingleton());
			}
			break;
		case SKSE::MessagingInterface::kPreLoadGame:
		case SKSE::MessagingInterface::kNewGame:
			g_modifierHeld = false;
			g_queued = nullptr;
			g_altAttackDueMs = 0;
			LoadSettings();
			break;
		default:
			break;
		}
	}
}

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	SKSE::log::info("ZenOCPASecondKey 1.0.0 loading, runtime {}", REL::Module::get().version().string());
	LoadSettings();

	REL::Relocation<std::uintptr_t> vtbl{ RE::VTABLE_PlayerCharacter[0] };
	PlayerUpdate::func = vtbl.write_vfunc(0xAD, PlayerUpdate::thunk);
	SKSE::log::info("PlayerCharacter::Update hooked");

	SKSE::GetMessagingInterface()->RegisterListener(MessageHandler);
	return true;
}
