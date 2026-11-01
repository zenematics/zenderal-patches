#include "pch.h"

#include <Windows.h>
#include <optional>
#include <unordered_map>
#include <unordered_set>

// A gamepad entry in controlmap.txt may be a combo, "0x1000+0x0100" = hold A, press LB, and the custom
// map stores it as (modifier << 16 | key) = 0x10000100. On SSE 1.5.97 the engine does not check the
// modifier when it turns a gamepad press into a user event, so a button bound both alone and as the
// second key of a combo resolves to one of the two whether or not the modifier is held. Measured in
// this list with Complete Controller Setup's Layout 133 [verified by the user 2026-10-19]:
//
//     LB alone, and A+LB   -> Ready Weapon (sheathe/draw); Left Attack/Block never fires
//     D-pad Down alone     -> Quick Map (the B + D-pad Down combo), not Hotkey8
//     Back alone           -> Wait, so B+Back (Tween Menu) is dead
//     RB alone             -> Right Attack, so A+RB (Shout) is dead
//
// This plugin rebuilds the gameplay gamepad bindings from the same files the engine reads, and for
// every press of a button that has a combo binding it picks the event itself: the combo whose
// modifier is held, else the plain binding, else nothing. The choice is made on the press and kept
// for the held/up events of that press, so a release always reaches the handler that saw the press.
// It is applied in the InputEvent* sinks of MenuControls and PlayerControls (vfunc 0x01), before the
// engine's handlers compare userEvent; every sink registered later sees the corrected event.

SKSEPluginInfo(
	.Version = REL::Version{ 1, 0, 2, 0 },
	.Name = "ZenGamepadCombos"sv,
	.Author = "Zenderal"sv,
	.StructCompatibility = SKSE::StructCompatibility::Independent,
	.RuntimeCompatibility = SKSE::VersionIndependence::AddressLibrary)

namespace
{
	constexpr auto kIniPath = "Data/SKSE/Plugins/ZenGamepadCombos.ini";
	constexpr auto kControlMapPath = "Data/Interface/Controls/PC/controlmap.txt";
	// Where this list ships the custom map (Zenderal - Input Defaults puts it at the mod root).
	constexpr std::array kCustomMapPaths{ "Data/ControlMap_Custom.txt", "Data/Interface/Controls/PC/ControlMap_Custom.txt" };
	constexpr std::uint32_t kUnbound = 0xFF;

	bool g_enabled{ true };
	bool g_log{ true };
	bool g_logPresses{ true };
	// 1.0.2: off by default. The 1.0.1 log showed the engine already resolves combos correctly (A+LB came
	// in as Ready Weapon) and this plugin's held-button tracking turned it back into Left Attack.
	bool g_rewrite{ false };
	bool g_traceGraph{ true };

	struct Event
	{
		std::string                                          name;
		bool                                                 remap[3]{};  // keyboard, mouse, gamepad
		std::vector<std::pair<std::uint16_t, std::uint16_t>> pad;         // (modifier, key); modifier 0 = none
	};

	struct Binding
	{
		std::uint16_t     modifier;  // 0 = plain
		RE::BSFixedString event;
	};

	// Only buttons that carry at least one combo binding; every other button is left as the engine set it.
	std::unordered_map<std::uint32_t, std::vector<Binding>> g_table;
	std::unordered_map<std::uint32_t, RE::BSFixedString>    g_latched;  // per button: the event chosen on its press
	std::vector<std::uint32_t>                              g_held;     // gamepad buttons currently down
	bool                                                    g_ready{ false };

	std::string_view Trim(std::string_view s)
	{
		const auto b = s.find_first_not_of(" \t\r\n");
		const auto e = s.find_last_not_of(" \t\r\n");
		return b == std::string_view::npos ? std::string_view{} : s.substr(b, e - b + 1);
	}

	bool IEquals(std::string_view a, std::string_view b)
	{
		return std::ranges::equal(a, b, [](char x, char y) { return std::tolower(static_cast<unsigned char>(x)) == std::tolower(static_cast<unsigned char>(y)); });
	}

	std::optional<std::uint32_t> ParseHex(std::string_view s)
	{
		s = Trim(s);
		if (s.starts_with("0x"sv) || s.starts_with("0X"sv)) {
			s.remove_prefix(2);
		}
		std::uint32_t value{};
		if (s.empty() || std::from_chars(s.data(), s.data() + s.size(), value, 16).ec != std::errc{}) {
			return std::nullopt;
		}
		return value;
	}

	std::vector<std::string_view> SplitFields(std::string_view line)
	{
		std::vector<std::string_view> fields;
		std::size_t                   pos = 0;
		while (pos < line.size()) {
			const auto start = line.find_first_not_of('\t', pos);
			if (start == std::string_view::npos) {
				break;
			}
			auto end = line.find('\t', start);
			if (end == std::string_view::npos) {
				end = line.size();
			}
			if (const auto field = Trim(line.substr(start, end - start)); !field.empty()) {
				fields.push_back(field);
			}
			pos = end;
		}
		return fields;
	}

	// "0xff" | "0x0100" | "0x1000+0x0100" | comma-separated alternatives of those.
	std::vector<std::pair<std::uint16_t, std::uint16_t>> ParsePadField(std::string_view field)
	{
		std::vector<std::pair<std::uint16_t, std::uint16_t>> result;
		while (!field.empty()) {
			const auto comma = field.find(',');
			const auto alt = field.substr(0, comma);
			field = comma == std::string_view::npos ? std::string_view{} : field.substr(comma + 1);

			const auto plus = alt.find('+');
			const auto key = ParseHex(plus == std::string_view::npos ? alt : alt.substr(plus + 1));
			const auto mod = plus == std::string_view::npos ? std::optional<std::uint32_t>{ 0 } : ParseHex(alt.substr(0, plus));
			if (key && mod && *key != kUnbound) {
				result.emplace_back(static_cast<std::uint16_t>(*mod), static_cast<std::uint16_t>(*key));
			}
		}
		return result;
	}

	// The Main Gameplay context: the first block of entries after "// Main Gameplay", up to a blank line.
	std::vector<Event> ReadGameplayEvents()
	{
		std::vector<Event> events;
		std::ifstream      file{ kControlMapPath };
		if (!file) {
			SKSE::log::error("Cannot open {}", kControlMapPath);
			return events;
		}
		std::string line;
		bool        inSection = false;
		while (std::getline(file, line)) {
			const auto view = Trim(line);
			if (!inSection) {
				inSection = view.starts_with("//"sv) && Trim(view.substr(2)).starts_with("Main Gameplay"sv);
				continue;
			}
			if (view.empty()) {
				if (!events.empty()) {
					break;
				}
				continue;
			}
			if (view.starts_with("//"sv)) {
				continue;
			}
			const auto fields = SplitFields(line);
			if (fields.size() < 4) {
				continue;
			}
			Event event;
			event.name = std::string{ fields[0] };
			for (std::size_t i = 0; i < 3; ++i) {
				event.remap[i] = fields.size() > 4 + i && fields[4 + i] == "1"sv;
			}
			event.pad = ParsePadField(fields[3]);
			events.push_back(std::move(event));
		}
		return events;
	}

	// Binary custom map: three blocks (keyboard, mouse, gamepad), each a 3-byte header followed by one
	// 5-byte entry per remappable event of that device: u8 index into Main Gameplay, u32 big-endian key.
	// The engine drops the whole file if any block's count disagrees with controlmap.txt's remap flags,
	// so this does the same.
	void ApplyCustomMap(std::vector<Event>& a_events)
	{
		std::size_t counts[3]{};
		for (const auto& event : a_events) {
			for (std::size_t i = 0; i < 3; ++i) {
				counts[i] += event.remap[i] ? 1 : 0;
			}
		}
		for (const auto* path : kCustomMapPaths) {
			std::ifstream file{ path, std::ios::binary };
			if (!file) {
				continue;
			}
			const std::vector<std::uint8_t> data{ std::istreambuf_iterator<char>{ file }, {} };
			const auto expected = 9 + 5 * (counts[0] + counts[1] + counts[2]);
			if (data.size() != expected) {
				SKSE::log::warn("{}: {} bytes, expected {} for {}/{}/{} remappable events - ignored, as the engine would",
					path, data.size(), expected, counts[0], counts[1], counts[2]);
				return;
			}
			std::size_t pos = 3 + 5 * counts[0] + 3 + 5 * counts[1] + 3;
			std::size_t applied = 0;
			for (std::size_t n = 0; n < counts[2]; ++n, pos += 5) {
				const auto index = data[pos];
				const std::uint32_t value = (std::uint32_t{ data[pos + 1] } << 24) | (std::uint32_t{ data[pos + 2] } << 16) |
				                            (std::uint32_t{ data[pos + 3] } << 8) | std::uint32_t{ data[pos + 4] };
				if (index >= a_events.size() || !a_events[index].remap[2]) {
					continue;
				}
				auto& pad = a_events[index].pad;
				pad.clear();
				if ((value & 0xFFFF) != kUnbound) {
					pad.emplace_back(static_cast<std::uint16_t>(value >> 16), static_cast<std::uint16_t>(value & 0xFFFF));
				}
				++applied;
			}
			SKSE::log::info("{}: applied {} gamepad bindings", path, applied);
			return;
		}
		SKSE::log::info("No ControlMap_Custom.txt found; using controlmap.txt alone");
	}

	void BuildTable()
	{
		g_table.clear();
		g_latched.clear();
		auto events = ReadGameplayEvents();
		SKSE::log::info("{}: {} Main Gameplay events", kControlMapPath, events.size());
		if (events.empty()) {
			return;
		}
		ApplyCustomMap(events);

		std::unordered_map<std::uint32_t, std::vector<Binding>> all;
		for (const auto& event : events) {
			for (const auto& [mod, key] : event.pad) {
				all[key].push_back({ mod, RE::BSFixedString{ event.name } });
			}
		}
		for (auto& [key, bindings] : all) {
			if (std::ranges::any_of(bindings, [](const Binding& b) { return b.modifier != 0; })) {
				for (const auto& b : bindings) {
					SKSE::log::info("  pad 0x{:04X}: {} {}", key, b.modifier ? fmt::format("held 0x{:04X} ->", b.modifier) : "alone       ->"s, b.event.c_str());
				}
				g_table.emplace(key, std::move(bindings));
			}
		}
		g_ready = !g_table.empty();
		SKSE::log::info("{} gamepad buttons carry combos", g_table.size());
	}

	// What the engine itself loaded, for comparison with the table above.
	void LogEngineMappings()
	{
		const auto* map = RE::ControlMap::GetSingleton();
		const auto* context = map ? map->controlMap[RE::UserEvents::INPUT_CONTEXT_ID::kGameplay] : nullptr;
		if (!context) {
			return;
		}
		for (const auto& m : context->deviceMappings[RE::INPUT_DEVICE::kGamepad]) {
			if (g_table.contains(m.inputKey)) {
				SKSE::log::info("  engine: pad 0x{:04X} modifier 0x{:04X} linked={} -> {}", m.inputKey, m.modifier, m.linked, m.eventID.c_str());
			}
		}
	}

	bool InGameplayContext()
	{
		const auto* map = RE::ControlMap::GetSingleton();
		if (!map) {
			return false;
		}
		const auto& stack = map->GetRuntimeData().contextPriorityStack;
		return !stack.empty() && stack.back() == RE::UserEvents::INPUT_CONTEXT_ID::kGameplay;
	}

	bool IsHeld(std::uint32_t a_button) { return std::ranges::find(g_held, a_button) != g_held.end(); }

	std::unordered_set<std::uint32_t> g_logged;  // buttons whose current press has been logged
	bool IsLogged(std::uint32_t a_button) { return g_logged.contains(a_button); }

	RE::BSFixedString Choose(const std::vector<Binding>& a_bindings)
	{
		for (const auto& b : a_bindings) {
			if (b.modifier != 0 && IsHeld(b.modifier)) {
				return b.event;
			}
		}
		for (const auto& b : a_bindings) {
			if (b.modifier == 0) {
				return b.event;
			}
		}
		return RE::BSFixedString{ "" };
	}

	std::string HeldList()
	{
		std::string s;
		for (const auto b : g_held) {
			s += fmt::format("{}0x{:04X}", s.empty() ? "" : " ", b);
		}
		return s;
	}

	// Called from both hooked sinks with the same event list: everything here is idempotent.
	void Resolve(RE::InputEvent* const* a_event)
	{
		if (!g_enabled || !g_ready || !a_event) {
			return;
		}
		for (auto* event = *a_event; event; event = event->next) {
			if (event->GetEventType() != RE::INPUT_EVENT_TYPE::kButton || event->GetDevice() != RE::INPUT_DEVICE::kGamepad) {
				continue;
			}
			const auto* button = event->AsButtonEvent();
			const auto  code = button->GetIDCode();
			const auto  it = std::ranges::find(g_held, code);
			if (button->IsPressed()) {
				if (it == g_held.end()) {
					g_held.push_back(code);
				}
			} else if (it != g_held.end()) {
				g_held.erase(it);
			}
		}
		if (!InGameplayContext()) {
			return;
		}
		for (auto* event = *a_event; event; event = event->next) {
			if (event->GetEventType() != RE::INPUT_EVENT_TYPE::kButton || event->GetDevice() != RE::INPUT_DEVICE::kGamepad) {
				continue;
			}
			auto*      button = event->AsButtonEvent();
			const auto code = button->GetIDCode();
			const auto entry = g_table.find(code);

			// Both hooked sinks see the same press: log it once, for every gamepad button.
			const bool logThis = g_logPresses && button->IsDown() && !IsLogged(code);
			if (!button->IsDown()) {
				g_logged.erase(code);
			}

			if (entry == g_table.end()) {
				if (logThis) {
					g_logged.insert(code);
					SKSE::log::info("press 0x{:04X} held [{}]: engine '{}' (no combo, left as is)", code, HeldList(), button->QUserEvent().c_str());
				}
				continue;
			}
			RE::BSFixedString chosen;
			if (button->IsDown() || !g_latched.contains(code)) {
				chosen = Choose(entry->second);
				g_latched[code] = chosen;
			} else {
				chosen = g_latched[code];
			}
			if (logThis) {
				g_logged.insert(code);
				SKSE::log::info("press 0x{:04X} held [{}]: engine '{}' -> '{}'", code, HeldList(), button->QUserEvent().c_str(), chosen.c_str());
			}
			if (g_rewrite && button->QUserEvent() != chosen) {
				button->SetUserEvent(chosen);
			}
		}
	}

	struct MenuControlsHook
	{
		static RE::BSEventNotifyControl thunk(RE::MenuControls* a_this, RE::InputEvent* const* a_event, RE::BSTEventSource<RE::InputEvent*>* a_source)
		{
			Resolve(a_event);
			return func(a_this, a_event, a_source);
		}
		static inline REL::Relocation<decltype(thunk)> func;
	};

	struct PlayerControlsHook
	{
		static RE::BSEventNotifyControl thunk(RE::PlayerControls* a_this, RE::InputEvent* const* a_event, RE::BSTEventSource<RE::InputEvent*>* a_source)
		{
			Resolve(a_event);
			return func(a_this, a_event, a_source);
		}
		static inline REL::Relocation<decltype(thunk)> func;
	};

	// Diagnostic: who starts a draw or sheathe? Logs every equip/sheathe-looking animation graph event sent
	// to the player, with the call stack resolved to module+offset, so the module that triggers an
	// unwanted sheathe shows up by name. A Papyrus caller shows as SkyrimSE.exe frames only.
	std::string DescribeAddress(void* a_address)
	{
		HMODULE module{};
		if (!::GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
				static_cast<LPCWSTR>(a_address), &module) ||
			!module) {
			return fmt::format("{}", a_address);
		}
		wchar_t path[MAX_PATH]{};
		::GetModuleFileNameW(module, path, MAX_PATH);
		std::wstring_view name{ path };
		if (const auto slash = name.find_last_of(L"\\/"); slash != std::wstring_view::npos) {
			name.remove_prefix(slash + 1);
		}
		std::string narrow;
		for (const auto c : name) {
			narrow.push_back(c < 128 ? static_cast<char>(c) : '?');
		}
		return fmt::format("{}+{:X}", narrow, reinterpret_cast<std::uintptr_t>(a_address) - reinterpret_cast<std::uintptr_t>(module));
	}

	bool IsWeaponGraphEvent(std::string_view a_name)
	{
		std::string lower{ a_name };
		std::ranges::transform(lower, lower.begin(), [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
		return lower.find("equip") != std::string::npos || lower.find("sheath") != std::string::npos ||
		       lower.find("draw") != std::string::npos || lower.find("weap") != std::string::npos;
	}

	struct PlayerGraphHook
	{
		static bool thunk(RE::IAnimationGraphManagerHolder* a_this, const RE::BSFixedString& a_eventName)
		{
			if (g_traceGraph && a_eventName.c_str() && IsWeaponGraphEvent(a_eventName.c_str())) {
				void*      frames[16]{};
				const auto count = ::RtlCaptureStackBackTrace(1, 16, frames, nullptr);
				std::string stack;
				for (USHORT i = 0; i < count; ++i) {
					stack += (i ? " < " : "") + DescribeAddress(frames[i]);
				}
				SKSE::log::info("graph '{}' held [{}] from {}", a_eventName.c_str(), HeldList(), stack);
			}
			return func(a_this, a_eventName);
		}
		static inline REL::Relocation<decltype(thunk)> func;
	};

	bool ReadIniBool(std::string_view a_key, bool a_default)
	{
		std::ifstream file{ kIniPath };
		std::string   line;
		while (file && std::getline(file, line)) {
			auto view = Trim(line);
			if (view.starts_with("\xEF\xBB\xBF"sv)) {
				view.remove_prefix(3);
			}
			const auto eq = view.find('=');
			if (view.empty() || view.front() == ';' || eq == std::string_view::npos || !IEquals(Trim(view.substr(0, eq)), a_key)) {
				continue;
			}
			return Trim(view.substr(eq + 1)) != "0"sv;
		}
		return a_default;
	}

	void MessageHandler(SKSE::MessagingInterface::Message* a_msg)
	{
		switch (a_msg->type) {
		case SKSE::MessagingInterface::kDataLoaded:
			BuildTable();
			if (g_log) {
				LogEngineMappings();
			}
			break;
		case SKSE::MessagingInterface::kPreLoadGame:
		case SKSE::MessagingInterface::kNewGame:
			g_held.clear();
			g_latched.clear();
			break;
		default:
			break;
		}
	}
}

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	SKSE::log::info("ZenGamepadCombos 1.0.2 loading, runtime {}", REL::Module::get().version().string());
	g_enabled = ReadIniBool("Enabled"sv, true);
	g_log = ReadIniBool("Log"sv, true);
	g_logPresses = g_log && ReadIniBool("LogPresses"sv, true);
	g_rewrite = ReadIniBool("Rewrite"sv, false);
	g_traceGraph = ReadIniBool("TraceGraph"sv, true);
	SKSE::log::info("Enabled={} Log={} LogPresses={} Rewrite={} TraceGraph={}", g_enabled, g_log, g_logPresses, g_rewrite, g_traceGraph);
	if (!g_enabled) {
		return true;
	}

	if (g_traceGraph) {
		REL::Relocation<std::uintptr_t> graphVtbl{ RE::VTABLE_PlayerCharacter[3] };
		PlayerGraphHook::func = graphVtbl.write_vfunc(0x1, PlayerGraphHook::thunk);
		SKSE::log::info("PlayerCharacter NotifyAnimationGraph traced");
	}

	REL::Relocation<std::uintptr_t> menuVtbl{ RE::VTABLE_MenuControls[0] };
	MenuControlsHook::func = menuVtbl.write_vfunc(0x1, MenuControlsHook::thunk);
	REL::Relocation<std::uintptr_t> playerVtbl{ RE::VTABLE_PlayerControls[0] };
	PlayerControlsHook::func = playerVtbl.write_vfunc(0x1, PlayerControlsHook::thunk);
	SKSE::log::info("MenuControls and PlayerControls input sinks hooked");

	SKSE::GetMessagingInterface()->RegisterListener(MessageHandler);
	return true;
}
