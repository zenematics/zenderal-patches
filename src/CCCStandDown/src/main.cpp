#include "pch.h"

#define SMOOTHCAM_API_COMMONLIB
#include "SmoothCamAPI.h"

// Cinematic Conversation Camera 1.5.0 (SceneDirector.dll, github.com/fatalCMD/ccc) pulls every
// conversation into a third-person crew camera. Enderal's memory scenes are built for first person:
// MQP01 ("A Summer's Day", the player as a child talking to Daddy 00046F93) shrinks the adult player
// with SetScale(0.85) and locks the view with ForceFirstPerson + DisablePlayerControls(abCamSwitch);
// MQP03's vision, the Myrad flight and others hide the player with SetAlpha(0). Filmed from outside,
// those scenes show a shrunken adult or frame an invisible speaker.
//
// CCC takes the camera through SmoothCam's API before it stages anything, and declines when another
// plugin already holds it (src/Compat/SmoothCam.cpp, Acquire: AlreadyTaken -> "not staging this
// conversation"; every restage and resume goes through the same Acquire). So while the player is
// shrunk, a child race or faded out, this plugin holds SmoothCam's camera, and releases it the frame
// the player is back to normal. Nothing in CCC is patched. Requests are made from PlayerCharacter::Update
// on the main thread, where SmoothCam accepts them (it answers BadThread elsewhere) and where CCC makes its own.

SKSEPluginInfo(
	.Version = REL::Version{ 1, 0, 0, 0 },
	.Name = "ZenCCCStandDown"sv,
	.Author = "Zenderal"sv,
	.StructCompatibility = SKSE::StructCompatibility::Independent,
	.RuntimeCompatibility = SKSE::VersionIndependence::AddressLibrary)

namespace
{
	constexpr auto kIniPath = "Data/SKSE/Plugins/ZenCCCStandDown.ini";

	// Retry interval while someone else (CCC mid-conversation) holds the camera.
	constexpr std::uint64_t kRetryMs = 250;

	float g_scaleBelow{ 0.90f };  // ref scale under this = shrunk to a child (MQP01 uses 0.85)
	float g_alphaBelow{ 0.99f };  // alpha under this = the player has been hidden or faded by a script
	bool  g_childRace{ true };
	bool  g_log{ true };

	SmoothCamAPI::IVSmoothCam1* g_api{ nullptr };
	bool                        g_holding{ false };
	bool                        g_wanted{ false };
	std::uint64_t               g_nextTryMs{ 0 };
	bool                        g_takenReported{ false };

	std::uint64_t NowMs() { return ::GetTickCount64(); }

	// Why the cinematic camera should stay out, or empty when it may film.
	std::string StandDownReason(RE::PlayerCharacter* a_player)
	{
		const float scale = a_player->GetScale();
		if (scale < g_scaleBelow) {
			return std::format("player scale {:.2f}", scale);
		}
		if (g_childRace) {
			if (const auto* race = a_player->GetRace(); race && race->IsChildRace()) {
				return std::format("child race {}", race->GetFormEditorID());
			}
		}
		const float alpha = a_player->GetAlpha();
		if (alpha < g_alphaBelow) {
			return std::format("player alpha {:.2f}", alpha);
		}
		return {};
	}

	void Hold(const std::string& a_reason)
	{
		const auto now = NowMs();
		if (now < g_nextTryMs) {
			return;
		}
		const auto result = g_api->RequestCameraControl(SKSE::GetPluginHandle());
		switch (result) {
		case SmoothCamAPI::APIResult::OK:
		case SmoothCamAPI::APIResult::AlreadyGiven:
			g_holding = true;
			g_takenReported = false;
			if (g_log) {
				SKSE::log::info("Holding SmoothCam's camera ({}); the cinematic conversation camera stands down", a_reason);
			}
			return;
		case SmoothCamAPI::APIResult::AlreadyTaken:
			// Usually CCC itself, staging a conversation that was already running when the scene began.
			if (g_log && !std::exchange(g_takenReported, true)) {
				SKSE::log::info("Wanted the camera ({}), but plugin {} holds it; retrying until it lets go", a_reason,
					static_cast<std::uint32_t>(g_api->GetCameraOwner()));
			}
			break;
		default:
			if (g_log && !std::exchange(g_takenReported, true)) {
				SKSE::log::warn("SmoothCam refused camera control (result {}); retrying", static_cast<std::uint32_t>(result));
			}
			break;
		}
		g_nextTryMs = now + kRetryMs;
	}

	void Release()
	{
		const auto result = g_api->ReleaseCameraControl(SKSE::GetPluginHandle());
		g_holding = false;
		if (g_log) {
			SKSE::log::info("Released SmoothCam's camera (result {}); the cinematic conversation camera may film again",
				static_cast<std::uint32_t>(result));
		}
	}

	void Check(RE::PlayerCharacter* a_player)
	{
		if (!g_api) {
			return;
		}
		const auto reason = StandDownReason(a_player);
		const bool wanted = !reason.empty();
		if (wanted != g_wanted) {
			g_wanted = wanted;
			g_nextTryMs = 0;
			g_takenReported = false;
		}
		if (wanted && !g_holding) {
			Hold(reason);
		} else if (!wanted && g_holding) {
			Release();
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

	void LoadSettings()
	{
		const auto scalePct = ReadIniInt(kIniPath, "General"sv, "ScaleBelowPct"sv, 90);
		const auto alphaPct = ReadIniInt(kIniPath, "General"sv, "AlphaBelowPct"sv, 99);
		g_scaleBelow = static_cast<float>(scalePct) / 100.0f;
		g_alphaBelow = static_cast<float>(alphaPct) / 100.0f;
		g_childRace = ReadIniInt(kIniPath, "General"sv, "ChildRace"sv, 1) != 0;
		g_log = ReadIniInt(kIniPath, "General"sv, "Log"sv, 1) != 0;
		SKSE::log::info("ScaleBelowPct={} AlphaBelowPct={} ChildRace={} Log={}", scalePct, alphaPct, g_childRace, g_log);
	}
}

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	SKSE::log::info("ZenCCCStandDown 1.0.0 loading, runtime {}", REL::Module::get().version().string());
	LoadSettings();

	const auto* messaging = SKSE::GetMessagingInterface();
	const bool  registered = SmoothCamAPI::RegisterInterfaceLoaderCallback(messaging,
		[](void* a_instance, SmoothCamAPI::InterfaceVersion a_version) {
			// Every version derives from IVSmoothCam1, which holds the camera calls.
			g_api = reinterpret_cast<SmoothCamAPI::IVSmoothCam1*>(a_instance);
			SKSE::log::info("SmoothCam interface obtained (V{})", static_cast<int>(a_version) + 1);
		});
	if (!registered) {
		SKSE::log::warn("SmoothCam callback registration failed; nothing will be done");
	}

	messaging->RegisterListener([](SKSE::MessagingInterface::Message* a_msg) {
		if (a_msg->type == SKSE::MessagingInterface::kPostPostLoad) {
			// V2, as CCC asks for: proven against the SmoothCam this list ships.
			if (!SmoothCamAPI::RequestInterface(SKSE::GetMessagingInterface(), SmoothCamAPI::InterfaceVersion::V2)) {
				SKSE::log::warn("SmoothCam is not loaded; CCC then takes the camera directly and this plugin cannot stop it");
			}
		}
	});

	REL::Relocation<std::uintptr_t> vtbl{ RE::VTABLE_PlayerCharacter[0] };
	PlayerUpdate::func = vtbl.write_vfunc(0xAD, PlayerUpdate::thunk);
	SKSE::log::info("PlayerCharacter::Update hooked");
	return true;
}
