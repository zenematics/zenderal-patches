cmake_minimum_required(VERSION 3.25)

# Zenderal Key Trace: reads dTry's Key Utils' config/custom/*.ini key-trace bindings (the Stances hotkeys)
# on AE, where the only DtryKeyUtil.dll that loads (PaulMix's extend v3.3) has no config reader.
# AE (Address Library), CommonLibSSE-NG.
project(ZenKeyTrace VERSION 1.0.0 LANGUAGES CXX)

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

find_path(SIMPLEINI_INCLUDE_DIRS "SimpleIni.h")

add_library(${PROJECT_NAME} SHARED src/main.cpp)
target_include_directories(${PROJECT_NAME} PRIVATE src ${SIMPLEINI_INCLUDE_DIRS})
target_precompile_headers(${PROJECT_NAME} PRIVATE src/pch.h)
target_link_libraries(${PROJECT_NAME} PRIVATE CommonLibSSE::CommonLibSSE)
target_compile_definitions(${PROJECT_NAME} PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
target_compile_options(${PROJECT_NAME} PRIVATE /utf-8 /permissive- /Zc:preprocessor /EHsc)
