"""Single source of truth for wall-plate geometry (mm).

Coordinates: X = width, Y = height (up), Z = out of the wall.
z = 0 is the wall surface, plate face at z = PT, z < 0 is inside the box (MAINS SIDE).

Tags:
  MEASURE   placeholder - replace with a caliper reading recorded in
            docs/MEASUREMENTS.md before printing anything final.
  ESTIMATE  taken from photos / drawings (source in docs/MEASUREMENTS.md, human request
            2026-10-08); replace with a caliper reading before printing anything final.
  REF       reference value from a published source (cited); confirm with calipers.
  DATASHEET value that must come from a cited datasheet (see docs/BOM.md).
  derived   computed below - do not edit, change the inputs instead.

v0.4 (DESIGN D-50, D-68): the printed insert and face plate, the wiring board and the ring board:
  insert  (insert.py)  all barrier geometry: remote pocket, switch well and rocker panel, collar flange with
                       its land on the ring board. UL94 V-0 filament.
  trim    (trim.py)    face plate, a plain cover: radar skin, bays, vents, sound hole. Any filament, face-down.
  board   (pcb/)       wiring board; positions mirrored below and compared by checks.py.
  ring    (ring.py)    ring board round the insert's plug: MSR-2 on CN2, SHT40, mic carrier, 5 V FFC in; the
                       riser with the battery-free remote's two spring pins (pcb/sensor/).
Also printed: the replacement back cover (backcover.py), coupons (coupons.py), steel plate jigs (plate_jig.py).
"""
from math import sqrt, hypot

# ---- trim plate ----
PW, PH, PT, PR = 72.2, 131.75, 14.4, 6.0  # width (the flange plus clearance and skin), height, proud of wall, corner
                                          # radius; PT = ring board + CN2 stack + MSR-2 + skin gap + radar skin (D-51,
                                          # D-66, checked)
PLATE_Y = 7.175                           # plate centre above the box centre (MSR-2 bay top, SHT40 bay bottom)
SKIN = 2.0                                # face/side wall of the hollow trim
FACE_CHAMFER = 1.2

# ---- NA single-gang device box ----
BOX_W, BOX_H = 50.8, 76.2                 # 2" x 3" opening
BOX_D = 63.5                              # MEASURE (2.5" assumed), per room
SCREW_PITCH = 83.3                        # #6-32 device ears, 3-9/32"
# #6-32 oval / flat head (ASME B18.6.3): shank 3.5, head 6.05-6.65 across, 82 deg countersink
SCREW_D, SCREW_HEAD_D = 3.6, 6.8         # clearance hole; countersink diameter at the face (head max + 0.15)
SCREW_CSK = 82.0                          # countersink included angle

# ---- IKEA BILRESA scroll wheel remote (kept intact, batteries in) ----
# B_W/B_H: IKEA UK product size 45 x 70 mm, matched by a third-party mount pocket
# (45.4 x 70.4). Reference values, confirm with calipers (docs/MEASUREMENTS.md).
B_W, B_H, B_D = 45.0, 70.0, 20.0          # REF outline (label drawing 1:1: 45.1 x 70.1) + depth (IKEA UK: 20 mm)
B_BACK_RUN = 8.1                          # MEASURED round-over across: gauge R8.1 fits the original cover best (human,
                                          # 2026-10-11; gauge burr 0.1-0.2, D-87)
B_BACK_RISE = 8.0                         # MEASURED round-over up, the same gauge
B_FRONT_R = 0.8                           # ESTIMATE front edge round-over (FCC external photo)
B_WHEEL_D = 41.5                          # ESTIMATE scroll wheel diameter (FCC photos)
B_WHEEL_Y = 12.5                          # ESTIMATE wheel centre above the remote centre (concentric with the end arc)
B_WHEEL_GAP = 0.3                         # ESTIMATE gap ring around the wheel
B_LED_Y = -12.0                           # ESTIMATE three LED dots, y of the row (terminal end)
B_LED_PITCH = 3.9                         # ESTIMATE
B_SEAM_Z = 9.8                            # MEASURED back cover depth, rim to back (human, 2026-10-09)
B_PROUD = 2.6                             # remote face above the plate face (keeps the seat with the thinner skin, D-51)
CLR = 0.5                                 # remote to pocket wall; 0.6 no longer fits the box with B_W = 45
POCKET_WALL = 1.6                         # pocket shell = mains barrier
SEAT_T = 2.5                              # minimum material under the remote seat
# The remote has a steel plate inside; it ships with an adhesive magnet for walls.
# That magnet is glued into a recess in the pocket floor. The recess is deeper than
# the magnet by MAGNET_SETBACK: the air gap weakens the pull (shim it up to strengthen).
# The supplied magnet (ESTIMATE ~47.4 x 17.5, full round ends R8.75) is cut once across by the user: the piece
# keeps one round end (down, in the recess's round end) and has a straight cut edge up.
MAGNET_FULL = (17.5, 47.4)                # ESTIMATE supplied steel plate (adhesive) before the cut (w, length; label drawing)
MAGNET = (17.5, 18.5, 2.0)                # cut steel piece (w, length from the round end to the cut, t ESTIMATE incl. tape)
# cutting jigs for the supplied steel plate (D-52): the whole plate in a pocket, round end on the stop, cut at MAGNET[1]
JIG_CLR, JIG_WALL, JIG_FLOOR = 0.15, 3.0, 2.0   # pocket clearance round the plate, side wall, floor
JIG_SAW = (1.2, 0.6, 8.0)                 # hacksaw guide: slot width, slot depth below the plate, wall height above it
JIG_NOTCH_R = 4.0                         # finger notches in the side walls to lift the plate out
MAGNET_Y = 0.0                            # ESTIMATE centre of the remote's internal plate (FCC photo: centred in its cover)
MAGNET_REC_Y = -3.75                      # cut piece centre: over the remote's plate and the back cover's steel, the
                                          # cut edge SEAT_T clear of the switch well
MAGNET_SETBACK = 0.5                      # magnet face below the seat
MAGNET_CLR = 0.3                          # recess clearance around the magnet
MAGNET_END_R = MAGNET[0] / 2              # ESTIMATE the magnet's round end (full round, label drawing R8.76)
MAGNET_SLOT_BOT = MAGNET_REC_Y - MAGNET[1] / 2 - MAGNET_CLR   # derived: recess bottom, at the round end

# ---- emergency rocker: Marquardt 1802.2504, DPST, PCB pins (D-26) ----
# DATASHEET: Marquardt drawing 1802.2504 rev g (2003-09-16). Mounted turned 90 deg: the
# drawing's 21 x 24 flange is 24 (x) x 21 (y) here; poles are the left/right pin columns.
SW_CUT = (21.9, 19.4)                     # DATASHEET cutout for a 1.25-2 mm panel (19.4 x 21.9)
SW_PANEL_T = 1.5                          # DATASHEET snap-in range 0.75-3 mm (cutout length depends on it)
SW_BEZEL = (24.0, 21.0)                   # DATASHEET flange 21 x 24
SW_ROCKER_H = 5.3                         # DATASHEET rocker top above the panel face (5.3 +- 0.5)
SW_ROCKER_TOL = 0.5                       # DATASHEET tolerance on SW_ROCKER_H
SW_ROCKER_CLR = 0.5                       # rocker top to the remote's back at maximum tolerance
SW_BODY = (22.0, 18.6, 16.2)              # DATASHEET body 18.6 x 22; depth = PCB seat below the panel's FRONT face
SW_PIN_GRID = (10.2, 7.0)                 # DATASHEET hole grid: poles 10.2 apart (x); pins 1 / 2 on the body's centre
                                          # line, 1a / 2a 7 off it (y)
SW_PAD = (6.2, 2.3)                       # plated slot pads (x, y) for the 1802.2504's pins and the E-Switch RA412C1100's
                                          # 4.8 x 0.8 tabs (D-88)
SW_SLOT_DY = 7.05                         # 1a / 2a slots off the centre line (1802.2504 pins 7.0, RA4 tabs 7.1)
SW_ALT_ROCKER_H = 6.0                     # DATASHEET E-Switch RA4: rocker top above the panel (second source, D-88)
SW_SW_DIR = 1                             # switched pins (1a / 2a) above (+1) or below (-1) the in pins (1 / 2)
SW_Y = 19.5                               # rocker centre (front-view y; from pcb/)
PAD_BODY_GAP = 1.0                        # through-hole pad edge to a part body on the other side of the board
                                          # (pin tail, solder fillet, iron)

# ---- wiring board (single board, D-24/D-25; KiCad project in pcb/) ----
WB = (47.0, 72.0, 1.6)                    # front face (F) towards the plate, back (B) into the box
WB_Y = 0.0                                # board centre
IRM = (37.0, 24.0, 15.0)                  # DATASHEET Mean Well IRM-03-5 body (IRM-03-SPEC 2025-08-08), on B
IRM_C = (0.0, -21.39)                     # PSU body centre on the board (front-view x, y; from pcb/)
WAGO6 = (32.4, 16.1, 20.7)                # DATASHEET WAGO 2604-1106 (3D model): width, depth at the board (entry face to
                                          # closed back; the levers overhang the entry side up top), height incl. pins (on B)
WAGO_X, WAGO_Y = 3.0, 5.05                # terminal block centre at the board (front-view x, y; from pcb/)
WAGO_ENTRY = (0, 1)                       # direction the wire entries face (front-view x, y): away from the PSU
WAGO_PSU_GAP = 1.0                        # minimum gap from the block's closed back to the PSU body
J2_POS = (13.5, -24.8)                    # SMD 5 V connector on F (front-view x, y; from pcb/), below the posts, FFC to +x
WIRE_SPACE_MIN = 10.0                     # free depth wanted behind the terminal block

# ---- board mounting: nylon standoffs (D-57) ----
# Four Keystone 25503 nylon M3 male-female hex standoffs (15 mm): the stud screws into a tapped blind hole in a boss
# on the insert's underside, a nylon M3 x 8 pan head screw through each board hole into the standoff. At the top
# right the pocket corner leaves room for a 5.5 mm hole only: that standoff's stud is cut to 5 mm before fitting.
MOUNT_HOLES = ((-21.0, 33.5), (-21.0, -33.5), (21.0, 24.77), (21.0, -33.5))  # board holes (front-view x, y; from pcb/)
MOUNT_HOLE_D = 3.2                        # board hole, M3 clearance (ISO 273 fine)
MOUNT_BOSS_D = 7.0                        # boss on the insert, from the standoff's face up into the insert
# boss tops: 1 mm into the corner taper; top right rises into the pocket corner under the remote's back round-over
MOUNT_BOSS_TOP = (-1.6, -1.6, -2.0, -1.6)
STANDOFF = (5.0, 8.0, 8.0)                # DATASHEET Keystone 25503 (catalog M65 p.76): hex across flats, male
                                          # thread length, internal thread depth; nylon 6/6 UL94 V-2
STANDOFF_L = 15.0                         # DATASHEET Keystone 25503 body length
MOUNT_STUD = (8.0, 8.0, 5.0, 8.0)         # stud length per hole (MOUNT_HOLES order): as supplied, top right cut to 5
STANDOFF_SCREW = (8.0, 5.6, 1.8)          # nylon M3 x 8 slotted pan head: length; head diameter and height ISO 1580 max
MOUNT_THREAD_D, MOUNT_TAP_D = 3.0, 2.5    # M3 x 0.5: stud, tap-drill hole (ISO 2306)
MOUNT_THREAD_L = tuple(s + 0.5 for s in MOUNT_STUD)   # tapped depth per hole: the stud plus 0.5 (45 deg cone end)
MOUNT_THREAD_MIN = 1.5 * 3.0              # stud engagement in the printed thread, >= 1.5 x M3
MOUNT_PASS_GAP = 1.0                      # boss to the 5 V pass-through channel

# ---- insert (box side, V-0) ----
PLUG_CLR = 0.75                           # insert body to box wall, each side
PLUG_R = 3.0
COLLAR_LIP = 1.25                         # flat seal band on the wall beyond the box edge
FLANGE = 3.0                              # flange beyond the island, clamped by the trim
ISLAND_RIM = 1.2                          # visible insert rim around pocket + scoops
ISLAND_R = 6.0
BOSS_R = 4.0                              # screw boss on the insert
KEY_D, KEY_H, KEY_CLR = 3.0, 1.0, 0.15    # locating pins insert -> trim (asymmetric = keyed)
KEY_POS = ((25.0, 30.0), (-25.0, -22.0))
SPLIT_CLR = 0.25                          # trim to insert clearance
SCOOP = (6.0, 16.0, 9.0)                  # finger scoop ellipsoid radii (x, y, z)
SCOOP_ZC = PT + 2.5                       # scoop centre height
PASS_D = 4.5                              # 5 V FFC pass-through (barrier opening, with the two pin holes): takes
                                          # the FFC's stiffened contact end when it is threaded through
PASS_E = (20.9, 32.9)                     # straight bore's top (D-74): it meets the flat slot here, at PASS_TOP_Z
PASS_RUN = 3.0                            # bore's run in plan from the underside plane (Z_BOT) to PASS_E, along PASS_DIR:
                                          # the most that keeps BARRIER_MIN to the remote pocket
PASS_BELOW = 4.0                          # bore modelled this far below the underside plane (cuts clean through)
PASS_DIR = (0.7071, 0.7071)               # bore and slot direction in plan: out through the flange's top-right corner
BARRIER_MIN = 1.6                         # thinnest barrier wall allowed
V0_RATED_T = 1.5                          # MEASURE placeholder: UL94 V-0 thickness of the chosen filament (TDS to cite)

# ---- Apollo MSR-2 with the SCD40 CO2 add-on, out of its case (msr2.py) ----
# Board frame: origin at the board's centre on its back face, x along the board (+x: the CN1 / CN2 end), y across
# (+y: the radar's edge), z out of the front. Sources: Apollo's case (Printables 932026, measured), the module
# datasheets, Apollo wiki photos (add-ons: CO2, GPIO header, rear USB-C); see docs/MEASUREMENTS.md.
MSR2_CASE = (38.08, 21.67, 10.41)         # REF case cavity w x h; face underside above the board's back plane
MSR2_ESP = (13.2, 16.6, 2.4)              # DATASHEET ESP32-C3-MINI-1 v1.3 (w x l x h)
MSR2_ESP_IN = 13.7                        # ESTIMATE module's +x side from the board's +x end; antenna end at the -y edge
MSR2_NOTCH = (13.7, 4.65)                 # ESTIMATE board notch under the ESP antenna (x, y), at the -y edge
MSR2_USB = (8.94, 7.35, 3.26)             # ESTIMATE USB-C receptacle (w, depth, h), top mount, flush with the -x end
MSR2_USB_Y = -5.3                         # REF case: USB opening y -9.65..1.35 about the cavity centre 1.19
MSR2_LD = (35.0, 7.0)                     # DATASHEET HLK-LD2410B module (x, y); flush with the +x end and the +y edge
MSR2_LD_T = 1.0                           # ESTIMATE radar board thickness
MSR2_LD_BACK = 8.4                        # ESTIMATE radar board's back above the board's back (photo, below the face)
MSR2_LD_PARTS = 0.9                       # ESTIMATE parts on the radar's front (its chip)
MSR2_LD_PINS = (5, 1.27, 1.2, 1.0)        # DATASHEET 5 pins at 1.27 along y; ESTIMATE 1.2 in from its +x end, 1.0 out of its front
MSR2_LD_PROP = (5.0, 5.0)                 # ESTIMATE support under the radar's -x end (photo; part unknown)
MSR2_CN1_IN = (6.1, 6.1)                  # ESTIMATE CN1 (front, the CO2 add-on's connector) centre from the +x end, -y edge
MSR2_CO2_BOARD = (11.0, 11.5, 0.8)        # ESTIMATE CO2 add-on board, centred on CN1
MSR2_SCD = (10.1, 10.1, 6.5)              # DATASHEET Sensirion SCD4x v1.4: 10.1 x 10.1 x 6.5 (Table 36, page 1)
MSR2_SW = (4.0, 3.0, 2.0)                 # ESTIMATE Boot / RST side-push switches on the back at the +y edge (x, y, h)
MSR2_SW_X = (-4.0, 4.0)                   # REF case: button holes at x -4.0 / 4.0, 0.5..1.5 behind the board
MSR2_HOLES = (0.9, 4.7)                   # ESTIMATE two plated holes on CN2's axis: diameter, offset either side of
                                          # CN2's centre (Apollo photos: CO2 add-on pic 8, rear USB-C pic 2)
MSR_SKIN_GAP = 0.3                        # NA: radar skin clear of the MSR-2's front (SCD4x, radar pins) (D-66)
MSR2_POSTS = ((-9.8, -3.9), (6.35, -3.9), (-17.5, 1.5))   # ESTIMATE face plate posts onto part-free spots on the
                                          # MSR-2's front (board frame): USB-C / ESP32, ESP32 / CO2 add-on, USB end;
                                          # NA: the ring board's spacers stand under them (D-68)
MSR2_POST_D = 1.8                         # NA: post diameter
MSR2_POST_CLR = 0.05                      # NA: least gap from a post to the MSR-2's parts
MSR2_SW_CLR = 0.3                         # switch bodies to the ring board's notches
MSR2_SCD_VENT = (2.0, 3, 3.5, 1.0)        # grille through the radar skin for the SCD4x and the light sensor: slot width,
                                          # count, pitch (along x), slot length = the SCD4x less this inset at each end;
                                          # the middle slot centred on the light sensor (D-65, D-69)
VENT_RADAR_CLR = 1.0                      # grille to the radar module's outline (slots shortened to keep it)
VENT_Z_OVER, VENT_H = 3.0, 5.0             # NA edge vents: centre above the ring board's parts, height
RADAR_WALL = 0.6                          # radar skin over the MSR-2 bay: three 0.2 mm layers (D-51)
LUX_POS = (12.0, 0.0)                     # MEASURE light sensor offset from bay centre

# ---- face plate bays and edge vents (NA and EU) ----
BAY_WALL = 1.6                            # MSR-2 and SHT40 bay frame wall
MSR_BAY_R = 1.0                           # MSR-2 bay frame inside corner radius
SHT_BAY_CLR, SHT_BAY_R = 0.4, 0.5         # SHT40 bay frame: inside clearance round SHT (each side), corner radius
MSR_VENTS = (5, 7.0, 1.5, 3.0, 6.0)       # vents through the top edge: count, pitch, x offset, slot width, depth (y)
SHT_VENTS = (3, 4.0, 2.0, 6.0, 10.0)      # SHT40 vents: count, pitch, slot width, face slot length, edge slot depth

# ---- SHT40 bay ----
SHT = (12.0, 8.0, 4.0)                    # SHT40 bay (the SHT40 DFN on the ring board below it, D-50)

# ---- 5 V cable: wiring board J2 -> pass-through -> ring board J1 (D-50) ----
# A stock FFC (6 contacts, 0.5 mm pitch) latched in Hirose FH12-6S-0.5SH slide-lock connectors at both ends: J2 on the
# wiring board, J1 on the ring board. It is pushed through the pass-through (a straight bore in the insert, D-74) from
# the box side; no loop in the box: J2 is plugged from the side with the board on its standoffs. The stock cable's
# spare length lies flat on the ring board, folded in four layers beside J1 (face side).
FH12 = (6.1, 5.6, 2.0)                    # REF FH12-6S body (x, y, height): KiCad footprint / Hirose FH12 series
JUMPER_W = 3.5                            # FFC width (6 contacts at 0.5)
JUMPER_END = (3.5, 4.0, 0.3)              # FFC contact end: width, stiffened length, thickness (FH12 FPC spec)
JUMPER_T = 0.12                           # FFC thickness
JUMPER_STOCK_L = 152.0                    # DATASHEET GCT 05-06-A-0152-A-4-06-4-G (or Wurth 687606152002): length
JUMPER_SLACK = (2.0, 10.0)                # spare length the route may leave (it bows in the free span): min, max
JUMPER_SPARE = 4.0                        # spare length the fold is sized to leave
JUMPER_FOLD_Y = 43.4                      # fold's centre line (room y): on the ring board between the flange and J1
JUMPER_LAYER = 0.15                       # fold's layer pitch (FFC 0.12)
JUMPER_SIDE_X, JUMPER_TURN_Y = 21.3, -11.0  # FFC from J2 out to the right, up past the spacer posts
JUMPER_WAYPOINT = (15.5, 24.8, -14.0)     # then between the rocker and the top-right standoff to the mouth (D-74)
PASS_TOP_Z = 2.3                          # the pass-through's 45 deg leg ends here (centre), a flat slot goes on out
PASS_SLOT = (4.5, 1.0, 3.5)               # flat slot out of the 45 deg leg, then a channel out to the board: width, height,
                                          # length along PASS_DIR
RING_J1 = (27.0, 48.2)                    # FH12 on the ring board (room x, y), cable in from -y

# ---- MSR-2 board and CN2 (NA ring board, EU cap board), back cover flex ----
MSR_BOARD = (38.0, 21.5)                  # REF bare MSR-2 board, from Apollo's case cavity 38.08 x 21.67 (Printables 932026)
MSR_BOARD_T = 1.6                         # MEASURE MSR-2 board thickness (the MSR envelope's x / y apply above it)
MSR_CN2_IN = 6.4                          # MEASURE REF CN2 centre from the board's end (Apollo wiki photo); CN2 at the right end here
B2B = (7.9, 3.4)                          # DATASHEET CN2 + plug, the larger of the pair: 51338-2474 7.9 x 3.4 with tails
                                          # (Molex SD-51338-003 rev K); 55909-2474 6.8 x 3.13 (SD-55909-003 rev J); D-82, D-89
B2B_STACK = 1.5                           # REF Molex 55909 plug on a 51338 receptacle: 1.5 mm mated (500913: 1.8); the
                                          # MSR-2's CN2 assumed 51338-2474, the more common one (human, D-82)
MSR2_CN1_STACK = B2B_STACK                # CN1 + the add-on's 55909 plug: the same receptacle assumed (D-82)
MSR2_FRONT = max(MSR_BOARD_T + MSR2_CN1_STACK + MSR2_CO2_BOARD[2] + MSR2_SCD[2],
                 MSR2_LD_BACK + MSR2_LD_T + max(MSR2_LD_PARTS, MSR2_LD_PINS[3]))   # front above the board's back
MSR = (40.0, 24.0, MSR2_FRONT)            # envelope (x, y from Apollo's case outside, height from the model)
FLEX_T = 0.12                             # single-layer polyimide flex (back cover)
SHT_CHIP = (1.5, 1.5, 0.5)                # DATASHEET Sensirion SHT40 DFN-4 body
# spring fingers: Harwin S7081-42R (the back cover's end contacts; EU)
FINGER = (3.18, 6.25)                     # DATASHEET S7081-42R body w x l (drawing S7081-42R iss. 7)
FINGER_PAD = (3.60, 6.65)                 # DATASHEET recommended pad layout
FINGER_FREE = 2.30                        # DATASHEET free height
FINGER_WH = 2.0                           # design working height (datasheet recommends 2.10)

# ---- microphone (D-29, D-83): Knowles SPK0641HT4H-1 top-port PDM mic + ADAU7002 PDM-to-I2S, on the board ----
# The ESP32-C3 has no PDM receiver: the ADAU7002 beside the mic turns its PDM into I2S on CN2's I2S lines. The face
# plate's sound column stands on a gasket on the board round the mic, hollow over it, its bore over the port
# (Knowles: gasket cavity >= 1.0, case hole 1.0-1.5).
MIC = (3.00, 4.00, 1.00)                  # DATASHEET SPK0641HT4H-1 rev A body w x l x h (+-0.10)
MIC_PORT_IN = 1.03                        # DATASHEET port centre from the body's port end (top face)
MIC_SKIN_HOLE_D = 1.6                     # sound hole through the face skin (1.0 closed up on the print, D-61)
MIN_PRINT_HOLE = 1.5                      # smallest open vertical hole the 0.4 mm nozzle prints reliably (D-61)
MIC_AT = (28.5, 63.0)                     # NA: port centre (room x, y), top right beside the MSR-2
MIC_BODY_Y = MIC_AT[1] - (MIC[1] / 2 - MIC_PORT_IN)   # mic body centre (port end up)
MIC_TUBE = (1.6, 0.3)                     # face plate's sound column: bore, gasket under its foot
MIC_BOOT = (0.2, 0.8, 0.3)                # boot over the mic: clearance round the body, wall, gap over its top
ADAU = (0.76, 1.56, 0.56)                 # DATASHEET ADAU7002 WLCSP CB-8-6 (rev C): w x l nominal, max height
# parts round the port: offset from the port (room x, y), body w, h, max height (C4 0402, 0.5 +-0.05 high; C3 1206 C0G,
# Murata GRM3195C1H104JA05D: 3.2 x 1.6, 0.95 max (DigiKey, D-98))
MIC_PARTS = {"U2": ((-4.1, -0.2), ADAU),                  # ADAU7002, ball A1 top left
             "C4": ((-5.2, -1.08), (0.5, 1.0, 0.55)),     # ADAU7002 100 nF on IOVDD
             "R1": ((-7.5, -0.6), (1.0, 0.5, 0.40)),      # I2S SD pull-down 100 k (ADAU7002 tristates SDATA)
             "C3": ((3.5, -2.525), (1.6, 3.2, 0.95))}     # microphone 100 nF C0G, outside the column's foot, pin 1 on the bus
MIC_SPAN = (9.6, 4.5)                     # board room the mic and its parts and lanes take left / right of the port

# ---- ring board (D-50, D-68): FR4 round the insert's collar, against the wall, under the face plate ----
RING_T = 1.6
RING_SIDE_CLR = 0.7                       # board edge to the face plate's side wall (beyond SPLIT_CLR)
RING_WIN_CLR = 0.3                        # board's window round the seal band
RING_LAND = 1.5                           # flat land at the flange taper's foot over the board's inner edge (D-68)
RING_RIB = (1.0, 0.15)                    # crush ribs on the collar's outside: width, interference into the board's
                                          # window edge (press fit for handling, D-68; COUPON coupon_ribs)
RING_RIBS = (("x", 22.0), ("y", 14.0))    # ribs on each straight side: along x at y +-22, along y at x +-14
RING_R = 3.4                              # outer corner radius
RING_KEEP = 8.0                           # copper path from the box opening's edge, along the wall (front layer: plus
                                          # the board's edge, RING_T); mains to 5 V target as on the wiring board (D-24)
SHT_AT = (0.0, -51.3)                     # SHT40 on the ring board (room x, y), in the face plate's vented bay
RING_NUT = (4.35, 1.5)                    # DATASHEET Wurth WA-SMSI M2 L1.5 9774015243R (SMT spacer): body diameter,
                                          # height; three under the MSR-2's board (D-68)
RING_NUT_HOLE, RING_NUT_PAD = 3.0, 5.3    # DATASHEET 9774015243R: unplated hole for its spigot, solder pad diameter
# small parts on the ring board: centre (room x, y), body w, h, max height
RING_SMALL = {"C1": ((21.0, 50.6), (1.6, 3.2, 1.8)),     # 22 uF 16 V 1206 at J1 (KEMET C1206C226M4PACTU, 1.8 max: DigiKey, D-95)
              "C2": ((2.6, -51.3), (0.5, 1.0, 0.55)),    # SHT40 100 nF 0402 (0.5 +-0.05)
              **{k: ((MIC_AT[0] + dx, MIC_AT[1] + dy), s) for k, ((dx, dy), s) in MIC_PARTS.items()}}

# ---- battery-free remote (D-50): two spring pins from the wiring board's 5 V area to the back cover's pads ----
# Harwin P70-2200045 SMT spring pin with peg (drawing P70-2200045 iss. 2, 2021-06-04). They stand on a riser board in
# a pocket under the pocket floor, through two holes in the floor (pin-filled barrier openings, human decision
# 2026-10-10); barrel and plunger enter windows in the cover's back onto pads on the cover flex. Two SMT spacer posts
# carry the riser and +5 V / GND up from the wiring board. The EU 5 V board carries the same pins (D-59).
PIN_FREE = 8.20                           # DATASHEET free height above the board
PIN_WH = (6.40, 7.10, 7.20)               # DATASHEET working height: minimum, normal, maximum
PIN_TOL = 0.3                             # stack tolerance the design working height must absorb (printed parts, boards)
PIN_FLANGE = (2.00, 1.00)                 # DATASHEET flange diameter, height
PIN_BARREL = (1.54, 6.20)                 # DATASHEET barrel diameter, top above the board
PIN_PLUNGER_D = 0.90                      # DATASHEET plunger
PIN_PEG = (1.00, 2.10)                    # DATASHEET peg diameter, length below the board
PIN_PAD_D, PIN_HOLE_D = 2.20, 1.20        # DATASHEET recommended solder pad, plated through hole for the peg
PIN_RADIAL = 0.2                          # floor holes round barrel and plunger
RISER = (14.0, 12.0, 0.8)                 # riser board w, h, t
RISER_C = (13.25, -13.4)                  # riser centre (room x, y): posts at its lower corners (in the wiring board's
                                          # 5 V area), the pins above and between them (D-79)
RISER_CLR = 0.3                           # riser to its pocket under the floor
# snap clips in the riser pocket (D-91): fingers hang from the pocket floor down past the riser's edges, a hook under its
# back face holds it against the pins' push. Clip centres on the riser's edges: (edge, position along it from the riser
# centre). With the two posts the top clip makes a three-point hold in line with the pins; the right one sits between the
# pins. None on the left edge: the steel piece's recess above it leaves no floor for a relief slot.
RISER_CLIPS = (("top", 0.0), ("right", 2.2))
RISER_CLIP = (3.0, 0.8, 0.4, 0.3)         # finger width, thickness, hook depth under the board, relief round the finger
RISER_CLIP_PLAY = 0.1                     # hook's catch face below the riser's back face
POSTS = ((9.85, -16.5), (16.65, -16.5))   # spacer posts on the wiring board's 5 V area (+5V, GND), level, the pins either side (D-60)
# each post: Wurth WA-SMSI M2 SMT spacer (soldered on the wiring board, 4.35 OD, through bore) + WA-SBRIE M2
# male-female brass standoff (4 mm hex) screwed into it; an M2 screw through the riser into the top; heatshrink over
# the stack
POST_STACK = (7.0, 10.0)                  # DATASHEET SMSI 9774070243R L 7 +-0.1, SBRIE 971100244 L 10
POST_THREAD = (5.0, 5.0)                  # DATASHEET SBRIE 971100244: male thread length, internal thread depth
POST_SPIGOT = (2.8, 1.4)                  # DATASHEET SMSI 9774070243R: locating spigot diameter, length (in the
                                          # land pattern's 3.0 unplated hole; solder on the front ring only)
RISER_SCREW_L = 5.0                       # M2 x 5 pan head through the riser into the SBRIE
M2_HEAD = (4.0, 1.6)                      # DATASHEET ISO 7045 M2 pan head dk, k (max)
POST_SP = (4.62, 0.4)                     # post across the hex corners, sleeve (heatshrink) wall

# ---- replacement back cover (D-35): the BILRESA E2490 without cells, powered from the plate ----
# Remote coordinates: origin = remote centre, x / y as the front view, z = 0 the back's outer face.
AAA_D, AAA_L = 10.5, 44.5                 # DATASHEET IEC 60086-2 LR03 / IEC 61951-2 HR03 maximum diameter, height
BC_CELL_X = 11.2                          # ESTIMATE cell axes at +-x (label drawing bays +-10.95, contacts +-11.4)
BC_CELL_Y0 = 0.0                          # REF compartment centre along y (FCC photos: centred; MEASURE)
BC_CELL_Z = 6.8                           # ESTIMATE cell axis above the back's outer face (wall + clearance + r)
BC_TERM_Y = -1                            # REF terminal end (VBAT / GND contacts) at -y, the LED end (FCC photos)
BC_VBAT_X = -1                            # REF VBAT contact on the -x cell, GND on the +x cell (FCC photos; check on a unit)
BC_WALL = 1.6                             # MEASURED cover shell thickness (human, 2026-10-09)
BC_SIDE_WALL = BC_WALL - 0.1              # side wall: 0.1 more room inside all round for the remote's housing (D-75)
BC_PRY = (6.0, 1.2)                       # MEASURE screwdriver notch in the rim at the bottom end (-y): width, depth
# snap clips: one at each end (x = 0), free-standing inside the end wall, below the rim; the housing's edge comes
# down into the cover and the clip's hook catches its wall
BC_LATCH_W = (4.0 - 2 * 0.15, 3.1)        # clip width (bottom, top): bottom fills the housing's 4.0 slot less 0.15 each side
                                          # (human 2026-10-11, D-92); top MEASURED 3.1 (human, 2026-10-09)
BC_LATCH_T = 1.2                          # ESTIMATE ear thickness (radial; photos)
BC_LATCH_HOOK = (0.8 + 0.3, 0.7)          # hook at the clip's tip, inwards (catches the housing's wall): top 0.2 deeper
                                          # than the original's 0.5, bottom 0.3 (test prints, human 2026-10-09/10), bottom
                                          # 0.3 more (it snapped once, then not again: human 2026-10-11, D-92)
BC_LATCH_RIM_GAP = 1.0                    # MEASURED top clip's top below the rim (human, 2026-10-09)
# clip tops above the inside floor: bottom end (-y) MEASURED 4.7 plus 0.2 towards the rim (test print, human
# 2026-10-10); top end (+y) from BC_LATCH_RIM_GAP
BC_LATCH_TOPS = (4.7 + 0.2, B_SEAM_Z - BC_WALL - BC_LATCH_RIM_GAP)
# innermost point (hook tip) in from the outside rim: bottom end from its face 2.9 in (MEASURED on a print, human
# 2026-10-09), top end measured 2.8 on the original; both plus the deeper hooks. Where reach - hook - thickness
# < BC_WALL the clip's back merges into the end wall.
BC_LATCH_REACH = (2.9 + BC_LATCH_HOOK[0], 2.8 + 0.2)
# small tabs inside both long side walls, two per side either side of mid-length, into slots in the housing's long
# sides (human, 2026-10-11, D-90): the slots' inside / outside spacing along y, tab top below the rim, tab height,
# tab protrusion from the wall
BC_TAB = (18.0, 25.0, 1.0, 0.8, 0.25 + 0.2)   # MEASURED (slots corrected 2026-10-11: 18 / 25, was 23 / 25); protrusion
                                          # the human's figure: 0.5, halved, then 0.2 more after the first print (D-92)
BC_TAB_CLR = 0.15                         # tab ends clear of the slots' ends (along y)
# side ribs at mid-length (y 0), free-standing on the shell's curved floor, against flex (human, 2026-10-09)
BC_SIDE_TAB = (6.0, 0.8)                  # length along y (ESTIMATE, photos), thickness (human, 2026-10-09)
BC_SIDE_TAB_GAP = 36.2                    # MEASURED inside spacing between the ribs
BC_SIDE_TAB_RIM_GAP = 3.6                 # MEASURED rib's top below the rim
BC_STEEL = (12.0, 20.0, 2.0)              # MEASURED the remote's plate (a magnet), x, y, t (human, 2026-10-09); moved
                                          # from its own cover
BC_STEEL_FLOOR = 0.8                      # plate, its ridge and clips 0.8 deeper than the full shell: a clip post touched
                                          # the housing (D-96), then as deep as the clips allow, for a stronger pull on
                                          # the steel piece (human 2026-10-11, D-99)
BC_STEEL_CLR = 0.05                       # plate to the ridge (0.15 rattled on the first print, human 2026-10-09)
BC_STEEL_CLIP_CLR = 0.15                  # plate's ends to the clips' tabs (fit confirmed on the first print)
BC_STEEL_RIDGE = (0.8, 1.2)               # ESTIMATE ridge round the plate (photos): thickness, height above the floor
BC_STEEL_RIDGE_GAP = 0.4                  # ridge to each side of a clip (the clip flexes free)
BC_REG_FLOOR = 0.4                        # cover wall left under the regulator recess
# cover flex retention (D-45): FR4 stiffener on the pad / regulator section, pressed down past snap hooks on both long
# edges (beside each finger and the regulator); the end section drops into a slot (a lip in front of each contact
# block) and snaps under a hook on the block's top
BC_PAD_STIFF_T = 0.8                      # FR4 stiffener on the pad and regulator sections (non-copper side, up)
BC_PAD_END = 1.0                          # flex beyond the upper finger's body
BC_FLEX_SNAP = (3.0, 0.7, 0.3, 0.1)       # snap hooks: width along y, post thickness, lip over the stiffener, post to
                                          # the stiffener's edge
BC_FLEX_SNAP_GAP = 0.05                   # lip underside above the stiffener's top
BC_FLEX_SNAP_ROOT = 0.4                   # post root: shell left under the relief round each post (the post flexes)
BC_FLEX_SNAP_RELIEF = 0.3                 # relief round each post (sides and behind)
BC_END_LIP = (1.2, 1.0, 0.1)              # lip in front of each block's foot: thickness, height above the ledge, gap
BC_END_SLOT = (0.8, 0.1, 0.5, 0.8, 0.1)   # slot along each block's outer face, the end section slides down it: side wall,
                                          # wall to the section's edge, lip reach over the edge, lip thickness, lip to copper
BC_STEEL_CLIP = (6.0, 0.48, 0.45)         # clips at both ends of the plate's pocket: width, tab thickness, hook over the
                                          # plate's edge (broke in PLA; the cover prints in PETG, to verify); tab 0.48
                                          # (was 0.8): 0.8 shorter with the plate sunk, strain <= 3 % (D-96, D-99)
BC_STEEL_CLIP_ROOT = 0.4                  # tab root: shell left under the relief round each tab (the tab flexes)
BC_STEEL_CLIP_RELIEF = 0.3                # relief round each tab (sides, behind, and towards the plate)
BC_STEEL_Y = -5.5                         # steel plate centre in the cover (the EU magnet sits under it, clear of the switch cup)
BC_FLEX_Z = 2.0                           # flex underside above the back face (the regulator hangs in a recess under it)
BC_FINGERS = ((13.2, -8.9), (13.2, -13.5))    # +5V, GND pads on the cover flex (x, y), the pad section above the GND
                                          # contact post (D-79): the spring pins come up
                                          # through windows in the back onto them, either side of the posts' line (D-53)
BC_DOME_DY = 0.0                          # DATASHEET contact dome 3.15 +-0.25 from the bend end of the 6.25 body (~centred)
BC_WIN_CLR = 0.3                          # window round the spring pin's barrel (it enters the window)
BC_PAD_D = 2.6                            # gold pad under each spring pin (cover flex)
BC_STRIP = (10.7, 16.5)                   # pad and regulator sections across x: +3V3 lane left of the pads, GND right
BC_RUN = (7.2, 9.8)                       # flex run across x to the terminal end: past the GND contact post's inner face,
                                          # clear of the steel plate's ridge (D-79)
BC_RUN_JOG = 2.0                          # jog from the pad section's inner edge across to the run, at its bottom
BC_JOG = 6.6                              # y length of the regulator section, above the pad section (D-53)
BC_PAD_LOW = 0.6                          # flex below the lower pad (the pad section ends just above the terminal bend)
# 3.3 V regulator on the cover flex (D-41), copper down in a recess in the cover: TI TLV75533PDBVR + 1 uF in / out
BC_REG = {"U1": (13.6, -3.3), "C3": (15.0, -5.7), "C4": (13.2, -0.7)}    # part centres (remote x, y)
BC_REG_BODY = (3.0, 3.0, 1.45)            # DATASHEET TLV755P DBV (SOT-23-5): body + leads <= 3.0 x 3.0, 1.45 max high
BC_CAP0402 = (1.0, 0.5, 0.55)             # DATASHEET 0402 capacitor (CL05A105KO5NNNC): 1.0 x 0.5, 0.55 max high
BC_REG_RECESS = (11.4, 16.4, -6.5, -0.3) # recess under the regulator section (x0, x1, y0, y1), down to BC_REG_FLOOR
BC_END_T = 0.4                            # FR4 stiffener behind the flex's end section
BC_END_H = 8.8                            # flex end section height above the flex plane: the contact pads plus 0.5
BC_END_R = AAA_D / 2 - 0.25               # above the rim, blocks and end section stay inside this circle round each cell
                                          # axis (the cell's room in the housing; square corners hit it, human 2026-10-09)
BC_CONTACT_W = FINGER_PAD[1] + 1.0        # end section width round each contact finger (long axis across x)
BC_TERM_SETBACK = 0.0                     # MEASURE fixed (+) contact plate's face behind the cell's end plane (0 = on it)
BC_END_CORNER = 1.5                       # 45 deg cut at the end section's lower outer corners (cover's curved back)
BC_PCB_W = 11.6                           # ESTIMATE the plastic divider between the cells (drawing; the PCB is 11.1)
BC_PCB_CLR = 0.5                          # flex end section to the PCB strip
BC_BRIDGE_H = 2.0                         # MEASURE flex band passing under the PCB strip (below its back-side parts)
BC_LANE_H = 0.6                           # +3V3 lane across the band, above the bend line (below the contact fingers)
BC_BLOCK_T = 4.0                          # contact block depth behind the end section (along the cell axis)
BC_BLOCK_XO = BC_CELL_X + BC_CONTACT_W / 2 + 0.5            # contact blocks' outer faces (|x|)
BC_END_XO = BC_BLOCK_XO - BC_END_SLOT[0] - BC_END_SLOT[1]   # end section's outer edges (|x|), inside the slots

# ================= derived =================
BC_CELL_END_Y = BC_CELL_Y0 + BC_TERM_Y * AAA_L / 2                    # a full-length cell's terminal end
BC_COPPER_Y = BC_CELL_END_Y + BC_TERM_Y * (BC_TERM_SETBACK - FINGER_WH)  # end section copper: contact fingers
                                                                       # at working height on the fixed plate
SEAT_Z = PT + B_PROUD - B_D               # remote's back rests here
POCKET_IN = (B_W + 2 * CLR, B_H + 2 * CLR)
POCKET_OUT = (POCKET_IN[0] + 2 * POCKET_WALL, POCKET_IN[1] + 2 * POCKET_WALL)
WELL_FLOOR_Z = SEAT_Z - SW_ROCKER_H - SW_ROCKER_TOL - SW_ROCKER_CLR   # top face of the switch panel
PANEL_BOT_Z = WELL_FLOOR_Z - SW_PANEL_T   # underside of the switch panel
WELL_IN = (SW_BEZEL[0] + 2 * CLR, SW_BEZEL[1] + 2 * CLR)
DECK_Z = PT - SKIN                        # insert flange top = trim face underside

WB_FRONT_Z = WELL_FLOOR_Z - SW_BODY[2]    # board front face = rocker PCB seat (measured from the panel's front face)
WB_BACK_Z = WB_FRONT_Z - WB[2]
MOUNT_FACE_Z = WB_FRONT_Z + STANDOFF_L    # bosses' faces: the standoffs' bodies between them and the board
Z_BOT = PANEL_BOT_Z                       # lowest point of the insert = print bed (panel underside)

# insert outline
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
MSR_BACK_Z = RING_T + B2B_STACK         # MSR-2 board back (CN2 side): on CN2 on the ring board, MSR_SKIN_GAP under the skin
MSR_CN2_X = MSR_BOARD[0] / 2 - MSR_CN2_IN
# the MSR-2's back switches stand deeper than the CN2 stack: notches in the ring board's top edge
MSR_SW_CUTS = [(x - MSR2_SW[0] / 2 - MSR2_SW_CLR, x + MSR2_SW[0] / 2 + MSR2_SW_CLR,
                MSR_Y + MSR_BOARD[1] / 2 - MSR2_SW[1] - MSR2_SW_CLR) for x in MSR2_SW_X]   # x0, x1, y0 (room)
RING_NOTCH_R = 0.5                        # inside corner radius of milled notches
MSR_SPACERS = [(x, MSR_Y + y) for x, y in MSR2_POSTS]   # ring board's SMT spacers under the MSR-2, below its posts (room)
SKIN_Z = PT - SKIN                        # underside of the trim's face skin
# ring board
_ring_in = SKIN + SPLIT_CLR + RING_SIDE_CLR                            # trim's outer edge to the board's edge
RING_HALF_W = PW / 2 - _ring_in
RING_Y = (PLATE_Y - PH / 2 + _ring_in, PLATE_Y + PH / 2 - _ring_in)
RING_INNER = (SEAL[0] + 2 * RING_WIN_CLR, SEAL[1] + 2 * RING_WIN_CLR, PLUG_R + COLLAR_LIP + RING_WIN_CLR)
RING_PARTS_TOP = RING_T + max([FH12[2]] + [d[2] for _, d in RING_SMALL.values()])   # tallest part on the ring board
FRAME_Z0 = RING_PARTS_TOP + SPLIT_CLR     # face plate's bay frames end here, over the ring board's parts (D-68)
# spring pins: tip on the cover flex's pads, riser board under the pocket floor
PIN_TIP_Z = SEAT_Z + BC_FLEX_Z
RISER_BOT = WB_FRONT_Z + POST_STACK[0] + POST_STACK[1]
RISER_TOP = RISER_BOT + RISER[2]
PIN_WORK = PIN_TIP_Z - RISER_TOP          # pins' design working height on the pads


def end_top(a, b, n=48):
    """Top edge (x, z) of a contact block / flex end section from x = a to x = b: flat at BC_END_H above the flex,
    no further out than BC_END_R from the cell axis on that side above the rim, and outboard of the axis above it
    (the battery holder shell wraps the cell there)."""
    cx = BC_CELL_X if a + b > 0 else -BC_CELL_X
    pts = []
    for i in range(n + 1):
        x = a + (b - a) * i / n
        dx = abs(x - cx)
        zc = BC_CELL_Z + sqrt(BC_END_R ** 2 - dx ** 2) if dx < BC_END_R else BC_CELL_Z
        outboard = (x - cx) * cx > 0
        floor = BC_CELL_Z if outboard else B_SEAM_Z
        pts.append((x, min(BC_FLEX_Z + BC_END_H, max(floor, zc))))
    return pts


def pass_points():
    """Pass-through axis (D-74): the straight bore's point in the underside plane (Z_BOT), its top where it meets the
    flat slot, the slot's end (room x, y, z)."""
    ux, uy = PASS_DIR
    e = (*PASS_E, PASS_TOP_Z)
    m = (e[0] - PASS_RUN * ux, e[1] - PASS_RUN * uy, Z_BOT)
    f = (e[0] + PASS_SLOT[2] * ux, e[1] + PASS_SLOT[2] * uy, PASS_TOP_Z)
    return m, e, f


def pass_at(z):
    """Point on the bore's axis at height z."""
    m, e, _ = pass_points()
    t = (z - m[2]) / (e[2] - m[2])
    return tuple(m[i] + t * (e[i] - m[i]) for i in range(3))


def jumper_path():
    """5 V FFC centre line (room x, y, z): J2 -> out to the right, up past the spacer posts -> between the rocker and the
    top-right standoff to the mouth -> the straight bore -> the flat slot -> out of the flange onto the ring board ->
    the fold -> J1 (D-74)."""
    return _jumper_pts(jumper_fold())


def _jumper_pts(fold):
    """The route with a fold of length `fold` (four flat layers along -x from J1's x, on the ring board)."""
    _, e, f = pass_points()
    jy = WB_Y + J2_POS[1]
    ent = (J2_POS[0] + FH12[1] / 2 + 0.3, jy, WB_FRONT_Z + FH12[2] / 2)          # J2 turned: cable out to +x
    lo = WB_FRONT_Z + FH12[2] + 1.5
    j1 = (RING_J1[0], RING_J1[1] - FH12[1] / 2 - 0.3, RING_T + 0.6)
    xr, xl, yb = RING_J1[0], RING_J1[0] - fold, JUMPER_FOLD_Y
    zs = [RING_T + 0.1 + i * JUMPER_LAYER for i in range(4)]
    layers = [(xr, yb, zs[0]), (xl, yb, zs[0]), (xl, yb, zs[1]), (xr, yb, zs[1]),
              (xr, yb, zs[2]), (xl, yb, zs[2]), (xl, yb, zs[3]), (xr, yb, zs[3])]
    return [ent, (JUMPER_SIDE_X, jy, lo), (JUMPER_SIDE_X, JUMPER_TURN_Y, lo), JUMPER_WAYPOINT, pass_at(Z_BOT - 1.0),
            e, f] + layers + [j1]


def _length(pts):
    return sum(hypot(*(b[i] - a[i] for i in range(3))) for a, b in zip(pts, pts[1:]))


def jumper_fold():
    """Fold length that leaves JUMPER_SPARE of the stock cable (4 mm of each end in its connector)."""
    target = JUMPER_STOCK_L - 2 * JUMPER_END[1] - JUMPER_SPARE
    return (target - _length(_jumper_pts(0.0))) / 4


def jumper_length():
    return _length(jumper_path())
