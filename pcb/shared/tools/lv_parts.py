"""Parts, nets and geometry shared by the low-voltage boards of both variants (docs/DESIGN.md D-50, D-35): the CN2
mate, the microphone and its parts, footprint names and datasheets, and the replacement back cover's flex (one board for
both variants). Each variant's sensor board and pin board: pcb/na/tools/lv_parts_na.py, pcb/eu/tools/lv_parts_eu.py.

Geometry comes from cad/build123d/params.py. All coordinates are room front view (x right, y up) unless a board says
otherwise.
"""
import sys
import uuid
from math import cos, pi, radians, sin
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "cad" / "build123d"))
sys.path.insert(1, str(ROOT / "pcb" / "tools"))
from common_parts import FP_ANT, FP_KICAD, URL                                            # noqa: E402,F401
from params import (FINGER, FINGER_PAD, FLEX_T, MIC, MIC_PORT_IN, MIC_PARTS, ADAU, MSR_NUT_HOLE, MSR_NUT_PAD,  # noqa: E402,F401
                    PIN_PAD_D, PIN_HOLE_D, PIN_FLANGE, SB_NOTCH_R,
                    BC_CELL_X, BC_CELL_Z, BC_VBAT_X, BC_FLEX_Z, BC_END_T, BC_END_H,
                    BC_FINGERS, BC_STRIP, BC_RUN, BC_RUN_JOG, BC_JOG, BC_COPPER_Y, BC_REG, BC_PCB_W, BC_PCB_CLR,
                    BC_BRIDGE_H, BC_LANE_H, BC_END_CORNER, BC_END_XO, BC_PAD_END, BC_PAD_LOW, BC_PAD_STIFF_T, BC_PAD_D, end_top,
                    BC_BEND_R, BC_BEND_CLR, BC_SLIT, BC_REG_RECESS, BC_PAD_CU)

LIB = "lv"
REV = "v0.6"
REV_DATE = "2026-10-12"                                     # title blocks
COVER = "cover_flex"

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


FP_B2B = "Molex_SlimStack_55909-2474_2x12_P0.40mm_Vertical"
FP_FINGER = "Harwin_S7081-42R"
FP_SHT = "Sensirion_DFN-4_1.5x1.5mm_P0.8mm_SHT4x_NoCentralPad"
FP_C = "C_0402_1005Metric"
FP_C0603 = "C_0603_1608Metric"
FP_TVS = "D_SOD-523_TI_DYA0002A"
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
POST_PAD = (3.8, 2.2)                                       # pin board pad under the M2 pan head (head 4.0), plated hole
FP_PIN_PAD = "Contact_Pad_D2.6mm"
TLV_DS = "https://www.ti.com/lit/ds/symlink/tlv755p.pdf"
TVS_DS = "https://www.ti.com/lit/ds/symlink/tpd1e10b06.pdf"
CAP0603_DS = "https://product.samsungsem.com/mlcc/CL10A105KO8NNN.do"
# TI TPD1E10B06 SOD-523 (DYA0002A) land pattern example (SLLSEB1G, Aug 2024): pads 0.4 x 0.67, 1.48 across
TVS_PAD, TVS_SPAN = (0.4, 0.67), 1.48
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


# Replacement back cover flex (D-35, D-50, D-53): the regulator section, below it two gold pads (on the cover's ledge,
# copper down, behind windows in the cover's back, where the plate's spring pins press) -> run -> one 90 deg bend at
# the terminal end -> two S7081-42R on the cell axes against the remote's battery contacts. Single
# copper layer, copper outside the bend. Flat coordinates, seen from the copper side: X = -x (remote),
# Y = y on the ledge; on the end section a point h above the bend line maps to Y = y_copper - h.
COVER_CONFIRMED = False                                     # positions are REF / MEASURE (FCC photos)
COVER_TRACK = 0.3
_y_c = BC_COPPER_Y                                          # end section copper face (room y)
_yt = max(y for _, y in BC_FINGERS) + BC_PAD_D / 2 + BC_PAD_END   # pad section top = regulator section bottom
_yb = min(y for _, y in BC_FINGERS) - BC_PAD_D / 2 - BC_PAD_LOW   # pad section bottom, the run below it
_yr = _yt + BC_JOG                                          # regulator section top
_xs0, _xs1 = -BC_STRIP[1], -BC_STRIP[0]                     # pad section in flat X
_xr0, _xr1 = -BC_RUN[1], -BC_RUN[0]                         # run in flat X
_xo = BC_END_XO                                             # end section half width (inside the cover's slots)
_xi = BC_PCB_W / 2 + BC_PCB_CLR                             # notch round the remote's PCB strip
_c = BC_END_CORNER
# the run's 90 deg bend (D-116): inside radius BC_BEND_R, the flex's mid-plane sets the developed length. The run
# leaves the ledge FLEX_T + BC_BEND_R short of the copper face and stands up from that height; the rest of the end
# section reaches down to the ledge beside it, cut free by a relief slit either side of the run.
_tr = FLEX_T + BC_BEND_R
_arc = pi / 2 * (BC_BEND_R + FLEX_T / 2)                     # bend zone's developed length


def flat_y(h):
    """Flat Y of the end section h above the flex plane (h >= 0; on the run only above the bend zone)."""
    return _y_c + 2 * _tr - _arc - h


COVER_BEND = (_y_c + _tr, _y_c + _tr - _arc)               # bend zone in flat Y: from the ledge, to the end section
_ys = flat_y(_tr + BC_SLIT[1])                              # relief slits' ends
_w = BC_SLIT[0]
COVER_Y_BAND = flat_y(BC_BRIDGE_H)                          # band under the PCB strip
COVER_Y_END = flat_y(BC_END_H)
COVER_Y_PAD = flat_y(BC_CELL_Z - BC_FLEX_Z)                 # contact fingers on the cell axes
COVER_LANE_Y = flat_y(BC_LANE_H)                            # +3V3 lane across the band
_top = [(x, flat_y(z - BC_FLEX_Z)) for x, z in end_top(_xo, _xi)]  # rounded to the cell above the rim
_yj = _yb + BC_RUN_JOG                                     # top of the jog from the pad section to the run (D-79)
_y0 = flat_y(0)                                             # the end section's lower edge (on the ledge)
_slit_r = 0.45 * _w                                         # full-round slit ends (fillet() caps a corner at 0.45 of a side)
COVER_OUTLINE = ([(_xs0, _yr), (_xs1, _yr), (_xs1, _yj), (_xr1, _yj), (_xr1, _ys), (_xr1 + _w, _ys), (_xr1 + _w, _y0),
                  (_xo - _c, _y0), (_xo, flat_y(_c))]
                 + _top + [(_xi, COVER_Y_BAND), (-_xi, COVER_Y_BAND)] + [(-x, y) for x, y in reversed(_top)]
                 + [(-_xo, flat_y(_c)), (-_xo + _c, _y0), (_xr0 - _w, _y0), (_xr0 - _w, _ys), (_xr0, _ys), (_xr0, _yb),
                    (_xs0, _yb)])
COVER_OUTLINE_R = [_slit_r if y == _ys else 0.76 for _, y in COVER_OUTLINE]   # inside corners >= 0.76 (tear stops)
# FR4 stiffeners (non-copper side). End section (BC_END_T): its outline, less a notch round the run and the slits up to
# BC_BEND_CLR past the bend zone. Pad and regulator sections (BC_PAD_STIFF_T): flush with their long edges (snap
# hooks), corners as the outline.
_yn = COVER_BEND[1] - BC_BEND_CLR
_xn0, _xn1 = _xr0 - _w - 0.2, _xr1 + _w + 0.2
COVER_STIFF = ([(-_xo, flat_y(_c)), (-_xo + _c, _y0), (_xn0, _y0), (_xn0, _yn), (_xn1, _yn), (_xn1, _y0),
                (_xo - _c, _y0), (_xo, flat_y(_c))]
               + _top + [(_xi, COVER_Y_BAND), (-_xi, COVER_Y_BAND)] + [(-x, y) for x, y in reversed(_top)])
COVER_PAD_STIFF = [(_xs0, _yr), (_xs1, _yr), (_xs1, _yb), (_xs0, _yb)]
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
    "C3": dict(label="1uF", sym="C", fp=FP_C0603, value="1uF 16V X5R 0603", nets={"1": "GND", "2": "+5V"},
               pos=(-BC_REG["C3"][0], BC_REG["C3"][1], 0), mfr="Samsung Electro-Mechanics", mpn="CL10A105KO8NNNC",
               desc="LDO input capacitor, 1 uF 16 V X5R 0603: 0.85 uF at 5 V (TLV755P: >= 0.47 uF effective, D-116)",
               ds=CAP0603_DS),
    "C4": dict(label="1uF", sym="C", fp=FP_C0603, value="1uF 16V X5R 0603", nets={"1": "GND", "2": "+3V3"},
               pos=(-BC_REG["C4"][0], BC_REG["C4"][1], 0), mfr="Samsung Electro-Mechanics", mpn="CL10A105KO8NNNC",
               desc="LDO output capacitor, 1 uF 16 V X5R 0603: 0.93 uF at 3.3 V (TLV755P: >= 0.47 uF effective, D-116)",
               ds=CAP0603_DS),
    "D1": dict(label="ESD", sym="D_TVS", fp=FP_TVS, value="TPD1E10B06DYAR", nets={"1": "GND", "2": "+5V"},
               pos=(-BC_REG["D1"][0], BC_REG["D1"][1], 0), mfr="Texas Instruments", mpn="TPD1E10B06DYAR",
               desc="ESD protection, bidirectional TVS, 5.5 V working, SOD-523: +5V at the exposed pin pads (D-116)",
               ds=TVS_DS),
}
