"""HACKSAW GUIDE for the steel plate supplied with the BILRESA (D-52, D-81): the whole plate lies in a pocket, round end
on the stop; walls above it with a hacksaw slot across at the cut line; clamp the jig in a vise. The cut at MAGNET[1]
leaves the piece the insert (NA) or the cap (EU) takes (D-43).
PETG, floor down, no supports.
Run:  python plate_jig.py  -> ../../build/plate_jig_saw.stl
"""
from build123d import Box, Cylinder, Pos
from params import MAGNET, MAGNET_FULL, JIG_CLR, JIG_WALL, JIG_FLOOR, JIG_SAW, JIG_NOTCH_R

W, KEEP, T = MAGNET[0], MAGNET[1], MAGNET[2]
FULL = MAGNET_FULL[1]


def round_slab(w, length, h, z0, y0=0.0):
    """Round-ended slab w wide, length long from y0, h thick from z0."""
    r = w / 2
    s = Pos(0, y0 + r, z0 + h / 2) * Cylinder(r, h)
    s += Pos(0, y0 + r + (length - 2 * r) / 2, z0 + h / 2) * Box(w, length - 2 * r, h)
    s += Pos(0, y0 + length - r, z0 + h / 2) * Cylinder(r, h)
    return s


def plate():
    """The supplied plate in the jig: kept end's apex at y = 0, cut line at y = KEEP."""
    return round_slab(W, FULL, T, JIG_FLOOR)


def tray(wall_h):
    """Block with the plate's pocket (open on top) and a finger notch in each side wall."""
    w = W + 2 * JIG_CLR
    body = Pos(0, FULL / 2, (JIG_FLOOR + wall_h) / 2) * Box(w + 2 * JIG_WALL, FULL + 2 * JIG_WALL, JIG_FLOOR + wall_h)
    body -= round_slab(w, FULL + 2 * JIG_CLR, wall_h + 1, JIG_FLOOR, -JIG_CLR)
    for s in (-1, 1):
        body -= Pos(s * (w / 2 + JIG_WALL / 2), FULL * 0.75, JIG_FLOOR + wall_h) * Cylinder(JIG_NOTCH_R, 2 * wall_h)
    return body


def saw_guide():
    slot, below, above = JIG_SAW
    h = T + above
    body = tray(h)
    z0 = JIG_FLOOR - below
    body -= Pos(0, KEEP, (z0 + JIG_FLOOR + h + 1) / 2) * Box(W + 2 * JIG_CLR + 2 * JIG_WALL + 2, slot, JIG_FLOOR + h + 1 - z0)
    return body


if __name__ == "__main__":
    from pathlib import Path
    from build123d import export_stl
    out = Path(__file__).resolve().parents[2] / "build"
    out.mkdir(exist_ok=True)
    for name, p in (("plate_jig_saw", saw_guide()),):
        bb = p.bounding_box()
        print(f"{name}: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm, {p.volume / 1000:.2f} cm3, "
              f"valid={p.is_valid} solids={len(p.solids())}")
        export_stl(p, str(out / f"{name}.stl"), tolerance=0.02, angular_tolerance=0.1)
