#include "pch.h"

#include <detours/detours.h>

// Bottled Shaders' Unified Water (a Community Shaders feature) replaces distant LOD water with its own tiles. When a
// terrain LOD chunk attaches, it looks the chunk up in its cache with WaterCache::GetLODCoords, which divides the
// chunk's base cell by the LOD level: it assumes chunks start at multiples of their size, as Tamriel's do. Vyn's LOD
// grid starts at cell -69, -55 (lodsettings\vyn.lod), so every chunk got the tiles of a different, 0-aligned chunk
// that only partly overlaps it. Those tiles hang under the wrong node and vanish with it as the camera turns, and
// where chunks of different LOD levels meet, cells get water twice or not at all (ZenWaterTrace, 2026-10-28).
//
// This runs after Unified Water's own attach hook (Detours chains onto it). For a chunk whose base cell is not a
// multiple of its LOD level, it throws away the tiles Unified Water made and builds them again, the way Unified Water
// does, from Unified Water's own disk cache (<worldspace>_cache.wc, the per-cell LOD4 entries), for the chunk's real
// cells. Aligned chunks (every Tamriel chunk) are left alone. Nothing is written to disk.

SKSEPluginInfo(
	.Version = REL::Version{ 1, 0, 0, 0 },
	.Name = "ZenUnifiedWaterGrid"sv,
	.Author = "Zenderal"sv,
	.StructCompatibility = SKSE::StructCompatibility::Independent,
	.RuntimeCompatibility = SKSE::VersionIndependence::AddressLibrary)

namespace
{
	// Unified Water's on-disk layout (WaterCache.h): a 32-byte header, then 32-byte instructions
	struct CacheHeader
	{
		std::uint32_t label;
		std::int32_t  width, height, minX, minY, maxX, maxY, dataCount;
	};
	static_assert(sizeof(CacheHeader) == 32);

	struct CacheInstruction
	{
		std::uint32_t lodLevel;
		std::uint32_t pad;
		std::uint64_t form;  // runtime FormID in the low 32 bits on disk
		std::int32_t  x, y;
		std::uint32_t size;
		float         waterHeight;
	};
	static_assert(sizeof(CacheInstruction) == 32);

	struct CellWater
	{
		RE::FormID formID;
		float      height;
	};

	struct WorldCache
	{
		std::filesystem::file_time_type             stamp{};
		bool                                        loaded = false;
		std::unordered_map<std::uint64_t, CellWater> cells;  // key = (x, y)
	};

	using Attach_t = void (*)(RE::BGSTerrainBlock*);
	Attach_t g_attach = nullptr;

	RE::NiPointer<RE::BSTriShape>              g_mesh;
	std::unordered_map<std::string, WorldCache> g_caches;
	int                                        g_rebuilt = 0;
	int                                        g_logged = 0;

	std::uint64_t Key(std::int32_t a_x, std::int32_t a_y)
	{
		return (static_cast<std::uint64_t>(static_cast<std::uint32_t>(a_x)) << 32) | static_cast<std::uint32_t>(a_y);
	}

	int Mod(int a_v, int a_m)
	{
		const int r = a_v % a_m;
		return r < 0 ? r + a_m : r;
	}

	RE::NiNode* WaterLODRoot()
	{
		// the global Unified Water parents its tiles to (gWaterLOD, UnifiedWater.cpp)
		static auto** root = reinterpret_cast<RE::NiNode**>(REL::RelocationID(516171, 402322).address());
		return root ? *root : nullptr;
	}

	const WorldCache* GetCache(const RE::TESWorldSpace* a_ws)
	{
		if (!a_ws || a_ws->editorID.empty()) {
			return nullptr;
		}
		const std::string name = a_ws->editorID.c_str();
		const std::filesystem::path path = std::filesystem::path("Data/SKSE/Plugins/CommunityShaders/UnifiedWaterCache") / (name + "_cache.wc");
		std::error_code ec;
		const auto stamp = std::filesystem::last_write_time(path, ec);
		auto& cache = g_caches[name];
		if (ec) {
			cache.loaded = false;
			return nullptr;
		}
		if (cache.loaded && cache.stamp == stamp) {
			return &cache;
		}
		// (re)read: first use, or Unified Water rebuilt the cache this session
		cache = {};
		std::ifstream in(path, std::ios::binary);
		CacheHeader   hdr{};
		if (!in.read(reinterpret_cast<char*>(&hdr), sizeof(hdr)) || hdr.label != 'HCTW' || hdr.dataCount < 0) {
			SKSE::log::error("{}: unreadable cache header ({})", name, path.string());
			return nullptr;
		}
		std::vector<CacheInstruction> ins(static_cast<std::size_t>(hdr.dataCount));
		if (!in.read(reinterpret_cast<char*>(ins.data()), static_cast<std::streamsize>(ins.size() * sizeof(CacheInstruction)))) {
			SKSE::log::error("{}: cache shorter than its {} instructions", name, hdr.dataCount);
			return nullptr;
		}
		for (const auto& i : ins) {
			if (i.lodLevel == 4 && i.size == 1) {  // LOD4 is never merged: one entry per water cell
				cache.cells[Key(i.x, i.y)] = { static_cast<RE::FormID>(i.form & 0xFFFFFFFF), i.waterHeight };
			}
		}
		cache.stamp = stamp;
		cache.loaded = true;
		SKSE::log::info("{}: read {} water cells from Unified Water's cache (bounds {},{} to {},{})", name, cache.cells.size(),
			hdr.minX, hdr.minY, hdr.maxX, hdr.maxY);
		return &cache;
	}

	struct Tile
	{
		std::int32_t      x, y, size;
		float             height;
		RE::TESWaterForm* form;
	};

	// Unified Water's GenerateInstructions merge, on the chunk's real cells: greedy squares of equal height and form
	std::vector<Tile> BuildTiles(const WorldCache& a_cache, std::int32_t a_bx, std::int32_t a_by, std::int32_t a_lod)
	{
		std::vector<Tile> out;
		std::vector<bool> done(static_cast<std::size_t>(a_lod * a_lod), false);
		const auto        at = [&](int lx, int ly) -> const CellWater* {
            const auto it = a_cache.cells.find(Key(a_bx + lx, a_by + ly));
            return it == a_cache.cells.end() ? nullptr : &it->second;
		};
		for (int ly = 0; ly < a_lod; ++ly) {
			for (int lx = 0; lx < a_lod; ++lx) {
				if (done[ly * a_lod + lx]) {
					continue;
				}
				done[ly * a_lod + lx] = true;
				const auto* c = at(lx, ly);
				if (!c) {
					continue;
				}
				auto* form = RE::TESForm::LookupByID<RE::TESWaterForm>(c->formID);
				if (!form || form->GetFormType() != RE::FormType::Water) {
					continue;
				}
				int size = 1;
				if (a_lod > 4) {  // LOD4 tiles stay single cells: they are hidden one by one as real cells load
					const int maxSize = std::min(a_lod - lx, a_lod - ly);
					for (int cand = 2; cand <= maxSize; ++cand) {
						bool ok = true;
						for (int d = 0; d < cand && ok; ++d) {
							for (const auto [qx, qy] : { std::pair{ lx + d, ly + cand - 1 }, std::pair{ lx + cand - 1, ly + d } }) {
								const auto* q = at(qx, qy);
								if (done[qy * a_lod + qx] || !q || q->height != c->height || q->formID != c->formID) {
									ok = false;
									break;
								}
							}
						}
						if (!ok) {
							break;
						}
						size = cand;
					}
				}
				for (int yy = ly; yy < ly + size; ++yy) {
					for (int xx = lx; xx < lx + size; ++xx) {
						done[yy * a_lod + xx] = true;
					}
				}
				out.push_back({ a_bx + lx, a_by + ly, size, c->height, form });
			}
		}
		return out;
	}

	void DropChildren(RE::BSMultiBoundNode* a_water, bool a_unregister)
	{
		auto* ws = RE::TESWaterSystem::GetSingleton();
		auto  count = a_water->GetChildren().size();
		while (count > 0) {
			const auto child = a_water->GetChildren()[count - 1];
			if (child && a_unregister && ws) {
				ws->RemoveWater(child.get());
			}
			a_water->DetachChildAt(static_cast<std::uint32_t>(--count));
		}
	}

	// UpdateWaterMeshSubVisibility's rule (UnifiedWater.cpp): a LOD4 tile over a loaded cell with water is hidden
	void CullOverLoadedCells(RE::BSMultiBoundNode* a_water)
	{
		auto* tes = RE::TES::GetSingleton();
		if (!tes || !tes->gridCells) {
			return;
		}
		const auto& grid = tes->gridCells;
		const int   len = static_cast<int>(grid->length);
		const int   offX = tes->currentGridX - (len >> 1);
		const int   offY = tes->currentGridY - (len >> 1);
		for (const auto& child : a_water->GetChildren()) {
			if (!child) {
				continue;
			}
			const int x = static_cast<int>(std::floor(child->world.translate.x / 4096.0f)) - offX;
			const int y = static_cast<int>(std::floor(child->world.translate.y / 4096.0f)) - offY;
			bool      cull = false;
			if (x >= 0 && y >= 0 && x < len && y < len) {
				if (const auto cell = grid->GetCell(x, y); cell && cell->cellState.any(RE::TESObjectCELL::CellState::kAttached, static_cast<RE::TESObjectCELL::CellState>(6))) {
					cull = cell->cellFlags.any(RE::TESObjectCELL::Flag::kHasWater);
				}
			}
			child->SetAppCulled(cull);
		}
	}

	void Rebuild(RE::BGSTerrainBlock* a_block)
	{
		auto* node = a_block->node;
		auto* water = a_block->water;
		if (!node || !water || !a_block->chunk || !g_mesh || !node->manager) {
			return;
		}
		const int lod = static_cast<int>(node->GetLODLevel());
		if (lod < 4 || lod > 32) {
			return;
		}
		const int bx = node->baseCellX;
		const int by = node->baseCellY;
		if (Mod(bx, lod) == 0 && Mod(by, lod) == 0) {
			return;  // Unified Water's lookup is right for aligned chunks
		}
		const auto* cache = GetCache(node->manager->worldSpace);
		if (!cache) {
			return;
		}
		auto* root = WaterLODRoot();
		if (!root) {
			return;
		}
		const auto tiles = BuildTiles(*cache, bx, by, lod);
		const bool owned = a_block->waterAttached;  // Unified Water took the node (it is under the LOD water root)
		if (tiles.empty()) {
			if (owned) {
				DropChildren(water, false);  // its tiles were for another chunk; this one has no water
			}
			return;
		}

		RE::NiPointer<RE::BSMultiBoundNode> keep(water);
		if (owned) {
			DropChildren(water, false);  // Unified Water already took its tiles out of the water system
		} else {
			// Unified Water found nothing for the wrong chunk and left the node on the terrain chunk: take it the same way
			a_block->chunk->DetachChild2(water);
			water->local.translate = a_block->chunk->local.translate;
			DropChildren(water, true);
		}

		std::vector<RE::BSTriShape*> built;
		built.reserve(tiles.size());
		float lo = FLT_MAX, hi = -FLT_MAX;
		for (const auto& t : tiles) {
			RE::NiCloningProcess cloning;
			auto*                clone = g_mesh->CreateClone(cloning);
			auto*                shape = clone ? static_cast<RE::NiAVObject*>(clone)->AsTriShape() : nullptr;
			if (!shape) {
				continue;
			}
			shape->local.scale = static_cast<float>(t.size);
			shape->local.translate = { (t.x - bx) * 4096.0f + t.size * 2048.0f, (t.y - by) * 4096.0f + t.size * 2048.0f, t.height };
			water->AttachChild(shape, true);
			built.push_back(shape);
			lo = std::min(lo, t.height);
			hi = std::max(hi, t.height);
		}

		auto* ws = RE::TESWaterSystem::GetSingleton();
		{
			RE::BSSpinLockGuard guard(ws->lock);
			ws->waterObjects.reserve(ws->waterObjects.size() + static_cast<std::uint32_t>(built.size()));
		}
		for (std::size_t i = 0; i < built.size(); ++i) {
			auto*       shape = built[i];
			const auto& t = tiles[i];
			ws->AddWater(shape, t.form, t.height, nullptr, true, false);
			if (const auto prop = shape->GetGeometryRuntimeData().shaderProperty.get(); prop && prop->GetRTTI() &&
				std::string_view(prop->GetRTTI()->GetName()) == "BSWaterShaderProperty"sv) {
				auto*                                                              wsp = static_cast<RE::BSWaterShaderProperty*>(prop);
				REX::EnumSet<RE::BSWaterShaderProperty::WaterFlag, std::uint32_t> flags = static_cast<RE::BSWaterShaderProperty::WaterFlag>(0b10000100);
				flags.set(RE::BSWaterShaderProperty::WaterFlag::kUseCubemapReflections, RE::BSWaterShaderProperty::WaterFlag::kUseReflections);
				if (t.form->flags.any(RE::TESWaterForm::Flag::kEnableFlowmap)) {
					flags.set(RE::BSWaterShaderProperty::WaterFlag::kEnableFlowmap);
				}
				if (t.form->flags.any(RE::TESWaterForm::Flag::kBlendNormals)) {
					flags.set(RE::BSWaterShaderProperty::WaterFlag::kBlendNormals);
				}
				wsp->waterFlags = flags;
			}
			// Unified Water manages its tiles itself: take the object AddWater just appended off the list again
			RE::BSSpinLockGuard guard(ws->lock);
			if (!ws->waterObjects.empty()) {
				ws->waterObjects.pop_back();
			}
		}

		// the node's multibound (from the .btr) covers this chunk at one height; stretch it over lake heights too
		if (auto* mbn = water->AsMultiBoundNode(); mbn && !built.empty()) {
			auto& mb = mbn->GetRuntimeData().multiBound;
			if (mb && mb->data && mb->data->GetRTTI() && std::string_view(mb->data->GetRTTI()->GetName()) == "BSMultiBoundAABB"sv) {
				auto*       box = static_cast<RE::BSMultiBoundAABB*>(mb->data.get());
				const float bLo = box->center.z - std::abs(box->size.z);
				const float bHi = box->center.z + std::abs(box->size.z);
				if (lo < bLo || hi > bHi) {
					const float nLo = std::min(lo, bLo), nHi = std::max(hi, bHi);
					box->center.z = (nLo + nHi) * 0.5f;
					box->size.z = (nHi - nLo) * 0.5f;
				}
			}
		}

		if (!owned) {
			root->AttachChild(water, true);
			a_block->waterAttached = true;
		}
		RE::NiUpdateData update;
		water->Update(update);
		if (lod == 4) {
			CullOverLoadedCells(water);
		}
		ws->Enable();

		++g_rebuilt;
		if (g_logged < 12) {
			++g_logged;
			SKSE::log::info("LOD{} chunk at cell {},{}: {} tiles rebuilt on the real grid ({})", lod, bx, by, built.size(),
				owned ? "replaced Unified Water's" : "Unified Water had none");
		} else if (g_rebuilt % 500 == 0) {
			SKSE::log::info("{} chunks rebuilt so far", g_rebuilt);
		}
	}

	void AttachHook(RE::BGSTerrainBlock* a_block)
	{
		const bool wasAttached = a_block && a_block->attached;
		g_attach(a_block);  // Unified Water's hook, then the game's own attach
		if (a_block && !wasAttached && a_block->attached) {
			Rebuild(a_block);
		}
	}

	bool LoadMesh()
	{
		// the same mesh and load arguments Unified Water uses (UnifiedWater::DataLoaded)
		auto args = RE::BSModelDB::DBTraits::ArgsType();
		args.unk8 = false;
		args.unkA = false;
		args.postProcess = false;
		RE::NiPointer<RE::NiNode> nif;
		if (RE::BSModelDB::Demand("meshes\\water\\watermesh.nif", nif, args) != RE::BSResource::ErrorCode::kNone || !nif ||
			nif->GetChildren().empty() || !nif->GetChildren().front() || !nif->GetChildren().front()->AsNode()) {
			return false;
		}
		auto* inner = nif->GetChildren().front()->AsNode();
		if (inner->GetChildren().empty() || !inner->GetChildren().front()) {
			return false;
		}
		g_mesh = RE::NiPointer<RE::BSTriShape>(inner->GetChildren().front()->AsTriShape());
		return g_mesh != nullptr;
	}

	void Install()
	{
		if (!GetModuleHandleW(L"CommunityShaders.dll")) {
			SKSE::log::info("CommunityShaders.dll not loaded; nothing to fix");
			return;
		}
		if (!LoadMesh()) {
			SKSE::log::error("could not load meshes\\water\\watermesh.nif; not installing");
			return;
		}
		const auto target = REL::RelocationID(30934, 31737).address();
		const auto* bytes = reinterpret_cast<const std::uint8_t*>(target);
		const bool  hooked = bytes[0] == 0xE9 || (bytes[0] == 0xFF && bytes[1] == 0x25);
		if (!hooked) {
			// without Unified Water's hook there is nothing to correct (Unified Water off, or its mesh failed)
			SKSE::log::info("BGSTerrainBlock::Attach is not hooked (first byte {:02X}): Unified Water inactive, not installing", bytes[0]);
			return;
		}
		g_attach = reinterpret_cast<Attach_t>(target);
		DetourTransactionBegin();
		DetourUpdateThread(GetCurrentThread());
		DetourAttach(reinterpret_cast<PVOID*>(&g_attach), reinterpret_cast<PVOID>(&AttachHook));
		const auto err = DetourTransactionCommit();
		SKSE::log::info("hooked BGSTerrainBlock::Attach after Unified Water: {}", err == NO_ERROR ? "ok"sv : "FAILED"sv);
	}
}

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	SKSE::log::info("ZenUnifiedWaterGrid 1.0.0 loading, runtime {}", REL::Module::get().version().string());
	SKSE::GetMessagingInterface()->RegisterListener([](SKSE::MessagingInterface::Message* a_msg) {
		if (a_msg->type == SKSE::MessagingInterface::kDataLoaded) {
			Install();
		}
	});
	return true;
}
