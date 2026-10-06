#pragma once

#include <RE/Skyrim.h>
#include <SKSE/SKSE.h>
#include <REX/REX/Singleton.h>

#include <algorithm>
#include <cctype>
#include <atomic>
#include <format>

using namespace std::literals;

// ZP: libxse's REX helpers used upstream are not in CommonLibSSE-NG; minimal equivalents.
namespace ZP
{
	// Enderal 2.0.12's SKSE registers UI.OpenCustomMenu menus under the swf name ("00E_heromenu");
	// 2.1.x's uses the generic "CustomMenu", which is what upstream checks for.
	inline constexpr std::string_view HeroMenuName = "00E_heromenu"sv;

	inline bool IContains(std::string_view a_haystack, std::string_view a_needle)
	{
		auto it = std::search(
			a_haystack.begin(), a_haystack.end(),
			a_needle.begin(), a_needle.end(),
			[](char a, char b) { return std::tolower(static_cast<unsigned char>(a)) == std::tolower(static_cast<unsigned char>(b)); });
		return it != a_haystack.end();
	}
}
