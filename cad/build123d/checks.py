"""Geometry sanity checks (run by `make check`). Every assert is a constraint.

Barrier test: air = (box cavity + space in front of the wall) - insert, with the
single 5 V pass-through plugged. The air volume touching the back of the box
(mains) must not reach the room or the trim's low-voltage hollow.
"""
import sys
import numpy as np
from build123d import Box, Pos, Rectangle, Vector
from params import *
from common import slab, rr, stadium
import insert
import trim

FAILS = []


def check(cond, msg):
    print(("  ok   " if cond else "  FAIL ") + msg)
    if not cond:
        FAILS.append(msg)


def dims():
    print("dimensions")
    from math import radians, tan
    d = (SCREW_HEAD_D - SCREW_D) / 2 / tan(radians(SCREW_CSK / 2))
    check(SCREW_CSK == 82.0 and 3.5 < SCREW_D <= 3.7 and 6.65 <= SCREW_HEAD_D <= 7.0 and d <= SKIN,
          f"#6 screws: {SCREW_D} hole, {SCREW_CSK:.0f} deg countersink {SCREW_HEAD_D} across, {d:.2f} deep in the "
          f"{SKIN} skin (heads 6.05-6.65, ASME B18.6.3)")
    check(POCKET_OUT[0] <= PLUG[0] and POCKET_OUT[1] <= PLUG[1], f"pocket {POCKET_OUT[0]:.1f}x{POCKET_OUT[1]:.1f} inside plug {PLUG[0]:.1f}x{PLUG[1]:.1f}")
    check(WB[0] / 2 <= PLUG[0] / 2 and WB[1] / 2 + abs(WB_Y) <= PLUG[1] / 2,
          f"wiring board {WB[0]} x {WB[1]} fits the box opening less clearance")
    check(FLANGE_OUT[0] >= SEAL[0] and FLANGE_OUT[1] >= SEAL[1], "flange covers the seal band on the wall")
    top = SEAT_Z - (WELL_FLOOR_Z + SW_ROCKER_H + SW_ROCKER_TOL)
    check(top >= SW_ROCKER_CLR - 1e-6, f"rocker top clears the remote's back by {top:.1f} mm at max tolerance")
    check(SW_BEZEL[0] <= WELL_IN[0] and SW_BEZEL[1] <= WELL_IN[1], "rocker flange fits the switch well")
    m = _well_margin()
    check(m >= 0.5, f"switch well inside the pocket footprint (corner margin {m:.1f} mm, no undercut)")
    alt = SEAT_Z - (WELL_FLOOR_Z + SW_ALT_ROCKER_H)
    print(f"       second-source rocker (E-Switch RA4, D-88): top {alt:.1f} mm under the remote's back (nominal)")
    pin_y = min(SW_Y, SW_Y + SW_SW_DIR * SW_SLOT_DY) - SW_PAD[1] / 2
    check(pin_y >= WB_Y + WAGO_Y + WAGO6[1] / 2, f"rocker slots (pad edge y {pin_y:.1f}) clear of the terminal block")
    check(PASS_E[0] * J2_POS[0] > 0, "5 V pass-through is on the same side as the 5 V connector")
    stack = RING_T + B2B_STACK + MSR[2] + MSR_SKIN_GAP + RADAR_WALL
    check(abs(PT - stack) < 1e-6, f"plate {PT} mm = ring board {RING_T} + CN2 stack {B2B_STACK} + MSR-2 {MSR[2]} + gap "
                                  f"{MSR_SKIN_GAP} + radar skin {RADAR_WALL} (D-51, D-66; MSR[2] and B2B_STACK MEASURE)")
    mag_floor = SEAT_Z - MAGNET[2] - MAGNET_SETBACK
    check(Z_BOT <= mag_floor - SEAT_T + 1e-6, "floor >= SEAT_T under the magnet recess")
    pad = (B_W - 2 * B_BACK_RUN, B_H - 2 * B_BACK_RUN)
    mag_top = MAGNET_REC_Y + MAGNET[1] / 2 + MAGNET_CLR
    check(MAGNET[0] + 2 * MAGNET_CLR <= pad[0] and mag_top <= pad[1] / 2 and MAGNET_SLOT_BOT >= -pad[1] / 2
          and MAGNET_SLOT_BOT <= MAGNET_REC_Y - MAGNET[1] / 2 - MAGNET_CLR,
          f"magnet recess lies under the remote's flat back ({pad[0]:.0f} x {pad[1]:.0f})")
    check(mag_top - MAGNET_SLOT_BOT >= MAGNET_END_R + MAGNET_CLR and MAGNET_END_R <= MAGNET[0] / 2,
          f"magnet recess {mag_top - MAGNET_SLOT_BOT:.1f} mm long holds the rounded end (R {MAGNET_END_R})")
    well_y0 = SW_Y - WELL_IN[1] / 2
    check(MAGNET_REC_Y + MAGNET[1] / 2 + MAGNET_CLR + SEAT_T <= well_y0, "magnet recess clear of the switch well")
    p0, p1 = MAGNET_Y - BC_STEEL[1] / 2, MAGNET_Y + BC_STEEL[1] / 2
    m0, m1 = MAGNET_REC_Y - MAGNET[1] / 2, MAGNET_REC_Y + MAGNET[1] / 2
    for name, (a, b) in (("the remote's own steel plate", (p0, p1)),
                         ("the back cover's steel plate", (BC_STEEL_Y - BC_STEEL[1] / 2, BC_STEEL_Y + BC_STEEL[1] / 2))):
        share = max(0.0, min(b, m1) - max(a, m0)) / MAGNET[1]
        check(share >= 0.75, f"magnet piece ({m0:.1f}..{m1:.1f}) {share * 100:.0f} % under {name} ({a:.1f}..{b:.1f})")
    check(MAGNET[1] >= MAGNET_END_R + 1.0 and MAGNET[1] <= MAGNET_FULL[1] - MAGNET_END_R,
          f"magnet piece {MAGNET[1]} mm cut from the {MAGNET_FULL[1]} mm magnet keeps one round end")
    check(min(POCKET_WALL, BARRIER_MIN) >= V0_RATED_T, f"barrier walls >= V-0 rated thickness {V0_RATED_T} (fill V0_RATED_T from the datasheet)")
    msr_top = MSR_Y + MSR[1] / 2 + CLR
    check(msr_top <= PLATE_Y + PH / 2 - SKIN, f"MSR-2 bay top {msr_top:.2f} inside trim (<= {PLATE_Y + PH/2-SKIN})")
    check(SHT_AT[1] - SHT[1] / 2 - 0.4 >= PLATE_Y - PH / 2 + SKIN, "SHT45 bay inside trim")
    deepest = min(WB_BACK_Z - WAGO6[2], WB_BACK_Z - IRM[2])
    left = BOX_D + deepest
    print(f"       board {WB_FRONT_Z:.1f}..{WB_BACK_Z:.1f} mm, deepest part {deepest:.1f} mm; "
          f"behind it in a {BOX_D} mm box: {left:.1f} mm, behind the board above the block: {BOX_D + WB_BACK_Z:.1f} mm")
    check(left >= WIRE_SPACE_MIN, f"at least {WIRE_SPACE_MIN} mm behind the terminal block / PSU")


def _behind(c, depth, e, box_c, box_size):
    """Gap from a block's closed back (centre c, depth along entry e) to a box; < 0 = overlap or in front."""
    back = c[0] * e[0] + c[1] * e[1] - depth / 2
    near = box_c[0] * e[0] + box_c[1] * e[1] + abs(e[0]) * box_size[0] / 2 + abs(e[1]) * box_size[1] / 2
    return back - near


def terminal_entry():
    print("terminal block entry vs. PSU")
    e = WAGO_ENTRY
    gap = _behind((WAGO_X, WB_Y + WAGO_Y), WAGO6[1], e, (IRM_C[0], WB_Y + IRM_C[1]), IRM[:2])
    check(gap >= WAGO_PSU_GAP, f"wire entries face {e}, PSU behind the block's closed back (gap {gap:.1f} mm "
          f">= {WAGO_PSU_GAP})")
    import kicad_board
    if not kicad_board.WB_PCB.exists():
        print("       no KiCad board, params only")
        return
    b = kicad_board.Board()
    ke = b.entry_dir("J1")
    check(ke == tuple(float(v) for v in e), f"KiCad J1 entries face {ke}, params WAGO_ENTRY {e}")
    for ref, c, size in (("J1", (WAGO_X, WB_Y + WAGO_Y), WAGO6[:2]), ("PS1", (IRM_C[0], WB_Y + IRM_C[1]), IRM[:2])):
        x0, x1, y0, y1 = b.fab_box(ref)
        kc, ks = ((x0 + x1) / 2, (y0 + y1) / 2), (x1 - x0, y1 - y0)
        if ref == "J1" and abs(ke[0]) > 0:
            ks = ks[::-1]                                   # depth along x when the entries face x
        ok = all(abs(kc[i] - c[i]) < 0.05 and abs(ks[i] - size[i]) < 0.05 for i in (0, 1))
        check(ok, f"KiCad {ref} body {ks[0]:.1f} x {ks[1]:.1f} at ({kc[0]:.2f}, {kc[1]:.2f}) matches params")
    jx0, jx1, jy0, jy1 = b.fab_box("J1")
    px0, px1, py0, py1 = b.fab_box("PS1")
    kgap = _behind(((jx0 + jx1) / 2, (jy0 + jy1) / 2), abs(ke[0]) * (jx1 - jx0) + abs(ke[1]) * (jy1 - jy0), ke,
                   ((px0 + px1) / 2, (py0 + py1) / 2), (px1 - px0, py1 - py0))
    check(kgap >= WAGO_PSU_GAP, f"KiCad: PSU behind J1's closed back (gap {kgap:.1f} mm >= {WAGO_PSU_GAP})")
    sx, sy = b.origin("S1")
    check(abs(sx) < 0.01 and abs(sy - SW_Y) < 0.01, f"KiCad S1 at ({sx:.2f}, {sy:.2f}) matches params SW_Y {SW_Y}")
    pad_body_check(b)


def pad_body_check(b):
    """Pin tails and solder fillets of through-hole pads clear of the part bodies on the other side."""
    gap, pad, body = min(b.pad_body_gaps())
    check(gap >= PAD_BODY_GAP - 1e-6,
          f"KiCad: through-hole pads clear of the bodies on the other side (closest {pad} to {body}: "
          f"{gap:.2f} mm >= {PAD_BODY_GAP})")


def msr2_model():
    """MSR-2 model (msr2.py): inside Apollo's case cavity, its front at the envelope's height, the radar on top."""
    print("MSR-2 model (CO2 version)")
    import msr2
    bb = msr2.model().bounding_box()
    check(bb.size.X <= MSR2_CASE[0] and bb.size.Y <= MSR2_CASE[1],
          f"model {bb.size.X:.2f} x {bb.size.Y:.2f} inside the case cavity {MSR2_CASE[0]} x {MSR2_CASE[1]}")
    check(bb.max.Z <= MSR2_CASE[2] + 1e-6, f"front {bb.max.Z:.2f} mm under the case's face ({MSR2_CASE[2]}) above the "
                                           f"board's back")
    check(abs(bb.max.Z - MSR[2]) < 1e-6, f"envelope height MSR[2] {MSR[2]:.2f} = the model's front")


def scd_vent_checks(tr, msr_y, back_z, pt):
    """Grille through the radar skin (D-65, D-69): open, the middle slot centred on the light sensor, the rest over
    the SCD4x, off the radar; no separate light-sensor hole."""
    print("grille: CO2 sensor and light sensor (D-65, D-69)")
    from build123d import Box
    import msr2
    w, n, pitch, inset = MSR2_SCD_VENT
    lx, ly = LUX_POS[0], msr_y + LUX_POS[1]
    check(w >= MIN_PRINT_HOLE, f"slot width {w} >= {MIN_PRINT_HOLE} (prints open)")
    for i in range(n):
        x = lx + (i - (n - 1) / 2) * pitch
        probe = Pos(x, ly, pt - RADAR_WALL / 2) * Box(w - 0.2, 0.4, RADAR_WALL + 0.2)
        r = probe & tr
        check(r is None or r.volume < 1e-4, f"slot {i + 1} at x {x:.1f} open through the {RADAR_WALL} mm skin")
    v = msr2.scd_vents(0, msr_y, pt, RADAR_WALL)
    mid = [s_ for s_ in v.solids() if abs(s_.center().X - lx) < 1e-3]
    c = mid[0].center() if mid else None
    check(n % 2 == 1 and c is not None and abs(c.Y - ly) < 1e-3, f"middle slot centred on the light sensor at "
                                                                  f"({lx}, {ly - msr_y:.1f}) from the MSR-2's centre")
    sx, sy = msr2.scd_centre()
    scd = Pos(sx, msr_y + sy, pt) * Box(MSR2_SCD[0], MSR2_SCD[1], 10)
    over = v & scd
    a = (over.volume if over else 0.0) / (RADAR_WALL + 1)
    check(a >= 15.0, f"{a:.1f} mm2 of the grille's {v.volume / (RADAR_WALL + 1):.1f} mm2 over the SCD4x (>= 15)")
    bb = v.bounding_box()
    radar_y0 = msr_y + MSR_BOARD[1] / 2 - MSR2_LD[1]
    check(bb.max.Y + VENT_RADAR_CLR <= radar_y0 + 1e-6, f"grille {radar_y0 - bb.max.Y:.2f} mm clear of the radar "
                                                        f"module's outline (>= {VENT_RADAR_CLR}; slots {msr2.vent_length():.1f} long)")
    gap = (pt - RADAR_WALL) - (back_z + MSR_BOARD_T + MSR2_CN1_STACK + MSR2_CO2_BOARD[2] + MSR2_SCD[2])
    check(gap >= -1e-6, f"SCD4x top {gap:.2f} mm under the skin (no interference)")


def msr_posts(tr, msr_y, back_z, pt):
    """Face plate posts (D-66, D-67): each lands on the MSR-2's board inside its outline, clear of its parts; the skin
    stands clear of the MSR-2's front, so the clamp goes through the board, not the CO2 add-on or the radar's pins."""
    print("MSR-2 clamp: face plate posts (D-66, D-67)")
    from build123d import Cylinder
    import msr2
    mp = msr2.placed_parts(0, msr_y, back_z)
    front = back_z + MSR_BOARD_T
    posts = msr2.posts(0, msr_y, back_z, pt - RADAR_WALL)
    r = posts & tr
    check(r is not None and abs(r.volume - posts.volume) < 0.01, "posts are part of the face plate")
    for i, (x, y) in enumerate(MSR2_POSTS):
        r = MSR2_POST_D / 2
        inside = abs(x) + r <= MSR_BOARD[0] / 2 and abs(y) + r <= MSR_BOARD[1] / 2
        check(inside, f"post {i + 1} at ({x}, {y}) on the board's outline")
        foot = Pos(x, msr_y + y, front - 0.05) * Cylinder(r - 0.05, 0.1)
        on = foot & mp["board"]
        a = on.volume / 0.05 if on is not None else 0.0
        check(a >= 0.9 * 3.14159 * (r - 0.05) ** 2, f"post {i + 1} foot on solid board ({a:.2f} mm2; notch and holes clear)")
        grown = Pos(x, msr_y + y, (front + pt) / 2 + 0.01) * Cylinder(r + MSR2_POST_CLR, pt - front)
        hit = [k for k, v in mp.items() if k != "board" and (grown & v) is not None and (grown & v).volume > 1e-5]
        check(not hit, f"post {i + 1} {MSR2_POST_CLR} mm clear of the MSR-2's parts" + (f" (hits {hit})" if hit else ""))
    bb = posts.bounding_box()
    check(abs(bb.min.Z - front) < 1e-6, f"posts end on the board's front (z {bb.min.Z:.2f})")
    skin = pt - RADAR_WALL
    for k in ("scd", "radar"):
        g = skin - mp[k].bounding_box().max.Z
        check(g >= MSR_SKIN_GAP - 1e-6, f"skin {g:.2f} mm clear of the {'SCD4x' if k == 'scd' else 'radar and its pins'}")
    r = tr & (mp["scd"] + mp["radar"] + mp["co2"] + mp["cn1"])
    check(r is None or r.volume < 1e-6, "face plate touches neither the CO2 add-on nor the radar")


def msr_spacers(ins):
    """MSR-2 (D-68): on CN2 and three SMT spacers on the ring board, each under a face plate post; the spacers on
    solid board on both sides, clear of the MSR-2's back parts and CN2's mate."""
    print("MSR-2 support: ring board spacers (D-68)")
    import ring
    import msr2
    from build123d import Cylinder
    rp = ring.parts()
    mp = msr2.placed_parts(0, MSR_Y, MSR_BACK_Z)
    check(abs(RING_NUT[1] - B2B_STACK) < 1e-6, f"spacers {RING_NUT[1]} mm = the CN2 stack {B2B_STACK} mm: the MSR-2's "
                                               f"back rests on them with CN2 mated (both to be measured)")
    check(all(abs(x - px) < 1e-6 and abs(y - MSR_Y - py) < 1e-6 for (x, y), (px, py) in zip(MSR_SPACERS, MSR2_POSTS))
          and len(MSR_SPACERS) == len(MSR2_POSTS), "a spacer under each face plate post")
    r0 = RING_NUT[0] / 2
    for i, (x, y) in enumerate(MSR_SPACERS):
        disc = Cylinder(r0 - 0.05, 0.1)
        top = (Pos(x, y, MSR_BACK_Z + 0.05) * disc) & mp["board"]
        foot = (Pos(x, y, RING_T - 0.05) * disc) & rp["ring"]
        full = 3.14159 * (r0 - 0.05) ** 2 * 0.1
        ring_a = full - 3.14159 * (RING_NUT_HOLE / 2) ** 2 * 0.1          # less its spigot hole
        a, f = (top.volume if top else 0.0) / full, (foot.volume if foot else 0.0) / ring_a
        check(a >= 0.9 and f >= 0.95, f"spacer {i + 1}: {a * 100:.0f} % under solid MSR-2 board, {f * 100:.0f} % on solid "
                                       f"ring board round its spigot hole")
    sp = rp["spacers"]
    for name, o in (("MSR-2's back switches", mp["sw"]), ("CN2 mate", rp["cn2"]), ("MSR-2 board", mp["board"])):
        r = sp & o
        check(r is None or r.volume < 1e-4, f"spacers clear of the {name}")
    for k in ("cn2", "msr", "spacers"):
        r = rp[k] & ins
        v = r.volume if r is not None else 0.0
        check(v < 0.01, f"{k} clear of the insert ({v:.3f} mm3)")
    r = rp["msr"] & rp["ring"]
    v = r.volume if r is not None else 0.0
    check(v < 0.01, f"MSR-2 (back switches {MSR2_SW[2]} mm deep, CN2 stack {B2B_STACK}) clear of the ring board's notches "
                    f"({v:.3f} mm3)")


def ring_mount(ins):
    """Ring board on the insert (D-68): no flat back over it; crush ribs grip its window edge; the flange's land
    rests on its inner edge; the land and the taper print without supports."""
    print("ring board on the insert (D-68)")
    import ring
    import insert
    from build123d import Box, Cylinder
    rb = ring.board()
    yc = (RING_Y[0] + RING_Y[1]) / 2
    over = Pos(0, yc, (RING_T + PT) / 2) * Box(2 * RING_HALF_W, RING_Y[1] - RING_Y[0], PT - RING_T)
    over -= slab(rr(*FLANGE_OUT, ISLAND_R + FLANGE), -1, PT + 1)
    for s in (-1, 1):
        over -= Pos(0, s * SCREW_PITCH / 2, PT / 2) * Cylinder(BOSS_R, PT + 2)
    r = ins & over
    check(r is None or r.volume < 0.01, f"no insert over the ring board beyond the flange ({r.volume if r else 0.0:.3f} mm3)")
    ribs = insert.ribs()
    n = len(ribs.solids())
    w, interf = RING_RIB
    check(n == 4 * len(RING_RIBS), f"{n} crush ribs on the collar's outside")
    bite = ribs & rb
    v = bite.volume if bite else 0.0
    d = RING_WIN_CLR + interf
    want = n * w * interf * (RING_T - (RING_WIN_CLR + interf / 2))      # the 45 deg lead-in takes z < r
    check(abs(v - want) < 0.02 * want + 1e-3, f"ribs bite {interf} mm into the board's window edge ({v:.3f} mm3, "
                                              f"{n} x {w} wide above the {d:.2f} mm lead-in)")
    r = rb & ins
    rv = r.volume if r else 0.0
    check(abs(rv - v) < 1e-3, f"the board meets the insert only at the ribs ({rv:.3f} mm3)")
    bb = ribs.bounding_box()
    check(bb.min.Z >= -1e-6 and bb.max.Z <= RING_T + 1e-6, f"ribs within the board's thickness, above the wall plane "
                                                           f"(z {bb.min.Z:.2f}..{bb.max.Z:.2f})")
    land = RING_WIN_CLR + RING_LAND
    band = slab(rr(*[v_ + 2 * land - 0.1 for v_ in RING_INNER[:2]], RING_INNER[2] + land), RING_T + 0.02, RING_T + 0.07) \
        - slab(rr(*RING_INNER), -1, PT)
    c = band & ins
    a = (c.volume if c else 0.0) / 0.05
    full = band.volume / 0.05
    check(RING_LAND >= 1.0 and a >= 0.7 * full, f"flange land {RING_LAND} mm over the board's inner edge, on it over "
                                                f"{a:.0f} of {full:.0f} mm2 (the #6 bosses and the FFC channel aside)")
    chk = (ins & (Pos(0, 0, RING_T - 0.05) * Box(300, 300, 0.1))) - slab(rr(*SEAL, PLUG_R + COLLAR_LIP), -1, 10)
    for s in (-1, 1):
        chk -= Pos(0, s * SCREW_PITCH / 2, 0) * Cylinder(BOSS_R + 0.01, 30)
    rest = (chk - ribs) if chk else None
    check(rest is None or rest.volume < 1e-3, "nothing of the insert between the board and the wall but the collar, the "
                                              "#6 bosses and the ribs")


def mounting(ins):
    """Board standoffs (D-57): bosses, tapped holes, standoffs and screws against the board, KiCad holes."""
    print("board mounting (nylon standoffs)")
    from build123d import Cylinder
    import bilresa, standoff, assembly
    check(all(d >= s + 0.5 - 1e-6 for d, s in zip(MOUNT_THREAD_L, MOUNT_STUD)) and min(MOUNT_STUD) >= MOUNT_THREAD_MIN,
          f"tapped depths {MOUNT_THREAD_L} mm for the studs {MOUNT_STUD} (>= {MOUNT_THREAD_MIN} engaged, 1.5 x M3)")
    check(MOUNT_FACE_Z >= Z_BOT - 1e-6, f"boss faces at z {MOUNT_FACE_Z:.1f}, {STANDOFF_L} mm standoffs to the board, "
                                       f"{MOUNT_FACE_Z - Z_BOT:.1f} above the insert's lowest point")
    depth = STANDOFF[2]
    sl, head_d, head_h = STANDOFF_SCREW
    eng = sl - WB[2]
    check(eng >= 2 * MOUNT_THREAD_D - 1e-6 and eng <= depth - 0.5, f"screw {eng:.1f} mm into the standoff's {depth} mm "
                                                                  f"thread (>= 2 x M3 in nylon, short of its end)")
    face = MOUNT_FACE_Z
    for (x, y), top, depth in zip(MOUNT_HOLES, MOUNT_BOSS_TOP, MOUNT_THREAD_L):
        tip = face + depth + MOUNT_TAP_D / 2
        shell = Pos(x, y, (face + tip + BARRIER_MIN) / 2) * Cylinder(MOUNT_TAP_D / 2 + BARRIER_MIN,
                                                                     tip + BARRIER_MIN - face)
        gap = (shell - insert.mount_hole(x, y, depth)) - ins
        v = gap.volume if gap is not None else 0.0
        check(v < 0.05, f"hole at ({x:.1f}, {y:.1f}): {depth} mm thread with >= {BARRIER_MIN} mm wall "
                        f"({v:.2f} mm3 missing)")
        check(abs(x) + MOUNT_BOSS_D / 2 <= PLUG[0] / 2 and abs(y - WB_Y) + MOUNT_BOSS_D / 2 <= PLUG[1] / 2,
              f"boss at ({x:.1f}, {y:.1f}) inside the box-fit outline")
        reach = Pos(x, y, (face + top + CLR) / 2) * Cylinder(MOUNT_BOSS_D / 2 + CLR, top + CLR - face)
        r = reach & bilresa.build()
        check((r.volume if r is not None else 0.0) < 0.01, f"boss at ({x:.1f}, {y:.1f}) clears the remote by {CLR} mm")
    board = assembly.wiring_board()
    r = standoff.placed() & board
    ov = r.volume if r is not None else 0.0
    src = "KiCad STEP" if assembly.WB_STEP.exists() else "envelope (no holes)"
    check(ov < 0.05 or not assembly.WB_STEP.exists(), f"standoffs and screws clear of the board's parts, screws "
                                                       f"through its holes ({src}: {ov:.2f} mm3)")
    check(MOUNT_HOLE_D >= MOUNT_THREAD_D + 0.2, f"board holes {MOUNT_HOLE_D} mm for the M3 screws")
    import kicad_board
    if kicad_board.WB_PCB.exists():
        b = kicad_board.Board()
        for i, (x, y) in enumerate(MOUNT_HOLES, 1):
            k = b.origin(f"MH{i}")
            check(abs(k[0] - x) < 0.01 and abs(k[1] - (WB_Y + y)) < 0.01,
                  f"KiCad MH{i} at ({k[0]:.2f}, {k[1]:.2f}) matches params MOUNT_HOLES")
        k = b.origin("J2")
        check(abs(k[0] - J2_POS[0]) < 0.01 and abs(k[1] - (WB_Y + J2_POS[1])) < 0.01,
              f"KiCad J2 at ({k[0]:.2f}, {k[1]:.2f}) matches params J2_POS")


def mic_column(col, mic, passives, board_top, port, hole_d):
    """Sound column over the top-port mic (D-83), NA and EU: foot on the gasket round the mic, cavity clear of the mic,
    bore over the port, no part under the gasket, bore and face hole within Knowles' advice and printable."""
    from build123d import Cylinder
    bore, gasket = MIC_TUBE
    clr, wall, gap = MIC_BOOT
    bb = col.bounding_box()
    check(abs(bb.min.Z - board_top - gasket) < 1e-6, f"sound column's foot {gasket} mm over the board (gasket round "
                                                     f"the mic)")
    d = col.distance_to(mic)
    check(d >= min(clr, gap) - 1e-6, f"sound column's cavity {d:.2f} mm clear of the mic (boot {clr} round, {gap} over)")
    mb = mic.bounding_box()
    port_y = mb.max.Y - MIC_PORT_IN                           # port end up
    check(abs(port_y - port[1]) < 1e-6 and abs((mb.min.X + mb.max.X) / 2 - port[0]) < 1e-6,
          f"mic port under the column's bore at ({port[0]:.1f}, {port[1]:.1f})")
    zc = board_top + MIC[2] + gap                              # cavity top
    probe = Pos(*port, (zc + bb.max.Z) / 2) * Cylinder(bore / 2 - 0.05, bb.max.Z - zc - 0.1)
    r = probe & col
    check(r is None or r.volume < 0.001, f"bore {bore} open from the cavity to the skin")
    ring_w = (MIC[0] + 2 * (clr + wall), MIC[1] + 2 * (clr + wall))
    pad = Pos(port[0], (mb.min.Y + mb.max.Y) / 2, 0) * slab(rr(*ring_w, wall), board_top, board_top + gasket)
    r = pad & passives
    check(r is None or r.volume < 1e-6, f"no part under the gasket ({ring_w[0]:.1f} x {ring_w[1]:.1f} round the mic)")
    check(bore >= 1.0 and 1.0 <= MIN_PRINT_HOLE <= hole_d,
          f"bore {bore} >= 1.0 (Knowles: gasket cavity); face hole {hole_d} prints open (>= {MIN_PRINT_HOLE}; "
          f"Knowles: case hole 1.0-1.5)")
    check(wall >= 0.8, f"column wall {wall} mm round the cavity (two lines)")


def ring_checks(ins, tr):
    """Ring board (D-50, D-68): inside the face plate, copper keep-out from the box opening, the parts on it in
    copper-allowed places, the MSR-2 behind the radar skin, the mic under its sound column."""
    print("ring board (D-50)")
    import ring, bilresa
    rp = ring.parts()
    for k in ("ring", "spacers", "cn2", "msr", "j1", "sht45", "passives", "mic"):
        for on, o in (("insert", ins), ("trim", tr)):
            if k == "ring" and on == "insert":
                continue                                    # the crush ribs bite into it: ring_mount()
            r = rp[k] & o
            v = r.volume if r is not None else 0.0
            check(v < 0.01, f"{k} clears the {on} ({v:.3f} mm3)")
    band = RING_HALF_W - 0.2 - (BOX_W / 2 + RING_KEEP - RING_T)
    need = 4 * 0.15 + 3 * 0.15
    check(band >= need, f"side rails: {band:.2f} mm of front-layer copper beyond {RING_KEEP} mm from the box opening "
                        f"(SDA, SCL, 3.3 V, GND at 0.15 / 0.15 need {need:.2f})")
    k_front = RING_KEEP - RING_T

    def allowed(x, y, r):
        """Front-layer copper disc at (x, y), radius r, at least k_front (plan) from the box opening's rectangle."""
        dx, dy = max(abs(x) - BOX_W / 2, 0.0), max(abs(y) - BOX_H / 2, 0.0)
        return (dx * dx + dy * dy) ** 0.5 - r
    for name, (x, y), r in [("J1", RING_J1, max(FH12[:2]) / 2 + 0.5), ("SHT45", SHT_AT, 1.5),
                            ("microphone", (MIC_AT[0], MIC_BODY_Y), max(MIC[:2]) / 2 + 0.3),
                            ("CN2 mate", (MSR_CN2_X, MSR_Y), max(B2B) / 2 + 0.5)] + \
                           [(k, p, max(d[:2]) / 2 + 0.3) for k, (p, d) in RING_SMALL.items()] + \
                           [(f"spacer {i + 1}", p, RING_NUT_PAD / 2) for i, p in enumerate(MSR_SPACERS)]:
        d = allowed(x, y, r)
        check(d >= k_front, f"{name} copper {d:.1f} mm from the box opening (front layer >= {k_front:.1f})")
    gap = (PT - RADAR_WALL) - (MSR_BACK_Z + MSR[2])
    check(abs(gap - MSR_SKIN_GAP) < 1e-6, f"MSR-2 on CN2, its front {gap:.2f} mm under the {RADAR_WALL} mm radar skin "
                                         f"(D-66; MSR[2] MEASURE)")
    mic_column(__import__("trim").mic_tube(), rp["mic"], rp["passives"], RING_T, MIC_AT, MIC_SKIN_HOLE_D)
    on_board = {k: rp[k] for k in ("passives", "mic", "j1", "spacers", "cn2", "sht45")}
    for a in on_board:
        for b in on_board:
            if a < b:
                r = on_board[a] & on_board[b]
                check(r is None or r.volume < 1e-6, f"ring board parts: {a} clear of {b}")
    from build123d import Cylinder
    probe = Pos(*MIC_AT, (SKIN_Z + PT) / 2) * Cylinder(MIC_SKIN_HOLE_D / 2 - 0.05, SKIN - 0.1)
    r = probe & tr
    check(r is None or r.volume < 0.001, "sound hole open through the face skin")
    r = rp["ring"] & bilresa.build()
    check(r is None or r.volume < 0.001, "ring board clears the remote")


def ffc_checks(ins, tr):
    """5 V FFC (D-50, D-68, D-74): stock 6-way cable through the pass-through, out of the flange onto the ring board,
    its spare folded flat beside J1, clear of everything else."""
    print("5 V FFC")
    import jumper, ring, bilresa, standoff
    from math import hypot
    diag = hypot(JUMPER_END[0], JUMPER_END[2])
    check(diag <= PASS_D - 0.5 and JUMPER_END[0] <= PASS_SLOT[0] - 0.5 and JUMPER_END[2] <= PASS_SLOT[1] - 0.3,
          f"FFC contact end ({JUMPER_END[0]} x {JUMPER_END[2]}) threads the {PASS_D} mm pass-through and its "
          f"{PASS_SLOT[0]} x {PASS_SLOT[1]} slot")
    need = jumper.length() + 2 * JUMPER_END[1]
    slack = JUMPER_STOCK_L - need
    check(JUMPER_SLACK[0] <= slack <= JUMPER_SLACK[1],
          f"FFC route {jumper.length():.0f} mm + {JUMPER_END[1]} mm into each connector leaves {slack:.1f} mm of the "
          f"{JUMPER_STOCK_L:.0f} mm stock cable to bow in the free span ({JUMPER_SLACK[0]}..{JUMPER_SLACK[1]}); no loop")
    fold = jumper_fold()
    lo_y, hi_y = JUMPER_FOLD_Y - JUMPER_W / 2, JUMPER_FOLD_Y + JUMPER_W / 2
    check(fold > 2.0 and lo_y >= FLANGE_OUT[1] / 2 + 0.2 - 1e-6 and hi_y <= RING_J1[1] - FH12[1] / 2 - 0.2 + 1e-6,
          f"spare length folded flat in four {fold:.1f} mm layers on the ring board (y {lo_y:.2f}..{hi_y:.2f}: beyond "
          f"the flange, short of J1's body)")
    xl = RING_J1[0] - fold - JUMPER_W / 2
    check(xl >= BOSS_R + 1.0, f"fold ends at x {xl:.1f}, clear of the #6 screw boss (r {BOSS_R})")
    # the straight bore (D-74): walls to the remote pocket and the standoffs' tapped holes, the mouth inside the plug,
    # the groove where it opens through the corner taper, threading (one bend, into the slot)
    from build123d import Cylinder
    m, e, f = pass_points()
    r = PASS_D / 2
    bore = insert.bore()
    pocket = slab(stadium(*POCKET_IN), SEAT_Z, PT + 5)
    d = bore.distance_to(pocket)
    check(d >= BARRIER_MIN - 1e-6, f"bore {d:.2f} mm from the remote pocket (>= {BARRIER_MIN})")
    tap = min(bore.distance_to(insert.mount_hole(x, y, t)) for (x, y), t in zip(MOUNT_HOLES, MOUNT_THREAD_L))
    check(tap >= 1.2, f"bore {tap:.2f} mm from the nearest standoff's tapped hole (>= 1.2)")
    bosses = insert.mount_bosses()
    d = bore.distance_to(bosses)
    check(d >= MOUNT_PASS_GAP - 1e-6 or tap >= 1.2, f"bore clears the standoff bosses' tapped holes ({d:.2f} mm to a boss "
                                                     f"face, inside the boss: {tap:.2f} mm to the hole)")
    edge = min(BOX_W / 2 - abs(m[0]), BOX_H / 2 - abs(m[1]))
    check(edge >= 6.0, f"bore's axis at the underside plane ({m[0]:.1f}, {m[1]:.1f}), {edge:.1f} mm in from the box wall")
    from math import atan2, degrees
    run = hypot(e[0] - m[0], e[1] - m[1])
    ang = degrees(atan2(e[2] - m[2], run))
    print(f"       bore {hypot(run, e[2] - m[2]):.1f} mm long, {ang:.0f} deg from horizontal; one bend, into the slot")
    env = insert.outline_solid()
    below = Pos(0, 0, -50 + Z_BOT + 0.05) * Box(200, 200, 100)
    groove = (bore - env) - below
    top = groove.bounding_box().max.Z if groove is not None and groove.volume > 1e-3 else Z_BOT
    check(top <= -3.0, f"bore closed above z {top:.1f}: the groove below opens through the corner taper, at least 3 mm "
                       f"under the wall plane")
    probe = Pos(m[0], m[1], Z_BOT - 0.5) * Cylinder(r - 0.3, 1.0)
    r_ = probe & ins
    check(r_ is None or r_.volume < 0.01, "bore's mouth open on the underside")
    jmp = jumper.build()["jumper"]
    rp = ring.parts()
    others = {"insert": ins, "trim": tr, "board standoffs": standoff.placed(), "remote": bilresa.build(),
              "riser": rp["riser"], "spacer posts": rp["posts"] + rp["sleeves"], "MSR-2": rp["msr"]}
    for on, o in others.items():
        r = jmp & o
        v = r.volume if r is not None else 0.0
        check(v < 0.05, f"FFC clears the {on} ({v:.3f} mm3)")
    slab_ = Pos(0, WB_Y, WB_FRONT_Z - WB[2] / 2) * Box(*WB)
    r = jmp & slab_
    check(r is None or r.volume < 0.01, "FFC clears the wiring board's slab")


def separation(ins, tr):
    """R9 / D-50: the face plate carries no electronics: it is clear of every electrical part."""
    print("face plate: no electrical parts (D-50)")
    import ring, jumper, assembly
    rp = ring.parts()
    parts = {k: rp[k] for k in ("ring", "spacers", "cn2", "msr", "j1", "sht45", "passives", "mic", "riser", "pins",
                                "posts")}
    parts["FFC"] = jumper.build()["jumper"]
    parts["wiring board"] = assembly.wiring_board()
    for name, p in parts.items():
        if name == "msr":                                   # the face plate's posts rest on the MSR-2's board
            r = tr & p
            v = r.volume if r is not None else 0.0
            check(v < 0.01, f"face plate posts rest on the MSR-2's board, no overlap ({v:.3f} mm3)")
            continue
        d = tr.distance_to(p)
        check(d >= 0.05, f"face plate not touching the {name} (gap {d:.2f} mm)")


def _well_margin():
    """Distance from the well's far corner to the pocket's inner stadium (positive = inside)."""
    from math import hypot
    r = POCKET_IN[0] / 2
    yc = POCKET_IN[1] / 2 - r
    xw, yw = WELL_IN[0] / 2, abs(SW_Y) + WELL_IN[1] / 2
    return r - hypot(xw, max(yw - yc, 0))


def solids(ins, tr):
    print("solids")
    check(ins.is_valid and len(ins.solids()) == 1, "insert is one valid solid")
    check(tr.is_valid and len(tr.solids()) == 1, "trim is one valid solid")
    ov = (ins & tr).volume
    check(ov < 0.01, f"insert and trim do not overlap ({ov:.3f} mm3)")
    import bilresa
    r = bilresa.build() & ins
    ov = r.volume if r is not None else 0.0
    check(ov < 0.01, f"BILRESA model clears the pocket ({ov:.3f} mm3)")


def board_fit(ins):
    print("wiring board in the insert")
    import assembly
    board = assembly.wiring_board()
    ov, rocker_ov = 0.0, 0.0
    for sol in board.solids():
        r = sol & ins
        v = r.volume if r is not None else 0.0
        if sol.bounding_box().max.Z > PANEL_BOT_Z:   # only the rocker reaches through the panel
            rocker_ov += v
        else:
            ov += v
    src = "KiCad STEP" if assembly.WB_STEP.exists() else "envelope"
    check(ov < 0.5, f"board and parts ({src}) do not collide with the insert ({ov:.2f} mm3)")
    print(f"       rocker model vs. panel cutout: {rocker_ov:.2f} mm3 (snap fit; cutout and body per the "
          f"Marquardt drawing tolerances, see the well/cutout checks)")
    if assembly.WB_STEP.exists():
        slab_ = max(board.solids(), key=lambda q: q.bounding_box().size.X * q.bounding_box().size.Y).bounding_box()
        check(abs(slab_.size.X - WB[0]) < 0.05 and abs(slab_.size.Y - WB[1]) < 0.05,
              f"KiCad board {slab_.size.X:.2f} x {slab_.size.Y:.2f} matches params WB {WB[0]} x {WB[1]}")


def barrier(ins):
    print("barrier")
    room = slab(rr(PW + 20, PH + 20, 5), 0, PT + 10)
    box = slab(Rectangle(BOX_W, BOX_H), -BOX_D, 0)
    # plug the openings that are closed by something else when installed: the 5 V pass-through (FFC), the rocker
    # cutout (the certified rocker body) and the two spring pins' holes in the pocket floor (the pins, D-50)
    rocker = Pos(0, SW_Y, 0) * slab(Rectangle(*SW_CUT), PANEL_BOT_Z - 1, WELL_FLOOR_Z + 1)
    import ring
    air = (room + box) - ins - insert.pass_through() - rocker - ring.pin_holes()   # pins fill their holes (D-50)
    parts = air.solids()
    mains = [s for s in parts if s.is_inside(Vector(0, 0, -BOX_D + 1))]
    check(len(mains) == 1, "found the mains air volume")
    m = mains[0]
    for name, p in [("room in front of the face", (0, 0, PT + 5)),
                    ("remote pocket", (0, 0, SEAT_Z + 1)),
                    ("trim hollow (low-voltage)", (28.0, 60.0, 5)),
                    ("MSR-2 bay", (0, MSR_Y, 5)),
                    ("ring board space beside the plug", (-30.0, 0.0, RING_T / 2))]:
        check(not m.is_inside(Vector(*p)), f"mains air does not reach the {name}")
    check(m.bounding_box().max.Z <= 0.01, f"mains air stays behind the wall plane (max z {m.bounding_box().max.Z:.2f})")


def _face_poly(f):
    import shapely
    def ring(w):
        pts = [v for e in w.edges() for v in (e.positions([i / 24 for i in range(25)]) if e.geom_type.name != "LINE" else [e.position_at(0), e.position_at(1)])]
        return [(q.X, q.Y) for q in pts]
    outer = ring(f.outer_wire())
    holes = [ring(w) for w in f.inner_wires()]
    return shapely.Polygon(outer, holes).buffer(0)


def overhangs(name, part, limit=3.0, angle=50.0, hole_r=2.5, small=0.0, supported=(), bridges=()):
    """Downward faces steeper than `angle` from vertical that are not on the bed.
    Planar faces: width = 2 x max inscribed circle (bridges and short ledges up to
    `limit` mm are accepted). Curved faces: small bores (r <= hole_r) and features whose
    bounding box diagonal is <= `small` mm are accepted (listed), anything else steeper
    than `angle` fails. Planar faces at a z in `supported` print on supports (listed).
    `bridges`: (z, span) pairs; a planar face at z over a closed recess bridges up to span mm (listed)."""
    import shapely
    zmin = part.bounding_box().min.Z
    worst, bad, sup = 0.0, [], []
    lim = -np.sin(np.radians(angle))  # normal.z of a face `angle` deg from vertical
    for f in part.faces():
        if f.bounding_box().max.Z < zmin + 0.05:
            continue  # on the bed
        gt = f.geom_type.name
        if gt == "PLANE":
            n = f.normal_at(f.center())
            if n.Z >= lim:
                continue
            w = 2 * shapely.maximum_inscribed_circle(_face_poly(f)).length
            bb = f.bounding_box()
            if any(abs(bb.min.Z - z) < 0.05 and bb.size.Z < 0.05 for z in supported):
                if w > limit:
                    sup.append(f.area)
                continue
            span = [s for z, s in bridges if abs(bb.min.Z - z) < 0.05 and bb.size.Z < 0.05]
            if span and w > limit:
                ok = w <= span[0]
                print(f"         bridge z={bb.min.Z:.1f} width {w:.1f} (<= {span[0]}){'' if ok else ' TOO WIDE'}")
                if ok:
                    continue
            worst = max(worst, w)
            if w > limit:
                bad.append(f"plane z={bb.min.Z:.1f} width {w:.1f} at x {bb.min.X:.0f}..{bb.max.X:.0f} y {bb.min.Y:.0f}..{bb.max.Y:.0f}")
            continue
        verts, tris = f.tessellate(0.05, 0.5)                # points on the trimmed face, not its whole surface
        step = max(1, len(tris) // 200)
        steep = False
        for t in tris[::step]:
            a, b, c3 = verts[t[0]], verts[t[1]], verts[t[2]]
            try:
                nz = f.normal_at((a + b + c3) / 3).Z
            except Exception:                               # centre not projectable: the surface normal at the corners,
                ns = []                                     # else the triangle's own (coarse on curved faces)
                for v in (a, b, c3):
                    try:
                        ns.append(f.normal_at(v).Z)
                    except Exception:
                        pass
                if ns:
                    nz = sum(ns) / len(ns)
                else:
                    n = (b - a).cross(c3 - a)
                    if n.length < 1e-9:
                        continue
                    nz = n.normalized().Z
            if nz < lim:
                steep = True
                break
        if not steep:
            continue
        if gt in ("CYLINDER", "SPHERE") and f.bounding_box().diagonal < 60 and _small_bore(f, hole_r):
            continue
        bb = f.bounding_box()
        if bb.diagonal <= small:
            print(f"         accepted small {gt.lower()} overhang, {bb.diagonal:.1f} mm across, z {bb.min.Z:.1f}..{bb.max.Z:.1f}")
            continue
        bad.append(f"{gt.lower()} area {f.area:.0f} at x {bb.min.X:.0f}..{bb.max.X:.0f} y {bb.min.Y:.0f}..{bb.max.Y:.0f} z {bb.min.Z:.1f}..{bb.max.Z:.1f}")
    if sup:
        print(f"         on supports: {len(sup)} faces, {sum(sup):.0f} mm2")
    for r in bad[:10]:
        print("         " + r)
    check(not bad, f"{name}: no unsupported overhangs (widest flat ledge/bridge {worst:.1f} mm <= {limit} mm)")


def _small_bore(f, r):
    try:
        return f.radius <= r + 1e-6
    except Exception:
        bb = f.bounding_box()
        return min(bb.size.X, bb.size.Y, bb.size.Z) <= 2 * r + 0.1


def cover_checks():
    """Replacement back cover (D-35, D-50): pads over the spring pin windows, flex clear of the body, end contacts on
    the cell axes clear of the remote's PCB strip, steel plate."""
    print("replacement back cover (D-35)")
    from build123d import Cylinder, Rot
    import backcover as bc
    ps = bc.cover_parts()
    c = ps["cover"]
    check(c.is_valid and len(c.solids()) == 1, f"cover: one valid solid ({c.volume / 1000:.2f} cm3)")
    check(BC_SIDE_WALL >= 1.2,
          f"side wall {BC_SIDE_WALL:.1f} mm (back {BC_WALL}): {B_W - 2 * BC_SIDE_WALL:.1f} x {B_H - 2 * BC_SIDE_WALL:.1f} "
          f"inside at the rim, 0.1 more all round for the remote's housing (D-75)")
    win = PIN_BARREL[0] / 2 + BC_WIN_CLR
    check(win - PIN_BARREL[0] / 2 >= 0.2 and BC_PAD_D / 2 >= win + 0.2,
          f"spring pin windows r {win:.2f} round the {PIN_BARREL[0]} barrel, pads r {BC_PAD_D / 2} over them (D-50)")
    for k in ("flex", "stiffener", "steel", "pin_pads", "contacts", "regulator"):
        r = ps[k] & c
        v = r.volume if r is not None else 0.0
        check(v < 0.01, f"{k} clears the cover body ({v:.3f} mm3)")
    xi = BC_PCB_W / 2 + BC_PCB_CLR
    pw, ph = FINGER_PAD[0], FINGER_PAD[1]                    # contact finger pad on the end section (x, z): vertical
    check(BC_CELL_X - pw / 2 >= xi + 0.5, f"contact finger pads clear of the remote's PCB strip "
                                          f"({BC_CELL_X - pw / 2 - xi:.2f} mm beyond the notch)")
    lane = BC_FLEX_Z + BC_LANE_H + 0.15                      # +3V3 trace (0.3) across the band
    check(BC_CELL_Z - ph / 2 - lane >= 0.3, f"+3V3 lane across the band {BC_CELL_Z - ph / 2 - lane:.2f} "
                                            f"mm below the contact finger pads")
    check(BC_FLEX_Z + BC_END_H >= BC_CELL_Z + ph / 2 + 0.5, "contact finger pads within the end section")
    edge = BC_END_XO - (BC_CELL_X + pw / 2)
    check(edge >= 0.5, f"contact finger pads {edge:.2f} mm inside the end section's outer edges")
    plate = BC_CELL_END_Y + BC_TERM_Y * BC_TERM_SETBACK
    dome = bc.end_fingers(FINGER_WH).bounding_box()
    tip = dome.min.Y if BC_TERM_Y < 0 else dome.max.Y
    check(abs(tip - plate) < 0.02, f"contact finger domes at working height {FINGER_WH} on the VBAT plate (y {plate:.2f}, "
                                   f"setback {BC_TERM_SETBACK} MEASURE)")
    arm = bc.end_fingers(FINGER_WH)
    top = arm.bounding_box().max.Z
    check(top >= BC_CELL_Z + FINGER[1] / 2 - 0.05, f"end fingers vertical, bend end up at z {top:.2f} (ramp faces "
                                                   "the remote as the cover goes on)")
    print("       GND contact: finger dome on the remote's leaf spring, which stands proud of the cell end plane "
          "(its travel MEASURE): finger and leaf share the compression")
    for x, y in BC_FINGERS:
        check(BC_STRIP[0] + 0.2 <= x - BC_PAD_D / 2 and x + BC_PAD_D / 2 <= BC_STRIP[1] - 0.2,
              f"pad at ({x}, {y}) inside the flex strip")
    check(BC_STEEL_FLOOR >= BC_WALL - 1e-6 and BC_REG_FLOOR >= 0.4 - 1e-6,
          f"{BC_STEEL_FLOOR} mm of cover wall under the plate (full shell), {BC_REG_FLOOR} under the regulator")
    rb = bc.steel_ridge().bounding_box()
    seat = (rb.size.X - 2 * BC_STEEL_RIDGE[0], rb.size.Y - 2 * BC_STEEL_RIDGE[0])
    check(abs(seat[0] - BC_STEEL[0] - 2 * BC_STEEL_CLR) < 0.01 and abs(seat[1] - BC_STEEL[1] - 2 * BC_STEEL_CLR) < 0.01,
          f"ridge round the plate: seat {seat[0]:.1f} x {seat[1]:.1f} mm ({BC_STEEL_CLR} clearance), "
          f"{BC_STEEL_RIDGE[1]} high, open {BC_STEEL_RIDGE_GAP} mm each side of the clips")
    r = bc.steel_ridge() & ps["steel"]
    check(r is None or r.volume < 0.001, "ridge clears the plate")
    r = ps["pad_stiffener"] & c
    check(r is None or r.volume < 0.01, "pad stiffener clears the cover body (under the snap lips)")
    w, t, lip, clr = BC_FLEX_SNAP
    snaps = bc.flex_snaps()
    n = len(snaps.solids())
    check(n == len(bc.flex_snap_spots()), f"{n} snap hooks on the flex section's long edges (beside each finger and "
                                          f"the regulator, none where the jog leaves the GND pad's inner edge)")
    check(lip - clr >= 0.15 and BC_FLEX_SNAP_GAP <= 0.1, f"snap lips {lip - clr:.2f} mm over the stiffener's edges, "
                                                         f"{BC_FLEX_SNAP_GAP} mm above it")
    for k in ("flex", "pad_stiffener", "pin_pads", "regulator", "steel"):
        r = snaps & ps[k]
        check(r is None or r.volume < 0.001, f"snap hooks clear the {k}")
    zl = BC_FLEX_Z + FLEX_T + BC_PAD_STIFF_T + BC_FLEX_SNAP_GAP
    root = max(e.bounding_box().min.Z for e in bc.flex_snap_reliefs().solids())
    arm = zl + lip / 2 - root                                 # post bends from the relief floor to the lip
    strain = 1.5 * t * (lip - clr) / arm ** 2                 # cantilever outer-fibre strain: the lip clears the edge
    check(strain <= 0.04, f"snap posts {arm:.1f} mm free, {t} thick, deflect {lip - clr:.1f}: strain "
                          f"{strain * 100:.1f} % (design target <= 4 % for PETG)")
    ledge = [Pos((x0 + x1) / 2, (y0 + y1) / 2, BC_FLEX_Z - 0.2) * Box(x1 - x0, y1 - y0, 0.4)
             for x0, x1, y0, y1 in bc.strip_boxes()[:2]]
    r = bc.flex_snap_reliefs() & (ledge[0] + ledge[1])
    check(r is None or r.volume < 0.001, "snap reliefs outside the ledge under the flex")
    above = Pos(0, 0, B_SEAM_Z + 50) * Box(200, 200, 100)
    room = None
    for sx in (-1, 1):
        cyl = Pos(sx * BC_CELL_X, 0, BC_CELL_Z) * Rot(90, 0, 0) * Cylinder(BC_END_R, 200)
        room = cyl if room is None else room + cyl
    for k in ("cover", "flex", "stiffener", "contacts"):
        r = (ps[k] & above) - room
        v = r.volume if r is not None else 0.0
        check(v < 0.01, f"{k} above the rim inside the cells' outline (r {BC_END_R}, rounded tops; {v:.3f} mm3 out)")
    t, h, gap = BC_END_LIP
    check(t >= 1.2 and h >= 0.8, f"end section held by a {t} x {h} mm lip at its foot")
    wall, sclr, reach, lt, sgap = BC_END_SLOT
    check(reach >= 0.4 and BC_END_XO - reach >= BC_CELL_X + pw / 2 + 0.3,
          f"slot lips {reach} mm over the section's outer edges, clear of the finger pads "
          f"({BC_END_XO - reach - BC_CELL_X - pw / 2:.2f} mm)")
    check(lt + sgap <= FINGER_WH - 0.5, f"slot lips {lt + sgap:.2f} mm in front of the copper (contacts at {FINGER_WH})")
    slots = bc.end_slots()
    sb = slots.bounding_box()
    check(sb.max.X <= BC_BLOCK_XO + 1e-6 and sb.min.X >= -BC_BLOCK_XO - 1e-6,
          f"slots inside the blocks' outline (|x| <= {BC_BLOCK_XO:.2f})")
    for k in ("flex", "stiffener", "contacts"):
        r = slots & ps[k]
        check(r is None or r.volume < 0.001, f"slots clear the {k}")
    lip_z = (slots & Pos(BC_END_XO - reach / 2, 0, 0) * Box(0.1, 200, 200)).bounding_box()
    check(lip_z.max.Z - BC_FLEX_Z >= 5.0, f"slot lips hold the section's outer edges from the ledge to z {lip_z.max.Z:.1f}")
    ye = (bc.copper_y() + bc.stiffener_y()) / 2          # the upright end section slides in from above: swept up,
    sect = (ps["flex"] + ps["stiffener"]) & Pos(0, ye, 52.3) * Box(200, 1.5, 100)    # it meets nothing (the strip
                                                         # on the ledge, z < 2.3, is pressed down past its hooks)
    hit = 0.0
    for dz in (0.5, 1.0, 2.0, 3.0, 5.0, 8.0, 12.0):
        r = Pos(0, 0, dz) * sect & ps["cover"]
        hit = max(hit, r.volume if r is not None else 0.0)
    check(hit < 0.01, f"end section slides straight down into the slots and the foot slot ({hit:.3f} mm3 in the way)")
    nb = bc.run_notch().bounding_box()
    f0, f1 = BC_CELL_X - FINGER_PAD[1] / 2, BC_CELL_X + FINGER_PAD[1] / 2     # GND finger's pad across x
    over = max(0.0, min(nb.max.X, f1) - max(nb.min.X, f0))
    check(over <= 3.0 and BC_END_T >= 0.4, f"run drops into a notch along the GND block's inner face from above (no "
                                           f"threading); the {BC_END_T} mm stiffener spans {over:.2f} mm of the "
                                           f"finger's pad over it (<= 3.0)")
    a, b, _, z1 = bc.end_blocks()[1]
    yb = bc.stiffener_y() - BC_TERM_Y * BC_BLOCK_T / 2
    post = (Pos((a + b) / 2, yb, (BC_WALL + z1) / 2) * Box(b - a, BC_BLOCK_T, z1 - BC_WALL)) & ps["cover"]
    sol = post.solids() if post is not None else []
    big = max((q.volume for q in sol), default=0.0)
    check(len([q for q in sol if q.volume > 1.0]) == 1, f"GND contact post one piece ({big:.0f} mm3): the run notch "
                                                        f"on its inner face, the pads and their hooks above it (D-79)")
    r = bc.run_notch() & ps["flex"]
    check(r is not None and r.volume > 0.01, "the run lies in the notch")
    holder = None                                        # outboard of each cell above its axis: the holder shell
    for sx in (-1, 1):
        h = Pos(sx * (BC_CELL_X + 50), 0, BC_CELL_Z + 50) * Box(100, 200, 100)
        h -= Pos(sx * BC_CELL_X, 0, BC_CELL_Z) * Rot(90, 0, 0) * Cylinder(BC_END_R, 200)
        holder = h if holder is None else holder + h
    end = Pos(0, bc.stiffener_y() - BC_TERM_Y * BC_BLOCK_T / 2, B_SEAM_Z / 2) * Box(200, BC_BLOCK_T + 6.0, B_SEAM_Z)
    inside = {"cover (less its shell)": ps["cover"] - bc.shell(), "flex": ps["flex"], "stiffener": ps["stiffener"]}
    for k, part in inside.items():
        r = part & end
        r = r & holder if r is not None and r.volume > 0 else None
        v = r.volume if r is not None else 0.0
        check(v < 0.01, f"{k} at the terminal end inside the cells' outline outboard above the axes (holder shell; "
                        f"{v:.3f} mm3 out)")
    clips = bc.steel_clips()
    r = clips & ps["steel"]
    check(r is None or r.volume < 0.001, "steel plate clips clear the plate")
    over = BC_STEEL_CLIP[2] - BC_STEEL_CLIP_CLR            # hook reach minus the gap to the plate's end
    cw, ct, ch = BC_STEEL_CLIP
    arm = BC_STEEL_FLOOR + BC_STEEL[2] + 0.1 + ch / 2 - BC_STEEL_CLIP_ROOT
    strain = 1.5 * ct * over / arm ** 2                    # cantilever outer-fibre strain as the plate passes the hook
    check(strain <= 0.03, f"plate clips {cw} wide, {ct} thick, {arm:.1f} mm free from their relief: strain "
                          f"{strain * 100:.1f} % snapping in (design target <= 3 %; broke in PLA, PETG to verify)")
    check(over >= 0.3, f"steel plate clips hook {over:.2f} mm over the plate's ends")
    ear = bc.latches().bounding_box()
    reach = sorted(round(B_H / 2 - abs(e.bounding_box().min.Y if e.bounding_box().center().Y > 0
                                       else e.bounding_box().max.Y), 2) for e in bc.latches().solids())
    check(ear.max.Y < B_H / 2 and reach == sorted(round(r, 2) for r in BC_LATCH_REACH),
          f"snap clip hook tips {reach} mm in from the outside rim, hooks {BC_LATCH_HOOK} mm inwards (bottom, top)")
    widths = [round(e.bounding_box().size.X, 2) for e in bc.latches().solids()]
    check(all(abs(w - BC_LATCH_W) < 0.01 for w in widths), f"snap clips {widths} mm wide")
    tops = sorted(round(e.bounding_box().max.Z - BC_WALL, 2) for e in bc.latches().solids())
    check(tops == sorted(round(t, 2) for t in BC_LATCH_TOPS) and ear.max.Z <= B_SEAM_Z, f"snap clips {tops} mm above the inside floor, "
                                                                  f"{B_SEAM_Z - BC_WALL - max(tops):.2f} below the rim")
    tab = bc.side_tabs().bounding_box()
    gap = 2 * min(abs(s.bounding_box().min.X) if s.bounding_box().min.X > 0 else abs(s.bounding_box().max.X)
                  for s in bc.side_tabs().solids())
    check(abs(gap - BC_SIDE_TAB_GAP) < 0.01 and abs(B_SEAM_Z - tab.max.Z - BC_SIDE_TAB_RIM_GAP) < 0.01,
          f"side ribs {gap:.1f} mm apart inside ({(B_W - gap) / 2:.1f} in from the outside), {BC_SIDE_TAB[1]} thick, "
          f"top {B_SEAM_Z - tab.max.Z:.1f} mm below the rim (measured)")
    gi, go, top, h, prot = BC_TAB
    tb = bc.tabs()
    ys = sorted(round(abs(v), 2) for t in tb.solids() for v in (t.bounding_box().min.Y, t.bounding_box().max.Y))
    xin = min(abs(t.bounding_box().min.X) if t.bounding_box().min.X > 0 else abs(t.bounding_box().max.X)
              for t in tb.solids())
    zs = (round(B_SEAM_Z - max(t.bounding_box().max.Z for t in tb.solids()), 2),
          round(B_SEAM_Z - min(t.bounding_box().min.Z for t in tb.solids()), 2))
    check(len(tb.solids()) == 4 and ys[0] >= gi / 2 + BC_TAB_CLR - 1e-3 and ys[-1] <= go / 2 - BC_TAB_CLR + 1e-3
          and abs(bc.inner_x(B_SEAM_Z - top - h / 2) - xin - prot) < 1e-3 and zs == (top, top + h),
          f"tabs inside both long side walls: y {ys[0]:.2f}..{ys[-1]:.2f} either side of mid-length ({BC_TAB_CLR} clear "
          f"of the housing's slots {gi / 2}..{go / 2}), {zs[0]}..{zs[1]} below the rim, {prot} in from the wall (D-90)")
    for name, part in (("snap clips", bc.latches()), ("side ribs", bc.side_tabs())):
        r = part & tb
        check(r is None or r.volume < 0.001, f"tabs clear of the {name}")
    for k in ("flex", "stiffener", "contacts", "regulator"):
        r = bc.latches() & ps[k]
        check(r is None or r.volume < 0.001, f"snap clips clear the {k}")
    x0, x1, y0, y1 = BC_REG_RECESS
    for ref, (x, y) in BC_REG.items():
        w, h, t = BC_REG_BODY if ref == "U1" else BC_CAP0402
        inside = x0 + 0.1 <= x - w / 2 and x + w / 2 <= x1 - 0.1 and y0 + 0.1 <= y - h / 2 and y + h / 2 <= y1 - 0.1
        check(inside and BC_FLEX_Z - t >= BC_REG_FLOOR + 0.1, f"regulator part {ref} inside its recess "
                                                                 f"({BC_FLEX_Z - t - BC_REG_FLOOR:.2f} mm above the floor)")
    pad, reg = bc.strip_boxes()[:2]                           # the regulator section above the pad section
    check(x0 >= reg[0] and x1 <= reg[1] and y0 >= reg[2] and y1 <= reg[3],
          "regulator recess under the flex's regulator section")
    wins = min(y for _, y in BC_FINGERS), max(y for _, y in BC_FINGERS)
    check(y0 >= wins[1] + PIN_BARREL[0] / 2 + BC_WIN_CLR + 0.5, f"regulator recess {y0 - wins[1] - PIN_BARREL[0] / 2 - BC_WIN_CLR:.2f} "
                                                        f"mm above the upper pin window")
    print(f"       contacts on the cell axes at z {BC_CELL_Z} (MEASURE), cell end y {BC_CELL_END_Y:.2f} (REF), "
          f"end section copper y {bc.copper_y():.2f}")


def battery_free_checks(ins, tr):
    """Battery-free remote, NA (D-50): two spring pins from the wiring board's 5 V area through the pocket floor onto
    the back cover flex's pads; riser in a pocket under the floor; posts on the board's 5 V area."""
    print("battery-free remote, NA (D-50)")
    import backcover as bc
    import ring, assembly
    rp = ring.parts()
    barrel = PIN_BARREL[0]
    lo, hi = PIN_WORK - PIN_TOL, PIN_WORK + PIN_TOL
    check(lo >= PIN_WH[0] - 1e-6 and hi <= PIN_WH[2] + 1e-6,
          f"pins at {PIN_WORK:.2f} mm working height, +-{PIN_TOL} -> {lo:.2f}..{hi:.2f} inside {PIN_WH[0]}..{PIN_WH[2]} "
          f"(Harwin P70-2200045; posts {POST_STACK[0]} + {POST_STACK[1]} mm)")
    print(f"       with the remote out the pins stand {RISER_TOP + PIN_FREE - SEAT_Z:.1f} mm above the pocket floor")
    gap = PIN_WH[0] - PIN_BARREL[1]
    check(gap >= 0.15, f"barrels stand {RISER_TOP + PIN_BARREL[1] - SEAT_Z:.2f} mm above the pocket floor inside the "
                       f"cover's windows; at the shortest working height the barrel top stays {gap:.2f} mm under the pad")
    peg = RISER_TOP - PIN_PEG[1]
    check(peg - WB_FRONT_Z >= 5.0, f"pegs {PIN_PEG[1] - RISER[2]:.1f} mm below the {RISER[2]} mm riser, "
                                   f"{peg - WB_FRONT_Z:.1f} above the wiring board")
    flange_top = RISER_TOP + PIN_FLANGE[1] + PIN_RADIAL
    check(SEAT_Z - flange_top >= BARRIER_MIN, f"pocket floor {SEAT_Z - flange_top:.1f} mm over the pins' flange "
                                              f"recesses >= {BARRIER_MIN}")
    cov = {k: Pos(0, 0, SEAT_Z) * v for k, v in bc.cover_parts().items()}
    for k, c in cov.items():
        if k == "pin_pads":
            continue
        r = rp["pins"] & c
        check(r is None or r.volume < 0.001, f"pins clear the back cover's {k}")
    d = rp["pins"].distance_to(cov["pin_pads"])
    check(d < 0.02, f"pin tips on the pads (gap {d:.3f} mm)")
    for name, o in (("insert", ins), ("trim", tr)):
        for k in ("pins", "riser", "posts", "sleeves", "screws"):
            r = rp[k] & o
            v = r.volume if r is not None else 0.0
            check(v < 0.01, f"{k} clear the {name} ({v:.3f} mm3)")
    floor = SEAT_Z - (RISER_TOP + RISER_CLR)
    mag = SEAT_Z - MAGNET[2] - MAGNET_SETBACK
    check(floor >= BARRIER_MIN and mag - (RISER_TOP + RISER_CLR) >= BARRIER_MIN,
          f"pocket floor {floor:.1f} mm over the riser's pocket ({mag - RISER_TOP - RISER_CLR:.1f} under the magnet "
          f"recess) >= {BARRIER_MIN}")
    head = SEAT_Z - (RISER_TOP + M2_HEAD[1] + RISER_CLR)
    check(head >= BARRIER_MIN, f"pocket floor {head:.1f} mm over the riser screws' head recesses >= {BARRIER_MIN}")
    for x, y in BC_FINGERS:
        dw = SW_Y - WELL_IN[1] / 2 - y - barrel / 2
        check(dw >= BARRIER_MIN or abs(x) - WELL_IN[0] / 2 - barrel / 2 >= BARRIER_MIN,
              f"pin at ({x}, {y}) clear of the switch well")
        check(abs(x) - (MAGNET[0] / 2 + MAGNET_CLR) - barrel / 2 >= BARRIER_MIN, f"pin at ({x}, {y}) clear of the "
                                                                                  f"magnet recess")
    board = assembly.wiring_board()
    for k in ("posts", "sleeves"):
        r = rp[k] & board
        v = r.volume if r is not None else 0.0
        check(v < 0.05, f"spacer {k} clear of the wiring board's parts ({v:.2f} mm3)")
    import kicad_board
    zone = None
    try:
        from importlib import util
        spec = util.spec_from_file_location("parts", str(kicad_board.ROOT / "pcb" / "tools" / "parts.py"))
        m = util.module_from_spec(spec)
        spec.loader.exec_module(m)
        zone = m.SELV_ZONE
    except Exception as e:                                  # pragma: no cover - reported, not fatal
        print(f"       no SELV zone from pcb/tools/parts.py ({e})")
    check(POST_SPIGOT[1] < WB[2], f"spacer posts surface-mounted: the {POST_SPIGOT[1]} mm spigot ends "
                                  f"{WB[2] - POST_SPIGOT[1]:.1f} mm inside the {WB[2]} mm board, nothing reaches the "
                                  f"back (the PSU under them)")
    check(POST_THREAD[0] < POST_STACK[0], f"standoff's male thread {POST_THREAD[0]} mm ends inside the "
                                          f"{POST_STACK[0]} mm SMT spacer, short of the board and the PSU behind it")
    check(RISER[2] < RISER_SCREW_L <= RISER[2] + POST_THREAD[1],
          f"riser screw M2 x {RISER_SCREW_L}: {RISER_SCREW_L - RISER[2]:.1f} mm in the standoff's "
          f"{POST_THREAD[1]} mm thread")
    if zone:
        pads = sorted(tuple(v["pcb"][:2]) for k, v in m.PARTS.items() if v.get("mpn") == "9774070243R")
        check(pads == sorted(POSTS), f"spacer posts {sorted(POSTS)} match the wiring board's P1 / P2 {pads}")
        xs, ys = [p[0] for p in zone], [p[1] for p in zone]
        for x, y in POSTS:
            r = POST_SP[0] / 2 + 0.5
            ok = min(xs) + r <= x <= max(xs) - r and min(ys) + r <= y - WB_Y <= max(ys) - r
            check(ok, f"spacer post at ({x}, {y}) inside the wiring board's 5 V area")
    s0, s1 = BC_STEEL_Y - BC_STEEL[1] / 2, BC_STEEL_Y + BC_STEEL[1] / 2
    m0, m1 = MAGNET_REC_Y - MAGNET[1] / 2, MAGNET_REC_Y + MAGNET[1] / 2
    share = max(0.0, min(s1, m1) - max(s0, m0)) / MAGNET[1]
    print(f"       magnet over the cover's steel plate: {share * 100:.0f} % of its height (pull test: MEASUREMENTS)")


def jig_checks():
    """Steel plate hacksaw guide (D-52, D-81): the plate fits the pocket, the cut falls at the piece length, printable."""
    print("steel plate hacksaw guide (D-52, D-81)")
    import plate_jig as pj
    plate = pj.plate()
    for name, j in (("saw guide", pj.saw_guide()),):
        r = j & plate
        check(r is None or r.volume < 1e-6, f"{name}: plate fits the pocket ({JIG_CLR} mm round it)")
        check(len(j.solids()) == 1, f"{name}: one solid")
        overhangs(f"{name} (floor down)", j)
    from build123d import Box
    slot, below, above = JIG_SAW
    j = pj.saw_guide()
    probe = Pos(0, MAGNET[1], JIG_FLOOR - below / 2) * Box(MAGNET[0], slot - 0.1, below - 0.05)
    r = j & probe
    check(r is None or r.volume < 1e-6, f"saw slot {slot} mm at {MAGNET[1]} mm from the round end, {below} mm into "
                                        f"the floor: the blade cuts right through")


def main():
    dims()
    terminal_entry()
    ins = insert.build()
    tr = trim.build()
    solids(ins, tr)
    board_fit(ins)
    mounting(ins)
    msr2_model()
    msr_spacers(ins)
    ring_mount(ins)
    ring_checks(ins, tr)
    scd_vent_checks(tr, MSR_Y, MSR_BACK_Z, PT)
    msr_posts(tr, MSR_Y, MSR_BACK_Z, PT)
    ffc_checks(ins, tr)
    separation(ins, tr)
    barrier(ins)
    cover_checks()
    battery_free_checks(ins, tr)
    from export import PRINT_ORIENT
    print("printability")
    overhangs("insert (supports only under the seal lip and in the riser pocket, D-68)", PRINT_ORIENT["insert"](ins),
              supported=(0.0, RISER_TOP + RISER_CLR, RISER_TOP + M2_HEAD[1] + RISER_CLR))   # seal lip on the wall
    overhangs("trim", PRINT_ORIENT["trim"](tr), limit=3.5)  # vent windows bridge 3 mm
    import coupons
    overhangs("crush rib coupon (as modelled)", coupons.ribs())
    import backcover
    overhangs("back cover", backcover.cover())                 # printed back down
    jig_checks()
    print("FAILED: " + "; ".join(FAILS) if FAILS else "all checks passed")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
