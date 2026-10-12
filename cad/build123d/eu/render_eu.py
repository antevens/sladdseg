"""EU variant renders (D-30): xvfb-run python render_eu.py -> docs/renders/eu_*.png"""
from build123d import Box, Cylinder, Pos, Rot
from params_eu import *
import render
import barrier_eu
import face_plate_eu
import boards_eu
import sensor_board_eu

render.COL.update({"switch": "#b23a32", "magnet": "#4a4a4a", "box": "#d9822b", "pins": "#e3c565",
               "pads": "#e3c565", "bf_pins": "#c9a227", "wago": "#9aa0a6", "psu": "#2b2b2b",
               "front": "#c8a03a", "mains_board": "#2f7a46", "mains_front": "#c8a03a", "header": "#2b2b2b",
               "socket": "#2b2b2b", "carrier": "#c9a86a", "sensor_board": "#2f7a46", "sb_pads": "#e3c565",
               "cn2": "#e9e6df", "spacers": "#c9ccd1", "passives": "#2f9e5b", "mic": "#d9534f", "sht45": "#5b2a86",
               "sb_screws": "#5a6068", "snaps": "#e07b1f"})


def box_shell():
    """The flush box (Ø60 inside, 1.5 mm wall), for context."""
    outer = Pos(0, 0, -BOX_D / 2 - 0.75) * Cylinder(BOX_R + 1.5, BOX_D + 1.5)
    return outer - Pos(0, 0, -BOX_D / 2 + 0.01) * Cylinder(BOX_R, BOX_D)


def parts(lift=0.0, plain=False, switch=False):
    """EU plate; plain: the rocker and battery-free plate (D-109), no sensor board, sensors or sensor pins."""
    b = boards_eu.parts()
    if plain or switch:
        keep = ("wago", "magnet", "mains_board") if switch else ("board", "psu", "wago", "magnet", "front", "mains_board",
                                                                 "mains_front", "header", "socket", "bf_pins")
        return {"face_plate": face_plate_eu.build(True), "barrier": barrier_eu.build(True, switch), "carrier": sensor_board_eu.carrier(True),
                "remote": boards_eu.remote(lift), "switch": boards_eu.switch_model(),
                **{k: b[k] for k in keep}, "box": box_shell()}
    return {"face_plate": face_plate_eu.build(), "barrier": barrier_eu.build(), "remote": boards_eu.remote(lift),
            "switch": boards_eu.switch_model(), "board": b["board"], "psu": b["psu"], "wago": b["wago"], "magnet": b["magnet"], "front": b["front"],
            "mains_board": b["mains_board"], "mains_front": b["mains_front"], "header": b["header"], "socket": b["socket"],
            "pins": b["pins"], "bf_pins": b["bf_pins"], "box": box_shell(), **sensor_board_eu.parts()}


def main():
    ps = parts()
    render.shot("eu_front", ps, [(130, -170, 260), (0, 8, 0), (0, 1, 0)], hide=("box",))
    render.shot("eu_plain_front", parts(plain=True), [(130, -170, 260), (0, 0, 0), (0, 1, 0)], hide=("box",))
    render.shot("eu_plain_remote_out", parts(lift=45, plain=True), [(170, -190, 300), (0, 0, 15), (0, 1, 0)], hide=("box",))
    render.shot("eu_switch_front", parts(switch=True), [(130, -170, 260), (0, 0, 0), (0, 1, 0)], hide=("box",))
    render.shot("eu_switch_remote_out", parts(lift=45, switch=True), [(170, -190, 300), (0, 0, 15), (0, 1, 0)], hide=("box",))
    render.shot("eu_remote_out", parts(lift=45), [(170, -190, 300), (0, 8, 15), (0, 1, 0)], hide=("box",))
    keep = Pos(-100, 0, 0) * Box(200, 400, 400)          # half left of the x = 0 plane: cup, rocker, boards, PSU
    cut = {k: v & keep for k, v in ps.items()}
    cut = {k: v for k, v in cut.items() if v is not None and v.volume > 1e-6}
    render.shot("eu_section", cut, [(230, 40, 60), (0, 5, -8), (0, 0, 1)])
    off = {"remote": 70, "face_plate": 45, "msr": 26, "cn2": 14, "spacers": 14, "passives": 8, "mic": 8,
           "sensor_board": 8, "sb_pads": 8, "sht45": 8, "sb_screws": 14, "carrier": 4,
           "barrier": 0, "magnet": -8,
           "board": -18, "front": -18, "pins": -18, "bf_pins": -18, "socket": -18, "switch": -30,
           "mains_board": -45, "mains_front": -45, "header": -45, "psu": -45, "wago": -45}
    ex = {k: Pos(0, 0, off[k]) * v for k, v in ps.items() if k in off}
    render.shot("eu_exploded", ex, [(300, -240, 120), (0, 0, -5), (0, 1, 0)], size=(1400, 1300), head=0.8)
    # the sensors' side on the barrier: carrier, sensor board with the MSR-2 on CN2 and its spacers, the mic, SHT40
    render.shot("eu_sensors", ps, [(150, -110, 170), (5, 20, 6), (0, 1, 0)], size=(1400, 1200),
            hide=("face_plate", "remote", "box"), head=0.9, alpha={"barrier": 0.5, "msr": 0.6})
    # cut through the sensor pins: pin board, pins through the barrier and the carrier onto the sensor board's pads
    keep = ("barrier", "carrier", "sensor_board", "sb_pads", "pins", "board", "front", "face_plate")
    cutter = Pos(PINS[0][0] - 100, 0, 0) * Box(200, 400, 400)
    cps = {k: v & cutter for k, v in ps.items() if k in keep}
    cps = {k: v for k, v in cps.items() if v is not None and v.volume > 1e-6}
    y = (PINS[0][1] + PINS[1][1]) / 2
    render.shot("eu_sensor_pins", cps, [(PINS[0][0] + 55, y, 12), (PINS[0][0] - 2, y, 0), (0, 0, 1)], size=(1200, 900),
            head=1.0, alpha={"face_plate": 0.4})
    # cut through the top right snap (D-77): finger from the face skin into the carrier's window, bump in its groove
    from math import cos, radians, sin
    a = SNAPS[0][0]
    c, s = cos(radians(a)), sin(radians(a))
    cutter = Rot(0, 0, a) * Pos(0, 100, 0) * Box(400, 200, 400)          # the half beyond the finger's mid-plane
    fingers = face_plate_eu.snaps()
    sps = {**{k: v for k, v in ps.items() if k in ("barrier", "carrier", "sensor_board", "board", "box")},
           "face_plate": ps["face_plate"] - fingers, "snaps": fingers}
    sps = {k: v & cutter for k, v in sps.items()}
    sps = {k: v for k, v in sps.items() if v is not None and v.volume > 1e-6}
    p = (SNAP_R * c + 1.0 * c, SNAP_R * s + 1.0 * s, 3.0)
    render.shot("eu_snaps", sps, [(p[0] + 42 * s, p[1] - 42 * c, 5.0), p, (0, 0, 1)], size=(1400, 1000), head=1.0)
    # carrier clamp (D-71): from the wall side, the barrier's teeth in the lip's gaps; section through the lip at the top
    render.shot("eu_carrier_clamp", {k: ps[k] for k in ("barrier", "carrier")}, [(40, -30, -190), (0, 8, 0), (0, 1, 0)],
            size=(1300, 1300), head=0.9)
    cutter = Pos(-100, 0, 0) * Box(200, 400, 400)
    lps = {k: v & cutter for k, v in ps.items() if k in ("barrier", "carrier", "sensor_board", "box")}
    lps = {k: v for k, v in lps.items() if v is not None and v.volume > 1e-6}
    render.shot("eu_carrier_lip", lps, [(40, CAP_R + 14, 16), (0, CAP_R - 1, 1.5), (0, 0, 1)], size=(1200, 900), head=1.0)
    # into the box from behind: mains board with the WAGO blocks and the PSU, rocker, pin board, bosses
    render.shot("eu_box", ps, [(90, -110, -170), (0, -2, -8), (0, 1, 0)], size=(1300, 1100),
            hide=("face_plate", "remote", "msr", "box"), head=1.0)
    render.shot("eu_back", ps, [(110, -140, -210), (0, 8, -8), (0, 1, 0)], size=(1300, 1100), hide=("box",), head=1.0)


if __name__ == "__main__":
    main()
