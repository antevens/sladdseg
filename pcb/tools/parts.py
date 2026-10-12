"""Single source for the wiring board: parts, nets and geometry (front view, mm).

Front view: X right, Y up towards the rocker, origin = board centre; KiCad y = -Y.
F (front) faces the plate, B (back) faces the box. Decisions: docs/DESIGN.md D-24, D-25.
"""
import uuid

NS = uuid.UUID("2b7f0c1e-4c1d-4f55-9b0e-3a8d6c2f1e07")
LIB = "wiring_board"
PROJECT = "wiring_board"
REV = "v0.5"
REV_DATE = "2026-10-12"                     # title blocks and silkscreen


def uid(*names):
    return str(uuid.uuid5(NS, "/".join(names)))


IRM_DS = "https://www.meanwell.com/Upload/PDF/IRM-03/IRM-03-SPEC.PDF"
WAGO_DS = "https://www.wago.com/global/pcb-terminal-blocks-and-pluggable-connectors/pcb-terminal-block/p/2604-1106"
UMT_DS = "https://us.schurter.com/bundles/snceschurter/epim/_ProdPool_/newDS/en/typ_UMT_250.pdf"
CU_DS = "https://www.farnell.com/datasheets/2921094.pdf"
FH12_DS = "https://www.hirose.com/product/en/products/FH12/FH12-6S-0.5SH(55)/"
SMSI_DS = "https://www.we-online.com/catalog/datasheet/9774070243R.pdf"
ROCKER_DS = "Marquardt drawing 1802.2504 rev g, 2003-09-16 (K-drawing 18022504.03)"

# Footprint names in the project library
FP_ROCKER = "Rocker_DPST_Marquardt_1802.2504_E-Switch_RA412C1100"
FP_WAGO = "WAGO_2604-1106_1x06_P5.00mm_Horizontal"
FP_IRM = "Converter_ACDC_MeanWell_IRM-03-xx_THT"
FP_FUSE = "Fuse_Schurter_UMT250"
FP_MOV = "Varistor_TDK_CU4032"
FP_J2 = "Hirose_FH12-6S-0.5SH_1x06-1MP_P0.50mm_Horizontal"
FP_POST = "Wurth_WA-SMSI_M2_SMT_Spacer_L7mm"
FP_ANT = "Ant_Logo_8mm_SilkScreen"
FP_KICAD = "KiCad-Logo2_5mm_SilkScreen"
FP_MH = "MountingHole_3.2mm_M3_NPTH"

# ref: symbol, footprint, value, pin -> net, placement (x, Y, rot_deg, side), bom
PARTS = {
    # turned 90 degrees: poles are columns (line left at X -5.1, neutral right at X 5.1),
    # in-pins on the body's centre line (Y 19.5), switched pins above (Y 26.5), away from J1
    "S1": dict(label="E-Switch RA412C1100\nor Marquardt 1802.2504", sym="SW_DPST_Marquardt", fp=FP_ROCKER, value="1802.2504",
               nets={"1": "L_IN", "1a": "L_SW", "2": "N_IN", "2a": "N_SW"},
               pcb=(0.0, 19.5, 0, "F"), mfr="Marquardt", mpn="1802.2504",
               desc="Rocker switch DPST, ENEC 12(4) A 250 V~, UL/CSA 15 A 125-250 VAC, PCB pins, "
                    "emergency off (line and neutral)",
               ds=ROCKER_DS),
    "J1": dict(sym="Screw_Terminal_01x06", fp=FP_WAGO, value="2604-1106",
               # pads 1..6 run right to left in front view (block is on the back):
               # seen from the back, left to right: PE, N_SW, N_IN, L_SW, L_IN, PE
               nets={"1": "PE", "2": "N_SW", "3": "N_IN", "4": "L_SW", "5": "L_IN", "6": "PE"},
               pcb=(3.0, 8.1, 0, "B"), mfr="WAGO", mpn="2604-1106",
               desc="PCB terminal block, push-in, lever, 6-pole, 5 mm pitch, 4 mm2 / 12 AWG, entry parallel to PCB",
               ds=WAGO_DS),
    "PS1": dict(sym="IRM-03-5", fp=FP_IRM, value="IRM-03-5",
                nets={"1": "L_F", "3": "N_SW", "16": "+5V", "14": "GND", "5": "NC5"},
                pcb=None, mfr="Mean Well", mpn="IRM-03-5",
                desc="AC-DC module 85-305 VAC in, 5 V 600 mA, 37x24x15 mm", ds=IRM_DS),
    "F1": dict(label="Schurter UMT250 T1A", sym="Fuse", fp=FP_FUSE, value="T1A 250V", nets={"1": "L_SW", "2": "L_F"},
               pcb=(-14.6, -23.0, 90, "F"), mfr="Schurter", mpn="3403.0166.11",
               desc="SMD fuse UMT 250, time-lag 1 A 250 VAC. Rating is a designer's choice: human review",
               ds=UMT_DS),
    "RV1": dict(label="TDK CU4032K275G2", sym="Varistor", fp=FP_MOV, value="CU4032K275G2", nets={"1": "L_F", "2": "N_SW"},
                pcb=(-5.5, -22.0, 90, "F"), mfr="TDK", mpn="B72660M0271K093",
                desc="SMD varistor SIOV-CU4032K275G2K1, 275 VAC", ds=CU_DS),
    # spacer posts for the battery-free remote's spring pins (D-50): the riser board screws onto them
    "P1": dict(label="Wurth WA-SMSI M2 L7", sym="Conn_01x01", fp=FP_POST, value="+5V post", nets={"1": "+5V"},
               pcb=(9.85, -16.5, 0, "F"), mfr="Wurth Elektronik", mpn="9774070243R",
               desc="SMT steel spacer, internal thread M2, 7 mm, tin: +5V to the riser board (D-50, D-59)", ds=SMSI_DS),
    "P2": dict(label="Wurth WA-SMSI M2 L7", sym="Conn_01x01", fp=FP_POST, value="GND post", nets={"1": "GND"},
               pcb=(16.65, -16.5, 0, "F"), mfr="Wurth Elektronik", mpn="9774070243R",
               desc="SMT steel spacer, internal thread M2, 7 mm, tin: GND to the riser board (D-50, D-59)", ds=SMSI_DS),
    # turned 90: the FFC leaves to the right, then up past the posts. Pinout mirror-symmetric (GND 1, 3, 4, 6;
    # +5V 2, 5), so an FFC with contacts on either side, flipped end to end, keeps the polarity
    "J2": dict(label="Hirose FH12-6S", sym="Conn_01x06", fp=FP_J2, value="5V out (FFC to the ring board)",
               nets={"1": "GND", "2": "+5V", "3": "GND", "4": "GND", "5": "+5V", "6": "GND"},
               pcb=(13.5, -24.8, 90, "F"), mfr="Hirose", mpn="FH12-6S-0.5SH(55)",
               desc="FPC connector 0.5 mm, 6 contacts, slide lock: 5 V to the ring board FFC (D-50)", ds=FH12_DS),
}

# Silkscreen logos (board-only footprints) and the project URL, as on the author's other
# boards. ANT_LOGO_H = height the ant logo is scaled to (source: pcb/art/Ant_Logo_SilkScreen.kicad_mod).
ANT_LOGO_H = 8.0
# ref: footprint, (x, Y), side, rotation (deg): ant upper left, KiCad logo upper right (turned to
# fit between the rocker and the right PE ring)
LOGOS = {"LOGO1": (FP_ANT, (-15.5, 27.0), "F", 0), "LOGO2": (FP_KICAD, (15.6, 27.0), "F", 90)}
URL = "github.com/antevens/smart-wallplate"
URL_POS = (0.0, 14.6, "B")

# Mounting holes for the insert's nylon standoffs (D-57), front view; mirrored in cad params
# (MOUNT_HOLES, checked by `make check`). All unplated, with no copper under the standoffs or the screw heads:
# a copper keep-out round each hole (MOUNT_KO) on both layers, and the PE ring detours round MH1 and MH3
# on the inside (PE_DETOURS), so earth continuity never depends on copper they press on, or
# on vias. Top right is lowered so the insert boss clears the 5 V pass-through.
MOUNT_D = 3.2                               # M3 clearance (ISO 273 fine)
STANDOFF_HEX_D = 5.0 / 0.866                # Keystone 25503 5.0 mm hex across its corners (front)
SCREW_HEAD_D = 5.6                          # Keystone 29341 M3 pan head, ISO 1580 maximum (back)
MOUNT_KO = max(STANDOFF_HEX_D, SCREW_HEAD_D) / 2 + 0.5   # copper keep-out radius round each hole
MOUNT = {"MH1": (-21.0, 33.5), "MH2": (-21.0, -33.5), "MH3": (21.0, 24.77), "MH4": (21.0, -33.5)}

# WA-SMSI M2 land pattern (DATASHEET 9774070243R, the same as the L6 9774060243R): spigot hole, solder pad, stencil ring
POST_HOLE = 3.0                             # non-plated through hole for the spigot (Ø2.8, 1.4 long: ends inside the 1.6 board)
POST_PAD = 5.3                              # solder pad outer diameter (inner = the hole)
POST_PASTE = (3.1, 5.2, 0.6)                # stencil ring inner / outer diameter, web width
SMSI_BODY_D = 4.35                          # spacer body diameter (Fab outline)

# PS1 on the back: target pad positions (front view). AC end left, DC end right.
PS1_PINS = {"1": (-15.24, -12.5), "3": (-10.16, -12.5), "5": (15.24, -12.5),
            "16": (10.16, -30.28), "14": (15.24, -30.28)}

MAINS_GAP = 3.0                             # L-N, in to switched, mains to PE: IEC 60664-1 OVC III clearance 3.0 on
                                            # high-CTI FR4 (creepage ~1.6), hard constraint 3, D-102 (EU: params_eu)
NETCLASS = {"Mains_L": ["L_IN", "L_SW", "L_F"], "Mains_N": ["N_IN", "N_SW"], "PE": ["PE"],
            "SELV": ["+5V", "GND"]}

BOARD = dict(w=47.0, h=72.0, t=1.6, r=1.5, slot=(3.0, 5.0, -10.9))

# PE ring round the AC part (both layers): outer outline and hole, front view
RING_OUTER = [(-22.5, -35.0), (2.5, -35.0), (2.5, -10.9), (22.5, -10.9), (22.5, 35.0), (-22.5, 35.0)]
RING_INNER = [(-20.0, -32.5), (0.0, -32.5), (0.0, -8.9), (20.0, -8.9), (20.0, 32.5), (-20.0, 32.5)]
SELV_ZONE = [(7.0, -33.5), (19.5, -33.5), (19.5, -13.0), (7.0, -13.0)]

# Load-path pours (net, layer, outline); the zone filler applies the spacing rules
POURS = [
    # in-pins (both J1 rows) straight up on the front
    ("L_IN", "F.Cu", [(-9.0, -2.0), (-1.5, -2.0), (-1.5, 21.5), (-9.0, 21.5)]),
    ("N_IN", "F.Cu", [(2.0, -2.0), (8.5, -2.0), (8.5, 21.5), (2.0, 21.5)]),
    # switched neutral: right of the N_IN pin, over the top to S1.2a (back)
    ("N_SW", "B.Cu", [(8.5, -2.0), (14.0, -2.0), (14.0, 29.0), (1.0, 29.0), (1.0, 24.5), (8.5, 24.5)]),
    # switched line (back): up from J1.4 into the band between J1's upper pin row and the rocker's in pins, left past
    # J1.5 / S1.1, up the left side to S1.1a; also down from J1.4 under J1 and up the left edge (in parallel), feeding F1
    ("L_SW", "B.Cu", [(2.0, 15.5), (2.0, -6.0), (-3.0, -6.0), (-3.0, -30.0), (-19.0, -30.0),
                      (-19.0, 29.0), (-1.0, 29.0), (-1.0, 15.5)]),
]

# PE arms: J1.6 / J1.1 (pin pairs at x -9.5 / 15.5) to the PE ring, flush with the outer edges of
# the pin pair's pads; they end square at the pins' centre line, behind the pads, so the pads
# still set the MAINS_GAP keep-away from the neighbouring L / N terminals.
PE_PIN_X = (-9.5, 15.5)
PE_ROWS = (-0.1, 8.1)                       # J1's two solder-pin rows (front view y): first row (entry side) above
WAGO_PAD = (2.2, 2.2)                       # J1 pad size (x, y), round, used by the footprint
WAGO_ROW_PITCH = 8.2                        # DATASHEET (WAGO 3D model 2604-1106): second row behind the first
WAGO_BODY = (5.0, 11.1, 8.1)                # DATASHEET (WAGO 3D model): entry face before / closed back behind the
                                            # first row at the board; the levers overhang the entry side up top
PE_ARM_W = abs(PE_ROWS[1] - PE_ROWS[0]) + WAGO_PAD[1]
_arm_y = ((PE_ROWS[0] + PE_ROWS[1]) - PE_ARM_W) / 2, ((PE_ROWS[0] + PE_ROWS[1]) + PE_ARM_W) / 2
_ring_l, _ring_r = RING_INNER[0][0] - 0.5, RING_INNER[3][0] + 0.5    # 0.5 mm into the ring

# PE ring detours round MH1 and MH3 on the inside: annular sectors from MOUNT_KO out to
# MOUNT_KO + PE_DETOUR_W over the inner side (degrees from the hole centre, counter-clockwise),
# overlapping the ring at both ends. MH2 (bottom-left corner, next to F1) interrupts the ring:
# PE runs J1.6 -> left edge -> MH1 -> top -> MH3 -> J1.1, and the ring's lower part stays joined
# to both arms. gen_pcb.py checks that this path holds on F.Cu without vias or hole copper.
PE_DETOUR_W = 2.0
PE_DETOURS = {"MH1": (-100.0, 10.0), "MH3": (80.0, 280.0)}
PE_ARMS = [("F.Cu", [(_ring_l, _arm_y[0]), (PE_PIN_X[0], _arm_y[0]), (PE_PIN_X[0], _arm_y[1]), (_ring_l, _arm_y[1])])]
PE_ARMS += [(lay, [(PE_PIN_X[1], _arm_y[0]), (_ring_r, _arm_y[0]), (_ring_r, _arm_y[1]), (PE_PIN_X[1], _arm_y[1])])
            for lay in ("F.Cu", "B.Cu")]

# Pour priorities: pours closer together than their spacing rule compete for copper, and equal
# priorities make the result depend on fill order. Line pours win over neutral.
POUR_PRIO = {"L_IN": 3, "N_IN": 2, "L_SW": 3, "N_SW": 2}

# Tracks: net -> [(layer, width, [(x, Y), ...])]
VIAS = {"L_SW": [(-16.0, -29.0), (-13.0, -29.0)],  # (x, y): 1.0 / 0.5 mm; or (x, y, diameter, drill)
        "+5V": [(10.4, -24.05, 0.6, 0.3), (10.4, -25.55, 0.6, 0.3)]}   # J2.5 / J2.2 to B.Cu

TRACKS = {
    # fused line: F1.2 (top) -> PS1.1, and F1.2 -> RV1.1 (bottom) straight across, clear of F1.1 (switched line)
    "L_F": [("F.Cu", 0.8, [(-14.6, -18.75), (-15.6, -17.0), (-15.6, -13.5), (-15.24, -12.5)]),
            ("F.Cu", 0.8, [(-14.6, -18.75), (-5.5, -26.65)])],
    # switched neutral: RV1.2 (top) -> PS1.3
    "N_SW": [("F.Cu", 0.8, [(-5.5, -17.35), (-5.5, -14.0), (-10.16, -12.5)]),
             # J1.2 -> under J1 -> RV1 track
             ("F.Cu", 0.5, [(10.5, -0.1), (10.5, -5.0), (-5.5, -5.0), (-5.5, -14.0)])],
    # PSU feed: F1.1 -> vias below F1 to the L_SW pour on the back (3.0 from the fused line and the PE ring)
    "L_SW": [("F.Cu", 0.8, [(-14.6, -27.25), (-14.6, -29.0)]), ("F.Cu", 0.8, [(-16.0, -29.0), (-13.0, -29.0)])],
    # PS1.16 -> P1 up the left (F, ends on the pad ring); J2.2 / J2.5 -> vias at their tails -> B.Cu -> PS1.16
    "+5V": [("F.Cu", 0.8, [(10.16, -30.28), (8.5, -28.62), (8.5, -19.5), (9.4, -18.75)]),
            ("F.Cu", 0.3, [(11.1, -24.05), (10.4, -24.05)]), ("F.Cu", 0.3, [(11.1, -25.55), (10.4, -25.55)]),
            ("B.Cu", 0.4, [(10.4, -24.05), (10.4, -29.3), (10.16, -30.28)])],
    # PS1.14 -> P2 up the right (F); J2.1 / 3 / 4 / 6 -> a bar left of the +5V vias -> the 5 V side pour
    "GND": [("F.Cu", 0.8, [(15.24, -30.28), (17.0, -30.28), (18.6, -28.68), (18.6, -20.0), (17.45, -18.65)]),
            ("F.Cu", 0.3, [(11.1, -23.55), (10.6, -23.05), (9.7, -23.05)]),
            ("F.Cu", 0.3, [(11.1, -26.05), (10.6, -26.55), (9.7, -26.55)]),
            ("F.Cu", 0.3, [(11.1, -24.55), (10.6, -24.8), (9.7, -24.8)]), ("F.Cu", 0.3, [(11.1, -25.05), (10.6, -24.8)]),
            ("F.Cu", 0.3, [(9.7, -26.55), (9.7, -23.05)])],
}
