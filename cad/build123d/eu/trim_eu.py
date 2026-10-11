"""EU TRIM PLATE (D-30, D-56): a passive cover: face, remote pocket walls (standing on the cap), finger scoops both sides (D-73),
MSR-2 bay (radar skin, vents over the CO2 sensor, posts onto the MSR-2's board) above, SHT45 bay below, the microphone's sound hole and tube. No electronics and no contacts:
the sensors sit on the cap board (capboard_eu.py). Four snap fingers at the corners catch grooves in the carrier's
windows (D-70, D-77). Low-voltage side only; any filament (PETG/ASA). Print face-down, no supports.
Run:  python trim_eu.py  -> ../../../build/eu/trim.step / .stl
"""
from math import sqrt
from build123d import Axis, Box, Cylinder, Ellipse, Plane, Pos, chamfer, loft
from params_eu import *
from common import rr, stadium, slab, frame
import msr2


def snaps():
    """Snap fingers (D-70, D-77): from the face skin down into closed windows in the cap board and the carrier at the
    corners, outside the pocket walls; the bump on each outer face catches the groove in its window's outer wall."""
    from math import cos, radians, sin
    from build123d import Rot
    from common import radial_prism
    t = SNAP[1]
    z0, z1 = SNAP_GROOVE
    zm, d = (z0 + z1) / 2, SNAP[2] - SNAP_BUMP_CLR        # bump just short of the groove's depth, 45 deg flanks
    out = None
    for a, w in SNAPS:
        u = (cos(radians(a)), sin(radians(a)))
        r = SNAP_R + t / 2
        f = Pos(u[0] * r, u[1] * r, (SNAP_TIP_Z + DECK_Z + 0.01) / 2) * Rot(0, 0, a) * Box(t, w, DECK_Z + 0.01 - SNAP_TIP_Z)
        ro = SNAP_R + t                                     # outer face: the bump catches the carrier's groove
        f += radial_prism((u[0] * ro, u[1] * ro), u, [(-0.01, zm - d), (d, zm), (-0.01, zm + d)], w)
        out = f if out is None else out + f
    return out


def scoop_sections():
    """(depth below the ellipsoid's centre, x half-width, y half-width) from 1 mm above the face down to the flat bottom:
    each half-width follows the ellipsoid while its wall is steeper than 45 deg, then shrinks at 45 deg (D-73)."""
    a0, b0, c = SCOOP_EU
    ua, ub = c * c / sqrt(a0 * a0 + c * c), c * c / sqrt(b0 * b0 + c * c)   # depths where the x / y walls reach 45 deg

    def half(r, u45, u):
        s = lambda v: r * sqrt(max(0.0, 1 - (v / c) ** 2))
        return s(u) if u <= u45 else s(u45) - (u - u45)

    out, u = [], SCOOP_RISE - 1.0
    while True:
        a, b = half(a0, ua, u), half(b0, ub, u)
        if a <= SCOOP_FLAT / 2:
            u_end = u - (SCOOP_FLAT / 2 - a)
            out.append((u_end, SCOOP_FLAT / 2, b + (u - u_end)))
            return out
        out.append((u, a, b))
        u += SCOOP_STEP


def scoop(sx, grow=0.0):
    """Finger scoop beside the pocket (grow > 0: the solid round it, extended `grow` below the bottom)."""
    zc = PT + SCOOP_RISE
    secs = scoop_sections()
    if grow:
        u, a, b = secs[-1]
        secs = secs + [(u + grow, a, b)]
    faces = [Plane.XY.offset(zc - u) * Ellipse(a + grow, b + grow) for u, a, b in secs]
    return Pos(sx * SCOOP_X_EU, 0, 0) * loft(faces)


def scoop_block(sx):
    """Solid trim round a scoop, up to the face."""
    pc = Pos(PC[0], PC[1], 0)
    return scoop(sx, SCOOP_WALL) & (pc * slab(rr(PW, PH, PR), 0, PT))


def mic_tube():
    """Sound tube from the skin down to a gasket on the mic carrier (on the cap board)."""
    od, bore, gasket = MIC_TUBE
    z0 = CB_TOP + MIC_CARRIER[2] + gasket
    return Pos(*MIC_AT, (z0 + SKIN_Z + 0.01) / 2) * (Cylinder(od / 2, SKIN_Z + 0.01 - z0) - Cylinder(bore / 2, PT))


def build():
    pc = Pos(PC[0], PC[1], 0)
    shell = pc * slab(rr(PW, PH, PR), 0, PT)
    shell = chamfer(shell.edges().group_by(Axis.Z)[-1], FACE_CHAMFER)
    shell -= pc * slab(rr(PW - 2 * SKIN, PH - 2 * SKIN, PR - SKIN), -1, DECK_Z)
    body = shell
    body += slab(stadium(*POCKET_OUT), CAP_T, PT)                                   # pocket walls
    for sx in (-1, 1):
        body += scoop_block(sx)
    z0 = CB_TOP + SPLIT_CLR                                                          # bay frames down to the cap board
    body += Pos(0, MSR_Y, 0) * frame(MSR_FRAME[0], MSR_FRAME[1], MSR_FRAME[2], MSR_BAY_R, z0, PT)
    sb = (SHT[0] + 2 * SHT_BAY_CLR, SHT[1] + 2 * SHT_BAY_CLR)
    body += Pos(0, SHT_Y, 0) * frame(*sb, BAY_WALL, SHT_BAY_R, z0, PT)
    body += mic_tube()
    # ---------------- cuts ----------------
    body -= slab(stadium(*POCKET_IN), CAP_T, PT + 1)                               # remote pocket
    for sx in (-1, 1):                                                               # finger scoops
        body -= scoop(sx)
    body += snaps()
    body -= Pos(0, MSR_Y, 0) * slab(rr(MSR_FRAME[0], MSR_FRAME[1], MSR_BAY_R), -0.01, PT - RADAR_WALL)
    body += msr2.posts(0, MSR_Y, MSR_BACK_Z, PT - RADAR_WALL)        # in the hollowed bay: clamp the MSR-2's board (D-67)
    body -= msr2.scd_vents(0, MSR_Y, PT, RADAR_WALL)      # grille: CO2 sensor and light sensor (D-65, D-69)
    zt, zb, h = EU_VENT_Z
    n, pitch, dx, w, d = MSR_VENTS
    for i in range(n):                                                               # MSR-2 vents, top edge
        body -= Pos((i - (n - 1) / 2) * pitch + dx, PL_Y[1] - SKIN + d / 2 - 1, zt) * Box(w, d, h)
    body -= Pos(0, SHT_Y, 0) * slab(rr(*sb, SHT_BAY_R), -0.01, PT - SKIN)
    # microphone sound hole over the tube
    hd, web, rd = MIC_HOLE_EU                               # sound hole through a thin web, recess from the face (D-52)
    body -= Pos(*MIC_AT, PT - SKIN / 2) * Cylinder(hd / 2, SKIN + 1)
    body -= Pos(*MIC_AT, PT - (SKIN - web) / 2 + 0.005) * Cylinder(rd / 2, SKIN - web + 0.01)
    n, pitch, w, lf, de = SHT_VENTS
    for i in range(n):                                                               # SHT45 vents: face + bottom edge
        x = (i - (n - 1) / 2) * pitch
        body -= Pos(x, SHT_Y, PT - SKIN / 2) * Box(w, lf, SKIN + 2)
        body -= Pos(x, PL_Y[0] + de / 2 - 1, zb) * Box(w, de, h)
    return body


if __name__ == "__main__":
    from pathlib import Path
    from build123d import export_step, export_stl
    out = Path(__file__).resolve().parents[3] / "build" / "eu"
    out.mkdir(parents=True, exist_ok=True)
    p = build()
    bb = p.bounding_box()
    print(f"trim bbox x {bb.min.X:.1f}..{bb.max.X:.1f} y {bb.min.Y:.1f}..{bb.max.Y:.1f} z {bb.min.Z:.1f}..{bb.max.Z:.1f}"
          f"  vol {p.volume/1000:.1f} cm3 valid={p.is_valid} solids={len(p.solids())}")
    export_step(p, str(out / "trim.step"))
    export_stl(p, str(out / "trim.stl"), tolerance=0.02, angular_tolerance=0.1)
