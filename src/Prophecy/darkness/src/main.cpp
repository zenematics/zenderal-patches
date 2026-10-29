#include "pch.h"

#include <atomic>
#include <chrono>
#include <map>
#include <thread>

#include <nlohmann/json.hpp>

// Prophecy's Shadow tree, Darkness (curator 2026-10-28). With Gather Shadows (the tree's root), Darkness fills while
// the player stands in darkness: the engine's light level on the player (GetLightLevel, the value behind the sneak
// eye), one point every N seconds by how dark it is - Gather Shadows' own thresholds 60/40/20. Shade Veil fills it
// faster while its effect is on (sneaking). In light (above the last threshold) it drains one point every DrainEvery
// seconds. The count is written to the ZP_Darkness global (saved with the game, so a load keeps it) and into the
// magnitude of the Darkness ability's effect ("You have <mag> Darkness." in Active Effects).
//
// The Shadow talents' spells cost Darkness instead of Mana: their Mana cost is 0 for the player (SpellItem::AdjustCost),
// a cast without enough Darkness is refused (ActorMagicCaster::CheckCast) with a notification, and a cast spends its
// cost (TESSpellCastEvent). Nightfall costs the full meter. Nightblade's dash hits spend half the Darkness for extra
// damage (1.1.0; its Mana drain is off by a condition in the plugin). Without Gather Shadows the spells cost Mana as before.
// Log: My Games/Skyrim Special Edition/SKSE/ZenProphecyDarkness.log

SKSEPluginInfo(
	.Version = REL::Version{ 1, 1, 2, 0 },
	.Name = "ZenProphecyDarkness"sv,
	.Author = "Zenderal"sv,
	.StructCompatibility = SKSE::StructCompatibility::Independent,
	.RuntimeCompatibility = SKSE::VersionIndependence::AddressLibrary)

namespace
{
	using Clock = std::chrono::steady_clock;
	constexpr auto kConfigPath = "Data/SKSE/Plugins/ZenProphecyDarkness.json"sv;

	struct Config
	{
		RE::TESGlobal*     darknessGlobal{ nullptr };
		RE::EffectSetting* darknessEffect{ nullptr };
		RE::EffectSetting* veilEffect{ nullptr };
		RE::BGSPerk*       root{ nullptr };
		int                max{ 10 };
		std::vector<std::pair<double, double>> fill;   // (light level at most, seconds per point), darkest first
		double             veilMult{ 2.0 };
		double             drainEvery{ 4.0 };
		std::map<RE::FormID, int> costs;              // spell -> Darkness (the full meter: max)
		std::map<RE::FormID, std::string> names;
		std::string        refusal{ "Not enough Darkness." };
		// Nightblade (1.1.0): each hit of Triumvirate's proc spends Fraction of the Darkness for PerPoint damage a point
		RE::FormID         nightbladeProc{ 0 };
		RE::SpellItem*     nightbladeDamage{ nullptr };
		double             nightbladeFraction{ 0.5 };
		double             nightbladePerPoint{ 15.0 };
		// the meter: Oxygen Meter 2's movie, our own copy of its menu (setLocation's arguments, two colours)
		double             meterX{ 50.0 }, meterY{ 21.0 }, meterRot{ 0.0 }, meterXScale{ 50.0 }, meterYScale{ 50.0 };
		double             meterBar{ 0x2A1A5E }, meterFlash{ 0x6B48C8 };
		bool               meterFollowsCastingBar{ true };
		double             meterXOffset{ 0.0 }, meterYOffset{ 0.0 };
		double             meterWidth{ 0.0 };
		bool               ready{ false };
	} g_cfg;

	// state - touched only on the game's main thread (the tick task, cast events and the cast hooks all run there)
	int               g_dark = 0;
	double            g_fillTimer = 0.0;   // seconds of darkness (weighted by the fill rate) towards the next point
	double            g_drainTimer = 0.0;
	Clock::time_point g_lastTick{};
	Clock::time_point g_lastRefusal{};
	Clock::time_point g_lastLightLog{};   // 1.0.1: the light level every LightLogEvery s, to tune the fill steps
	constexpr double  kLightLogEvery = 5.0;
	Clock::time_point g_quietUntil{};   // after a full-meter spell (Nightfall): its script casts the Shadow buffs, free
	constexpr double  kQuietAfterFull = 3.0;
	std::atomic<bool> g_running{ false };
	RE::SCRIPT_FUNCTION::Condition_t* g_lightLevel{ nullptr };

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
			SKSE::log::error("{} missing - Darkness is off", kConfigPath);
			return;
		}
		nlohmann::json j;
		try {
			j = nlohmann::json::parse(in);
		} catch (const std::exception& e) {
			SKSE::log::error("{}: {} - Darkness is off", kConfigPath, e.what());
			return;
		}
		const auto plugin = j["plugin"].get<std::string>();
		auto& c = g_cfg;
		c.darknessGlobal = Lookup<RE::TESGlobal>(plugin, j["darknessGlobal"], "ZP_Darkness global");
		c.darknessEffect = Lookup<RE::EffectSetting>(plugin, j["darknessEffect"], "Darkness effect");
		c.veilEffect = Lookup<RE::EffectSetting>(plugin, j["veilEffect"], "Shade Veil effect");
		c.root = Lookup<RE::BGSPerk>(plugin, j["perks"]["root"], "Gather Shadows perk");
		c.max = j["max"].get<int>();
		for (auto& f : j["fill"]) {
			c.fill.emplace_back(f["lightAtMost"].get<double>(), f["secondsPerPoint"].get<double>());
		}
		std::ranges::sort(c.fill);
		c.veilMult = j["veilMult"].get<double>();
		c.drainEvery = j["drainEvery"].get<double>();
		c.refusal = j.value("refusal", c.refusal);
		for (auto& s : j["spells"]) {
			const auto name = s["name"].get<std::string>();
			if (auto* spell = Lookup<RE::SpellItem>(s["plugin"].get<std::string>(), s["id"], name)) {
				const int cost = s["cost"].is_string() ? c.max : s["cost"].get<int>();   // "full": the whole meter
				c.costs[spell->GetFormID()] = cost;
				c.names[spell->GetFormID()] = name;
				SKSE::log::info("spell {}: {:08X}, {} Darkness", name, spell->GetFormID(), cost);
			}
		}
		if (j.contains("nightblade")) {
			auto& nb = j["nightblade"];
			if (auto* proc = Lookup<RE::SpellItem>(nb["procPlugin"].get<std::string>(), nb["procId"], "Nightblade proc")) {
				c.nightbladeProc = proc->GetFormID();
			}
			c.nightbladeDamage = Lookup<RE::SpellItem>(plugin, nb["damageSpell"], "Nightblade Darkness damage");
			c.nightbladeFraction = nb["fraction"].get<double>();
			c.nightbladePerPoint = nb["perPoint"].get<double>();
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
			c.meterYOffset = m.value("yOffset", 0.0);
			c.meterWidth = m.value("width", 0.0);
		}
		if (c.meterFollowsCastingBar) {
			FollowCastingBar();
		}
		c.meterX += c.meterXOffset;
		c.meterY += c.meterYOffset;
		if (c.meterWidth > 0.0) {
			c.meterXScale = c.meterWidth;
		}
		if (auto* cmd = RE::SCRIPT_FUNCTION::LocateScriptCommand("GetLightLevel"); cmd && cmd->conditionFunction) {
			g_lightLevel = cmd->conditionFunction;
		} else {
			SKSE::log::error("GetLightLevel's condition function not found - Darkness cannot fill");
		}
		c.ready = c.darknessGlobal && c.root && !c.fill.empty();
		SKSE::log::info("config loaded: max {}, {} fill steps, drain every {} s, {} spells{}", c.max, c.fill.size(),
			c.drainEvery, c.costs.size(), c.ready ? "" : " - NOT READY (global, root perk or fill steps missing)");
	}

	RE::PlayerCharacter* Player() { return RE::PlayerCharacter::GetSingleton(); }

	bool Has(RE::BGSPerk* a_perk) { return a_perk && Player() && Player()->HasPerk(a_perk); }

	bool Active() { return g_cfg.ready && Has(g_cfg.root); }

	int CostOf(const RE::MagicItem* a_spell)
	{
		if (!a_spell) {
			return -1;
		}
		auto it = g_cfg.costs.find(a_spell->GetFormID());
		return it == g_cfg.costs.end() ? -1 : it->second;
	}

	// ---------------------------------------------------------------- the meter (the Rage DLL's, in its own menu)
	constexpr auto kMeterMenu = "ZenProphecyDarknessMeter"sv;
	constexpr auto kMeterMovie = "oxygenMeter2"sv;
	bool g_meterRegistered = false;
	bool g_meterShown = false;
	Clock::time_point g_meterZeroSince{};
	constexpr double  kMeterHideDelay = 1.0;
	bool g_meterLaidOut = false;

	// Casting Bar 4.0's live CastingBar.ini: the centre slot's position and the spell widget's scale (see the Rage DLL)
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

	// 1.1.1: what the movie really holds, for "the meter doesn't show" (logged with the light level)
	std::string MeterState()
	{
		auto view = MeterView();
		if (!view) {
			return fmt::format("no view (registered {}, open {})", g_meterRegistered, RE::UI::GetSingleton()->IsMenuOpen(kMeterMenu));
		}
		auto num = [&](const char* a_path) {
			RE::GFxValue v;
			if (!view->GetVariable(&v, a_path)) {
				return std::string{ "?" };
			}
			if (v.IsNumber()) {
				return fmt::format("{:.1f}", v.GetNumber());
			}
			if (v.IsBool()) {
				return std::string{ v.GetBool() ? "true" : "false" };
			}
			return std::string{ v.IsUndefined() ? "undef" : "other" };
		};
		const auto r = view->GetVisibleFrameRect();
		return fmt::format("open {}, view visible {}, shown {}, main _x {} _y {} _visible {} _alpha {} _xscale {} _width {} _height {}, visible rect ({:.0f},{:.0f})-({:.0f},{:.0f})",
			RE::UI::GetSingleton()->IsMenuOpen(kMeterMenu), view->GetVisible(), g_meterShown, num("main._x"), num("main._y"),
			num("main._visible"), num("main._alpha"), num("main._xscale"), num("main._width"), num("main._height"),
			r.left, r.top, r.right, r.bottom);
	}

	class DarknessMeter : public RE::IMenu
	{
	public:
		DarknessMeter()
		{
			depthPriority = 0;
			menuFlags.set(RE::UI_MENU_FLAGS::kAlwaysOpen, RE::UI_MENU_FLAGS::kRequiresUpdate, RE::UI_MENU_FLAGS::kAllowSaving);
			inputContext = Context::kNone;
			if (!RE::BSScaleformManager::GetSingleton()->LoadMovieEx(this, kMeterMovie, [](RE::GFxMovieDef*) {})) {
				SKSE::log::error("could not load Interface/{}.swf (Oxygen Meter 2): no Darkness meter", kMeterMovie);
			}
		}

		static RE::IMenu* Create() { return new DarknessMeter(); }
	};

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

	// 1.1.2: something closes the always-open menu (seen 2026-10-29 at a save + message box in Dal'valstaag's vault);
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

	// never doFadeOut (see the Rage DLL: each one appended a fade that later hid a shown meter)
	void MeterUpdate(int a_dark, int a_max)
	{
		if (!MeterSetUp()) {
			return;
		}
		const double pct = a_max > 0 ? 100.0 * a_dark / a_max : 0.0;
		MeterCall("main.updateMeterPercent", { pct });
		if (a_dark > 0 && !g_meterShown) {
			MeterCall("main.doShow");
			g_meterShown = true;
		} else if (a_dark == 0) {
			g_meterZeroSince = Clock::now();
		}
	}

	// the global (saved with the game), the Darkness ability's magnitude (the Active Effects menu) and the meter
	void Publish()
	{
		MeterUpdate(g_dark, g_cfg.max);
		if (g_cfg.darknessGlobal) {
			g_cfg.darknessGlobal->value = static_cast<float>(g_dark);
		}
		if (!g_cfg.darknessEffect || !Player()) {
			return;
		}
		if (auto* list = Player()->AsMagicTarget()->GetActiveEffectList()) {
			for (auto* ae : *list) {
				if (ae && ae->GetBaseObject() == g_cfg.darknessEffect) {
					ae->magnitude = static_cast<float>(g_dark);
				}
			}
		}
	}

	void SetDarkness(int a_value, std::string_view a_why)
	{
		const int v = std::clamp(a_value, 0, g_cfg.max);
		if (v == g_dark) {
			return;
		}
		SKSE::log::info("Darkness {} -> {} ({})", g_dark, v, a_why);
		const bool filled = v == g_cfg.max && g_dark < g_cfg.max;
		g_dark = v;
		Publish();
		if (filled) {
			MeterCall("main.doFlash");
		}
	}

	// ---------------------------------------------------------------- casting
	// the spells' Mana cost: 0 for the player while Darkness pays (SpellItem vtable, AdjustCost 0x63 - where the engine
	// applies the caster's own cost changes)
	struct AdjustCost
	{
		static void thunk(RE::SpellItem* a_this, float& a_cost, RE::Actor* a_actor)
		{
			func(a_this, a_cost, a_actor);
			if (a_actor && a_actor->IsPlayerRef() && CostOf(a_this) >= 0 && Active()) {
				a_cost = 0.0f;
			}
		}
		static inline REL::Relocation<decltype(thunk)> func;
	};

	// a cast without enough Darkness is refused (ActorMagicCaster vtable, CheckCast 0x0A)
	struct CheckCast
	{
		static bool thunk(RE::ActorMagicCaster* a_this, RE::MagicItem* a_spell, bool a_dualCast, float* a_effectStrength,
			RE::MagicSystem::CannotCastReason* a_reason, bool a_useBaseValueForCost)
		{
			const int cost = CostOf(a_spell);
			auto* caster = a_this ? a_this->GetCasterAsActor() : nullptr;
			// hands and voice only: a script's Cast (Nightfall's buffs) goes through the instant caster and is free
			const bool scripted = a_this && a_this->GetCastingSource() == RE::MagicSystem::CastingSource::kInstant;
			if (cost > 0 && !scripted && caster && caster->IsPlayerRef() && Active() && g_dark < cost) {
				if (a_reason) {
					*a_reason = RE::MagicSystem::CannotCastReason::kCustomReasonNoStart;
				}
				const auto now = Clock::now();
				if (Seconds(now - g_lastRefusal) > 1.5) {
					g_lastRefusal = now;
					RE::SendHUDMessage::ShowHUDMessage(g_cfg.refusal.c_str());
					SKSE::log::info("{} refused: {} Darkness, needs {}", g_cfg.names[a_spell->GetFormID()], g_dark, cost);
				}
				return false;
			}
			return func(a_this, a_spell, a_dualCast, a_effectStrength, a_reason, a_useBaseValueForCost);
		}
		static inline REL::Relocation<decltype(thunk)> func;
	};

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
			if (!a_event || !a_event->object || a_event->object.get() != Player() || !Active()) {
				return RE::BSEventNotifyControl::kContinue;
			}
			auto it = g_cfg.costs.find(a_event->spell);
			if (it == g_cfg.costs.end()) {
				return RE::BSEventNotifyControl::kContinue;
			}
			const auto now = Clock::now();
			if (now < g_quietUntil) {
				SKSE::log::info("{} cast by Nightfall: free", g_cfg.names[a_event->spell]);
				return RE::BSEventNotifyControl::kContinue;
			}
			if (it->second >= g_cfg.max) {
				g_quietUntil = now + std::chrono::duration_cast<Clock::duration>(std::chrono::duration<double>(kQuietAfterFull));
			}
			SetDarkness(g_dark - it->second, g_cfg.names[a_event->spell]);
			return RE::BSEventNotifyControl::kContinue;
		}
	};

	// ---------------------------------------------------------------- Nightblade
	// The proc's own hit events (one per effect that lands) - one spend per target per DedupeWindow
	std::map<RE::FormID, Clock::time_point> g_nightbladeHits;
	constexpr double kNightbladeDedupe = 0.5;

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
			auto& c = g_cfg;
			if (!a_event || !c.nightbladeProc || a_event->source != c.nightbladeProc || !c.nightbladeDamage ||
				!a_event->cause || a_event->cause.get() != Player() || !a_event->target || !Active()) {
				return RE::BSEventNotifyControl::kContinue;
			}
			auto* target = a_event->target->As<RE::Actor>();
			if (!target || target->IsDead()) {
				return RE::BSEventNotifyControl::kContinue;
			}
			const auto now = Clock::now();
			auto& last = g_nightbladeHits[target->GetFormID()];
			if (Seconds(now - last) < kNightbladeDedupe) {
				return RE::BSEventNotifyControl::kContinue;
			}
			last = now;
			const int spend = static_cast<int>(std::ceil(g_dark * c.nightbladeFraction));
			if (spend <= 0) {
				return RE::BSEventNotifyControl::kContinue;
			}
			const float damage = static_cast<float>(spend * c.nightbladePerPoint);
			SetDarkness(g_dark - spend, "Nightblade");
			Player()->GetMagicCaster(RE::MagicSystem::CastingSource::kInstant)
				->CastSpellImmediate(c.nightbladeDamage, false, target, 1.0f, false, damage, Player());
			SKSE::log::info("Nightblade: {} Darkness -> {:.0f} damage on {:08X}", spend, damage, target->GetFormID());
			return RE::BSEventNotifyControl::kContinue;
		}
	};

	// ---------------------------------------------------------------- filling
	double LightLevel()
	{
		double level = 1000.0;
		if (g_lightLevel) {
			g_lightLevel(Player(), nullptr, nullptr, level);
		}
		return level;
	}

	// every 250 ms on the main thread
	void Tick()
	{
		auto* player = Player();
		const bool paused = RE::UI::GetSingleton()->GameIsPaused();
		MeterKeepOpen();
		if (auto view = MeterView()) {
			MeterSetUp();
			if (g_dark > 0 && !g_meterShown) {
				MeterUpdate(g_dark, g_cfg.max);   // after a reopen's layout hid it
			}
			if (g_meterShown && g_dark == 0 && Seconds(Clock::now() - g_meterZeroSince) >= kMeterHideDelay) {
				MeterCall("main.doHide");
				g_meterShown = false;
			}
			view->SetVisible(!paused);
		}
		const auto now = Clock::now();
		const double dt = std::min(Seconds(now - g_lastTick), 1.0);
		g_lastTick = now;
		if (!g_cfg.ready || !player || !player->Is3DLoaded() || paused || !Has(g_cfg.root)) {
			return;
		}
		const double light = LightLevel();
		if (Seconds(now - g_lastLightLog) >= kLightLogEvery) {
			g_lastLightLog = now;
			SKSE::log::info("light {:.0f}, Darkness {}; meter: {}", light, g_dark, MeterState());
		}
		const auto step = std::ranges::find_if(g_cfg.fill, [&](auto& f) { return light <= f.first; });
		if (step != g_cfg.fill.end()) {
			g_drainTimer = 0.0;
			const bool veil = g_cfg.veilEffect && player->AsMagicTarget()->HasMagicEffect(g_cfg.veilEffect);
			g_fillTimer += dt * (veil ? g_cfg.veilMult : 1.0);
			if (g_fillTimer >= step->second) {
				g_fillTimer = 0.0;
				if (g_dark < g_cfg.max) {
					SetDarkness(g_dark + 1, fmt::format("light {:.0f}{}", light, veil ? ", Shade Veil" : ""));
				}
			}
		} else {
			g_fillTimer = 0.0;
			g_drainTimer += dt;
			if (g_drainTimer >= g_cfg.drainEvery) {
				g_drainTimer = 0.0;
				if (g_dark > 0) {
					SetDarkness(g_dark - 1, fmt::format("light {:.0f}", light));
				}
			}
		}
	}

	void StartTicker()
	{
		if (g_running.exchange(true)) {
			return;
		}
		g_lastTick = Clock::now();
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
			RE::ScriptEventSourceHolder::GetSingleton()->AddEventSink<RE::TESSpellCastEvent>(CastSink::Get());
			RE::ScriptEventSourceHolder::GetSingleton()->AddEventSink<RE::TESHitEvent>(HitSink::Get());
			if (std::filesystem::exists("Data/Interface/oxygenMeter2.swf")) {
				RE::UI::GetSingleton()->Register(kMeterMenu, DarknessMeter::Create);
				g_meterRegistered = true;
			} else {
				SKSE::log::warn("Interface/oxygenMeter2.swf not found (Oxygen Meter 2 not installed): no Darkness meter");
			}
			StartTicker();
			break;
		case SKSE::MessagingInterface::kPostLoadGame:
		case SKSE::MessagingInterface::kNewGame:
			MeterOpen();
			// the global is saved with the game: a load keeps the Darkness it had
			SKSE::GetTaskInterface()->AddTask([new_game = a_msg->type == SKSE::MessagingInterface::kNewGame] {
				g_dark = (!new_game && g_cfg.darknessGlobal) ? std::clamp(static_cast<int>(g_cfg.darknessGlobal->value), 0, g_cfg.max) : 0;
				g_fillTimer = g_drainTimer = 0.0;
				SKSE::log::info("Darkness {} after {}", g_dark, new_game ? "a new game" : "a load");
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
	SKSE::log::info("ZenProphecyDarkness 1.1.2 loading, runtime {}", REL::Module::get().version().string());
	REL::Relocation<std::uintptr_t> spellVtbl{ RE::VTABLE_SpellItem[0] };
	AdjustCost::func = spellVtbl.write_vfunc(0x63, AdjustCost::thunk);
	REL::Relocation<std::uintptr_t> casterVtbl{ RE::VTABLE_ActorMagicCaster[0] };
	CheckCast::func = casterVtbl.write_vfunc(0x0A, CheckCast::thunk);
	SKSE::GetMessagingInterface()->RegisterListener(OnMessage);
	return true;
}
