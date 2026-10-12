"""Parts, nets and geometry for the low-voltage boards (docs/DESIGN.md D-50, D-35).

Geometry comes from cad/build123d/params.py. All coordinates are room front view (x right, y up) unless a
board says otherwise.

Ring board: 1.6 mm FR4, two layers, round the insert's collar against the wall (pressed onto its crush ribs, D-68).
The MSR-2 on CN2 and three SMT spacers, J1 for the 5 V FFC from the wiring board, the SHT40, the top-port PDM
microphone and the ADAU7002 that turns its PDM into I2S on CN2 (D-83). Front copper keeps
RING_KEEP - RING_T (plan) from the box opening, back copper RING_KEEP: the sides carry front copper only.

Riser board: 0.8 mm FR4 on the two spacer posts from the wiring board's 5 V area; two SMT spring pins on top.

Back cover flex: see below.
"""
import sys
import uuid
from math import atan2, cos, degrees, radians, sin, sqrt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "cad" / "build123d"))
from params import (FINGER, FINGER_PAD, FLEX_T, MIC, MIC_PORT_IN, MIC_AT, MIC_PARTS, ADAU, BOX_W, BOX_H, RING_T, RING_KEEP, RING_HALF_W, RING_Y, RING_R, RING_INNER, RING_J1,
                    MSR_SPACERS, RING_NUT_HOLE, RING_NUT_PAD, RING_SMALL, SCREW_PITCH, BOSS_R, MSR_CN2_X, MSR_Y,
                    SHT_AT, RISER, RISER_C, POSTS, PIN_PAD_D, PIN_HOLE_D, PIN_FLANGE, MSR_SW_CUTS, RING_NOTCH_R,
                    BC_CELL_X, BC_CELL_Z, BC_VBAT_X, BC_FLEX_Z, BC_END_T, BC_END_H,
                    BC_FINGERS, BC_STRIP, BC_RUN, BC_RUN_JOG, BC_JOG, BC_COPPER_Y, BC_REG, BC_PCB_W, BC_PCB_CLR,
                    BC_BRIDGE_H, BC_LANE_H, BC_END_CORNER, BC_END_XO, BC_PAD_END, BC_PAD_LOW, BC_PAD_STIFF_T, BC_PAD_D, end_top)

LIB = "sensor"
REV = "v0.5"
REV_DATE = "2026-10-12"                                     # title blocks
RING, RISER_B, COVER = "ring_board", "riser_board", "cover_flex"

# ---- CN2 mate (D-82, D-89): Molex 55909-2474 SlimStack plug, 24 contacts, 2 rows, 0.4 mm, mating the MSR-2's CN2
# (assumed Molex 51338-2474, 1.5 mm mated). Land pattern from Molex SD-55909-003 rev J sheet 2 ("P.C.BOARD PATTERN
# DIMENSION (REFERENCE)"). The contact map and pin 1 (the drawing numbers no pins) wait for Apollo's pinout:
# CN2_CONFIRMED stays False.
CN2_CONFIRMED = False
CN2_PINS, CN2_PITCH = 24, 0.4                               # DATASHEET 2 x 12, pitch 0.4
CN2_PAD = (0.22, 0.9)                                       # DATASHEET signal pad w x l
CN2_ROW = (1.73 + CN2_PAD[1]) / 2                           # DATASHEET row centre off the centre line (rows 1.73 apart, inner edges)
CN2_NAIL = (0.5, 0.85)                                      # DATASHEET fitting nail pad w x l
CN2_NAIL_AT = ((CN2_PINS // 2 - 1) * CN2_PITCH / 2 + 0.8, (0.63 + CN2_NAIL[1]) / 2)   # DATASHEET 0.8 beyond the end pads; 0.63 apart
CN2_BODY = (6.8, 3.13, 1.14)                                # DATASHEET housing length, tail tip to tip, height
# Placeholder map, contact -> net. NOT the MSR-2's pinout (I2S in the ADAU7002's ball order: no crossings).
CN2_MAP = {"13": "+5V", "15": "GND", "17": "I2S_SD", "19": "I2S_WS", "21": "I2S_SCK",
           "18": "SCL", "20": "SDA", "22": "+3V3", "24": "GND"}

# silkscreen logos and the project URL on the boards with room for them (the riser and cover flex have none): footprint, (x, y), side, rotation; URL (x, y, side)
FP_ANT, FP_KICAD = "Ant_Logo_8mm_SilkScreen", "KiCad-Logo2_5mm_SilkScreen"
URL = "github.com/antevens/smart-wallplate"
BRAND = {"ring_board": ([(FP_ANT, (-27.6, 58.0), "F", 0), (FP_KICAD, (22.2, -44.0), "F", 0)], (-15.1, -47.7, "F")),
         "eu_cap_board": ([(FP_ANT, (-32.4, 58.9), "F", 0), (FP_KICAD, (25.9, -44.6), "F", 0)], (8.1, -38.3, "F"))}

FP_B2B = "Molex_SlimStack_55909-2474_2x12_P0.40mm_Vertical"
FP_FINGER = "Harwin_S7081-42R"
FP_SHT = "Sensirion_DFN-4_1.5x1.5mm_P0.8mm_SHT4x_NoCentralPad"
FP_C = "C_0402_1005Metric"
FP_C1206 = "C_1206_3216Metric"
C0G_DS = "https://pim.murata.com/asset/pim4/ceramicCapacitorSMD/GRM3195C1H104JA05-01A-EN_PDF_CERAMICCAPACITORSMD"
FP_R = "R_0402_1005Metric"
FP_SOT = "SOT-23-5"
FP_FH12 = "Hirose_FH12-6S-0.5SH_1x06-1MP_P0.50mm_Horizontal"
FP_NUT = "Wurth_WA-SMSI_M2_SMT_Spacer_L1.5mm"
FP_MIC = "Knowles_SPK0641HT4H-1_3x4mm"
FP_ADAU = "Analog_WLCSP-8_0.76x1.56mm_P0.4mm"
FP_PIN = "Harwin_P70-2200045"
FP_POST_PAD = "M2_Post_Pad_D3.8mm"
POST_PAD = (3.8, 2.2)                                       # riser pad under the M2 pan head (head 4.0), plated hole
FP_PIN_PAD = "Contact_Pad_D2.6mm"
TLV_DS = "https://www.ti.com/lit/ds/symlink/tlv755p.pdf"
HARWIN_DS = ("https://content.harwin.com/asset/8cd5d0a8-d578-46b3-8278-7289045a1613/"
             "DRG-02322-Technical-Drawing-Datasheet-S7081R-pdf.pdf")
SHT_DS = "https://sensirion.com/media/documents/33FD6951/624C4357/Datasheet_SHT4x.pdf"
MIC_DS = "https://www.knowles.com/docs/default-source/model-downloads/spk0641ht4h-1-rev-a.pdf"
ADAU_DS = "https://www.analog.com/media/en/technical-documentation/data-sheets/ADAU7002.pdf"
FH12_DS = "https://www.hirose.com/product/en/products/FH12/FH12-6S-0.5SH(55)/"
NUT_DS = "https://www.we-online.com/catalog/datasheet/9774015243R.pdf"
PIN_DS = ("https://content.harwin.com/asset/7e702b12-8f84-42b5-9282-d7e22f3466f3/"
          "DRG-02624-Technical-Drawing-Datasheet-P70-220-pdf.pdf")
# SPK0641HT4H-1 example land pattern (datasheet rev A p. 6), body frame, top view, +y towards the port end: signal pads
# 0.45 x 0.95 at x +-0.425, y +-0.675 (2 CLOCK, 3 SELECT at +y; 1 DATA, 4 VDD at -y); GND ring 0.325 wide: sides 6 (-x)
# and 8 (+x) 2.30 long, ends 7 (+y) and 5 (-y) 1.30 long, 0.40 from the signal pads (end pad height: 0.725 edge
# distance less the 0.40 gap; drawn to that on the drawing).
MIC_SIG = (0.45, 0.95, 0.425, 0.675)                        # signal pad w, h, centre x, y
MIC_SIG_PINS = {"2": (-1, 1), "3": (1, 1), "1": (-1, -1), "4": (1, -1)}
MIC_GND = (0.325, 2.30, 1.30)                               # ring width, side pad length, end pad length
MIC_GND_PINS = {"6": (-1, 0), "8": (1, 0), "7": (0, 1), "5": (0, -1)}
MIC_GND_AT = (1.375 - 0.325 / 2, 1.875 - 0.325 / 2)        # side pad x, end pad y (outer edges 2.75 x 3.75)
# ADAU7002 WLCSP CB-8-6 (datasheet rev C, top view, ball side down): rows A-D downwards, columns 1-2 rightwards, 0.4
# pitch. Land: the datasheet gives none; 0.20 mm NSMD as KiCad's ADI WLCSP 0.4 mm pitch footprints.
ADAU_PITCH, ADAU_PAD = 0.4, 0.20
ADAU_BALLS = {"A1": "PDM_DAT", "A2": "PDM_CLK", "B1": "SDATA", "B2": "BCLK", "C1": "GND", "C2": "LRCLK",
              "D1": "IOVDD", "D2": "CONFIG"}


def mic_parts(port):
    """The microphone and its parts round the port (room x, y) (D-83): MK1 SPK0641HT4H-1 (top port, PDM; SELECT low),
    U2 ADAU7002 (PDM to I2S, CONFIG high = I2S), C4 its 100 nF, R1 SD pull-down, C3 the mic's 100 nF (C0G:
    Knowles advises no Class 2 dielectrics near the mic)."""
    at = {k: ((port[0] + dx, port[1] + dy), d) for k, ((dx, dy), d) in MIC_PARTS.items()}

    def pos(ref):
        (x, y), (w, h, _) = at[ref]
        return x, y, (90 if h > w else 0)
    body_y = port[1] - (MIC[1] / 2 - MIC_PORT_IN)
    return {
        "MK1": dict(sym="SPK0641HT4H-1", fp=FP_MIC, value="SPK0641HT4H-1", label="",
                    nets={"1": "PDM_DAT", "2": "PDM_CLK", "3": "GND", "4": "+3V3", "5": "GND", "6": "GND", "7": "GND",
                          "8": "GND"}, pos=(port[0], body_y, 0), mfr="Knowles", mpn="SPK0641HT4H-1",
                    desc="PDM MEMS microphone, top port, 1.6-3.6 V; SELECT low", ds=MIC_DS),
        "U2": dict(sym="ADAU7002", fp=FP_ADAU, value="ADAU7002", label="",
                   nets={"A1": "PDM_DAT", "A2": "PDM_CLK", "B1": "I2S_SD", "B2": "I2S_SCK", "C1": "GND", "C2": "I2S_WS",
                         "D1": "+3V3", "D2": "+3V3"}, pos=(*at["U2"][0], 0), mfr="Analog Devices",
                   mpn="ADAU7002ACBZ-R7", desc="Stereo PDM to I2S converter, WLCSP-8 0.4 mm; CONFIG high = I2S",
                   ds=ADAU_DS),
        "C4": dict(label="100nF", sym="C", fp=FP_C, value="100nF", nets={"1": "+3V3", "2": "GND"}, pos=pos("C4"),
                   mfr="any", mpn="0402 X7R 100 nF 16 V", desc="ADAU7002 IOVDD decoupling", ds=""),
        "R1": dict(label="100k", sym="R", fp=FP_R, value="100k", nets={"1": "I2S_SD", "2": "GND"}, pos=pos("R1"),
                   mfr="any", mpn="0402 1% 100 kOhm", desc="I2S SD pull-down (ADAU7002 tristates SDATA)", ds=""),
        "C3": dict(label="100nF C0G", sym="C", fp=FP_C1206, value="100nF C0G", nets={"1": "+3V3", "2": "GND"},
                   pos=pos("C3"), mfr="Murata", mpn="GRM3195C1H104JA05D", desc="Microphone decoupling, C0G 50 V 1206",
                   ds=C0G_DS),
    }


def uid(*parts):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "smart-wallplate/sensor/" + "/".join(parts)))


def arc(c, r, a0, a1, step=5.0):
    """Points on a circle round c from a0 to a1 (degrees), both ends included."""
    n = max(2, int(abs(a1 - a0) / step) + 1)
    return [(c[0] + r * cos(radians(a0 + (a1 - a0) * i / n)), c[1] + r * sin(radians(a0 + (a1 - a0) * i / n)))
            for i in range(n + 1)]


def rounded_rect(cx, cy, w, h, r, step=7.5):
    """Closed polyline of a rounded rectangle, counter-clockwise from the right edge."""
    x0, x1, y0, y1 = cx - w / 2 + r, cx + w / 2 - r, cy - h / 2 + r, cy + h / 2 - r
    return (arc((x1, y1), r, 0, 90, step)[:-1] + arc((x0, y1), r, 90, 180, step)[:-1]
            + arc((x0, y0), r, 180, 270, step)[:-1] + arc((x1, y0), r, 270, 360, step)[:-1])


# ============================== ring board ==============================
RING_OUTER = [(RING_HALF_W, RING_Y[0]), (RING_HALF_W, RING_Y[1])]
for _x0, _x1, _y0 in sorted(MSR_SW_CUTS, reverse=True):     # notches under the MSR-2's back switches, right to left
    RING_OUTER += [(_x1, RING_Y[1]), (_x1, _y0), (_x0, _y0), (_x0, RING_Y[1])]
RING_OUTER += [(-RING_HALF_W, RING_Y[1]), (-RING_HALF_W, RING_Y[0])]
RING_OUTER_R = [RING_R, RING_R] + [RING_NOTCH_R] * 4 * len(MSR_SW_CUTS) + [RING_R, RING_R]


def _window():
    """Inner cut-out: the seal band's window plus a notch round each screw boss (closed, counter-clockwise)."""
    w, h, r = RING_INNER
    br, by = BOSS_R + 0.3, SCREW_PITCH / 2
    xt = sqrt(br * br - (by - h / 2) ** 2)                  # notch meets the window's top / bottom edge
    a = degrees(atan2(h / 2 - by, xt))                      # angle of that point from the boss centre (< 0)
    x0, x1, y0, y1 = -w / 2 + r, w / 2 - r, -h / 2 + r, h / 2 - r
    pts = arc((x1, y1), r, 0, 90)[:-1]
    pts += arc((0, by), br, a, 180 - a)[:-1]                 # top notch, right to left over the top
    pts += arc((x0, y1), r, 90, 180)[:-1] + arc((x0, y0), r, 180, 270)[:-1]
    pts += arc((0, -by), br, 180 + a, 360 - a)[:-1]          # bottom notch, left to right under the bottom
    pts += arc((x1, y0), r, 270, 360)[:-1]
    return pts


RING_WINDOW = _window()
K_FRONT, K_BACK = RING_KEEP - RING_T, RING_KEEP
KEEP_FRONT = rounded_rect(0, 0, BOX_W + 2 * K_FRONT, BOX_H + 2 * K_FRONT, K_FRONT)
KEEP_BACK = rounded_rect(0, 0, BOX_W + 2 * K_BACK, BOX_H + 2 * K_BACK, K_BACK)
RAIL_W, RAIL_PITCH = 0.15, 0.33                             # right rail lanes (front copper)
RAIL_X = tuple(BOX_W / 2 + K_FRONT + 0.2 + i * RAIL_PITCH for i in range(3))   # inner to outer
FH12_NETS = {"1": "GND", "2": "+5V", "3": "GND", "4": "GND", "5": "+5V", "6": "GND"}   # mirror-symmetric (D-50)


def _small(ref):
    (x, y), (w, h, _) = RING_SMALL[ref]
    return x, y, (90 if h > w else 0)


RING_PARTS = {
    "J1": dict(label="Hirose FH12-6S", sym="Conn_01x06", fp=FP_FH12, value="5V in (FFC)", nets=FH12_NETS,
               pos=(*RING_J1, 0), mfr="Hirose", mpn="FH12-6S-0.5SH(55)",
               desc="FPC connector 0.5 mm, 6 contacts, slide lock: 5 V from the wiring board's J2 (D-50)", ds=FH12_DS),
    "C1": dict(label="22uF 16V X5R 1206", sym="C", fp=FP_C1206, value="22uF 16V X5R", nets={"1": "+5V", "2": "GND"},
               pos=(*RING_SMALL["C1"][0], 270), mfr="KEMET", mpn="C1206C226M4PACTU",
               desc="Ceramic 22 uF 16 V X5R 1206 at J1, 1.8 mm max", ds="https://yageogroup.com/content/datasheet/asset/file/KEM_C1006_X5R_SMD"),
    "J2": dict(sym="Conn_02x12_Odd_Even", fp=FP_B2B, value="55909-2474", label="Molex 55909-2474",
               nets=dict(CN2_MAP), pos=(MSR_CN2_X, MSR_Y, 0), mfr="Molex", mpn="55909-2474",
               desc="SlimStack plug 24 contacts, 0.4 mm, 2 rows, mating the MSR-2's CN2 (assumed Molex 51338-2474, "
                    "1.5 mm mated; land pattern and contact map placeholders, D-82)",
               ds="https://www.molex.com/en-us/products/part-detail/559092474"),
    "U1": dict(label="Sensirion SHT40", sym="SHT4x", fp=FP_SHT, value="SHT40",
               nets={"1": "SDA", "2": "SCL", "3": "+3V3", "4": "GND"}, pos=(*SHT_AT, 0), mfr="Sensirion",
               mpn="SHT40-AD1B-R2", desc="Humidity and temperature sensor, I2C 0x44", ds=SHT_DS),
    "C2": dict(label="100nF", sym="C", fp=FP_C, value="100nF", nets={"1": "+3V3", "2": "GND"}, pos=_small("C2"),
               mfr="any", mpn="0402 X7R 100 nF 16 V", desc="SHT40 decoupling", ds=""),
    **mic_parts(MIC_AT),
}
for i, (x, y) in enumerate(MSR_SPACERS):
    RING_PARTS[f"H{i + 1}"] = dict(sym="Conn_01x01", fp=FP_NUT, value="spacer 1.5", label="Wurth WA-SMSI M2 L1.5",
                                   nets={"1": "GND"}, pos=(x, y, 0), mfr="Wurth Elektronik", mpn="9774015243R",
                                   desc="SMT steel spacer M2, 1.5 mm, tin: the MSR-2's board rests on it under the face "
                                        "plate's posts (D-68)", ds=NUT_DS)

# ============================== riser board ==============================
# Riser frame = room front view (x, y).
RISER_PARTS = {
    "P1": dict(sym="Conn_01x01", fp=FP_POST_PAD, value="+5V post", nets={"1": "+5V"}, pos=(*POSTS[0], 0),
               in_bom=False, desc="M2 screw onto the +5V spacer post (wiring board P1)"),
    "P2": dict(sym="Conn_01x01", fp=FP_POST_PAD, value="GND post", nets={"1": "GND"}, pos=(*POSTS[1], 0),
               in_bom=False, desc="M2 screw onto the GND spacer post (wiring board P2)"),
    "J1": dict(sym="Conn_01x01", fp=FP_PIN, value="+5V pin", nets={"1": "+5V"}, pos=(*BC_FINGERS[0], 0),
               label="", mfr="Harwin", mpn="P70-2200045",
               desc="SMT spring pin with peg, 2 A, gold: +5V onto the back cover's pad", ds=PIN_DS),
    "J2": dict(sym="Conn_01x01", fp=FP_PIN, value="GND pin", nets={"1": "GND"}, pos=(*BC_FINGERS[1], 0),
               label="", mfr="Harwin", mpn="P70-2200045",
               desc="SMT spring pin with peg, 2 A, gold: GND onto the back cover's pad", ds=PIN_DS),
}
RISER_RECT = (RISER_C[0], RISER_C[1], RISER[0], RISER[1])


# Replacement back cover flex (D-35, D-50, D-53): the regulator section, below it two gold pads (on the cover's ledge,
# copper down, behind windows in the cover's back, where the plate's spring pins press) -> run -> one 90 deg bend at
# the terminal end -> two S7081-42R on the cell axes against the remote's battery contacts. Single
# copper layer, copper outside the bend. Flat coordinates, seen from the copper side: X = -x (remote),
# Y = y on the ledge; on the end section a point h above the bend line maps to Y = y_copper - h.
COVER_CONFIRMED = False                                     # positions are REF / MEASURE (FCC photos)
COVER_TRACK = 0.3
_y_c = BC_COPPER_Y                                          # end section copper face (room y) = bend line
_yt = max(y for _, y in BC_FINGERS) + BC_PAD_D / 2 + BC_PAD_END   # pad section top = regulator section bottom
_yb = min(y for _, y in BC_FINGERS) - BC_PAD_D / 2 - BC_PAD_LOW   # pad section bottom, the run below it
_yr = _yt + BC_JOG                                          # regulator section top
_xs0, _xs1 = -BC_STRIP[1], -BC_STRIP[0]                     # pad section in flat X
_xr0, _xr1 = -BC_RUN[1], -BC_RUN[0]                         # run in flat X
_xo = BC_END_XO                                             # end section half width (inside the cover's slots)
_xi = BC_PCB_W / 2 + BC_PCB_CLR                             # notch round the remote's PCB strip
_c = BC_END_CORNER
COVER_Y_BAND = _y_c - BC_BRIDGE_H                           # band under the PCB strip
COVER_Y_END = _y_c - BC_END_H
COVER_Y_PAD = _y_c - (BC_CELL_Z - BC_FLEX_Z)                # contact fingers on the cell axes
COVER_BEND_Y = _y_c
_top = [(x, _y_c - (z - BC_FLEX_Z)) for x, z in end_top(_xo, _xi)]  # rounded to the cell above the rim
_yj = _yb + BC_RUN_JOG                                     # top of the jog from the pad section to the run (D-79)
COVER_OUTLINE = ([(_xs0, _yr), (_xs1, _yr), (_xs1, _yj), (_xr1, _yj)]
                 + [(_xr1, _y_c), (_xo - _c, _y_c), (_xo, _y_c - _c)]
                 + _top + [(_xi, COVER_Y_BAND), (-_xi, COVER_Y_BAND)] + [(-x, y) for x, y in reversed(_top)]
                 + [(-_xo, _y_c - _c), (-_xo + _c, _y_c), (_xr0, _y_c), (_xr0, _yb), (_xs0, _yb)])
COVER_STIFF = [((-_xo, COVER_Y_END), (_xo, _y_c))]          # FR4 BC_END_T behind the end section (non-copper side)
COVER_PAD_STIFF = [((_xs0, _yb), (_xs1, _yr))]                # FR4 BC_PAD_STIFF_T on the pad and regulator sections
COVER_LANES = (_xr1 - 0.75, _xr0 + 0.75)                    # +3V3 (inner), GND (outer) down the run
COVER_GND_X = _xs0 + 0.7                                    # GND lane up the pad section's outer edge to the regulator
COVER_PARTS = {
    "J1": dict(sym="TestPoint", fp=FP_PIN_PAD, value="+5V pin pad", nets={"1": "+5V"}, in_bom=False, label="+5V",
               pos=(-BC_FINGERS[0][0], BC_FINGERS[0][1], 0),
               desc="Gold pad under the plate's +5V spring pin (D-50, D-53)"),
    "J2": dict(sym="TestPoint", fp=FP_PIN_PAD, value="GND pin pad", nets={"1": "GND"}, in_bom=False, label="GND",
               pos=(-BC_FINGERS[1][0], BC_FINGERS[1][1], 0),
               desc="Gold pad under the plate's GND spring pin (D-50, D-53)"),
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
               pos=(-BC_REG["U1"][0], BC_REG["U1"][1], 0),
               mfr="Texas Instruments", mpn="TLV75533PDBVR",
               desc="LDO 3.3 V 500 mA, 1.45-5.5 V in, SOT-23-5: the remote's supply from +5 V", ds=TLV_DS),
    "C3": dict(label="1uF", sym="C", fp=FP_C, value="1uF", nets={"1": "GND", "2": "+5V"},
               pos=(-BC_REG["C3"][0], BC_REG["C3"][1], 0), mfr="Samsung Electro-Mechanics", mpn="CL05A105KO5NNNC",
               desc="LDO input capacitor, 1 uF 16 V X5R 0402 (TLV755P: >= 1 uF)", ds=""),
    "C4": dict(label="1uF", sym="C", fp=FP_C, value="1uF", nets={"1": "GND", "2": "+3V3"},
               pos=(-BC_REG["C4"][0], BC_REG["C4"][1], 0), mfr="Samsung Electro-Mechanics", mpn="CL05A105KO5NNNC",
               desc="LDO output capacitor, 1 uF 16 V X5R 0402 (TLV755P: >= 1 uF)", ds=""),
}
