@echo off
rem Builds ZenProphecyUI.dll (AE 1.7.104, Address Library) with the VS 2026 Build Tools' bundled CMake/Ninja/vcpkg.
setlocal
set "VSROOT=C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools"
set "PATH=D:\Claude & Tools\Git\cmd;C:\Program Files (x86)\Microsoft Visual Studio\Installer;%SystemRoot%\System32;%SystemRoot%;%PATH%"
call "%VSROOT%\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 exit /b 1
set "PATH=%VSROOT%\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin;%VSROOT%\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja;%PATH%"
set "VCPKG_ROOT=%VSROOT%\VC\vcpkg"
cd /d "%~dp0"
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_TOOLCHAIN_FILE="%VCPKG_ROOT%\scripts\buildsystems\vcpkg.cmake" -DVCPKG_TARGET_TRIPLET=x64-windows-static -DVCPKG_APPLOCAL_DEPS=OFF
if errorlevel 1 exit /b 1
cmake --build build --config Release
if errorlevel 1 exit /b 1
endlocal
