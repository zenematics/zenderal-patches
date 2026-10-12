// Zenderal Precision Lift Fix (SSE 1.5.97 / Enderal SE 2.0.12, CommonLibSSE-NG).
//
// Precision gives living actors an "active ragdoll": their ragdoll bodies are in the physics world,
// driven to the animation pose, and a landed hit applies a real impulse to the struck body and its
// neighbours (PrecisionHandler::ApplyHitImpulse). While that runs, Precision switches gravity OFF for
// the ragdoll (Settings::bDisableGravityForActiveRagdolls, hard-coded true) and treats the ragdoll's
// ROOT body as where the creature is.
//
// That is fine for a human: 19 light bodies, and torso hits land on spine bodies. The frost atronach's
// ragdoll has no spine or head bodies at all - a heavy COM (mass 100) with the limbs hanging off it - so
// most torso hits land on the root itself, and with no gravity it floats upward until the pose pulls it
// back (reported 2026-10-12; confirmed in game by turning Precision's "Apply impulse on hit" off).
// Precision has no per-actor impulse setting and its API cannot modify an impulse, so this plugin:
//
//   - on every Precision hit (PostHitCallback) against a configured race, opens a short window;
//   - on every physics step (PrePhysicsStepCallback), for actors in a window, finds the ragdoll root
//     body. The first step after the hit records how high it sits above the actor's feet (the pose:
//     the impulse has only set a velocity, nothing has integrated yet). On later steps, if the root has
//     risen more than `toleranceUnits` above that height, the plugin cancels its upward
//     velocity and pulls it back down. Limbs keep their push (the hit reaction stays), the body only
//     cannot lift off. Dead actors are skipped, so death ragdolls are untouched.
//
// Uses Precision's published API header (PrecisionAPI.h, ersh1/Precision, GPL-3.0).

#include "PrecisionAPI.h"

SKSEPluginInfo(
	.Version = REL::Version{ 1, 0, 0, 0 },
	.Name = "ZenPrecisionLiftFix"sv,
	.Author = "Zenderal"sv,
	.StructCompatibility = SKSE::StructCompatibility::Independent,
	.RuntimeCompatibility = SKSE::VersionIndependence::AddressLibrary)

namespace
{
	constexpr auto kConfigPath = "Data/SKSE/Plugins/ZenPrecisionLiftFix.json"sv;

	using Clock = std::chrono::steady_clock;

	struct Config
	{
		std::vector<RE::TESRace*> races;
		float                     windowSeconds{ 1.5f };
		float                     toleranceUnits{ 6.0f };
		float                     pullbackGain{ 12.0f };       // 1/s: pull-down speed per unit of excess height
		float                     maxPullbackSpeed{ 300.0f };  // Skyrim units per second
		bool                      debugLog{ false };
		bool                      clamp{ true };  // mode "clamp": false = observe only (diagnostics)
		bool                      disableMode{ true };  // mode "disable": Precision ignores these actors entirely
	};

	struct Tracked
	{
		RE::ActorHandle   handle;
		float             baseline{ 0.0f };  // root body height above the actor's feet at the first step
		bool              hasBaseline{ false };
		Clock::time_point expires;
		float             maxExcess{ 0.0f };  // debug: highest excess seen this window
		int               clampedSteps{ 0 };
		int               step{ 0 };              // debug: physics steps since the window opened
		Clock::time_point opened;
	};

	Config                                     g_cfg;
	std::mutex                                 g_lock;
	std::unordered_map<std::uint32_t, Tracked> g_tracked;
	PRECISION_API::IVPrecision4*               g_precision{ nullptr };
	SKSE::PluginHandle                         g_pluginHandle{ 0 };

	void LoadConfig()
	{
		Config cfg;
		std::ifstream in{ std::string(kConfigPath) };
		if (!in) {
			SKSE::log::error("Config {} not found - plugin inactive", kConfigPath);
			g_cfg = cfg;
			return;
		}
		try {
			auto j = nlohmann::json::parse(in, nullptr, true, true);
			auto* dh = RE::TESDataHandler::GetSingleton();
			for (auto& r : j.value("races", nlohmann::json::array())) {
				const auto plugin = r.value("plugin", ""s);
				const auto idStr = r.value("formID", ""s);
				const auto id = static_cast<RE::FormID>(std::stoul(idStr, nullptr, 16));
				if (auto* race = dh ? dh->LookupForm<RE::TESRace>(id, plugin) : nullptr) {
					cfg.races.push_back(race);
					SKSE::log::info("Race {} {} -> {}", plugin, idStr, race->GetFormEditorID());
				} else {
					SKSE::log::warn("Race {} {} not found - skipped", plugin, idStr);
				}
			}
			cfg.windowSeconds = j.value("windowSeconds", cfg.windowSeconds);
			cfg.toleranceUnits = j.value("toleranceUnits", cfg.toleranceUnits);
			cfg.pullbackGain = j.value("pullbackGain", cfg.pullbackGain);
			cfg.maxPullbackSpeed = j.value("maxPullbackSpeed", cfg.maxPullbackSpeed);
			cfg.debugLog = j.value("debugLog", cfg.debugLog);
			cfg.clamp = j.value("clamp", cfg.clamp);
			cfg.disableMode = j.value("mode", "disable"s) == "disable";
		} catch (const std::exception& e) {
			SKSE::log::error("Failed to read {}: {}", kConfigPath, e.what());
		}
		SKSE::log::info("mode {}, {} races, window {} s, tolerance {}, gain {}, max pull {}",
			cfg.disableMode ? "disable" : "clamp", cfg.races.size(), cfg.windowSeconds, cfg.toleranceUnits, cfg.pullbackGain, cfg.maxPullbackSpeed);
		std::scoped_lock l{ g_lock };
		g_cfg = std::move(cfg);
		g_tracked.clear();
	}

	bool IsConfiguredRace(RE::Actor* a_actor)
	{
		auto* race = a_actor->GetRace();
		return race && std::ranges::find(g_cfg.races, race) != g_cfg.races.end();
	}

	// ---------------------------------------------------------------- mode "disable"
	//
	// PrecisionHandler::ToggleDisableActor ("Disables Precision for an actor (removes the ragdoll etc.)")
	// keeps the actor out of Precision's world, so it never gets an active ragdoll and cannot float.
	// Precision CLEARS its disabled list whenever the physics world changes (PrecisionHandler::Clear,
	// called from its havok-hit-jobs hook), so this is re-applied every scan, not once.

	std::atomic_bool  g_scanQueued{ false };
	Clock::time_point g_lastScan{};

	void DisableIfConfigured(RE::Actor* a_actor)
	{
		if (!g_precision || !a_actor || !IsConfiguredRace(a_actor)) {
			return;
		}
		if (g_precision->ToggleDisableActor(a_actor->GetHandle(), true) && g_cfg.debugLog) {
			SKSE::log::info("{:08X}: Precision disabled for this actor", a_actor->GetFormID());
		}
	}

	void ScanAndDisable()  // main thread (SKSE task)
	{
		g_scanQueued = false;
		std::scoped_lock l{ g_lock };
		if (!g_cfg.disableMode || g_cfg.races.empty()) {
			return;
		}
		if (auto* lists = RE::ProcessLists::GetSingleton()) {
			for (auto& handle : lists->highActorHandles) {
				if (auto actor = handle.get()) {
					DisableIfConfigured(actor.get());
				}
			}
		}
	}

	// ---------------------------------------------------------------- Precision callbacks

	void OnPostHit(const PRECISION_API::PrecisionHitData& a_hit, const RE::HitData&)
	{
		auto* target = a_hit.target ? a_hit.target->As<RE::Actor>() : nullptr;
		if (!target || target->IsDead()) {
			return;
		}
		std::scoped_lock l{ g_lock };
		if (g_cfg.races.empty() || !IsConfiguredRace(target)) {
			return;
		}
		if (g_cfg.disableMode) {
			if (g_cfg.debugLog) {
				SKSE::log::info("{:08X}: Precision hit registered on a configured actor", target->GetFormID());
			}
			DisableIfConfigured(target);  // in case the scan has not reached it yet
			return;
		}
		const auto now = Clock::now();
		const auto window = std::chrono::duration_cast<Clock::duration>(std::chrono::duration<float>(g_cfg.windowSeconds));
		const auto key = target->GetHandle().native_handle();

		if (auto it = g_tracked.find(key); it != g_tracked.end() && it->second.expires > now) {
			it->second.expires = now + window;  // already guarded: keep the original baseline
			return;
		}
		Tracked t;
		t.handle = target->GetHandle();
		t.expires = now + window;
		t.opened = now;
		g_tracked[key] = t;
		if (g_cfg.debugLog) {
			SKSE::log::info("{:08X}: hit, window opened", target->GetFormID());
		}
	}

	RE::hkpRigidBody* GetRagdollRoot(RE::hkbRagdollDriver* a_driver)
	{
		if (!a_driver || !a_driver->ragdoll) {
			return nullptr;
		}
		auto* ragdoll = a_driver->ragdoll;
		if (ragdoll->rigidBodies.size() == 0) {
			return nullptr;
		}
		int index = ragdoll->boneToRigidBodyMap.size() > 0 ? ragdoll->boneToRigidBodyMap[0] : -1;
		if (index < 0 || index >= static_cast<int>(ragdoll->rigidBodies.size())) {
			index = 0;
		}
		return ragdoll->rigidBodies[index];
	}

	void OnPrePhysicsStep(RE::bhkWorld*)
	{
		std::scoped_lock l{ g_lock };
		const auto now = Clock::now();
		if (g_cfg.disableMode) {
			if (now - g_lastScan > 500ms && !g_scanQueued.exchange(true)) {
				g_lastScan = now;
				SKSE::GetTaskInterface()->AddTask([] { ScanAndDisable(); });
			}
			return;
		}
		if (g_tracked.empty()) {
			return;
		}
		const float scale = RE::bhkWorld::GetWorldScale();          // Skyrim units -> Havok
		const float scaleInv = RE::bhkWorld::GetWorldScaleInverse();  // Havok -> Skyrim units

		for (auto it = g_tracked.begin(); it != g_tracked.end();) {
			auto& t = it->second;
			auto actorPtr = t.handle.get();
			auto* actor = actorPtr.get();
			if (!actor || actor->IsDead() || now >= t.expires) {
				if (g_cfg.debugLog && actor) {
					SKSE::log::info("{:08X}: window closed, max excess {:.1f}, clamped {} steps", actor->GetFormID(), t.maxExcess, t.clampedSteps);
				}
				it = g_tracked.erase(it);
				continue;
			}

			RE::BSAnimationGraphManagerPtr manager;
			if (actor->GetAnimationGraphManager(manager) && manager) {
				RE::BSSpinLockGuard guard(manager->GetRuntimeData().updateLock);
				for (auto& graph : manager->graphs) {
					if (!graph) {
						continue;
					}
					auto* root = GetRagdollRoot(graph->characterInstance.ragdollDriver.get());
					// Not in a world yet = Precision has not added the active ragdoll; its pose is stale.
					if (!root || !root->world || root->motion.type == RE::hkpMotion::MotionType::kKeyframed) {
						continue;
					}
					const float height = root->motion.motionState.transform.translation.quad.m128_f32[2] * scaleInv - actor->GetPosition().z;
					if (!t.hasBaseline) {
						t.baseline = height;
						t.hasBaseline = true;
						if (g_cfg.debugLog) {
							std::string bodies;
							for (auto* rb : graph->characterInstance.ragdollDriver->ragdoll->rigidBodies) {
								if (rb) {
									bodies += fmt::format(" [{} {:.0f}]", rb->name.c_str() ? rb->name.c_str() : "?",
										rb->motion.motionState.transform.translation.quad.m128_f32[2] * scaleInv - actor->GetPosition().z);
								}
							}
							SKSE::log::info("{:08X}: root baseline {:.1f}, bodies:{}", actor->GetFormID(), height, bodies);
						}
						continue;
					}
					const float excess = height - t.baseline - g_cfg.toleranceUnits;
					t.maxExcess = std::max(t.maxExcess, height - t.baseline);
					float&      vz = root->motion.linearVelocity.quad.m128_f32[2];
					const float vzBefore = vz * scaleInv;
					if (g_cfg.clamp && excess > 0.0f) {
						// Above the allowed height: no further rise, and a proportional pull back down.
						const float pull = std::min(g_cfg.pullbackGain * excess, g_cfg.maxPullbackSpeed) * scale;
						vz = std::min(vz, -pull);
						++t.clampedSteps;
					}
					if (g_cfg.debugLog && (t.step++ % 3) == 0) {
						// Timeline: is it the ragdoll root, the actor (character controller) or only the model?
						float modelZ = 0.0f, comZ = 0.0f;
						if (auto* obj = actor->Get3D()) {
							modelZ = obj->world.translate.z;
							if (auto* com = obj->GetObjectByName("NPC COM [COM ]")) {
								comZ = com->world.translate.z;
							}
						}
						const float ms = std::chrono::duration<float, std::milli>(now - t.opened).count();
						SKSE::log::info("{:08X} +{:5.0f}ms actorZ {:8.1f} rootH {:6.1f} (base {:6.1f}) vz {:7.1f}->{:7.1f} model-actor {:6.1f} COMnode-actor {:6.1f}",
							actor->GetFormID(), ms, actor->GetPosition().z, height, t.baseline, vzBefore, vz * scaleInv,
							modelZ - actor->GetPosition().z, comZ - actor->GetPosition().z);
						// Every ragdoll body's centre height above the feet: which one sits on the ground?
						if ((t.step % 9) == 1) {
							std::string bodies;
							auto* ragdoll = graph->characterInstance.ragdollDriver->ragdoll;
							for (auto* rb : ragdoll->rigidBodies) {
								if (!rb) {
									continue;
								}
								const float h = rb->motion.motionState.transform.translation.quad.m128_f32[2] * scaleInv - actor->GetPosition().z;
								bodies += fmt::format(" [{} {:.0f}]", rb->name.c_str() ? rb->name.c_str() : "?", h);
							}
							SKSE::log::info("{:08X}   bodies:{}", actor->GetFormID(), bodies);
						}
					}
				}
			}
			++it;
		}
	}

	// ---------------------------------------------------------------- setup

	bool RegisterWithPrecision()
	{
		if (g_precision) {
			return true;
		}
		g_precision = reinterpret_cast<PRECISION_API::IVPrecision4*>(PRECISION_API::RequestPluginAPI(PRECISION_API::InterfaceVersion::V4));
		if (!g_precision) {
			SKSE::log::error("Precision API (V4) not available - is Precision.dll loaded? Plugin inactive");
			return false;
		}
		const auto hit = g_precision->AddPostHitCallback(g_pluginHandle, OnPostHit);
		const auto step = g_precision->AddPrePhysicsStepCallback(g_pluginHandle, OnPrePhysicsStep);
		SKSE::log::info("Registered with Precision: post-hit {}, pre-physics {}", static_cast<int>(hit), static_cast<int>(step));
		return hit == PRECISION_API::APIResult::OK && step == PRECISION_API::APIResult::OK;
	}

	void MessageHandler(SKSE::MessagingInterface::Message* a_msg)
	{
		switch (a_msg->type) {
		case SKSE::MessagingInterface::kDataLoaded:
			LoadConfig();
			RegisterWithPrecision();
			break;
		case SKSE::MessagingInterface::kPostLoadGame:
			LoadConfig();  // pick up tuning without a restart
			RegisterWithPrecision();
			break;
		default:
			break;
		}
	}
}

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	SKSE::log::info("ZenPrecisionLiftFix 1.0.0 loading, runtime {}", REL::Module::get().version().string());
	g_pluginHandle = a_skse->GetPluginHandle();
	SKSE::GetMessagingInterface()->RegisterListener(MessageHandler);
	return true;
}
