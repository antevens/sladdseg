"""PCBWay order packs: the boards ready to order, in two options.

  option_a_pcbway_smt/   PCBWay makes the boards and fits the SMD parts (turnkey): per board the Gerbers, the
                         assembly BOM and centroid (SMD parts only), the assembly drawings; the parts you solder
                         yourself (THT parts, the rockers, the mechanical parts) as DigiKey / Mouser lists.
  option_b_self_solder/  PCBWay makes bare boards (stencils optional); every part as DigiKey / Mouser lists.

Usage: python3 pcb/tools/order_pcbway.py [NA_PLATES] [EU_PLATES]   (defaults 3 and 2; needs kicad-cli and pcbnew)
Writes pcb/order/pcbway/ (and its README.md) from the boards' KiCad files, their part tables and fab packs. Boards
whose design is not confirmed yet (ring board and EU cap board: CN2; cover flex: positions REF / MEASURE) are listed
in the README, not packed.
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
import order_bom  # noqa: E402

MIN_PCB = 5                                   # PCBWay's minimum quantity per design
# name, variants using it, KiCad board, fab pack, (variant, board) in order_bom.tables(), order notes
BOARDS = [
    dict(name="wiring_board", variants=("NA",), pcb="pcb/kicad/wiring_board.kicad_pcb", fab="pcb/fab",
         table=("NA", "wiring board"), finish="HASL lead-free or ENIG",
         notes=["Routed isolation slot in the outline (Edge.Cuts), 5 mm wide from the bottom edge up under PS1: "
                "do not omit", "Copper weight 1 oz as designed; 2 oz is the option under thermal review "
                "(pcb/fab/README.md)", "Four 3.2 mm unplated mounting holes"]),
    dict(name="riser_board", variants=("NA",), pcb="pcb/sensor/kicad/riser_board.kicad_pcb",
         fab="pcb/sensor/fab/riser_board", table=("NA", "riser"), finish="ENIG",
         notes=["0.8 mm FR4", "Two plated 2.2 mm holes for the M2 screws (P1, P2) and plated 1.2 mm holes for the "
                "spring pins' pegs", "Small board: let PCBWay panelize it for assembly"]),
    dict(name="mic_carrier", variants=("NA", "EU"), pcb="pcb/sensor/kicad/mic_carrier.kicad_pcb",
         fab="pcb/sensor/fab/mic_carrier", table=("NA", "mic carrier"), finish="ENIG",
         notes=["0.8 mm FR4", "Castellated (half-plated) holes on two edges: select castellated holes",
                "Very small board (about 7 x 6 mm): let PCBWay panelize it with rails; the microphone is a "
                "bottom-port LGA, ENIG for flat pads"]),
    dict(name="eu_mains_board", variants=("EU",), pcb="pcb/eu/kicad/eu_mains_board.kicad_pcb",
         fab="pcb/eu/fab/eu_mains_board", table=("EU", "mains board"), finish="HASL lead-free or ENIG",
         notes=["Routed relief slot under the PSU in the outline (Edge.Cuts): do not omit",
                "Mains board: do the review in pcb/eu/fab/README.md before ordering"]),
    dict(name="eu_5v_board", variants=("EU",), pcb="pcb/eu/kicad/eu_5v_board.kicad_pcb",
         fab="pcb/eu/fab/eu_5v_board", table=("EU", "5 V board"), finish="ENIG",
         notes=["Plated 1.2 mm holes for the spring pins' pegs"]),
]
NOT_READY = [("ring board (NA)", "the MSR-2's CN2 plug and contact map are not confirmed (CN2_CONFIRMED)"),
             ("EU cap board", "the MSR-2's CN2 plug and contact map are not confirmed (CN2_CONFIRMED)"),
             ("back cover flex", "its positions are REF / MEASURE until measured on a remote (COVER_CONFIRMED)")]
# fitted by hand in both options: the rocker snaps into the printed insert / cap before it is soldered (D-26)
HAND = {"S1": "rocker: snapped into the printed insert / cap first, then soldered by hand"}


def board_info(pcb_path):
    """Size, copper layers, thickness and per-footprint data (ref -> smd?, layer, x, y, rotation) of a board."""
    b = pcbnew.LoadBoard(str(pcb_path))
    bb = b.GetBoardEdgesBoundingBox()
    fps = {}
    for f in b.GetFootprints():
        fps[f.GetReference()] = bool(f.GetAttributes() & pcbnew.FP_SMD)
    return dict(w=bb.GetWidth() / 1e6, h=bb.GetHeight() / 1e6, layers=b.GetCopperLayerCount(),
                t=b.GetDesignSettings().GetBoardThickness() / 1e6, smd=fps)


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


def fitted_by_pcbway(info, parts):
    """SMD parts with a part number, not hand-fitted: PCBWay places these in option A."""
    return [r for r, p in parts.items() if info["smd"].get(r) and p.get("in_bom", True) and p.get("mpn")
            and p["mpn"] != "TBD" and r not in HAND]


def write_assembly(bd, info, parts, refs, folder):
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


def copy_fab(bd, folder, assembly):
    fab = ROOT / bd["fab"]
    zips = sorted(fab.glob("*_gerbers.zip"))
    if not zips:
        sys.exit(f'{bd["name"]}: no Gerber zip in {fab}: run make pcb')
    shutil.copy(zips[0], folder / zips[0].name)
    if assembly:
        for pdf in sorted(fab.glob("*_assembly_*.pdf")) + sorted(fab.glob("*_fab.pdf")):
            shutil.copy(pdf, folder / pdf.name)
    return zips[0].name


def main():
    plates = {"NA": int(sys.argv[1]) if len(sys.argv) > 1 else 3, "EU": int(sys.argv[2]) if len(sys.argv) > 2 else 2}
    if OUT.exists():
        shutil.rmtree(OUT)
    a, b = OUT / "option_a_pcbway_smt", OUT / "option_b_self_solder"
    rows, pcbway_refs = [], {}
    for bd in BOARDS:
        info = board_info(ROOT / bd["pcb"])
        parts = part_table(bd["table"])
        need = sum(plates[v] for v in bd["variants"])
        refs = fitted_by_pcbway(info, parts)
        pcbway_refs[bd["table"]] = set(refs)
        for opt, assembly in ((a, True), (b, False)):
            folder = opt / bd["name"]
            folder.mkdir(parents=True)
            gz = copy_fab(bd, folder, assembly)
            if assembly:
                write_assembly(bd, info, parts, refs, folder)
        hand = [r for r, p in parts.items() if p.get("in_bom", True) and p.get("mpn") and r not in refs]
        rows.append(dict(bd=bd, info=info, need=need, qty=max(MIN_PCB, need), refs=refs, hand=hand, gz=gz))
    # parts lists: option A without what PCBWay fits; both options only for the boards packed here + NA mechanical
    packed = {bd["table"] for bd in BOARDS} | {("NA", "mechanical")}
    for opt, keep in ((a, lambda v, bdn, r: (v, bdn) in packed and r not in pcbway_refs.get((v, bdn), ())),
                      (b, lambda v, bdn, r: (v, bdn) in packed)):
        lines, _ = order_bom.collect(plates, keep)
        order_bom.write("parts", lines, plates, out=opt)
    write_readme(rows, plates)


def write_readme(rows, plates):
    L = ["# PCBWay order", "",
         f"Generated by `make order` (`pcb/tools/order_pcbway.py`) for {plates['NA']} NA and {plates['EU']} EU "
         "test plates (`make order NA_PLATES=… EU_PLATES=…`). Two options for the same boards:", "",
         "- **Option A** (`option_a_pcbway_smt/`): PCBWay makes the boards and fits the SMD parts (turnkey, they "
         "source the parts). You solder the THT parts and the rockers.",
         "- **Option B** (`option_b_self_solder/`): PCBWay makes bare boards; you buy every part and solder "
         "everything.", "",
         "Do the human reviews in `pcb/fab/README.md` and `pcb/eu/fab/README.md` (fuse rating, isolation, "
         "thermal, approvals) before ordering the mains boards. Nothing here is a compliance claim.", "",
         "## Boards in this order", "",
         "| Board | Plates | PCBs to order | Size | Layers / thickness | Finish | PCBWay fits (option A) | You fit (option A) |",
         "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in rows:
        bd, i = r["bd"], r["info"]
        L.append(f'| {bd["name"]} | {r["need"]} ({", ".join(bd["variants"])}) | {r["qty"]} (assemble {r["need"]}) | '
                 f'{i["w"]:.1f} × {i["h"]:.1f} mm | {i["layers"]} / {i["t"]:.1f} mm FR4 | {bd["finish"]} | '
                 f'{", ".join(r["refs"]) or "-"} | {", ".join(r["hand"]) or "-"} |')
    L += ["", "Order settings common to all boards: FR4 TG150 or standard, 1 oz copper (see the wiring board's note), "
          "green solder mask and white silkscreen both sides, no impedance control, no V-cut; Gerbers are RS-274X "
          "with Excellon drills in mm; Gerbers, drills and centroid share the board's drill / aux origin.", "",
          "Per board:", ""]
    for r in rows:
        L.append(f'- **{r["bd"]["name"]}** (`{r["gz"]}`): ' + "; ".join(r["bd"]["notes"]) + ".")
    L += ["", "## Not in this order", ""]
    for name, why in NOT_READY:
        L.append(f"- {name}: {why}.")
    L += ["", "Their parts are in the plate lists in `pcb/order/` (`make order`).", "",
          "## Option A: PCB + SMD assembly by PCBWay", "",
          "Per board in `option_a_pcbway_smt/<board>/`: `<board>_v…_gerbers.zip`, `<board>_pcbway_bom.csv`, "
          "`<board>_pcbway_centroid.csv`, assembly drawings.", "",
          "1. pcbway.com → PCB Assembly → Turnkey. Upload the Gerber zip and fill the board settings from the table.",
          "2. Assembly: SMT only, top side unless the centroid lists Bottom parts; the quantity to assemble is the "
          "plate count (column \"PCBs to order\").",
          "3. Upload the BOM and the centroid. The BOM lists only the SMD parts PCBWay fits; THT parts and the "
          "rockers are not in it (do not fit). Safety-critical parts (F1, RV1) must be the listed MPN: no "
          "substitutes without review.",
          "4. Add the board's notes above to the order remarks.",
          "5. Buy the rest from DigiKey or Mouser: `parts_digikey.csv` / `parts_mouser.csv` (and the `_rest_` file "
          "for parts the other distributor does not carry), imported as described in `pcb/order/README.md`. "
          "They hold the THT parts, the rockers and the NA mechanical parts (studs, standoffs, FFC).", "",
          "## Option B: bare boards, you solder", "",
          "Per board in `option_b_self_solder/<board>/`: the Gerber zip.", "",
          "1. pcbway.com → PCB Instant Quote. Upload the Gerber zip, fill the board settings from the table.",
          "2. Optional: add a stencil (framework-less, top) for the boards with SMD parts: the paste layers are in "
          "the Gerbers. The mic carrier's bottom-port LGA microphone, the WA-SMSI posts and the P70 spring pins "
          "are reflow parts (hot plate or hot air with paste).",
          "3. Buy every part: `parts_digikey.csv` / `parts_mouser.csv` (and the `_rest_` file).", "",
          "## Quantities", "",
          "Part quantities are per plate times the plates plus spares (rules in `pcb/order/README.md`). PCBWay's "
          f"minimum is {MIN_PCB} boards per design; the spare boards cost little and cover a failed assembly.", ""]
    (OUT / "README.md").write_text("\n".join(L))
    print("wrote", OUT / "README.md")


if __name__ == "__main__":
    main()
