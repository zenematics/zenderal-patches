#include "pch.h"

#include <chrono>
#include <ctime>
#include <mutex>
#include <unordered_map>

// Testing tool, not part of the list (2026-11-11). Enemies holding a flintlock pistol reload through
// ZP_PistolReloadArmNPCEffect, which starts the reload cast the way the player's script does (bWantCast<side>,
// M?h_SpellAimedStart, M?h_SpellRelease_Event). For NPCs the graph mostly refuses it (seventh test: every kick refused,
// bWantCast already false) and Papyrus cannot see why. For every non-player actor (the Character vtable) holding a
// pistol (Pistol_Animation_By_Loop 0x801 on the weapon in either hand), this logs:
//   IN    every event sent into its behaviour graph (IAnimationGraphManagerHolder::NotifyAnimationGraph), accepted or
//         not; M?h_ / cast events with a VARS snapshot;
//   OUT   every event the graph sends back (BSTEventSink<BSAnimationGraphEvent>), footsteps left out;
//   VARS  bWantCast, IsCasting, each hand's MagicCaster state, the reload request, hand types, item charge, attacking,
//         blocking, staggering: whenever any of them changes (10 Hz sample from Actor::Update);
//   NODES the magic-related active nodes of its behaviour graph (names with mlh/mrh/magic/cast/stf/staff/spell/ready/
//         release/equip), descending into behaviour references: what entered (+) and left (-) since the last sample.
// Every line starts with the local wall-clock time, to line up with the Papyrus log's [ZP PistolReload NPC] lines.
// Log: My Games/Skyrim Special Edition/SKSE/ZenPistolNPCTrace.log

SKSEPluginInfo(
	.Version = REL::Version{ 1, 0, 0, 0 },
	.Name = "ZenPistolNPCTrace"sv,
	.Author = "Zenderal"sv,
	.StructCompatibility = SKSE::StructCompatibility::Independent,
	.RuntimeCompatibility = SKSE::VersionIndependence::AddressLibrary)

namespace
{
	constexpr std::int64_t kSampleEveryMs = 100;
	constexpr std::array   kNodeWords{ "mlh"sv, "mrh"sv, "magic"sv, "cast"sv, "stf"sv, "staff"sv, "spell"sv, "ready"sv,
		"release"sv, "equip"sv };
	constexpr std::array   kQuietOut{ "FootLeft"sv, "FootRight"sv, "FootFront"sv, "FootBack"sv, "FootSprintLeft"sv,
		"FootSprintRight"sv, "FootScuffLeft"sv, "FootScuffRight"sv };

	struct Trace
	{
		std::int64_t             lastSampleMs{ 0 };
		std::string              vars;
		std::vector<std::string> nodes;
	};

	std::mutex                                  g_lock;
	std::unordered_map<RE::FormID, Trace>       g_traces;
	RE::BGSKeyword*                             g_pistol{ nullptr };
	std::uintptr_t                              g_refGenVtbl{ 0 };
	std::uintptr_t                              g_graphVtbl{ 0 };
	const std::chrono::steady_clock::time_point g_start = std::chrono::steady_clock::now();

	std::int64_t NowMs()
	{
		return std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - g_start).count();
	}

	std::string Clock()
	{
		const auto        now = std::chrono::system_clock::now();
		const std::time_t t = std::chrono::system_clock::to_time_t(now);
		std::tm           tm{};
		localtime_s(&tm, &t);
		const auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(now.time_since_epoch()).count() % 1000;
		return std::format("{:02}:{:02}:{:02}.{:03}", tm.tm_hour, tm.tm_min, tm.tm_sec, ms);
	}

	bool PistolIn(RE::Actor* a_actor, bool a_left)
	{
		auto* obj = a_actor->GetEquippedObject(a_left);
		auto* weap = obj ? obj->As<RE::TESObjectWEAP>() : nullptr;
		return weap && g_pistol && weap->HasKeyword(g_pistol);
	}

	bool HasPistol(RE::Actor* a_actor)
	{
		return a_actor && !a_actor->IsPlayerRef() && (PistolIn(a_actor, true) || PistolIn(a_actor, false));
	}

	bool Bool(RE::Actor* a_actor, std::string_view a_name)
	{
		bool v = false;
		a_actor->GetGraphVariableBool(a_name, v);
		return v;
	}

	float Float(RE::Actor* a_actor, std::string_view a_name)
	{
		float v = 0.0f;
		a_actor->GetGraphVariableFloat(a_name, v);
		return v;
	}

	int Int(RE::Actor* a_actor, std::string_view a_name)
	{
		std::int32_t v = 0;
		a_actor->GetGraphVariableInt(a_name, v);
		return v;
	}

	int CasterState(RE::Actor* a_actor, RE::MagicSystem::CastingSource a_source)
	{
		auto* caster = a_actor->GetMagicCaster(a_source);
		return caster ? static_cast<int>(caster->state.underlying()) : -1;
	}

	std::string Vars(RE::Actor* a_actor)
	{
		auto* av = a_actor->AsActorValueOwner();
		return std::format("L: want={} casting={} caster={} req={:.0f} type={} charge={:.1f} gun={} | R: want={} casting={} "
						   "caster={} req={:.0f} type={} charge={:.1f} gun={} | attacking={} blocking={} stagger={} combat={}",
			Bool(a_actor, "bWantCastLeft"sv), Bool(a_actor, "IsCastingLeft"sv),
			CasterState(a_actor, RE::MagicSystem::CastingSource::kLeftHand), Float(a_actor, "fZenPistolReloadL"sv),
			Int(a_actor, "iLeftHandType"sv), av->GetActorValue(RE::ActorValue::kLeftItemCharge), PistolIn(a_actor, true),
			Bool(a_actor, "bWantCastRight"sv), Bool(a_actor, "IsCastingRight"sv),
			CasterState(a_actor, RE::MagicSystem::CastingSource::kRightHand), Float(a_actor, "fZenPistolReloadR"sv),
			Int(a_actor, "iRightHandType"sv), av->GetActorValue(RE::ActorValue::kRightItemCharge), PistolIn(a_actor, false),
			Bool(a_actor, "IsAttacking"sv), Bool(a_actor, "IsBlocking"sv), Bool(a_actor, "IsStaggering"sv), a_actor->IsInCombat());
	}

	bool NodeOfInterest(std::string_view a_name)
	{
		std::string lower{ a_name };
		std::ranges::transform(lower, lower.begin(), [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
		return std::ranges::any_of(kNodeWords, [&](std::string_view w) { return lower.find(w) != std::string::npos; });
	}

	std::uintptr_t Vtbl(const void* a_obj)
	{
		return a_obj ? *reinterpret_cast<const std::uintptr_t*>(a_obj) : 0;
	}

	// hkbBehaviorReferenceGenerator (not in CommonLib): hkbGenerator (0x48), hkStringPtr behaviorName 0x48,
	// hkbBehaviorGraph* behavior 0x50 (Havok's layout); only followed when that pointer's vtable is hkbBehaviorGraph's
	void CollectNodes(RE::hkbBehaviorGraph* a_graph, std::vector<std::string>& a_out, int a_depth)
	{
		if (!a_graph || Vtbl(a_graph) != g_graphVtbl || !a_graph->activeNodes || a_depth > 6) {
			return;
		}
		auto& nodes = *a_graph->activeNodes;
		for (std::int32_t i = 0; i < static_cast<std::int32_t>(nodes.size()); ++i) {
			const auto& info = nodes[i];
			auto*       node = info.nodeTemplate ? info.nodeTemplate : info.nodeClone;
			if (node) {
				const char* name = node->name.c_str();
				if (name && NodeOfInterest(name)) {
					a_out.emplace_back(a_depth ? std::format("{}:{}", a_depth, name) : std::string{ name });
				}
			}
			auto* clone = info.nodeClone ? info.nodeClone : info.nodeTemplate;
			if (clone && Vtbl(clone) == g_refGenVtbl) {
				auto* sub = *reinterpret_cast<RE::hkbBehaviorGraph**>(reinterpret_cast<std::uintptr_t>(clone) + 0x50);
				CollectNodes(sub, a_out, a_depth + 1);
			}
		}
	}

	std::vector<std::string> ActiveNodes(RE::Actor* a_actor)
	{
		std::vector<std::string>                         out;
		RE::BSTSmartPointer<RE::BSAnimationGraphManager> manager;
		if (!a_actor->GetAnimationGraphManager(manager) || !manager) {
			return out;
		}
		auto&                rd = manager->GetRuntimeData();
		RE::BSSpinLockGuard  locker(rd.updateLock);
		const auto           index = rd.activeGraph;
		if (index >= manager->graphs.size() || !manager->graphs[index]) {
			return out;
		}
		CollectNodes(manager->graphs[index]->behaviorGraph, out, 0);
		std::ranges::sort(out);
		out.erase(std::unique(out.begin(), out.end()), out.end());
		return out;
	}

	std::string Who(RE::Actor* a_actor)
	{
		return std::format("{:08X} '{}'", a_actor->GetFormID(), a_actor->GetName());
	}

	bool IsCastEvent(std::string_view a_name)
	{
		return a_name.starts_with("MLh_"sv) || a_name.starts_with("MRh_"sv) || a_name.find("Cast"sv) != std::string_view::npos;
	}

	struct NotifyAnimationGraph
	{
		static bool thunk(RE::IAnimationGraphManagerHolder* a_this, const RE::BSFixedString& a_eventName)
		{
			const bool result = func(a_this, a_eventName);
			auto*      actor = static_cast<RE::TESObjectREFR*>(a_this)->As<RE::Actor>();
			if (HasPistol(actor)) {
				const std::string_view name{ a_eventName.c_str() ? a_eventName.c_str() : "" };
				SKSE::log::info("{} {} IN    {}{}{}", Clock(), Who(actor), name, result ? "" : "  (NOT ACCEPTED)",
					IsCastEvent(name) ? "  | " + Vars(actor) : ""s);
			}
			return result;
		}
		static inline REL::Relocation<decltype(thunk)> func;
	};

	struct GraphEventSink
	{
		static RE::BSEventNotifyControl thunk(RE::BSTEventSink<RE::BSAnimationGraphEvent>* a_this,
			const RE::BSAnimationGraphEvent* a_event, RE::BSTEventSource<RE::BSAnimationGraphEvent>* a_source)
		{
			if (a_event) {
				auto* actor = static_cast<RE::TESObjectREFR*>(a_this)->As<RE::Actor>();
				if (HasPistol(actor)) {
					const std::string_view tag{ a_event->tag.c_str() ? a_event->tag.c_str() : "" };
					if (std::ranges::none_of(kQuietOut, [&](std::string_view q) { return tag == q; })) {
						const std::string_view payload{ a_event->payload.c_str() ? a_event->payload.c_str() : "" };
						SKSE::log::info("{} {} OUT   {}{}{}", Clock(), Who(actor), tag, payload.empty() ? "" : " ", payload);
					}
				}
			}
			return func(a_this, a_event, a_source);
		}
		static inline REL::Relocation<decltype(thunk)> func;
	};

	struct CharacterUpdate
	{
		static void thunk(RE::Character* a_this, float a_delta)
		{
			func(a_this, a_delta);
			if (!HasPistol(a_this)) {
				return;
			}
			const auto now = NowMs();
			{
				std::scoped_lock l{ g_lock };
				auto [it, fresh] = g_traces.try_emplace(a_this->GetFormID());
				if (!fresh && now - it->second.lastSampleMs < kSampleEveryMs) {
					return;
				}
				it->second.lastSampleMs = now;
				if (fresh) {
					SKSE::log::info("{} {} TRACE start (a pistol in hand)", Clock(), Who(a_this));
				}
			}
			auto             vars = Vars(a_this);
			auto             nodes = ActiveNodes(a_this);
			std::scoped_lock l{ g_lock };
			auto*            trace = &g_traces[a_this->GetFormID()];     // looked up again: the map may have grown
			if (vars != trace->vars) {
				SKSE::log::info("{} {} VARS  {}", Clock(), Who(a_this), vars);
				trace->vars = std::move(vars);
			}
			if (nodes != trace->nodes) {
				std::string diff;
				for (const auto& n : nodes) {
					if (!std::ranges::binary_search(trace->nodes, n)) {
						diff += " +" + n;
					}
				}
				for (const auto& n : trace->nodes) {
					if (!std::ranges::binary_search(nodes, n)) {
						diff += " -" + n;
					}
				}
				SKSE::log::info("{} {} NODES{}", Clock(), Who(a_this), diff);
				trace->nodes = std::move(nodes);
			}
		}
		static inline REL::Relocation<decltype(thunk)> func;
	};
}

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	SKSE::log::info("ZenPistolNPCTrace 1.0.0 loading, runtime {}", REL::Module::get().version().string());
	SKSE::log::info("caster state: 0 none, 1 start, 2 startCharge, 3 ready, 4 preStart, 5 charging, 6 casting, 7 ?, "
					"8 interrupt, 9 interrupt/deselect");
	g_refGenVtbl = REL::Relocation<std::uintptr_t>{ RE::VTABLE_hkbBehaviorReferenceGenerator[0] }.address();
	g_graphVtbl = REL::Relocation<std::uintptr_t>{ RE::VTABLE_hkbBehaviorGraph[0] }.address();

	// Character's vtables: [0] TESForm/Actor, [2] BSTEventSink<BSAnimationGraphEvent>, [3] IAnimationGraphManagerHolder.
	REL::Relocation<std::uintptr_t> actorVtbl{ RE::VTABLE_Character[0] };
	CharacterUpdate::func = actorVtbl.write_vfunc(0xAD, CharacterUpdate::thunk);
	REL::Relocation<std::uintptr_t> sinkVtbl{ RE::VTABLE_Character[2] };
	GraphEventSink::func = sinkVtbl.write_vfunc(0x1, GraphEventSink::thunk);
	REL::Relocation<std::uintptr_t> graphVtbl{ RE::VTABLE_Character[3] };
	NotifyAnimationGraph::func = graphVtbl.write_vfunc(0x1, NotifyAnimationGraph::thunk);
	SKSE::log::info("Character Update, graph event sink and NotifyAnimationGraph hooked");

	SKSE::GetMessagingInterface()->RegisterListener([](SKSE::MessagingInterface::Message* a_msg) {
		if (a_msg->type == SKSE::MessagingInterface::kDataLoaded) {
			g_pistol = RE::TESDataHandler::GetSingleton()->LookupForm<RE::BGSKeyword>(0x801, "Pistol animation by Loop.esp"sv);
			SKSE::log::info("pistol keyword Pistol_Animation_By_Loop: {}", g_pistol ? std::format("{:08X}", g_pistol->GetFormID()) : "NOT FOUND"s);
		}
	});
	return true;
}
