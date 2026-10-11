# Smart wall plate

Replacement for a single-gang light switch: recessed IKEA BILRESA remote, hidden
emergency rocker, Apollo MSR-2 mmWave presence + SHT45 climate + a push-to-talk
microphone for Home Assistant voice, powered by a Mean Well IRM-03-5 on the wiring board.

Start with `AGENTS.md` (for people too), then `docs/SAFETY.md`. `docs/PRINTING.md` lists the print
jobs in order, `docs/ASSEMBLY.md` what holds each part, `docs/MEASUREMENTS.md` what is measured and
what is still an estimate.

Two variants: **NA** (single-gang Decora box, this page's main renders) and **EU** (round DIN 49073
box, `cad/build123d/eu/`, `pcb/eu/`). Both can run the BILRESA without batteries through a
replacement back cover powered from the plate.

The plate is two printed parts: a **box insert** (all mains/low-voltage barrier
geometry, UL94 V-0 PC-FR) and a passive **trim plate** (PLA for tests; PETG/ABS/ASA installed), for an Elegoo Centauri
Carbon 2. The sensors sit on a **ring board** pressed onto the insert's collar, under the face plate (v0.4, D-50, D-68).

The house wiring lands on one board: L/N/PE in and out on a WAGO push-in block,
the Marquardt 1802.2504 DPST emergency rocker, and the PSU, all in a 2.5"
single-gang box. The KiCad project is in `pcb/`.

```bash
make system-deps     # once, Ubuntu 24.04 (KiCad 9, headless slicer libs)
make setup           # once (venv + pinned OrcaSlicer)
make cad check       # CAD -> build/, all checks must pass
make print           # OrcaSlicer projects -> print/*.3mf
make pcb             # all boards and flexes: ERC/DRC, STEP, PCBWay packs -> pcb/fab/, pcb/sensor/fab/, pcb/eu/fab/
make eu              # EU variant: CAD, checks, renders
make renders         # docs/renders/*.png
```

Nothing here is certified or code-compliant; see `docs/SAFETY.md`.

## How it is meant to be used

The design assumes every light bulb and device on the switched circuit is a smart
device that turns itself on and off (here IKEA Matter-over-Thread bulbs). The circuit
stays powered; day-to-day control is wireless: the BILRESA remote in the plate, Home
Assistant, the IKEA app, or Alexa / Google / other assistants.

The rocker hidden behind the remote is not the everyday light switch. It is there for
two cases:

- **Controller or cloud down.** When Home Assistant, the IKEA hub or the voice
  assistant is unavailable, turn the rocker off and on again. The bulbs restart and come
  on by themselves at their built-in power-on brightness. This needs each bulb's power-on
  behaviour set to "On" (D-8); check it per bulb.
- **Safety.** Off cuts line and neutral to the fixtures on this circuit (and powers down
  the plate's sensors), for example when a bulb or fixture misbehaves or needs changing.
  It is not a substitute for the breaker: turn the breaker off before working on any
  wiring (`docs/SAFETY.md`).

Voice: the plate's microphone streams to Home Assistant's Assist pipeline only when
listening is started from Home Assistant, for example by an automation on a BILRESA button
(D-29). There is no wake word and no speaker in the plate; replies go to another device.

Plain (non-smart) bulbs on this circuit would just follow the rocker, and the remote,
the sensors and the automations could not control them.

## Renders

### v0.4

Shaded views of the assembly: face plate (white), box insert (grey), BILRESA remote (model), Marquardt
1802.2504 rocker (red), wiring board (green, KiCad model), ring board (green) on the insert's collar
with the MSR-2 (black), the mic carrier and the SHT45, nylon board standoffs. Regenerate with `make renders`.

| Front | Remote lifted out |
| --- | --- |
| ![v0.4 front](docs/renders/v0.4_front.png) | ![v0.4 remote out](docs/renders/v0.4_remote_out.png) |

| Half-section | Back, mains side |
| --- | --- |
| ![v0.4 half-section](docs/renders/v0.4_section.png) | ![v0.4 back](docs/renders/v0.4_back.png) |

Exploded: remote, face plate, insert, ring board with the MSR-2, riser with the spring pins on the spacer
posts, the four nylon board standoffs (D-57), wiring board.

![v0.4 exploded assembly](docs/renders/v0.4_exploded.png)

Face plate lifted off (see-through): it carries nothing but plastic; the ring board, the MSR-2, the mic
carrier and the SHT45 stay on the insert (D-50, D-68).

![v0.4 face plate lifted off](docs/renders/v0.4_face_off.png)

Ring board from the front, red where copper may not go (8 mm along the wall from the box opening): the
MSR-2 on CN2 and three SMT spacers, J1 for the FFC, the mic carrier at the top right, the SHT45 at the bottom.

![v0.4 ring board](docs/renders/v0.4_ring.png)

5 V power path (insert cut at the pass-through, seen from the right): a stock 6-way FFC from J2 on the
wiring board runs between the rocker and the top-right standoff to a straight bore in the insert's top-right corner
(an open groove in the corner taper, then closed from 4.4 mm under the wall plane, D-74), one bend into a flat slot and
out of the flange onto the ring board to J1; its spare
length lies folded flat beside J1 (D-68). Both ends latch (Hirose FH12, slide lock).

![v0.4 5 V power path](docs/renders/v0.4_power.png)

Battery-free remote: two spring pins on the riser board, which stands on the two spacer posts from the
wiring board's 5 V area, through the pocket floor onto the pads of the replacement back cover.

| Exploded | Section through the pins |
| --- | --- |
| ![v0.4 battery-free](docs/renders/v0.4_battery_free.png) | ![v0.4 spring pins](docs/renders/v0.4_pins.png) |

Microphone (D-29, D-50): the bottom-port I²S mic under its carrier, hanging into a window in the ring
board, the port up through the carrier into the face plate's sound tube (gasket on the carrier).

![v0.4 microphone sections](docs/renders/v0.4_mic_section.png)

BILRESA model: stadium outline, wheel with its gap ring, three LEDs, side
parting line, and a back that curves from a flat central pad out to the sides.

| Front | Back |
| --- | --- |
| ![BILRESA model, front](docs/renders/bilresa_model.png) | ![BILRESA model, back](docs/renders/bilresa_back.png) |

MSR-2 model with the SCD40 CO2 add-on (`cad/build123d/msr2.py`, D-64): board, ESP32-C3-MINI-1 over its antenna
notch, USB-C, LD2410B radar on its header, CN1 with the add-on and the SCD4x, Boot / RST switches on the back. Sizes
from the datasheets, the board plane and limits from Apollo's case; part positions are estimates from Apollo's photos.

| Front | Back |
| --- | --- |
| ![MSR-2 model, front](docs/renders/msr2_front.png) | ![MSR-2 model, back](docs/renders/msr2_back.png) |

Cross-sections of every v0.4 part (legend under the sheet, each panel titled with what it shows). The dashed
line is the wall surface.

![v0.4 assembly cross-sections](docs/renders/v0.4_sections.png)

### v0.4 wiring board

KiCad renders of `pcb/`. The front faces the plate (rocker, SMD
fuse and MOV, 5 V connector J2, the two SMT spacer posts below it); the back faces the box (WAGO block, PSU). The four
corner holes take the insert's nylon standoffs (M3 screws from the back); they are unplated with no copper round
them, and the PE ring detours round them, so earth continuity never depends on the standoffs or on vias.

| Front | Back |
| --- | --- |
| ![Wiring board, front](docs/renders/wiring_board_front.png) | ![Wiring board, back](docs/renders/wiring_board_back.png) |
| ![Wiring board, front, angled](docs/renders/wiring_board_iso_front.png) | ![Wiring board, back, angled](docs/renders/wiring_board_iso_back.png) |

Without components, so every trace and pour shows:

| Front | Back |
| --- | --- |
| ![Wiring board, bare front](docs/renders/wiring_board_bare_front.png) | ![Wiring board, bare back](docs/renders/wiring_board_bare_back.png) |
| ![Wiring board, front copper](docs/renders/wiring_board_copper_front.png) | ![Wiring board, back copper, seen from behind](docs/renders/wiring_board_copper_back.png) |

![Wiring board, bare, angled](docs/renders/wiring_board_bare_iso.png)

### EU variant (concept, D-30, D-36)

A separate design for a round EU flush box (68 mm hole saw, Ø60 inside); `make eu`, `cad/build123d/eu/`,
`pcb/eu/`. The remote sits on a V-0 cap over the box, 2.6 mm proud of the face as on the NA plate (D-70); the emergency rocker (Marquardt 1802.2504,
as on the NA plate) under it is hidden until the remote is lifted out. Two boards: a mains board at
the rocker's PCB seat (rocker, two WAGO push-in blocks, fuse, MOV, PSU over a routed relief slot,
5 V island with a header) and a 5 V board just under the cap (pin socket on the header, four spring pins
up through the cap: two for the battery-free back cover, two onto a cap board). The sensors sit on the
cap side, nothing in the face plate and no flex (D-56, D-59, D-70): a 1.6 mm FR4 cap board in a printed
carrier with the MSR-2 on its CN2 mate and three SMT spacers, the microphone and the SHT45, as on the NA ring
board. The carrier goes on the wall first; the cap's edge pins its lip to the wall and the cap's teeth stop it
turning (D-71). The face plate snaps into the carrier: four fingers at the corners catch grooves in closed, keyed
windows (D-77). The plate is 84.6 × 122.4 mm, 19.0 mm thick (D-70, D-78). Box values are catalogue placeholders
until measured; the stack reaches 43.8 mm deep, to be tried in the printed test socket (D-76) and a real box.

| Remote in place | Remote lifted: rocker |
| --- | --- |
| ![EU plate](docs/renders/eu_front.png) | ![EU plate, remote out](docs/renders/eu_remote_out.png) |
| ![EU section](docs/renders/eu_section.png) | ![EU box from behind](docs/renders/eu_box.png) |

![EU exploded](docs/renders/eu_exploded.png)

The sensors' side with the face plate and remote off: the carrier round the cap, the cap board in it with the MSR-2 on
CN2 and its spacers, the mic carrier, the SHT45.

![EU sensors](docs/renders/eu_sensors.png)

The carrier clamp (D-71) from the wall side: the cap's teeth at the snap angles in the gaps of the carrier's lip;
section at the top: the lip under the cap's rebate, outside the seal band.

| Wall side | Section |
| --- | --- |
| ![EU carrier clamp](docs/renders/eu_carrier_clamp.png) | ![EU carrier lip](docs/renders/eu_carrier_lip.png) |

| Sensor pins onto the cap board's pads | Face plate snap: finger, bump in the groove of the carrier's window |
| --- | --- |
| ![EU sensor pins](docs/renders/eu_sensor_pins.png) | ![EU snap](docs/renders/eu_snaps.png) |

| Cap board, front copper | Cap board, back copper |
| --- | --- |
| ![EU cap board, front copper](docs/renders/eu_cap_board_copper_front.png) | ![EU cap board, back copper](docs/renders/eu_cap_board_copper_back.png) |

| Mains board, front | Mains board, back |
| --- | --- |
| ![EU mains board, front](docs/renders/eu_mains_board_front.png) | ![EU mains board, back](docs/renders/eu_mains_board_back.png) |
| ![EU mains board, front copper](docs/renders/eu_mains_board_copper_front.png) | ![EU mains board, back copper](docs/renders/eu_mains_board_copper_back.png) |

| 5 V board, front | 5 V board, back |
| --- | --- |
| ![EU 5 V board, front](docs/renders/eu_5v_board_front.png) | ![EU 5 V board, back](docs/renders/eu_5v_board_back.png) |
| ![EU 5 V board, front copper](docs/renders/eu_5v_board_copper_front.png) | ![EU 5 V board, back copper](docs/renders/eu_5v_board_copper_back.png) |

### Steel plate hacksaw guide (D-52, D-81)

The steel plate that ships with the BILRESA is cut to an 18.5 mm piece for the insert (NA) or the cap (EU) in a hacksaw
guide: clamp it in a vise, saw down the slot. Red: the cut line.

![Steel plate hacksaw guide](docs/renders/plate_jigs.png)

### Replacement back cover (D-35, D-40, D-41, D-44, D-45)

Runs the remote without cells. The printed cover snaps onto the remote like the original (clips at
the top and bottom, side ribs, a pry notch) and carries the remote's magnet plate inside a ridge, clipped at both ends,
and a flex: two gold pads behind windows in its back take +5 V and GND from the plate (NA: the spring pins
through the pocket floor, D-50; EU: two spring pins from the 5 V board through the cap, D-54), a 3.3 V regulator on the flex feeds the
remote, and at the terminal end two spring fingers press on the remote's VBAT plate and GND spring. The flex is
held by a 0.8 mm stiffener under five snap hooks on its long edges, its run lies in a notch along the GND contact
post (D-79) and, at the end, a lip at the foot of each contact block and a slot along each block's outer face that it
slides down into hold it. Several remote dimensions are still estimates
(`docs/MEASUREMENTS.md`).

| Cover, inside | Cover, back (pin windows) |
| --- | --- |
| ![Back cover, inside](docs/renders/bc_inside.png) | ![Back cover, back](docs/renders/bc_back.png) |

Exploded in the EU plate: remote, cover, the battery-free pins through the cap:

![Back cover, exploded](docs/renders/bc_exploded.png)

Cut through a pin pad: the spring pin at mid-stroke through its window onto the pad, ledge, flex. And
through the VBAT contact: the finger on the end section, its dome on the remote's battery plate.

![Back cover, pin section](docs/renders/bc_pin_section.png)

![Back cover, VBAT contact section](docs/renders/bc_contact_section.png)

![Back cover flex, copper](docs/renders/cover_flex_copper_front.png)

### Ring board, mic carrier, riser

KiCad projects in `pcb/sensor/` (D-50). Ring board: I²S and +5V on the front, SDA, SCL and +3V3 across the
top band on the back to the right rail, down the rail on the front round the box's corner keep-out to the
SHT45; GND pours (the left rail carries GND). The CN2 mate and its map are placeholders: no fab files yet.

| Ring board, front | Ring board, back |
| --- | --- |
| ![Ring board, front](docs/renders/ring_board_front.png) | ![Ring board, back](docs/renders/ring_board_back.png) |
| ![Ring board, front copper](docs/renders/ring_board_copper_front.png) | ![Ring board, back copper](docs/renders/ring_board_copper_back.png) |

Mic carrier (7 × 6 mm, castellated) and riser board (two spring pins, two M2 post pads):

| Mic carrier, front | Mic carrier, back (mic side) | Riser, front | Riser, back |
| --- | --- | --- | --- |
| ![Mic carrier, front copper](docs/renders/mic_carrier_copper_front.png) | ![Mic carrier, back copper](docs/renders/mic_carrier_copper_back.png) | ![Riser, front copper](docs/renders/riser_board_copper_front.png) | ![Riser, back copper](docs/renders/riser_board_copper_back.png) |
