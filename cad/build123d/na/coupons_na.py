"""Fast test-fit coupons (print in PETG before committing PC-FR / a full face plate).

  coupon_pocket_well  top of the barrier: switch well + panel, magnet recess, upper pocket end, key pin,
                      5 V pass-through, top screw boss. Rocker snap-in + remote fit.
  coupon_msr          top of the face plate: MSR-2 bay, radar skin, CO2 and light sensor grille, vents.
  coupon_rocker       panel-thickness ladder for the Marquardt 1802.2504 snap-in (SW_PANEL_T is MEASURE):
                      one notch per step on the frame edge = 1.0, 1.5, 2.0, 2.5, 3.0 mm.
  coupon_ribs         a straight piece of the collar with the flange's land and taper and three crush ribs at
                      RIB_STEPS interference (1, 2, 3 notches): press the sensor board's window edge (or a 1.6 mm FR4
                      offcut with a routed edge) on, pick the rib that holds without cracking (D-68).
"""
from build123d import Box, Pos, Rectangle, Rot
from params_na import *
from common import slab, rr
import barrier_na
import face_plate_na

PANEL_STEPS = (1.0, 1.5, 2.0, 2.5, 3.0)
RIB_STEPS = (0.10, 0.15, 0.20)                     # crush rib interference into the board's edge


def pocket_well(ins=None):
    ins = ins or barrier_na.build()
    y0 = MAGNET_SLOT_BOT - 3.0                             # include the magnet recess
    keep = Pos(0, (y0 + 60) / 2, (PANEL_BOT_Z + PT + 5) / 2) * Box(100, 60 - y0, PT + 5 - PANEL_BOT_Z)
    return ins & keep


def msr(tr=None):
    tr = tr or face_plate_na.build()
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
    """Collar piece: the collar face at x 0, the board side at x > 0 (the wall plane z 0, as in the barrier), the land
    at SB_T then 45 deg up; one rib per step, its lead-in as in barrier_na.ribs()."""
    from common import radial_prism
    length, top, back, base = 12.0 * len(RIB_STEPS), 6.0, 8.0, 3.0
    land = SB_WIN_CLR + SB_LAND
    prof = [(-back, -base), (0.0, -base), (0.0, SB_T), (land, SB_T), (land + top - SB_T, top), (-back, top)]
    c = radial_prism((0.0, length / 2), (1.0, 0.0), prof, length)
    w = SB_RIB[0]
    for i, interf in enumerate(RIB_STEPS):
        y = 6.0 + 12.0 * i
        d = SB_WIN_CLR + interf
        r = Pos(d / 2, y, SB_T / 2) * Box(d, w, SB_T)
        r -= Pos(d, y, 0) * Rot(0, 45, 0) * Box(d * 2 ** 0.5, w + 1, d * 2 ** 0.5)
        c += r
        for k in range(i + 1):                                                  # step marker notches on the top
            c -= Pos(-back / 2, y - 2.0 + 1.6 * k, top) * Box(back - 2, 0.8, 1.2)
    return c


if __name__ == "__main__":
    for name, p in (("pocket_well", pocket_well()), ("msr", msr()), ("rocker", rocker_ladder()), ("ribs", ribs())):
        bb = p.bounding_box()
        print(f"coupon_{name}: {bb.size.X:.0f} x {bb.size.Y:.0f} x {bb.size.Z:.0f} mm, {p.volume/1000:.1f} cm3, valid={p.is_valid}, solids={len(p.solids())}")
