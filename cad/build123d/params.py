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

Two printed parts (DESIGN D-12..D-17) and the wiring board (D-24..D-26):
  insert  (insert.py)  all barrier geometry: remote pocket, switch well and rocker
                       panel, collar flange. UL94 V-0 filament, printed floor-down.
  trim    (trim.py)    face, MSR-2 / SHT45 bays, vents. Any filament, face-down.
  board   (pcb/)       KiCad project; positions mirrored below and compared by checks.py.
"""
from math import sqrt, hypot

# ---- trim plate ----
PW, PH, PT, PR = 72.2, 131.75, 13.0, 6.0  # width (the flange plus clearance and skin), height, proud of wall, corner
                                          # radius (D-47: 5 V contact and mic above the flange, flex down its band)
PLATE_Y = 7.175                           # plate centre above the box centre (MSR-2 bay top, SHT45 bay bottom)
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
B_BACK_RUN = 9.1                          # ESTIMATE flat back inset from the outline (label drawing: flat 51.8 x 26.7)
B_BACK_RISE = 9.0                         # ESTIMATE height where the curved back meets the straight side
B_FRONT_R = 0.8                           # ESTIMATE front edge round-over (FCC external photo)
B_WHEEL_D = 41.5                          # ESTIMATE scroll wheel diameter (FCC photos)
B_WHEEL_Y = 12.5                          # ESTIMATE wheel centre above the remote centre (concentric with the end arc)
B_WHEEL_GAP = 0.3                         # ESTIMATE gap ring around the wheel
B_LED_Y = -12.0                           # ESTIMATE three LED dots, y of the row (terminal end)
B_LED_PITCH = 3.9                         # ESTIMATE
B_SEAM_Z = 9.8                            # MEASURED back cover depth, rim to back (human, 2026-10-09)
B_PROUD = 2.0
CLR = 0.5                                 # remote to pocket wall; 0.6 no longer fits the box with B_W = 45
POCKET_WALL = 1.6                         # pocket shell = mains barrier
SEAT_T = 2.5                              # minimum material under the remote seat
# The remote has a steel plate inside; it ships with an adhesive magnet for walls.
# That magnet is glued into a recess in the pocket floor. The recess is deeper than
# the magnet by MAGNET_SETBACK: the air gap weakens the pull (shim it up to strengthen).
# The supplied magnet (ESTIMATE ~47.4 x 17.5, full round ends R8.75) is cut once across by the user: the piece
# keeps one round end (down, in the recess's round end) and has a straight cut edge up.
MAGNET_FULL = (17.5, 47.4)                # ESTIMATE supplied magnet before the cut (w, length; label drawing ring)
MAGNET = (17.5, 18.5, 2.0)                # cut piece (w, length from the round end to the cut, t ESTIMATE incl. tape)
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
J2_POS = (13.0, -19.5)                    # SMD 5 V connector on F (front-view x, y; from pcb/), right of the slot
WIRE_SPACE_MIN = 10.0                     # free depth wanted behind the terminal block

# ---- board mounting: screw-in snap posts (D-28) ----
# Four PC-FR posts screw into bosses on the insert's underside and snap through holes in the
# board. Threads are cut after printing, M4 x 0.7: the bosses' holes are printed at the tap-drill
# size and tapped, the posts' studs at the major diameter and cut with a die.
MOUNT_HOLES = ((-21.0, 33.5), (-21.0, -33.5), (21.0, 24.77), (21.0, -33.5))  # board holes (front-view x, y; from pcb/)
MOUNT_HOLE_D = 2.6                        # board hole (pcb MOUNT_D)
MOUNT_BOSS_D = 7.0                        # boss on the insert, stands on the print-bed plane Z_BOT
# boss tops: 1 mm into the corner taper; top right rises into the pocket corner under the remote's
# back round-over, just enough to keep BARRIER_MIN over the hole's cone tip
MOUNT_BOSS_TOP = (-1.6, -1.6, -2.55, -1.6)
MOUNT_THREAD_D, MOUNT_TAP_D = 4.0, 3.3    # M4 x 0.7: stud before the die, tap-drill hole
MOUNT_THREAD_L = 7.0                      # tapped depth (the hole ends in a 45 deg cone)
MOUNT_THREAD_MIN = 6.0                    # minimum engagement, 1.5 x M4
MOUNT_PASS_GAP = 1.0                      # boss to the 5 V pass-through channel
POST_SHAFT_D = 2.3                        # through the board hole
POST_SHOULDER_D = 4.5                     # carries the board's front face
POST_HEAD_D, POST_HEAD_H = 3.2, 1.8       # split cone head over the board's back face
POST_SPLIT_W, POST_SPLIT_L = 0.6, 4.5     # slot through head and shaft, length above the head
POST_HEX_AF, POST_HEX_H = 6.0, 2.0        # hex collar against the boss, across flats
POST_FLAT = 0.1                           # flat on the stud side so the post prints lying down

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
PASS_D = 4.5                              # 5 V flex jumper pass-through (the only barrier opening): takes the
                                          # jumper's stiffened connector end when it is threaded through
PASS_X, PASS_Y = 21.5, 33.5               # vertical leg position (room frame, same side as J2)
PASS_DIR = (0.7071, 0.7071)               # 45 deg leg's direction in plan: out through the flange's top-right corner
BARRIER_MIN = 1.6                         # thinnest barrier wall allowed
V0_RATED_T = 1.5                          # DATASHEET thickness at which the chosen filament is UL94 V-0

# ---- Apollo MSR-2 (bare board, out of its case) ----
MSR = (40.0, 24.0, 10.0)                  # MEASURE envelope
RADAR_WALL = 1.2
LUX_POS = (12.0, 0.0)                     # MEASURE light sensor offset from bay centre

# ---- SHT45 breakout tab ----
SHT = (12.0, 8.0, 4.0)                    # SHT45 bay (the sensor sits on the flex tail, D-27)
SHT_Y = -51.3                             # just under the bottom screw boss

# ---- 5 V flex jumper: wiring board J2 -> pass-through -> pad end on the shelf (D-27, R9, no wires) ----
# J2 is a Hirose FH12-6S-0.5SH slide-lock FPC connector (3 contacts per net); the jumper's pad end
# lies on the insert shelf where the face plate's spring fingers press it. Its connector end is
# threaded through the pass-through from the shelf side and plugged into J2 with the board held
# beside the insert (latch in view); the spare length folds into the gap between board and insert.
FH12 = (6.1, 5.6, 2.0)                    # REF FH12-6S body (x, y, height): KiCad footprint / Hirose FH12 series
JUMPER_W = 3.0                            # flex run width
JUMPER_END = (3.5, 4.0, 0.3)              # MEASURE connector end: width (6 contacts at 0.5), stiffened length, thickness
JUMPER_T = 0.2                            # 2-layer polyimide flex (design value; confirm with the PCBWay stack-up)
JUMPER_X = 15.0                           # run between the rocker body (x <= 11.3) and the right-hand bosses
JUMPER_SERVICE = 40.0                     # spare length folded between board and insert (plug in with the board beside it)

# ---- sensor flex (D-27, D-47): MSR-2 CN2 -> spring fingers over the 5 V jumper's pad end -> SHT45 ----
# Single-layer flex in the trim: plug end under the MSR-2, out of the bay frame's right wall and up to just
# under the face skin while running right, a 45 deg fold into the top-right corner (microphone, spring-finger
# section), down the flange's right band on the flange top in a groove of the trim, a 45 deg fold at the
# bottom, along the bottom to the SHT45 bay.
MSR_BOARD = (38.0, 21.5)                  # REF bare MSR-2 board, from Apollo's case cavity 38.08 x 21.67 (Printables 932026)
MSR_HOOK = 0.5                            # snap hooks at the board's short ends: lip over its back face (D-45)
MSR_CN2_IN = 6.4                          # MEASURE REF CN2 centre from the board's end (Apollo wiki photo); CN2 at the right end here
B2B = (7.6, 3.0)                          # MEASURE REF CN2 housing (photo); 0.4 mm pitch, 2 rows, ~26-30 contacts (D-27)
B2B_STACK = 1.5                           # MEASURE mated height of CN2 + plug (1.5 if P4S-like)
FLEX_W, FLEX_T, STIFF_T = 4.0, 0.12, 0.15  # flex width (to the fingers), single-layer polyimide flex (back cover, EU),
                                          # FR4 stiffener under the plug / pins
SFLEX_T = 0.2                             # NA sensor flex: two copper layers (D-47; design value, confirm the stack-up)
PLUG_STIFF_T = 0.1                        # FR4 stiffener under the NA sensor flex's CN2 plug (stack behind the MSR-2)
FLEX_RUN_W = 2.4                          # flex width down the flange band: SDA, SCL, 3V3, GND to the SHT45
FLEX_PLUG = (12.0, 8.0)                   # plug end of the flex (along x, across): CN2 mate and fan-out
FLEX_NECK_L = 10.0                        # taper from the plug end to FLEX_W
FLEX_RIGHT = 33.4                         # flex's right edge in the corner and down the band (trim wall inside: PW / 2 - SKIN)
FLEX_SKIN_GAP = 0.15                      # flex + stiffener top below the trim's face skin
FLEX_GROOVE = 0.3                         # groove in the trim's underside over the flange band (flex SFLEX_T + 0.1)
TAPE_T = 0.06                             # 3M 467MP double-sided tape at the flex tape points (docs/ASSEMBLY.md)
FLEX_EXIT = 0.5                           # flex starts its rise this far right of the bay frame's right wall
SHT_PADDLE = 3.0                          # the tail widens back to FLEX_W from here (room x) for the SHT45
SHT_CHIP = (1.5, 1.5, 0.5)                # DATASHEET Sensirion SHT45 DFN-4 body, on the flex tail
# power contact: two Harwin S7081-42R SMT spring fingers (+5 V, GND) on the flex underside, side by side
FINGER = (3.18, 6.25)                     # DATASHEET S7081-42R body w x l (drawing S7081-42R iss. 7)
FINGER_PAD = (3.60, 6.65)                 # DATASHEET recommended pad layout
FINGER_FREE, FINGER_WH_MIN = 2.30, 1.70   # DATASHEET free height, recommended minimum working height
FINGER_WH = 2.0                           # design working height (datasheet recommends 2.10)
FINGER_TOL = 0.2                          # z stack tolerance (prints + flex) the working height must absorb
FINGERS = ((24.65, 45.5), (29.05, 45.5))  # +5V (outer), GND (inner) finger centres (x, y), long axis along y: in the
                                          # corner, left of the flex run, inside the shelf's print limit
SHELF_UNDER_Z = 7.0                       # shelf underside: 45 deg out from the seal band up to this height, then flat
SHELF_OUT = 2.8                           # flat underside beyond the 45 deg part (<= 3.0 prints unsupported)
TARGET_T = 0.6                            # jumper pad end thickness, flex + stiffener (pads under the fingers)
TARGET_X = (22.6, 31.1)                   # jumper pad end extent across (room x)
TARGET_Y0 = 41.8                          # jumper pad end's lower edge (the run joins here); it extends up over the fingers
TARGET_END = 1.6                          # pad end beyond the fingers' pads (upwards)
JUMPER_JOIN = 0.3                         # the jumper's run ends this far into the pad end (clear of the fingers)

# ---- microphone (D-29): I2S MEMS mic on the sensor flex, push-to-talk ----
# PUI Audio DMM-4026-B-I2S-R, bottom port, on the flex's underside on the run below the flange band, before
# the bottom fold (D-47). Its port faces the face skin through a hole in flex + stiffener, sealed to the skin
# by an adhesive gasket, and a sound hole through the skin.
MIC = (3.00, 4.00, 1.00)                  # DATASHEET body w x l x h (DMM-4026-B-I2S-R rev A)
MIC_PORT_IN = 1.00                        # DATASHEET port centre from the body's port end
MIC_Y = -44.4                             # body centre along the run (room y), port end up
MIC_FLEX_Y = 2.0                          # body centre from the corner run's centre line (FLEX_X), inwards (-x)
MIC_SEC_W = 5.4                           # widened flex section: edge from FLEX_X, inwards
MIC_SEC_Y = (-49.5, -41.9)                # widened section's extent along the run (room y): below the flange, above
                                          # the bottom fold
MIC_FLEX_HOLE_D = 0.5                     # port hole through flex + stiffener
MIC_GASKET_D = 2.6                        # adhesive gasket ring OD (ID = MIC_SKIN_HOLE_D), FLEX_SKIN_GAP thick
MIC_SKIN_HOLE_D = 1.0                     # sound hole through the face skin
MIC_CLR = 0.5                             # flex section and mic body to the insert and the bay frame

# ---- replacement back cover (D-35): the BILRESA E2490 without cells, powered from the plate ----
# Remote coordinates: origin = remote centre, x / y as the front view, z = 0 the back's outer face.
AAA_D, AAA_L = 10.5, 44.5                 # DATASHEET IEC 60086-2 LR03 / IEC 61951-2 HR03 maximum diameter, height
BC_CELL_X = 11.2                          # ESTIMATE cell axes at +-x (label drawing bays +-10.95, contacts +-11.4)
BC_CELL_Y0 = 0.0                          # REF compartment centre along y (FCC photos: centred; MEASURE)
BC_CELL_Z = 6.8                           # ESTIMATE cell axis above the back's outer face (wall + clearance + r)
BC_TERM_Y = -1                            # REF terminal end (VBAT / GND contacts) at -y, the LED end (FCC photos)
BC_VBAT_X = -1                            # REF VBAT contact on the -x cell, GND on the +x cell (FCC photos; check on a unit)
BC_WALL = 1.6                             # MEASURED cover shell thickness (human, 2026-10-09)
BC_PRY = (6.0, 1.2)                       # MEASURE screwdriver notch in the rim at the bottom end (-y): width, depth
# snap clips: one at each end (x = 0), free-standing inside the end wall, below the rim; the housing's edge comes
# down into the cover and the clip's hook catches its wall
BC_LATCH_W = 3.1                          # MEASURED clip width, both ends (human, 2026-10-09)
BC_LATCH_T = 1.2                          # ESTIMATE ear thickness (radial; photos)
BC_LATCH_HOOK = (0.7, 0.7)                # hook at the clip's tip, inwards (catches the housing's wall): both 0.2 deeper
                                          # than the original's 0.5 (did not catch on the print, human 2026-10-09)
BC_LATCH_RIM_GAP = 1.0                    # MEASURED top clip's top below the rim (human, 2026-10-09)
# clip tops above the inside floor: bottom end (-y) MEASURED; top end (+y) from BC_LATCH_RIM_GAP
BC_LATCH_TOPS = (4.7, B_SEAM_Z - BC_WALL - BC_LATCH_RIM_GAP)
# innermost point (hook tip) in from the outside rim: bottom end from its face 2.9 in (MEASURED on a print, human
# 2026-10-09), top end measured 2.8 on the original; both plus the deeper hooks. Where reach - hook - thickness
# < BC_WALL the clip's back merges into the end wall.
BC_LATCH_REACH = (2.9 + 0.7, 2.8 + 0.2)
# side ribs at mid-length (y 0), free-standing on the shell's curved floor, against flex (human, 2026-10-09)
BC_SIDE_TAB = (6.0, 0.8)                  # length along y (ESTIMATE, photos), thickness (human, 2026-10-09)
BC_SIDE_TAB_GAP = 36.2                    # MEASURED inside spacing between the ribs
BC_SIDE_TAB_RIM_GAP = 3.6                 # MEASURED rib's top below the rim
BC_STEEL = (12.0, 20.0, 2.0)              # MEASURED the remote's plate (a magnet), x, y, t (human, 2026-10-09); moved
                                          # from its own cover
BC_STEEL_FLOOR = BC_WALL                  # plate on the full shell thickness (as the original cover)
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
BC_END_SNAP = (1.0, 0.35, 0.1, 0.8, 0.05)  # snap hook beside each block's outer side over the end section's outer edge:
                                          # post thickness (flexes in x), lip reach over the edge, post to the edge, lip
                                          # thickness, lip to the copper face (PETG only, human 2026-10-09)
BC_END_SNAP_Z = (7.0, 9.0)                # lip band (below the rim, nothing enters the housing's contact slots)
BC_END_SNAP_BACK = 2.0                    # post length behind the stiffener (into the block's side)
BC_STEEL_CLIP = (6.0, 0.8, 0.45)          # clips at both ends of the plate's pocket: width, tab thickness, hook over the
                                          # plate's edge (broke in PLA; the cover prints in PETG, to verify)
BC_STEEL_CLIP_ROOT = 0.4                  # tab root: shell left under the relief round each tab (the tab flexes)
BC_STEEL_CLIP_RELIEF = 0.3                # relief round each tab (sides, behind, and towards the plate)
BC_STEEL_Y = -5.5                         # steel plate centre in the cover (the EU magnet sits under it, clear of the switch cup)
BC_FLEX_Z = FINGER_WH                     # flex underside above the back face: fingers at working height on flush pads
BC_FINGERS = ((14.4, 4.0), (14.4, -5.0))  # +5V, GND spring fingers (S7081-42R) on the cover's back (x, y), long axis y
BC_DOME_DY = 0.0                          # DATASHEET contact dome 3.15 +-0.25 from the bend end of the 6.25 body (~centred)
BC_WIN_CLR = 0.3                          # finger window round the finger body
BC_STRIP = (11.3, 16.5)                   # flex pad section across x (finger windows + the +3V3 lane past the GND finger)
BC_RUN = (10.7, 13.3)                     # flex run across x to the terminal end (clear of the curved wall; slot roof <= 3 mm)
BC_JOG = 6.0                              # y length of the regulator section between the pad section and the run
# 3.3 V regulator on the cover flex (D-41), copper down in a recess in the cover: TI TLV75533PDBVR + 1 uF in / out
BC_REG = {"U1": (13.1, -11.8), "C3": (14.6, -9.2), "C4": (12.5, -14.6)}   # part centres (remote x, y)
BC_REG_BODY = (3.0, 3.0, 1.45)            # DATASHEET TLV755P DBV (SOT-23-5): body + leads <= 3.0 x 3.0, 1.45 max high
BC_CAP0402 = (1.0, 0.5, 0.55)             # DATASHEET 0402 capacitor (CL05A105KP5NNNC): 1.0 x 0.5, 0.55 max high
BC_REG_RECESS = (11.4, 16.4, -15.0, -8.8) # recess under the regulator section (x0, x1, y0, y1), down to BC_REG_FLOOR
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
BC_BLOCK_W = BC_CONTACT_W + 1.0           # contact block width across
# pocket-floor insert (face plate side): printed floor, sensor-flex tongue with flush pads under the fingers
BC_FLOOR_T = 0.6                          # floor insert under the remote (raises it by this)
BC_FLOOR_CLR = 0.3                        # floor insert to the pocket wall
BC_FLOOR_PAD = (4.0, 7.0)                 # flush gold pads on the tongue under the fingers (finger 6.25 long)
BC_TONGUE_W = 5.0                         # sensor-flex tongue width
BC_TONGUE_Y = -12.0                       # tongue run from the right channel into the pocket (y), below the pads
BC_RECESS_CLR = 0.02                      # tongue recess depth over the flex thickness
# NA (D-49): the tongue is part of the sensor flex (face plate side). It leaves the finger section's left edge, runs
# left in the band above the flange under the trim's skin, a 45 deg fold turns it down the plate (copper up), along a
# groove in the skin's underside over the flange and under the trim's tab in the island notch, turns in its plane to
# meet the pocket's top arc square, down the wall behind the trim's strip (in a groove in the arc above the wall
# plane, in front of the wall below it), under the floor insert (a channel in its underside), up through a slot onto
# the pad strip on its top (copper up, pads flush) and the tail down through a second slot. A notch from each slot to
# the floor insert's edge lets the tongue be laid in sideways (no threading). The floor insert hangs from the
# strip's foot (snap), so face plate, strip, tongue and floor insert come off together; nothing is left on the insert.
BC_NA_WALL_X = 16.5                       # tongue goes down the pocket's top arc here (room x of the arc point)
BC_NA_TURN = 3.5                          # radial run on the island from the turn to the arc's top edge
BC_NA_BAND_Y = 43.0                       # tongue centre (room y) in the band above the flange
BC_NA_NECK_W = 2.4                        # tongue width from the finger section to the pad strip on the floor
BC_NA_TAB_W = 4.0                         # trim tab in the island notch (the tongue in a groove in its underside)
BC_NA_TAB_CLR = 0.25                      # trim tab and strip to the insert's notch and groove sides
BC_NA_TGROOVE = (BC_NA_NECK_W + 0.4, 0.3, 0.5)   # groove for the tongue in the trim's underside: width, depth, depth
                                          # at the fold (two layers)
BC_NA_STRIP = (4.4, 1.0)                  # trim strip down the pocket's arc over the tongue: width, thickness
BC_NA_TROOM = 0.3                         # room for the tongue behind the strip
BC_NA_JOG_E = 0.15                        # the groove's 45 deg end runs this far behind the strip's jog (room for the tongue)
BC_NA_DOWN = (15.4, 3.0, 7.8)             # floor: x centre and width of the strip down to the pads, pad strip top y
BC_NA_GROOVE_BOT = 0.5                    # wall groove's lower end (above the wall plane), 45 deg down to the wall
BC_NA_SLOT = 2.0                          # floor insert slots (the tongue rises / the tail drops): length along y
BC_NA_TAIL = 3.0                          # tail under the floor insert beyond the tail slot
BC_NA_FLOOR_TAB = (4.4, 0.8, 3.4)         # floor insert's tab in front of the strip's foot: width, thickness, height
BC_NA_FOOT_HOOK = (0.4, 0.8, (1.2, 2.4))  # strip foot's hook into the tab's window: reach, height, window z above
                                          # the floor insert's top

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

# MSR-2 bay sits just above the top screw (boss + countersink), SHT45 bay as before
MSR_Y = SCREW_PITCH / 2 + max(BOSS_R + SPLIT_CLR, SCREW_HEAD_D / 2 + 1.0) + MSR[1] / 2 + CLR
MSR_BACK_Z = PT - RADAR_WALL - MSR[2]     # MSR-2 board back (CN2 side) towards the wall
MSR_CN2_X = MSR_BOARD[0] / 2 - MSR_CN2_IN
SKIN_Z = PT - SKIN                        # underside of the trim's face skin
FLEX_HI_Z = SKIN_Z - FLEX_SKIN_GAP - STIFF_T - SFLEX_T  # flex underside in the corner and the bottom
FLEX_BAND_Z = DECK_Z                                    # flex underside down the flange band (on the flange top)
TARGET_TOP_Z = FLEX_HI_Z - FINGER_WH                    # target pads at the fingers' working height
SHELF_TOP_Z = TARGET_TOP_Z - TARGET_T
SHT_ENTRY = SHT[0] / 2 + 0.4 + 1.6 + 1.0  # flex tail enters the SHT45 bay frame from the right
FLEX_X = FLEX_RIGHT - FLEX_W / 2                                      # flex centre line on the corner run
FLEX_BAND_X = FLEX_RIGHT - FLEX_RUN_W / 2                             # flex centre line down the flange band
FRAME_RIGHT = MSR[0] / 2 + CLR + 1.6                                  # MSR-2 bay frame's right wall, outer face
FRAME_BOT = MSR_Y - MSR[1] / 2 - CLR - 1.6                            # MSR-2 bay frame's lower wall, outer face
FLEX_EXIT_X = FRAME_RIGHT + FLEX_EXIT                                 # rise starts here (room x)
FINGER_SEC_IN = min(x for x, _ in FINGERS) - FINGER_PAD[0] / 2 - 0.3  # finger section's inner (left) edge
FINGER_SEC_Y = (FINGERS[0][1] - FINGER_PAD[1] / 2 - 0.5, MSR_Y - FLEX_W / 2 - 0.5)   # from the pads to the fold
TARGET_Y = (TARGET_Y0, FINGERS[0][1] + FINGER_PAD[1] / 2 + TARGET_END)  # pad end extent along y
MIC_X = FLEX_X - MIC_FLEX_Y                                           # mic body centre (room x)
MIC_PORT = (MIC_X, MIC_Y + (MIC[1] / 2 - MIC_PORT_IN))                # port / sound hole axis (room x, y)
MIC_SEC_IN = FLEX_X - MIC_SEC_W                                       # widened section's inner (left) edge
FLEX_Z_LO = PLUG_STIFF_T + SFLEX_T / 2                                      # flex centre at the MSR-2 end
FLEX_Z_HI = FLEX_HI_Z + SFLEX_T / 2                                    # flex centre in the corner and the bottom
FLEX_Z_BAND = FLEX_BAND_Z + SFLEX_T / 2                                # flex centre down the band (on the flange)
FLEX_Z_SHT = SKIN_Z - 0.5 - SHT_CHIP[2] - SFLEX_T / 2                  # SHT45 on the flex top, 0.5 under the vents
_rc = ISLAND_R + FLANGE
_xb = FLEX_RIGHT - FLEX_RUN_W                                          # band run's left edge: last onto the flange
FLEX_Y_ON = FLANGE_OUT[1] / 2 - _rc + sqrt(max(0.0, _rc ** 2 - (_xb - (FLANGE_OUT[0] / 2 - _rc)) ** 2)) - 0.4
FLEX_Y_CLIMB = FLEX_Y_ON + 1.4                                        # band run climbs onto the flange from here


def pocket_wall_x(y):
    """x of the remote pocket's right wall at room y (stadium: straight sides, semicircular ends)."""
    a = POCKET_IN[0] / 2
    over = abs(y) - (POCKET_IN[1] / 2 - a)
    return a if over <= 0 else sqrt(a * a - over * over)


def end_top(a, b, n=48):
    """Top edge (x, z) of a contact block / flex end section from x = a to x = b: flat at BC_END_H above the flex,
    above the rim no further out than BC_END_R from the cell axis on that side."""
    cx = BC_CELL_X if a + b > 0 else -BC_CELL_X
    pts = []
    for i in range(n + 1):
        x = a + (b - a) * i / n
        dx = abs(x - cx)
        zc = BC_CELL_Z + sqrt(BC_END_R ** 2 - dx ** 2) if dx < BC_END_R else B_SEAM_Z
        pts.append((x, min(BC_FLEX_Z + BC_END_H, max(B_SEAM_Z, zc))))
    return pts


def pocket_wall_y(x, w=None):
    """y of the remote pocket's top wall at room x (inner stadium by default, or a stadium w wide)."""
    a = (w or POCKET_IN[0]) / 2
    return (POCKET_IN[1] / 2 - POCKET_IN[0] / 2) + sqrt(max(0.0, a * a - x * x))


def tongue_arc():
    """NA tongue (D-47) at the pocket's top arc: arc point P on the inner wall, outward radial unit u, the
    turn point Q on the island (P + BC_NA_TURN u); the straight run down across flange and island is at Q's x."""
    r = POCKET_IN[0] / 2
    yc = POCKET_IN[1] / 2 - r
    p = (BC_NA_WALL_X, pocket_wall_y(BC_NA_WALL_X))
    u = (p[0] / r, (p[1] - yc) / r)
    q = (p[0] + BC_NA_TURN * u[0], p[1] + BC_NA_TURN * u[1])
    return p, u, q


def na_tongue_route():
    """NA tongue centre line (D-49), 3D, from the finger section's left edge to the floor insert's first slot: the
    band (rising to the trim's groove), the 45 deg fold, down the plate, the radial turn, behind the strip down the
    arc's groove, the 45 deg jog out of it, down the wall, under the floor insert radially in, down the floor."""
    p, u, q = tongue_arc()
    z_sec = FLEX_HI_Z + SFLEX_T / 2
    z_g = SKIN_Z + BC_NA_TGROOVE[1] - SFLEX_T / 2
    r_up = BC_NA_STRIP[1] + BC_NA_TROOM / 2                 # behind the strip in the groove
    r_lo = -BC_NA_TROOM / 2 - 0.03                          # between the strip's proud foot and the wall (its curve)
    z_f = SEAT_Z + SFLEX_T / 2                              # on the pocket floor, under the floor insert
    gb = BC_NA_GROOVE_BOT
    zj = lambda r: gb + r + BC_NA_TROOM / 2 - BC_NA_JOG_E / 2   # mid-line between the strip's jog and the groove's end
    a, b = (p[0] + r_up * u[0], p[1] + r_up * u[1]), (p[0] + r_lo * u[0], p[1] + r_lo * u[1])
    xd, _, y_pad = BC_NA_DOWN
    s_floor = (b[0] - xd) / u[0]
    f = (xd, b[1] - s_floor * u[1])
    return [(FINGER_SEC_IN, BC_NA_BAND_Y, z_sec), (FINGER_SEC_IN - 1.5, BC_NA_BAND_Y, z_g), (q[0], BC_NA_BAND_Y, z_g),
            (q[0], q[1], z_g), (*a, z_g), (*a, zj(r_up)), (*b, zj(r_lo)), (*b, z_f), (*f, z_f), (xd, y_pad + BC_NA_SLOT, z_f)]


def in_rr(x, y, w, h, r):
    """Inside a rounded rectangle w x h (corner radius r) centred on the origin."""
    dx, dy = abs(x) - (w / 2 - r), abs(y) - (h / 2 - r)
    if dx <= 0 or dy <= 0:
        return abs(x) <= w / 2 and abs(y) <= h / 2
    return hypot(dx, dy) <= r


def flange_exit():
    """Horizontal run from the pass-through's vertical leg along PASS_DIR to the flange's outer edge."""
    t = 0.0
    while in_rr(PASS_X + t * PASS_DIR[0], PASS_Y + t * PASS_DIR[1], *FLANGE_OUT, ISLAND_R + FLANGE):
        t += 0.01
    return t


def flex_half_width(x):
    """Sensor flex half width at flat X (from the CN2 plug centre): plug end, neck taper, strip."""
    p, w = FLEX_PLUG[0] / 2, FLEX_PLUG[1] / 2
    if x <= p:
        return w
    if x >= p + FLEX_NECK_L:
        return FLEX_W / 2
    return w - (w - FLEX_W / 2) * (x - p) / FLEX_NECK_L


def jumper_path():
    """5 V flex jumper centre line (room x, y, z): J2 -> service loop (Z-fold in the gap between board
    and insert) -> pass-through (along the bottom of its 45 deg leg) -> pad end on the corner shelf."""
    zk = -1.0                                            # bend of the pass-through (insert.pass_through)
    ux, uy = PASS_DIR
    r = PASS_D / 2
    chord = r - sqrt(r * r - (JUMPER_W / 2) ** 2)        # the strip lies across the bottom of the round leg
    o = (r - chord - JUMPER_T) / sqrt(2)                 # strip centre below the leg's axis (plan and z parts)
    t = flange_exit()
    e = (J2_POS[0], WB_Y + J2_POS[1] + FH12[1] / 2 + 0.3, WB_FRONT_Z + FH12[2] / 2)
    lo, mid, hi = WB_FRONT_Z + FH12[2] + 1.5, (WB_FRONT_Z + Z_BOT) / 2, Z_BOT - 2.5
    y0 = WB_Y + J2_POS[1] + 9.0
    fold = JUMPER_SERVICE / 2                            # two runs of the Z-fold add the spare length
    xe, ye = PASS_X + (t + o) * ux, PASS_Y + (t + o) * uy
    return [e, (JUMPER_X, y0, lo), (JUMPER_X, y0 + fold, lo), (JUMPER_X, y0 + fold, mid),
            (JUMPER_X, y0, mid), (JUMPER_X, y0, hi), (JUMPER_X, PASS_Y - 4.0, hi),
            (PASS_X + o * ux, PASS_Y + o * uy, Z_BOT - 1.7), (PASS_X + o * ux, PASS_Y + o * uy, zk - o),
            (xe, ye, zk + t - o),                                            # leaves the flange's corner
            (xe, TARGET_Y[0] + JUMPER_JOIN, SHELF_TOP_Z + TARGET_T + JUMPER_T / 2)]


def jumper_length():
    pts = jumper_path()
    return sum(hypot(*(b[i] - a[i] for i in range(3))) for a, b in zip(pts, pts[1:]))
