cmake_minimum_required(VERSION 3.25)

# Casting Bar (zax-ftw/CastingBar 3.0.0, Apache-2.0) rebuilt for 1.7.104 with the repo's CommonLibSSE-NG,
# plus Zenderal's SKSE Menu Framework page, per-widget layouts and Ultimate Immersion Toggle hiding.
# Ships as CastingBar.dll so it reads the existing CastingBar.ini. AE (Address Library).
project(CastingBar VERSION 3.0.1 LANGUAGES CXX)

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

find_package(magic_enum CONFIG REQUIRED)
find_path(SIMPLEINI_INCLUDE_DIRS "SimpleIni.h")

set(SOURCE_FILES
	src/Main.cpp
	src/Settings.cpp
	src/CastingBar.cpp
	src/StateController.cpp
	src/EventHandler.cpp
	src/UI.cpp
	src/States/DefaultState.cpp
	src/States/RangedState.cpp
	src/States/MagicState.cpp
	src/States/RightMagicState.cpp
	src/States/LeftMagicState.cpp
	src/States/VoiceState.cpp
	src/Hooks/PlayerCharacter.cpp)

add_library(${PROJECT_NAME} SHARED ${SOURCE_FILES})
target_include_directories(${PROJECT_NAME} PRIVATE src ${SIMPLEINI_INCLUDE_DIRS})
target_precompile_headers(${PROJECT_NAME} PRIVATE src/PCH.h)
target_link_libraries(${PROJECT_NAME} PRIVATE CommonLibSSE::CommonLibSSE magic_enum::magic_enum)
target_compile_definitions(${PROJECT_NAME} PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
target_compile_options(${PROJECT_NAME} PRIVATE /utf-8 /permissive- /Zc:preprocessor /EHsc)
