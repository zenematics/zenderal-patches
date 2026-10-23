#include "pch.h"

// While the player aims a bow, crossbow or musket in third person, the body is turned to the camera every
// frame. Pressing a strafe key together with forward (W+A) swung the body, and the weapon with it, off the
// crosshair and back again; TDM's "Face Crosshair Instantly" did not change it.
//
// The camera's world yaw in third person is the player's heading plus ThirdPersonState::freeRotation.x
// (the same sum TDM aims with). After Actor::Update each aiming frame the heading is set to that yaw and
// freeRotation.x zeroed, so the camera does not move and the body faces where it looks.
//
// Log=1 also records every aiming frame in which the heading moved by more than LogThresholdDegrees, split
// into "outside" (between our last correction and this frame's Actor::Update) and "inside" (during it). If
// the log stays quiet while the turn is still visible, the heading never moved and the turn is in the
// animation (pelvis/spine), not something this plugin can lock.

SKSEPluginInfo(
	.Version = REL::Version{ 1, 0, 0, 0 },
	.Name = "ZenAimFacingLock"sv,
	.Author = "Zenderal"sv,
	.StructCompatibility = SKSE::StructCompatibility::Independent,
	.RuntimeCompatibility = SKSE::VersionIndependence::AddressLibrary)

namespace
{
	constexpr auto  kIniPath = "Data/SKSE/Plugins/ZenAimFacingLock.ini";
	constexpr float kPi = 3.14159265358979f;
	constexpr float kTwoPi = 2.0f * kPi;

	bool  g_enabled{ true };
	bool  g_log{ true };
	float g_logThresholdRad{ 0.5f * kPi / 180.0f };

	bool          g_wasAiming{ false };
	float         g_lockedHeading{ 0.0f };  // heading this plugin left the player at last frame
	std::uint64_t g_lastLogMs{ 0 };

	std::uint64_t NowMs() { return ::GetTickCount64(); }

	float NormalAbsolute(float a)
	{
		a = std::fmod(a, kTwoPi);
		return a < 0.0f ? a + kTwoPi : a;
	}

	float NormalRelative(float a)
	{
		a = NormalAbsolute(a);
		return a > kPi ? a - kTwoPi : a;
	}

	float Degrees(float a_rad) { return a_rad * 180.0f / kPi; }

	bool IEquals(std::string_view a, std::string_view b)
	{
		return std::ranges::equal(a, b, [](char x, char y) { return std::tolower(static_cast<unsigned char>(x)) == std::tolower(static_cast<unsigned char>(y)); });
	}

	bool IsAiming(RE::PlayerCharacter* a_player)
	{
		const auto* state = a_player->AsActorState();
		if (!state || state->GetWeaponState() != RE::WEAPON_STATE::kDrawn || state->IsSprinting() || a_player->IsOnMount()) {
			return false;
		}
		const auto* object = a_player->GetEquippedObject(false);
		const auto* weap = object ? object->As<RE::TESObjectWEAP>() : nullptr;
		if (!weap || !(weap->IsBow() || weap->IsCrossbow())) {
			return false;
		}
		using enum RE::ATTACK_STATE_ENUM;
		switch (state->GetAttackState()) {
		case kBowDraw:
		case kBowDrawn:
		case kBowReleasing:
		case kBowReleased:
			return true;
		case kBowAttached:
			return weap->IsBow();  // a nocked arrow; for a crossbow/musket this is the reload
		default:
			return false;
		}
	}

	RE::ThirdPersonState* ThirdPerson()
	{
		auto* camera = RE::PlayerCamera::GetSingleton();
		auto* state = camera ? camera->currentState.get() : nullptr;
		return state && state->id == RE::CameraState::kThirdPerson ? static_cast<RE::ThirdPersonState*>(state) : nullptr;
	}

	void LogDrift(float a_outside, float a_inside, const RE::ThirdPersonState* a_tps)
	{
		if (!g_log || (std::fabs(a_outside) < g_logThresholdRad && std::fabs(a_inside) < g_logThresholdRad)) {
			return;
		}
		const auto now = NowMs();
		if (now - g_lastLogMs < 50) {
			return;
		}
		g_lastLogMs = now;
		const auto* controls = RE::PlayerControls::GetSingleton();
		const auto  move = controls ? controls->data.moveInputVec : RE::NiPoint2{};
		SKSE::log::info("Aiming: heading moved {:+.1f} deg outside Actor::Update, {:+.1f} deg inside; camera offset {:+.1f} deg; move input ({:+.2f}, {:+.2f})",
			Degrees(a_outside), Degrees(a_inside), Degrees(a_tps->freeRotation.x), move.x, move.y);
	}

	// Actor::Update (vfunc 0xAD) on the player's vtable: once per frame while the game runs.
	struct PlayerUpdate
	{
		static void thunk(RE::PlayerCharacter* a_this, float a_delta)
		{
			const float before = a_this->data.angle.z;
			func(a_this, a_delta);

			auto* tps = ThirdPerson();
			const bool aiming = tps && IsAiming(a_this);
			if (!aiming) {
				g_wasAiming = false;
				return;
			}

			const float after = a_this->data.angle.z;
			if (g_wasAiming) {
				LogDrift(NormalRelative(before - g_lockedHeading), NormalRelative(after - before), tps);
			}
			if (g_enabled && std::fabs(tps->freeRotation.x) > 1e-5f) {
				a_this->SetHeading(NormalAbsolute(after + tps->freeRotation.x));
				tps->freeRotation.x = 0.0f;
			}
			g_lockedHeading = a_this->data.angle.z;
			g_wasAiming = true;
		}
		static inline REL::Relocation<decltype(thunk)> func;
	};

	// GetPrivateProfileString can't be used: a relative path is looked up in the Windows directory, and a
	// UTF-8 BOM glues itself to the first section header (ZenBlockReleaseFix 1.0.0). Parse it ourselves.
	std::optional<std::string> ReadIniValue(const char* a_path, std::string_view a_section, std::string_view a_key)
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
				inSection = end != std::string_view::npos && IEquals(trim(view.substr(1, end - 1)), a_section);
				continue;
			}
			const auto eq = view.find('=');
			if (inSection && eq != std::string_view::npos && IEquals(trim(view.substr(0, eq)), a_key)) {
				return std::string{ trim(view.substr(eq + 1)) };
			}
		}
		return std::nullopt;
	}

	template <class T>
	T ReadIniNumber(std::string_view a_section, std::string_view a_key, T a_default)
	{
		const auto value = ReadIniValue(kIniPath, a_section, a_key);
		T          result{};
		if (value && std::from_chars(value->data(), value->data() + value->size(), result).ec == std::errc{}) {
			return result;
		}
		return a_default;
	}

	void LoadSettings()
	{
		g_enabled = ReadIniNumber<std::uint32_t>("General"sv, "Enabled"sv, 1) != 0;
		g_log = ReadIniNumber<std::uint32_t>("General"sv, "Log"sv, 1) != 0;
		g_logThresholdRad = std::max(0.0f, ReadIniNumber<float>("General"sv, "LogThresholdDegrees"sv, 0.5f)) * kPi / 180.0f;
		SKSE::log::info("Enabled={} Log={} LogThresholdDegrees={}", g_enabled, g_log, Degrees(g_logThresholdRad));
	}
}

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	SKSE::log::info("ZenAimFacingLock 1.0.0 loading, runtime {}", REL::Module::get().version().string());
	LoadSettings();

	REL::Relocation<std::uintptr_t> vtbl{ RE::VTABLE_PlayerCharacter[0] };
	PlayerUpdate::func = vtbl.write_vfunc(0xAD, PlayerUpdate::thunk);
	SKSE::log::info("PlayerCharacter::Update hooked");
	return true;
}
