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
//
// 2. Slower movement while aiming. Bows and crossbows share NPC_BowDrawn_MT 03580C, so a record edit
//    cannot single out muskets. While a musket is raised or held aimed (kBowDraw, kBowDrawn) the
//    player's SpeedMult is lowered by SpeedMultPenalty, and restored the moment aiming ends. A SpeedMult
//    change only takes effect once the engine recomputes movement speed, which a carry-weight change
//    forces. The penalty is lifted before every save (kSaveGame) and the amount still applied is kept in
//    the co-save and undone on load, so a save made mid-aim cannot keep it.

SKSEPluginInfo(
	.Version = REL::Version{ 1, 0, 0, 0 },
	.Name = "ZenMusketHandling"sv,
	.Author = "Zenderal"sv,
	.StructCompatibility = SKSE::StructCompatibility::Independent,
	.RuntimeCompatibility = SKSE::VersionIndependence::AddressLibrary)

namespace
{
	constexpr auto          kIniPath = "Data/SKSE/Plugins/ZenMusketHandling.ini";
	constexpr std::uint32_t kCosaveId = 'ZMSH';
	constexpr std::uint32_t kCosaveSlow = 'SLOW';
	constexpr std::uint32_t kCosaveVersion = 1;

	std::uint32_t            g_lockAfterShotMs{ 2300 };
	std::vector<std::string> g_blockedEventPrefixes{ "TKDodge" };
	float                    g_speedMultPenalty{ 35.0f };
	std::vector<std::string> g_musketPlugins{ "OrdoLegionisMuskets.esp" };
	bool                     g_log{ true };

	std::uint64_t         g_shotAtMs{ 0 };  // 0 = no musket shot being locked out
	RE::ATTACK_STATE_ENUM g_prevState{ RE::ATTACK_STATE_ENUM::kNone };
	float                 g_appliedPenalty{ 0.0f };  // SpeedMult currently taken away by this plugin (temporary modifier, as magic effects use)

	std::uint64_t NowMs() { return ::GetTickCount64(); }

	bool IEquals(std::string_view a, std::string_view b)
	{
		return std::ranges::equal(a, b, [](char x, char y) { return std::tolower(static_cast<unsigned char>(x)) == std::tolower(static_cast<unsigned char>(y)); });
	}

	bool HoldingDrawnMusket(RE::PlayerCharacter* a_player)
	{
		const auto* state = a_player->AsActorState();
		if (!state || state->GetWeaponState() != RE::WEAPON_STATE::kDrawn) {
			return false;
		}
		const auto* object = a_player->GetEquippedObject(false);
		const auto* weap = object ? object->As<RE::TESObjectWEAP>() : nullptr;
		if (!weap || !weap->IsCrossbow()) {
			return false;
		}
		const auto* file = weap->GetFile(0);
		if (!file) {
			return false;
		}
		const auto name = file->GetFilename();
		return std::ranges::any_of(g_musketPlugins, [&](const std::string& p) { return IEquals(name, p); });
	}

	bool DodgeLocked()
	{
		if (g_shotAtMs == 0) {
			return false;
		}
		auto* player = RE::PlayerCharacter::GetSingleton();
		if (!player || NowMs() - g_shotAtMs >= g_lockAfterShotMs || !HoldingDrawnMusket(player)) {
			g_shotAtMs = 0;
			return false;
		}
		return true;
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
			if (g_log) {
				SKSE::log::info("Musket shot: dodge locked for {} ms", g_lockAfterShotMs);
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
	// sends its dodge through this; a dropped event plays nothing and costs no stamina.
	struct PlayerNotifyAnimationGraph
	{
		static bool thunk(RE::IAnimationGraphManagerHolder* a_this, const RE::BSFixedString& a_eventName)
		{
			const std::string_view name{ a_eventName.c_str() ? a_eventName.c_str() : "" };
			const bool dodge = std::ranges::any_of(g_blockedEventPrefixes, [&](const std::string& p) {
				return name.size() >= p.size() && IEquals(name.substr(0, p.size()), p);
			});
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

	void OnSave(SKSE::SerializationInterface* a_intfc)
	{
		// Normally 0 here: kSaveGame lifted the penalty before the game wrote the save.
		if (a_intfc->OpenRecord(kCosaveSlow, kCosaveVersion)) {
			a_intfc->WriteRecordData(g_appliedPenalty);
		}
	}

	void OnLoad(SKSE::SerializationInterface* a_intfc)
	{
		std::uint32_t type, version, length;
		while (a_intfc->GetNextRecordInfo(type, version, length)) {
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
		g_blockedEventPrefixes = ReadIniList("Dodge"sv, "BlockedEvents"sv, { "TKDodge" });
		g_speedMultPenalty = std::max(0.0f, ReadIniNumber<float>("Aim"sv, "SpeedMultPenalty"sv, 35.0f));
		g_log = ReadIniNumber<std::uint32_t>("General"sv, "Log"sv, 1) != 0;
		SKSE::log::info("Muskets=[{}] LockAfterShotMs={} BlockedEvents=[{}] SpeedMultPenalty={} Log={}",
			Join(g_musketPlugins), g_lockAfterShotMs, Join(g_blockedEventPrefixes), g_speedMultPenalty, g_log);
	}
}

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	SKSE::log::info("ZenMusketHandling 1.0.0 loading, runtime {}", REL::Module::get().version().string());
	LoadSettings();

	REL::Relocation<std::uintptr_t> vtbl{ RE::VTABLE_PlayerCharacter[0] };
	PlayerUpdate::func = vtbl.write_vfunc(0xAD, PlayerUpdate::thunk);
	REL::Relocation<std::uintptr_t> graphVtbl{ RE::VTABLE_PlayerCharacter[3] };
	PlayerNotifyAnimationGraph::func = graphVtbl.write_vfunc(0x1, PlayerNotifyAnimationGraph::thunk);
	SKSE::log::info("PlayerCharacter::Update and NotifyAnimationGraph hooked");

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
