# Sladdseg

Sladdseg is a wall plate that replaces a traditional light switch where all bulbs on its circuit are smart bulbs (here IKEA
Matter-over-Thread). The bulbs stay powered; an IKEA BILRESA scroll-wheel remote sits recessed in the plate and lifts
out. Behind it is a hidden emergency rocker switch that cuts line and neutral to the fixtures. Two variants, three
editions:

| Edition | Contents | North American single-gang / Decora (NA): 2 × 3 in box | European round flush box, DIN 49073 (EU): Ø60 / 68 mm |
| --- | --- | --- | --- |
| **1. Switch only** | rocker switch and terminal blocks on the mains board, nothing else; the remote on its own cells and back cover | standard-size face plate 69.85 × 114.3 mm | face plate 80 × 80 mm |
| **2. Battery-free** | the mains board fully populated (rocker switch, terminal blocks, 5 V power supply); the parts that bring 5 V to the spring pins; the replacement back cover with its flex, so the remote stays in place without cells | standard-size face plate 69.85 × 114.3 mm | face plate 80 × 80 mm |
| **3. Full** | as 2, plus Apollo MSR-2 (mmWave presence, optional CO2), SHT40 temperature and humidity, push-to-talk microphone | face plate 72.2 × 131.75 mm | face plate 84.6 × 122.4 mm |

- **Remote:** stands 2.6 mm proud of the face. In editions 2 and 3 a printed replacement back cover runs it from the
  plate's 5 V through spring pins, without cells: for fixed installs, the remote stays in the plate.
- **Mains:** house wiring lands on the board in WAGO push-in blocks.
  - Rocker switch: E-Switch RA412C1100 (Marquardt 1802.2504 fits the same footprint).
  - 5 V power supply (editions 2 and 3), two parts:
    - NA: Mean Well IRM-03-5 (5 V, 600 mA);
    - EU: Zettler ZPI03S0500WC (5 V, 600 mA).
- **Sensors (edition 3):** on a board under the face plate (both variants), 5 V from the mains board.
- **Printed parts:** the barrier between mains and low voltage (NA barrier, EU barrier) in flame-retardant PC-FR; the face
  plate, EU carrier and back cover in PETG. Printed on an Elegoo Centauri Carbon 2.

Nothing here is certified or code-compliant; see `docs/SAFETY.md`.

| Document | Contents |
| --- | --- |
| `AGENTS.md` | project overview, rules, status, backlog |
| `docs/SAFETY.md` | safety notes and limits |
| `docs/DESIGN.md` | requirements and decision log |
| `docs/BOM.md` | parts per plate |
| `docs/ASSEMBLY.md` | what holds each part, assembly order, detail views |
| `docs/PRINTING.md` | print jobs, settings, order of work |
| `docs/MEASUREMENTS.md` | measured values and the ones still estimated |
| `pcb/README.md` | all seven boards: what each carries, editions, status |
| `pcb/na/README.md`, `pcb/eu/README.md`, `pcb/shared/README.md` | each variant's boards and the shared cover flex in detail: parts, nets, rules, board renders |
| `pcb/order/README.md` | DigiKey / Mouser order lists and PCBWay packs |

```bash
make system-deps     # once, Ubuntu 24.04 (KiCad 9, headless slicer libs)
make setup           # once (venv + pinned OrcaSlicer)
make pcb             # boards: ERC / DRC, STEP, fab packs
make cad check       # CAD to build/, all checks (shared parts, NA, EU)
make na              # NA variant: CAD, checks, renders
make eu              # EU variant: CAD, checks, renders
make print           # OrcaSlicer projects in print/
make renders         # docs/renders/*.png
make order           # DigiKey / Mouser lists, PCBWay packs
```

## Use

Day-to-day the lights are controlled wirelessly: the remote, Home Assistant, the IKEA app or a voice assistant. The
rocker switch is for two cases:

- **Controller or network down:** turn the rocker switch off and on. The bulbs restart and come on at their power-on
  setting, which must be set to "On" in each bulb.
- **Safety:** off cuts line and neutral to the fixtures on this circuit and powers down the plate's electronics.

> **Warning: the rocker switch does not replace the breaker.** Turn the circuit's breaker off, and check with a
> tester that the wires are dead, before working on any wiring, the plate or the fixtures.

> **Warning: polarity matters.** Connect the supply's line to **L IN** and its neutral to **N IN**, as marked on the
> board, with the load wires on **L SW / N SW** (NA) or **L LOAD / N LOAD** (EU). Earth goes to **PE** on the NA board;
> on the EU plate it is joined in the box with a WAGO 221-412 lever connector. The PSU's fuse is
> in the line; with line and neutral swapped, the fuse sits in the neutral and line stays on the PSU when it blows.
> Confirm which supply wire is line with a tester before connecting.

The microphone (full edition) streams to Home Assistant's Assist pipeline only when listening is started from Home
Assistant, for example by an automation on a remote button. There is no wake word and no speaker.

## North American single-gang / Decora

Full edition (3):

| Remote in place | Remote out, rocker switch exposed |
| --- | --- |
| ![NA full plate](docs/renders/na_front.png) | ![NA full plate, remote out](docs/renders/na_remote_out.png) |

| Half-section | Back, box side |
| --- | --- |
| ![NA half-section](docs/renders/na_section.png) | ![NA back](docs/renders/na_back.png) |

Full edition (3), exploded: remote, face plate, barrier, sensor board with the MSR-2, pin board with the spring pins on two spacer posts, four
nylon standoffs, mains board.

![NA exploded](docs/renders/na_exploded.png)

Switch-only edition (1):

| Remote in place | Remote out, rocker switch exposed |
| --- | --- |
| ![NA switch-only plate](docs/renders/na_switch_front.png) | ![NA switch-only plate, remote out](docs/renders/na_switch_remote_out.png) |

Battery-free edition (2):

| Remote in place | Remote out, rocker switch exposed |
| --- | --- |
| ![NA battery-free plate](docs/renders/na_plain_front.png) | ![NA battery-free plate, remote out](docs/renders/na_plain_remote_out.png) |

## European round flush box (DIN 49073)

The barrier closes the box and carries the remote; the mains board sits at the rocker switch's seat under it, the pin board just
under the barrier, the sensor board in a printed carrier on the wall, and the face plate snaps into the carrier.

Full edition (3):

| Remote in place | Remote out, rocker switch exposed |
| --- | --- |
| ![EU full plate](docs/renders/eu_front.png) | ![EU full plate, remote out](docs/renders/eu_remote_out.png) |

Back, box side: the mains board with its two WAGO push-in blocks (grey) and the PSU (black); the pin board sits
between it and the barrier.

![EU back](docs/renders/eu_back.png)

![EU exploded](docs/renders/eu_exploded.png)

Switch-only edition (1):

| Remote in place | Remote out, rocker switch exposed |
| --- | --- |
| ![EU switch-only plate](docs/renders/eu_switch_front.png) | ![EU switch-only plate, remote out](docs/renders/eu_switch_remote_out.png) |

Battery-free edition (2):

| Remote in place | Remote out, rocker switch exposed |
| --- | --- |
| ![EU battery-free plate](docs/renders/eu_plain_front.png) | ![EU battery-free plate, remote out](docs/renders/eu_plain_remote_out.png) |

## Battery-free back cover

For fixed installs only: the printed cover replaces the remote's own back cover and runs it from the plate with no
cells. The remote works only while it sits in the plate; lifted out, it is off. Two gold pads behind windows in the
cover's back take 5 V from the plate's spring pins, and a 3.3 V regulator on the cover's flex feeds two spring
fingers on the remote's battery contacts. It is not a charging circuit and holds no energy. A version with a battery
and a charger would be welcome as a merge or pull request.

| Cover with its flex | Exploded in the EU plate |
| --- | --- |
| ![Back cover, inside](docs/renders/bc_inside.png) | ![Back cover, exploded](docs/renders/bc_exploded.png) |

## Status

- **Ready to order:**
  - mains board (NA), mains and pin boards (EU): PCBWay packs, after the review in `pcb/na/fab/README.md` and
    `pcb/eu/fab/README.md`;
  - pin board.
- **Prototype only:**
  - NA and EU sensor boards: the MSR-2's CN2 pinout is not confirmed;
  - back cover flex: contact positions not yet measured on a remote.
- **To measure:** the `MEASURE` and `ESTIMATE` values in `docs/MEASUREMENTS.md`, from test prints and a real box.

## Cost (2026-10-12)

Parts and PCBs per plate, USD.

| Package | 1 plate | 5 plates | 100 plates | 1,000 plates | 10,000 plates |
| --- | --- | --- | --- | --- | --- |
| NA full | 111.65 | 60.03 | 37.74 | 34.31 | 32.59 |
| NA full + MSR-2 | 149.64 | 98.02 | 75.73 | 72.30 | 70.58 |
| NA full + MSR-2 with CO2 | 169.64 | 118.02 | 95.73 | 92.30 | 90.58 |
| NA switch only | 20.68 | 15.96 | 10.00 | 9.06 | 8.60 |
| NA battery-free | 68.71 | 38.63 | 24.87 | 22.61 | 21.47 |
| EU full | 102.61 | 48.95 | 31.13 | 28.37 | 26.99 |
| EU full + MSR-2 | 140.60 | 86.94 | 69.12 | 66.36 | 64.98 |
| EU full + MSR-2 with CO2 | 160.60 | 106.94 | 89.12 | 86.36 | 84.98 |
| EU switch only | 15.59 | 9.18 | 6.64 | 6.04 | 5.74 |
| EU battery-free | 60.83 | 29.26 | 19.24 | 17.55 | 16.70 |

Sources and assumptions:

- **Parts at 1, 5 and 100 (sourced):** DigiKey US list prices for the order lists' parts (`pcb/order/`), cheapest
  packaging and price break for the total need, read 2026-10-12. Per plate:
  - 1 plate: NA full 51.72, NA battery-free 33.71, NA switch only 15.68; EU full 42.17, EU battery-free 25.83,
    EU switch only 10.59.
  - 5 plates: NA full 48.04, NA battery-free 31.63, NA switch only 14.96; EU full 36.86, EU battery-free 22.26,
    EU switch only 8.18.
  - 100 plates: NA full 34.33, NA battery-free 22.64, NA switch only 9.36; EU full 27.60, EU battery-free 16.92,
    EU switch only 6.00.
- **Parts at 1,000 and 10,000 (assumption):** 10 % and 15 % below the 100-plate price. DigiKey shows no prices
  above about 100 without a quote.
- **PCBs at 1 and 5 (sourced):** PCBWay's 5-piece minimum order, 2026-10-12; one plate pays for the whole order.
  - Mains board, pin board, EU mains board, EU pin board: 5.00 each order.
  - Sensor board 24.93, EU sensor board 25.44.
  - Cover flex: about 25 (prototype price, given by the human).
  - Per plate: 1 plate NA full 59.93, NA battery-free 35.00, EU full 60.44, EU battery-free 35.00, switch only
    5.00 (the mains board alone); 5 plates one fifth of that.
- **PCBs at 100 (sourced):** PCBWay quotes for 100 pieces, 2026-10-12.
  - Mains board 0.64, sensor board 1.17, pin board 0.36.
  - EU mains board 0.64, EU pin board 0.45, EU sensor board 1.21.
  - Cover flex 1.24.
  - Per plate: NA full 3.41, NA battery-free 2.23, EU full 3.53, EU battery-free 2.32, switch only 0.64.
- **PCBs at 1,000 and 10,000 (assumption):** the 100-piece price (no quote). This is cautious: board prices
  usually fall at volume.
- **MSR-2 (assumption):** Apollo's retail price at every quantity, 37.99 base and 57.99 with CO2. No volume price
  is published.

Known gaps:

- **Quote specs differ from the design:**
  - The mains boards were quoted in standard FR4 with 1 oz copper; the design calls for high-CTI FR4 and 2 oz.
  - The pin board was quoted at 1.6 mm, not 0.8.
- **Not included:**
  - PCB assembly (the sensor board, the EU sensor board and the cover flex need it);
  - the IKEA remote;
  - printed parts, screws and heatshrink;
  - shipping and duties.
- **Cheaper terminal blocks:** Same Sky TBL-0021-500-06GR (NA) and TBL-0020-500-02GR (EU), push-in without a lever,
  fit the WAGO 2604 footprint and cost about 5–6 (NA) and 3 (EU) less per plate at 100. Not in the design.

### Printed parts (own printer, 2026-10-12)

The barrier part (NA barrier, EU barrier) is printed in Elegoo PC-FR; the face plate, the EU carrier and the back cover
in Elegoo PETG. Grams and times come from the OrcaSlicer projects (`make print`). USD per plate.

| Package | Printed parts | Filament | Print time | Filament cost | Electricity | Printer wear | **Total** |
| --- | --- | --- | --- | --- | --- | --- | --- |
| NA full | barrier 51.9 g PC-FR; face plate 23.2 g, back cover 8.3 g PETG | 83.4 g | 3.3 h | 1.54 | 0.08 | 0.29 | **1.91** |
| NA switch only | barrier 51.3 g PC-FR; face plate 16.0 g PETG | 67.2 g | 2.6 h | 1.36 | 0.06 | 0.23 | **1.65** |
| NA battery-free | barrier 51.7 g PC-FR; face plate 16.0 g, back cover 8.3 g PETG | 76.0 g | 3.0 h | 1.46 | 0.07 | 0.27 | **1.80** |
| EU full | barrier 9.8 g PC-FR; face plate 42.9 g, carrier 18.1 g, back cover 8.3 g PETG | 79.1 g | 2.7 h | 0.99 | 0.06 | 0.24 | **1.29** |
| EU switch only | barrier 9.7 g PC-FR; face plate 27.2 g, carrier 4.6 g PETG | 41.5 g | 1.5 h | 0.57 | 0.03 | 0.13 | **0.73** |
| EU battery-free | barrier 9.8 g PC-FR; face plate 27.2 g, carrier 4.6 g, back cover 8.3 g PETG | 49.9 g | 1.9 h | 0.67 | 0.04 | 0.16 | **0.87** |

Sources and assumptions:

- **Filament (sourced):** Elegoo US store, 10 kg packs, read 2026-10-12.
  - PC-FR: 229.99, 23.00 / kg (1 kg spool 34.99).
  - PETG Pro: 109.99, 11.00 / kg (1 kg spool 13.99).
- **PETG weights (assumption):** the face plates and carriers are sliced in PLA only. Their weight is scaled by
  the density ratio (PETG 1.27 / PLA 1.24) at the same print time.
- **Electricity (assumption):** 150 W average at 0.15 / kWh.
- **Printer wear (assumption):** about 440 for the CC2 Combo (Elegoo's bundles list at 435–499) over 5,000 print
  hours.
- **Not included:** labour, failed prints, bed adhesive.
- **Print services:** not quoted.
