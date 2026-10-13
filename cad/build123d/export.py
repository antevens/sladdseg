"""Print-orientation helpers and mesh export for every printable part.

Run: python export.py -> ../../build/print/<part>.stl (oriented, on the bed, centred)
"""
from pathlib import Path
import trimesh
from build123d import Rot, Pos, export_stl, export_step

OUT = Path(__file__).resolve().parents[2] / "build"

PRINT_ORIENT = {
    "na_barrier": lambda p: p,                          # floor-down: as modelled; supports under the seal lip and the pin board pocket (D-68)
    "na_face_plate": lambda p: Rot(180, 0, 0) * p,           # face-down
    "na_blank_board": lambda p: p,                  # pegs up (D-127)
    "na_plain_face_plate": lambda p: Rot(180, 0, 0) * p,     # face-down (D-109)
    "na_coupon_pocket_well": lambda p: p,
    "na_coupon_msr": lambda p: Rot(180, 0, 0) * p,
    "na_coupon_rocker": lambda p: p,
    "na_coupon_ribs": lambda p: p,
    "back_cover": lambda p: p,                      # back down: as modelled (D-35)
    "eu_barrier": lambda p: Rot(180, 0, 0) * p,         # face-down (barrier, D-30)
    "eu_face_plate": lambda p: Rot(180, 0, 0) * p,        # face-down
    "eu_carrier": lambda p: p,                      # bottom down: the rim up, the lip under the barrier on the bed (D-71)
    "eu_blank_board": lambda p: p,                  # pegs and ledge up (D-127)
    "eu_plain_face_plate": lambda p: Rot(180, 0, 0) * p,  # face-down (D-109)
    "eu_plain_carrier": lambda p: p,                # as the carrier (D-109)
    "eu_testbox": lambda p: p,                      # floor down, open side up (D-76)
    "eu_testbox_plate": lambda p: p,                # flat
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
    sys.path[1:1] = [str(Path(__file__).resolve().parent / v) for v in ("na", "eu")]
    import barrier_na, face_plate_na, sensor_board_na, coupons_na, backcover, plate_jig
    import barrier_eu, face_plate_eu, sensor_board_eu, boards_eu, testbox_eu
    ins, tr = barrier_na.build(), face_plate_na.build()
    return {"na_barrier": ins, "na_face_plate": tr,
            "na_blank_board": sensor_board_na.blank_board(), "na_plain_face_plate": face_plate_na.build(plain=True),
            "na_coupon_pocket_well": coupons_na.pocket_well(ins),
            "na_coupon_msr": coupons_na.msr(tr),
            "na_coupon_rocker": coupons_na.rocker_ladder(),
            "na_coupon_ribs": coupons_na.ribs(),
            "back_cover": backcover.cover(),
            "eu_barrier": barrier_eu.build(), "eu_face_plate": face_plate_eu.build(),
            "eu_carrier": sensor_board_eu.carrier(),
            "eu_blank_board": boards_eu.blank_board(), "eu_plain_face_plate": face_plate_eu.build(plain=True),
            "eu_plain_carrier": sensor_board_eu.carrier(plain=True),
            "eu_testbox": testbox_eu.box(), "eu_testbox_plate": testbox_eu.plate(),
            "plate_jig_saw": plate_jig.saw_guide()}


def main():
    pdir = OUT / "print"
    pdir.mkdir(parents=True, exist_ok=True)
    for name, p in parts().items():
        if name in ("na_barrier", "na_face_plate", "na_plain_face_plate"):  # model frame, for the assembly/renders
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
