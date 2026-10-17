// Zenderal memory dump (diagnostic, SSE 1.5.97). SkyrimSE.exe is DRM-encrypted on disk, so its code can
// only be read once the process has decrypted it. On load this writes the whole in-memory image of the
// executable (base .. base+SizeOfImage) to <SKSE log dir>/SkyrimSE_1597_image.bin, logs the base, and
// does nothing else. Used to locate game call sites for the Precision fork; never shipped.
#include <Windows.h>

SKSEPluginInfo(
	.Version = REL::Version{ 1, 0, 0, 0 },
	.Name = "ZenMemDump"sv,
	.Author = "Zenderal"sv,
	.StructCompatibility = SKSE::StructCompatibility::Independent,
	.RuntimeCompatibility = SKSE::VersionIndependence::AddressLibrary)

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	const auto base = reinterpret_cast<std::uint8_t*>(::GetModuleHandleW(nullptr));
	const auto dos = reinterpret_cast<IMAGE_DOS_HEADER*>(base);
	const auto nt = reinterpret_cast<IMAGE_NT_HEADERS64*>(base + dos->e_lfanew);
	const std::size_t size = nt->OptionalHeader.SizeOfImage;
	auto dir = SKSE::log::log_directory();
	if (!dir) {
		return true;
	}
	const auto path = *dir / "SkyrimSE_1597_image.bin";
	std::ofstream out(path, std::ios::binary);
	std::size_t written = 0;
	MEMORY_BASIC_INFORMATION mbi{};
	for (std::size_t off = 0; off < size;) {
		::VirtualQuery(base + off, &mbi, sizeof(mbi));
		std::size_t chunk = std::min<std::size_t>(reinterpret_cast<std::uint8_t*>(mbi.BaseAddress) + mbi.RegionSize - (base + off), size - off);
		const bool readable = mbi.State == MEM_COMMIT && !(mbi.Protect & (PAGE_NOACCESS | PAGE_GUARD));
		if (readable) {
			out.write(reinterpret_cast<const char*>(base + off), static_cast<std::streamsize>(chunk));
		} else {
			std::string zeros(chunk, '\0');
			out.write(zeros.data(), static_cast<std::streamsize>(chunk));
		}
		written += chunk;
		off += chunk;
	}
	SKSE::log::info("Dumped {} bytes of image at {:X} (SizeOfImage {:X}) to {}", written, reinterpret_cast<std::uintptr_t>(base), size, path.string());
	SKSE::log::info("hkbRagdollDriver hooks: 62621 -> {:X}, 62622 -> {:X}", REL::Relocation<std::uintptr_t>{ REL::ID(62621) }.address() - reinterpret_cast<std::uintptr_t>(base),
		REL::Relocation<std::uintptr_t>{ REL::ID(62622) }.address() - reinterpret_cast<std::uintptr_t>(base));
	return true;
}
