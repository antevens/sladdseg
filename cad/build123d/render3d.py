"""Shaded 3D renders for the docs: xvfb-run python render3d.py -> docs/renders/v0.6_*.png"""
import tempfile
from pathlib import Path
import pyvista as pv
from build123d import Box, Pos, export_stl
from params import *
import assembly
import bilresa
import insert
import standoff
import ring
import jumper
import trim

R = Path(__file__).resolve().parents[2] / "docs" / "renders"
COL = {"trim": "#f2f1ee", "insert": "#8d949b", "remote": "#fbfaf6", "rocker": "#b23a32",
       "board": "#1f6b3a", "posts": "#d9822b", "flex": "#c98a1c", "tongue": "#c98a1c", "plug": "#222222", "sht45": "#5b2a86",
       "fingers": "#e3c565", "target": "#2f7a46", "jumper": "#d99a2b", "irm": "#2b2b2b", "wago": "#c9ccd1", "small": "#c8a03a",
       "msr": "#3a3a3a", "mic": "#2c5d8f", "floor": "#7d8a96", "floor_flex": "#d99a2b", "floor_pads": "#e3c565",
       "cover": "#e9e6df", "stiffener": "#2f7a46", "pads": "#e3c565", "contacts": "#c9a227", "regulator": "#2b2b2b",
       "steel": "#6d7075", "cflex": "#d99a2b", "front_half": "#fbfaf6", "pad_stiffener": "#2f7a46",
       "ring": "#2f7a46", "keep": "#d9534f", "spacers": "#c9ccd1", "cn2": "#222222", "j1": "#e9e6df", "passives": "#8a6d3b",
       "esp": "#b9bcc0", "usb": "#c9ccd1", "radar": "#1d4f91", "cn1": "#222222", "co2": "#3f9a5a", "scd": "#55585c",
       "sw": "#e9e6df", "riser": "#2f7a46", "pins": "#c9a227", "pin_posts": "#b8860b", "sleeves": "#2b2b2b", "screws": "#9aa0a6", "pin_pads": "#c9a227"}
BOARD_KEYS = ("board", "rocker", "irm", "wago", "small")
NO_ROCKER = tuple(k for k in BOARD_KEYS if k != "rocker")   # the wiring board hidden, its rocker shown


def board_parts():
    """Split the wiring board into coloured groups. From the KiCad STEP when present (it includes
    the rocker model), else the parameter envelopes."""
    from build123d import Compound
    b = assembly.wiring_board()
    if not assembly.WB_STEP.exists():
        sw = Compound([Pos(0, SW_Y, WELL_FLOOR_Z + SW_ROCKER_H / 2) * Box(SW_BEZEL[0], SW_BEZEL[1], SW_ROCKER_H),
                       Pos(0, SW_Y, WELL_FLOOR_Z - SW_BODY[2] / 2) * Box(*SW_BODY)])
        return {"board": b, "rocker": sw}
    groups = {k: [] for k in ("board", "rocker", "irm", "wago", "small")}
    for sol in b.solids():                                  # by where each solid sits (vendor models are many solids)
        bb = sol.bounding_box()
        c = bb.center()
        if bb.size.Z < 2.0 and bb.size.X > WB[0] - 1:
            groups["board"].append(sol)
        elif c.Z > WB_FRONT_Z and abs(c.X) < SW_BEZEL[0] / 2 + 1 and abs(c.Y - SW_Y) < SW_BEZEL[1] / 2 + 1:
            groups["rocker"].append(sol)
        elif c.Z < WB_BACK_Z and abs(c.X - IRM_C[0]) < IRM[0] / 2 + 1 and abs(c.Y - WB_Y - IRM_C[1]) < IRM[1] / 2 + 1:
            groups["irm"].append(sol)
        elif c.Z < WB_BACK_Z and abs(c.X - WAGO_X) < WAGO6[0] / 2 + 1 and abs(c.Y - WB_Y - WAGO_Y) < 12:
            groups["wago"].append(sol)
        else:
            groups["small"].append(sol)
    return {k: Compound(v) for k, v in groups.items() if v}


def mesh(part, d, name):
    f = Path(d) / f"{name}.stl"
    export_stl(part, str(f), tolerance=0.02, angular_tolerance=0.1)
    return pv.read(str(f))


def parts(lift=0.0, cut=False, pins_out=0.0, plain=False, switch=False):
    """Assembly parts; lift raises the remote, pins_out the spring pins (1.5 = extended with the remote out); plain:
    the rocker and battery-free plate (D-109), no ring board, sensors or FFC."""
    rp = ring.parts()
    rp["pin_posts"] = rp.pop("posts")
    rp.pop("keep")
    rp["pins"] = Pos(0, 0, pins_out) * rp["pins"]
    if plain or switch:
        rp = {} if switch else {k: rp[k] for k in ("riser", "pins", "pin_posts")}
    ps = {"trim": trim.build(plain or switch), "insert": insert.build(plain, switch), "remote": bilresa.build(lift),
          "posts": standoff.placed(), **rp, **({} if plain or switch else jumper.build())}
    ps.update(board_parts())
    if cut:  # keep x <= 0 for a half-section (board parts are clipped as meshes in shot())
        keep = Pos(-100, 0, 0) * Box(200, 400, 400)
        ps = {k: (v if k in BOARD_KEYS else v & keep) for k, v in ps.items()}
        ps = {k: v for k, v in ps.items() if k in BOARD_KEYS or (v is not None and v.volume > 1e-6)}
    return ps, cut


def battery_free(lift_cover=0.0, lift_remote=0.0):
    """NA battery-free remote (D-41, D-50): the replacement back cover and the remote's front half on the pocket
    floor (lifted for exploded views); the spring pins come from the riser (ring.parts)."""
    import backcover
    ps = {}
    cov = backcover.cover_parts()
    ps.update({("cflex" if k == "flex" else k): Pos(0, 0, SEAT_Z + lift_cover) * v for k, v in cov.items()})
    ps["front_half"] = Pos(0, 0, SEAT_Z + lift_remote) * backcover.remote_front()
    return ps


def shot(name, ps, cam, size=(1400, 1100), hide=(), head=0.55, alpha=None):
    ps, cut = ps if isinstance(ps, tuple) else (ps, False)
    with tempfile.TemporaryDirectory() as d:
        p = pv.Plotter(off_screen=True, window_size=size, lighting="none")
        p.set_background("white")
        p.add_light(pv.Light(light_type="headlight", intensity=head))
        p.add_light(pv.Light(position=(200, 300, 400), focal_point=(0, 0, 0), intensity=0.6, light_type="scene light"))
        p.add_light(pv.Light(position=(-300, -100, 200), focal_point=(0, 0, 0), intensity=0.25, light_type="scene light"))
        for k, v in ps.items():
            if k in hide or v is None:
                continue
            m = mesh(v, d, k)
            if cut and k in BOARD_KEYS:
                m = m.clip(normal="x", origin=(0, 0, 0))
            p.add_mesh(m, color=COL[k], smooth_shading=True, split_sharp_edges=True,
                       specular=0.25, specular_power=20, opacity=(alpha or {}).get(k, 1.0))
        p.camera_position = cam
        p.enable_anti_aliasing("ssaa")
        p.screenshot(str(R / f"{name}.png"))
        p.close()
    print("wrote", R / f"{name}.png")


def main():
    R.mkdir(parents=True, exist_ok=True)
    ring_keys = ("ring", "spacers", "cn2", "msr", "j1", "sht45", "passives", "mic")
    shot("v0.6_front", parts(), [(150, -170, 260), (0, 0, 0), (0, 1, 0)], hide=BOARD_KEYS)
    shot("v0.6_remote_out", parts(lift=45, pins_out=1.5), [(210, -200, 330), (0, 0, 15), (0, 1, 0)], hide=NO_ROCKER)
    shot("v0.6_section", parts(cut=True), [(290, 70, 150), (0, 0, -5), (0, 1, 0)])
    shot("plain_front", parts(plain=True), [(150, -170, 260), (0, 0, 0), (0, 1, 0)], hide=BOARD_KEYS)
    shot("plain_remote_out", parts(lift=45, pins_out=1.5, plain=True), [(210, -200, 330), (0, 0, 15), (0, 1, 0)],
         hide=NO_ROCKER)
    shot("switch_front", parts(switch=True), [(150, -170, 260), (0, 0, 0), (0, 1, 0)], hide=BOARD_KEYS)
    shot("switch_remote_out", parts(lift=45, switch=True), [(210, -200, 330), (0, 0, 15), (0, 1, 0)], hide=NO_ROCKER)
    shot("v0.6_back", parts(), [(130, -120, -230), (0, -5, -10), (0, 1, 0)], hide=("trim",), head=1.0,
         alpha={"insert": 0.45})
    # exploded: remote, face plate, insert with the ring board, wiring board pulled apart along z
    ps, _ = parts()
    off = {"remote": 95, "trim": 55, "insert": 0, "posts": -25, "jumper": 0, "riser": -25, "pins": -25,
           "pin_posts": -25, "sleeves": -25, "screws": -25, **{k: -20 for k in ring_keys}, **{k: -55 for k in BOARD_KEYS}}
    exploded = {k: Pos(0, 0, off[k]) * v for k, v in ps.items() if k in off}
    shot("v0.6_exploded", exploded, [(330, -260, 120), (0, 0, 15), (0, 1, 0)], size=(1400, 1300), head=0.8)
    # face plate lifted off: nothing comes with it but the plastic (D-50)
    ps, _ = parts(pins_out=1.5)
    ps.pop("remote")
    sep = {k: (Pos(0, 0, 40) * v if k == "trim" else v) for k, v in ps.items()}
    shot("v0.6_face_off", sep, [(230, -200, 200), (5, 5, 10), (0, 0, 1)], size=(1400, 1300),
         hide=("posts",) + BOARD_KEYS, head=0.9, alpha={"trim": 0.3})
    # the ring board with its parts, from the front
    ps, _ = parts()
    rb = {k: ps[k] for k in ring_keys}
    rb["keep"] = ring.keepout()
    shot("v0.6_ring", rb, [(30, -60, 240), (0, 6, 0), (0, 1, 0)], size=(1200, 1600), head=0.9)
    # 5 V cable path: insert and face plate cut at the pass-through, seen from the right
    ps, _ = parts()
    keep = Pos(PASS_E[0] - 150, 0, 0) * Box(300, 400, 400)
    ps = {k: (v & keep if k in ("insert", "trim", "ring") else v) for k, v in ps.items()}
    shot("v0.6_power", ps, [(230, -40, 30), (22, 5, -8), (0, 1, 0)], size=(1400, 1100),
         hide=("remote", "trim", "posts", "msr"), head=1.0)
    # battery-free remote: back cover (pads) and remote lifted off the pocket, the pins extended
    ps, _ = parts(pins_out=1.5)
    ps.pop("remote")
    bf = battery_free(lift_cover=30, lift_remote=55)
    shot("v0.6_battery_free", {**ps, **bf}, [(260, -230, 210), (5, 0, 10), (0, 1, 0)], size=(1400, 1300),
         hide=("trim", "posts") + BOARD_KEYS, head=0.85, alpha={"insert": 0.6})
    # spring pins: cut through both pins (x), seen from +x: board, posts, riser, pins, floor, cover, remote
    ps, _ = parts()
    ps.pop("remote")
    bf = battery_free()
    x = BC_FINGERS[0][0]
    keep = Pos(x - 100, 0, 0) * Box(200, 400, 400)
    cutp = {k: (v & keep) for k, v in {**ps, **bf}.items() if k not in BOARD_KEYS}
    cutp = {k: v for k, v in cutp.items() if v is not None and v.volume > 1e-6}
    cutp.update({k: v for k, v in ps.items() if k in BOARD_KEYS})
    shot("v0.6_pins", cutp, [(x + 120, -5, -5), (x, -5, -8), (0, 0, 1)], size=(1400, 1100),
         hide=("trim", "posts", "wago"), head=1.0, alpha={"front_half": 0.35, "cover": 0.5})
    # hacksaw guide for the steel plate (D-52, D-81), the supplied plate in it, cut line red
    import plate_jig as pj
    from params import MAGNET, JIG_FLOOR, JIG_SAW
    COL.update({"jig": "#f2a541", "steel": "#9aa0a6", "cut": "#d9534f"})
    js = {"jig": pj.saw_guide(), "steel": pj.plate(),
          "cut": Pos(0, MAGNET[1], JIG_FLOOR + MAGNET[2] + JIG_SAW[2] + 0.1) * Box(40, 0.25, 0.05)}
    shot("plate_jigs", js, [(60, -55, 75), (0, 20, 2), (0, 0, 1)], size=(1100, 950), head=0.9)
    # MSR-2 with the CO2 add-on (msr2.py): front and back, board frame
    import msr2
    m2 = msr2.parts()
    m2["cn2"] = Pos(MSR_CN2_X, 0, -B2B_STACK / 2) * Box(B2B[0], B2B[1], B2B_STACK)     # CN2 with its mate
    shot("msr2_front", m2, [(22, -42, 52), (0, 0, 4), (0, 1, 0)], size=(1200, 900), head=0.9)
    shot("msr2_back", m2, [(-20, -38, -52), (0, 0, 2), (0, 1, 0)], size=(1200, 900), head=1.0)
    shot("bilresa_model", {"remote": bilresa.build()}, [(70, -90, 120), (0, 0, 0), (0, 1, 0)], size=(900, 900))
    shot("bilresa_back", {"remote": bilresa.build()}, [(95, -60, -110), (0, 0, SEAT_Z + B_D / 2), (0, 1, 0)], size=(900, 900), head=1.0)


if __name__ == "__main__":
    main()
