"""BOARD STANDOFFS - Keystone 25503 nylon M3 male-female hex standoffs and nylon M3 x 8 screws (D-57).

The stud screws into the barrier boss's tapped hole (face at MOUNT_FACE_Z), the hex body spans to the board's front,
the screw goes through the board hole from the back into the standoff.
Run:  python standoff_na.py  -> ../../build/standoff_na.step
"""
from build123d import Cylinder, Pos, RegularPolygon, extrude
from params_na import *


def build(stud=STANDOFF[1]):
    """One standoff (stud long) with its screw, z = 0 the board's front face, the stud up."""
    hex_af = STANDOFF[0]
    sl, head_d, head_h = STANDOFF_SCREW
    out = extrude(RegularPolygon(hex_af / 2, 6, major_radius=False), STANDOFF_L)
    out += Pos(0, 0, STANDOFF_L + stud / 2) * Cylinder(MOUNT_THREAD_D / 2, stud)
    out += Pos(0, 0, sl / 2 - MB[2]) * Cylinder(MOUNT_THREAD_D / 2, sl)       # screw shank from the board's back
    out += Pos(0, 0, -MB[2] - head_h / 2) * Cylinder(head_d / 2, head_h)
    return out


def placed():
    """All four in assembly position."""
    out = None
    for (x, y), stud in zip(MOUNT_HOLES, MOUNT_STUD):
        q = Pos(x, MB_Y + y, MB_FRONT_Z) * build(stud)
        out = q if out is None else out + q
    return out


if __name__ == "__main__":
    from pathlib import Path
    from build123d import export_step
    out = Path(__file__).resolve().parents[3] / "build" / "na"
    out.mkdir(parents=True, exist_ok=True)
    export_step(build(), str(out / "standoff.step"))
    print("standoff", build().bounding_box().size)
