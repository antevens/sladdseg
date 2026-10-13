"""BARRIER - every piece of mains/low-voltage barrier lives here (v0.4, D-50, D-68).

The sensor board presses onto crush ribs on the collar's outside; in the box a flat land at the foot of the flange's
45 deg taper clamps its inner edge against the wall (D-68). No flat back over the board.
Print: UL94 V-0 filament, as modelled (z up, lowest face Z_BOT = the switch panel's underside and the
mounting bosses on the bed). The mains board hangs on four nylon standoffs (standoff_na.py) screwed into the bosses'
tapped M3 holes (D-57).
Run:  python barrier_na.py  -> ../../../build/na/barrier.step / .stl, blank_board.step / .stl
"""
from build123d import Box, Cone, Cylinder, Rectangle, Pos, Rot
from params_na import *
from common import rr, stadium, slab, taper, ellipsoid, prism, mouth_chamfer


def outline_solid():
    """Barrier without any cavities (also used by face_plate_na.py as its clearance envelope)."""
    # pocket shell / thick floor, from the bed up to the face
    body = slab(stadium(*POCKET_OUT), Z_BOT, PT)
    # 45-degree taper carrying the flange out to the plug outline inside the box (no overhang there)
    t = taper(*POCKET_OUT, POCKET_OUT[0] / 2, -TAPER_D, 0, TAPER_D)
    body += t & slab(rr(*PLUG, PLUG_R), -TAPER_D - 1, 0)
    # flange: on the wall over the seal band round the box opening; beyond it, over the sensor board, a flat land then
    # a 45 deg taper out to the flange's outline (prints without supports, D-68)
    f = slab(rr(*SEAL, PLUG_R + COLLAR_LIP), 0, DECK_Z)
    land = SB_WIN_CLR + SB_LAND
    f += taper(SEAL[0] + 2 * land, SEAL[1] + 2 * land, PLUG_R + COLLAR_LIP + land, SB_T, DECK_Z, DECK_Z - SB_T) \
        & slab(rr(*FLANGE_OUT, ISLAND_R + FLANGE), SB_T, DECK_Z)
    for s in (-1, 1):
        f += Pos(0, s * SCREW_PITCH / 2, DECK_Z / 2) * Cylinder(BOSS_R, DECK_Z)
    body += f + ribs()
    # island: flush with the face plate face
    body += slab(rr(*ISLAND, ISLAND_R), DECK_Z - 0.01, PT)
    return body


def build():
    """The barrier, one for every edition (D-127): the remote pocket, the switch well, the 5 V cable's slit (D-134),
    the spring pins' holes, the pin board's pocket and its clips (in the switch-only edition the printed blank board,
    sensor_board_na.blank_board(), sits in the pocket and its pegs fill the holes)."""
    import sensor_board_na
    body = outline_solid()
    # ---------------- cuts ----------------
    cut = slab(stadium(*POCKET_IN), SEAT_Z, PT + 5)                                       # remote pocket
    cut += Pos(0, SW_Y, 0) * slab(rr(*WELL_IN, 1), WELL_FLOOR_Z, SEAT_Z + 0.1)            # switch well
    cut += Pos(0, SW_Y, 0) * slab(Rectangle(*SW_CUT), PANEL_BOT_Z - 1, WELL_FLOOR_Z + 1)
    cut += magnet_recess()
    for s in (-1, 1):                                                                     # finger scoops
        cut += Pos(s * SCOOP_X, 0, SCOOP_ZC) * ellipsoid(*SCOOP)
    for s in (-1, 1):                                                                     # #6 screw clearance
        cut += Pos(0, s * SCREW_PITCH / 2, DECK_Z / 2) * Cylinder(SCREW_D / 2, DECK_Z + 2)
    cut += ffc_slot()
    cut += sensor_board_na.pin_holes() + sensor_board_na.pin_board_pocket()               # battery-free remote (D-50)
    clip_relief, clip_hooks = sensor_board_na.pin_board_clips()                           # pin board snap clips (D-91)
    body -= cut + clip_relief
    body += clip_hooks
    for kx, ky in KEY_POS:                                                                # locating pins
        body += Pos(kx, ky, DECK_Z + KEY_H / 2 - 0.01) * Cylinder(KEY_D / 2, KEY_H + 0.02)
    import face_plate_na
    body -= prism(face_plate_na.screw_lobes().buffer(SCREW_LOBE[1], 64), DECK_Z - 0.01, PT + 1)   # the face plate's lobes (D-132)
    body += mount_bosses()                                                                # after the pocket cut
    body -= mount_holes()
    body -= arrows()
    body -= mouth_chamfer(*POCKET_IN, PT, POCKET_CHAMFER)                                 # 45 deg round the pocket's mouth
    return body


def ribs():
    """Crush ribs on the collar's outside (D-68): they bridge the board's window clearance with SB_RIB[1]
    interference; a 45 deg lead-in at the wall end guides the board on and prints without support."""
    w, interf = SB_RIB
    d = SB_WIN_CLR + interf
    hx, hy = SEAL[0] / 2, SEAL[1] / 2
    pts = []
    for ax, t in SB_RIBS:
        for s1 in (-1, 1):
            for s2 in (-1, 1):
                pts.append((s1 * hx, s2 * t, s1, 0) if ax == "x" else (s2 * t, s1 * hy, 0, s1))
    out = None
    for x, y, nx, ny in pts:
        bx, by = (d, w) if nx else (w, d)
        r = Pos(x + nx * d / 2, y + ny * d / 2, SB_T / 2) * Box(bx, by, SB_T)
        a = d * 2 ** 0.5                                    # square turned 45 deg on the outer bottom edge: d x d lead-in
        if nx:
            r -= Pos(x + nx * d, y, 0) * Rot(0, 45, 0) * Box(a, w + 1, a)
        else:
            r -= Pos(x, y + ny * d, 0) * Rot(45, 0, 0) * Box(w + 1, a, a)
        out = r if out is None else out + r
    return out


def ffc_slot():
    """The 5 V cable's slit (D-134), the barrier's single cable opening: through the bottom wall along the cable's own
    line (ffc_curve()), in through the taper below the plug's bottom face, the straight run up through the wall behind a
    lip, the bend over onto the sensor board guided by the curved slit, out under the flange to J1; FFC_SLOT[1] round
    the cable. Open along its left side (FFC_SLOT[2]) so the cable, bent to shape, slides in sideways; the lip cut
    back below FFC_LIP_Z (no knife edge at the mouth)."""
    from shapely.geometry import LineString, Polygon, box as sbox
    from common import radial_prism
    w, gap, notch = FFC_SLOT
    g = gap / 2
    pts, (t1, _) = ffc_curve()
    k = next(i for i, p in enumerate(pts) if p[1] >= t1[1] - 1e-6)
    run = [p for p in pts if p[1] < FFC_BOARD_Z - 1e-6 or p[0] >= FFC_ARC_END_Y - 1e-6]   # J2 to the end of the bend

    def yz(poly, width, xc):                             # section (y, z) polygon, width along x
        return radial_prism((xc, 0.0), (0.0, 1.0), list(poly.exterior.coords)[:-1], width)

    slot = LineString(run).buffer(g, cap_style=2, join_style=1)
    out = yz(slot, w, FFC_SLOT_X)
    side = Polygon(run[k:] + [(-60.0, FFC_BOARD_Z + g), (-60.0, run[k][1])]).union(slot).buffer(0)
    out += yz(side, notch, FFC_SLOT_X - w / 2 + notch / 2)
    out += yz(side.intersection(sbox(-60.0, -40.0, 0.0, FFC_LIP_Z)), w, FFC_SLOT_X)
    z0, z1 = SB_T - 0.01, FFC_BOARD_Z + g + 0.3                # over the board, out under the flange to J1
    j1 = SB_J1[1] + FH12_ENTRY
    prof = [(-w / 2, z0), (w / 2, z0), (w / 2, z1), (0.0, z1 + w / 2), (-w / 2, z1)]
    out += radial_prism((FFC_SLOT_X, (FFC_ARC_END_Y + 0.3 + j1) / 2), (1.0, 0.0), prof, FFC_ARC_END_Y + 0.3 - j1)
    return out


def arrows():
    """Arrows engraved in the plug's bottom face either side of the slit, pointing at it: the cable goes in the slit,
    not between the box and the barrier (D-134)."""
    from build123d import Polyline, extrude, make_face
    L, hw, d, zc = ARROW
    out = None
    for s in (-1, 1):
        tip = FFC_SLOT_X + s * (FFC_SLOT[0] / 2 + 1.0)
        tail = tip + s * L
        pts = [(tail, zc - 0.4), (tip + s * hw, zc - 0.4), (tip + s * hw, zc - hw / 2), (tip, zc),
               (tip + s * hw, zc + hw / 2), (tip + s * hw, zc + 0.4), (tail, zc + 0.4)]
        face = make_face(Polyline(*[(px, -PLUG_TOP - 0.01, pz) for px, pz in pts], close=True))
        a = extrude(face, d + 0.01, dir=(0, 1, 0))
        out = a if out is None else out + a
    return out


def mount_bosses():
    """Bosses for the board standoffs, from the standoffs' face up into the barrier."""
    out = None
    for (x, y), top in zip(MOUNT_HOLES, MOUNT_BOSS_TOP):
        b = Pos(x, y, (MOUNT_FACE_Z + top) / 2) * Cylinder(MOUNT_BOSS_D / 2, top - MOUNT_FACE_Z)
        out = b if out is None else out + b
    return out


def mount_hole(x, y, depth):
    """Blind tap-drill hole from the boss face, ending in a 45 deg cone (prints unsupported)."""
    bore = Pos(x, y, MOUNT_FACE_Z + depth / 2 - 0.01) * Cylinder(MOUNT_TAP_D / 2, depth)
    r0, r1 = MOUNT_TAP_D / 2, 0.1                             # 45 deg cone, small flat tip (meshes cleanly)
    tip = Pos(x, y, MOUNT_FACE_Z + depth + (r0 - r1) / 2 - 0.01) * Cone(r0, r1, r0 - r1)
    return bore + tip


def mount_holes():
    out = None
    for (x, y), depth in zip(MOUNT_HOLES, MOUNT_THREAD_L):
        h = mount_hole(x, y, depth)
        out = h if out is None else out + h
    return out


def magnet_recess():
    """Supplied magnet recess: from above the magnet's nominal position down to the end of the
    flat back. The bottom end follows the magnet's own rounded end, so the magnet only needs a
    straight cut at the top."""
    w = MAGNET[0] + 2 * MAGNET_CLR
    r = MAGNET_END_R + MAGNET_CLR
    top = MAGNET_REC_Y + MAGNET[1] / 2 + MAGNET_CLR
    z0, z1 = SEAT_Z - MAGNET[2] - MAGNET_SETBACK, SEAT_Z + 0.1
    end = Pos(0, MAGNET_SLOT_BOT + r, 0) * slab(rr(w, 2 * r, r), z0, z1)
    upper = Pos(0, (top + MAGNET_SLOT_BOT + r) / 2, 0) * slab(Rectangle(w, top - MAGNET_SLOT_BOT - r), z0, z1)
    return end + upper


if __name__ == "__main__":
    from pathlib import Path
    from build123d import export_step, export_stl
    out = Path(__file__).resolve().parents[3] / "build" / "na"
    out.mkdir(parents=True, exist_ok=True)
    import sensor_board_na
    for name, p in (("barrier", build()), ("blank_board", sensor_board_na.blank_board())):
        bb = p.bounding_box()
        print(f"{name} bbox x {bb.min.X:.1f}..{bb.max.X:.1f} y {bb.min.Y:.1f}..{bb.max.Y:.1f} z {bb.min.Z:.1f}..{bb.max.Z:.1f}"
              f"  vol {p.volume/1000:.1f} cm3 valid={p.is_valid} solids={len(p.solids())}")
        export_step(p, str(out / f"{name}.step"))
        export_stl(p, str(out / f"{name}.stl"), tolerance=0.02, angular_tolerance=0.1)
