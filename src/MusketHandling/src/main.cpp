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
//    1.3.0 (2026-11-03, curator: players unequipped a fired musket to skip the reload): 1.2.0 remembered only the last
//    musket a shot emptied, so firing a second musket made the first loaded again. Every musket put away empty is
//    now kept (by base form, with a count: two of the same musket are told apart only by number), and taken up again
//    it stays empty until its own reload. The engine does not say which of several alike it equips, so a loaded one
//    is assumed while the player has any (SyncHand).
//
// 4. Enemies' pistol reloads (1.4.0, 2026-11-11). Zenderal - Pistol Ramrod Reload's ZP_PistolReloadArmNPCEffect
//    reloads an NPC's empty flintlock pistol the way the player's script does: the hand's request variable
//    (fZenPistolReloadL/R) at 1, then bWantCast<side> false -> true, then M?h_SpellAimedStart and
//    M?h_SpellRelease_Event. The graph turns the edge into BeginCast<side> on its own update, enters its casting state,
//    and leaves it again on the next update unless an aimed cast has begun (CastStop). An NPC's graph takes the edge
//    ~0.1-0.2 s later than Papyrus sends the events, so they were refused (ZenPistolNPCTrace, 2026-11-11: of a dozen
//    reloads asked for, the one that played had its M?h_SpellAimedStart land in the same millisecond as
//    BeginCastLeft). So the graph's BeginCast<side> of a non-player actor whose request variable is set is answered at
//    once from that actor's BSAnimationGraphEvent sink with M?h_SpellAimedStart (+ MRh_SpellReady_Event, the right
//    hand's aimed cast releases only from its ready state) and M?h_SpellRelease_Event, as the engine answers its own
//    casts on the same thread. The AI's own casts leave the request variable at 0 and are untouched; the player is a
//    PlayerCharacter (its own vtable, sections 1-3) and never comes through here. 1.4.1: the request is cleared as it
//    is answered (one answer per reload: a second BeginCast with the request still set fired a real shot mid-reload).

SKSEPluginInfo(
	.Version = REL::Version{ 1, 4, 1, 0 },
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
	constexpr std::uint32_t kCosaveEmptyVersion = 2;  // 1.2.0 wrote version 1: one FormID

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
	bool                     g_npcPistolReload{ true };  // section 4

	std::uint64_t         g_shotAtMs{ 0 };  // 0 = no musket shot being locked out
	// The musket in the right hand (drawn or not, 0 = none) and whether it is empty, loaded by its reload's
	// g_loadedEvent (graph events arrive on worker threads); the empty muskets out of the hand by base form, counted
	// (main thread only: Update and the co-save callbacks).
	std::atomic<RE::FormID>             g_handForm{ 0 };
	std::atomic<bool>                   g_handEmpty{ false };
	std::map<RE::FormID, std::uint32_t> g_stowedEmpty;
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

	// The right-hand musket, drawn or not
	RE::TESObjectWEAP* EquippedMusket(RE::PlayerCharacter* a_player)
	{
		auto* object = a_player->GetEquippedObject(false);
		auto* weap = object ? object->As<RE::TESObjectWEAP>() : nullptr;
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

	// The right-hand musket, if one is drawn
	const RE::TESObjectWEAP* DrawnMusket(RE::PlayerCharacter* a_player)
	{
		const auto* state = a_player->AsActorState();
		if (!state || state->GetWeaponState() != RE::WEAPON_STATE::kDrawn) {
			return nullptr;
		}
		return EquippedMusket(a_player);
	}

	bool HoldingDrawnMusket(RE::PlayerCharacter* a_player) { return DrawnMusket(a_player) != nullptr; }

	bool HoldingEmptyMusket(RE::PlayerCharacter* a_player)
	{
		const auto* weap = g_handEmpty ? DrawnMusket(a_player) : nullptr;
		return weap && weap->GetFormID() == g_handForm.load();
	}

	// The musket in hand changed (seen once a frame, so a swap and back inside a menu changes nothing): an empty one
	// put away is kept in g_stowedEmpty, and the one taken up is empty if every one of its form the player has out of
	// the hand is (the count includes it; one sold or dropped counts as a loaded one gone)
	void SyncHand(RE::PlayerCharacter* a_player)
	{
		auto*            weap = EquippedMusket(a_player);
		const RE::FormID now = weap ? weap->GetFormID() : 0;
		const RE::FormID was = g_handForm;
		if (now == was) {
			return;
		}
		if (was && g_handEmpty) {
			const auto kept = ++g_stowedEmpty[was];
			if (g_log) {
				SKSE::log::info("Musket {:08X} put away empty ({} of its form)", was, kept);
			}
		}
		bool empty = false;
		if (const auto it = g_stowedEmpty.find(now); now && it != g_stowedEmpty.end()) {
			const auto counts = a_player->GetInventoryCounts([&](RE::TESBoundObject& a_obj) { return &a_obj == weap; });
			const auto found = counts.find(weap);
			const auto owned = static_cast<std::uint32_t>(std::max(1, found != counts.end() ? found->second : 1));
			it->second = std::min(it->second, owned);
			empty = it->second >= owned;
			if (empty) {
				--it->second;
			}
			if (g_log) {
				SKSE::log::info("Musket {:08X} taken up {} ({} of {} out of the hand were empty)", now,
					empty ? "EMPTY" : "loaded", it->second + (empty ? 1 : 0), owned);
			}
			if (it->second == 0) {
				g_stowedEmpty.erase(it);
			}
		}
		g_handForm = now;
		g_handEmpty = empty;
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
		SyncHand(a_player);
		const auto attack = state->GetAttackState();
		const auto prev = std::exchange(g_prevState, attack);
		const bool musket = HoldingDrawnMusket(a_player);

		const auto isRelease = [](RE::ATTACK_STATE_ENUM s) {
			return s == RE::ATTACK_STATE_ENUM::kBowReleasing || s == RE::ATTACK_STATE_ENUM::kBowReleased;
		};
		if (musket && isRelease(attack) && !isRelease(prev)) {
			g_shotAtMs = NowMs();
			if (g_onDemand) {
				g_handEmpty = true;
			}
			if (g_log) {
				SKSE::log::info("Musket shot: dodge locked for {} ms{}", g_lockAfterShotMs,
					g_onDemand ? std::format(", {:08X} empty until reloaded", g_handForm.load()) : std::string{});
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
			if (g_onDemand && g_handEmpty && StartsWithAny(name, g_attackEvents)) {
				auto* player = RE::PlayerCharacter::GetSingleton();
				if (player && HoldingEmptyMusket(player)) {
					// refused while the reload plays (its state takes no reloadStart), so a held or repeated
					// press restarts nothing; the empty musket never fires
					const bool started = func(a_this, RE::BSFixedString{ g_reloadEvent.c_str() });
					if (started && g_log) {
						SKSE::log::info("{} on empty musket {:08X}: {} sent instead", name, g_handForm.load(), g_reloadEvent);
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
			if (g_handEmpty && a_event && a_event->tag.c_str() && IEquals(a_event->tag.c_str(), g_loadedEvent)) {
				auto* player = RE::PlayerCharacter::GetSingleton();
				if (player && HoldingEmptyMusket(player)) {
					if (g_log) {
						SKSE::log::info("{}: musket {:08X} loaded", g_loadedEvent, g_handForm.load());
					}
					g_handEmpty = false;
				}
			}
			return func(a_this, a_event, a_source);
		}
		static inline REL::Relocation<decltype(thunk)> func;
	};

	// Section 4: BSTEventSink<BSAnimationGraphEvent>::ProcessEvent (vfunc 0x01) on the Character vtable [2], every
	// non-player actor's graph events. BeginCast<side> with that hand's reload request set: the aimed cast and its
	// release, sent at once.
	struct NpcGraphEvent
	{
		static RE::BSEventNotifyControl thunk(RE::BSTEventSink<RE::BSAnimationGraphEvent>* a_this, const RE::BSAnimationGraphEvent* a_event,
			RE::BSTEventSource<RE::BSAnimationGraphEvent>* a_source)
		{
			const auto result = func(a_this, a_event, a_source);
			if (!g_npcPistolReload || !a_event || !a_event->tag.c_str()) {
				return result;
			}
			const std::string_view tag{ a_event->tag.c_str() };
			const bool             left = IEquals(tag, "BeginCastLeft"sv);
			if (!left && !IEquals(tag, "BeginCastRight"sv)) {
				return result;
			}
			auto* actor = static_cast<RE::TESObjectREFR*>(a_this)->As<RE::Actor>();
			float request = 0.0f;
			if (!actor || actor->IsPlayerRef() ||
				!actor->GetGraphVariableFloat(left ? "fZenPistolReloadL"sv : "fZenPistolReloadR"sv, request) || request < 0.5f) {
				return result;
			}
			// 1.4.1: one answer per request. The script held its request (and bWantCast) for a second, the graph raised a
			// second BeginCast after the first cast was thrown away, and its answer fired a real shot mid-reload
			// (ZenPistolNPCTrace, 2026-11-11 22:06:26.8)
			actor->SetGraphVariableFloat(left ? "fZenPistolReloadL"sv : "fZenPistolReloadR"sv, 0.0f);
			const auto prefix = left ? "MLh_"s : "MRh_"s;
			const bool aimed = actor->NotifyAnimationGraph((prefix + "SpellAimedStart").c_str());
			const bool ready = left || actor->NotifyAnimationGraph("MRh_SpellReady_Event");
			const bool release = actor->NotifyAnimationGraph((prefix + "SpellRelease_Event").c_str());
			if (g_log) {
				SKSE::log::info("NPC {:08X} '{}': {} with its pistol reload asked for: {}SpellAimedStart {}, {}SpellRelease_Event {}{}",
					actor->GetFormID(), actor->GetName(), tag, prefix, aimed ? "taken" : "REFUSED", prefix, release ? "taken" : "REFUSED",
					left ? "" : (ready ? " (ready taken)" : " (ready REFUSED)"));
			}
			return result;
		}
		static inline REL::Relocation<decltype(thunk)> func;
	};

	void OnSave(SKSE::SerializationInterface* a_intfc)
	{
		// Normally 0 here: kSaveGame lifted the penalty before the game wrote the save.
		if (a_intfc->OpenRecord(kCosaveSlow, kCosaveVersion)) {
			a_intfc->WriteRecordData(g_appliedPenalty);
		}
		// empty muskets stay empty in a save: the one in hand (0: none) and whether it is, then the ones put away
		if (a_intfc->OpenRecord(kCosaveEmpty, kCosaveEmptyVersion)) {
			const RE::FormID    hand = g_handForm;
			const std::uint8_t  handEmpty = g_handEmpty ? 1 : 0;
			const std::uint32_t kinds = static_cast<std::uint32_t>(g_stowedEmpty.size());
			a_intfc->WriteRecordData(hand);
			a_intfc->WriteRecordData(handEmpty);
			a_intfc->WriteRecordData(kinds);
			for (const auto& [form, count] : g_stowedEmpty) {
				a_intfc->WriteRecordData(form);
				a_intfc->WriteRecordData(count);
			}
		}
	}

	void OnLoad(SKSE::SerializationInterface* a_intfc)
	{
		std::uint32_t type, version, length;
		while (a_intfc->GetNextRecordInfo(type, version, length)) {
			if (type == kCosaveEmpty && version == 1) {
				// 1.2.0: the one musket the last shot emptied, in hand or not; the first frame's SyncHand takes it up
				RE::FormID saved = 0, resolved = 0;
				if (a_intfc->ReadRecordData(saved) && saved && a_intfc->ResolveFormID(saved, resolved)) {
					g_stowedEmpty[resolved] = 1;
					SKSE::log::info("Save (1.2.0) carried empty musket {:08X}", resolved);
				}
				continue;
			}
			if (type == kCosaveEmpty && version == kCosaveEmptyVersion) {
				RE::FormID    hand = 0, resolved = 0;
				std::uint8_t  handEmpty = 0;
				std::uint32_t kinds = 0;
				if (!a_intfc->ReadRecordData(hand) || !a_intfc->ReadRecordData(handEmpty) || !a_intfc->ReadRecordData(kinds)) {
					continue;
				}
				if (hand && a_intfc->ResolveFormID(hand, resolved)) {
					g_handForm = resolved;
					g_handEmpty = handEmpty != 0;
				}
				for (std::uint32_t i = 0; i < kinds; ++i) {
					RE::FormID    form = 0;
					std::uint32_t count = 0;
					if (!a_intfc->ReadRecordData(form) || !a_intfc->ReadRecordData(count)) {
						break;
					}
					if (count && a_intfc->ResolveFormID(form, resolved)) {
						g_stowedEmpty[resolved] += count;
					}
				}
				SKSE::log::info("Save carried musket {:08X} in hand{}, {} kinds put away empty", g_handForm.load(),
					g_handEmpty ? " (empty)" : "", g_stowedEmpty.size());
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
		g_handForm = 0;
		g_handEmpty = false;
		g_stowedEmpty.clear();
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
		g_npcPistolReload = ReadIniNumber<std::uint32_t>("Pistols"sv, "NpcReloadCast"sv, 1) != 0;
		SKSE::log::info("Muskets=[{}] LockAfterShotMs={} MaxLockMs={} BlockedEvents=[{}] SpeedMultPenalty={} Log={}",
			Join(g_musketPlugins), g_lockAfterShotMs, g_maxLockMs, Join(g_blockedEventPrefixes), g_speedMultPenalty, g_log);
		SKSE::log::info("Reload OnDemand={} AttackEvents=[{}] ReloadEvent={} LoadedEvent={}", g_onDemand, Join(g_attackEvents),
			g_reloadEvent, g_loadedEvent);
		SKSE::log::info("Pistols NpcReloadCast={}", g_npcPistolReload);
	}
}

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	SKSE::log::info("ZenMusketHandling 1.4.1 loading, runtime {}", REL::Module::get().version().string());
	LoadSettings();

	REL::Relocation<std::uintptr_t> vtbl{ RE::VTABLE_PlayerCharacter[0] };
	PlayerUpdate::func = vtbl.write_vfunc(0xAD, PlayerUpdate::thunk);
	REL::Relocation<std::uintptr_t> graphVtbl{ RE::VTABLE_PlayerCharacter[3] };
	PlayerNotifyAnimationGraph::func = graphVtbl.write_vfunc(0x1, PlayerNotifyAnimationGraph::thunk);
	REL::Relocation<std::uintptr_t> sinkVtbl{ RE::VTABLE_PlayerCharacter[2] };
	PlayerGraphEvent::func = sinkVtbl.write_vfunc(0x1, PlayerGraphEvent::thunk);
	SKSE::log::info("PlayerCharacter::Update, NotifyAnimationGraph and its graph event sink hooked");
	REL::Relocation<std::uintptr_t> npcSinkVtbl{ RE::VTABLE_Character[2] };
	NpcGraphEvent::func = npcSinkVtbl.write_vfunc(0x1, NpcGraphEvent::thunk);
	SKSE::log::info("Character graph event sink hooked (section 4: enemies' pistol reload casts)");

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
