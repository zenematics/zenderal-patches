#include "pch.h"

#include <atomic>
#include <chrono>
#include <thread>

// Testing tool, not part of the list. With Bottled Shaders' Unified Water on, Vyn's sea loses whole rectangles of
// water that come back as the camera turns (curator's video, 2026-10-28). Unified Water's cache has every sea cell
// (checked against Vyn_cache.wc), so the tiles exist; something hides them. This reads, on the main thread:
//   - every 500 ms, one summary line: camera, the LOD water root (Unified Water parents its tiles there), how many
//     chunk nodes/tiles are hidden (AppCulled), out of the camera frustum by their world bound, out by their
//     multibound AABB, and how many tiles are in view but sit in a node whose bound is out of view (those would be
//     culled with the node: the suspected cause);
//   - on F11, the same per chunk node and per tile, plus the loaded cells' water flags and the game's own water
//     objects (loaded-cell water);
//   - 1.1.0, also on F11: every sea cell (from Unified Water's cache) near the camera that no shown tile covers, row
//     by row, and whether a hidden tile or hidden node would cover it (the holes the grid fix left, 2026-10-28).
// Reads only, never changes a flag. Log: My Games/Skyrim Special Edition/SKSE/ZenWaterTrace.log

SKSEPluginInfo(
	.Version = REL::Version{ 1, 6, 0, 0 },
	.Name = "ZenWaterTrace"sv,
	.Author = "Zenderal"sv,
	.StructCompatibility = SKSE::StructCompatibility::Independent,
	.RuntimeCompatibility = SKSE::VersionIndependence::AddressLibrary)

namespace
{
	constexpr int kMaxSummaries = 4000;  // about 33 minutes of summaries
	constexpr int kMaxDetailLines = 6000;

	std::atomic<bool> g_busy{ false };
	std::atomic<bool> g_detail{ false };
	int               g_summaries{ 0 };
	int               g_dumps{ 0 };

	std::int64_t NowMs()
	{
		static const auto start = std::chrono::steady_clock::now();
		return std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - start).count();
	}

	RE::NiNode* WaterLODRoot()
	{
		// the same global Unified Water attaches its tiles to (gWaterLOD, UnifiedWater.cpp)
		static auto** root = reinterpret_cast<RE::NiNode**>(REL::RelocationID(516171, 402322).address());
		return root ? *root : nullptr;
	}

	RE::BSMultiBoundAABB* NodeAABB(RE::NiAVObject* a_obj)
	{
		auto* mbn = a_obj ? a_obj->AsMultiBoundNode() : nullptr;
		if (!mbn) {
			return nullptr;
		}
		auto& mb = mbn->GetRuntimeData().multiBound;
		if (!mb || !mb->data) {
			return nullptr;
		}
		auto* rtti = mb->data->GetRTTI();
		if (!rtti || std::string_view(rtti->GetName()) != "BSMultiBoundAABB"sv) {
			return nullptr;
		}
		return static_cast<RE::BSMultiBoundAABB*>(mb->data.get());
	}

	bool AABBInFrustum(const RE::BSMultiBoundAABB* a_box, RE::NiCamera* a_cam)
	{
		// sphere around the box: the engine tests the box itself, this is the looser test, so "out" here is surely out
		const RE::NiBound bound{ a_box->center, a_box->size.Length() };
		return RE::NiCamera::BoundInFrustum(bound, a_cam);
	}

	bool InsideAABB(const RE::NiPoint3& a_p, const RE::BSMultiBoundAABB* a_box)
	{
		constexpr float slack = 64.0f;
		return std::abs(a_p.x - a_box->center.x) <= std::abs(a_box->size.x) + slack &&
		       std::abs(a_p.y - a_box->center.y) <= std::abs(a_box->size.y) + slack;
	}

	RE::BSWaterShaderProperty* WaterProp(RE::NiAVObject* a_obj)
	{
		auto* geom = a_obj ? a_obj->AsGeometry() : nullptr;
		auto* prop = geom ? geom->GetGeometryRuntimeData().shaderProperty.get() : nullptr;
		if (!prop || !prop->GetRTTI() || std::string_view(prop->GetRTTI()->GetName()) != "BSWaterShaderProperty"sv) {
			return nullptr;
		}
		return static_cast<RE::BSWaterShaderProperty*>(prop);
	}

	// 1.5.0: which geometries the water shader actually set up for drawing, and when (render thread)
	using Setup_t = void (*)(RE::BSShader*, RE::BSRenderPass*, std::uint32_t);
	Setup_t                                                  g_setup = nullptr;
	std::mutex                                               g_drawMutex;
	std::unordered_map<const RE::BSGeometry*, std::int64_t> g_lastDraw;
	std::atomic<std::int64_t>                                g_draws{ 0 };

	void SetupHook(RE::BSShader* a_shader, RE::BSRenderPass* a_pass, std::uint32_t a_flags)
	{
		if (a_pass && a_pass->geometry) {
			const auto now = NowMs();
			std::scoped_lock lock(g_drawMutex);
			g_lastDraw[a_pass->geometry] = now;
		}
		++g_draws;
		g_setup(a_shader, a_pass, a_flags);
	}

	// drawn within the last a_ms milliseconds (a frame is ~10-30 ms; the trace ticks every 500)
	bool DrawnRecently(const RE::NiAVObject* a_obj, std::int64_t a_now, std::int64_t a_ms = 200)
	{
		std::scoped_lock lock(g_drawMutex);
		const auto       it = g_lastDraw.find(static_cast<const RE::BSGeometry*>(a_obj));
		return it != g_lastDraw.end() && a_now - it->second <= a_ms;
	}

	struct Totals
	{
		int nodes = 0, nodesHidden = 0, nodesOutBound = 0, nodesOutAABB = 0, nodesNoAABB = 0;
		int tiles = 0, tilesHidden = 0, tilesInView = 0, tilesInViewNodeOut = 0, tilesOutsideAABB = 0;
		int inViewDrawn = 0, inViewNotDrawn = 0, outViewDrawn = 0;
	};

	void Scan(RE::NiCamera* a_cam, bool a_detail, int& a_lines)
	{
		auto*  root = WaterLODRoot();
		Totals t;
		const auto now = NowMs();
		if (!root) {
			SKSE::log::info("{} ms: no LOD water root", NowMs());
			return;
		}
		for (auto& child : root->GetChildren()) {
			auto* node = child.get();
			if (!node) {
				continue;
			}
			++t.nodes;
			const bool nodeHidden = node->GetAppCulled();
			const bool boundIn = RE::NiCamera::BoundInFrustum(node->worldBound, a_cam);
			auto*      box = NodeAABB(node);
			const bool boxIn = box ? AABBInFrustum(box, a_cam) : true;
			t.nodesHidden += nodeHidden;
			t.nodesOutBound += !boundIn;
			t.nodesOutAABB += box && !boxIn;
			t.nodesNoAABB += !box;
			int nTiles = 0, nHidden = 0, nIn = 0, nInNodeOut = 0, nOutside = 0;
			auto* asNode = node->AsNode();
			if (asNode) {
				for (auto& tc : asNode->GetChildren()) {
					auto* tile = tc.get();
					if (!tile) {
						continue;
					}
					++nTiles;
					const bool hidden = tile->GetAppCulled();
					const bool in = RE::NiCamera::BoundInFrustum(tile->worldBound, a_cam);
					const bool outside = box && !InsideAABB(tile->world.translate, box);
					nHidden += hidden;
					nIn += in && !hidden;
					nInNodeOut += in && !hidden && (!boundIn || !boxIn);
					nOutside += outside;
					const bool drawn = DrawnRecently(tile, now);
					t.inViewDrawn += in && !hidden && drawn;
					t.inViewNotDrawn += in && !hidden && !drawn;
					t.outViewDrawn += !in && drawn;
					if (a_detail && a_lines < kMaxDetailLines) {
						++a_lines;
						const auto* wsp = WaterProp(tile);
						SKSE::log::info("    tile local ({:.0f},{:.0f},{:.0f}) x{:.0f} world ({:.0f},{:.0f},{:.0f}) bound r{:.0f}{}{}{}{} | {}",
							tile->local.translate.x, tile->local.translate.y, tile->local.translate.z, tile->local.scale,
							tile->world.translate.x, tile->world.translate.y, tile->world.translate.z, tile->worldBound.radius,
							hidden ? " HIDDEN" : "", in ? " in-view" : " out-of-view", outside ? " OUTSIDE-AABB" : "",
							drawn ? " drawn" : (in && !hidden ? " IN-VIEW-NOT-DRAWN" : " not-drawn"),
							wsp ? std::format("prop {} flags {:X} plane n({:.3f},{:.3f},{:.3f}) c {:.1f}", static_cast<const void*>(wsp),
									  wsp->waterFlags.underlying(), wsp->plane.normal.x, wsp->plane.normal.y, wsp->plane.normal.z, wsp->plane.constant) :
							      "no water property"s);
					}
				}
			}
			t.tiles += nTiles;
			t.tilesHidden += nHidden;
			t.tilesInView += nIn;
			t.tilesInViewNodeOut += nInNodeOut;
			t.tilesOutsideAABB += nOutside;
			if (a_detail && a_lines < kMaxDetailLines) {
				++a_lines;
				const auto* rtti = node->GetRTTI();
				SKSE::log::info("  node {} '{}'{} world ({:.0f},{:.0f},{:.0f}) bound ({:.0f},{:.0f},{:.0f}) r{:.0f} {} | "
				                "AABB {} | tiles {} hidden {} in-view {} in-view-but-node-out {} outside-AABB {}",
					rtti ? rtti->GetName() : "?", node->name.c_str() ? node->name.c_str() : "", nodeHidden ? " HIDDEN" : "",
					node->world.translate.x, node->world.translate.y, node->world.translate.z, node->worldBound.center.x,
					node->worldBound.center.y, node->worldBound.center.z, node->worldBound.radius, boundIn ? "bound-in" : "BOUND-OUT",
					box ? std::format("c({:.0f},{:.0f},{:.0f}) s({:.0f},{:.0f},{:.0f}) {}", box->center.x, box->center.y,
							  box->center.z, box->size.x, box->size.y, box->size.z, boxIn ? "in" : "OUT") :
					      "none"s,
					nTiles, nHidden, nIn, nInNodeOut, nOutside);
			}
		}
		const auto& cp = a_cam->world.translate;
		const auto  fwd = a_cam->world.rotate.GetVectorY();
		SKSE::log::info("{} ms{}: cam ({:.0f},{:.0f},{:.0f}) dir ({:.2f},{:.2f},{:.2f}) | root{} children {} | nodes {} hidden {} "
		                "bound-out {} AABB-out {} no-AABB {} | tiles {} hidden {} in-view {} IN-VIEW-NODE-OUT {} outside-AABB {} | "
		                "draws: in-view drawn {} IN-VIEW-NOT-DRAWN {} out-of-view drawn {} (water setups so far {})",
			NowMs(), a_detail ? " DETAIL" : "", cp.x, cp.y, cp.z, fwd.x, fwd.y, fwd.z, root->GetAppCulled() ? " HIDDEN" : "",
			root->GetChildren().size(), t.nodes, t.nodesHidden, t.nodesOutBound, t.nodesOutAABB, t.nodesNoAABB, t.tiles,
			t.tilesHidden, t.tilesInView, t.tilesInViewNodeOut, t.tilesOutsideAABB, t.inViewDrawn, t.inViewNotDrawn, t.outViewDrawn,
			g_draws.load());
	}

	void DumpCellsAndWaterObjects(RE::NiCamera* a_cam, int& a_lines)
	{
		auto* tes = RE::TES::GetSingleton();
		if (tes && tes->gridCells) {
			const auto len = tes->gridCells->length;
			for (std::uint32_t x = 0; x < len; ++x) {
				for (std::uint32_t y = 0; y < len; ++y) {
					auto* cell = tes->gridCells->GetCell(x, y);
					if (!cell || !cell->IsExteriorCell()) {
						continue;
					}
					const auto* c = cell->GetCoordinates();
					++a_lines;
					SKSE::log::info("  cell ({},{}) {:08X}{}{} water height {:.0f}", c ? c->cellX : 0, c ? c->cellY : 0,
						cell->GetFormID(), cell->IsAttached() ? " attached" : " not-attached",
						cell->cellFlags.any(RE::TESObjectCELL::Flag::kHasWater) ? " HasWater" : " no-water-flag",
						cell->GetExteriorWaterHeight());
				}
			}
		}
		auto* ws = RE::TESWaterSystem::GetSingleton();
		if (!ws) {
			return;
		}
		RE::BSSpinLockGuard guard(ws->lock);
		SKSE::log::info("  water system: enabled {} objects {}", ws->enabled, ws->waterObjects.size());
		for (auto& obj : ws->waterObjects) {
			if (!obj || a_lines >= kMaxDetailLines) {
				continue;
			}
			++a_lines;
			auto* shape = obj->shape.get();
			if (!shape) {
				SKSE::log::info("    water object: no shape, flags {:02X}", obj->flags);
				continue;
			}
			SKSE::log::info("    water object {:08X} flags {:02X} world ({:.0f},{:.0f},{:.0f}) r{:.0f}{} {} multibounds {}",
				obj->waterType ? obj->waterType->GetFormID() : 0, obj->flags, shape->world.translate.x, shape->world.translate.y,
				shape->world.translate.z, shape->worldBound.radius, shape->GetAppCulled() ? " HIDDEN" : "",
				RE::NiCamera::BoundInFrustum(shape->worldBound, a_cam) ? "in-view" : "out-of-view", obj->multiBounds.size());
		}
	}

	// Unified Water's disk cache (WaterCache.h): 32-byte header, 32-byte instructions; LOD4 entries are single cells
	std::unordered_set<std::uint64_t> g_cacheCells;
	bool                              g_cacheRead = false;

	std::uint64_t Key(std::int32_t a_x, std::int32_t a_y)
	{
		return (static_cast<std::uint64_t>(static_cast<std::uint32_t>(a_x)) << 32) | static_cast<std::uint32_t>(a_y);
	}

	void ReadCache(const RE::TESWorldSpace* a_ws)
	{
		if (g_cacheRead || !a_ws || a_ws->editorID.empty()) {
			return;
		}
		g_cacheRead = true;
		const auto    path = std::filesystem::path("Data/SKSE/Plugins/CommunityShaders/UnifiedWaterCache") / (std::string(a_ws->editorID.c_str()) + "_cache.wc");
		std::ifstream in(path, std::ios::binary);
		std::int32_t  hdr[8]{};
		if (!in.read(reinterpret_cast<char*>(hdr), sizeof(hdr))) {
			SKSE::log::info("coverage: no cache at {}", path.string());
			return;
		}
		struct Ins
		{
			std::uint32_t lod, pad;
			std::uint64_t form;
			std::int32_t  x, y;
			std::uint32_t size;
			float         h;
		} i{};
		while (in.read(reinterpret_cast<char*>(&i), sizeof(i))) {
			if (i.lod == 4 && i.size == 1) {
				g_cacheCells.insert(Key(i.x, i.y));
			}
		}
		SKSE::log::info("coverage: {} water cells in {}", g_cacheCells.size(), path.string());
	}

	int CellOf(float a_v) { return static_cast<int>(std::floor(a_v / 4096.0f)); }

	// Every cache water cell within kRadius cells of the camera that no shown tile covers, and what (if anything)
	// covers it while hidden. Loaded cells are left out: there the real cell water is drawn instead.
	void Coverage(RE::NiCamera* a_cam, int& a_lines)
	{
		constexpr int kRadius = 48;  // row-by-row listing; the per-chunk totals below cover the whole sea
		auto*         player = RE::PlayerCharacter::GetSingleton();
		auto*         root = WaterLODRoot();
		if (!root || !player) {
			return;
		}
		ReadCache(player->GetWorldspace());
		std::unordered_map<std::uint64_t, int> shown;  // cell -> how many shown tiles cover it
		std::unordered_set<std::uint64_t>      hiddenTile, hiddenNode;
		for (auto& child : root->GetChildren()) {
			auto* node = child ? child->AsNode() : nullptr;
			if (!node) {
				continue;
			}
			for (auto& tc : node->GetChildren()) {
				auto* tile = tc.get();
				if (!tile) {
					continue;
				}
				const float half = 2048.0f * tile->world.scale;
				const int   x0 = CellOf(tile->world.translate.x - half + 1.0f), x1 = CellOf(tile->world.translate.x + half - 1.0f);
				const int   y0 = CellOf(tile->world.translate.y - half + 1.0f), y1 = CellOf(tile->world.translate.y + half - 1.0f);
				for (int x = x0; x <= x1; ++x) {
					for (int y = y0; y <= y1; ++y) {
						if (node->GetAppCulled()) {
							hiddenNode.insert(Key(x, y));
						} else if (tile->GetAppCulled()) {
							hiddenTile.insert(Key(x, y));
						} else {
							++shown[Key(x, y)];
						}
					}
				}
			}
		}
		std::unordered_set<std::uint64_t> loaded;
		if (auto* tes = RE::TES::GetSingleton(); tes && tes->gridCells) {
			for (std::uint32_t x = 0; x < tes->gridCells->length; ++x) {
				for (std::uint32_t y = 0; y < tes->gridCells->length; ++y) {
					auto* cell = tes->gridCells->GetCell(x, y);
					if (const auto* c = cell && cell->IsAttached() ? cell->GetCoordinates() : nullptr) {
						loaded.insert(Key(c->cellX, c->cellY));
					}
				}
			}
		}
		const int cx = CellOf(a_cam->world.translate.x), cy = CellOf(a_cam->world.translate.y);
		int       none = 0, onlyHiddenTile = 0, onlyHiddenNode = 0, doubled = 0;
		for (int y = cy - kRadius; y <= cy + kRadius; ++y) {
			std::string row;  // runs of uncovered cells on this row, x from..to
			int         runStart = INT_MIN, runEnd = 0;
			char        runWhy = 0;
			const auto  flush = [&] {
				if (runStart != INT_MIN) {
					row += std::format(" {}..{}{}", runStart, runEnd, runWhy == 'n' ? "" : runWhy == 't' ? "(hidden tile)" : "(hidden node)");
					runStart = INT_MIN;
				}
			};
			for (int x = cx - kRadius; x <= cx + kRadius; ++x) {
				const auto k = Key(x, y);
				if (!g_cacheCells.contains(k) || loaded.contains(k)) {
					flush();
					continue;
				}
				const auto it = shown.find(k);
				if (it != shown.end()) {
					doubled += it->second > 1;
					flush();
					continue;
				}
				const char why = hiddenNode.contains(k) ? 'd' : hiddenTile.contains(k) ? 't' : 'n';
				none += why == 'n';
				onlyHiddenTile += why == 't';
				onlyHiddenNode += why == 'd';
				if (runStart != INT_MIN && (why != runWhy || x != runEnd + 1)) {
					flush();
				}
				if (runStart == INT_MIN) {
					runStart = x;
					runWhy = why;
				}
				runEnd = x;
			}
			flush();
			if (!row.empty() && a_lines < kMaxDetailLines) {
				++a_lines;
				SKSE::log::info("  uncovered y {}:{}", y, row);
			}
		}
		// 1.2.0: the whole cache, grouped by the LOD32 chunk of Vyn's grid (origin -69,-55), inside the terrain LOD only
		std::map<std::pair<int, int>, int> byChunk;
		int                                allNone = 0;
		for (const auto k : g_cacheCells) {
			const int x = static_cast<std::int32_t>(k >> 32), y = static_cast<std::int32_t>(k & 0xFFFFFFFF);
			if (x < -69 || x > 58 || y < -55 || y > 136 || loaded.contains(k) || shown.contains(k)) {
				continue;
			}
			++allNone;
			++byChunk[{ -69 + ((x + 69) / 32) * 32, -55 + ((y + 55) / 32) * 32 }];
		}
		for (const auto& [c, n] : byChunk) {
			SKSE::log::info("  whole sea: LOD32 chunk {},{}: {} uncovered cells", c.first, c.second, n);
		}
		SKSE::log::info("  whole sea (terrain LOD area): {} uncovered cells", allNone);
		SKSE::log::info("  coverage around camera cell ({},{}), radius {}: uncovered sea cells: no tile {} | only a hidden tile {} | "
		                "only in a hidden node {} | cells under 2+ shown tiles {}",
			cx, cy, kRadius, none, onlyHiddenTile, onlyHiddenNode, doubled);
	}

	// 1.3.0 EXPERIMENT (the trace's only writes): the curator sees Unified Water's tiles vanish while in view and come
	// back when the camera turns, with every tile present and in the frustum. F10 cycles how the engine may cull the
	// chunk water nodes under the LOD water root, so one launch shows which culling pass hides them.
	std::atomic<int> g_mode{ 0 };
	int              g_appliedMode = 0;

	struct Saved
	{
		RE::BSCullingProcess::BSCPCullingType cull;
		RE::NiPoint3                          center, size;
		bool                                  hasBox, alwaysDraw;
	};
	std::unordered_map<RE::NiAVObject*, Saved> g_saved;

	constexpr const char* kModeNames[] = { "0 off (as Unified Water leaves it)", "1 ignore multibounds", "2 cull all pass",
		"3 always draw", "4 tall AABB (+-8192)", "5 flat plane at each tile's height", "6 no Depth flag (0x4)", "7 no Refractions flag (0x80)" };
	std::unordered_map<RE::BSWaterShaderProperty*, std::uint32_t> g_savedFlags;
	std::unordered_map<RE::BSWaterShaderProperty*, RE::NiPlane> g_savedPlanes;

	void ApplyMode()
	{
		auto*     root = WaterLODRoot();
		const int mode = g_mode.load();
		if (!root) {
			return;
		}
		if (mode != g_appliedMode) {
			SKSE::log::info("experiment: mode {}", kModeNames[mode]);
			RE::SendHUDMessage::ShowHUDMessage(std::format("Water trace: mode {}", kModeNames[mode]).c_str(), nullptr, false);
			g_appliedMode = mode;
		}
		for (auto& child : root->GetChildren()) {
			auto* mbn = child ? child->AsMultiBoundNode() : nullptr;
			if (!mbn) {
				continue;
			}
			auto& rd = mbn->GetRuntimeData();
			auto* box = NodeAABB(mbn);
			auto  it = g_saved.find(mbn);
			if (it == g_saved.end()) {
				it = g_saved.emplace(mbn, Saved{ rd.cullingMode, box ? box->center : RE::NiPoint3{}, box ? box->size : RE::NiPoint3{},
											   box != nullptr, mbn->GetFlags().any(RE::NiAVObject::Flag::kAlwaysDraw) })
				         .first;
			}
			const auto& s = it->second;
			rd.cullingMode = mode == 1 ? RE::BSCullingProcess::BSCPCullingType::kIgnoreMultiBounds :
			                 mode == 2 ? RE::BSCullingProcess::BSCPCullingType::kAllPass :
			                             s.cull;
			const bool always = mode == 3 || s.alwaysDraw;
			const auto setAlways = [&](RE::NiAVObject* a_obj) {
				if (always) {
					a_obj->GetFlags().set(RE::NiAVObject::Flag::kAlwaysDraw);
				} else {
					a_obj->GetFlags().reset(RE::NiAVObject::Flag::kAlwaysDraw);
				}
			};
			setAlways(mbn);
			for (auto& tc : mbn->GetChildren()) {
				if (!tc) {
					continue;
				}
				setAlways(tc.get());
				if (auto* wsp = WaterProp(tc.get())) {
					const auto savedFlags = g_savedFlags.try_emplace(wsp, wsp->waterFlags.underlying()).first->second;
					std::uint32_t flags = savedFlags;
					if (mode == 6) {
						flags &= ~0x4u;
					} else if (mode == 7) {
						flags &= ~0x80u;
					}
					wsp->waterFlags = static_cast<RE::BSWaterShaderProperty::WaterFlag>(flags);
					const auto saved = g_savedPlanes.try_emplace(wsp, wsp->plane).first->second;
					if (mode == 5) {
						wsp->plane.normal = { 0.0f, 0.0f, 1.0f };
						wsp->plane.constant = tc->world.translate.z;
					} else {
						wsp->plane = saved;
					}
				}
			}
			if (box && s.hasBox) {
				box->center = s.center;
				box->size = s.size;
				if (mode == 4) {
					box->size.z = std::max(std::abs(s.size.z), 8192.0f);
				}
			}
		}
	}

	void Tick()
	{
		ApplyMode();
		auto* cam = RE::Main::WorldRootCamera();
		auto* player = RE::PlayerCharacter::GetSingleton();
		if (!cam || !player || !player->GetParentCell() || player->GetParentCell()->IsInteriorCell()) {
			return;
		}
		const bool detail = g_detail.exchange(false);
		if (!detail && g_summaries >= kMaxSummaries) {
			return;
		}
		int lines = 0;
		if (detail) {
			SKSE::log::info("==== F11 dump {} at {} ms ====", ++g_dumps, NowMs());
		}
		Scan(cam, detail, lines);
		++g_summaries;
		if (detail) {
			DumpCellsAndWaterObjects(cam, lines);
			Coverage(cam, lines);
			SKSE::log::info("==== end of dump {} ({} lines) ====", g_dumps, lines);
		}
	}

	void Loop()
	{
		bool f11Was = false;
		auto next = std::chrono::steady_clock::now();
		for (;;) {
			std::this_thread::sleep_for(std::chrono::milliseconds(20));
			const bool f11 = (GetAsyncKeyState(VK_F11) & 0x8000) != 0;
			if (f11 && !f11Was) {
				g_detail = true;
			}
			f11Was = f11;
			static bool f10Was = false;
			const bool  f10 = (GetAsyncKeyState(VK_F10) & 0x8000) != 0;
			if (f10 && !f10Was) {
				g_mode = (g_mode.load() + 1) % 8;
				g_detail = true;  // apply now (and dump, so the log has the state under each mode)
			}
			f10Was = f10;
			const auto now = std::chrono::steady_clock::now();
			if (now < next && !g_detail) {
				continue;
			}
			next = now + std::chrono::milliseconds(500);
			if (g_busy.exchange(true)) {
				continue;
			}
			SKSE::GetTaskInterface()->AddTask([] {
				Tick();
				g_busy = false;
			});
		}
	}
}

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	SKSE::log::info("ZenWaterTrace 1.6.0 loading, runtime {}", REL::Module::get().version().string());
	SKSE::GetMessagingInterface()->RegisterListener([](SKSE::MessagingInterface::Message* a_msg) {
		if (a_msg->type == SKSE::MessagingInterface::kDataLoaded) {
			// outermost wrapper: Unified Water and Horizon Fix hooked this slot earlier; their code still runs
			REL::Relocation<std::uintptr_t> vtbl{ RE::VTABLE_BSWaterShader[0] };
			g_setup = reinterpret_cast<Setup_t>(vtbl.write_vfunc(0x6, &SetupHook));
			SKSE::log::info("hooked BSWaterShader::SetupGeometry (previous {:X})", reinterpret_cast<std::uintptr_t>(g_setup));
			std::thread(Loop).detach();
		}
	});
	return true;
}
