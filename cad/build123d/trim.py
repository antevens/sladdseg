"""TRIM PLATE (face plate) - a plain cover (v0.4, D-50, D-51): face, thin radar skin over the MSR-2 with posts onto its
board (D-66), SHT45 bay, vents,
vents over the CO2 sensor, the
microphone's sound hole and sound tube. No electronics and no contacts: the MSR-2, the SHT45 and the mic sit on the
ring board on the insert's collar (D-68).

Low-voltage side only: it carries no barrier duty. Any filament (PETG/ASA).
Print: face down (the exported print STL is already flipped), no supports.
Run:  python trim.py  -> ../../build/trim.step / .stl
"""
from math import radians, tan
from build123d import Box, Cylinder, Cone, Pos, Axis, chamfer
from params import *
from common import rr, slab, frame
import msr2


MSR_BAY = (MSR[0] + 2 * CLR, MSR[1] + 2 * CLR)          # round the MSR-2


def mic_tube():
    """Sound tube from the skin down to a gasket on the mic carrier (the face plate's screws press it on)."""
    od, bore, gasket = MIC_TUBE
    z0 = RING_T + MIC_CARRIER[2] + gasket
    return Pos(*MIC_PORT, (z0 + SKIN_Z + 0.01) / 2) * (Cylinder(od / 2, SKIN_Z + 0.01 - z0) - Cylinder(bore / 2, PT))


def msr_posts():
    """Posts from the radar skin onto the MSR-2's board (D-66): they press it onto the ring board's spacers (D-68); the skin stands
    MSR_SKIN_GAP clear of its front."""
    return msr2.posts(0, MSR_Y, MSR_BACK_Z, PT - RADAR_WALL)


def build():
    shell = Pos(0, PLATE_Y, 0) * slab(rr(PW, PH, PR), 0, PT)
    shell = chamfer(shell.edges().group_by(Axis.Z)[-1], FACE_CHAMFER)
    shell -= Pos(0, PLATE_Y, 0) * slab(rr(PW - 2 * SKIN, PH - 2 * SKIN, PR - SKIN), -1, PT - SKIN)
    body = shell
    # MSR-2 and SHT45 bay frames, down to just over the ring board's parts
    z0 = FRAME_Z0                                       # over the ring board's parts (D-68)
    body += frame(MSR_BAY[0], MSR_BAY[1], 1.6, 1, z0, PT, MSR_Y)
    body += frame(SHT[0] + 0.8, SHT[1] + 0.8, 1.6, 0.5, z0, PT, SHT_AT[1])
    body += mic_tube()

    # ---------------- cuts ----------------
    # clearance envelope of the insert: island window through the face, flange underneath
    body -= slab(rr(ISLAND[0] + 2 * SPLIT_CLR, ISLAND[1] + 2 * SPLIT_CLR, ISLAND_R + SPLIT_CLR), DECK_Z - 1, PT + 1)
    fl = slab(rr(FLANGE_OUT[0] + 2 * SPLIT_CLR, FLANGE_OUT[1] + 2 * SPLIT_CLR, ISLAND_R + FLANGE + SPLIT_CLR), -1, DECK_Z)
    for s in (-1, 1):
        fl += Pos(0, s * SCREW_PITCH / 2, DECK_Z / 2) * Cylinder(BOSS_R + SPLIT_CLR, DECK_Z + 2)
    body -= fl
    for kx, ky in KEY_POS:  # sockets for the insert's locating pins
        body -= Pos(kx, ky, DECK_Z + (KEY_H + 0.2) / 2 - 0.01) * Cylinder(KEY_D / 2 + KEY_CLR, KEY_H + 0.2)
    for s in (-1, 1):  # countersunk #6 holes, clamp trim + insert to the box ears
        y = s * SCREW_PITCH / 2
        body -= Pos(0, y, PT / 2) * Cylinder(SCREW_D / 2, PT + 2)
        d = (SCREW_HEAD_D - SCREW_D) / 2 / tan(radians(SCREW_CSK / 2))   # countersink depth
        body -= Pos(0, y, PT - d / 2 + 0.005) * Cone(SCREW_D / 2, SCREW_HEAD_D / 2 + 0.01, d + 0.01)
    body -= Pos(0, MSR_Y, 0) * slab(rr(*MSR_BAY, 1), -0.01, PT - RADAR_WALL)
    body += msr_posts()                                 # in the hollowed bay (D-66)
    body -= msr2.scd_vents(0, MSR_Y, PT, RADAR_WALL)      # grille: CO2 sensor and light sensor (D-65, D-69)
    zv = RING_PARTS_TOP + 3.0                           # vents through the edges, above the ring board's parts
    for i in range(-2, 3):  # MSR vents, top edge
        body -= Pos(i * 7 + 1.5, PLATE_Y + PH / 2 - SKIN + 2, zv) * Box(3, 6, 5)
    body -= Pos(0, SHT_AT[1], 0) * slab(rr(SHT[0] + 0.8, SHT[1] + 0.8, 0.5), -0.01, PT - SKIN)
    body -= Pos(*MIC_PORT, PT - SKIN / 2) * Cylinder(MIC_SKIN_HOLE_D / 2, SKIN + 1)   # microphone sound hole (D-29)
    for i in (-1, 0, 1):  # SHT vents: face + bottom edge
        body -= Pos(i * 4, SHT_AT[1], PT - 1) * Box(2, 6, 4)
        body -= Pos(i * 4, PLATE_Y - PH / 2 + 4, zv) * Box(2, 10, 5)
    return body


if __name__ == "__main__":
    from pathlib import Path
    from build123d import export_step, export_stl
    out = Path(__file__).resolve().parents[2] / "build"
    out.mkdir(exist_ok=True)
    p = build()
    bb = p.bounding_box()
    print(f"trim bbox x {bb.min.X:.1f}..{bb.max.X:.1f} y {bb.min.Y:.1f}..{bb.max.Y:.1f} z {bb.min.Z:.1f}..{bb.max.Z:.1f}"
          f"  vol {p.volume/1000:.1f} cm3 valid={p.is_valid} solids={len(p.solids())}")
    export_step(p, str(out / "trim.step"))
    export_stl(p, str(out / "trim.stl"), tolerance=0.02, angular_tolerance=0.1)
