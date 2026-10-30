#include "pch.h"

#include <Windows.h>

// WHEELER - Refined 1.3.4 saves its wheels into the SKSE co-save as JSON (SerializationEntry::Save). It opens the
// record ('WJSN', version 2), then calls nlohmann's basic_json::dump(-1, ' ', false, error_handler_t::strict). Each
// weapon and armour item carries its display name ("missingName"), and Enderal's strings are Windows-1252, so its
// accents (Kiléan Falcata, the Rhalâta/Rhalâim gear) are not UTF-8. dump throws type_error 316 on them, the
// throw is swallowed, and the open record stays 0 bytes long. Loading that save then logs "Load: failed to read
// record data, clearing wheel state", so every wheel was gone (found 2026-10-30 in the co-saves and the disassembly).
//
// This plugin rewrites the two stores before that one dump call in wheeler.dll's memory so the call gets
// error_handler_t::replace: a bad byte becomes U+FFFD in the saved name, the rest is written as before. It only
// patches the exact 1.3.4 build (PE timestamp and the 9 original bytes); anything else is logged and left alone.

SKSEPluginInfo(
	.Version = REL::Version{ 1, 0, 1, 0 },
	.Name = "ZenWheelerSaveFix"sv,
	.Author = "Zenderal"sv,
	.StructCompatibility = SKSE::StructCompatibility::Independent,
	.RuntimeCompatibility = SKSE::VersionIndependence::AddressLibrary)

namespace
{
	constexpr std::uint32_t kTimeDateStamp = 0x6AB24A10;  // wheeler.dll 1.3.4 (WHEELER - Refined)
	constexpr std::uintptr_t kSite = 0x1238A3;            // SerializationEntry::Save, the args of the dump call

	// mov dword ptr [rsp+28h], ebx (error_handler = strict, ebx is 0)   mov byte ptr [rsp+20h], 0 (ensure_ascii = false)
	constexpr std::array<std::uint8_t, 9> kOriginal{ 0x89, 0x5C, 0x24, 0x28, 0xC6, 0x44, 0x24, 0x20, 0x00 };

	bool InRel32(std::uintptr_t a_from, std::uintptr_t a_to)
	{
		const auto delta = static_cast<std::int64_t>(a_to) - static_cast<std::int64_t>(a_from);
		return delta >= INT32_MIN && delta <= INT32_MAX;
	}

	// Commits one page in the first free region found walking down, then up, from a_near in 64 KB steps.
	void* AllocateNear(std::uintptr_t a_near)
	{
		constexpr std::uintptr_t kStep = 0x10000;
		constexpr std::uintptr_t kRange = 0x7FF00000;
		const std::uintptr_t start = a_near & ~(kStep - 1);
		for (std::uintptr_t off = kStep; off < kRange; off += kStep) {
			for (const auto addr : { start - off, start + off }) {
				MEMORY_BASIC_INFORMATION mbi{};
				if (!VirtualQuery(reinterpret_cast<void*>(addr), &mbi, sizeof(mbi)) || mbi.State != MEM_FREE) {
					continue;
				}
				if (auto* p = VirtualAlloc(reinterpret_cast<void*>(addr), 0x1000, MEM_RESERVE | MEM_COMMIT, PAGE_EXECUTE_READWRITE)) {
					const auto got = reinterpret_cast<std::uintptr_t>(p);
					if (InRel32(a_near + 5, got) && InRel32(got + 18, a_near + 9)) {
						return p;
					}
					VirtualFree(p, 0, MEM_RELEASE);
				}
			}
		}
		return nullptr;
	}

	void Install()
	{
		const auto module = reinterpret_cast<std::uintptr_t>(GetModuleHandleW(L"wheeler.dll"));
		if (!module) {
			SKSE::log::info("wheeler.dll not loaded; nothing to patch");
			return;
		}
		const auto* dos = reinterpret_cast<const IMAGE_DOS_HEADER*>(module);
		const auto* nt = reinterpret_cast<const IMAGE_NT_HEADERS64*>(module + dos->e_lfanew);
		if (nt->FileHeader.TimeDateStamp != kTimeDateStamp) {
			SKSE::log::error("wheeler.dll timestamp {:08X}, expected {:08X} (1.3.4); not patched", nt->FileHeader.TimeDateStamp, kTimeDateStamp);
			return;
		}
		const auto site = module + kSite;
		if (std::memcmp(reinterpret_cast<const void*>(site), kOriginal.data(), kOriginal.size()) != 0) {
			SKSE::log::error("wheeler.dll+{:X} does not hold the expected dump arguments; not patched", kSite);
			return;
		}

		// The stub sets both arguments and jumps back; it must lie within 2 GB of wheeler.dll for the rel32 jumps.
		// 1.0.0 took CommonLib's Trampoline::create(size, module), which placed it 2.8 GB away: the truncated jump
		// crashed the first save.
		auto* stub = static_cast<std::uint8_t*>(AllocateNear(site));
		if (!stub) {
			SKSE::log::error("no free page within 2 GB of wheeler.dll+{:X}; not patched", kSite);
			return;
		}
		const std::array<std::uint8_t, 13> body{
			0xC7, 0x44, 0x24, 0x28, 0x01, 0x00, 0x00, 0x00,  // mov dword ptr [rsp+28h], 1 (error_handler_t::replace)
			0xC6, 0x44, 0x24, 0x20, 0x00                     // mov byte ptr [rsp+20h], 0 (ensure_ascii = false, as before)
		};
		std::memcpy(stub, body.data(), body.size());
		const auto back = static_cast<std::int32_t>((site + kOriginal.size()) - (reinterpret_cast<std::uintptr_t>(stub) + 18));
		stub[13] = 0xE9;
		std::memcpy(stub + 14, &back, 4);

		std::array<std::uint8_t, 9> jump{ 0xE9, 0, 0, 0, 0, 0x90, 0x90, 0x90, 0x90 };
		const auto to = static_cast<std::int32_t>(reinterpret_cast<std::uintptr_t>(stub) - (site + 5));
		std::memcpy(jump.data() + 1, &to, 4);
		REL::safe_write(site, jump.data(), jump.size());
		SKSE::log::info("wheeler.dll 1.3.4 patched: co-save JSON now written with error_handler::replace (stub at {:X})", reinterpret_cast<std::uintptr_t>(stub));
	}
}

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	SKSE::log::info("ZenWheelerSaveFix 1.0.1 loading, runtime {}", REL::Module::get().version().string());
	SKSE::GetMessagingInterface()->RegisterListener([](SKSE::MessagingInterface::Message* a_msg) {
		if (a_msg->type == SKSE::MessagingInterface::kPostLoad) {
			Install();
		}
	});
	return true;
}
