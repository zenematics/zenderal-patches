#include "pch.h"

// Muskets should be powerful but slow to use, bows agile. Two changes, both for muskets only: the
// right-hand weapon is a crossbow (Ordo's muskets are AnimationType Crossbow) whose record comes from
// one of [Muskets] Plugins. Bows and Enderal SE - Crossbows' crossbows are untouched.
//
// 1. No dodge straight after a shot. TK Dodge NG (itahol/TK-Dodge-NG, TKRE.cpp canDodge) only refuses
//    a dodge while the attack state is not kNone, but the engine returns a musket to kNone ~1.6 s after
//    the shot while DAR Rifles' musket release clip runs 2.4 s (arrowRelease@0.133, reload sound@1.6).
//    A dodge in that gap cut the visible reload short. TK starts a dodge with
//    player->NotifyAnimationGraph("TKDodge<Dir>"), and charges stamina only on the resulting
//    TKDR_DodgeStart animation event, so this plugin drops those events for LockAfterShotMs after the
//    shot (kBowReleasing/kBowReleased) while a drawn musket is still in hand.
//    1.1.0: since the 1.7.104 update the list's TK ini sets enableDodgeAttackCancel = true, so TK
//    accepts a dodge in ANY attack state and a dodge right after the shot interrupts the reload
//    outright. The lock now also holds while the musket is still in its post-shot cycle (kBowReleasing
//    .. kBowFollowThrough, kBowAttached = the reload), whatever the timer says, up to MaxLockMs.
//
// 2. Slower movement while aiming. Bows and crossbows share NPC_BowDrawn_MT 03580C, so a record edit
//    cannot single out muskets. While a musket is raised or held aimed (kBowDraw, kBowDrawn) the
//    player's SpeedMult is lowered by SpeedMultPenalty, and restored the moment aiming ends. A SpeedMult
//    change only takes effect once the engine recomputes movement speed, which a carry-weight change
//    forces. The penalty is lifted before every save (kSaveGame) and the amount still applied is kept in
//    the co-save and undone on load, so a save made mid-aim cannot keep it.
//
// 3. Reload on demand (1.2.0, 2026-11-03, curator: like the pistols, a musket reloads only when fire is pressed
//    again). Zenderal - Musket Ramrod Reload's shot clips carry no reload any more, and the engine fires a musket
//    whose shot did not reload it (traced, SpellAimTrace 1.4.1: five shots in 6.8 s, no reloadStart). So a shot
//    marks that musket empty; while it is drawn and empty, the engine's attack press (crossbowAttackStart, sent
//    through NotifyAnimationGraph) is dropped and reloadStart sent instead, which both 1hm graphs take from
//    1HM_Ready_State and CrossBow_AttackState into CrossBow_ReloadState (Zodd's reload clip). That state has no
//    reloadStart transition of its own, so presses while it plays are refused; a reload cut short leaves the graph
//    ready, and the next press starts it again. The reload clip's reloadStop (its clip trigger 0.195 s before the
//    end), heard through the player's BSAnimationGraphEvent sink, loads it. The empty musket is kept in the co-save.

SKSEPluginInfo(
	.Version = REL::Version{ 1, 2, 0, 0 },
	.Name = "ZenMusketHandling"sv,
	.Author = "Zenderal"sv,
	.StructCompatibility = SKSE::StructCompatibility::Independent,
	.RuntimeCompatibility = SKSE::VersionIndependence::AddressLibrary)

namespace
{
	constexpr auto          kIniPath = "Data/SKSE/Plugins/ZenMusketHandling.ini";
	constexpr std::uint32_t kCosaveId = 'ZMSH';
	constexpr std::uint32_t kCosaveSlow = 'SLOW';
	constexpr std::uint32_t kCosaveEmpty = 'EMPT';
	constexpr std::uint32_t kCosaveVersion = 1;

	std::uint32_t            g_lockAfterShotMs{ 2300 };
	std::uint32_t            g_maxLockMs{ 5000 };  // a stuck attack state never locks the dodge for longer
	std::vector<std::string> g_blockedEventPrefixes{ "TKDodge" };
	float                    g_speedMultPenalty{ 35.0f };
	std::vector<std::string> g_musketPlugins{ "OrdoLegionisMuskets.esp" };
	bool                     g_log{ true };
	bool                     g_onDemand{ true };
	std::vector<std::string> g_attackEvents{ "crossbowAttackStart" };
	std::string              g_reloadEvent{ "reloadStart" };
	std::string              g_loadedEvent{ "reloadStop" };

	std::uint64_t         g_shotAtMs{ 0 };  // 0 = no musket shot being locked out
	std::atomic<RE::FormID> g_emptyForm{ 0 };  // the musket the last shot emptied (0 = none), loaded by its reload's
	                                           // g_loadedEvent; graph events arrive on worker threads
	RE::ATTACK_STATE_ENUM g_prevState{ RE::ATTACK_STATE_ENUM::kNone };
	float                 g_appliedPenalty{ 0.0f };  // SpeedMult currently taken away by this plugin (temporary modifier, as magic effects use)

	std::uint64_t NowMs() { return ::GetTickCount64(); }

	bool IEquals(std::string_view a, std::string_view b)
	{
		return std::ranges::equal(a, b, [](char x, char y) { return std::tolower(static_cast<unsigned char>(x)) == std::tolower(static_cast<unsigned char>(y)); });
	}

	bool StartsWithAny(std::string_view a_name, const std::vector<std::string>& a_prefixes)
	{
		return std::ranges::any_of(a_prefixes, [&](const std::string& p) {
			return a_name.size() >= p.size() && IEquals(a_name.substr(0, p.size()), p);
		});
	}

	// The right-hand musket, if one is drawn
	const RE::TESObjectWEAP* DrawnMusket(RE::PlayerCharacter* a_player)
	{
		const auto* state = a_player->AsActorState();
		if (!state || state->GetWeaponState() != RE::WEAPON_STATE::kDrawn) {
			return nullptr;
		}
		const auto* object = a_player->GetEquippedObject(false);
		const auto* weap = object ? object->As<RE::TESObjectWEAP>() : nullptr;
		if (!weap || !weap->IsCrossbow()) {
			return nullptr;
		}
		const auto* file = weap->GetFile(0);
		if (!file) {
			return nullptr;
		}
		const auto name = file->GetFilename();
		return std::ranges::any_of(g_musketPlugins, [&](const std::string& p) { return IEquals(name, p); }) ? weap : nullptr;
	}

	bool HoldingDrawnMusket(RE::PlayerCharacter* a_player) { return DrawnMusket(a_player) != nullptr; }

	bool HoldingEmptyMusket(RE::PlayerCharacter* a_player)
	{
		const auto* weap = g_emptyForm ? DrawnMusket(a_player) : nullptr;
		return weap && weap->GetFormID() == g_emptyForm.load();
	}

	bool DodgeLocked()
	{
		if (g_shotAtMs == 0) {
			return false;
		}
		auto* player = RE::PlayerCharacter::GetSingleton();
		const auto elapsed = player ? NowMs() - g_shotAtMs : 0;
		if (!player || elapsed >= g_maxLockMs || !HoldingDrawnMusket(player)) {
			g_shotAtMs = 0;
			return false;
		}
		if (elapsed < g_lockAfterShotMs) {
			return true;
		}
		using enum RE::ATTACK_STATE_ENUM;
		const auto attack = player->AsActorState()->GetAttackState();
		const bool reloading = attack == kBowReleasing || attack == kBowReleased || attack == kBowAttached ||
		                       attack == kBowNextAttack || attack == kBowFollowThrough;
		if (!reloading) {
			g_shotAtMs = 0;
		}
		return reloading;
	}

	void NudgeMovementSpeed(RE::PlayerCharacter* a_player)
	{
		// The engine recomputes movement speed when carry weight changes; SpeedMult alone waits for that.
		auto* avs = a_player->AsActorValueOwner();
		avs->ModActorValue(RE::ACTOR_VALUE_MODIFIER::kTemporary, RE::ActorValue::kCarryWeight, 0.1f);
		avs->ModActorValue(RE::ACTOR_VALUE_MODIFIER::kTemporary, RE::ActorValue::kCarryWeight, -0.1f);
	}

	void SetPenalty(RE::PlayerCharacter* a_player, float a_penalty)
	{
		if (a_penalty == g_appliedPenalty) {
			return;
		}
		a_player->AsActorValueOwner()->ModActorValue(RE::ACTOR_VALUE_MODIFIER::kTemporary, RE::ActorValue::kSpeedMult, g_appliedPenalty - a_penalty);
		g_appliedPenalty = a_penalty;
		NudgeMovementSpeed(a_player);
	}

	void Update(RE::PlayerCharacter* a_player)
	{
		const auto* state = a_player->AsActorState();
		if (!state) {
			return;
		}
		const auto attack = state->GetAttackState();
		const auto prev = std::exchange(g_prevState, attack);
		const bool musket = HoldingDrawnMusket(a_player);

		const auto isRelease = [](RE::ATTACK_STATE_ENUM s) {
			return s == RE::ATTACK_STATE_ENUM::kBowReleasing || s == RE::ATTACK_STATE_ENUM::kBowReleased;
		};
		if (musket && isRelease(attack) && !isRelease(prev)) {
			g_shotAtMs = NowMs();
			if (g_onDemand) {
				g_emptyForm = DrawnMusket(a_player)->GetFormID();
			}
			if (g_log) {
				SKSE::log::info("Musket shot: dodge locked for {} ms{}", g_lockAfterShotMs,
					g_onDemand ? std::format(", {:08X} empty until reloaded", g_emptyForm.load()) : std::string{});
			}
		}

		const bool aiming = musket && (attack == RE::ATTACK_STATE_ENUM::kBowDraw || attack == RE::ATTACK_STATE_ENUM::kBowDrawn);
		SetPenalty(a_player, aiming ? g_speedMultPenalty : 0.0f);
	}

	// Actor::Update (vfunc 0xAD) on the player's vtable: once per frame while the game runs.
	struct PlayerUpdate
	{
		static void thunk(RE::PlayerCharacter* a_this, float a_delta)
		{
			func(a_this, a_delta);
			Update(a_this);
		}
		static inline REL::Relocation<decltype(thunk)> func;
	};

	// IAnimationGraphManagerHolder::NotifyAnimationGraph (vfunc 0x01) on the player's vtable [3]. TK Dodge
	// sends its dodge through this; a dropped event plays nothing and costs no stamina. The engine sends the
	// attack press through it too: on an empty musket that becomes the reload (3.).
	struct PlayerNotifyAnimationGraph
	{
		static bool thunk(RE::IAnimationGraphManagerHolder* a_this, const RE::BSFixedString& a_eventName)
		{
			const std::string_view name{ a_eventName.c_str() ? a_eventName.c_str() : "" };
			if (g_onDemand && g_emptyForm && StartsWithAny(name, g_attackEvents)) {
				auto* player = RE::PlayerCharacter::GetSingleton();
				if (player && HoldingEmptyMusket(player)) {
					// refused while the reload plays (its state takes no reloadStart), so a held or repeated
					// press restarts nothing; the empty musket never fires
					const bool started = func(a_this, RE::BSFixedString{ g_reloadEvent.c_str() });
					if (started && g_log) {
						SKSE::log::info("{} on empty musket {:08X}: {} sent instead", name, g_emptyForm.load(), g_reloadEvent);
					}
					return false;
				}
			}
			const bool dodge = StartsWithAny(name, g_blockedEventPrefixes);
			if (dodge && DodgeLocked()) {
				if (g_log) {
					SKSE::log::info("Dropped {} {} ms after a musket shot", name, NowMs() - g_shotAtMs);
				}
				return false;
			}
			return func(a_this, a_eventName);
		}
		static inline REL::Relocation<decltype(thunk)> func;
	};

	// BSTEventSink<BSAnimationGraphEvent>::ProcessEvent (vfunc 0x01) on the player's vtable [2]: every event the
	// player's graphs (1P and 3P) send. The reload clip's g_loadedEvent loads the empty musket.
	struct PlayerGraphEvent
	{
		static RE::BSEventNotifyControl thunk(RE::BSTEventSink<RE::BSAnimationGraphEvent>* a_this, const RE::BSAnimationGraphEvent* a_event,
			RE::BSTEventSource<RE::BSAnimationGraphEvent>* a_source)
		{
			if (g_emptyForm && a_event && a_event->tag.c_str() && IEquals(a_event->tag.c_str(), g_loadedEvent)) {
				auto* player = RE::PlayerCharacter::GetSingleton();
				if (player && HoldingEmptyMusket(player)) {
					if (g_log) {
						SKSE::log::info("{}: musket {:08X} loaded", g_loadedEvent, g_emptyForm.load());
					}
					g_emptyForm = 0;
				}
			}
			return func(a_this, a_event, a_source);
		}
		static inline REL::Relocation<decltype(thunk)> func;
	};

	void OnSave(SKSE::SerializationInterface* a_intfc)
	{
		// Normally 0 here: kSaveGame lifted the penalty before the game wrote the save.
		if (a_intfc->OpenRecord(kCosaveSlow, kCosaveVersion)) {
			a_intfc->WriteRecordData(g_appliedPenalty);
		}
		// the empty musket stays empty in a save (0: none)
		if (a_intfc->OpenRecord(kCosaveEmpty, kCosaveVersion)) {
			const RE::FormID empty = g_emptyForm;
			a_intfc->WriteRecordData(empty);
		}
	}

	void OnLoad(SKSE::SerializationInterface* a_intfc)
	{
		std::uint32_t type, version, length;
		while (a_intfc->GetNextRecordInfo(type, version, length)) {
			if (type == kCosaveEmpty && version == kCosaveVersion) {
				RE::FormID saved = 0, resolved = 0;
				if (a_intfc->ReadRecordData(saved) && saved && a_intfc->ResolveFormID(saved, resolved)) {
					g_emptyForm = resolved;
					SKSE::log::info("Save carried empty musket {:08X}", resolved);
				}
				continue;
			}
			float saved = 0.0f;
			if (type != kCosaveSlow || version != kCosaveVersion || !a_intfc->ReadRecordData(saved) || saved == 0.0f) {
				continue;
			}
			if (auto* player = RE::PlayerCharacter::GetSingleton()) {
				player->AsActorValueOwner()->ModActorValue(RE::ACTOR_VALUE_MODIFIER::kTemporary, RE::ActorValue::kSpeedMult, saved);
				NudgeMovementSpeed(player);
				SKSE::log::info("Save carried a {} SpeedMult aim penalty; restored", saved);
			}
		}
	}

	void OnRevert(SKSE::SerializationInterface*)
	{
		// The game state about to be loaded (or a new game) never carries our in-memory penalty.
		g_appliedPenalty = 0.0f;
		g_shotAtMs = 0;
		g_emptyForm = 0;
		g_prevState = RE::ATTACK_STATE_ENUM::kNone;
	}

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

	std::vector<std::string> ReadIniList(std::string_view a_section, std::string_view a_key, std::vector<std::string> a_default)
	{
		const auto value = ReadIniValue(kIniPath, a_section, a_key);
		if (!value) {
			return a_default;
		}
		std::vector<std::string> result;
		for (const auto part : std::views::split(*value, ',')) {
			std::string_view item{ part.begin(), part.end() };
			const auto       b = item.find_first_not_of(" \t");
			const auto       e = item.find_last_not_of(" \t");
			if (b != std::string_view::npos) {
				result.emplace_back(item.substr(b, e - b + 1));
			}
		}
		return result;
	}

	std::string Join(const std::vector<std::string>& a_items)
	{
		std::string out;
		for (const auto& item : a_items) {
			out += out.empty() ? item : ", " + item;
		}
		return out;
	}

	void LoadSettings()
	{
		g_musketPlugins = ReadIniList("Muskets"sv, "Plugins"sv, { "OrdoLegionisMuskets.esp" });
		g_lockAfterShotMs = ReadIniNumber<std::uint32_t>("Dodge"sv, "LockAfterShotMs"sv, 2300);
		g_maxLockMs = std::max(g_lockAfterShotMs, ReadIniNumber<std::uint32_t>("Dodge"sv, "MaxLockMs"sv, 5000));
		g_blockedEventPrefixes = ReadIniList("Dodge"sv, "BlockedEvents"sv, { "TKDodge" });
		g_speedMultPenalty = std::max(0.0f, ReadIniNumber<float>("Aim"sv, "SpeedMultPenalty"sv, 35.0f));
		g_log = ReadIniNumber<std::uint32_t>("General"sv, "Log"sv, 1) != 0;
		g_onDemand = ReadIniNumber<std::uint32_t>("Reload"sv, "OnDemand"sv, 1) != 0;
		g_attackEvents = ReadIniList("Reload"sv, "AttackEvents"sv, { "crossbowAttackStart" });
		g_reloadEvent = ReadIniValue(kIniPath, "Reload"sv, "ReloadEvent"sv).value_or("reloadStart");
		g_loadedEvent = ReadIniValue(kIniPath, "Reload"sv, "LoadedEvent"sv).value_or("reloadStop");
		SKSE::log::info("Muskets=[{}] LockAfterShotMs={} MaxLockMs={} BlockedEvents=[{}] SpeedMultPenalty={} Log={}",
			Join(g_musketPlugins), g_lockAfterShotMs, g_maxLockMs, Join(g_blockedEventPrefixes), g_speedMultPenalty, g_log);
		SKSE::log::info("Reload OnDemand={} AttackEvents=[{}] ReloadEvent={} LoadedEvent={}", g_onDemand, Join(g_attackEvents),
			g_reloadEvent, g_loadedEvent);
	}
}

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	SKSE::log::info("ZenMusketHandling 1.2.0 loading, runtime {}", REL::Module::get().version().string());
	LoadSettings();

	REL::Relocation<std::uintptr_t> vtbl{ RE::VTABLE_PlayerCharacter[0] };
	PlayerUpdate::func = vtbl.write_vfunc(0xAD, PlayerUpdate::thunk);
	REL::Relocation<std::uintptr_t> graphVtbl{ RE::VTABLE_PlayerCharacter[3] };
	PlayerNotifyAnimationGraph::func = graphVtbl.write_vfunc(0x1, PlayerNotifyAnimationGraph::thunk);
	REL::Relocation<std::uintptr_t> sinkVtbl{ RE::VTABLE_PlayerCharacter[2] };
	PlayerGraphEvent::func = sinkVtbl.write_vfunc(0x1, PlayerGraphEvent::thunk);
	SKSE::log::info("PlayerCharacter::Update, NotifyAnimationGraph and its graph event sink hooked");

	const auto* serialization = SKSE::GetSerializationInterface();
	serialization->SetUniqueID(kCosaveId);
	serialization->SetSaveCallback(OnSave);
	serialization->SetLoadCallback(OnLoad);
	serialization->SetRevertCallback(OnRevert);

	SKSE::GetMessagingInterface()->RegisterListener([](SKSE::MessagingInterface::Message* a_msg) {
		if (a_msg->type == SKSE::MessagingInterface::kSaveGame && g_appliedPenalty != 0.0f) {
			if (auto* player = RE::PlayerCharacter::GetSingleton()) {
				SetPenalty(player, 0.0f);  // re-applied next frame if still aiming
			}
		}
	});
	return true;
}
