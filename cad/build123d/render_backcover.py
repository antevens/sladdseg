"""Replacement back cover renders (D-35): xvfb-run python render_backcover.py -> docs/renders/bc_*.png"""
import sys
from pathlib import Path
from build123d import Pos
import render3d as r3
import backcover as bc

sys.path.insert(0, str(Path(__file__).resolve().parent / "eu"))
import params_eu as eu                                      # noqa: E402

r3.COL.update({"cover": "#e9e6df", "flex": "#d99a2b", "stiffener": "#2f7a46", "pads": "#e3c565",
               "pin_pads": "#c9a227", "contacts": "#c9a227", "regulator": "#2b2b2b", "pad_stiffener": "#2f7a46", "steel": "#6d7075", "bf_pins": "#c9a227",
               "cap": "#8d949b", "front_half": "#fbfaf6"})


def placed(parts, z):
    return {k: Pos(0, 0, z) * v for k, v in parts.items()}


def eu_context():
    import cap_eu
    import trim_eu
    return {"cap": cap_eu.build(), "trim": trim_eu.build()}


def main():
    cov = bc.cover_parts(free=True)
    r3.shot("bc_inside", cov, [(70, -120, 140), (0, -6, 4), (0, 0, 1)], size=(1300, 1100), head=0.9)
    r3.shot("bc_back", cov, [(60, -90, -140), (4, -4, 0), (0, 0, 1)], size=(1300, 1100), head=0.9)
    # in the EU plate: cover and remote lifted above the pocket, the battery-free pins through the cap
    import boards_eu
    ctx = {**eu_context(), "bf_pins": boards_eu.bf_pins()}
    lift = eu.SEAT_Z
    ex = {**ctx, **placed(bc.cover_parts(), lift + 25), "front_half": Pos(0, 0, lift + 50) * bc.remote_front()}
    r3.shot("bc_exploded", ex, [(230, -200, 130), (0, 0, 25), (0, 0, 1)], size=(1400, 1300), head=0.85,
            alpha={"trim": 0.2})


def finger_section():
    """2D sections in the NA plate, cover frame (z 0 = the cover's back face): through the +5V pin (pocket floor,
    riser, spring pin, window, pad) and through the VBAT finger (block, end section, finger, the remote's plate)."""
    import subprocess
    import insert
    import ring
    from build123d import Box, export_stl
    from params import SEAT_Z, BC_TERM_SETBACK
    root = Path(__file__).resolve().parents[2]
    out = root / "build" / "backcover"
    out.mkdir(parents=True, exist_ok=True)
    tool = [sys.executable, str(root / "cad" / "tools" / "sections.py")]
    rp = ring.parts()
    na = lambda part: Pos(0, 0, -SEAT_Z) * part              # plate parts into the cover's frame

    def run(name, parts, title, cuts, dpi=120):
        args = []
        for k, (part, col, label) in parts.items():
            export_stl(part, str(out / f"{name}_{k}.stl"), tolerance=0.01)
            args.append(f"{out / f'{name}_{k}.stl'}:{col}|{label}")
        subprocess.run(tool + [str(r3.R / f"{name}.png")] + args + ["--title", title, "--dpi", str(dpi)] +
                       [a for c in cuts for a in ("--cut", c)], check=True)
        print("wrote", r3.R / f"{name}.png")

    x, y = bc.BC_FINGERS[0]
    run("bc_pin_section", {
        "insert": (na(insert.build()), "tab:red", "insert: pocket floor (UL94 V-0)"),
        "riser": (na(rp["riser"] + rp["posts"] + rp["screws"]), "tab:green", "riser board, spacer posts"),
        "pin": (na(rp["pins"]), "goldenrod", "spring pin (Harwin P70-2200045), working height"),
        "cover": (bc.cover(), "tab:blue", "replacement back cover"),
        "flex": (bc.flex() + bc.pad_stiffener(), "tab:orange", "cover flex + FR4 stiffener"),
        "pad": (bc.pin_pads(), "tab:purple", "gold pad on the flex underside")},
        "+5V spring pin in the NA plate: from the riser under the pocket floor, through the floor's hole and the "
        "cover's window onto the flex's pad (D-50, D-53). z 0 = the cover's back face (remote seated)",
        [f"x={x}@{y - 7},{y + 7},-7,5#along the remote (y), through the pin",
         f"y={y}@{x - 7},{x + 7},-7,5#across the remote (x), through the pin"])
    xv, yc = bc.BC_VBAT_X * bc.BC_CELL_X, bc.copper_y()
    yp = bc.BC_CELL_END_Y + bc.BC_TERM_Y * BC_TERM_SETBACK
    plate = Pos(xv, yp + bc.BC_TERM_Y * 0.15, bc.BC_CELL_Z) * Box(6.0, 0.3, 6.0)
    run("bc_contact_section", {
        "plate": (plate, "dimgray", "VBAT plate face (position REF, size MEASURE)"),
        "cover": (bc.cover(), "tab:blue", "replacement back cover: contact block"),
        "flex": (bc.flex(), "tab:orange", "cover flex end section"),
        "stiffener": (bc.stiffener(), "tab:green", "FR4 stiffener"),
        "contacts": (bc.end_fingers(), "goldenrod", "S7081-42R finger, working height")},
        f"VBAT contact (D-40): the finger on the end section, its dome on the remote's VBAT plate (y {yp:.2f}). "
        "z 0 = the cover's back face",
        [f"x={xv}@{yc - 5},{yc + 7},-0.5,14#through the finger"])


if __name__ == "__main__":
    main()
    finger_section()
