"""Build slicer projects (.3mf) and G-code for the Elegoo Centauri Carbon 2.

    python print/slice.py            (or: make print)

Uses OrcaSlicer (pinned in the Makefile, tested 2.4.2; `make slicer` downloads it to
.tools/). SLICER overrides it: an OrcaSlicer AppImage, an extracted squashfs-root/AppRun,
or another OrcaSlicer fork with the same CLI. Headless machines need xvfb-run
(`make system-deps`).

Settings = stock CC2 system profiles + the small override sets below (also written
to print/profiles/*.json so they can be imported into the GUI as user presets).
Outputs:
  print/<job>.3mf                 project: model + settings, opens in OrcaSlicer/ElegooSlicer
  build/print/gcode/<job>.gcode   sliced, for checking time/material (or printing)
"""
import json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STL = ROOT / "build" / "print"
PRINTER = "Elegoo Centauri Carbon 2 0.4 nozzle"
BASE_PROCESS = "0.20mm Strength @Elegoo CC2 0.4 nozzle"
BED = "Textured PEI Plate"                 # CC2 ships with a textured PEI sheet

# Whole insert is barrier, so it gets barrier settings everywhere (no modifiers needed):
# 6 walls (2.7 mm) makes every 1.6 mm barrier wall solid, 6 top/bottom layers.
BARRIER = {"wall_loops": "6", "top_shell_layers": "6", "bottom_shell_layers": "6",
           "sparse_infill_density": "40%", "sparse_infill_pattern": "gyroid",
           "enable_support": "0", "brim_type": "outer_only", "brim_width": "5",
           "seam_position": "back", "detect_thin_wall": "1"}
# Trim prints face-down: 7 bottom layers keep the face skin solid (the radar skin is 0.6 mm, D-51).
TRIM = {"wall_loops": "4", "top_shell_layers": "4", "bottom_shell_layers": "7",
        "sparse_infill_density": "20%", "sparse_infill_pattern": "gyroid",
        "enable_support": "0", "brim_type": "no_brim", "seam_position": "back"}
# v0.4 insert (D-68): plug down; supports only under the seal lip and in the riser pocket.
INSERT = dict(BARRIER, enable_support="1", support_type="normal(auto)", support_on_build_plate_only="1",
              support_threshold_angle="40")
COUPON = dict(INSERT, brim_type="no_brim")
# Replacement back cover (D-35): back down, 1.2 mm walls, 0.4 mm floor under the steel plate and the regulator.
COVER = {"wall_loops": "3", "top_shell_layers": "4", "bottom_shell_layers": "2", "sparse_infill_density": "30%",
         "sparse_infill_pattern": "gyroid", "enable_support": "0", "brim_type": "no_brim", "seam_position": "back",
         "detect_thin_wall": "1"}                     # the plate clips' 0.48 mm tabs print as one line (D-99)
# Steel plate cutting jigs (D-52): small, solid enough to take a vise and a saw.
JIG = {"wall_loops": "4", "top_shell_layers": "4", "bottom_shell_layers": "4", "sparse_infill_density": "40%",
       "sparse_infill_pattern": "gyroid", "enable_support": "0", "brim_type": "no_brim", "seam_position": "back"}

# test prints: PLA (human, 2026-10-11), except the back cover (PETG, D-44); the barrier parts also as PC-FR finals
TEST = "Elegoo PLA @ECC2"

JOBS = {
    # name: (parts, filament, process overrides)
    "insert_PC-FR": (["insert"], "Elegoo PC-FR @ECC2", INSERT),
    "insert_PLA_testfit": (["insert"], TEST, dict(INSERT, brim_type="no_brim")),
    "trim_PLA": (["trim"], TEST, TRIM),
    "coupons_PLA": (["coupon_pocket_well", "coupon_msr", "coupon_rocker", "coupon_ribs"], TEST, COUPON),
    "backcover_PETG": (["back_cover"], "Elegoo PETG @ECC2", COVER),   # its clips broke in PLA (D-44)
    "backcover_ABS": (["back_cover"], "Elegoo ABS @ECC2", COVER),     # test while the PETG is on its way; ABS shrinks more
    "plate_jig_PLA": (["plate_jig_saw"], TEST, JIG),
    "eu_cap_PC-FR": (["cap_eu"], "Elegoo PC-FR @ECC2", BARRIER),
    "eu_cap_PLA_testfit": (["cap_eu"], TEST, dict(BARRIER, brim_type="no_brim")),
    "eu_trim_PLA": (["trim_eu"], TEST, TRIM),
    "eu_carrier_PLA": (["carrier_eu"], TEST, JIG),   # cap board carrier (D-70)
    "eu_testbox_PLA": (["testbox_eu", "testbox_plate_eu"], TEST, JIG),   # test socket (D-76)
    # plain plates: rocker and battery-free remote only (D-109)
    "plain_insert_PC-FR": (["insert_plain"], "Elegoo PC-FR @ECC2", INSERT),
    "plain_insert_PLA_testfit": (["insert_plain"], TEST, dict(INSERT, brim_type="no_brim")),
    "plain_trim_PLA": (["trim_plain"], TEST, TRIM),
    "eu_plain_cap_PC-FR": (["cap_plain_eu"], "Elegoo PC-FR @ECC2", BARRIER),
    "eu_plain_cap_PLA_testfit": (["cap_plain_eu"], TEST, dict(BARRIER, brim_type="no_brim")),
    "eu_plain_trim_PLA": (["trim_plain_eu"], TEST, TRIM),
    "eu_plain_carrier_PLA": (["carrier_plain_eu"], TEST, JIG),
    # switch-only plates: rocker switch and terminal blocks; the plain face plate and carrier (D-122)
    "switch_insert_PC-FR": (["insert_switch"], "Elegoo PC-FR @ECC2", INSERT),
    "switch_insert_PLA_testfit": (["insert_switch"], TEST, dict(INSERT, brim_type="no_brim")),
    "eu_switch_cap_PC-FR": (["cap_switch_eu"], "Elegoo PC-FR @ECC2", BARRIER),
    "eu_switch_cap_PLA_testfit": (["cap_switch_eu"], TEST, dict(BARRIER, brim_type="no_brim")),
}


def slicer():
    cands = [os.environ.get("SLICER", "")]
    cands += sorted(str(p) for p in (ROOT / ".tools").glob("OrcaSlicer_*.AppImage"))[-1:]
    cands += [shutil.which(n) or "" for n in ("orca-slicer", "OrcaSlicer")]
    for c in cands:
        if c and Path(c).exists():
            return Path(c)
    sys.exit("OrcaSlicer not found: run `make slicer`, or set SLICER to an OrcaSlicer AppImage")


def version(run):
    with tempfile.TemporaryDirectory() as t:  # the CLI drops result.json in its cwd
        r = subprocess.run(run + ["--help"], capture_output=True, text=True, cwd=t)
    m = re.search(r"^(\S+Slicer-[\d.]+):", r.stdout + r.stderr, re.M)
    return m.group(1) if m else "unknown slicer"


def profiles_dir(exe):
    for base in (exe.parent, exe.parent / "squashfs-root"):
        d = base / "resources" / "profiles"
        if d.exists():
            return d
    tmp = Path(tempfile.mkdtemp())
    subprocess.run([str(exe), "--appimage-extract", "resources/profiles/*"], cwd=tmp, check=True,
                   stdout=subprocess.DEVNULL)
    return tmp / "squashfs-root" / "resources" / "profiles"


def index(pdir):
    idx = {}
    for vendor in ["Elegoo"] + sorted(p.name for p in pdir.iterdir() if p.is_dir() and p.name != "Elegoo"):
        for f in (pdir / vendor).rglob("*.json"):
            try:
                d = json.loads(f.read_text())
            except Exception:
                continue
            if isinstance(d, dict) and "name" in d and "type" in d:
                idx.setdefault((d["type"], d["name"]), d)
    return idx


def flat(idx, typ, name):
    d = dict(idx[(typ, name)])
    if d.get("inherits"):
        base = flat(idx, typ, d["inherits"])
        base.update(d)
        d = base
    return d


def main():
    exe = slicer()
    idx = index(profiles_dir(exe))
    run = [str(exe)]
    if not os.environ.get("DISPLAY"):
        if not shutil.which("xvfb-run"):
            sys.exit("no DISPLAY and no xvfb-run: run `make system-deps` (or install xvfb)")
        run = ["xvfb-run", "-a"] + run
    os.environ.setdefault("APPIMAGE_EXTRACT_AND_RUN", "1")  # AppImages without FUSE
    print("slicer:", version(run), f"({exe})")
    gdir = ROOT / "build" / "print" / "gcode"
    gdir.mkdir(parents=True, exist_ok=True)
    pdir = ROOT / "print" / "profiles"
    pdir.mkdir(exist_ok=True)
    for f in pdir.glob("process_*.json"):                  # profiles of jobs no longer in JOBS
        if f.stem[len("process_"):] not in JOBS:
            f.unlink()
    for f in (ROOT / "print").glob("*.3mf"):               # projects of jobs no longer in JOBS
        if f.stem not in JOBS:
            f.unlink()
    machine = flat(idx, "machine", PRINTER)
    report = []
    for job, (parts, fil, over) in JOBS.items():
        missing = [p for p in parts if not (STL / f"{p}.stl").exists()]
        if missing:
            sys.exit(f"missing {missing}: run `make cad` first")
        proc = flat(idx, "process", BASE_PROCESS)
        proc.update(over)
        proc.update({"name": f"smart-wallplate {job}", "curr_bed_type": BED,
                     "compatible_printers": [PRINTER]})
        fila = flat(idx, "filament", fil)
        user = {"type": "process", "name": proc["name"], "inherits": BASE_PROCESS, "from": "User",
                "instantiation": "true", **over}
        (ROOT / "print" / "profiles" / f"process_{job}.json").write_text(json.dumps(user, indent=2) + "\n")
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            for n, d in (("machine", machine), ("process", proc), ("filament", fila)):
                d = {k: v for k, v in d.items() if k != "inherits"}
                (t / f"{n}.json").write_text(json.dumps(d))
            models = [str(STL / f"{p}.stl") for p in parts]
            common = run + ["--load-settings", f"{t/'machine.json'};{t/'process.json'}",
                            "--load-filaments", str(t / "filament.json"),
                            "--arrange", "1", "--orient", "0", "--ensure-on-bed"]  # STLs are centred on 0,0: let it place them
            # 1) sliced G-code (proves it slices with these settings, gives time/material)
            out = t / "out"
            r = subprocess.run(common + ["--slice", "0", "--outputdir", str(out)] + models,
                               capture_output=True, text=True, cwd=t)
            g = sorted(out.glob("*.gcode")) if out.exists() else []
            if r.returncode != 0 or not g:
                print(r.stdout[-3000:], r.stderr[-3000:])
                sys.exit(f"{job}: slicing failed (exit {r.returncode})")
            shutil.copy(g[0], gdir / f"{job}.gcode")
            head = g[0].read_text(errors="ignore")
            est = re.search(r"estimated printing time \(normal mode\) = (.*)", head)
            grams = re.search(r"total filament weight \[g\] : ([\d.]+)", head) or re.search(r"filament used \[g\] = ([\d.]+)", head)
            supp = re.search(r"; enable_support = (\d)", head)
            # 2) project 3MF with the same settings
            r2 = subprocess.run(common + ["--export-3mf", str(ROOT / "print" / f"{job}.3mf")] + models,
                                capture_output=True, text=True, cwd=t)
            if r2.returncode != 0:
                print(r2.stdout[-2000:], r2.stderr[-2000:])
                sys.exit(f"{job}: 3MF export failed")
        report.append((job, fil, est.group(1).strip() if est else "?", grams.group(1) if grams else "?",
                       supp.group(1) if supp else "?"))
    print(f"{'job':22s} {'filament':22s} {'time':>12s} {'g':>7s} supports")
    for j, f, e, gr, s in report:
        print(f"{j:22s} {f:22s} {e:>12s} {gr:>7s} {s}")


if __name__ == "__main__":
    main()
