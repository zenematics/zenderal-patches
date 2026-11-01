"""Zenderal - Pus Beetle Fixes, plugin part: the pus beetle's venom spit no longer knocks the player back.

EGO adds `XionParalyzeKnockback 0008C8` (a Stagger-archetype effect with voicepusheffectscript) as the first effect of
`crChaurusPoisonSpit01 06F6FE`, the spit every pus beetle casts. Override = EGO's record verbatim minus that effect;
the poison (`crChaurusSpitFFAimed 06F6FD`) stays. EGO is the only plugin that overrides this spell.

Usage: python 02-build-spit-without-knockback.py <serialized EGO folder>   (reference/mods/EGO)"""
import os
import sys

NAME = "crChaurusPoisonSpit01 - 06F6FE_Skyrim.esm.yaml"
SRC = os.path.join(sys.argv[1], "Spells", NAME)
HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "..", "PusBeetleFixesESP", "Spells")

raw = open(SRC, "rb").read()
nl = "\r\n" if b"\r\n" in raw else "\n"
lines = raw.decode("utf-8").split(nl)

assert lines[0] == "FormKey: 06F6FE:Skyrim.esm"
knock = ["- BaseEffect: 0008C8:Enderal SE - Gameplay Overhaul.esp", "  Data: {}"]
i = lines.index(knock[0])
assert lines[i:i + 2] == knock, lines[i:i + 2]
del lines[i:i + 2]
assert "- BaseEffect: 06F6FD:Skyrim.esm" in lines and not any("0008C8" in l for l in lines)

os.makedirs(OUT_DIR, exist_ok=True)
open(os.path.join(OUT_DIR, NAME), "wb").write(nl.join(lines).encode("utf-8"))
print("wrote", NAME)
