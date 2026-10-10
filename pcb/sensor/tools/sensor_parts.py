"""Parts, nets and geometry for the sensor flex and the power jumper (docs/DESIGN.md D-27).

Geometry comes from cad/build123d/params.py, so the boards follow the CAD route and shelf.

Sensor flex, single copper layer: a straight strip in the flat. Each 90 degree corner of the
route in the trim is a 45 degree fold, which turns the strip over, so the CN2 plug (facing the
MSR-2), the spring fingers (facing the target) and the SHT45 (facing the vents) all sit on the
copper side. Two copper layers (D-47). Flat coordinates: X along the strip from the plug centre, Y
across it; on the corner run, down the band and below it Y = FLEX_X - room x. The two spring fingers
(side by side across the strip) sit on a section widened to the left (+Y) in the corner; the I2S
microphone (D-29) on another below the band, before the bottom fold.

Power jumper: single-layer flex from the wiring board's J2 (FH12 slide lock) through the
pass-through to a stiffened pad end on the corner shelf, under the spring fingers.
"""
import sys
import uuid
from math import hypot
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "cad" / "build123d"))
from params import (MSR_CN2_X, MSR_Y, FLEX_X, FLEX_W, FLEX_RUN_W, FLEX_RIGHT, FLEX_EXIT_X, FLEX_BAND_X, FLEX_BAND_Z,
                    STIFF_T, FLEX_T, SFLEX_T, FLEX_HI_Z, SHT_Y, SHT_CHIP, SKIN_Z, SHT_ENTRY, FINGERS, FINGER_PAD, FINGER,
                    FLEX_Z_LO, FLEX_Z_HI, FLEX_Z_BAND, FLEX_Z_SHT, FLEX_Y_ON, FLEX_Y_CLIMB, SHT_PADDLE, MIC_SEC_IN,
                    PLUG_STIFF_T,
                    FINGER_SEC_IN, FINGER_SEC_Y, TARGET_X, TARGET_Y, SHELF_TOP_Z, TARGET_T, JUMPER_JOIN,
                    JUMPER_W, JUMPER_END, JUMPER_T, JUMPER_SERVICE, jumper_length, jumper_path, tongue_arc, pocket_wall_y,
                    AAA_L, BC_CELL_X, BC_CELL_Y0, BC_CELL_Z, BC_TERM_Y, BC_VBAT_X, BC_FLEX_Z, BC_END_T, BC_END_H,
                    BC_FINGERS, BC_STRIP, BC_RUN, BC_JOG, BC_CONTACT_W, BC_COPPER_Y, BC_REG, BC_PCB_W, BC_PCB_CLR, BC_BRIDGE_H, BC_LANE_H,
                    BC_END_CORNER, BC_NA_BAND_Y, BC_NA_NECK_W, BC_NA_DOWN, BC_NA_SLOT, BC_NA_TAIL, na_tongue_route,
                    BC_FLOOR_PAD, BC_TONGUE_W, BC_FLOOR_T, BC_RECESS_CLR, SEAT_Z, TARGET_TOP_Z, DECK_Z,
                    BC_PAD_END, BC_PAD_STIFF_T, end_top,
                    MIC, MIC_Y, MIC_FLEX_Y, MIC_SEC_W, MIC_SEC_Y, MIC_FLEX_HOLE_D, FLEX_PLUG, FLEX_NECK_L)

LIB = "sensor"
REV = "v0.1"
FLEX, JUMPER, COVER = "sensor_flex", "power_jumper", "cover_flex"

# ---- route lengths (3D) -> flat X positions --------------------------------------------
_z_lo, _z_hi, _z_sht = FLEX_Z_LO, FLEX_Z_HI, FLEX_Z_SHT
_dz_band = FLEX_Z_BAND - _z_hi
S_B = (FLEX_EXIT_X - MSR_CN2_X) + hypot(FLEX_X - FLEX_EXIT_X, _z_hi - _z_lo)   # plug -> corner (fold 1)
_climb = hypot(FLEX_Y_CLIMB - FLEX_Y_ON, _dz_band)
S_D = S_B + (MSR_Y - FLEX_Y_CLIMB) + 2 * _climb + 2 * FLEX_Y_ON + (-FLEX_Y_CLIMB - SHT_Y)   # bottom corner (fold 2)
_tail = hypot(SHT_ENTRY, _z_hi - _z_sht)
S_F = S_D + (FLEX_BAND_X - SHT_ENTRY) + _tail               # SHT45 at the tail
S_PADDLE = S_F - _tail * SHT_PADDLE / SHT_ENTRY         # the tail widens back to FLEX_W for the SHT45


def s_corner(y):
    """Flat X of a point on the corner run at room y (above the band's climb)."""
    return S_B + (MSR_Y - y)


S_LOW0 = S_B + (MSR_Y - FLEX_Y_CLIMB) + 2 * _climb + 2 * FLEX_Y_ON   # where the run leaves the band at the bottom


def s_low(y):
    """Flat X of a point on the run below the band (room y below -FLEX_Y_CLIMB)."""
    return S_LOW0 + (-FLEX_Y_CLIMB - y)


def y_corner(x):
    """Flat Y of a point on the corner run, the band or the run below it at room x (+Y to the left)."""
    return FLEX_X - x


# ---- flex outline (flat): plug pad, strip, finger section, narrow band, mic section, tail ---------
HALF = FLEX_W / 2
RUN_LO, RUN_HI = y_corner(FLEX_RIGHT), y_corner(FLEX_RIGHT - FLEX_RUN_W)   # band strip across Y
RUN_C = (RUN_LO + RUN_HI) / 2
PLUG_HALF, PLUG_LEN = FLEX_PLUG[1] / 2, FLEX_PLUG[0] / 2   # plug end: room for the fan-out
SEC_X0, SEC_X1 = s_corner(FINGER_SEC_Y[1]), s_corner(FINGER_SEC_Y[0])   # finger section along X
SEC_Y = y_corner(FINGER_SEC_IN)                             # finger section's left edge (+Y)
MIC_X0, MIC_X1 = s_low(MIC_SEC_Y[1]), s_low(MIC_SEC_Y[0])   # microphone section along X
MIC_XC = s_low(MIC_Y)                                       # mic body centre (flat), port end towards -X
TAIL_X = S_F + 3.6
NECK_X = PLUG_LEN + FLEX_NECK_L                             # gentle taper from the plug end to the strip
def _offset(pts, d):
    """Polyline pts offset by d to the left of travel (mitred corners)."""
    segs = []
    for a, b in zip(pts, pts[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = hypot(dx, dy)
        segs.append(((a[0] - dy / n * d, a[1] + dx / n * d), (b[0] - dy / n * d, b[1] + dx / n * d)))
    out = [segs[0][0]]
    for (a1, b1), (a2, b2) in zip(segs, segs[1:]):
        d1, d2 = (b1[0] - a1[0], b1[1] - a1[1]), (b2[0] - a2[0], b2[1] - a2[1])
        den = d1[0] * d2[1] - d1[1] * d2[0]
        if abs(den) < 1e-12:
            out.append(b1)
            continue
        t = ((a2[0] - a1[0]) * d2[1] - (a2[1] - a1[1]) * d2[0]) / den
        out.append((a1[0] + t * d1[0], a1[1] + t * d1[1]))
    out.append(segs[-1][1])
    return out


# Battery-free tongue (D-49) off the finger section's left edge (flat +Y): the band, the 45 deg fold (the strip
# runs on straight in the flat; copper up after it), down the plate, the radial turn (an elbow in the flat), the
# bends down the arc, the jog and onto the floor (straight in the flat), the elbow back to the strip down the
# floor, the rise through the floor insert's slot, the pad strip (copper up, TP3 / TP4), the drop, the tail.
# After the fold a room direction (dx, dy) is (-dx, -dy) in the flat.
_R = na_tongue_route()
_u = tongue_arc()[1]
_dirs = [(0.0, 1.0)] * 3 + [(_u[0], _u[1])] * 5 + [(0.0, 1.0)]
_T = [(s_corner(BC_NA_BAND_Y), SEC_Y)]
for (a, b), d in zip(zip(_R, _R[1:]), _dirs):
    n = hypot(*(b[i] - a[i] for i in range(3)))
    _T.append((_T[-1][0] + n * d[0], _T[-1][1] + n * d[1]))
_y_bot = min(y for _, y in BC_FINGERS) - BC_FLOOR_PAD[1] / 2 - 1.0
_l_slot = hypot(BC_NA_SLOT, BC_FLOOR_T - SFLEX_T - BC_RECESS_CLR)
X_DOWN = _T[-1][0]
Y_PS0 = _T[-1][1] + _l_slot                                 # pad strip on the floor insert's top
Y_PS1 = Y_PS0 + (BC_NA_DOWN[2] - _y_bot)
Y_TAIL = Y_PS1 + _l_slot + BC_NA_TAIL
X_PC = X_DOWN + (BC_NA_DOWN[0] - BC_FINGERS[0][0])           # pad strip centre (under the fingers)
TONGUE_PATH = _T + [(X_DOWN, Y_PS0)]
TONGUE_FOLD = _T[2]


def tongue_floor(room_x, room_y):
    """Flat (X, Y) of a point on the pad strip (room coordinates on the floor insert's top)."""
    return X_DOWN + (BC_NA_DOWN[0] - room_x), Y_PS0 + (BC_NA_DOWN[2] - room_y)


_hw, _pw = BC_NA_NECK_W / 2, BC_TONGUE_W / 2
_right, _left = _offset(TONGUE_PATH, -_hw), _offset(TONGUE_PATH, _hw)
TONGUE_PTS = (_right + [(X_PC + _pw, Y_PS0), (X_PC + _pw, Y_PS1), (X_PC + _hw, Y_PS1), (X_PC + _hw, Y_TAIL),
                        (X_PC - _hw, Y_TAIL), (X_PC - _hw, Y_PS1), (X_PC - _pw, Y_PS1), (X_PC - _pw, Y_PS0)]
              + _left[::-1])

FLEX_OUTLINE = [(-PLUG_LEN, -PLUG_HALF), (PLUG_LEN, -PLUG_HALF), (NECK_X, -HALF), (SEC_X1, -HALF), (SEC_X1, RUN_LO),
                (S_PADDLE, RUN_LO), (S_PADDLE, RUN_C - HALF), (TAIL_X, RUN_C - HALF), (TAIL_X, RUN_C + HALF),
                (S_PADDLE, RUN_C + HALF), (S_PADDLE, RUN_HI), (MIC_X1, RUN_HI), (MIC_X1, MIC_SEC_W), (MIC_X0, MIC_SEC_W),
                (MIC_X0, RUN_HI), (SEC_X1, RUN_HI), (SEC_X1, SEC_Y)] + TONGUE_PTS + [(SEC_X0, SEC_Y), (SEC_X0, HALF), (NECK_X, HALF),
                (PLUG_LEN, PLUG_HALF), (-PLUG_LEN, PLUG_HALF)]


def _clean(pts):
    """Drop repeated points and points on a straight line between their neighbours (closed outline)."""
    out = [q for i, q in enumerate(pts) if abs(q[0] - pts[i - 1][0]) + abs(q[1] - pts[i - 1][1]) > 1e-6]
    keep = []
    for i, q in enumerate(out):
        a, b = out[i - 1], out[(i + 1) % len(out)]
        if abs((q[0] - a[0]) * (b[1] - a[1]) - (q[1] - a[1]) * (b[0] - a[0])) > 1e-9:
            keep.append(q)
    return keep


FLEX_OUTLINE = _clean(FLEX_OUTLINE)
FOLDS = ((S_B, 0.0, HALF), (S_D, RUN_C, FLEX_RUN_W / 2))   # 45 deg folds (fab drawing): X, strip centre, half width
_mic_stiff = ((MIC_XC - MIC[1] / 2 - 0.5, MIC_FLEX_Y - MIC[0] / 2 - 0.5),
              (MIC_XC + MIC[1] / 2 + 0.5, MIC_FLEX_Y + MIC[0] / 2 + 0.5))
FIN_X0 = s_corner(FINGERS[0][1] + FINGER_PAD[1] / 2 + 0.5)  # finger stiffener along X
STIFFENERS = [((-PLUG_LEN, -PLUG_HALF), (PLUG_LEN, PLUG_HALF), PLUG_STIFF_T),     # behind the CN2 plug
              ((FIN_X0, -HALF), (SEC_X1, SEC_Y), STIFF_T),                        # behind the fingers
              _mic_stiff + (STIFF_T,)]                                            # behind the microphone

# ---- CN2 mate: placeholder until the part and contact map are confirmed (MEASURE) ----------
CN2_CONFIRMED = False
CN2_PINS, CN2_PITCH, CN2_ROW = 30, 0.4, 1.2                 # 2 x 15, rows at Y +-CN2_ROW
# Placeholder map: lane -> contact, chosen so the fan-out keeps the lane order the outer (+5V) and inner
# (GND) fingers, the microphone and the SHT45 need. NOT the MSR-2's pinout. The microphone and the SHT45
# share a ground contact of their own (net GND_SENS, joined to GND on the MSR-2): the fingers' GND
# leaves the strip at the inner finger.
CN2_MAP = {"+5V": "19", "GND": "21", "I2S_WS": "23", "I2S_SCK": "25", "I2S_SD": "27",
           "GND_SENS": "30", "+3V3": "28", "SDA": "26", "SCL": "24"}
I2S_GPIO = {"I2S_SCK": "IO4", "I2S_WS": "IO6", "I2S_SD": "IO7"}   # MSR-2 GPIOs (D-29), free on CN2


FP_B2B = "B2B_0.4mm_2x15_PLACEHOLDER"
FP_FINGER = "Harwin_S7081-42R"
FP_SHT = "Sensirion_DFN-4_1.5x1.5mm_P0.8mm_SHT4x_NoCentralPad"
FP_C = "C_0402_1005Metric"
FP_SOT = "SOT-23-5"
TLV_DS = "https://www.ti.com/lit/ds/symlink/tlv755p.pdf"
FP_TP_CONTACT = "Contact_Pad_2.2x4.5mm"
FP_FPC = "FPC_6P_P0.50mm_Contacts"
HARWIN_DS = ("https://content.harwin.com/asset/8cd5d0a8-d578-46b3-8278-7289045a1613/"
             "DRG-02322-Technical-Drawing-Datasheet-S7081R-pdf.pdf")
SHT_DS = "https://sensirion.com/media/documents/33FD6951/624C4357/Datasheet_SHT4x.pdf"
FP_MIC = "PUI_DMM-4026-B-I2S_4x3mm"
FP_R = "R_0402_1005Metric"
MIC_DS = "https://api.puiaudio.com/filename/DMM-4026-B-I2S-R.pdf"
# DMM-4026-B-I2S-R land pattern (datasheet rev A), body frame with +y towards the port: pad columns
# 2.15 apart, rows 0.65 apart, the port 1.28 below the nearest row; pads 0.60 x 0.40; GND ring
# 1.05 / 1.65. Top view: LR, CONFIG, VDD on one column, SD, SCK, WS on the other, far end first.
MIC_PAD, MIC_COL, MIC_ROW, MIC_PORT_ROW = (0.60, 0.40), 2.15 / 2, 0.65, 1.28
MIC_RING = (1.05, 1.65)

# ref: symbol, footprint, value, pin -> net, flat (x, y, rot), bom
FLEX_PARTS = {
    "J1": dict(sym="Conn_02x15_Odd_Even", fp=FP_B2B, value="CN2 mate (TBD)", label="CN2 mate (TBD)",
               nets={pin: lane for lane, pin in CN2_MAP.items()}, pos=(0.0, 0.0, 0), mfr="TBD", mpn="TBD",
               desc="Board-to-board plug mating the MSR-2's rear connector CN2, 0.4 mm, 2 rows (part and "
                    "contact map unconfirmed)", ds=""),
    "J2": dict(sym="Conn_01x01", fp=FP_FINGER, value="S7081-42R +5V", nets={"1": "+5V"}, label="Harwin S7081-42R +5V",
               pos=(s_corner(FINGERS[0][1]), y_corner(FINGERS[0][0]), 0), mfr="Harwin", mpn="S7081-42R",
               desc="SMT spring finger, gold, 4 A, working height 2.0 mm: +5 V from the target board", ds=HARWIN_DS),
    "J3": dict(sym="Conn_01x01", fp=FP_FINGER, value="S7081-42R GND", nets={"1": "GND"}, label="Harwin S7081-42R GND",
               pos=(s_corner(FINGERS[1][1]), y_corner(FINGERS[1][0]), 0), mfr="Harwin", mpn="S7081-42R",
               desc="SMT spring finger, gold, 4 A, working height 2.0 mm: GND from the target board", ds=HARWIN_DS),
    "TP3": dict(sym="TestPoint", fp="Contact_Pad_7x4mm", value="+5V floor pad", nets={"1": "+5V"}, in_bom=False,
                label="+5V", pos=(*tongue_floor(*BC_FINGERS[0]), 90),
                desc="Floor pad under the back cover's +5V finger (D-41, D-49)"),
    "TP4": dict(sym="TestPoint", fp="Contact_Pad_7x4mm", value="GND floor pad", nets={"1": "GND"}, in_bom=False,
                label="GND", pos=(*tongue_floor(*BC_FINGERS[1]), 90),
                desc="Floor pad under the back cover's GND finger (D-41, D-49)"),
    "U1": dict(label="Sensirion SHT45", sym="SHT4x", fp=FP_SHT, value="SHT45", nets={"1": "SDA", "2": "SCL", "3": "+3V3", "4": "GND_SENS"},
               pos=(S_F, RUN_C, 0), mfr="Sensirion", mpn="SHT45-AD1B-R2",
               desc="Humidity and temperature sensor, I2C 0x44", ds=SHT_DS),
    "C1": dict(label="100nF", sym="C", fp=FP_C, value="100nF", nets={"1": "+3V3", "2": "GND_SENS"},
               pos=(S_F + 2.6, RUN_C, 90), mfr="any", mpn="0402 X7R 100 nF 16 V",
               desc="SHT45 decoupling", ds=""),
    "MK1": dict(sym="DMM-4026-B-I2S", fp=FP_MIC, value="DMM-4026-B-I2S-R",
                nets={"1": "GND_SENS", "2": "GND_SENS", "3": "+3V3", "4": "GND_SENS", "5": "I2S_WS", "6": "I2S_SCK",
                      "7": "I2S_SD"},
                pos=(MIC_XC, MIC_FLEX_Y, 270), mfr="PUI Audio", mpn="DMM-4026-B-I2S-R",
                desc="I2S MEMS microphone, bottom port, 1.62-3.63 V; LR low = left channel", ds=MIC_DS),
    "C2": dict(label="100nF", sym="C", fp=FP_C, value="100nF", nets={"1": "GND_SENS", "2": "+3V3"},
               pos=(MIC_XC + 3.3, MIC_FLEX_Y + 1.08, 0), mfr="any", mpn="0402 X7R 100 nF 16 V",
               desc="Microphone decoupling", ds=""),
    "R1": dict(label="100k", sym="R", fp=FP_R, value="100k", nets={"1": "I2S_SD", "2": "GND_SENS"},
               pos=(MIC_XC + 3.3, MIC_FLEX_Y - 1.08, 0), mfr="any", mpn="0402 1% 100 kOhm",
               desc="I2S SD pull-down (microphone datasheet)", ds=""),
}

# 5 V flex jumper (R9, no wires, D-47): wiring board J2 (Hirose FH12-6S, slide lock) -> pass-through -> pad
# end on the corner shelf, under the sensor flex's spring fingers. Two copper layers. Flat coordinates, seen
# from the copper side: X along the strip from the connector-end tip, Y across it; on the pad end (copper up)
# X = PE_X0 + (room y - TARGET_Y[0]) and Y = PE_XE - room x (the run joins its lower edge going up).
END_W, END_L, END_T = JUMPER_END                              # connector end: width, stiffened length, thickness
PE_XE = jumper_path()[-1][0]                                  # room x where the run joins the pad end
PE_LEN = TARGET_Y[1] - TARGET_Y[0]
PE_X0 = END_L + jumper_length() - JUMPER_JOIN                 # the jumper's path ends JUMPER_JOIN into the pad end
PE_END = PE_X0 + PE_LEN
PE_Y0, PE_Y1 = PE_XE - TARGET_X[1], PE_XE - TARGET_X[0]       # pad end across (right, left edge)
FPC_PITCH, FPC_PAD = 0.5, (3.0, 0.3)                          # MEASURE contact pads (length x, width y), FH12 FPC spec
CONTACT_PAD = (4.5, 1.8)                                      # gold pad under a spring finger (x along the strip, y)
TRACK_W = 0.5                                                 # +5V / GND (MSR-2 < 0.2 A)
GND_Y, P5_Y = -0.75, 0.75                                     # run lanes: GND to the pad ahead, +5V to the one on the left
RUN_HALF = JUMPER_W / 2


def pe_x(room_y):
    """Flat X of a point on the pad end at room y."""
    return PE_X0 + (room_y - TARGET_Y[0])


def pe_y(room_x):
    """Flat Y of a point on the pad end at room x."""
    return PE_XE - room_x


FP_FLOOR_CONTACT = "Contact_Pad_7x4mm"
JUMPER_LEN = PE_END
JUMPER_OUTLINE = _clean([(0.0, -END_W / 2), (END_L, -END_W / 2), (END_L + 2.0, -RUN_HALF), (PE_X0 - 2.0, -RUN_HALF),
                   (PE_X0, PE_Y0), (PE_END, PE_Y0), (PE_END, PE_Y1)]
                  + [(PE_X0, PE_Y1), (PE_X0 - 2.0, RUN_HALF), (END_L + 2.0, RUN_HALF), (END_L, END_W / 2), (0.0, END_W / 2)])
JUMPER_STIFFENERS = [((0.0, -END_W / 2), (END_L, END_W / 2)),             # connector end: to FPC thickness
                     ((PE_X0, PE_Y0), (PE_END, PE_Y1))]                   # pad end: to the old target's 0.6 mm
# FPC contacts 1-3 GND (Y < 0), 4-6 +5V (Y > 0), matching J2's pins (check the contact side on a sample)
JUMPER_PARTS = {"J1": dict(sym="Conn_01x06", fp=FP_FPC, value="FPC 6P 0.5 mm", label="to FH12-6S: 1-3 GND 4-6 +5V",
                           nets={str(n): "GND" if n <= 3 else "+5V" for n in range(1, 7)},
                           pos=(0.2 + FPC_PAD[0] / 2, 0.0, 0), in_bom=False,
                           desc="Flex contacts into J2 of the wiring board (Hirose FH12-6S, slide lock)")}
JUMPER_PARTS.update({
    "TP1": dict(sym="TestPoint", fp=FP_TP_CONTACT, value="+5V contact", nets={"1": "+5V"}, in_bom=False, label="+5V",
                pos=(pe_x(FINGERS[0][1]), pe_y(FINGERS[0][0]), 0), desc="Under the +5 V spring finger (sensor flex J2)"),
    "TP2": dict(sym="TestPoint", fp=FP_TP_CONTACT, value="GND contact", nets={"1": "GND"}, in_bom=False, label="GND",
                pos=(pe_x(FINGERS[1][1]), pe_y(FINGERS[1][0]), 0), desc="Under the GND spring finger (sensor flex J3)"),
})


# Replacement back cover flex (D-35): two S7081-42R spring fingers on the pad section (on the cover's
# ledge, copper down, fingers through windows onto the plate's floor pads) -> run -> one 90 deg bend at
# the terminal end -> two more S7081-42R on the cell axes against the remote's battery contacts. Single
# copper layer, copper outside the bend. Flat coordinates, seen from the copper side: X = -x (remote),
# Y = y on the ledge; on the end section a point h above the bend line maps to Y = y_copper - h.
COVER_CONFIRMED = False                                     # positions are REF / MEASURE (FCC photos)
COVER_TRACK = 0.3
_y_c = BC_COPPER_Y                                          # end section copper face (room y) = bend line
_yt = max(y for _, y in BC_FINGERS) + FINGER[1] / 2 + BC_PAD_END
_yb = min(y for _, y in BC_FINGERS) - FINGER[1] / 2 - 1.0
_yj = _yb - BC_JOG
_xs0, _xs1 = -BC_STRIP[1], -BC_STRIP[0]                     # pad section in flat X
_xr0, _xr1 = -BC_RUN[1], -BC_RUN[0]                         # run in flat X
_xo = BC_CELL_X + BC_CONTACT_W / 2 + 0.5                    # end section half width
_xi = BC_PCB_W / 2 + BC_PCB_CLR                             # notch round the remote's PCB strip
_c = BC_END_CORNER
COVER_Y_BAND = _y_c - BC_BRIDGE_H                           # band under the PCB strip
COVER_Y_END = _y_c - BC_END_H
COVER_Y_PAD = _y_c - (BC_CELL_Z - BC_FLEX_Z)                # contact fingers on the cell axes
COVER_BEND_Y = _y_c
_top = [(x, _y_c - (z - BC_FLEX_Z)) for x, z in end_top(_xo, _xi)]  # rounded to the cell above the rim
COVER_OUTLINE = ([(_xs0, _yt), (_xs1, _yt), (_xs1, _yb), (_xr1, _yb), (_xr1, _y_c), (_xo - _c, _y_c), (_xo, _y_c - _c)]
                 + _top + [(_xi, COVER_Y_BAND), (-_xi, COVER_Y_BAND)] + [(-x, y) for x, y in reversed(_top)]
                 + [(-_xo, _y_c - _c), (-_xo + _c, _y_c), (_xr0, _y_c), (_xr0, _yj), (_xs0, _yj)])
COVER_STIFF = [((-_xo, COVER_Y_END), (_xo, _y_c))]          # FR4 BC_END_T behind the end section (non-copper side)
COVER_PAD_STIFF = [((_xs0, _yb), (_xs1, _yt)),                # FR4 BC_PAD_STIFF_T on the pad and regulator sections
                   ((min(_xs0, _xr0), _yj), (max(_xs1, _xr1), _yb))]
COVER_LANES = (_xr1 - 0.75, _xr0 + 0.75)                    # +3V3 (inner), GND (outer) down the run
COVER_PARTS = {
    "J1": dict(sym="Conn_01x01", fp=FP_FINGER, value="S7081-42R +5V", nets={"1": "+5V"}, label="S7081-42R",
               pos=(-BC_FINGERS[0][0], BC_FINGERS[0][1], 90), mfr="Harwin", mpn="S7081-42R",
               desc="SMT spring finger, gold, 4 A, working height 2.0 mm: +5 V from the plate's floor pad", ds=HARWIN_DS),
    "J2": dict(sym="Conn_01x01", fp=FP_FINGER, value="S7081-42R GND", nets={"1": "GND"}, label="S7081-42R",
               pos=(-BC_FINGERS[1][0], BC_FINGERS[1][1], 90), mfr="Harwin", mpn="S7081-42R",
               desc="SMT spring finger, gold, 4 A, working height 2.0 mm: GND from the plate's floor pad", ds=HARWIN_DS),
    "J3": dict(sym="Conn_01x01", fp=FP_FINGER, value="S7081-42R VBAT", nets={"1": "+3V3"}, label="S7081-42R",
               pos=(-BC_VBAT_X * BC_CELL_X, COVER_Y_PAD, 0), mfr="Harwin", mpn="S7081-42R",
               desc="SMT spring finger, gold, 4 A, working height 2.0 mm: on the remote's VBAT (P1) contact plate",
               ds=HARWIN_DS),
    "J4": dict(sym="Conn_01x01", fp=FP_FINGER, value="S7081-42R GND", nets={"1": "GND"}, label="S7081-42R",
               pos=(BC_VBAT_X * BC_CELL_X, COVER_Y_PAD, 0), mfr="Harwin", mpn="S7081-42R",
               desc="SMT spring finger, gold, 4 A: on the remote's GND (P2) leaf spring", ds=HARWIN_DS),
    # 3.3 V for the remote (D-41): copper down in a recess in the cover; pin 1 IN, 2 GND, 3 EN, 4 NC, 5 OUT
    "U1": dict(sym="TLV75533PDBV", fp=FP_SOT, value="TLV75533PDBVR", label="TI TLV75533PDBVR",
               nets={"1": "+5V", "2": "GND", "3": "+5V", "5": "+3V3"}, pin_names={"4": "NC"},
               pos=(-BC_REG["U1"][0], BC_REG["U1"][1], 90),
               mfr="Texas Instruments", mpn="TLV75533PDBVR",
               desc="LDO 3.3 V 500 mA, 1.45-5.5 V in, SOT-23-5: the remote's supply from +5 V", ds=TLV_DS),
    "C3": dict(label="1uF", sym="C", fp=FP_C, value="1uF", nets={"1": "GND", "2": "+5V"},
               pos=(-BC_REG["C3"][0], BC_REG["C3"][1], 0), mfr="Samsung Electro-Mechanics", mpn="CL05A105KP5NNNC",
               desc="LDO input capacitor, 1 uF 10 V X5R 0402 (TLV755P: >= 1 uF)", ds=""),
    "C4": dict(label="1uF", sym="C", fp=FP_C, value="1uF", nets={"1": "GND", "2": "+3V3"},
               pos=(-BC_REG["C4"][0], BC_REG["C4"][1], 0), mfr="Samsung Electro-Mechanics", mpn="CL05A105KP5NNNC",
               desc="LDO output capacitor, 1 uF 10 V X5R 0402 (TLV755P: >= 1 uF)", ds=""),
}

def uid(*parts):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "smart-wallplate/sensor/" + "/".join(parts)))
