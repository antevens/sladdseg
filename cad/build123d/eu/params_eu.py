"""EU variant (D-30): geometry for a round EU flush box (DIN 49073, 68 mm hole saw, Ø60 inside).

A design of its own (shares only the BILRESA, the MSR-2, the SHT40 and the microphone with the NA
plate). Coordinates as in params.py, origin = box centre = remote centre: X width, Y up, Z out of
the wall, z = 0 the wall surface, z < 0 inside the box (MAINS SIDE).

- The BILRESA cannot go below the wall in a Ø60 box (its flat back alone spans ~Ø60), so it sits
  on a 1.6 mm V-0 floor over the box and stands B_PROUD out of the face plate (D-70).
- The barrier is one flat V-0 cap over the box and the seal band: the floor under the remote, a
  cup down to the panel of the emergency rocker (Marquardt 1802.2504, DPST, PCB pins) under the
  remote's upper half, four holes for the 5 V board's spring pins (D-54, D-59). Two countersunk
  screws into the box's top and bottom domes, in the pocket floor under the remote.
- The supplied steel piece sits in a recess in the pocket floor (front side, as on NA), under the back cover's
  magnet; a cup under the recess keeps the barrier's floor under it (D-72).
- Two boards (D-36). The mains board, at the rocker's PCB seat, carries the rocker, two WAGO
  2604-3102 push-in blocks (L in / switched, N in / switched; wires enter from the back of the box),
  fuse, MOV and the PSU (Traco TMPS 03-105) over a routed relief slot; the PSU's outputs land on a
  5 V island cut off by the slot, with a pin header. The 5 V board, just under the cap, takes 5 V
  from that header through a pin socket and carries four spring pins through the cap: two onto gold
  pads under the cap board, two onto the back cover's pads (R9, R10). Both hang from bosses under the cap.
- The sensors sit on a cap board in a printed carrier on the wall round the cap; the cap's edge pins
  the carrier to the wall (D-56, D-70, D-71).
- The face plate (PETG) carries everything visible: face, remote pocket walls, finger scoops, MSR-2
  and SHT40 bays. Four fingers snap into closed windows in the carrier (D-77).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from params import (B_W, B_H, B_D, CLR, POCKET_WALL, MAGNET, MAGNET_END_R, MAGNET_SETBACK, MAGNET_CLR, MSR,  # noqa: E402,F401
                    RADAR_WALL, MSR_SKIN_GAP, MSR2_POSTS, SHT, SKIN, FACE_CHAMFER, PR, SPLIT_CLR, BARRIER_MIN,
                    V0_RATED_T, MSR_BOARD, MSR_CN2_IN, B2B, B2B_STACK, SHT_CHIP, MIC, MIC_PORT_IN, MIC_BOOT, MIC_PARTS,
                    BC_FINGERS, BC_FLEX_Z, PIN_FREE, PIN_WH, PIN_TOL, PIN_FLANGE, PIN_BARREL, PIN_PLUNGER_D,
                    PIN_PAD_D, PIN_HOLE_D, PIN_RADIAL, RING_NUT, RING_NUT_HOLE, MSR2_SW, MSR2_SW_X, MSR2_SW_CLR,
                    MIC_SPAN, MIC_TUBE, MIN_PRINT_HOLE, M2_HEAD, BC_STEEL_FLOOR, BC_STEEL_Y, BC_STEEL,
                    SW_CUT, SW_PANEL_T, SW_BEZEL, SW_ROCKER_H, SW_ROCKER_TOL, SW_ROCKER_CLR, SW_BODY, SW_PIN_GRID, SW_PAD, SW_SLOT_DY,
                    PAD_BODY_GAP, BAY_WALL, MSR_BAY_R, SHT_BAY_CLR, SHT_BAY_R, MSR_VENTS, SHT_VENTS)

# ---- EU flush box: DIN 49073, Ø68 hole saw ----
# Catalogue values (DIN 49073 box listings, e.g. Kaiser 1555-04; docs/MEASUREMENTS.md), not measured.
BOX_DIA = 60.0                            # MEASURE inside diameter = device opening
BOX_HOLE = 68.0                           # MEASURE hole in the wall (box rim outer diameter)
BOX_D = 47.0                              # MEASURE standard depth
DOME_PITCH = 60.0                         # MEASURE device screw domes: 4 per box at 90 deg, on the box wall
DOME_D = 7.0                              # MEASURE screw dome diameter, full box depth, top at the wall plane
DOME_CLR = 0.75                           # board / parts to a dome
SCREW_D, SCREW_HEAD_D = 3.2, 6.0          # MEASURE device screws 3.2 mm, countersunk head
PLUG_CLR = 0.75                           # cap cup / board to the box wall
COLLAR_LIP = 1.25                         # flat seal band on the wall beyond the box hole
# test socket (D-76): a printed stand-in for the flush box, BOX_DIA inside / BOX_HOLE outside, the DOMES, in a wall plate
TB_DEPTH = 65.0                           # inside depth, wall plane to the floor
TB_MARKS = (40.0, 43.0, 60.0, 63.0)       # depth markers below the wall plane
TB_FLOOR = 2.0                            # floor thickness
TB_PILOT_D, TB_PILOT_L = 2.7, 20.0        # device screw pilot hole in each dome (SCREW_D thread-forming), depth
TB_GROOVE = 0.5                           # marker V-groove depth (45 deg flanks), inside and outside
TB_PLATE_T = 3.0                          # wall plate thickness; the tube's rim is flush with its face
TB_PLATE_MARGIN = 10.0                    # wall plate beyond the face plate's outline, each side
TB_PLATE_CLR = 0.15                       # wall plate's hole round the tube
TB_SHOULDER = 2.0                         # shoulder on the tube under the plate (45 deg underside)
TB_KEY = (4.0, 1.5)                       # key on the tube at the top (+y) and its notch in the plate: width, radial
TB_WINDOW = (10.0, 30.0)                  # inspection window in the wall at -45 deg: width, top below the wall plane
TB_FIN = (2.0, 7.0)                       # label fin beside the window: thickness, radial
TB_TEXT = (3.0, 0.4)                      # depth labels on the fin: height, engraving depth
WIRE_SPACE_MIN = 10.0                    # free depth wanted behind the deepest part (reported, not enforced: human
                                          # decision 2026-10-08, depth to be tested in a box)

# ---- emergency rocker: Marquardt 1802.2504, DPST, PCB pins (as the NA plate, D-26; values in params.py) ----
SW_Y = 12.5                               # rocker centre: cup clear of the top screw dome and of the magnet
SW_SW_DIR = -1                            # switched pins (1a / 2a) 7 mm below the in pins (1 / 2, on SW_Y)

# ---- remote and plate ----
B_PROUD = 2.6                             # remote top this far proud of the face, as on the NA plate (D-70)
CAP_T = BARRIER_MIN                       # cap floor = barrier (V-0)
CAP_MARGIN = 0.5                          # cap beyond the seal band and the pocket walls
# face plate snaps (D-70, D-77): four fingers hang from the face skin at the corners into closed windows in the carrier
# and the cap board (they locate the plate and stop it turning); a bump on each finger's outer face catches a groove in
# the carrier window's outer wall. The carrier's inner edge stays whole: SNAP_WEB of it between each window and its bore
SNAP = (6.0, 2.4, 0.6)                    # finger width (tangential), thickness (radial), groove depth (outward)
SNAP_BUMP_CLR = 0.05                      # bump this much short of the groove's depth
SNAP_KEY_W = 8.0                          # the top right finger and its window are wider: the plate fits one way only
SNAP_ANGLES = (45.0, 135.0, 225.0, 315.0)  # finger positions round the cap's centre (deg from +x)
SNAP_GROOVE = (0.2, 1.4)                  # groove in the window's outer wall: z range; 45 deg flanks, SNAP[2] deep
SNAP_TIP_Z = 0.2                          # finger tip over the wall
SNAP_CLR = 0.15                           # finger to its window (tangential and radial)
SNAP_WEB = 1.6                            # carrier between its bore and each snap window
MSR_GAP = 1.0                             # pocket walls / cap to the MSR-2 and SHT40 bay frames
BAY_EDGE = 1.0                            # bay frames to the face plate's inner wall (top and bottom)
EU_VENT_Z = (6.0, 5.0, 6.0)               # edge vents: centre height at the top (MSR-2) and bottom (SHT40) edges, height

# ---- sensors (D-56, D-59, D-70): cap board in a printed carrier, the MSR-2 on its CN2 mate and three spacers ----
# All four spring pins on the 5 V board are the NA part (params.py PIN_*, Harwin P70-2200045) at one working height:
# two press on gold pads under the cap board (5 V for the sensors), two on the battery-free back cover's pads. The cap
# board's underside is level with the cover's pads. Nothing electrical crosses to the face plate (R9).
EU_PIN_WH = 6.8                           # design working height of the four pins (6.5..7.1 with PIN_TOL)
PINS = ((26.4, -4.8), (26.4, -7.6))       # sensor pins GND, +5 V (room x, y): on the 5 V board, clear of the right dome
PIN_CAP_HOLE_D = PIN_BARREL[0] + 2 * PIN_RADIAL   # cap / carrier hole round each pin barrel, all four pins (D-80)
CB_T = 1.6                                # cap board, FR4 (D-70)
CB_EDGE = 0.5                             # carrier to the trim's outer walls
CARRIER_RIM = 1.6                         # carrier's rim round the cap board, up to its top (D-70)
CB_RIM_CLR = 0.2                          # cap board to the rim
CB_POCKET_CLR = 0.3                       # cap board / carrier cut-out round the trim's pocket walls
CB_PAD_D = 2.4                            # gold pad under each sensor pin (plunger 0.9)
CB_SCREWS = ((-32.0, 48.0), (32.0, 36.0), (-32.0, -36.0), (32.0, -36.0))   # M2 x 6 thread-forming screws through the
                                          # cap board into the carrier
CB_SCREW_D, CB_TAP_D = 2.0, 1.6           # M2 clearance hole in the board; tap-drill hole in the carrier
CARRIER_CAP_CLR = 0.2                     # carrier's bore round the cap disc
CARRIER_SIDE = 2.0                        # carrier left outside its bore at the plate's sides (D-78)
# carrier clamp (D-71): a lip on the carrier's wall face reaches under the cap's edge into a rebate in the cap's
# underside; the cap's screws pin it to the wall. Full-thickness teeth of the cap at each snap angle sit in gaps in
# the lip: they stop the carrier turning (the wider key tooth: one way only).
LIP_T = 0.8                               # lip thickness = rebate depth (line-to-line)
LIP_SEAL_CLR = 0.5                        # rebate starts this far outside the seal band
LIP_CLR = 0.2                             # lip to the rebate's inner edge; lip gap to each tooth (each side)
LIP_TOOTH = 1.5                           # cap's tooth at each snap angle: finger width + 2 x SNAP_CLR + this, each side
MIC_ROW_DY = -7.0                         # microphone port below the MSR-2 centre, beside its bay frame
MIC_HOLE_EU = (1.6, 0.6, 3.0)             # sound hole (D-52): diameter, skin web left, recess from the face (diameter)

# ---- 5 V board (D-shaped, just under the cap, below the switch cup) ----
WB_T = 1.6
WB_CUT_CLR = 1.0                          # board's straight edge below the switch cup
WB_MOUNT = ((-12.0, -22.0), (16.8, -20.6))  # board holes (M2, from pcb/eu), screwed to bosses under the cap
WB_MOUNT_D, WB_BOSS_D = 2.2, 5.0          # board hole; cap boss (tap-drilled for an M2 thread-forming screw)
FRONT_PARTS = {"C1": (3.2, 1.6, 1.8)}      # 1206 capacitor on the 5 V board's front

# ---- mains board (round, at the rocker's PCB seat) ----
MB_T = 1.6
MB_PSU_C = (0.0, -12.5)                   # PSU centre (on the back), inputs on its upper row
PSU = (25.4, 25.4, 16.3)                  # DATASHEET Traco TMPS 03-105 body w, h, height above the board (rev. 2026-07-01)
WAGO_EU = (12.6, 16.7, 21.3)              # DATASHEET WAGO 2604-3102 (3D model): body 12.4 wide, 0.1 off the poles' centre
                                          # (bound +-6.3 about it), depth, height above the board
WAGO_PITCH = 5.0                          # DATASHEET pin spacing (poles)
WAGO_ROW = 8.2                            # DATASHEET (WAGO 3D model 2604-3102): distance of the two solder-pin rows
WAGO_ROW_OFF = 0.65                       # DATASHEET (WAGO 3D model): rows' centre from the body centre, towards the
                                          # entry side (body 3.6 past the first row, 4.9 past the second, lever side)
S1_WAGO_BODY_GAP = 0.0                    # S1's slot pads (back) may come up to the WAGO bodies, kept off their pins (D-88)
S1_WAGO_PIN_GAP = 3.5                     # S1's slot pads to any WAGO pad, copper edge to edge (D-24 L-N target)
MB_WAGO_C = ((16.6, 7.5), (-16.6, 7.5))   # L block (right), N block (left), body centres on the back; poles
                                          # along y, upper pole in, lower pole switched (as the rocker's poles);
                                          # levers towards the board centre
MB_SLOT = (-18.0, 18.0, -17.5, 2.0)       # routed relief slot under the PSU: x0, x1, y, width
MB_HDR = (-5.0, -20.5)                    # 2-pin header on the 5 V island (front): pin 1 (+5V) here, pin 2 (GND) 2.54 below
MB_BOSS = ((-17.5, 19.5), (17.5, 19.5), (-20.0, -12.0))  # mains board holes (M2) on long cap bosses: two beside
                                          # the switch cup, one through the 5 V board (the PSU end)
MB_BOSS_D, MB_BOSS_CLR = 6.0, 0.5         # long boss diameter; hole round it in the 5 V board (each side)
MB_FRONT_PARTS = {"RV1": (10.2, 8.0, 4.5),  # DATASHEET TDK CU4032 body (w, h, t)
                  "F1": (10.1, 3.1, 3.3)}  # REF Schurter UMT 250 body
HDR = (2.54, 5.08, 10.67)                 # DATASHEET Samtec TSM-102-02-L-SV (SMT): insulator 2.54 + post 8.13 above the board
HDR_BODY = 2.54                           # DATASHEET TSM insulator height
SOCKET = (2.54, 5.08, 8.5)                # MEASURE placeholder: 2.54 mm 1x2 pin socket, 8.5 mm (part and datasheet to cite)

# ================= derived =================
BOX_R = BOX_DIA / 2
SEAL_R = BOX_HOLE / 2 + COLLAR_LIP
POCKET_IN = (B_W + 2 * CLR, B_H + 2 * CLR)
POCKET_OUT = (POCKET_IN[0] + 2 * POCKET_WALL, POCKET_IN[1] + 2 * POCKET_WALL)
SEAT_Z = CAP_T                                             # remote's back on the cap (D-54)
PT = SEAT_Z + B_D - B_PROUD                                # plate face
DECK_Z = PT - SKIN
CAP_R = max(SEAL_R, POCKET_OUT[1] / 2) + CAP_MARGIN        # cap disc (covers seal band and pocket walls)
# switch cup: from the floor down to the rocker's panel
CUP_IN = (SW_BEZEL[0] + 2 * CLR, SW_BEZEL[1] + 2 * CLR)
CUP_OUT = (CUP_IN[0] + 2 * BARRIER_MIN, CUP_IN[1] + 2 * BARRIER_MIN)
PANEL_TOP_Z = SEAT_Z - SW_ROCKER_CLR - SW_ROCKER_H - SW_ROCKER_TOL   # rocker top under the remote at max tolerance
PANEL_BOT_Z = PANEL_TOP_Z - SW_PANEL_T
SW_BOT_Z = PANEL_TOP_Z - SW_BODY[2]                        # rocker's PCB seat = mains board front
DOMES = ((0.0, DOME_PITCH / 2), (DOME_PITCH / 2, 0.0), (0.0, -DOME_PITCH / 2), (-DOME_PITCH / 2, 0.0))
SCREWS = (DOMES[0], DOMES[2])             # top and bottom domes: countersunk in the pocket floor, under the remote
# supplied steel piece in a recess in the pocket floor, MAGNET_SETBACK below the seat, under the back cover's magnet;
# a cup under the recess, BARRIER_MIN under and round it (D-72)
MAGNET_Z = (SEAT_Z - MAGNET_SETBACK - MAGNET[2], SEAT_Z - MAGNET_SETBACK)
EU_MAGNET_Y = min(BC_STEEL_Y, SW_Y - CUP_IN[1] / 2 - BARRIER_MIN - MAGNET_CLR - MAGNET[1] / 2)   # under the cover's
                                                                                  # magnet, BARRIER_MIN from the switch cup
MAG_CUP_BOT = MAGNET_Z[0] - BARRIER_MIN                     # magnet cup's underside
MAG_BRIDGE = 20.0                         # longest bridge accepted over the recess (cap printed face down)
# 5 V board: circle less clearance, cut below the cup
WB_R = BOX_R - PLUG_CLR
BF_TIP_Z = SEAT_Z + BC_FLEX_Z                              # battery-free pins' tips on the cover's pads
CB_PAD_Z = BF_TIP_Z                                        # cap board underside (pads): level with the cover's pads
CB_TOP = CB_PAD_Z + CB_T
WB_FRONT = CB_PAD_Z - EU_PIN_WH                            # board front: all four pins at their design working height
WB_BACK = WB_FRONT - WB_T
WB_CUT_Y = SW_Y - CUP_OUT[1] / 2 - WB_CUT_CLR
MB_FRONT = SW_BOT_Z
MB_BACK = MB_FRONT - MB_T
DEEPEST = min(MB_BACK - PSU[2], MB_BACK - WAGO_EU[2])
HDR_GAP = WB_BACK - MB_FRONT                               # mains board front to the 5 V board's back
HDR_ENGAGE = (MB_FRONT + HDR[2]) - (WB_BACK - SOCKET[2])   # header post inside the socket
DOME_NOTCH_R = DOME_D / 2 + DOME_CLR      # board notch round a dome
# trim: finger scoops both sides of the pocket (D-73), the NA ellipsoid (params.py SCOOP) wider; below the depth where
# a wall reaches 45 deg it carries on at 45 deg to a flat bottom (face-down print, no supports)
SCOOP_EU = (7.5, 16.0, 9.0)               # ellipsoid radii x, y, z (NA 6.0, 16.0, 9.0)
SCOOP_RISE = 2.5                          # ellipsoid centre above the face (as NA)
SCOOP_X_EU = POCKET_IN[0] / 2 + 0.6       # scoop centre line (as NA): cuts into the pocket wall
SCOOP_FLAT = 2.0                          # flat bottom width (x)
SCOOP_WALL = 1.6                          # solid trim round each scoop
SCOOP_STEP = 0.5                          # loft section spacing (depth)
MSR_Y = POCKET_OUT[1] / 2 + MSR_GAP + BAY_WALL + MSR[1] / 2 + CLR
SHT_Y = -(POCKET_OUT[1] / 2 + MSR_GAP + BAY_WALL + SHT[1] / 2 + SHT_BAY_CLR)
PW = 2 * (CAP_R + CARRIER_CAP_CLR + CARRIER_SIDE + CB_EDGE + SKIN)   # face plate width: the carrier whole at the sides
PL_Y = (SHT_Y - SHT[1] / 2 - SHT_BAY_CLR - BAY_WALL - SKIN - BAY_EDGE,
        MSR_Y + MSR[1] / 2 + CLR + BAY_WALL + SKIN + BAY_EDGE)
PH = PL_Y[1] - PL_Y[0]
PC = (0.0, (PL_Y[0] + PL_Y[1]) / 2)                        # plate centre relative to the box centre

# sensors, derived
MSR_BACK_Z = CB_TOP + B2B_STACK                            # MSR-2's back on CN2 and the spacers on the cap board
MSR_CN2_X = MSR_BOARD[0] / 2 - MSR_CN2_IN
MSR_SPACERS = [(x, MSR_Y + y) for x, y in MSR2_POSTS]      # cap board's SMT spacers under the MSR-2, below its posts
SKIN_Z = PT - SKIN
MSR_FRAME = (MSR[0] + 2 * CLR, MSR[1] + 2 * CLR, BAY_WALL)      # trim's MSR-2 bay frame: inside w, h, wall
MIC_AT = (MSR_FRAME[0] / 2 + MSR_FRAME[2] + 0.3 + MIC_SPAN[0], MSR_Y + MIC_ROW_DY)   # mic port; its parts and lanes
                                          # between it and the bay frame (D-83)
CB_INSET = CB_EDGE + CARRIER_RIM + CB_RIM_CLR              # cap board edge in from the trim's outer walls' inside
SNAPS = [(a, SNAP_KEY_W if a == SNAP_ANGLES[0] else SNAP[0]) for a in SNAP_ANGLES]   # angle, width
SNAP_WIN_R = CAP_R + CARRIER_CAP_CLR + SNAP_WEB                 # snap windows' inner wall (radius)
SNAP_R = SNAP_WIN_R + SNAP[2] + SNAP_CLR                         # finger's inner face: room inside it to bend in
SNAP_WALL_R = SNAP_R + SNAP[1] + SNAP_CLR                         # carrier window's outer wall, with the groove
REBATE_R = SEAL_R + LIP_SEAL_CLR                            # cap's rebate for the carrier's lip, from here out
LIP_R = REBATE_R + LIP_CLR                                  # lip's inner edge
TEETH = [(a, w + 2 * SNAP_CLR + 2 * LIP_TOOTH) for a, w in SNAPS]   # cap's teeth at the snap angles: angle, width
CB_TOP_Y = PL_Y[1] - SKIN - CB_INSET                       # cap board's top edge
# the MSR-2's back switches stand deeper than CN2's stack: notches in the cap board's top edge (as the NA ring board)
EU_SW_CUTS = [(x - MSR2_SW[0] / 2 - MSR2_SW_CLR, x + MSR2_SW[0] / 2 + MSR2_SW_CLR,
               MSR_Y + MSR_BOARD[1] / 2 - MSR2_SW[1] - MSR2_SW_CLR) for x in MSR2_SW_X]   # x0, x1, y0
