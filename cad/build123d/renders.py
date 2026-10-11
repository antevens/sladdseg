"""Section renders of the assembly for the docs: python renders.py -> docs/renders/*.png"""
import subprocess, sys
from pathlib import Path
from build123d import export_stl
import assembly

ROOT = Path(__file__).resolve().parents[2]
B = ROOT / "build"
R = ROOT / "docs" / "renders"


def stl(part, name, tol=0.02):
    export_stl(part, str(B / f"{name}.stl"), tolerance=tol)
    return B / f"{name}.stl"


def main():
    R.mkdir(parents=True, exist_ok=True)
    import insert, trim, ring, jumper, standoff
    import backcover as bc
    from build123d import Pos
    from params import SW_Y, PASS_E, MSR_Y, SHT_AT, RING_T, WB_FRONT_Z, WB, BC_FINGERS, SEAT_Z
    rp = ring.parts()
    cov = bc.cover_parts()
    seated = lambda part: Pos(0, 0, SEAT_Z) * part
    parts = [(insert.build(), "insert_placed", "tab:red", "insert (UL94 V-0)"),
             (trim.build(), "trim_placed", "tab:blue", "face plate (trim)"),
             (assembly.wiring_board(), "wiring_board_placed", "tab:green", "wiring board"),
             (rp["ring"], "ring_placed", "darkgreen", "ring board"),
             (rp["msr"], "msr_placed", "dimgray", "MSR-2 with CO2 add-on (model)"),
             (rp["cn2"] + rp["j1"] + rp["sht45"] + rp["passives"] + rp["mic"] + rp["spacers"],
              "ring_parts_placed", "gold", "ring board parts (CN2, J1, SHT40, mic, spacers)"),
             (rp["riser"] + rp["pins"] + rp["posts"] + rp["screws"], "riser_placed", "darkorange",
              "riser, spring pins, spacer posts"),
             (jumper.build()["jumper"], "ffc_placed", "cyan", "5 V FFC"),
             (seated(bc.remote_front()), "remote_front_placed", "lightgray", "BILRESA (front half)"),
             (seated(cov["cover"]), "cover_placed", "tan", "replacement back cover"),
             (seated(cov["flex"] + cov["pin_pads"] + cov["stiffener"] + cov["pad_stiffener"]), "cover_flex_placed",
              "peru", "back cover flex, pads, stiffeners"),
             (standoff.placed(), "standoffs_placed", "sienna", "board standoffs + screws (nylon, D-57)")]
    args = [f"{stl(part, name)}:{col}|{label}" for part, name, col, label in parts]
    x5, y5 = BC_FINGERS[0]
    cuts = ["x=0#long section: MSR-2 on CN2, remote, rocker well, SHT40, wiring board",
            f"x={x5}#spring pins: riser on its posts, pocket floor, back cover pads, CN2",
            f"y={MSR_Y}@-38,38,-6,18#MSR-2 on CN2 on the ring board, 0.6 mm radar skin",
            f"y={SW_Y}#rocker well, wiring board, WAGO block",
            f"y={y5}@-8,32,-30,16#+5V spring pin from the riser through the pocket floor",
            f"y={PASS_E[1]}#5 V FFC through the pass-through",
            f"y={SHT_AT[1]}@-38,38,-6,18#SHT40 on the ring board under its vents",
            f"z={RING_T / 2}#ring board on the insert's collar, crush ribs at its window",
            f"z={WB_FRONT_Z - WB[2] / 2}#wiring board: posts, spacer posts, J2"]
    tool = [sys.executable, str(ROOT / "cad" / "tools" / "sections.py")]
    subprocess.run(tool + [str(R / "v0.4_sections.png")] + args +
                   ["--title", "v0.4 sections (dashed red = wall surface, z 0)", "--dpi", "90"] +
                   [a for c in cuts for a in ("--cut", c)], check=True)
    print("wrote", R / "v0.4_sections.png")
    # microphone (D-29, D-83): mic and ADAU7002 on the ring board, the sound column over them to the hole, zoomed
    from params import MIC_AT
    export_stl(rp["ring"] + rp["passives"], str(B / "ring_mic_placed.stl"), tolerance=0.01)
    export_stl(rp["mic"], str(B / "mic_placed.stl"), tolerance=0.01)
    x, y = MIC_AT
    subprocess.run(tool + [str(R / "v0.4_mic_section.png"), f"{B/'insert_placed.stl'}:tab:red", f"{B/'trim_placed.stl'}:tab:blue",
                           f"{B/'ring_mic_placed.stl'}:tab:green", f"{B/'mic_placed.stl'}:tab:purple",
                           "--title", "microphone (D-83): face skin, sound hole and column (blue) on its gasket round "
                           "the mic (purple), ring board and ADAU7002 (green), insert (red)",
                           "--cut", f"y={y:.2f}@{x - 7:.1f},{x + 7:.1f},0,16",
                           "--cut", f"x={x:.2f}@{y - 7:.1f},{y + 7:.1f},0,16", "--dpi", "110"], check=True)
    print("wrote", R / "v0.4_mic_section.png")


if __name__ == "__main__":
    main()
