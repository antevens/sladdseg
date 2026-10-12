"""Build the NA mains board's project-local libraries (kicad/na_mains_board.kicad_sym and .pretty).

Stock KiCad parts are copied so the project is self-contained. Built from datasheets here: the WAGO 2604-1106
terminal block, the Wurth WA-SMSI M2 spacer posts and the standoff mounting hole; the rocker switch, the varistor and
the logos come from pcb/tools/fplib.py.
"""
import copy
import shutil
import sys
from pathlib import Path

sys.path.insert(1, str(Path(__file__).resolve().parents[2] / "tools"))     # pcb/tools: sexpr, fplib, kigen
from sexpr import loads, dumps, first, Sym, S                               # noqa: E402
from fplib import (SYM_DIR, FP_DIR, stock_symbol, rename_symbol, marquardt_symbol, _fp, rect, tht, circ,  # noqa: E402
                   fp_rocker, fp_mov, fp_smsi, fp_ant_logo, model3d, localize_models, write_lib_tables)
from parts_na import (LIB, FP_WAGO, FP_IRM, FP_FUSE, FP_J2, FP_POST, FP_MH, FP_KICAD,  # noqa: E402
                      MOUNT_D, STANDOFF_HEX_D, SCREW_HEAD_D, WAGO_PAD, WAGO_ROW_PITCH, WAGO_BODY, WAGO_DS, BOARD,
                      PS1_PINS, SMSI_DS, POST_HOLE, POST_PAD)

PRJ = Path(__file__).resolve().parents[1] / "kicad"



# (stock lib, stock name, project name)
SYMBOLS = [
    ("Converter_ACDC", "IRM-03-5", "IRM-03-5"),
    ("Device", "Fuse", "Fuse"),
    ("Device", "Varistor", "Varistor"),
    ("Connector_Generic", "Conn_01x01", "Conn_01x01"),
    ("Connector", "Screw_Terminal_01x06", "Screw_Terminal_01x06"),
    ("Connector_Generic", "Conn_01x06", "Conn_01x06"),
    ("power", "+5V", "+5V"),
    ("power", "GND", "GND"),
    ("power", "PWR_FLAG", "PWR_FLAG"),
]

STOCK_FP = {
    FP_IRM: ("Converter_ACDC", FP_IRM),
    FP_FUSE: ("Fuse", FP_FUSE),
    FP_J2: ("Connector_FFC-FPC", FP_J2),
    FP_KICAD: ("Symbol", FP_KICAD),
}


def build_symbols():
    out = [Sym("kicad_symbol_lib"), S("version", Sym("20241209")), S("generator", "gen_libs"),
           S("generator_version", "9.0")]
    for lib, name, new in SYMBOLS:
        out.append(rename_symbol(stock_symbol(lib, name), new))
    out.append(marquardt_symbol())
    (PRJ / f"{LIB}.kicad_sym").write_text(dumps(out) + "\n")


def fp_wago():
    # WAGO 2604-1106 (datasheet page; pin rows and body from WAGO's 3D model): 6-pole, pitch 5 mm,
    # 2 solder pins per potential in rows WAGO_ROW_PITCH apart (pins 0.8 x 1 mm, drilled hole
    # 1.3 (+0.1) mm); the second row lies behind the first, away from the entries. Fab outline = the
    # body at the board; the courtyard also covers the levers, which overhang the entry side up top.
    front, back, lever = WAGO_BODY
    items = []
    for i in range(6):
        x = i * 5.0 - 12.5
        for y in (0.0, WAGO_ROW_PITCH):
            shape = "rect" if i == 0 and y == 0.0 else "circle"
            items.append(tht(str(i + 1), x, y, shape, *WAGO_PAD, 1.3))
    items += [rect(-16.2, -front, 16.2, back, "F.Fab", 0.1),
              rect(-16.32, -front - 0.12, 16.32, back + 0.12, "F.SilkS", 0.12),
              rect(-16.45, -lever - 0.25, 16.45, back + 0.25, "F.CrtYd", 0.05)]
    items.append(model3d("WAGO_2604-1106"))
    return _fp(FP_WAGO, f"WAGO 2604-1106 PCB terminal block, push-in lever, 6-pole, P5.00 mm, 4 mm2, "
               f"entry parallel to PCB (entry side -y), 400 V III/2, {WAGO_DS}; pin rows {WAGO_ROW_PITCH} mm apart "
               "and body from WAGO's 3D model", "WAGO 2604 terminal block push-in", "through_hole", items)


def fp_mount():
    """Unplated hole for one of the barrier's nylon standoffs, with no copper: the standoff's hex
    (front) and the screw head (back) bear on bare laminate. The board keeps copper MOUNT_KO away."""
    items = [S("pad", "", Sym("np_thru_hole"), Sym("circle"), S("at", 0, 0), S("size", MOUNT_D, MOUNT_D),
               S("drill", MOUNT_D), S("layers", "*.Cu", "*.Mask"))]
    items += [circ("F.CrtYd", STANDOFF_HEX_D / 2 + 0.25, 0.05),
              circ("B.CrtYd", SCREW_HEAD_D / 2 + 0.25, 0.05),
              circ("F.Fab", STANDOFF_HEX_D / 2, 0.1)]
    return _fp(FP_MH, f"Mounting hole {MOUNT_D} mm for the barrier's M3 nylon standoffs, unplated, no copper "
               "(docs/DESIGN.md D-57)", "mounting hole standoff",
               "through_hole board_only exclude_from_pos_files exclude_from_bom", items)


def fp_post():
    """The mains board's spacer posts: WA-SMSI M2, L 7 mm."""
    return fp_smsi(FP_POST, 7, POST_HOLE, POST_PAD, SMSI_DS)


def build_footprints():
    d = PRJ / f"{LIB}.pretty"
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    for new, (lib, name) in STOCK_FP.items():
        fp = loads((FP_DIR / f"{lib}.pretty" / f"{name}.kicad_mod").read_text())
        fp[1] = new
        if new == FP_IRM:
            trim_irm_silk(fp)
        if new == FP_KICAD:                 # no schematic symbol: keep it out of the parity check
            first(fp, "attr").insert(1, Sym("board_only"))
        localize_models(fp, PRJ)
        (d / f"{new}.kicad_mod").write_text(dumps(fp) + "\n")
    for fp in (fp_rocker(), fp_wago(), fp_mov(), fp_mount(), fp_post(), fp_ant_logo()):
        (d / f"{fp[1]}.kicad_mod").write_text(dumps(fp) + "\n")


def trim_irm_silk(fp):
    """Break the body silk line where the slot passes under the module. PS1 sits on the back,
    turned so that local y runs along front-view X (X = pin1 X + y) and local x 21.01 is the
    body edge nearest the board's bottom edge."""
    sx, sw, _ = BOARD["slot"]
    gap = [sx - sw / 2 - 0.5 - PS1_PINS["1"][0], sx + sw / 2 + 0.5 - PS1_PINS["1"][0]]
    for i, x in enumerate(fp):
        if isinstance(x, list) and x and x[0] == "fp_line" and first(x, "layer")[1] == "F.SilkS":
            st, en = first(x, "start"), first(x, "end")
            if float(st[1]) == float(en[1]) == 21.01 and float(st[2]) < gap[0] < gap[1] < float(en[2]):
                upper = copy.deepcopy(x)
                en[2] = gap[0]
                first(upper, "start")[2] = gap[1]
                first(upper, "uuid")[1] = "6d1c1f3e-0000-4000-8000-00000000b3c4"
                fp.insert(i + 1, upper)
                first(fp, "descr")[1] += " | silk body line split at the isolation slot"
                return
    raise RuntimeError("IRM silk line not found")


def _have_stock():
    if not SYM_DIR or not FP_DIR:
        return False
    return all((SYM_DIR / f"{lib}.kicad_sym").exists() for lib in {lib for lib, _, _ in SYMBOLS} | {"Switch"}) and \
        all((FP_DIR / f"{lib}.pretty" / f"{n}.kicad_mod").exists() for lib, n in STOCK_FP.values())


if __name__ == "__main__":
    PRJ.mkdir(parents=True, exist_ok=True)
    if _have_stock():
        build_symbols()
        build_footprints()
        print(f"libs written to {PRJ}")
    elif (PRJ / f"{LIB}.kicad_sym").exists() and (PRJ / f"{LIB}.pretty").is_dir():
        print(f"gen_libs: KiCad stock libraries not found; keeping the committed libraries in {PRJ}",
              file=sys.stderr)
    else:
        sys.exit("gen_libs: KiCad stock libraries not found; set KICAD9_SYMBOL_DIR / KICAD9_FOOTPRINT_DIR")
    write_lib_tables(PRJ, LIB, "Project")
