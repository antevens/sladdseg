"""5 V CABLE (D-50, R9, R10): wiring board J2 -> pass-through -> J1 on the ring board.

A stock FFC (6 contacts, 0.5 mm pitch) latched in Hirose FH12-6S slide-lock connectors at both ends, so nothing
is wired or soldered at assembly. It leaves J2 to the right, runs up past the spacer posts at JUMPER_SIDE_X, between the
rocker and the top-right standoff to the straight bore's mouth on the insert's underside, through the bore and the slot
(D-74) and out of the flange onto the ring board,
where the stock cable's spare lies folded flat in four layers beside J1 (D-68).
"""
from build123d import Box, Pos
from params import *
from common import ribbon


def entry():
    """Where the jumper leaves J2 (the connector is turned so the flex enters from +x)."""
    return jumper_path()[0]


def path():
    return jumper_path()


def end():
    """Stiffened connector end, in J2."""
    x, y, z = entry()
    return Pos(x - JUMPER_END[1] / 2, y, z) * Box(JUMPER_END[1], JUMPER_END[0], JUMPER_END[2])


def length():
    return jumper_length()


def build():
    return {"jumper": ribbon(path(), JUMPER_W, JUMPER_T) + end()}
