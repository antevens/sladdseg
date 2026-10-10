"""Each printed part with its flexes and their tape points (semi-translucent): xvfb-run python render_tape.py
-> docs/renders/tape_*.png"""
import sys
from pathlib import Path
from build123d import Box, Pos
import render3d as r3
import tape

sys.path.insert(0, str(Path(__file__).resolve().parent / "eu"))

r3.COL.update({"tape": "#1f8fe0", "part": "#9ea3aa", "flex": "#d99a2b", "stiffener": "#2f7a46", "fingers": "#c9a227",
               "mic": "#5b4aa0", "sht45": "#2b2b2b", "plug": "#2b2b2b", "target": "#e3c565", "floor": "#9aa5b1",
               "floor_flex": "#d99a2b", "floor_pads": "#e3c565", "pads": "#e3c565", "contacts": "#c9a227",
               "regulator": "#2b2b2b", "pad_stiffener": "#2f7a46", "steel": "#6d7075", "cover": "#e9e6df"})
GLASS = {"tape": 0.5, "flex": 0.6, "floor_flex": 0.6}
LIFT = 2.5                                # flexes drawn this far off their part (the tape stays on the part)
FLEX_KEYS = ("flex", "fingers", "mic", "sht45", "plug", "target", "pads", "floor_flex", "floor_pads", "contacts",
             "regulator", "pad_stiffener", "stiffener")


def lifted(ps, dz):
    """The flexes and their parts moved dz along z, away from the part they are taped to."""
    return {k: (Pos(0, 0, dz) * v if k in FLEX_KEYS else v) for k, v in ps.items()}


def union(d):
    out = None
    for v in d.values():
        out = v if out is None else out + v
    return out


def crop(ps, box):
    out = {}
    for k, v in ps.items():
        c = v & box
        if c is not None and c.volume > 1e-6:
            out[k] = c
    return out


def na_trim():
    """Face plate: the sensor flex (tongue included) on the trim, the floor insert hanging from the strip, seen from
    the wall side."""
    import trim
    import floor_na
    import sensor_flex as sf
    fp = sf.parts()
    fl = floor_na.parts()
    ps = {"part": trim.build(), "flex": fp["flex"] + sf.tongue(), "fingers": fp["fingers"], "mic": fp["mic"],
          "sht45": fp["sht45"], "plug": fp["plug"], "floor": fl["floor"], "floor_flex": fl["floor_flex"],
          "floor_pads": fl["floor_pads"], "tape": union(tape.trim_side())}
    ps = lifted(ps, -LIFT)
    r3.shot("tape_na_trim", ps, [(-60, -40, -230), (0, 5, 6), (0, 1, 0)], size=(1300, 1500), head=0.7, alpha=GLASS)
    corner = Pos(26, 50, 5) * Box(24, 30, 20)
    r3.shot("tape_na_trim_corner", crop(ps, corner), [(-10, 20, -70), (27, 50, 6), (0, 1, 0)], size=(1300, 1100),
            head=0.7, alpha=GLASS)
    bottom = Pos(17, -48, 5) * Box(40, 20, 20)
    r3.shot("tape_na_trim_bottom", crop(ps, bottom), [(-5, -75, -60), (17, -48, 8), (0, 1, 0)], size=(1300, 1000),
            head=0.7, alpha=GLASS)


def na_insert():
    """Insert side (seen from the room): the 5 V jumper's pad end on the corner shelf, the only flex left on the
    insert when the face plate is off."""
    import insert
    import jumper
    import sensor_flex as sf
    ps = {"part": insert.build(), "flex": jumper.build()["jumper"], "target": sf.target(),
          "tape": union(tape.insert_side())}
    ps = lifted(ps, LIFT)
    r3.shot("tape_na_insert", ps, [(80, -120, 220), (5, 10, 0), (0, 1, 0)], size=(1300, 1300), head=0.7, alpha=GLASS)
    corner = Pos(23, 40, 0) * Box(24, 26, 40)
    r3.shot("tape_na_insert_corner", crop(ps, corner), [(70, 95, 75), (23, 40, 5), (0, 0, 1)], size=(1300, 1100),
            head=0.7, alpha=GLASS)


def cover():
    """Replacement back cover: the cover flex, its end section taped to the contact blocks."""
    import backcover as bc
    ps = dict(bc.cover_parts())
    t = union(tape.cover_side())
    if t is not None:
        ps["tape"] = t
    ps = {k: (Pos(0, LIFT * bc.BC_TERM_Y, 0) * v if k in ("flex", "stiffener", "contacts") else v) for k, v in ps.items()}
    r3.shot("tape_cover", ps, [(70, -120, 140), (0, -12, 4), (0, 0, 1)], size=(1300, 1100), head=0.7, alpha=GLASS)
    end = Pos(0, bc.copper_y(), 6) * Box(34, 12, 16)
    r3.shot("tape_cover_end", crop(ps, end), [(25, bc.copper_y() - 45, 30), (0, bc.copper_y(), 6), (0, 0, 1)],
            size=(1300, 1000), head=0.7, alpha=GLASS)


def eu_trim():
    """EU face plate: the sensor flex on the trim (ramps over its slopes), seen from the wall side."""
    import trim_eu
    import sensor_eu as se
    import tape_eu
    fp = se.parts()
    ps = {"part": trim_eu.build(), "flex": fp["flex"], "mic": fp["mic"], "sht45": fp["sht45"], "plug": fp["plug"],
          "pads": fp["pads"], "tape": union(tape_eu.trim_side())}
    ps = lifted(ps, -LIFT)
    r3.shot("tape_eu_trim", ps, [(-60, -40, -230), (0, 5, 10), (0, 1, 0)], size=(1300, 1500), head=0.7, alpha=GLASS)
    side = Pos(31.0, 10, 10) * Box(11.4, 80, 30)        # the right channel only, not the pocket wall
    r3.shot("tape_eu_trim_channel", crop(ps, side), [(5, -10, -65), (28, 10, 12), (0, 1, 0)], size=(1000, 1400),
            head=0.7, alpha=GLASS)


def eu_floor():
    """EU floor insert on the cap: the tongue taped in the recess."""
    import cap_eu
    import floor_eu
    import tape_eu
    fl = floor_eu.parts()
    ps = {"part": cap_eu.build(), "floor": fl["floor"], "floor_flex": fl["floor_flex"], "floor_pads": fl["floor_pads"],
          "tape": union(tape_eu.floor_side())}
    ps = lifted(ps, LIFT)
    r3.shot("tape_eu_floor", ps, [(70, -110, 200), (8, -2, 0), (0, 1, 0)], size=(1300, 1200), head=0.7, alpha=GLASS)


if __name__ == "__main__":
    only = sys.argv[1:] or ["na_trim", "na_insert", "cover", "eu_trim", "eu_floor"]
    for name in only:
        globals()[name]()
