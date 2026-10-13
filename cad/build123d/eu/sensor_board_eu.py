"""EU SENSOR BOARD (D-56, D-59, D-70): the sensors' side of the EU plate, all on the barrier, nothing in the face plate.

A 1.6 mm FR4 sensor board sits in a printed carrier (any filament, low-voltage side): the carrier fills from the wall up
to the sensor board round the barrier disc, with a rim round the board; four M2 screws hold the board to it. The carrier goes
on the wall first: a lip on its wall face reaches under the barrier's edge, the barrier's screws pin it to the wall, the barrier's
teeth in gaps in the lip stop it turning (D-71). The pin board's two sensor spring pins come up through the barrier
and the carrier onto gold pads under the board, level with the battery-free pins' pads on the back cover. On the board,
as on the NA sensor board: the MSR-2 on its CN2 mate and three SMT spacers under the face plate's posts, the top-port
microphone and its ADAU7002 (D-83), the SHT40 under its vents. The face plate's four snap fingers drop into closed windows in the
board and the carrier at the corners and catch grooves in the carrier (D-77).
Run:  python sensor_board_eu.py  -> ../../../build/eu/carrier.step / .stl
"""
from math import cos, radians, sin
from build123d import Box, Cylinder, Pos, Rot
from params_eu import *
from common import rr, slab, stadium
import msr2


def outline(inset=SB_EDGE, plain=False):
    """Outline inside the face plate's walls (less `inset`), and the cut-out round the face plate's pocket walls."""
    pw, ph, pc = plate(plain)
    w, h = pw - 2 * (SKIN + inset), ph - 2 * (SKIN + inset)
    return Pos(*pc) * rr(w, h, PR - SKIN - inset), stadium(POCKET_OUT[0] + 2 * SB_POCKET_CLR,
                                                           POCKET_OUT[1] + 2 * SB_POCKET_CLR)


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


def board():
    o, pocket = outline(SB_INSET)
    b = slab(o, SB_PAD_Z, SB_TOP) - slab(pocket, SB_PAD_Z - 1, SB_TOP + 1)
    zc, h = (SB_PAD_Z + SB_TOP) / 2, SB_T + 1
    for x, y in SB_SCREWS:
        b -= Pos(x, y, zc) * Cylinder(SB_SCREW_D / 2 + 0.1, h)
    for x, y in MSR_SPACERS:
        b -= Pos(x, y, zc) * Cylinder(MSR_NUT_HOLE / 2, h)
    for x0, x1, y0 in MSR_SW_CUTS:                           # notches under the MSR-2's back switches
        y1 = SB_TOP_Y + 1
        b -= Pos((x0 + x1) / 2, (y0 + y1) / 2, zc) * Box(x1 - x0, y1 - y0, h)
    return b - snap_windows(SB_PAD_Z - 1, SB_TOP + 1, SNAP_WALL_R + SNAP[2])      # the bumps pass through


def carrier(plain=False):
    """Fills from the wall up to the sensor board round the barrier disc (a bore, so the barrier goes in from the front), a lip at
    the wall under the barrier's edge with gaps for the barrier's teeth (D-71), a rim round the board up to its top (D-70).
    Plain (D-109): the square plate's outline up to the sensor board's level and the same rim (D-150), no pin or screw
    holes.
    Prints bottom down, no supports."""
    import barrier_eu
    o, pocket = outline(plain=plain)
    r0 = CAP_R + CARRIER_CAP_CLR
    c = slab(o, 0, SB_PAD_Z) - slab(pocket, LIP_T, SB_PAD_Z + 1)
    ob, _ = outline(SB_INSET - SB_RIM_CLR, plain=plain)
    c += slab(o, SB_PAD_Z, SB_TOP) - slab(ob, SB_PAD_Z - 1, SB_TOP + 1)          # rim (plain: the same, for stiffness, D-150)
    c -= Pos(0, 0, (LIP_T + SB_TOP + 1) / 2) * Cylinder(r0, SB_TOP + 1 - LIP_T)    # bore round the barrier disc
    c -= Pos(0, 0, LIP_T / 2) * Cylinder(LIP_R, LIP_T + 2)                         # lip's inner edge
    c -= barrier_eu.teeth(LIP_R - 1, r0 + 0.01, -1, LIP_T + 0.01, LIP_CLR)             # gaps in the lip for the barrier's teeth
    if plain:
        return c - snap_windows(-1, SB_TOP + 1) - snap_grooves()
    for x, y in PINS:
        c -= Pos(x, y, SB_PAD_Z / 2) * Cylinder(PIN_CAP_HOLE_D / 2, SB_PAD_Z + 2)
    depth = min(SB_PAD_Z - 0.6, 3.0)
    for x, y in SB_SCREWS:
        c -= Pos(x, y, SB_PAD_Z - depth / 2 + 0.01) * Cylinder(SB_TAP_D / 2, depth)
    return c - snap_windows(-1, SB_TOP + 1) - snap_grooves()


def pads():
    out = None
    for x, y in PINS:
        p = Pos(x, y, SB_PAD_Z + 0.01) * Cylinder(SB_PAD_D / 2, 0.02)
        out = p if out is None else out + p
    return out


def cn2():
    """The MSR-2's CN2 with its mate on the sensor board (the mated stack)."""
    return Pos(MSR_CN2_X, MSR_Y, SB_TOP + B2B_STACK / 2) * Box(B2B[0], B2B[1], B2B_STACK)


def spacers():
    """SMT spacers under the MSR-2's board, below the face plate's posts (as the NA sensor board, D-68)."""
    out = None
    for x, y in MSR_SPACERS:
        s = Pos(x, y, SB_TOP + MSR_NUT[1] / 2) * (Cylinder(MSR_NUT[0] / 2, MSR_NUT[1]) - Cylinder(1.0, MSR_NUT[1] + 1))
        out = s if out is None else out + s
    return out


def msr():
    """The MSR-2 with the CO2 add-on (cad/build123d/msr2.py) on CN2 and the spacers."""
    return msr2.placed(MSR_X, MSR_Y, MSR_BACK_Z)


def mic():
    """Top-port microphone on the sensor board, port end up, port under MIC_AT (D-83)."""
    return Pos(MIC_AT[0], mic_body_y(), SB_TOP + MIC[2] / 2) * Box(*MIC)


def passives():
    """The microphone's parts round its port (MIC_PARTS): ADAU7002, its capacitor, the SD pull-down, the mic's
    capacitor."""
    out = None
    for (dx, dy), (w, h, t) in MIC_PARTS.values():
        b = Pos(MIC_AT[0] + dx, MIC_AT[1] + dy, SB_TOP + t / 2) * Box(w, h, t)
        out = b if out is None else out + b
    return out


def sht45():
    return Pos(0, SHT_Y, SB_TOP + SHT_CHIP[2] / 2) * Box(*SHT_CHIP)


def screws():
    hd, hk = M2_HEAD
    out = None
    for x, y in SB_SCREWS:
        s = Pos(x, y, SB_TOP + hk / 2) * Cylinder(hd / 2, hk) + Pos(x, y, SB_TOP - 3.0) * Cylinder(1.0, 6.0)
        out = s if out is None else out + s
    return out


def parts():
    return {"carrier": carrier(), "sensor_board": board(), "sb_pads": pads(), "cn2": cn2(), "spacers": spacers(),
            "msr": msr(), "passives": passives(), "mic": mic(), "sht45": sht45(), "sb_screws": screws()}


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
