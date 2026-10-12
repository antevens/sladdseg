"""Reference assembly: barrier + face plate + models of every bought-in part.

Envelopes are simple boxes/stadiums sized from params.py - they are for
clearance checks only, NOT vendor models. The mains board uses the KiCad STEP
(build/na_mains_board.step, from pcb/na_mains_board) when present. Its F side faces the
plate, so KiCad +x = room +x and no flip is needed.

Run: python assembly_na.py  -> ../../build/assembly_na.step
"""
from pathlib import Path
from build123d import Box, Compound, Color, Pos, export_step, import_step
from params_na import *
import barrier_na
import face_plate_na
import bilresa
import standoff_na
import sensor_board_na
import jumper_na

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "build" / "na"
MB_STEP = ROOT / "build" / "na_mains_board.step"


def env(part, name, rgb):
    part.label, part.color = name, Color(*rgb)
    return part


def mains_board():
    """Mains board: KiCad STEP when built (`make pcb`), else parameter envelopes."""
    if MB_STEP.exists():
        board = import_step(str(MB_STEP))
        # KiCad exports in sheet coordinates: recentre on the board slab, back face at MB_BACK_Z
        slab = max(board.solids(), key=lambda q: q.bounding_box().size.X * q.bounding_box().size.Y).bounding_box()
        cx, cy = (slab.min.X + slab.max.X) / 2, (slab.min.Y + slab.max.Y) / 2
        return env(Pos(-cx, MB_Y - cy, MB_BACK_Z - slab.min.Z) * board, "mains_board", (0.12, 0.42, 0.23))
    parts = [Pos(0, MB_Y, MB_FRONT_Z - MB[2] / 2) * Box(*MB),
             Pos(IRM_C[0], MB_Y + IRM_C[1], MB_BACK_Z - IRM[2] / 2) * Box(*IRM),
             Pos(WAGO_X, MB_Y + WAGO_Y, MB_BACK_Z - WAGO6[2] / 2) * Box(*WAGO6),
             Pos(J2_POS[0], MB_Y + J2_POS[1], MB_FRONT_Z + 3) * Box(10, 8, 6)]
    return env(Compound(parts), "mains_board_envelope", (0.12, 0.42, 0.23))


def build_assembly():
    ins = env(barrier_na.build(), "barrier_V0", (0.85, 0.3, 0.25))
    tr = env(face_plate_na.build(), "face_plate", (0.95, 0.95, 0.95))
    remote = env(bilresa.build(SEAT_Z), "bilresa_model", (0.98, 0.98, 0.96))
    sw_top = Pos(0, SW_Y, WELL_FLOOR_Z + SW_ROCKER_H / 2) * Box(SW_BEZEL[0], SW_BEZEL[1], SW_ROCKER_H)
    sw_body = Pos(0, SW_Y, WELL_FLOOR_Z - SW_BODY[2] / 2) * Box(*SW_BODY)
    switch = env(Compound([sw_top, sw_body]), "marquardt_1802_envelope", (0.7, 0.13, 0.13))
    rp = sensor_board_na.parts()
    msr = env(rp["msr"], "msr2_envelope", (0.2, 0.2, 0.2))
    rb = env(rp["sensor_board"], "sensor_board", (0.12, 0.42, 0.23))
    small = env(rp["cn2"] + rp["j1"] + rp["sht45"] + rp["passives"] + rp["mic"] + rp["spacers"], "sensor_board_parts",
                (0.8, 0.7, 0.3))
    pins = env(rp["pin_board"] + rp["pins"] + rp["posts"] + rp["screws"], "pin_board_pins_posts", (0.8, 0.7, 0.3))
    lead5 = env(jumper_na.build()["jumper"], "ffc_5v", (0.85, 0.85, 0.85))
    box = Pos(0, 0, -BOX_D / 2) * (Box(BOX_W + 3, BOX_H + 3, BOX_D) - Pos(0, 0, 1.5) * Box(BOX_W, BOX_H, BOX_D))
    box = env(box, "device_box_ref", (0.55, 0.6, 0.65))
    posts = env(standoff_na.placed(), "board_standoffs", (0.95, 0.95, 0.9))
    rest = [] if MB_STEP.exists() else [switch]          # the board STEP carries the rocker model
    return Compound(label="wallplate_assembly", children=[ins, tr, remote, *rest, posts, mains_board(), msr, rb,
                                                           small, pins, lead5, box])


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    export_step(build_assembly(), str(OUT / "assembly.step"))
    print("wrote assembly_na.step", "(KiCad mains board STEP)" if MB_STEP.exists() else "(mains board envelope)")
