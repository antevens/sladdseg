"""NA sensor board and pin board (docs/DESIGN.md D-50, D-68): parts, nets and outlines for pcb/shared/tools/gen_lv.py.

Sensor board: 1.6 mm FR4, two layers, round the barrier's collar against the wall (pressed onto its crush ribs, D-68).
The MSR-2 on CN2 and three SMT spacers, J1 for the 5 V FFC from the mains board, the SHT40, the top-port PDM microphone
and the ADAU7002 that turns its PDM into I2S on CN2 (D-83). Front copper keeps SB_KEEP - SB_T (plan) from the box
opening, back copper SB_KEEP: the sides carry front copper only.

Pin board: 0.8 mm FR4 on the two spacer posts from the mains board's 5 V area; two SMT spring pins on top.

Geometry from cad/build123d/na/params_na.py; room front view (x right, y up).
"""
import sys
from math import atan2, degrees, sqrt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "cad" / "build123d" / "na"))
sys.path.insert(1, str(ROOT / "pcb" / "shared" / "tools"))
from lv_parts import *                                                                     # noqa: E402,F401,F403
from params_na import (BOX_W, BOX_H, SB_T, SB_KEEP, SB_HALF_W, SB_Y, SB_R, SB_INNER, SB_J1, MIC_AT,  # noqa: E402
                       MSR_SPACERS, SB_SMALL, SCREW_PITCH, BOSS_R, MSR_CN2_X, MSR_Y, SHT_AT, PB, PB_C, POSTS, MSR_SW_CUTS)

SB_BOARD, PB_BOARD = "na_sensor_board", "na_pin_board"
# silkscreen logos and the project URL (the pin board has no room): footprint, (x, y), side, rotation; URL (x, y, side)
BRAND = {SB_BOARD: ([(FP_ANT, (-28.0, -48.5), "F", 0), (FP_KICAD, (26.4, -49.6), "F", 0)], (-13.0, -47.7, "F"))}


# ============================== sensor board ==============================
SB_OUTER = [(SB_HALF_W, SB_Y[0]), (SB_HALF_W, SB_Y[1])]
for _x0, _x1, _y0 in sorted(MSR_SW_CUTS, reverse=True):     # notches under the MSR-2's back switches, right to left
    SB_OUTER += [(_x1, SB_Y[1]), (_x1, _y0), (_x0, _y0), (_x0, SB_Y[1])]
SB_OUTER += [(-SB_HALF_W, SB_Y[1]), (-SB_HALF_W, SB_Y[0])]
SB_OUTER_R = [SB_R, SB_R] + [SB_NOTCH_R] * 4 * len(MSR_SW_CUTS) + [SB_R, SB_R]


def _window():
    """Inner cut-out: the seal band's window plus a notch round each screw boss (closed, counter-clockwise)."""
    w, h, r = SB_INNER
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


SB_WINDOW = _window()
K_FRONT, K_BACK = SB_KEEP - SB_T, SB_KEEP
KEEP_FRONT = rounded_rect(0, 0, BOX_W + 2 * K_FRONT, BOX_H + 2 * K_FRONT, K_FRONT)
KEEP_BACK = rounded_rect(0, 0, BOX_W + 2 * K_BACK, BOX_H + 2 * K_BACK, K_BACK)
RAIL_W, RAIL_PITCH = 0.15, 0.33                             # right rail lanes (front copper)
RAIL_X = tuple(BOX_W / 2 + K_FRONT + 0.2 + i * RAIL_PITCH for i in range(3))   # inner to outer
FH12_NETS = {"1": "GND", "2": "+5V", "3": "GND", "4": "GND", "5": "+5V", "6": "GND"}   # mirror-symmetric (D-50)


def _small(ref):
    (x, y), (w, h, _) = SB_SMALL[ref]
    return x, y, (90 if h > w else 0)


SB_PARTS = {
    "J1": dict(label="Hirose FH12-6S", sym="Conn_01x06", fp=FP_FH12, value="5V in (FFC)", nets=FH12_NETS,
               pos=(*SB_J1, 180), mfr="Hirose", mpn="FH12-6S-0.5SH(55)",
               desc="FPC connector 0.5 mm, 6 contacts, slide lock: 5 V from the mains board's J2 (D-50)", ds=FH12_DS),
    "C1": dict(label="22uF 16V X5R 1206", sym="C", fp=FP_C1206, value="22uF 16V X5R", nets={"1": "+5V", "2": "GND"},
               pos=(*SB_SMALL["C1"][0], 180), mfr="KEMET", mpn="C1206C226M4PACTU",
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
    SB_PARTS[f"H{i + 1}"] = dict(sym="Conn_01x01", fp=FP_NUT, value="spacer 1.5", label="Wurth WA-SMSI M2 L1.5",
                                   nets={"1": "GND"}, pos=(x, y, 0), mfr="Wurth Elektronik", mpn="9774015243R",
                                   desc="SMT steel spacer M2, 1.5 mm, tin: the MSR-2's board rests on it under the face "
                                        "plate's posts (D-68)", ds=NUT_DS)

# ============================== pin board ==============================
# Pin board frame = room front view (x, y).
PB_PARTS = {
    "P1": dict(sym="Conn_01x01", fp=FP_POST_PAD, value="+5V post", nets={"1": "+5V"}, pos=(*POSTS[0], 0),
               in_bom=False, desc="M2 screw onto the +5V spacer post (mains board P1)"),
    "P2": dict(sym="Conn_01x01", fp=FP_POST_PAD, value="GND post", nets={"1": "GND"}, pos=(*POSTS[1], 0),
               in_bom=False, desc="M2 screw onto the GND spacer post (mains board P2)"),
    "J1": dict(sym="Conn_01x01", fp=FP_PIN, value="+5V pin", nets={"1": "+5V"}, pos=(*BC_FINGERS[0], 0),
               label="", mfr="Harwin", mpn="P70-2200045",
               desc="SMT spring pin with peg, 2 A, gold: +5V onto the back cover's pad", ds=PIN_DS),
    "J2": dict(sym="Conn_01x01", fp=FP_PIN, value="GND pin", nets={"1": "GND"}, pos=(*BC_FINGERS[1], 0),
               label="", mfr="Harwin", mpn="P70-2200045",
               desc="SMT spring pin with peg, 2 A, gold: GND onto the back cover's pad", ds=PIN_DS),
}
PB_RECT = (PB_C[0], PB_C[1], PB[0], PB[1])
