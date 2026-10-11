"""EU CAP BOARD (D-56, D-59, D-70): the sensors' side of the EU plate, all on the cap, nothing in the face plate.

A 1.6 mm FR4 cap board sits in a printed carrier (any filament, low-voltage side): the carrier fills from the wall up
to the cap board round the cap disc, with a rim round the board; four M2 screws hold the board to it. The carrier goes
on the wall first: a lip on its wall face reaches under the cap's edge, the cap's screws pin it to the wall, the cap's
teeth in gaps in the lip stop it turning (D-71). The 5 V board's two sensor spring pins come up through the cap
and the carrier onto gold pads under the board, level with the battery-free pins' pads on the back cover. On the board,
as on the NA ring board: the MSR-2 on its CN2 mate and three SMT spacers under the face plate's posts, the top-port
microphone and its ADAU7002 (D-83), the SHT45 under its vents. The face plate's four snap fingers drop into closed windows in the
board and the carrier at the corners and catch grooves in the carrier (D-77).
Run:  python capboard_eu.py  -> ../../../build/eu/carrier.step / .stl
"""
from math import cos, radians, sin
from build123d import Box, Cylinder, Pos, Rot
from params_eu import *
from common import rr, slab, stadium
import msr2


def outline(inset=CB_EDGE):
    """Outline inside the trim's walls (less `inset`), and the cut-out round the trim's pocket walls."""
    w, h = PW - 2 * (SKIN + inset), PH - 2 * (SKIN + inset)
    return Pos(*PC) * rr(w, h, PR - SKIN - inset), stadium(POCKET_OUT[0] + 2 * CB_POCKET_CLR,
                                                           POCKET_OUT[1] + 2 * CB_POCKET_CLR)


def snap_windows(z0, z1, r1=SNAP_WALL_R):
    """Closed windows round the face plate's snap fingers (D-77): from SNAP_WIN_R (SNAP_WEB outside the carrier's bore;
    room inside each finger to bend in) out to r1."""
    out = None
    for a, w in SNAPS:
        r = (SNAP_WIN_R + r1) / 2
        b = Pos(r * cos(radians(a)), r * sin(radians(a)), (z0 + z1) / 2) * Rot(0, 0, a) * Box(r1 - SNAP_WIN_R,
                                                                                            w + 2 * SNAP_CLR, z1 - z0)
        out = b if out is None else out + b
    return out


def snap_grooves():
    """Grooves in the carrier windows' outer walls that the fingers' bumps catch (45 deg flanks, SNAP[2] deep)."""
    from common import radial_prism
    z0, z1 = SNAP_GROOVE
    out = None
    for a, w in SNAPS:
        u = (cos(radians(a)), sin(radians(a)))
        g = radial_prism((u[0] * SNAP_WALL_R, u[1] * SNAP_WALL_R), u,
                         [(-0.01, z0), (SNAP[2], (z0 + z1) / 2), (-0.01, z1)], w + 2 * SNAP_CLR)
        out = g if out is None else out + g
    return out


def mic_body_y():
    return MIC_AT[1] - (MIC[1] / 2 - MIC_PORT_IN)          # port end up


def cap_board():
    o, pocket = outline(CB_INSET)
    b = slab(o, CB_PAD_Z, CB_TOP) - slab(pocket, CB_PAD_Z - 1, CB_TOP + 1)
    zc, h = (CB_PAD_Z + CB_TOP) / 2, CB_T + 1
    for x, y in CB_SCREWS:
        b -= Pos(x, y, zc) * Cylinder(CB_SCREW_D / 2 + 0.1, h)
    for x, y in MSR_SPACERS:
        b -= Pos(x, y, zc) * Cylinder(RING_NUT_HOLE / 2, h)
    for x0, x1, y0 in EU_SW_CUTS:                           # notches under the MSR-2's back switches
        y1 = CB_TOP_Y + 1
        b -= Pos((x0 + x1) / 2, (y0 + y1) / 2, zc) * Box(x1 - x0, y1 - y0, h)
    return b - snap_windows(CB_PAD_Z - 1, CB_TOP + 1, SNAP_WALL_R + SNAP[2])      # the bumps pass through


def carrier():
    """Fills from the wall up to the cap board round the cap disc (a bore, so the cap goes in from the front), a lip at
    the wall under the cap's edge with gaps for the cap's teeth (D-71), a rim round the board up to its top (D-70).
    Prints bottom down, no supports."""
    import cap_eu
    o, pocket = outline()
    r0 = CAP_R + CARRIER_CAP_CLR
    c = slab(o, 0, CB_PAD_Z) - slab(pocket, LIP_T, CB_PAD_Z + 1)
    ob, _ = outline(CB_INSET - CB_RIM_CLR)
    c += slab(o, CB_PAD_Z, CB_TOP) - slab(ob, CB_PAD_Z - 1, CB_TOP + 1)          # rim
    c -= Pos(0, 0, (LIP_T + CB_TOP + 1) / 2) * Cylinder(r0, CB_TOP + 1 - LIP_T)    # bore round the cap disc
    c -= Pos(0, 0, LIP_T / 2) * Cylinder(LIP_R, LIP_T + 2)                         # lip's inner edge
    c -= cap_eu.teeth(LIP_R - 1, r0 + 0.01, -1, LIP_T + 0.01, LIP_CLR)             # gaps in the lip for the cap's teeth
    for x, y in PINS:
        c -= Pos(x, y, CB_PAD_Z / 2) * Cylinder(PIN_CAP_HOLE_D / 2, CB_PAD_Z + 2)
    depth = min(CB_PAD_Z - 0.6, 3.0)
    for x, y in CB_SCREWS:
        c -= Pos(x, y, CB_PAD_Z - depth / 2 + 0.01) * Cylinder(CB_TAP_D / 2, depth)
    return c - snap_windows(-1, CB_TOP + 1) - snap_grooves()


def pads():
    out = None
    for x, y in PINS:
        p = Pos(x, y, CB_PAD_Z + 0.01) * Cylinder(CB_PAD_D / 2, 0.02)
        out = p if out is None else out + p
    return out


def cn2():
    """The MSR-2's CN2 with its mate on the cap board (the mated stack)."""
    return Pos(MSR_CN2_X, MSR_Y, CB_TOP + B2B_STACK / 2) * Box(B2B[0], B2B[1], B2B_STACK)


def spacers():
    """SMT spacers under the MSR-2's board, below the face plate's posts (as the NA ring board, D-68)."""
    out = None
    for x, y in MSR_SPACERS:
        s = Pos(x, y, CB_TOP + RING_NUT[1] / 2) * (Cylinder(RING_NUT[0] / 2, RING_NUT[1]) - Cylinder(1.0, RING_NUT[1] + 1))
        out = s if out is None else out + s
    return out


def msr():
    """The MSR-2 with the CO2 add-on (cad/build123d/msr2.py) on CN2 and the spacers."""
    return msr2.placed(0, MSR_Y, MSR_BACK_Z)


def mic():
    """Top-port microphone on the cap board, port end up, port under MIC_AT (D-83)."""
    return Pos(MIC_AT[0], mic_body_y(), CB_TOP + MIC[2] / 2) * Box(*MIC)


def passives():
    """The microphone's parts round its port (MIC_PARTS): ADAU7002, its capacitor, the SD pull-down, the mic's
    capacitor."""
    out = None
    for (dx, dy), (w, h, t) in MIC_PARTS.values():
        b = Pos(MIC_AT[0] + dx, MIC_AT[1] + dy, CB_TOP + t / 2) * Box(w, h, t)
        out = b if out is None else out + b
    return out


def sht45():
    return Pos(0, SHT_Y, CB_TOP + SHT_CHIP[2] / 2) * Box(*SHT_CHIP)


def screws():
    hd, hk = M2_HEAD
    out = None
    for x, y in CB_SCREWS:
        s = Pos(x, y, CB_TOP + hk / 2) * Cylinder(hd / 2, hk) + Pos(x, y, CB_TOP - 3.0) * Cylinder(1.0, 6.0)
        out = s if out is None else out + s
    return out


def parts():
    return {"carrier": carrier(), "capboard": cap_board(), "cb_pads": pads(), "cn2": cn2(), "spacers": spacers(),
            "msr": msr(), "passives": passives(), "mic": mic(), "sht45": sht45(), "cb_screws": screws()}


if __name__ == "__main__":
    from pathlib import Path
    from build123d import export_step, export_stl
    out = Path(__file__).resolve().parents[3] / "build" / "eu"
    out.mkdir(parents=True, exist_ok=True)
    ps = parts()
    for k, v in ps.items():
        print(k, round(v.volume, 1), v.is_valid, len(v.solids()))
    export_step(ps["carrier"], str(out / "carrier.step"))
    export_stl(ps["carrier"], str(out / "carrier.stl"), tolerance=0.02, angular_tolerance=0.1)
