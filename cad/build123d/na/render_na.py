"""NA plate renders for the docs: xvfb-run python render_na.py -> docs/renders/na_*.png"""
from build123d import Box, Pos
from params_na import *
from render import R, shot
import assembly_na
import bilresa
import barrier_na
import standoff_na
import sensor_board_na
import jumper_na
import face_plate_na

BOARD_KEYS = ("board", "rocker", "irm", "wago", "small")
NO_ROCKER = tuple(k for k in BOARD_KEYS if k != "rocker")   # the mains board hidden, its rocker shown


def board_parts():
    """Split the mains board into coloured groups. From the KiCad STEP when present (it includes
    the rocker model), else the parameter envelopes."""
    from build123d import Compound
    b = assembly_na.mains_board()
    if not assembly_na.MB_STEP.exists():
        sw = Compound([Pos(0, SW_Y, WELL_FLOOR_Z + SW_ROCKER_H / 2) * Box(SW_BEZEL[0], SW_BEZEL[1], SW_ROCKER_H),
                       Pos(0, SW_Y, WELL_FLOOR_Z - SW_BODY[2] / 2) * Box(*SW_BODY)])
        return {"board": b, "rocker": sw}
    groups = {k: [] for k in ("board", "rocker", "irm", "wago", "small")}
    for sol in b.solids():                                  # by where each solid sits (vendor models are many solids)
        bb = sol.bounding_box()
        c = bb.center()
        if bb.size.Z < 2.0 and bb.size.X > MB[0] - 1:
            groups["board"].append(sol)
        elif c.Z > MB_FRONT_Z and abs(c.X) < SW_BEZEL[0] / 2 + 1 and abs(c.Y - SW_Y) < SW_BEZEL[1] / 2 + 1:
            groups["rocker"].append(sol)
        elif c.Z < MB_BACK_Z and abs(c.X - IRM_C[0]) < IRM[0] / 2 + 1 and abs(c.Y - MB_Y - IRM_C[1]) < IRM[1] / 2 + 1:
            groups["irm"].append(sol)
        elif c.Z < MB_BACK_Z and abs(c.X - WAGO_X) < WAGO6[0] / 2 + 1 and abs(c.Y - MB_Y - WAGO_Y) < 12:
            groups["wago"].append(sol)
        else:
            groups["small"].append(sol)
    return {k: Compound(v) for k, v in groups.items() if v}


def parts(lift=0.0, cut=False, pins_out=0.0, plain=False, switch=False):
    """Assembly parts; lift raises the remote, pins_out the spring pins (1.5 = extended with the remote out); plain:
    the rocker and battery-free plate (D-109), no sensor board, sensors or FFC."""
    rp = sensor_board_na.parts()
    rp["pin_posts"] = rp.pop("posts")
    rp.pop("keep")
    rp["pins"] = Pos(0, 0, pins_out) * rp["pins"]
    if plain or switch:
        rp = {} if switch else {k: rp[k] for k in ("pin_board", "pins", "pin_posts")}
    ps = {"face_plate": face_plate_na.build(plain or switch), "barrier": barrier_na.build(plain, switch), "remote": bilresa.build(SEAT_Z, lift),
          "posts": standoff_na.placed(), **rp, **({} if plain or switch else jumper_na.build())}
    ps.update(board_parts())
    if cut:  # keep x <= 0 for a half-section (board parts are clipped as meshes in shot())
        keep = Pos(-100, 0, 0) * Box(200, 400, 400)
        ps = {k: (v if k in BOARD_KEYS else v & keep) for k, v in ps.items()}
        ps = {k: v for k, v in ps.items() if k in BOARD_KEYS or (v is not None and v.volume > 1e-6)}
    return ps, cut


def battery_free(lift_cover=0.0, lift_remote=0.0):
    """NA battery-free remote (D-41, D-50): the replacement back cover and the remote's front half on the pocket
    floor (lifted for exploded views); the spring pins come from the pin board (sensor_board_na.parts)."""
    import backcover
    ps = {}
    cov = backcover.cover_parts()
    ps.update({("cflex" if k == "flex" else k): Pos(0, 0, SEAT_Z + lift_cover) * v for k, v in cov.items()})
    ps["front_half"] = Pos(0, 0, SEAT_Z + lift_remote) * backcover.remote_front()
    return ps


def main():
    R.mkdir(parents=True, exist_ok=True)
    sb_keys = ("sensor_board", "spacers", "cn2", "msr", "j1", "sht45", "passives", "mic")
    shot("na_front", parts(), [(150, -170, 260), (0, 0, 0), (0, 1, 0)], hide=BOARD_KEYS)
    shot("na_remote_out", parts(lift=45, pins_out=1.5), [(210, -200, 330), (0, 0, 15), (0, 1, 0)], hide=NO_ROCKER)
    shot("na_section", parts(cut=True), [(290, 70, 150), (0, 0, -5), (0, 1, 0)], clip=BOARD_KEYS)
    shot("na_plain_front", parts(plain=True), [(150, -170, 260), (0, 0, 0), (0, 1, 0)], hide=BOARD_KEYS)
    shot("na_plain_remote_out", parts(lift=45, pins_out=1.5, plain=True), [(210, -200, 330), (0, 0, 15), (0, 1, 0)],
         hide=NO_ROCKER)
    shot("na_switch_front", parts(switch=True), [(150, -170, 260), (0, 0, 0), (0, 1, 0)], hide=BOARD_KEYS)
    shot("na_switch_remote_out", parts(lift=45, switch=True), [(210, -200, 330), (0, 0, 15), (0, 1, 0)], hide=NO_ROCKER)
    shot("na_back", parts(), [(130, -120, -230), (0, -5, -10), (0, 1, 0)], hide=("face_plate",), head=1.0,
         alpha={"barrier": 0.45})
    # exploded: remote, face plate, barrier with the sensor board, mains board pulled apart along z
    ps, _ = parts()
    off = {"remote": 95, "face_plate": 55, "barrier": 0, "posts": -25, "jumper": 0, "pin_board": -25, "pins": -25,
           "pin_posts": -25, "sleeves": -25, "screws": -25, **{k: -20 for k in sb_keys}, **{k: -55 for k in BOARD_KEYS}}
    exploded = {k: Pos(0, 0, off[k]) * v for k, v in ps.items() if k in off}
    shot("na_exploded", exploded, [(330, -260, 120), (0, 0, 15), (0, 1, 0)], size=(1400, 1300), head=0.8)
    # face plate lifted off: nothing comes with it but the plastic (D-50)
    ps, _ = parts(pins_out=1.5)
    ps.pop("remote")
    sep = {k: (Pos(0, 0, 40) * v if k == "face_plate" else v) for k, v in ps.items()}
    shot("na_face_off", sep, [(230, -200, 200), (5, 5, 10), (0, 0, 1)], size=(1400, 1300),
         hide=("posts",) + BOARD_KEYS, head=0.9, alpha={"face_plate": 0.3})
    # the sensor board with its parts, from the front
    ps, _ = parts()
    rb = {k: ps[k] for k in sb_keys}
    rb["keep"] = sensor_board_na.keepout()
    shot("na_sensors", rb, [(30, -60, 240), (0, 6, 0), (0, 1, 0)], size=(1200, 1600), head=0.9)
    # 5 V cable path: barrier and face plate cut at the pass-through, seen from the right
    ps, _ = parts()
    keep = Pos(PASS_E[0] - 150, 0, 0) * Box(300, 400, 400)
    ps = {k: (v & keep if k in ("barrier", "face_plate", "sensor_board") else v) for k, v in ps.items()}
    shot("na_power", ps, [(230, -40, 30), (22, 5, -8), (0, 1, 0)], size=(1400, 1100),
         hide=("remote", "face_plate", "posts", "msr"), head=1.0)
    # battery-free remote: back cover (pads) and remote lifted off the pocket, the pins extended
    ps, _ = parts(pins_out=1.5)
    ps.pop("remote")
    bf = battery_free(lift_cover=30, lift_remote=55)
    shot("na_battery_free", {**ps, **bf}, [(260, -230, 210), (5, 0, 10), (0, 1, 0)], size=(1400, 1300),
         hide=("face_plate", "posts") + BOARD_KEYS, head=0.85, alpha={"barrier": 0.6})
    # spring pins: cut through both pins (x), seen from +x: board, posts, pin board, pins, floor, cover, remote
    ps, _ = parts()
    ps.pop("remote")
    bf = battery_free()
    x = BC_FINGERS[0][0]
    keep = Pos(x - 100, 0, 0) * Box(200, 400, 400)
    cutp = {k: (v & keep) for k, v in {**ps, **bf}.items() if k not in BOARD_KEYS}
    cutp = {k: v for k, v in cutp.items() if v is not None and v.volume > 1e-6}
    cutp.update({k: v for k, v in ps.items() if k in BOARD_KEYS})
    shot("na_pins", cutp, [(x + 120, -5, -5), (x, -5, -8), (0, 0, 1)], size=(1400, 1100),
         hide=("face_plate", "posts", "wago"), head=1.0, alpha={"front_half": 0.35, "cover": 0.5})


if __name__ == "__main__":
    main()
