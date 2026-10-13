"""NA section renders for the docs: python sections_na.py -> docs/renders/na_sections.png, na_mic_section.png"""
import subprocess, sys
from pathlib import Path
from build123d import export_stl
import assembly_na

ROOT = Path(__file__).resolve().parents[3]
B = ROOT / "build" / "na"
R = ROOT / "docs" / "renders"


def stl(part, name, tol=0.02):
    export_stl(part, str(B / f"{name}.stl"), tolerance=tol)
    return B / f"{name}.stl"


def main():
    R.mkdir(parents=True, exist_ok=True)
    import barrier_na, face_plate_na, sensor_board_na, jumper_na, standoff_na
    import backcover as bc
    from build123d import Pos
    from params_na import SW_Y, FFC_SLOT_X, MSR_Y, SHT_AT, SB_T, MB_FRONT_Z, MB, BC_FINGERS, SEAT_Z
    rp = sensor_board_na.parts()
    cov = bc.cover_parts()
    seated = lambda part: Pos(0, 0, SEAT_Z) * part
    parts = [(barrier_na.build(), "barrier_placed", "tab:red", "barrier (UL94 V-0)"),
             (face_plate_na.build(), "face_plate_placed", "tab:blue", "face plate"),
             (assembly_na.mains_board(), "mains_board_placed", "tab:green", "mains board"),
             (rp["sensor_board"], "sensor_board_placed", "darkgreen", "sensor board"),
             (rp["msr"], "msr_placed", "dimgray", "MSR-2 with CO2 add-on (model)"),
             (rp["cn2"] + rp["j1"] + rp["sht45"] + rp["passives"] + rp["mic"] + rp["spacers"],
              "sensor_board_parts_placed", "gold", "sensor board parts (CN2, J1, SHT40, mic, spacers)"),
             (rp["pin_board"] + rp["pins"] + rp["posts"] + rp["screws"], "pin_board_placed", "darkorange",
              "pin board, spring pins, spacer posts"),
             (jumper_na.build()["jumper"], "ffc_placed", "cyan", "5 V FFC"),
             (seated(bc.remote_front()), "remote_front_placed", "lightgray", "BILRESA (front half)"),
             (seated(cov["cover"]), "cover_placed", "tan", "replacement back cover"),
             (seated(cov["flex"] + cov["pin_pads"] + cov["stiffener"] + cov["pad_stiffener"]), "cover_flex_placed",
              "peru", "back cover flex, pads, stiffeners"),
             (standoff_na.placed(), "standoffs_placed", "sienna", "board standoffs + screws (nylon, D-57)")]
    args = [f"{stl(part, name)}:{col}|{label}" for part, name, col, label in parts]
    x5, y5 = BC_FINGERS[0]
    cuts = ["x=0#long section: MSR-2 on CN2, remote, rocker well, SHT40, mains board",
            f"x={x5}#spring pins: pin board on its posts, pocket floor, back cover pads, CN2",
            f"y={MSR_Y}@-38,38,-6,18#MSR-2 on CN2 on the sensor board, 0.6 mm radar skin",
            f"y={SW_Y}#rocker well, mains board, WAGO block",
            f"y={y5}@-8,32,-30,16#+5V spring pin from the pin board through the pocket floor",
            f"x={FFC_SLOT_X}@-58,-16,-28,12#5 V FFC: J2, the slit in the barrier's bottom wall, J1 (D-134)",
            f"y={SHT_AT[1]}@-38,38,-6,18#SHT40 on the sensor board under its vents",
            f"z={SB_T / 2}#sensor board on the barrier's collar, crush ribs at its window",
            f"z={MB_FRONT_Z - MB[2] / 2}#mains board: posts, spacer posts, J2"]
    tool = [sys.executable, str(ROOT / "cad" / "tools" / "sections.py")]
    subprocess.run(tool + [str(R / "na_sections.png")] + args +
                   ["--title", "v0.7 sections (dashed red = wall surface, z 0)", "--dpi", "90"] +
                   [a for c in cuts for a in ("--cut", c)], check=True)
    print("wrote", R / "na_sections.png")
    # microphone (D-29, D-83): mic and ADAU7002 on the sensor board, the sound column over them to the hole, zoomed
    from params_na import MIC_AT
    export_stl(rp["sensor_board"] + rp["passives"], str(B / "sensor_board_mic_placed.stl"), tolerance=0.01)
    export_stl(rp["mic"], str(B / "mic_placed.stl"), tolerance=0.01)
    x, y = MIC_AT
    subprocess.run(tool + [str(R / "na_mic_section.png"), f"{B/'barrier_placed.stl'}:tab:red", f"{B/'face_plate_placed.stl'}:tab:blue",
                           f"{B/'sensor_board_mic_placed.stl'}:tab:green", f"{B/'mic_placed.stl'}:tab:purple",
                           "--title", "microphone (D-83): face skin, sound hole and column (blue) on its gasket round "
                           "the mic (purple), sensor board and ADAU7002 (green), barrier (red)",
                           "--cut", f"y={y:.2f}@{x - 7:.1f},{x + 7:.1f},0,16",
                           "--cut", f"x={x:.2f}@{y - 7:.1f},{y + 7:.1f},0,16", "--dpi", "110"], check=True)
    print("wrote", R / "na_mic_section.png")


if __name__ == "__main__":
    main()
