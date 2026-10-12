"""Write the seed kicad/wiring_board.kicad_pro and the custom DRC rules (.kicad_dru).

gen_pcb.py re-saves the project file with netclasses set through the pcbnew API.
"""
import json
from pathlib import Path
from parts import PROJECT, MAINS_GAP

PRJ = Path(__file__).resolve().parents[1] / "kicad"

PRO = {
    "board": {"design_settings": {"rule_severities": {"lib_footprint_issues": "warning",
                                                      "lib_footprint_mismatch": "warning"}}},
    "meta": {"filename": f"{PROJECT}.kicad_pro", "version": 3},
    "schematic": {"meta": {"version": 1}},
    "sheets": [["", "Root"]],
}

MAINS = "(A.NetClass == 'Mains_L' || A.NetClass == 'Mains_N')"
DRU = f"""(version 1)
# Spacing design TARGETS for the wiring board (docs/DESIGN.md D-24, AGENTS.md hard
# constraint 3): 270 V working, overvoltage category III, pollution degree 2, stricter of
# IEC 60664-1 / EN, BS EN, UL and CSA 62368-1. Not a compliance claim: human review required.

(rule "Board edge clearance"
    (constraint edge_clearance (min 0.5mm)))

(rule "Mains copper to board edge >= 1.0 mm"
    (condition "{MAINS}")
    (constraint edge_clearance (min 1.0mm)))

(rule "Mains copper to mounting holes >= 1.0 mm"
    (condition "{MAINS} && B.Type == 'Hole'")
    (constraint hole_clearance (min 1.0mm)))

# Creepage: on this flat board the surface path between copper on one layer is never shorter
# than the straight gap, so the mains targets below are checked as clearance, which lets
# the rated-part exception further down apply per pad (KiCad's creepage check evaluates rule
# conditions without the footprint, so a per-part creepage exception cannot be written).
# Creepage is checked where the path runs round the slot and board edge: mains to 5 V side.

(rule "L-N clearance >= {MAINS_GAP} mm"
    (condition "A.NetClass == 'Mains_L' && B.NetClass == 'Mains_N'")
    (constraint clearance (min {MAINS_GAP}mm)))

(rule "L in to switched/fused L >= {MAINS_GAP} mm"
    (condition "A.NetName == '/L_IN' && (B.NetName == '/L_SW' || B.NetName == '/L_F')")
    (constraint clearance (min {MAINS_GAP}mm)))

(rule "N in to switched N >= {MAINS_GAP} mm"
    (condition "A.NetName == '/N_IN' && B.NetName == '/N_SW'")
    (constraint clearance (min {MAINS_GAP}mm)))

(rule "Different mains nets >= {MAINS_GAP} mm (switched line / fused line across F1, and any other pair)"
    (condition "{MAINS} && (B.NetClass == 'Mains_L' || B.NetClass == 'Mains_N') && A.NetName != B.NetName")
    (constraint clearance (min {MAINS_GAP}mm)))

(rule "Mains to PE >= {MAINS_GAP} mm"
    (condition "{MAINS} && B.NetClass == 'PE'")
    (constraint clearance (min {MAINS_GAP}mm)))

(rule "Mains to 5 V side >= 8.0 mm (reinforced, routed slot under the PSU)"
    (condition "{MAINS} && B.NetClass == 'SELV'")
    (constraint clearance (min 8.0mm))
    (constraint creepage (min 8.0mm)))

(rule "Mains to the PSU's NC pin (DC end) >= 8.0 mm"
    (condition "{MAINS} && B.NetName == 'unconnected-(PS1-NC-Pad5)'")
    (constraint clearance (min 8.0mm)))

# Exception (AGENTS.md hard constraint 3): pins of one rated part keep the part's own
# spacing (WAGO 2604 400 V III/2, Marquardt 1802 ENEC / UL / CSA, IRM-03 4.2 kVAC).
(rule "Pins of one rated part"
    (condition "A.Type == 'Pad' && B.Type == 'Pad' && A.Parent.Reference == B.Parent.Reference")
    (constraint clearance (min 0.2mm)))

# MH2 / MH4: the standoff screws' heads (Ø5.6, back) reach into PS1's courtyard margin (1.95 mm round its
# body) but stay 1.35 mm clear of the body; `make check` tests the heads against the board STEP (D-57).
(rule "Standoff screw heads in PS1's courtyard margin"
    (condition "((A.Reference == 'MH2' || A.Reference == 'MH4') && B.Reference == 'PS1') || (A.Reference == 'PS1' && (B.Reference == 'MH2' || B.Reference == 'MH4'))")
    (constraint courtyard_clearance (min -2mm)))
"""

if __name__ == "__main__":
    PRJ.mkdir(parents=True, exist_ok=True)
    (PRJ / f"{PROJECT}.kicad_pro").write_text(json.dumps(PRO, indent=2) + "\n")
    (PRJ / f"{PROJECT}.kicad_dru").write_text(DRU)
    print("project seed + rules written")
