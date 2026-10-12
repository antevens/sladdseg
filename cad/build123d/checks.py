"""Checks for the parts both variants share (run by `make check`): the replacement back cover, the steel plate's
hacksaw guide, the MSR-2 model; and the helpers the variant checks use (check, overhangs, the MSR-2 grille and posts,
the microphone column). na/checks_na.py and eu/checks_eu.py import this module as `base`.
"""
import sys
from math import hypot, radians, tan
import numpy as np
from build123d import Box, Pos
from params import *
from common import slab, rr

FAILS = []


def check(cond, msg):
    print(("  ok   " if cond else "  FAIL ") + msg)
    if not cond:
        FAILS.append(msg)


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
    zs = [i * 0.005 for i in range(int(B_SEAM_Z / 0.005) + 1)]
    steps = [max(abs(f(z + 0.005) - f(z)) for z in zs[:-1]) for f in
             (lambda z: back_run(z, B_BACK_RUN, B_BACK_RISE), shell_in)]
    check(max(steps) < 0.01, f"round-over without steps, outside and inside (largest change per 0.005 mm of height "
                             f"{max(steps):.4f}; D-126)")
    outside = [(back_run(z, B_BACK_RUN, B_BACK_RISE), z) for z in zs]
    wall = min(min(hypot(shell_in(z) - r, z - zo) for r, zo in outside[::4]) for z in zs[::10] if z >= BC_WALL)
    check(wall >= BC_SIDE_WALL - 0.05, f"thinnest shell wall {wall:.2f} mm (side walls {BC_SIDE_WALL})")
    zb = BC_EASE[1]
    was = BC_WALL - 0.1 - 0.2 + (B_BACK_RUN + 0.2) * (1 - sqrt(1 - (1 - (zb - BC_WALL) / B_BACK_RISE) ** 2))  # D-123
    check(was - shell_in(zb) >= 0.3, f"inside eased out through the rubbing band: {was - shell_in(zb):.2f} mm more room "
                                     f"(horizontal) at {zb} above the back face than D-123, nothing at the floor and "
                                     f"the straight wall (D-126)")
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
    lane0, lane1 = BC_LANE_H - 0.15, BC_LANE_H + 0.15        # +3V3 trace (0.3) across the band, above the flex plane
    tr = FLEX_T + BC_BEND_R                                  # the bend zone ends this high
    check(lane0 - tr >= BC_BEND_CLR - 0.15 - 1e-6 and BC_BRIDGE_H - lane1 >= 0.3 - 1e-6,
          f"+3V3 lane across the band: it turns {BC_LANE_H - tr:.2f} mm past the bend zone (>= {BC_BEND_CLR}), "
          f"{BC_BRIDGE_H - lane1:.2f} mm under the band's top edge (>= 0.3)")
    check(BC_BEND_R >= 6 * FLEX_T - 1e-6, f"run's bend: inside r {BC_BEND_R} mm >= 6 x the {FLEX_T} mm flex "
                                          "(IPC-2223 single-sided, bend to install; D-116)")
    zn = tr + BC_BEND_CLR                                    # end stiffener's notch top above the flex plane
    check(BC_CELL_Z - BC_FLEX_Z - ph / 2 >= zn - 1e-6, f"contact finger pads start {BC_CELL_Z - BC_FLEX_Z - ph / 2:.3f} "
                                                       f"above the flex plane, on the stiffener (notch to {zn:.2f})")
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
    check(BC_STEEL_FLOOR >= 0.8 - 1e-6 and BC_REG_FLOOR >= 0.4 - 1e-6,
          f"{BC_STEEL_FLOOR:.1f} mm of cover wall under the plate (D-96, D-99), {BC_REG_FLOOR} under the regulator")
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
    check(lip - clr >= 0.25 and BC_FLEX_SNAP_GAP <= 0.2, f"snap lips {lip - clr:.2f} mm over the stiffener's edges, "
                                                         f"{BC_FLEX_SNAP_GAP} mm above it")
    for k in ("flex", "pad_stiffener", "pin_pads", "regulator", "steel"):
        r = snaps & ps[k]
        check(r is None or r.volume < 0.001, f"snap hooks clear the {k}")
    zl = BC_FLEX_Z + FLEX_T + BC_STIFF_ADH + BC_PAD_STIFF_T + BC_FLEX_SNAP_GAP
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
    check(strain <= 0.05, f"plate clips {cw} wide, {ct} thick, {arm:.1f} mm free from their relief: strain "
                          f"{strain * 100:.1f} % snapping in (<= 5 %: strength before flex, D-111)")
    check(over >= 0.3, f"steel plate clips hook {over:.2f} mm over the plate's ends")
    ear = bc.latches().bounding_box()
    reach = sorted(round(B_H / 2 - abs(e.bounding_box().min.Y if e.bounding_box().center().Y > 0
                                       else e.bounding_box().max.Y), 2) for e in bc.latches().solids())
    check(ear.max.Y < B_H / 2 and reach == sorted(round(r, 2) for r in BC_LATCH_REACH),
          f"snap clip hook tips {reach} mm in from the outside rim, hooks {BC_LATCH_HOOK} mm inwards (bottom, top)")
    tip_z = (BC_WALL + BC_LATCH_CATCH_Z, B_SEAM_Z - BC_LATCH_RIM_GAP - 2 * BC_LATCH_HOOK[1])   # catch / tip face's foot
    proud = [BC_LATCH_REACH[i] - shell_in_base(z) for i, z in enumerate(tip_z)]
    eased = [BC_LATCH_REACH[i] - shell_in(z) for i, z in enumerate(tip_z)]
    check(abs(proud[0] - proud[1]) < 0.01, f"clip tips placed {proud[0]:.2f} (bottom, at its catch) and {proud[1]:.2f} mm "
                                           f"(top) clear of the inner surface before the ease (D-118); with it "
                                           f"{eased[0]:.2f} and {eased[1]:.2f} (tips kept, D-126)")
    for i, f in enumerate(BC_LATCH_CATCH):                 # flat underside: room under it, proud of the shell
        if f is None:
            continue
        zc = BC_WALL + BC_LATCH_TOPS[i] - BC_LATCH_HOOK[i] - f
        tip = B_H / 2 - BC_LATCH_REACH[i]
        ledge = BC_LATCH_REACH[i] - (B_W / 2 - bc.inner_x(zc))   # tip beyond the shell's inside face at zc (same round-over)
        under = 0.1 * tan(radians(BC_LATCH_RAMP)) if i == 0 else 0.0     # the ramp's drop 0.1 behind the tip
        probe = Pos(0, -(tip + 0.1), zc - under - 0.15) * Box(0.6, 0.15, 0.2)
        r = probe & ps["cover"]
        check(ledge >= BC_LATCH_LEDGE_MIN and (r is None or r.volume < 1e-6),
              f"{'bottom' if i == 0 else 'top'} clip: catch {zc - BC_WALL:.2f} above the inside floor, a {BC_LATCH_RAMP:.0f} deg ramp under the hook, "
              f"{ledge:.2f} mm proud of the shell's inner surface (>= {BC_LATCH_LEDGE_MIN}), clear under the tip")
    widths = [round(e.bounding_box().size.X, 2) for e in sorted(bc.latches().solids(), key=lambda e: e.bounding_box().center().Y)]
    check(all(abs(w - BC_LATCH_W[i]) < 0.01 for i, w in enumerate(widths)), f"snap clips {widths} mm wide (bottom, top)")
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
          and abs(B_W / 2 - shell_in_base(B_SEAM_Z - top - h / 2) - xin - prot) < 1e-3 and zs == (round(top, 2), round(top + h, 2)),
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
        w, h, t = {"U1": BC_REG_BODY, "D1": BC_TVS}.get(ref, BC_CAP0603)
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
    msr2_model()
    cover_checks()
    import backcover
    print("printability")
    overhangs("back cover", backcover.cover())                 # printed back down
    jig_checks()
    print("FAILED: " + "; ".join(FAILS) if FAILS else "all checks passed")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
