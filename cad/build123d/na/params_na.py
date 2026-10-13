"""North American variant (single-gang box, Decora): geometry on top of the shared params.py (mm).

The printed barrier (barrier_na.py): remote pocket, switch well and rocker panel, collar flange with its land on the
sensor board; UL94 V-0 filament. The face plate (face_plate_na.py): radar skin, bays, vents, sound hole; face down.
The mains board (pcb/na/), positions mirrored below and compared by checks_na.py. The sensor board round the
barrier's collar: the MSR-2 on CN2, the SHT40, the microphone, the 5 V FFC in; the pin board with the battery-free
remote's two spring pins (sensor_board_na.py, pcb/na/).

Coordinates as in params.py: X width, Y up, Z out of the wall, z = 0 the wall surface, z < 0 inside the box (MAINS
SIDE). Tags as in params.py.
"""
import sys
from math import sqrt, hypot
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from params import *                                        # noqa: E402,F401,F403

# ---- face plate ----
PW, PH, PT = 72.2, 131.75, 14.4           # width (the flange plus clearance and skin), height, proud of wall;
                                          # PT = sensor board + CN2 stack + MSR-2 + skin gap + radar skin (D-51, D-66, checked)
PLATE_Y = 7.175                           # plate centre above the box centre (MSR-2 bay top, SHT40 bay bottom)
# plain plate (rocker and battery-free remote only, no sensors; D-109): standard-size single-gang wallplate,
# 2-3/4 x 4-1/2 in (NEMA WD 6), centred on the box
PLAIN_PW, PLAIN_PH = 69.85, 114.3
PLAIN_WALL_MIN = 1.0                      # plain plate's side wall beside the barrier's flange, at least

# ---- NA single-gang device box ----
BOX_W, BOX_H = 50.8, 76.2                 # 2" x 3" opening
BOX_D = 63.5                              # MEASURE (2.5" assumed), per room
SCREW_PITCH = 83.3                        # #6-32 device ears, 3-9/32"
# #6-32 oval / flat head (ASME B18.6.3): shank 3.5, head 6.05-6.65 across, 82 deg countersink
SCREW_D, SCREW_HEAD_D = 3.6, 6.8         # clearance hole; countersink diameter at the face (head max + 0.15)
SCREW_CSK = 82.0                          # countersink included angle

# ---- remote seat and steel piece ----
SEAT_T = 2.5                              # minimum material under the remote seat
MAGNET_Y = 0.0                            # ESTIMATE centre of the remote's internal plate (FCC photo: centred in its cover)
MAGNET_REC_Y = -3.75                      # cut piece centre: over the remote's plate and the back cover's steel, the
                                          # cut edge SEAT_T clear of the switch well
MAGNET_SLOT_BOT = MAGNET_REC_Y - MAGNET[1] / 2 - MAGNET_CLR   # derived: recess bottom, at the round end

# ---- rocker switch position ----
SW_SW_DIR = 1                             # switched pins (1a / 2a) above (+1) or below (-1) the in pins (1 / 2)
SW_Y = 19.5                               # rocker centre (front-view y; from pcb/)

# ---- mains board (single board, D-24/D-25; KiCad project in pcb/) ----
MB = (47.0, 72.0, 1.6)                    # front face (F) towards the plate, back (B) into the box
MB_Y = 0.0                                # board centre
IRM = (37.0, 24.0, 15.0)                  # DATASHEET Mean Well IRM-03-5 body (IRM-03-SPEC 2025-08-08), on B
IRM_C = (0.0, -21.39)                     # PSU body centre on the board (front-view x, y; from pcb/)
WAGO6 = (32.4, 16.1, 20.7)                # DATASHEET WAGO 2604-1106 (3D model): width, depth at the board (entry face to
                                          # closed back; the levers overhang the entry side up top), height incl. pins (on B)
WAGO_X, WAGO_Y = 3.0, 5.05                # terminal block centre at the board (front-view x, y; from pcb/)
WAGO_ENTRY = (0, 1)                       # direction the wire entries face (front-view x, y): away from the PSU
WAGO_PSU_GAP = 1.0                        # minimum gap from the block's closed back to the PSU body
J2_POS = (12.7, -23.3)                    # SMD 5 V connector on F (front-view x, y; from pcb/), below the posts, FFC down (-y)
WIRE_SPACE_MIN = 10.0                     # free depth wanted behind the terminal block

# ---- board mounting: nylon standoffs (D-57) ----
# Four Keystone 25503 nylon M3 male-female hex standoffs (15 mm): the stud screws into a tapped blind hole in a boss
# on the barrier's underside, a nylon M3 x 8 pan head screw through each board hole into the standoff.
MOUNT_HOLES = ((-21.0, 33.5), (-21.0, -33.5), (21.0, 33.5), (21.0, -33.5))  # board holes (front-view x, y; from pcb/)
MOUNT_HOLE_D = 3.2                        # board hole, M3 clearance (ISO 273 fine)
MOUNT_BOSS_D = 7.0                        # boss on the barrier, from the standoff's face up into the barrier
# boss tops: 1 mm into the corner taper
MOUNT_BOSS_TOP = (-1.6, -1.6, -1.6, -1.6)
STANDOFF = (5.0, 8.0, 8.0)                # DATASHEET Keystone 25503 (catalog M65 p.76): hex across flats, male
                                          # thread length, internal thread depth; nylon 6/6 UL94 V-2
STANDOFF_L = 15.0                         # DATASHEET Keystone 25503 body length
MOUNT_STUD = (8.0, 8.0, 8.0, 8.0)         # stud length per hole (MOUNT_HOLES order): as supplied
STANDOFF_SCREW = (8.0, 5.6, 1.8)          # nylon M3 x 8 slotted pan head: length; head diameter and height ISO 1580 max
MOUNT_THREAD_D, MOUNT_TAP_D = 3.0, 2.5    # M3 x 0.5: stud, tap-drill hole (ISO 2306)
MOUNT_THREAD_L = tuple(s + 0.5 for s in MOUNT_STUD)   # tapped depth per hole: the stud plus 0.5 (45 deg cone end)
MOUNT_THREAD_MIN = 1.5 * 3.0              # stud engagement in the printed thread, >= 1.5 x M3

# ---- barrier (box side, V-0) ----
PLUG_CLR = 0.75                           # barrier body to box wall, each side
PLUG_R = 3.0
COLLAR_LIP = 1.25                         # flat seal band on the wall beyond the box edge
FLANGE = 3.0                              # flange beyond the island, clamped by the face plate
ISLAND_RIM = 1.2                          # visible barrier rim around pocket + scoops
ISLAND_R = 6.0
BOSS_R = 4.0                              # screw boss on the barrier
KEY_D, KEY_H, KEY_CLR = 3.0, 1.0, 0.15    # locating pins barrier -> face plate (asymmetric = keyed)
KEY_POS = ((25.0, 30.0), (-25.0, -22.0))
SCREW_LOBE = (7.0, 0.15, 1.5)             # face plate round each screw, reaching in to the remote pocket (D-132): radius
                                          # round the screw, seam to the barrier's island, fillet where it meets the window
SCOOP = (6.0, 16.0, 9.0)                  # finger scoop ellipsoid radii (x, y, z)
SCOOP_ZC = PT + 2.5                       # scoop centre height

# ---- edge vents ----
VENT_Z_OVER, VENT_H = 3.0, 5.0             # NA edge vents: centre above the sensor board's parts, height

# ---- 5 V cable: mains board J2 -> slit in the barrier's bottom wall -> sensor board J1 (D-50, D-134) ----
# A stock FFC (6 contacts, 0.5 mm pitch, contacts on the same side at both ends) latched in Hirose FH12-6S-0.5SH
# slide-lock connectors: J2 on the mains board, cable out downwards; J1 at the bottom of the sensor board, cable in from
# above; both on x FFC_SLOT_X. The cable stays in that plane (ffc_curve()): a bend up out of J2, one straight run through
# a slit in the barrier's bottom wall, a bend over onto the sensor board, guided by the slit.
FH12 = (6.1, 5.6, 2.0)                    # REF FH12-6S body (x, y, height): KiCad footprint / Hirose FH12 series
FH12_ENTRY = 4.9                          # FH12 footprint origin to the body's cable face (KiCad footprint, F.Fab)
JUMPER_W = 3.5                            # FFC width (6 contacts at 0.5)
JUMPER_END = (3.5, 4.0, 0.3)              # FFC contact end: width, length in the connector, thickness (FH12 FPC spec)
JUMPER_T = 0.12                           # FFC thickness
JUMPER_STOCK_L = 50.0                     # DATASHEET GCT 05-06-A-0050-A-4-06-4-G (or Wurth 687606050002): length
JUMPER_SLACK = (2.0, 10.0)                # spare length the route may leave (it bows in the free span): min, max
FFC_SLOT_X = 12.7                         # J2, J1 and the slit on this x: between PS1's +5V and GND pins
FFC_SLOT = (4.4, 0.5, 1.1)                # slit: width, gap round the cable (both sides), side notch the cable goes in by
FFC_EXIT = 1.0                            # straight out of J2 before the first bend
FFC_BEND = (3.0, 4.0)                     # bend radii: up out of J2, over onto the sensor board
FFC_LIP = 0.8                             # least lip outside the slit (cut back below FFC_LIP_Z, no knife edge)
FFC_LIP_Z = -8.1                          # the lip's lower end
ARROW = (4.5, 2.2, 0.35, -1.5)            # engraved arrows either side of the slit on the plug's bottom face: length,
                                          # head width, depth, centre z
SB_J1 = (FFC_SLOT_X, -50.0)             # FH12 on the sensor board (room x, y), cable in from +y

# ---- microphone position ----
MIC_SKIN_HOLE_D = 1.6                     # sound hole through the face skin (1.0 closed up on the print, D-61)
MIC_AT = (28.5, 63.0)                     # NA: port centre (room x, y), top right beside the MSR-2
MIC_BODY_Y = MIC_AT[1] - (MIC[1] / 2 - MIC_PORT_IN)   # mic body centre (port end up)

# ---- sensor board (D-50, D-68): FR4 round the barrier's collar, against the wall, under the face plate ----
SB_T = 1.6
SB_SIDE_CLR = 0.7                       # board edge to the face plate's side wall (beyond SPLIT_CLR)
SB_WIN_CLR = 0.3                        # board's window round the seal band
SB_LAND = 1.5                           # flat land at the flange taper's foot over the board's inner edge (D-68)
SB_RIB = (1.0, 0.15)                    # crush ribs on the collar's outside: width, interference into the board's
                                          # window edge (press fit for handling, D-68; COUPON coupon_ribs)
SB_RIBS = (("x", 22.0), ("y", 18.0))    # ribs on each straight side: along x at y +-22, along y at x +-18
SB_R = 3.4                              # outer corner radius
SB_KEEP = 8.0                           # copper path from the box opening's edge, along the wall (front layer: plus
                                          # the board's edge, SB_T); mains to 5 V target as on the mains board (D-24)
SHT_AT = (0.0, -51.3)                     # SHT40 on the sensor board (room x, y), in the face plate's vented bay
# small parts on the sensor board: centre (room x, y), body w, h, max height
SB_SMALL = {"C1": ((20.0, -54.2), (3.2, 1.6, 1.8)),     # 22 uF 16 V 1206 at J1 (KEMET C1206C226M4PACTU, 1.8 max: DigiKey, D-95)
              "C2": ((2.6, -51.3), (0.5, 1.0, 0.55)),    # SHT40 100 nF 0402 (0.5 +-0.05)
              **{k: ((MIC_AT[0] + dx, MIC_AT[1] + dy), s) for k, ((dx, dy), s) in MIC_PARTS.items()}}

# ---- battery-free remote (D-50): two spring pins from the mains board's 5 V area to the back cover's pads ----
# They stand on a pin board in a pocket under the pocket floor, through two holes in the floor (pin-filled barrier
# openings, human decision 2026-10-10); barrel and plunger enter windows in the cover's back onto pads on the cover
# flex. Two SMT spacer posts carry the pin board and +5 V / GND up from the mains board.
PB = (14.0, 12.0, 0.8)                 # pin board w, h, t
PB_C = (13.25, -13.4)                  # pin board centre (room x, y): posts at its lower corners (in the mains board's
                                          # 5 V area), the pins above and between them (D-79)
PB_CLR = 0.3                           # pin board to its pocket under the floor
# snap clips in the pin board pocket (D-91): fingers hang from the pocket floor down past the pin board's edges, a hook under its
# back face holds it against the pins' push. Clip centres on the pin board's edges: (edge, position along it from the pin board
# centre). With the two posts the top clip makes a three-point hold in line with the pins; the right one sits between the
# pins; the bottom one, between the posts, holds the printed blank board (switch only, no posts) with the other two
# (human 2026-10-12, D-127). None on the left edge: the steel piece's recess above it leaves no floor for a relief slot.
PB_CLIPS = (("top", 0.0), ("right", 2.2), ("bottom", 0.0))
PB_CLIP = (3.0, 0.8, 0.4, 0.3)         # finger width, thickness, hook depth under the board, relief round the finger
PB_CLIP_PLAY = 0.1                     # hook's catch face below the pin board's back face
POSTS = ((9.85, -16.5), (16.65, -16.5))   # spacer posts on the mains board's 5 V area (+5V, GND), level, the pins either side (D-60)
# each post: Wurth WA-SMSI M2 SMT spacer (soldered on the mains board, 4.35 OD, through bore) + WA-SBRIE M2
# male-female brass standoff (4 mm hex) screwed into it; an M2 screw through the pin board into the top; heatshrink over
# the stack
POST_STACK = (7.0, 10.0)                  # DATASHEET SMSI 9774070243R L 7 +-0.1, SBRIE 971100244 L 10
POST_THREAD = (5.0, 5.0)                  # DATASHEET SBRIE 971100244: male thread length, internal thread depth
POST_SPIGOT = (2.8, 1.4)                  # DATASHEET SMSI 9774070243R: locating spigot diameter, length (in the
                                          # land pattern's 3.0 unplated hole; solder on the front ring only)
PB_SCREW_L = 5.0                       # M2 x 5 pan head through the pin board into the SBRIE
POST_SP = (4.62, 0.4)                     # post across the hex corners, sleeve (heatshrink) wall

# ================= derived =================
SEAT_Z = PT + B_PROUD - B_D               # remote's back rests here
POCKET_IN = (B_W + 2 * CLR, B_H + 2 * CLR)
POCKET_OUT = (POCKET_IN[0] + 2 * POCKET_WALL, POCKET_IN[1] + 2 * POCKET_WALL)
WELL_FLOOR_Z = SEAT_Z - SW_ROCKER_H - SW_ROCKER_TOL - SW_ROCKER_CLR   # top face of the switch panel
PANEL_BOT_Z = WELL_FLOOR_Z - SW_PANEL_T   # underside of the switch panel
WELL_IN = (SW_BEZEL[0] + 2 * CLR, SW_BEZEL[1] + 2 * CLR)
DECK_Z = PT - SKIN                        # barrier flange top = face plate face underside

MB_FRONT_Z = WELL_FLOOR_Z - SW_BODY[2]    # board front face = rocker PCB seat (measured from the panel's front face)
MB_BACK_Z = MB_FRONT_Z - MB[2]
MOUNT_FACE_Z = MB_FRONT_Z + STANDOFF_L    # bosses' faces: the standoffs' bodies between them and the board
Z_BOT = PANEL_BOT_Z                       # lowest point of the barrier = print bed (panel underside)

# barrier outline
PLUG = (BOX_W - 2 * PLUG_CLR, BOX_H - 2 * PLUG_CLR)
SEAL = (BOX_W + 2 * COLLAR_LIP, BOX_H + 2 * COLLAR_LIP)
_sc_face = SCOOP[0] * sqrt(max(0.0, 1 - ((SCOOP_ZC - PT) / SCOOP[2]) ** 2))
SCOOP_X = POCKET_IN[0] / 2 + 0.6
ISLAND = (2 * (SCOOP_X + _sc_face + ISLAND_RIM), POCKET_OUT[1] + 2 * ISLAND_RIM)
FLANGE_OUT = (ISLAND[0] + 2 * FLANGE, ISLAND[1] + 2 * FLANGE)
# depth of the 45-degree taper that carries the flange underside (plug corner -> pocket shell)
_r = POCKET_OUT[0] / 2
_cx, _cy = PLUG[0] / 2 - PLUG_R * (1 - 0.7071), PLUG[1] / 2 - PLUG_R * (1 - 0.7071)
TAPER_D = round(hypot(_cx, _cy - (POCKET_OUT[1] / 2 - _r)) - _r + 0.6, 1)

# MSR-2 bay sits just above the top screw (boss + countersink), SHT40 bay as before
MSR_Y = SCREW_PITCH / 2 + max(BOSS_R + SPLIT_CLR, SCREW_HEAD_D / 2 + 1.0) + MSR[1] / 2 + CLR
MSR_BACK_Z = SB_T + B2B_STACK         # MSR-2 board back (CN2 side): on CN2 on the sensor board, MSR_SKIN_GAP under the skin
MSR_X = -LUX_POS[0]                       # MSR-2 centre (room x): the grille over its light sensor on the plate's centre line
MSR_CN2_X = MSR_X + MSR_BOARD[0] / 2 - MSR_CN2_IN
# the MSR-2's back switches stand deeper than the CN2 stack: notches in the sensor board's top edge
MSR_SW_CUTS = [(MSR_X + x - MSR2_SW[0] / 2 - MSR2_SW_CLR, MSR_X + x + MSR2_SW[0] / 2 + MSR2_SW_CLR,
                MSR_Y + MSR_BOARD[1] / 2 - MSR2_SW[1] - MSR2_SW_CLR) for x in MSR2_SW_X]   # x0, x1, y0 (room)
MSR_SPACERS = [(MSR_X + x, MSR_Y + y) for x, y in MSR2_POSTS]   # sensor board's SMT spacers under the MSR-2, below its posts (room)
SKIN_Z = PT - SKIN                        # underside of the face plate's face skin
# sensor board
_sb_in = SKIN + SPLIT_CLR + SB_SIDE_CLR                            # face plate's outer edge to the board's edge
SB_HALF_W = PW / 2 - _sb_in
SB_Y = (PLATE_Y - PH / 2 + _sb_in, PLATE_Y + PH / 2 - _sb_in)
SB_INNER = (SEAL[0] + 2 * SB_WIN_CLR, SEAL[1] + 2 * SB_WIN_CLR, PLUG_R + COLLAR_LIP + SB_WIN_CLR)
SB_PARTS_TOP = SB_T + max([FH12[2]] + [d[2] for _, d in SB_SMALL.values()])   # tallest part on the sensor board
FRAME_Z0 = SB_PARTS_TOP + SPLIT_CLR     # face plate's bay frames end here, over the sensor board's parts (D-68)
# spring pins: tip on the cover flex's pads, pin board under the pocket floor
PIN_TIP_Z = SEAT_Z + BC_FLEX_Z
PB_BOT = MB_FRONT_Z + POST_STACK[0] + POST_STACK[1]
PB_TOP = PB_BOT + PB[2]
PIN_WORK = PIN_TIP_Z - PB_TOP          # pins' design working height on the pads



FFC_BOARD_Z = SB_T + 0.1                  # 5 V cable's centre over the sensor board
FFC_ARC_END_Y = -(SB_INNER[1] / 2) + 0.15  # the second bend ends just inside the sensor board's window edge
PLUG_TOP = PLUG[1] / 2


def ffc_curve(n=24):
    """FFC centre line in the plane x = FFC_SLOT_X as (y, z): straight out of J2 (-y), a bend up (FFC_BEND[0]), one
    straight run at its own angle through the barrier's bottom wall, a bend over onto the sensor board (FFC_BEND[1]),
    straight to 1 mm inside J1. Also returns the straight run's ends."""
    from math import atan2, cos, sin, radians, pi
    r1, r2 = FFC_BEND
    e = (MB_Y + J2_POS[1] - FH12_ENTRY, MB_FRONT_Z + 1.0)
    e1 = (e[0] - FFC_EXIT, e[1])
    c1 = (e1[0], e1[1] + r1)                             # turned clockwise (y right, z up)
    c2 = (FFC_ARC_END_Y, FFC_BOARD_Z - r2)               # turned anticlockwise

    def ends(a):
        hy, hz = -cos(a), sin(a)                         # heading of the straight run
        t1 = (c1[0] - r1 * hz, c1[1] + r1 * hy)
        t2 = (c2[0] + r2 * hz, c2[1] - r2 * hy)
        return t1, t2, (t2[0] - t1[0]) * hz - (t2[1] - t1[1]) * hy

    lo, hi = radians(5), radians(89.9)
    for _ in range(80):                                  # the run tangent to both bends
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if ends(lo)[2] * ends(mid)[2] > 0 else (lo, mid)
    t1, t2, _ = ends(lo)
    a1 = atan2(t1[1] - c1[1], t1[0] - c1[0])
    a2 = atan2(t2[1] - c2[1], t2[0] - c2[0])
    a1 = a1 - 2 * pi if a1 > -pi / 2 else a1             # clockwise from the bottom (-90 deg) down to a1
    arc1 = [(c1[0] + r1 * cos(-pi / 2 + (a1 + pi / 2) * i / n), c1[1] + r1 * sin(-pi / 2 + (a1 + pi / 2) * i / n))
            for i in range(n + 1)]
    arc2 = [(c2[0] + r2 * cos(a2 + (pi / 2 - a2) * i / n), c2[1] + r2 * sin(a2 + (pi / 2 - a2) * i / n))
            for i in range(n + 1)]
    pts = [e] + arc1 + arc2 + [(SB_J1[1] + FH12_ENTRY - 1.0, FFC_BOARD_Z)]
    return pts, (t1, t2)


def slot_path():
    """FFC centre line (room x, y, z): ffc_curve() in the plane x = FFC_SLOT_X."""
    return [(FFC_SLOT_X, y, z) for y, z in ffc_curve()[0]]


def jumper_length():
    """FFC length the route needs: J2's cable face to J1's, plus JUMPER_END[1] into each connector."""
    from math import dist
    pts = ffc_curve()[0]
    return sum(dist(a, b) for a, b in zip(pts, pts[1:])) - 1.0 + 2 * JUMPER_END[1]
