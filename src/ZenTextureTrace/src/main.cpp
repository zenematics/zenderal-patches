#include "pch.h"

// Testing tool, not part of the list. Objects intermittently render untextured (a grey sack, a white plant): the files
// exist and are valid, and the same object is textured after a reload (curator, 2026-10-30). This tells apart "the
// texture never loaded" from "it loaded but is drawn wrong". Once a second, on the main thread (an SKSE task), it walks
// every placed reference within kRadius of the player and, for each BSLightingShaderProperty shape, checks the
// material's diffuse and normal NiSourceTexture: present, with a renderer texture and a shader resource view.
//   - A shape bad for kStuckMs is logged once as STUCK: ref, base form + plugin, model, shape, slot, the texture set's
//     path, the NiSourceTexture's own name and pointers.
//   - When a STUCK shape becomes good it is logged as RECOVERED with the time it took.
//   - Every 30 s a summary line (refs, shapes, bad now, stuck so far).
// If an object is untextured on screen while the log shows nothing for it, the texture is loaded and the fault is in
// how it is drawn. Reads only, never writes. Log: My Games/Skyrim Special Edition/SKSE/ZenTextureTrace.log

SKSEPluginInfo(
	.Version = REL::Version{ 1, 1, 0, 0 },
	.Name = "ZenTextureTrace"sv,
	.Author = "Zenderal"sv,
	.StructCompatibility = SKSE::StructCompatibility::Independent,
	.RuntimeCompatibility = SKSE::VersionIndependence::AddressLibrary)

namespace
{
	constexpr float        kRadius = 6000.0f;
	constexpr std::int64_t kStuckMs = 3000;
	constexpr std::int64_t kSummaryMs = 30000;
	constexpr int          kMaxLines = 50000;

	struct Entry
	{
		std::int64_t firstBad{ -1 };
		bool         logged{ false };
		std::int64_t seen{ 0 };
	};

	std::atomic<bool>                        g_busy{ false };
	std::unordered_map<std::uint64_t, Entry> g_entries;  // key: geometry pointer ^ slot
	std::int64_t                             g_scan{ 0 };
	std::int64_t                             g_nextSummary{ 0 };
	int                                      g_lines{ 0 };
	int                                      g_stuckTotal{ 0 };

	std::int64_t NowMs()
	{
		static const auto start = std::chrono::steady_clock::now();
		return std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - start).count();
	}

	template <class... Args>
	void Log(std::format_string<Args...> a_fmt, Args&&... a_args)
	{
		if (g_lines++ < kMaxLines) {
			SKSE::log::info("{}", std::format(a_fmt, std::forward<Args>(a_args)...));
		}
	}

	const char* Str(const char* a_s) { return a_s && *a_s ? a_s : "(none)"; }

	std::string FormLabel(const RE::TESForm* a_form)
	{
		if (!a_form) {
			return "(none)"s;
		}
		const auto* file = a_form->GetFile(0);
		return std::format("{:08X} [{}] {}", a_form->GetFormID(), Str(file ? file->fileName : nullptr),
			RE::FormTypeToString(a_form->GetFormType()));
	}

	// Shader resource view -> the texture names using it this scan. While a texture streams in, the engine binds a
	// shared placeholder, so one view used under many different names is a placeholder.
	std::unordered_map<const void*, std::unordered_map<std::string, int>> g_views;

	// Why a slot is bad, or empty if it is loaded. 1.1.0: a diffuse whose GPU texture is 8x8 or smaller is a stand-in
	// (1.0.0 only checked that a texture was bound, and a placeholder passes that).
	std::string_view BadReason(const RE::NiSourceTexture* a_tex, int a_slot)
	{
		if (!a_tex) {
			return "no texture object"sv;
		}
		if (!a_tex->rendererTexture) {
			return "no renderer texture"sv;
		}
		if (!a_tex->rendererTexture->resourceView) {
			return "no shader resource view"sv;
		}
		if (a_slot == 0 && a_tex->rendererTexture->width * a_tex->rendererTexture->height <= 64) {
			return "tiny GPU texture (placeholder?)"sv;
		}
		return {};
	}

	void CheckSlot(RE::TESObjectREFR* a_ref, RE::BSGeometry* a_geom, RE::BSLightingShaderMaterialBase* a_mat, int a_slot,
		std::int64_t a_now, int& a_badNow)
	{
		const RE::NiSourceTexture* tex = a_slot == 0 ? a_mat->diffuseTexture.get() : a_mat->normalTexture.get();
		const auto key = reinterpret_cast<std::uintptr_t>(a_geom) ^ static_cast<std::uint64_t>(a_slot);
		auto& e = g_entries[key];
		e.seen = g_scan;

		if (tex && tex->rendererTexture && tex->rendererTexture->resourceView) {
			++g_views[tex->rendererTexture->resourceView][Str(tex->name.c_str())];
		}
		const auto reason = BadReason(tex, a_slot);
		if (reason.empty()) {
			if (e.logged) {
				Log("RECOVERED after {:.1f} s: ref {:08X} shape '{}' slot {}", (a_now - e.firstBad) / 1000.0, a_ref->GetFormID(),
					Str(a_geom->name.c_str()), a_slot == 0 ? "diffuse"sv : "normal"sv);
			}
			e.firstBad = -1;
			e.logged = false;
			return;
		}
		++a_badNow;
		if (e.firstBad < 0) {
			e.firstBad = a_now;
		}
		if (e.logged || a_now - e.firstBad < kStuckMs) {
			return;
		}
		e.logged = true;
		++g_stuckTotal;

		const auto* base = a_ref->GetBaseObject();
		const auto* model = base ? base->As<RE::TESModel>() : nullptr;
		const char* setPath = nullptr;
		if (a_mat->textureSet) {
			setPath = a_mat->textureSet->GetTexturePath(a_slot == 0 ? RE::BSTextureSet::Texture::kDiffuse : RE::BSTextureSet::Texture::kNormal);
		}
		const auto* player = RE::PlayerCharacter::GetSingleton();
		const auto* rt = tex ? tex->rendererTexture : nullptr;
		Log("STUCK {:.1f} s: {} | ref {} base {} | model '{}' | shape '{}' slot {} | set path '{}' | tex name '{}' tex {} renderer {} gpu {}x{} mips {} view {} | dist {:.0f}",
			(a_now - e.firstBad) / 1000.0, reason, a_ref->GetFormID() ? std::format("{:08X}", a_ref->GetFormID()) : "(temp)"s,
			FormLabel(base), Str(model ? model->GetModel() : nullptr), Str(a_geom->name.c_str()), a_slot == 0 ? "diffuse"sv : "normal"sv,
			Str(setPath), Str(tex ? tex->name.c_str() : nullptr), static_cast<const void*>(tex), static_cast<const void*>(rt),
			rt ? rt->width : 0, rt ? rt->height : 0, rt ? rt->mips : 0, static_cast<const void*>(rt ? rt->resourceView : nullptr),
			player ? player->GetPosition().GetDistance(a_ref->GetPosition()) : -1.0f);
	}

	void Scan()
	{
		auto* player = RE::PlayerCharacter::GetSingleton();
		auto* tes = RE::TES::GetSingleton();
		if (!player || !tes || !player->Get3D()) {
			return;
		}
		const auto now = NowMs();
		++g_scan;
		g_views.clear();
		int refs = 0, shapes = 0, badNow = 0;

		tes->ForEachReferenceInRange(player, kRadius, [&](RE::TESObjectREFR* a_ref) {
			auto* root = a_ref ? a_ref->Get3D() : nullptr;
			if (!root || a_ref->IsDisabled()) {
				return RE::BSContainer::ForEachResult::kContinue;
			}
			++refs;
			RE::BSVisit::TraverseScenegraphGeometries(root, [&](RE::BSGeometry* a_geom) {
				if (a_geom->GetFlags().any(RE::NiAVObject::Flag::kHidden)) {
					return RE::BSVisit::BSVisitControl::kContinue;
				}
				auto* prop = a_geom->lightingShaderProp_cast();
				auto* mat = prop ? static_cast<RE::BSLightingShaderMaterialBase*>(prop->material) : nullptr;
				if (!mat) {
					return RE::BSVisit::BSVisitControl::kContinue;
				}
				++shapes;
				CheckSlot(a_ref, a_geom, mat, 0, now, badNow);
				CheckSlot(a_ref, a_geom, mat, 1, now, badNow);
				return RE::BSVisit::BSVisitControl::kContinue;
			});
			return RE::BSContainer::ForEachResult::kContinue;
		});

		std::erase_if(g_entries, [](const auto& a_kv) { return a_kv.second.seen != g_scan; });

		if (now >= g_nextSummary) {
			g_nextSummary = now + kSummaryMs;
			const auto* cell = player->GetParentCell();
			Log("summary: cell {} | {} refs, {} shapes in range | {} slots bad now | {} stuck so far", FormLabel(cell), refs, shapes, badNow,
				g_stuckTotal);
			// GPU views bound under several different texture names: a shared stand-in rather than a real texture.
			for (const auto& [view, names] : g_views) {
				if (names.size() < 3) {
					continue;
				}
				std::string list;
				int shown = 0;
				for (const auto& [name, count] : names) {
					if (shown++ < 6) {
						list += std::format("{}'{}' x{}", list.empty() ? "" : ", ", name, count);
					}
				}
				Log("  shared view {} used by {} different textures: {}{}", view, names.size(), list, names.size() > 6 ? ", ..." : "");
			}
		}
	}

	void Loop()
	{
		for (;;) {
			std::this_thread::sleep_for(std::chrono::milliseconds(1000));
			if (g_busy.exchange(true)) {
				continue;
			}
			SKSE::GetTaskInterface()->AddTask([] {
				Scan();
				g_busy = false;
			});
		}
	}
}

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	SKSE::log::info("ZenTextureTrace 1.1.0 loading, runtime {}", REL::Module::get().version().string());
	SKSE::GetMessagingInterface()->RegisterListener([](SKSE::MessagingInterface::Message* a_msg) {
		if (a_msg->type == SKSE::MessagingInterface::kDataLoaded) {
			std::thread(Loop).detach();
		}
	});
	return true;
}
