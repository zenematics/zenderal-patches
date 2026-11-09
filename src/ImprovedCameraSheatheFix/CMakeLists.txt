cmake_minimum_required(VERSION 3.25)

# Zenderal IC Sheathe Fix: runtime byte patches for Improved Camera SE, each gated on the build's bytes.
#   1.1.2.4228: TranslateCamera() drops its first-person camera raise (NPCEyeBone height) while the
#               weapon is drawn, so every sheathe ends with the camera snapping up - patched so the raise
#               always applies; optional combat head bob.
#   2.0.0.2226: CAMERA::Manager::UpdateFOV() writes the profile FOV into the camera every frame in every
#               state but Free/Cinematic - ThirdPerson (and any state listed in the ini) joins them, so
#               SmoothCam's third-person FOV offsets survive.
#               Its SetMode forces first person in its Animation state (sitting, sleeping, scripted idles) -
#               it steps aside there instead, and its ForceThirdPerson hook no longer turns a forced third person
#               (furniture, Immersive Interactions) into its head-camera view.
# SSE 1.5.97 / 1.6.x via CommonLibSSE-NG.
project(ZenICSheatheFix VERSION 1.8.0 LANGUAGES CXX)

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

add_library(${PROJECT_NAME} SHARED src/main.cpp)
target_include_directories(${PROJECT_NAME} PRIVATE src)
target_precompile_headers(${PROJECT_NAME} PRIVATE src/pch.h)
target_link_libraries(${PROJECT_NAME} PRIVATE CommonLibSSE::CommonLibSSE)
target_compile_definitions(${PROJECT_NAME} PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
target_compile_options(${PROJECT_NAME} PRIVATE /utf-8 /permissive- /Zc:preprocessor /EHsc)
