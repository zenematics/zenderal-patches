cmake_minimum_required(VERSION 3.25)

# Baka Hero Menu (shad0wshayd3, GPL-3.0 + modding exception), ported to Enderal SE 2.0.12 / SSE 1.5.97
# on CommonLibSSE-NG. Upstream targets libxse CommonLibSSE (1.6.x+/Enderal 2.1.x only).
project(BakaHeroMenu VERSION 1.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")

# SE (1.5.97) only: Enderal SE 2.0.12 is pinned to it.
set(ENABLE_SKYRIM_SE ON CACHE BOOL "" FORCE)
set(ENABLE_SKYRIM_AE OFF CACHE BOOL "" FORCE)
set(ENABLE_SKYRIM_VR OFF CACHE BOOL "" FORCE)
set(BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(SKSE_SUPPORT_PATCH_SAFETY OFF CACHE BOOL "" FORCE)  # no trampoline use; avoids a git FetchContent of hde64
add_subdirectory(lib/CommonLibNG EXCLUDE_FROM_ALL)

add_library(${PROJECT_NAME} SHARED src/main.cpp)
target_include_directories(${PROJECT_NAME} PRIVATE src)
target_precompile_headers(${PROJECT_NAME} PRIVATE src/pch.h)
target_link_libraries(${PROJECT_NAME} PRIVATE CommonLibSSE::CommonLibSSE)
target_compile_definitions(${PROJECT_NAME} PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
target_compile_options(${PROJECT_NAME} PRIVATE /utf-8 /permissive- /Zc:preprocessor /EHsc)
