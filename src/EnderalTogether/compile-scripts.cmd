@echo off
rem Compiles Enderal Together's four Enderal script patches (the class-menu one merged with Meditation Area's 3rd-person
rem version, in Scripts\source) into Scripts\compiled. Enderal's tree comes first: the compiler's -i is first-wins.
rem The other three sources come from the patched clone's GameFiles (patch 0003), which also has SkyrimTogetherUtils.psc.
setlocal
set "PC=E:\Zenderal\mods\Creation Kit\Root\Papyrus Compiler\PapyrusCompiler.exe"
set "OUR=%~dp0Scripts\source"
set "STR=%~dp0..\..\lib\rebuilds\TiltedEvolution\GameFiles\Skyrim\scripts\source"
set "OUT=%~dp0Scripts\compiled"
set "IMP=%OUR%;%STR%;E:\zenderal-patches\papyrus-source\enderal-2.1.4.4\source\scripts;E:\Zenderal\mods\Skyrim Script Extender (SKSE64) Scripts\Scripts\Source;E:\zenderal-patches\papyrus-source\vanilla-stubs"
if not exist "%STR%\SkyrimTogetherUtils.psc" (
    echo lib\rebuilds\TiltedEvolution is missing or unpatched - see arch-docs/patches/EnderalTogether.md.
    exit /b 1
)
"%PC%" "%OUR%\_00e_class_openclassmenuscript.psc" -f="TESV_Papyrus_Flags.flg" -i="%IMP%" -o="%OUT%" -optimize
if errorlevel 1 exit /b 1
for %%S in (_00E_MQ00TemplePuzzleSCN _00e_dungeonliftscript _00e_mqp03_exitdoorscript) do (
    "%PC%" "%STR%\%%S.psc" -f="TESV_Papyrus_Flags.flg" -i="%IMP%" -o="%OUT%" -optimize
    if errorlevel 1 exit /b 1
)
endlocal
