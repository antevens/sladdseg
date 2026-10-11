"""Distributor order lists (DigiKey BOM Manager, Mouser BOM Import): one plate of each variant and a devkit.

Usage: python3 pcb/tools/order_bom.py [DEVKIT_SETS]   (default 4)
Writes pcb/order/{unit_na,unit_eu,devkit_na,devkit_eu}_{digikey,mouser}.csv (and the _rest_ files for parts one
distributor does not carry) from the boards' part tables (parts.py, eu_parts.py, sensor_parts.py,
eu_capboard_parts.py) and the parts not on a board (EXTRA_NA, EXTRA_EU). Lines merge by MPN; the quantity is
exactly the per-plate count times the plates (no spares). Parts without an MPN yet are listed on stdout.
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
    "C1206C226M4PACTU": "399-12290-1-ND",             # DigiKey API 2026-10-11 (D-95)
    "FH12-6S-0.5SH(55)": "HFJ106CT-ND",
    "S7081-42R": "952-1734-1-ND",
    "SHT40-AD1B-R2": "1649-SHT40-AD1B-R2CT-ND",
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
    "221-412": "2946-221-412-ND",              # DigiKey API 2026-10-11 (bulk)
    "ZPI03S0500WC": "3388-ZPI03S0500WC-ND",    # DigiKey API 2026-10-11 (tube, 142; D-100)
    "ADAU7002ACBZ-R7": "505-ADAU7002ACBZ-R7CT-ND",   # cut tape (DigiKey cart, API 2026-10-11)
    "GRM3195C1H104JA05D": "490-GRM3195C1H104JA05DCT-ND",   # DigiKey API 2026-10-11 (D-98)
    "05-06-A-0152-A-4-06-4-G": "2073-05-06-A-0152-A-4-06-4-G-ND",   # DigiKey API 2026-10-11 (D-98)
}
# Mouser's own numbers where its BOM import does not match the MPN (search results 2026-10-09); None: not
# carried by Mouser (import reported no match), those go to <name>_mouser_rest_digikey.csv
MOUSER = {
    "1802.2504": "979-1802.2504",               # in stock 2026-10-11 (01802.2504-03: non-stocked)
    "TSM-102-02-L-SV": "",                     # TODO distributor PN (imports by MPN until then)
    "2604-3102": None,
    "P70-2200045": None,
    "ADAU7002ACBZ-R7": None,                   # Mouser: not restocked once sold out (human, 2026-10-11)
}
# parts ordered as their second source on the same footprint, per variant (D-97): both plates take the E-Switch
# RA412C1100 (UL/cUL 10 A 250 VAC, ENEC 10(4) A 250 V~; at DigiKey, a fraction of the Marquardt's price)
_RA4 = ("E-Switch", "RA412C1100", "Rocker switch DPST, 4.8 mm tabs into the slots, UL/cUL 16 A 125 VAC and 10 A 250 VAC, "
        "ENEC 10(4) A 250 V~ (second source, D-88, D-97)")
PREFERRED = {"NA": {"1802.2504": _RA4}, "EU": {"1802.2504": _RA4}}
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
    "W1": dict(mfr="GCT", mpn="05-06-A-0152-A-4-06-4-G", fp="FFC", desc="FFC 0.5 mm, 6 contacts, 152 mm, Type 1: "
               "wiring board J2 to the ring board J1"),
}
# EU parts that are not on a board (D-94): the lights' protective earth, joined in the box
EXTRA_EU = {
    "PE1": dict(mfr="WAGO", mpn="221-412", fp="lever connector", desc="Lever splicing connector, 2 conductors, "
                "0.2-4 mm2: PE in from the supply to PE out to the lights, in the box (no PE on the boards)"),
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
            ("EU", "cover flex", sen.COVER_PARTS), ("EU", "mechanical", EXTRA_EU)]


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
            if mpn in PREFERRED.get(variant, {}):
                mfr, mpn, desc = PREFERRED[variant][mpn]
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


def write(name, lines, plates, out=OUT, spares=False):
    rows = []
    for mpn, line in lines.items():
        q = quantity(line, plates) if spares else sum(n * plates[v] for v, n in line["per"].items())
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
    devkit = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    OUT.mkdir(parents=True, exist_ok=True)
    open_all = set()
    for name, plates in (("unit_na", {"NA": 1}), ("unit_eu", {"EU": 1}), ("devkit_na", {"NA": devkit}),
                         ("devkit_eu", {"EU": devkit})):
        lines, open_parts = collect(plates)
        write(name, lines, plates)
        open_all.update(open_parts)
    print(f"unit: 1 plate each; devkit: {devkit} sets of parts per variant")
    for o in sorted(open_all):
        print("not in the lists (no part yet):", o)
    for v, items in LOCAL.items():
        for o in items:
            print(f"not in the lists (buy locally), {v}:", o)


if __name__ == "__main__":
    main()
