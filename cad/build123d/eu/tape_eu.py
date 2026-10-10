"""EU tape points (3M 467MP, TAPE_T thick, docs/ASSEMBLY.md) as solids, for renders: the sensor flex on the trim
(the three slopes under their ramps, the pad section on its rib, the microphone stiffener, the SHT45 tail) and the
tongue in the floor insert's recess."""
from math import hypot
from build123d import Box, Cylinder, Pos
from params_eu import *
from sensor_flex import segment
import sensor_eu as se
import floor_eu

TAPE_T = 0.06                             # as cad/build123d/params.py
TAPE_IN = 0.4


def sheet(x0, x1, y0, y1, z):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, z) * Box(x1 - x0, y1 - y0, TAPE_T)


def along(a, b, w):
    """Tape on the skin side of a straight flex segment a -> b (centre line, FLEX_T thick), along y."""
    dy, dz = b[1] - a[1], b[2] - a[2]
    off = (FLEX_T + TAPE_T) / 2 * hypot(dy, dz) / abs(dy)
    return segment((a[0], a[1], a[2] + off), (b[0], b[1], b[2] + off), w, TAPE_T)


def trim_side():
    r = se.ROUTE
    out = {}
    w = FLEX_W - 2 * TAPE_IN
    fold = FLEX_W / 2 + 0.8                     # clear of the fold at the top of the rise
    for name, (a, b), s0 in (("rise", (r[1], r[2]), fold), ("dip_down", (r[3], r[4]), 1.0),
                             ("dip_up", (r[5], r[6]), 1.0)):
        L = abs(b[1] - a[1])
        t0, t1 = s0 / L, 1.0 - 1.0 / L
        pa = tuple(a[i] + (b[i] - a[i]) * t0 for i in range(3))
        pb = tuple(a[i] + (b[i] - a[i]) * t1 for i in range(3))
        out[name] = along(pa, pb, w)
    (x0, x1), (y0, y1) = FLEX_PAD_SEC, se.PIN_Y
    z = FLEX_PIN_Z + FLEX_T + STIFF_T + TAPE_T / 2
    out["pad_section"] = sheet(x0 + TAPE_IN, x1 - TAPE_IN, y0 + TAPE_IN, y1 - TAPE_IN, z)
    z = FLEX_HI_Z + FLEX_T + STIFF_T + TAPE_T / 2
    mw, mh = MIC[0] + 1.0, MIC[1] + 1.0
    mic = sheet(MIC_X - mw / 2, MIC_X + mw / 2, MIC_Y - mh / 2, MIC_Y + mh / 2, z)
    out["mic"] = mic - Pos(*MIC_PORT, z) * Cylinder(MIC_GASKET_D / 2 + 0.2, 1.0)
    out["sht_tail"] = sheet(-2.5, 2.5, SHT_Y - FLEX_W / 2 + TAPE_IN, SHT_Y + FLEX_W / 2 - TAPE_IN,
                            se.Z_SHT - (FLEX_T + TAPE_T) / 2)
    return out


def floor_side():
    """The tongue's pad piece taped in the floor insert's top recess (the run, fold and neck lie under the floor)."""
    out = {}
    z = CAP_T + BC_FLOOR_T - FLEX_T - BC_RECESS_CLR - TAPE_T / 2
    for i, (x0, x1, y0, y1, n, kind) in enumerate(floor_eu.tongue_path()):
        if kind == "top" and min(x1 - x0, y1 - y0) > 2 * TAPE_IN + 0.5:
            out[f"floor_{i}"] = sheet(x0 + TAPE_IN, x1 - TAPE_IN, y0 + TAPE_IN, y1 - TAPE_IN, z)
    return out
