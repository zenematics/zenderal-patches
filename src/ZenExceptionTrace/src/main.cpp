#include "pch.h"

#include <Windows.h>
#include <cstdio>
#include <mutex>
#include <thread>

// Testing tool, not part of the list. Shatterveil 1.3.1, patched for 1.7.104 (src/ShatterveilAE), is refused by
// SKSE with "fatal error occurred while loading plugin" and writes no log: SKSE catches an exception thrown inside
// its SKSEPlugin_Load. This plugin loads first (its file name starts with '_') and adds a vectored exception handler
// that logs every first-chance exception whose stack holds a frame in Target: the code, the faulting module + RVA,
// the C++ exception's type and what(), and the stack as module + RVA. Logging stops after kMaxLines.
// Log: My Games/Skyrim Special Edition/SKSE/_ZenExceptionTrace.log

SKSEPluginInfo(
	.Version = REL::Version{ 1, 3, 0, 0 },
	.Name = "_ZenExceptionTrace"sv,
	.Author = "Zenderal"sv,
	.StructCompatibility = SKSE::StructCompatibility::Independent,
	.RuntimeCompatibility = SKSE::VersionIndependence::AddressLibrary)

namespace
{
	constexpr const wchar_t* kTarget = L"Shatterveil.dll";
	constexpr int            kMaxLines = 400;

	std::FILE* g_log{ nullptr };
	int        g_lines{ 0 };
	std::mutex g_lock;

	void line(const char* a_fmt, ...)
	{
		if (!g_log || g_lines >= kMaxLines) {
			return;
		}
		va_list args;
		va_start(args, a_fmt);
		std::vfprintf(g_log, a_fmt, args);
		va_end(args);
		std::fputc('\n', g_log);
		std::fflush(g_log);
		++g_lines;
	}

	// "Shatterveil.dll+0x1234" for an address
	std::string where(const void* a_addr)
	{
		HMODULE mod{ nullptr };
		if (!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
				static_cast<LPCWSTR>(a_addr), &mod) || !mod) {
			char buf[32];
			std::snprintf(buf, sizeof(buf), "%p", a_addr);
			return buf;
		}
		char path[MAX_PATH]{};
		GetModuleFileNameA(mod, path, MAX_PATH);
		const char* name = std::strrchr(path, '\\');
		name = name ? name + 1 : path;
		char buf[MAX_PATH + 32];
		std::snprintf(buf, sizeof(buf), "%s+0x%llX", name,
			static_cast<unsigned long long>(reinterpret_cast<std::uintptr_t>(a_addr) - reinterpret_cast<std::uintptr_t>(mod)));
		return buf;
	}

	bool in_target(const void* a_addr)
	{
		HMODULE mod{ nullptr };
		return GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
				   static_cast<LPCWSTR>(a_addr), &mod) &&
		       mod && mod == GetModuleHandleW(kTarget);
	}

	// MSVC C++ exception (0xE06D7363): params = magic, object, ThrowInfo (RVA-based on x64), image base
	void describe_cpp(const EXCEPTION_RECORD* a_rec)
	{
		if (a_rec->NumberParameters < 4) {
			return;
		}
		const auto obj = reinterpret_cast<const void*>(a_rec->ExceptionInformation[1]);
		const auto info = reinterpret_cast<const std::uint8_t*>(a_rec->ExceptionInformation[2]);
		const auto base = static_cast<std::uintptr_t>(a_rec->ExceptionInformation[3]);
		if (!info || !base) {
			return;
		}
		__try {
			const auto cta = reinterpret_cast<const std::int32_t*>(base + *reinterpret_cast<const std::int32_t*>(info + 12));
			const int  n = cta[0];
			for (int i = 0; i < n && i < 6; ++i) {
				const auto ct = reinterpret_cast<const std::uint8_t*>(base + cta[1 + i]);
				const auto td = reinterpret_cast<const char*>(base + *reinterpret_cast<const std::int32_t*>(ct + 4));
				line("    C++ type: %s", td + 16);   // TypeDescriptor: vftable, spare, name
			}
			const auto ct0 = reinterpret_cast<const std::uint8_t*>(base + cta[1]);
			const char* name0 = reinterpret_cast<const char*>(base + *reinterpret_cast<const std::int32_t*>(ct0 + 4)) + 16;
			bool        isStd = false;
			for (int i = 0; i < n && i < 6; ++i) {
				const auto ct = reinterpret_cast<const std::uint8_t*>(base + cta[1 + i]);
				if (std::strstr(reinterpret_cast<const char*>(base + *reinterpret_cast<const std::int32_t*>(ct + 4)) + 16, "exception@std")) {
					isStd = true;
				}
			}
			if (isStd && obj && name0) {
				line("    what(): %s", static_cast<const std::exception*>(obj)->what());
			}
		} __except (EXCEPTION_EXECUTE_HANDLER) {
			line("    (could not read the C++ exception)");
		}
	}

	LONG CALLBACK handler(EXCEPTION_POINTERS* a_info)
	{
		const auto rec = a_info->ExceptionRecord;
		const auto code = rec->ExceptionCode;
		if (code == 0x406D1388 || code == 0x40010006 || code == 0x4001000A || code == DBG_CONTROL_C) {
			return EXCEPTION_CONTINUE_SEARCH;   // thread naming, OutputDebugString
		}
		void*      frames[48]{};
		const auto count = RtlCaptureStackBackTrace(0, 48, frames, nullptr);
		bool       hit = in_target(rec->ExceptionAddress);
		for (USHORT i = 0; i < count && !hit; ++i) {
			hit = in_target(frames[i]);
		}
		if (!hit) {
			return EXCEPTION_CONTINUE_SEARCH;
		}
		std::scoped_lock l(g_lock);
		line("exception 0x%08lX at %s (thread %lu)", code, where(rec->ExceptionAddress).c_str(), GetCurrentThreadId());
		if (code == EXCEPTION_ACCESS_VIOLATION && rec->NumberParameters >= 2) {
			line("    %s address %p", rec->ExceptionInformation[0] ? "write to" : "read of",
				reinterpret_cast<void*>(rec->ExceptionInformation[1]));
		}
		if (code == 0xE06D7363) {
			describe_cpp(rec);
		}
		for (USHORT i = 0; i < count; ++i) {
			line("    #%02u %s", i, where(frames[i]).c_str());
		}
		return EXCEPTION_CONTINUE_SEARCH;
	}
}

// 1.1.0 (2026-10-28): Shatterveil probe. After a save loads, logs the forms Shatterveil 1.3.1 resolved at data load
// (its globals, RVAs read from its form resolver at 0xFFCB0), the slow-time spell's effect count, the player's
// instant magic caster and Shatterveil's live fShoutSlowTime (settings singleton 0xF0450, +0x16C) - to see why the
// Veil Wyrm's sounds and slow time do nothing on 1.7.104. RVAs are for the patched 1.3.1 DLL only.
namespace
{
	struct Global
	{
		std::uint32_t rva;
		std::uint32_t formID;
		const char*   what;
	};
	constexpr Global kGlobals[] = {
		{ 0x1B9E20, 0xE6A, "shout" }, { 0x1B9E28, 0xE67, "word 1" }, { 0x1B9E30, 0xE68, "word 2" }, { 0x1B9E38, 0xE69, "word 3" },
		{ 0x1B9E58, 0xE71, "wave spell 1" }, { 0x1B9E70, 0xE35, "shrapnel spell" }, { 0x1B9E78, 0xF26, "slow-time spell" },
		{ 0x1B9E80, 0xF36, "cover spell" }, { 0x1B9E88, 0xF27, "imod" }, { 0x1B9E98, 0xE75, "SNDR resonance" },
		{ 0x1B9EA0, 0xE76, "SNDR dust" }, { 0x1B9EA8, 0xE77, "SNDR form" }, { 0x1B9EB0, 0xEC1, "SNDR EC1" },
		{ 0x1B9EB8, 0xF35, "SNDR theme" }, { 0x1B9F30, 0xE79, "SNDR roar dragon" }, { 0x1B9F38, 0xE7A, "SNDR roar brute" },
		{ 0x1B9F40, 0xE7B, "SNDR roar alduin" }, { 0x1B9F48, 0xE7C, "SNDR roar ancient" },
	};

	void probe()
	{
		const auto base = reinterpret_cast<std::uintptr_t>(GetModuleHandleW(kTarget));
		if (!base) {
			line("probe: %ls not loaded", kTarget);
			return;
		}
		line("probe: %ls at %p", kTarget, reinterpret_cast<void*>(base));
		__try {
			for (const auto& g : kGlobals) {
				const auto form = *reinterpret_cast<RE::TESForm* const*>(base + g.rva);
				if (form) {
					line("    %-18s (Shatterveil %03X) = %p  formID %08X type %02X", g.what, g.formID, static_cast<void*>(form),
						form->GetFormID(), static_cast<unsigned>(form->GetFormType()));
				} else {
					line("    %-18s (Shatterveil %03X) = NULL", g.what, g.formID);
				}
			}
			if (const auto slow = *reinterpret_cast<RE::SpellItem* const*>(base + 0x1B9E78)) {
				line("    slow-time spell effects: %u", slow->effects.size());
			}
			using settings_t = std::uint8_t* (*)();
			const auto settings = reinterpret_cast<settings_t>(base + 0xF0450)();
			line("    settings %p: fShoutSlowTime (+0x16C) = %.3f, +0x170 = %.3f", static_cast<void*>(settings),
				*reinterpret_cast<float*>(settings + 0x16C), *reinterpret_cast<float*>(settings + 0x170));
			const auto player = RE::PlayerCharacter::GetSingleton();
			line("    player %p, instant magic caster %p", static_cast<void*>(player),
				player ? static_cast<void*>(player->GetMagicCaster(RE::MagicSystem::CastingSource::kInstant)) : nullptr);
		} __except (EXCEPTION_EXECUTE_HANDLER) {
			line("    probe faulted");
		}
	}

	// 1.2.0: the Veil Wyrm stays silent though its sound records resolve. Its sounds go through one wrapper
	// (Shatterveil+0x48470: std::string (*)(SNDR*, TESObjectREFR*, float volume, float), which returns a status text the
	// callers drop). Each of its 6 call sites is redirected here: log the record, the reference it plays at and the
	// status it returns.
	constexpr std::uint32_t kPlayWrapper = 0x48470;
	constexpr std::uint32_t kPlaySites[] = { 0x3A1B0, 0xFE6D6, 0xFF35B, 0xFF6E3, 0x100566, 0x100BD8 };

	using play_t = std::string* (*)(std::string*, RE::BGSSoundDescriptorForm*, RE::TESObjectREFR*, float, float);
	play_t g_play{ nullptr };

	void describe_play(std::string* ret, RE::BGSSoundDescriptorForm* a_sound, RE::TESObjectREFR* a_ref, float a_volume, float a_extra)
	{
		__try {
			const auto pos = a_ref ? a_ref->GetPosition() : RE::NiPoint3{};
			line("play: sound %08X at %08X (%s, 3D %s, pos %.0f %.0f %.0f) volume %.2f / %.2f -> \"%s\"",
				a_sound ? a_sound->GetFormID() : 0, a_ref ? a_ref->GetFormID() : 0,
				a_ref ? (a_ref->IsPlayerRef() ? "player" : a_ref->GetFormType() == RE::FormType::ActorCharacter ? "actor" : "ref") : "none",
				a_ref && a_ref->Get3D() ? "yes" : "no", pos.x, pos.y, pos.z, a_volume, a_extra, ret ? ret->c_str() : "?");
		} __except (EXCEPTION_EXECUTE_HANDLER) {
			line("play: (could not describe the call)");
		}
	}

	std::string* play_hook(std::string* a_out, RE::BGSSoundDescriptorForm* a_sound, RE::TESObjectREFR* a_ref, float a_volume, float a_extra)
	{
		const auto ret = g_play(a_out, a_sound, a_ref, a_volume, a_extra);
		std::scoped_lock l(g_lock);
		describe_play(ret, a_sound, a_ref, a_volume, a_extra);
		return ret;
	}

	void install_play_hooks()
	{
		const auto base = reinterpret_cast<std::uintptr_t>(GetModuleHandleW(kTarget));
		if (!base) {
			return;
		}
		// One 14-byte stub (jmp [rip+0]; dq play_hook) in a page within 2 GB below Shatterveil, so its rel32 calls reach
		// it (CommonLib's trampoline landed out of range: "displacement is out of range").
		std::uint8_t* stub = nullptr;
		SYSTEM_INFO   si{};
		GetSystemInfo(&si);
		const std::uintptr_t gran = si.dwAllocationGranularity;
		for (std::uintptr_t addr = (base & ~(gran - 1)) - gran; addr > base - 0x7FF00000 && !stub; addr -= gran) {
			MEMORY_BASIC_INFORMATION mbi{};
			if (VirtualQuery(reinterpret_cast<void*>(addr), &mbi, sizeof(mbi)) && mbi.State == MEM_FREE) {
				stub = static_cast<std::uint8_t*>(VirtualAlloc(reinterpret_cast<void*>(addr), gran, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE));
			}
		}
		if (!stub) {
			line("play hook: no free page within 2 GB of %ls - not installed", kTarget);
			return;
		}
		const std::uint8_t jmp[6] = { 0xFF, 0x25, 0, 0, 0, 0 };
		std::memcpy(stub, jmp, 6);
		const auto hook = reinterpret_cast<std::uintptr_t>(&play_hook);
		std::memcpy(stub + 6, &hook, 8);
		g_play = reinterpret_cast<play_t>(base + kPlayWrapper);
		int done = 0;
		for (const auto site : kPlaySites) {
			const auto at = base + site;
			const auto bytes = reinterpret_cast<std::uint8_t*>(at);
			const auto target = at + 5 + *reinterpret_cast<const std::int32_t*>(at + 1);
			if (bytes[0] != 0xE8 || target != base + kPlayWrapper) {
				line("play hook: site 0x%X is not a call to the wrapper - skipped", site);
				continue;
			}
			const auto rel = static_cast<std::int64_t>(reinterpret_cast<std::uintptr_t>(stub)) - static_cast<std::int64_t>(at + 5);
			if (rel < INT32_MIN || rel > INT32_MAX) {
				line("play hook: stub out of range of 0x%X", site);
				continue;
			}
			DWORD old = 0;
			VirtualProtect(bytes, 5, PAGE_EXECUTE_READWRITE, &old);
			const auto rel32 = static_cast<std::int32_t>(rel);
			std::memcpy(bytes + 1, &rel32, 4);
			VirtualProtect(bytes, 5, old, &old);
			++done;
		}
		line("play hook: %d of %zu call sites", done, std::size(kPlaySites));
	}

	void on_message(SKSE::MessagingInterface::Message* a_msg)
	{
		if (a_msg->type == SKSE::MessagingInterface::kPostLoad) {
			install_play_hooks();
		}
		if (a_msg->type == SKSE::MessagingInterface::kPostLoadGame || a_msg->type == SKSE::MessagingInterface::kNewGame) {
			probe();
		}
	}
}

SKSEPluginLoad(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse, false);
	SKSE::GetMessagingInterface()->RegisterListener(on_message);
	if (auto dir = SKSE::log::log_directory()) {
		*dir /= "_ZenExceptionTrace.log";
		g_log = _wfopen(dir->c_str(), L"w");
	}
	line("_ZenExceptionTrace 1.3.1: watching %ls", kTarget);
	AddVectoredExceptionHandler(1, handler);
	return true;
}
