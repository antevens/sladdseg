"""EU TEST SOCKET (D-76): a printed stand-in for the DIN 49073 flush box, to try the EU stack's depth before a real wall.

The box: BOX_DIA inside, BOX_HOLE outside, TB_DEPTH inside depth, the four device screw domes (DOMES, DOME_D) with
pilot holes for the cap's screws, V-grooves inside and outside at the TB_MARKS depths, an inspection window in the
wall at -45 deg with a labelled fin beside it. The wall plate: TB_PLATE_T thick, larger than the face plate, sits on
a shoulder on the box so the box's rim is flush with its face; a key at the top sets the orientation.
Print: box floor down, plate flat, no supports. Any filament.
Run:  python testbox_eu.py  -> ../../../build/eu/testbox.step, testbox_plate.step
"""
from math import cos, radians, sin
from build123d import Axis, Box, Cone, Cylinder, Plane, Polyline, Pos, Rot, Text, extrude, make_face, revolve
from params_eu import *
from common import rr, slab

Z_FLOOR = -TB_DEPTH                                   # floor's top face
Z_BOTTOM = Z_FLOOR - TB_FLOOR
R_OUT = BOX_HOLE / 2
WINDOW_A = -45.0                                      # window angle (deg from +x)
FIN_A = WINDOW_A + 14.0                               # fin beside the window, towards +x


def ring(profile):
    """Solid of revolution about z from an (r, z) profile."""
    face = make_face(Polyline(*[(r, 0, z) for r, z in profile], close=True))
    return revolve(face, Axis.Z)


def grooves(r, outward):
    """V-grooves (45 deg flanks) at the TB_MARKS depths into the wall surface at radius r."""
    g, s = TB_GROOVE, 1 if outward else -1
    out = None
    for d in TB_MARKS:
        p = [(r - s * 0.01, -d - g), (r + s * g, -d), (r - s * 0.01, -d + g)]
        v = ring(p)
        out = v if out is None else out + v
    return out


def window():
    """Inspection window through the wall at WINDOW_A, a 45 deg gable on top (prints without a bridge)."""
    w, top = TB_WINDOW
    a = radians(WINDOW_A)
    pl = Plane(origin=((BOX_R + R_OUT) / 2 * cos(a), (BOX_R + R_OUT) / 2 * sin(a), 0), x_dir=(-sin(a), cos(a), 0),
               z_dir=(cos(a), sin(a), 0))
    bot = Z_FLOOR + 1.0
    pts = [(-w / 2, bot), (w / 2, bot), (w / 2, -top), (0.0, -top + w / 2), (-w / 2, -top)]
    return extrude(pl * make_face(Polyline(*pts, close=True)), R_OUT - BOX_R + 2, both=True)


def fin():
    """Label fin on the outside beside the window: a tick and the depth on alternating faces at each marker."""
    t, rad = TB_FIN
    a = radians(FIN_A)
    u, n = (cos(a), sin(a)), (-sin(a), cos(a))
    z0, z1 = Z_BOTTOM, -TB_PLATE_T - TB_SHOULDER - 1.0
    rm = R_OUT - 0.5 + rad / 2
    f = Pos(u[0] * rm, u[1] * rm, (z0 + z1) / 2) * Rot(0, 0, FIN_A) * Box(rad + 0.5, t, z1 - z0)
    th, depth = TB_TEXT
    for i, d in enumerate(TB_MARKS):
        side = 1 if i % 2 == 0 else -1                # 40 and 60 on one face, 43 and 63 on the other
        fo = (n[0] * side * t / 2, n[1] * side * t / 2)
        # on this face, x_dir = -side * u keeps the text upright (y_dir = +z) and reading left to right from outside
        pl = Plane(origin=(fo[0], fo[1], -d), x_dir=(-side * u[0], -side * u[1], 0), z_dir=(n[0] * side, n[1] * side, 0))
        rt, rl = R_OUT + 1.0, R_OUT + 2.3 + th * 0.6       # tick centre, label centre (radius)
        tick = Pos(u[0] * rt, u[1] * rt, 0) * (pl * Box(2.0, 0.5, 2 * depth))
        label = Pos(u[0] * rl, u[1] * rl, 0) * extrude(pl * Text(f"{d:.0f}", font_size=th), -depth)
        f -= tick + label
    return f


def box():
    body = Pos(0, 0, (Z_BOTTOM + 0) / 2) * Cylinder(R_OUT, -Z_BOTTOM)
    body -= Pos(0, 0, (Z_FLOOR + 1) / 2) * Cylinder(BOX_R, 1 - Z_FLOOR)
    body -= grooves(BOX_R, True) + grooves(R_OUT, False)
    body -= window()
    for x, y in DOMES:
        body += Pos(x, y, (Z_FLOOR - 0.01) / 2) * Cylinder(DOME_D / 2, -Z_FLOOR + 0.01)   # top at the wall plane
    for x, y in DOMES:
        r = TB_PILOT_D / 2
        body -= Pos(x, y, -TB_PILOT_L / 2 + 0.5) * Cylinder(r, TB_PILOT_L + 1)
        body -= Pos(x, y, -TB_PILOT_L - r / 2 + 0.01) * Cone(0.05, r, r)
    sh = TB_SHOULDER
    body += ring([(R_OUT - 0.1, -TB_PLATE_T), (R_OUT + sh, -TB_PLATE_T), (R_OUT - 0.1, -TB_PLATE_T - sh - 0.1)])
    kw, kr = TB_KEY
    body += Pos(0, R_OUT + kr / 2 - 0.25, -TB_PLATE_T / 2) * Box(kw, kr + 0.5, TB_PLATE_T)
    body += fin()
    return body


def plate():
    """Wall plate: covers the face plate's outline plus TB_PLATE_MARGIN, the box's hole with the key's notch."""
    m = TB_PLATE_MARGIN
    p = Pos(*PC, 0) * slab(rr(PW + 2 * m, PH + 2 * m, PR + m), -TB_PLATE_T, 0)
    p -= Pos(0, 0, -TB_PLATE_T / 2) * Cylinder(R_OUT + TB_PLATE_CLR, TB_PLATE_T + 2)
    kw, kr = TB_KEY
    c = TB_PLATE_CLR
    p -= Pos(0, R_OUT + (kr + c) / 2 - 0.25, -TB_PLATE_T / 2) * Box(kw + 2 * c, kr + c + 0.5, TB_PLATE_T + 2)
    return p


if __name__ == "__main__":
    from pathlib import Path
    from build123d import export_step
    out = Path(__file__).resolve().parents[3] / "build" / "eu"
    out.mkdir(parents=True, exist_ok=True)
    for name, part in (("testbox", box()), ("testbox_plate", plate())):
        bb = part.bounding_box()
        print(f"{name}: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm, valid={part.is_valid}, "
              f"solids={len(part.solids())}")
        export_step(part, str(out / f"{name}.step"))
