"""5 V FLEX JUMPER (D-31, D-47, R9, R10): wiring board J2 -> pass-through -> pad end on the corner shelf.

A single-layer flex carries 5 V, so nothing is wired or soldered at assembly. The
connector end (stiffened) latches into J2, a Hirose FH12-6S slide-lock FPC connector on the board's
front face. The run goes up the gap between board and insert at x = JUMPER_X with a Z-folded
service loop (JUMPER_SERVICE of spare length, so it can be plugged in with the board held beside the
insert), up the pass-through's vertical leg, along the bottom of its 45 deg leg (exits the flange's
top-right corner) and onto the corner shelf, where its pad end (flex on an FR4 stiffener) carries the gold
pads the face plate's spring fingers press on (D-49: the battery-free tongue is on the sensor flex).
"""
from build123d import Box, Pos
from params import *
from common import ribbon


def entry():
    """Where the jumper leaves J2 (the connector is turned so the flex enters from +y)."""
    return jumper_path()[0]


def path():
    return jumper_path()


def end():
    """Stiffened connector end, in J2."""
    x, y, z = entry()
    return Pos(x, y - JUMPER_END[1] / 2, z) * Box(JUMPER_END[0], JUMPER_END[1], JUMPER_END[2])


def length():
    return jumper_length()


def build():
    return {"jumper": ribbon(path(), JUMPER_W, JUMPER_T) + end()}
