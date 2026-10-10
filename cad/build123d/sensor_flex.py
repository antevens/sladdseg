"""SENSOR FLEX (D-27, D-47): single-layer flex in the trim from the MSR-2's CN2 to the SHT45.

Route: plug end under the MSR-2 (CN2 at the board's right end), out through the bay frame's right
wall and up to just under the face skin while running right, a 45 deg fold into the top-right
corner, down the corner run (the I2S microphone, D-29, on a section widened to the left, then the
spring-finger section: two Harwin S7081-42R, +5 V and GND, side by side on the flex underside over
the gold pads of the 5 V jumper's pad end on the corner shelf), narrowed to FLEX_RUN_W down the
flange's right band (on the flange top, in a groove of the trim), a 45 deg fold at the bottom and
along the bottom to the SHT45 bay, the SHT45 soldered on the flex tail.
Open (D-27): CN2's exact part, contact count and pin map (MEASURE).
"""
from math import atan2, degrees, hypot
from build123d import Box, Cylinder, Pos, Rot
from params import *
from common import rr, slab, taper

Z_LO, Z_HI, Z_BAND, Z_SHT = FLEX_Z_LO, FLEX_Z_HI, FLEX_Z_BAND, FLEX_Z_SHT
Y_ON, Y_CLIMB = FLEX_Y_ON, FLEX_Y_CLIMB          # band run fully on the flange / climbs from Z_HI

Y_NARROW = FINGER_SEC_Y[0]                       # the run narrows to FLEX_RUN_W below the finger section

# centre line, with the flex width of each leg
ROUTE = [((MSR_CN2_X, MSR_Y, Z_LO), FLEX_W), ((FLEX_EXIT_X, MSR_Y, Z_LO), FLEX_W), ((FLEX_X, MSR_Y, Z_HI), FLEX_W),
         ((FLEX_X, Y_NARROW, Z_HI), FLEX_RUN_W),
         ((FLEX_BAND_X, Y_NARROW, Z_HI), FLEX_RUN_W), ((FLEX_BAND_X, Y_CLIMB, Z_HI), FLEX_RUN_W),
         ((FLEX_BAND_X, Y_ON, Z_BAND), FLEX_RUN_W), ((FLEX_BAND_X, -Y_ON, Z_BAND), FLEX_RUN_W),
         ((FLEX_BAND_X, -Y_CLIMB, Z_HI), FLEX_RUN_W), ((FLEX_BAND_X, SHT_Y, Z_HI), FLEX_RUN_W),
         ((SHT_ENTRY, SHT_Y, Z_HI), FLEX_RUN_W),
         ((SHT_PADDLE, SHT_Y, Z_HI + (Z_SHT - Z_HI) * (SHT_ENTRY - SHT_PADDLE) / SHT_ENTRY), FLEX_W),
         ((0.0, SHT_Y, Z_SHT), None)]


def segment(a, b, w=FLEX_W, t=SFLEX_T):
    """Flat strip w x t from a to b (a run in x with a change in z, or in the y-z plane)."""
    dx, dy, dz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    c = Pos((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2)
    if abs(dy) < 1e-9:
        tilt = degrees(atan2(dz, dx))
        return c * Rot(0, -tilt, 0) * Box(hypot(dx, dz) + 0.01, w, t)
    if abs(dx) < 1e-9:
        tilt = degrees(atan2(dz, dy))
        return c * Rot(tilt, 0, 0) * Box(w, hypot(dy, dz) + 0.01, t)
    raise ValueError("segments run along x or along y")


def flex():
    out = plug_end()
    for (a, w), (b, _) in zip(ROUTE, ROUTE[1:]):
        if abs(a[1] - b[1]) < 1e-9 and abs(a[2] - b[2]) < 1e-9 and abs(a[0] - b[0]) < 1.0:
            continue                                  # the narrowing step: the run's right edge stays put
        out += segment(a, b, w)
    return out


def plug_end():
    """Plug end and neck taper of the flex at the wall plane (outline from params.flex_half_width)."""
    from build123d import Polyline, extrude, make_face
    xs = [-FLEX_PLUG[0] / 2, FLEX_PLUG[0] / 2, FLEX_PLUG[0] / 2 + FLEX_NECK_L]
    top = [(MSR_CN2_X + x, MSR_Y + flex_half_width(x)) for x in xs]
    bot = [(MSR_CN2_X + x, MSR_Y - flex_half_width(x)) for x in reversed(xs)]
    face = make_face(Polyline(*top, *bot, top[0]))
    return Pos(0, 0, Z_LO - SFLEX_T / 2) * extrude(face, SFLEX_T)


def stiffeners():
    """FR4 stiffeners: under the CN2 plug (wall side) and over the spring fingers and the mic (skin side)."""
    plug = Pos(MSR_CN2_X, MSR_Y, PLUG_STIFF_T / 2) * Box(B2B[0] + 2.0, FLEX_W, PLUG_STIFF_T)
    x0, x1 = FINGER_SEC_IN, FLEX_RIGHT
    y0, y1 = FINGER_SEC_Y[0], max(y for _, y in FINGERS) + FINGER_PAD[1] / 2 + 0.5
    fingers = Pos((x0 + x1) / 2, (y0 + y1) / 2, FLEX_HI_Z + SFLEX_T + STIFF_T / 2) * Box(x1 - x0, y1 - y0, STIFF_T)
    return plug + fingers + mic_stiffener()


def mic_section():
    """Flex widened to the left over the microphone (D-29)."""
    (y0, y1), x1 = MIC_SEC_Y, FLEX_RIGHT
    return Pos((MIC_SEC_IN + x1) / 2, (y0 + y1) / 2, FLEX_HI_Z + SFLEX_T / 2) * Box(x1 - MIC_SEC_IN, y1 - y0, SFLEX_T)


def mic_stiffener():
    """FR4 stiffener over the microphone (skin side), port hole through flex and stiffener."""
    w, h = MIC[0] + 1.0, MIC[1] + 1.0
    z = FLEX_HI_Z + SFLEX_T + STIFF_T / 2
    s = Pos(MIC_X, MIC_Y, z) * Box(w, h, STIFF_T)
    return s - Pos(*MIC_PORT, z) * Cylinder(MIC_FLEX_HOLE_D / 2, STIFF_T + 0.1)


def mic():
    """Microphone body under the flex and the adhesive gasket ring between stiffener and skin."""
    body = Pos(MIC_X, MIC_Y, FLEX_HI_Z - MIC[2] / 2) * Box(*MIC)
    z0 = FLEX_HI_Z + SFLEX_T + STIFF_T
    ring = Pos(*MIC_PORT, (z0 + SKIN_Z) / 2) * (Cylinder(MIC_GASKET_D / 2, SKIN_Z - z0)
                                                - Cylinder(MIC_SKIN_HOLE_D / 2, SKIN_Z - z0 + 0.1))
    return body + ring


def finger_section():
    """Flex widened to the left from the corner fold down over the two spring fingers (the +5 V lane climbs to
    the outer finger)."""
    (y0, y1), x0, x1 = FINGER_SEC_Y, FINGER_SEC_IN, FLEX_RIGHT
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, FLEX_HI_Z + SFLEX_T / 2) * Box(x1 - x0, y1 - y0, SFLEX_T)


def fingers():
    """Spring fingers at their working height (envelope: body footprint x working height)."""
    out = None
    for x, y in FINGERS:
        f = Pos(x, y, FLEX_HI_Z - FINGER_WH / 2) * Box(FINGER[0], FINGER[1], FINGER_WH)
        out = f if out is None else out + f
    return out


def tongue():
    """Battery-free tongue (D-49) from the finger section to the floor insert's first slot (the floor part is
    floor_na's): the band, the fold, under the trim's groove and tab, behind the trim's strip down the arc."""
    from common import ribbon
    u = tongue_arc()[1]
    return ribbon(na_tongue_route(), BC_NA_NECK_W, SFLEX_T, (u[0], u[1], 0))


def target():
    """The 5 V jumper's pad end on the corner shelf (flex on its stiffener): gold pads under the fingers."""
    (x0, x1), (y0, y1) = TARGET_X, TARGET_Y
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, SHELF_TOP_Z + TARGET_T / 2) * Box(x1 - x0, y1 - y0, TARGET_T)


def shelf_limit():
    """How far beyond the seal band the shelf reaches: 45 deg up to SHELF_UNDER_Z, then SHELF_OUT flat."""
    return SHELF_UNDER_Z + SHELF_OUT


def shelf():
    """Insert shelf at the flange's top-right corner carrying the jumper's pad end: a block from the flange
    out under the pad end, its underside 45 deg out from the seal band (prints unsupported), flat for at most
    SHELF_OUT beyond that. The flange's outer face below the pad end keeps it from sliding down."""
    import insert
    x0 = max(TARGET_X[0] - 0.2, FRAME_RIGHT + SPLIT_CLR)
    x1 = TARGET_X[1] + 0.5
    y0, y1 = FLANGE_OUT[1] / 2 - 9.0, TARGET_Y[1] + 0.5
    block = Pos((x0 + x1) / 2, (y0 + y1) / 2, SHELF_TOP_Z / 2) * Box(x1 - x0, y1 - y0, SHELF_TOP_Z)
    r = PLUG_R + COLLAR_LIP
    lower = taper(*SEAL, r, 0, SHELF_UNDER_Z, SHELF_UNDER_Z)
    g = shelf_limit()
    upper = slab(rr(SEAL[0] + 2 * g, SEAL[1] + 2 * g, r + g), SHELF_UNDER_Z - 0.01, SHELF_TOP_Z + 0.01)
    return (block & (lower + upper)) - insert.pass_through()


def plug():
    """CN2 mating plug envelope (MEASURE: footprint and contact count to be confirmed)."""
    z0 = PLUG_STIFF_T + SFLEX_T
    return Pos(MSR_CN2_X, MSR_Y, z0 + B2B_STACK / 2) * Box(B2B[0], B2B[1], B2B_STACK)


def sht45():
    return Pos(0.0, SHT_Y, Z_SHT + SFLEX_T / 2 + SHT_CHIP[2] / 2) * Box(*SHT_CHIP)


def parts():
    port = Pos(*MIC_PORT, FLEX_HI_Z + SFLEX_T / 2) * Cylinder(MIC_FLEX_HOLE_D / 2, SFLEX_T + 0.1)
    return {"flex": flex() + finger_section() + mic_section() + stiffeners() - port, "fingers": fingers(),
            "target": target(), "plug": plug(), "sht45": sht45(), "mic": mic()}
