"""Print-orientation helpers and mesh export for every printable part.

Run: python export.py -> ../../build/print/<part>.stl (oriented, on the bed, centred)
"""
from pathlib import Path
import trimesh
from build123d import Rot, Pos, export_stl, export_step

OUT = Path(__file__).resolve().parents[2] / "build"

PRINT_ORIENT = {
    "insert": lambda p: p,                          # floor-down: as modelled; supports under the seal lip and the riser pocket (D-68)
    "trim": lambda p: Rot(180, 0, 0) * p,           # face-down
    "insert_plain": lambda p: p,                    # as the insert (D-109)
    "insert_switch": lambda p: p,                   # as the insert (D-122)
    "trim_plain": lambda p: Rot(180, 0, 0) * p,     # face-down (D-109)
    "coupon_pocket_well": lambda p: p,
    "coupon_msr": lambda p: Rot(180, 0, 0) * p,
    "coupon_rocker": lambda p: p,
    "coupon_ribs": lambda p: p,
    "coupon_back_gauges": lambda p: p,              # flat (D-87)
    "coupon_end_gauges": lambda p: p,               # flat (D-101)
    "coupon_shell_gauges": lambda p: p,             # bottom (the round-over's 45 deg point) down (D-101)
    "back_cover": lambda p: p,                      # back down: as modelled (D-35)
    "cap_eu": lambda p: Rot(180, 0, 0) * p,         # face-down (barrier, D-30)
    "trim_eu": lambda p: Rot(180, 0, 0) * p,        # face-down
    "carrier_eu": lambda p: p,                      # bottom down: the rim up, the lip under the cap on the bed (D-71)
    "cap_plain_eu": lambda p: Rot(180, 0, 0) * p,   # as the cap (D-109)
    "cap_switch_eu": lambda p: Rot(180, 0, 0) * p,  # as the cap (D-122)
    "trim_plain_eu": lambda p: Rot(180, 0, 0) * p,  # face-down (D-109)
    "carrier_plain_eu": lambda p: p,                # as the carrier (D-109)
    "testbox_eu": lambda p: p,                      # floor down, open side up (D-76)
    "testbox_plate_eu": lambda p: p,                # flat
    "plate_jig_saw": lambda p: p,                   # floor down (D-52)
}


def on_bed(part):
    bb = part.bounding_box()
    return Pos(-(bb.min.X + bb.max.X) / 2, -(bb.min.Y + bb.max.Y) / 2, -bb.min.Z) * part


def mesh_of(part, tol=0.02):
    import tempfile, os
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, "m.stl")
        export_stl(part, f, tolerance=tol, angular_tolerance=0.1)
        m = trimesh.load(f)
    m.merge_vertices()
    return m


def parts():
    import sys
    import insert, trim, coupons, backcover, plate_jig
    sys.path.insert(0, str(Path(__file__).resolve().parent / "eu"))
    import cap_eu, trim_eu, capboard_eu, testbox_eu
    ins, tr = insert.build(), trim.build()
    return {"insert": ins, "trim": tr,
            "insert_plain": insert.build(plain=True), "trim_plain": trim.build(plain=True),
            "insert_switch": insert.build(switch=True),
            "coupon_pocket_well": coupons.pocket_well(ins),
            "coupon_msr": coupons.msr(tr),
            "coupon_rocker": coupons.rocker_ladder(),
            "coupon_ribs": coupons.ribs(),
            "coupon_back_gauges": coupons.back_gauges(),
            "coupon_end_gauges": coupons.end_gauges(),
            "coupon_shell_gauges": coupons.shell_gauges(),
            "back_cover": backcover.cover(),
            "cap_eu": cap_eu.build(), "trim_eu": trim_eu.build(),
            "carrier_eu": capboard_eu.carrier(),
            "cap_plain_eu": cap_eu.build(plain=True), "trim_plain_eu": trim_eu.build(plain=True),
            "cap_switch_eu": cap_eu.build(switch=True),
            "carrier_plain_eu": capboard_eu.carrier(plain=True),
            "testbox_eu": testbox_eu.box(), "testbox_plate_eu": testbox_eu.plate(),
            "plate_jig_saw": plate_jig.saw_guide()}


def main():
    pdir = OUT / "print"
    pdir.mkdir(parents=True, exist_ok=True)
    for name, p in parts().items():
        if name in ("insert", "trim", "insert_plain", "trim_plain", "insert_switch"):  # model frame, for the assembly/renders
            export_step(p, str(OUT / f"{name}.step"))
            export_stl(p, str(OUT / f"{name}.stl"), tolerance=0.02, angular_tolerance=0.1)
        q = on_bed(PRINT_ORIENT[name](p))
        export_stl(q, str(pdir / f"{name}.stl"), tolerance=0.02, angular_tolerance=0.1)
        m = trimesh.load(pdir / f"{name}.stl")
        print(f"{name:20s} {m.extents.round(1)} mm  watertight={m.is_watertight}  -> build/print/{name}.stl")
        if not m.is_watertight or max(m.extents[:2]) > 250 or m.extents[2] > 250:
            raise SystemExit(f"{name}: mesh not watertight or larger than the CC2 bed (256 x 256 x 256)")


if __name__ == "__main__":
    main()
