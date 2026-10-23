#include "pch.h"

#include <SimpleIni.h>

#include <filesystem>
#include <unordered_map>

// dTry's Key Utils binds keys to spells in Data/SKSE/Plugins/dtryKeyUtil/config/custom/*.ini: while a bound
// button is held the spell is on the player (AddSpell on press, RemoveSpell on release). The Stances mod's
// hotkeys work that way (F1-F4 and the D-pad keys -> stances_switchspell_*). On 1.7.104 the only
// DtryKeyUtil.dll that loads is PaulMix's "extend" v3.3, a rewrite with no config reader, and dTry's own AE
// 1.1 build uses the old Address Library format, which SKSE 2.3 refuses. This plugin re-implements just
// that key-trace part, following D7ry/DtryKeyUtil (src/inputEventHandler.cpp, src/inputHandler/inputTracer.cpp):
//   - sections KeyTrace_EventID_Keyboard / _Mouse / _GamePad: "<name> = <id>|<formID>|<plugin>", id is the
//     keyboard DX scan code, mouse button + 256, or gamepad button index + 266 (SKSE numbering);
//   - section KeyTrace_userEvent: "<name> = <user event>|<formID>|<plugin>";
//   - button events are ignored while the game is paused, as in dTry.
// Movement-direction tracing (Keytrace.esp 801-804) is left to PaulMix's DLL, which still does it.

SKSEPluginInfo(
	.Version = REL::Version{ 1, 0, 0, 0 },
	.Name = "ZenKeyTrace"sv,
	.Author = "Zenderal"sv,
	.StructCompatibility = SKSE::StructCompatibility::Independent,
	.RuntimeCompatibility = SKSE::VersionIndependence::AddressLibrary)

namespace
{
	constexpr auto          kConfigDir = "Data/SKSE/Plugins/dtryKeyUtil/config/custom";
	constexpr std::uint32_t kMouseOffset = 256;
	constexpr std::uint32_t kGamepadOffset = 266;
	constexpr std::uint32_t kInvalid = static_cast<std::uint32_t>(-1);

	using SpellList = std::vector<RE::SpellItem*>;
	std::unordered_map<std::uint32_t, SpellList> g_keyboard;
	std::unordered_map<std::uint32_t, SpellList> g_mouse;
	std::unordered_map<std::uint32_t, SpellList> g_gamepad;
	std::unordered_map<std::string, SpellList>   g_userEvent;

	std::vector<std::string> Tokenize(std::string_view a_line)
	{
		std::vector<std::string> out;
		for (auto part : a_line | std::views::split('|')) {
			std::string token(part.begin(), part.end());
			while (!token.empty() && std::isspace(static_cast<unsigned char>(token.back()))) {
				token.pop_back();
			}
			while (!token.empty() && std::isspace(static_cast<unsigned char>(token.front()))) {
				token.erase(token.begin());
			}
			if (!token.empty()) {
				out.push_back(std::move(token));
			}
		}
		return out;
	}

	RE::SpellItem* LookupSpell(const std::string& a_formID, const std::string& a_plugin)
	{
		std::uint32_t id = 0;
		try {
			id = static_cast<std::uint32_t>(std::stoul(a_formID, nullptr, 0));
		} catch (...) {
			SKSE::log::warn("  bad form ID '{}'", a_formID);
			return nullptr;
		}
		auto* spell = RE::TESDataHandler::GetSingleton()->LookupForm<RE::SpellItem>(id, a_plugin);
		if (!spell) {
			SKSE::log::warn("  no spell {:X} in {}", id, a_plugin);
		}
		return spell;
	}

	template <class Key, class Parse>
	int LoadSection(CSimpleIniA& a_ini, const char* a_section, std::unordered_map<Key, SpellList>& a_map, Parse a_parse)
	{
		int count = 0;
		CSimpleIniA::TNamesDepend keys;
		a_ini.GetAllKeys(a_section, keys);
		for (const auto& key : keys) {
			CSimpleIniA::TNamesDepend values;
			a_ini.GetAllValues(a_section, key.pItem, values);
			for (const auto& value : values) {
				const auto tokens = Tokenize(value.pItem);
				if (tokens.size() < 3) {
					SKSE::log::warn("  [{}] {} = '{}': expected <input>|<formID>|<plugin>", a_section, key.pItem, value.pItem);
					continue;
				}
				std::optional<Key> input = a_parse(tokens[0]);
				auto*              spell = LookupSpell(tokens[1], tokens[2]);
				if (!input || !spell) {
					continue;
				}
				a_map[*input].push_back(spell);
				SKSE::log::info("  [{}] {} -> {} ({:08X})", a_section, tokens[0], spell->GetName(), spell->GetFormID());
				++count;
			}
		}
		return count;
	}

	std::optional<std::uint32_t> ParseId(const std::string& a_text)
	{
		try {
			return static_cast<std::uint32_t>(std::stoul(a_text, nullptr, 0));
		} catch (...) {
			SKSE::log::warn("  bad input ID '{}'", a_text);
			return std::nullopt;
		}
	}

	void LoadConfigs()
	{
		std::error_code ec;
		if (!std::filesystem::is_directory(kConfigDir, ec)) {
			SKSE::log::error("{} not found; nothing to trace", kConfigDir);
			return;
		}
		int files = 0, bindings = 0;
		for (const auto& entry : std::filesystem::directory_iterator(kConfigDir, ec)) {
			if (!entry.is_regular_file() || entry.path().extension() != ".ini") {
				continue;
			}
			SKSE::log::info("Loading {}", entry.path().string());
			CSimpleIniA ini;
			ini.SetMultiKey(true);
			if (ini.LoadFile(entry.path().string().c_str()) < 0) {
				SKSE::log::warn("  could not read it");
				continue;
			}
			bindings += LoadSection(ini, "KeyTrace_EventID_Keyboard", g_keyboard, ParseId);
			bindings += LoadSection(ini, "KeyTrace_EventID_Mouse", g_mouse, ParseId);
			bindings += LoadSection(ini, "KeyTrace_EventID_GamePad", g_gamepad, ParseId);
			bindings += LoadSection(ini, "KeyTrace_userEvent", g_userEvent, [](const std::string& a_text) { return std::optional<std::string>(a_text); });
			++files;
		}
		SKSE::log::info("Loaded {} bindings from {} ini files", bindings, files);
	}

	std::uint32_t GamepadIndex(std::uint32_t a_key)
	{
		using Key = RE::BSWin32GamepadDevice::Key;
		switch (static_cast<Key>(a_key)) {
		case Key::kUp: return 0;
		case Key::kDown: return 1;
		case Key::kLeft: return 2;
		case Key::kRight: return 3;
		case Key::kStart: return 4;
		case Key::kBack: return 5;
		case Key::kLeftThumb: return 6;
		case Key::kRightThumb: return 7;
		case Key::kLeftShoulder: return 8;
		case Key::kRightShoulder: return 9;
		case Key::kA: return 10;
		case Key::kB: return 11;
		case Key::kX: return 12;
		case Key::kY: return 13;
		case Key::kLeftTrigger: return 14;
		case Key::kRightTrigger: return 15;
		default: return kInvalid;
		}
	}

	void Apply(const SpellList& a_spells, bool a_down)
	{
		auto* player = RE::PlayerCharacter::GetSingleton();
		if (!player) {
			return;
		}
		for (auto* spell : a_spells) {
			if (a_down) {
				player->AddSpell(spell);
			} else {
				player->RemoveSpell(spell);
			}
		}
	}

	template <class Key>
	void Trace(const std::unordered_map<Key, SpellList>& a_map, const Key& a_key, bool a_down)
	{
		if (const auto it = a_map.find(a_key); it != a_map.end()) {
			Apply(it->second, a_down);
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
			auto* ui = RE::UI::GetSingleton();
			if (!a_event || !ui || ui->GameIsPaused()) {
				return RE::BSEventNotifyControl::kContinue;
			}
			for (auto* event = *a_event; event; event = event->next) {
				if (event->GetEventType() != RE::INPUT_EVENT_TYPE::kButton) {
					continue;
				}
				const auto* button = static_cast<RE::ButtonEvent*>(event);
				const bool  down = button->IsDown();
				if (!down && !button->IsUp()) {
					continue;
				}
				if (!g_userEvent.empty()) {
					Trace(g_userEvent, std::string(button->QUserEvent().c_str()), down);
				}
				const std::uint32_t code = button->GetIDCode();
				switch (button->GetDevice()) {
				case RE::INPUT_DEVICE::kKeyboard:
					Trace(g_keyboard, code, down);
					break;
				case RE::INPUT_DEVICE::kMouse:
					Trace(g_mouse, code + kMouseOffset, down);
					break;
				case RE::INPUT_DEVICE::kGamepad:
					if (const auto index = GamepadIndex(code); index != kInvalid) {
						Trace(g_gamepad, index + kGamepadOffset, down);
					}
					break;
				default:
					break;
				}
			}
			return RE::BSEventNotifyControl::kContinue;
		}
	};
}

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	SKSE::log::info("ZenKeyTrace 1.0.0 loading, runtime {}", REL::Module::get().version().string());
	SKSE::GetMessagingInterface()->RegisterListener([](SKSE::MessagingInterface::Message* a_msg) {
		if (a_msg->type == SKSE::MessagingInterface::kDataLoaded) {
			LoadConfigs();
			if (auto* devices = RE::BSInputDeviceManager::GetSingleton()) {
				devices->AddEventSink(InputSink::GetSingleton());
				SKSE::log::info("Input sink registered");
			}
		}
	});
	return true;
}
