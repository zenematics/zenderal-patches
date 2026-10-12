cmake_minimum_required(VERSION 3.25)

# Zenderal Precision Lift Fix: stops Precision's live hit impulse from lifting creatures whose ragdoll
# root carries the whole body (the frost atronach). SSE 1.5.97 only (Enderal SE 2.0.12), CommonLibSSE-NG.
project(ZenPrecisionLiftFix VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")

set(ENABLE_SKYRIM_SE ON CACHE BOOL "" FORCE)
set(ENABLE_SKYRIM_AE OFF CACHE BOOL "" FORCE)
set(ENABLE_SKYRIM_VR OFF CACHE BOOL "" FORCE)
set(BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(SKSE_SUPPORT_PATCH_SAFETY OFF CACHE BOOL "" FORCE)

# Shares the CommonLibSSE-NG clone used by BakaHeroMenu (gitignored; see that folder's notes).
set(COMMONLIB_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../BakaHeroMenu/lib/CommonLibNG" CACHE PATH "CommonLibSSE-NG checkout")
add_subdirectory(${COMMONLIB_DIR} CommonLibNG EXCLUDE_FROM_ALL)

find_package(nlohmann_json CONFIG REQUIRED)

add_library(${PROJECT_NAME} SHARED src/main.cpp)
target_include_directories(${PROJECT_NAME} PRIVATE src)
target_precompile_headers(${PROJECT_NAME} PRIVATE src/pch.h)
target_link_libraries(${PROJECT_NAME} PRIVATE CommonLibSSE::CommonLibSSE nlohmann_json::nlohmann_json)
target_compile_definitions(${PROJECT_NAME} PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
target_compile_options(${PROJECT_NAME} PRIVATE /utf-8 /permissive- /Zc:preprocessor /EHsc)
