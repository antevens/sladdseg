"""Footprint and symbol helpers shared by every board generator (pcb/na/tools, pcb/eu/tools, pcb/shared/tools).

Stock KiCad parts are copied so each project is self-contained. Built from datasheets: the Marquardt 1802.2504 /
E-Switch RA412C1100 rocker switch, the TDK CU4032 SMD varistor, the Wurth WA-SMSI M2 spacer, the Harwin P70 spring
pin; the ant logo from pcb/art.
"""
import copy
import os
import re
import shutil
from pathlib import Path
from sexpr import loads, find, first, Sym, S
from common_parts import (FP_ROCKER, FP_MOV, FP_ANT, FP_KICAD, ANT_LOGO_H, ROCKER_DS, CU_DS, POST_PASTE,
                          SMSI_BODY_D)

_BASES = ["/usr/share/kicad", "/usr/local/share/kicad", "/opt/kicad/share/kicad",
          "/var/lib/flatpak/app/org.kicad.KiCad/current/active/files/share/kicad",
          "~/.local/share/flatpak/app/org.kicad.KiCad/current/active/files/share/kicad",
          "/Applications/KiCad/KiCad.app/Contents/SharedSupport"]

_cli = shutil.which("kicad-cli")
if _cli:
    _BASES.insert(0, str(Path(_cli).resolve().parents[1] / "share" / "kicad"))


def stock_dir(kind, env):
    """kind: 'symbols' or 'footprints'; env: SYMBOL or FOOTPRINT."""
    cands = [os.environ.get(f"KICAD{v}_{env}_DIR", "") for v in ("9", "8", "")]
    cands += [str(Path(b).expanduser() / kind) for b in _BASES]
    for c in cands:
        if c and Path(c).is_dir():
            return Path(c)
    return None


SYM_DIR = stock_dir("symbols", "SYMBOL")
FP_DIR = stock_dir("footprints", "FOOTPRINT")
ART = Path(__file__).resolve().parents[1] / "art"

# SW_DPST pins 1-2 and 3-4 are the two poles; the Marquardt drawing numbers them 1-1a and 2-2a
ROCKER_PINS = {"1": "1", "2": "1a", "3": "2", "4": "2a"}


def stock_symbol(lib, name):
    """Return a flattened copy of a stock symbol (resolves `extends`)."""
    tree = loads((SYM_DIR / f"{lib}.kicad_sym").read_text())
    syms = {s[1]: s for s in find(tree, "symbol")}
    s = copy.deepcopy(syms[name])
    ext = first(s, "extends")
    if not ext:
        return s
    base = copy.deepcopy(syms[ext[1]])
    bname = base[1]
    base[1] = name
    dprops = {p[1]: p for p in find(s, "property")}
    for i, x in enumerate(base):
        if isinstance(x, list) and x and x[0] == "property" and x[1] in dprops:
            base[i] = dprops.pop(x[1])
    for p in dprops.values():
        base.insert(len(base) - len(find(base, "symbol")) - 1, p)
    for sub in find(base, "symbol"):
        sub[1] = sub[1].replace(bname, name, 1)
    return base


def rename_symbol(sym, new):
    """Rename a symbol and its units in place; returns it."""
    old = sym[1]
    sym[1] = new
    for sub in find(sym, "symbol"):
        sub[1] = sub[1].replace(old, new, 1)
    return sym


def marquardt_symbol():
    """The Marquardt 1802.2504 rocker: the stock SW_DPST with pins 1 / 1a, 2 / 2a."""
    sym = rename_symbol(stock_symbol("Switch", "SW_DPST"), "SW_DPST_Marquardt")
    renumber_rocker(sym)
    return sym


def renumber_rocker(sym):
    """Rename pin numbers and the unit names, set datasheet fields."""
    def walk(node):
        for x in node:
            if isinstance(x, list) and x:
                if x[0] == "pin":
                    num = first(x, "number")
                    num[1] = ROCKER_PINS[num[1]]
                else:
                    walk(x)
    walk(sym)
    for p in find(sym, "property"):
        if p[1] == "Datasheet":
            p[2] = ROCKER_DS
        if p[1] == "Description":
            p[2] = "Marquardt 1802.2504 DPST rocker: 1-1a one pole, 2-2a the other"
        if p[1] == "ki_fp_filters":
            p[2] = "Marquardt*"


# ---------------- footprints built from datasheets ----------------


def _fp(name, descr, tags, attr, items):
    head = [Sym("footprint"), name, S("version", Sym("20241229")), S("generator", "gen_libs"),
            S("generator_version", "9.0"), S("layer", "F.Cu"), S("descr", descr), S("tags", tags)]
    props = [S("property", "Reference", "REF**", S("at", 0, 0, 0), S("layer", "F.SilkS"),
               S("effects", S("font", S("size", 1, 1), S("thickness", 0.15)))),
             S("property", "Value", name, S("at", 0, 0, 0), S("layer", "F.Fab"),
               S("effects", S("font", S("size", 1, 1), S("thickness", 0.15))))]
    return head + props + [S("attr", Sym(attr))] + items + [S("embedded_fonts", Sym("no"))]


def rect(x0, y0, x1, y1, layer, w):
    return S("fp_rect", S("start", x0, y0), S("end", x1, y1),
             S("stroke", S("width", w), S("type", Sym("solid"))), S("fill", Sym("no")), S("layer", layer))


def line(x0, y0, x1, y1, layer, w):
    return S("fp_line", S("start", x0, y0), S("end", x1, y1), S("stroke", S("width", w), S("type", Sym("solid"))),
             S("layer", layer))


def tht(num, x, y, shape, sx, sy, drill):
    return S("pad", num, Sym("thru_hole"), Sym(shape), S("at", x, y), S("size", sx, sy),
             S("drill", drill), S("layers", "*.Cu", "*.Mask"))


def smd(num, x, y, sx, sy):
    return S("pad", num, Sym("smd"), Sym("rect"), S("at", x, y), S("size", sx, sy),
             S("layers", "F.Cu", "F.Paste", "F.Mask"))


def body(w, h, cx=0.0, cy=0.0, crt=0.25, silk=True):
    x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2
    out = [rect(x0, y0, x1, y1, "F.Fab", 0.1), rect(x0 - crt, y0 - crt, x1 + crt, y1 + crt, "F.CrtYd", 0.05)]
    if silk:
        out.append(rect(x0 - 0.12, y0 - 0.12, x1 + 0.12, y1 + 0.12, "F.SilkS", 0.12))
    return out


def slot(num, x, y, sx, sy, dx, dy):
    """Plated slot: oval pad sx x sy, oval drill dx x dy."""
    return S("pad", num, Sym("thru_hole"), Sym("oval"), S("at", x, y), S("size", sx, sy),
             S("drill", Sym("oval"), dx, dy), S("layers", "*.Cu", "*.Mask"))


def fp_rocker(name=FP_ROCKER, slots=True):
    # Mounted turned 90 degrees; origin = body centre, poles 10.2 mm apart along x (pole 1 = 1/1a at -x, pole 2 =
    # 2/2a at +x), 1 / 2 on the body's centre line, 1a / 2a off it (-y). Marquardt 1802.2504 (drawing rev g): 0.8 mm
    # pins, 1a / 2a 7.0 off, holes 1.3 (+0.1). slots: also the E-Switch RA412C1100 (RA4 drawing, D-88): 4.8 x 0.8 tabs
    # along x, 7.1 off, snapped in either way round so its tabs land on the slots: slots 5.2 x 1.2, pads 6.2 x 2.3,
    # 1a / 2a 7.05 off. Pin numbering per the DPST schematic: confirm on samples.
    if slots:
        items = [slot(n, x, y, 6.2, 2.3, 5.2, 1.2) for n, x, y in
                 (("1", -5.1, 0.0), ("1a", -5.1, -7.05), ("2", 5.1, 0.0), ("2a", 5.1, -7.05))]
        what = ("Rocker switch DPST: Marquardt 1802.2504 (0.8 mm pins) or E-Switch RA412C1100 (4.8 x 0.8 tabs), plated "
                "slots 5.2 x 1.2 on 10.2 x 7.05 mm")
    else:
        items = [tht(n, x, y, "circle", 2.4, 2.4, 1.4) for n, x, y in
                 (("1", -5.1, 0.0), ("1a", -5.1, -7.0), ("2", 5.1, 0.0), ("2a", 5.1, -7.0))]
        what = "Rocker switch DPST, PCB pins 0.8 mm, holes 1.3 mm on 10.2 x 7 mm grid"
    items += body(22.0, 18.6, crt=1.25, silk=False)       # courtyard round the 24 x 21 flange (overhangs at the panel)
    items.append(model3d("Marquardt_1802.2504"))
    return _fp(name, f"{what} (1 / 2 on the body centre line), body 22x18.6 mm, flange 24x21 mm, 1802.2504 PCB seat "
               f"16.2 mm below the panel face; {ROCKER_DS}" + ("; E-Switch RA4 datasheet" if slots else ""),
               "rocker switch DPST Marquardt 1800" + (" E-Switch RA4" if slots else ""),
               "through_hole", items)


def fp_kicad_logo():
    """The stock KiCad logo, board-only (no schematic symbol: kept out of the parity check)."""
    fp = loads((FP_DIR / "Symbol.pretty" / f"{FP_KICAD}.kicad_mod").read_text())
    first(fp, "attr").insert(1, Sym("board_only"))
    return fp


def fp_ant_logo():
    """The ant logo from pcb/art (the author's own artwork, KiCad 5 format), centred and scaled
    to ANT_LOGO_H tall; stroke widths scale with it."""
    src = loads((ART / "Ant_Logo_SilkScreen.kicad_mod").read_text())
    lines = [(float(first(x, "start")[1]), float(first(x, "start")[2]), float(first(x, "end")[1]),
              float(first(x, "end")[2]), float(first(x, "width")[1])) for x in find(src, "fp_line")]
    xs = [v for l in lines for v in (l[0], l[2])]
    ys = [v for l in lines for v in (l[1], l[3])]
    k = ANT_LOGO_H / (max(ys) - min(ys) + lines[0][4])
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    items = [S("fp_line", S("start", round((x0 - cx) * k, 4), round((y0 - cy) * k, 4)),
               S("end", round((x1 - cx) * k, 4), round((y1 - cy) * k, 4)),
               S("stroke", S("width", round(w * k, 4)), S("type", Sym("solid"))), S("layer", "F.SilkS"))
             for x0, y0, x1, y1, w in lines]
    return _fp(FP_ANT, f"Ant logo, {ANT_LOGO_H} mm, from pcb/art/Ant_Logo_SilkScreen.kicad_mod", "logo ant",
               "board_only exclude_from_pos_files exclude_from_bom allow_missing_courtyard", items)


def circ(layer, r, w):
    """Circle of radius r round the footprint origin."""
    return S("fp_circle", S("center", 0, 0), S("end", r, 0), S("stroke", S("width", w), S("type", Sym("solid"))),
             S("fill", Sym("no")), S("layer", layer))


def _arc_pts(r, a0, a1, n=12):
    from math import cos, sin, radians
    return [(round(r * cos(radians(a0 + (a1 - a0) * i / n)), 4), round(r * sin(radians(a0 + (a1 - a0) * i / n)), 4))
            for i in range(n + 1)]


def _ring_pads(num, layers, ri, ro, web):
    """Custom SMD pads forming a ring ri..ro round the origin: two half rings that meet (web 0) or four
    sectors split by webs of width web. Each pad is anchored on its own sector."""
    from math import asin, cos, sin, degrees, radians
    a = degrees(asin(web / 2 / ri)) if web else 0.0
    n, rm, anchor, out = (4, 90) if web else (2, 180), (ri + ro) / 2, min(0.5, ro - ri - 0.05), []
    for k in range(n[0]):
        a0, a1 = k * n[1] + a, (k + 1) * n[1] - a
        cx, cy = round(rm * cos(radians((a0 + a1) / 2)), 4), round(rm * sin(radians((a0 + a1) / 2)), 4)
        pts = _arc_pts(ro, a0, a1) + _arc_pts(ri, a1, a0)
        prim = S("gr_poly", S("pts", *[S("xy", round(x - cx, 4), round(y - cy, 4)) for x, y in pts]),
                 S("width", 0), S("fill", Sym("yes")))
        out.append(S("pad", num, Sym("smd"), Sym("custom"), S("at", cx, cy), S("size", anchor, anchor),
                     S("layers", *layers), S("options", S("clearance", Sym("outline")), S("anchor", Sym("circle"))),
                     S("primitives", prim)))
    return out


def fp_smsi(name, length, hole, pad, ds, silk=True):
    """Wurth WA-SMSI M2 SMT spacer of the given length: unplated hole for the spigot (front mask open over
    the ring only), solder pad ring in two halves, stencil ring in four sectors, per the datasheet's land pattern."""
    items = [S("pad", "", Sym("np_thru_hole"), Sym("circle"), S("at", 0, 0), S("size", hole, hole),
               S("drill", hole), S("layers", "*.Cu", "B.Mask"))]
    items += _ring_pads("1", ["F.Cu", "F.Mask"], hole / 2, pad / 2, 0)
    items += _ring_pads("", ["F.Paste"], POST_PASTE[0] / 2, POST_PASTE[1] / 2, POST_PASTE[2])
    items.append(circ("F.Fab", SMSI_BODY_D / 2, 0.1))
    if silk:
        items.append(circ("F.SilkS", pad / 2 + 0.2, 0.12))
    items.append(circ("F.CrtYd", pad / 2 + 0.25, 0.05))
    return _fp(name, f"Wurth WA-SMSI SMT steel spacer M2, L {length} mm, body {SMSI_BODY_D} mm, spigot hole {hole} mm "
               f"unplated, pad {pad} mm, stencil ring {POST_PASTE[0]}/{POST_PASTE[1]} mm, {ds}",
               "spacer standoff SMT M2", "smd allow_soldermask_bridges", items)


def fp_p70(name, pad_d, hole_d, flange_d, ds):
    """Harwin P70-2200045 SMT spring pin with peg: recommended pad over a plated hole for the peg."""
    items = [S("pad", "1", Sym("thru_hole"), Sym("circle"), S("at", 0, 0), S("size", pad_d, pad_d), S("drill", hole_d),
               S("layers", "*.Cu", "*.Mask", "F.Paste")),
             circ("F.Fab", flange_d / 2, 0.1), circ("F.CrtYd", pad_d / 2 + 0.25, 0.05), model3d(name)]
    return _fp(name, f"Harwin P70-2200045 SMT spring pin with peg, pad {pad_d} mm, hole {hole_d} mm, {ds}",
               "spring pin pogo", "smd", items)


def model3d(name):
    """3D model from the project's kicad/3d (pcb/tools/gen_3d.py), already in footprint coordinates."""
    return S("model", f"${{KIPRJMOD}}/3d/{name}.step", S("offset", S("xyz", 0, 0, 0)),
             S("scale", S("xyz", 1, 1, 1)), S("rotate", S("xyz", 0, 0, 0)))


def localize_models(fp, prj):
    """Point a copied stock footprint's 3D model at the project's kicad/3d when gen_3d.py made one
    of that name (the stock library lacks it)."""
    for m in find(fp, "model"):
        stem = Path(m[1]).stem
        if (Path(prj) / "3d" / f"{stem}.step").exists():
            m[1] = f"${{KIPRJMOD}}/3d/{stem}.step"
    return fp


def fp_mov():
    # TDK SIOV-CU4032K275G2K1 (B72660M0271K093): body 10.2 x 8.0 x 4.5 mm; solder pads
    # A = 3.5 (pad height), B = 2.8 (pad width), C = 6.5 (gap). The datasheet also gives
    # D = 10.1, which disagrees with B + C + B = 12.1; the larger gap is used.
    pitch = 6.5 + 2.8
    items = [smd("1", -pitch / 2, 0, 2.8, 3.5), smd("2", pitch / 2, 0, 2.8, 3.5)]
    items += body(10.2, 8.0, crt=0.5, silk=False)
    items += [rect(-6.3, -4.3, 6.3, 4.3, "F.SilkS", 0.12)]
    items.append(model3d(FP_MOV))
    return _fp(FP_MOV, f"TDK SMD disk varistor CU4032 (10.2x8.0x4.5 mm), pads per datasheet {CU_DS} "
               "(A 3.5, B 2.8, C 6.5 mm)", "varistor SIOV CU4032", "smd", items)


def write_lib_tables(prj, lib, what):
    """Add <lib>.pretty and <lib>.kicad_sym to the project's fp-lib-table and sym-lib-table, keeping the other
    generators' libraries in the same project folder."""
    for kind, ext, noun in (("fp", "pretty", "footprints"), ("sym", "kicad_sym", "symbols")):
        f = Path(prj) / f"{kind}-lib-table"
        rows = {}
        if f.exists():
            for m in re.finditer(r'\(lib \(name "([^"]+)"\).*\)\n', f.read_text()):
                rows[m.group(1)] = m.group(0)
        rows[lib] = (f'(lib (name "{lib}")(type "KiCad")(uri "${{KIPRJMOD}}/{lib}.{ext}")'
                     f'(options "")(descr "{what} {noun}"))\n')
        f.write_text(f"({kind}_lib_table\n\t(version 7)\n" + "".join(f"\t{rows[k]}" for k in sorted(rows)) + ")\n")
