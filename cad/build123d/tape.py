"""Tape points (3M 467MP, TAPE_T thick, docs/ASSEMBLY.md) as solids, for renders: one sheet wherever a flex is
taped to a printed part, inset TAPE_IN from the flex's edges. Face plate (trim) side, insert side, back cover."""
from math import hypot
from build123d import Box, Cylinder, Pos
from params import *
import sensor_flex as sf
import backcover as bc

TAPE_IN = 0.4                             # tape inset from the flex's edges


def sheet(x0, x1, y0, y1, z):
    """Flat tape sheet centred on z."""
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, z) * Box(x1 - x0, y1 - y0, TAPE_T)


def along(a, b, w, side):
    """Tape on one face of a straight flex segment a -> b (centre line, SFLEX_T thick): side +1 above, -1 below."""
    dx, dy, dz = (b[i] - a[i] for i in range(3))
    run = hypot(dx, dy)
    off = side * (SFLEX_T + TAPE_T) / 2 * hypot(run, dz) / run
    return sf.segment((a[0], a[1], a[2] + off), (b[0], b[1], b[2] + off), w, TAPE_T)


def trim_side():
    """Sensor flex tape points, all on the face plate (trim)."""
    out = {}
    x1 = FLEX_X - FLEX_W / 2 - 0.3
    z1 = FLEX_Z_LO + (FLEX_Z_HI - FLEX_Z_LO) * (x1 - FLEX_EXIT_X) / (FLEX_X - FLEX_EXIT_X)
    out["rise"] = along((FLEX_EXIT_X + 0.5, MSR_Y, FLEX_Z_LO + 0.6 * (FLEX_Z_HI - FLEX_Z_LO) / (FLEX_X - FLEX_EXIT_X)),
                        (x1 - 0.5, MSR_Y, z1 - 0.5 * (FLEX_Z_HI - FLEX_Z_LO) / (FLEX_X - FLEX_EXIT_X)),
                        FLEX_W - 2 * TAPE_IN, +1)
    z_st = FLEX_HI_Z + SFLEX_T + STIFF_T + TAPE_T / 2
    y_pad = max(y for _, y in FINGERS) + FINGER_PAD[1] / 2 + 0.5
    out["fingers"] = sheet(FINGER_SEC_IN + TAPE_IN, FLEX_RIGHT - TAPE_IN, FINGER_SEC_Y[0] + TAPE_IN, y_pad - TAPE_IN, z_st)
    out["band"] = sheet(FLEX_RIGHT - FLEX_RUN_W + TAPE_IN, FLEX_RIGHT - TAPE_IN, -FLEX_Y_ON, FLEX_Y_ON,
                        FLEX_BAND_Z + SFLEX_T + TAPE_T / 2)
    w, h = MIC[0] + 1.0, MIC[1] + 1.0
    mic = sheet(MIC_X - w / 2, MIC_X + w / 2, MIC_Y - h / 2, MIC_Y + h / 2, z_st)
    out["mic"] = mic - Pos(*MIC_PORT, z_st) * Cylinder(MIC_GASKET_D / 2 + 0.2, 1.0)
    z_run = FLEX_HI_Z + SFLEX_T + TAPE_T / 2
    y0, y1 = SHT_Y - FLEX_RUN_W / 2 + TAPE_IN, SHT_Y + FLEX_RUN_W / 2 - TAPE_IN
    out["bottom"] = sheet(SHT_ENTRY + 2.0, FLEX_BAND_X - FLEX_RUN_W, y0, y1, z_run)
    out["sht_tail"] = sheet(-SHT_PADDLE + 0.5, SHT_PADDLE - 0.5, SHT_Y - FLEX_W / 2 + TAPE_IN, SHT_Y + FLEX_W / 2 - TAPE_IN,
                            FLEX_Z_SHT - (SFLEX_T + TAPE_T) / 2)
    return out


def insert_side():
    """5 V jumper's pad end on the corner shelf (the only flex on the insert, D-49)."""
    out = {}
    (x0, x1), (y0, y1) = TARGET_X, TARGET_Y
    out["pad_end"] = sheet(x0 + TAPE_IN, x1 - TAPE_IN, y0 + TAPE_IN, y1 - TAPE_IN, SHELF_TOP_Z)
    return out


def cover_side():
    """Back cover: no tape (snap hooks hold the pad and regulator sections and the end section)."""
    return {}
