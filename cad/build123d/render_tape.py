"""Each printed part with its flexes and their tape points (semi-translucent; NA has no flex left in the plate, D-50): xvfb-run python render_tape.py
-> docs/renders/tape_*.png"""
import sys
from pathlib import Path
from build123d import Box, Pos
import render3d as r3

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


def cover():
    """Replacement back cover: the cover flex, its end section taped to the contact blocks."""
    import backcover as bc
    ps = dict(bc.cover_parts())
    ps = {k: (Pos(0, LIFT * bc.BC_TERM_Y, 0) * v if k in ("flex", "stiffener", "contacts") else v) for k, v in ps.items()}
    r3.shot("tape_cover", ps, [(70, -120, 140), (0, -12, 4), (0, 0, 1)], size=(1300, 1100), head=0.7, alpha=GLASS)
    end = Pos(0, bc.copper_y(), 6) * Box(34, 12, 16)
    r3.shot("tape_cover_end", crop(ps, end), [(25, bc.copper_y() - 45, 30), (0, bc.copper_y(), 6), (0, 0, 1)],
            size=(1300, 1000), head=0.7, alpha=GLASS)


if __name__ == "__main__":
    only = sys.argv[1:] or ["cover"]
    for name in only:
        globals()[name]()
