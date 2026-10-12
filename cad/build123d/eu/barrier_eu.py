"""EU CAP (D-30, D-36): the whole mains / low-voltage barrier of the EU plate.

A flat 1.6 mm floor over the box and the seal band round the Ø68 hole (the remote rests on it; the
sensor board's carrier sits on the wall round it, its lip under the barrier's edge), a cup under the remote's upper half down to the emergency rocker's
panel (Marquardt 1802.2504; the rocker body plugs the cutout), bosses for the pin board and (long) for the mains
board, holes for the pin board's four spring pins (no wires),
a rebate in its underside outside the seal band over the carrier's lip, with four teeth that key the carrier (D-71).
Two countersunk screws into the box's top and bottom domes, in the pocket floor, fix it. The supplied steel piece
sits in a recess in the pocket floor, a cup under it keeps the barrier's floor (D-72).
Print: UL94 V-0 filament, top face down (export flips it), no supports.
Run:  python barrier_eu.py  -> ../../../build/eu/barrier.step / .stl
"""
from build123d import Box, Cone, Cylinder, Pos, Rectangle, Rot
from params_eu import *
from common import rr, slab


def screw_hole(x, y):
    bore = Pos(x, y, CAP_T / 2) * Cylinder(SCREW_D / 2, CAP_T + 2)
    sink = (SCREW_HEAD_D - SCREW_D) / 2
    head = Pos(x, y, CAP_T - sink / 2 + 0.01) * Cone(SCREW_D / 2, SCREW_HEAD_D / 2, sink)
    return bore + head


def board_bosses():
    """Bosses from the floor's underside down to the pin board's front, M2 bores from below."""
    out = None
    for x, y in PB_MOUNT:
        b = Pos(x, y, PB_FRONT / 2 + 0.01) * Cylinder(PB_BOSS_D / 2, -PB_FRONT + 0.02)
        b -= Pos(x, y, PB_FRONT + 2.5 - 0.01) * Cylinder(PB_MOUNT_D * 0.75 / 2, 5.0)
        out = b if out is None else out + b
    return out


def mains_bosses():
    """Long bosses from the floor's underside down to the mains board's front, M2 bores from below."""
    out = None
    for x, y in MB_BOSS:
        b = Pos(x, y, MB_FRONT / 2 + 0.01) * Cylinder(MB_BOSS_D / 2, -MB_FRONT + 0.02)
        b -= Pos(x, y, MB_FRONT + 3.0 - 0.01) * Cylinder(PB_MOUNT_D * 0.75 / 2, 6.0)
        out = b if out is None else out + b
    return out


def teeth(r0, r1, z0, z1, clr=0.0):
    """Boxes over the barrier's teeth at the snap angles (radial r0..r1, z0..z1), `clr` wider each side."""
    from math import cos, radians, sin
    out = None
    rm = (r0 + r1) / 2
    for a, w in TEETH:
        b = Pos(rm * cos(radians(a)), rm * sin(radians(a)), (z0 + z1) / 2) * Rot(0, 0, a) * Box(r1 - r0, w + 2 * clr,
                                                                                               z1 - z0)
        out = b if out is None else out + b
    return out


def rebate():
    """Underside rebate outside the seal band for the carrier's lip, less the teeth (D-71)."""
    ring = Pos(0, 0, (LIP_T - 1) / 2) * (Cylinder(CAP_R + 1, LIP_T + 1) - Cylinder(REBATE_R, LIP_T + 2))
    return ring - teeth(REBATE_R - 1, CAP_R + 2, -2, LIP_T + 1)


def magnet_outline(grow=0.0):
    """Outline of the steel piece's recess (round end down, as the piece), `grow` wider all round."""
    w = MAGNET[0] + 2 * (MAGNET_CLR + grow)
    r = MAGNET_END_R + MAGNET_CLR + grow
    y0 = MAGNET_REC_Y - MAGNET[1] / 2 - MAGNET_CLR - grow
    y1 = MAGNET_REC_Y + MAGNET[1] / 2 + MAGNET_CLR + grow
    return Pos(0, y0 + r) * rr(w, 2 * r, r) + Pos(0, (y0 + r + y1) / 2) * Rectangle(w, y1 - y0 - r)


def magnet_cup():
    """Cup under the steel piece's recess: BARRIER_MIN under and round it (D-72)."""
    return slab(magnet_outline(BARRIER_MIN), MAG_CUP_BOT, 0.01)


def magnet_recess():
    """Recess for the supplied steel piece in the pocket floor, MAGNET_SETBACK below the seat (D-72)."""
    return slab(magnet_outline(), MAGNET_Z[0], CAP_T + 1)


def cup():
    """Switch cup: walls from the floor down to the rocker's panel, panel with the snap-in cutout."""
    outer = Pos(0, SW_Y, 0) * slab(rr(*CUP_OUT, 1.0), PANEL_BOT_Z, 0.01)
    return outer


def cup_cut():
    inner = Pos(0, SW_Y, 0) * slab(rr(*CUP_IN, 0.5), PANEL_TOP_Z, CAP_T + 1)
    cutout = Pos(0, SW_Y, 0) * slab(Rectangle(*SW_CUT), PANEL_BOT_Z - 1, PANEL_TOP_Z + 0.1)
    return inner + cutout


def pin_holes(plain=False):
    """The barrier's pin openings: one round each sensor pin to the sensor board's pads (R9) and each battery-free pin to the
    back cover's pads (D-54), filled by the pins' barrels; the other opening is the rocker's cutout. Plain (D-109):
    the battery-free pins only."""
    out = None
    for x, y in (() if plain else PINS) + tuple(BC_FINGERS):
        h = Pos(x, y, CAP_T / 2) * Cylinder(PIN_CAP_HOLE_D / 2, CAP_T + 2)
        out = h if out is None else out + h
    return out


def build(plain=False, switch=False):
    """Barrier; plain (battery-free edition): without the sensor pins' holes (no sensor board, D-109); switch (switch-only
    edition): no pin holes and no pin board bosses (D-122)."""
    body = Pos(0, 0, CAP_T / 2) * Cylinder(CAP_R, CAP_T)
    body += cup()
    body += magnet_cup()
    if not switch:
        body += board_bosses()
    body += mains_bosses()
    body -= cup_cut()
    body -= magnet_recess()
    for x, y in SCREWS:
        body -= screw_hole(x, y)
    body -= rebate()
    if not switch:
        body -= pin_holes(plain)
    return body


if __name__ == "__main__":
    from pathlib import Path
    from build123d import export_step, export_stl
    out = Path(__file__).resolve().parents[3] / "build" / "eu"
    out.mkdir(parents=True, exist_ok=True)
    p = build()
    bb = p.bounding_box()
    print(f"barrier bbox x {bb.min.X:.1f}..{bb.max.X:.1f} y {bb.min.Y:.1f}..{bb.max.Y:.1f} z {bb.min.Z:.1f}..{bb.max.Z:.1f}"
          f"  vol {p.volume/1000:.1f} cm3 valid={p.is_valid} solids={len(p.solids())}")
    export_step(p, str(out / "barrier.step"))
    export_stl(p, str(out / "barrier.stl"), tolerance=0.02, angular_tolerance=0.1)
