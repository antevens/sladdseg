"""Generate the low-voltage boards' KiCad projects in pcb/sensor/kicad/ (D-50): ring board, mic carrier, riser
board, back cover flex (D-35) and the EU cap board (D-56, D-70).

Libraries, project and rules, schematics and boards, all from sensor_parts.py (which takes its
geometry from cad/build123d/params.py). Run with the Python that ships pcbnew.
"""
import copy
from math import cos, radians, sin
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(1, str(HERE.parents[1] / "tools"))          # pcb/tools: sexpr + stock library lookup
import pcbnew as P
import sensor_parts as sp
import eu_capboard_parts as eu
from sexpr import loads, dumps, find, first, Sym, S
import gen_libs as gl
import kigen
from kigen import Board, build_schematic

PRJ = HERE.parent / "kicad"
LIB = sp.LIB
POWER = ("+5V", "+3V3", "GND")

SYMBOLS = [("Connector_Generic", "Conn_02x15_Odd_Even"), ("Connector_Generic", "Conn_01x01"),
           ("Connector_Generic", "Conn_01x06"), ("Mechanical", "MountingHole"),
           ("Sensor_Humidity", "SHT4x"), ("Device", "C"), ("Device", "R"), ("Connector", "TestPoint"),
           ("Regulator_Linear", "TLV75533PDBV"),
           ("power", "+5V"), ("power", "+3V3"), ("power", "GND"), ("power", "PWR_FLAG")]
STOCK_FP = {sp.FP_SHT: "Sensor_Humidity", sp.FP_C: "Capacitor_SMD", sp.FP_R: "Resistor_SMD",
            sp.FP_SOT: "Package_TO_SOT_SMD", sp.FP_C1206: "Capacitor_SMD", sp.FP_FH12: "Connector_FFC-FPC",
            eu.FP_HOLE: "MountingHole"}
# DMM-4026-B-I2S-R pins (datasheet rev A) from the stock SPH0645LM4H symbol's pins, plus CONFIG
MIC_PINS = {"1": ("5", "WS"), "2": ("1", "LR"), "3": ("4", "GND"), "4": ("6", "SCK"), "5": ("3", "VDD"),
            "6": ("7", "SD")}


# ============================== libraries ==============================
def pad(num, x, y, sx, sy, layers=("F.Cu", "F.Mask"), shape="rect"):
    return S("pad", num, Sym("smd"), Sym(shape), S("at", x, y), S("size", sx, sy), S("layers", *layers))


def rect_pts(x, y, w, h):
    """Closed rectangle w x h centred on (x, y), counter-clockwise from the bottom right corner."""
    return [(x + w / 2, y - h / 2), (x + w / 2, y + h / 2), (x - w / 2, y + h / 2), (x - w / 2, y - h / 2)]


def courtyard(w, h):
    """Courtyard rectangle w x h around the footprint origin."""
    return gl.rect(-w / 2, -h / 2, w / 2, h / 2, "F.CrtYd", 0.05)


def fp_b2b():
    """Placeholder for the CN2 mating plug: 2 x 15 at 0.4 mm. Odd pins on the row at local -y
    (flat +Y). NOT a vendor footprint: replace once the CN2 part is confirmed."""
    cols = sp.CN2_PINS // 2
    items = []
    for n in range(1, sp.CN2_PINS + 1):
        k = (n - 1) // 2
        x = -(cols - 1) / 2 * sp.CN2_PITCH + k * sp.CN2_PITCH
        y = -sp.CN2_ROW if n % 2 else sp.CN2_ROW
        items.append(pad(str(n), round(x, 3), y, 0.23, 0.8, ("F.Cu", "F.Paste", "F.Mask")))
    items += [gl.rect(-3.8, -1.5, 3.8, 1.5, "F.Fab", 0.1), courtyard(8.2, 3.6),
              S("fp_text", Sym("user"), "PLACEHOLDER: CN2 mate unconfirmed", S("at", 0, 2.6, 0),
                S("layer", "F.Fab"), S("effects", S("font", S("size", 0.6, 0.6), S("thickness", 0.1))))]
    return gl._fp(sp.FP_B2B, "PLACEHOLDER board-to-board plug, 0.4 mm, 2 x 15: mates the MSR-2's CN2 "
                  "(part, footprint and contact map unconfirmed, docs/DESIGN.md D-27)", "placeholder b2b",
                  "smd", items)


def fp_finger():
    """Harwin S7081-42R, recommended pad layout 6.65 x 3.60 (drawing S7081-42R iss. 7); bend end at -x (Fab mark)."""
    bx = -sp.FINGER[1] / 2 + 0.6
    items = [pad("1", 0, 0, sp.FINGER_PAD[1], sp.FINGER_PAD[0], ("F.Cu", "F.Paste", "F.Mask")),
             gl.rect(-sp.FINGER[1] / 2, -sp.FINGER[0] / 2, sp.FINGER[1] / 2, sp.FINGER[0] / 2, "F.Fab", 0.1),
             gl.line(bx, -sp.FINGER[0] / 2, bx, sp.FINGER[0] / 2, "F.Fab", 0.1),
             courtyard(sp.FINGER_PAD[1] + 0.5, sp.FINGER_PAD[0] + 0.5), gl.model3d(sp.FP_FINGER)]
    return gl._fp(sp.FP_FINGER, f"Harwin S7081-42R SMT spring finger, gold, 4 A, bend end at -x, {sp.HARWIN_DS}",
                  "spring finger contact", "smd", items)


def fp_mic():
    """PUI Audio DMM-4026-B-I2S-R land pattern (datasheet rev A): origin = body centre, +y towards the
    port. GND ring pad (soldered all round: it seals the port) and the port hole through the carrier."""
    port_y = sp.MIC[1] / 2 - sp.MIC_PORT_IN             # port centre from the body's port end
    rows = [port_y - sp.MIC_PORT_ROW - i * sp.MIC_ROW for i in range(3)]       # nearest the port first
    items = []
    for col, pins in ((-sp.MIC_COL, ("3", "2", "1")), (sp.MIC_COL, ("5", "6", "7"))):
        for y, n in zip(rows, pins):
            items.append(pad(n, round(col, 3), round(y, 3), *sp.MIC_PAD, ("F.Cu", "F.Paste", "F.Mask")))
    r_mid = sum(sp.MIC_RING) / 4                         # ring centre line radius
    ring_w = (sp.MIC_RING[1] - sp.MIC_RING[0]) / 2
    items.append(S("pad", "4", Sym("smd"), Sym("custom"), S("at", r_mid, port_y), S("size", ring_w, ring_w),
                   S("layers", "F.Cu", "F.Paste", "F.Mask"),
                   S("options", S("clearance", Sym("outline")), S("anchor", Sym("circle"))),
                   S("primitives", S("gr_circle", S("center", -r_mid, 0), S("end", 0, 0), S("width", ring_w),
                                     S("fill", Sym("no"))))))
    items.append(S("pad", "", Sym("np_thru_hole"), Sym("circle"), S("at", 0, port_y),
                   S("size", sp.MIC_FLEX_HOLE_D, sp.MIC_FLEX_HOLE_D), S("drill", sp.MIC_FLEX_HOLE_D),
                   S("layers", "*.Mask")))
    w, h = sp.MIC[0], sp.MIC[1]
    items += [gl.rect(-w / 2, -h / 2, w / 2, h / 2, "F.Fab", 0.1), courtyard(w + 0.5, h + 0.5), gl.model3d(sp.FP_MIC)]
    return gl._fp(sp.FP_MIC, f"PUI Audio DMM-4026-B-I2S-R I2S MEMS microphone, bottom port, {sp.MIC_DS}",
                  "microphone MEMS I2S bottom port", "smd", items)


def mic_symbol():
    """DMM-4026-B-I2S symbol: the stock SPH0645LM4H with the DMM-4026 pin numbers and a CONFIG pin."""
    new = "DMM-4026-B-I2S"
    s = gl.rename_symbol(gl.stock_symbol("Sensor_Audio", "SPH0645LM4H"), new)
    host, lr = None, None
    for sub in find(s, "symbol"):
        for x in sub:
            if isinstance(x, list) and x and x[0] == "pin":
                num, name = first(x, "number"), first(x, "name")
                num[1], name[1] = MIC_PINS[num[1]]
                if num[1] == "1":
                    host, lr = sub, x
    cfg = copy.deepcopy(lr)
    first(cfg, "number")[1], first(cfg, "name")[1] = "2", "CONFIG"
    first(cfg, "at")[2] = -float(first(lr, "at")[2])
    host.append(cfg)
    for p in find(s, "property"):
        p[2] = {"Value": new, "Footprint": f"{LIB}:{sp.FP_MIC}", "Datasheet": sp.MIC_DS,
                "Description": "PUI Audio I2S MEMS microphone, bottom port, LGA-7",
                "ki_fp_filters": "PUI*DMM*4026*", "ki_keywords": "microphone MEMS I2S"}.get(p[1], p[2])
    return s


def fp_round_pad(name, d, descr):
    """Bare gold (ENIG) round pad, no paste."""
    return gl._fp(name, descr, "pad target contact", "smd", [pad("1", 0, 0, d, d, shape="circle"),
                                                             courtyard(d + 0.25, d + 0.25)])


def _carrier_pads():
    """(number, x, y) of the six castellations: left column 1-3 top to bottom, right column 4-6 top to bottom."""
    out = []
    for col, nums in ((-1, ("1", "2", "3")), (1, ("4", "5", "6"))):
        for k, n in enumerate(nums):
            out.append((n, col * sp.CARRIER_W / 2, (1 - k) * sp.CARRIER_PITCH))
    return out


def fp_carrier():
    """Mic carrier castellations: plated half-holes centred on the side edges, pads CARRIER_CAST[0] inwards (the
    outer half is milled off with the edge). KiCad y runs down: room y -> -y."""
    px, py, drill = sp.CARRIER_CAST
    items = []
    for n, x, y in _carrier_pads():
        items.append(S("pad", n, Sym("thru_hole"), Sym("roundrect"), S("at", x, -y),
                       S("size", px * 2, py), S("drill", drill), S("layers", "*.Cu", "*.Mask"),
                       S("roundrect_rratio", 0.15), S("property", Sym("pad_prop_castellated"))))
    w, h = sp.CARRIER_W, sp.CARRIER_H
    items += [gl.rect(-w / 2, -h / 2, w / 2, h / 2, "F.Fab", 0.1), courtyard(w + 2 * px + 0.5, h + 0.5)]
    return gl._fp(sp.FP_CARRIER, "Mic carrier castellations, 2 x 3, half-holes on the board edge", "castellated",
                  "through_hole", items)


def fp_carrier_land():
    """Ring board land for the mic carrier: six pads centred on the carrier's side edges (y up = room)."""
    lx, ly = sp.CARRIER_LAND
    items = [pad(n, x, -y, lx, ly, ("F.Cu", "F.Paste", "F.Mask")) for n, x, y in _carrier_pads()]
    w, h = sp.CARRIER_W, sp.CARRIER_H
    items += [gl.rect(-w / 2, -h / 2, w / 2, h / 2, "F.Fab", 0.1), courtyard(w + lx + 0.5, h + 0.5)]
    return gl._fp(sp.FP_CARRIER_LAND, "Land for the mic carrier's castellations (the window under the mic is on the "
                  "board's Edge.Cuts)", "castellated land", "smd", items)


def fp_post_pad():
    """Plated M2 hole with a ring pad under the screw head, on both sides (the standoff's face on the back)."""
    d, drill = sp.POST_PAD
    items = [S("pad", "1", Sym("thru_hole"), Sym("circle"), S("at", 0, 0), S("size", d, d), S("drill", drill),
               S("layers", "*.Cu", "*.Mask")), gl.circ("F.CrtYd", d / 2 + 0.1, 0.05)]
    return gl._fp(sp.FP_POST_PAD, f"M2 screw onto a spacer post: plated {drill} mm hole, {d} mm pad (pan head 4.0)",
                  "M2 post pad", "through_hole", items)


def build_libs():
    syms = [Sym("kicad_symbol_lib"), S("version", Sym("20241209")), S("generator", "gen_sensor"),
            S("generator_version", "9.0")]
    for lib, name in SYMBOLS:
        syms.append(gl.stock_symbol(lib, name))
    syms.append(mic_symbol())
    (PRJ / f"{LIB}.kicad_sym").write_text(dumps(syms) + "\n")
    d = PRJ / f"{LIB}.pretty"
    d.mkdir(parents=True, exist_ok=True)
    for f in d.glob("*.kicad_mod"):
        f.unlink()
    for name, lib in STOCK_FP.items():
        fp = gl.localize_models(loads((gl.FP_DIR / f"{lib}.pretty" / f"{name}.kicad_mod").read_text()), PRJ)
        (d / f"{name}.kicad_mod").write_text(dumps(fp) + "\n")
    for fp in (fp_b2b(), fp_finger(), fp_mic(), fp_carrier(), fp_carrier_land(), fp_post_pad(),
               gl.fp_smsi(sp.FP_NUT, 1.5, sp.RING_NUT_HOLE, sp.RING_NUT_PAD, sp.NUT_DS, silk=False),
               gl.fp_p70(sp.FP_PIN, sp.PIN_PAD_D, sp.PIN_HOLE_D, sp.PIN_FLANGE[0], sp.PIN_DS),
               fp_round_pad(sp.FP_PIN_PAD, sp.BC_PAD_D, "Gold pad under a spring pin (back cover flex)"),
               fp_round_pad(eu.FP_PAD, eu.E.CB_PAD_D, "Gold pad under a spring pin (EU cap board)")):
        (d / f"{fp[1]}.kicad_mod").write_text(dumps(fp) + "\n")
    gl.write_lib_tables(PRJ, LIB, "Low-voltage board")


# ============================== project + rules ==============================
RULES = {
    sp.RING: """(version 1)
# Ring board (low voltage only): FR4 1.6 mm. Copper keep-out from the box opening: rule areas on the board.
(rule "Board edge clearance"
    (constraint edge_clearance (min 0.25mm)))
""",
    sp.CARRIER: """(version 1)
# Mic carrier (low voltage only): FR4 0.8 mm, castellated edges.
(rule "Board edge clearance"
    (constraint edge_clearance (min 0.2mm))
    (condition "!A.isPlated()"))
""",
    sp.RISER_B: """(version 1)
# Riser board (low voltage only): FR4 0.8 mm.
(rule "Board edge clearance"
    (constraint edge_clearance (min 0.3mm)))
""",
    sp.COVER: """(version 1)
# Back cover flex (low voltage only): single-layer polyimide flex.
(rule "Flex edge clearance"
    (constraint edge_clearance (min 0.2mm)))
""",
    eu.CAPBOARD: """(version 1)
# EU cap board (low voltage only): FR4 1.6 mm in the cap's carrier.
(rule "Board edge clearance"
    (constraint edge_clearance (min 0.3mm)))
""",
}


def build_project(name):
    pro = {"board": {"design_settings": {"rule_severities": {"lib_footprint_issues": "warning",
                                                             "lib_footprint_mismatch": "warning"}}},
           "meta": {"filename": f"{name}.kicad_pro", "version": 3},
           "schematic": {"meta": {"version": 1}}, "sheets": [["", "Root"]]}
    (PRJ / f"{name}.kicad_pro").write_text(json.dumps(pro, indent=2) + "\n")
    (PRJ / f"{name}.kicad_dru").write_text(RULES[name])


# ============================== schematics + boards (pcb/tools/kigen.py) ==============================
CTX = kigen.Lib(PRJ, LIB, sp.uid, POWER)


def build_eu_capboard():
    """EU cap board (D-70), as the NA ring board round CN2: I2S from CN2's upper row up, right and down to the mic
    carrier's land, +3V3 from the lower row down under the land to its right column; SDA, SCL, +3V3 on the back down
    the outer left edge (outside the snap windows and the screws) to the SHT45; +5V from the pin pad on the back up the
    outer right edge and across to CN2; GND pours on both layers."""
    bd = Board(CTX, eu.CAPBOARD, 2, eu.E.CB_T, 0.12, 0.12, via_min=(0.45, 0.2))    # fine vias round CN2
    bd.outline(eu.CB_OUTER, eu.CB_OUTER_R)
    bd.polyline(eu.CB_POCKET)
    bd.outline(rect_pts(*eu.MIC_WIN), 0.4)
    for win in eu.CB_SNAP_WINDOWS:
        bd.outline(win, 0.5)
    for ref, p in eu.CAPBOARD_PARTS.items():
        bd.place(ref, p, False)
    F, B = P.F_Cu, P.B_Cu
    for lay in (F, B):
        bd.zone("GND", lay, eu.CB_OUTER, min_w=0.25, fillet_r=0.5, name="GND")
    via = lambda net, v: bd.via(net, *v, d=0.45, drill=0.2)
    pin = {n: bd.pad_xy("J2", n) for n in sp.CN2_MAP}
    land = {n: bd.pad_xy("J3", n) for n in sp.CARRIER_NETS}
    cy = eu.E.MSR_Y
    up, lo = pin["19"][1] + 0.4, pin["24"][1] - 0.4          # upper row pads' top ends, lower row pads' bottom ends
    # I2S on the front: up from the upper row, right (leftmost pad highest), down to the land's left column
    for n, dy, xd, dn in (("23", 2.95, 21.4, "1"), ("25", 2.5, 21.0, "2"), ("27", 2.1, 20.6, "3")):
        x0, dst = pin[n][0], land[dn]
        bd.track(sp.CN2_MAP[n], 0.12, [(x0, up), (x0, cy + dy), (xd, cy + dy), (xd, dst[1]), dst])
    r1, r1g = bd.pad_xy("R1", "1"), bd.pad_xy("R1", "2")
    bd.track("I2S_SD", 0.15, [r1, (21.4, r1[1])])           # SD pull-down off the SD lane
    vr = (r1g[0] + 0.9, r1g[1])
    bd.track("GND", 0.2, [r1g, vr])
    via("GND", vr)
    # +3V3 on the front: lower row down under the land to its right column and C3; a via to the back lanes
    p3 = pin["28"]
    y3 = land["3"][1] - 1.0
    xl6 = land["6"][0] - 1.2
    bd.track("+3V3", 0.2, [(p3[0], lo), (p3[0], y3), (xl6, y3), (xl6, land["6"][1]), land["6"]])
    c3, c3g = bd.pad_xy("C3", "1"), bd.pad_xy("C3", "2")
    bd.track("+3V3", 0.2, [land["6"], (c3[0], land["6"][1]), c3])
    vc3 = (c3g[0] + 0.9, c3g[1])
    bd.track("GND", 0.2, [c3g, vc3])
    via("GND", vc3)
    v33 = (p3[0], lo - 1.6)
    via("+3V3", v33)
    # SDA, SCL: vias under the lower row
    vsda, vscl = (pin["26"][0] - 0.1, lo - 1.0), (pin["24"][0] - 0.5, lo - 1.0)
    bd.track("SDA", 0.12, [(pin["26"][0], lo), (vsda[0], lo - 0.3), vsda])
    bd.track("SCL", 0.12, [(pin["24"][0], lo), (pin["24"][0], lo - 0.45), (vscl[0], lo - 0.65), vscl])
    via("SDA", vsda)
    via("SCL", vscl)
    # back: down, left above the pocket, down the outer left edge, right below the pocket to the SHT45
    u = {n: bd.pad_xy("U1", n) for n in ("1", "2", "3", "4")}
    c2p, c2g = bd.pad_xy("C2", "1"), bd.pad_xy("C2", "2")
    xl = {"SCL": -34.8, "SDA": -34.3, "+3V3": -33.8}        # the lane leaving highest runs outermost
    yt = {"SCL": 44.6, "SDA": 44.0, "+3V3": 43.4}
    yb = {"SCL": -41.2, "SDA": -40.6, "+3V3": -40.0}
    xv = {"SCL": -2.0, "SDA": -1.3, "+3V3": 4.2}            # vias to the front at the SHT45
    for net, v in (("SCL", vscl), ("SDA", vsda), ("+3V3", v33)):
        bd.track(net, 0.2, [v, (v[0], yt[net]), (xl[net], yt[net]), (xl[net], yb[net]), (xv[net], yb[net])], B)
        bd.via(net, xv[net], yb[net])
    bd.track("SDA", 0.2, [(xv["SDA"], yb["SDA"]), (xv["SDA"], u["1"][1]), u["1"]])
    bd.track("SCL", 0.2, [(xv["SCL"], yb["SCL"]), (xv["SCL"], u["2"][1]), u["2"]])
    bd.track("+3V3", 0.2, [(xv["+3V3"], yb["+3V3"]), (xv["+3V3"], c2p[1]), c2p])
    bd.track("+3V3", 0.2, [c2p, u["3"]])
    bd.track("GND", 0.2, [u["4"], c2g])
    vs = (c2g[0], c2g[1] + 1.1)
    bd.track("GND", 0.25, [c2g, vs])
    # +5V: CN2's upper row up-left to a via; on the back across and down the outer right edge to the pin pad and C1
    tp5, tpg = bd.pad_xy("TP2", "1"), bd.pad_xy("TP1", "1")
    c5, cg = bd.pad_xy("C1", "1"), bd.pad_xy("C1", "2")
    xr = 34.3
    v5 = (pin["19"][0] - 0.6, cy + 2.0)
    bd.track("+5V", 0.25, [(pin["19"][0], up), (pin["19"][0], v5[1]), v5])
    via("+5V", v5)
    bd.track("+5V", 0.5, [v5, (v5[0], cy + 6.0), (xr, cy + 6.0), (xr, tp5[1]), tp5], B)
    vc5 = (c5[0] + 1.6, c5[1])
    bd.track("+5V", 0.4, [c5, vc5])
    bd.via("+5V", *vc5)
    bd.track("+5V", 0.4, [vc5, (xr, vc5[1])], B)
    # GND: pin pad, C1, CN2's GND contacts to the pours; the land's GND pins together
    vg = (tpg[0] + 2.2, tpg[1])
    bd.track("GND", 0.5, [tpg, vg], B)
    bd.via("GND", *vg)
    vcg = (cg[0] - 1.6, cg[1])
    bd.track("GND", 0.4, [cg, vcg])
    bd.via("GND", *vcg)
    g21 = (pin["21"][0], cy)
    bd.track("GND", 0.15, [(pin["21"][0], pin["21"][1] - 0.4), g21])
    via("GND", g21)
    g30 = (pin["30"][0] + 0.3, lo - 1.0)
    bd.track("GND", 0.15, [(pin["30"][0], lo), g30])
    via("GND", g30)
    bd.track("GND", 0.3, [land["4"], land["5"]])
    via("GND", (land["4"][0] + 0.45, land["4"][1] + 0.6))
    for v in (vs, (-20.0, -46.0), (20.0, -40.0), (-20.0, 52.0), (20.0, 60.0), (-28.0, 40.0)):
        bd.via("GND", *v)
    bd.text(f"EU CAP BOARD {sp.REV} (D-70)", -20.0, -46.0, P.F_SilkS, 1.0)
    if not eu.CN2_CONFIRMED:
        bd.text("J2 FOOTPRINT AND PIN MAP ARE PLACEHOLDERS - DO NOT FABRICATE", 0.0, 30.0, P.Cmts_User, 1.0)
    bd.save()


def build_cover():
    bd = Board(CTX, sp.COVER, 1, sp.FLEX_T, 0.15, sp.COVER_TRACK)
    bd.outline(sp.COVER_OUTLINE, 0.5)
    for ref, p in sp.COVER_PARTS.items():
        bd.place(ref, p, False)
    w = sp.COVER_TRACK
    f1, f2, vbat, gnd = (bd.pad_xy(r, "1") for r in ("J1", "J2", "J3", "J4"))
    x_in, x_out = sp.COVER_LANES
    y_band = sp.COVER_BEND_Y - sp.BC_LANE_H
    # end fingers: long axis across the bend line, bend end away from it (up in the cover)
    for ref in ("J3", "J4"):
        f = bd.fps[ref]
        for rot in (0, 90, 180, 270):
            f.SetOrientationDegrees(rot)
            g = [g for g in f.GraphicalItems() if g.GetLayer() == P.F_Fab and g.GetShape() == P.SHAPE_T_SEGMENT][0]
            (sx, sy), (ex, ey) = kigen.mm(g.GetStart()), kigen.mm(g.GetEnd())
            mark = ((sx + ex) / 2, (sy + ey) / 2)
            c = bd.pad_xy(ref, "1")
            if abs(mark[0] - c[0]) < 0.6 and mark[1] < c[1] - 1.0:
                break
        else:
            raise RuntimeError(f"no orientation of {ref} puts its bend end away from the bend line")
    # regulator above the pads (D-53), unrotated: IN / GND / EN down its outer column, OUT / NC on the inner one
    p_in, p_gnd, p_en, p_out = (bd.pad_xy("U1", n) for n in ("1", "2", "3", "5"))
    xm = bd.fps["U1"].GetPosition()
    xm = kigen.mm(xm)[0]                                 # under the body, between the two columns
    c3_gnd, c3_5v = bd.pad_xy("C3", "1"), bd.pad_xy("C3", "2")
    c4_gnd, c4_3v3 = bd.pad_xy("C4", "1"), bd.pad_xy("C4", "2")
    xg = sp.COVER_GND_X
    y_up = sp._yt + 0.1                                  # just inside the regulator section
    # +5V: straight up from the upper pad, under U1 to IN, EN on the way, C3 beside it
    bd.track("+5V", w, [f1, (f1[0], y_up - 0.4), (xm, y_up), (xm, p_in[1]), p_in])
    bd.track("+5V", w, [(xm, p_en[1]), p_en])
    bd.track("+5V", w, [c3_5v, (xm, c3_5v[1])])
    # GND: lower pad up the outer edge to U1's GND pin, C3 and C4; and down into the run to J4
    bd.track("GND", w, [f2, (xg, f2[1]), (xg, c4_gnd[1]), c4_gnd])
    bd.track("GND", w, [p_gnd, (xg, p_gnd[1])])
    bd.track("GND", w, [c3_gnd, (xg, c3_gnd[1])])
    bd.track("GND", w, [f2, (f2[0], sp._yb + 0.5), (x_out, sp._yb + 0.5), (x_out, gnd[1] + 2.0), gnd])
    # +3V3: OUT up to C4, down the pad section's inner edge past both pads, across the jog above the GND lane (D-79),
    # down the run's inner lane, across the band, into VBAT
    x_e = sp._xs1 - 0.65
    y_j = sp._yb + 1.3
    bd.track("+3V3", w, [p_out, (p_out[0], c4_3v3[1] - 0.7), c4_3v3, (x_e, c4_3v3[1]), (x_e, y_j), (x_in, y_j),
                         (x_in, y_band), (vbat[0], y_band), vbat])
    bd.shape(P.SHAPE_T_SEGMENT, P.Cmts_User, 0.1, (sp._xr0, sp.COVER_BEND_Y), (sp._xr1, sp.COVER_BEND_Y))
    bd.text("BEND 90 deg, copper outside", 0.0, sp.COVER_BEND_Y + 1.2, P.Cmts_User, 0.6)
    for (a0, b0), (a1, b1) in sp.COVER_STIFF:
        bd.polyline([(a0, b0), (a1, b0), (a1, b1), (a0, b1)], P.User_1, 0.1)
        bd.text(f"STIFFENER FR4 {sp.BC_END_T} mm, back side (cut to the outline)", (a0 + a1) / 2, b0 - 1.0, P.User_1, 0.6)
    for (a0, b0), (a1, b1) in sp.COVER_PAD_STIFF:
        bd.polyline([(a0, b0), (a1, b0), (a1, b1), (a0, b1)], P.User_1, 0.1)
    bd.text(f"STIFFENER FR4 {sp.BC_PAD_STIFF_T} mm, back side, flush with the long edges (snap hooks)",
            sp._xs0 - 4.0, sp._yb + 2.0, P.User_1, 0.6, 90)
    if not sp.COVER_CONFIRMED:
        bd.text("POSITIONS REF / MEASURE - DO NOT FABRICATE", 0.0, 2.0, P.Cmts_User, 0.9)
    bd.save()


def rule_area(bd, pts, layer, name):
    """Keep-out rule area on one copper layer: no tracks, vias, pads or pours."""
    z = P.ZONE(bd.b)
    z.SetLayer(layer)
    z.SetIsRuleArea(True)
    for f in (z.SetDoNotAllowCopperPour, z.SetDoNotAllowTracks, z.SetDoNotAllowVias, z.SetDoNotAllowPads):
        f(True)
    z.SetDoNotAllowFootprints(False)
    z.SetZoneName(name)
    ol = z.Outline()
    ol.NewOutline()
    for x, y in pts:
        ol.Append(kigen.V(x, y))
    bd.b.Add(z)


def place_ring():
    bd = Board(CTX, sp.RING, 2, 1.6, 0.12, 0.15)
    bd.outline(sp.RING_OUTER, sp.RING_OUTER_R)
    bd.polyline(sp.RING_WINDOW)
    bd.outline(rect_pts(*sp.MIC_WIN_RECT), 0.4)
    for ref, p in sp.RING_PARTS.items():
        bd.place(ref, p, False)
    return bd


def build_ring():
    """Ring board: CN2 fan-out on the front, I2S to the mic carrier's left column, +3V3 under the carrier to its right
    column; SDA, SCL, +3V3 on the back across the top band to the right rail, down the rail on the front round the
    box's corner keep-out and along the bottom band to the SHT45; +5V from J1 on the back to CN2; GND pours."""
    bd = place_ring()
    F, B = P.F_Cu, P.B_Cu
    rule_area(bd, sp.KEEP_FRONT, F, "front copper keep-out: box opening + 6.4 mm")
    rule_area(bd, sp.KEEP_BACK, B, "back copper keep-out: box opening + 8.0 mm")
    for lay in (F, B):
        bd.zone("GND", lay, sp.RING_OUTER, min_w=0.25, fillet_r=0.5, name="GND")
    pin = {net: bd.pad_xy("J2", n) for n, net in sp.CN2_MAP.items() if net != "GND"}
    top, bot = pin["I2S_WS"][1] + 0.4, pin["SCL"][1] - 0.4   # upper / lower row pad ends
    land = {n: bd.pad_xy("J3", n) for n in sp.CARRIER_NETS}
    # I2S: up from the upper row, right, up the jog to the carrier's left column
    for net, y, xj, n in (("I2S_SD", 61.4, 22.6, "1"), ("I2S_SCK", 61.0, 23.2, "2"), ("I2S_WS", 60.6, 23.8, "3")):
        x0 = pin[net][0]
        bd.track(net, 0.12, [(x0, top), (x0, y), (xj, y), (xj, land[n][1]), land[n]])
    r1 = bd.pad_xy("R1", "1")
    bd.track("I2S_SD", 0.12, [r1, (r1[0], 61.4)])
    # +5V: CN2 up-left to a via; J1's +5V pins to vias; C1 to a via; joined on the back
    p5 = pin["+5V"]
    v5 = (12.9, 61.4)
    bd.track("+5V", 0.2, [(p5[0], top), (p5[0], 60.6), v5])
    j1 = {n: bd.pad_xy("J1", n) for n in sp.FH12_NETS}
    vj = [(j1["2"][0], 51.3), (j1["5"][0], 51.3)]
    for n, v in zip(("2", "5"), vj):
        bd.track("+5V", 0.3, [(j1[n][0], j1[n][1] + 0.6), v])
    c1 = bd.pad_xy("C1", "1")
    vc = (c1[0], c1[1] + 1.25)
    bd.track("+5V", 0.4, [c1, vc])
    for v in vj + [vc, v5]:
        bd.via("+5V", *v)
    bd.track("+5V", 0.4, [vj[1], vj[0], (vj[0][0], 58.5), (v5[0], 58.5), v5], B)
    bd.track("+5V", 0.4, [vc, (vc[0], 58.5)], B)
    # J1 GND: 1 / 6 out and up, 3 / 4 up between the +5V vias, a bar above them
    yb = 52.0
    for n, dx in (("1", -0.4), ("6", 0.4)):
        bd.track("GND", 0.25, [(j1[n][0], j1[n][1] + 0.6), (j1[n][0] + dx, 51.3), (j1[n][0] + dx, yb)])
    xm = (j1["3"][0] + j1["4"][0]) / 2
    for n in ("3", "4"):
        bd.track("GND", 0.25, [(j1[n][0], j1[n][1] + 0.6), (xm, 51.2)])
    bd.track("GND", 0.25, [(xm, 51.2), (xm, yb)])
    bd.track("GND", 0.3, [(j1["1"][0] - 0.4, yb), (j1["6"][0] + 0.4, yb)])
    # CN2 GND contacts: vias to both pours
    g21, g30 = bd.pad_xy("J2", "21"), bd.pad_xy("J2", "30")
    vg1, vg2 = (g21[0], 62.1), (g30[0] + 0.55, bot - 0.5)
    bd.track("GND", 0.15, [(g21[0], top), vg1])
    bd.track("GND", 0.15, [(g30[0], bot), (g30[0], bot - 0.25), vg2])
    for v in (vg1, vg2):
        bd.via("GND", *v)
    # +3V3: lower row down, right, via to the back; on up to C3 and under the carrier to its right column
    p3 = pin["+3V3"]
    v3 = (24.5, 55.5)
    c3, c3g = bd.pad_xy("C3", "1"), bd.pad_xy("C3", "2")
    yw = 59.0                                               # below the mic window
    bd.track("+3V3", 0.2, [(p3[0], bot), (p3[0], v3[1]), v3, (v3[0], yw), (30.9, yw), (30.9, c3[1]), c3, land["6"]])
    vc3 = (31.6, 58.0)
    bd.track("GND", 0.25, [c3g, vc3])
    bd.via("GND", *vc3)
    bd.track("GND", 0.3, [land["4"], land["5"]])
    # SDA / SCL: lower row down to vias
    sda, scl = pin["SDA"], pin["SCL"]
    vsda, vscl = (sda[0], 54.7), (13.6, 54.5)
    bd.track("SDA", 0.15, [(sda[0], bot), vsda])
    bd.track("SCL", 0.15, [(scl[0], bot), (scl[0], 55.6), (vscl[0], 55.0), vscl])
    for net, v in (("SDA", vsda), ("SCL", vscl), ("+3V3", v3)):
        bd.via(net, *v)
    # back: three lanes across the top band (under J1) to the rail vias
    lanes = (("SCL", vscl, 48.4, (31.3, 48.4)), ("SDA", vsda, 49.4, (31.3, 49.4)), ("+3V3", v3, 50.4, (31.3, 50.4)))
    w = sp.RAIL_W
    for net, v, y, vr in lanes:
        bd.track(net, w, [v, (v[0], y), vr], B)
        bd.via(net, *vr)
    # front: from the rail vias onto the rail, down it, round the corner keep-out, along the bottom band
    cx, cy = sp.BOX_W / 2, -sp.BOX_H / 2                     # the box opening's bottom right corner
    r0 = sp.RAIL_X[0] - cx
    rail_top = sp.BOX_H / 2 + sp.K_FRONT - 0.1               # where the front keep-out begins
    starts = [(vr, vr[1] - (sp.RAIL_X[i] - vr[0])) for i, (_, _, _, vr) in enumerate(lanes)]   # 45 deg onto the rail
    u1 = {n: bd.pad_xy("U1", n) for n in ("1", "2", "3", "4")}
    c2p, c2g = bd.pad_xy("C2", "1"), bd.pad_xy("C2", "2")
    for i, ((net, _, _, _), (via, y1)) in enumerate(zip(lanes, starts)):
        x = sp.RAIL_X[i]
        r = r0 + i * sp.RAIL_PITCH
        corner = [(cx + r * cos(radians(a)), cy + r * sin(radians(a))) for a in range(0, -91, -5)]
        yl = cy - r                                         # lane along the bottom band, then down past the boss notch
        x0 = 9.0 + 0.137 * i
        yl2 = yl - 1.9
        pts = [via, (x, y1), (x, rail_top)] + corner + [(x0, yl), (x0 - 1.9, yl2)]
        yl = yl2
        if net == "+3V3":                                   # first down (lowest lane): C2, then VDD
            pts += [(3.4, yl), (3.4, c2p[1]), c2p]
            bd.track(net, w, pts)
            bd.track(net, w, [c2p, u1["3"]])
        elif net == "SDA":
            pts += [(-1.3, yl), (-1.3, u1["1"][1]), u1["1"]]   # into pin 1 from outside the sensor's keep-out
            bd.track(net, w, pts)
        else:                                               # SCL: round the left of the SHT45 into pin 2
            pts += [(-2.0, yl), (-2.0, u1["2"][1]), u1["2"]]
            bd.track(net, w, pts)
    bd.track("GND", 0.2, [u1["4"], c2g])
    vs = (c2g[0], c2g[1] + 1.1)                              # the SHT45's GND patch to the back pour
    bd.track("GND", 0.25, [c2g, vs])
    for v in (vs, (-20.0, -50.0), (20.0, -50.0), (-20.0, 52.0), (-8.0, 68.5), (8.0, 68.5)):   # stitching, beside the switch notches
        bd.via("GND", *v)
    bd.text(f"RING BOARD {sp.REV} (D-50)", 0.0, -53.6, P.F_SilkS, 1.0)
    if not sp.CN2_CONFIRMED:
        bd.text("J2 FOOTPRINT AND PIN MAP ARE PLACEHOLDERS - DO NOT FABRICATE", 0.0, 66.5, P.Cmts_User, 1.0)
    bd.save()


def build_carrier():
    """Mic carrier: mic on the back, port hole at the origin; I2S to the left castellations, power to the right."""
    bd = Board(CTX, sp.CARRIER, 2, sp.CARRIER_T, 0.12, 0.15)
    rect = rect_pts(0.0, 0.0, sp.CARRIER_W, sp.CARRIER_H)
    bd.outline(rect, 0.3)
    for ref, p in sp.CARRIER_PARTS.items():
        bd.place(ref, p, False)
    bd.zone("GND", P.F_Cu, rect, min_w=0.2, fillet_r=0.2, name="GND")
    B = P.B_Cu
    mk = {n: bd.pad_xy("MK1", n) for n in ("1", "2", "3", "4", "5", "6", "7")}
    cs = {n: bd.pad_xy("J1", n) for n in sp.CARRIER_NETS}
    e = sp.CARRIER_W / 2 - sp.CARRIER_CAST[0]               # castellation pads' inner edge
    # I2S: WS (nearest the port) to the bottom castellation, SCK the middle, SD the top
    bd.track("I2S_WS", 0.15, [mk["5"], (-2.0, mk["5"][1]), (-2.0, cs["3"][1]), cs["3"]], B)
    bd.track("I2S_SCK", 0.15, [mk["6"], (-2.35, mk["6"][1]), (-2.35, cs["2"][1]), cs["2"]], B)
    bd.track("I2S_SD", 0.15, [mk["7"], (-(e + 0.3), mk["7"][1]), (-(e + 0.3), cs["1"][1]), cs["1"]], B)
    # VDD down the right to the bottom castellation; CONFIG and LR to the top one (GND)
    bd.track("+3V3", 0.2, [mk["3"], (2.0, mk["3"][1]), (2.0, cs["6"][1]), cs["6"]], B)
    bd.track("GND", 0.2, [mk["2"], (e + 0.4, mk["2"][1])], B)
    bd.track("GND", 0.2, [mk["1"], (2.0, mk["1"][1]), (2.0, mk["2"][1])], B)
    # port ring to the front pour through a via under the body's port end
    vg = (0.0, -1.6)
    bd.track("GND", 0.2, [(0.0, -sum(sp.MIC_RING) / 4), vg], B)
    bd.via("GND", *vg)
    bd.text(f"MK1 PORT {sp.MIC_FLEX_HOLE_D} mm: gasket seat, keep flat", 0.0, sp.CARRIER_H / 2 + 0.8, P.Cmts_User, 0.5)
    bd.save()


def build_riser():
    """Riser (D-53, D-60, D-79): the posts level at its lower corners, the pins above and between them; +5V post to
    the upper pin, GND post to the lower."""
    bd = Board(CTX, sp.RISER_B, 2, sp.RISER[2], 0.2, 0.5)
    bd.outline(rect_pts(*sp.RISER_RECT), 1.0)
    for ref, p in sp.RISER_PARTS.items():
        bd.place(ref, p, False)
    p5, pg = bd.pad_xy("P1", "1"), bd.pad_xy("P2", "1")
    j5, jg = bd.pad_xy("J1", "1"), bd.pad_xy("J2", "1")
    bd.track("+5V", 1.0, [p5, (j5[0] - 1.8, j5[1]), j5])
    bd.track("GND", 1.0, [pg, (jg[0] + 1.8, jg[1]), jg])
    bd.text(f"RISER {sp.REV}", sp.RISER_RECT[0], (j5[1] + jg[1]) / 2, P.B_SilkS, 0.8)          # between the pins' pads
    bd.save()


def main():
    PRJ.mkdir(parents=True, exist_ok=True)
    build_libs()
    for name in (sp.RING, sp.CARRIER, sp.RISER_B, sp.COVER, eu.CAPBOARD):
        build_project(name)
    status = "CN2 mate and contact map UNCONFIRMED (placeholder) - do not fabricate" if not sp.CN2_CONFIRMED \
        else "CN2 mate confirmed"
    gen = "Generated by pcb/sensor/tools/gen_sensor.py - edit sensor_parts.py"

    def schematic(name, parts, flags, title, comments, notes):
        build_schematic(CTX, name, parts, flags, f"Smart wall plate - {title}", sp.REV, sp.REV_DATE, comments, notes)
    schematic(sp.RING, sp.RING_PARTS, ("+5V", "+3V3", "GND"), "ring board", [status, gen],
              "Ring board (docs/DESIGN.md D-50): FR4 1.6 mm round the insert's plug, against the wall.\n"
              "J1: 5 V from the wiring board's J2 over a 6-way 0.5 mm FFC (pinout mirror-symmetric).\n"
              "J2 mates the MSR-2's rear connector CN2 (MSR-2 powered through its 5V pin).\n"
              "U1: SHT45, I2C on the MSR-2 bus (SDA = IO1, SCL = IO0).\n"
              "J3: land for the mic carrier (I2S microphone, D-29): SCK = IO4, WS = IO6, SD = IO7.\n"
              "H1-H3: SMT spacers under the MSR-2's board. Copper keeps 8 mm from the box opening.")
    schematic(sp.CARRIER, sp.CARRIER_PARTS, ("+3V3", "GND"), "mic carrier",
              [gen], "Mic carrier (docs/DESIGN.md D-50): the bottom-port I2S microphone on the back, port up\n"
              "through the carrier; castellated edges soldered flat on the ring board's land (J3 there).\n"
              "LR and CONFIG to GND: left channel.")
    schematic(sp.RISER_B, sp.RISER_PARTS, ("+5V", "GND"), "riser board",
              [gen], "Riser board (docs/DESIGN.md D-50): on the two spacer posts from the wiring board's 5 V area\n"
              "(M2 screws, P1 +5V, P2 GND); J1 / J2 Harwin P70-2200045 spring pins onto the back cover's pads.")
    schematic(sp.COVER, sp.COVER_PARTS, ("+5V", "GND"), "back cover flex", [gen],
              "Replacement back cover flex (docs/DESIGN.md D-35, D-50): J1 / J2 pads under the plate's spring\n"
              "pins (+5V, GND), U1 3.3 V regulator, J3 / J4 spring fingers on the BILRESA's VBAT plate / GND leaf\n"
              "spring. One bend, single layer.")
    schematic(eu.CAPBOARD, eu.CAPBOARD_PARTS, ("+5V", "+3V3", "GND"), "EU cap board",
              [status, "Generated by pcb/sensor/tools/gen_sensor.py - edit eu_capboard_parts.py"],
              "EU cap board (docs/DESIGN.md D-56, D-70): FR4 1.6 mm in the cap's printed carrier.\n"
              "TP1 / TP2 on the underside: pads under the 5 V board's sensor spring pins (GND, +5 V).\n"
              "J2 mates the MSR-2's rear connector CN2 (MSR-2 powered through its 5V pin); H5-H7 SMT spacers.\n"
              "J3: land for the mic carrier (I2S microphone, D-29) over a window; U1: SHT45 on the MSR-2's I2C.\n"
              "H1-H4: holes for the M2 screws into the carrier.")
    # board files: build in memory, save (KiCad 9 python cannot refill/reload safely in one board)
    build_ring()
    build_carrier()
    build_riser()
    build_cover()
    build_eu_capboard()


if __name__ == "__main__":
    main()
