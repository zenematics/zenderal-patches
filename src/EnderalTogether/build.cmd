@echo off
rem Builds Skyrim Together Reborn (tiltedphoques/TiltedEvolution dev, GPL-3.0) with the Enderal patches in patches\
rem into lib\rebuilds\TiltedEvolution\distrib\bin, then the Together UI into Code\skyrim_ui\dist\UI.
rem Needs (see arch-docs/patches/EnderalTogether.md): the patched clone at lib\rebuilds\TiltedEvolution (no spaces in
rem the path), lib\rebuilds\_env.cmd (VS 2026 Build Tools), portable xmake 3.1.0 at lib\xmake, git reachable without
rem the "&" of "D:\Claude & Tools" (junction lib\gitroot), Node.js (npx runs pnpm 9).
rem Then: compile-scripts.cmd, deserialize SkyrimTogetherESP\, tools\01-package-mo2.py.
setlocal
rem xmake treats a Git Bash parent as an MSYS host; clear its markers.
set MSYSTEM=
set MSYS=
set CHERE_INVOKING=
rem DirectXTK's package build runs CompileShaders.cmd from its own folder, which this variable forbids.
set NoDefaultCurrentDirectoryInExePath=
call "%~dp0..\..\lib\rebuilds\_env.cmd" >nul 2>&1
set "PATH=%~dp0..\..\lib\gitroot\cmd;%~dp0..\..\lib\xmake;%PATH%"
set XMAKE_ROOT=y
set "SRC=%~dp0..\..\lib\rebuilds\TiltedEvolution"
if not exist "%SRC%\xmake.lua" (
    echo lib\rebuilds\TiltedEvolution is missing - clone it and apply patches\ first.
    exit /b 1
)
cd /d "%SRC%"
rem --vs_sdkver: xmake-repo's directxtk check reads the SDK version from the toolchain and fails on nil without it.
xmake config --plat=windows --arch=x64 --mode=releasedbg --skyrim_version=latest --vs_sdkver=10.0.26100.0 --yes
if not "%ERRORLEVEL%"=="0" exit /b 1
xmake -y
if not "%ERRORLEVEL%"=="0" exit /b 1
xmake install -o distrib
if not "%ERRORLEVEL%"=="0" exit /b 1
cd /d "%SRC%\Code\skyrim_ui"
call npx -y pnpm@9 install --frozen-lockfile
if not "%ERRORLEVEL%"=="0" exit /b 1
call npx -y pnpm@9 run deploy:production
if not "%ERRORLEVEL%"=="0" exit /b 1
endlocal
