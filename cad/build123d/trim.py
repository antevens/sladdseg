"""TRIM PLATE (face plate) - a plain cover (v0.4, D-50, D-51): face, thin radar skin over the MSR-2 with posts onto its
board (D-66), SHT40 bay, vents, vents over the CO2 sensor, the microphone's sound hole and sound
column (D-83). No electronics and no contacts: the MSR-2, the SHT40 and the mic sit on the
ring board on the insert's collar (D-68).

Low-voltage side only: it carries no barrier duty. Any filament (PETG/ASA).
Print: face down (the exported print STL is already flipped), no supports.
Plain plate (D-109): the standard-size single-gang outline, no MSR-2 / SHT40 bays, vents or microphone; same insert
clearances, keys and screws.
Run:  python trim.py  -> ../../build/trim.step / .stl, trim_plain.step / .stl
"""
from math import radians, tan
from build123d import Box, Cylinder, Cone, Pos, Axis, chamfer
from params import *
from common import rr, slab, frame, sound_column
import msr2


MSR_BAY = (MSR[0] + 2 * CLR, MSR[1] + 2 * CLR)          # round the MSR-2


def mic_tube():
    """Sound column from the skin down to a gasket on the ring board round the mic (the face plate's screws press it
    on, D-83)."""
    return sound_column(MIC_AT, MIC, MIC_PORT_IN, RING_T, SKIN_Z + 0.01, *MIC_TUBE, MIC_BOOT)


def msr_posts():
    """Posts from the radar skin onto the MSR-2's board (D-66): they press it onto the ring board's spacers (D-68); the skin stands
    MSR_SKIN_GAP clear of its front."""
    return msr2.posts(0, MSR_Y, MSR_BACK_Z, PT - RADAR_WALL)


def build(plain=False):
    """Face plate; plain: the standard-size plate without the sensor bays (D-109)."""
    pw, ph, py = (PLAIN_PW, PLAIN_PH, 0.0) if plain else (PW, PH, PLATE_Y)
    shell = Pos(0, py, 0) * slab(rr(pw, ph, PR), 0, PT)
    shell = chamfer(shell.edges().group_by(Axis.Z)[-1], FACE_CHAMFER)
    shell -= Pos(0, py, 0) * slab(rr(pw - 2 * SKIN, ph - 2 * SKIN, PR - SKIN), -1, PT - SKIN)
    body = shell
    sb = (SHT[0] + 2 * SHT_BAY_CLR, SHT[1] + 2 * SHT_BAY_CLR)
    if not plain:
        # MSR-2 and SHT40 bay frames, down to just over the ring board's parts
        z0 = FRAME_Z0                                   # over the ring board's parts (D-68)
        body += frame(MSR_BAY[0], MSR_BAY[1], BAY_WALL, MSR_BAY_R, z0, PT, MSR_Y)
        body += frame(*sb, BAY_WALL, SHT_BAY_R, z0, PT, SHT_AT[1])
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
    if plain:
        return body
    body -= Pos(0, MSR_Y, 0) * slab(rr(*MSR_BAY, 1), -0.01, PT - RADAR_WALL)
    body += msr_posts()                                 # in the hollowed bay (D-66)
    body -= msr2.scd_vents(0, MSR_Y, PT, RADAR_WALL)      # grille: CO2 sensor and light sensor (D-65, D-69)
    zv = RING_PARTS_TOP + VENT_Z_OVER                   # vents through the edges, above the ring board's parts
    n, pitch, dx, w, d = MSR_VENTS
    for i in range(n):  # MSR vents, top edge
        body -= Pos((i - (n - 1) / 2) * pitch + dx, PLATE_Y + PH / 2 - SKIN + d / 2 - 1, zv) * Box(w, d, VENT_H)
    body -= Pos(0, SHT_AT[1], 0) * slab(rr(*sb, SHT_BAY_R), -0.01, PT - SKIN)
    body -= Pos(*MIC_AT, PT - SKIN / 2) * Cylinder(MIC_SKIN_HOLE_D / 2, SKIN + 1)   # microphone sound hole (D-29)
    n, pitch, w, lf, de = SHT_VENTS
    for i in range(n):  # SHT vents: face + bottom edge
        x = (i - (n - 1) / 2) * pitch
        body -= Pos(x, SHT_AT[1], PT - SKIN / 2) * Box(w, lf, SKIN + 2)
        body -= Pos(x, PLATE_Y - PH / 2 + de / 2 - 1, zv) * Box(w, de, VENT_H)
    return body


if __name__ == "__main__":
    from pathlib import Path
    from build123d import export_step, export_stl
    out = Path(__file__).resolve().parents[2] / "build"
    out.mkdir(exist_ok=True)
    for name, plain in (("trim", False), ("trim_plain", True)):
        p = build(plain)
        bb = p.bounding_box()
        print(f"{name} bbox x {bb.min.X:.1f}..{bb.max.X:.1f} y {bb.min.Y:.1f}..{bb.max.Y:.1f} z {bb.min.Z:.1f}..{bb.max.Z:.1f}"
              f"  vol {p.volume/1000:.1f} cm3 valid={p.is_valid} solids={len(p.solids())}")
        export_step(p, str(out / f"{name}.step"))
        export_stl(p, str(out / f"{name}.stl"), tolerance=0.02, angular_tolerance=0.1)
