r"""Generate the Undercity Water Fix plugin YAML -- never hand-edit its Waters/.

Report (players, video 2026-11-15): flat grey sheets in the Ark Undercity pits outside Meddok's Fishery
("Divide and Conquer"); they mirror the fishing net above them, so they are a water surface. The water there is
SureAI's Water1024Murky activator 062A60 with water type MurkyWater 062A72, which no plugin in the list overrides
(Water for Enderal CS included). The working guess is that Bottled Shaders' water shading turns the type's
reflectivity 0.55 into a light, mirror-like sheet in a dark interior.

GUESS FIX, unverified: MurkyWater copied verbatim from base Enderal 2.1 with WaterReflectivity 0.55 -> REFLECTIVITY.
Nothing else changes. MurkyWater is also used by about 20 other interiors (Ark tomb, Alt Askamahn, Soltyris, ...),
which get the same duller water. Asserted: exactly one field changes.
"""
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
NAME = "MurkyWater - 062A72_Skyrim.esm.yaml"
SRC = os.path.join(ROOT, "reference", "base-2.1.4.4", "Skyrim", "Waters", NAME)
OUT = os.path.join(ROOT, "src", "UndercityWaterFix", "UndercityWaterFixESP", "Waters", NAME)
OLD = "WaterReflectivity: 0.55"
REFLECTIVITY = "0.1"


def main():
    text = open(SRC, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in text else "\n"
    if text.count(OLD + nl) != 1:
        raise SystemExit(f"{SRC}: expected exactly one '{OLD}'")
    new = text.replace(OLD + nl, f"WaterReflectivity: {REFLECTIVITY}{nl}")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8", newline="").write(new)
    changed = [a for a, b in zip(text.split(nl), new.split(nl)) if a != b]
    assert len(changed) == 1, changed
    print(f"wrote {OUT}: {OLD} -> {REFLECTIVITY}")


if __name__ == "__main__":
    main()
