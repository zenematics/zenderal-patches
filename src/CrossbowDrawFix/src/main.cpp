#include "pch.h"

// A crossbow draw (weapequip.hkx clip generator CrossBow_Equip, 1st and 3rd person) fires two behaviour
// triggers: arrowAttach@0.571, which sets the player's attack state to kBowAttached (9), and
// WeapEquip_Out at the end of the 1.47 s clip, after which the engine is back at kNone. If the draw is
// cut short - seen when drawing within ~0.3 s of a sprint, likely Sprint Draw And Sheath Fixes'
// SprintStop/SprintStart restart - arrowAttach has fired but WeapEquip_Out never does. The state stays
// kBowAttached, and the engine refuses sprinting and sheathing until a shot runs the bow attack cycle.
// Graph events (attackStop, bowEnd, reloadStop) do not clear it.
//
// Measured in game 2026-10-14 (attack state traced per frame): a normal draw holds kBowAttached ~0.9 s,
// a post-shot reload ~1.6 s before kBowNextAttack. This plugin returns a drawn crossbow's kBowAttached
// to kNone once it has lasted DrawHoldMs (default 1000) when it began from kNone (a draw), or HoldMs
// (default 2500) when it began anywhere else (a reload), with no equip in progress. 1.0.0 used 2500 for
// both: the reset worked (logged) but a 2.5 s lock still read as "did nothing" in game. 1.1.0's 1 s
// still read as stuck, so 1.2.0 also resets a draw's kBowAttached the moment Sprint or Ready Weapon is
// pressed or Sprint is held (the input the engine would refuse); on Ready Weapon it then sheathes, since that press is
// already spent. Clearing early is safe: a normal draw ends at kNone too, and attacks start from kNone.

SKSEPluginInfo(
	.Version = REL::Version{ 1, 2, 0, 0 },
	.Name = "ZenCrossbowDrawFix"sv,
	.Author = "Zenderal"sv,
	.StructCompatibility = SKSE::StructCompatibility::Independent,
	.RuntimeCompatibility = SKSE::VersionIndependence::AddressLibrary)

namespace
{
	constexpr auto kIniPath = "Data/SKSE/Plugins/ZenCrossbowDrawFix.ini";

	std::uint32_t g_holdMs{ 2500 };
	std::uint32_t g_drawHoldMs{ 1000 };
	bool          g_log{ true };

	std::uint64_t          g_attachedSinceMs{ 0 };  // 0 = not currently in kBowAttached
	bool                   g_fromDraw{ false };     // the current kBowAttached began from kNone
	RE::ATTACK_STATE_ENUM  g_prevState{ RE::ATTACK_STATE_ENUM::kNone };

	// Set by the input sink while Sprint is held / on the first frame of a Ready Weapon press; consumed by the update.
	bool g_sprintPressed{ false };
	bool g_readyPressed{ false };

	std::uint64_t NowMs() { return ::GetTickCount64(); }

	bool RightHandIsCrossbow(RE::PlayerCharacter* a_player)
	{
		const auto* weapon = a_player->GetEquippedObject(false);
		const auto* weap = weapon ? weapon->As<RE::TESObjectWEAP>() : nullptr;
		return weap && weap->IsCrossbow();
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
			const auto* strings = RE::UserEvents::GetSingleton();
			for (auto* event = a_event ? *a_event : nullptr; strings && event; event = event->next) {
				const auto* button = event->GetEventType() == RE::INPUT_EVENT_TYPE::kButton ? event->AsButtonEvent() : nullptr;
				if (!button || !button->IsPressed()) {
					continue;
				}
				const auto& userEvent = button->QUserEvent();
				if (userEvent == strings->sprint) {
					g_sprintPressed = true;  // held counts: the stuck draw usually comes straight out of a sprint
				} else if (userEvent == strings->readyWeapon && button->IsDown()) {
					g_readyPressed = true;
				}
			}
			return RE::BSEventNotifyControl::kContinue;
		}
	};

	void CheckStuckAttach(RE::PlayerCharacter* a_player)
	{
		const bool sprintPressed = std::exchange(g_sprintPressed, false);
		const bool readyPressed = std::exchange(g_readyPressed, false);

		auto* state = a_player->AsActorState();
		if (!state) {
			return;
		}
		const auto prev = g_prevState;
		g_prevState = state->GetAttackState();
		if (state->GetAttackState() != RE::ATTACK_STATE_ENUM::kBowAttached ||
			state->GetWeaponState() != RE::WEAPON_STATE::kDrawn || !RightHandIsCrossbow(a_player)) {
			g_attachedSinceMs = 0;
			return;
		}

		const auto now = NowMs();
		if (g_attachedSinceMs == 0) {
			g_attachedSinceMs = now;
			g_fromDraw = prev == RE::ATTACK_STATE_ENUM::kNone;
			return;
		}
		const bool onPress = g_fromDraw && (sprintPressed || readyPressed);
		if (!onPress) {
			if (now - g_attachedSinceMs < (g_fromDraw ? g_drawHoldMs : g_holdMs)) {
				return;
			}
			bool isEquipping = false;
			a_player->GetGraphVariableBool("IsEquipping"sv, isEquipping);
			if (isEquipping) {
				return;
			}
		}

		state->actorState1.meleeAttackState = RE::ATTACK_STATE_ENUM::kNone;
		if (g_log) {
			SKSE::log::info("Cleared kBowAttached after {} ms (began from {}; {})", now - g_attachedSinceMs,
				g_fromDraw ? "a draw" : "a reload",
				onPress ? (readyPressed ? "Ready Weapon pressed, sheathing" : "Sprint pressed") : "timer");
		}
		g_attachedSinceMs = 0;
		if (onPress && readyPressed) {
			a_player->DrawWeaponMagicHands(false);
		}
	}

	// Actor::Update (vfunc 0xAD) on the player's vtable: once per frame while the game runs.
	struct PlayerUpdate
	{
		static void thunk(RE::PlayerCharacter* a_this, float a_delta)
		{
			func(a_this, a_delta);
			CheckStuckAttach(a_this);
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

	void LoadSettings()
	{
		g_holdMs = ReadIniInt(kIniPath, "General"sv, "HoldMs"sv, 2500);
		g_drawHoldMs = ReadIniInt(kIniPath, "General"sv, "DrawHoldMs"sv, 1000);
		g_log = ReadIniInt(kIniPath, "General"sv, "Log"sv, 1) != 0;
		SKSE::log::info("DrawHoldMs={} HoldMs={} Log={}", g_drawHoldMs, g_holdMs, g_log);
	}
}

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	SKSE::log::info("ZenCrossbowDrawFix 1.2.0 loading, runtime {}", REL::Module::get().version().string());
	LoadSettings();

	REL::Relocation<std::uintptr_t> vtbl{ RE::VTABLE_PlayerCharacter[0] };
	PlayerUpdate::func = vtbl.write_vfunc(0xAD, PlayerUpdate::thunk);
	SKSE::log::info("PlayerCharacter::Update hooked");

	SKSE::GetMessagingInterface()->RegisterListener([](SKSE::MessagingInterface::Message* a_msg) {
		if (a_msg->type == SKSE::MessagingInterface::kInputLoaded) {
			if (auto* input = RE::BSInputDeviceManager::GetSingleton()) {
				input->AddEventSink(InputSink::GetSingleton());
				SKSE::log::info("Input sink registered");
			}
		}
	});
	return true;
}
