"""PCBWay order packs for the devkit (MIN_PCB boards of every design, DEVKIT_SETS sets of parts per variant), in two
options.

  option_a_pcbway_smt/   PCBWay makes the boards and fits the SMD parts (turnkey): per board the Gerbers, the
                         assembly BOM and centroid (SMD parts only), the assembly / fab drawings; the parts you solder
                         yourself (THT parts, the rockers, the mechanical parts) as DigiKey / Mouser lists.
  option_b_self_solder/  PCBWay makes bare boards (stencils optional); every part as DigiKey / Mouser lists.

Usage: python3 pcb/tools/order_pcbway.py [DEVKIT_SETS]   (default 4; needs kicad-cli and pcbnew)
Writes pcb/order/pcbway/ (and its README.md) from the boards' KiCad files, their part tables and fab packs. Boards
whose design is not confirmed yet (ring board and EU cap board: CN2; cover flex: positions REF / MEASURE) are packed
as fit-test prototypes: their Gerbers are exported here (not into the fab packs) and named _PROTOTYPE.
"""
import csv
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "pcb" / "order" / "pcbway"
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "pcb" / "sensor" / "tools"))
import order_bom  # noqa: E402
import sensor_parts as sp  # noqa: E402

MIN_PCB = 5                                   # PCBWay's minimum quantity per design
RIGID = "F.Cu,B.Cu,F.Mask,B.Mask,F.Paste,F.Silkscreen,B.Silkscreen,Edge.Cuts"
CN2_PROTO = ("FIT-TEST PROTOTYPE: J2 is the Molex 55909-2474 plug for the MSR-2's CN2 (D-82) on Molex's land "
             "pattern (D-89), but its pin 1 and contact map are placeholders until Apollo's pinout is in hand: the "
             "MSR-2's signals will not line up. PCBWay does not fit J2")
# name, KiCad board, fab pack (None: export here), order_bom.tables() keys it serves (the first gives the part
# table), finish, order notes, prototype reason (None: ready), Gerber layers for a prototype
BOARDS = [
    dict(name="wiring_board", pcb="pcb/kicad/wiring_board.kicad_pcb", fab="pcb/fab", tables=[("NA", "wiring board")],
         finish="HASL lead-free or ENIG",
         notes=["Routed isolation slot in the outline (Edge.Cuts), 5 mm wide from the bottom edge up under PS1: "
                "do not omit", "Copper weight 1 oz as designed; 2 oz is the option under thermal review "
                "(pcb/fab/README.md)", "Four 3.2 mm unplated mounting holes",
                "Laminate: high-CTI FR4, CTI >= 600 V (PLC 0, IEC 60664-1 material group I): the mains spacing targets assume it (D-102)"]),
    dict(name="riser_board", pcb="pcb/sensor/kicad/riser_board.kicad_pcb", fab="pcb/sensor/fab/riser_board",
         tables=[("NA", "riser")], finish="ENIG",
         notes=["0.8 mm FR4", "Two plated 2.2 mm holes for the M2 screws (P1, P2) and plated 1.2 mm holes for the "
                "spring pins' pegs", "Small board: let PCBWay panelize it for assembly"]),
    dict(name="eu_mains_board", pcb="pcb/eu/kicad/eu_mains_board.kicad_pcb", fab="pcb/eu/fab/eu_mains_board",
         tables=[("EU", "mains board")], finish="HASL lead-free or ENIG",
         notes=["Routed relief slot under the PSU in the outline (Edge.Cuts): do not omit",
                "Mains board: do the review in pcb/eu/fab/README.md before ordering",
                "Laminate: high-CTI FR4, CTI >= 600 V (PLC 0, IEC 60664-1 material group I): the mains spacing targets assume it (D-102)"]),
    dict(name="eu_5v_board", pcb="pcb/eu/kicad/eu_5v_board.kicad_pcb", fab="pcb/eu/fab/eu_5v_board",
         tables=[("EU", "5 V board")], finish="ENIG", notes=["Plated 1.2 mm holes for the spring pins' pegs"]),
    dict(name="ring_board", pcb="pcb/sensor/kicad/ring_board.kicad_pcb", fab=None, tables=[("NA", "ring board")],
         finish="ENIG", proto=CN2_PROTO, layers=RIGID, skip={"J2"},
         notes=["Copper keeps 8 mm from the box opening (do not let PCBWay add copper fill there)",
                "Fit test: outline, crush-rib window, spacers H1-H3, SHT40, FFC connector J1; microphone MK1 "
                "and the ADAU7002 U2 (WLCSP 0.4 mm pitch: order this board with PCBWay assembly, option A, either way)"]),
    dict(name="eu_cap_board", pcb="pcb/sensor/kicad/eu_cap_board.kicad_pcb", fab=None, tables=[("EU", "cap board")],
         finish="ENIG", proto=CN2_PROTO, layers=RIGID, skip={"J2"},
         notes=["Closed snap windows at the corners (routed cut-outs inside the outline): do not omit",
                "Fit test: outline, snap windows, screws, spacers H5-H7, SHT40, sensor pin pads; microphone MK1 "
                "and the ADAU7002 U2 (WLCSP 0.4 mm pitch: order this board with PCBWay assembly, option A, either way)"]),
    dict(name="cover_flex", pcb="pcb/sensor/kicad/cover_flex.kicad_pcb", fab=None,
         tables=[("NA", "cover flex"), ("EU", "cover flex")], finish="ENIG",
         proto=("FIT-TEST PROTOTYPE: pad, contact and regulator positions come from photos and drawings (REF / "
                "MEASURE) until measured on a remote"),
         layers="F.Cu,F.Mask,F.Paste,F.Silkscreen,B.Silkscreen,Edge.Cuts,User.1",
         notes=["FLEX PCB: one copper layer (F.Cu), polyimide, about 0.12 mm thick without stiffeners; coverlay on "
                "F.Mask openings", f"FR4 stiffeners on the non-copper side: {sp.BC_END_T} mm behind the end section, "
                f"{sp.BC_PAD_STIFF_T} mm on the pad and regulator sections; outlines on the User_1 Gerber and the fab "
                "drawing", "One 90 deg bend at the marked line, copper outside: no stiffener across it"]),
]
# fitted by hand in both options: the rocker snaps into the printed insert / cap before it is soldered (D-26)
HAND = {"S1": "rocker: snapped into the printed insert / cap first, then soldered by hand"}


def board_info(pcb_path):
    """Size, copper layers, thickness and which footprints are SMD."""
    b = pcbnew.LoadBoard(str(pcb_path))
    bb = b.GetBoardEdgesBoundingBox()
    smd = {f.GetReference(): bool(f.GetAttributes() & pcbnew.FP_SMD) for f in b.GetFootprints()}
    return dict(w=bb.GetWidth() / 1e6, h=bb.GetHeight() / 1e6, layers=b.GetCopperLayerCount(),
                t=b.GetDesignSettings().GetBoardThickness() / 1e6, smd=smd)


def centroid(pcb_path, refs):
    """PCBWay centroid rows (Designator, Mid X, Mid Y, Layer, Rotation) for refs, from kicad-cli with the Gerbers'
    origin (the drill / aux origin)."""
    with tempfile.TemporaryDirectory() as t:
        pos = Path(t) / "pos.csv"
        subprocess.run(["kicad-cli", "pcb", "export", "pos", str(pcb_path), "-o", str(pos), "--format", "csv",
                        "--units", "mm", "--side", "both", "--use-drill-file-origin"], check=True,
                       capture_output=True)
        rows = list(csv.DictReader(pos.open()))
    return [(r["Ref"], f'{float(r["PosX"]):.4f}mm', f'{float(r["PosY"]):.4f}mm',
             "Top" if r["Side"] == "top" else "Bottom", f'{float(r["Rot"]):.1f}') for r in rows if r["Ref"] in refs]


def part_table(key):
    return next(parts for variant, board, parts in order_bom.tables() if (variant, board) == key)


def fitted_by_pcbway(info, parts, skip=()):
    """SMD parts with a part number, not hand-fitted or on a placeholder footprint: PCBWay places these in option A."""
    return [r for r, p in parts.items() if info["smd"].get(r) and p.get("in_bom", True) and p.get("mpn")
            and p["mpn"] != "TBD" and r not in HAND and r not in skip]


def write_assembly(bd, parts, refs, folder):
    with (folder / f'{bd["name"]}_pcbway_bom.csv').open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Item #", "Designator", "Qty", "Manufacturer", "Mfg Part #", "Description / Value",
                    "Package/Footprint", "Type", "Your Instructions / Notes"])
        groups = {}
        for r in refs:
            p = parts[r]
            mfr, mpn, desc = p["mfr"], p["mpn"], p.get("desc", "")
            if mpn in order_bom.SUBST:
                mfr, mpn, desc = order_bom.SUBST[mpn]
            groups.setdefault(mpn, dict(mfr=mfr, desc=f'{p.get("value", "")} - {order_bom.short(desc)}',
                                        fp=p["fp"], refs=[]))["refs"].append(r)
        for i, (mpn, g) in enumerate(groups.items(), 1):
            w.writerow([i, ",".join(g["refs"]), len(g["refs"]), g["mfr"], mpn, g["desc"], g["fp"], "SMD",
                        "Source this MPN exactly" if g["mfr"] != "any" else ""])
    with (folder / f'{bd["name"]}_pcbway_centroid.csv').open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        w.writerows(centroid(ROOT / bd["pcb"], set(refs)))


def export_prototype(bd, folder, drawing):
    """Gerbers, drills (and the fab drawing) of an unconfirmed board, exported as build.sh does, named _PROTOTYPE."""
    pcb = ROOT / bd["pcb"]
    name = f'{bd["name"]}_{sp.REV}_PROTOTYPE'
    with tempfile.TemporaryDirectory() as t:
        g = Path(t)
        subprocess.run(["kicad-cli", "pcb", "export", "gerbers", "-o", f"{g}/", "--use-drill-file-origin", "--layers",
                        bd["layers"], "--subtract-soldermask", "--no-x2", str(pcb)], check=True, capture_output=True)
        subprocess.run(["kicad-cli", "pcb", "export", "drill", "-o", f"{g}/", "--format", "excellon", "--drill-origin",
                        "plot", "--excellon-units", "mm", "--excellon-separate-th", "--generate-map", "--map-format",
                        "gerberx2", str(pcb)], check=True, capture_output=True)
        shutil.make_archive(str(folder / f"{name}_gerbers"), "zip", g)
    if drawing:
        subprocess.run(["kicad-cli", "pcb", "export", "pdf", "-o", str(folder / f"{name}_fab.pdf"), "--mode-single",
                        "--layers", f'{bd["layers"]},Cmts.User,User.1', "--include-border-title", str(pcb)],
                       check=True, capture_output=True)
    return f"{name}_gerbers.zip"


def copy_fab(bd, folder, drawing):
    if bd["fab"] is None:
        return export_prototype(bd, folder, drawing)
    fab = ROOT / bd["fab"]
    zips = sorted(fab.glob("*_gerbers.zip"))
    if not zips:
        sys.exit(f'{bd["name"]}: no Gerber zip in {fab}: run make pcb')
    shutil.copy(zips[0], folder / zips[0].name)
    if drawing:
        for pdf in sorted(fab.glob("*_assembly_*.pdf")) + sorted(fab.glob("*_fab.pdf")):
            shutil.copy(pdf, folder / pdf.name)
    return zips[0].name


def main():
    devkit = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    plates = {"NA": devkit, "EU": devkit}                # a devkit per variant: MIN_PCB boards, devkit sets of parts
    if OUT.exists():
        shutil.rmtree(OUT)
    a, b = OUT / "option_a_pcbway_smt", OUT / "option_b_self_solder"
    rows, by_pcbway = [], set()
    for bd in BOARDS:
        info = board_info(ROOT / bd["pcb"])
        parts = part_table(bd["tables"][0])
        need = sum(plates[v] for v, _ in bd["tables"])
        refs = fitted_by_pcbway(info, parts, bd.get("skip", ()))
        by_pcbway |= {(key, r) for key in bd["tables"] for r in refs}
        for opt, assembly in ((a, True), (b, False)):
            folder = opt / bd["name"]
            folder.mkdir(parents=True)
            gz = copy_fab(bd, folder, assembly or bd.get("proto"))
            if assembly:
                write_assembly(bd, parts, refs, folder)
        hand = [r for r, p in parts.items() if p.get("in_bom", True) and p.get("mpn") and p["mpn"] != "TBD"
                and r not in refs and r not in bd.get("skip", ())]
        open_ = [r for r, p in parts.items() if p.get("mpn") == "TBD" or r in bd.get("skip", ())]
        rows.append(dict(bd=bd, info=info, need=need, qty=max(MIN_PCB, need), refs=refs, hand=hand, open=open_,
                         gz=gz))
    # parts lists for the boards packed here and the parts not on a board; option A without what PCBWay fits
    packed = {key for bd in BOARDS for key in bd["tables"]} | {("NA", "mechanical"), ("EU", "mechanical")}
    for opt, keep in ((a, lambda v, bdn, r: (v, bdn) in packed and ((v, bdn), r) not in by_pcbway),
                      (b, lambda v, bdn, r: (v, bdn) in packed)):
        lines, _ = order_bom.collect(plates, keep)
        order_bom.write("parts", lines, plates, out=opt)
    write_readme(rows, plates)


def write_readme(rows, plates):
    L = ["# PCBWay order", "",
         f"Generated by `make order` (`pcb/tools/order_pcbway.py`): a devkit of each variant, {MIN_PCB} PCBs of "
         f"every design (PCBWay's minimum; more where both variants use the board) and {plates['NA']} sets of parts "
         f"per variant (`make order DEVKIT_SETS=…`), in two options:", "",
         "- **Option A** (`option_a_pcbway_smt/`): PCBWay makes the boards and fits the SMD parts (turnkey, they "
         "source the parts). You solder the THT parts and the rockers.",
         "- **Option B** (`option_b_self_solder/`): PCBWay makes bare boards; you buy every part and solder "
         "everything.", "",
         "Do the human reviews in `pcb/fab/README.md` and `pcb/eu/fab/README.md` (fuse rating, isolation, "
         "thermal, approvals) before ordering the mains boards. Nothing here is a compliance claim.", "",
         "**Prototypes.** The ring board, the EU cap board and the back cover flex are not confirmed yet; their "
         "files are named `_PROTOTYPE` and are for fit tests only:", ""]
    for r in rows:
        if r["bd"].get("proto"):
            L.append(f'- {r["bd"]["name"]}: {r["bd"]["proto"]}.')
    L += ["", "## Boards", "",
          "| Board | Plates | PCBs to order | Size | Copper / thickness | Finish | PCBWay fits (option A) | You fit (option A) |",
          "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in rows:
        bd, i = r["bd"], r["info"]
        flag = " (prototype)" if bd.get("proto") else ""
        cu = "1 layer flex" if bd["name"] == "cover_flex" else f'{i["layers"]} layers FR4'
        variants = ", ".join(v for v, _ in bd["tables"])
        hand = ", ".join(r["hand"]) or "-"
        if r["open"]:
            hand += f' (not fitted: {", ".join(r["open"])})'
        L.append(f'| {bd["name"]}{flag} | {r["need"]} ({variants}) | {r["qty"]} (assemble {r["need"]}) | '
                 f'{i["w"]:.1f} × {i["h"]:.1f} mm | {cu} / {i["t"]:.2f} mm | {bd["finish"]} | '
                 f'{", ".join(r["refs"]) or "-"} | {hand} |')
    L += ["", "Order settings common to the rigid boards: FR4 TG150 or standard (the two mains boards: high-CTI FR4, "
          "see their notes), 1 oz copper (see the wiring board's note), green solder mask and white silkscreen both sides, no impedance control, no V-cut. Gerbers are "
          "RS-274X with Excellon drills in mm; Gerbers, drills and centroid share the board's drill / aux origin.", "",
          "Per board (add to the order remarks):", ""]
    for r in rows:
        L.append(f'- **{r["bd"]["name"]}** (`{r["gz"]}`): ' + "; ".join(r["bd"]["notes"]) + ".")
    L += ["", "## Option A: PCB + SMD assembly by PCBWay", "",
          "Per board in `option_a_pcbway_smt/<board>/`: the Gerber zip, `<board>_pcbway_bom.csv`, "
          "`<board>_pcbway_centroid.csv`, the assembly or fab drawings.", "",
          "1. pcbway.com → PCB Assembly → Turnkey (the cover flex: Flex PCB with assembly). Upload the Gerber zip "
          "and fill the board settings from the table.",
          "2. Assembly: SMT only, the sides the centroid lists; "
          "the quantity to assemble is the plate count (column \"PCBs to order\").",
          "3. Upload the BOM and the centroid. The BOM lists only the SMD parts PCBWay fits; THT parts, the "
          "rockers and the prototypes' placeholder CN2 mates are not in it (do not fit). Safety-critical parts "
          "(F1, RV1) must be the listed MPN: no substitutes without review.",
          "4. Add the board's notes above to the order remarks.",
          "5. Buy the rest from DigiKey or Mouser: `parts_digikey.csv` / `parts_mouser.csv` (and the `_rest_` file "
          "for parts the other distributor does not carry), imported as described in `pcb/order/README.md`. "
          "They hold the THT parts, the rockers and the parts not on a board (NA: studs, standoffs, FFC; EU: the PE "
          "lever connector).", "",
          "## Option B: bare boards, you solder", "",
          "Per board in `option_b_self_solder/<board>/`: the Gerber zip (the prototypes also their fab drawing).", "",
          "1. pcbway.com → PCB Instant Quote (the cover flex: Flex PCB). Upload the Gerber zip, fill the board "
          "settings from the table.",
          "2. Optional: add a stencil (framework-less, top) for the boards with SMD parts: the paste layers are in "
          "the Gerbers. The microphone (LGA), the SHT40 (DFN), the WA-SMSI posts and spacers and the P70 spring "
          "pins are reflow parts (hot plate or hot air with paste). The ADAU7002 (WLCSP-8, 0.4 mm pitch) is not a "
          "hand part: order the ring board and the EU cap board with PCBWay assembly (option A) even here.",
          "3. Buy every part: `parts_digikey.csv` / `parts_mouser.csv` (and the `_rest_` file).", "",
          "## Quantities", "",
          f"Part quantities are exactly {plates['NA']} sets per variant, no spares (`pcb/order/README.md`). "
          f"PCBWay's minimum is {MIN_PCB} boards per design; the spare board costs little and covers a failed "
          "assembly.", ""]
    (OUT / "README.md").write_text("\n".join(L))
    print("wrote", OUT / "README.md")


if __name__ == "__main__":
    main()
