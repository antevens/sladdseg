"""North American variant checks (run by `make check`). Every assert is a constraint.

Barrier test: air = (box cavity + space in front of the wall) - barrier, with the single 5 V pass-through plugged.
The air volume touching the back of the box (mains) must not reach the room or the face plate's low-voltage hollow.
"""
import sys
from build123d import Box, Pos, Rectangle, Vector
from params_na import *
from common import slab, rr, stadium
import checks as base
import kicad_board
from checks import FAILS, check, overhangs, pad_body_check, mic_column   # noqa: F401
import barrier_na
import face_plate_na

ROOT = kicad_board.ROOT
MB_PCB = ROOT / "pcb" / "na" / "kicad" / "na_mains_board.kicad_pcb"


def dims():
    print("dimensions")
    from math import radians, tan
    d = (SCREW_HEAD_D - SCREW_D) / 2 / tan(radians(SCREW_CSK / 2))
    check(SCREW_CSK == 82.0 and 3.5 < SCREW_D <= 3.7 and 6.65 <= SCREW_HEAD_D <= 7.0 and d <= SKIN,
          f"#6 screws: {SCREW_D} hole, {SCREW_CSK:.0f} deg countersink {SCREW_HEAD_D} across, {d:.2f} deep in the "
          f"{SKIN} skin (heads 6.05-6.65, ASME B18.6.3)")
    check(POCKET_OUT[0] <= PLUG[0] and POCKET_OUT[1] <= PLUG[1], f"pocket {POCKET_OUT[0]:.1f}x{POCKET_OUT[1]:.1f} inside plug {PLUG[0]:.1f}x{PLUG[1]:.1f}")
    check(MB[0] / 2 <= PLUG[0] / 2 and MB[1] / 2 + abs(MB_Y) <= PLUG[1] / 2,
          f"mains board {MB[0]} x {MB[1]} fits the box opening less clearance")
    check(FLANGE_OUT[0] >= SEAL[0] and FLANGE_OUT[1] >= SEAL[1], "flange covers the seal band on the wall")
    top = SEAT_Z - (WELL_FLOOR_Z + SW_ROCKER_H + SW_ROCKER_TOL)
    check(top >= SW_ROCKER_CLR - 1e-6, f"rocker top clears the remote's back by {top:.1f} mm at max tolerance")
    check(SW_BEZEL[0] <= WELL_IN[0] and SW_BEZEL[1] <= WELL_IN[1], "rocker flange fits the switch well")
    m = _well_margin()
    check(m >= 0.5, f"switch well inside the pocket footprint (corner margin {m:.1f} mm, no undercut)")
    alt = SEAT_Z - (WELL_FLOOR_Z + SW_ALT_ROCKER_H)
    print(f"       second-source rocker (E-Switch RA4, D-88): top {alt:.1f} mm under the remote's back (nominal)")
    pin_y = min(SW_Y, SW_Y + SW_SW_DIR * SW_SLOT_DY) - SW_PAD[1] / 2
    check(pin_y >= MB_Y + WAGO_Y + WAGO6[1] / 2, f"rocker slots (pad edge y {pin_y:.1f}) clear of the terminal block")
    check(PASS_E[0] * J2_POS[0] > 0, "5 V pass-through is on the same side as the 5 V connector")
    stack = SB_T + B2B_STACK + MSR[2] + MSR_SKIN_GAP + RADAR_WALL
    check(abs(PT - stack) < 1e-6, f"plate {PT} mm = sensor board {SB_T} + CN2 stack {B2B_STACK} + MSR-2 {MSR[2]} + gap "
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
    check(msr_top <= PLATE_Y + PH / 2 - SKIN, f"MSR-2 bay top {msr_top:.2f} inside face plate (<= {PLATE_Y + PH/2-SKIN})")
    check(SHT_AT[1] - SHT[1] / 2 - 0.4 >= PLATE_Y - PH / 2 + SKIN, "SHT40 bay inside face plate")
    deepest = min(MB_BACK_Z - WAGO6[2], MB_BACK_Z - IRM[2])
    left = BOX_D + deepest
    print(f"       board {MB_FRONT_Z:.1f}..{MB_BACK_Z:.1f} mm, deepest part {deepest:.1f} mm; "
          f"behind it in a {BOX_D} mm box: {left:.1f} mm, behind the board above the block: {BOX_D + MB_BACK_Z:.1f} mm")
    check(left >= WIRE_SPACE_MIN, f"at least {WIRE_SPACE_MIN} mm behind the terminal block / PSU")


def _behind(c, depth, e, box_c, box_size):
    """Gap from a block's closed back (centre c, depth along entry e) to a box; < 0 = overlap or in front."""
    back = c[0] * e[0] + c[1] * e[1] - depth / 2
    near = box_c[0] * e[0] + box_c[1] * e[1] + abs(e[0]) * box_size[0] / 2 + abs(e[1]) * box_size[1] / 2
    return back - near


def terminal_entry():
    print("terminal block entry vs. PSU")
    e = WAGO_ENTRY
    gap = _behind((WAGO_X, MB_Y + WAGO_Y), WAGO6[1], e, (IRM_C[0], MB_Y + IRM_C[1]), IRM[:2])
    check(gap >= WAGO_PSU_GAP, f"wire entries face {e}, PSU behind the block's closed back (gap {gap:.1f} mm "
          f">= {WAGO_PSU_GAP})")
    import kicad_board
    if not MB_PCB.exists():
        print("       no KiCad board, params only")
        return
    b = kicad_board.Board(MB_PCB, MB_Y)
    ke = b.entry_dir("J1")
    check(ke == tuple(float(v) for v in e), f"KiCad J1 entries face {ke}, params WAGO_ENTRY {e}")
    for ref, c, size in (("J1", (WAGO_X, MB_Y + WAGO_Y), WAGO6[:2]), ("PS1", (IRM_C[0], MB_Y + IRM_C[1]), IRM[:2])):
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


def msr_spacers(ins):
    """MSR-2 (D-68): on CN2 and three SMT spacers on the sensor board, each under a face plate post; the spacers on
    solid board on both sides, clear of the MSR-2's back parts and CN2's mate."""
    print("MSR-2 support: sensor board spacers (D-68)")
    import sensor_board_na
    import msr2
    from build123d import Cylinder
    rp = sensor_board_na.parts()
    mp = msr2.placed_parts(0, MSR_Y, MSR_BACK_Z)
    check(abs(MSR_NUT[1] - B2B_STACK) < 1e-6, f"spacers {MSR_NUT[1]} mm = the CN2 stack {B2B_STACK} mm: the MSR-2's "
                                               f"back rests on them with CN2 mated (both to be measured)")
    check(all(abs(x - px) < 1e-6 and abs(y - MSR_Y - py) < 1e-6 for (x, y), (px, py) in zip(MSR_SPACERS, MSR2_POSTS))
          and len(MSR_SPACERS) == len(MSR2_POSTS), "a spacer under each face plate post")
    r0 = MSR_NUT[0] / 2
    for i, (x, y) in enumerate(MSR_SPACERS):
        disc = Cylinder(r0 - 0.05, 0.1)
        top = (Pos(x, y, MSR_BACK_Z + 0.05) * disc) & mp["board"]
        foot = (Pos(x, y, SB_T - 0.05) * disc) & rp["sensor_board"]
        full = 3.14159 * (r0 - 0.05) ** 2 * 0.1
        ring_a = full - 3.14159 * (MSR_NUT_HOLE / 2) ** 2 * 0.1          # less its spigot hole
        a, f = (top.volume if top else 0.0) / full, (foot.volume if foot else 0.0) / ring_a
        check(a >= 0.9 and f >= 0.95, f"spacer {i + 1}: {a * 100:.0f} % under solid MSR-2 board, {f * 100:.0f} % on solid "
                                       f"sensor board round its spigot hole")
    sp = rp["spacers"]
    for name, o in (("MSR-2's back switches", mp["sw"]), ("CN2 mate", rp["cn2"]), ("MSR-2 board", mp["board"])):
        r = sp & o
        check(r is None or r.volume < 1e-4, f"spacers clear of the {name}")
    for k in ("cn2", "msr", "spacers"):
        r = rp[k] & ins
        v = r.volume if r is not None else 0.0
        check(v < 0.01, f"{k} clear of the barrier ({v:.3f} mm3)")
    r = rp["msr"] & rp["sensor_board"]
    v = r.volume if r is not None else 0.0
    check(v < 0.01, f"MSR-2 (back switches {MSR2_SW[2]} mm deep, CN2 stack {B2B_STACK}) clear of the sensor board's notches "
                    f"({v:.3f} mm3)")


def sensor_board_mount(ins):
    """Sensor board on the barrier (D-68): no flat back over it; crush ribs grip its window edge; the flange's land
    rests on its inner edge; the land and the taper print without supports."""
    print("sensor board on the barrier (D-68)")
    import sensor_board_na
    import barrier_na
    from build123d import Box, Cylinder
    rb = sensor_board_na.board()
    yc = (SB_Y[0] + SB_Y[1]) / 2
    over = Pos(0, yc, (SB_T + PT) / 2) * Box(2 * SB_HALF_W, SB_Y[1] - SB_Y[0], PT - SB_T)
    over -= slab(rr(*FLANGE_OUT, ISLAND_R + FLANGE), -1, PT + 1)
    for s in (-1, 1):
        over -= Pos(0, s * SCREW_PITCH / 2, PT / 2) * Cylinder(BOSS_R, PT + 2)
    r = ins & over
    check(r is None or r.volume < 0.01, f"no barrier over the sensor board beyond the flange ({r.volume if r else 0.0:.3f} mm3)")
    ribs = barrier_na.ribs()
    n = len(ribs.solids())
    w, interf = SB_RIB
    check(n == 4 * len(SB_RIBS), f"{n} crush ribs on the collar's outside")
    bite = ribs & rb
    v = bite.volume if bite else 0.0
    d = SB_WIN_CLR + interf
    want = n * w * interf * (SB_T - (SB_WIN_CLR + interf / 2))      # the 45 deg lead-in takes z < r
    check(abs(v - want) < 0.02 * want + 1e-3, f"ribs bite {interf} mm into the board's window edge ({v:.3f} mm3, "
                                              f"{n} x {w} wide above the {d:.2f} mm lead-in)")
    r = rb & ins
    rv = r.volume if r else 0.0
    check(abs(rv - v) < 1e-3, f"the board meets the barrier only at the ribs ({rv:.3f} mm3)")
    bb = ribs.bounding_box()
    check(bb.min.Z >= -1e-6 and bb.max.Z <= SB_T + 1e-6, f"ribs within the board's thickness, above the wall plane "
                                                           f"(z {bb.min.Z:.2f}..{bb.max.Z:.2f})")
    land = SB_WIN_CLR + SB_LAND
    band = slab(rr(*[v_ + 2 * land - 0.1 for v_ in SB_INNER[:2]], SB_INNER[2] + land), SB_T + 0.02, SB_T + 0.07) \
        - slab(rr(*SB_INNER), -1, PT)
    c = band & ins
    a = (c.volume if c else 0.0) / 0.05
    full = band.volume / 0.05
    check(SB_LAND >= 1.0 and a >= 0.7 * full, f"flange land {SB_LAND} mm over the board's inner edge, on it over "
                                                f"{a:.0f} of {full:.0f} mm2 (the #6 bosses and the FFC channel aside)")
    chk = (ins & (Pos(0, 0, SB_T - 0.05) * Box(300, 300, 0.1))) - slab(rr(*SEAL, PLUG_R + COLLAR_LIP), -1, 10)
    for s in (-1, 1):
        chk -= Pos(0, s * SCREW_PITCH / 2, 0) * Cylinder(BOSS_R + 0.01, 30)
    rest = (chk - ribs) if chk else None
    check(rest is None or rest.volume < 1e-3, "nothing of the barrier between the board and the wall but the collar, the "
                                              "#6 bosses and the ribs")


def mounting(ins):
    """Board standoffs (D-57): bosses, tapped holes, standoffs and screws against the board, KiCad holes."""
    print("board mounting (nylon standoffs)")
    from build123d import Cylinder
    import bilresa, standoff_na, assembly_na
    check(all(d >= s + 0.5 - 1e-6 for d, s in zip(MOUNT_THREAD_L, MOUNT_STUD)) and min(MOUNT_STUD) >= MOUNT_THREAD_MIN,
          f"tapped depths {MOUNT_THREAD_L} mm for the studs {MOUNT_STUD} (>= {MOUNT_THREAD_MIN} engaged, 1.5 x M3)")
    check(MOUNT_FACE_Z >= Z_BOT - 1e-6, f"boss faces at z {MOUNT_FACE_Z:.1f}, {STANDOFF_L} mm standoffs to the board, "
                                       f"{MOUNT_FACE_Z - Z_BOT:.1f} above the barrier's lowest point")
    depth = STANDOFF[2]
    sl, head_d, head_h = STANDOFF_SCREW
    eng = sl - MB[2]
    check(eng >= 2 * MOUNT_THREAD_D - 1e-6 and eng <= depth - 0.5, f"screw {eng:.1f} mm into the standoff's {depth} mm "
                                                                  f"thread (>= 2 x M3 in nylon, short of its end)")
    face = MOUNT_FACE_Z
    for (x, y), top, depth in zip(MOUNT_HOLES, MOUNT_BOSS_TOP, MOUNT_THREAD_L):
        tip = face + depth + MOUNT_TAP_D / 2
        shell = Pos(x, y, (face + tip + BARRIER_MIN) / 2) * Cylinder(MOUNT_TAP_D / 2 + BARRIER_MIN,
                                                                     tip + BARRIER_MIN - face)
        gap = (shell - barrier_na.mount_hole(x, y, depth)) - ins
        v = gap.volume if gap is not None else 0.0
        check(v < 0.05, f"hole at ({x:.1f}, {y:.1f}): {depth} mm thread with >= {BARRIER_MIN} mm wall "
                        f"({v:.2f} mm3 missing)")
        check(abs(x) + MOUNT_BOSS_D / 2 <= PLUG[0] / 2 and abs(y - MB_Y) + MOUNT_BOSS_D / 2 <= PLUG[1] / 2,
              f"boss at ({x:.1f}, {y:.1f}) inside the box-fit outline")
        reach = Pos(x, y, (face + top + CLR) / 2) * Cylinder(MOUNT_BOSS_D / 2 + CLR, top + CLR - face)
        r = reach & bilresa.build(SEAT_Z)
        check((r.volume if r is not None else 0.0) < 0.01, f"boss at ({x:.1f}, {y:.1f}) clears the remote by {CLR} mm")
    board = assembly_na.mains_board()
    r = standoff_na.placed() & board
    ov = r.volume if r is not None else 0.0
    src = "KiCad STEP" if assembly_na.MB_STEP.exists() else "envelope (no holes)"
    check(ov < 0.05 or not assembly_na.MB_STEP.exists(), f"standoffs and screws clear of the board's parts, screws "
                                                       f"through its holes ({src}: {ov:.2f} mm3)")
    check(MOUNT_HOLE_D >= MOUNT_THREAD_D + 0.2, f"board holes {MOUNT_HOLE_D} mm for the M3 screws")
    import kicad_board
    if MB_PCB.exists():
        b = kicad_board.Board(MB_PCB, MB_Y)
        for i, (x, y) in enumerate(MOUNT_HOLES, 1):
            k = b.origin(f"MH{i}")
            check(abs(k[0] - x) < 0.01 and abs(k[1] - (MB_Y + y)) < 0.01,
                  f"KiCad MH{i} at ({k[0]:.2f}, {k[1]:.2f}) matches params MOUNT_HOLES")
        k = b.origin("J2")
        check(abs(k[0] - J2_POS[0]) < 0.01 and abs(k[1] - (MB_Y + J2_POS[1])) < 0.01,
              f"KiCad J2 at ({k[0]:.2f}, {k[1]:.2f}) matches params J2_POS")


def sensor_board_checks(ins, tr):
    """Sensor board (D-50, D-68): inside the face plate, copper keep-out from the box opening, the parts on it in
    copper-allowed places, the MSR-2 behind the radar skin, the mic under its sound column."""
    print("sensor board (D-50)")
    import sensor_board_na, bilresa
    rp = sensor_board_na.parts()
    for k in ("sensor_board", "spacers", "cn2", "msr", "j1", "sht45", "passives", "mic"):
        for on, o in (("barrier", ins), ("face plate", tr)):
            if k == "sensor_board" and on == "barrier":
                continue                                    # the crush ribs bite into it: sensor_board_mount()
            r = rp[k] & o
            v = r.volume if r is not None else 0.0
            check(v < 0.01, f"{k} clears the {on} ({v:.3f} mm3)")
    band = SB_HALF_W - 0.2 - (BOX_W / 2 + SB_KEEP - SB_T)
    need = 4 * 0.15 + 3 * 0.15
    check(band >= need, f"side rails: {band:.2f} mm of front-layer copper beyond {SB_KEEP} mm from the box opening "
                        f"(SDA, SCL, 3.3 V, GND at 0.15 / 0.15 need {need:.2f})")
    k_front = SB_KEEP - SB_T

    def allowed(x, y, r):
        """Front-layer copper disc at (x, y), radius r, at least k_front (plan) from the box opening's rectangle."""
        dx, dy = max(abs(x) - BOX_W / 2, 0.0), max(abs(y) - BOX_H / 2, 0.0)
        return (dx * dx + dy * dy) ** 0.5 - r
    for name, (x, y), r in [("J1", SB_J1, max(FH12[:2]) / 2 + 0.5), ("SHT40", SHT_AT, 1.5),
                            ("microphone", (MIC_AT[0], MIC_BODY_Y), max(MIC[:2]) / 2 + 0.3),
                            ("CN2 mate", (MSR_CN2_X, MSR_Y), max(B2B) / 2 + 0.5)] + \
                           [(k, p, max(d[:2]) / 2 + 0.3) for k, (p, d) in SB_SMALL.items()] + \
                           [(f"spacer {i + 1}", p, MSR_NUT_PAD / 2) for i, p in enumerate(MSR_SPACERS)]:
        d = allowed(x, y, r)
        check(d >= k_front, f"{name} copper {d:.1f} mm from the box opening (front layer >= {k_front:.1f})")
    gap = (PT - RADAR_WALL) - (MSR_BACK_Z + MSR[2])
    check(abs(gap - MSR_SKIN_GAP) < 1e-6, f"MSR-2 on CN2, its front {gap:.2f} mm under the {RADAR_WALL} mm radar skin "
                                         f"(D-66; MSR[2] MEASURE)")
    mic_column(face_plate_na.mic_tube(), rp["mic"], rp["passives"], SB_T, MIC_AT, MIC_SKIN_HOLE_D)
    on_board = {k: rp[k] for k in ("passives", "mic", "j1", "spacers", "cn2", "sht45")}
    for a in on_board:
        for b in on_board:
            if a < b:
                r = on_board[a] & on_board[b]
                check(r is None or r.volume < 1e-6, f"sensor board parts: {a} clear of {b}")
    from build123d import Cylinder
    probe = Pos(*MIC_AT, (SKIN_Z + PT) / 2) * Cylinder(MIC_SKIN_HOLE_D / 2 - 0.05, SKIN - 0.1)
    r = probe & tr
    check(r is None or r.volume < 0.001, "sound hole open through the face skin")
    r = rp["sensor_board"] & bilresa.build(SEAT_Z)
    check(r is None or r.volume < 0.001, "sensor board clears the remote")


def ffc_checks(ins, tr):
    """5 V FFC (D-50, D-68, D-74): stock 6-way cable through the pass-through, out of the flange onto the sensor board,
    its spare folded flat beside J1, clear of everything else."""
    print("5 V FFC")
    import jumper_na, sensor_board_na, bilresa, standoff_na
    from math import hypot
    diag = hypot(JUMPER_END[0], JUMPER_END[2])
    check(diag <= PASS_D - 0.5 and JUMPER_END[0] <= PASS_SLOT[0] - 0.5 and JUMPER_END[2] <= PASS_SLOT[1] - 0.3,
          f"FFC contact end ({JUMPER_END[0]} x {JUMPER_END[2]}) threads the {PASS_D} mm pass-through and its "
          f"{PASS_SLOT[0]} x {PASS_SLOT[1]} slot")
    need = jumper_na.length() + 2 * JUMPER_END[1]
    slack = JUMPER_STOCK_L - need
    check(JUMPER_SLACK[0] <= slack <= JUMPER_SLACK[1],
          f"FFC route {jumper_na.length():.0f} mm + {JUMPER_END[1]} mm into each connector leaves {slack:.1f} mm of the "
          f"{JUMPER_STOCK_L:.0f} mm stock cable to bow in the free span ({JUMPER_SLACK[0]}..{JUMPER_SLACK[1]}); no loop")
    fold = jumper_fold()
    lo_y, hi_y = JUMPER_FOLD_Y - JUMPER_W / 2, JUMPER_FOLD_Y + JUMPER_W / 2
    check(fold > 2.0 and lo_y >= FLANGE_OUT[1] / 2 + 0.2 - 1e-6 and hi_y <= SB_J1[1] - FH12[1] / 2 - 0.2 + 1e-6,
          f"spare length folded flat in four {fold:.1f} mm layers on the sensor board (y {lo_y:.2f}..{hi_y:.2f}: beyond "
          f"the flange, short of J1's body)")
    xl = SB_J1[0] - fold - JUMPER_W / 2
    check(xl >= BOSS_R + 1.0, f"fold ends at x {xl:.1f}, clear of the #6 screw boss (r {BOSS_R})")
    # the straight bore (D-74): walls to the remote pocket and the standoffs' tapped holes, the mouth inside the plug,
    # the groove where it opens through the corner taper, threading (one bend, into the slot)
    from build123d import Cylinder
    m, e, f = pass_points()
    r = PASS_D / 2
    bore = barrier_na.bore()
    pocket = slab(stadium(*POCKET_IN), SEAT_Z, PT + 5)
    d = bore.distance_to(pocket)
    check(d >= BARRIER_MIN - 1e-6, f"bore {d:.2f} mm from the remote pocket (>= {BARRIER_MIN})")
    tap = min(bore.distance_to(barrier_na.mount_hole(x, y, t)) for (x, y), t in zip(MOUNT_HOLES, MOUNT_THREAD_L))
    check(tap >= 1.2, f"bore {tap:.2f} mm from the nearest standoff's tapped hole (>= 1.2)")
    bosses = barrier_na.mount_bosses()
    d = bore.distance_to(bosses)
    check(d >= MOUNT_PASS_GAP - 1e-6 or tap >= 1.2, f"bore clears the standoff bosses' tapped holes ({d:.2f} mm to a boss "
                                                     f"face, inside the boss: {tap:.2f} mm to the hole)")
    edge = min(BOX_W / 2 - abs(m[0]), BOX_H / 2 - abs(m[1]))
    check(edge >= 6.0, f"bore's axis at the underside plane ({m[0]:.1f}, {m[1]:.1f}), {edge:.1f} mm in from the box wall")
    from math import atan2, degrees
    run = hypot(e[0] - m[0], e[1] - m[1])
    ang = degrees(atan2(e[2] - m[2], run))
    print(f"       bore {hypot(run, e[2] - m[2]):.1f} mm long, {ang:.0f} deg from horizontal; one bend, into the slot")
    env = barrier_na.outline_solid()
    below = Pos(0, 0, -50 + Z_BOT + 0.05) * Box(200, 200, 100)
    groove = (bore - env) - below
    top = groove.bounding_box().max.Z if groove is not None and groove.volume > 1e-3 else Z_BOT
    check(top <= -3.0, f"bore closed above z {top:.1f}: the groove below opens through the corner taper, at least 3 mm "
                       f"under the wall plane")
    probe = Pos(m[0], m[1], Z_BOT - 0.5) * Cylinder(r - 0.3, 1.0)
    r_ = probe & ins
    check(r_ is None or r_.volume < 0.01, "bore's mouth open on the underside")
    jmp = jumper_na.build()["jumper"]
    rp = sensor_board_na.parts()
    others = {"barrier": ins, "face plate": tr, "board standoffs": standoff_na.placed(), "remote": bilresa.build(SEAT_Z),
              "pin_board": rp["pin_board"], "spacer posts": rp["posts"] + rp["sleeves"], "MSR-2": rp["msr"]}
    for on, o in others.items():
        r = jmp & o
        v = r.volume if r is not None else 0.0
        check(v < 0.05, f"FFC clears the {on} ({v:.3f} mm3)")
    slab_ = Pos(0, MB_Y, MB_FRONT_Z - MB[2] / 2) * Box(*MB)
    r = jmp & slab_
    check(r is None or r.volume < 0.01, "FFC clears the mains board's slab")


def separation(ins, tr):
    """R9 / D-50: the face plate carries no electronics: it is clear of every electrical part."""
    print("face plate: no electrical parts (D-50)")
    import sensor_board_na, jumper_na, assembly_na
    rp = sensor_board_na.parts()
    parts = {k: rp[k] for k in ("sensor_board", "spacers", "cn2", "msr", "j1", "sht45", "passives", "mic", "pin_board", "pins",
                                "posts")}
    parts["FFC"] = jumper_na.build()["jumper"]
    parts["mains board"] = assembly_na.mains_board()
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
    check(ins.is_valid and len(ins.solids()) == 1, "barrier is one valid solid")
    check(tr.is_valid and len(tr.solids()) == 1, "face plate is one valid solid")
    ov = (ins & tr).volume
    check(ov < 0.01, f"barrier and face plate do not overlap ({ov:.3f} mm3)")
    import bilresa
    r = bilresa.build(SEAT_Z) & ins
    ov = r.volume if r is not None else 0.0
    check(ov < 0.01, f"BILRESA model clears the pocket ({ov:.3f} mm3)")


def board_fit(ins):
    print("mains board in the barrier")
    import assembly_na
    board = assembly_na.mains_board()
    ov, rocker_ov = 0.0, 0.0
    for sol in board.solids():
        r = sol & ins
        v = r.volume if r is not None else 0.0
        if sol.bounding_box().max.Z > PANEL_BOT_Z:   # only the rocker reaches through the panel
            rocker_ov += v
        else:
            ov += v
    src = "KiCad STEP" if assembly_na.MB_STEP.exists() else "envelope"
    check(ov < 0.5, f"board and parts ({src}) do not collide with the barrier ({ov:.2f} mm3)")
    print(f"       rocker model vs. panel cutout: {rocker_ov:.2f} mm3 (snap fit; cutout and body per the "
          f"Marquardt drawing tolerances, see the well/cutout checks)")
    if assembly_na.MB_STEP.exists():
        slab_ = max(board.solids(), key=lambda q: q.bounding_box().size.X * q.bounding_box().size.Y).bounding_box()
        check(abs(slab_.size.X - MB[0]) < 0.05 and abs(slab_.size.Y - MB[1]) < 0.05,
              f"KiCad board {slab_.size.X:.2f} x {slab_.size.Y:.2f} matches params MB {MB[0]} x {MB[1]}")


def barrier(ins, plain=False, switch=False):
    print("barrier" + (" (switch-only barrier, D-122)" if switch else " (plain barrier, D-109)" if plain else ""))
    room = slab(rr(PW + 20, PH + 20, 5), 0, PT + 10)
    box = slab(Rectangle(BOX_W, BOX_H), -BOX_D, 0)
    # plug the openings that are closed by something else when installed: the 5 V pass-through (FFC; the plain barrier
    # has none), the rocker cutout (the certified rocker body) and the two spring pins' holes in the pocket floor
    # (the pins, D-50)
    rocker = Pos(0, SW_Y, 0) * slab(Rectangle(*SW_CUT), PANEL_BOT_Z - 1, WELL_FLOOR_Z + 1)
    import sensor_board_na
    air = (room + box) - ins - rocker
    if not switch:
        air -= sensor_board_na.pin_holes()                            # pins fill their holes (D-50)
    if not plain:
        air -= barrier_na.pass_through()
    parts = air.solids()
    mains = [s for s in parts if s.is_inside(Vector(0, 0, -BOX_D + 1))]
    check(len(mains) == 1, "found the mains air volume")
    m = mains[0]
    for name, p in [("room in front of the face", (0, 0, PT + 5)),
                    ("remote pocket", (0, 0, SEAT_Z + 1)),
                    ("face plate hollow (low-voltage)", (28.0, 60.0, 5)),
                    ("MSR-2 bay", (0, MSR_Y, 5)),
                    ("sensor board space beside the plug", (-30.0, 0.0, SB_T / 2))]:
        check(not m.is_inside(Vector(*p)), f"mains air does not reach the {name}")
    check(m.bounding_box().max.Z <= 0.01, f"mains air stays behind the wall plane (max z {m.bounding_box().max.Z:.2f})")


def battery_free_checks(ins, tr):
    """Battery-free remote, NA (D-50): two spring pins from the mains board's 5 V area through the pocket floor onto
    the back cover flex's pads; pin board in a pocket under the floor; posts on the board's 5 V area."""
    print("battery-free remote, NA (D-50)")
    import backcover as bc
    import sensor_board_na, assembly_na
    rp = sensor_board_na.parts()
    import barrier_na as insm
    relief, hooks = sensor_board_na.pin_board_clips()
    above = insm.magnet_recess() + sensor_board_na.pin_holes() + slab(stadium(*POCKET_IN), SEAT_Z, PT + 5)
    hit = Pos(0, 0, POCKET_WALL - 0.01) * relief & above
    check(hit is None or hit.volume < 1e-4, f"pin board clip relief slots {POCKET_WALL} mm or more under the steel recess, the "
                                            f"pin holes and the remote pocket (D-91)")
    fw, ft, hd, g = PB_CLIP
    w, hgt, _ = PB
    over = [round(min(abs(hb.bounding_box().max.X - (PB_C[0] - w / 2)), abs(hb.bounding_box().min.X - (PB_C[0] + w / 2)),
                      abs(hb.bounding_box().min.Y - (PB_C[1] + hgt / 2))), 2) for hb in hooks.solids()]
    zc = max(hb.bounding_box().max.Z for hb in hooks.solids())
    L = (SEAT_Z - POCKET_WALL) - min(hb.bounding_box().min.Z for hb in hooks.solids())
    check(len(hooks.solids()) == len(PB_CLIPS) and all(abs(o - hd) < 0.01 for o in over)
          and abs(PB_BOT - zc - PB_CLIP_PLAY) < 1e-3,
          f"pin board clips {len(PB_CLIPS)}: hooks {hd} mm under the pin board's back face, catch {PB_CLIP_PLAY} below it; "
          f"fingers {ft} x {fw}, {L:.1f} mm free (bending strain at {hd} mm deflection {1.5 * ft * hd / L ** 2 * 100:.1f} %)")
    for k in ("pins", "posts", "sleeves", "screws"):
        r = hooks & rp[k]
        check(r is None or r.volume < 1e-4, f"pin board clip hooks clear the {k}")
    barrel = PIN_BARREL[0]
    lo, hi = PIN_WORK - PIN_TOL, PIN_WORK + PIN_TOL
    check(lo >= PIN_WH[0] - 1e-6 and hi <= PIN_WH[2] + 1e-6,
          f"pins at {PIN_WORK:.2f} mm working height, +-{PIN_TOL} -> {lo:.2f}..{hi:.2f} inside {PIN_WH[0]}..{PIN_WH[2]} "
          f"(Harwin P70-2200045; posts {POST_STACK[0]} + {POST_STACK[1]} mm)")
    print(f"       with the remote out the pins stand {PB_TOP + PIN_FREE - SEAT_Z:.1f} mm above the pocket floor")
    gap = PIN_WH[0] - PIN_BARREL[1]
    check(gap >= 0.15, f"barrels stand {PB_TOP + PIN_BARREL[1] - SEAT_Z:.2f} mm above the pocket floor inside the "
                       f"cover's windows; at the shortest working height the barrel top stays {gap:.2f} mm under the pad")
    peg = PB_TOP - PIN_PEG[1]
    check(peg - MB_FRONT_Z >= 5.0, f"pegs {PIN_PEG[1] - PB[2]:.1f} mm below the {PB[2]} mm pin board, "
                                   f"{peg - MB_FRONT_Z:.1f} above the mains board")
    flange_top = PB_TOP + PIN_FLANGE[1] + PIN_RADIAL
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
    for name, o in (("barrier", ins), ("face plate", tr)):
        for k in ("pins", "pin_board", "posts", "sleeves", "screws"):
            r = rp[k] & o
            v = r.volume if r is not None else 0.0
            check(v < 0.01, f"{k} clear the {name} ({v:.3f} mm3)")
    floor = SEAT_Z - (PB_TOP + PB_CLR)
    mag = SEAT_Z - MAGNET[2] - MAGNET_SETBACK
    check(floor >= BARRIER_MIN and mag - (PB_TOP + PB_CLR) >= BARRIER_MIN,
          f"pocket floor {floor:.1f} mm over the pin board's pocket ({mag - PB_TOP - PB_CLR:.1f} under the magnet "
          f"recess) >= {BARRIER_MIN}")
    head = SEAT_Z - (PB_TOP + M2_HEAD[1] + PB_CLR)
    check(head >= BARRIER_MIN, f"pocket floor {head:.1f} mm over the pin board screws' head recesses >= {BARRIER_MIN}")
    for x, y in BC_FINGERS:
        dw = SW_Y - WELL_IN[1] / 2 - y - barrel / 2
        check(dw >= BARRIER_MIN or abs(x) - WELL_IN[0] / 2 - barrel / 2 >= BARRIER_MIN,
              f"pin at ({x}, {y}) clear of the switch well")
        check(abs(x) - (MAGNET[0] / 2 + MAGNET_CLR) - barrel / 2 >= BARRIER_MIN, f"pin at ({x}, {y}) clear of the "
                                                                                  f"magnet recess")
    board = assembly_na.mains_board()
    for k in ("posts", "sleeves"):
        r = rp[k] & board
        v = r.volume if r is not None else 0.0
        check(v < 0.05, f"spacer {k} clear of the mains board's parts ({v:.2f} mm3)")
    zone = None
    try:
        from importlib import util
        spec = util.spec_from_file_location("parts", str(ROOT / "pcb" / "na" / "tools" / "parts_na.py"))
        m = util.module_from_spec(spec)
        spec.loader.exec_module(m)
        zone = m.SELV_ZONE
    except Exception as e:                                  # pragma: no cover - reported, not fatal
        print(f"       no SELV zone from pcb/na/tools/parts_na.py ({e})")
    check(POST_SPIGOT[1] < MB[2], f"spacer posts surface-mounted: the {POST_SPIGOT[1]} mm spigot ends "
                                  f"{MB[2] - POST_SPIGOT[1]:.1f} mm inside the {MB[2]} mm board, nothing reaches the "
                                  f"back (the PSU under them)")
    check(POST_THREAD[0] < POST_STACK[0], f"standoff's male thread {POST_THREAD[0]} mm ends inside the "
                                          f"{POST_STACK[0]} mm SMT spacer, short of the board and the PSU behind it")
    check(PB[2] < PB_SCREW_L <= PB[2] + POST_THREAD[1],
          f"pin board screw M2 x {PB_SCREW_L}: {PB_SCREW_L - PB[2]:.1f} mm in the standoff's "
          f"{POST_THREAD[1]} mm thread")
    if zone:
        pads = sorted(tuple(v["pcb"][:2]) for k, v in m.PARTS.items() if v.get("mpn") == "9774070243R")
        check(pads == sorted(POSTS), f"spacer posts {sorted(POSTS)} match the mains board's P1 / P2 {pads}")
        xs, ys = [p[0] for p in zone], [p[1] for p in zone]
        for x, y in POSTS:
            r = POST_SP[0] / 2 + 0.5
            ok = min(xs) + r <= x <= max(xs) - r and min(ys) + r <= y - MB_Y <= max(ys) - r
            check(ok, f"spacer post at ({x}, {y}) inside the mains board's 5 V area")
    s0, s1 = BC_STEEL_Y - BC_STEEL[1] / 2, BC_STEEL_Y + BC_STEEL[1] / 2
    m0, m1 = MAGNET_REC_Y - MAGNET[1] / 2, MAGNET_REC_Y + MAGNET[1] / 2
    share = max(0.0, min(s1, m1) - max(s0, m0)) / MAGNET[1]
    print(f"       magnet over the cover's steel plate: {share * 100:.0f} % of its height (pull test: MEASUREMENTS)")


def edge_chamfer(tr):
    """The face plate's front edge chamfer is the same all round: nothing added inside the plate fills it."""
    from build123d import Box
    c, top = FACE_CHAMFER, PLATE_Y + PH / 2
    filled = []
    for x in (-PW / 2 + 8, 0.0, 15.0, PW / 2 - 8):
        for y, s in ((top, -1), (PLATE_Y - PH / 2, 1)):
            probe = Pos(x, y + s * c * 0.25, PT - c * 0.25) * Box(0.1, 0.1, 0.1)   # inside the chamfer's cut corner
            r = probe & tr
            if r is not None and r.volume > 1e-6:
                filled.append((x, round(y, 1)))
    check(not filled, f"face plate: front edge chamfer {c} mm all round (filled at {filled})" if filled else
          f"face plate: front edge chamfer {c} mm all round, also over the MSR-2 and SHT40 bays")


def switch_checks():
    """Switch-only plate (D-122): the barrier without spring-pin holes, pin board pocket or cable bore, the plain face plate;
    the mains board carries only the rocker switch and the terminal block."""
    print("switch-only plate (rocker switch and terminal block, D-122)")
    ins, tr = barrier_na.build(switch=True), face_plate_na.build(plain=True)
    check(ins.is_valid and len(ins.solids()) == 1, "switch-only barrier: one valid solid")
    r = ins & tr
    check(r is None or r.volume < 0.01, f"switch-only barrier and plain face plate do not overlap "
                                        f"({r.volume if r else 0.0:.3f} mm3)")
    from build123d import Cylinder
    open_ = []
    for x, y in BC_FINGERS:                                 # through the pocket floor, under the seat
        probe = Pos(x, y, SEAT_Z - 0.5) * Cylinder(0.3, 0.4)
        r = probe & ins
        if r is None or r.volume < 0.99 * probe.volume:
            open_.append((x, y))
    check(not open_, "switch-only barrier: the pocket floor is solid where the spring pins would pass"
                     + (f" (open at {open_})" if open_ else ""))
    barrier(ins, plain=True, switch=True)
    from export import PRINT_ORIENT
    overhangs("switch-only barrier", PRINT_ORIENT["na_switch_barrier"](ins), supported=(0.0,))   # seal lip on the wall


def plain_checks():
    """Plain plate (D-109): the barrier without the 5 V cable bore and the standard-size face plate, on the same wiring
    board, pin board and spring pins as the full plate."""
    print("plain plate (rocker and battery-free remote, D-109)")
    ins, tr = barrier_na.build(plain=True), face_plate_na.build(plain=True)
    check(ins.is_valid and len(ins.solids()) == 1 and tr.is_valid and len(tr.solids()) == 1,
          "plain barrier and plain face plate are one valid solid each")
    bb = tr.bounding_box()
    check(abs(bb.size.X - PLAIN_PW) < 0.01 and abs(bb.size.Y - PLAIN_PH) < 0.01 and abs(bb.center().Y) < 0.01,
          f"plain face plate {bb.size.X:.2f} x {bb.size.Y:.2f} mm, centred on the box (standard single-gang plate)")
    wall = (PLAIN_PW - FLANGE_OUT[0]) / 2 - SPLIT_CLR
    check(wall >= PLAIN_WALL_MIN, f"plain face plate side wall beside the barrier's flange {wall:.2f} mm "
                                  f"(>= {PLAIN_WALL_MIN})")
    check(PLAIN_PH / 2 - SCREW_PITCH / 2 - SCREW_HEAD_D / 2 >= 5.0,
          f"plain face plate: {PLAIN_PH / 2 - SCREW_PITCH / 2 - SCREW_HEAD_D / 2:.1f} mm beyond each screw head")
    r = ins & tr
    ov = r.volume if r is not None else 0.0
    check(ov < 0.01, f"plain barrier and plain face plate do not overlap ({ov:.3f} mm3)")
    import bilresa
    r = bilresa.build(SEAT_Z) & ins
    ov = r.volume if r is not None else 0.0
    check(ov < 0.01, f"BILRESA model clears the plain barrier's pocket ({ov:.3f} mm3)")
    env = barrier_na.pass_through() & barrier_na.outline_solid()       # the pass-through within the barrier's outline
    sol = barrier_na.pass_through() & ins
    v_env, v_sol = env.volume, (sol.volume if sol is not None else 0.0)
    check(abs(v_env - v_sol) < 0.5, f"plain barrier: the 5 V pass-through's space is solid ({v_sol:.1f} of {v_env:.1f} mm3)")
    import sensor_board_na, assembly_na
    rp = sensor_board_na.parts()
    for name, p in {**{k: rp[k] for k in ("pin_board", "pins", "posts")}, "mains board": assembly_na.mains_board()}.items():
        d = tr.distance_to(p)
        check(d >= 0.05, f"plain face plate not touching the {name} (gap {d:.2f} mm)")
    barrier(ins, plain=True)
    from export import PRINT_ORIENT
    overhangs("plain barrier", PRINT_ORIENT["na_plain_barrier"](ins),
              supported=(0.0, PB_TOP + PB_CLR, PB_TOP + M2_HEAD[1] + PB_CLR))
    overhangs("plain face plate", PRINT_ORIENT["na_plain_face_plate"](tr), limit=3.5)


def main():
    dims()
    terminal_entry()
    ins = barrier_na.build()
    tr = face_plate_na.build()
    solids(ins, tr)
    edge_chamfer(tr)
    board_fit(ins)
    mounting(ins)
    msr_spacers(ins)
    sensor_board_mount(ins)
    sensor_board_checks(ins, tr)
    base.scd_vent_checks(tr, MSR_Y, MSR_BACK_Z, PT)
    base.msr_posts(tr, MSR_Y, MSR_BACK_Z, PT)
    ffc_checks(ins, tr)
    separation(ins, tr)
    barrier(ins)
    battery_free_checks(ins, tr)
    from export import PRINT_ORIENT
    print("printability")
    overhangs("barrier (supports only under the seal lip and in the pin board pocket, D-68)", PRINT_ORIENT["na_barrier"](ins),
              supported=(0.0, PB_TOP + PB_CLR, PB_TOP + M2_HEAD[1] + PB_CLR))   # seal lip on the wall
    overhangs("face plate", PRINT_ORIENT["na_face_plate"](tr), limit=3.5)  # vent windows bridge 3 mm
    import coupons_na
    overhangs("crush rib coupon (as modelled)", coupons_na.ribs())
    plain_checks()
    switch_checks()
    print("FAILED: " + "; ".join(FAILS) if FAILS else "all checks passed")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
