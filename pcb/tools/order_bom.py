"""Distributor order lists (DigiKey BOM Manager, Mouser BOM Import) for hand-soldered test plates.

Usage: python3 pcb/tools/order_bom.py [NA_PLATES] [EU_PLATES]   (defaults 3 and 2)
Writes pcb/order/{na,eu,all}_{digikey,mouser}.csv from the boards' part tables (parts.py, eu_parts.py,
sensor_parts.py, eu_capboard_parts.py) and the NA mechanical parts (EXTRA_NA). Lines merge by MPN; the quantity is the per-plate count times the plates plus
spares. Parts without an MPN yet (the CN2 plug) are listed on stdout, not in the files.
"""
import csv
import math
import sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "pcb" / "order"

# generic passives ("any") ordered as these parts
SUBST = {
    "0402 X7R 100 nF 16 V": ("Murata", "GRM155R71C104KA88J", "Ceramic 100 nF 16 V X7R 0402"),
    "0402 1% 100 kOhm": ("Yageo", "RC0402FR-07100KL", "Resistor 100 kOhm 1 % 0402"),
}
# hand-soldered small parts: half again as spares (at least 2); 0402 passives rounded up to tens
# DigiKey part numbers, cut tape where the part comes on tape (the import otherwise picks a full reel or rejects
# an MPN sold in several packagings); from DigiKey's listings and its -1-ND / CT-ND cut-tape convention,
# 2026-10-09. None: not carried by DigiKey (import: invalid part number), those go to
# <name>_digikey_rest_mouser.csv. MPNs not listed import as they are.
DIGIKEY = {
    "1802.2504": None,
    "IRM-03-5": "1866-3020-ND",
    "B72660M0271K093": "495-1467-1-ND",
    "CL31A226KPHNNNE": "1276-1287-1-ND",
    "FH12-6S-0.5SH(55)": "HFJ106CT-ND",
    "S7081-42R": "952-1734-1-ND",
    "SHT45-AD1B-R2": "1649-SHT45-AD1B-R2CT-ND",
    "GRM155R71C104KA88J": "490-6328-1-ND",             # KA88D: 0 at DigiKey (API 2026-10-11)
    "SPK0641HT4H-1": "6017-SPK0641HT4H-1CT-ND",           # DigiKey listing, 2026-10-11
    "RC0402FR-07100KL": "311-100KLRCT-ND",
    "TLV75533PDBVR": "296-50411-1-ND",
    "TSM-102-02-L-SV": "SAM10268-ND",          # DigiKey API 2026-10-11 (bulk)
    "SSW-102-01-G-S": "612-SSW-102-01-G-S-ND",
    "P70-2200045": "952-3124-ND",
    "55909-2474": "WM3787CT-ND",               # DigiKey lists it as 0559092474 (API 2026-10-11)
    "25503": "36-25503-ND",                    # bare 25503 is ambiguous at DigiKey (API 2026-10-11)
    "RA412C1100": "EG5628-ND",                 # DigiKey API 2026-10-11 (584, 9 wk)
    "ADAU7002ACBZ-R7": "505-ADAU7002ACBZ-R7CT-ND",   # cut tape (DigiKey cart, API 2026-10-11)
    "C1206C104J3GACTU": "399-C1206C104J3GACTUCT-ND", # cut tape (DigiKey cart, API 2026-10-11)
}
# Mouser's own numbers where its BOM import does not match the MPN (search results 2026-10-09); None: not
# carried by Mouser (import reported no match), those go to <name>_mouser_rest_digikey.csv
MOUSER = {
    "TMPS 03-105": "495-TMPS03-105",
    "1802.2504": "979-1802.2504",               # in stock 2026-10-11 (01802.2504-03: non-stocked)
    "TSM-102-02-L-SV": "",                     # TODO distributor PN (imports by MPN until then)
    "2604-3102": None,
    "P70-2200045": None,
}
# second sources on the same footprint, used by distributors.py push for a distributor that does not carry the part
ALTERNATES = {"1802.2504": ("E-Switch", "RA412C1100", "Rocker switch DPST, 4.8 mm tabs into the slots, ENEC 10(4) A 250 V~, "
                            "UL/cUL 16 A 125 VAC (second source, D-88)")}
SMALL = ("0402", "1206", "SOT-23", "DFN", "SPK0641", "WLCSP", "S7081", "P70-", "FH12", "UMT250", "CU4032", "SMD", "WA-SMSI",
         "WA-SBRIE")
# NA parts that are not on a board (D-50, D-57): the spacer posts' studs, the board standoffs and the 5 V FFC
EXTRA_NA = {
    "ST1": dict(mfr="Wurth Elektronik", mpn="971100244", fp="WA-SBRIE", desc="Brass spacer stud M2 male-female, 10 mm, "
                "4 mm hex: spacer post, wiring board P1 to the riser"),
    "ST2": dict(mfr="Wurth Elektronik", mpn="971100244", fp="WA-SBRIE", desc="Brass spacer stud M2 male-female, 10 mm, "
                "4 mm hex: spacer post, wiring board P2 to the riser"),
    **{f"SO{i}": dict(mfr="Keystone", mpn="25503", fp="standoff", desc="Nylon M3 male-female hex standoff, 15 mm, "
                      "5.0 mm hex: wiring board to the insert (D-57)") for i in range(1, 5)},
    "W1": dict(mfr="Wurth Elektronik", mpn="687606152002", fp="FFC", desc="FFC 0.5 mm, 6 contacts, 152 mm, Type 1: "
               "wiring board J2 to the ring board J1"),
}
# bought locally: no MPN in the lists (printed on stdout)
LOCAL = {"NA": ["M2 x 5 pan head screw ISO 7045, steel: 2 per plate (riser onto the spacer posts)",
                "heatshrink 6 mm (2:1), 15 mm: 2 per plate (over the spacer posts)",
                "M3 x 8 slotted pan head screw ISO 1580, nylon: 4 per plate (wiring board onto the standoffs)"],
         "EU": ["M2 x 6 thread-forming screw for plastics: 4 per plate (cap board into the carrier)"]}


def tables():
    """(variant, board, part table) for every board of each variant."""
    def load(path, mod):
        sys.path.insert(0, str(ROOT / path))
        try:
            return __import__(mod)
        finally:
            sys.path.pop(0)
    na, eu = load("pcb/tools", "parts"), load("pcb/eu/tools", "eu_parts")
    sen, euc = load("pcb/sensor/tools", "sensor_parts"), load("pcb/sensor/tools", "eu_capboard_parts")
    return [("NA", "wiring board", na.PARTS), ("NA", "ring board", sen.RING_PARTS),
            ("NA", "riser", sen.RISER_PARTS), ("NA", "cover flex", sen.COVER_PARTS),
            ("NA", "mechanical", EXTRA_NA),
            ("EU", "mains board", eu.MAINS_PARTS), ("EU", "5 V board", eu.LV_PARTS),
            ("EU", "cap board", euc.CAPBOARD_PARTS),
            ("EU", "cover flex", sen.COVER_PARTS)]


def short(desc, n=90):
    """First sentence of a part description, without remarks in brackets, cut at a word boundary to n characters."""
    d = desc.split(". ")[0].split(": ")[0].split(" (")[0]
    return d if len(d) <= n else d[:n].rsplit(" ", 1)[0]


def collect(plates, keep=None):
    """MPN -> line (manufacturer, description, per-plate count per variant, refs); open parts listed apart.
    keep(variant, board, ref): only the parts it accepts (all when None)."""
    lines, open_parts = OrderedDict(), []
    for variant, board, parts in tables():
        if not plates.get(variant):
            continue
        for ref, p in parts.items():
            if not p.get("in_bom", True) or not p.get("mpn") or (keep and not keep(variant, board, ref)):
                continue
            mfr, mpn, desc = p["mfr"], p["mpn"], p.get("desc", "")
            if mpn == "TBD":
                open_parts.append(f"{variant} {board} {ref}: {desc}")
                continue
            if mpn in SUBST:
                mfr, mpn, desc = SUBST[mpn]
            line = lines.setdefault(mpn, dict(mfr=mfr, desc=short(desc), fp=p["fp"], per={}, refs=[]))
            line["per"][variant] = line["per"].get(variant, 0) + 1
            line["refs"].append(f"{variant} {board} {ref}")
    return lines, open_parts


def quantity(line, plates):
    need = sum(n * plates[v] for v, n in line["per"].items())
    if any(k in line["fp"] for k in SMALL):
        q = need + max(2, math.ceil(need / 2))
        return math.ceil(q / 10) * 10 if "0402" in line["fp"] else q
    return need + 1


def write(name, lines, plates, out=OUT):
    rows = []
    for mpn, line in lines.items():
        q = quantity(line, plates)
        per = ", ".join(f"{n}/plate {v}" for v, n in line["per"].items())
        ref = "WP " + " ".join(sorted({r.split()[0] for r in line["refs"]})) + " " + line["refs"][0].split()[-1]
        rows.append((q, mpn, line["mfr"], ref[:48], f'{line["desc"]} ({per}; {"; ".join(line["refs"])})'))
    dk_head = ["Digi-Key Part Number", "Manufacturer Part Number", "Manufacturer", "Quantity", "Customer Reference",
               "Description"]
    ms_head = ["Mouser Part Number", "Mfr Part Number", "Manufacturer", "Quantity", "Customer Part Number",
               "Description"]
    files = []
    for dist, table, head in (("digikey", DIGIKEY, dk_head), ("mouser", MOUSER, ms_head)):
        other, other_table, other_head = (("mouser", MOUSER, ms_head) if dist == "digikey"
                                          else ("digikey", DIGIKEY, dk_head))
        here = [r for r in rows if table.get(r[1], "") is not None]
        rest = [r for r in rows if table.get(r[1], "") is None]
        with (out / f"{name}_{dist}.csv").open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(head)
            w.writerows((table.get(mpn, ""), mpn, mfr, q, ref, desc) for q, mpn, mfr, ref, desc in here)
        files.append(f"_{dist}.csv ({len(here)})")
        rest_path = out / f"{name}_{dist}_rest_{other}.csv"
        if rest:
            with rest_path.open("w", newline="") as f:
                w = csv.writer(f)
                w.writerow(other_head)
                w.writerows((other_table.get(mpn, ""), mpn, mfr, q, ref, desc) for q, mpn, mfr, ref, desc in rest)
            files.append(f"_{dist}_rest_{other}.csv ({len(rest)}: not at {dist})")
        elif rest_path.exists():
            rest_path.unlink()
    print(f"wrote {out / name}: " + ", ".join(files))


def main():
    na = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    eu = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    OUT.mkdir(parents=True, exist_ok=True)
    for name, plates in (("na", {"NA": na}), ("eu", {"EU": eu}), ("all", {"NA": na, "EU": eu})):
        lines, open_parts = collect(plates)
        write(name, lines, plates)
    print(f"plates: NA {na}, EU {eu}")
    for o in sorted(set(open_parts)):
        print("not in the lists (no part yet):", o)
    for v, items in LOCAL.items():
        for o in items:
            print(f"not in the lists (buy locally), {v}:", o)


if __name__ == "__main__":
    main()
