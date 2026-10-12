"""Generate the low-voltage boards' KiCad projects in pcb/sensor/kicad/ (D-50): ring board, riser board, back cover
flex (D-35) and the EU cap board (D-56, D-70).

Libraries, project and rules, schematics and boards, all from sensor_parts.py (which takes its
geometry from cad/build123d/params.py). Run with the Python that ships pcbnew.
"""
import copy
from math import cos, hypot, radians, sin
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

SYMBOLS = [("Connector_Generic", "Conn_02x12_Odd_Even"), ("Connector_Generic", "Conn_01x01"),
           ("Connector_Generic", "Conn_01x06"), ("Mechanical", "MountingHole"),
           ("Sensor_Humidity", "SHT4x"), ("Device", "C"), ("Device", "R"), ("Connector", "TestPoint"),
           ("Regulator_Linear", "TLV75533PDBV"), ("Device", "D_TVS"),
           ("power", "+5V"), ("power", "+3V3"), ("power", "GND"), ("power", "PWR_FLAG")]
STOCK_FP = {sp.FP_SHT: "Sensor_Humidity", sp.FP_C: "Capacitor_SMD", sp.FP_C0603: "Capacitor_SMD", sp.FP_R: "Resistor_SMD",
            sp.FP_SOT: "Package_TO_SOT_SMD", sp.FP_C1206: "Capacitor_SMD", sp.FP_FH12: "Connector_FFC-FPC",
            eu.FP_HOLE: "MountingHole"}
# SPK0641HT4H-1 pins (datasheet rev A) from the stock SPH0641LU4H-1 symbol's pins; GND 6-8 stacked on GND 5
MIC_PINS = {"1": "1", "4": "2", "2": "3", "5": "4", "3": "5"}


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
    """Molex 55909-2474 (2 x 12, 0.4 mm) mating the MSR-2's CN2, land pattern from Molex SD-55909-003 rev J (sheet 2):
    signal pads 0.22 x 0.9, rows 1.73 apart (inner edges), four fitting nail pads 0.5 x 0.85, 0.8 beyond the end pads,
    0.63 apart. Odd pins on the row at local -y (flat +Y); the drawing numbers no pins: pin 1 with the contact map."""
    cols = sp.CN2_PINS // 2
    items = []
    for n in range(1, sp.CN2_PINS + 1):
        k = (n - 1) // 2
        x = -(cols - 1) / 2 * sp.CN2_PITCH + k * sp.CN2_PITCH
        y = -sp.CN2_ROW if n % 2 else sp.CN2_ROW
        items.append(pad(str(n), round(x, 3), round(y, 3), *sp.CN2_PAD, ("F.Cu", "F.Paste", "F.Mask")))
    nx, ny = sp.CN2_NAIL_AT
    for sx in (-1, 1):
        for sy in (-1, 1):
            items.append(pad("", round(sx * nx, 3), round(sy * ny, 3), *sp.CN2_NAIL, ("F.Cu", "F.Paste", "F.Mask")))
    bl, bw, _ = sp.CN2_BODY
    cx = max(bl / 2, nx + sp.CN2_NAIL[0] / 2) + 0.25
    cy = max(bw / 2, sp.CN2_ROW + sp.CN2_PAD[1] / 2) + 0.25
    items += [gl.rect(-bl / 2, -bw / 2, bl / 2, bw / 2, "F.Fab", 0.1), courtyard(2 * cx, 2 * cy)]
    return gl._fp(sp.FP_B2B, "Molex 55909-2474 SlimStack plug, 0.4 mm, 2 x 12, 1.5 mm mated on 51338: mates the MSR-2's "
                  "CN2; land pattern Molex SD-55909-003 rev J (contact map: docs/DESIGN.md D-82, D-89)",
                  "molex slimstack 55909", "smd", items)


def fp_finger():
    """Harwin S7081-42R, recommended pad layout 6.65 x 3.60 (drawing S7081-42R iss. 7); bend end at -x (Fab mark)."""
    bx = -sp.FINGER[1] / 2 + 0.6
    items = [pad("1", 0, 0, sp.FINGER_PAD[1], sp.FINGER_PAD[0], ("F.Cu", "F.Paste", "F.Mask")),
             gl.rect(-sp.FINGER[1] / 2, -sp.FINGER[0] / 2, sp.FINGER[1] / 2, sp.FINGER[0] / 2, "F.Fab", 0.1),
             gl.line(bx, -sp.FINGER[0] / 2, bx, sp.FINGER[0] / 2, "F.Fab", 0.1),
             courtyard(sp.FINGER_PAD[1] + 0.5, sp.FINGER_PAD[0] + 0.5), gl.model3d(sp.FP_FINGER)]
    return gl._fp(sp.FP_FINGER, f"Harwin S7081-42R SMT spring finger, gold, 4 A, bend end at -x, {sp.HARWIN_DS}",
                  "spring finger contact", "smd", items)


def fp_tvs():
    """TI TPD1E10B06 SOD-523 (DYA0002A): the datasheet's example land pattern (SLLSEB1G), pads 0.4 x 0.67, 1.48 across."""
    (w, h), span = sp.TVS_PAD, sp.TVS_SPAN
    x = (span - w) / 2
    items = [pad("1", -x, 0, w, h, ("F.Cu", "F.Paste", "F.Mask")), pad("2", x, 0, w, h, ("F.Cu", "F.Paste", "F.Mask")),
             gl.rect(-0.5, -0.3, 0.5, 0.3, "F.Fab", 0.05), courtyard(span + 0.3, h + 0.3)]
    return gl._fp(sp.FP_TVS, f"TI SOD-523 (DYA0002A), example land pattern, {sp.TVS_DS}", "SOD-523 TVS ESD",
                  "smd allow_soldermask_bridges", items)


def fp_mic():
    """Knowles SPK0641HT4H-1 example land pattern (datasheet rev A p. 6): origin = body centre, +y (room) towards the
    port end; signal pads inside a four-pad GND ring. KiCad y runs down: room y -> -y."""
    w, h, sx, sy = sp.MIC_SIG
    items = [pad(n, sx * a, -sy * b, w, h, ("F.Cu", "F.Paste", "F.Mask")) for n, (a, b) in sp.MIC_SIG_PINS.items()]
    t, side, end = sp.MIC_GND
    gx, gy = sp.MIC_GND_AT
    for n, (a, b) in sp.MIC_GND_PINS.items():
        size = (t, side) if a else (end, t)
        items.append(pad(n, gx * a, -gy * b, *size, ("F.Cu", "F.Paste", "F.Mask")))
    bw, bl = sp.MIC[0], sp.MIC[1]
    port = -(bl / 2 - sp.MIC_PORT_IN)
    items += [gl.rect(-bw / 2, -bl / 2, bw / 2, bl / 2, "F.Fab", 0.1),
              S("fp_circle", S("center", 0, port), S("end", 0.25, port), S("stroke", S("width", 0.1),
                                                                         S("type", Sym("solid"))),
                S("fill", Sym("no")), S("layer", "F.Fab")),
              courtyard(bw + 0.5, bl + 0.5), gl.model3d(sp.FP_MIC)]
    return gl._fp(sp.FP_MIC, f"Knowles SPK0641HT4H-1 PDM MEMS microphone, top port (circle on Fab), {sp.MIC_DS}",
                  "microphone MEMS PDM top port", "smd", items)


def mic_symbol():
    """SPK0641HT4H-1 symbol: the stock SPH0641LU4H-1 with the SPK0641 pin numbers, GND 6-8 stacked on GND 5."""
    new = "SPK0641HT4H-1"
    s = gl.rename_symbol(gl.stock_symbol("Sensor_Audio", "SPH0641LU4H-1"), new)
    for sub in find(s, "symbol"):
        for x in list(sub):
            if isinstance(x, list) and x and x[0] == "pin":
                num = first(x, "number")
                num[1] = MIC_PINS[num[1]]
                if num[1] == "5":
                    for n in ("6", "7", "8"):
                        g = copy.deepcopy(x)
                        g[1] = Sym("passive")
                        first(g, "number")[1] = n
                        sub.append(g)
    for p in find(s, "property"):
        p[2] = {"Value": new, "Footprint": f"{LIB}:{sp.FP_MIC}", "Datasheet": sp.MIC_DS,
                "Description": "Knowles PDM MEMS microphone, top port, LGA-8",
                "ki_fp_filters": "Knowles*SPK0641*", "ki_keywords": "microphone MEMS PDM"}.get(p[1], p[2])
    return s


def _ball_xy(ball):
    """ADAU7002 ball centre in the footprint (KiCad y down): rows A-D downwards, columns 1-2 rightwards."""
    r, c = "ABCD".index(ball[0]), int(ball[1]) - 1
    return round((c - 0.5) * sp.ADAU_PITCH, 3), round((r - 1.5) * sp.ADAU_PITCH, 3)


def fp_adau():
    """Analog Devices ADAU7002 WLCSP CB-8-6 (datasheet rev C): 2 x 4 balls, 0.4 mm pitch, round NSMD lands."""
    d = sp.ADAU_PAD
    items = [pad(b, *_ball_xy(b), d, d, ("F.Cu", "F.Paste", "F.Mask"), shape="circle") for b in sp.ADAU_BALLS]
    w, h = sp.ADAU[0], sp.ADAU[1]
    items += [gl.rect(-w / 2, -h / 2, w / 2, h / 2, "F.Fab", 0.05),
              gl.line(-w / 2, -h / 2 + 0.25, -w / 2 + 0.25, -h / 2, "F.Fab", 0.05),     # ball A1 corner
              courtyard(w + 0.5, h + 0.5), gl.model3d(sp.FP_ADAU)]
    return gl._fp(sp.FP_ADAU, f"Analog Devices ADAU7002 WLCSP-8 0.76 x 1.56, 0.4 mm pitch, {d} mm NSMD lands, "
                  f"{sp.ADAU_DS}", "WLCSP BGA ADAU7002", "smd", items)


def adau_symbol():
    """ADAU7002: PDM in on the left, I2S out on the right, IOVDD up, GND down."""
    name = "ADAU7002"
    eff = S("effects", S("font", S("size", 1.27, 1.27)))
    hid = S("effects", S("font", S("size", 1.27, 1.27)), S("hide", Sym("yes")))

    def pin(kind, num, nm, x, y, ang):
        return S("pin", Sym(kind), Sym("line"), S("at", x, y, ang), S("length", 2.54), S("name", nm, eff),
                 S("number", num, eff))
    pins = [pin("input", "A1", "PDM_DAT", -10.16, 2.54, 0), pin("output", "A2", "PDM_CLK", -10.16, 0, 0),
            pin("input", "D2", "CONFIG", -10.16, -2.54, 0), pin("output", "B1", "SDATA", 10.16, 2.54, 180),
            pin("input", "B2", "BCLK", 10.16, 0, 180), pin("input", "C2", "LRCLK", 10.16, -2.54, 180),
            pin("power_in", "D1", "IOVDD", 0, 7.62, 270), pin("power_in", "C1", "GND", 0, -7.62, 90)]
    props = [("Reference", "U", 0, 6.35, eff), ("Value", name, 0, -6.35, eff),
             ("Footprint", f"{LIB}:{sp.FP_ADAU}", 0, 0, hid), ("Datasheet", sp.ADAU_DS, 0, 0, hid),
             ("Description", "Stereo PDM to I2S / TDM converter, 1.62-3.6 V, WLCSP-8", 0, 0, hid),
             ("ki_keywords", "PDM I2S decimator microphone", 0, 0, hid)]
    return S("symbol", name, S("exclude_from_sim", Sym("no")), S("in_bom", Sym("yes")), S("on_board", Sym("yes")),
             *[S("property", k, v, S("at", x, y, 0), e) for k, v, x, y, e in props],
             S("symbol", f"{name}_0_1", S("rectangle", S("start", -7.62, 5.08), S("end", 7.62, -5.08),
                                          S("stroke", S("width", 0.254), S("type", Sym("default"))),
                                          S("fill", S("type", Sym("background"))))),
             S("symbol", f"{name}_1_1", *pins))


def fp_round_pad(name, d, descr, cu=None):
    """Bare gold (ENIG) round pad, no paste; cu: larger copper under a d opening (mask-defined, the edge held)."""
    if cu is None:
        return gl._fp(name, descr, "pad target contact", "smd", [pad("1", 0, 0, d, d, shape="circle"),
                                                                 courtyard(d + 0.25, d + 0.25)])
    p = pad("1", 0, 0, cu, cu, shape="circle")
    p.append(S("solder_mask_margin", round((d - cu) / 2, 3)))
    return gl._fp(name, f"{descr}; {cu} mm copper, {d} mm opening", "pad target contact", "smd",
                  [p, courtyard(cu + 0.25, cu + 0.25)])


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
    syms += [mic_symbol(), adau_symbol()]
    (PRJ / f"{LIB}.kicad_sym").write_text(dumps(syms) + "\n")
    d = PRJ / f"{LIB}.pretty"
    d.mkdir(parents=True, exist_ok=True)
    for f in d.glob("*.kicad_mod"):
        f.unlink()
    for name, lib in STOCK_FP.items():
        fp = gl.localize_models(loads((gl.FP_DIR / f"{lib}.pretty" / f"{name}.kicad_mod").read_text()), PRJ)
        if name == sp.FP_SOT:                                # cover flex: one coverlay opening over each pin row
            next(n for n in fp if isinstance(n, list) and n and n[0] == Sym("attr")).append(Sym("allow_soldermask_bridges"))
        (d / f"{name}.kicad_mod").write_text(dumps(fp) + "\n")
    for fp in (fp_b2b(), fp_finger(), fp_mic(), fp_adau(), fp_post_pad(), fp_tvs(),
               gl.fp_smsi(sp.FP_NUT, 1.5, sp.RING_NUT_HOLE, sp.RING_NUT_PAD, sp.NUT_DS, silk=False),
               gl.fp_p70(sp.FP_PIN, sp.PIN_PAD_D, sp.PIN_HOLE_D, sp.PIN_FLANGE[0], sp.PIN_DS),
               fp_round_pad(sp.FP_PIN_PAD, sp.BC_PAD_D, "Gold pad under a spring pin (back cover flex)", sp.BC_PAD_CU),
               fp_round_pad(eu.FP_PAD, eu.E.CB_PAD_D, "Gold pad under a spring pin (EU cap board)"),
               gl.fp_ant_logo(), gl.fp_kicad_logo()):
        (d / f"{fp[1]}.kicad_mod").write_text(dumps(fp) + "\n")
    gl.write_lib_tables(PRJ, LIB, "Low-voltage board")


# ============================== project + rules ==============================
RULES = {
    sp.RING: """(version 1)
# Ring board (low voltage only): FR4 1.6 mm. Copper keep-out from the box opening: rule areas on the board.
(rule "Board edge clearance"
    (constraint edge_clearance (min 0.25mm)))
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


MIC_ENTRY = -8.6                                            # lanes join the mic's parts this far left of the port
MIC_LANES = {"I2S_SD": 0.0, "I2S_WS": -2.2, "I2S_SCK": -2.5}  # lane heights from the port (ADAU7002 ball order)
MIC_BUS = -4.0                                              # +3V3 bus under the parts, from the port


def route_mic(bd, port):
    """The microphone's parts round the port (D-83), the same on both boards. Front: PDM_CLK from U2 to the mic's
    upper left pad; I2S lanes from MIC_ENTRY into U2 (SD straight in on the left, WS / SCK under U2 and up its right);
    U2's GND and IOVDD to C4; a +3V3 bus at MIC_BUS to the mic's VDD and C3. Back: PDM_DAT from U2 round to the mic's
    lower left pad; +3V3 from C4 down to the bus. Returns the lane entry points and the bus's left end."""
    B = P.B_Cu
    px, py = port
    via = lambda net, v: bd.via(net, *v, d=0.45, drill=0.2)
    u = {b: bd.pad_xy("U2", b) for b in sp.ADAU_BALLS}
    m = {n: bd.pad_xy("MK1", n) for n in ("1", "2", "3", "4", "5", "6", "7", "8")}
    c4p, c4g = bd.pad_xy("C4", "1"), bd.pad_xy("C4", "2")
    c3p, c3g = bd.pad_xy("C3", "1"), bd.pad_xy("C3", "2")
    r1s, r1g = bd.pad_xy("R1", "1"), bd.pad_xy("R1", "2")

    def escape(n):
        """Mic signal pad out through its corner of the GND ring, 45 deg."""
        sx, sy = sp.MIC_SIG_PINS[n]
        c = m[n]
        return [c, (c[0], c[1] + sy * 0.25), (c[0] + sx * 1.0, c[1] + sy * 1.25)]
    clk, dat, vdd = escape("2"), escape("1"), escape("4")
    # PDM_CLK: A2 right, up 45 deg, along to the mic's escape
    a2 = u["A2"]
    xa = a2[0] + 1.02
    yc = clk[2][1]
    bd.track("PDM_CLK", 0.12, [a2, (xa, a2[1]), (xa + yc - a2[1], yc)] + clk[::-1][:])
    # PDM_DAT: A1 left to a via, on the back over U2 and down beside the mic, a via, its escape
    a1 = u["A1"]
    v1, v2 = (a1[0] - 0.6, a1[1] + 0.25), (dat[2][0] - 0.475, dat[2][1])
    bd.track("PDM_DAT", 0.12, [a1, (a1[0] - 0.35, a1[1]), v1])
    xb = px - 2.6
    bd.track("PDM_DAT", 0.12, [v1, (xb, v1[1]), (xb, v2[1] + (v2[0] - xb)), v2], B)
    bd.track("PDM_DAT", 0.12, [v2] + dat[::-1])
    for v in (v1, v2):
        via("PDM_DAT", v)
    # I2S: SD straight into B1; WS / SCK under U2 and up its right into C2 / B2
    ent = {net: (px + MIC_ENTRY, py + dy) for net, dy in MIC_LANES.items()}
    bd.track("I2S_SD", 0.12, [ent["I2S_SD"], u["B1"]])
    bd.track("I2S_SD", 0.12, [r1s, (r1s[0], ent["I2S_SD"][1])])
    for net, ball, dx in (("I2S_WS", "C2", 0.4), ("I2S_SCK", "B2", 0.8)):
        b = u[ball]
        bd.track(net, 0.12, [b, (b[0] + dx, b[1]), (b[0] + dx, ent[net][1]), ent[net]])
    # GND: C1 to C4, C4 and R1 to a via; IOVDD / CONFIG together, down to C4
    bd.track("GND", 0.12, [u["C1"], (c4g[0], u["C1"][1])])
    vg = (c4g[0] - 0.85, c4g[1])
    bd.track("GND", 0.2, [c4g, vg])
    bd.track("GND", 0.2, [r1g, vg])
    via("GND", vg)
    bd.track("+3V3", 0.12, [u["D1"], u["D2"]])
    bd.track("+3V3", 0.15, [u["D1"], (u["D1"][0], c4p[1]), c4p])
    # +3V3: C4 to a via, on the back down to the bus, the bus to the mic's VDD and C3
    v3a = (c4p[0] - 0.9, c4p[1])
    v3b = (v3a[0] + 1.0, py + MIC_BUS + 0.3)
    bd.track("+3V3", 0.2, [c4p, v3a])
    bd.track("+3V3", 0.2, [v3a, (v3a[0], v3b[1] + 1.0), v3b], B)
    yb = py + MIC_BUS
    bd.track("+3V3", 0.2, [v3b, (v3b[0], yb), (c3p[0], yb)] + ([c3p] if abs(c3p[1] - yb) > 1e-3 else []))
    bd.track("+3V3", 0.15, [(vdd[2][0], yb)] + vdd[::-1])
    for v in (v3a, v3b):
        via("+3V3", v)
    # mic: SELECT low to the GND ring; GND ring (pads 5 and 6 between the escapes too) and C3 to the back pour
    bd.track("GND", 0.15, [m["3"], (m["8"][0], m["3"][1])])
    vm = (m["7"][0], m["7"][1] + 0.75)
    bd.track("GND", 0.2, [m["7"], vm])
    v5, v6 = (m["5"][0], m["5"][1] - 0.72), (m["6"][0] - 0.75, m["6"][1])
    bd.track("GND", 0.2, [m["5"], v5])
    bd.track("GND", 0.2, [m["6"], v6])
    vc = (c3g[0], c3g[1] + 0.75)
    bd.track("GND", 0.2, [c3g, vc])
    for v in (vm, v5, v6, vc):
        via("GND", v)
    return ent, (v3b[0], yb)


def build_eu_capboard():
    """EU cap board (D-70), as the NA ring board round CN2: I2S from CN2's upper row up, right, down and right into the
    microphone's parts (route_mic), +3V3 from the lower row down and right to their bus; SDA, SCL, +3V3 on the back down
    the outer left edge (outside the snap windows and the screws) to the SHT40; +5V from the pin pad on the back up the
    outer right edge and across to CN2; GND pours on both layers."""
    bd = Board(CTX, eu.CAPBOARD, 2, eu.E.CB_T, 0.12, 0.12, via_min=(0.45, 0.2))    # fine vias round CN2
    bd.outline(eu.CB_OUTER, eu.CB_OUTER_R)
    bd.polyline(eu.CB_POCKET)
    for win in eu.CB_SNAP_WINDOWS:
        bd.outline(win, 0.5)
    for ref, p in eu.CAPBOARD_PARTS.items():
        bd.place(ref, p, False)
    F, B = P.F_Cu, P.B_Cu
    for lay in (F, B):
        bd.zone("GND", lay, eu.CB_OUTER, min_w=0.25, fillet_r=0.5, name="GND")
    via = lambda net, v: bd.via(net, *v, d=0.45, drill=0.2)
    pin = {n: bd.pad_xy("J2", n) for n in sp.CN2_MAP}
    cy = eu.E.MSR_Y
    up, lo = pin["13"][1] + sp.CN2_PAD[1] / 2, pin["18"][1] - sp.CN2_PAD[1] / 2   # upper row pads' top ends, lower row pads' bottom ends
    ent, bus = route_mic(bd, eu.E.MIC_AT)
    # I2S on the front: up from the upper row, right (leftmost pad highest, outermost column), down, into the parts
    for i, (n, dy) in enumerate((("17", 2.95), ("19", 2.5), ("21", 2.1))):
        net = sp.CN2_MAP[n]
        x0, (xe, ye) = pin[n][0], ent[net]
        xd = xe - 0.4 * i
        bd.track(net, 0.12, [(x0, up), (x0, cy + dy), (xd, cy + dy), (xd, ye)] + ([(xe, ye)] if i else []))
    # +3V3 on the front: lower row down and right to the bus; a via to the back lanes on the way
    p3 = pin["22"]
    bd.track("+3V3", 0.2, [(p3[0], lo), (p3[0], bus[1]), bus])
    v33 = (p3[0], lo - 1.6)
    via("+3V3", v33)
    # SDA, SCL: vias under the lower row
    vsda, vscl = (pin["20"][0] - 0.1, lo - 1.0), (pin["18"][0] - 0.5, lo - 1.0)
    bd.track("SDA", 0.12, [(pin["20"][0], lo), (vsda[0], lo - 0.3), vsda])
    bd.track("SCL", 0.12, [(pin["18"][0], lo), (pin["18"][0], lo - 0.45), (vscl[0], lo - 0.65), vscl])
    via("SDA", vsda)
    via("SCL", vscl)
    # back: down, left above the pocket, down the outer left edge, right below the pocket to the SHT40
    u = {n: bd.pad_xy("U1", n) for n in ("1", "2", "3", "4")}
    c2p, c2g = bd.pad_xy("C2", "1"), bd.pad_xy("C2", "2")
    xl = {"SCL": -34.8, "SDA": -34.3, "+3V3": -33.8}        # the lane leaving highest runs outermost
    yt = {"SCL": 44.6, "SDA": 44.0, "+3V3": 43.4}
    yb = {"SCL": -41.2, "SDA": -40.6, "+3V3": -40.0}
    xv = {"SCL": -2.0, "SDA": -1.3, "+3V3": 4.2}            # vias to the front at the SHT40
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
    v5 = (pin["13"][0] - 0.6, up + 0.4)
    bd.track("+5V", 0.25, [(pin["13"][0], up), (pin["13"][0], v5[1]), v5])
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
    g21 = (pin["15"][0], cy)
    bd.track("GND", 0.15, [(pin["15"][0], pin["15"][1] - sp.CN2_PAD[1] / 2), g21])
    via("GND", g21)
    g30 = (pin["24"][0] + 0.3, lo - 1.0)
    bd.track("GND", 0.15, [(pin["24"][0], lo), g30])
    via("GND", g30)
    for v in (vs, (-20.0, -46.0), (20.0, -40.0), (-20.0, 52.0), (20.0, 60.0), (-28.0, 40.0)):
        bd.via("GND", *v)
    bd.text(f"EU CAP BOARD {sp.REV} (D-70)", -20.0, -46.0, P.F_SilkS, 1.0)
    if not eu.CN2_CONFIRMED:
        bd.text("J2 PIN MAP AND PIN 1 ARE PLACEHOLDERS - DO NOT FABRICATE", 0.0, 30.0, P.Cmts_User, 1.0)
    bd.branding(*sp.BRAND[eu.CAPBOARD], sp.URL)
    bd.save()


def closed_path(bd, pts, r, layer, width=0.1):
    """Closed polyline with filleted corners (kigen.fillet) on a drawing layer."""
    for piece in kigen.fillet(pts, r, closed=True):
        if piece[0] == "seg":
            bd.shape(P.SHAPE_T_SEGMENT, layer, width, piece[1], piece[2])
        else:
            bd.shape(P.SHAPE_T_ARC, layer, width, piece[1], piece[2], piece[3])


def build_cover():
    bd = Board(CTX, sp.COVER, 1, sp.FLEX_T, 0.15, sp.COVER_TRACK)
    ds = bd.b.GetDesignSettings()
    ds.m_SolderMaskExpansion = P.FromMM(0.1)                # coverlay openings 0.1 beyond the pads (D-116)
    ds.m_SolderMaskMinWidth = P.FromMM(0.25)                # webs under 0.25 merge (gang openings)
    tb = bd.b.GetTitleBlock()
    tb.SetTitle("Sladdseg - back cover flex")
    tb.SetRevision(sp.REV)
    tb.SetDate(sp.REV_DATE)
    bd.outline(sp.COVER_OUTLINE, sp.COVER_OUTLINE_R)
    for ref, p in sp.COVER_PARTS.items():
        bd.place(ref, p, False)
    w = sp.COVER_TRACK
    f1, f2, vbat, gnd = (bd.pad_xy(r, "1") for r in ("J1", "J2", "J3", "J4"))
    x_in, x_out = sp.COVER_LANES
    y_band = sp.COVER_LANE_Y
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
    d1_gnd, d1_5v = bd.pad_xy("D1", "1"), bd.pad_xy("D1", "2")
    xg = sp.COVER_GND_X
    y_up = sp._yt + 0.1                                  # just inside the regulator section
    # +5V: straight up from the upper pad, under U1 to IN, EN on the way, C3 and the ESD diode beside it
    bd.track("+5V", w, [f1, (f1[0], y_up - 0.4), (xm, y_up), (xm, p_in[1]), p_in])
    bd.track("+5V", w, [(xm, p_en[1]), p_en])
    bd.track("+5V", w, [c3_5v, (xm, c3_5v[1])])
    bd.track("+5V", w, [d1_5v, (xm, d1_5v[1])])
    # GND: lower pad up the outer edge to U1's GND pin, C3, D1 and C4; and down into the run to J4
    bd.track("GND", w, [f2, (xg, f2[1]), (xg, c4_gnd[1]), c4_gnd])
    bd.track("GND", w, [p_gnd, (xg, p_gnd[1])])
    bd.track("GND", w, [c3_gnd, (xg, c3_gnd[1])])
    bd.track("GND", w, [d1_gnd, (xg, d1_gnd[1])])
    bd.track("GND", w, [f2, (f2[0], sp._yb + 0.5), (x_out, sp._yb + 0.5), (x_out, gnd[1] + 2.0), gnd])
    # +3V3: OUT up to C4, down the pad section's inner edge past both pads, across the jog above the GND lane (D-79),
    # down the run's inner lane straight through the bend zone, across the band BC_BEND_CLR past it, into VBAT
    x_e = sp._xs1 - 0.65
    y_j = sp._yb + 1.3
    bd.track("+3V3", w, [p_out, (p_out[0], c4_3v3[1] - 0.7), c4_3v3, (x_e, c4_3v3[1]), (x_e, y_j), (x_in, y_j),
                         (x_in, y_band), (vbat[0], y_band), vbat])
    # teardrops: a 0.5 mm wide first stretch from each pad along its track (flex: no sharp neck at the pad)
    for ref, num, toward, net in (("J1", "1", (f1[0], y_up - 0.4), "+5V"), ("J2", "1", (xg, f2[1]), "GND"),
                                  ("J2", "1", (f2[0], sp._yb + 0.5), "GND"), ("J3", "1", (vbat[0], y_band), "+3V3"),
                                  ("J4", "1", (x_out, gnd[1] + 2.0), "GND"), ("C3", "1", (xg, c3_gnd[1]), "GND"),
                                  ("C3", "2", (xm, c3_5v[1]), "+5V"), ("C4", "1", (xg, c4_gnd[1]), "GND"),
                                  ("D1", "1", (xg, d1_gnd[1]), "GND"), ("D1", "2", (xm, d1_5v[1]), "+5V")):
        c = bd.pad_xy(ref, num)
        pd = [q for q in bd.fps[ref].Pads() if q.GetNumber() == num][0]
        half = max(kigen.mm(pd.GetSize())) / 2
        dx, dy = toward[0] - c[0], toward[1] - c[1]
        n = hypot(dx, dy)
        reach = min(half + 0.5, n)
        bd.track(net, 0.5, [c, (c[0] + dx / n * reach, c[1] + dy / n * reach)])
    # bend zone, stiffeners, fab notes
    for yb in sp.COVER_BEND:
        bd.shape(P.SHAPE_T_SEGMENT, P.Cmts_User, 0.1, (sp._xr0 - 0.5, yb), (sp._xr1 + 0.5, yb))
    bd.text(f"BEND ZONE 90 deg, inside r {sp.BC_BEND_R} mm, copper outside", 0.0, sp.COVER_BEND[0] + 0.9, P.Cmts_User, 0.6)
    closed_path(bd, sp.COVER_STIFF, 0.5, P.User_1)
    bd.text(f"BOTTOM STIFFENER FR4 {sp.BC_END_T} mm", 0.0, sp.COVER_Y_END + 1.6, P.User_1, 0.6)
    closed_path(bd, sp.COVER_PAD_STIFF, [0.76, 0.76, 0.0, 0.76], P.User_1)
    bd.text(f"BOTTOM STIFFENER FR4 {sp.BC_PAD_STIFF_T} mm", sp._xs0 - 1.2, (sp._yb + sp._yr) / 2, P.User_1, 0.6, 90)
    notes = ["1 copper layer flex: polyimide, 0.10 mm without stiffeners, 1/2 oz Cu, yellow coverlay, ENIG",
             f"FR4 stiffeners on the bottom (non-copper) side: {sp.BC_PAD_STIFF_T} mm and {sp.BC_END_T} mm, outlines on User_1",
             f"One 90 deg bend in the run, inside r {sp.BC_BEND_R} mm, copper outside, installed once",
             "Coverlay openings 0.1 mm beyond the pads; no holes"]
    for i, s in enumerate(notes):
        bd.text(s, 0.0, sp._yr - 3.0 - 1.0 * i, P.Cmts_User, 0.6)
    if not sp.COVER_CONFIRMED:
        bd.text("FIT-TEST PROTOTYPE: positions REF / MEASURE", 0.0, 2.0, P.Cmts_User, 0.9)
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
    bd = Board(CTX, sp.RING, 2, 1.6, 0.12, 0.15, via_min=(0.45, 0.2))    # fine vias round CN2 and U2
    bd.outline(sp.RING_OUTER, sp.RING_OUTER_R)
    bd.polyline(sp.RING_WINDOW)
    for ref, p in sp.RING_PARTS.items():
        bd.place(ref, p, False)
    return bd


def build_ring():
    """Ring board: CN2 fan-out on the front, I2S lanes up and right to the microphone's parts (route_mic), +3V3 from
    CN2 to their bus; SDA, SCL, +3V3 on the back across the top band to the right rail, down the rail on the front round
    the box's corner keep-out and along the bottom band to the SHT40; +5V from J1 on the back to CN2; GND pours."""
    bd = place_ring()
    F, B = P.F_Cu, P.B_Cu
    rule_area(bd, sp.KEEP_FRONT, F, "front copper keep-out: box opening + 6.4 mm")
    rule_area(bd, sp.KEEP_BACK, B, "back copper keep-out: box opening + 8.0 mm")
    for lay in (F, B):
        bd.zone("GND", lay, sp.RING_OUTER, min_w=0.25, fillet_r=0.5, name="GND")
    pin = {net: bd.pad_xy("J2", n) for n, net in sp.CN2_MAP.items() if net != "GND"}
    top, bot = pin["I2S_WS"][1] + sp.CN2_PAD[1] / 2, pin["SCL"][1] - sp.CN2_PAD[1] / 2   # upper / lower row pad ends
    ent, bus = route_mic(bd, sp.MIC_AT)
    # I2S: up from the upper row (leftmost highest), right to the mic's parts
    for net, (xe, ye) in ent.items():
        bd.track(net, 0.12, [(pin[net][0], top), (pin[net][0], ye), (xe, ye)])
    # +5V: CN2 up-left to a via; J1's +5V pins to vias; C1 to a via; joined on the back
    p5 = pin["+5V"]
    v5 = (p5[0] - 0.5, 61.4)
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
    gnd_odd, gnd_even = (min((n for n, net in sp.CN2_MAP.items() if net == "GND" and int(n) % 2 == r), key=int)
                         for r in (1, 0))
    g21, g30 = bd.pad_xy("J2", gnd_odd), bd.pad_xy("J2", gnd_even)          # GND contacts on each row
    vg1, vg2 = (g21[0] - 0.3, 62.2), (g30[0] + 0.55, bot - 0.5)
    bd.track("GND", 0.15, [(g21[0], top), (g21[0], vg1[1] - 0.3), vg1])
    bd.track("GND", 0.15, [(g30[0], bot), (g30[0], bot - 0.25), vg2])
    for v in (vg1, vg2):
        bd.via("GND", *v)
    # +3V3: lower row down, right to a via to the back lanes; on up to the mic's bus
    p3 = pin["+3V3"]
    v3 = (24.5, 55.5)
    bd.track("+3V3", 0.2, [(p3[0], bot), (p3[0], v3[1]), v3, (v3[0], bus[1])])
    # SDA / SCL: lower row down to vias
    sda, scl = pin["SDA"], pin["SCL"]
    vsda, vscl = (sda[0], 54.7), (scl[0] - 0.6, 54.5)
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
        else:                                               # SCL: round the left of the SHT40 into pin 2
            pts += [(-2.0, yl), (-2.0, u1["2"][1]), u1["2"]]
            bd.track(net, w, pts)
    bd.track("GND", 0.2, [u1["4"], c2g])
    vs = (c2g[0], c2g[1] + 1.1)                              # the SHT40's GND patch to the back pour
    bd.track("GND", 0.25, [c2g, vs])
    for v in (vs, (-20.0, -50.0), (20.0, -50.0), (-20.0, 52.0), (-8.0, 68.5), (8.0, 68.5)):   # stitching, beside the switch notches
        bd.via("GND", *v)
    bd.text(f"RING BOARD {sp.REV} (D-50)", 0.0, -53.6, P.F_SilkS, 1.0)
    if not sp.CN2_CONFIRMED:
        bd.text("J2 PIN MAP AND PIN 1 ARE PLACEHOLDERS - DO NOT FABRICATE", 0.0, 66.5, P.Cmts_User, 1.0)
    bd.branding(*sp.BRAND[sp.RING], sp.URL)
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
    for name in (sp.RING, sp.RISER_B, sp.COVER, eu.CAPBOARD):
        build_project(name)
    status = "CN2 mate and contact map UNCONFIRMED (placeholder) - do not fabricate" if not sp.CN2_CONFIRMED \
        else "CN2 mate confirmed"
    gen = "Generated by pcb/sensor/tools/gen_sensor.py - edit sensor_parts.py"

    def schematic(name, parts, flags, title, comments, notes):
        build_schematic(CTX, name, parts, flags, f"Sladdseg - {title}", sp.REV, sp.REV_DATE, comments, notes)
    schematic(sp.RING, sp.RING_PARTS, ("+5V", "+3V3", "GND"), "ring board", [status, gen],
              "Ring board (docs/DESIGN.md D-50): FR4 1.6 mm round the insert's plug, against the wall.\n"
              "J1: 5 V from the wiring board's J2 over a 6-way 0.5 mm FFC (pinout mirror-symmetric).\n"
              "J2 mates the MSR-2's rear connector CN2 (MSR-2 powered through its 5V pin).\n"
              "U1: SHT40, I2C on the MSR-2 bus (SDA = IO1, SCL = IO0).\n"
              "MK1: top-port PDM microphone, SELECT low; U2: ADAU7002 PDM to I2S, CONFIG high = I2S (D-83).\n"
              "I2S to the MSR-2: SCK = IO4, WS = IO6, SD = IO7. Sample rate >= 16 kHz (PDM clock 64 x fs >= 1 MHz).\n"
              "H1-H3: SMT spacers under the MSR-2's board. Copper keeps 8 mm from the box opening.")
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
              "MK1: top-port PDM microphone; U2: ADAU7002 PDM to I2S (D-83); U1: SHT40 on the MSR-2's I2C.\n"
              "H1-H4: holes for the M2 screws into the carrier.")
    # board files: build in memory, save (KiCad 9 python cannot refill/reload safely in one board)
    build_ring()
    build_riser()
    build_cover()
    build_eu_capboard()


if __name__ == "__main__":
    main()
