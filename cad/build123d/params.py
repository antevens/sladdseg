"""Geometry both variants share (mm): the BILRESA remote and its replacement back cover, the supplied steel plate,
the rocker switch, the Apollo MSR-2, the SHT40, the microphone, the spring pins, the face plates' common sizes.

Each variant adds its own on top: na/params_na.py (North American single-gang box) and eu/params_eu.py (European
round flush box, DIN 49073); both start with `from params import *`.

Coordinates: X = width, Y = height (up), Z = out of the wall. z = 0 is the wall surface, z < 0 is inside the box
(MAINS SIDE).

Tags:
  MEASURE   placeholder - replace with a caliper reading recorded in
            docs/MEASUREMENTS.md before printing anything final.
  ESTIMATE  taken from photos / drawings (source in docs/MEASUREMENTS.md, human request
            2026-10-08); replace with a caliper reading before printing anything final.
  REF       reference value from a published source (cited); confirm with calipers.
  DATASHEET value that must come from a cited datasheet (see docs/BOM.md).
  derived   computed below - do not edit, change the inputs instead.
"""
from math import sqrt

# ---- face plates (both variants) ----
PR = 6.0                                  # face plate corner radius
SKIN = 2.0                                # face/side wall of the hollow face plate
FACE_CHAMFER = 1.2
SPLIT_CLR = 0.25                          # face plate to barrier clearance
BARRIER_MIN = 1.6                         # thinnest barrier wall allowed
V0_RATED_T = 1.5                          # MEASURE placeholder: UL94 V-0 thickness of the chosen filament (TDS to cite)
PAD_BODY_GAP = 1.0                        # through-hole pad edge to a part body on the other side of the board
                                          # (pin tail, solder fillet, iron)
M2_HEAD = (4.0, 1.6)                      # DATASHEET ISO 7045 M2 pan head dk, k (max)

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
MAGNET_SETBACK = 0.5                      # magnet face below the seat
MAGNET_CLR = 0.3                          # recess clearance around the magnet
MAGNET_END_R = MAGNET[0] / 2              # ESTIMATE the magnet's round end (full round, label drawing R8.76)

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
                                          # NA: the sensor board's spacers stand under them (D-68)
MSR2_POST_D = 1.8                         # NA: post diameter
MSR2_POST_CLR = 0.05                      # NA: least gap from a post to the MSR-2's parts
MSR2_SW_CLR = 0.3                         # switch bodies to the sensor board's notches
MSR2_SCD_VENT = (2.0, 3, 3.5, 1.0)        # grille through the radar skin for the SCD4x and the light sensor: slot width,
                                          # count, pitch (along x), slot length = the SCD4x less this inset at each end;
                                          # the middle slot centred on the light sensor (D-65, D-69)
VENT_RADAR_CLR = 1.0                      # grille to the radar module's outline (slots shortened to keep it)
RADAR_WALL = 0.6                          # radar skin over the MSR-2 bay: three 0.2 mm layers (D-51)
LUX_POS = (12.0, 0.0)                     # MEASURE light sensor offset from bay centre

# ---- face plate bays and edge vents (NA and EU) ----
BAY_WALL = 1.6                            # MSR-2 and SHT40 bay frame wall
MSR_BAY_R = 1.0                           # MSR-2 bay frame inside corner radius
SHT_BAY_CLR, SHT_BAY_R = 0.4, 0.5         # SHT40 bay frame: inside clearance round SHT (each side), corner radius
MSR_VENTS = (5, 7.0, 1.5, 3.0, 6.0)       # vents through the top edge: count, pitch, x offset, slot width, depth (y)
SHT_VENTS = (3, 4.0, 2.0, 6.0, 10.0)      # SHT40 vents: count, pitch, slot width, face slot length, edge slot depth

# ---- SHT40 bay ----
SHT = (12.0, 8.0, 4.0)                    # SHT40 bay (the SHT40 DFN on the sensor board below it, D-50)

# ---- MSR-2 board and CN2 (the sensor boards), back cover flex ----
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
FLEX_T = 0.10                             # single-layer polyimide flex (back cover): PCBWay default thickness (D-114)
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
MIN_PRINT_HOLE = 1.5                      # smallest open vertical hole the 0.4 mm nozzle prints reliably (D-61)
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
SB_NOTCH_R = 0.5                          # sensor boards: inside corner radius of milled notches
MSR_NUT = (4.35, 1.5)                     # DATASHEET Wurth WA-SMSI M2 L1.5 9774015243R (SMT spacer): body diameter,
                                          # height; three under the MSR-2's board (D-68)
MSR_NUT_HOLE, MSR_NUT_PAD = 3.0, 5.3      # DATASHEET 9774015243R: unplated hole for its spigot, solder pad diameter

# ---- battery-free remote (D-50): spring pins onto the back cover's pads, both variants ----
# Harwin P70-2200045 SMT spring pin with peg (drawing P70-2200045 iss. 2, 2021-06-04).
PIN_FREE = 8.20                           # DATASHEET free height above the board
PIN_WH = (6.40, 7.10, 7.20)               # DATASHEET working height: minimum, normal, maximum
PIN_TOL = 0.3                             # stack tolerance the design working height must absorb (printed parts, boards)
PIN_FLANGE = (2.00, 1.00)                 # DATASHEET flange diameter, height
PIN_BARREL = (1.54, 6.20)                 # DATASHEET barrel diameter, top above the board
PIN_PLUNGER_D = 0.90                      # DATASHEET plunger
PIN_PEG = (1.00, 2.10)                    # DATASHEET peg diameter, length below the board
PIN_PAD_D, PIN_HOLE_D = 2.20, 1.20        # DATASHEET recommended solder pad, plated through hole for the peg
PIN_RADIAL = 0.2                          # floor holes round barrel and plunger

# ---- replacement back cover (D-35): the BILRESA E2490 without cells, powered from the plate ----
# Remote coordinates: origin = remote centre, x / y as the front view, z = 0 the back's outer face.
AAA_D, AAA_L = 10.5, 44.5                 # DATASHEET IEC 60086-2 LR03 / IEC 61951-2 HR03 maximum diameter, height
BC_CELL_X = 11.2                          # ESTIMATE cell axes at +-x (label drawing bays +-10.95, contacts +-11.4)
BC_CELL_Y0 = 0.0                          # REF compartment centre along y (FCC photos: centred; MEASURE)
BC_CELL_Z = 6.8                           # ESTIMATE cell axis above the back's outer face (wall + clearance + r)
BC_TERM_Y = -1                            # MEASURED terminal end (VBAT / GND contacts) at -y, the LED end (FCC photos;
                                          # checked on a unit, human 2026-10-12)
BC_VBAT_X = -1                            # MEASURED VBAT contact on the -x cell, GND on the +x cell (FCC photos; checked on
                                          # a unit, human 2026-10-12: from the back, wheel end up, + bottom right)
BC_WALL = 1.6                             # MEASURED cover shell thickness (human, 2026-10-09)
BC_SIDE_WALL = BC_WALL - 0.1 - 0.2        # side wall: 0.1 more room inside all round for the remote's housing (D-75),
                                          # 0.2 more for the round-over's middle (D-123)
BC_IN_RUN = B_BACK_RUN + 0.2              # inside round-over across: as much wider as the wall moved out, so it leaves
                                          # the flat back where it did; about 0.1 more room at its middle (D-123)
BC_PRY = (6.0, 1.2)                       # MEASURE screwdriver notch in the rim at the bottom end (-y): width, depth
# snap clips: one at each end (x = 0), free-standing inside the end wall, below the rim; the housing's edge comes
# down into the cover and the clip's hook catches its wall
BC_LATCH_W = (4.0 - 2 * 0.15, 3.1)        # clip width (bottom, top): bottom fills the housing's 4.0 slot less 0.15 each side
                                          # (human 2026-10-11, D-92); top MEASURED 3.1 (human, 2026-10-09)
BC_LATCH_T = 1.2                          # ESTIMATE ear thickness (radial; photos)
BC_LATCH_HOOK = (0.8 + 0.3 + 0.2 + 0.2 + 0.2, 0.7)   # hook at the clip's tip, inwards (catches the housing's wall): top 0.2
                                          # deeper than the original's 0.5, bottom 0.3 (test prints, human 2026-10-09/10),
                                          # bottom 0.3 more (it snapped once, then not again: human 2026-10-11, D-92),
                                          # bottom 0.2 more (human 2026-10-12, D-108), and 0.2 more (D-110), and 0.2
                                          # more (D-112)
BC_LATCH_RIM_GAP = 1.0                    # MEASURED top clip's top below the rim (human, 2026-10-09)
# hook underside: bottom clip flat (a ledge that catches the housing's slot) under a tip face this tall; top clip
# None = 45 deg back to the column. The bottom hook sits in the shell's round-over (D-113)
BC_LATCH_CATCH = (0.3, None)
BC_LATCH_CATCH_Z = 3.22                   # bottom clip's flat underside above the inside floor (human 2026-10-12: 0.15
                                          # higher than D-117's 3.07, D-118)


def shell_in(z):
    """Distance of the shell's inner surface in from the outside rim at height z (round-over, then straight)."""
    zr = z - BC_WALL
    if zr >= B_BACK_RISE:
        return BC_SIDE_WALL
    return BC_SIDE_WALL + BC_IN_RUN * (1 - sqrt(1 - (1 - zr / B_BACK_RISE) ** 2))


# top clip: top from BC_LATCH_RIM_GAP, hook tip 2.7 in from the outside rim (human 2026-10-12, D-107); its tip
# stands BC_LATCH_PROUD clear of the shell's inner surface at the tip face's lower end. The bottom clip's tip stands
# out the same at its catch, wherever the catch sits (D-118). Where reach - hook - thickness < BC_WALL the clip's
# back merges into the end wall.
_top_tip_z = B_SEAM_Z - BC_LATCH_RIM_GAP - 2 * BC_LATCH_HOOK[1]
BC_LATCH_PROUD = 2.7 - shell_in(_top_tip_z)
BC_LATCH_REACH = (shell_in(BC_WALL + BC_LATCH_CATCH_Z) + BC_LATCH_PROUD, 2.7)
# clip tops above the inside floor: bottom from its catch, hook and tip face; top end from BC_LATCH_RIM_GAP
BC_LATCH_TOPS = (BC_LATCH_CATCH_Z + BC_LATCH_HOOK[0] + BC_LATCH_CATCH[0], B_SEAM_Z - BC_WALL - BC_LATCH_RIM_GAP)
BC_LATCH_LEDGE_MIN = 0.4                  # flat underside proud of the shell's inner surface, at least
# small tabs inside both long side walls, two per side either side of mid-length, into slots in the housing's long
# sides (human, 2026-10-11, D-90): the slots' inside / outside spacing along y, tab top below the rim, tab height,
# tab protrusion from the wall
BC_TAB = (18.0, 25.0, 1.0 - 0.1, 0.8, 0.25 + 0.2)   # MEASURED (slots corrected 2026-10-11: 18 / 25, was 23 / 25); top
                                          # 0.1 nearer the rim (human 2026-10-12, D-108); protrusion the human's figure:
                                          # 0.5, halved, then 0.2 more after the first print (D-92)
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
BC_FLEX_SNAP = (3.0, 0.7, 0.4, 0.1)       # snap hooks: width along y, post thickness, lip over the stiffener, post to
                                          # the stiffener's edge
BC_FLEX_SNAP_GAP = 0.15                   # lip underside above the stiffener's top: stiffener thickness tolerance (FR4
                                          # 0.8 +-10 %) and adhesive variation (D-116)
BC_STIFF_ADH = 0.05                       # adhesive between the flex and its FR4 stiffeners (fab: not stated; 0.025-0.05
                                          # is usual, D-116)
BC_FLEX_SNAP_ROOT = 0.4                   # post root: shell left under the relief round each post (the post flexes)
BC_FLEX_SNAP_RELIEF = 0.3                 # relief round each post (sides and behind)
BC_END_LIP = (1.2, 1.0, 0.1)              # lip in front of each block's foot: thickness, height above the ledge, gap
BC_END_SLOT = (0.8, 0.1, 0.5, 0.8, 0.1)   # slot along each block's outer face, the end section slides down it: side wall,
                                          # wall to the section's edge, lip reach over the edge, lip thickness, lip to copper
BC_STEEL_CLIP = (6.0, 0.8, 0.45)          # clips at both ends of the plate's pocket: width, tab thickness, hook over the
                                          # plate's edge; tab 0.8 (was 0.48, D-99): they snapped off, flex was no issue
                                          # (human 2026-10-12, D-111); 2.8 x the bending strength, about 4.8 % strain
BC_STEEL_CLIP_ROOT = 0.4                  # tab root: shell left under the relief round each tab (the tab flexes)
BC_STEEL_CLIP_RELIEF = 0.3                # relief round each tab (sides, behind, and towards the plate)
BC_STEEL_Y = -5.5                         # steel plate centre in the cover (the EU magnet sits under it, clear of the switch cup)
BC_FLEX_Z = 2.0                           # flex underside above the back face (the regulator hangs in a recess under it)
BC_FINGERS = ((13.2, -8.9), (13.2, -13.5))    # +5V, GND pads on the cover flex (x, y), the pad section above the GND
                                          # contact post (D-79): the spring pins come up
                                          # through windows in the back onto them, either side of the posts' line (D-53)
BC_DOME_DY = 0.0                          # DATASHEET contact dome 3.15 +-0.25 from the bend end of the 6.25 body (~centred)
BC_WIN_CLR = 0.3                          # window round the spring pin's barrel (it enters the window)
BC_PAD_D = 2.6                            # gold pad under each spring pin (cover flex): the coverlay opening; the copper
BC_PAD_CU = 3.0                           # under it is BC_PAD_CU, its edge held by the coverlay (flex pad anchoring, D-116)
BC_STRIP = (10.7, 16.5)                   # pad and regulator sections across x: +3V3 lane left of the pads, GND right
BC_RUN = (7.2, 9.8)                       # flex run across x to the terminal end: past the GND contact post's inner face,
                                          # clear of the steel plate's ridge (D-79)
BC_RUN_JOG = 2.0                          # jog from the pad section's inner edge across to the run, at its bottom
BC_JOG = 8.0                              # y length of the regulator section, above the pad section (D-53; 6.6 -> 8.0
                                          # for the 0603 capacitors and the ESD diode, D-116)
BC_PAD_LOW = 0.6                          # flex below the lower pad (the pad section ends just above the terminal bend)
# 3.3 V regulator on the cover flex (D-41), copper down in a recess in the cover: TI TLV75533PDBVR + 1 uF in / out
BC_REG = {"U1": (13.6, -1.95), "C3": (14.8, -5.7), "C4": (13.2, 0.55), "D1": (14.8, -4.4)}   # part centres
                                          # (remote x, y); D1 the ESD diode on +5V beside C3 (D-116)
BC_REG_BODY = (3.0, 3.0, 1.45)            # DATASHEET TLV755P DBV (SOT-23-5): body + leads <= 3.0 x 3.0, 1.45 max high
BC_CAP0603 = (1.6, 0.8, 0.9)              # DATASHEET 0603 capacitor (Samsung CL10A105KO8NNNC): 1.6 x 0.8, 0.9 max high (D-116)
BC_TVS = (1.0, 0.6, 0.43)                 # DATASHEET onsemi ESD9B5.0ST5G SOD-923: 1.0 x 0.6 body, 0.43 max high (D-116)
BC_REG_RECESS = (11.4, 16.4, -6.5, 1.1)  # recess under the regulator section (x0, x1, y0, y1), down to BC_REG_FLOOR
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
BC_LANE_H = 1.55                          # +3V3 lane across the band, above the flex plane: past the bend zone by
                                          # BC_BEND_CLR, 0.3 under the band's top edge (D-116)
BC_BEND_R = 0.6                           # inside radius of the run's 90 deg bend: 6 x FLEX_T (IPC-2223 single-sided,
                                          # bend to install; PCBWay 3-6 x), copper outside (D-116)
BC_BEND_CLR = 0.76                        # stiffener edges, outline width changes and track turns this far from the bend
                                          # zone (30 mil, flex design guides, D-116)
BC_SLIT = (0.9, 0.4)                      # relief slits beside the run (the end section's lower edge stays on the ledge):
                                          # width (full-round end), length past the bend zone (D-116)
BC_BLOCK_T = 4.0                          # contact block depth behind the end section (along the cell axis)
BC_BLOCK_XO = BC_CELL_X + BC_CONTACT_W / 2 + 0.5            # contact blocks' outer faces (|x|)
BC_END_XO = BC_BLOCK_XO - BC_END_SLOT[0] - BC_END_SLOT[1]   # end section's outer edges (|x|), inside the slots

# ================= derived =================
BC_CELL_END_Y = BC_CELL_Y0 + BC_TERM_Y * AAA_L / 2                    # a full-length cell's terminal end
BC_COPPER_Y = BC_CELL_END_Y + BC_TERM_Y * (BC_TERM_SETBACK - FINGER_WH)  # end section copper: contact fingers
                                                                       # at working height on the fixed plate


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
