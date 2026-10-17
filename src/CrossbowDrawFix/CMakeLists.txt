cmake_minimum_required(VERSION 3.25)

# Zenderal Crossbow Draw Fix: a crossbow draw sets the player's attack state to kBowAttached
# (arrowAttach@0.571 on CrossBow_Equip) and only WeapEquip_Out at the clip's end clears it. A draw cut
# short (drawn right after sprinting) never gets WeapEquip_Out, so sprinting and sheathing stay blocked
# until a shot. Clears a kBowAttached that outlives any real draw or reload. SSE 1.5.97 only, CommonLibSSE-NG.
project(ZenCrossbowDrawFix VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")

set(ENABLE_SKYRIM_SE ON CACHE BOOL "" FORCE)
set(ENABLE_SKYRIM_AE OFF CACHE BOOL "" FORCE)
set(ENABLE_SKYRIM_VR OFF CACHE BOOL "" FORCE)
set(BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(SKSE_SUPPORT_PATCH_SAFETY OFF CACHE BOOL "" FORCE)

# Shares the CommonLibSSE-NG clone in the repo-root lib/ (gitignored; clone the ng branch of alandtse/CommonLibVR there).
set(COMMONLIB_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../../lib/CommonLibNG" CACHE PATH "CommonLibSSE-NG checkout")
add_subdirectory(${COMMONLIB_DIR} CommonLibNG EXCLUDE_FROM_ALL)

add_library(${PROJECT_NAME} SHARED src/main.cpp)
target_include_directories(${PROJECT_NAME} PRIVATE src)
target_precompile_headers(${PROJECT_NAME} PRIVATE src/pch.h)
target_link_libraries(${PROJECT_NAME} PRIVATE CommonLibSSE::CommonLibSSE)
target_compile_definitions(${PROJECT_NAME} PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
target_compile_options(${PROJECT_NAME} PRIVATE /utf-8 /permissive- /Zc:preprocessor /EHsc)
