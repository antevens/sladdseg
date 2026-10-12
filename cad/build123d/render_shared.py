"""Renders of the parts both variants share: xvfb-run python render_shared.py -> docs/renders/bc_*.png (replacement
back cover, D-35), plate_jigs.png, msr2_*.png, bilresa_*.png"""
import sys
from pathlib import Path
from build123d import Box, Pos
import render
import backcover as bc

sys.path[1:1] = [str(Path(__file__).resolve().parent / v) for v in ("na", "eu")]
import params_eu as eu                                      # noqa: E402

render.COL.update({"cover": "#e9e6df", "flex": "#d99a2b", "stiffener": "#2f7a46", "pads": "#e3c565",
               "pin_pads": "#c9a227", "contacts": "#c9a227", "regulator": "#2b2b2b", "pad_stiffener": "#2f7a46", "steel": "#6d7075", "bf_pins": "#c9a227",
               "front_half": "#fbfaf6"})


FLEX_LIFT = 2.5                         # flex drawn this far off the contact posts in flex_views()


def placed(parts, z):
    return {k: Pos(0, 0, z) * v for k, v in parts.items()}


def eu_context():
    import barrier_eu
    import face_plate_eu
    return {"barrier": barrier_eu.build(), "face_plate": face_plate_eu.build()}


def main():
    cov = bc.cover_parts(free=True)
    render.shot("bc_inside", cov, [(70, -120, 140), (0, -6, 4), (0, 0, 1)], size=(1300, 1100), head=0.9)
    render.shot("bc_back", cov, [(60, -90, -140), (4, -4, 0), (0, 0, 1)], size=(1300, 1100), head=0.9)
    # in the EU plate: cover and remote lifted above the pocket, the battery-free pins through the barrier
    import boards_eu
    ctx = {**eu_context(), "bf_pins": boards_eu.bf_pins()}
    lift = eu.SEAT_Z
    ex = {**ctx, **placed(bc.cover_parts(), lift + 25), "front_half": Pos(0, 0, lift + 50) * bc.remote_front()}
    render.shot("bc_exploded", ex, [(230, -200, 130), (0, 0, 25), (0, 0, 1)], size=(1400, 1300), head=0.85,
            alpha={"face_plate": 0.2})


def finger_section():
    """2D sections in the NA plate, cover frame (z 0 = the cover's back face): through the +5V pin (pocket floor,
    pin board, spring pin, window, pad) and through the VBAT finger (block, end section, finger, the remote's plate)."""
    import subprocess
    import barrier_na
    import sensor_board_na
    from build123d import Box, export_stl
    from params import BC_TERM_SETBACK
    from params_na import SEAT_Z
    root = Path(__file__).resolve().parents[2]
    out = root / "build" / "backcover"
    out.mkdir(parents=True, exist_ok=True)
    tool = [sys.executable, str(root / "cad" / "tools" / "sections.py")]
    rp = sensor_board_na.parts()
    na = lambda part: Pos(0, 0, -SEAT_Z) * part              # plate parts into the cover's frame

    def run(name, parts, title, cuts, dpi=120):
        args = []
        for k, (part, col, label) in parts.items():
            export_stl(part, str(out / f"{name}_{k}.stl"), tolerance=0.01)
            args.append(f"{out / f'{name}_{k}.stl'}:{col}|{label}")
        subprocess.run(tool + [str(render.R / f"{name}.png")] + args + ["--title", title, "--dpi", str(dpi)] +
                       [a for c in cuts for a in ("--cut", c)], check=True)
        print("wrote", render.R / f"{name}.png")

    x, y = bc.BC_FINGERS[0]
    run("bc_pin_section", {
        "barrier": (na(barrier_na.build()), "tab:red", "barrier: pocket floor (UL94 V-0)"),
        "pin_board": (na(rp["pin_board"] + rp["posts"] + rp["screws"]), "tab:green", "pin board, spacer posts"),
        "pin": (na(rp["pins"]), "goldenrod", "spring pin (Harwin P70-2200045), working height"),
        "cover": (bc.cover(), "tab:blue", "replacement back cover"),
        "flex": (bc.flex() + bc.pad_stiffener(), "tab:orange", "cover flex + FR4 stiffener"),
        "pad": (bc.pin_pads(), "tab:purple", "gold pad on the flex underside")},
        "+5V spring pin in the NA plate: from the pin board under the pocket floor, through the floor's hole and the "
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


def flex_views():
    """The cover flex lifted LIFT out of the cover towards the cells (drop-in order: end section, run, pad section)."""
    from build123d import Box
    ps = dict(bc.cover_parts())
    ps = {k: (Pos(0, FLEX_LIFT * bc.BC_TERM_Y, 0) * v if k in ("flex", "stiffener", "contacts") else v)
          for k, v in ps.items()}
    glass = {"flex": 0.6}
    render.shot("bc_flex", ps, [(70, -120, 140), (0, -12, 4), (0, 0, 1)], size=(1300, 1100), head=0.7, alpha=glass)
    end = Pos(0, bc.copper_y(), 6) * Box(34, 12, 16)
    near = {k: v & end for k, v in ps.items()}
    near = {k: v for k, v in near.items() if v is not None and v.volume > 1e-6}
    render.shot("bc_flex_end", near, [(25, bc.copper_y() - 45, 30), (0, bc.copper_y(), 6), (0, 0, 1)],
            size=(1300, 1000), head=0.7, alpha=glass)


def parts_views():
    """The steel plate's hacksaw guide (D-52, D-81), the MSR-2 with the CO2 add-on, the BILRESA model."""
    import bilresa
    import msr2
    import plate_jig as pj
    from params import MAGNET, JIG_FLOOR, JIG_SAW, MSR_BOARD, MSR_CN2_IN, B2B, B2B_STACK, B_D
    render.COL.update({"jig": "#f2a541", "steel": "#9aa0a6", "cut": "#d9534f"})
    js = {"jig": pj.saw_guide(), "steel": pj.plate(),
          "cut": Pos(0, MAGNET[1], JIG_FLOOR + MAGNET[2] + JIG_SAW[2] + 0.1) * Box(40, 0.25, 0.05)}   # cut line red
    render.shot("plate_jigs", js, [(60, -55, 75), (0, 20, 2), (0, 0, 1)], size=(1100, 950), head=0.9)
    m2 = msr2.parts()                                       # board frame
    m2["cn2"] = Pos(MSR_BOARD[0] / 2 - MSR_CN2_IN, 0, -B2B_STACK / 2) * Box(B2B[0], B2B[1], B2B_STACK)   # CN2, its mate
    render.shot("msr2_front", m2, [(22, -42, 52), (0, 0, 4), (0, 1, 0)], size=(1200, 900), head=0.9)
    render.shot("msr2_back", m2, [(-20, -38, -52), (0, 0, 2), (0, 1, 0)], size=(1200, 900), head=1.0)
    remote = {"remote": bilresa.build()}                    # back at z 0
    render.shot("bilresa_model", remote, [(70, -90, 123), (0, 0, 3), (0, 1, 0)], size=(900, 900))
    render.shot("bilresa_back", remote, [(95, -60, -107), (0, 0, B_D / 2), (0, 1, 0)], size=(900, 900), head=1.0)


if __name__ == "__main__":
    main()
    finger_section()
    flex_views()
    parts_views()
