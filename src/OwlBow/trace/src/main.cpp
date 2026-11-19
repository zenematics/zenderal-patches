// Zenderal - Snowveil Trace (ZenSnowveilTrace.dll): TESTING TOOL, not part of the list. Read only.
//
// Snowveil's snowfall (enchant art on the bow) and its arrow's snow trail + wind (particles and effect shapes in the
// flight model) never showed in game (2026-11-17, three builds). Twice a second while Snowveil is equipped this logs:
//   * the bow's enchantment and its effects' enchant art / enchant shader (what the game will attach)
//   * every node in the player's 3P and 1P 3D whose name contains "OwlBowSnowFX" (the attached art): flags (hidden,
//     culled), world position, and per particle system: active particles, world space, world bound radius
//   * every projectile within 6000 units whose base is Snowveil's arrow projectile: its 3D root name (is it our
//     IceArrowFlight.nif?), each shape's name and flags, each particle system's active particles and bound
// Log: My Games/Skyrim Special Edition/SKSE/ZenSnowveilTrace.log

SKSEPluginInfo(
	.Version = REL::Version{ 1, 0, 0, 0 },
	.Name = "ZenSnowveilTrace"sv,
	.Author = "Zenderal"sv,
	.StructCompatibility = SKSE::StructCompatibility::Independent,
	.RuntimeCompatibility = SKSE::VersionIndependence::AddressLibrary)

namespace
{
	constexpr auto kPlugin = "Zenderal - Owl Bow.esp"sv;
	RE::TESObjectWEAP*  g_bow = nullptr;
	RE::BGSProjectile*  g_proj = nullptr;
	double              g_last = 0.0;
	std::set<RE::FormID> g_seenProj;

	double Now()
	{
		using namespace std::chrono;
		return duration<double>(steady_clock::now().time_since_epoch()).count();
	}

	std::string Flags(RE::NiAVObject* a)
	{
		auto f = a->GetFlags();
		std::string s;
		if (f.any(RE::NiAVObject::Flag::kHidden)) s += "hidden ";
		if (f.any(RE::NiAVObject::Flag::kDisableSorting)) s += "nosort ";
		return s.empty() ? "visible" : s;
	}

	void DumpTree(RE::NiAVObject* a, int depth, int maxDepth)
	{
		if (!a || depth > maxDepth) return;
		std::string line(depth * 2, ' ');
		line += fmt::format("{} '{}' [{}] pos ({:.0f},{:.0f},{:.0f}) scale {:.2f}", a->GetRTTI() ? a->GetRTTI()->GetName() : "?",
			a->name.c_str(), Flags(a), a->world.translate.x, a->world.translate.y, a->world.translate.z, a->world.scale);
		if (auto* ps = netimmerse_cast<RE::NiParticleSystem*>(a)) {
			auto& pd = ps->GetParticlesRuntimeData();
			int active = pd.particleData ? pd.particleData->GetActiveVertexCount() : -1;
			int maxn = pd.particleData ? pd.particleData->maxNumVertices : -1;
			line += fmt::format(" PSYS active {}/{} worldSpace {} bound r {:.1f}", active, maxn,
				ps->GetParticleSystemRuntimeData().isWorldspace, a->worldBound.radius);
		} else if (auto* g = a->AsGeometry()) {
			auto* sp = g->GetGeometryRuntimeData().shaderProperty.get();
			auto* ap = g->GetGeometryRuntimeData().alphaProperty.get();
			line += fmt::format(" GEOM shader {} alpha {}", sp && sp->GetRTTI() ? sp->GetRTTI()->GetName() : "none",
				ap ? fmt::format("flags {:04x}", ap->alphaFlags) : "none");
		}
		SKSE::log::info("{}", line);
		if (auto* n = a->AsNode()) {
			for (auto& c : n->GetChildren()) {
				DumpTree(c.get(), depth + 1, maxDepth);
			}
		}
	}

	void FindByName(RE::NiAVObject* a, std::string_view part, std::vector<RE::NiAVObject*>& out)
	{
		if (!a) return;
		std::string_view n{ a->name.c_str() };
		std::string ln(n), lp(part);
		std::transform(ln.begin(), ln.end(), ln.begin(), ::tolower);
		std::transform(lp.begin(), lp.end(), lp.begin(), ::tolower);
		if (ln.find(lp) != std::string::npos) out.push_back(a);
		if (auto* node = a->AsNode()) {
			for (auto& c : node->GetChildren()) FindByName(c.get(), part, out);
		}
	}

	void Tick(RE::PlayerCharacter* pc)
	{
		const double now = Now();
		if (now - g_last < 0.5) return;
		g_last = now;
		auto* wep = pc->GetEquippedObject(false);
		if (!g_bow || wep != g_bow) return;
		static bool once = false;
		if (!once) {
			once = true;
			auto* ench = g_bow->formEnchanting;
			SKSE::log::info("Snowveil enchantment: {}", ench ? fmt::format("{:08X} '{}', {} effects", ench->GetFormID(), ench->GetName(), ench->effects.size()) : "NONE");
			if (ench) {
				for (auto* e : ench->effects) {
					auto* m = e ? e->baseEffect : nullptr;
					if (!m) continue;
					SKSE::log::info("  effect {:08X} '{}': enchantShader {} enchantEffectArt {} hitEffectArt {} flags {:08X}", m->GetFormID(), m->GetName(),
						m->data.enchantShader ? fmt::format("{:08X}", m->data.enchantShader->GetFormID()) : "NULL",
						m->data.enchantEffectArt ? fmt::format("{:08X} '{}'", m->data.enchantEffectArt->GetFormID(), m->data.enchantEffectArt->model.c_str()) : "NULL",
						m->data.hitEffectArt ? fmt::format("{:08X}", m->data.hitEffectArt->GetFormID()) : "NULL",
						m->data.flags.underlying());
				}
			}
		}
		const bool drawn = pc->AsActorState()->IsWeaponDrawn();
		for (int fp = 0; fp < 2; ++fp) {
			auto* root = pc->Get3D(fp == 1);
			if (!root) continue;
			std::vector<RE::NiAVObject*> art;
			FindByName(root, "OwlBowSnowFX", art);
			SKSE::log::info("{} weapon drawn {}: OwlBowSnowFX nodes x{}", fp ? "1P" : "3P", drawn, art.size());
			for (auto* a : art) DumpTree(a, 1, 4);
		}
		auto* tes = RE::TES::GetSingleton();
		if (tes && g_proj) {
			tes->ForEachReferenceInRange(pc, 6000.0f, [&](RE::TESObjectREFR* ref) {
				if (ref && ref->GetBaseObject() == g_proj) {
					const bool first = g_seenProj.insert(ref->GetFormID()).second;
					auto* r3 = ref->Get3D();
					SKSE::log::info("projectile {:08X}{}: 3D {}", ref->GetFormID(), first ? " (new)" : "", r3 ? r3->name.c_str() : "NONE");
					if (r3) DumpTree(r3, 1, first ? 6 : 2);
				}
				return RE::BSContainer::ForEachResult::kContinue;
			});
		}
	}

	struct PlayerUpdate
	{
		static void thunk(RE::PlayerCharacter* a_this, float a_delta)
		{
			func(a_this, a_delta);
			Tick(a_this);
		}
		static inline REL::Relocation<decltype(thunk)> func;
	};
}

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	SKSE::log::info("ZenSnowveilTrace 1.0.0 loading, runtime {}", REL::Module::get().version().string());
	REL::Relocation<std::uintptr_t> playerVtbl{ RE::VTABLE_PlayerCharacter[0] };
	PlayerUpdate::func = playerVtbl.write_vfunc(0xAD, PlayerUpdate::thunk);
	SKSE::GetMessagingInterface()->RegisterListener([](SKSE::MessagingInterface::Message* a_msg) {
		if (a_msg->type == SKSE::MessagingInterface::kDataLoaded) {
			if (auto* dh = RE::TESDataHandler::GetSingleton()) {
				g_bow = dh->LookupForm<RE::TESObjectWEAP>(0x800, kPlugin);
				g_proj = dh->LookupForm<RE::BGSProjectile>(0x803, kPlugin);
			}
			SKSE::log::info("Snowveil {} / projectile {}", g_bow ? "found" : "NOT found", g_proj ? "found" : "NOT found");
		}
	});
	return true;
}
