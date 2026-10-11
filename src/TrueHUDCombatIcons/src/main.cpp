// Zenderal TrueHUD Combat Icons (SSE 1.5.97 / Enderal SE 2.0.12, CommonLibSSE-NG).
//
// Draws For Honor Reforged's status icons INSIDE TrueHUD's floating info bars instead of as
// Status Indicator Framework icons above the actor's head:
//   - the incoming-attack direction arrow on the matching side of the bar (left / right),
//   - one priority icon (unstable, then the knockdown cooldowns) on the right: by default inline,
//     after the right arrow (or next to the bar when no right attack is incoming); with
//     "statusStyle": "circle" inside a drawn circle on the bar's right end instead.
//
// How it attaches: TrueHUD (1.1.9) creates each actor's info bar with
//   _root.TrueHUD.TrueHUD_MainVisibilityWidgets.attachMovie("TrueHUD_InfoBar", <actor handle>, ...)
// so the bar is reachable by the actor's native ObjectRefHandle value. We add our clips as CHILDREN
// of that bar, so they inherit its screen position, distance scaling and fade for free; we only lay
// them out in the bar's local space (from the health-bar frame's bounds) and toggle which icon shows.
// Nothing here calls into TrueHUD.dll - only its Flash movie - so a TrueHUD update that renames those
// clips makes this plugin draw nothing, it cannot crash it.

SKSEPluginInfo(
	.Version = REL::Version{ 1, 0, 0, 0 },
	.Name = "ZenTrueHUDCombatIcons"sv,
	.Author = "Zenderal"sv,
	.StructCompatibility = SKSE::StructCompatibility::Independent,
	.RuntimeCompatibility = SKSE::VersionIndependence::AddressLibrary)

namespace
{
	constexpr auto kConfigPath = "Data/SKSE/Plugins/ZenTrueHUDCombatIcons.json"sv;
	constexpr auto kBarContainer = "_root.TrueHUD.TrueHUD_MainVisibilityWidgets";
	constexpr auto kRootName = "ZenCombatIcons";

	// ---------------------------------------------------------------- config

	struct Term
	{
		RE::EffectSetting* effect{ nullptr };
		RE::BGSKeyword*    keyword{ nullptr };
	};

	struct Rule
	{
		std::string       source;
		std::string       symbol;
		std::vector<Term> all;
		std::vector<Term> any;
		std::vector<Term> none;
	};

	struct Layout
	{
		double       gap{ 4.0 };
		double       arrowSize{ 22.0 };
		bool         statusInCircle{ false };  // "statusStyle": "inline" (default) | "circle"
		double       statusIconSize{ 22.0 };   // inline mode
		bool         reserveRightArrowSlot{ false };  // inline: keep the arrow's gap even when no arrow shows
		double       circleRadius{ 12.0 };
		double       circleIconSize{ 18.0 };
		bool         circleAlwaysVisible{ true };
		std::uint32_t circleFillColor{ 0x000000 };
		double       circleFillAlpha{ 55.0 };
		std::uint32_t circleLineColor{ 0xC8B88A };
		double       circleLineAlpha{ 90.0 };
		double       circleLineThickness{ 1.5 };
		double       offsetY{ 0.0 };
	};

	enum Slot : std::size_t
	{
		kLeft,
		kRight,
		kCircle,
		kSlotCount
	};
	constexpr const char* kSlotNames[kSlotCount] = { "left", "right", "circle" };

	struct Config
	{
		bool              requireHostile{ true };
		bool              requireInCombat{ true };
		Layout            layout;
		std::vector<Rule> slots[kSlotCount];
		std::uint32_t     generation{ 0 };  // bumped on reload so existing clips rebuild
	};

	Config g_config;
	bool   g_dataLoaded{ false };

	RE::TESForm* LookupForm(const std::string& a_spec)
	{
		const auto bar = a_spec.find('|');
		if (bar == std::string::npos) {
			return nullptr;
		}
		const auto plugin = a_spec.substr(0, bar);
		const auto id = static_cast<RE::FormID>(std::stoul(a_spec.substr(bar + 1), nullptr, 16));
		auto* dh = RE::TESDataHandler::GetSingleton();
		return dh ? dh->LookupForm(id, plugin) : nullptr;
	}

	bool ParseTerms(const nlohmann::json& a_rule, const char* a_key, std::vector<Term>& a_out, const std::string& a_source)
	{
		if (!a_rule.contains(a_key)) {
			return true;
		}
		for (const auto& t : a_rule[a_key]) {
			Term term;
			if (t.contains("effect")) {
				const auto spec = t["effect"].get<std::string>();
				auto* form = LookupForm(spec);
				term.effect = form ? form->As<RE::EffectSetting>() : nullptr;
				if (!term.effect) {
					SKSE::log::warn("{}: magic effect {} not found - rule disabled", a_source, spec);
					return false;
				}
			} else if (t.contains("keyword")) {
				const auto spec = t["keyword"].get<std::string>();
				auto* form = LookupForm(spec);
				term.keyword = form ? form->As<RE::BGSKeyword>() : nullptr;
				if (!term.keyword) {
					SKSE::log::warn("{}: keyword {} not found - rule disabled", a_source, spec);
					return false;
				}
			} else {
				SKSE::log::warn("{}: term without 'effect' or 'keyword' - rule disabled", a_source);
				return false;
			}
			a_out.push_back(term);
		}
		return true;
	}

	std::uint32_t ParseColor(const nlohmann::json& a_j, const char* a_key, std::uint32_t a_default)
	{
		if (!a_j.contains(a_key)) {
			return a_default;
		}
		const auto& v = a_j[a_key];
		return v.is_string() ? static_cast<std::uint32_t>(std::stoul(v.get<std::string>(), nullptr, 16)) : v.get<std::uint32_t>();
	}

	void LoadConfig()
	{
		Config cfg;
		cfg.generation = g_config.generation + 1;

		try {
			std::ifstream file{ std::filesystem::path{ kConfigPath } };
			if (!file.is_open()) {
				SKSE::log::error("Config {} not found - nothing will be drawn", kConfigPath);
				g_config = std::move(cfg);
				return;
			}
			const auto j = nlohmann::json::parse(file, nullptr, true, true);

			cfg.requireHostile = j.value("requireHostile", true);
			cfg.requireInCombat = j.value("requireInCombat", true);

			if (j.contains("layout")) {
				const auto& l = j["layout"];
				auto& o = cfg.layout;
				o.gap = l.value("gap", o.gap);
				o.arrowSize = l.value("arrowSize", o.arrowSize);
				o.statusInCircle = l.value("statusStyle", std::string{ "inline" }) == "circle";
				o.statusIconSize = l.value("statusIconSize", o.statusIconSize);
				o.reserveRightArrowSlot = l.value("reserveRightArrowSlot", o.reserveRightArrowSlot);
				o.circleRadius = l.value("circleRadius", o.circleRadius);
				o.circleIconSize = l.value("circleIconSize", o.circleIconSize);
				o.circleAlwaysVisible = l.value("circleAlwaysVisible", o.circleAlwaysVisible);
				o.circleFillColor = ParseColor(l, "circleFillColor", o.circleFillColor);
				o.circleFillAlpha = l.value("circleFillAlpha", o.circleFillAlpha);
				o.circleLineColor = ParseColor(l, "circleLineColor", o.circleLineColor);
				o.circleLineAlpha = l.value("circleLineAlpha", o.circleLineAlpha);
				o.circleLineThickness = l.value("circleLineThickness", o.circleLineThickness);
				o.offsetY = l.value("offsetY", o.offsetY);
			}

			for (std::size_t s = 0; s < kSlotCount; ++s) {
				if (!j.contains(kSlotNames[s])) {
					continue;
				}
				for (const auto& r : j[kSlotNames[s]]) {
					Rule rule;
					rule.source = r.value("source", "");
					rule.symbol = r.value("symbol", "");
					if (rule.source.empty() || rule.symbol.empty()) {
						SKSE::log::warn("{}: rule without 'source' or 'symbol' skipped", kSlotNames[s]);
						continue;
					}
					if (ParseTerms(r, "all", rule.all, rule.source) &&
						ParseTerms(r, "any", rule.any, rule.source) &&
						ParseTerms(r, "none", rule.none, rule.source)) {
						cfg.slots[s].push_back(std::move(rule));
					}
				}
				SKSE::log::info("Slot '{}': {} rules", kSlotNames[s], cfg.slots[s].size());
			}
		} catch (const std::exception& e) {
			SKSE::log::error("Failed to read {}: {}", kConfigPath, e.what());
		}

		g_config = std::move(cfg);
	}

	// ---------------------------------------------------------------- matching

	bool TermActive(RE::BSSimpleList<RE::ActiveEffect*>* a_effects, const Term& a_term)
	{
		for (auto* ae : *a_effects) {
			auto* base = ae ? ae->GetBaseObject() : nullptr;
			if (!base) {
				continue;
			}
			if (a_term.effect ? base == a_term.effect : base->HasKeyword(a_term.keyword)) {
				return true;
			}
		}
		return false;
	}

	// Index of the first matching rule in the slot, or -1.
	int MatchSlot(RE::BSSimpleList<RE::ActiveEffect*>* a_effects, const std::vector<Rule>& a_rules)
	{
		if (!a_effects) {
			return -1;
		}
		for (std::size_t i = 0; i < a_rules.size(); ++i) {
			const auto& r = a_rules[i];
			bool ok = std::ranges::all_of(r.all, [&](const Term& t) { return TermActive(a_effects, t); });
			ok = ok && (r.any.empty() || std::ranges::any_of(r.any, [&](const Term& t) { return TermActive(a_effects, t); }));
			ok = ok && std::ranges::none_of(r.none, [&](const Term& t) { return TermActive(a_effects, t); });
			if (ok) {
				return static_cast<int>(i);
			}
		}
		return -1;
	}

	// ---------------------------------------------------------------- Flash helpers

	struct Bounds
	{
		double xMin{ 0 }, xMax{ 0 }, yMin{ 0 }, yMax{ 0 };
		[[nodiscard]] bool Valid() const { return xMax > xMin && yMax > yMin; }
	};

	bool GetBounds(RE::GFxValue& a_clip, RE::GFxValue& a_space, Bounds& a_out)
	{
		RE::GFxValue res;
		if (!a_clip.IsDisplayObject() || !a_clip.Invoke("getBounds", &res, &a_space, 1) || !res.IsObject()) {
			return false;
		}
		RE::GFxValue v;
		res.GetMember("xMin", &v);
		a_out.xMin = v.GetNumber();
		res.GetMember("xMax", &v);
		a_out.xMax = v.GetNumber();
		res.GetMember("yMin", &v);
		a_out.yMin = v.GetNumber();
		res.GetMember("yMax", &v);
		a_out.yMax = v.GetNumber();
		return a_out.Valid() && std::abs(a_out.xMax) < 1e6;
	}

	double GetNumberMember(RE::GFxValue& a_obj, const char* a_name, double a_default)
	{
		RE::GFxValue v;
		return a_obj.GetMember(a_name, &v) && v.IsNumber() ? v.GetNumber() : a_default;
	}

	bool GetBoolMember(RE::GFxValue& a_obj, const char* a_name)
	{
		RE::GFxValue v;
		return a_obj.GetMember(a_name, &v) && v.IsBool() && v.GetBool();
	}

	bool NewClip(RE::GFxValue& a_parent, const char* a_name, RE::GFxValue& a_out)
	{
		RE::GFxValue depth;
		a_parent.Invoke("getNextHighestDepth", &depth);
		return a_parent.CreateEmptyMovieClip(&a_out, a_name, depth.IsNumber() ? static_cast<std::int32_t>(depth.GetNumber()) : -1);
	}

	void SetPos(RE::GFxValue& a_clip, double a_x, double a_y)
	{
		RE::GFxValue::DisplayInfo di;
		a_clip.GetDisplayInfo(&di);
		di.SetPosition(a_x, a_y);
		a_clip.SetDisplayInfo(di);
	}

	void SetVisible(RE::GFxValue& a_clip, bool a_visible)
	{
		RE::GFxValue::DisplayInfo di;
		a_clip.GetDisplayInfo(&di);
		di.SetVisible(a_visible);
		a_clip.SetDisplayInfo(di);
	}

	void DrawCircle(RE::GFxValue& a_clip, const Layout& a_l)
	{
		a_clip.Invoke("clear");
		{
			std::array<RE::GFxValue, 3> args{ RE::GFxValue{ a_l.circleLineThickness }, RE::GFxValue{ static_cast<double>(a_l.circleLineColor) }, RE::GFxValue{ a_l.circleLineAlpha } };
			a_clip.Invoke("lineStyle", args);
		}
		{
			std::array<RE::GFxValue, 2> args{ RE::GFxValue{ static_cast<double>(a_l.circleFillColor) }, RE::GFxValue{ a_l.circleFillAlpha } };
			a_clip.Invoke("beginFill", args);
		}
		// 8 quadratic segments; control points at r / cos(22.5 deg).
		const double r = a_l.circleRadius;
		const double c = r / std::cos(std::numbers::pi / 8.0);
		{
			std::array<RE::GFxValue, 2> args{ RE::GFxValue{ r }, RE::GFxValue{ 0.0 } };
			a_clip.Invoke("moveTo", args);
		}
		for (int i = 1; i <= 8; ++i) {
			const double a = i * std::numbers::pi / 4.0;
			const double ac = a - std::numbers::pi / 8.0;
			std::array<RE::GFxValue, 4> args{ RE::GFxValue{ c * std::cos(ac) }, RE::GFxValue{ c * std::sin(ac) }, RE::GFxValue{ r * std::cos(a) }, RE::GFxValue{ r * std::sin(a) } };
			a_clip.Invoke("curveTo", args);
		}
		a_clip.Invoke("endFill");
	}

	// Slot holder layout:  <slot>.i<N>          one per rule, scaled to the slot's icon size
	//                      <slot>.i<N>.m        the loaded icon .swf (its stage is EMPTY), re-centred
	//                      <slot>.i<N>.m.s      the .swf's exported symbol, attached once it has loaded
	// The FHR icon .swfs only export a sprite (SIF imports it by name), so loading the file draws
	// nothing; attachMovie on the loaded clip resolves the symbol from that file's own library -
	// the same load-then-attach TrueHUD uses for TrueHUD_Widgets.swf.
	void BuildSlot(RE::GFxValue& a_root, Slot a_slot)
	{
		RE::GFxValue holder;
		if (!NewClip(a_root, kSlotNames[a_slot], holder)) {
			return;
		}
		if (a_slot == kCircle && g_config.layout.statusInCircle) {
			RE::GFxValue circle;
			if (NewClip(holder, "bg", circle)) {
				DrawCircle(circle, g_config.layout);
			}
		}
		const auto& rules = g_config.slots[a_slot];
		for (std::size_t i = 0; i < rules.size(); ++i) {
			RE::GFxValue icon, movie;
			const auto name = "i" + std::to_string(i);
			if (!NewClip(holder, name.c_str(), icon) || !NewClip(icon, "m", movie)) {
				continue;
			}
			SetVisible(icon, false);
			RE::GFxValue url{ rules[i].source.c_str() };
			movie.Invoke("loadMovie", nullptr, &url, 1);
		}
	}

	// Centres a loaded icon on its holder's origin and scales it to a_size (largest side).
	void FitIcon(RE::GFxValue& a_icon, const std::string& a_symbol, double a_size)
	{
		if (GetBoolMember(a_icon, "zFit")) {
			return;
		}
		RE::GFxValue movie, sprite;
		if (!a_icon.GetMember("m", &movie) || !movie.IsDisplayObject()) {
			return;
		}
		if (!movie.GetMember("s", &sprite) || !sprite.IsDisplayObject()) {
			std::array<RE::GFxValue, 3> args{ RE::GFxValue{ a_symbol.c_str() }, RE::GFxValue{ "s" }, RE::GFxValue{ 1.0 } };
			movie.Invoke("attachMovie", &sprite, args.data(), args.size());
			if (!sprite.IsDisplayObject()) {
				// .swf not loaded yet - or the symbol name is wrong, which never resolves.
				const double tries = GetNumberMember(a_icon, "zTries", 0.0) + 1.0;
				a_icon.SetMember("zTries", RE::GFxValue{ tries });
				if (tries == 300.0) {
					SKSE::log::warn("Symbol '{}' still not attachable after 300 frames - wrong 'symbol' or missing .swf?", a_symbol);
				}
				return;
			}
		}
		Bounds b;
		if (!GetBounds(sprite, movie, b)) {
			return;
		}
		SetPos(movie, -(b.xMin + b.xMax) / 2.0, -(b.yMin + b.yMax) / 2.0);
		const double scale = 100.0 * a_size / std::max(b.xMax - b.xMin, b.yMax - b.yMin);
		RE::GFxValue::DisplayInfo di;
		a_icon.GetDisplayInfo(&di);
		di.SetScale(scale, scale);
		a_icon.SetDisplayInfo(di);
		a_icon.SetMember("zFit", RE::GFxValue{ true });
	}

	// Shows rule a_active in the slot (or none), returns whether anything is visible.
	bool ShowSlot(RE::GFxValue& a_holder, Slot a_slot, int a_active, double a_size)
	{
		const auto count = g_config.slots[a_slot].size();
		for (std::size_t i = 0; i < count; ++i) {
			RE::GFxValue icon;
			const auto name = "i" + std::to_string(i);
			if (!a_holder.GetMember(name.c_str(), &icon) || !icon.IsDisplayObject()) {
				continue;
			}
			FitIcon(icon, g_config.slots[a_slot][i].symbol, a_size);
			SetVisible(icon, static_cast<int>(i) == a_active && GetBoolMember(icon, "zFit"));
		}
		return a_active >= 0;
	}

	// ---------------------------------------------------------------- per-bar update

	void UpdateBar(RE::GFxValue& a_bar, RE::Actor* a_actor)
	{
		const auto& cfg = g_config;
		const auto& l = cfg.layout;

		RE::GFxValue root;
		if (!a_bar.GetMember(kRootName, &root) || !root.IsDisplayObject() ||
			GetNumberMember(root, "zGen", -1.0) != static_cast<double>(cfg.generation)) {
			if (root.IsDisplayObject()) {
				root.Invoke("removeMovieClip");
			}
			if (!NewClip(a_bar, kRootName, root)) {
				return;
			}
			root.SetMember("zGen", RE::GFxValue{ static_cast<double>(cfg.generation) });
			for (std::size_t s = 0; s < kSlotCount; ++s) {
				BuildSlot(root, static_cast<Slot>(s));
			}
		}

		const bool eligible = !a_actor->IsDead() &&
		                      (!cfg.requireInCombat || a_actor->IsInCombat()) &&
		                      (!cfg.requireHostile || a_actor->IsHostileToActor(RE::PlayerCharacter::GetSingleton()));
		SetVisible(root, eligible);
		if (!eligible) {
			return;
		}

		// Layout reference: the health bar's frame, in the info bar's own coordinates. It is
		// re-read every frame because TrueHUD animates the bar width when the target changes.
		RE::GFxValue bars, health, frame;
		Bounds hb;
		if (!a_bar.GetMember("Bars", &bars) || !bars.GetMember("HealthBar", &health)) {
			return;
		}
		if (!(health.GetMember("Frame", &frame) && GetBounds(frame, a_bar, hb)) && !GetBounds(health, a_bar, hb)) {
			return;
		}
		double leftEdge = hb.xMin;
		RE::GFxValue indicator;
		Bounds ib;
		if (a_bar.GetMember("Indicator", &indicator) && indicator.IsDisplayObject()) {
			RE::GFxValue::DisplayInfo di;
			indicator.GetDisplayInfo(&di);
			if (di.GetVisible() && di.GetAlpha() > 0.0 && GetBounds(indicator, a_bar, ib)) {
				leftEdge = std::min(leftEdge, ib.xMin);
			}
		}
		const double cy = (hb.yMin + hb.yMax) / 2.0 + l.offsetY;

		auto* effects = a_actor->GetMagicTarget() ? a_actor->GetMagicTarget()->GetActiveEffectList() : nullptr;

		RE::GFxValue left, right, circle;
		if (root.GetMember(kSlotNames[kLeft], &left) && left.IsDisplayObject()) {
			ShowSlot(left, kLeft, MatchSlot(effects, cfg.slots[kLeft]), l.arrowSize);
			SetPos(left, leftEdge - l.gap - l.arrowSize / 2.0, cy);
		}

		double rightEdge = hb.xMax;
		const bool haveRight = root.GetMember(kSlotNames[kRight], &right) && right.IsDisplayObject();
		const bool haveStatus = root.GetMember(kSlotNames[kCircle], &circle) && circle.IsDisplayObject();

		if (l.statusInCircle) {
			// [bar] (status) [right arrow]
			if (haveStatus) {
				const bool any = ShowSlot(circle, kCircle, MatchSlot(effects, cfg.slots[kCircle]), l.circleIconSize);
				const bool show = any || l.circleAlwaysVisible;
				SetVisible(circle, show);
				if (show) {
					SetPos(circle, rightEdge + l.gap + l.circleRadius, cy);
					rightEdge += l.gap + 2.0 * l.circleRadius;
				}
			}
			if (haveRight) {
				ShowSlot(right, kRight, MatchSlot(effects, cfg.slots[kRight]), l.arrowSize);
				SetPos(right, rightEdge + l.gap + l.arrowSize / 2.0, cy);
			}
		} else {
			// [bar] [right arrow] [status]: the arrow always takes the spot next to the bar; the
			// status icon follows it, or moves up to the bar when no right attack is incoming.
			if (haveRight) {
				const bool shown = ShowSlot(right, kRight, MatchSlot(effects, cfg.slots[kRight]), l.arrowSize);
				SetPos(right, rightEdge + l.gap + l.arrowSize / 2.0, cy);
				if (shown || l.reserveRightArrowSlot) {
					rightEdge += l.gap + l.arrowSize;
				}
			}
			if (haveStatus) {
				ShowSlot(circle, kCircle, MatchSlot(effects, cfg.slots[kCircle]), l.statusIconSize);
				SetPos(circle, rightEdge + l.gap + l.statusIconSize / 2.0, cy);
			}
		}
	}

	void UpdateAll()
	{
		if (!g_dataLoaded) {
			return;
		}
		auto* ui = RE::UI::GetSingleton();
		auto view = ui ? ui->GetMovieView("TrueHUD"sv) : nullptr;
		if (!view) {
			return;
		}
		RE::GFxValue container;
		if (!view->GetVariable(&container, kBarContainer) || !container.IsDisplayObject()) {
			return;
		}
		auto* lists = RE::ProcessLists::GetSingleton();
		if (!lists) {
			return;
		}
		for (auto& handle : lists->highActorHandles) {
			auto actor = handle.get();
			if (!actor) {
				continue;
			}
			RE::GFxValue bar;
			const auto key = std::to_string(handle.native_handle());
			if (container.GetMember(key.c_str(), &bar) && bar.IsDisplayObject()) {
				UpdateBar(bar, actor.get());
			}
		}
	}

	// ---------------------------------------------------------------- hook

	// HUDMenu::AdvanceMovie runs once per frame on the UI thread, the same thread TrueHUD
	// updates its own movie on.
	struct HUDAdvanceMovie
	{
		static void thunk(RE::HUDMenu* a_this, float a_interval, std::uint32_t a_currentTime)
		{
			func(a_this, a_interval, a_currentTime);
			UpdateAll();
		}
		static inline REL::Relocation<decltype(thunk)> func;
	};

	void MessageHandler(SKSE::MessagingInterface::Message* a_msg)
	{
		switch (a_msg->type) {
		case SKSE::MessagingInterface::kDataLoaded:
			LoadConfig();
			g_dataLoaded = true;
			break;
		case SKSE::MessagingInterface::kPostLoadGame:
			LoadConfig();  // pick up layout tweaks without a restart
			break;
		default:
			break;
		}
	}
}

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	SKSE::log::info("ZenTrueHUDCombatIcons 1.0.0 loading, runtime {}", REL::Module::get().version().string());

	REL::Relocation<std::uintptr_t> vtbl{ RE::VTABLE_HUDMenu[0] };
	HUDAdvanceMovie::func = vtbl.write_vfunc(0x05, HUDAdvanceMovie::thunk);

	SKSE::GetMessagingInterface()->RegisterListener(MessageHandler);
	return true;
}
