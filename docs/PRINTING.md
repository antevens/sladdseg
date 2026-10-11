# Printing

Printer: **Elegoo Centauri Carbon 2 Combo** (256 × 256 × 256 mm, enclosed, hardened
0.4 mm nozzle up to 350 °C, bed up to 110 °C, CANVAS 4-filament hub). Slicer:
**OrcaSlicer** (tested 2.4.2, Linux AppImage). ElegooSlicer (an OrcaSlicer fork, tested
1.5.3.5) ships the same CC2 profiles and opens the same projects. The CANVAS hub isn't needed:
every part is single-material.

## Files

| File | Part(s) | Filament | Est. time / mass (OrcaSlicer 2.4.2) |
|------|---------|----------|------------------------------------------|
| `print/coupons_PLA.3mf` | pocket+well coupon (with the steel piece's recess), MSR-2 bay coupon, rocker panel ladder, crush-rib coupon (D-68) | PLA | 2 h 18 m / 60.2 g |
| `print/insert_PLA_testfit.3mf` | NA box insert (fit check only, **not for mains**), on supports | PLA | 2 h 19 m / 59.0 g |
| `print/trim_PLA.3mf` | NA trim plate (face plate, passive) | PLA | 38 m / 22.4 g |
| `print/insert_PC-FR.3mf` | NA box insert, **final**, on supports | Elegoo PC-FR (flame retardant; no UL94 class stated, D-18) | 2 h 19 m / 51.9 g |
| `print/backcover_PETG.3mf` | replacement back cover for the battery-free BILRESA (D-35), back down; PETG: its clips broke in PLA (D-44) | PETG | 21 m / 8.5 g |
| `print/backcover_ABS.3mf` | the same cover in ABS, to test before the PETG arrives (shrinks more: check the fit first) | ABS | 17 m / 7.5 g |
| `print/back_gauges_PLA.3mf` | five flat profile gauges for the inside of the remote's original back cover, side to side: the modelled back (round-over 8.1 × 8.0, measured) with its round-over 0.5 mm smaller to 0.5 mm larger in 0.25 mm steps (engraved R7.60 … R8.60), a line at the rim (D-87); deburr the arcs before use | PLA | 18 m / 7.8 g |
| `print/plate_jig_PLA.3mf` | steel plate hacksaw guide (D-52, D-81), floor down | PLA | 18 m / 7.8 g |
| `print/eu_cap_PLA_testfit.3mf` | EU cap (fit check only, **not for mains**), face down | PLA | 28 m / 10.9 g |
| `print/eu_cap_PC-FR.3mf` | EU cap, **final** (the EU barrier), face down | Elegoo PC-FR (flame retardant; no UL94 class stated, D-18) | 37 m / 9.8 g |
| `print/eu_trim_PLA.3mf` | EU trim plate, face down | PLA | 1 h 5 m / 41.6 g |
| `print/eu_carrier_PLA.3mf` | EU cap board carrier, bottom down: the rim up, the 0.8 mm lip under the cap on the bed (D-71) | PLA | 39 m / 17.6 g |
| `print/eu_testbox_PLA.3mf` | EU test socket: the box floor down, the wall plate flat (D-76) | PLA | 3 h 12 m / 102.7 g |

Open a `.3mf` in OrcaSlicer, check the plate, slice, send. The projects carry the
printer (CC2 0.4 nozzle), filament and process settings; the parts are already
oriented. `print/profiles/*.json` hold just the process overrides, importable as
user presets. Thumbnails are missing (generated headless); the slicer redraws them.

Regenerate after any CAD change: `make cad check print`. `make print` downloads the
pinned OrcaSlicer AppImage into `.tools/` (checksum-verified) on first use; set `SLICER`
to use another OrcaSlicer build. Headless machines need `xvfb-run` (`make system-deps`). Sliced G-code for checking
time/material lands in `build/print/gcode/`.

## Order of work

1. `coupons_PLA`: rocker ladder → find the panel thickness that latches firmly,
   record it as `SW_PANEL_T` in `docs/MEASUREMENTS.md`. Pocket+well coupon → remote
   drop-in/lift-out, rocker snap-in, key pin, pass-through. MSR-2 coupon → board fit,
   radar skin, the grille for the CO2 and light sensors (D-69), the three Ø1.8 posts onto the MSR-2's board (D-66).
   Crush-rib coupon → the ring board's fit on the ribs (0.10 / 0.15 / 0.20), record `RING_RIB`.
   `back_gauges_PLA`: take the back cover off a remote, stand each gauge across the inside, in the straight part
   where the floor is clear of the magnet plate and the side ribs; the gauge that sits on the floor and touches
   round both curves gives the round-over (D-87). The engraved line shows where the rim should be. Record it in
   `docs/MEASUREMENTS.md`; if it falls between two, ask for a finer set.
2. Update `params.py` from the measurements, `make cad check print`.
3. `insert_PLA_testfit` + `trim_PLA` → full dry fit in the box (breaker off, nothing
   connected). Check the corner taper against the box ears.
4. `insert_PC-FR` for the installed part. Keep the filament datasheet with the build record.
5. `plate_jig_PLA`: saw the supplied steel plate (D-43, D-52: one straight cut, an 18.5 mm piece
   with one round end; check its real size first).
6. Battery-free remote: `backcover_PETG` on a BILRESA (latches, the remote's magnet plate, contact
   positions, the end fingers' ramp; the plate clips and flex snap hooks snapped in PLA: snap the plate
   in and out a few times and check the clips survive in PETG, D-44; they broke in PLA). ABS (`backcover_ABS`)
   until the PETG arrives: it typically shrinks 0.5–0.7 % (PETG 0.2–0.4 %), so measure the inside against the
   model (42.0 × 67.0 mm at the rim) and try it on a remote; if it is tight, set OrcaSlicer's filament
   shrinkage from the measured shortfall.
7. EU: `eu_testbox_PLA` (test socket, D-76), then `eu_cap_PLA_testfit`, `eu_carrier_PLA` and
   `eu_trim_PLA` in it (domes, the carrier clamp, the snaps, the depth of the board stack against
   the depth markers); then `eu_cap_PC-FR`.

Many BILRESA dimensions are `ESTIMATE` (from photos and drawings, `docs/MEASUREMENTS.md`): the
first prints of the trim pockets and the back cover are for measuring and
adjusting, not final parts.

## Settings (and why)

- **Back cover** (`COVER`): back down as modelled, 3 walls (1.2 mm), 2 bottom layers (the 0.4 mm
  floor under the regulator; the magnet plate sits on the full 1.6 mm shell, D-44), 30 % gyroid, no supports (the back's round-over
  is filled to 45° below its 45° point for that).
- **EU cap**: the EU barrier, `BARRIER` settings like the NA insert, face down. The floor of the steel
  piece's recess prints as an 18.1 mm bridge (D-72); check it for sag.
- **Insert** (`INSERT`: `BARRIER` plus supports): the whole insert is barrier, so no
  modifiers are needed: 6 walls (≈ 2.7 mm, so every 1.6 mm barrier wall prints solid),
  6 top/bottom layers, 40 % gyroid, 5 mm outer brim for PC-FR (warping). Orientation: as
  modelled, lowest face (the rocker panel's underside) on the bed. Supports (normal, from
  the plate only, 40°) carry only the seal lip on the wall plane and the riser pocket's
  ceiling (D-68: no flat back; the flange's underside is a 45° taper, its land over the
  ring board 1.8 mm, the FFC channel peaked); `make check` lists those planes and
  verifies no other overhang is wider than 3 mm. Clear the supports out of the riser pocket
  and the pin holes completely: the riser and the pins must sit free.
- **Trim** (`TRIM`): face down on the textured PEI sheet (gives the face its finish).
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
  the way: PC, PC-FR, PETG (all Elegoo). OrcaSlicer has CC2 profiles for all of them but TPU 72A.
- PLA softens from about 55 °C: fine for fit checks, not for parts in a warm box or in sun.
- Insert (barrier): Elegoo PC-FR for now. Its data sheet claims flame retardancy and
  rapid self-extinguishing but states no UL94 class or test thickness. Certification is
  out of scope for this stage (human decision 2026-10-08); a spool with a stated UL94 V-0
  rating will be chosen before an installed build, and its rated thickness goes into
  `V0_RATED_T` (`make check` compares it with the thinnest barrier wall, 1.6 mm).
- Trim: PLA for tests; PETG (or ABS / ASA where it gets warm or sunny) for the installed plate.

## Checks after printing

- Remote drops in and lifts out with the finger scoops; its magnet holds onto the steel piece.
- Hold: fit the cut steel piece in its recess on the pocket coupon first. It sits 0.5 mm below
  the seat (`MAGNET_SETBACK`).
  - Too strong: add a thin non-magnetic spacer on top of it (tape, card), or
    reprint with a larger `MAGNET_SETBACK`.
  - Too weak: shim under the steel piece to bring it up to the seat.
- Rocker snaps in and latches; rocker clears the remote's back in both positions.
- Trim seats on the flange with the two key pins; island flush with the face.
- Board standoffs (D-57): tap the insert's four boss holes M3 × 0.5 (8.5 mm deep, the top right 5.5;
  keep the tap square, clear the chips), cut the top-right standoff's stud to 5 mm, screw the four
  standoffs in by hand until the hex seats on the boss, then screw the board on with the nylon M3 × 8.
- MSR-2 detection range compared with and without the radar skin.
