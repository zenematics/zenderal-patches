#include "pch.h"

#include <chrono>
#include <filesystem>
#include <optional>

// DBVO 2.0.2.2 plays the player's voice line with the engine's own speech call, but nothing drives the
// player's mouth from it: Cinematic Conversation Camera's diagnostics show the player's viseme channel
// at 0 slots while a DBVO line plays, until CCC's Lip Sync Fallback starts writing shapes it guesses
// from the subtitle's letters, spaced evenly over the line. Every DBVO .fuz already carries the line's
// real .lip track. This plugin plays it.
//
// Finding the file: DBVO names each line Sound/DBVO/<pack>/<XXH64(prompt)>.fuz, XXH64 with seed 0 over
// the prompt's exact UTF-8 text, upper-case hex (6 of 6 logged lines matched, 2026-10-17).
//
// The .lip format (reverse-engineered from all 3551 files of the Nehrimese pack; tools/lipdump.py):
//   u32 1 | u32 decodedSize | u32 13 | zero-run-compressed body (00 <u16 n> = n zero bytes, any other
//   byte literal) that decodes to u32 frames | i32 ? | u32 16 | frames x 33 floats, 30 frames a second.
//   Floats 0-15 are the 16 phonemes in the engine's order (Aah..W); 16-32 the 17 modifiers, unused here.
//
// Timing: the line starts when one of the player's two high-process sound handles starts playing while
// the dialogue menu is open, and the text is MenuTopicManager::lastSelectedDialogue at that moment. The
// mouth closes when the track ends, when that handle stops (a skipped line), or when the menu closes.

SKSEPluginInfo(
	.Version = REL::Version{ 1, 0, 0, 0 },
	.Name = "ZenDBVOLipSync"sv,
	.Author = "Zenderal"sv,
	.StructCompatibility = SKSE::StructCompatibility::Independent,
	.RuntimeCompatibility = SKSE::VersionIndependence::AddressLibrary)

namespace
{
	constexpr auto kIniPath = "Data/SKSE/Plugins/ZenDBVOLipSync.ini";
	constexpr auto kPackRoot = "Data/Sound/DBVO";
	constexpr std::size_t kPhonemes = 16;
	constexpr std::size_t kFloatsPerFrame = 33;

	using Frame = std::array<float, kPhonemes>;

	std::int32_t g_offsetMs{ 0 };
	float        g_strength{ 1.0f };
	float        g_frameRate{ 30.0f };
	std::string  g_voicePack;
	bool         g_log{ true };

	std::vector<std::string> g_packs;  // folder names under Data/Sound/DBVO

	struct Line
	{
		std::vector<Frame> frames;
		std::string        text;
		std::string        file;
		double             startMs{ 0.0 };
		bool               active{ false };
	};
	Line g_line;
	bool g_handleWasPlaying{ false };
	bool g_mouthDirty{ false };  // we wrote non-zero phonemes that still need clearing

	double NowMs()
	{
		using namespace std::chrono;
		return duration<double, std::milli>(steady_clock::now().time_since_epoch()).count();
	}

	// ---- XXH64, seed 0 -------------------------------------------------------------------------------

	constexpr std::uint64_t P1 = 0x9E3779B185EBCA87ull, P2 = 0xC2B2AE3D27D4EB4Full, P3 = 0x165667B19E3779F9ull,
							P4 = 0x85EBCA77C2B2AE63ull, P5 = 0x27D4EB2F165667C5ull;

	std::uint64_t Rotl(std::uint64_t a_x, int a_r) { return (a_x << a_r) | (a_x >> (64 - a_r)); }
	std::uint64_t Read64(const std::uint8_t* a_p) { std::uint64_t v; std::memcpy(&v, a_p, 8); return v; }
	std::uint32_t Read32(const std::uint8_t* a_p) { std::uint32_t v; std::memcpy(&v, a_p, 4); return v; }
	std::uint64_t Round(std::uint64_t a_acc, std::uint64_t a_in) { return Rotl(a_acc + a_in * P2, 31) * P1; }
	std::uint64_t Merge(std::uint64_t a_acc, std::uint64_t a_v) { return (a_acc ^ Round(0, a_v)) * P1 + P4; }

	std::uint64_t XXH64(std::string_view a_text)
	{
		const auto*       p = reinterpret_cast<const std::uint8_t*>(a_text.data());
		const std::size_t len = a_text.size();
		const auto*       end = p + len;
		std::uint64_t     h;
		if (len >= 32) {
			std::uint64_t v1 = P1 + P2, v2 = P2, v3 = 0, v4 = 0 - P1;
			for (; p + 32 <= end; p += 32) {
				v1 = Round(v1, Read64(p));
				v2 = Round(v2, Read64(p + 8));
				v3 = Round(v3, Read64(p + 16));
				v4 = Round(v4, Read64(p + 24));
			}
			h = Rotl(v1, 1) + Rotl(v2, 7) + Rotl(v3, 12) + Rotl(v4, 18);
			h = Merge(Merge(Merge(Merge(h, v1), v2), v3), v4);
		} else {
			h = P5;
		}
		h += len;
		for (; p + 8 <= end; p += 8) {
			h = Rotl(h ^ Round(0, Read64(p)), 27) * P1 + P4;
		}
		if (p + 4 <= end) {
			h = Rotl(h ^ (static_cast<std::uint64_t>(Read32(p)) * P1), 23) * P2 + P3;
			p += 4;
		}
		for (; p < end; ++p) {
			h = Rotl(h ^ (*p * P5), 11) * P1;
		}
		h ^= h >> 33;
		h *= P2;
		h ^= h >> 29;
		h *= P3;
		h ^= h >> 32;
		return h;
	}

	// ---- .fuz / .lip ---------------------------------------------------------------------------------

	std::optional<std::vector<std::uint8_t>> ReadLip(const std::string& a_path)
	{
		RE::BSResourceNiBinaryStream stream{ a_path };
		if (!stream.good()) {
			return std::nullopt;
		}
		std::array<char, 12> header{};
		if (!stream.read(header.data(), 12) || std::memcmp(header.data(), "FUZE", 4) != 0) {
			return std::nullopt;
		}
		std::uint32_t lipSize{};
		std::memcpy(&lipSize, header.data() + 8, 4);
		if (lipSize == 0 || lipSize > 16 * 1024 * 1024) {
			return std::nullopt;
		}
		std::vector<std::uint8_t> lip(lipSize);
		if (!stream.read(reinterpret_cast<char*>(lip.data()), lipSize)) {
			return std::nullopt;
		}
		return lip;
	}

	std::optional<std::vector<Frame>> DecodeLip(const std::vector<std::uint8_t>& a_lip, std::string& a_why)
	{
		if (a_lip.size() < 12 || Read32(a_lip.data()) != 1 || Read32(a_lip.data() + 8) != 13) {
			a_why = "unexpected .lip header";
			return std::nullopt;
		}
		const std::uint32_t   decodedSize = Read32(a_lip.data() + 4);
		std::vector<std::uint8_t> out;
		out.reserve(decodedSize);
		for (std::size_t i = 12; i < a_lip.size();) {
			if (a_lip[i] == 0) {
				if (i + 2 >= a_lip.size()) {
					a_why = "truncated zero run";
					return std::nullopt;
				}
				const std::size_t n = a_lip[i + 1] | (a_lip[i + 2] << 8);
				out.insert(out.end(), n, 0);
				i += 3;
			} else {
				out.push_back(a_lip[i++]);
			}
		}
		if (out.size() < 12) {
			a_why = "body too short";
			return std::nullopt;
		}
		const std::uint32_t frames = Read32(out.data());
		if (out.size() != 12 + frames * kFloatsPerFrame * 4 || decodedSize != out.size() + 16) {
			a_why = fmt::format("size mismatch (decoded {}, frames {}, header {})", out.size(), frames, decodedSize);
			return std::nullopt;
		}
		std::vector<Frame> result(frames);
		for (std::uint32_t k = 0; k < frames; ++k) {
			std::memcpy(result[k].data(), out.data() + 12 + k * kFloatsPerFrame * 4, kPhonemes * 4);
		}
		return result;
	}

	// ---- the player's face ---------------------------------------------------------------------------

	void WriteMouth(RE::PlayerCharacter* a_player, const Frame* a_frame)
	{
		auto* anim = a_player->GetFaceGenAnimationData();
		if (!anim) {
			return;
		}
		RE::BSSpinLockGuard guard{ anim->lock };
		auto&               kf = anim->phenomeKeyFrame;
		if (!kf.values || kf.count < kPhonemes) {
			return;
		}
		for (std::size_t i = 0; i < kPhonemes; ++i) {
			kf.SetValue(static_cast<std::uint32_t>(i), a_frame ? std::clamp((*a_frame)[i] * g_strength, 0.0f, 1.0f) : 0.0f);
		}
		g_mouthDirty = a_frame != nullptr;
	}

	void EndLine(RE::PlayerCharacter* a_player, std::string_view a_why)
	{
		if (g_line.active && g_log) {
			SKSE::log::info("  ended ({}) at {:.2f}s", a_why, (NowMs() - g_line.startMs) / 1000.0);
		}
		g_line.active = false;
		if (g_mouthDirty) {
			WriteMouth(a_player, nullptr);
		}
	}

	bool PlayerVoicePlaying(RE::PlayerCharacter* a_player)
	{
		auto* high = a_player->GetHighProcess();
		if (!high) {
			return false;
		}
		for (auto& handle : high->soundHandles) {
			if (handle.soundID != RE::BSSoundHandle::kInvalidID && handle.IsPlaying()) {
				return true;
			}
		}
		return false;
	}

	std::optional<std::string> FindFuz(std::uint64_t a_hash)
	{
		const auto name = fmt::format("{:016X}.fuz", a_hash);
		std::vector<std::string> packs;
		if (!g_voicePack.empty()) {
			packs.push_back(g_voicePack);
		} else {
			packs = g_packs;
		}
		for (const auto& pack : packs) {
			auto path = fmt::format("Sound\\DBVO\\{}\\{}", pack, name);
			if (RE::BSResourceNiBinaryStream{ path }.good()) {
				return path;
			}
		}
		return std::nullopt;
	}

	void StartLine(RE::PlayerCharacter* a_player, const RE::MenuTopicManager* a_topics)
	{
		EndLine(a_player, "next line");
		const auto* dialogue = a_topics->lastSelectedDialogue;
		const char* text = dialogue ? dialogue->topicText.c_str() : nullptr;
		if (!text || !*text) {
			if (g_log) {
				SKSE::log::info("Player voice started, but no topic is selected; leaving the mouth alone");
			}
			return;
		}
		const auto hash = XXH64(text);
		const auto path = FindFuz(hash);
		if (!path) {
			if (g_log) {
				SKSE::log::info("\"{}\": no {:016X}.fuz in any of {} voice pack(s); leaving the mouth alone", text, hash, g_voicePack.empty() ? g_packs.size() : 1);
			}
			return;
		}
		std::string why;
		const auto  lip = ReadLip(*path);
		auto        frames = lip ? DecodeLip(*lip, why) : std::nullopt;
		if (!frames || frames->empty()) {
			SKSE::log::warn("\"{}\": {} has no usable lip track ({})", text, *path, lip ? why : "could not read the .fuz");
			return;
		}
		g_line.frames = std::move(*frames);
		g_line.text = text;
		g_line.file = *path;
		g_line.startMs = NowMs() + g_offsetMs;
		g_line.active = true;
		if (g_log) {
			SKSE::log::info("\"{}\": {} frames ({:.2f}s) from {}", text, g_line.frames.size(), g_line.frames.size() / g_frameRate, *path);
		}
	}

	void Tick(RE::PlayerCharacter* a_player)
	{
		const auto* topics = RE::MenuTopicManager::GetSingleton();
		const bool  inDialogue = topics && topics->menuOpen;
		const bool  playing = inDialogue && PlayerVoicePlaying(a_player);
		const bool  wasPlaying = std::exchange(g_handleWasPlaying, playing);

		if (playing && !wasPlaying) {
			StartLine(a_player, topics);
		} else if (!playing && wasPlaying) {
			EndLine(a_player, inDialogue ? "voice stopped" : "dialogue closed");
		}
		if (!g_line.active) {
			return;
		}

		const double t = (NowMs() - g_line.startMs) / 1000.0 * g_frameRate;
		if (t < 0.0) {
			WriteMouth(a_player, nullptr);  // OffsetMs > 0: mouth still waiting for the voice
			return;
		}
		const auto index = static_cast<std::size_t>(t);
		if (index + 1 >= g_line.frames.size()) {
			EndLine(a_player, "track finished");
			return;
		}
		const float frac = static_cast<float>(t - static_cast<double>(index));
		const auto& a = g_line.frames[index];
		const auto& b = g_line.frames[index + 1];
		Frame       mixed;
		for (std::size_t i = 0; i < kPhonemes; ++i) {
			mixed[i] = a[i] + (b[i] - a[i]) * frac;
		}
		WriteMouth(a_player, &mixed);
	}

	// Actor::Update (vfunc 0xAD) on the player's vtable: once per frame while the game runs.
	struct PlayerUpdate
	{
		static void thunk(RE::PlayerCharacter* a_this, float a_delta)
		{
			func(a_this, a_delta);
			Tick(a_this);
		}
		static inline REL::Relocation<decltype(thunk)> func;
	};

	// ---- settings ------------------------------------------------------------------------------------

	// GetPrivateProfileString can't be used: a relative path is looked up in the Windows directory, and a
	// UTF-8 BOM glues itself to the first section header (ZenBlockReleaseFix 1.0.0). Parse it ourselves.
	std::optional<std::string> ReadIni(std::string_view a_section, std::string_view a_key)
	{
		std::ifstream file{ kIniPath };
		if (!file) {
			return std::nullopt;
		}
		const auto trim = [](std::string_view s) {
			const auto b = s.find_first_not_of(" \t\r");
			const auto e = s.find_last_not_of(" \t\r");
			return b == std::string_view::npos ? std::string_view{} : s.substr(b, e - b + 1);
		};
		const auto iequals = [](std::string_view a, std::string_view b) {
			return std::ranges::equal(a, b, [](char x, char y) { return std::tolower(static_cast<unsigned char>(x)) == std::tolower(static_cast<unsigned char>(y)); });
		};
		std::string line;
		bool        inSection = false;
		bool        first = true;
		while (std::getline(file, line)) {
			std::string_view view{ line };
			if (first && view.starts_with("\xEF\xBB\xBF"sv)) {
				view.remove_prefix(3);
			}
			first = false;
			view = trim(view);
			if (view.empty() || view.front() == ';' || view.front() == '#') {
				continue;
			}
			if (view.front() == '[') {
				const auto end = view.find(']');
				inSection = end != std::string_view::npos && iequals(trim(view.substr(1, end - 1)), a_section);
				continue;
			}
			const auto eq = view.find('=');
			if (inSection && eq != std::string_view::npos && iequals(trim(view.substr(0, eq)), a_key)) {
				return std::string{ trim(view.substr(eq + 1)) };
			}
		}
		return std::nullopt;
	}

	template <class T>
	T ReadIniNumber(std::string_view a_key, T a_default)
	{
		const auto value = ReadIni("General"sv, a_key);
		T          result{};
		if (value && std::from_chars(value->data(), value->data() + value->size(), result).ec == std::errc{}) {
			return result;
		}
		return a_default;
	}

	void LoadSettings()
	{
		g_offsetMs = ReadIniNumber<std::int32_t>("OffsetMs"sv, 0);
		g_strength = std::clamp(ReadIniNumber<std::int32_t>("Strength"sv, 100), 0, 200) / 100.0f;
		g_frameRate = std::clamp(ReadIniNumber<float>("FrameRate"sv, 30.0f), 5.0f, 120.0f);
		g_voicePack = ReadIni("General"sv, "VoicePack"sv).value_or("");
		g_log = ReadIniNumber<std::int32_t>("Log"sv, 1) != 0;
		SKSE::log::info("OffsetMs={} Strength={:.2f} FrameRate={:.1f} VoicePack=\"{}\" Log={}", g_offsetMs, g_strength, g_frameRate, g_voicePack, g_log);
	}

	void FindPacks()
	{
		std::error_code ec;
		for (const auto& entry : std::filesystem::directory_iterator{ kPackRoot, ec }) {
			if (entry.is_directory(ec)) {
				g_packs.push_back(entry.path().filename().string());
			}
		}
		SKSE::log::info("{} voice pack folder(s) under {}{}", g_packs.size(), kPackRoot, ec ? fmt::format(" (listing stopped: {})", ec.message()) : "");
		for (const auto& pack : g_packs) {
			SKSE::log::info("  {}", pack);
		}
	}
}

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	SKSE::log::info("ZenDBVOLipSync 1.0.0 loading, runtime {}", REL::Module::get().version().string());
	LoadSettings();

	REL::Relocation<std::uintptr_t> vtbl{ RE::VTABLE_PlayerCharacter[0] };
	PlayerUpdate::func = vtbl.write_vfunc(0xAD, PlayerUpdate::thunk);
	SKSE::log::info("PlayerCharacter::Update hooked");

	SKSE::GetMessagingInterface()->RegisterListener([](SKSE::MessagingInterface::Message* a_msg) {
		if (a_msg->type == SKSE::MessagingInterface::kDataLoaded) {
			FindPacks();
			// Two of DBVO's real filenames: one under 32 bytes, one over (XXH64's two code paths).
			const bool hashOk = XXH64("Is there any news?"sv) == 0x76AB9B622A8D0F5Dull &&
			                    XXH64("I'm new in the city and I'm looking for work. Do you know where I can find any?"sv) == 0xB47C67F04228BCCFull;
			SKSE::log::info("XXH64 self-check {}", hashOk ? "passed" : "FAILED - no line will be found");
		}
	});
	return true;
}
