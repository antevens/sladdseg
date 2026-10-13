"""Build slicer projects (.3mf) and G-code for the Elegoo Centauri Carbon 2.

    python print/slice.py            (or: make print)

Uses ElegooSlicer, an OrcaSlicer fork (pinned in the Makefile, tested 1.5.3.5; `make slicer` downloads it to
.tools/), so the projects open in ElegooSlicer as its own. SLICER overrides it: another OrcaSlicer fork's AppImage
or an extracted squashfs-root/AppRun with the same CLI (OrcaSlicer 2.4.2 stamps its projects BambuStudio 2.6, which
ElegooSlicer opens with its own default settings). Headless machines need xvfb-run (`make system-deps`).

Settings = stock CC2 system profiles + the small override sets below (also written
to print/profiles/*.json so they can be imported into the GUI as user presets).
Outputs:
  print/<job>.3mf                 project: model + settings, opens in ElegooSlicer (and OrcaSlicer); the
                                  overrides are also object settings, kept on any printer or process preset
  build/print/gcode/<job>.gcode   sliced, for checking time/material (or printing)
"""
import json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STL = ROOT / "build" / "print"
PRINTER = "Elegoo Centauri Carbon 2 0.4 nozzle"
BASE_PROCESS = "0.20mm Strength @Elegoo CC2 0.4 nozzle"
BED = "Textured PEI Plate"                 # CC2 ships with a textured PEI sheet

# Whole barrier is barrier, so it gets barrier settings everywhere (no modifiers needed):
# 6 walls (2.7 mm) makes every 1.6 mm barrier wall solid, 6 top/bottom layers.
BARRIER = {"wall_loops": "6", "top_shell_layers": "6", "bottom_shell_layers": "6",
           "sparse_infill_density": "40%", "sparse_infill_pattern": "gyroid",
           "enable_support": "0", "brim_type": "outer_only", "brim_width": "5",
           "seam_position": "back", "detect_thin_wall": "1"}
# Face plate prints face-down: 7 bottom layers keep the face skin solid (the radar skin is 0.6 mm, D-51).
TRIM = {"wall_loops": "4", "top_shell_layers": "4", "bottom_shell_layers": "7",
        "sparse_infill_density": "20%", "sparse_infill_pattern": "gyroid",
        "enable_support": "0", "brim_type": "no_brim", "seam_position": "back"}
# v0.4 barrier (D-68): plug down; supports only under the seal lip and in the pin board pocket.
INSERT = dict(BARRIER, enable_support="1", support_type="normal(auto)", support_on_build_plate_only="1",
              support_threshold_angle="40")
COUPON = dict(INSERT, brim_type="no_brim")
# Replacement back cover (D-35): back down, 1.2 mm walls, 0.4 mm floor under the steel plate and the regulator.
COVER = {"wall_loops": "3", "top_shell_layers": "4", "bottom_shell_layers": "2", "sparse_infill_density": "30%",
         "sparse_infill_pattern": "gyroid", "enable_support": "0", "brim_type": "no_brim", "seam_position": "back",
         "detect_thin_wall": "1"}                     # the plate clips' 0.48 mm tabs print as one line (D-99)
# The cover's rim tapers 0.64 mm over 55 mm (D-145, D-147): fine layers from below its lowest point to the top, so it
# steps 0.08 mm at a time; the rim's flat at the bottom end (z 9.16) lies midway between two of their slicing planes
# (9.12, 9.20).
COVER_FINE = (8.6, 0.08)                      # from z, layer height (to the part's top)
# Steel plate cutting jigs (D-52): small, solid enough to take a vise and a saw.
JIG = {"wall_loops": "4", "top_shell_layers": "4", "bottom_shell_layers": "4", "sparse_infill_density": "40%",
       "sparse_infill_pattern": "gyroid", "enable_support": "0", "brim_type": "no_brim", "seam_position": "back"}

# test prints: PLA (human, 2026-10-11), except the back cover (PETG, D-44); the barrier parts also as PC-FR finals
TEST = "Elegoo PLA @ECC2"

JOBS = {
    # name: (parts, filament, process overrides)
    "na_barrier_PC-FR": (["na_barrier", "na_blank_board"], "Elegoo PC-FR @ECC2", INSERT),
    "na_barrier_PLA_testfit": (["na_barrier", "na_blank_board"], TEST, dict(INSERT, brim_type="no_brim")),
    "na_face_plate_PLA": (["na_face_plate"], TEST, TRIM),
    "na_coupons_PLA": (["na_coupon_pocket_well", "na_coupon_msr", "na_coupon_rocker", "na_coupon_ribs"], TEST, COUPON),
    "backcover_PETG": (["back_cover"], "Elegoo PETG @ECC2", COVER),   # its clips broke in PLA (D-44)
    "backcover_ABS": (["back_cover"], "Elegoo ABS @ECC2", COVER),     # test while the PETG is on its way; ABS shrinks more
    "plate_jig_PLA": (["plate_jig_saw"], TEST, JIG),
    "eu_barrier_PC-FR": (["eu_barrier", "eu_blank_board"], "Elegoo PC-FR @ECC2", BARRIER),
    "eu_barrier_PLA_testfit": (["eu_barrier", "eu_blank_board"], TEST, dict(BARRIER, brim_type="no_brim")),
    "eu_face_plate_PLA": (["eu_face_plate"], TEST, TRIM),
    "eu_carrier_PLA": (["eu_carrier"], TEST, JIG),   # sensor board carrier (D-70)
    "eu_testbox_PLA": (["eu_testbox", "eu_testbox_plate"], TEST, JIG),   # test socket (D-76)
    # plain plates: rocker and battery-free remote only (D-109)
    "na_plain_face_plate_PLA": (["na_plain_face_plate"], TEST, TRIM),
    "eu_plain_face_plate_PLA": (["eu_plain_face_plate"], TEST, TRIM),
    "eu_plain_carrier_PLA": (["eu_plain_carrier"], TEST, JIG),
    # switch-only plates: rocker switch and terminal blocks; the plain face plate and carrier (D-122)
}

FINE = {"backcover_PETG": COVER_FINE, "backcover_ABS": COVER_FINE}   # jobs with fine layers over their top (D-145)


def slicer():
    cands = [os.environ.get("SLICER", "")]
    cands += sorted(str(p) for p in (ROOT / ".tools").glob("ElegooSlicer_*.AppImage"))[-1:]
    cands += [shutil.which(n) or "" for n in ("elegoo-slicer", "ElegooSlicer")]
    for c in cands:
        if c and Path(c).exists():
            return Path(c)
    sys.exit("ElegooSlicer not found: run `make slicer`, or set SLICER to an OrcaSlicer fork's AppImage")


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


def object_settings(project, over):
    """Write the process overrides onto every object of a project 3MF (Metadata/model_settings.config): object
    settings stay with the parts whatever printer and process preset the project is opened with."""
    import xml.etree.ElementTree as ET
    import zipfile
    name = "Metadata/model_settings.config"
    with zipfile.ZipFile(project) as z:
        items = [(i, z.read(i.filename)) for i in z.infolist()]
    root = ET.fromstring(dict((i.filename, d) for i, d in items)[name])
    for obj in root.iter("object"):
        have = {m.get("key"): m for m in obj.findall("metadata")}
        at = list(obj).index(obj.find("part")) if obj.find("part") is not None else len(obj)
        for k, v in over.items():
            if k in have:
                have[k].set("value", str(v))
            else:
                m = ET.Element("metadata", key=k, value=str(v))
                m.tail = "\n    "
                obj.insert(at, m)
                at += 1
    data = b'<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="utf-8")
    tmp = project.with_suffix(".tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for i, d in items:
            z.writestr(i, data if i.filename == name else d)
    tmp.replace(project)


def layer_ranges(project, z0, h):
    """Layer height h from z0 to the top of every object of a project 3MF (Metadata/layer_config_ranges.xml, the
    slicers' height range modifiers; objects numbered from 1 in the order of the model)."""
    import zipfile
    name = "Metadata/layer_config_ranges.xml"
    with zipfile.ZipFile(project) as z:
        items = [(i, z.read(i.filename)) for i in z.infolist() if i.filename != name]
        n = z.read("3D/3dmodel.model").decode().count("<item ")
    objs = "".join(f' <object id="{i}">\n  <range min_z="{z0}" max_z="1000">\n'
                   f'   <option opt_key="extruder">0</option>\n   <option opt_key="layer_height">{h}</option>\n'
                   f'  </range>\n </object>\n' for i in range(1, n + 1))
    tmp = project.with_suffix(".tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for i, d in items:
            z.writestr(i, d)
        z.writestr(name, f'<?xml version="1.0" encoding="utf-8"?>\n<objects>\n{objs}</objects>\n')
    tmp.replace(project)


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
        proc.update({"name": f"sladdseg {job}", "curr_bed_type": BED,
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
            # 1) project 3MF: these settings, the overrides also on the objects, fine layers where a job has them
            project = ROOT / "print" / f"{job}.3mf"
            r2 = subprocess.run(common + ["--export-3mf", str(project)] + models, capture_output=True, text=True, cwd=t)
            if r2.returncode != 0:
                print(r2.stdout[-2000:], r2.stderr[-2000:])
                sys.exit(f"{job}: 3MF export failed")
            object_settings(project, over)
            if job in FINE:
                layer_ranges(project, *FINE[job])
            # 2) the project sliced as it is opened (proves it slices, gives time/material)
            out = t / "out"
            r = subprocess.run(run + ["--slice", "0", "--outputdir", str(out), str(project)],
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
        report.append((job, fil, est.group(1).strip() if est else "?", grams.group(1) if grams else "?",
                       supp.group(1) if supp else "?"))
    print(f"{'job':22s} {'filament':22s} {'time':>12s} {'g':>7s} supports")
    for j, f, e, gr, s in report:
        print(f"{j:22s} {f:22s} {e:>12s} {gr:>7s} {s}")


if __name__ == "__main__":
    main()
