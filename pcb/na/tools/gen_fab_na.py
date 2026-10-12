"""Write the NA mains board's PCBWay BOM and centroid files into pcb/na/fab/na_mains_board/ from parts_na.py.

Usage: python3 gen_fab_na.py POS_CSV   (POS_CSV from `kicad-cli pcb export pos --format csv`)
Parts in DNP are left out of the centroid and listed as not fitted in the BOM.
"""
import csv
import sys
from pathlib import Path

sys.path.insert(1, str(Path(__file__).resolve().parents[2] / "tools"))     # pcb/tools: sexpr, kigen
from parts_na import PARTS, PROJECT, REV

OUT = Path(__file__).resolve().parents[1] / "fab" / PROJECT
# S1 snaps into the printed barrier from the front before it can be soldered (D-26)
DNP = {"S1": "Do not fit. Soldered by hand after the rocker is snapped into the printed barrier"}
NOTES = {
    "F1": "Rating T1A is the designer's choice (Mean Well gives none) - confirm before ordering",
    "PS1": "Safety-critical, do not substitute. Back (B) side, sit flush on the board",
    "J1": "Safety-critical, do not substitute. Back (B) side, wire entries face the board's top edge",
    "RV1": "Safety-critical, do not substitute without review",
}
SIDE = {"F": "Top", "B": "Bottom"}


def side_of(ref, p):
    return "B" if ref == "PS1" else p["pcb"][3]


def write_bom():
    path = OUT / f"{PROJECT}_{REV}_bom.csv"
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Item", "Designator", "Qty", "Manufacturer", "Manufacturer Part Number",
                    "Description/Value", "Package/Footprint", "Layer", "Datasheet", "Notes"])
        for i, (ref, p) in enumerate(PARTS.items(), 1):
            w.writerow([i, ref, 0 if ref in DNP else 1, p["mfr"], p["mpn"], f'{p["value"]} - {p["desc"]}',
                        p["fp"], SIDE[side_of(ref, p)], p["ds"], DNP.get(ref, NOTES.get(ref, ""))])
    print("wrote", path)


def write_centroid(pos_csv):
    path = OUT / f"{PROJECT}_{REV}_centroid.csv"
    with open(pos_csv, newline="") as src, path.open("w", newline="") as dst:
        rows = csv.reader(src)
        w = csv.writer(dst)
        w.writerow(next(rows))
        for row in rows:
            if row and row[0] not in DNP:
                w.writerow(row)
    print("wrote", path)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    write_bom()
    write_centroid(sys.argv[1])


if __name__ == "__main__":
    main()
