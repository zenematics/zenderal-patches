@echo off
rem Rebuilds Fitting Room 1.2.0 (maartenharms/fitting-room v1.2.0, GPL-3.0) with the Zenderal patches in patches/,
rem using the VS 2026 Build Tools' bundled CMake/Ninja/vcpkg. The working clone is the gitignored
rem lib\rebuilds\FittingRoom (see arch-docs/patches/FittingRoom.md for how to recreate it).
rem Output: lib\rebuilds\FittingRoom\build\release\FittingRoom.dll -> copy to compiled\FittingRoom.dll.
setlocal
set "VSROOT=C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools"
set "PATH=D:\Claude & Tools\Git\cmd;C:\Program Files (x86)\Microsoft Visual Studio\Installer;%SystemRoot%\System32;%SystemRoot%;%PATH%"
call "%VSROOT%\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 exit /b 1
set "PATH=%VSROOT%\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin;%VSROOT%\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja;%PATH%"
set "VCPKG_ROOT=%VSROOT%\VC\vcpkg"
set "SRC=%~dp0..\..\lib\rebuilds\FittingRoom"
if not exist "%SRC%\CMakeLists.txt" (
    echo lib\rebuilds\FittingRoom is missing - clone maartenharms/fitting-room v1.2.0 there first.
    exit /b 1
)
cd /d "%SRC%"
rem The upstream "release" preset hardcodes a VS Community Ninja path; this is the same configuration spelled out.
rem CommonLibSSE-NG 7.5.4 FetchContent-clones hde64, and CMake's FindGit does not see the "Claude & Tools" PATH entry.
cmake -S . -B build\release -G Ninja ^
    -DCMAKE_BUILD_TYPE=Release ^
    -DGIT_EXECUTABLE="D:\Claude & Tools\Git\cmd\git.exe" ^
    -DCMAKE_CXX_COMPILER=cl.exe ^
    -DCMAKE_TOOLCHAIN_FILE="%VCPKG_ROOT%\scripts\buildsystems\vcpkg.cmake" ^
    -DVCPKG_TARGET_TRIPLET=x64-windows-static-md ^
    -DVCPKG_OVERLAY_TRIPLETS="%SRC%\cmake" ^
    -DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreadedDLL ^
    -DCMAKE_CXX_FLAGS="/permissive- /Zc:preprocessor /EHsc /MP /W4 /we4062 -DWIN32_LEAN_AND_MEAN -DNOMINMAX -DUNICODE -D_UNICODE" ^
    -DVCPKG_APPLOCAL_DEPS=OFF
if errorlevel 1 exit /b 1
cmake --build build\release --config Release
if errorlevel 1 exit /b 1
endlocal
