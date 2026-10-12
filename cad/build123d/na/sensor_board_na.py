"""SENSOR BOARD (D-50, D-68): one FR4 board round the barrier's collar, against the wall, under the face plate.

It carries the MSR-2 on CN2 and three SMT spacers under its board, the SHT40 in its vented bay, the top-port PDM
microphone with the ADAU7002 that turns its PDM into I2S for the MSR-2 (D-83), and J1, where the 5 V FFC from the wiring
board latches. Front-layer
copper keeps SB_KEEP along the wall plus the board's edge from the box opening; back-layer copper SB_KEEP.
Held on the barrier by crush ribs on the collar's outside; in the box the flange's land clamps its inner edge.

Also here: the pin board with the battery-free remote's two spring pins, on two SMT spacer posts from the wiring
board's 5 V area, in a pocket under the pocket floor.
Run:  python sensor_board_na.py  -> ../../build/ring_parts.step
"""
from build123d import Box, Cylinder, Pos
from params_na import *
from common import rr, slab


def board():
    out = Pos(0, (SB_Y[0] + SB_Y[1]) / 2, 0) * slab(rr(2 * SB_HALF_W, SB_Y[1] - SB_Y[0], SB_R), 0, SB_T)
    out -= slab(rr(*SB_INNER), -1, SB_T + 1)
    for s in (-1, 1):                                       # the barrier's screw bosses stand through it to the wall
        out -= Pos(0, s * SCREW_PITCH / 2, SB_T / 2) * Cylinder(BOSS_R + 0.3, SB_T + 1)
    for x, y in MSR_SPACERS:
        out -= Pos(x, y, SB_T / 2) * Cylinder(MSR_NUT_HOLE / 2, SB_T + 1)
    for x0, x1, y0 in MSR_SW_CUTS:                          # notches under the MSR-2's back switches
        y1 = SB_Y[1] + 1
        out -= Pos((x0 + x1) / 2, (y0 + y1) / 2, SB_T / 2) * Box(x1 - x0, y1 - y0, SB_T + 1)
    return out


def keepout(layer="front"):
    """Where copper may not go: closer than SB_KEEP to the box opening's edge along the wall (front layer: less the
    board's edge, SB_T). Drawn as a film on the board's face."""
    k = SB_KEEP - (SB_T if layer == "front" else 0.0)
    z = SB_T if layer == "front" else 0.0
    band = slab(rr(BOX_W + 2 * k, BOX_H + 2 * k, k), z - 0.02, z + 0.02)
    return band & board()


def spacers():
    """SMT spacers under the MSR-2's board, below the face plate's posts (D-68)."""
    out = None
    for x, y in MSR_SPACERS:
        n = Pos(x, y, SB_T + MSR_NUT[1] / 2) * (Cylinder(MSR_NUT[0] / 2, MSR_NUT[1]) - Cylinder(1.0, MSR_NUT[1] + 1))
        out = n if out is None else out + n
    return out


def small():
    """Passives on the sensor board (SB_SMALL)."""
    out = None
    for (x, y), (w, h, t) in SB_SMALL.values():
        b = Pos(x, y, SB_T + t / 2) * Box(w, h, t)
        out = b if out is None else out + b
    return out


def cn2():
    return Pos(MSR_CN2_X, MSR_Y, SB_T + B2B_STACK / 2) * Box(B2B[0], B2B[1], B2B_STACK)


def msr():
    """The MSR-2 with the CO2 add-on (msr2.py) on CN2."""
    import msr2
    return msr2.placed(0, MSR_Y, MSR_BACK_Z)


def j1():
    """FH12-6S for the 5 V FFC, cable in from -y."""
    return Pos(*SB_J1, SB_T + FH12[2] / 2) * Box(*FH12)


def sht45():
    return Pos(*SHT_AT, SB_T + SHT_CHIP[2] / 2) * Box(*SHT_CHIP)


def mic():
    """Top-port microphone on the sensor board's front, port end up, port under MIC_AT (D-83)."""
    return Pos(MIC_AT[0], MIC_BODY_Y, SB_T + MIC[2] / 2) * Box(*MIC)


def pin_board():
    """Pin board, the two spring pins at their working height (tips on the cover flex's pads), the two spacer posts with
    their sleeves down to the mains board, the M2 screws holding the pin board on the posts."""
    w, h, t = PB
    brd = Pos(*PB_C, PB_TOP - t / 2) * Box(w, h, t)
    from common import pogo
    pins = None
    for x, y in BC_FINGERS:
        pn = pogo(x, y, PB_TOP, PIN_TIP_Z, PIN_FLANGE, PIN_BARREL, PIN_PLUNGER_D)      # compressed to the pads
        pins = pn if pins is None else pins + pn
    posts, sleeves, screws = None, None, None
    d, wall = POST_SP
    hd, hk = M2_HEAD
    z0, z1 = MB_FRONT_Z, PB_BOT
    for x, y in POSTS:
        c = Pos(x, y, (z0 + z1) / 2) * Cylinder(d / 2, z1 - z0)
        sl = Pos(x, y, (z0 + 1.0 + z1 - 0.5) / 2) * (Cylinder(d / 2 + wall, z1 - z0 - 1.5) - Cylinder(d / 2, z1 - z0))
        sc = Pos(x, y, PB_TOP + hk / 2) * Cylinder(hd / 2, hk)
        sc += Pos(x, y, PB_TOP - PB_SCREW_L / 2) * Cylinder(1.0, PB_SCREW_L)
        posts = c if posts is None else posts + c
        sleeves = sl if sleeves is None else sleeves + sl
        screws = sc if screws is None else screws + sc
    return brd, pins, posts, sleeves, screws


def pin_holes():
    """Holes through the pocket floor: flange size over the flange, barrel size up to the barrel top, plunger size
    above it (when the barrel ends under the floor), PIN_RADIAL round each."""
    barrel, plunger = PIN_BARREL[0], PIN_PLUNGER_D
    zb = PB_TOP + PIN_BARREL[1]                          # barrel top
    out = None
    for x, y in BC_FINGERS:
        z1 = max(zb + 0.2, SEAT_Z + 1)
        h = Pos(x, y, (Z_BOT - 1 + z1) / 2) * Cylinder(barrel / 2 + PIN_RADIAL, z1 - Z_BOT + 1)
        zf = PB_TOP + PIN_FLANGE[1] + PIN_RADIAL                                  # round the flange
        h += Pos(x, y, (Z_BOT - 1 + zf) / 2) * Cylinder(PIN_FLANGE[0] / 2 + PIN_RADIAL, zf - Z_BOT + 1)
        if z1 < SEAT_Z + 1:
            h += Pos(x, y, (z1 + SEAT_Z + 1) / 2) * Cylinder(plunger / 2 + PIN_RADIAL, SEAT_Z + 1 - z1)
        out = h if out is None else out + h
    return out


def pin_board_pocket():
    """Pocket in the barrier's underside for the pin board, with a recess over each screw head."""
    w, h, t = PB
    c = PB_CLR
    z1 = PB_TOP + c
    out = Pos(*PB_C, (Z_BOT - 1 + z1) / 2) * Box(w + 2 * c, h + 2 * c, z1 - Z_BOT + 1)
    hd, hk = M2_HEAD
    for x, y in POSTS:
        out += Pos(x, y, PB_TOP + (hk + c) / 2 - 0.01) * Cylinder(hd / 2 + c, hk + c + 0.02)
    return out


def _pin_board_clip_frames():
    """(edge point (x, y), outward normal (nx, ny), tangent (tx, ty)) for each clip on the pin board's edges."""
    w, h, _ = PB
    cx, cy = PB_C
    out = []
    for edge, s in PB_CLIPS:
        if edge == "top":
            out.append(((cx + s, cy + h / 2), (0, 1), (1, 0)))
        else:
            sx = -1 if edge == "left" else 1
            out.append(((cx + sx * w / 2, cy + s), (sx, 0), (0, 1)))
    return out


def pin_board_clips():
    """Snap clips holding the pin board up against the pins' push (D-91): (relief cut, hooks). Each finger is the pocket's
    wall, freed by a relief slot all round it (in front: above the pocket's ceiling) from the barrier's underside up to
    POCKET_WALL under the seat, and below its tip; its hook stands in under the pin board's back face (catch PB_CLIP_PLAY below it) with a 45 deg
    ramp underneath, so the pin board snaps in from behind with the mains board."""
    from build123d import Plane, Polyline, extrude, make_face
    fw, ft, hd, g = PB_CLIP
    c = PB_CLR
    z_root = SEAT_Z - POCKET_WALL
    z_catch = PB_BOT - PB_CLIP_PLAY
    z_tip = z_catch - 0.2 - (c + hd)                       # 0.2 flat face, then the 45 deg ramp back to the wall
    zb = Z_BOT - 1
    relief, hooks = None, None
    for (ex, ey), (nx, ny), (tx, ty) in _pin_board_clip_frames():
        def box(n0, n1, t0, t1, z0, z1):
            cn, ct = (n0 + n1) / 2, (t0 + t1) / 2
            sn, st = n1 - n0, t1 - t0
            return Pos(ex + nx * cn + tx * ct, ey + ny * cn + ty * ct, (z0 + z1) / 2) * \
                Box(abs(nx) * sn + abs(tx) * st, abs(ny) * sn + abs(ty) * st, z1 - z0)
        r = box(c - g, c + ft + g, -fw / 2 - g, fw / 2 + g, zb, z_root) - box(c, c + ft, -fw / 2, fw / 2, z_tip, z_root + 1)
        relief = r if relief is None else relief + r
        pl = Plane(origin=(ex, ey, 0), x_dir=(nx, ny, 0), z_dir=(ny, -nx, 0))      # profile in the (n, z) plane, y up
        prof = [(c + 0.01, z_catch), (-hd, z_catch), (-hd, z_catch - 0.2), (c + 0.01, z_tip)]
        k = extrude(pl * make_face(Polyline(*prof, prof[0])), fw / 2, both=True)
        hooks = k if hooks is None else hooks + k
    return relief, hooks


def parts():
    brd, pins, posts, sleeves, screws = pin_board()
    return {"sensor_board": board(), "keep": keepout(), "spacers": spacers(), "cn2": cn2(), "msr": msr(), "j1": j1(),
            "sht45": sht45(), "passives": small(), "mic": mic(), "pin_board": brd, "pins": pins, "posts": posts,
            "sleeves": sleeves, "screws": screws}


if __name__ == "__main__":
    from pathlib import Path
    from build123d import Compound, export_step
    out = Path(__file__).resolve().parents[3] / "build" / "na"
    out.mkdir(parents=True, exist_ok=True)
    ps = parts()
    for k, v in ps.items():
        print(k, round(v.volume, 2), v.is_valid)
    export_step(Compound([v for k, v in ps.items() if k != "keep"]), str(out / "sensor_board_parts.step"))
