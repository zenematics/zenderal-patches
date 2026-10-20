@echo off
rem Builds Precision.dll (ersh1/Precision 2.0.6, GPL-3.0) from upstream\ for SSE 1.5.97 and AE (1.6.x / 1.7.104) with the
rem VS 2026 Build Tools' bundled CMake/Ninja/vcpkg, against CommonLibSSE-NG (alandtse/CommonLibVR) at 8339e6d (2026-09-02 02:09:16), the parent of
rem 231543d, which added Havok types that clash with Precision's own Havok.h. (d27f409 on the same
rem branch is libxse-style and lacks NG APIs Precision uses, e.g. REL::VariantOffset.)
setlocal
set "VSROOT=C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools"
set "PATH=D:\Claude & Tools\Git\cmd;C:\Program Files (x86)\Microsoft Visual Studio\Installer;%SystemRoot%\System32;%SystemRoot%;%PATH%"
call "%VSROOT%\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 exit /b 1
set "PATH=%VSROOT%\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin;%VSROOT%\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja;%PATH%"
set "VCPKG_ROOT=%VSROOT%\VC\vcpkg"
cd /d "%~dp0"
set "CommonLibSSEPath=%~dp0lib\CommonLibNG-8339e6d"
set "CompiledPluginsPath=%~dp0build\out"
cmake -S upstream -B build2 -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_TOOLCHAIN_FILE="%VCPKG_ROOT%\scripts\buildsystems\vcpkg.cmake" -DVCPKG_TARGET_TRIPLET=x64-windows-static-md -DVCPKG_APPLOCAL_DEPS=OFF -DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreadedDLL -DCOPY_OUTPUT=OFF -DENABLE_SKYRIM_SE=ON -DENABLE_SKYRIM_AE=ON -DENABLE_SKYRIM_VR=OFF -DSKSE_SUPPORT_PATCH_SAFETY=OFF -DBUILD_TESTS=OFF
if errorlevel 1 exit /b 1
cmake --build build2 --config Release
if errorlevel 1 exit /b 1
endlocal
