#include "pch.h"

#include <algorithm>
#include <atomic>
#include <chrono>
#include <map>
#include <mutex>
#include <optional>
#include <random>
#include <thread>

#include <nlohmann/json.hpp>

// Prophecy's Rage tree (curator 2026-10-27). Rage stacks come from hit events: every melee hit the player lands and
// every hit the player takes adds one, up to Max (Untempered: MaxUntempered). After FadeAfter seconds without a hit
// Rage fades one stack every FadeEvery seconds (Untempered: twice that), and CombatGrace seconds out of combat it is
// gone. The count is written to the ZP_Rage global (Bloodied Fury's per-stack damage entries read it) and into the
// magnitude of the Rage ability's effect ("You have <mag> stacks of Rage." in Active Effects).
//
// A power attack that lands fires the player's Rage talents for its direction - the attack's PowerAttackType keyword
// (Standing/Forward/Side/Back), or "sprint" when the player is sprinting or stopped sprinting less than SprintGrace
// seconds before - when Rage covers the talent's cost: each owned talent of that trigger is cast (A Dark Warrior's
// Tale's damage spell and its visual, from the player at the target, as the pack's _CDW_MagicCastMultipleSpellsScript
// cast them; never its Health "rebound") and the largest cost among them is spent once. Hits come from TESHitEvent,
// not a perk's ApplyCombatHitSpell: the engine applies only one of those per hit, and EGO's XionPowerStagger and
// Enderal's class talents already use it on melee hits.
//
// Vehemence (the capstone): Rage at its peak casts the Vehemence spell on the player; while its effect is on, power
// attacks cost no Stamina (a perk entry) and actions spend no Rage. When it ends, Rage is spent.
// Rage is not saved: a load starts at 0.
//
// Dragon's Breath (Martial Arts, 1.1.0): every Every-th unarmed hit the player lands (one per swing, whatever it hits;
// Rage tree or not) casts one of its three spells, at random, from the player at the target: short elemental cones.
// 1.1.1 also sets off that element's harmless blast at the target; 1.1.2 a small one at the punching fist.
//
// Twin Effigies (Sorcery, 1.2.0): Shatterveil's DLL dresses its effigies in the player's armor and weapons only, so a
// caster's effigies punched. When the player casts Twin Effigies, the spells in their hands then (not Twin Effigies
// itself, not summons) are remembered; each effigy that appears within SpawnWindow seconds casts them in turn, every
// CastEvery seconds, at its combat target or the nearest foe of the player within Range - from the effigy, blamed on
// the player, at no cost. Self-delivered spells land on the effigy.
// 1.3.2: with "castSpell" set (curator: casting any of the player's spells for free was terrible for balance) the
// effigies cast only that spell - Flow State's Chain Lightning - whatever the player holds.
//
// Ricochet Rounds (Firearms, 1.3.0): a pistol hit (its source a staff whose enchantment - or the enchantment itself -
// has an effect with the Flintlock Overhaul's ZP_FlintlockShot keyword) has Chance% to re-cast that shot enchantment
// from the target at the nearest other foe of the player within Range, blamed on the player. The bounce's own hit
// cannot bounce again (that target is ignored for Cooldown seconds).
// Log: My Games/Skyrim Special Edition/SKSE/ZenProphecyRage.log

SKSEPluginInfo(
	.Version = REL::Version{ 1, 3, 2, 0 },
	.Name = "ZenProphecyRage"sv,
	.Author = "Zenderal"sv,
	.StructCompatibility = SKSE::StructCompatibility::Independent,
	.RuntimeCompatibility = SKSE::VersionIndependence::AddressLibrary)

namespace
{
	using Clock = std::chrono::steady_clock;
	constexpr auto kConfigPath = "Data/SKSE/Plugins/ZenProphecyRage.json"sv;

	struct Action
	{
		std::string                name;
		RE::BGSPerk*               perk{ nullptr };
		std::string                trigger;
		int                        cost{ 0 };
		std::vector<RE::SpellItem*> spells;
	};

	struct Config
	{
		RE::TESGlobal*     rageGlobal{ nullptr };
		RE::SpellItem*     vehemenceSpell{ nullptr };
		RE::EffectSetting* vehemenceEffect{ nullptr };
		RE::EffectSetting* rageEffect{ nullptr };
		RE::BGSPerk*       root{ nullptr };
		RE::BGSPerk*       untempered{ nullptr };
		RE::BGSPerk*       vehemence{ nullptr };
		int                max{ 10 };
		int                maxUntempered{ 15 };
		double             fadeAfter{ 6.0 };
		double             fadeEvery{ 3.0 };
		double             combatGrace{ 3.0 };
		double             sprintGrace{ 1.0 };
		double             hitDedupe{ 0.25 };
		double             swingWindow{ 0.5 };   // one action per swing
		std::map<RE::BGSKeyword*, std::string> directions;   // PowerAttackType keyword -> trigger
		std::vector<Action> actions;
		// the meter: Oxygen Meter 2's movie, our own copy of its menu (setLocation's arguments, two colours)
		double             meterX{ 50.0 }, meterY{ 21.0 }, meterRot{ 0.0 }, meterXScale{ 50.0 }, meterYScale{ 50.0 };
		double             meterBar{ 0xE8400C }, meterFlash{ 0xFF2A00 };
		bool               meterFollowsCastingBar{ true };
		double             meterXOffset{ 0.0 };     // percent of the stage width, added after following the casting bar
		double             meterWidth{ 0.0 };       // an xscale of its own (0: the casting bar's); the height keeps the casting bar's
		bool               ready{ false };
		// Dragon's Breath
		RE::BGSPerk*       dragonPerk{ nullptr };
		std::vector<RE::SpellItem*> dragonSpells;
		std::vector<RE::BGSExplosion*> dragonBlasts;   // 1.1.1: each spell's look, set off at the target with it
		int                dragonEvery{ 5 };
		// Twin Effigies
		std::vector<RE::FormID> effigySpells;     // Shatterveil's Twin Effigies spells (all tiers)
		RE::TESFaction*    effigyFaction{ nullptr };
		RE::TESNPC*        effigyBase{ nullptr };
		double             effigyCastEvery{ 3.0 };
		double             effigyRange{ 2048.0 };
		double             effigySpawnWindow{ 3.0 };
		RE::SpellItem*     effigyCastSpell{ nullptr };   // 1.3.2: the one spell they cast (none: the player's)
		// Ricochet Rounds
		RE::BGSPerk*       ricochetPerk{ nullptr };
		RE::BGSKeyword*    ricochetKeyword{ nullptr };
		int                ricochetChance{ 25 };
		double             ricochetRange{ 960.0 };
		double             ricochetCooldown{ 1.0 };
	} g_cfg;

	// state - touched only on the game's main thread (hit events and the tick task both run there)
	int               g_rage = 0;
	Clock::time_point g_lastHit{};
	Clock::time_point g_lastFade{};
	Clock::time_point g_lastSprint{};
	Clock::time_point g_outOfCombatSince{};
	bool              g_wasInCombat = false;
	bool              g_vehemenceOn = false;
	std::map<std::pair<RE::FormID, RE::FormID>, Clock::time_point> g_recentHits;   // (cause, target) -> last counted
	std::atomic<bool> g_running{ false };

	double Seconds(Clock::duration a_d) { return std::chrono::duration<double>(a_d).count(); }

	RE::FormID Hex(const nlohmann::json& a_j) { return static_cast<RE::FormID>(std::stoul(a_j.get<std::string>(), nullptr, 16)); }

	template <class T>
	T* Lookup(std::string_view a_plugin, const nlohmann::json& a_id, std::string_view a_what)
	{
		auto* form = RE::TESDataHandler::GetSingleton()->LookupForm<T>(Hex(a_id), a_plugin);
		if (!form) {
			SKSE::log::warn("{} {:06X} not found in {}", a_what, Hex(a_id), a_plugin);
		}
		return form;
	}

	void FollowCastingBar();

	void LoadConfig()
	{
		std::ifstream in{ std::string(kConfigPath) };
		if (!in) {
			SKSE::log::error("{} missing - Rage is off", kConfigPath);
			return;
		}
		nlohmann::json j;
		try {
			j = nlohmann::json::parse(in);
		} catch (const std::exception& e) {
			SKSE::log::error("{}: {} - Rage is off", kConfigPath, e.what());
			return;
		}
		const auto plugin = j["plugin"].get<std::string>();
		const auto actionPlugin = j["actionPlugin"].get<std::string>();
		auto& c = g_cfg;
		c.rageGlobal = Lookup<RE::TESGlobal>(plugin, j["rageGlobal"], "ZP_Rage global");
		c.vehemenceSpell = Lookup<RE::SpellItem>(plugin, j["vehemenceSpell"], "Vehemence spell");
		c.vehemenceEffect = Lookup<RE::EffectSetting>(plugin, j["vehemenceEffect"], "Vehemence effect");
		c.rageEffect = Lookup<RE::EffectSetting>(plugin, j["rageEffect"], "Rage effect");
		c.root = Lookup<RE::BGSPerk>(plugin, j["perks"]["root"], "Bloodied Fury perk");
		c.untempered = Lookup<RE::BGSPerk>(plugin, j["perks"]["untempered"], "Untempered perk");
		c.vehemence = Lookup<RE::BGSPerk>(plugin, j["perks"]["vehemence"], "Vehemence perk");
		c.max = j["max"].get<int>();
		c.maxUntempered = j["maxUntempered"].get<int>();
		c.fadeAfter = j["fadeAfter"].get<double>();
		c.fadeEvery = j["fadeEvery"].get<double>();
		c.combatGrace = j["combatGrace"].get<double>();
		c.sprintGrace = j["sprintGrace"].get<double>();
		c.hitDedupe = j["hitDedupe"].get<double>();
		c.swingWindow = j.value("swingWindow", 0.5);
		if (j.contains("dragonsBreath")) {
			auto& d = j["dragonsBreath"];
			c.dragonPerk = Lookup<RE::BGSPerk>(plugin, d["perk"], "Dragon's Breath perk");
			c.dragonEvery = d["every"].get<int>();
			for (auto& s : d["spells"]) {
				if (auto* spell = Lookup<RE::SpellItem>(plugin, s, "Dragon's Breath spell")) {
					c.dragonSpells.push_back(spell);
				}
			}
			if (d.contains("explosions")) {
				for (auto& s : d["explosions"]) {
					c.dragonBlasts.push_back(Lookup<RE::BGSExplosion>(plugin, s, "Dragon's Breath blast"));
				}
			}
			SKSE::log::info("Dragon's Breath: every {} unarmed hits, {} spells, {} blasts", c.dragonEvery,
				c.dragonSpells.size(), c.dragonBlasts.size());
		}
		if (j.contains("ricochet")) {
			auto& r = j["ricochet"];
			c.ricochetPerk = Lookup<RE::BGSPerk>(plugin, r["perk"], "Ricochet Rounds perk");
			c.ricochetKeyword = Lookup<RE::BGSKeyword>(r["keywordPlugin"].get<std::string>(), r["keyword"], "ZP_FlintlockShot keyword");
			c.ricochetChance = r["chance"].get<int>();
			c.ricochetRange = r["range"].get<double>();
			c.ricochetCooldown = r["cooldown"].get<double>();
			SKSE::log::info("Ricochet Rounds: {}% within {} units", c.ricochetChance, c.ricochetRange);
		}
		if (j.contains("effigies")) {
			auto& e = j["effigies"];
			const auto ep = e["plugin"].get<std::string>();
			for (auto& s : e["spells"]) {
				if (auto* spell = Lookup<RE::SpellItem>(ep, s, "Twin Effigies spell")) {
					c.effigySpells.push_back(spell->GetFormID());
				}
			}
			c.effigyFaction = Lookup<RE::TESFaction>(ep, e["faction"], "effigy faction");
			c.effigyBase = Lookup<RE::TESNPC>(ep, e["base"], "effigy record");
			c.effigyCastEvery = e["castEvery"].get<double>();
			c.effigyRange = e["range"].get<double>();
			c.effigySpawnWindow = e["spawnWindow"].get<double>();
			if (e.contains("castSpell")) {
				c.effigyCastSpell = Lookup<RE::SpellItem>(plugin, e["castSpell"], "effigy cast spell");
			}
			SKSE::log::info("Twin Effigies: {} spells, cast every {} s", c.effigySpells.size(), c.effigyCastEvery);
		}
		if (j.contains("meter")) {
			auto& m = j["meter"];
			c.meterX = m["x"].get<double>();
			c.meterY = m["y"].get<double>();
			c.meterRot = m["rotation"].get<double>();
			c.meterXScale = m["xscale"].get<double>();
			c.meterYScale = m["yscale"].get<double>();
			c.meterBar = static_cast<double>(std::stoul(m["barColour"].get<std::string>(), nullptr, 16));
			c.meterFlash = static_cast<double>(std::stoul(m["flashColour"].get<std::string>(), nullptr, 16));
			c.meterFollowsCastingBar = m.value("followCastingBar", true);
			c.meterXOffset = m.value("xOffset", 0.0);
			c.meterWidth = m.value("width", 0.0);
		}
		for (auto& [trigger, id] : j["powerAttackTypes"].items()) {
			if (auto* kw = Lookup<RE::BGSKeyword>("Skyrim.esm"sv, id, "PowerAttackType keyword")) {
				c.directions[kw] = trigger;
			}
		}
		const bool havePack = RE::TESDataHandler::GetSingleton()->LookupModByName(actionPlugin) != nullptr;
		if (!havePack) {
			SKSE::log::warn("{} is not loaded: Rage builds, but its talents' actions are off", actionPlugin);
		}
		for (auto& ja : j["actions"]) {
			Action a;
			a.name = ja["name"].get<std::string>();
			a.perk = Lookup<RE::BGSPerk>(plugin, ja["perk"], a.name + " perk");
			a.trigger = ja["trigger"].get<std::string>();
			a.cost = ja["cost"].get<int>();
			if (havePack) {
				for (auto& s : ja["spells"]) {
					if (auto* spell = Lookup<RE::SpellItem>(actionPlugin, s, a.name + " spell")) {
						a.spells.push_back(spell);
					}
				}
			}
			SKSE::log::info("action {}: trigger {}, cost {}, {} spells", a.name, a.trigger, a.cost, a.spells.size());
			c.actions.push_back(std::move(a));
		}
		if (c.meterFollowsCastingBar) {
			FollowCastingBar();
		}
		// matched to the health bar (curator 2026-10-27): the movie's bar is centre-anchored (its shape spans -181.7..182.6),
		// so a wider bar also needs its centre moved
		c.meterX += c.meterXOffset;
		if (c.meterWidth > 0.0) {
			c.meterXScale = c.meterWidth;
		}
		c.ready = c.rageGlobal && c.root;
		SKSE::log::info("config loaded: max {}/{}, fade after {} s every {} s, {} actions{}", c.max, c.maxUntempered,
			c.fadeAfter, c.fadeEvery, c.actions.size(), c.ready ? "" : " - NOT READY (global or root perk missing)");
	}

	RE::PlayerCharacter* Player() { return RE::PlayerCharacter::GetSingleton(); }

	bool Has(RE::BGSPerk* a_perk) { return a_perk && Player()->HasPerk(a_perk); }

	bool Untempered() { return Has(g_cfg.untempered); }

	int MaxRage() { return Untempered() ? g_cfg.maxUntempered : g_cfg.max; }

	bool VehemenceActive()
	{
		return g_cfg.vehemenceEffect && Player()->AsMagicTarget()->HasMagicEffect(g_cfg.vehemenceEffect);
	}

	// ---------------------------------------------------------------- the meter
	// Oxygen Meter 2 (in the list) has no API, but its movie interface/oxygenMeter2.swf takes calls on "main." -
	// setLocation(xpos, ypos, rot, xscale, yscale), setBarAndFlashColor(bar, flash), setMeterPercent /
	// updateMeterPercent(percent), doShow, doFadeOut, doFlash (names from oxygenMeter2.dll's strings, parameters from
	// the SWF's function definitions). This opens that movie in a menu of our own, so the air meter is untouched.
	constexpr auto kMeterMenu = "ZenProphecyRageMeter"sv;
	constexpr auto kMeterMovie = "oxygenMeter2"sv;
	bool g_meterRegistered = false;
	bool g_meterShown = false;
	Clock::time_point g_meterZeroSince{};   // when Rage last reached 0 while the meter was shown
	constexpr double  kMeterHideDelay = 1.0;   // seconds at 0 before the meter hides (no flicker on spend-then-hit)
	bool g_meterLaidOut = false;   // 1.0.0 laid it out from a task queued with the menu's kShow - before the menu existed,
	                               // so the meter stayed at the movie's own default spot (top left); now on first use

	// Casting Bar 4.0's live CastingBar.ini (Aspect Layout writes it per screen shape): the centre slot's position and
	// the spell widget's scale, so the Rage meter sits where the casting bar does. Same movie lineage ("meter." /
	// "main." setLocation): percent of the 16:9 stage, which a wider screen extends past (X -5.2 at 21:9 is on screen).
	void FollowCastingBar()
	{
		std::ifstream in{ "Data/SKSE/Plugins/CastingBar.ini" };
		if (!in) {
			SKSE::log::info("meter: no CastingBar.ini - using the configured position");
			return;
		}
		std::string line, section;
		std::optional<double> x, y, scale;
		while (std::getline(in, line)) {
			if (auto c = line.find(';'); c != std::string::npos) {
				line.erase(c);
			}
			std::erase_if(line, [](unsigned char ch) { return std::isspace(ch); });
			if (line.empty()) {
				continue;
			}
			if (line.front() == '[') {
				section = line;
				continue;
			}
			const auto eq = line.find('=');
			if (eq == std::string::npos) {
				continue;
			}
			const auto key = line.substr(0, eq);
			double v = 0.0;
			try {
				v = std::stod(line.substr(eq + 1));
			} catch (...) {
				continue;
			}
			if (section == "[CenterSlot]" && key == "fPositionX") x = v;
			if (section == "[CenterSlot]" && key == "fPositionY") y = v;
			if (section == "[Spell]" && key == "fScale") scale = v;
		}
		if (x && y) {
			g_cfg.meterX = *x;
			g_cfg.meterY = *y;
		}
		if (scale) {
			g_cfg.meterXScale = g_cfg.meterYScale = *scale;
		}
		SKSE::log::info("meter: following CastingBar.ini - {}", x && y ? "centre slot found" : "no [CenterSlot] position");
	}

	RE::GPtr<RE::GFxMovieView> MeterView()
	{
		return g_meterRegistered ? RE::UI::GetSingleton()->GetMovieView(kMeterMenu) : nullptr;
	}

	void MeterCall(const char* a_fn, std::initializer_list<double> a_args = {})
	{
		auto view = MeterView();
		if (!view) {
			return;
		}
		std::vector<RE::GFxValue> args;
		for (double v : a_args) {
			args.emplace_back(v);
		}
		view->Invoke(a_fn, nullptr, args.empty() ? nullptr : args.data(), static_cast<std::uint32_t>(args.size()));
	}

	class RageMeter : public RE::IMenu
	{
	public:
		RageMeter()
		{
			depthPriority = 0;
			menuFlags.set(RE::UI_MENU_FLAGS::kAlwaysOpen, RE::UI_MENU_FLAGS::kRequiresUpdate, RE::UI_MENU_FLAGS::kAllowSaving);
			inputContext = Context::kNone;
			if (!RE::BSScaleformManager::GetSingleton()->LoadMovieEx(this, kMeterMovie, [](RE::GFxMovieDef*) {})) {
				SKSE::log::error("could not load Interface/{}.swf (Oxygen Meter 2): no Rage meter", kMeterMovie);
			}
		}

		static RE::IMenu* Create() { return new RageMeter(); }
	};

	// position, colours, empty - once the menu really exists (MeterView() is null until the queued kShow is processed)
	bool MeterSetUp()
	{
		if (g_meterLaidOut) {
			return true;
		}
		auto view = MeterView();
		if (!view) {
			return false;
		}
		auto& c = g_cfg;
		// the movie's setLocation sets _x/_y straight from its arguments (its bytecode), so the percentages become
		// stage pixels here, as Oxygen Meter's and Casting Bar's own plugins do (both movies' stages are 1920x1080).
		// 1.0.1 passed the percentages through: (-5.2, 90.7) px is the stage's top-left corner, off a 21:9 screen.
		const auto* def = view->GetMovieDef();
		const double w = def ? def->GetWidth() : 1920.0;
		const double h = def ? def->GetHeight() : 1080.0;
		MeterCall("main.setLocation", { c.meterX / 100.0 * w, c.meterY / 100.0 * h, c.meterRot, c.meterXScale, c.meterYScale });
		MeterCall("main.setBarAndFlashColor", { c.meterBar, c.meterFlash });
		MeterCall("main.setMeterPercent", { 0.0 });
		MeterCall("main.doHide");
		g_meterShown = false;
		g_meterLaidOut = true;
		SKSE::log::info("meter laid out at ({}%, {}%) = ({:.0f}, {:.0f}) px of a {}x{} stage, scale {} x {}", c.meterX, c.meterY,
			c.meterX / 100.0 * w, c.meterY / 100.0 * h, w, h, c.meterXScale, c.meterYScale);
		return true;
	}

	void MeterOpen()
	{
		if (!g_meterRegistered) {
			return;
		}
		g_meterLaidOut = false;
		RE::UIMessageQueue::GetSingleton()->AddMessage(kMeterMenu, RE::UI_MESSAGE_TYPE::kShow, nullptr);
	}

	// 1.3.1: something closes the always-open menu (seen 2026-10-29 at a save + message box in Dal'valstaag's vault);
	// open it again, at most once a second, outside loading screens
	Clock::time_point g_meterReopenAt{};

	void MeterKeepOpen()
	{
		auto* ui = RE::UI::GetSingleton();
		if (!g_meterRegistered || !Player() || !Player()->Is3DLoaded() || ui->IsMenuOpen(RE::LoadingMenu::MENU_NAME) ||
			ui->IsMenuOpen(kMeterMenu) || Seconds(Clock::now() - g_meterReopenAt) < 1.0) {
			return;
		}
		g_meterReopenAt = Clock::now();
		SKSE::log::info("meter menu was closed - opening it again");
		MeterOpen();
	}

	void MeterUpdate(int a_rage, int a_max)
	{
		if (!MeterSetUp()) {
			return;
		}
		const double pct = a_max > 0 ? 100.0 * a_rage / a_max : 0.0;
		MeterCall("main.updateMeterPercent", { pct });
		// never doFadeOut: it appends a 1 s fade-to-0 to the movie's FaderTimeline and replays the whole timeline, and doShow
		// does not stop it - each fight added a fade that later hid the shown meter again (1.0.2: "mostly doesn't show").
		// doShow sets _visible/_alpha 100; doHide sets _visible false. The hide waits kMeterHideDelay at 0 (Tick).
		if (a_rage > 0 && !g_meterShown) {
			MeterCall("main.doShow");
			g_meterShown = true;
		} else if (a_rage == 0) {
			g_meterZeroSince = Clock::now();
		}
	}

	// the global (perk conditions), the Rage ability's magnitude (the Active Effects menu) and the meter
	void Publish()
	{
		MeterUpdate(g_rage, MaxRage());
		if (g_cfg.rageGlobal) {
			g_cfg.rageGlobal->value = static_cast<float>(g_rage);
		}
		if (!g_cfg.rageEffect) {
			return;
		}
		if (auto* list = Player()->AsMagicTarget()->GetActiveEffectList()) {
			for (auto* ae : *list) {
				if (ae && ae->GetBaseObject() == g_cfg.rageEffect) {
					ae->magnitude = static_cast<float>(g_rage);
				}
			}
		}
	}

	void SetRage(int a_value, std::string_view a_why)
	{
		const int v = std::clamp(a_value, 0, MaxRage());
		if (v == g_rage) {
			return;
		}
		SKSE::log::info("Rage {} -> {} ({})", g_rage, v, a_why);
		g_rage = v;
		Publish();
		if (g_rage >= MaxRage() && Has(g_cfg.vehemence) && g_cfg.vehemenceSpell && !VehemenceActive()) {
			Player()->GetMagicCaster(RE::MagicSystem::CastingSource::kInstant)
				->CastSpellImmediate(g_cfg.vehemenceSpell, false, Player(), 1.0f, false, 0.0f, Player());
			g_vehemenceOn = true;
			MeterCall("main.doFlash");
			SKSE::log::info("Vehemence");
		}
	}

	// ---------------------------------------------------------------- the power attack's direction
	// 1.0.4's second test: every non-sprint power attack under MCO/For Honor Reforged reports PowerAttackTypeStanding in
	// its attack data, so the keyword only ever said "standing" (24 Shadowbringers, no other action). The direction is in
	// the event the game sends the player's graph to start the attack (the IDLE's AnimationEvent): attackPowerStartInPlace,
	// ...Forward, ...Backward, ...Left/Right, ..._Sprint / _2HMSprint / _2HWSprint, with LeftHand/RightHand/H2H suffixes,
	// and mods' attackStart...Power... names (AttackStartLeftRunningPower: Left is the hand there). Recorded here, read
	// when the hit lands.
	std::string       g_paDirection;
	Clock::time_point g_paAt{};
	constexpr double  kPaWindow = 2.5;   // seconds from the start event to the hit

	std::string DirectionOf(std::string a_event)
	{
		std::ranges::transform(a_event, a_event.begin(), [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
		if (a_event.find("power") == std::string::npos || a_event.starts_with("bash")) {
			return {};
		}
		std::string rest;
		if (a_event.starts_with("attackpowerstart")) {
			rest = a_event.substr(16);
		} else if (a_event.starts_with("attackstart")) {
			rest = a_event.substr(11);
			for (std::string_view hand : { "left"sv, "right"sv }) {     // the hand, not a direction
				if (rest.starts_with(hand)) {
					rest = rest.substr(hand.size());
				}
			}
		} else {
			return {};
		}
		for (std::string_view hand : { "lefthand"sv, "righthand"sv }) {
			if (auto p = rest.find(hand); p != std::string::npos) {
				rest.erase(p, hand.size());
			}
		}
		if (rest.find("sprint") != std::string::npos || rest.find("running") != std::string::npos) return "sprint";
		if (rest.find("back") != std::string::npos) return "back";
		if (rest.find("left") != std::string::npos || rest.find("right") != std::string::npos) return "side";
		if (rest.find("forward") != std::string::npos) return "forward";
		return "standing";
	}

	struct NotifyPlayerGraph
	{
		static bool thunk(RE::IAnimationGraphManagerHolder* a_this, const RE::BSFixedString& a_event)
		{
			if (a_event.c_str()) {
				if (auto dir = DirectionOf(a_event.c_str()); !dir.empty()) {
					// 1.0.5's test: every non-sprint power attack starts as attackPowerStartInPlace - the list picks
					// the directional swing itself, from the movement input at the attack (OAR: For Honor Reforged in
					// third person, SIGMA in first). So "standing" is read from that input too: forward / back /
					// left-right, or nothing held. Works the same in both views.
					std::string from = "event";
					if (dir == "standing") {
						const auto in = RE::PlayerControls::GetSingleton()->data.moveInputVec;
						constexpr float kDead = 0.3f;
						if (in.y > kDead && in.y >= std::abs(in.x)) {
							dir = "forward";
						} else if (in.y < -kDead && -in.y >= std::abs(in.x)) {
							dir = "back";
						} else if (std::abs(in.x) > kDead) {
							dir = "side";
						}
						from = fmt::format("input ({:.2f}, {:.2f})", in.x, in.y);
					}
					g_paDirection = dir;
					g_paAt = Clock::now();
					SKSE::log::info("power attack start '{}' -> {} (from {})", a_event.c_str(), dir, from);
				}
			}
			return func(a_this, a_event);
		}
		static inline REL::Relocation<decltype(thunk)> func;
	};

	std::string Trigger(bool a_sprint)
	{
		if (!g_paDirection.empty() && Seconds(Clock::now() - g_paAt) <= kPaWindow) {
			return (a_sprint && g_paDirection == "forward") ? "sprint" : g_paDirection;
		}
		if (a_sprint) {
			return "sprint";
		}
		auto* proc = Player()->GetActorRuntimeData().currentProcess;
		if (proc && proc->high && proc->high->attackData) {
			auto* kw = proc->high->attackData->data.attackType;
			if (auto it = g_cfg.directions.find(kw); it != g_cfg.directions.end()) {
				return it->second;
			}
			SKSE::log::info("power attack with attack type {:08X} ({}): treated as standing", kw ? kw->GetFormID() : 0,
				kw ? kw->GetFormEditorID() : "none");
		}
		return "standing";
	}

	Clock::time_point g_lastAction{};

	void FireActions(RE::Actor* a_target)
	{
		const auto now = Clock::now();
		// once per swing: a power attack that strikes several enemies raises a hit event for each (1.0.1 fired
		// Shadowbringer twice 16 ms apart and spent Rage twice, 10 -> 5 -> 0)
		if (Seconds(now - g_lastAction) < g_cfg.swingWindow) {
			return;
		}
		g_lastAction = now;
		const bool sprint = Player()->AsActorState()->IsSprinting() || Seconds(now - g_lastSprint) <= g_cfg.sprintGrace;
		const auto trigger = Trigger(sprint);
		const bool free = VehemenceActive();
		int spend = 0;
		for (auto& a : g_cfg.actions) {
			if (a.trigger != trigger || !Has(a.perk) || a.spells.empty() || (!free && g_rage < a.cost)) {
				continue;
			}
			auto* caster = Player()->GetMagicCaster(RE::MagicSystem::CastingSource::kInstant);
			for (auto* s : a.spells) {
				caster->CastSpellImmediate(s, false, a_target, 1.0f, false, 0.0f, Player());
			}
			spend = std::max(spend, a.cost);
			SKSE::log::info("{} ({} power attack){}", a.name, trigger, free ? ", Vehemence: free" : "");
		}
		if (spend > 0 && !free) {
			SetRage(g_rage - spend, "spent");
		}
	}

	// true once per (cause, target) per HitDedupe: one swing can raise several hit events (enchantments, cleaves)
	bool Counts(RE::TESObjectREFR* a_cause, RE::TESObjectREFR* a_target)
	{
		const auto now = Clock::now();
		auto& last = g_recentHits[{ a_cause->GetFormID(), a_target->GetFormID() }];
		const bool counts = Seconds(now - last) > g_cfg.hitDedupe;
		if (counts) {
			last = now;
		}
		if (g_recentHits.size() > 256) {
			std::erase_if(g_recentHits, [&](auto& kv) { return Seconds(now - kv.second) > 5.0; });
		}
		return counts;
	}

	bool IsMeleeWeapon(RE::FormID a_source)
	{
		auto* weap = RE::TESForm::LookupByID<RE::TESObjectWEAP>(a_source);
		return weap && !weap->IsBow() && !weap->IsCrossbow() && !weap->IsStaff();
	}

	// ---------------------------------------------------------------- Dragon's Breath
	int               g_dragonHits = 0;
	Clock::time_point g_dragonLastHit{};
	constexpr double  kDragonSwing = 0.15;  // hit events closer than this are one swing (several targets)

	// 1.1.2: the blast bursts from the punch - at whichever hand node is nearer the target's chest (the current 3D:
	// first or third person). Without 3D, or if the engine will not create the reference there, at the target
	void FistBurst(RE::Actor* a_player, RE::Actor* a_victim, RE::BGSExplosion* a_blast)
	{
		auto aim = a_victim->GetPosition();
		aim.z += a_victim->GetHeight() * 0.6f;
		std::optional<RE::NiPoint3> fist;
		float best = std::numeric_limits<float>::max();
		if (auto* root = a_player->Get3D()) {
			for (auto name : { "NPC R Hand [RHnd]"sv, "NPC L Hand [LHnd]"sv }) {
				if (auto* node = root->GetObjectByName(name)) {
					const auto d = node->world.translate.GetDistance(aim);
					if (d < best) {
						best = d;
						fist = node->world.translate;
					}
				}
			}
		}
		if (fist) {
			const auto ref = RE::TESDataHandler::GetSingleton()->CreateReferenceAtLocation(a_blast, *fist,
				a_player->data.angle, a_player->GetParentCell(), a_player->GetWorldspace(), nullptr, nullptr,
				RE::ObjectRefHandle{}, false, false);
			if (ref) {
				return;
			}
			SKSE::log::warn("Dragon's Breath: no blast reference at the fist - placing it at the target");
		}
		a_victim->PlaceObjectAtMe(a_blast, false);
	}

	void DragonsBreath(const RE::TESHitEvent* a_event)
	{
		auto& c = g_cfg;
		auto* player = Player();
		if (!c.dragonPerk || c.dragonSpells.empty() || a_event->cause.get() != player || a_event->target.get() == player ||
			!Has(c.dragonPerk)) {
			return;
		}
		auto* victim = a_event->target->As<RE::Actor>();
		auto* weap = RE::TESForm::LookupByID<RE::TESObjectWEAP>(a_event->source);
		// 1.1.3: every player hit is logged while the perk is owned (the curator counted more than 5 punches)
		const auto* form = RE::TESForm::LookupByID(a_event->source);
		const auto  kind = form ? static_cast<int>(form->GetFormType()) : -1;
		if (!victim || !weap || !weap->IsHandToHandMelee()) {
			SKSE::log::info("Dragon's Breath: hit on {:08X} by {:08X} (form type {}) - not unarmed",
				a_event->target->GetFormID(), a_event->source, kind);
			return;
		}
		const auto now = Clock::now();
		if (Seconds(now - g_dragonLastHit) < kDragonSwing) {
			SKSE::log::info("Dragon's Breath: punch on {:08X} - same swing, not counted", victim->GetFormID());
			return;
		}
		g_dragonLastHit = now;
		++g_dragonHits;
		SKSE::log::info("Dragon's Breath: punch on {:08X} (flags {:X}) - {}/{}", victim->GetFormID(),
			a_event->flags.underlying(), g_dragonHits, c.dragonEvery);
		if (g_dragonHits < c.dragonEvery) {
			return;
		}
		g_dragonHits = 0;
		static std::mt19937 rng{ std::random_device{}() };
		const auto pick = std::uniform_int_distribution<std::size_t>(0, c.dragonSpells.size() - 1)(rng);
		auto* spell = c.dragonSpells[pick];
		player->GetMagicCaster(RE::MagicSystem::CastingSource::kInstant)
			->CastSpellImmediate(spell, false, victim, 1.0f, false, 0.0f, player);
		if (pick < c.dragonBlasts.size() && c.dragonBlasts[pick]) {
			FistBurst(player, victim, c.dragonBlasts[pick]);
		}
		SKSE::log::info("Dragon's Breath: {:08X} at {:08X}", spell->GetFormID(), victim->GetFormID());
	}

	// ---------------------------------------------------------------- Ricochet Rounds
	RE::FormID        g_ricochetTarget = 0;
	Clock::time_point g_ricochetAt{};

	RE::MagicItem* PistolShot(RE::FormID a_source)
	{
		auto* form = RE::TESForm::LookupByID(a_source);
		if (!form) {
			return nullptr;
		}
		RE::MagicItem* shot = nullptr;
		if (auto* weap = form->As<RE::TESObjectWEAP>()) {
			shot = weap->formEnchanting;
		} else {
			shot = form->As<RE::MagicItem>();
		}
		if (!shot) {
			return nullptr;
		}
		for (auto* e : shot->effects) {
			if (e && e->baseEffect && e->baseEffect->HasKeyword(g_cfg.ricochetKeyword)) {
				return shot;
			}
		}
		return nullptr;
	}

	void Ricochet(const RE::TESHitEvent* a_event)
	{
		auto& c = g_cfg;
		auto* player = Player();
		if (!c.ricochetPerk || !c.ricochetKeyword || a_event->cause.get() != player || a_event->target.get() == player ||
			!Has(c.ricochetPerk)) {
			return;
		}
		auto* victim = a_event->target->As<RE::Actor>();
		auto* shot = victim ? PistolShot(a_event->source) : nullptr;
		if (!shot) {
			return;
		}
		const auto now = Clock::now();
		if (victim->GetFormID() == g_ricochetTarget && Seconds(now - g_ricochetAt) < c.ricochetCooldown) {
			return;   // the bounce's own hit
		}
		static std::mt19937 rng{ std::random_device{}() };
		if (std::uniform_int_distribution<int>(1, 100)(rng) > c.ricochetChance) {
			return;
		}
		RE::Actor* next = nullptr;
		float      bestD = static_cast<float>(c.ricochetRange);
		for (auto& h : RE::ProcessLists::GetSingleton()->highActorHandles) {
			auto a = h.get();
			if (!a || a.get() == victim || a.get() == player || a->IsDead() || !a->IsHostileToActor(player)) {
				continue;
			}
			const auto d = a->GetPosition().GetDistance(victim->GetPosition());
			if (d < bestD) {
				bestD = d;
				next = a.get();
			}
		}
		if (!next) {
			SKSE::log::info("Ricochet: no other foe within {} of {:08X}", c.ricochetRange, victim->GetFormID());
			return;
		}
		g_ricochetTarget = next->GetFormID();
		g_ricochetAt = now;
		victim->GetMagicCaster(RE::MagicSystem::CastingSource::kInstant)
			->CastSpellImmediate(shot, false, next, 1.0f, false, 0.0f, player);
		SKSE::log::info("Ricochet: {:08X} bounced off {:08X} into {:08X} ({:.0f} units)", shot->GetFormID(),
			victim->GetFormID(), next->GetFormID(), bestD);
	}

	class HitSink : public RE::BSTEventSink<RE::TESHitEvent>
	{
	public:
		static HitSink* Get()
		{
			static HitSink sink;
			return &sink;
		}

		RE::BSEventNotifyControl ProcessEvent(const RE::TESHitEvent* a_event, RE::BSTEventSource<RE::TESHitEvent>*) override
		{
			using Flag = RE::TESHitEvent::Flag;
			if (!a_event || !a_event->cause || !a_event->target) {
				return RE::BSEventNotifyControl::kContinue;
			}
			DragonsBreath(a_event);
			Ricochet(a_event);
			if (!g_cfg.ready || !Has(g_cfg.root)) {
				return RE::BSEventNotifyControl::kContinue;
			}
			auto* player = Player();
			auto* cause = a_event->cause.get();
			auto* target = a_event->target.get();
			if (cause == player && target != player) {
				auto* victim = target->As<RE::Actor>();
				if (!victim || !IsMeleeWeapon(a_event->source) || !Counts(cause, target)) {
					return RE::BSEventNotifyControl::kContinue;
				}
				g_lastHit = Clock::now();
				// actions first, on the Rage the swing started with; then the hit's own stack
				if (a_event->flags.any(Flag::kPowerAttack)) {
					FireActions(victim);
				}
				SetRage(g_rage + 1, "hit landed");
			} else if (target == player && cause != player && cause->As<RE::Actor>()) {
				if (!RE::TESForm::LookupByID<RE::TESObjectWEAP>(a_event->source) || !Counts(cause, target)) {
					return RE::BSEventNotifyControl::kContinue;   // weapon hits only: spells and hazards raise their own events
				}
				g_lastHit = Clock::now();
				SetRage(g_rage + 1, "hit taken");
			}
			return RE::BSEventNotifyControl::kContinue;
		}
	};

	// ---------------------------------------------------------------- Twin Effigies
	struct Effigy
	{
		std::vector<RE::SpellItem*> spells;
		Clock::time_point           next{};
		std::size_t                 turn{ 0 };
	};
	std::vector<RE::SpellItem*>       g_effigyLoadout;       // the hands' spells at the last Twin Effigies cast
	Clock::time_point                 g_effigyCastAt{};
	std::map<RE::FormID, Effigy>      g_effigies;            // live effigy refs -> what they cast

	bool IsEffigySpell(RE::FormID a_id)
	{
		return std::find(g_cfg.effigySpells.begin(), g_cfg.effigySpells.end(), a_id) != g_cfg.effigySpells.end();
	}

	bool CastsWell(RE::SpellItem* a_spell)
	{
		using Arch = RE::EffectArchetypes::ArchetypeID;
		if (!a_spell || a_spell->GetSpellType() != RE::MagicSystem::SpellType::kSpell || IsEffigySpell(a_spell->GetFormID())) {
			return false;
		}
		for (auto* e : a_spell->effects) {
			if (e && e->baseEffect) {
				const auto a = e->baseEffect->GetArchetype();
				if (a == Arch::kSummonCreature || a == Arch::kReanimate || a == Arch::kCommandSummoned) {
					return false;   // an effigy's summons would bypass the player's summon limit
				}
			}
		}
		return true;
	}

	class CastSink : public RE::BSTEventSink<RE::TESSpellCastEvent>
	{
	public:
		static CastSink* Get()
		{
			static CastSink sink;
			return &sink;
		}

		RE::BSEventNotifyControl ProcessEvent(const RE::TESSpellCastEvent* a_event, RE::BSTEventSource<RE::TESSpellCastEvent>*) override
		{
			auto* player = Player();
			if (!a_event || !a_event->object || a_event->object.get() != player || !IsEffigySpell(a_event->spell)) {
				return RE::BSEventNotifyControl::kContinue;
			}
			g_effigyLoadout.clear();
			for (bool left : { false, true }) {
				if (g_cfg.effigyCastSpell) {
					g_effigyLoadout.push_back(g_cfg.effigyCastSpell);
					break;
				}
				auto* obj = player->GetEquippedObject(left);
				auto* spell = obj ? obj->As<RE::SpellItem>() : nullptr;
				if (CastsWell(spell) &&
					std::find(g_effigyLoadout.begin(), g_effigyLoadout.end(), spell) == g_effigyLoadout.end()) {
					g_effigyLoadout.push_back(spell);
				}
			}
			g_effigyCastAt = Clock::now();
			std::string names;
			for (auto* s : g_effigyLoadout) {
				names += (names.empty() ? "" : ", ") + std::string(s->GetName());
			}
			SKSE::log::info("Twin Effigies cast: the effigies will cast [{}]", names);
			return RE::BSEventNotifyControl::kContinue;
		}
	};

	bool IsEffigy(RE::Actor* a_actor)
	{
		auto& c = g_cfg;
		return a_actor && ((c.effigyFaction && a_actor->IsInFaction(c.effigyFaction)) ||
							  (c.effigyBase && a_actor->GetActorBase() == c.effigyBase));
	}

	RE::Actor* EffigyTarget(RE::Actor* a_effigy, RE::Actor* a_player)
	{
		auto ok = [&](RE::Actor* a) {
			return a && a != a_player && a != a_effigy && !a->IsDead() && !IsEffigy(a) && a->IsHostileToActor(a_player) &&
			       a->GetPosition().GetDistance(a_effigy->GetPosition()) <= g_cfg.effigyRange;
		};
		if (auto target = a_effigy->GetActorRuntimeData().currentCombatTarget.get(); ok(target.get())) {
			return target.get();
		}
		RE::Actor* best = nullptr;
		float      bestD = std::numeric_limits<float>::max();
		for (auto& h : RE::ProcessLists::GetSingleton()->highActorHandles) {
			auto a = h.get();
			if (ok(a.get())) {
				const auto d = a->GetPosition().GetDistance(a_effigy->GetPosition());
				if (d < bestD) {
					bestD = d;
					best = a.get();
				}
			}
		}
		return best;
	}

	void EffigyTick(RE::Actor* a_player)
	{
		auto& c = g_cfg;
		if (c.effigySpells.empty()) {
			return;
		}
		const auto now = Clock::now();
		// new effigies: the ones that appear just after a Twin Effigies cast take that cast's spells
		if (!g_effigyLoadout.empty() && Seconds(now - g_effigyCastAt) <= c.effigySpawnWindow) {
			for (auto& h : RE::ProcessLists::GetSingleton()->highActorHandles) {
				auto a = h.get();
				if (a && IsEffigy(a.get()) && !a->IsDead() && !g_effigies.contains(a->GetFormID())) {
					g_effigies[a->GetFormID()] = { g_effigyLoadout, now + std::chrono::milliseconds(750), 0 };
					SKSE::log::info("effigy {:08X}: casts {} spell(s)", a->GetFormID(), g_effigyLoadout.size());
				}
			}
		}
		for (auto it = g_effigies.begin(); it != g_effigies.end();) {
			auto* e = RE::TESForm::LookupByID<RE::Actor>(it->first);
			if (!e || e->IsDead() || e->IsDisabled() || e->IsDeleted() || !e->Is3DLoaded()) {
				it = g_effigies.erase(it);
				continue;
			}
			auto& st = it->second;
			if (now >= st.next && !st.spells.empty()) {
				if (auto* target = EffigyTarget(e, a_player)) {
					auto* spell = st.spells[st.turn++ % st.spells.size()];
					auto* at = spell->GetDelivery() == RE::MagicSystem::Delivery::kSelf ? e : target;
					e->GetMagicCaster(RE::MagicSystem::CastingSource::kInstant)
						->CastSpellImmediate(spell, false, at, 1.0f, false, 0.0f, a_player);
					st.next = now + std::chrono::milliseconds(static_cast<long long>(c.effigyCastEvery * 1000));
				} else {
					st.next = now + std::chrono::milliseconds(500);
				}
			}
			++it;
		}
	}

	// every 250 ms on the main thread: sprint memory, fading, combat end, Vehemence's end
	void Tick()
	{
		auto* player = Player();
		const bool paused = RE::UI::GetSingleton()->GameIsPaused();
		if (player && player->Is3DLoaded() && !paused) {
			EffigyTick(player);
		}
		MeterKeepOpen();
		if (auto view = MeterView()) {
			MeterSetUp();
			if (g_rage > 0 && !g_meterShown) {
				MeterUpdate(g_rage, MaxRage());   // after a reopen's layout hid it
			}
			if (g_meterShown && g_rage == 0 && Seconds(Clock::now() - g_meterZeroSince) >= kMeterHideDelay) {
				MeterCall("main.doHide");
				g_meterShown = false;
			}
			view->SetVisible(!paused);   // the menu is always open: keep it out of the inventory, map and other menus
		}
		if (!g_cfg.ready || !player || !player->Is3DLoaded() || paused) {
			return;
		}
		const auto now = Clock::now();
		if (player->AsActorState()->IsSprinting()) {
			g_lastSprint = now;
		}
		if (g_vehemenceOn && !VehemenceActive()) {
			g_vehemenceOn = false;
			SetRage(0, "Vehemence ended");
		}
		if (g_rage == 0) {
			return;
		}
		// out of combat for CombatGrace - counted from the later of leaving combat and the last hit. 1.0.0 counted from
		// leaving combat only, and a fight the game had not flagged as combat yet (the first swings) had no such moment,
		// so Rage reset within 0.25 s of being built (5 -> 0 mid-fight in the first test).
		const bool inCombat = player->IsInCombat();
		if (!inCombat) {
			if (g_wasInCombat) {
				g_outOfCombatSince = now;
			}
			const auto since = std::max(g_outOfCombatSince, g_lastHit);
			if (Seconds(now - since) >= g_cfg.combatGrace) {
				SetRage(0, "out of combat");
			}
		}
		g_wasInCombat = inCombat;
		const double every = g_cfg.fadeEvery * (Untempered() ? 2.0 : 1.0);
		if (!VehemenceActive() && Seconds(now - g_lastHit) >= g_cfg.fadeAfter && Seconds(now - g_lastFade) >= every) {
			g_lastFade = now;
			SetRage(g_rage - 1, "fading");
		}
	}

	void StartTicker()
	{
		if (g_running.exchange(true)) {
			return;
		}
		std::thread([] {
			while (g_running) {
				std::this_thread::sleep_for(250ms);
				SKSE::GetTaskInterface()->AddTask([] { Tick(); });
			}
		}).detach();
	}

	void OnMessage(SKSE::MessagingInterface::Message* a_msg)
	{
		switch (a_msg->type) {
		case SKSE::MessagingInterface::kDataLoaded:
			LoadConfig();
			RE::ScriptEventSourceHolder::GetSingleton()->AddEventSink<RE::TESHitEvent>(HitSink::Get());
			RE::ScriptEventSourceHolder::GetSingleton()->AddEventSink<RE::TESSpellCastEvent>(CastSink::Get());
			if (std::filesystem::exists("Data/Interface/oxygenMeter2.swf")) {
				RE::UI::GetSingleton()->Register(kMeterMenu, RageMeter::Create);
				g_meterRegistered = true;
			} else {
				SKSE::log::warn("Interface/oxygenMeter2.swf not found (Oxygen Meter 2 not installed): no Rage meter");
			}
			StartTicker();
			break;
		case SKSE::MessagingInterface::kPostLoadGame:
		case SKSE::MessagingInterface::kNewGame:
			MeterOpen();
			SKSE::GetTaskInterface()->AddTask([] {
				g_rage = 0;
				g_vehemenceOn = false;
				g_effigies.clear();
				g_effigyLoadout.clear();
				Publish();
			});
			break;
		default:
			break;
		}
	}
}

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	SKSE::log::info("ZenProphecyRage 1.3.2 loading, runtime {}", REL::Module::get().version().string());
	// the player's graph events (power attack direction): PlayerCharacter's IAnimationGraphManagerHolder vtable, slot 1
	REL::Relocation<std::uintptr_t> graphVtbl{ RE::VTABLE_PlayerCharacter[3] };
	NotifyPlayerGraph::func = graphVtbl.write_vfunc(0x1, NotifyPlayerGraph::thunk);
	SKSE::GetMessagingInterface()->RegisterListener(OnMessage);
	return true;
}
