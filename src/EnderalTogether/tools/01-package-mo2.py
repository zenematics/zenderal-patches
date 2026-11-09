"""Assemble the MO2 testing mod "Zenderal - Enderal Together (testing)" from the patched Skyrim Together build.

Layout follows upstream CI's release zip (.github/workflows/windows.yml, "Package build and organize directories"):
GameFiles/Skyrim/* at the Data root, and the launcher, server, CEF files and UI in SkyrimTogetherReborn/.
Zenderal changes on top of that:
  - SkyrimTogether.esp is the Enderal-safe build of SkyrimTogetherESP/ (upstream's four own records, byte-identical;
    its overrides of 03AE9F/03AEA2/03AEA3 would revert Enderal's and EGO's cloak spells, and T03/MagicOrBowCams
    would inject vanilla records Enderal does not have).
  - SkyrimTogetherQuestPatches.esp is left out (its only record is a College of Winterhold scene, absent in Enderal).
  - meshes/Interface/logo is left out (it would replace the main-menu logo).
  - The four Enderal scripts are the ones compile-scripts.cmd built from source; the class-menu one is merged with
    Meditation Area v2.1.0 3rd Person POV Unlock's version.

Usage: python -I tools/01-package-mo2.py <SkyrimTogether.esp built from SkyrimTogetherESP/>
The mod folder is replaced wholesale; nothing else in MO2 is touched.
"""
import pathlib
import shutil
import sys

REPO = pathlib.Path(__file__).resolve().parents[3]
PATCH = REPO / "src" / "EnderalTogether"
CLONE = REPO / "lib" / "rebuilds" / "TiltedEvolution"
MOD = pathlib.Path(r"E:/Zenderal/mods/Zenderal - Enderal Together (testing)")
# Futura Book BT for the overlay UI (patch 0007 declares 'futura-book' in UI/index.html). It is the list's own
# MenuFrameworkFutura build (commercial font from Vel'dun UI, never committed), shipped in Patch Collection.
FUTURA = pathlib.Path(r"E:/Zenderal/mods/Zenderal - Patch Collection/SKSE/Plugins/Fonts/MainFont.ttf")

SKIP_BIN_SUFFIXES = (".pdb", ".lib", ".exp")
OUR_SCRIPTS = ["_00e_class_openclassmenuscript", "_00E_MQ00TemplePuzzleSCN", "_00e_dungeonliftscript",
               "_00e_mqp03_exitdoorscript"]


def main() -> None:
    esp = pathlib.Path(sys.argv[1])
    assert esp.name == "SkyrimTogether.esp" and esp.is_file(), esp
    bin_dir = CLONE / "distrib" / "bin"
    ui_dir = CLONE / "Code" / "skyrim_ui" / "dist" / "UI"
    game_files = CLONE / "GameFiles" / "Skyrim"
    for p in (bin_dir / "SkyrimTogether.exe", bin_dir / "SkyrimTogetherServer.exe", ui_dir / "index.html",
              game_files / "SkyrimTogetherRebornBehaviors"):
        assert p.exists(), f"missing build output: {p}"
    assert "futura-book" in (ui_dir / "index.html").read_text(encoding="utf-8"), "UI built without patch 0007"
    assert FUTURA.is_file() and FUTURA.read_bytes()[:4] == b"\x00\x01\x00\x00", f"Futura TTF missing: {FUTURA}"
    compiled = PATCH / "Scripts" / "compiled"
    for s in OUR_SCRIPTS:
        assert (compiled / f"{s}.pex").is_file(), f"run compile-scripts.cmd first: {s}.pex"

    if MOD.exists():
        shutil.rmtree(MOD)
    runtime = MOD / "SkyrimTogetherReborn"

    # Launcher, server, CEF and assets, minus debug/link files and test runners (as upstream CI does).
    def skip_bin(_dir, names):
        return [n for n in names if n.lower().endswith(SKIP_BIN_SUFFIXES) or n.endswith("Tests.exe")]
    shutil.copytree(bin_dir, runtime, ignore=skip_bin)
    shutil.copytree(ui_dir, runtime / "UI")
    shutil.copy2(FUTURA, runtime / "UI" / "assets" / "futura-book.ttf")

    # Game-side files.
    def skip_game(directory, names):
        d = pathlib.Path(directory)
        out = []
        for n in names:
            rel = (d / n).relative_to(game_files).as_posix().lower()
            if rel in ("skyrimtogether.esp", "skyrimtogetherquestpatches.esp", "meshes"):
                out.append(n)
        return out
    shutil.copytree(game_files, MOD, ignore=skip_game, dirs_exist_ok=True)
    shutil.copy2(esp, MOD / "SkyrimTogether.esp")
    for s in OUR_SCRIPTS:
        shutil.copy2(compiled / f"{s}.pex", MOD / "scripts" / f"{s}.pex")
    shutil.copy2(PATCH / "Scripts" / "source" / "_00e_class_openclassmenuscript.psc",
                 MOD / "scripts" / "source" / "_00e_class_openclassmenuscript.psc")
    # The launcher writes steam_appid.txt (Skyrim SE's 489830, which Enderal's exe DRM is bound to) into the game
    # root on every start. Root Builder (copy mode) moves a new root file into overwrite\Root, which then deploys in
    # every profile; shipping the same file in this mod's Root keeps it to the profiles that enable this mod.
    (MOD / "Root").mkdir()
    (MOD / "Root" / "steam_appid.txt").write_bytes(b"489830")

    # Checks: what must and must not be there.
    assert not (MOD / "SkyrimTogetherQuestPatches.esp").exists()
    assert not (MOD / "meshes").exists()
    assert not list(runtime.glob("*.pdb")) and not list(runtime.glob("*Tests.exe"))
    for s in OUR_SCRIPTS:
        assert (MOD / "scripts" / f"{s}.pex").read_bytes() == (compiled / f"{s}.pex").read_bytes()
    files = [p for p in MOD.rglob("*") if p.is_file()]
    size = sum(p.stat().st_size for p in files)
    print(f"{MOD}: {len(files)} files, {size / 1e6:.0f} MB")
    for p in sorted(MOD.iterdir()):
        print("  ", p.name + ("/" if p.is_dir() else ""))


if __name__ == "__main__":
    main()
