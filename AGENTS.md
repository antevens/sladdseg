# AGENTS.md — Sladdseg, a smart wall plate (BILRESA + MSR-2 + emergency switch)

Read this whole file before changing anything. Then read `docs/SAFETY.md`.
`docs/DESIGN.md` has the requirements and the decision log; `docs/BOM.md` the
parts.

## What this project is

A replacement for a light switch in a house where every bulb is an IKEA Matter-over-Thread smart bulb. Bulbs stay
powered; control is wireless. Two variants, equal in every respect: **NA** for a North American single-gang box
(Decora/Leviton; Canada, BC) and **EU** for a European round flush box (DIN 49073). Each plate holds:

- an **IKEA BILRESA scroll-wheel remote**, kept intact (batteries in), in a pocket in the barrier; the adhesive steel
  plate supplied with it, cut to an 18.5 mm piece (D-43, D-52), sits in a recess in the pocket floor and the remote's
  internal magnet holds onto it; the remote lifts out;
- a **hidden emergency rocker** behind the remote (Marquardt 1802.2504, DPST, PCB pins, D-26) breaking line and
  neutral of the lighting load. Off = bulbs AND sensors de-powered. Off→on with bulbs set to power-on "On" = lights
  on when Home Assistant is down;
- a printed **barrier** (UL94 V-0) between the mains volume and the low-voltage side: an barrier in the NA box, a barrier
  over the EU box;
- a **mains board** (D-24, D-25, D-36) carrying the rocker, WAGO 2604 push-in blocks for the house wiring and a
  certified 5 V PSU fed from the **switched side** (NA: Mean Well IRM-03-5; EU: Zettler ZPI03S0500WC);
- a **sensor board** (D-50, D-68, D-70) under the face plate, 5 V from the mains board (NA: stock FFC; EU: spring
  pins). On it:
  - an **Apollo MSR-2** (ESP32-C3 + LD2410B mmWave, ESPHome over Wi-Fi) on its rear connector (CN2), in a bay
    above the remote behind a 0.6 mm radar skin (D-51);
  - an **SHT40** temp/humidity sensor in its own vented bay below the remote (I²C from the MSR-2);
  - a **top-port PDM MEMS microphone** (Knowles SPK0641HT4H-1) with an **ADAU7002** PDM-to-I²S converter beside it
    (the ESP32-C3 has no PDM input), under the face plate's sound column to a hole in the face skin, push-to-talk
    voice to Home Assistant started from HA (D-29, D-83);
- a passive **face plate**: no electronics, no contacts (EU: snapped into a printed carrier that holds the sensor
  board);
- for the battery-free remote, **spring pins** on a **pin board** (NA: on two spacer posts from the mains board's
  5 V area; EU: on the 5 V header from the mains board), through the pocket floor onto pads on the replacement back
  cover (D-35, D-50, D-54).

Three editions of each variant (D-109, D-122): switch only, battery-free, full.

Home Assistant runs on an Nvidia Orin NX. No Shelly / smart relay: deliberately
removed.

## Repository layout

```text
AGENTS.md            this file (CLAUDE.md imports it)
docs/                DESIGN (requirements + decisions), SAFETY, BOM,
                     MEASUREMENTS (placeholders to fill), PRINTING, ASSEMBLY (what holds each part), renders/
cad/build123d/       ACTIVE parametric CAD (Python, build123d); the parts both variants share at the top
  params.py          geometry both variants share (remote, back cover, rocker, MSR-2, mic, pins)
  backcover.py       replacement back cover geometry (D-35, D-50, D-79)
  bilresa.py         BILRESA remote model (rounded back, wheel; MEASURE sizes)
  msr2.py            Apollo MSR-2 + SCD40 CO2 add-on model (datasheets, Apollo's case, photo estimates; D-64)
  plate_jig.py       hacksaw guide for cutting the supplied steel plate (D-52, D-81)
  common.py          small geometry helpers shared by the printed parts
  kicad_board.py     reads footprint placement from a board's .kicad_pcb
  checks.py          checks of the shared parts and the helpers both variants' checks use
  render.py          pyvista render helpers; render_shared.py the shared parts' renders (bc_*, msr2_*, ...)
  export.py          print-oriented STLs of every printed part -> build/print/
  na/                NA variant (single-gang box): params_na, barrier_na (the barrier: ALL barrier geometry,
                     rocker panel, UL94 V-0), face_plate_na, sensor_board_na (sensor board, its parts, pin board,
                     spring pins, spacer posts), standoff_na (Keystone 25503 nylon standoffs, D-57), jumper_na
                     (5 V FFC, D-50), coupons_na (test-fit coupons), assembly_na, checks_na, render_na,
                     sections_na (`make na`)
  eu/                EU variant (round DIN 49073 box, D-30): params_eu, barrier_eu (the barrier: V-0 barrier),
                     face_plate_eu, sensor_board_eu (sensor board, carrier, MSR-2 on CN2), boards_eu (mains and pin
                     board envelopes), testbox_eu (printed test socket, D-76), checks_eu, render_eu (`make eu`)
cad/tools/           sections.py (section renders for review), check_renders.py (render inventory)
pcb/                 all boards (README: overview)
  na/                NA mains board, sensor board, pin board: kicad/, tools/ (edit parts_na.py, lv_parts_na.py),
                     fab/ (PCBWay packs, review checklist)
  eu/                EU mains board, pin board, sensor board: kicad/, tools/ (edit parts_eu.py, lv_parts_eu.py), fab/
  shared/            back cover flex (kicad/, tools/lv_parts.py) and the low-voltage board generator (tools/gen_lv.py)
  tools/             helpers every generator uses (kigen, fplib, common_parts, gen_3d), render_bare, order tools
  order/             DigiKey / Mouser order lists for test plates (`make order`, tools/order_bom.py; stock and
                     upload: tools/distributors.py)
print/               OrcaSlicer projects (*.3mf) for the CC2, slice.py, profiles/
reference/v0.1-openscad/  FROZEN first pass (OpenSCAD). Do not edit.
build/               generated outputs (git-ignored): build/na/, build/eu/, build/print/
scratch/             git-ignored: 3d/ vendor STEP models (read by pcb/tools/gen_3d.py),
                     sources/ datasheets, FCC photos, remote photos
```

## Commands

```bash
make system-deps # apt: KiCad 9, venv, headless OrcaSlicer libs (Ubuntu 24.04)
make setup       # venv + requirements + pinned OrcaSlicer in .tools/ (once)
make pcb         # every board, NA, EU and shared: ERC + DRC, fab packs
make cad         # STEP/STL into build/, print STLs into build/print/
make check       # shared parts, NA and EU: geometry, barrier, board fit, printability, render inventory - must pass
make print       # OrcaSlicer projects + G-code (SLICER=... overrides the pin)
make renders     # docs/renders/*.png: every group whose sources changed (NA, EU, shared parts, boards)
make check-renders  # no render older than its sources, every render used by a doc - must pass
make na          # NA variant: CAD to build/na, NA checks, NA renders
make eu          # EU variant: CAD to build/eu, EU checks, EU renders
make order       # DigiKey / Mouser CSVs: one NA plate, one EU plate, a devkit (5 NA + 5 EU); PCBWay devkit packs
make stock       # live DigiKey / Mouser stock and lifecycle, parts rule D-84 (keys: pcb/order/README.md)
make order-push  # DigiKey myLists link + Mouser cart: 1 NA plate by default (VARIANT=na|eu|both, PLATES, PRIMARY)
```

KiCad 9.x (`kicad-cli` on PATH). `pcb/na/tools/build.sh`, `pcb/eu/tools/build.sh` and `pcb/shared/tools/build.sh`
run the generators with KICAD_PYTHON (default `python3`, needs `import pcbnew`) and the 3D envelopes with CAD_PYTHON
(default `.venv/bin/python`). Each gates on every board of its folder, for example:

```bash
kicad-cli sch erc --severity-all --exit-code-violations pcb/eu/kicad/eu_mains_board.kicad_sch
kicad-cli pcb drc --severity-all --schematic-parity --exit-code-violations pcb/eu/kicad/eu_mains_board.kicad_pcb
```

## Conventions

- Units: millimetres. Coordinates: X width, Y up, Z out of the wall; z=0 = wall
  surface; z<0 = inside the box = **mains side**.
- Nothing may be soldered or plugged between the face plate and the barrier: every
  electrical interface across that split is a spring ("pogo") contact (DESIGN R9).
- 5 V connections, NA and EU: prefer spring ("pogo") contacts between boards and modules. Use a
  flex with a latching connector and room for hands only where spring contacts cannot reach,
  and record why in DESIGN (R10; NA 5 V stock FFC, D-50).
- Mains connections: house wiring and every mains lead end in WAGO push-in terminals on the
  board; no soldered mains leads (R10).
- Every dimension lives in the params files: `cad/build123d/params.py` for what both variants share,
  `na/params_na.py` and `eu/params_eu.py` for each variant. Never hard-code a number in a model that belongs in
  params. The boards are generated from the part files in `pcb/<variant>/tools/`; the board positions the CAD uses
  are mirrored in the params (NA: `MB`, `WAGO_*`, `IRM_C`, `J2_POS`; EU: `PB_MOUNT`, `MB_BOSS`, `MB_HDR`, ...), and
  `make check` compares them with the board files and STEP. Change both together.
- Variants are equal: name a file, render, print job or board by what it is with an `na_` / `eu_` prefix or
  `_na` / `_eu` suffix, never one variant bare; parts both use stay unprefixed (D-125).
- Values tagged `MEASURE` are placeholders. **Do not replace them with guesses
  or values "found online".** Only use readings recorded in
  `docs/MEASUREMENTS.md` or datasheet values with a cited source. If a task
  needs one that is missing, stop and ask.
- Values tagged `ESTIMATE` were taken from photos and drawings at the human's
  request (2026-10-08; sources in `docs/MEASUREMENTS.md`). Treat them like
  `MEASURE`: replace each with a caliper reading before printing anything final.
- Keep `make check` green; extend `checks()` when you add a constraint.
- Renders: after any change run `make renders`; `make check-renders` must pass before a render, view or
  design state is reported as current. A view that is dropped from a render script is deleted from
  `docs/renders/` in the same change; a part or route the human rejects is removed from the model (or the
  render marked superseded in the doc that shows it) in the same change, not left for a later rebuild.
- Commit only with the human's explicit approval (see Working rules); then keep
  commits small, one concern each. Update the `docs/DESIGN.md` decision log for
  any design decision.
- Versions: work happens on `main`. At each version bump, tag the last commit of the
  old version `vX.Y` and leave a branch `vX.Y` at it (human, 2026-10-12); tags and
  branches, like commits, only with the human's approval.

## Working rules

General rules for any agent working in this repo.

- Before trying to update a file, always read it first to ensure you have the
  correct content.
- Do not commit or push changes without explicit user approval.
- After modifying any code, I must verify the syntax to ensure correctness and
  prevent regressions.
- The user prefers an iterative approach to problem-solving: trying a simple
  solution first and then refining it, rather than implementing a comprehensive
  solution from the start.
- Don't show any prompts about thinking or effort or problem solving, just show
  the raw data and numbers.
- Don't use flattery or behave like a sycophant, only state the facts.
- Never ever include any co-authored by or mention of the AI tool being used in
  commit messages, comments or design docs.
- Keep comments short and to the point, don't include historical data or
  reasons for a strategy, comment on what the code does currently.
- Don't create .github files or directories, we don't use GitHub
- Never use words like Pondering, Picturing, Crystalizing, Verifying, Picturing,
  Identifying, Calibrating, Leavening, Thinking, Canoodling, Swooping,
  Befuddling, Billowing, Creating, Reticulating, Propagating, Frolicking,
  Pouncing, Doodling, Cogitaded, Reticulating, Churned, Jitterbugging, Cooked,
  Infusing, Metamorphosing, Flibbertygibbering, Tomfoolering, Puttering,
  Tinkering, Choreographing, Percolating Blanching, Booping, Ebbing,
  Perambulating, Simmerting don't make up words or use ones that don't apply,
  stick to facts.
- Don't use phrases like "high effort", "almost done", "still thinking",
  "thinking more", stick with facts.
- Don't hack things, don't take shortcuts, do the proper thing according to
  best established software engineering principules.

### Languages Rules

- Always check for trailing white spaces and trailing new-lines and remove
  where possible.

#### Shells

- The user prefers bash over bourne and zsh shells
- The user requires keyword based function definitions in shell scripts.
- The user requires the Google shell style guide for shell scripts.
- The user prefers all internal variables in shell scripts be lower case but
  all external/environment variables be upper case.
- The user prefers all shell scripts pass a shellcheck syntax check.
- When using external commands in bash to populate an array use mapfile where
  possible, replace existing readarray references to use mapfile.
- Avoid using IFS based shell commands where possible

#### Golang

- Always check the version of external dependencies and modules and pick the
  latest stable version.
- Always check if the depenedency already exists and if it's not the latest
  prompt the user to ask to upgrade
- Always check for white spaces instead of tabs in code, use gofmt to correct
  formatting and warn the user

#### Markdown Files

- Always make sure to write the content in the following format:
- Use headings, subheadings, bullet points, and numbered lists where
  appropriate.
- There should be **ATLEAST** 1 empty line used to separate different sections
  for better readability and to avoid re-working on linting errors.
- Use proper Markdown syntax for links, images, and other elements.
- Ensure that code blocks are properly formatted with triple backticks and the
  correct language specified (**ALWAYS**).

### Dockerfiles

- When editing Dockerfiles always make sure changes are being performed in the
  right stage if it's a staged build so changes either make it into build
  phases as required or into the final image

### Kubernetes & Docker

- Never ever use node-shells or execute anything directly on the node, you are
  not allowed to access the underlying host in any way or interface directly
  with host devices other than network cards using SR-IOV or DPDK

### Helm

- Entries in values.yaml that have defaults should not be set to an empty
  string but should rather bet commented out.
- A non-present value should always be represented with a nil, not an empty
  string, logic checks should be explicit about the difference between the two.
- README.yaml in a helm chart is visible to customers, it should never include
  git information or other development references, installations from local
  exploded charts, etc, it should reference tagged builds with semantic
  versions.

## Hard constraints

Do not violate these; ask the human if a task seems to require it.

1. **Mains mains board (D-23, human decision 2026-10-07).** The lighting
   circuit's line, neutral and ground (PE) enter and leave on the PCB through
   listed push-in terminals: L in → certified rocker → switched L out, N in → N
   out, PE in → PE out. Only the rocker switches the load. Every mains path,
   PE included, is sized for 15 A continuous (IPC-2221, ≤10 °C rise) and for
   fault current until the branch breaker trips. Line copper on one side of the
   board, neutral on the other, PE copper along both sides.
2. **Barrier continuity (D-80).** NA: the barrier's pocket shell + switch
   well + collar separate the mains volume (box) from the low-voltage volume
   (plate hollow, remote pocket). No openings may be added except the single 5 V
   FFC bore (D-74) and the two spring-pin holes in the pocket floor, each filled
   by its pin's barrel (D-50, human decision 2026-10-10). EU: the barrier is the whole
   barrier; its only openings are the four spring-pin holes, each filled by its
   pin's barrel (D-54, D-59), and the two device-screw holes, each filled by its
   screw. On both, the rocker's panel cutout is closed by the rocker body.
   A slot through a barrier part entirely above the wall plane, between two
   low-voltage spaces, is not an opening in the barrier; `make check` /
   `make eu` keep it above z 0 and the mains-air check must still pass.
   Anything forming the barrier is printed in a UL94 V-0 filament (see PRINTING).
3. **PCB isolation (D-24, D-102).** Designed for EU/UK (EN/BS EN 62368-1, IEC 60664-1)
   and US/CA (UL/CSA 62368-1), 270 V working, overvoltage category III,
   pollution degree 2, on high-CTI FR4 (CTI ≥ 600, material group I) for the mains
   boards, using the stricter table in each case:
   L–N and L–L(switched) ≥3.0 mm, L or N to PE ≥3.0 mm, mains to the 5 V side
   ≥8.0 mm plus a routed slot under the PSU (reinforced). Clearance and
   creepage both. Exception: between the pins of a certified part rated for
   ≥270 V at OVC III / PD2 (e.g. the WAGO 2604 terminal block, the rocker), the
   part's own pin spacing applies, using the maker's recommended footprint.
   These are design targets, not a compliance claim — flag them for human
   review, don't certify.
4. **Bought-in, certified parts carry the safety-critical jobs**: rocker
   (CSA/UL; ENEC to be confirmed), the PSUs Mean Well IRM-03-5 (NA, cURus/CB/TÜV) and Zettler
   ZPI03S0500WC (EU, UL/EN 62368-1). Don't substitute
   uncertified parts on the mains side.
5. Never describe the device as code-compliant, certified, or safe to install.
   Say what was checked. Energising anything mains-side is a human decision.

## Current status (v0.6)

The decision log in `docs/DESIGN.md` (D-50..D-79 for v0.4, D-80..D-119 for v0.5, D-120 on for v0.6) has the history.

NA: barrier (the insert, PC-FR) and passive face plate; mains board (rocker, WAGO block, PSU,
J2) on four nylon standoffs (D-57), ERC/DRC clean, PCBWay pack in `pcb/na/fab/na_mains_board/`; sensor board on the
barrier's collar (crush ribs, D-68) with the MSR-2 on CN2, the SHT40 and the microphone + ADAU7002 (D-83); 5 V over
a stock FFC through one straight bore (D-74); battery-free remote on two Harwin P70 spring pins
from a pin board on two spacer posts (D-59, D-60, D-79).

EU: barrier (the cap, PC-FR), mains board and pin board (PCBWay packs in `pcb/eu/fab/`); sensor board on a
printed carrier pinned to the wall by the barrier (D-70, D-71), the MSR-2 straight on it; face plate
snapped into the carrier (D-77); steel piece in the barrier's pocket floor (D-72); printed test socket
(D-76).

Both variants: replacement back cover with regulator, pads and spring fingers (D-35, D-41, D-79); KiCad for
the sensor boards and the cover flex (ERC/DRC clean; fab packs for the pin boards and the mains boards); the
microphone on both sensor boards, no carrier (D-83); OrcaSlicer projects for every printed part (`print/`); what holds each
part in `docs/ASSEMBLY.md`.

Editions (D-109, D-122): full (above), battery-free (rocker and battery-free remote) and switch only, NA and EU: plain barriers, plain
face plates (NA 69.85 × 114.3 mm, EU 80 × 80 mm), EU plain carrier; same boards less the sensor parts; checks, print
jobs and order lists for both.

Not done: caliper readings for the `MEASURE` and `ESTIMATE` values (several measured
by the human 2026-10-09, see `docs/MEASUREMENTS.md`), test prints (under way),
human review of the PCB checklists (`pcb/na/fab/README.md`, `pcb/eu/fab/README.md`),
the MSR-2's CN2 contact map and pin 1 (part assumed: Molex 55909-2474 on a 51338-2474, D-82; land pattern from Molex's drawing, D-89; blocks both sensor boards' fab files),
the cover flex's fab files (`COVER_CONFIRMED`), PC-FR datasheet (`V0_RATED_T`), ESPHome configuration.

## Backlog (in order)

1. **Measurements and test prints** – help the human fill `docs/MEASUREMENTS.md`
   (coupons first: the rocker ladder gives `SW_PANEL_T`, the crush-rib coupon `SB_RIB`; then the
   PLA barrier and face plate, the back cover on a remote, the EU barrier, carrier and face plate in the test socket),
   update params, `make cad check print`. Replace `ESTIMATE` values as readings come in.
2. **CN2 (D-50, D-51, D-82, D-89)**: part assumed (Molex 55909-2474 plug, 51338-2474 on the MSR-2); land pattern
   from Molex's drawing (D-89); the contact map and pin 1 (from a GPIO add-on or Apollo); until then the
   sensor board and the EU sensor board have no fab files. Microphone (D-83): pin 1 of the mic and the
   ADAU7002 against parts, firmware test on an MSR-2 (16 kHz, I²S slot, C3 load).
3. **Human review** of the PCB (`pcb/na/fab/README.md` checklist: F1 rating,
   isolation, thermal, approvals) before ordering from PCBWay.
4. Dry-fit prints (PLA barrier + face plate) in a real box; check the corner taper vs
   box ears and the wire room behind the board. Then the PC-FR barrier.
5. Rocker feel: confirm the panel thickness and that the latches hold.
6. ESPHome YAML for MSR-2 + SHT40 + microphone (starting point in
   `pcb/shared/README.md`), once the CN2 contact map is known.
7. Later: UK (86 mm, shallow back box) variant; versions for the BILRESA
   dual-button remote (E2489, outline and cells recorded from IKEA's drawing);
   jumbo-plate option; the EU stack in a real 47 mm box (the printed test socket, D-76,
   has markers at 40, 43, 60 and 63 mm). If the face plates are ever injection moulded: a front edge rounded
   into the window / remote cutout (human, 2026-10-12; FDM face-down cannot print a round tangent to the bed).
8. Plain plates (D-109, modelled): test prints of the plain barrier / face plate (NA) and the plain barrier, carrier and
   face plate (EU); the NA plate's 1.11 mm side wall beside the barrier's flange on the print.

## Open questions for the human

- Box material (metal ears intrude + may shield the remote's radio) and depth
  per room.
- Neutral present in each switch box? (required for the PSU)
- MSR-2: the CO₂ version is modelled (D-64) on the assumption that it is the one used;
  bare-board dimensions; confirm the MSR-2's CN2 is a Molex 51338-2474 (D-82).
- Inspector's view on a concealed emergency switch (BC homeowner permit).
- F1 fuse rating (T1A chosen, Mean Well gives none) and PCB isolation review.
- Elegoo PC-FR datasheet: V-0 test thickness.
