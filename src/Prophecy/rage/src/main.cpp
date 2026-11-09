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
// 1.3.3: the bounce is a real bullet - the shot's own projectile launched from just past the first target towards the
// second (Projectile::Launch, shooter the player). 1.3.0's CastSpellImmediate from the target's instant caster fired
// (logged) but showed no projectile (curator 2026-10-29). Each shot's hit arrives twice; one bounce per victim per
// 0.15 s.
//
// The pistol branch (Firearms, 1.4.0, curator 2026-11-01). On a pistol hit (as Ricochet's, once per shot):
// - Hair Trigger casts its hit spell at the target (Elemental Rounds' fire and Bleeding Shot's bleed, each gated on
//   its own perk in the record);
// - Point Blank (target within PointBlankRange of the player) and Coup de Grace (target staggered, knocked down,
//   bleeding out or below CoupHealth of its Health) add fractions of the shot's damage, dealt as one extra damage
//   spell. The shot's damage is each keyworded effect's magnitude through the ModSpellMagnitude entry point, as the
//   engine computes it (ID 34053 calls HandleEntryPoint 0x1D with caster, spell, target, &magnitude); Point Blank also
//   casts the Utility Droid's stagger;
// - Blade and Barrel adds its marker ability (its perk's ModAttackDamage entry reads it) until the next melee hit or
//   BladeSeconds; a melee hit with a pistol in either hand sends mod event ZP_FlintlockReload, which the Flintlock
//   Overhaul's reload script answers by loading every fired pistol at once.
// Fan the Hammer's effect makes every pistol hit ricochet (Ricochet Rounds owned or not); Hair Trigger raises the chance
// (2026-11-02: its faster reload went - the ramrod reload sets the pace).
//
// Arcane Arsenal's elemental arrows (Arcane Archery, 1.6.0, curator 2026-11-02): with Arcane Arsenal's element global
// at 1-3, that element's art object (a shrunk spell-menu orb: fire, frost, lightning) burns on the arrowhead
// - while the player holds a bow with an arrow nocked (attack state BowAttached/BowDrawn), and
// - on every arrow the player shoots from a bow, from launch until it hits something or is gone.
// The art is attached (ApplyArtObject with an attach node) to a node of ours placed at the arrow's head: the head is
// the end of the arrow mesh's bound along its Y axis that points the way the player faces (nocked) or the way the
// arrow flies. 1.5.0 used the enchantment shaders, which the engine draws over the whole actor whatever the node.
// Every 20 ms; our art effects are stopped before a save and after a load (an endless art would be saved).
// 1.6.1 (2026-11-05, player crash log): the engine's ApplyArtObject (ID 22769) returns a BOOL on 1.7.104, not the
// ModelReferenceEffect* CommonLib's header says (rax = 1 at the call, disassembled); 1.6.0 kept that 1 as a pointer and
// crashed on its refcount at every first draw. The effect is never kept now: it is found again when it has to stop
// (ProcessLists::ForEachModelEffect: our art object on that reference).
// Log: My Games/Skyrim Special Edition/SKSE/ZenProphecyRage.log

SKSEPluginInfo(
	.Version = REL::Version{ 1, 6, 3, 0 },
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
		int                ricochetHairTriggerBonus{ 25 };   // added to the chance with Hair Trigger (2026-11-02)
		double             ricochetRange{ 960.0 };
		double             ricochetCooldown{ 1.0 };
		// the pistol branch
		RE::BGSPerk*       hairTrigger{ nullptr };
		RE::BGSPerk*       pointBlank{ nullptr };
		RE::BGSPerk*       bladeBarrel{ nullptr };
		RE::BGSPerk*       coup{ nullptr };
		RE::SpellItem*     pistolHitSpell{ nullptr };
		RE::SpellItem*     bonusSpell{ nullptr };
		RE::SpellItem*     staggerSpell{ nullptr };
		RE::SpellItem*     bladeAbility{ nullptr };
		RE::EffectSetting* fanEffect{ nullptr };
		double             pointBlankRange{ 256.0 };
		double             pointBlankBonus{ 0.5 };
		double             coupBonus{ 1.0 };
		double             coupHealth{ 0.25 };
		double             bladeSeconds{ 3.0 };
		// Arcane Arsenal's elemental arrows
		RE::BGSPerk*       arsenalPerk{ nullptr };
		RE::TESGlobal*     arsenalGlobal{ nullptr };
		std::vector<RE::BGSArtObject*> arsenalArts;   // fire, frost, lightning
		float              arsenalScale{ 0.3f };
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
			c.ricochetHairTriggerBonus = r.value("hairTriggerBonus", 0);
			c.ricochetRange = r["range"].get<double>();
			c.ricochetCooldown = r["cooldown"].get<double>();
			SKSE::log::info("Ricochet Rounds: {}% (+{}% with Hair Trigger) within {} units", c.ricochetChance,
				c.ricochetHairTriggerBonus, c.ricochetRange);
		}
		if (j.contains("pistols")) {
			auto& p = j["pistols"];
			c.hairTrigger = Lookup<RE::BGSPerk>(plugin, p["hairTrigger"], "Hair Trigger perk");
			c.pointBlank = Lookup<RE::BGSPerk>(plugin, p["pointBlank"], "Point Blank perk");
			c.bladeBarrel = Lookup<RE::BGSPerk>(plugin, p["bladeBarrel"], "Blade and Barrel perk");
			c.coup = Lookup<RE::BGSPerk>(plugin, p["coup"], "Coup de Grace perk");
			c.pistolHitSpell = Lookup<RE::SpellItem>(plugin, p["hitSpell"], "Hair Trigger hit spell");
			c.bonusSpell = Lookup<RE::SpellItem>(plugin, p["bonusSpell"], "pistol bonus damage spell");
			c.staggerSpell = Lookup<RE::SpellItem>(plugin, p["staggerSpell"], "Point Blank stagger spell");
			c.bladeAbility = Lookup<RE::SpellItem>(plugin, p["bladeAbility"], "Blade and Barrel ability");
			c.fanEffect = Lookup<RE::EffectSetting>(plugin, p["fanEffect"], "Fan the Hammer effect");
			c.pointBlankRange = p["pointBlankRange"].get<double>();
			c.pointBlankBonus = p["pointBlankBonus"].get<double>();
			c.coupBonus = p["coupBonus"].get<double>();
			c.coupHealth = p["coupHealth"].get<double>();
			c.bladeSeconds = p["bladeSeconds"].get<double>();
			SKSE::log::info("pistol talents: point blank {} units +{}, coup +{} below {}, blade {} s", c.pointBlankRange,
				c.pointBlankBonus, c.coupBonus, c.coupHealth, c.bladeSeconds);
		}
		if (j.contains("arsenal")) {
			auto& a = j["arsenal"];
			c.arsenalPerk = Lookup<RE::BGSPerk>(plugin, a["perk"], "Arcane Arsenal perk");
			c.arsenalGlobal = Lookup<RE::TESGlobal>(plugin, a["global"], "Arcane Arsenal element global");
			for (auto& s : a["arts"]) {
				c.arsenalArts.push_back(Lookup<RE::BGSArtObject>(plugin, s, "Arcane Arsenal arrow art"));
			}
			c.arsenalScale = a.value("scale", 0.3f);
			SKSE::log::info("Arcane Arsenal arrows: {} arts, scale {}", c.arsenalArts.size(), c.arsenalScale);
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
	// 1.6.3 (curator, 2026-11-09: "a lot of Rage talents aren't triggering in first person, especially one-handed"):
	// the log showed power attacks whose hits landed, with Rage to spare, and fired nothing - the hit event came
	// without its PowerAttack flag. The flag is read from the attacker's current attack data at the hit, and in first
	// person that is not reliably the power attack's. So the graph hook also remembers whether the LAST attack start
	// of any kind was a power attack, and a melee hit inside kPaWindow of a power start with no light start since
	// counts as a power-attack hit whatever the flag says.
	bool              g_lastStartPower = false;
	Clock::time_point g_lastStartAt{};

	// an attack start of any kind (light or power, either hand), never a bash
	bool IsAttackStart(std::string a_event)
	{
		std::ranges::transform(a_event, a_event.begin(), [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
		return (a_event.starts_with("attackstart") || a_event.starts_with("attackpowerstart")) && !a_event.starts_with("bash");
	}

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
				if (IsAttackStart(a_event.c_str())) {
					g_lastStartPower = !DirectionOf(a_event.c_str()).empty();
					g_lastStartAt = Clock::now();
				}
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
		// 1.6.2 (cptflame, 2026-11-06: the Staff of Electrospheres fired Invoker): a hit the engine blames on the
		// player with no weapon of its own (a staff's spheres, a placed hazard) carries the empty hand's fist as its
		// source, so the source alone does not prove a punch. Both hands must be free of weapons (spells are fine).
		for (const bool left : { false, true }) {
			auto* held = player->GetEquippedObject(left);
			auto* heldWeap = held ? held->As<RE::TESObjectWEAP>() : nullptr;
			if (heldWeap && !heldWeap->IsHandToHandMelee()) {
				SKSE::log::info("Dragon's Breath: hit on {:08X} blamed on the fist while {:08X} is in the {} hand - not a punch",
					victim->GetFormID(), heldWeap->GetFormID(), left ? "left" : "right");
				return;
			}
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
	RE::FormID        g_ricochetVictim = 0;     // 1.3.3: the same shot's second hit event
	Clock::time_point g_ricochetVictimAt{};

	void LaunchBounce(RE::MagicItem* a_shot, RE::Actor* a_from, RE::Actor* a_to, RE::Actor* a_player)
	{
		auto* mgef = a_shot->GetAVEffect();
		auto* proj = mgef ? mgef->data.projectileBase : nullptr;
		if (!proj) {
			SKSE::log::info("Ricochet: {:08X} has no projectile - cast instead", a_shot->GetFormID());
			a_from->GetMagicCaster(RE::MagicSystem::CastingSource::kInstant)
				->CastSpellImmediate(a_shot, false, a_to, 1.0f, false, 0.0f, a_player);
			return;
		}
		RE::NiPoint3 from = a_from->GetPosition();
		from.z += a_from->GetHeight() * 0.6f;
		RE::NiPoint3 to = a_to->GetPosition();
		to.z += a_to->GetHeight() * 0.6f;
		RE::NiPoint3 d = to - from;
		const float len = d.Length();
		if (len < 1.0f) {
			return;
		}
		d /= len;
		const float clear = std::min(60.0f, len * 0.5f);   // start outside the first target's body
		from += d * clear;
		RE::Projectile::ProjectileRot rot{ std::atan2(-d.z, std::hypot(d.x, d.y)), std::atan2(d.x, d.y) };
		RE::Projectile::LaunchData data(a_player, from, rot, a_shot);
		data.projectileBase = proj;
		data.parentCell = a_from->GetParentCell();
		data.desiredTarget = a_to;
		data.castingSource = RE::MagicSystem::CastingSource::kInstant;
		data.autoAim = false;
		data.useOrigin = true;
		RE::ProjectileHandle handle{};
		RE::Projectile::Launch(&handle, data);
		SKSE::log::info("Ricochet: launched {:08X} ({}) {:.0f} units", proj->GetFormID(), handle ? "ok" : "no handle", len);
	}

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

	bool FanActive()
	{
		return g_cfg.fanEffect && Player()->AsMagicTarget()->HasMagicEffect(g_cfg.fanEffect);
	}

	// ---------------------------------------------------------------- the pistol branch
	RE::FormID        g_pistolVictim = 0;       // each shot's hit arrives twice: one per victim per 0.15 s
	Clock::time_point g_pistolVictimAt{};
	bool              g_bladeOn = false;        // Blade and Barrel's ability is on the player
	Clock::time_point g_bladeUntil{};

	// the shot's damage on this target: its keyworded effects' magnitudes after the caster's ModSpellMagnitude perks
	float ShotDamage(RE::MagicItem* a_shot, RE::Actor* a_player, RE::Actor* a_victim)
	{
		float total = 0.0f;
		for (auto* e : a_shot->effects) {
			if (e && e->baseEffect && e->baseEffect->HasKeyword(g_cfg.ricochetKeyword)) {
				float m = e->effectItem.magnitude;
				RE::BGSEntryPoint::HandleEntryPoint(RE::BGSEntryPoint::ENTRY_POINT::kModSpellMagnitude, a_player,
					a_shot, a_victim, &m);
				total += m;
			}
		}
		return total;
	}

	bool Vulnerable(RE::Actor* a_victim)
	{
		auto* st = a_victim->AsActorState();
		if (st->IsBleedingOut() || st->IsStaggered() || st->GetKnockState() != RE::KNOCK_STATE_ENUM::kNormal) {
			return true;
		}
		auto*       av = a_victim->AsActorValueOwner();
		const float max = av->GetPermanentActorValue(RE::ActorValue::kHealth);
		return max > 0.0f && av->GetActorValue(RE::ActorValue::kHealth) < max * static_cast<float>(g_cfg.coupHealth);
	}

	void BladeOff(const char* a_why)
	{
		if (g_bladeOn && g_cfg.bladeAbility) {
			Player()->RemoveSpell(g_cfg.bladeAbility);
			SKSE::log::info("Blade and Barrel: marker off ({})", a_why);
		}
		g_bladeOn = false;
	}

	bool PistolInHand(RE::Actor* a_player)
	{
		for (bool left : { false, true }) {
			if (auto* obj = a_player->GetEquippedObject(left); obj && PistolShot(obj->GetFormID())) {
				return true;
			}
		}
		return false;
	}

	void PistolTalents(const RE::TESHitEvent* a_event)
	{
		auto& c = g_cfg;
		auto* player = Player();
		if (!c.ricochetKeyword || a_event->cause.get() != player || a_event->target.get() == player) {
			return;
		}
		auto* victim = a_event->target->As<RE::Actor>();
		if (!victim) {
			return;
		}
		// a melee hit: Blade and Barrel spends its bonus (the hit's damage already had it) and reloads the pistols
		if (IsMeleeWeapon(a_event->source)) {
			BladeOff("melee hit");
			if (Has(c.bladeBarrel) && PistolInHand(player)) {
				SKSE::ModCallbackEvent ev{ "ZP_FlintlockReload", "", 0.0f, nullptr };
				SKSE::GetModCallbackEventSource()->SendEvent(&ev);
				SKSE::log::info("Blade and Barrel: melee hit on {:08X} - reload sent", victim->GetFormID());
			}
			return;
		}
		auto* shot = PistolShot(a_event->source);
		if (!shot) {
			return;
		}
		const auto now = Clock::now();
		if (victim->GetFormID() == g_pistolVictim && Seconds(now - g_pistolVictimAt) < 0.15) {
			return;
		}
		g_pistolVictim = victim->GetFormID();
		g_pistolVictimAt = now;
		auto* caster = player->GetMagicCaster(RE::MagicSystem::CastingSource::kInstant);
		if (Has(c.hairTrigger) && c.pistolHitSpell) {
			caster->CastSpellImmediate(c.pistolHitSpell, false, victim, 1.0f, false, 0.0f, player);
		}
		double     bonus = 0.0;
		const bool coup = Has(c.coup) && Vulnerable(victim);   // before Point Blank's own stagger
		const auto dist = player->GetPosition().GetDistance(victim->GetPosition());
		const bool close = Has(c.pointBlank) && dist <= c.pointBlankRange;
		if (coup) {
			bonus += c.coupBonus;
		}
		if (close) {
			bonus += c.pointBlankBonus;
		}
		if (bonus > 0.0 && c.bonusSpell && !victim->IsDead()) {
			const float dmg = ShotDamage(shot, player, victim) * static_cast<float>(bonus);
			if (dmg > 0.0f) {
				caster->CastSpellImmediate(c.bonusSpell, false, victim, 1.0f, false, dmg, player);
			}
			SKSE::log::info("pistol hit on {:08X} ({:.0f} units){}{}: +{:.1f}", victim->GetFormID(), dist,
				coup ? " coup de grace" : "", close ? " point blank" : "", dmg);
		}
		if (close && c.staggerSpell && !victim->IsDead()) {
			caster->CastSpellImmediate(c.staggerSpell, false, victim, 1.0f, false, 0.0f, player);
		}
		if (Has(c.bladeBarrel) && c.bladeAbility) {
			if (!g_bladeOn) {
				player->AddSpell(c.bladeAbility);
			}
			g_bladeOn = true;
			g_bladeUntil = now + std::chrono::milliseconds(static_cast<long long>(c.bladeSeconds * 1000));
		}
	}

	void Ricochet(const RE::TESHitEvent* a_event)
	{
		auto& c = g_cfg;
		auto* player = Player();
		if (!c.ricochetKeyword || a_event->cause.get() != player || a_event->target.get() == player) {
			return;
		}
		const bool fan = FanActive();   // 1.4.0: Fan the Hammer - every pistol hit ricochets
		if (!fan && !Has(c.ricochetPerk)) {
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
		if (victim->GetFormID() == g_ricochetVictim && Seconds(now - g_ricochetVictimAt) < 0.15) {
			return;   // the same shot's second hit event
		}
		g_ricochetVictim = victim->GetFormID();
		g_ricochetVictimAt = now;
		static std::mt19937 rng{ std::random_device{}() };
		const int chance = c.ricochetChance + (Has(c.hairTrigger) ? c.ricochetHairTriggerBonus : 0);
		if (!fan && std::uniform_int_distribution<int>(1, 100)(rng) > chance) {
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
		LaunchBounce(shot, victim, next, player);
		SKSE::log::info("Ricochet: {:08X} bounced off {:08X} into {:08X} ({:.0f} units)", shot->GetFormID(),
			victim->GetFormID(), next->GetFormID(), bestD);
	}

	// ---------------------------------------------------------------- Arcane Arsenal's elemental arrows
	struct ArrowArt
	{
		RE::NiPointer<RE::NiNode> tip;              // our node at the arrowhead the art hangs on
		RE::BGSArtObject*         art{ nullptr };
		RE::FormID                on{ 0 };          // the reference the art was applied to
		bool                      applied{ false };
		bool                      done{ false };    // flying arrow that hit: never again
	};
	ArrowArt                                   g_nocked;
	RE::NiPointer<RE::NiAVObject>              g_nockedArrow;   // the arrow mesh g_nocked sits on
	std::map<RE::FormID, ArrowArt>             g_flying;        // the player's arrows in flight
	std::vector<RE::NiPointer<RE::NiNode>>     g_staleTips;     // detached on the next tick (after the art let go)
	int                                        g_arrowMisses = 0;

	std::string Lower(std::string_view a_s)
	{
		std::string s(a_s);
		std::transform(s.begin(), s.end(), s.begin(), [](unsigned char ch) { return static_cast<char>(std::tolower(ch)); });
		return s;
	}

	RE::NiAVObject* FindArrowIn(RE::NiAVObject* a_obj, const std::string& a_stem, int a_depth)
	{
		if (!a_obj || a_depth > 4) {
			return nullptr;
		}
		const auto name = Lower(a_obj->name.c_str());
		if (!name.empty() && ((!a_stem.empty() && name.find(a_stem) != std::string::npos) || name.find("arrow") != std::string::npos)) {
			return a_obj;
		}
		if (auto* node = a_obj->AsNode()) {
			for (auto& child : node->GetChildren()) {
				if (auto* hit = FindArrowIn(child.get(), a_stem, a_depth + 1)) {
					return hit;
				}
			}
		}
		return nullptr;
	}

	// The arrow's own mesh under a_obj: a lit (BSLightingShaderProperty) shape, preferring one named like an arrow;
	// a flight model also holds effect-shader tracer shapes (trailShort, Flow), which are never picked.
	RE::BSGeometry* ArrowMesh(RE::NiAVObject* a_obj, int a_depth = 0)
	{
		if (!a_obj || a_depth > 5) {
			return nullptr;
		}
		if (auto* g = a_obj->AsGeometry()) {
			return g->lightingShaderProp_cast() ? g : nullptr;
		}
		RE::BSGeometry* any = nullptr;
		if (auto* node = a_obj->AsNode()) {
			for (auto& child : node->GetChildren()) {
				if (auto* g = ArrowMesh(child.get(), a_depth + 1)) {
					const auto n = Lower(g->name.c_str());
					if (n.find("arrow") != std::string::npos || n.find("bolt") != std::string::npos) {
						return g;
					}
					if (!any) {
						any = g;
					}
				}
			}
		}
		return any;
	}

	void LogChildren(RE::NiAVObject* a_root, const char* a_name)
	{
		auto* at = a_root ? a_root->GetObjectByName(a_name) : nullptr;
		auto* node = at ? at->AsNode() : nullptr;
		std::string names;
		if (node) {
			for (auto& child : node->GetChildren()) {
				if (child) {
					names += fmt::format("'{}' ", child->name.c_str());
				}
			}
		}
		SKSE::log::info("Arcane Arsenal: {} {} children: {}", a_name, node ? "has" : "not found -", names);
	}

	RE::BSGeometry* NockedArrow(RE::PlayerCharacter* a_player)
	{
		auto* root = a_player->Get3D();
		if (!root) {
			return nullptr;
		}
		std::string stem;
		if (auto* ammo = a_player->GetCurrentAmmo()) {
			std::string m = Lower(ammo->GetModel() ? ammo->GetModel() : "");
			if (auto s = m.find_last_of("\\/"); s != std::string::npos) {
				m = m.substr(s + 1);
			}
			if (auto d = m.rfind('.'); d != std::string::npos) {
				m = m.substr(0, d);
			}
			stem = m;
		}
		auto* weapon = root->GetObjectByName("WEAPON");
		if (auto* hit = FindArrowIn(weapon, stem, 0); hit && hit != weapon) {
			if (auto* mesh = ArrowMesh(hit)) {
				return mesh;
			}
		}
		if (g_arrowMisses++ < 5) {
			SKSE::log::info("Arcane Arsenal: no nocked arrow mesh (ammo model '{}')", stem);
			LogChildren(root, "WEAPON");
		}
		return nullptr;
	}

	// Our node at the arrowhead, under the mesh's parent. a_forward picks which end of the mesh is the head.
	RE::NiNode* MakeTip(RE::BSGeometry* a_mesh, const RE::NiPoint3& a_forward)
	{
		auto* parent = a_mesh->parent;
		if (!parent) {
			return nullptr;
		}
		const auto& b = a_mesh->worldBound;
		auto        axis = a_mesh->world.rotate * RE::NiPoint3{ 0.0f, 1.0f, 0.0f };
		if (axis.Dot(a_forward) < 0.0f) {
			axis = -axis;
		}
		const auto head = b.center + axis * (b.radius * 0.85f);   // on the arrowhead, not past its point
		auto*      tip = RE::NiNode::Create(0);
		tip->name = "ZP_ArcaneArrowHead";
		tip->local.translate = parent->world.Invert() * head;
		tip->local.rotate = a_mesh->local.rotate;
		tip->local.scale = g_cfg.arsenalScale;
		parent->AttachChild(tip, true);
		RE::NiUpdateData ud{};
		tip->Update(ud);
		return tip;
	}

	// Ends every model effect carrying a_art on reference a_on (none kept: see the top).
	void FinishArt(RE::BGSArtObject* a_art, RE::FormID a_on)
	{
		if (!a_art || !a_on) {
			return;
		}
		RE::ProcessLists::GetSingleton()->ForEachModelEffect([&](RE::ModelReferenceEffect* a_effect) {
			if (a_effect && a_effect->artObject == a_art) {
				auto target = a_effect->target.get();
				if (target && target->GetFormID() == a_on) {
					a_effect->finished = true;
				}
			}
			return RE::BSContainer::ForEachResult::kContinue;
		});
	}

	void StopArt(ArrowArt& a_art)
	{
		if (a_art.applied) {
			FinishArt(a_art.art, a_art.on);
		}
		if (a_art.tip) {
			g_staleTips.push_back(a_art.tip);
		}
		a_art.tip.reset();
		a_art.art = nullptr;
		a_art.on = 0;
		a_art.applied = false;
	}

	bool StartArt(ArrowArt& a_art, RE::TESObjectREFR* a_on, RE::BSGeometry* a_mesh, const RE::NiPoint3& a_forward,
		RE::BGSArtObject* a_artObject)
	{
		auto* tip = MakeTip(a_mesh, a_forward);
		if (!tip) {
			return false;
		}
		a_art.tip.reset(tip);
		a_art.art = a_artObject;
		a_art.on = a_on->GetFormID();
		// the engine returns a bool here (1.6.1): never treat it as a pointer
		a_art.applied = a_on->ApplyArtObject(a_artObject, -1.0f, nullptr, false, false, tip, false) != nullptr;
		return true;
	}

	// Before a save and after a load: no art of ours may be saved, or come back from a save without its node.
	void StopAllArrowArts()
	{
		StopArt(g_nocked);
		g_nockedArrow.reset();
		for (auto& [id, a] : g_flying) {
			StopArt(a);
		}
		g_flying.clear();
		const auto& arts = g_cfg.arsenalArts;
		if (arts.empty()) {
			return;
		}
		RE::ProcessLists::GetSingleton()->ForEachModelEffect([&](RE::ModelReferenceEffect* a_effect) {
			if (a_effect && std::find(arts.begin(), arts.end(), a_effect->artObject) != arts.end()) {
				a_effect->finished = true;
			}
			return RE::BSContainer::ForEachResult::kContinue;
		});
	}

	void ArsenalTick()
	{
		auto& c = g_cfg;
		auto* player = Player();
		for (auto& tip : g_staleTips) {
			if (tip && tip->parent) {
				tip->parent->DetachChild2(tip.get());
			}
		}
		g_staleTips.clear();
		if (!c.arsenalGlobal || c.arsenalArts.empty() || !player || !player->Is3DLoaded()) {
			return;
		}
		RE::BGSArtObject* want = nullptr;
		const auto element = static_cast<int>(c.arsenalGlobal->value);
		if (element >= 1 && element <= static_cast<int>(c.arsenalArts.size()) && Has(c.arsenalPerk)) {
			want = c.arsenalArts[element - 1];
		}

		// the nocked arrow
		using AS = RE::ATTACK_STATE_ENUM;
		const auto state = player->AsActorState()->GetAttackState();
		auto*      weap = player->GetEquippedObject(false);
		auto*      bow = weap ? weap->As<RE::TESObjectWEAP>() : nullptr;
		RE::BSGeometry* mesh = nullptr;
		if (want && bow && bow->IsBow() && (state == AS::kBowAttached || state == AS::kBowDrawn)) {
			mesh = NockedArrow(player);
		}
		if (g_nocked.tip && (!mesh || g_nockedArrow.get() != mesh || g_nocked.art != want)) {
			StopArt(g_nocked);
			g_nockedArrow.reset();
		}
		if (mesh && !g_nocked.tip) {
			const float h = player->GetAngleZ();
			if (StartArt(g_nocked, player, mesh, { std::sin(h), std::cos(h), 0.0f }, want)) {
				g_nockedArrow.reset(mesh);
				SKSE::log::info("Arcane Arsenal: {:08X} on nocked '{}' ({})", want->GetFormID(), mesh->name.c_str(),
					g_nocked.applied ? "applied" : "NOT applied");
			}
		}

		// arrows in flight
		std::vector<RE::FormID> seen;
		auto*                   mgr = RE::Projectile::Manager::GetSingleton();
		for (auto* list : { &mgr->unlimited, &mgr->limited, &mgr->pending }) {
			for (auto& handle : *list) {
				auto ptr = handle.get();
				auto* proj = ptr.get();
				if (!proj) {
					continue;
				}
				auto& rd = proj->GetProjectileRuntimeData();
				if (!rd.ammoSource || !rd.weaponSource || !rd.weaponSource->IsBow() || rd.shooter.get().get() != player) {
					continue;
				}
				const auto id = proj->GetFormID();
				seen.push_back(id);
				auto it = g_flying.find(id);
				if (it != g_flying.end()) {
					if (!it->second.done && !rd.impacts.empty()) {
						StopArt(it->second);
						it->second.done = true;
					}
					continue;
				}
				if (!want || !rd.impacts.empty() || rd.livingTime > 0.5f) {
					g_flying[id].done = true;   // shot without an element, or already old: leave it be
					continue;
				}
				auto* root = proj->Get3D();
				auto* flightMesh = root ? ArrowMesh(root) : nullptr;
				if (!flightMesh) {
					continue;   // its model may still be loading: next tick
				}
				auto fwd = rd.linearVelocity.SqrLength() > 1.0f ? rd.linearVelocity : rd.velocity;
				ArrowArt a;
				if (StartArt(a, proj, flightMesh, fwd, want)) {
					SKSE::log::info("Arcane Arsenal: {:08X} on arrow {:08X} '{}' ({})", want->GetFormID(), id,
						flightMesh->name.c_str(), a.applied ? "applied" : "NOT applied");
					g_flying[id] = std::move(a);
				}
			}
		}
		for (auto it = g_flying.begin(); it != g_flying.end();) {
			if (std::find(seen.begin(), seen.end(), it->first) == seen.end()) {
				StopArt(it->second);
				it = g_flying.erase(it);
			} else {
				++it;
			}
		}
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
			PistolTalents(a_event);
			Ricochet(a_event);
			if (!g_cfg.ready || !Has(g_cfg.root)) {
				return RE::BSEventNotifyControl::kContinue;
			}
			auto* player = Player();
			auto* cause = a_event->cause.get();
			auto* target = a_event->target.get();
			if (cause == player && target != player) {
				auto* victim = target->As<RE::Actor>();
				const bool melee = IsMeleeWeapon(a_event->source);
				const bool flagged = a_event->flags.any(Flag::kPowerAttack);
				const auto sinceStart = Seconds(Clock::now() - g_lastStartAt);
				const bool byStart = !flagged && g_lastStartPower && sinceStart <= kPaWindow;
				{   // 1.6.3 diagnostics: what the hit looked like (first person vs third, the engine's attack data)
					auto* proc = player->GetActorRuntimeData().currentProcess;
					auto* ad = (proc && proc->high) ? proc->high->attackData.get() : nullptr;
					auto* cam = RE::PlayerCamera::GetSingleton();
					SKSE::log::info("player hit on {:08X} by {:08X}: flags {:#x}{}{}, {}, attack data '{}'{}, {:.2f} s after a {} start{}",
						target->GetFormID(), a_event->source, a_event->flags.underlying(), flagged ? " power" : "",
						melee ? "" : " (not a melee weapon)", (cam && cam->IsInFirstPerson()) ? "1st person" : "3rd person",
						ad ? ad->event.c_str() : "none",
						(ad && ad->data.flags.any(RE::AttackData::AttackFlag::kPowerAttack)) ? " (power)" : "",
						sinceStart, g_lastStartPower ? "power" : "light", byStart ? " -> power attack by its start" : "");
				}
				if (!victim || !melee || !Counts(cause, target)) {
					return RE::BSEventNotifyControl::kContinue;
				}
				g_lastHit = Clock::now();
				// actions first, on the Rage the swing started with; then the hit's own stack
				if (flagged || byStart) {
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
			if (g_bladeOn && Clock::now() >= g_bladeUntil) {
				BladeOff("timed out");
			}
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
		std::thread([] {   // Arcane Arsenal's arrows follow the draw and the launch closely
			while (g_running) {
				std::this_thread::sleep_for(20ms);
				SKSE::GetTaskInterface()->AddTask([] { ArsenalTick(); });
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
		case SKSE::MessagingInterface::kSaveGame:
			StopAllArrowArts();   // sent on the main thread before the save is written
			break;
		case SKSE::MessagingInterface::kPostLoadGame:
		case SKSE::MessagingInterface::kNewGame:
			MeterOpen();
			SKSE::GetTaskInterface()->AddTask([] {
				g_rage = 0;
				g_vehemenceOn = false;
				g_effigies.clear();
				g_effigyLoadout.clear();
				g_bladeOn = false;
				StopAllArrowArts();
				if (g_cfg.bladeAbility && Player()->HasSpell(g_cfg.bladeAbility)) {
					Player()->RemoveSpell(g_cfg.bladeAbility);   // an ability is saved with the game
				}
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
	SKSE::log::info("ZenProphecyRage 1.6.3 loading, runtime {}", REL::Module::get().version().string());
	// the player's graph events (power attack direction): PlayerCharacter's IAnimationGraphManagerHolder vtable, slot 1
	REL::Relocation<std::uintptr_t> graphVtbl{ RE::VTABLE_PlayerCharacter[3] };
	NotifyPlayerGraph::func = graphVtbl.write_vfunc(0x1, NotifyPlayerGraph::thunk);
	SKSE::GetMessagingInterface()->RegisterListener(OnMessage);
	return true;
}
