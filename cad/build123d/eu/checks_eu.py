"""EU variant checks (D-30), run by `make eu`.

Barrier test as in checks_na.py: air = (box cavity less its four screw domes + space in front of the
wall) - barrier, with the rocker cutout (closed by the rocker body) and the four spring-pin holes
(pin barrels) plugged. The air touching the back of the box (mains) must stay behind the wall plane.
"""
import sys
from math import cos, hypot, radians, sin
from build123d import Box, Cylinder, Pos, Rectangle, Rot, Vector
from params_eu import *
from common import rr, slab
import checks as base
import barrier_eu
import face_plate_eu
import boards_eu
import sensor_board_eu

check = base.check


def _corners(cx, cy, w, h):
    return [(cx + sx * w / 2, cy + sy * h / 2) for sx in (-1, 1) for sy in (-1, 1)]


def _rmax(cx, cy, w, h):
    return max(hypot(x, y) for x, y in _corners(cx, cy, w, h))


def _in_stadium(x, y, w, h):
    """Point inside a stadium w x h (long axis y) centred on the origin."""
    r = w / 2
    yc = max(0.0, abs(y) - (h / 2 - r))
    return hypot(x, yc) <= r


def layout():
    print("layout")
    print(f"       plate {PW:.1f} x {PH:.1f} mm, {PT:.1f} mm proud (remote {B_PROUD} mm beyond it), centre y {PC[1]:.1f} from the box "
          f"centre; barrier Ø{2 * CAP_R:.1f} x {CAP_T} mm")
    floor = MAGNET_Z[0] - MAG_CUP_BOT
    check(min(CAP_T, floor) >= V0_RATED_T, f"barrier {CAP_T} mm and the steel piece's cup floor {floor:.1f} mm >= "
                                          f"{V0_RATED_T} mm (V-0 rated thickness)")
    lim = BOX_R - PLUG_CLR
    r = _rmax(0, SW_Y, *CUP_OUT)
    check(r <= lim, f"switch cup inside the box (corner r {r:.2f} <= {lim:.2f})")
    hidden = all(_in_stadium(x, y, B_W - 2.0, B_H - 2.0) for x, y in _corners(0, SW_Y, *CUP_IN))
    check(hidden, "switch cup under the remote (1 mm inside its outline)")
    for x, y in SCREWS:
        check(abs(hypot(x, y) - BOX_R) < 1e-6 and DOME_D - SCREW_D >= 2.0,
              f"barrier screw at ({x:.0f}, {y:.0f}) on a box dome's axis (Ø{SCREW_D} in Ø{DOME_D})")
        inside = all(_in_stadium(x + dx, y + dy, POCKET_IN[0] - 1.0, POCKET_IN[1] - 1.0)
                     for dx, dy in ((SCREW_HEAD_D / 2, 0), (-SCREW_HEAD_D / 2, 0), (0, SCREW_HEAD_D / 2),
                                    (0, -SCREW_HEAD_D / 2)))
        cup = abs(y - SW_Y) - CUP_OUT[1] / 2 - SCREW_HEAD_D / 2
        check(inside and cup >= 1.0, f"barrier screw head in the pocket floor under the remote, {cup:.1f} mm from the cup")
    for x, y in PINS:
        r = hypot(x, y) + PIN_PAD_D / 2
        check(r <= PB_R - 0.25, f"spring pin pad at ({x}, {y}) on the pin board (r {r:.2f} <= {PB_R - 0.25:.2f})")
        check(not _in_stadium(x - PIN_CAP_HOLE_D / 2 - 0.3, y, *POCKET_OUT),
              f"spring pin hole at ({x}, {y}) outside the pocket walls (opens under the carrier, beside the pocket)")
        d = min(hypot(x - dx, y - dy) for dx, dy in DOMES) - DOME_NOTCH_R - PIN_PAD_D / 2
        check(d >= 0.0, f"spring pin pad {d:.2f} mm clear of the board's dome notches")
    g = BARRIER_MIN + MAGNET_CLR
    r = _rmax(0, MAGNET_REC_Y, MAGNET[0] + 2 * g, MAGNET[1] + 2 * g)
    check(r <= lim, f"steel piece's cup inside the box (corner r {r:.2f} <= {lim:.2f}, D-72)")
    wall = (SW_Y - CUP_IN[1] / 2) - (MAGNET_REC_Y + MAGNET[1] / 2 + MAGNET_CLR)
    check(wall >= BARRIER_MIN - 1e-6, f"steel piece's recess {wall:.2f} mm from the switch cup (>= {BARRIER_MIN})")
    check(abs(MAGNET_Z[1] - (SEAT_Z - MAGNET_SETBACK)) < 1e-6 and MAGNET_Z[0] - MAG_CUP_BOT >= BARRIER_MIN - 1e-6,
          f"steel piece {MAGNET_SETBACK} mm below the seat, cup floor {MAGNET_Z[0] - MAG_CUP_BOT:.1f} mm under it")
    gap = MAG_CUP_BOT - PB_FRONT
    check(gap >= 0.5, f"cup {gap:.2f} mm over the pin board's front (>= 0.5)")
    s0, s1 = BC_STEEL_Y - BC_STEEL[1] / 2, BC_STEEL_Y + BC_STEEL[1] / 2
    m0, m1 = MAGNET_REC_Y - MAGNET[1] / 2, MAGNET_REC_Y + MAGNET[1] / 2
    share = max(0.0, min(s1, m1) - max(s0, m0)) / MAGNET[1]
    check(share >= 0.75, f"steel piece ({m0:.1f}..{m1:.1f}) {share * 100:.0f} % under the back cover's magnet "
                         f"({s0:.1f}..{s1:.1f})")
    top = PANEL_TOP_Z + SW_ROCKER_H + SW_ROCKER_TOL
    check(top <= SEAT_Z - SW_ROCKER_CLR + 1e-6, f"rocker top {top:.2f} under the remote's back ({SEAT_Z:.2f}) at max tolerance")
    print(f"       rocker panel {PANEL_TOP_Z:.1f}..{PANEL_BOT_Z:.1f}, PCB seat (mains board front) {MB_FRONT:.1f} mm")
    # mains board: PSU and WAGO blocks on the back, inside the board, clear of each other and the rocker's pins
    rects = {"PSU": (MB_PSU_C, (PSU[0], PSU[1]))}
    rects.update({f"WAGO block {k}": (c, (WAGO2[1], WAGO2[0])) for k, c in zip("LN", MB_WAGO_C)})
    for name, (c, (w, h)) in rects.items():
        r = _rmax(*c, w, h)
        check(r <= PB_R - 0.5, f"{name} on the mains board (corner r {r:.2f} <= {PB_R - 0.5:.2f})")
        for dx, dy in DOMES:
            gap = hypot(max(abs(dx - c[0]) - w / 2, 0), max(abs(dy - c[1]) - h / 2, 0)) - DOME_D / 2
            check(gap >= DOME_CLR - 1e-6, f"{name} {gap:.2f} mm from the dome at ({dx:.0f}, {dy:.0f})")
        for sx in (-1, 1):
            for sy in (0, SW_SW_DIR):
                px, py = sx * SW_PIN_GRID[0] / 2, SW_Y + sy * SW_SLOT_DY
                gap = max(abs(px - c[0]) - (w + SW_PAD[0]) / 2, abs(py - c[1]) - (h + SW_PAD[1]) / 2)
                need = S1_WAGO_BODY_GAP if name.startswith("WAGO") else 0.3
                check(gap >= need - 1e-6, f"{name} {gap:.2f} mm clear of the rocker slot at ({px:.1f}, {py:.1f}) (>= {need})")
    names = list(rects)
    for a in range(len(names)):
        for b in range(a + 1, len(names)):
            (c1, (w1, h1)), (c2, (w2, h2)) = rects[names[a]], rects[names[b]]
            gap = max(abs(c1[0] - c2[0]) - (w1 + w2) / 2, abs(c1[1] - c2[1]) - (h1 + h2) / 2)
            check(gap >= 0.8, f"{names[a]} {gap:.2f} mm from the {names[b]}")
    x0, x1, ys, w = MB_SLOT
    pin_out = MB_PSU_C[1] - PSU_ROWS / 2                   # PSU output row (Zettler ZPI03, datasheet)
    pin_in = MB_PSU_C[1] + PSU_ROWS / 2
    check(pin_out < ys - w / 2 - 1.0 and pin_in > ys + w / 2 + 1.0 and x1 - x0 >= PSU[0] + 6,
          f"relief slot under the PSU between its input row (y {pin_in:.1f}) and output row (y {pin_out:.1f}), "
          f"{x1 - x0:.0f} mm long")
    check(MB_HDR[1] - 2.54 - 1.0 > -PB_R and MB_HDR[1] + 1.0 < ys - w / 2, "header on the 5 V island below the slot")
    for x, y in MB_BOSS:
        r = hypot(x, y) + MB_BOSS_D / 2
        check(r <= lim, f"long boss at ({x}, {y}) inside the box (r {r:.2f})")
        cup = max(abs(x) - CUP_OUT[0] / 2, abs(y - SW_Y) - CUP_OUT[1] / 2) - MB_BOSS_D / 2
        check(cup >= 0.3, f"long boss at ({x}, {y}) {cup:.2f} mm from the switch cup")
        for name, (c, (w, h)) in rects.items():
            gap = hypot(max(abs(x - c[0]) - w / 2, 0), max(abs(y - c[1]) - h / 2, 0)) - M2_HEAD[0] / 2
            check(gap >= 0.3, f"mains board screw at ({x}, {y}) head {gap:.2f} mm from the {name}")
    check(HDR_ENGAGE >= 2.5, f"header posts {HDR_ENGAGE:.2f} mm into the pin board's socket ({HDR_GAP:.1f} mm between "
                            f"the boards; MEASURE with the parts)")
    left = BOX_D + DEEPEST
    print(f"       pin board {PB_FRONT:.1f}..{PB_BACK:.1f}; mains board {MB_FRONT:.1f}..{MB_BACK:.1f}, PSU to "
          f"{MB_BACK - PSU[2]:.1f}, WAGO to {MB_BACK - WAGO2[2]:.1f} (wires enter its back face)")
    print(f"       depth: deepest part {DEEPEST:.1f} mm, {left:.1f} mm left behind it in a {BOX_D} mm box "
          f"(wanted {WIRE_SPACE_MIN}; to be tested in a box, human decision 2026-10-08)")


def solids(cap, tr):
    print("solids")
    check(cap.is_valid and len(cap.solids()) == 1, f"barrier: one valid solid ({cap.volume / 1000:.1f} cm3)")
    check(tr.is_valid and len(tr.solids()) == 1, f"face plate: one valid solid ({tr.volume / 1000:.1f} cm3)")
    parts = boards_eu.parts()
    rem = boards_eu.remote()
    pairs = [("barrier", cap, "face plate", tr), ("remote", rem, "barrier", cap), ("remote", rem, "face plate", tr),
             ("remote", rem, "rocker", parts["switch"])]
    pairs += [(k, v, "barrier", cap) for k, v in parts.items() if k != "switch"]
    r = hypot(*max(PB_MOUNT, key=lambda q: hypot(*q))) + PB_BOSS_D / 2
    check(r <= BOX_R - PLUG_CLR, f"pin board bosses inside the box (r {r:.2f})")
    mb = parts["mains_board"]
    pairs += [("pin board", parts["board"], "rocker", parts["switch"]),
              ("pin board", parts["board"], "header", parts["header"]),
              ("mains board", mb, "PSU", parts["psu"]), ("mains board", mb, "WAGO blocks", parts["wago"]),
              ("rocker", parts["switch"], "mains board front parts", parts["mains_front"]),
              ("rocker", parts["switch"], "header", parts["header"]),
              ("WAGO blocks", parts["wago"], "PSU", parts["psu"]),
              ("magnet", parts["magnet"], "pin board", parts["board"]),
              ("pin board front parts", parts["front"], "magnet", parts["magnet"]),
              ("pin board front parts", parts["front"], "rocker", parts["switch"]),
              ("socket", parts["socket"], "mains board front parts", parts["mains_front"]),
              ("socket", parts["socket"], "header body", boards_eu.header_body())]
    for an, a, bn, b in pairs:
        r = a & b
        v = r.volume if r is not None else 0.0
        check(v < 0.05, f"{an} clears the {bn} ({v:.3f} mm3)")
    domes = boards_eu.domes()
    for k, v in {**parts, "barrier": cap}.items():
        r = v & domes
        vol = r.volume if r is not None else 0.0
        check(vol < 0.05, f"{k} clears the box's screw domes ({vol:.3f} mm3)")
    r = parts["switch"] & cap
    print(f"       rocker vs. barrier: {r.volume if r is not None else 0.0:.2f} mm3 (snap fit in the panel cutout)")
    import barrier_eu
    bosses = barrier_eu.mains_bosses()
    for k in ("board", "psu", "wago", "switch", "mains_front", "header", "socket", "front", "pins"):
        r = parts[k] & bosses
        v = r.volume if r is not None else 0.0
        check(v < 0.05, f"long barrier bosses clear the {k.replace('_', ' ')} ({v:.3f} mm3)")


def sensors(cap, tr):
    """Sensor board, carrier, MSR-2, microphone, SHT40 (D-56, D-70): pin heights, stack, clearances."""
    print("sensor board, MSR-2, microphone, SHT40 (D-56, D-59, D-70)")
    lo, hi = PIN_WORK - PIN_TOL, PIN_WORK + PIN_TOL
    check(lo >= PIN_WH[0] - 1e-6 and hi <= PIN_WH[2] + 1e-6,
          f"all four spring pins at {PIN_WORK} mm working height, +-{PIN_TOL} -> {lo:.1f}..{hi:.1f} inside "
          f"{PIN_WH[0]}..{PIN_WH[2]} (Harwin P70-2200045)")
    for name, tip in (("sensor pins (sensor board pads)", SB_PAD_Z), ("battery-free pins (back cover pads)", BF_TIP_Z)):
        check(abs(tip - PB_FRONT - PIN_WORK) < 1e-6, f"{name}: tips {tip - PB_FRONT:.2f} mm above the pin board")
    gap = PIN_WH[0] - PIN_BARREL[1]
    check(gap >= 0.15, f"at the shortest working height the barrel tops stay {gap:.2f} mm under the pads")
    holes = barrier_eu.pin_holes().solids()
    dia = sorted({round(2 * (h.bounding_box().size.X / 2), 3) for h in holes})
    check(len(holes) == len(PINS) + len(BC_FINGERS) and dia == [round(PIN_CAP_HOLE_D, 3)],
          f"{len(holes)} pin holes in the barrier, all Ø{PIN_CAP_HOLE_D:.2f} (D-80)")
    check(PIN_CAP_HOLE_D - PIN_BARREL[0] <= 0.4, f"barrier / carrier hole {PIN_CAP_HOLE_D:.2f} round the {PIN_BARREL[0]} mm pin "
                                                  f"barrel ({(PIN_CAP_HOLE_D - PIN_BARREL[0]) / 2:.2f} mm radial gap)")
    proud = SEAT_Z + B_D - PT
    check(abs(proud - B_PROUD) < 1e-6, f"remote {proud:.1f} mm proud of the face (face plate {PT:.1f} mm, D-70)")
    gap = (PT - RADAR_WALL) - (MSR_BACK_Z + MSR[2])
    check(gap >= MSR_SKIN_GAP - 1e-6, f"MSR-2 straight on the sensor board's CN2 mate: front {gap:.2f} mm under the radar "
                                      f"skin (>= {MSR_SKIN_GAP})")
    check(abs(MSR_NUT[1] - B2B_STACK) < 1e-6, f"sensor board spacers {MSR_NUT[1]} mm = the CN2 stack {B2B_STACK} mm")
    pocket_x = POCKET_OUT[0] / 2 + SB_POCKET_CLR
    for x, y in PINS:
        check(x - SB_PAD_D / 2 - pocket_x >= 0.3 - 1e-6, f"pad at ({x}, {y}) {x - SB_PAD_D / 2 - pocket_x:.2f} mm inside the "
                                                  f"sensor board's edge at the pocket")
    probe = Pos(*MIC_AT, (SKIN_Z + PT) / 2) * Cylinder(MIC_HOLE[0] / 2 - 0.05, SKIN - 0.1)
    r = probe & tr
    check(r is None or r.volume < 0.001, "microphone sound hole open through the face skin")
    cp = sensor_board_eu.parts()
    base.mic_column(face_plate_eu.mic_tube(), cp["mic"], cp["passives"], SB_TOP, MIC_AT, MIC_HOLE[0])
    d = cp["cn2"].distance_to(cp["msr"]) + cp["cn2"].distance_to(cp["sensor_board"])
    check(d < 0.01, "CN2 mate between the sensor board and the MSR-2's back")
    d = cp["spacers"].distance_to(cp["msr"]) + cp["spacers"].distance_to(cp["sensor_board"])
    check(d < 0.01, "spacers between the sensor board and the MSR-2's board")
    import msr2
    mb = msr2.placed_parts(0, MSR_Y, MSR_BACK_Z)["board"]
    for i, (x, y) in enumerate(MSR_SPACERS):
        disc = Pos(x, y, MSR_BACK_Z + 0.05) * Cylinder(MSR_NUT[0] / 2 - 0.05, 0.1)
        r = disc & mb
        a = (r.volume if r else 0.0) / disc.volume
        check(a >= 0.9, f"spacer {i + 1} {a * 100:.0f} % under solid MSR-2 board, under a face plate post")
    b = boards_eu.parts()
    others = {"barrier": cap, "face plate": tr, "remote": boards_eu.remote(), "box domes": boards_eu.domes(),
              "seated back cover": Pos(0, 0, SEAT_Z) * __import__("backcover").cover(), **b}
    mates = {("carrier", "sensor_board"), ("sensor_board", "cn2"), ("cn2", "msr"), ("sensor_board", "spacers"), ("spacers", "msr"),
             ("sensor_board", "passives"), ("sensor_board", "mic"), ("sensor_board", "sht45"), ("sensor_board", "sb_pads")}
    names = [k for k in cp if k != "sb_screws"]
    for i, pn in enumerate(names):
        for qn in names[i + 1:]:
            if (pn, qn) in mates or (qn, pn) in mates:
                continue
            r = cp[pn] & cp[qn]
            v = r.volume if r is not None else 0.0
            check(v < 0.05, f"{pn} clears the {qn} ({v:.3f} mm3)")
        for on, o in others.items():
            r = cp[pn] & o
            v = r.volume if r is not None else 0.0
            check(v < 0.05, f"{pn} clears the {on} ({v:.3f} mm3)")
    for on in ("face plate", "remote", "msr", "spacers", "cn2", "sht45"):
        o = others.get(on, cp.get(on))
        r = cp["sb_screws"] & o
        v = r.volume if r is not None else 0.0
        check(v < 0.05, f"sensor board screws clear the {on} ({v:.3f} mm3)")


def bf_checks(cap, tr):
    """Battery-free spring pins (D-54, D-59): from the pin board through the barrier onto the back cover's pads."""
    print("battery-free spring pins (D-54, D-59)")
    import backcover
    b = boards_eu.parts()
    bf = b["bf_pins"]
    print(f"       with the remote out the pins stand {PB_FRONT + PIN_FREE - SEAT_Z:.1f} mm above the pocket floor; "
          f"barrels {PB_FRONT + PIN_BARREL[1] - SEAT_Z:.2f} mm above it, inside the cover's windows")
    cov = {k: Pos(0, 0, SEAT_Z) * v for k, v in backcover.cover_parts().items()}
    for k, c in cov.items():
        if k == "pin_pads":
            continue
        r = bf & c
        check(r is None or r.volume < 0.001, f"pins clear the back cover's {k}")
    d = bf.distance_to(cov["pin_pads"])
    check(d < 0.02, f"pin tips on the pads (gap {d:.3f} mm)")
    for on, o in (("barrier", cap), ("face plate", tr), ("rocker", b["switch"]), ("pin board front parts", b["front"]),
                  ("sensor pins", b["pins"]), ("socket", b["socket"]), ("header", b["header"])):
        r = bf & o
        v = r.volume if r is not None else 0.0
        check(v < 0.01, f"battery-free pins clear the {on} ({v:.3f} mm3)")
    for x, y in BC_FINGERS:
        for mx, my in PB_MOUNT:
            g = hypot(x - mx, y - my) - PB_BOSS_D / 2 - PIN_FLANGE[0] / 2 - PIN_RADIAL
            check(g >= 0.5, f"pin at ({x}, {y}) clear of the board boss at ({mx}, {my}) ({g:.2f} mm)")
        for px, py in PINS:
            g = hypot(x - px, y - py) - PIN_PAD_D
            check(g >= 0.5, f"pin at ({x}, {y}) clear of the sensor pin pad at ({px}, {py}) ({g:.2f} mm)")
    seated = Pos(0, 0, SEAT_Z) * backcover.cover()
    for on, o in (("face plate", tr), ("rocker", b["switch"]), ("barrier", cap)):
        r = seated & o
        v = r.volume if r is not None else 0.0
        check(v < 0.05, f"seated back cover clears the {on} ({v:.3f} mm3)")
    print(f"       steel piece to the cover's magnet {MAGNET_SETBACK + BC_STEEL_FLOOR:.1f} mm (setback {MAGNET_SETBACK} + "
          f"cover {BC_STEEL_FLOOR}); "
          f"hold vs. 2 fingers >= 2 x 1.2 N: MEASURE")


def separation(tr):
    """R9 / D-56: the face plate carries no electronics: it is clear of every electrical part; only its posts rest on
    the MSR-2's board (D-67)."""
    print("face plate: no electrical parts (R9)")
    cp, b = sensor_board_eu.parts(), boards_eu.parts()
    parts = {k: cp[k] for k in ("sensor_board", "sb_pads", "cn2", "spacers", "passives", "mic", "sht45")}
    parts.update({k: b[k] for k in ("board", "pins", "bf_pins", "front", "socket", "mains_board", "header")})
    r = tr & cp["msr"]
    check(r is None or r.volume < 0.01, f"face plate posts rest on the MSR-2's board, no overlap "
                                        f"({r.volume if r else 0.0:.3f} mm3)")
    for name, p in parts.items():
        d = tr.distance_to(p)
        check(d >= 0.05, f"face plate not touching the {name} (gap {d:.2f} mm)")


def snaps(cap, tr):
    """Face plate snaps (D-70, D-77): four fingers from the face skin into closed windows in the sensor board and the
    carrier, keyed, the bump in the carrier's groove when the pocket walls sit on the barrier, room inside each finger to
    bend in; the carrier's inner edge whole; fingers clear of the barrier, the carrier and the sensor board."""
    print("face plate snaps (D-70, D-77)")
    from math import cos, radians, sin
    import face_plate_eu
    f = face_plate_eu.snaps()
    r = f & tr
    check(len(f.solids()) == 4 and r is not None and abs(r.volume - f.volume) < 0.01,
          f"{len(f.solids())} snap fingers, part of the face plate")
    check(SNAP_KEY_W > SNAP[0] + 2 * SNAP_CLR + 0.5, f"keyed: one finger and window {SNAP_KEY_W} wide, the others "
                                                     f"{SNAP[0]}: the plate fits one way only")
    t, d = SNAP[1], SNAP[2] - SNAP_BUMP_CLR
    length = DECK_Z - SNAP_TIP_Z
    strain = 1.5 * t * d / length ** 2
    check(strain <= 0.02, f"fingers {SNAP[0]} x {t} mm, {length:.1f} mm long: {strain * 100:.2f} % strain as the bump "
                          f"passes into the carrier's window (PETG <= 2 %)")
    z0, z1 = SNAP_GROOVE
    zm = (z0 + z1) / 2
    check(z0 < zm - d and zm + d < z1 and SNAP_TIP_Z >= 0.1, f"bump {zm - d:.1f}..{zm + d:.1f} inside the groove "
                                                             f"{z0}..{z1} with the pocket walls on the barrier; tips "
                                                             f"{SNAP_TIP_Z} over the wall")
    reach = SNAP_R + t + d - SNAP_WALL_R
    check(reach >= 0.3, f"bump reaches {reach:.2f} mm past the window's outer wall into the groove")
    room = SNAP_R - SNAP_WIN_R
    check(room >= d + 0.05, f"{room:.2f} mm inside each finger to bend in as the bump passes (bump {d:.2f})")
    web = SNAP_WIN_R - (CAP_R + CARRIER_CAP_CLR)
    check(web >= SNAP_WEB - 1e-6, f"carrier {web:.1f} mm between its bore and each window: the inner edge stays whole")
    c = sensor_board_eu.carrier()
    for a, w in SNAPS:
        u = (cos(radians(a)), sin(radians(a)))
        rp = CAP_R + CARRIER_CAP_CLR + web / 2
        probe = Pos(u[0] * rp, u[1] * rp, (LIP_T + SB_PAD_Z) / 2) * Box(0.2, 0.2, SB_PAD_Z - LIP_T - 0.1)
        r = probe & c
        check(r is not None and r.volume > 0.99 * probe.volume, f"window at {a:.0f} deg ({w} wide) closed towards the bore")
    r = f & cap
    check(r is None or r.volume < 0.001, f"fingers clear of the barrier ({r.volume if r else 0.0:.3f} mm3)")
    cp = sensor_board_eu.parts()
    for k in ("carrier", "sensor_board", "sb_screws", "msr"):
        r = f & cp[k]
        check(r is None or r.volume < 0.001, f"fingers clear of the {k} ({r.volume if r else 0.0:.3f} mm3)")
    from params import M2_HEAD
    for x, y in SB_SCREWS:
        h = Pos(x, y, (SB_PAD_Z + SB_TOP) / 2) * Cylinder(M2_HEAD[0] / 2, SB_T)
        g = h.distance_to(sensor_board_eu.snap_windows(SB_PAD_Z, SB_TOP, SNAP_WALL_R + SNAP[2]))
        check(g >= 1.0, f"sensor board screw at ({x:.0f}, {y:.0f}): head {g:.2f} mm from a snap window")


def finger_scoops(tr):
    """Finger scoops (D-73): open at the face both sides of the pocket, into the pocket, solid round them."""
    print("finger scoops (D-73)")
    u, a, b = face_plate_eu.scoop_sections()[-1]
    bottom = PT + SCOOP_RISE - u
    _, fa, fb = face_plate_eu.scoop_sections()[2]                     # section at the face
    print(f"       scoops {2 * fa:.1f} x {2 * fb:.1f} mm at the face, {PT - bottom:.1f} mm deep, flat bottom "
          f"{2 * a:.1f} x {2 * b:.1f}")
    for sx in (-1, 1):
        probe = Pos(sx * SCOOP_X, 0, PT - 0.5) * Box(0.4, 0.4, 0.4)
        r = probe & tr
        check(r is None or r.volume < 1e-6, f"scoop {'left' if sx < 0 else 'right'} open at the face")
        edge = Pos(sx * (POCKET_IN[0] / 2 + 0.3), 0, PT - 1.0) * Box(0.4, 4.0, 0.4)
        r = edge & tr
        check(r is None or r.volume < 1e-6, f"scoop {'left' if sx < 0 else 'right'} cuts through the pocket wall")
    gap = bottom - SCOOP_WALL - (SB_TOP + MIC[2])
    check(gap >= 1.0, f"scoop blocks {gap:.1f} mm over the sensor board's parts (>= 1.0)")


def carrier_clamp(cap):
    """Carrier clamp (D-71): the lip under the barrier's edge, outside the seal band, pinned to the wall; the barrier goes in
    from the front; the barrier's teeth in the lip's gaps stop it turning, keyed."""
    print("carrier clamp (D-71)")
    from math import degrees
    c = sensor_board_eu.carrier()
    check(REBATE_R >= SEAL_R + 0.5 - 1e-6, f"barrier's rebate from r {REBATE_R:.2f}, outside the seal band (r {SEAL_R})")
    check(CAP_T - LIP_T >= 0.8 - 1e-6, f"barrier {CAP_T - LIP_T:.1f} mm over the lip (>= 0.8)")
    check(CAP_R - LIP_R >= 1.0, f"lip {CAP_R - LIP_R:.2f} mm under the barrier's edge (>= 1.0)")
    bb = c.bounding_box()
    d = c.distance_to(cap)
    r = c & cap
    v = r.volume if r is not None else 0.0
    check(abs(bb.min.Z) < 1e-6 and d < 0.01 and v < 0.05, f"carrier on the wall (z {bb.min.Z:.2f}), its lip against the "
                                                         f"barrier's rebate (gap {d:.3f}, overlap {v:.3f} mm3)")
    probe = Pos(0, 0, (LIP_T + SB_TOP + 1) / 2) * Cylinder(CAP_R, SB_TOP + 1 - LIP_T)
    r = c & probe
    check(r is None or r.volume < 0.001, "carrier clear of the barrier disc's outline above the lip: the barrier goes in from the "
                                         "front")
    side = PW / 2 - SKIN - SB_EDGE - (CAP_R + CARRIER_CAP_CLR)
    probe = Pos(PW / 2 - SKIN - SB_EDGE - side / 2, 0, SB_PAD_Z / 2) * Box(0.2, 0.2, SB_PAD_Z - 0.1)
    r = c & probe
    check(side >= CARRIER_SIDE - 1e-6 and r is not None and r.volume > 0.99 * probe.volume,
          f"carrier {side:.1f} mm outside its bore at the sides, full height: top and bottom halves joined (D-78)")
    play = degrees(LIP_CLR / REBATE_R)
    check(play <= 0.5, f"teeth in the lip's gaps: the carrier turns <= {play:.2f} deg")
    key = TEETH[0][1]
    others = max(w for _, w in TEETH[1:]) + 2 * LIP_CLR
    check(key > others + 0.5, f"key tooth {key:.1f} wide, other gaps {others:.1f}: the carrier fits one way only")
    for a, w in TEETH:
        u = (cos(radians(a)), sin(radians(a)))
        rp = (REBATE_R + CAP_R) / 2
        probe = Pos(u[0] * rp, u[1] * rp, LIP_T / 2) * Box(0.2, 0.2, 0.2)
        r = probe & cap
        check(r is not None and r.volume > 0.0079, f"tooth at {a:.0f} deg ({w:.1f} wide) full thickness to the wall")


def test_socket(cap):
    """Test socket (D-76): the flush box's sizes and domes, the markers, the plate under the face plate, the stack
    inside it."""
    print("test socket (D-76)")
    import testbox_eu as tb
    bx, pl = tb.box(), tb.plate()
    for name, p in (("box", bx), ("plate", pl)):
        check(p.is_valid and len(p.solids()) == 1, f"{name}: one valid solid")
    bb = bx.bounding_box()
    probe = Pos(0, 0, -TB_DEPTH + 0.05) * Cylinder(1.0, 0.1)
    floor = Pos(0, 0, -TB_DEPTH - 0.05) * Cylinder(1.0, 0.1)
    r1, r2 = probe & bx, floor & bx
    check((r1 is None or r1.volume < 1e-6) and r2 is not None and r2.volume > 0.15 and abs(bb.max.Z) < 1e-6,
          f"inside depth {TB_DEPTH} mm from the rim (wall plane) to the floor; Ø{BOX_DIA} inside, Ø{BOX_HOLE} outside")
    for x, y in DOMES:
        q = Pos(x, y, -1.0) * Cylinder(TB_PILOT_D / 2 - 0.1, 1.0)
        w = Pos(x + (DOME_D / 2 - 0.3) * (-x / BOX_R), y + (DOME_D / 2 - 0.3) * (-y / BOX_R), -10) * Box(0.2, 0.2, 0.2)
        r_q, r_w = q & bx, w & bx
        check((r_q is None or r_q.volume < 1e-6) and r_w is not None and r_w.volume > 0.0079,
              f"dome at ({x:.0f}, {y:.0f}) with a Ø{TB_PILOT_D} pilot for the barrier's screws")
    for d in TB_MARKS:
        a = radians(22.5)                               # between two domes
        p_in = Pos((BOX_R + TB_GROOVE / 2) * cos(a), (BOX_R + TB_GROOVE / 2) * sin(a), -d) * Box(0.1, 0.1, 0.1)
        p_out = Pos((BOX_HOLE / 2 - TB_GROOVE / 2) * cos(a), (BOX_HOLE / 2 - TB_GROOVE / 2) * sin(a), -d) * Box(0.1, 0.1, 0.1)
        r = (p_in + p_out) & bx
        check(r is None or r.volume < 1e-6, f"marker groove at {d:.0f} mm, {TB_GROOVE} deep inside and outside")
    gap = TB_DEPTH + DEEPEST
    print(f"       deepest part of the stack at {-DEEPEST:.1f} mm: {TB_DEPTH + DEEPEST:.1f} mm above the floor")
    check(gap > 0, f"stack inside the {TB_DEPTH} mm socket")
    stack = {"barrier": cap, **{k: v for k, v in boards_eu.parts().items() if k not in ("magnet",)}}
    for k, v in stack.items():
        r = v & bx
        check(r is None or r.volume < 0.05, f"socket clears the {k} ({r.volume if r else 0.0:.3f} mm3)")
    m = TB_PLATE_MARGIN
    plb = pl.bounding_box()
    check(abs(plb.max.Z) < 1e-6 and plb.size.X >= PW + 2 * m - 0.01 and plb.size.Y >= PH + 2 * m - 0.01,
          f"plate {plb.size.X:.1f} x {plb.size.Y:.1f}, face at the wall plane, {m} mm beyond the face plate")
    r = bx & pl
    check(r is None or r.volume < 0.01, "plate on the box's shoulder, the box's rim flush with its face")
    base.overhangs("test socket box (floor down)", bx, small=5.0)
    base.overhangs("test socket plate", pl)


def barrier(cap, plain=False, switch=False):
    print("barrier" + (" (switch-only barrier, D-122)" if switch else " (plain barrier, D-109)" if plain else ""))
    room = Pos(PC[0], PC[1], 0) * slab(rr(PW + 20, PH + 20, 5), 0, PT + 10)
    box = Pos(0, 0, -BOX_D / 2) * Cylinder(BOX_R, BOX_D)
    for x, y in DOMES:
        box -= Pos(x, y, -BOX_D / 2) * Cylinder(DOME_D / 2, BOX_D + 0.01)
    plugs = Pos(0, SW_Y, 0) * slab(Rectangle(*SW_CUT), PANEL_BOT_Z - 0.2, PANEL_TOP_Z + 0.2)
    if not switch:
        plugs += barrier_eu.pin_holes(plain)
    air = (room + box) - cap - plugs
    mains = [s for s in air.solids() if s.is_inside(Vector(0, 0, -BOX_D + 1))]
    check(len(mains) == 1, "found the mains air volume")
    m = mains[0]
    for name, p in [("room in front of the face", (0, PC[1], PT + 5)),
                    ("remote pocket", (0, -10, SEAT_Z + 1)),
                    ("switch cup", (0, SW_Y, PANEL_TOP_Z + 1)),
                    ("face plate hollow (low-voltage)", (-(CAP_R + 0.2), MSR_Y - 15, 5)),
                    ("MSR-2 bay", (0, MSR_Y, 5))]:
        check(not m.is_inside(Vector(*p)), f"mains air does not reach the {name}")
    check(m.bounding_box().max.Z <= 1e-3, f"mains air stays behind the wall plane (max z {m.bounding_box().max.Z:.2f})")


def board_checks():
    import kicad_board
    print("EU boards (KiCad)")
    for name in ("eu_mains_board", "eu_pin_board"):
        path = kicad_board.ROOT / "pcb" / "eu" / "kicad" / f"{name}.kicad_pcb"
        if not path.exists():
            print(f"       {name}: no KiCad board (run make pcb)")
            continue
        b = kicad_board.Board(path)
        s1_wago = lambda pad, body: pad.startswith("S1.") and body in ("J1", "J2")
        gaps = b.pad_body_gaps()
        gap, pad, body = min(g for g in gaps if not s1_wago(g[1], g[2]))
        check(gap >= PAD_BODY_GAP - 1e-6, f"{name}: through-hole pads clear of the bodies on the other side "
              f"(closest {pad} to {body}: {gap:.2f} mm >= {PAD_BODY_GAP})")
        if "S1" not in b.fps:
            continue
        gap, pad, body = min(g for g in gaps if s1_wago(g[1], g[2]))
        check(gap >= S1_WAGO_BODY_GAP - 1e-6, f"{name}: rocker slot pads clear of the WAGO bodies "
              f"(closest {pad} to {body}: {gap:.2f} mm >= {S1_WAGO_BODY_GAP}, D-88)")
        pin = min((hypot(max(abs(x - wx) - SW_PAD[0] / 2, 0), max(abs(y - wy) - SW_PAD[1] / 2, 0)) - wr,
                   f"S1.{n} to {ref}.{wn}") for n, x, y, _ in b.tht_pads("S1") for ref in ("J1", "J2")
                  for wn, wx, wy, wr in b.tht_pads(ref))
        check(pin[0] >= S1_WAGO_PIN_GAP - 1e-6, f"{name}: rocker slot pads {pin[0]:.2f} mm from the WAGO pins "
              f"(closest {pin[1]}, >= {S1_WAGO_PIN_GAP})")


def plain_checks():
    """Plain plate (D-109): the barrier with the battery-free pins' holes only, the carrier without the sensor board, the
    80 x 80 face plate; the mains board and the pin board as the full plate, without the sensor pins P1 / P2."""
    print("plain plate (rocker and battery-free remote, D-109)")
    from math import cos, radians, sin
    import face_plate_eu
    cap, tr, car = barrier_eu.build(plain=True), face_plate_eu.build(plain=True), sensor_board_eu.carrier(plain=True)
    for name, q in (("barrier", cap), ("face plate", tr), ("carrier", car)):
        check(q.is_valid and len(q.solids()) == 1, f"plain {name}: one valid solid ({q.volume / 1000:.1f} cm3)")
    bb = tr.bounding_box()
    check(abs(bb.size.X - PLAIN_PW) < 0.01 and abs(bb.size.Y - PLAIN_PH) < 0.01 and abs(bb.center().X) < 0.01
          and abs(bb.center().Y) < 0.01, f"plain face plate {bb.size.X:.1f} x {bb.size.Y:.1f} mm, centred on the box")
    room = PLAIN_PW / 2 - SKIN - (CAP_R + CARRIER_CAP_CLR)
    check(room >= 0.0, f"barrier disc and carrier bore inside the plain plate's walls ({room:.2f} mm to spare at the sides)")
    parts = boards_eu.parts()
    rem = boards_eu.remote()
    pairs = [("barrier", cap, "face plate", tr), ("carrier", car, "face plate", tr), ("carrier", car, "barrier", cap),
             ("remote", rem, "barrier", cap), ("remote", rem, "face plate", tr)]
    pairs += [(k, v, "barrier", cap) for k, v in parts.items() if k not in ("switch", "pins")]
    for an, a, bn, b in pairs:
        r = a & b
        v = r.volume if r is not None else 0.0
        check(v < 0.05, f"plain: {an} clears the {bn} ({v:.3f} mm3)")
    for k in ("board", "bf_pins", "front", "socket", "mains_board", "header"):
        d = tr.distance_to(parts[k])
        check(d >= 0.05, f"plain face plate not touching the {k} (gap {d:.2f} mm)")
    f = face_plate_eu.snaps()
    for name, q in (("carrier", car), ("barrier", cap)):
        r = f & q
        check(r is None or r.volume < 0.001, f"plain: snap fingers clear of the {name} ({r.volume if r else 0.0:.3f} mm3)")
    web = SNAP_WIN_R - (CAP_R + CARRIER_CAP_CLR)
    for a, w in SNAPS:
        u = (cos(radians(a)), sin(radians(a)))
        rp = CAP_R + CARRIER_CAP_CLR + web / 2
        probe = Pos(u[0] * rp, u[1] * rp, (LIP_T + SB_PAD_Z) / 2) * Box(0.2, 0.2, SB_PAD_Z - LIP_T - 0.1)
        r = probe & car
        check(r is not None and r.volume > 0.99 * probe.volume,
              f"plain carrier: window at {a:.0f} deg closed towards the bore")
        g = Pos(u[0] * (SNAP_WALL_R + SNAP[2] / 2), u[1] * (SNAP_WALL_R + SNAP[2] / 2),
                sum(SNAP_GROOVE) / 2) * Box(0.1, 0.1, 0.1)
        r = g & car
        check(r is None or r.volume < 1e-6, f"plain carrier: groove at {a:.0f} deg for the finger's bump")
    cb = car.bounding_box()
    d = car.distance_to(cap)
    check(abs(cb.min.Z) < 1e-6 and d < 0.01, f"plain carrier on the wall, its lip against the barrier's rebate (gap {d:.3f})")
    probe = Pos(0, 0, (LIP_T + SB_TOP + 1) / 2) * Cylinder(CAP_R, SB_TOP + 1 - LIP_T)
    r = car & probe
    check(r is None or r.volume < 0.001, "plain carrier clear of the barrier disc above the lip: the barrier goes in from the front")
    barrier(cap, plain=True)
    base.overhangs("plain barrier", Rot(180, 0, 0) * cap, bridges=((-MAGNET_Z[0], MAG_BRIDGE),))
    base.overhangs("plain face plate", Rot(180, 0, 0) * tr, limit=3.5)
    base.overhangs("plain carrier (bottom down)", car)


def switch_checks():
    """Switch-only plate (D-122): the barrier without pin holes or pin board bosses; the mains board carries only the rocker
    switch and the terminal blocks; the plain carrier and face plate."""
    print("switch-only plate (rocker switch and terminal blocks, D-122)")
    import face_plate_eu
    cap, tr, car = barrier_eu.build(switch=True), face_plate_eu.build(plain=True), sensor_board_eu.carrier(plain=True)
    check(cap.is_valid and len(cap.solids()) == 1, f"switch-only barrier: one valid solid ({cap.volume / 1000:.1f} cm3)")
    parts = boards_eu.parts()
    for an, a in (("face plate", tr), ("carrier", car), ("remote", boards_eu.remote()), ("mains board", parts["mains_board"]),
                  ("terminal blocks", parts["wago"])):
        r = a & cap
        check(r is None or r.volume < 0.05, f"switch-only: {an} clears the barrier ({r.volume if r else 0.0:.3f} mm3)")
    sol = barrier_eu.pin_holes(True) & cap
    check(sol is not None and sol.volume > 0.99 * (barrier_eu.pin_holes(True) & Pos(0, 0, CAP_T / 2) * Cylinder(CAP_R, CAP_T)).volume,
          "switch-only barrier: solid where the battery-free pins pass")
    barrier(cap, plain=True, switch=True)
    base.overhangs("switch-only barrier", Rot(180, 0, 0) * cap, bridges=((-MAGNET_Z[0], MAG_BRIDGE),))


def main():
    layout()
    board_checks()
    cap, tr = barrier_eu.build(), face_plate_eu.build()
    solids(cap, tr)
    sensors(cap, tr)
    bf_checks(cap, tr)
    separation(tr)
    base.scd_vent_checks(tr, MSR_Y, MSR_BACK_Z, PT)
    base.msr_posts(tr, MSR_Y, MSR_BACK_Z, PT)
    snaps(cap, tr)
    finger_scoops(tr)
    carrier_clamp(cap)
    test_socket(cap)
    barrier(cap)
    print("printability (no supports)")
    base.overhangs("barrier", Rot(180, 0, 0) * cap, bridges=((-MAGNET_Z[0], MAG_BRIDGE),))   # floor over the steel recess
    base.overhangs("face plate", Rot(180, 0, 0) * tr, limit=3.5)
    cp = sensor_board_eu.parts()
    base.overhangs("sensor board carrier (bottom down)", cp["carrier"])
    plain_checks()
    switch_checks()
    print("FAILED: " + "; ".join(base.FAILS) if base.FAILS else "all checks passed")
    return 1 if base.FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
