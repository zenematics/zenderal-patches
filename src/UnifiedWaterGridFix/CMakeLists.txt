cmake_minimum_required(VERSION 3.25)

# Zenderal Unified Water Grid Fix: Bottled Shaders' Unified Water assumes terrain LOD chunks start at multiples of
# their size (Tamriel's grid); Vyn's starts at cell -69, -55. After Unified Water builds a chunk's water, this rebuilds
# it from Unified Water's own cache on the chunk's real cells. AE (Address Library), CommonLibSSE-NG, Microsoft Detours.
project(ZenUnifiedWaterGrid VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")

set(ENABLE_SKYRIM_SE ON CACHE BOOL "" FORCE)
set(ENABLE_SKYRIM_AE ON CACHE BOOL "" FORCE)
set(ENABLE_SKYRIM_VR OFF CACHE BOOL "" FORCE)
set(BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(SKSE_SUPPORT_PATCH_SAFETY OFF CACHE BOOL "" FORCE)

# Shares the CommonLibSSE-NG clone in the repo-root lib/ (gitignored; clone the ng branch of alandtse/CommonLibVR there).
set(COMMONLIB_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../../lib/CommonLibNG" CACHE PATH "CommonLibSSE-NG checkout")
add_subdirectory(${COMMONLIB_DIR} CommonLibNG EXCLUDE_FROM_ALL)

find_path(DETOURS_INCLUDE_DIRS "detours/detours.h" REQUIRED)
find_library(DETOURS_LIBRARY detours REQUIRED)

add_library(${PROJECT_NAME} SHARED src/main.cpp)
target_include_directories(${PROJECT_NAME} PRIVATE src ${DETOURS_INCLUDE_DIRS})
target_precompile_headers(${PROJECT_NAME} PRIVATE src/pch.h)
target_link_libraries(${PROJECT_NAME} PRIVATE CommonLibSSE::CommonLibSSE ${DETOURS_LIBRARY})
target_compile_definitions(${PROJECT_NAME} PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
target_compile_options(${PROJECT_NAME} PRIVATE /utf-8 /permissive- /Zc:preprocessor /EHsc)
