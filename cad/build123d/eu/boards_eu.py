"""EU bought-in parts and boards as envelopes (D-30, D-36), for clearance checks and renders only:
the BILRESA model, the supplied steel piece in the pocket floor's recess, the emergency rocker, the mains board
(rocker, WAGO blocks, fuse, MOV, PSU over its relief slot, header on the 5 V island) and the 5 V
board (socket, capacitor, spring pins up through the barrier onto the sensor board's and the back cover's pads, R9).
"""
from build123d import Box, Cylinder, Pos
from params_eu import *


def remote(lift=0.0):
    """BILRESA model on the barrier's pocket floor."""
    import bilresa
    return bilresa.build(SEAT_Z, lift)


def magnet():
    """The cut steel piece in the pocket floor's recess: round end down (-y), the cut edge up towards the switch cup."""
    t, r = MAGNET[2] - 0.01, MAGNET_END_R
    z = (MAGNET_Z[0] + MAGNET_Z[1]) / 2 - 0.005
    y0, y1 = MAGNET_REC_Y - MAGNET[1] / 2, MAGNET_REC_Y + MAGNET[1] / 2
    body = Pos(0, (y0 + r + y1) / 2, z) * Box(MAGNET[0], y1 - y0 - r, t)
    return body + Pos(0, y0 + r, z) * Cylinder(r, t)


def switch():
    """Marquardt 1802.2504 (drawing rev g): flange on the panel face, rocker up to SW_ROCKER_H (+ tolerance),
    body below the panel face down to the PCB seat (the mains board's front)."""
    flange = Pos(0, SW_Y, PANEL_TOP_Z + 1.0) * Box(SW_BEZEL[0], SW_BEZEL[1], 2.0)
    rocker = Pos(0, SW_Y, PANEL_TOP_Z + (SW_ROCKER_H + SW_ROCKER_TOL) / 2) * Box(19.0, 16.0, SW_ROCKER_H + SW_ROCKER_TOL)
    body = Pos(0, SW_Y, (PANEL_TOP_Z + MB_FRONT) / 2) * Box(SW_BODY[0], SW_BODY[1], PANEL_TOP_Z - MB_FRONT)
    return flange + rocker + body


def switch_model():
    """The rocker's 3D model from the EU KiCad project (Marquardt 1802.1108 housing on the 1802.2504
    underside, pcb/tools/gen_3d.py) at its place on the mains board's front; the envelope without it."""
    from pathlib import Path
    from build123d import Rot, import_step
    f = Path(__file__).resolve().parents[3] / "pcb" / "eu" / "kicad" / "3d" / "Marquardt_1802.2504.step"
    if not f.exists():
        return switch()
    return Pos(0, SW_Y, MB_FRONT) * Rot(0, 0, 180 if SW_SW_DIR < 0 else 0) * import_step(str(f))


def _notched(disc, z0, t):
    for x, y in DOMES:                                   # round the box's screw domes
        disc -= Pos(x, y, z0 - t / 2) * Cylinder(DOME_NOTCH_R, t + 1)
    return disc


def pin_board():
    """pin board: the box circle less clearance, cut straight below the switch cup, notched round
    the domes; holes for its screws and for the mains board's long boss."""
    z = PB_FRONT - PB_T / 2
    disc = Pos(0, 0, z) * Cylinder(PB_R, PB_T)
    disc &= Pos(0, PB_CUT_Y - 50, z) * Box(100, 100, PB_T + 1)
    disc = _notched(disc, PB_FRONT, PB_T)
    for x, y in PB_MOUNT:
        disc -= Pos(x, y, z) * Cylinder(PB_MOUNT_D / 2, PB_T + 1)
    for x, y in MB_BOSS:
        if y < PB_CUT_Y:
            disc -= Pos(x, y, z) * Cylinder(MB_BOSS_D / 2 + MB_BOSS_CLR, PB_T + 1)
    return disc


def blank_board():
    """Printed blank board for the switch-only edition (D-127, D-131), printed with the barrier in V-0: the pin board's
    outline, on its bosses and screws, resting on the barrier's ridge; a peg up each of the barrier's four pin holes to
    just under its face (BLANK_CLR round it) and its own ridge beside the barrier's (ridges_eu.blank_ridge()) up to
    BLANK_LEDGE[1] under the barrier: it stiffens the board and, with the barrier's ridge, closes the box."""
    import ridges_eu
    out = pin_board()
    for x, y in tuple(PINS) + tuple(BC_FINGERS):
        z1 = CAP_T - BLANK_CLR
        out += Pos(x, y, (PB_FRONT + z1) / 2) * Cylinder(PIN_CAP_HOLE_D / 2 - BLANK_CLR, z1 - PB_FRONT)
    return out + ridges_eu.solid(ridges_eu.blank_ridge(), PB_FRONT - 0.01, -BLANK_LEDGE[1])


def mains_board():
    """Mains board: the box circle less clearance, notched round the domes, the relief slot under the
    PSU, holes for the long bosses."""
    z = MB_FRONT - MB_T / 2
    disc = _notched(Pos(0, 0, z) * Cylinder(PB_R, MB_T), MB_FRONT, MB_T)
    x0, x1, ys, w = MB_SLOT
    disc -= Pos((x0 + x1) / 2, ys, z) * Box(x1 - x0, w, MB_T + 1)
    for x in (x0, x1):
        disc -= Pos(x, ys, z) * Cylinder(w / 2, MB_T + 1)
    for x, y in MB_BOSS:
        disc -= Pos(x, y, z) * Cylinder(PB_MOUNT_D / 2, MB_T + 1)
    return disc


def domes():
    """The box's four screw domes (MEASURE), full depth, for clearance checks."""
    out = None
    for x, y in DOMES:
        d = Pos(x, y, -BOX_D / 2) * Cylinder(DOME_D / 2, BOX_D)
        out = d if out is None else out + d
    return out


def pins():
    """Sensor spring pins (P70-2200045) on the pin board's front at the design working height, tips on the sensor board's
    pads."""
    from common import pogo
    out = None
    for x, y in PINS:
        p = pogo(x, y, PB_FRONT, SB_PAD_Z, PIN_FLANGE, PIN_BARREL, PIN_PLUNGER_D)
        out = p if out is None else out + p
    return out


def bf_pins():
    """Battery-free spring pins (P70-2200045) on the pin board's front, tips on the back cover's pads (D-54, D-59)."""
    from common import pogo
    out = None
    for x, y in BC_FINGERS:
        p = pogo(x, y, PB_FRONT, BF_TIP_Z, PIN_FLANGE, PIN_BARREL, PIN_PLUNGER_D)
        out = p if out is None else out + p
    return out


def psu():
    return Pos(*MB_PSU_C, MB_BACK - PSU[2] / 2) * Box(*PSU)


def wago():
    """The two WAGO 2604-3102 blocks on the mains board's back, poles along y; conductors enter
    their far face (90 deg to the PCB)."""
    out = None
    for c in MB_WAGO_C:
        b = Pos(*c, MB_BACK - WAGO2[2] / 2) * Box(WAGO2[1], WAGO2[0], WAGO2[2])
        out = b if out is None else out + b
    return out


def _ep():
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "pcb" / "eu" / "tools"))
    import parts_eu
    return parts_eu


def _boxes(sizes, parts, z0):
    out = None
    for ref, (w, h, t) in sizes.items():
        x, y, rot = parts[ref]["pos"]
        if rot % 180:
            w, h = h, w
        b = Pos(x, y, z0 + t / 2) * Box(w, h, t)
        out = b if out is None else out + b
    return out


def front_parts():
    """Capacitor on the pin board's front (position from pcb/eu/tools/parts_eu.py)."""
    return _boxes(FRONT_PARTS, _ep().PB_PARTS, PB_FRONT)


def mains_front_parts():
    """Fuse and varistor on the mains board's front."""
    return _boxes(MB_FRONT_PARTS, _ep().MB_PARTS, MB_FRONT)


def header_body():
    """The header's plastic body on the mains board (pin 1 at MB_HDR, pin 2 2.54 below)."""
    x, y = MB_HDR
    return Pos(x, y - HDR[0] / 2, MB_FRONT + HDR_BODY / 2) * Box(HDR[0], HDR[1], HDR_BODY)


def header():
    """2-pin SMT header on the mains board's 5 V island: body and posts."""
    x, y = MB_HDR
    h = header_body()
    for yy in (y, y - 2.54):
        h += Pos(x, yy, MB_FRONT + HDR[2] / 2) * Box(0.64, 0.64, HDR[2])
    return h


def socket():
    """2-pin socket on the pin board's back, over the header."""
    x, y = MB_HDR
    return Pos(x, y - HDR[0] / 2, PB_BACK - SOCKET[2] / 2) * Box(SOCKET[0], SOCKET[1], SOCKET[2])


def parts():
    return {"board": pin_board(), "mains_board": mains_board(), "psu": psu(), "wago": wago(), "switch": switch(),
            "magnet": magnet(), "front": front_parts(), "mains_front": mains_front_parts(), "header": header(),
            "socket": socket(), "pins": pins(), "bf_pins": bf_pins()}
