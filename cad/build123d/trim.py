"""TRIM PLATE - face, MSR-2 bay (radar skin), SHT45 bay, vents, microphone sound hole.

Low-voltage side only: it carries no barrier duty. Any filament (PETG/ASA).
Print: face down (the exported print STL is already flipped), no supports.
Run:  python trim.py  -> ../../build/trim.step / .stl
"""
from math import radians, tan
from build123d import Box, Cylinder, Cone, Rectangle, Pos, Axis, chamfer
from params import *
from common import rr, slab, frame
import insert


def msr_hooks():
    """Snap hooks holding the MSR-2 board in its bay (D-45): at the board's short ends, from the radar skin."""
    from common import board_hooks
    return board_hooks(MSR_Y, MSR_BOARD[0], MSR_BACK_Z, PT - RADAR_WALL, MSR[0] / 2 + CLR, MSR_HOOK)


def band_groove():
    """Groove in the skin's underside over the flange's right band: the sensor flex lies on the flange top."""
    import sensor_flex as sf
    x0, x1 = FLEX_RIGHT - FLEX_RUN_W - 0.15, FLEX_RIGHT + 0.15
    y = sf.Y_CLIMB + 1.0
    return Pos((x0 + x1) / 2, 0, SKIN_Z + FLEX_GROOVE / 2 - 0.005) * Box(x1 - x0, 2 * y, FLEX_GROOVE + 0.01)


def flex_ramp():
    """Ramp over the sensor flex's rise from the MSR-2 bay to the corner fold, down from the skin."""
    from common import ramp_over
    x1 = FLEX_X - FLEX_W / 2 - 0.3                       # stops short of the corner fold
    z1 = FLEX_Z_LO + (FLEX_Z_HI - FLEX_Z_LO) * (x1 - FLEX_EXIT_X) / (FLEX_X - FLEX_EXIT_X)
    return ramp_over((FLEX_EXIT_X, MSR_Y, FLEX_Z_LO), (x1, MSR_Y, z1), FLEX_W + 1.0, SFLEX_T, SKIN_Z + 0.01)


def tongue_tab():
    """Battery-free tongue (D-49): tab in the insert's island notch, flush with the face, down to the deck, and the
    strip down the pocket's top arc in the insert's groove (flush above the groove's end, in front of the wall
    below it, 45 deg between), the tongue behind both; the floor insert snaps onto the strip's foot."""
    from common import bar, radial_prism
    p, u, q = tongue_arc()
    w = BC_NA_TAB_W
    y1 = ISLAND[1] / 2 + SPLIT_CLR + 0.5
    q2 = (q[0] + w / 2 * u[0], q[1] + w / 2 * u[1])
    tab = bar((q[0], y1), q, w, DECK_Z, PT, w / 2) + bar(q2, p, w, DECK_Z, PT)
    t, room = BC_NA_STRIP[1], BC_NA_TROOM
    gb = BC_NA_GROOVE_BOT
    zf = SEAT_Z + BC_FLOOR_T + 0.1                          # foot, just above the floor insert
    strip = radial_prism(p, u, [(0.0, DECK_Z + 0.01), (0.0, gb + t + room), (-(t + room), gb), (-(t + room), zf),
                                (-room, zf), (-room, gb), (t, gb + t + room), (t, DECK_Z + 0.01)], BC_NA_STRIP[0])
    reach, hh, (w0, w1) = BC_NA_FOOT_HOOK
    fl = SEAT_Z + BC_FLOOR_T
    r0 = -(t + room)
    z1 = fl + w1 - 0.1                                       # hook's top under the window's top edge
    z0 = fl + w0 + reach + 0.05                              # the lead-in starts inside the window
    hook = radial_prism(p, u, [(r0 + 0.01, z0 - reach), (r0 - reach, z0), (r0 - reach, z1), (r0 + 0.01, z1)],
                        BC_NA_STRIP[0] - 2.0)
    return tab + strip + hook


def tongue_groove():
    """Groove in the skin's underside for the tongue: the band from the finger section to the fold, then down the
    plate over the flange to the island window, deeper at the fold (two layers); and in the tab's underside."""
    from common import bar
    p, u, q = tongue_arc()
    gw, gd, gf = BC_NA_TGROOVE
    y1 = ISLAND[1] / 2 + SPLIT_CLR
    out = bar((FINGER_SEC_IN + 0.5, BC_NA_BAND_Y), (q[0], BC_NA_BAND_Y), gw, SKIN_Z - 0.01, SKIN_Z + gd, gw / 2)
    out += bar((q[0], BC_NA_BAND_Y), (q[0], y1 - 0.5), gw, SKIN_Z - 0.01, SKIN_Z + gd, gw / 2)
    out += bar((q[0], BC_NA_BAND_Y + gw / 2), (q[0], BC_NA_BAND_Y - gw / 2), gw, SKIN_Z - 0.01, SKIN_Z + gf, 0.2)
    r_up = BC_NA_STRIP[1]
    out += bar((q[0], y1 + 0.5), q, gw, DECK_Z - 0.01, DECK_Z + gd, gw / 2)
    out += bar(q, (p[0] + r_up * u[0], p[1] + r_up * u[1]), gw, DECK_Z - 0.01, DECK_Z + gd)
    return out


def build():
    shell = Pos(0, PLATE_Y, 0) * slab(rr(PW, PH, PR), 0, PT)
    shell = chamfer(shell.edges().group_by(Axis.Z)[-1], FACE_CHAMFER)
    shell -= Pos(0, PLATE_Y, 0) * slab(rr(PW - 2 * SKIN, PH - 2 * SKIN, PR - SKIN), -1, PT - SKIN)
    body = shell
    # MSR-2 and SHT45 bay frames
    body += frame(MSR[0] + 2 * CLR, MSR[1] + 2 * CLR, 1.6, 1, 0, PT, MSR_Y)
    body += frame(SHT[0] + 0.8, SHT[1] + 0.8, 1.6, 0.5, 0, PT, SHT_Y)
    hooks, reliefs = msr_hooks()

    # ---------------- cuts ----------------
    # clearance envelope of the insert: island window through the face, flange underneath
    body -= slab(rr(ISLAND[0] + 2 * SPLIT_CLR, ISLAND[1] + 2 * SPLIT_CLR, ISLAND_R + SPLIT_CLR), DECK_Z - 1, PT + 1)
    fl = slab(rr(FLANGE_OUT[0] + 2 * SPLIT_CLR, FLANGE_OUT[1] + 2 * SPLIT_CLR, ISLAND_R + FLANGE + SPLIT_CLR), -1, DECK_Z)
    for s in (-1, 1):
        fl += Pos(0, s * SCREW_PITCH / 2, DECK_Z / 2) * Cylinder(BOSS_R + SPLIT_CLR, DECK_Z + 2)
    body -= fl
    for kx, ky in KEY_POS:  # sockets for the insert's locating pins
        body -= Pos(kx, ky, DECK_Z + (KEY_H + 0.2) / 2 - 0.01) * Cylinder(KEY_D / 2 + KEY_CLR, KEY_H + 0.2)
    for s in (-1, 1):  # countersunk #6 holes, clamp trim + insert to the box ears
        y = s * SCREW_PITCH / 2
        body -= Pos(0, y, PT / 2) * Cylinder(SCREW_D / 2, PT + 2)
        d = (SCREW_HEAD_D - SCREW_D) / 2 / tan(radians(SCREW_CSK / 2))   # countersink depth
        body -= Pos(0, y, PT - d / 2 + 0.005) * Cone(SCREW_D / 2, SCREW_HEAD_D / 2 + 0.01, d + 0.01)
    body -= Pos(0, MSR_Y, 0) * slab(rr(MSR[0] + 2 * CLR, MSR[1] + 2 * CLR, 1), -0.01, PT - RADAR_WALL)
    body -= Pos(LUX_POS[0], MSR_Y + LUX_POS[1], PT - 0.5) * Cylinder(1.5, 6)
    for i in range(-2, 3):  # MSR vents, top edge
        body -= Pos(i * 7 + 1.5, PLATE_Y + PH / 2 - SKIN + 2, 6) * Box(3, 6, 6)
    body -= Pos(0, SHT_Y, 0) * slab(rr(SHT[0] + 0.8, SHT[1] + 0.8, 0.5), -0.01, PT - SKIN)
    # sensor flex (D-27, D-47) passes the bay frames: MSR-2 frame (right wall, at the wall plane) and the
    # SHT45 frame (right wall, just under the skin)
    nx = MSR[0] / 2 + CLR + 1.0                    # notch centre (room x), 4 mm long
    w = 2 * flex_half_width(nx - 2.0 - MSR_CN2_X) + 0.6
    body -= Pos(nx, MSR_Y, 0.45) * Box(4.0, w, 0.92)
    w = FLEX_RUN_W + 0.6
    body -= Pos(SHT[0] / 2 + 0.4 + 0.8, SHT_Y, (SKIN_Z + 9.4) / 2) * Box(3.0, w, SKIN_Z - 9.4 + 0.01)
    body -= band_groove()
    body -= Pos(*MIC_PORT, PT - SKIN / 2) * Cylinder(MIC_SKIN_HOLE_D / 2, SKIN + 1)   # microphone sound hole (D-29)
    body = body - reliefs + hooks                       # MSR-2 snap hooks (D-45)
    body += tongue_tab()                                # island notch, strip down the arc (D-49)
    body -= tongue_groove()
    body += flex_ramp()                                 # the flex's rise from CN2 is taped to it
    for i in (-1, 0, 1):  # SHT vents: face + bottom edge
        body -= Pos(i * 4, SHT_Y, PT - 1) * Box(2, 6, 4)
        body -= Pos(i * 4, PLATE_Y - PH / 2 + 4, 5) * Box(2, 10, 6)
    return body


if __name__ == "__main__":
    from pathlib import Path
    from build123d import export_step, export_stl
    out = Path(__file__).resolve().parents[2] / "build"
    out.mkdir(exist_ok=True)
    p = build()
    bb = p.bounding_box()
    print(f"trim bbox x {bb.min.X:.1f}..{bb.max.X:.1f} y {bb.min.Y:.1f}..{bb.max.Y:.1f} z {bb.min.Z:.1f}..{bb.max.Z:.1f}"
          f"  vol {p.volume/1000:.1f} cm3 valid={p.is_valid} solids={len(p.solids())}")
    export_step(p, str(out / "trim.step"))
    export_stl(p, str(out / "trim.stl"), tolerance=0.02, angular_tolerance=0.1)
