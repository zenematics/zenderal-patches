"""Zenderal - MQ16 Yuslan Kneel Fix: a watchdog for The Shards of Order, Part II's corpse scene.

Scene MQ16_SC04_Journey_04 (147193:Skyrim.esm), City of a Thousand Floods: after Yuslan's "Good question."
(action 4, phase 2) phase 3 completes only when Yuslan is in furniture state Sit. His package
MQ16_SC04_SitTarget (1471B7) kneels him at KneelingMarker ref 1471B6 beside the fourth corpse. A player's Yuslan
never knelt and the quest stopped there (Discord report 2026-11-14); a console disable/enable of Yuslan freed it.
No plugin, mesh or animation set in the list touches any of it (see arch-docs/patches/MQ16YuslanKneelFix.md).

This copies SureAI's _00E_MQ16_Functions (ScriptsEnderal.zip 2.1.4.4), adds one call at the end of
DisableFollower_SC04 (the scene's phase 0 end) and appends the watchdog (non-property variables only), then:
- compiles SureAI's unmodified source and checks its strings against the game's shipped .pex (no source drift);
- compiles the fork and checks it keeps every shipped string and declares the same properties.

Usage (repo root): python src/MQ16YuslanKneelFix/tools/01-build-yuslan-kneel-fix.py
"""
import json
import os
import re
import struct
import subprocess
import sys
import tempfile

import lz4.frame

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
OUT_SRC = os.path.join(HERE, "..", "Scripts", "source")
OUT_PEX = os.path.join(HERE, "..", "Scripts", "compiled")
TOOLS = json.load(open(os.path.join(REPO, ".claude", "config", "tools.json"), encoding="utf-8-sig"))
SRC = TOOLS["papyrusSource"]["enderal"]
DATA = os.path.join(TOOLS["gameRoot"], "Data")
SCRIPT = "_00E_MQ16_Functions"
BSAS = ("E - Misc.bsa", "E - Update.bsa", "Enderal - Forgotten Stories.bsa", "Skyrim - Misc.bsa")

HOOK_OLD = re.compile(
    rb"(Function DisableFollower_SC04\(\)\r?\n\r?\n"
    rb"\t_00E_Func_SetNPCAsCompanion\.SetNPCAsCompanion\(_00E_MC_TealorREF, False\)\r?\n"
    rb"\t_00E_Func_SetNPCAsCompanion\.SetNPCAsCompanion\(_00E_MC_YuslanREF, False\)\r?\n"
    rb"\t_00E_Func_SetNPCAsCompanion\.SetNPCAsCompanion\(akCompanion, False\)\r?\n)"
    rb"(\r?\nEndFunction)")
HOOK_NEW = (b"\t; ZP: watch phase 3, where the scene waits for Yuslan to kneel (MQ16 Yuslan Kneel Fix)\n"
            b"\tZP_StartKneelWatch()\n")

WATCHDOG = r'''
;=====================================================================================
;                 ZP (Zenderal - MQ16 Yuslan Kneel Fix): SC04 kneel watchdog
;=====================================================================================
; Scene MQ16_SC04_Journey_04 (147193): after Yuslan's "Good question." (action 4, phase 2), phase 3 waits
; until Yuslan is in furniture state Sit. His package MQ16_SC04_SitTarget (1471B7) kneels him at the
; KneelingMarker ref 1471B6 by the fourth corpse. A player's Yuslan never knelt and the quest stopped there
; (report 2026-11-14); a console disable/enable of Yuslan freed it. DisableFollower_SC04 (phase 0's end)
; starts this watchdog. It times phases 3-4 (action 4 done, Yuslan's next line, action 20, not yet done),
; logs Yuslan's state as [ZP MQ16 kneel] and, if he has not knelt, nudges him one step at a time, up to
; the disable/enable that worked. Non-property variables only: no property is added to SureAI's script.

int iZPPhaseSeconds     ; seconds spent in phases 3-4
int iZPUnseatedSeconds  ; of those, seconds Yuslan was not sitting
int iZPStep
bool bZPSeatedReset
bool bZPInTick

Function ZP_StartKneelWatch()

	iZPPhaseSeconds = 0
	iZPUnseatedSeconds = 0
	iZPStep = 0
	bZPSeatedReset = False
	bZPInTick = False
	Debug.Trace("[ZP MQ16 kneel] watch started (SC04 phase 0 done)")
	RegisterForSingleUpdate(1.0)

EndFunction

Event OnUpdate()

	If bZPInTick
		; a step is waiting on a latent call: keep the chain alive, do nothing else
		RegisterForSingleUpdate(1.0)
		Return
	EndIf

	If !MQ16_SC04_Journey_04.IsPlaying() || MQ16_SC04_Journey_04.IsActionComplete(20) || GetCurrentStageID() >= 60
		Debug.Trace("[ZP MQ16 kneel] watch ended: playing=" + MQ16_SC04_Journey_04.IsPlaying() + " yuslanLine=" + MQ16_SC04_Journey_04.IsActionComplete(20) + " stage=" + GetCurrentStageID() + " | phases 3-4 " + iZPPhaseSeconds + " s, not kneeling " + iZPUnseatedSeconds + " s")
		Return
	EndIf

	; next tick first: nothing below may end the watch
	RegisterForSingleUpdate(1.0)

	If MQ16_SC04_Journey_04.IsActionComplete(4)
		bZPInTick = True
		ZP_KneelTick()
		bZPInTick = False
	EndIf

EndEvent

Function ZP_KneelTick()

	Actor akY = _00E_MC_YuslanREF
	iZPPhaseSeconds += 1
	bool bSeated = akY.GetSitState() == 3
	If !bSeated
		iZPUnseatedSeconds += 1
	EndIf

	If iZPPhaseSeconds == 1
		ZP_KneelLog("phase 3 (after 'Good question.')")
	EndIf

	If !bSeated
		If iZPStep == 0 && iZPUnseatedSeconds >= 12
			iZPStep = 1
			ZP_KneelLog("not kneeling after 12 s: EvaluatePackage")
			akY.EvaluatePackage()
		ElseIf iZPStep == 1 && iZPUnseatedSeconds >= 20
			iZPStep = 2
			ZP_KneelLog("not kneeling after 20 s: sheathe, IdleForceDefaultState, EvaluatePackage")
			If akY.IsWeaponDrawn()
				akY.SheatheWeapon()
			EndIf
			Debug.SendAnimationEvent(akY, "IdleForceDefaultState")
			akY.EvaluatePackage()
		ElseIf iZPStep == 2 && iZPUnseatedSeconds >= 30
			iZPStep = 3
			ZP_KneelLog("not kneeling after 30 s: disable/enable (the console fix)")
			ZP_ResetYuslan()
			ZP_KneelLog("after disable/enable")
		ElseIf iZPStep == 3 && iZPUnseatedSeconds >= 45
			iZPStep = 4
			ZP_KneelLog("not kneeling after 45 s: MoveTo the kneel marker and activate it")
			ObjectReference akKneel = Game.GetForm(0x001471B6) as ObjectReference
			If akKneel
				akY.MoveTo(akKneel)
				akKneel.Activate(akY)
			EndIf
			akY.EvaluatePackage()
		ElseIf iZPStep == 4 && iZPUnseatedSeconds >= 60
			iZPStep = 5
			ZP_KneelLog("not kneeling after 60 s: disable/enable again")
			ZP_ResetYuslan()
			ZP_KneelLog("after disable/enable")
		ElseIf iZPStep >= 5 && iZPUnseatedSeconds % 30 == 0
			ZP_KneelLog("STALL: still not kneeling. Console: prid 102DED, disable, enable")
		EndIf
	ElseIf !bZPSeatedReset && iZPPhaseSeconds - iZPUnseatedSeconds >= 40
		; his next line takes ~6 s once he kneels: 40 s kneeling with no line = the scene does not see him seated
		bZPSeatedReset = True
		ZP_KneelLog("kneeling 40 s but the scene has not moved on: disable/enable")
		ZP_ResetYuslan()
		ZP_KneelLog("after disable/enable")
	EndIf

EndFunction

Function ZP_ResetYuslan()

	Actor akY = _00E_MC_YuslanREF
	akY.Disable()
	Utility.Wait(0.5)
	akY.Enable()
	akY.EvaluatePackage()

EndFunction

Function ZP_KneelLog(string sWhat)

	Actor akY = _00E_MC_YuslanREF
	ObjectReference akKneel = Game.GetForm(0x001471B6) as ObjectReference
	Actor akCalia = (GetAlias(1) as ReferenceAlias).GetActorRef()
	string s = "[ZP MQ16 kneel] " + sWhat + " | t=" + iZPPhaseSeconds + " notKneeling=" + iZPUnseatedSeconds
	s += " | Yuslan sit=" + akY.GetSitState() + " pkg=" + akY.GetCurrentPackage() + " disabled=" + akY.IsDisabled() + " 3D=" + akY.Is3DLoaded()
	s += " pos=" + akY.GetPositionX() + "," + akY.GetPositionY() + "," + akY.GetPositionZ()
	If akKneel
		s += " | to marker: Yuslan=" + akY.GetDistance(akKneel) + " player=" + PlayerREF.GetDistance(akKneel) + " Tealor=" + _00E_MC_TealorREF.GetDistance(akKneel)
		If akCalia
			s += " Calia=" + akCalia.GetDistance(akKneel)
		EndIf
		If akCompanion
			s += " companion=" + akCompanion.GetDistance(akKneel)
		EndIf
	EndIf
	s += " | weaponDrawn=" + akY.IsWeaponDrawn() + " combat=" + akY.GetCombatState() + " bleedout=" + akY.IsBleedingOut() + " unconscious=" + akY.IsUnconscious() + " dialogue=" + akY.IsInDialogueWithPlayer()
	s += " R=" + akY.GetEquippedObject(1) + " L=" + akY.GetEquippedObject(0)
	s += " | graph animDriven=" + akY.GetAnimationVariableBool("bAnimationDriven") + " equipping=" + akY.GetAnimationVariableBool("IsEquipping") + " unequipping=" + akY.GetAnimationVariableBool("IsUnequipping") + " stagger=" + akY.GetAnimationVariableBool("IsStaggering") + " block=" + akY.GetAnimationVariableBool("IsBlocking") + " jump=" + akY.GetAnimationVariableBool("bInJumpState") + " synced=" + akY.GetAnimationVariableBool("bIsSynced") + " iState=" + akY.GetAnimationVariableInt("iState")
	s += " | scene playing=" + MQ16_SC04_Journey_04.IsPlaying() + " a4=" + MQ16_SC04_Journey_04.IsActionComplete(4) + " a19=" + MQ16_SC04_Journey_04.IsActionComplete(19) + " a20=" + MQ16_SC04_Journey_04.IsActionComplete(20)
	Debug.Trace(s)

EndFunction
'''


def bsa_file(bsa, want):
    """Bytes of one file from an SSE v105 BSA, or None."""
    f = open(bsa, "rb")
    _, ver, _, aflags, nfold, _, _, lfile, _ = struct.unpack("<4sIIIIIIII", f.read(36))
    folders = [struct.unpack("<QIIQ", f.read(24)) for _ in range(nfold)]
    recs = []
    for _, cnt, _, _ in folders:
        n = f.read(1)[0]
        name = f.read(n)[:-1].decode("cp1252")
        for _ in range(cnt):
            _, size, off = struct.unpack("<QII", f.read(16))
            recs.append((name, size, off))
    names = f.read(lfile).split(b"\0")
    for (folder, size, off), name in zip(recs, names):
        if (folder + "\\" + name.decode("cp1252")).lower() != want.lower():
            continue
        comp = bool(aflags & 4) ^ bool(size & 0x40000000)
        f.seek(off)
        data = f.read(size & 0x3FFFFFFF)
        if aflags & 0x100:
            data = data[1 + data[0]:]
        return lz4.frame.decompress(data[4:]) if comp else data
    return None


def pex_strings(data):
    i = 16
    for _ in range(3):
        i += 2 + struct.unpack_from(">H", data, i)[0]
    n = struct.unpack_from(">H", data, i)[0]
    i += 2
    out = []
    for _ in range(n):
        ln = struct.unpack_from(">H", data, i)[0]
        out.append(data[i + 2:i + 2 + ln].decode("latin1"))
        i += 2 + ln
    return out


def normal(strings):
    return {s.lower() for s in strings if not s.startswith("::temp")}


TYPE_NAMES = {"float", "int", "bool", "string"}
PROPERTY = re.compile(rb"(?im)^\s*[\w\[\]]+\s+Property\s+(\w+)")


def compile_one(psc, outdir, imports):
    # The compiler resolves the script by NAME through -i, first wins: without psc's own folder first it
    # silently compiles SureAI's copy of the same name from the Enderal source tree (it did, 2026-11-14).
    imports = os.path.dirname(os.path.abspath(psc)) + ";" + imports
    r = subprocess.run([TOOLS["papyrusCompiler"], psc, "-f=" + TOOLS.get("papyrusFlags", "TESV_Papyrus_Flags.flg"),
                        "-i=" + imports, "-o=" + outdir, "-op"], capture_output=True, text=True)
    assert "1 succeeded" in r.stdout, r.stdout + r.stderr
    return open(os.path.join(outdir, os.path.splitext(os.path.basename(psc))[0] + ".pex"), "rb").read()


def main():
    os.makedirs(OUT_SRC, exist_ok=True)
    os.makedirs(OUT_PEX, exist_ok=True)
    imports = ";".join([SRC, TOOLS["papyrusSource"]["skse"], TOOLS["papyrusSource"]["vanilla"]] + TOOLS.get("importDirs", []))
    raw = open(os.path.join(SRC, SCRIPT.lower() + ".psc"), "rb").read()
    assert re.match(rb"(?i)\s*scriptname\s+" + SCRIPT.encode(), raw), "not SureAI's script"
    assert b"ZP_" not in raw and not re.search(rb"(?im)^\s*Event\s+OnUpdate", raw), "SureAI's script already has an OnUpdate"
    assert len(HOOK_OLD.findall(raw)) == 1, "DisableFollower_SC04 is not as expected"

    shipped = None
    for b in BSAS:
        p = os.path.join(DATA, b)
        if os.path.isfile(p):
            shipped = bsa_file(p, "scripts\\" + SCRIPT.lower() + ".pex")
            if shipped:
                print(f"  shipped .pex from {b}")
                break
    assert shipped, "not found in Enderal's BSAs"
    a = normal(pex_strings(shipped))

    with tempfile.TemporaryDirectory() as tmp:
        orig = os.path.join(tmp, SCRIPT + ".psc")
        open(orig, "wb").write(raw)
        rebuilt = normal(pex_strings(compile_one(orig, tmp, imports)))
    drift = (a - rebuilt) - TYPE_NAMES
    assert not drift and not (rebuilt - a), ("SureAI's source differs from the shipped .pex", sorted(drift)[:8], sorted(rebuilt - a)[:8])
    print(f"  SureAI's source rebuilds to the shipped .pex ({len(a)} strings)")

    new = HOOK_OLD.sub(lambda m: m.group(1) + HOOK_NEW + m.group(2), raw)
    new = new.rstrip(b"\r\n") + b"\r\n" + WATCHDOG.replace("\n", "\r\n").encode("ascii")
    props_old, props_new = PROPERTY.findall(raw), PROPERTY.findall(new)
    assert props_old == props_new, "the fork must declare exactly SureAI's properties"
    dst = os.path.join(OUT_SRC, SCRIPT + ".psc")
    open(dst, "wb").write(new)
    ours = normal(pex_strings(compile_one(dst, OUT_PEX, imports)))
    lost = (a - ours) - TYPE_NAMES
    assert not lost, ("the fork lost shipped strings", sorted(lost)[:8])
    added = ours - a
    assert "zp_startkneelwatch" in added and any("[zp mq16 kneel]" in s for s in added), "the watchdog is not in the .pex"
    print(f"  fork compiled: all shipped strings kept, {len(props_new)} properties as SureAI's, +{len(ours - a)} strings")
    print(f"  -> {os.path.relpath(dst, REPO)}")
    print(f"  -> {os.path.relpath(os.path.join(OUT_PEX, SCRIPT + '.pex'), REPO)}")


if __name__ == "__main__":
    sys.exit(main())
