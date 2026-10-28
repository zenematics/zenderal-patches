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
//     objects (loaded-cell water).
// Reads only, never changes a flag. Log: My Games/Skyrim Special Edition/SKSE/ZenWaterTrace.log

SKSEPluginInfo(
	.Version = REL::Version{ 1, 0, 0, 0 },
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

	struct Totals
	{
		int nodes = 0, nodesHidden = 0, nodesOutBound = 0, nodesOutAABB = 0, nodesNoAABB = 0;
		int tiles = 0, tilesHidden = 0, tilesInView = 0, tilesInViewNodeOut = 0, tilesOutsideAABB = 0;
	};

	void Scan(RE::NiCamera* a_cam, bool a_detail, int& a_lines)
	{
		auto*  root = WaterLODRoot();
		Totals t;
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
					if (a_detail && a_lines < kMaxDetailLines) {
						++a_lines;
						SKSE::log::info("    tile local ({:.0f},{:.0f},{:.0f}) x{:.0f} world ({:.0f},{:.0f},{:.0f}) bound r{:.0f}{}{}{}",
							tile->local.translate.x, tile->local.translate.y, tile->local.translate.z, tile->local.scale,
							tile->world.translate.x, tile->world.translate.y, tile->world.translate.z, tile->worldBound.radius,
							hidden ? " HIDDEN" : "", in ? " in-view" : " out-of-view", outside ? " OUTSIDE-AABB" : "");
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
		                "bound-out {} AABB-out {} no-AABB {} | tiles {} hidden {} in-view {} IN-VIEW-NODE-OUT {} outside-AABB {}",
			NowMs(), a_detail ? " DETAIL" : "", cp.x, cp.y, cp.z, fwd.x, fwd.y, fwd.z, root->GetAppCulled() ? " HIDDEN" : "",
			root->GetChildren().size(), t.nodes, t.nodesHidden, t.nodesOutBound, t.nodesOutAABB, t.nodesNoAABB, t.tiles,
			t.tilesHidden, t.tilesInView, t.tilesInViewNodeOut, t.tilesOutsideAABB);
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

	void Tick()
	{
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
	SKSE::log::info("ZenWaterTrace 1.0.0 loading, runtime {}", REL::Module::get().version().string());
	SKSE::GetMessagingInterface()->RegisterListener([](SKSE::MessagingInterface::Message* a_msg) {
		if (a_msg->type == SKSE::MessagingInterface::kDataLoaded) {
			std::thread(Loop).detach();
		}
	});
	return true;
}
