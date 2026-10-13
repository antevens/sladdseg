"""5 V CABLE (D-50, R9, R10, D-134): mains board J2 -> slit in the barrier's bottom wall -> J1 on the sensor board.

A stock FFC (6 contacts, 0.5 mm pitch) latched in Hirose FH12-6S slide-lock connectors at both ends, so nothing
is wired or soldered at assembly. It stays in the plane x = FFC_SLOT_X: out of J2 downwards, a bend up, one straight
run through the slit, a bend over onto the sensor board into J1 (params_na.ffc_curve()).
"""
from build123d import Box, Pos
from params_na import *
from common import ribbon


def entry():
    """Where the jumper leaves J2 (cable out -y)."""
    return slot_path()[0]


def path():
    return slot_path()


def end():
    """Stiffened connector end, in J2."""
    x, y, z = entry()
    return Pos(x, y + JUMPER_END[1] / 2, z) * Box(JUMPER_END[0], JUMPER_END[1], JUMPER_END[2])


def length():
    return jumper_length()


def build():
    return {"jumper": ribbon(path(), JUMPER_W, JUMPER_T, wall=(0, 1, 0)) + end()}
