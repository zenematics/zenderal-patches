#include "pch.h"

#include <atomic>
#include <chrono>
#include <unordered_map>

// Testing tool, not part of the list. For Honor Reforged's parry did not seem to fire in first person with
// Zenderal - FHR First Person (arch-docs/patches/FHRFirstPerson.md). FHR's chain: the back light attack's annotation
// PIE.$ParrySpell casts BackLightParrySpell 80E on the player (ParryWeaponSelf 810 / ParryShieldSelf 80F = the
// window); an enemy hit landing in the window gets the attacker's ReforgedParryController 876 to apply
// HitFrameTriggerSpell 803 to the player (WeaponParryTrigger 82A / ShieldParryTrigger 811 if the window was open,
// ParryDamageCheck 874 if not); the player's own swing then lands with BackLight 88A + 82A and the player's 876
// applies Weapon Parry Poise Damage 892 to the enemy. This logs, read-only, every link:
//   EVENT  animation events the player's graphs send to the player (PlayerCharacter's BSTEventSink): every PIE
//          payload and attack/hit/window events, tagged with the graph that sent it (1P or 3P) and the active one;
//   FX     the player's FHR parry effects switching on/off, the camera and the melee attack state (player update);
//   APPLY  every magic effect application (TESMagicEffectApplyEvent) to or from the player whose effect was
//          defined by an FHR plugin;
//   HIT    every hit to or from the player (TESHitEvent), with the parry effects the player had at that moment.
//   DIR    (1.1.0) the direction signals FHRFirstPerson's conditions read, on every change and at every attack start:
//          DMK's DirecionalCycleMoveset in each graph, PaulMix's KDForward/KDLeft/KDBack/KDRight bools, Keytrace.esp's
//          held-key effects 801-804 and the actor state's moving flags. Built after an attack following a parry
//          replayed the parry with S released (2026-10-31).
// No lock is held while calling into the game (ZenRagdollTrace's lesson); graph pointers are cached on the main
// thread and only compared in the event sink.
// Log: My Games/Skyrim Special Edition/SKSE/ZenParryTrace.log

SKSEPluginInfo(
	.Version = REL::Version{ 1, 4, 0, 0 },
	.Name = "ZenParryTrace"sv,
	.Author = "Zenderal"sv,
	.StructCompatibility = SKSE::StructCompatibility::Independent,
	.RuntimeCompatibility = SKSE::VersionIndependence::AddressLibrary)

namespace
{
	constexpr auto kBalance = "For Honor Balance Patch.esp"sv;
	constexpr std::array kFhrPlugins{ "For Honor Balance Patch.esp"sv, "For Honor in Skyrim.esp"sv,
		"Reforged Directional Combat.esp"sv };

	struct Watched
	{
		RE::FormID           localID;
		std::string_view     label;
		RE::EffectSetting*   form{ nullptr };
	};

	std::array g_fx{
		Watched{ 0x810, "ParryWeaponSelf(window)"sv },
		Watched{ 0x80F, "ParryShieldSelf(window)"sv },
		Watched{ 0x8B2, "ParryStanceSFX"sv },
		Watched{ 0x82A, "WeaponParryTrigger(parried)"sv },
		Watched{ 0x811, "ShieldParryTrigger(parried)"sv },
		Watched{ 0x874, "ParryDamageCheck(hit-before-window)"sv },
		Watched{ 0x88A, "BackLight"sv },
		Watched{ 0x5F9, "PlayerBackLightCooldown"sv },
		Watched{ 0x894, "ShieldFollowupStrikeController"sv },
		// 1.3.0: the side markers PIE's $LeftLight/$RightLight/$LeftHeavy/$RightHeavy put on the attacker; Reforged
		// Directional Combat's dispel perk 82C reads them when the hit lands
		Watched{ 0x880, "LeftLightMark"sv },
		Watched{ 0x881, "RightLightMark"sv },
		Watched{ 0x882, "LeftHeavyMark"sv },
		Watched{ 0x883, "RightHeavyMark"sv },
	};

	// 1.3.0: Reforged Directional Combat's empowered attacks (the HUD arrows), on any actor
	constexpr auto kDirectional = "Reforged Directional Combat.esp"sv;
	std::array g_buffs{
		Watched{ 0x805, "LeftLight"sv },
		Watched{ 0x804, "RightLight"sv },
		Watched{ 0x806, "BackLight"sv },
		Watched{ 0x802, "LeftHeavy"sv },
		Watched{ 0x801, "RightHeavy"sv },
		Watched{ 0x803, "BackHeavy"sv },
	};

	RE::BGSPerk* g_parryPerk = nullptr;
	RE::TESQuest* g_distQuest = nullptr;

	std::atomic<std::uintptr_t> g_graph[4]{};
	std::atomic<bool>           g_graphIs1P[4]{};
	std::atomic<std::uint32_t>  g_activeGraph{ 99 };
	std::atomic<std::uint32_t>  g_fxMask{ 0 };
	std::atomic<bool>           g_firstPerson{ false };

	// Keytrace.esp (PaulMix's dTry Key Utils extend): held-key effects, in F L B R order.
	std::array<RE::EffectSetting*, 4> g_keytrace{};
	constexpr std::array              kKeytraceIDs{ 0x801u, 0x802u, 0x803u, 0x804u };
	constexpr std::array              kKDVars{ "KDForward"sv, "KDLeft"sv, "KDBack"sv, "KDRight"sv };
	constexpr auto                    kDMKVar = "DirecionalCycleMoveset"sv;

	std::string FLBR(std::uint32_t a_mask)
	{
		std::string out;
		for (std::size_t i = 0; i < 4; ++i) {
			out += (a_mask & (1u << i)) ? "FLBR"[i] : '.';
		}
		return out;
	}

	// Direction signals, read on the main thread (player update).
	std::string DirectionSnapshot(RE::PlayerCharacter* a_player, RE::BSAnimationGraphManager* a_manager)
	{
		std::string dmk, kd;
		if (a_manager) {
			std::uint32_t i = 0;
			for (auto& graph : a_manager->graphs) {
				if (!graph) {
					continue;
				}
				const char* tag = g_graphIs1P[i < 4 ? i : 0].load() ? "1P" : "3P";
				int value = -1;
				const bool has = graph->GetGraphVariableInt(RE::BSFixedString{ kDMKVar }, value);
				dmk += std::format("{}={} ", tag, has ? std::to_string(value) : "absent"s);
				std::uint32_t kdMask = 0;
				for (std::size_t k = 0; k < kKDVars.size(); ++k) {
					bool b = false;
					if (graph->GetGraphVariableBool(RE::BSFixedString{ kKDVars[k] }, b) && b) {
						kdMask |= 1u << k;
					}
				}
				kd += std::format("{}={} ", tag, FLBR(kdMask));
				++i;
			}
		}
		std::uint32_t keyMask = 0;
		if (auto* list = a_player->AsMagicTarget()->GetActiveEffectList()) {
			for (auto* effect : *list) {
				if (!effect || effect->flags.any(RE::ActiveEffect::Flag::kInactive, RE::ActiveEffect::Flag::kDispelled)) {
					continue;
				}
				for (std::size_t k = 0; k < g_keytrace.size(); ++k) {
					if (effect->GetBaseObject() && effect->GetBaseObject() == g_keytrace[k]) {
						keyMask |= 1u << k;
					}
				}
			}
		}
		const auto& s = a_player->AsActorState()->actorState1;
		std::uint32_t moving = (s.movingForward ? 1u : 0) | (s.movingLeft ? 2u : 0) | (s.movingBack ? 4u : 0) | (s.movingRight ? 8u : 0);
		return std::format("DMK[{}] KD[{}] keytrace={} moving={}", dmk, kd, FLBR(keyMask), FLBR(moving));
	}

	const std::chrono::steady_clock::time_point g_start = std::chrono::steady_clock::now();

	std::int64_t NowMs()
	{
		return std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - g_start).count();
	}

	std::string Lower(std::string_view a_s)
	{
		std::string out{ a_s };
		std::ranges::transform(out, out.begin(), [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
		return out;
	}

	bool Interesting(std::string_view a_tag)
	{
		const auto l = Lower(a_tag);
		static constexpr std::array kWords{ "hitframe"sv, "weaponswing"sv, "attackwin"sv, "attackstop"sv, "collision_add"sv,
			"collision_attack"sv, "sbf_"sv, "mco_"sv, "fakehit"sv, "stagger"sv, "blockstart"sv, "blockstop"sv, "prehitframe"sv };
		return l == "pie" || std::ranges::any_of(kWords, [&](std::string_view w) { return l.find(w) != std::string::npos; });
	}

	std::string MaskText(std::uint32_t a_mask)
	{
		std::string out;
		for (std::size_t i = 0; i < g_fx.size(); ++i) {
			if (a_mask & (1u << i)) {
				out += out.empty() ? "" : " ";
				out += g_fx[i].label;
			}
		}
		return out.empty() ? "-" : out;
	}

	std::string Who(const RE::TESObjectREFR* a_ref)
	{
		if (!a_ref) {
			return "none";
		}
		if (a_ref->IsPlayerRef()) {
			return "PLAYER";
		}
		return std::format("{:08X} '{}'", a_ref->GetFormID(), a_ref->GetName());
	}

	std::string FormText(RE::FormID a_id)
	{
		if (!a_id) {
			return "0";
		}
		auto* form = RE::TESForm::LookupByID(a_id);
		if (!form) {
			return std::format("{:08X}", a_id);
		}
		const auto* file = form->GetFile(0);
		return std::format("{:08X} {} '{}' ({})", a_id, RE::FormTypeToString(form->GetFormType()), form->GetName(),
			file ? file->GetFilename() : "?"sv);
	}

	// 1.2.0: actors the player hit in the last kFollowMs ("followed"), written by HitSink, read lock-free everywhere.
	constexpr std::int64_t kFollowMs = 6000;
	constexpr std::int64_t kApplyMs = 1500;
	struct Followed
	{
		std::atomic<RE::FormID>   id{ 0 };
		std::atomic<std::int64_t> hitMs{ 0 };
	};
	std::array<Followed, 8> g_followed;

	void Follow(RE::FormID a_id, std::int64_t a_now)
	{
		std::size_t slot = 0;
		for (std::size_t i = 0; i < g_followed.size(); ++i) {
			if (g_followed[i].id.load() == a_id) {
				slot = i;
				break;
			}
			if (g_followed[i].hitMs.load() < g_followed[slot].hitMs.load()) {
				slot = i;
			}
		}
		g_followed[slot].id = a_id;
		g_followed[slot].hitMs = a_now;
	}

	// ms since the player last hit this actor, or -1
	std::int64_t SinceHit(RE::FormID a_id, std::int64_t a_now)
	{
		for (auto& f : g_followed) {
			if (a_id && f.id.load() == a_id) {
				return a_now - f.hitMs.load();
			}
		}
		return -1;
	}

	// empowered arrows on an actor: present, and "(inactive)" when the effect's conditions currently fail
	std::string BuffText(RE::Actor* a_actor)
	{
		std::string out;
		if (auto* list = a_actor->AsMagicTarget()->GetActiveEffectList()) {
			for (auto* effect : *list) {
				if (!effect || effect->flags.any(RE::ActiveEffect::Flag::kDispelled)) {
					continue;
				}
				const auto* base = effect->GetBaseObject();
				for (auto& b : g_buffs) {
					if (base && base == b.form) {
						out += out.empty() ? "" : " ";
						out += b.label;
						if (effect->flags.any(RE::ActiveEffect::Flag::kInactive)) {
							out += "(inactive)";
						}
					}
				}
			}
		}
		return out.empty() ? "-" : out;
	}

	bool EnemyInteresting(std::string_view a_tag)
	{
		const auto l = Lower(a_tag);
		static constexpr std::array kWords{ "stagger"sv, "recoil"sv, "knock"sv, "getup"sv, "ragdoll"sv, "bleedout"sv,
			"death"sv, "msl_"sv, "block"sv, "attackstart"sv, "attackstop"sv, "pie"sv, "parry"sv };
		return std::ranges::any_of(kWords, [&](std::string_view w) { return l.find(w) != std::string::npos; });
	}

	struct EnemyGraphEvent
	{
		static RE::BSEventNotifyControl thunk(RE::BSTEventSink<RE::BSAnimationGraphEvent>* a_this,
			const RE::BSAnimationGraphEvent* a_event, RE::BSTEventSource<RE::BSAnimationGraphEvent>* a_source)
		{
			if (a_event && a_event->tag.c_str()) {
				const auto  now = NowMs();
				const auto* refr = static_cast<RE::TESObjectREFR*>(a_this);
				const auto  since = SinceHit(refr->formID, now);
				if (since >= 0 && since < kFollowMs && EnemyInteresting(a_event->tag.c_str())) {
					const std::string_view payload{ a_event->payload.c_str() ? a_event->payload.c_str() : "" };
					SKSE::log::info("{:>8} ENEMY {:08X} OUT {}{}{}   (+{} ms after player hit)", now, refr->formID, a_event->tag.c_str(),
						payload.empty() ? "" : " ", payload, since);
				}
			}
			return func(a_this, a_event, a_source);
		}
		static inline REL::Relocation<decltype(thunk)> func;
	};

	struct EnemyNotifyGraph
	{
		static bool thunk(RE::IAnimationGraphManagerHolder* a_this, const RE::BSFixedString& a_eventName)
		{
			const bool  result = func(a_this, a_eventName);
			const auto  now = NowMs();
			const auto* refr = static_cast<RE::TESObjectREFR*>(a_this);
			const auto  since = SinceHit(refr->formID, now);
			if (since >= 0 && since < kFollowMs && a_eventName.c_str() && EnemyInteresting(a_eventName.c_str())) {
				SKSE::log::info("{:>8} ENEMY {:08X} IN  {}{}   (+{} ms after player hit)", now, refr->formID, a_eventName.c_str(),
					result ? "" : " (not accepted)", since);
			}
			return result;
		}
		static inline REL::Relocation<decltype(thunk)> func;
	};

	// 1.4.0: events sent INTO the player's graphs (idles, scripts, SKSE plugins) with the manager's answer. Built for
	// first-person unarmed power attacks that never start (2026-11-10): shows whether attackPowerStartForwardH2HRightHand
	// arrives at all and whether the graphs take it.
	bool PlayerInInteresting(std::string_view a_name)
	{
		const auto l = Lower(a_name);
		static constexpr std::array kWords{ "attack"sv, "power"sv, "bash"sv, "block"sv, "h2h"sv, "equip"sv };
		return std::ranges::any_of(kWords, [&](std::string_view w) { return l.find(w) != std::string::npos; });
	}

	struct PlayerNotifyGraph
	{
		static bool thunk(RE::IAnimationGraphManagerHolder* a_this, const RE::BSFixedString& a_eventName)
		{
			const bool result = func(a_this, a_eventName);
			if (a_eventName.c_str() && PlayerInInteresting(a_eventName.c_str())) {
				auto* player = static_cast<RE::PlayerCharacter*>(a_this);
				SKSE::log::info("{:>8} IN    {}{}   [cam {}, attackState {}]", NowMs(), a_eventName.c_str(),
					result ? "" : " (NOT ACCEPTED)", g_firstPerson.load() ? "1P" : "3P",
					std::to_underlying(player->AsActorState()->GetAttackState()));
			}
			return result;
		}
		static inline REL::Relocation<decltype(thunk)> func;
	};

	// 1.4.0: each graph's iState tag and the variables the H2H attack transitions test, read on the main thread.
	std::string GraphVarsSnapshot(RE::BSAnimationGraphManager* a_manager)
	{
		std::string out;
		if (!a_manager) {
			return out;
		}
		std::uint32_t i = 0;
		for (auto& graph : a_manager->graphs) {
			if (!graph) {
				++i;
				continue;
			}
			int  iState = -1, right = -1, left = -1, wantBlock = -1;
			bool castLeft = false;
			graph->GetGraphVariableInt(RE::BSFixedString{ "iState" }, iState);
			graph->GetGraphVariableInt(RE::BSFixedString{ "iRightHandType" }, right);
			graph->GetGraphVariableInt(RE::BSFixedString{ "iLeftHandType" }, left);
			graph->GetGraphVariableInt(RE::BSFixedString{ "iWantBlock" }, wantBlock);
			graph->GetGraphVariableBool(RE::BSFixedString{ "bWantCastLeft" }, castLeft);
			out += std::format("{}[iState={} R={} L={} castL={} wantBlock={}] ", g_graphIs1P[i < 4 ? i : 0].load() ? "1P" : "3P",
				iState, right, left, castLeft ? 1 : 0, wantBlock);
			++i;
		}
		return out;
	}

	struct GraphEventSink
	{
		static RE::BSEventNotifyControl thunk(RE::BSTEventSink<RE::BSAnimationGraphEvent>* a_this,
			const RE::BSAnimationGraphEvent* a_event, RE::BSTEventSource<RE::BSAnimationGraphEvent>* a_source)
		{
			if (a_event && a_event->tag.c_str()) {
				const std::string_view tag{ a_event->tag.c_str() };
				if (Interesting(tag)) {
					const auto src = reinterpret_cast<std::uintptr_t>(static_cast<RE::BShkbAnimationGraph*>(a_source));
					std::string graph = "?";
					std::uint32_t index = 99;
					for (std::uint32_t i = 0; i < 4; ++i) {
						if (src && g_graph[i].load() == src) {
							graph = g_graphIs1P[i].load() ? "1P" : "3P";
							index = i;
						}
					}
					const std::string_view payload{ a_event->payload.c_str() ? a_event->payload.c_str() : "" };
					SKSE::log::info("{:>8} EVENT {}{} {}{}{}   [cam {}, fx {}]", NowMs(), graph,
						index == g_activeGraph.load() ? "*" : " ", tag, payload.empty() ? "" : " ", payload,
						g_firstPerson.load() ? "1P" : "3P", MaskText(g_fxMask.load()));
				}
			}
			return func(a_this, a_event, a_source);
		}
		static inline REL::Relocation<decltype(thunk)> func;
	};

	struct PlayerUpdate
	{
		static void thunk(RE::PlayerCharacter* a_this, float a_delta)
		{
			func(a_this, a_delta);
			const auto now = NowMs();

			RE::BSTSmartPointer<RE::BSAnimationGraphManager> manager;
			if (a_this->GetAnimationGraphManager(manager) && manager) {
				std::uint32_t i = 0;
				for (auto& graph : manager->graphs) {
					if (i >= 4) {
						break;
					}
					const auto ptr = reinterpret_cast<std::uintptr_t>(graph.get());
					if (g_graph[i].exchange(ptr) != ptr && graph) {
						const std::string_view project{ graph->projectName.c_str() ? graph->projectName.c_str() : "" };
						g_graphIs1P[i] = Lower(project).find("first") != std::string::npos;
						SKSE::log::info("{:>8} GRAPH {} = '{}' ({})", now, i, project, g_graphIs1P[i].load() ? "1P" : "3P");
					}
					++i;
				}
				const auto active = manager->GetRuntimeData().activeGraph;
				if (g_activeGraph.exchange(active) != active) {
					SKSE::log::info("{:>8} GRAPH active = {}", now, active);
				}
			}

			const auto* camera = RE::PlayerCamera::GetSingleton();
			const bool  firstPerson = camera && camera->IsInFirstPerson();
			if (g_firstPerson.exchange(firstPerson) != firstPerson) {
				SKSE::log::info("{:>8} CAMERA {}", now, firstPerson ? "1P" : "3P");
			}

			std::uint32_t mask = 0;
			if (auto* list = a_this->AsMagicTarget()->GetActiveEffectList()) {
				for (auto* effect : *list) {
					if (!effect || effect->flags.any(RE::ActiveEffect::Flag::kInactive, RE::ActiveEffect::Flag::kDispelled)) {
						continue;
					}
					const auto* base = effect->GetBaseObject();
					for (std::size_t i = 0; base && i < g_fx.size(); ++i) {
						if (base == g_fx[i].form) {
							mask |= 1u << i;
						}
					}
				}
			}
			const auto old = g_fxMask.exchange(mask);
			if (old != mask) {
				SKSE::log::info("{:>8} FX    on [{}] off [{}] now [{}] attackState={} blocking={}", now, MaskText(mask & ~old),
					MaskText(old & ~mask), MaskText(mask), std::to_underlying(a_this->AsActorState()->GetAttackState()),
					a_this->IsBlocking());
			}

			const auto vars = GraphVarsSnapshot(manager.get());
			static std::string lastVars;
			if (vars != lastVars) {
				SKSE::log::info("{:>8} VARS  {}  attackState={}", now, vars, std::to_underlying(a_this->AsActorState()->GetAttackState()));
				lastVars = vars;
			}

			const auto dir = DirectionSnapshot(a_this, manager.get());
			static std::string lastDir;
			if (dir != lastDir) {
				SKSE::log::info("{:>8} DIR   {}", now, dir);
				lastDir = dir;
			}

			static RE::ATTACK_STATE_ENUM lastAttack = RE::ATTACK_STATE_ENUM::kNone;
			const auto attack = a_this->AsActorState()->GetAttackState();
			if (attack != lastAttack) {
				SKSE::log::info("{:>8} ATTACK state {} -> {}{}", now, std::to_underlying(lastAttack), std::to_underlying(attack),
					lastAttack == RE::ATTACK_STATE_ENUM::kNone ? "   start with " + dir : ""s);
				lastAttack = attack;
			}

			// followed actors: knock state / ragdoll / stagger flag on change
			static std::array<std::string, 8> lastEnemy;
			for (std::size_t i = 0; i < g_followed.size(); ++i) {
				const auto id = g_followed[i].id.load();
				const auto since = now - g_followed[i].hitMs.load();
				if (!id || since > kFollowMs) {
					continue;
				}
				auto* actor = RE::TESForm::LookupByID<RE::Actor>(id);
				if (!actor) {
					continue;
				}
				bool staggered = false;
				actor->GetGraphVariableBool("IsStaggering"sv, staggered);
				const auto state = std::format("knock={} ragdoll={} staggering={} dead={}",
					std::to_underlying(actor->AsActorState()->GetKnockState()), actor->IsInRagdollState(), staggered, actor->IsDead());
				if (state != lastEnemy[i]) {
					SKSE::log::info("{:>8} ENEMY {:08X} STATE {}   (+{} ms after player hit)", now, id, state, since);
					lastEnemy[i] = state;
				}
			}

			// 1.3.0: empowered arrows on every loaded actor, on change - did the player's side attack strip one?
			static std::unordered_map<RE::FormID, std::string> lastBuffs;
			if (auto* lists = RE::ProcessLists::GetSingleton()) {
				for (auto& handle : lists->highActorHandles) {
					auto actor = handle.get();
					if (!actor || actor->IsPlayerRef()) {
						continue;
					}
					const auto buffs = BuffText(actor.get());
					auto [it, added] = lastBuffs.try_emplace(actor->formID, "-"s);
					if (it->second != buffs) {
						const auto since = SinceHit(actor->formID, now);
						SKSE::log::info("{:>8} BUFF  {} arrows [{}] was [{}]   [fx {}]{}", now, Who(actor.get()), buffs, it->second,
							MaskText(g_fxMask.load()), since >= 0 ? std::format(" (+{} ms after player hit)", since) : ""s);
						it->second = buffs;
					}
				}
			}
		}
		static inline REL::Relocation<decltype(thunk)> func;
	};

	struct ApplySink : RE::BSTEventSink<RE::TESMagicEffectApplyEvent>
	{
		RE::BSEventNotifyControl ProcessEvent(const RE::TESMagicEffectApplyEvent* a_event,
			RE::BSTEventSource<RE::TESMagicEffectApplyEvent>*) override
		{
			if (!a_event) {
				return RE::BSEventNotifyControl::kContinue;
			}
			const auto now = NowMs();
			// 1.2.0: anything applied to an actor the player just hit, from any plugin - which combat hit spell won the
			// engine's single slot (a hit spell's caster reads as its target, so the player never shows as caster)
			const auto since = a_event->target ? SinceHit(a_event->target->formID, now) : -1;
			const bool hitTarget = since >= 0 && since < kApplyMs;
			const bool mine = (a_event->target && a_event->target->IsPlayerRef()) || (a_event->caster && a_event->caster->IsPlayerRef());
			if (!mine && !hitTarget) {
				return RE::BSEventNotifyControl::kContinue;
			}
			auto*       form = RE::TESForm::LookupByID(a_event->magicEffect);
			const auto* file = form ? form->GetFile(0) : nullptr;
			const std::string_view name = file ? file->GetFilename() : ""sv;
			if (!hitTarget && std::ranges::find(kFhrPlugins, name) == kFhrPlugins.end()) {
				return RE::BSEventNotifyControl::kContinue;
			}
			SKSE::log::info("{:>8} APPLY{} {} -> {}: {}   [fx {}]{}", now, hitTarget ? "*" : " ", Who(a_event->caster.get()),
				Who(a_event->target.get()), FormText(a_event->magicEffect), MaskText(g_fxMask.load()),
				hitTarget ? std::format(" (+{} ms after player hit)", since) : ""s);
			return RE::BSEventNotifyControl::kContinue;
		}
	};

	struct HitSink : RE::BSTEventSink<RE::TESHitEvent>
	{
		RE::BSEventNotifyControl ProcessEvent(const RE::TESHitEvent* a_event, RE::BSTEventSource<RE::TESHitEvent>*) override
		{
			if (!a_event) {
				return RE::BSEventNotifyControl::kContinue;
			}
			const bool mine = (a_event->target && a_event->target->IsPlayerRef()) || (a_event->cause && a_event->cause->IsPlayerRef());
			if (!mine) {
				return RE::BSEventNotifyControl::kContinue;
			}
			if (a_event->cause && a_event->cause->IsPlayerRef() && a_event->target && a_event->target->Is(RE::FormType::ActorCharacter)) {
				Follow(a_event->target->formID, NowMs());
			}
			SKSE::log::info("{:>8} HIT   {} -> {} source {} proj {} flags {:X}   [cam {}, fx {}]", NowMs(), Who(a_event->cause.get()),
				Who(a_event->target.get()), FormText(a_event->source), a_event->projectile ? FormText(a_event->projectile) : "-",
				a_event->flags.underlying(), g_firstPerson.load() ? "1P" : "3P", MaskText(g_fxMask.load()));
			return RE::BSEventNotifyControl::kContinue;
		}
	};

	void LogSetup()
	{
		auto* player = RE::PlayerCharacter::GetSingleton();
		if (!player) {
			return;
		}
		SKSE::log::info("{:>8} SETUP player has ReforgedParryController 876: {}; dist quest 806 running: {}", NowMs(),
			g_parryPerk ? (player->HasPerk(g_parryPerk) ? "yes" : "NO") : "perk not found",
			g_distQuest ? (g_distQuest->IsRunning() ? "yes" : "NO") : "quest not found");
		// 1.3.0: every ApplyCombatHitSpell entry the player has. One combat hit spell lands per hit, so these compete:
		// FHR's side strips (82C) and riposte poise damage (876, 892) against everything else's
		auto* data = RE::TESDataHandler::GetSingleton();
		for (auto* perk : data->GetFormArray<RE::BGSPerk>()) {
			if (!perk || !player->HasPerk(perk)) {
				continue;
			}
			for (auto* entry : perk->perkEntries) {
				if (!entry || entry->GetType() != RE::PERK_ENTRY_TYPE::kEntryPoint) {
					continue;
				}
				auto* point = static_cast<RE::BGSEntryPointPerkEntry*>(entry);
				if (!point->IsEntryPoint(RE::BGSEntryPoint::ENTRY_POINTS::kApplyCombatHitSpell)) {
					continue;
				}
				const auto* spellData = skyrim_cast<RE::BGSEntryPointFunctionDataSpellItem*>(point->functionData);
				std::size_t conditions = 0;
				for (auto& tab : point->conditions) {
					for (auto* item = tab.head; item; item = item->next) {
						++conditions;
					}
				}
				SKSE::log::info("{:>8} SETUP hit spell entry: priority {} rank {} conditions {} perk {} -> {}", NowMs(),
					entry->header.priority, entry->header.rank, conditions, FormText(perk->GetFormID()),
					spellData && spellData->spell ? FormText(spellData->spell->GetFormID()) : "?"s);
			}
		}
	}
}

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	SKSE::log::info("ZenParryTrace 1.3.0 loading, runtime {}", REL::Module::get().version().string());
	SKSE::log::info("EVENT lines: graph that sent it (1P/3P, * = the active graph). attackState: 0 none, 1 draw, 2 swing, "
					"3 hit, 4 next attack, 5 follow-through, 6 bash, 8 bow draw ...");

	// PlayerCharacter's vtables: [0] TESForm/Actor, [2] BSTEventSink<BSAnimationGraphEvent>.
	REL::Relocation<std::uintptr_t> sinkVtbl{ RE::VTABLE_PlayerCharacter[2] };
	GraphEventSink::func = sinkVtbl.write_vfunc(0x1, GraphEventSink::thunk);
	REL::Relocation<std::uintptr_t> playerVtbl{ RE::VTABLE_PlayerCharacter[0] };
	PlayerUpdate::func = playerVtbl.write_vfunc(0xAD, PlayerUpdate::thunk);
	// Character's vtables: [2] BSTEventSink<BSAnimationGraphEvent>, [3] IAnimationGraphManagerHolder (ZenRagdollTrace's hooks;
	// that tool is disabled). Only actors the player hit in the last 6 s are logged; no lock, no game call but formID.
	REL::Relocation<std::uintptr_t> enemySinkVtbl{ RE::VTABLE_Character[2] };
	EnemyGraphEvent::func = enemySinkVtbl.write_vfunc(0x1, EnemyGraphEvent::thunk);
	REL::Relocation<std::uintptr_t> enemyGraphVtbl{ RE::VTABLE_Character[3] };
	EnemyNotifyGraph::func = enemyGraphVtbl.write_vfunc(0x1, EnemyNotifyGraph::thunk);
	// 1.4.0: PlayerCharacter's own IAnimationGraphManagerHolder vtable ([3], as for Character): events into the player.
	REL::Relocation<std::uintptr_t> playerGraphVtbl{ RE::VTABLE_PlayerCharacter[3] };
	PlayerNotifyGraph::func = playerGraphVtbl.write_vfunc(0x1, PlayerNotifyGraph::thunk);
	SKSE::log::info("player graph event sink and update hooked; Character graph events hooked for followed targets");

	SKSE::GetMessagingInterface()->RegisterListener([](SKSE::MessagingInterface::Message* a_msg) {
		if (a_msg->type == SKSE::MessagingInterface::kDataLoaded) {
			auto* data = RE::TESDataHandler::GetSingleton();
			for (auto& w : g_fx) {
				w.form = data->LookupForm<RE::EffectSetting>(w.localID, kBalance);
				SKSE::log::info("watch {:03X} {} -> {}", w.localID, w.label, w.form ? std::format("{:08X}", w.form->GetFormID()) : "NOT FOUND"s);
			}
			for (std::size_t k = 0; k < g_keytrace.size(); ++k) {
				g_keytrace[k] = data->LookupForm<RE::EffectSetting>(kKeytraceIDs[k], "Keytrace.esp"sv);
				SKSE::log::info("keytrace {:03X} -> {}", kKeytraceIDs[k], g_keytrace[k] ? std::format("{:08X}", g_keytrace[k]->GetFormID()) : "NOT FOUND"s);
			}
			for (auto& b : g_buffs) {
				b.form = data->LookupForm<RE::EffectSetting>(b.localID, kDirectional);
				SKSE::log::info("arrow {:03X} {} -> {}", b.localID, b.label, b.form ? std::format("{:08X}", b.form->GetFormID()) : "NOT FOUND"s);
			}
			g_parryPerk = data->LookupForm<RE::BGSPerk>(0x876, kBalance);
			g_distQuest = data->LookupForm<RE::TESQuest>(0x806, kBalance);
			static ApplySink applySink;
			static HitSink   hitSink;
			auto* holder = RE::ScriptEventSourceHolder::GetSingleton();
			holder->AddEventSink<RE::TESMagicEffectApplyEvent>(&applySink);
			holder->AddEventSink<RE::TESHitEvent>(&hitSink);
			SKSE::log::info("magic effect apply + hit sinks registered");
		} else if (a_msg->type == SKSE::MessagingInterface::kPostLoadGame || a_msg->type == SKSE::MessagingInterface::kNewGame) {
			LogSetup();
		}
	});
	return true;
}
