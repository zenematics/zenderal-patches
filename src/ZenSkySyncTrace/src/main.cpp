#include "pch.h"

// Testing tool, not part of the list. With Bottled Shaders' Sky Sync on, each lightning strike in a storm turns into a
// long sweep of daylight and shadows (curator, 2026-10-23 and 2026-10-29). Sky Sync's ShadowTransitionDuration 0 and
// UseAlternateSunPath false did not stop it, so the sweep is not (only) Sky Sync's own fader. This reads, on the main
// thread once per frame (an SKSE task), and logs:
//   - the sky: game hour, weather, flash amount/timer, lighting transition;
//   - the sun: its node position, the engine's global sun position, its directional light's local and world direction;
//   - the sun shadow light (BSShadowDirectionalLight): sunVector, lastSunVector, sunUpdate, sunUpdateMode.
// Every frame from a strike (flash > 0) until 25 s after it, otherwise once a second. Directions are heading/elevation in
// degrees. Log: My Games/Skyrim Special Edition/SKSE/ZenSkySyncTrace.log
//
// 1.1.0 experiment (rivers/waterfalls flicker ~10 Hz with Sky Sync on, 2026-11-07): Pause or Numpad 5 (F10 is
// Bottled Shaders' overlay key) steps through freeze modes,
// applied after Sky::Update (Detours, chained after Sky Sync), each announced on screen and logged every frame for 6 s:
//   0 off; 1 hold the sun light's rotation; 2 also hold the sun node, glare node and global sun position;
//   3 hold only the sun node/glare/global position (light free).
// Mode 0 writes nothing, so with the key untouched this is still a read-only trace.

SKSEPluginInfo(
	.Version = REL::Version{ 1, 1, 0, 0 },
	.Name = "ZenSkySyncTrace"sv,
	.Author = "Zenderal"sv,
	.StructCompatibility = SKSE::StructCompatibility::Independent,
	.RuntimeCompatibility = SKSE::VersionIndependence::AddressLibrary)

namespace
{
	constexpr int          kMaxLines = 120000;
	constexpr std::int64_t kHotMs = 25000;

	std::atomic<bool> g_busy{ false };
	int               g_lines{ 0 };
	std::int64_t      g_hotUntil{ -1 };
	std::int64_t      g_nextCalm{ 0 };
	int               g_strikes{ 0 };
	bool              g_wasFlash{ false };
	std::atomic<int>          g_mode{ 0 };
	std::atomic<std::int64_t> g_freezeLogUntil{ -1 };

	std::int64_t NowMs()
	{
		static const auto start = std::chrono::steady_clock::now();
		return std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - start).count();
	}

	std::string Dir(RE::NiPoint3 a_v)
	{
		const float len = a_v.Length();
		if (len < 1e-6f) {
			return "(none)"s;
		}
		a_v /= len;
		constexpr float deg = 57.2957795f;
		return std::format("h{:7.2f} e{:6.2f}", std::atan2(a_v.y, a_v.x) * deg, std::asin(std::clamp(a_v.z, -1.0f, 1.0f)) * deg);
	}

	RE::NiPoint3 LightDir(const RE::NiMatrix3& a_m)
	{
		// Sky Sync writes entry[i][0] = -dir (SetLighting), so the light shines along -column 0
		return { -a_m.entry[0][0], -a_m.entry[1][0], -a_m.entry[2][0] };
	}

	RE::FormID WeatherID(const RE::TESWeather* a_w) { return a_w ? a_w->GetFormID() : 0; }

	void Tick()
	{
		if (g_lines >= kMaxLines) {
			return;
		}
		auto* sky = RE::Sky::GetSingleton();
		if (!sky || !sky->sun) {
			return;
		}
		const auto now = NowMs();
		const bool flash = sky->flash > 0.0f;
		if (flash && !g_wasFlash) {
			++g_strikes;
			SKSE::log::info("---- strike {} at {} ms (weather {:08X}) ----", g_strikes, now, WeatherID(sky->currentWeather));
		}
		g_wasFlash = flash;
		if (flash) {
			g_hotUntil = now + kHotMs;
		}
		const bool hot = now <= g_hotUntil || now <= g_freezeLogUntil.load();
		if (!hot) {
			if (now < g_nextCalm) {
				return;
			}
			g_nextCalm = now + 1000;
		}

		auto* sun = sky->sun;
		static auto* gSunPos = reinterpret_cast<RE::NiPoint3*>(REL::RelocationID(527924, 414871).address());
		const RE::NiPoint3 sunNode = sun->root ? sun->root->local.translate : RE::NiPoint3{};
		std::string lightLocal = "(no light)", lightWorld = "(no light)";
		if (sun->light) {
			lightLocal = Dir(LightDir(sun->light->local.rotate));
			lightWorld = Dir(LightDir(sun->light->world.rotate));
		}

		std::string shadow = "(no shadow light)";
		auto* ssn = RE::BSShaderManager::State::GetSingleton().shadowSceneNode[0];
		if (ssn) {
			if (auto* sl = ssn->GetRuntimeData().sunShadowDirLight) {
				auto& d = sl->GetShadowDirectionalLightRuntimeData();
				shadow = std::format("shadow sunVec {} last {} upd {:.3f} mode {}", Dir(d.sunVector), Dir(d.lastSunVector), d.sunUpdate, d.sunUpdateMode);
			}
		}

		SKSE::log::info("{:8} {}{} hr {:6.3f} wx {:08X}<{:08X} {:.2f} flash {:.3f} ft {} ltr {:.3f}/{:.3f} | sunNode {} gSun {} | light L {} W {} | {}",
			now, hot ? "*" : " ", g_mode.load(), sky->currentGameHour, WeatherID(sky->currentWeather), WeatherID(sky->lastWeather), sky->currentWeatherPct,
			sky->flash, sky->flashTime, sky->lightingTransition, sky->lightingTransitionTimer,
			Dir(sunNode), gSunPos ? Dir(*gSunPos) : "(none)"s, lightLocal, lightWorld, shadow);
		++g_lines;
	}

	void LogSettings()
	{
		if (auto* gs = RE::GameSettingCollection::GetSingleton()) {
			for (auto name : { "fWeatherFlashDirectional", "fWeatherFlashAmbient", "fWeatherFlashDuration", "fSunAlphaTransTime" }) {
				if (auto* s = gs->GetSetting(name)) {
					SKSE::log::info("GMST {} = {}", name, s->GetFloat());
				}
			}
		}
		auto logIni = [](auto* a_coll, std::string_view a_which) {
			if (!a_coll) {
				return;
			}
			for (auto name : { "fSunShadowUpdateTime:Display", "fSunUpdateThreshold:Display" }) {
				if (auto* s = a_coll->GetSetting(name)) {
					SKSE::log::info("{} {} = {}", a_which, name, s->GetFloat());
				}
			}
		};
		logIni(RE::INISettingCollection::GetSingleton(), "INI"sv);
		logIni(RE::INIPrefSettingCollection::GetSingleton(), "INIPref"sv);
	}

	// ---- 1.1.0 freeze experiment ----
	using Update_t = void (*)(RE::Sky*);
	Update_t g_update{ nullptr };

	struct Held
	{
		RE::NiMatrix3 lightRot{};
		RE::NiPoint3  sunPos{};
		RE::NiPoint3  glarePos{};
		RE::NiPoint3  gSun{};
	};
	Held g_held{};
	int  g_heldMode{ 0 };

	constexpr const char* kModeNames[] = { "off", "hold light", "hold light + sun position", "hold sun position only" };

	void UpdateHook(RE::Sky* a_sky)
	{
		g_update(a_sky);
		const int mode = g_mode.load();
		if (!a_sky || !a_sky->sun || !a_sky->sun->light || !a_sky->sun->root || !a_sky->sun->sunGlareNode) {
			return;
		}
		auto&       sun = *a_sky->sun;
		static auto* gSunPos = reinterpret_cast<RE::NiPoint3*>(REL::RelocationID(527924, 414871).address());
		if (mode != g_heldMode) {
			// capture this frame's values (after Sky Sync wrote them) when a mode starts
			g_held = { sun.light->local.rotate, sun.root->local.translate, sun.sunGlareNode->local.translate, gSunPos ? *gSunPos : RE::NiPoint3{} };
			g_heldMode = mode;
		}
		if (mode == 0) {
			return;
		}
		RE::NiUpdateData data;
		if (mode == 1 || mode == 2) {
			sun.light->local.rotate = g_held.lightRot;
			sun.light->Update(data);
		}
		if (mode == 2 || mode == 3) {
			sun.root->local.translate = g_held.sunPos;
			sun.sunGlareNode->local.translate = g_held.glarePos;
			if (gSunPos) {
				*gSunPos = g_held.gSun;
			}
			sun.root->Update(data);
		}
	}

	void InstallHook()
	{
		g_update = reinterpret_cast<Update_t>(REL::RelocationID(25682, 26229).address());
		DetourTransactionBegin();
		DetourUpdateThread(GetCurrentThread());
		DetourAttach(reinterpret_cast<PVOID*>(&g_update), reinterpret_cast<PVOID>(&UpdateHook));
		const auto err = DetourTransactionCommit();
		SKSE::log::info("freeze experiment (Pause / Numpad 5): hooked Sky::Update: {}", err == NO_ERROR ? "ok"sv : "FAILED"sv);
	}

	void Loop()
	{
		bool f10Was = false;
		for (;;) {
			std::this_thread::sleep_for(std::chrono::milliseconds(4));
			const bool f10 = (GetAsyncKeyState(VK_PAUSE) & 0x8000) != 0 || (GetAsyncKeyState(VK_NUMPAD5) & 0x8000) != 0;
			if (f10 && !f10Was) {
				const int mode = (g_mode.load() + 1) % 4;
				g_mode = mode;
				g_freezeLogUntil = NowMs() + 6000;
				SKSE::GetTaskInterface()->AddTask([mode] {
					SKSE::log::info("==== key: mode {} ({}) ====", mode, kModeNames[mode]);
					RE::SendHUDMessage::ShowHUDMessage(std::format("Sky Sync test {}: {}", mode, kModeNames[mode]).c_str());
				});
			}
			f10Was = f10;
			if (g_busy.exchange(true)) {
				continue;
			}
			SKSE::GetTaskInterface()->AddTask([] {
				Tick();
				g_busy = false;
			});
		}
	}
}

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	SKSE::log::info("ZenSkySyncTrace 1.1.0 loading, runtime {}", REL::Module::get().version().string());
	SKSE::GetMessagingInterface()->RegisterListener([](SKSE::MessagingInterface::Message* a_msg) {
		if (a_msg->type == SKSE::MessagingInterface::kDataLoaded) {
			LogSettings();
			InstallHook();
			std::thread(Loop).detach();
		}
	});
	return true;
}
