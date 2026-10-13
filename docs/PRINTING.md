# Printing

Printer: **Elegoo Centauri Carbon 2 Combo** (256 × 256 × 256 mm, enclosed, hardened
0.4 mm nozzle up to 350 °C, bed up to 110 °C, CANVAS 4-filament hub). Slicer:
**ElegooSlicer** (an OrcaSlicer fork, tested 1.5.3.5, Linux AppImage): the projects are built with it, so they open as
its own, settings included. OrcaSlicer 2.4.2 stamps the projects it exports as BambuStudio 2.6, and ElegooSlicer opens
those with its default settings (supports on, its own infill). The CANVAS hub isn't needed:
every part is single-material.

## Files

| File | Part(s) | Filament | Est. time / mass (ElegooSlicer 1.5.3.5) |
|------|---------|----------|------------------------------------------|
| `print/na_coupons_PLA.3mf` | pocket+well coupon (with the steel piece's recess), MSR-2 bay coupon, rocker panel ladder, crush-rib coupon (D-68) | PLA | 2 h 18 m / 60.5 g |
| `print/na_barrier_PLA_testfit.3mf` | NA barrier (every edition) and the blank board for switch only (D-127; fit check only, **not for mains**), the barrier on supports | PLA | 2 h 20 m / 59.5 g |
| `print/na_face_plate_PLA.3mf` | NA face plate (face plate, passive) | PLA | 42 m / 23.2 g |
| `print/na_barrier_PC-FR.3mf` | NA barrier and blank board, **final**, the barrier on supports | Elegoo PC-FR (flame retardant; no UL94 class stated, D-18) | 2 h 21 m / 52.5 g |
| `print/backcover_PETG.3mf` | replacement back cover for the battery-free BILRESA (D-35), back down; PETG: its clips broke in PLA (D-44) | PETG | 26 m / 8.1 g |
| `print/backcover_ABS.3mf` | the same cover in ABS, to test before the PETG arrives (shrinks more: check the fit first) | ABS | 20 m / 7.1 g |
| `print/plate_jig_PLA.3mf` | steel plate hacksaw guide (D-52, D-81), floor down | PLA | 18 m / 7.8 g |
| `print/eu_barrier_PLA_testfit.3mf` | EU barrier (every edition), face down, and the blank board for switch only, pegs up (D-127; fit check only, **not for mains**) | PLA | 40 m / 14.8 g |
| `print/eu_barrier_PC-FR.3mf` | EU barrier and blank board, **final** | Elegoo PC-FR (flame retardant; no UL94 class stated, D-18) | 48 m / 13.3 g |
| `print/eu_face_plate_PLA.3mf` | EU face plate, face down | PLA | 1 h 8 m / 42.3 g |
| `print/eu_carrier_PLA.3mf` | EU sensor board carrier, bottom down: the rim up, the 0.8 mm lip under the barrier on the bed (D-71) | PLA | 40 m / 18.1 g |
| `print/eu_testbox_PLA.3mf` | EU test socket: the box floor down, the wall plate flat (D-76) | PLA | 3 h 13 m / 103.2 g |
| `print/na_plain_face_plate_PLA.3mf` | NA plain face plate, 69.85 × 114.3 mm (D-109), face down | PLA | 27 m / 16.3 g |
| `print/eu_plain_face_plate_PLA.3mf` | EU plain face plate, 84.6 × 84.6 mm (D-109, D-146), face down | PLA | 44 m / 29.5 g |
| `print/eu_plain_carrier_PLA.3mf` | EU plain carrier (lip, rim and snap windows, no sensor board, D-109, D-150), bottom down | PLA | 21 m / 8.4 g |

Open a `.3mf` in ElegooSlicer (import the whole project, settings included), check the plate, slice, send. The projects carry the
printer (CC2 0.4 nozzle), filament and process settings; the parts are already
oriented. The process overrides (walls, top / bottom layers, infill, supports, brim, seam) are also written onto
each object, so they stay with the parts on another printer or process preset (checked: a Bambu Lab P1S with its stock
process slices them to the same mass as with the overrides in the process). `print/profiles/*.json` hold just the
process overrides, importable as user presets (they inherit the CC2's 0.20 mm Strength process). The back cover jobs also
carry 0.08 mm layers from z 8.6 to the top (a height range): the rim's taper at the bottom end (D-145) then
steps 0.08 mm at a time. Thumbnails are missing (generated headless); the slicer redraws them.

Regenerate after any CAD change: `make cad check print`. `make print` downloads the
pinned ElegooSlicer AppImage into `.tools/` (checksum-verified) on first use; set `SLICER`
to use another OrcaSlicer fork. Headless machines need `xvfb-run` (`make system-deps`). Sliced G-code for checking
time/material lands in `build/print/gcode/`.

## Order of work

1. `na_coupons_PLA`: rocker ladder → find the panel thickness that latches firmly,
   record it as `SW_PANEL_T` in `docs/MEASUREMENTS.md`. Pocket+well coupon → remote
   drop-in/lift-out, rocker snap-in, key pin. MSR-2 coupon → board fit,
   radar skin, the grille for the CO2 and light sensors (D-69), the three Ø1.8 posts onto the MSR-2's board (D-66).
   Crush-rib coupon → the sensor board's fit on the ribs (0.10 / 0.15 / 0.20), record `SB_RIB`.
2. Update `params.py` from the measurements, `make cad check print`.
3. `na_barrier_PLA_testfit` + `na_face_plate_PLA` → full dry fit in the box (breaker off, nothing
   connected). Check the corner taper against the box ears.
4. `na_barrier_PC-FR` for the installed part. Keep the filament datasheet with the build record.
5. `plate_jig_PLA`: saw the supplied steel plate (D-43, D-52: one straight cut, an 18.5 mm piece
   with one round end; check its real size first).
6. Battery-free remote: `backcover_PETG` on a BILRESA (latches, the remote's magnet plate, contact
   positions, the end fingers' ramp; the plate clips and flex snap hooks snapped in PLA: snap the plate
   in and out a few times and check the clips survive in PETG, D-44; they broke in PLA). ABS (`backcover_ABS`)
   until the PETG arrives: it typically shrinks 0.5–0.7 % (PETG 0.2–0.4 %), so measure the inside against the
   model (42.0 × 67.0 mm at the rim) and try it on a remote; if it is tight, set the slicer's filament
   shrinkage from the measured shortfall.
7. EU: `eu_testbox_PLA` (test socket, D-76), then `eu_barrier_PLA_testfit`, `eu_carrier_PLA` and
   `eu_face_plate_PLA` in it (domes, the carrier clamp, the snaps, the depth of the board stack against
   the depth markers); then `eu_barrier_PC-FR`.
8. Plain plates (D-109): `na_plain_face_plate_PLA` (NA), `eu_plain_carrier_PLA` + `eu_plain_face_plate_PLA` (EU) on the
   barriers of the full plates; switch only: the blank boards (printed in the barrier jobs) in place of the pin boards.

Many BILRESA dimensions are `ESTIMATE` (from photos and drawings, `docs/MEASUREMENTS.md`): the
first prints of the face plate pockets and the back cover are for measuring and
adjusting, not final parts.

## Settings (and why)

- **Back cover** (`COVER`): back down as modelled, 3 walls (1.2 mm), 2 bottom layers (the 0.4 mm
  floor under the regulator; the magnet plate sits on the full 1.6 mm shell, D-44), 30 % gyroid, no supports (the back's round-over
  is filled to 45° below its 45° point for that).
- **EU barrier**: the EU barrier, `BARRIER` settings like the NA barrier, face down. The floor of the steel
  piece's recess prints as an 18.1 mm bridge (D-72); check it for sag.
- **Barrier** (`INSERT`: `BARRIER` plus supports): the whole barrier is barrier, so no
  modifiers are needed: 6 walls (≈ 2.7 mm, so every 1.6 mm barrier wall prints solid),
  6 top/bottom layers, 40 % gyroid, 5 mm outer brim for PC-FR (warping). Orientation: as
  modelled, lowest face (the rocker panel's underside) on the bed. Supports (normal, from
  the plate only, 40°) carry only the seal lip on the wall plane and the pin board pocket's
  ceiling (D-68: no flat back; the flange's underside is a 45° taper, its land over the
  sensor board 1.8 mm, the FFC channel under it peaked); `make check` lists those planes and
  verifies no other overhang is wider than 3 mm. Clear the supports out of the pin board pocket
  and the pin holes completely: the pin board and the pins must sit free.
- **Face plate** (`TRIM`): face down on the textured PEI sheet (gives the face its finish).
  7 bottom layers keep the face solid; the 0.6 mm radar skin over the MSR-2 (D-51) is three of them; 4 walls, 20 %.
  Only bridges are the 2–3 mm vent windows.
- Base process: "0.20mm Strength @Elegoo CC2 0.4 nozzle"; bed: Textured PEI Plate.
- PC-FR: stock "Elegoo PC-FR @ECC2" profile. Elegoo's data sheet (as listed on
  spoolscout.com/data-sheets/elegoo): dry 80 ± 5 °C for 8 h before use (required); print
  and store at ≤ 20 % RH (sealed, desiccant); nozzle 260–280 °C, hardened steel ≥ 0.4 mm;
  bed 90–110 °C on textured/smooth PEI with glue (required); enclosure required, chamber
  45–60 °C; speed < 100 mm/s. Keep the chamber closed and let the part cool on the plate.
- PC-FR is much weaker across layers than along them (tensile 26 vs 55 MPa, impact
  12.2 vs 70.9 kJ/m², data sheet).

## Materials

- Test fits: Elegoo PLA (human 2026-10-11), except the back cover: PETG (its clips broke in PLA, D-44). On hand: PLA, ABS, TPU 72A, TPU 95A; on
  the way: PC, PC-FR, PETG (all Elegoo). ElegooSlicer has CC2 profiles for all of them but TPU 72A.
- PLA softens from about 55 °C: fine for fit checks, not for parts in a warm box or in sun.
- Barrier (NA barrier, EU barrier): Elegoo PC-FR for now. Its data sheet claims flame retardancy and
  rapid self-extinguishing but states no UL94 class or test thickness. Certification is
  out of scope for this stage (human decision 2026-10-08); a spool with a stated UL94 V-0
  rating will be chosen before an installed build, and its rated thickness goes into
  `V0_RATED_T` (`make check` compares it with the thinnest barrier wall, 1.6 mm).
- Face plate: PLA for tests; PETG (or ABS / ASA where it gets warm or sunny) for the installed plate.

## Checks after printing

- Remote drops in and lifts out with the finger scoops; its magnet holds onto the steel piece.
- Hold: fit the cut steel piece in its recess on the pocket coupon first. It sits 0.5 mm below
  the seat (`MAGNET_SETBACK`).
  - Too strong: add a thin non-magnetic spacer on top of it (tape, card), or
    reprint with a larger `MAGNET_SETBACK`.
  - Too weak: shim under the steel piece to bring it up to the seat.
- Rocker snaps in and latches; rocker clears the remote's back in both positions.
- Face plate seats on the flange with the two key pins; island flush with the face.
- Board standoffs (D-57): tap the barrier's four boss holes M3 × 0.5 (8.5 mm deep;
  keep the tap square, clear the chips), screw the four
  standoffs in by hand until the hex seats on the boss, then screw the board on with the nylon M3 × 8.
- MSR-2 detection range compared with and without the radar skin.
