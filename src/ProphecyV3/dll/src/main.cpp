// Zenderal Prophecy UI (Prophecy v3).
//
// The Prophecy power opens this window instead of B612's card menu: ZP_ProphecyMenu (v1's script, shared) checks
// SKSE.GetPluginVersion("ZenProphecyUI") and, when this plugin is loaded, sends the mod event ZP_ProphecyUI_Open.
// The window is an SKSE Menu Framework window (AddWindow) that draws each tree as a constellation: nodes, solid
// lines between learned nodes, dashed lines otherwise, root at the bottom. Hover shows the perk's card art and text;
// clicking a learnable node asks to confirm, then sends ZP_ProphecyLearn (numArg = the node's index), and the script
// learns it with its usual TryLearn - points, powers and gifts stay in Papyrus.
//
// Data: Data/SKSE/Plugins/ZenProphecyUI.json, generated from the plugin's own menu quest arrays, so a node's index is
// the script's array index. Layout (tiers, centred rows) is generated too.
//
// ImGui: SKSE Menu Framework 1.90.8's cimgui exports, bound by name (as Zenderal's Casting Bar does). Functions that
// return an ImVec2 write it through a first out-pointer (checked by disassembly of igGetCursorScreenPos and
// igCalcTextSize). AddWindow(RenderFunction) returns a handle whose first member is std::atomic<bool> IsOpen;
// LoadTexture(const char* path, ImVec2* size) returns an ImTextureID.
//
// Threads: Render runs on SMF's render thread. Game state (perks owned, points) is read on the game thread by a
// queued task into a snapshot under a mutex; Render only reads the snapshot.

SKSEPluginInfo(
	.Version = REL::Version{ 1, 0, 0, 0 },
	.Name = "ZenProphecyUI"sv,
	.Author = "Zenderal"sv,
	.StructCompatibility = SKSE::StructCompatibility::Independent,
	.RuntimeCompatibility = SKSE::VersionIndependence::AddressLibrary)

namespace
{
	// ---------------------------------------------------------------------------------------------- ImGui binding
	struct ImVec2
	{
		float x = 0.0f;
		float y = 0.0f;
	};
	struct ImVec4
	{
		float x = 0.0f;
		float y = 0.0f;
		float z = 0.0f;
		float w = 0.0f;
	};
	using ImU32 = std::uint32_t;
	using RenderFunction = void(__stdcall*)();

	struct WindowInterface
	{
		std::atomic<bool> IsOpen{ false };
	};

	HMODULE Framework()
	{
		static HMODULE module = GetModuleHandleW(L"SKSEMenuFramework");
		return module;
	}

	template <class T>
	T Get(const char* a_name)
	{
		auto* func = reinterpret_cast<T>(GetProcAddress(Framework(), a_name));
		if (!func) {
			SKSE::log::error("SKSEMenuFramework.dll has no export {}", a_name);
		}
		return func;
	}

#define ZP_BIND(name, type) static auto name = Get<type>(#name)

	constexpr ImU32 Col(int r, int g, int b, int a = 255)
	{
		return (ImU32(a) << 24) | (ImU32(b) << 16) | (ImU32(g) << 8) | ImU32(r);
	}

	// ImGui enums (1.90.8)
	constexpr int kCondAppearing = 8;
	constexpr int kWindowNoCollapse = 1 << 5;
	constexpr int kWindowNoSavedSettings = 1 << 8;
	constexpr int kWindowAlwaysAutoResize = 1 << 6;
	constexpr int kKeyEscape = 526;

	namespace ig
	{
		bool Begin(const char* a_name, bool* a_open, int a_flags)
		{
			ZP_BIND(igBegin, bool (*)(const char*, bool*, int));
			return igBegin && igBegin(a_name, a_open, a_flags);
		}
		void End()
		{
			ZP_BIND(igEnd, void (*)());
			if (igEnd) igEnd();
		}
		void SetNextWindowSize(ImVec2 a_size, int a_cond)
		{
			ZP_BIND(igSetNextWindowSize, void (*)(ImVec2, int));
			if (igSetNextWindowSize) igSetNextWindowSize(a_size, a_cond);
		}
		void SetNextWindowPos(ImVec2 a_pos, int a_cond, ImVec2 a_pivot)
		{
			ZP_BIND(igSetNextWindowPos, void (*)(ImVec2, int, ImVec2));
			if (igSetNextWindowPos) igSetNextWindowPos(a_pos, a_cond, a_pivot);
		}
		void* GetWindowDrawList()
		{
			ZP_BIND(igGetWindowDrawList, void* (*)());
			return igGetWindowDrawList ? igGetWindowDrawList() : nullptr;
		}
		ImVec2 GetCursorScreenPos()
		{
			ZP_BIND(igGetCursorScreenPos, void (*)(ImVec2*));
			ImVec2 v{};
			if (igGetCursorScreenPos) igGetCursorScreenPos(&v);
			return v;
		}
		void SetCursorScreenPos(ImVec2 a_pos)
		{
			ZP_BIND(igSetCursorScreenPos, void (*)(ImVec2));
			if (igSetCursorScreenPos) igSetCursorScreenPos(a_pos);
		}
		ImVec2 GetContentRegionAvail()
		{
			ZP_BIND(igGetContentRegionAvail, void (*)(ImVec2*));
			ImVec2 v{};
			if (igGetContentRegionAvail) igGetContentRegionAvail(&v);
			return v;
		}
		ImVec2 CalcTextSize(const char* a_text)
		{
			ZP_BIND(igCalcTextSize, void (*)(ImVec2*, const char*, const char*, bool, float));
			ImVec2 v{};
			if (igCalcTextSize) igCalcTextSize(&v, a_text, nullptr, false, -1.0f);
			return v;
		}
		bool InvisibleButton(const char* a_id, ImVec2 a_size)
		{
			ZP_BIND(igInvisibleButton, bool (*)(const char*, ImVec2, int));
			return igInvisibleButton && igInvisibleButton(a_id, a_size, 0);
		}
		bool IsItemHovered()
		{
			ZP_BIND(igIsItemHovered, bool (*)(int));
			return igIsItemHovered && igIsItemHovered(0);
		}
		bool IsItemClicked()
		{
			ZP_BIND(igIsItemClicked, bool (*)(int));
			return igIsItemClicked && igIsItemClicked(0);
		}
		bool BeginTooltip()
		{
			ZP_BIND(igBeginTooltip, bool (*)());
			return igBeginTooltip && igBeginTooltip();
		}
		void EndTooltip()
		{
			ZP_BIND(igEndTooltip, void (*)());
			if (igEndTooltip) igEndTooltip();
		}
		void TextUnformatted(const char* a_text)
		{
			ZP_BIND(igTextUnformatted, void (*)(const char*, const char*));
			if (igTextUnformatted) igTextUnformatted(a_text, nullptr);
		}
		void TextColored(ImVec4 a_col, const char* a_text)
		{
			ZP_BIND(igTextColored, void (*)(ImVec4, const char*, ...));
			if (igTextColored) igTextColored(a_col, "%s", a_text);
		}
		void TextWrapped(const char* a_text)
		{
			ZP_BIND(igTextWrapped, void (*)(const char*, ...));
			if (igTextWrapped) igTextWrapped("%s", a_text);
		}
		void PushTextWrapPos(float a_pos)
		{
			ZP_BIND(igPushTextWrapPos, void (*)(float));
			if (igPushTextWrapPos) igPushTextWrapPos(a_pos);
		}
		void PopTextWrapPos()
		{
			ZP_BIND(igPopTextWrapPos, void (*)());
			if (igPopTextWrapPos) igPopTextWrapPos();
		}
		void Image(void* a_tex, ImVec2 a_size)
		{
			ZP_BIND(igImage, void (*)(void*, ImVec2, ImVec2, ImVec2, ImVec4, ImVec4));
			if (igImage && a_tex) igImage(a_tex, a_size, ImVec2{ 0, 0 }, ImVec2{ 1, 1 }, ImVec4{ 1, 1, 1, 1 }, ImVec4{ 0, 0, 0, 0 });
		}
		bool BeginTabBar(const char* a_id)
		{
			ZP_BIND(igBeginTabBar, bool (*)(const char*, int));
			return igBeginTabBar && igBeginTabBar(a_id, 0);
		}
		void EndTabBar()
		{
			ZP_BIND(igEndTabBar, void (*)());
			if (igEndTabBar) igEndTabBar();
		}
		bool BeginTabItem(const char* a_label)
		{
			ZP_BIND(igBeginTabItem, bool (*)(const char*, bool*, int));
			return igBeginTabItem && igBeginTabItem(a_label, nullptr, 0);
		}
		void EndTabItem()
		{
			ZP_BIND(igEndTabItem, void (*)());
			if (igEndTabItem) igEndTabItem();
		}
		void OpenPopup(const char* a_id)
		{
			ZP_BIND(igOpenPopup_Str, void (*)(const char*, int));
			if (igOpenPopup_Str) igOpenPopup_Str(a_id, 0);
		}
		bool BeginPopupModal(const char* a_name)
		{
			ZP_BIND(igBeginPopupModal, bool (*)(const char*, bool*, int));
			return igBeginPopupModal && igBeginPopupModal(a_name, nullptr, kWindowAlwaysAutoResize | kWindowNoSavedSettings);
		}
		void EndPopup()
		{
			ZP_BIND(igEndPopup, void (*)());
			if (igEndPopup) igEndPopup();
		}
		void CloseCurrentPopup()
		{
			ZP_BIND(igCloseCurrentPopup, void (*)());
			if (igCloseCurrentPopup) igCloseCurrentPopup();
		}
		bool Button(const char* a_label, ImVec2 a_size = {})
		{
			ZP_BIND(igButton, bool (*)(const char*, ImVec2));
			return igButton && igButton(a_label, a_size);
		}
		void SameLine()
		{
			ZP_BIND(igSameLine, void (*)(float, float));
			if (igSameLine) igSameLine(0.0f, -1.0f);
		}
		void Separator()
		{
			ZP_BIND(igSeparator, void (*)());
			if (igSeparator) igSeparator();
		}
		void Dummy(ImVec2 a_size)
		{
			ZP_BIND(igDummy, void (*)(ImVec2));
			if (igDummy) igDummy(a_size);
		}
		bool IsKeyPressed(int a_key)
		{
			ZP_BIND(igIsKeyPressed_Bool, bool (*)(int, bool));
			return igIsKeyPressed_Bool && igIsKeyPressed_Bool(a_key, false);
		}
		void PushID(int a_id)
		{
			ZP_BIND(igPushID_Int, void (*)(int));
			if (igPushID_Int) igPushID_Int(a_id);
		}
		void PopID()
		{
			ZP_BIND(igPopID, void (*)());
			if (igPopID) igPopID();
		}
	}

	namespace dl
	{
		void Line(void* a_dl, ImVec2 a_a, ImVec2 a_b, ImU32 a_col, float a_thick)
		{
			ZP_BIND(ImDrawList_AddLine, void (*)(void*, ImVec2, ImVec2, ImU32, float));
			if (ImDrawList_AddLine && a_dl) ImDrawList_AddLine(a_dl, a_a, a_b, a_col, a_thick);
		}
		void Circle(void* a_dl, ImVec2 a_c, float a_r, ImU32 a_col, float a_thick)
		{
			ZP_BIND(ImDrawList_AddCircle, void (*)(void*, ImVec2, float, ImU32, int, float));
			if (ImDrawList_AddCircle && a_dl) ImDrawList_AddCircle(a_dl, a_c, a_r, a_col, 0, a_thick);
		}
		void Disc(void* a_dl, ImVec2 a_c, float a_r, ImU32 a_col)
		{
			ZP_BIND(ImDrawList_AddCircleFilled, void (*)(void*, ImVec2, float, ImU32, int));
			if (ImDrawList_AddCircleFilled && a_dl) ImDrawList_AddCircleFilled(a_dl, a_c, a_r, a_col, 0);
		}
		void Text(void* a_dl, ImVec2 a_pos, ImU32 a_col, const char* a_text)
		{
			ZP_BIND(ImDrawList_AddText_Vec2, void (*)(void*, ImVec2, ImU32, const char*, const char*));
			if (ImDrawList_AddText_Vec2 && a_dl) ImDrawList_AddText_Vec2(a_dl, a_pos, a_col, a_text, nullptr);
		}
		// text at a given pixel size (the window font, scaled)
		void TextSized(void* a_dl, float a_size, ImVec2 a_pos, ImU32 a_col, const char* a_text)
		{
			ZP_BIND(igGetFont, void* (*)());
			ZP_BIND(ImDrawList_AddText_FontPtr, void (*)(void*, void*, float, ImVec2, ImU32, const char*, const char*, float, const ImVec4*));
			if (igGetFont && ImDrawList_AddText_FontPtr && a_dl) {
				ImDrawList_AddText_FontPtr(a_dl, igGetFont(), a_size, a_pos, a_col, a_text, nullptr, 0.0f, nullptr);
			} else {
				Text(a_dl, a_pos, a_col, a_text);
			}
		}
		void Image(void* a_dl, void* a_tex, ImVec2 a_min, ImVec2 a_max, ImVec2 a_uv0, ImVec2 a_uv1, ImU32 a_tint)
		{
			ZP_BIND(ImDrawList_AddImage, void (*)(void*, void*, ImVec2, ImVec2, ImVec2, ImVec2, ImU32));
			if (ImDrawList_AddImage && a_dl && a_tex) ImDrawList_AddImage(a_dl, a_tex, a_min, a_max, a_uv0, a_uv1, a_tint);
		}
		void Rect(void* a_dl, ImVec2 a_min, ImVec2 a_max, ImU32 a_col)
		{
			ZP_BIND(ImDrawList_AddRectFilled, void (*)(void*, ImVec2, ImVec2, ImU32, float, int));
			if (ImDrawList_AddRectFilled && a_dl) ImDrawList_AddRectFilled(a_dl, a_min, a_max, a_col, 0.0f, 0);
		}
		// corners: upper-left, upper-right, bottom-right, bottom-left
		void Gradient(void* a_dl, ImVec2 a_min, ImVec2 a_max, ImU32 a_ul, ImU32 a_ur, ImU32 a_br, ImU32 a_bl)
		{
			ZP_BIND(ImDrawList_AddRectFilledMultiColor, void (*)(void*, ImVec2, ImVec2, ImU32, ImU32, ImU32, ImU32));
			if (ImDrawList_AddRectFilledMultiColor && a_dl) ImDrawList_AddRectFilledMultiColor(a_dl, a_min, a_max, a_ul, a_ur, a_br, a_bl);
		}
		void DashedLine(void* a_dl, ImVec2 a_a, ImVec2 a_b, ImU32 a_col, float a_thick, float a_dash = 5.0f, float a_gap = 5.0f)
		{
			const float dx = a_b.x - a_a.x, dy = a_b.y - a_a.y;
			const float len = std::sqrt(dx * dx + dy * dy);
			if (len < 1.0f) return;
			const float ux = dx / len, uy = dy / len;
			for (float s = 0.0f; s < len; s += a_dash + a_gap) {
				const float e = std::min(s + a_dash, len);
				Line(a_dl, ImVec2{ a_a.x + ux * s, a_a.y + uy * s }, ImVec2{ a_a.x + ux * e, a_a.y + uy * e }, a_col, a_thick);
			}
		}
	}

	// ---------------------------------------------------------------------------------------------- data
	struct Node
	{
		int              index = 0;
		std::uint32_t    perkId = 0;
		std::string      name;
		std::string      description;
		std::string      image;
		std::vector<int> parents;  // global indices; either one unlocks the node
		float            x = 0.0f;
		int              tier = 0;
		int              minLevel = 0;  // capstones: level 30 (curator 2026-10-25); the script enforces it too
		RE::BGSPerk*     perk = nullptr;
		void*            texture = nullptr;
		bool             textureTried = false;
	};

	struct Tree
	{
		std::string       name;
		std::string       description;
		std::string       background;   // Data\Interface\ProphecyBackgrounds\<Tree>.dds, or empty
		void*             backgroundTex = nullptr;
		bool              backgroundTried = false;
		std::vector<Node> nodes;

		// optional hand-drawn constellation (a sword, a crucifix, a rifle): square units, y up
		struct Route
		{
			int                 from = -1;
			int                 to = -1;
			std::vector<ImVec2> via;
		};
		bool                                     shaped = false;
		std::unordered_map<int, ImVec2>          shapePos;   // node index -> position
		std::vector<Route>                       routes;
		std::vector<ImVec2>                      decorStars;
		std::vector<std::pair<ImVec2, ImVec2>>   decorLines;
		std::vector<int>                         labelsAbove; // node indices whose name sits above the star
	};

	ImVec2 Pt(const nlohmann::json& a_j)
	{
		return ImVec2{ a_j.at(0).get<float>(), a_j.at(1).get<float>() };
	}

	std::vector<Tree>         g_trees;
	std::string               g_plugin;
	std::uint32_t             g_pointsGlobalId = 0;
	std::vector<std::uint32_t>             g_noteIds;     // the selection notes, melody order
	std::vector<RE::BGSSoundDescriptorForm*> g_notes;
	std::atomic<std::size_t>               g_nextNote{ 0 };
	RE::SpellItem*                         g_power = nullptr;   // ZP_ProphecyPower, cast by the hotkey
	std::uint32_t                          g_hotkey = 25;
	void                                   PlayNextNote();
	RE::TESGlobal*            g_points = nullptr;
	WindowInterface*          g_window = nullptr;

	struct Snapshot
	{
		std::vector<bool> learned;  // by global index
		int               points = 0;
		int               level = 0;
	};
	std::mutex        g_lock;
	Snapshot          g_snap;
	std::atomic<bool> g_refreshQueued{ false };
	int               g_pending = -1;   // node index awaiting confirmation (render thread only)
	bool              g_openConfirm = false;   // set by a click inside a tab; the popup is opened at window level
	int               g_frame = 0;

	bool LoadData()
	{
		constexpr auto path = "Data/SKSE/Plugins/ZenProphecyUI.json";
		std::ifstream in(path);
		if (!in) {
			SKSE::log::error("{} not found", path);
			return false;
		}
		try {
			auto j = nlohmann::json::parse(in);
			g_plugin = j.at("plugin").get<std::string>();
			g_pointsGlobalId = j.at("pointsGlobal").get<std::uint32_t>();
			g_noteIds = j.value("selectNotes", std::vector<std::uint32_t>{});
			for (auto& jt : j.at("trees")) {
				Tree t;
				t.name = jt.at("name").get<std::string>();
				t.description = jt.value("description", "");
				t.background = jt.value("background", "");
				if (jt.contains("shape") && jt["shape"].is_object()) {
					const auto& js = jt["shape"];
					t.shaped = true;
					for (auto& [k, v] : js.at("nodes").items()) t.shapePos[std::stoi(k)] = Pt(v);
					for (auto& jr : js.at("routes")) {
						Tree::Route r;
						r.from = jr.at("from").get<int>();
						r.to = jr.at("to").get<int>();
						for (auto& p : jr.at("via")) r.via.push_back(Pt(p));
						t.routes.push_back(std::move(r));
					}
					for (auto& p : js.at("stars")) t.decorStars.push_back(Pt(p));
					for (auto& l : js.at("lines")) t.decorLines.emplace_back(Pt(l.at(0)), Pt(l.at(1)));
					if (js.contains("labelsAbove")) t.labelsAbove = js["labelsAbove"].get<std::vector<int>>();
				}
				for (auto& jn : jt.at("nodes")) {
					Node n;
					n.index = jn.at("index").get<int>();
					n.perkId = jn.at("perk").get<std::uint32_t>();
					n.name = jn.at("name").get<std::string>();
					n.description = jn.value("description", "");
					n.image = jn.value("image", "");
					n.parents = jn.at("parents").get<std::vector<int>>();
					n.x = jn.at("x").get<float>();
					n.tier = jn.at("tier").get<int>();
					n.minLevel = jn.value("minLevel", 0);
					t.nodes.push_back(std::move(n));
				}
				g_trees.push_back(std::move(t));
			}
		} catch (const std::exception& e) {
			SKSE::log::error("{}: {}", path, e.what());
			g_trees.clear();
			return false;
		}
		return true;
	}

	void ResolveForms()
	{
		auto* dh = RE::TESDataHandler::GetSingleton();
		int   missing = 0, count = 0;
		for (auto& t : g_trees) {
			for (auto& n : t.nodes) {
				n.perk = dh->LookupForm<RE::BGSPerk>(n.perkId, g_plugin);
				++count;
				if (!n.perk) {
					++missing;
					SKSE::log::error("perk {:03X} ({}) not found in {}", n.perkId, n.name, g_plugin);
				}
			}
		}
		g_points = dh->LookupForm<RE::TESGlobal>(g_pointsGlobalId, g_plugin);
		for (auto id : g_noteIds) {
			if (auto* snd = dh->LookupForm<RE::BGSSoundDescriptorForm>(id, g_plugin)) g_notes.push_back(snd);
		}
		SKSE::log::info("{} of {} selection notes resolved", g_notes.size(), g_noteIds.size());
		g_power = dh->LookupForm<RE::SpellItem>(0x805, g_plugin);   // ZP_ProphecyPower
		SKSE::log::info("Prophecy power {}", g_power ? "found" : "MISSING");
		SKSE::log::info("{} trees, {} perks ({} unresolved), points global {}", g_trees.size(), count, missing,
			g_points ? "found" : "MISSING");
	}

	int NodeCount()
	{
		int n = 0;
		for (auto& t : g_trees) n += static_cast<int>(t.nodes.size());
		return n;
	}

	// game thread
	void RefreshSnapshot()
	{
		Snapshot s;
		s.learned.assign(NodeCount(), false);
		if (auto* player = RE::PlayerCharacter::GetSingleton()) {
			s.level = player->GetLevel();
			for (auto& t : g_trees) {
				for (auto& n : t.nodes) {
					if (n.perk && n.index >= 0 && n.index < static_cast<int>(s.learned.size())) {
						s.learned[n.index] = player->HasPerk(n.perk);
					}
				}
			}
		}
		s.points = g_points ? static_cast<int>(g_points->value) : 0;
		std::scoped_lock l(g_lock);
		g_snap = std::move(s);
	}

	void QueueRefresh()
	{
		if (g_refreshQueued.exchange(true)) return;
		SKSE::GetTaskInterface()->AddTask([] {
			RefreshSnapshot();
			g_refreshQueued = false;
		});
	}

	void SendLearn(int a_index)
	{
		SKSE::GetTaskInterface()->AddTask([a_index] {
			SKSE::ModCallbackEvent ev{ "ZP_ProphecyLearn", "", static_cast<float>(a_index), nullptr };
			SKSE::GetModCallbackEventSource()->SendEvent(&ev);
			SKSE::log::info("learn request: node {}", a_index);
		});
	}

	// ---------------------------------------------------------------------------------------------- drawing
	enum class State
	{
		Learned,
		Available,  // unlocked and at least one point
		Unlocked,   // unlocked, no points
		Locked
	};

	State NodeState(const Node& a_n, const Snapshot& a_s)
	{
		auto learned = [&](int i) { return i >= 0 && i < static_cast<int>(a_s.learned.size()) && a_s.learned[i]; };
		if (learned(a_n.index)) return State::Learned;
		bool unlocked = a_n.parents.empty();
		for (int p : a_n.parents) unlocked = unlocked || learned(p);
		if (!unlocked || a_s.level < a_n.minLevel) return State::Locked;
		return a_s.points > 0 ? State::Available : State::Unlocked;
	}

	const Node* FindNode(int a_index)
	{
		for (auto& t : g_trees)
			for (auto& n : t.nodes)
				if (n.index == a_index) return &n;
		return nullptr;
	}

	std::string RequirementText(const Node& a_n, const Snapshot& a_s)
	{
		std::string t;
		auto learned = [&](int i) { return i >= 0 && i < static_cast<int>(a_s.learned.size()) && a_s.learned[i]; };
		bool parentMet = a_n.parents.empty();
		for (int p : a_n.parents) parentMet = parentMet || learned(p);
		if (!parentMet) {
			for (std::size_t k = 0; k < a_n.parents.size(); ++k) {
				if (auto* p = FindNode(a_n.parents[k])) {
					if (!t.empty()) t += " or ";
					t += p->name;
				}
			}
		}
		if (a_s.level < a_n.minLevel) t += (t.empty() ? "" : " and ") + std::format("level {}", a_n.minLevel);
		return t;
	}

	// colours (the website's dark constellation look)
	constexpr ImU32 kLineLit = Col(200, 196, 186, 230);
	constexpr ImU32 kLineDim = Col(120, 118, 112, 200);
	constexpr ImU32 kNodeDim = Col(110, 106, 98);
	constexpr ImU32 kNodeOpen = Col(150, 145, 135);
	constexpr ImU32 kNodeLearned = Col(235, 232, 222);
	constexpr ImU32 kRingAvailable = Col(214, 178, 96);
	constexpr ImU32 kLabelDim = Col(150, 140, 120);
	constexpr ImU32 kLabelLit = Col(240, 236, 226);
	constexpr ImU32 kLabelAvailable = Col(232, 200, 120);

	void Tooltip(Node& a_n, State a_state, const Snapshot& a_s)
	{
		if (!ig::BeginTooltip()) return;
		ig::PushTextWrapPos(ig::CalcTextSize("M").x * 42.0f);
		ig::TextColored(ImVec4{ 0.95f, 0.92f, 0.85f, 1.0f }, a_n.name.c_str());
		switch (a_state) {
		case State::Learned:
			ig::TextColored(ImVec4{ 0.75f, 0.85f, 0.70f, 1.0f }, "Learned");
			break;
		case State::Available:
			ig::TextColored(ImVec4{ 0.84f, 0.70f, 0.38f, 1.0f }, "Click to learn (1 Prophecy point)");
			break;
		case State::Unlocked:
			ig::TextColored(ImVec4{ 0.70f, 0.66f, 0.60f, 1.0f }, "No Prophecy points left");
			break;
		case State::Locked:
			ig::TextColored(ImVec4{ 0.70f, 0.50f, 0.45f, 1.0f }, ("Requires " + RequirementText(a_n, a_s)).c_str());
			break;
		}
		ig::Separator();
		if (!a_n.textureTried) {
			a_n.textureTried = true;
			if (!a_n.image.empty() && std::filesystem::exists(a_n.image)) {
				ZP_BIND(LoadTexture, void* (*)(const char*, ImVec2*));
				if (LoadTexture) a_n.texture = LoadTexture(a_n.image.c_str(), nullptr);
				SKSE::log::info("texture {}: {}", a_n.image, a_n.texture ? "loaded" : "failed");
			}
		}
		if (a_n.texture) {
			ig::Image(a_n.texture, ImVec2{ 233.0f, 190.0f });
		}
		ig::TextWrapped(a_n.description.c_str());
		ig::PopTextWrapPos();
		ig::EndTooltip();
	}

	void DrawTree(Tree& a_tree, const Snapshot& a_s)
	{
		void*        list = ig::GetWindowDrawList();
		const ImVec2 origin = ig::GetCursorScreenPos();
		const ImVec2 avail = ig::GetContentRegionAvail();
		if (avail.x < 50.0f || avail.y < 50.0f) return;

		// background art (curator's, one per tree): cover-fit, dimmed, with a dark vignette so the stars and labels
		// stay readable. Loaded on first draw (render thread).
		if (!a_tree.backgroundTried) {
			a_tree.backgroundTried = true;
			if (!a_tree.background.empty() && std::filesystem::exists(a_tree.background)) {
				ZP_BIND(LoadTexture, void* (*)(const char*, ImVec2*));
				if (LoadTexture) a_tree.backgroundTex = LoadTexture(a_tree.background.c_str(), nullptr);
				SKSE::log::info("background {}: {}", a_tree.background, a_tree.backgroundTex ? "loaded" : "failed");
			}
		}
		if (a_tree.backgroundTex) {
			const ImVec2 lo = origin, hi{ origin.x + avail.x, origin.y + avail.y };
			const float  imgAspect = 1600.0f / 900.0f, canvasAspect = avail.x / avail.y;
			ImVec2       uv0{ 0.0f, 0.0f }, uv1{ 1.0f, 1.0f };
			if (canvasAspect > imgAspect) {
				const float h = imgAspect / canvasAspect;
				uv0.y = 0.5f - h * 0.5f; uv1.y = 0.5f + h * 0.5f;
			} else {
				const float w = canvasAspect / imgAspect;
				uv0.x = 0.5f - w * 0.5f; uv1.x = 0.5f + w * 0.5f;
			}
			dl::Image(list, a_tree.backgroundTex, lo, hi, uv0, uv1, Col(150, 146, 140));
			dl::Rect(list, lo, hi, Col(0, 0, 0, 40));
			const ImU32 dark = Col(0, 0, 0, 170), clear = Col(0, 0, 0, 0);
			const float vy = avail.y * 0.18f, vx = avail.x * 0.12f;
			dl::Gradient(list, lo, ImVec2{ hi.x, lo.y + vy }, dark, dark, clear, clear);
			dl::Gradient(list, ImVec2{ lo.x, hi.y - vy }, hi, clear, clear, dark, dark);
			dl::Gradient(list, lo, ImVec2{ lo.x + vx, hi.y }, dark, clear, clear, dark);
			dl::Gradient(list, ImVec2{ hi.x - vx, lo.y }, hi, clear, dark, dark, clear);
		}

		int   maxTier = 0;
		float maxX = 0.5f;
		for (auto& n : a_tree.nodes) {
			maxTier = std::max(maxTier, n.tier);
			maxX = std::max(maxX, std::abs(n.x));
		}
		// zoomed to fill the canvas (curator, 2026-10-25: the first build drew the tree at half the window's height):
		// tiers spread over the full height, the width follows at 1.3x the tier step, and stars and labels scale with it
		ZP_BIND(igGetFontSize, float (*)());
		const float baseFont = igGetFontSize ? igGetFontSize() : ig::CalcTextSize("Ag").y;
		const float baseLabelH = ig::CalcTextSize("Ag").y;
		const float marginY = 28.0f + baseLabelH * 1.6f;
		float       stepY = std::min(260.0f, (avail.y - 2.0f * marginY) / std::max(1, maxTier));
		const float stepX = std::min(stepY * 1.3f, (avail.x * 0.5f - 140.0f) / maxX);

		// a hand-drawn shape: fit the whole figure (talents, waypoints, decoration) into the canvas, one scale for x and y
		float shapeScale = 0.0f, shapeCX = 0.0f, shapeCY = 0.0f;
		if (a_tree.shaped) {
			float lx = 1e9f, ly = 1e9f, hx = -1e9f, hy = -1e9f;
			auto grow = [&](ImVec2 p) { lx = std::min(lx, p.x); ly = std::min(ly, p.y); hx = std::max(hx, p.x); hy = std::max(hy, p.y); };
			for (auto& [i, p] : a_tree.shapePos) grow(p);
			for (auto& r : a_tree.routes) for (auto& p : r.via) grow(p);
			for (auto& p : a_tree.decorStars) grow(p);
			for (auto& [a, b] : a_tree.decorLines) { grow(a); grow(b); }
			const float w = std::max(0.5f, hx - lx), h = std::max(0.5f, hy - ly);
			shapeScale = std::min({ 260.0f, (avail.x - 240.0f) / w, (avail.y - 2.0f * marginY) / h });
			shapeCX = (lx + hx) * 0.5f;
			shapeCY = (ly + hy) * 0.5f;
			stepY = shapeScale;     // sizes stars, lines and labels below
		}
		const float zoom = std::clamp(stepY / 150.0f, 1.0f, 1.8f);
		const float labelSize = baseFont * std::clamp(zoom * 1.15f, 1.0f, 1.6f);
		const float labelScale = labelSize / baseFont;
		const float labelH = baseLabelH * labelScale;
		const float cx = origin.x + avail.x * 0.5f;
		const float baseY = origin.y + avail.y * 0.5f + stepY * maxTier * 0.5f;   // the tree centred vertically
		const float cy = origin.y + avail.y * 0.5f;
		auto toScreen = [&](ImVec2 u) { return ImVec2{ cx + (u.x - shapeCX) * shapeScale, cy - (u.y - shapeCY) * shapeScale }; };
		auto at = [&](const Node& n) {
			if (a_tree.shaped) {
				if (auto it = a_tree.shapePos.find(n.index); it != a_tree.shapePos.end()) return toScreen(it->second);
			}
			return ImVec2{ cx + n.x * stepX, baseY - n.tier * stepY };
		};
		auto learned = [&](int i) { return i >= 0 && i < static_cast<int>(a_s.learned.size()) && a_s.learned[i]; };

		// the figure's faint outline (decoration only)
		if (a_tree.shaped) {
			constexpr ImU32 kDecorLine = Col(185, 175, 155, 80);
			constexpr ImU32 kDecorStar = Col(215, 205, 185, 120);
			for (auto& [a, b] : a_tree.decorLines) dl::Line(list, toScreen(a), toScreen(b), kDecorLine, 1.0f * zoom);
			for (auto& p : a_tree.decorStars) dl::Disc(list, toScreen(p), 2.6f * zoom, kDecorStar);
		}

		// prerequisite lines, under the nodes; a shaped tree routes them through its waypoints
		for (auto& n : a_tree.nodes) {
			for (int p : n.parents) {
				const Node* pn = FindNode(p);
				if (!pn) continue;
				std::vector<ImVec2> path{ at(*pn) };
				for (auto& r : a_tree.routes) {
					if (r.from == p && r.to == n.index) {
						for (auto& v : r.via) path.push_back(toScreen(v));
						break;
					}
				}
				path.push_back(at(n));
				const bool lit = learned(n.index) && learned(p);
				for (std::size_t k = 0; k + 1 < path.size(); ++k) {
					if (lit) {
						dl::Line(list, path[k], path[k + 1], kLineLit, 1.6f * zoom);
					} else {
						dl::DashedLine(list, path[k], path[k + 1], kLineDim, 1.2f * zoom, 6.0f * zoom, 6.0f * zoom);
					}
				}
			}
		}

		for (auto& n : a_tree.nodes) {
			const ImVec2 c = at(n);
			const State  st = NodeState(n, a_s);
			const bool   capstone = n.tier == maxTier && maxTier > 0;
			const float  r = (capstone ? 13.0f : 9.0f) * zoom;

			switch (st) {
			case State::Learned:
				dl::Disc(list, c, r, kNodeLearned);
				dl::Circle(list, c, r + 4.0f, kNodeLearned, 2.0f);
				break;
			case State::Available:
				dl::Disc(list, c, r - 2.0f, kNodeOpen);
				dl::Circle(list, c, r + 3.0f, kRingAvailable, 2.0f);
				break;
			case State::Unlocked:
				dl::Disc(list, c, r - 2.0f, kNodeOpen);
				break;
			case State::Locked:
				dl::Disc(list, c, r - 3.0f, kNodeDim);
				break;
			}
			if (capstone && st != State::Learned) {
				dl::Circle(list, c, r + 1.0f, st == State::Locked ? kNodeDim : kNodeOpen, 2.0f);
			}

			ImVec2       ts = ig::CalcTextSize(n.name.c_str());
			ts.x *= labelScale;
			ts.y *= labelScale;
			const ImU32  lc = st == State::Learned ? kLabelLit : st == State::Available ? kLabelAvailable : kLabelDim;
			const bool   above = std::find(a_tree.labelsAbove.begin(), a_tree.labelsAbove.end(), n.index) != a_tree.labelsAbove.end();
			const ImVec2 lp{ c.x - ts.x * 0.5f, above ? c.y - r - 6.0f - ts.y : c.y + r + 6.0f };
			if (a_tree.backgroundTex) {      // a soft drop shadow keeps labels readable on the art
				const ImU32 shadow = Col(0, 0, 0, 210);
				dl::TextSized(list, labelSize, ImVec2{ lp.x + 1.5f, lp.y + 1.5f }, shadow, n.name.c_str());
				dl::TextSized(list, labelSize, ImVec2{ lp.x - 1.0f, lp.y + 1.0f }, shadow, n.name.c_str());
			}
			dl::TextSized(list, labelSize, lp, lc, n.name.c_str());

			// hit area: the node and its label
			const float hw = std::max(r + 6.0f, ts.x * 0.5f + 4.0f);
			ig::SetCursorScreenPos(ImVec2{ c.x - hw, above ? c.y - r - 12.0f - labelH : c.y - r - 6.0f });
			ig::PushID(n.index);
			ig::InvisibleButton("node", ImVec2{ hw * 2.0f, r * 2.0f + 12.0f + labelH });
			const bool hovered = ig::IsItemHovered();
			const bool clicked = ig::IsItemClicked();
			ig::PopID();
			if (hovered) {
				Tooltip(n, st, a_s);
			}
			if (clicked && st == State::Available) {
				g_pending = n.index;
				g_openConfirm = true;     // opened by ConfirmPopup, in the same ID scope that draws it
				PlayNextNote();
			}
		}
		ig::SetCursorScreenPos(origin);
		ig::Dummy(avail);
	}

	// The curator's piano melody, one note per selection (2026-10-25): each click on a learnable star plays the next
	// note, so choosing talents plays the tune in order. AudioCategoryUI / SOMUIDefault: heard while the game is paused.
	void PlayNextNote()
	{
		if (g_notes.empty()) return;
		const std::size_t k = g_nextNote.fetch_add(1) % g_notes.size();
		auto* snd = g_notes[k];
		SKSE::GetTaskInterface()->AddTask([snd] {
			if (auto* audio = RE::BSAudioManager::GetSingleton()) audio->Play(snd);
		});
	}

	// A popup is found by its name in the current ID stack: opening it inside the tab item and drawing it outside
	// the tab bar never matched, so clicks did nothing (curator, 2026-10-25). Open and draw it at the same level.
	void ConfirmPopup()
	{
		if (g_openConfirm) {
			g_openConfirm = false;
			ig::OpenPopup("Learn talent##zp");
		}
		if (!ig::BeginPopupModal("Learn talent##zp")) return;
		const Node* n = FindNode(g_pending);
		if (n) {
			ig::TextUnformatted(("Learn " + n->name + " for 1 Prophecy point?").c_str());
			ig::Dummy(ImVec2{ 0.0f, 6.0f });
			if (ig::Button("Learn", ImVec2{ 120.0f, 0.0f })) {
				SendLearn(n->index);
				g_pending = -1;
				ig::CloseCurrentPopup();
			}
			ig::SameLine();
		}
		if (ig::Button("Cancel", ImVec2{ 120.0f, 0.0f }) || !n) {
			g_pending = -1;
			ig::CloseCurrentPopup();
		}
		ig::EndPopup();
	}

	void __stdcall Render()
	{
		if (!g_window) return;
		if ((g_frame++ % 10) == 0) {
			QueueRefresh();      // keep the snapshot fresh while open (learning happens in Papyrus)
		}
		Snapshot s;
		{
			std::scoped_lock l(g_lock);
			s = g_snap;
		}

		// opens centred, 85% of the screen tall, every time (curator, 2026-10-25: a fixed 980x760 was small on an
		// ultrawide). DisplaySize is ImGuiIO's third member (after ConfigFlags and BackendFlags, offset 8).
		ImVec2 display{ 1920.0f, 1080.0f };
		{
			ZP_BIND(igGetIO, char* (*)());
			if (igGetIO) {
				const ImVec2 d = *reinterpret_cast<const ImVec2*>(igGetIO() + 8);
				if (d.x > 100.0f && d.y > 100.0f) display = d;
			}
		}
		ig::SetNextWindowSize(ImVec2{ std::clamp(display.x * 0.45f, 900.0f, 1500.0f), display.y * 0.85f }, kCondAppearing);
		ig::SetNextWindowPos(ImVec2{ display.x * 0.5f, display.y * 0.5f }, kCondAppearing, ImVec2{ 0.5f, 0.5f });
		bool open = true;
		if (ig::Begin("The Prophecy##ZenProphecyUI", &open, kWindowNoCollapse)) {
			ig::TextColored(ImVec4{ 0.84f, 0.70f, 0.38f, 1.0f }, std::format("Prophecy points: {}", s.points).c_str());
			ig::SameLine();
			ig::TextColored(ImVec4{ 0.55f, 0.53f, 0.50f, 1.0f }, "   Hover a star to read it; click a lit one to learn it.");
			if (ig::BeginTabBar("trees##zp")) {
				for (auto& t : g_trees) {
					if (ig::BeginTabItem(t.name.c_str())) {
						if (!t.description.empty()) {
							ig::TextColored(ImVec4{ 0.70f, 0.66f, 0.60f, 1.0f }, t.description.c_str());
						}
						DrawTree(t, s);
						ig::EndTabItem();
					}
				}
				ig::EndTabBar();
			}
			ConfirmPopup();
		}
		ig::End();
		if (!open || (g_pending < 0 && ig::IsKeyPressed(kKeyEscape))) {
			g_window->IsOpen = false;
		}
	}

	// ---------------------------------------------------------------------------------------------- open event
	class OpenSink : public RE::BSTEventSink<SKSE::ModCallbackEvent>
	{
	public:
		RE::BSEventNotifyControl ProcessEvent(const SKSE::ModCallbackEvent* a_event, RE::BSTEventSource<SKSE::ModCallbackEvent>*) override
		{
			if (a_event && a_event->eventName == "ZP_ProphecyUI_Open"sv) {
				RefreshSnapshot();   // we are on the game thread here
				g_pending = -1;
				if (g_window && !g_trees.empty()) {
					g_window->IsOpen = true;
					SKSE::log::info("window opened");
				} else {
					SKSE::log::error("open requested but the window is not available (window {}, trees {})",
						static_cast<void*>(g_window), g_trees.size());
				}
			}
			return RE::BSEventNotifyControl::kContinue;
		}
	};
	OpenSink g_openSink;

	// ---------------------------------------------------------------------------------------------- hotkey
	// The Prophecy key (curator, 2026-10-25: P; Quick Magic was moved off P in the list's keybind files). It casts the
	// Prophecy power instantly, so it does exactly what the power does (ZP_ProphecyPowerEffect: refresh the arrays,
	// then ZP_ProphecyMenu.RequestOpen pays points, repairs powers and opens this window). Pressed while the window is
	// open, it closes it. Ignored in menus, dialogue and the console. Data/SKSE/Plugins/ZenProphecyUI.ini [General] Hotkey.
	class HotkeySink : public RE::BSTEventSink<RE::InputEvent*>
	{
	public:
		RE::BSEventNotifyControl ProcessEvent(RE::InputEvent* const* a_event, RE::BSTEventSource<RE::InputEvent*>*) override
		{
			if (!a_event || g_hotkey == 0) return RE::BSEventNotifyControl::kContinue;
			for (auto* e = *a_event; e; e = e->next) {
				if (e->GetEventType() != RE::INPUT_EVENT_TYPE::kButton) continue;
				auto* b = e->AsButtonEvent();
				if (!b || b->GetDevice() != RE::INPUT_DEVICE::kKeyboard || b->GetIDCode() != g_hotkey || !b->IsDown()) continue;
				if (g_window && g_window->IsOpen) {
					g_window->IsOpen = false;
					continue;
				}
				auto* ui = RE::UI::GetSingleton();
				auto* player = RE::PlayerCharacter::GetSingleton();
				if (!ui || !player || !player->Is3DLoaded() || ui->GameIsPaused() ||
					ui->IsMenuOpen(RE::Console::MENU_NAME) || ui->IsMenuOpen(RE::DialogueMenu::MENU_NAME) ||
					ui->IsMenuOpen(RE::MainMenu::MENU_NAME) || ui->IsMenuOpen(RE::LoadingMenu::MENU_NAME)) {
					continue;
				}
				if (g_power) {
					if (auto* caster = player->GetMagicCaster(RE::MagicSystem::CastingSource::kInstant)) {
						caster->CastSpellImmediate(g_power, false, player, 1.0f, false, 0.0f, player);
					}
				}
			}
			return RE::BSEventNotifyControl::kContinue;
		}
	};
	HotkeySink g_hotkeySink;

	// ---------------------------------------------------------------------------------------------- Righteous Path ward
	// (curator 2026-10-25: "appear quicker and disappear fast too") The ward shield ZP_Prophecy_RighteousPath_Ward
	// (FX01 slot, Kittytails' shield of light) is worn while the player blocks with Righteous Path and an empty, spell or
	// scroll left hand, and taken off the moment that stops. Papyrus could only follow the ability's condition checks
	// (about once a second): Dual Wield Parrying forces its block into the graph, which raises no block events. Checked
	// every 33 ms on the game thread. The Papyrus paths (ZP_RighteousPathWard / ZP_RighteousPathEffect) stand down
	// when this DLL is loaded.
	constexpr RE::FormID kRighteousPathPerk = 0x811;   // ZP_Prophecy_RighteousPath
	constexpr RE::FormID kRighteousPathWard = 0xA68;   // ZP_Prophecy_RighteousPath_Ward
	RE::BGSPerk*       g_rpPerk = nullptr;
	RE::TESObjectARMO* g_rpWard = nullptr;
	std::atomic<bool>  g_rpQueued{ false };
	bool               g_rpShown = true;               // true at start: the first tick clears a ward left in a save

	bool WardWanted(RE::PlayerCharacter* a_player)
	{
		if (!g_rpPerk || a_player->IsDead() || !a_player->HasPerk(g_rpPerk)) return false;
		bool blocking = false;
		if (!a_player->GetGraphVariableBool("IsBlocking", blocking) || !blocking) return false;
		auto* left = a_player->GetEquippedObject(true);
		return !left || left->Is(RE::FormType::Spell) || left->Is(RE::FormType::Scroll);
	}

	std::int32_t WardCount(RE::PlayerCharacter* a_player)
	{
		auto counts = a_player->GetInventoryCounts([](RE::TESBoundObject& a_obj) { return &a_obj == g_rpWard; });
		auto it = counts.find(g_rpWard);
		return it == counts.end() ? 0 : it->second;
	}

	void WardTick()   // game thread
	{
		auto* player = RE::PlayerCharacter::GetSingleton();
		if (!player || !g_rpWard || !player->Is3DLoaded()) return;
		const bool want = WardWanted(player);
		if (want == g_rpShown) return;
		auto* equip = RE::ActorEquipManager::GetSingleton();
		if (!equip) return;
		if (want) {
			if (WardCount(player) < 1) player->AddObjectToContainer(g_rpWard, nullptr, 1, nullptr);
			equip->EquipObject(player, g_rpWard, nullptr, 1, nullptr, false, true, false, true);
		} else if (const auto n = WardCount(player); n > 0) {
			equip->UnequipObject(player, g_rpWard, nullptr, n, nullptr, false, true, false, true, nullptr);
			player->RemoveItem(g_rpWard, n, RE::ITEM_REMOVE_REASON::kRemove, nullptr, nullptr);
		}
		g_rpShown = want;
	}

	void StartWard()
	{
		auto* dh = RE::TESDataHandler::GetSingleton();
		if (!dh || g_plugin.empty()) return;
		g_rpPerk = dh->LookupForm<RE::BGSPerk>(kRighteousPathPerk, g_plugin);
		g_rpWard = dh->LookupForm<RE::TESObjectARMO>(kRighteousPathWard, g_plugin);
		SKSE::log::info("Righteous Path ward: perk {}, ward {}", g_rpPerk ? "found" : "MISSING", g_rpWard ? "found" : "MISSING");
		if (!g_rpPerk || !g_rpWard) return;
		std::thread([] {
			for (;;) {
				std::this_thread::sleep_for(std::chrono::milliseconds(33));
				if (g_rpQueued.exchange(true)) continue;
				SKSE::GetTaskInterface()->AddTask([] {
					WardTick();
					g_rpQueued = false;
				});
			}
		}).detach();
	}

	void LoadIni()
	{
		constexpr auto path = "Data/SKSE/Plugins/ZenProphecyUI.ini";
		g_hotkey = GetPrivateProfileIntA("General", "Hotkey", 25, path);   // DX scan code; 25 = P, 0 = off
		SKSE::log::info("hotkey {}", g_hotkey);
	}

	void OnPostLoad()
	{
		if (!Framework()) {
			SKSE::log::error("SKSE Menu Framework is not loaded - the Prophecy window is unavailable");
			return;
		}
		ZP_BIND(AddWindow, WindowInterface* (*)(RenderFunction));
		if (AddWindow) {
			g_window = AddWindow(Render);
			SKSE::log::info("SKSE Menu Framework window registered");
		}
	}
}

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	SKSE::log::info("ZenProphecyUI 1.0.0 loading, runtime {}", REL::Module::get().version().string());
	SKSE::GetMessagingInterface()->RegisterListener([](SKSE::MessagingInterface::Message* a_msg) {
		switch (a_msg->type) {
		case SKSE::MessagingInterface::kPostLoad:
			OnPostLoad();
			break;
		case SKSE::MessagingInterface::kDataLoaded:
			if (LoadData()) {
				ResolveForms();
			}
			SKSE::GetModCallbackEventSource()->AddEventSink(&g_openSink);
			LoadIni();
			if (auto* input = RE::BSInputDeviceManager::GetSingleton()) input->AddEventSink(&g_hotkeySink);
			StartWard();
			break;
		case SKSE::MessagingInterface::kPostLoadGame:
		case SKSE::MessagingInterface::kNewGame:
			g_rpShown = true;   // re-check: clear a ward a save may hold
			break;
		default:
			break;
		}
	});
	return true;
}
