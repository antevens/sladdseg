"""EU cap board (D-56, D-59, D-70): parts and outline for gen_sensor.py.

FR4 1.6 mm in the cap's printed carrier, round the remote pocket. TP1 / TP2 on its underside take GND / +5V from the
5 V board's sensor spring pins; as on the NA ring board, J2 mates the MSR-2's CN2 (the MSR-2 rests on CN2 and the three
SMT spacers H5-H7), MK1 the top-port microphone with U2, the ADAU7002, beside it (D-83), U1 the SHT45 under its vents. Windows at the
corners let the face plate's snap fingers pass to the cap's edge; notches in the top edge clear the MSR-2's back
switches. Coordinates: room front view (x, y) in mm, from cad/build123d/eu/params_eu.py.
"""
import sys
from math import cos, radians, sin
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "cad" / "build123d" / "eu"))
sys.path.insert(0, str(ROOT / "cad" / "build123d"))
import params_eu as E                                         # noqa: E402
import sensor_parts as sp                                     # noqa: E402

CAPBOARD = "eu_cap_board"
CN2_CONFIRMED = sp.CN2_CONFIRMED
FP_HOLE = "MountingHole_2.2mm_M2"
FP_PAD = "Contact_Pad_D2.4mm"


def _arc(c, r, a0, a1, step=7.5):
    n = max(2, int(abs(a1 - a0) / step) + 1)
    return [(c[0] + r * cos(radians(a0 + (a1 - a0) * i / (n - 1))), c[1] + r * sin(radians(a0 + (a1 - a0) * i / (n - 1))))
            for i in range(n)]


def stadium(w, h):
    """Closed stadium polyline, straight sides along y, counter-clockwise."""
    r = w / 2
    yc = h / 2 - r
    return _arc((0, yc), r, 0, 180)[:-1] + _arc((0, -yc), r, 180, 360)[:-1]


CB_W, CB_H = E.PW - 2 * (E.SKIN + E.CB_INSET), E.PH - 2 * (E.SKIN + E.CB_INSET)
CB_R = E.PR - E.SKIN - E.CB_INSET
_x0, _x1 = E.PC[0] - CB_W / 2, E.PC[0] + CB_W / 2
_y0, _y1 = E.PC[1] - CB_H / 2, E.PC[1] + CB_H / 2
assert abs(_y1 - E.CB_TOP_Y) < 1e-6
CB_OUTER = [(_x1, _y0), (_x1, _y1)]
for _a, _b, _c in sorted(E.EU_SW_CUTS, reverse=True):          # notches under the MSR-2's back switches, right to left
    CB_OUTER += [(_b, _y1), (_b, _c), (_a, _c), (_a, _y1)]
CB_OUTER += [(_x0, _y1), (_x0, _y0)]
CB_OUTER_R = [CB_R, CB_R] + [sp.RING_NOTCH_R] * 4 * len(E.EU_SW_CUTS) + [CB_R, CB_R]
CB_POCKET = stadium(E.POCKET_OUT[0] + 2 * E.CB_POCKET_CLR, E.POCKET_OUT[1] + 2 * E.CB_POCKET_CLR)


def snap_windows():
    """Closed windows round the face plate's snap fingers, the bumps passing through (as capboard_eu.cap_board, D-77),
    closed polylines."""
    out = []
    r0, r1 = E.SNAP_WIN_R, E.SNAP_WALL_R + E.SNAP[2]
    for a, w in E.SNAPS:
        r = (r0 + r1) / 2
        c, s = cos(radians(a)), sin(radians(a))
        hw, ht = (w + 2 * E.SNAP_CLR) / 2, (r1 - r0) / 2
        pts = []
        for dr, dt in ((ht, -hw), (ht, hw), (-ht, hw), (-ht, -hw)):
            pts.append((c * (r + dr) - s * dt, s * (r + dr) + c * dt))
        out.append(pts)
    return out


CB_SNAP_WINDOWS = snap_windows()

CAPBOARD_PARTS = {
    "TP1": dict(sym="TestPoint", fp=FP_PAD, value="GND pin pad", nets={"1": "GND"}, in_bom=False, label="GND",
                pos=(*E.PINS[0], 0), side="B", desc="Under the 5 V board's GND sensor spring pin (P1)"),
    "TP2": dict(sym="TestPoint", fp=FP_PAD, value="+5V pin pad", nets={"1": "+5V"}, in_bom=False, label="+5V",
                pos=(*E.PINS[1], 0), side="B", desc="Under the 5 V board's +5V sensor spring pin (P2)"),
    "C1": dict(label="22uF 10V X5R 1206", sym="C", fp=sp.FP_C1206, value="22uF 10V X5R", nets={"1": "+5V", "2": "GND"},
               pos=(31.0, -2.0, 90), mfr="Samsung Electro-Mechanics", mpn="CL31A226KPHNNNE",
               desc="Ceramic 22 uF 10 V X5R 1206 at the pin pads", ds="https://www.samsungsem.com"),
    "J2": dict(sym="Conn_02x12_Odd_Even", fp=sp.FP_B2B, value="55909-2474", label="Molex 55909-2474",
               nets=dict(sp.CN2_MAP), pos=(E.MSR_CN2_X, E.MSR_Y, 0), mfr="Molex", mpn="55909-2474",
               desc="SlimStack plug 24 contacts, 0.4 mm, 2 rows, mating the MSR-2's CN2 (assumed Molex 51338-2474, "
                    "1.5 mm mated; land pattern and contact map placeholders, D-82)",
               ds="https://www.molex.com/en-us/products/part-detail/559092474"),
    **sp.mic_parts(E.MIC_AT),
    "U1": dict(label="Sensirion SHT45", sym="SHT4x", fp=sp.FP_SHT, value="SHT45",
               nets={"1": "SDA", "2": "SCL", "3": "+3V3", "4": "GND"}, pos=(0.0, E.SHT_Y, 0), mfr="Sensirion",
               mpn="SHT45-AD1B-R2", desc="Humidity and temperature sensor, I2C 0x44", ds=sp.SHT_DS),
    "C2": dict(label="100nF", sym="C", fp=sp.FP_C, value="100nF", nets={"1": "+3V3", "2": "GND"},
               pos=(2.6, E.SHT_Y, 90), mfr="any", mpn="0402 X7R 100 nF 16 V", desc="SHT45 decoupling", ds=""),
}
for _i, (_x, _y) in enumerate(E.CB_SCREWS):
    CAPBOARD_PARTS[f"H{_i + 1}"] = dict(sym="MountingHole", fp=FP_HOLE, value="M2", nets={}, pos=(_x, _y, 0),
                                        in_bom=False, label="", desc="M2 screw into the carrier")
for _i, (_x, _y) in enumerate(E.MSR_SPACERS):
    CAPBOARD_PARTS[f"H{len(E.CB_SCREWS) + _i + 1}"] = dict(
        sym="Conn_01x01", fp=sp.FP_NUT, value="spacer 1.5", label="Wurth WA-SMSI M2 L1.5", nets={"1": "GND"},
        pos=(_x, _y, 0), mfr="Wurth Elektronik", mpn="9774015243R",
        desc="SMT steel spacer M2, 1.5 mm, tin: the MSR-2's board rests on it under the face plate's posts (D-70)",
        ds=sp.NUT_DS)
