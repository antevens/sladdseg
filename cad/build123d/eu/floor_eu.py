"""EU pocket-floor insert (D-35, D-41): printed floor in the remote pocket, on the cap, bonded to the trim
(face plate side, lifts off with it). Openings over the switch cup and round the trim's screw
tabs; the sensor-flex tongue comes in under the right pocket wall between the spring pins, runs under the
floor, folds 45 deg there (copper up), rises through a slot onto the top (a notch from the slot to the edge lets
it in sideways) and carries the two gold pads, flush, under the replacement back cover's spring fingers (+5V,
GND). Only the pads show when the remote is out (D-49). Geometry in backcover.py.
"""
from build123d import Pos
from params_eu import *
import backcover


def cutouts():
    tabs = [(sx * (POCKET_IN[0] / 2 - TRIM_TAB[0] / 2), TRIM_SCREW_Y, TRIM_TAB[0], TRIM_TAB[1]) for sx in (-1, 1)]
    return [(0.0, SW_Y, CUP_IN[0], CUP_IN[1])] + tabs


def pads():
    """(x0, x1, y0, y1) of the floor pads: +5V, GND."""
    return [(*EU_PAD_X, y - BC_FLOOR_PAD[1] / 2, y + BC_FLOOR_PAD[1] / 2) for _, y in BC_FINGERS]


def tongue_path():
    """The tongue on the floor (x0, x1, y0, y1, layers, kind): the run from the wall (copper down) and the 45 deg
    fold under the floor (a channel in its underside), the neck above the fold up to the slot, the slot (it rises
    onto the top), the pad piece on the top (copper up, pads flush): the strip up past the +5V pad and, beside the
    neck (the flex slit between them), the part down past the GND pad (D-49)."""
    wall_x = POCKET_IN[0] / 2 + POCKET_WALL
    h = EU_TONGUE_W / 2
    f0, f1 = EU_FOLD_X - h, EU_FOLD_X + h
    y_top = max(y for _, y in BC_FINGERS) + BC_FLOOR_PAD[1] / 2 + 0.5
    y_bot = min(y for _, y in BC_FINGERS) - BC_FLOOR_PAD[1] / 2 - 1.0
    r0, r1 = EU_RISE
    run = (f1, wall_x, EU_TONGUE_Y - h, EU_TONGUE_Y + h, 1, "under")
    fold = (f0, f1, EU_TONGUE_Y - h, EU_TONGUE_Y + h, 2, "under")
    neck = (f0, f1, EU_TONGUE_Y + h, r0, 1, "under")
    rise = (f0, f1, r0, r1, 1, "slot")
    up = (EU_STRIP_X0, f1, r1, y_top, 1, "top")
    side = (EU_STRIP_X0, EU_SLIT_X[0], y_bot, r1, 1, "top")
    return [run, fold, neck, rise, up, side]


def notches():
    """From the slot to the floor's right edge (the tongue goes in sideways)."""
    h = EU_TONGUE_W / 2
    return [(EU_FOLD_X + h + 0.1, POCKET_IN[0], *EU_RISE)]


def parts():
    p = backcover.floor_insert(POCKET_IN, POCKET_IN[0] / 2 + POCKET_WALL, cutouts(), tongue_path(), pads(),
                               notches=notches())
    return {k: Pos(0, 0, CAP_T) * v for k, v in p.items()}
