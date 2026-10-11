"""Fast test-fit coupons (print in PETG before committing PC-FR / a full trim).

  coupon_pocket_well  top of the insert: switch well + panel, magnet recess, upper pocket end, key pin,
                      5 V pass-through, top screw boss. Rocker snap-in + remote fit.
  coupon_msr          top of the trim: MSR-2 bay, radar skin, CO2 and light sensor grille, vents.
  coupon_rocker       panel-thickness ladder for the Marquardt 1802.2504 snap-in (SW_PANEL_T is MEASURE):
                      one notch per step on the frame edge = 1.0, 1.5, 2.0, 2.5, 3.0 mm.
  coupon_ribs         a straight piece of the collar with the flange's land and taper and three crush ribs at
                      RIB_STEPS interference (1, 2, 3 notches): press the ring board's window edge (or a 1.6 mm FR4
                      offcut with a routed edge) on, pick the rib that holds without cracking (D-68).
  coupon_back_gauges  five flat profile gauges for the inside of the remote's original back cover, side to side: the
                      modelled back (flat, quarter-ellipse round-over B_BACK_RUN x B_BACK_RISE) with the round-over
                      changed by GAUGE_DR (engraved: its run), a line at the rim (D-87).
"""
from math import cos, pi, sin
from build123d import Box, Pos, Rectangle, Rot, Polyline, Text, extrude, make_face
from params import *
from common import slab, rr
import insert
import trim

PANEL_STEPS = (1.0, 1.5, 2.0, 2.5, 3.0)
RIB_STEPS = (0.10, 0.15, 0.20)                     # crush rib interference into the board's edge
GAUGE_DR = (-0.5, -0.25, 0.0, 0.25, 0.5)          # back gauges: change of the round-over's run and rise
GAUGE_T = 2.0                                      # gauge thickness
GAUGE_GRIP = 8.0                                   # gauge above the cover's rim


def pocket_well(ins=None):
    ins = ins or insert.build()
    y0 = MAGNET_SLOT_BOT - 3.0                             # include the magnet recess
    keep = Pos(0, (y0 + 60) / 2, (PANEL_BOT_Z + PT + 5) / 2) * Box(100, 60 - y0, PT + 5 - PANEL_BOT_Z)
    return ins & keep


def msr(tr=None):
    tr = tr or trim.build()
    y0 = MSR_Y - MSR[1] / 2 - CLR - 1.6 - 2.0
    return tr & (Pos(0, (y0 + PH) / 2, PT / 2) * Box(PW + 2, PH - y0, PT + 2))


def rocker_ladder():
    cell = (SW_CUT[0] + 10, SW_CUT[1] + 10)
    wall_h = 6.0
    parts = None
    for i, t in enumerate(PANEL_STEPS):
        y = (i - (len(PANEL_STEPS) - 1) / 2) * (cell[1] - 2)
        c = Pos(0, y, 0) * slab(rr(*cell, 2), 0, wall_h)
        c -= Pos(0, y, 0) * slab(rr(cell[0] - 4, cell[1] - 4, 1), t, wall_h + 1)       # pocket above the panel
        c -= Pos(0, y, 0) * slab(Rectangle(*SW_CUT), -1, wall_h + 1)                    # datasheet cutout
        for k in range(i + 1):                                                          # step marker notches
            c -= Pos(cell[0] / 2 - 0.5, y - cell[1] / 2 + 3 + 2.2 * k, wall_h) * Box(2.5, 1.2, 3)
        parts = c if parts is None else parts + c
    return parts


def ribs():
    """Collar piece: the collar face at x 0, the board side at x > 0 (the wall plane z 0, as in the insert), the land
    at RING_T then 45 deg up; one rib per step, its lead-in as in insert.ribs()."""
    from common import radial_prism
    length, top, back, base = 12.0 * len(RIB_STEPS), 6.0, 8.0, 3.0
    land = RING_WIN_CLR + RING_LAND
    prof = [(-back, -base), (0.0, -base), (0.0, RING_T), (land, RING_T), (land + top - RING_T, top), (-back, top)]
    c = radial_prism((0.0, length / 2), (1.0, 0.0), prof, length)
    w = RING_RIB[0]
    for i, interf in enumerate(RIB_STEPS):
        y = 6.0 + 12.0 * i
        d = RING_WIN_CLR + interf
        r = Pos(d / 2, y, RING_T / 2) * Box(d, w, RING_T)
        r -= Pos(d, y, 0) * Rot(0, 45, 0) * Box(d * 2 ** 0.5, w + 1, d * 2 ** 0.5)
        c += r
        for k in range(i + 1):                                                  # step marker notches on the top
            c -= Pos(-back / 2, y - 2.0 + 1.6 * k, top) * Box(back - 2, 0.8, 1.2)
    return c


def back_gauge(dr):
    """Flat gauge (x across the remote, y up from the original cover's inside floor), printed flat: the inside of
    the original cover side to side as modelled (B_W less BC_WALL each side, the back's round-over B_BACK_RUN x
    B_BACK_RISE) with the round-over's run and rise changed by dr, up to the rim (B_SEAM_Z less BC_WALL), then
    straight up; a line at the rim."""
    a = B_W / 2 - BC_WALL
    run, rise = B_BACK_RUN + dr, B_BACK_RISE + dr
    depth = B_SEAM_Z - BC_WALL
    n = 48
    side = []
    for i in range(n + 1):
        t = (pi / 2) * i / n
        x, y = a - run * (1 - sin(t)), rise * (1 - cos(t))
        if y >= depth:
            x0, y0 = side[-1]
            x = x0 + (x - x0) * (depth - y0) / (y - y0)
            side.append((x, depth))
            break
        side.append((x, y))
    top = depth + GAUGE_GRIP
    xr = side[-1][0]
    pts = [(-x, y) for x, y in reversed(side)] + side + [(xr, top), (-xr, top)]
    g = extrude(make_face(Polyline(*pts, pts[0])), GAUGE_T)
    g -= Pos(0, depth, GAUGE_T) * Box(2 * a + 1, 0.4, 0.8)        # rim line
    g -= Pos(0, depth + GAUGE_GRIP / 2 + 0.3, GAUGE_T - 0.2) * extrude(Text(f"R{run:.2f}", 4.5), 0.6)
    return g


def back_gauges():
    """The GAUGE_DR gauges side by side along y, the smallest round-over at the bottom."""
    h = B_SEAM_Z - BC_WALL + GAUGE_GRIP + 4.0
    out = None
    for i, dr in enumerate(GAUGE_DR):
        g = Pos(0, i * h, 0) * back_gauge(dr)
        out = g if out is None else out + g
    return out


if __name__ == "__main__":
    for name, p in (("pocket_well", pocket_well()), ("msr", msr()), ("rocker", rocker_ladder()), ("ribs", ribs()),
                    ("back_gauges", back_gauges())):
        bb = p.bounding_box()
        print(f"coupon_{name}: {bb.size.X:.0f} x {bb.size.Y:.0f} x {bb.size.Z:.0f} mm, {p.volume/1000:.1f} cm3, valid={p.is_valid}, solids={len(p.solids())}")
