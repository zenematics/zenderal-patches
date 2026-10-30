#include "pch.h"

// A lightning strike tilts the sun's directional light toward the zenith for the length of the flash (heading kept,
// elevation 35° -> 85° at flash 1, falling back as the flash fades over fWeatherFlashDuration 0.5 s), while the sun
// itself stays put (ZenSkySyncTrace, 2026-10-29). With Bottled Shaders' Sky Sync on, the sun shadows follow that light
// up and back down, so every strike reads as daylight sweeping across the scene. Sky Sync's own options do not reach
// it (ShadowTransitionDuration 0 and UseAlternateSunPath false were tried, 2026-10-23).
//
// This chains after Sky Sync's Sky::Update hook (Detours follows its jump) and, while the sky's flash is above 0, puts
// the light back on the rotation it had on the last frame without a flash. The flash's colour and ambient boost are
// left alone, so a strike still lights the scene. For the first strikes it also logs, from an SKSE task later in the
// same frame, whether the light is still held there (if something after Sky::Update tilted it again, the log says so).
// Log: My Games/Skyrim Special Edition/SKSE/ZenSkySyncLightning.log

SKSEPluginInfo(
	.Version = REL::Version{ 1, 0, 0, 0 },
	.Name = "ZenSkySyncLightning"sv,
	.Author = "Zenderal"sv,
	.StructCompatibility = SKSE::StructCompatibility::Independent,
	.RuntimeCompatibility = SKSE::VersionIndependence::AddressLibrary)

namespace
{
	using Update_t = void (*)(RE::Sky*);
	Update_t g_update{ nullptr };

	constexpr int kLoggedStrikes = 5;

	RE::NiMatrix3     g_held{};
	bool              g_haveHeld{ false };
	bool              g_wasFlash{ false };
	int               g_strikes{ 0 };
	int               g_strikeLines{ 0 };
	std::atomic<bool> g_checkQueued{ false };

	std::string Dir(const RE::NiMatrix3& a_m)
	{
		// the light shines along -column 0 (Sky Sync's SetLighting writes entry[i][0] = -dir)
		RE::NiPoint3 v{ -a_m.entry[0][0], -a_m.entry[1][0], -a_m.entry[2][0] };
		const float  len = v.Length();
		if (len < 1e-6f) {
			return "(none)"s;
		}
		v /= len;
		constexpr float deg = 57.2957795f;
		return std::format("h{:.2f} e{:.2f}", std::atan2(v.y, v.x) * deg, std::asin(std::clamp(v.z, -1.0f, 1.0f)) * deg);
	}

	void CheckLater(float a_flash)
	{
		if (g_checkQueued.exchange(true)) {
			return;
		}
		SKSE::GetTaskInterface()->AddTask([a_flash] {
			g_checkQueued = false;
			auto* sky = RE::Sky::GetSingleton();
			if (!sky || !sky->sun || !sky->sun->light) {
				return;
			}
			const auto& m = sky->sun->light->local.rotate;
			SKSE::log::info("    later in frame: light {} ({})", Dir(m), Dir(m) == Dir(g_held) ? "still held"sv : "TILTED AGAIN"sv);
			(void)a_flash;
		});
	}

	void UpdateHook(RE::Sky* a_sky)
	{
		g_update(a_sky);

		if (!a_sky || !a_sky->sun || !a_sky->sun->light) {
			return;
		}
		auto&       light = *a_sky->sun->light;
		const float flash = a_sky->flash;

		if (flash <= 0.0f) {
			g_held = light.local.rotate;
			g_haveHeld = true;
			g_wasFlash = false;
			return;
		}
		if (!g_haveHeld) {
			return;
		}

		if (!g_wasFlash) {
			++g_strikes;
			g_strikeLines = 0;
			if (g_strikes <= kLoggedStrikes) {
				SKSE::log::info("strike {}: holding light at {}", g_strikes, Dir(g_held));
			}
		}
		g_wasFlash = true;

		if (g_strikes <= kLoggedStrikes && g_strikeLines < 40) {
			++g_strikeLines;
			SKSE::log::info("  flash {:.3f}: after Sky::Update light {} -> {}", flash, Dir(light.local.rotate), Dir(g_held));
			CheckLater(flash);
		}

		light.local.rotate = g_held;
		RE::NiUpdateData data;
		light.Update(data);
	}

	void Install()
	{
		const auto  target = REL::RelocationID(25682, 26229).address();
		const auto* bytes = reinterpret_cast<const std::uint8_t*>(target);
		const bool  hooked = bytes[0] == 0xE9 || (bytes[0] == 0xFF && bytes[1] == 0x25);
		if (!hooked) {
			SKSE::log::info("Sky::Update is not hooked (first byte {:02X}): Sky Sync inactive, not installing", bytes[0]);
			return;
		}
		g_update = reinterpret_cast<Update_t>(target);
		DetourTransactionBegin();
		DetourUpdateThread(GetCurrentThread());
		DetourAttach(reinterpret_cast<PVOID*>(&g_update), reinterpret_cast<PVOID>(&UpdateHook));
		const auto err = DetourTransactionCommit();
		SKSE::log::info("hooked Sky::Update after Sky Sync: {}", err == NO_ERROR ? "ok"sv : "FAILED"sv);
	}
}

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	SKSE::log::info("ZenSkySyncLightning 1.0.0 loading, runtime {}", REL::Module::get().version().string());
	SKSE::GetMessagingInterface()->RegisterListener([](SKSE::MessagingInterface::Message* a_msg) {
		if (a_msg->type == SKSE::MessagingInterface::kDataLoaded) {
			Install();
		}
	});
	return true;
}
