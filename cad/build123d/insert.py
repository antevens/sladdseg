"""BOX INSERT - every piece of mains/low-voltage barrier lives here (v0.4, D-50, D-68).

The ring board presses onto crush ribs on the collar's outside; in the box a flat land at the foot of the flange's
45 deg taper clamps its inner edge against the wall (D-68). No flat back over the board.
Print: UL94 V-0 filament, as modelled (z up, lowest face Z_BOT = the switch panel's underside and the
mounting bosses on the bed). The wiring board hangs on four nylon standoffs (standoff.py) screwed into the bosses'
tapped M3 holes (D-57).
Plain insert (D-109, no ring board): no 5 V cable channel or bore, so its only openings are the spring-pin holes.
Run:  python insert.py  -> ../../build/insert.step / .stl, insert_plain.step / .stl
"""
from math import hypot
from build123d import Box, Cone, Cylinder, Rectangle, Pos, Rot
from params import *
from common import rr, stadium, slab, taper, ellipsoid, rod


def outline_solid():
    """Insert without any cavities (also used by trim.py as its clearance envelope)."""
    # pocket shell / thick floor, from the bed up to the face
    body = slab(stadium(*POCKET_OUT), Z_BOT, PT)
    # 45-degree taper carrying the flange out to the plug outline inside the box (no overhang there)
    t = taper(*POCKET_OUT, POCKET_OUT[0] / 2, -TAPER_D, 0, TAPER_D)
    body += t & slab(rr(*PLUG, PLUG_R), -TAPER_D - 1, 0)
    # flange: on the wall over the seal band round the box opening; beyond it, over the ring board, a flat land then
    # a 45 deg taper out to the flange's outline (prints without supports, D-68)
    f = slab(rr(*SEAL, PLUG_R + COLLAR_LIP), 0, DECK_Z)
    land = RING_WIN_CLR + RING_LAND
    f += taper(SEAL[0] + 2 * land, SEAL[1] + 2 * land, PLUG_R + COLLAR_LIP + land, RING_T, DECK_Z, DECK_Z - RING_T) \
        & slab(rr(*FLANGE_OUT, ISLAND_R + FLANGE), RING_T, DECK_Z)
    for s in (-1, 1):
        f += Pos(0, s * SCREW_PITCH / 2, DECK_Z / 2) * Cylinder(BOSS_R, DECK_Z)
    body += f + ribs()
    # island: flush with the trim face
    body += slab(rr(*ISLAND, ISLAND_R), DECK_Z - 0.01, PT)
    return body


def build(plain=False):
    """Box insert; plain: without the 5 V cable's channel and bore (no ring board, D-109)."""
    import ring
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
    if not plain:
        cut += ffc_channel()
    cut += ring.pin_holes() + ring.riser_pocket()                                         # battery-free remote (D-50)
    clip_relief, clip_hooks = ring.riser_clips()                                          # riser snap clips (D-91)
    cut += clip_relief
    body -= cut
    body += clip_hooks
    for kx, ky in KEY_POS:                                                                # locating pins
        body += Pos(kx, ky, DECK_Z + KEY_H / 2 - 0.01) * Cylinder(KEY_D / 2, KEY_H + 0.02)
    body += mount_bosses()                                                                # after the pocket cut
    body -= mount_holes()
    if not plain:
        body -= pass_through()                                                            # after the bosses: past MH3's side
    return body


def ribs():
    """Crush ribs on the collar's outside (D-68): they bridge the board's window clearance with RING_RIB[1]
    interference; a 45 deg lead-in at the wall end guides the board on and prints without support."""
    w, interf = RING_RIB
    d = RING_WIN_CLR + interf
    hx, hy = SEAL[0] / 2, SEAL[1] / 2
    pts = []
    for ax, t in RING_RIBS:
        for s1 in (-1, 1):
            for s2 in (-1, 1):
                pts.append((s1 * hx, s2 * t, s1, 0) if ax == "x" else (s2 * t, s1 * hy, 0, s1))
    out = None
    for x, y, nx, ny in pts:
        bx, by = (d, w) if nx else (w, d)
        r = Pos(x + nx * d / 2, y + ny * d / 2, RING_T / 2) * Box(bx, by, RING_T)
        a = d * 2 ** 0.5                                    # square turned 45 deg on the outer bottom edge: d x d lead-in
        if nx:
            r -= Pos(x + nx * d, y, 0) * Rot(0, 45, 0) * Box(a, w + 1, a)
        else:
            r -= Pos(x, y + ny * d, 0) * Rot(45, 0, 0) * Box(w + 1, a, a)
        out = r if out is None else out + r
    return out


def ffc_channel():
    """Out of the pass-through's flat slot through the collar and the flange onto the ring board, towards J1 and the
    fold: flat floor on the board, 45 deg peaked roof (prints without supports)."""
    from common import radial_prism
    _, e, f = pass_points()
    w = PASS_SLOT[0]
    z0, z1 = RING_T - 0.01, RING_T + FH12[2] + 0.2
    prof = [(-w / 2, z0), (w / 2, z0), (w / 2, z1), (0.0, z1 + w / 2), (-w / 2, z1)]
    out = None
    for t in ((RING_J1[0], RING_J1[1]), (RING_J1[0], JUMPER_FOLD_Y)):
        dx, dy = t[0] - f[0], t[1] - f[1]
        n = hypot(dx, dy)
        ux, uy = dx / n, dy / n
        c = radial_prism(((f[0] + t[0]) / 2, (f[1] + t[1]) / 2), (-uy, ux), prof, n + w)
        out = c if out is None else out + c
    return out


def mount_bosses():
    """Bosses for the board standoffs, from the standoffs' face up into the insert."""
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


def bore():
    """The pass-through's straight bore (D-74), from below the underside up to the flat slot."""
    _, e, _ = pass_points()
    return rod(pass_at(Z_BOT - PASS_BELOW), e, PASS_D)


def pass_through():
    """The single 5 V cable hole (D-74): one straight bore from the insert's underside in the top-right corner, past the
    remote pocket, to a flat slot out through the collar; its lower part opens through the corner taper as a groove."""
    _, e, f = pass_points()
    leg = bore()
    from common import radial_prism
    w, h, _ = PASS_SLOT
    z0, z1 = PASS_TOP_Z - h / 2, PASS_TOP_Z + h / 2
    ux, uy = PASS_DIR
    n = (-uy, ux)                                          # across the slot
    length = hypot(f[0] - e[0], f[1] - e[1]) + w / 2
    # cross-section in the plane across the slot: flat floor, 45 deg peaked roof (prints without a bridge)
    prof = [(-w / 2, z0), (w / 2, z0), (w / 2, z1), (0.0, z1 + w / 2), (-w / 2, z1)]
    mid = ((e[0] + f[0]) / 2 + ux * w / 4, (e[1] + f[1]) / 2 + uy * w / 4)
    slot = radial_prism(mid, n, prof, length)
    return leg + slot


if __name__ == "__main__":
    from pathlib import Path
    from build123d import export_step, export_stl
    out = Path(__file__).resolve().parents[2] / "build"
    out.mkdir(exist_ok=True)
    for name, plain in (("insert", False), ("insert_plain", True)):
        p = build(plain)
        bb = p.bounding_box()
        print(f"{name} bbox x {bb.min.X:.1f}..{bb.max.X:.1f} y {bb.min.Y:.1f}..{bb.max.Y:.1f} z {bb.min.Z:.1f}..{bb.max.Z:.1f}"
              f"  vol {p.volume/1000:.1f} cm3 valid={p.is_valid} solids={len(p.solids())}")
        export_step(p, str(out / f"{name}.step"))
        export_stl(p, str(out / f"{name}.stl"), tolerance=0.02, angular_tolerance=0.1)
