# Low-voltage boards (D-50, D-35, D-56, D-70)

The ring board, the riser board, the replacement back cover's flex and the EU cap board,
generated from `tools/sensor_parts.py` and `tools/eu_capboard_parts.py`, which
take their geometry from `cad/build123d/params.py` and `eu/params_eu.py` (the CAD models are in
`cad/build123d/ring.py`, `backcover.py` and `eu/capboard_eu.py`).

Nothing here touches mains. All boards are low-voltage only.

## Ring board (`kicad/ring_board.*`)

FR4 1.6 mm, two layers, round the insert's collar against the wall, pressed onto its crush ribs (D-68)
(outline 66.3 × 125.9 mm, window 53.9 × 79.3 mm with a notch round each screw boss; two notches in the top edge
under the MSR-2's Boot / RST switches, which stand deeper behind its board than the CN2 stack, D-64). Seen from the
front (F faces the insert):

- J1: Hirose FH12-6S for the 5 V FFC from the wiring board's J2; GND 1, 3, 4, 6, +5V 2, 5 (the
  same mirror-symmetric pinout as J2, so the FFC's type and orientation cannot swap the polarity).
  C1 22 µF at J1.
- J2: Molex 55909-2474 (24 contacts, 0.4 mm) mating the MSR-2's rear connector CN2 (D-82); land pattern from Molex
  SD-55909-003 rev J (D-89); contact map and pin 1 placeholders, below.
- U1: SHT45 with C2 (100 nF) under the face plate's vents at the bottom.
- MK1: Knowles SPK0641HT4H-1 (top-port PDM microphone, SELECT low) at the top right, port end up under the face
  plate's sound column; U2: Analog Devices ADAU7002 (PDM to I²S, CONFIG high = I²S, WLCSP-8 0.4 mm) to its left with
  C4 (100 nF), R1 (100 kΩ I²S SD pull-down: SDATA is tristated between words) and C3 (the mic's 100 nF, C0G 1206, D-85) outside the
  column's gasket (D-83). The I²S lanes run from CN2's upper row into U2 (SD straight in on the left, WS and SCK
  under it and up its right); PDM_CLK goes to the mic on the front, PDM_DAT on the back; a +3V3 bus under the parts
  feeds the mic and C3. The mic's GND ring pads that the signal escapes enclose (5, 6) have their own vias.
- H1–H3: Würth WA-SMSI M2 L1.5 SMT spacers (9774015243R, Ø5.3 pad on a Ø3.0 unplated hole, GND)
  under the MSR-2's board, below the face plate's posts (D-68).

Copper keeps 8 mm along the wall from the box opening (rule areas: front 6.4 mm in plan, the board
edge adds 1.6; back 8.0). So the back layer only has the bands above and below the box; the right
side carries three front lanes (SCL, SDA, +3V3; 0.15 mm, 0.33 mm pitch) round the box's corner to the
SHT45, the left side a GND pour that joins the top and bottom pours. SDA, SCL and +3V3 cross the top
band on the back, under J1, to three vias above the rail; the I²S lanes and +5V stay on the front. Vias 0.45 / 0.2 mm
round CN2 and U2.

**Not ready to fabricate.** J2's contact map and pin 1 are placeholders: CN2's part is assumed (D-82: Molex
55909-2474 on the MSR-2's 51338-2474, 1.5 mm mated); the land pattern is Molex's (SD-55909-003 rev J sheet 2:
pads 0.22 × 0.9 at 0.4, rows 1.73 apart, four 0.5 × 0.85 fitting nail pads, D-89), but the drawing numbers no pins. `CN2_MAP` only keeps the
fan-out from crossing. `tools/build.sh` writes no ring board fab files while `CN2_CONFIRMED` is false.

## Riser board (`kicad/riser_board.*`, fab pack in `fab/riser_board/`)

FR4 0.8 mm, two layers, 14 × 12 mm, in a pocket under the insert's pocket floor (D-53, D-60, D-79). P1 / P2: M2 pads
(Ø3.8 on a plated Ø2.2 hole, under the pan heads) over the two spacer posts at its lower corners (P1 +5V, P2 GND), held by
M2 × 5 screws, which carry the current through the WA-SBRIE studs. J1 / J2: Harwin P70-2200045 SMT
spring pins with pegs (Ø2.2 pad over a plated Ø1.2 hole; +5V above, GND below) above and between the posts, at the
back cover's pad positions. 1 mm tracks.

## 5 V FFC

Stock: Würth WR-FFC 687606152002 (0.5 mm, 6 contacts, 152 mm, Type 1). Wiring board J2 → the straight bore in the
insert's top-right corner (D-74) → out of the flange onto the ring board → ring board J1, both latched (FH12 slide
lock); the spare length lies folded flat in four layers (12 mm) at y 43.4, between the flange and J1 (D-68). Assembly:
with the wiring board on its standoffs, push the end up the bore from the insert's underside round its one bend into
the slot and latch it into J2 from the side; press the ring board onto the collar's crush ribs (no screws, D-68), pull
the cable taut from the face side, fold the spare, latch J1.

## Microphone firmware (D-29, D-83)

ESPHome on the MSR-2, push-to-talk: Home Assistant starts listening (for example from a BILRESA
button automation calling the action) and the voice pipeline ends it on silence. Untested
starting point:

```yaml
i2s_audio:
  - id: i2s_mic_bus
    i2s_lrclk_pin: GPIO6
    i2s_bclk_pin: GPIO4

microphone:
  - platform: i2s_audio
    id: plate_mic
    i2s_audio_id: i2s_mic_bus
    adc_type: external
    i2s_din_pin: GPIO7
    channel: left              # SELECT low: check which slot carries the mic on an MSR-2
    bits_per_sample: 32bit     # ADAU7002: 20-bit data in 32-bit slots, BCLK = 64 x fs
    sample_rate: 16000         # PDM clock 64 x fs = 1.024 MHz: the mic's performance mode starts at 1.0 MHz

voice_assistant:
  microphone: plate_mic

api:
  actions:
    - action: start_listening
      then:
        - voice_assistant.start:
    - action: stop_listening
      then:
        - voice_assistant.stop:
```

Open: whether the pipeline accepts 48 kHz from this microphone on the C3 or needs 32 kHz, and
the C3's RAM / CPU headroom next to the radar, Wi-Fi and BLE.

## Back cover flex

Single copper layer, polyimide, for the replacement back cover that powers a BILRESA E2490
without cells (`cad/build123d/backcover.py`, DESIGN D-35). Drawn flat, seen from the copper side.

- J1, J2: Ø2.6 gold pads (+5V, GND) on the pad section, which lies copper down on a ledge in the
  cover, behind Ø2.1 windows in its back: the plate's spring pins press on them (NA, D-50).
- A 2.6 mm run (in a notch along the GND contact post's inner face, D-79) to the terminal end; one 90°
  bend (copper outside).
- J1 takes +5 V from the plate (D-41, D-50); U1 TI TLV75533PDBVR (3.3 V, SOT-23-5) with C3 / C4 1 µF on
  the section below the fingers, copper down in a recess in the cover (0.4 mm wall left), feeds VBAT.
- A 0.8 mm FR4 stiffener (back side) on the pad and regulator sections, flush with their long
  edges: five snap hooks in the cover hold it down against the pins' push (D-45, D-79). No holes.
- J3, J4: Harwin S7081-42R spring fingers (VBAT, GND) on the end section, on the cell axes, long
  axis vertical with the bend end up (the battery contacts ride down the arm's ramp as the cover
  goes on), on a 0.4 mm FR4 stiffener (back side); it slides down slots along the contact blocks (D-55). The end section stands 2.0 mm (the fingers'
  working height) in from the cell end plane: J3 presses the remote's fixed VBAT plate, J4 its GND
  leaf spring (finger and leaf share the travel). Between them only a band passes under the
  remote's PCB strip.

Not ready to fabricate: the positions come from the FCC internal photos (REF) or are MEASURE;
`tools/build.sh` writes no `fab/cover_flex/` while `COVER_CONFIRMED` is false.

## EU cap board (`kicad/eu_cap_board.*`, D-56, D-70)

FR4 1.6 mm, two layers, round the remote pocket in the cap's printed carrier (its rim round the board). TP1 / TP2:
Ø2.4 gold pads on the underside under the 5 V board's sensor spring pins (GND, +5V). As on the ring board: J2 mates
the MSR-2's CN2 (Molex land pattern, placeholder contact map) and H5–H7 (Würth WA-SMSI 9774015243R, 1.5 mm) carry its board under the face plate's
posts; MK1 and U2 with C3, C4 and R1 as on the ring board (`route_mic`, D-83), the mic at x 32.0 so its parts and
lanes sit between it and the MSR-2's bay frame. I²S from CN2's upper row up, right, down and into U2, +3V3 from the
lower row down and right to the parts' bus; SDA, SCL and +3V3 on the back
down the outer left edge (outside the snap windows and the screws) to U1 (SHT45) and C2 at the bottom; +5V from the
pin pad on the back up the outer right edge to CN2; GND pours on both layers; 0.45 / 0.2 mm vias round CN2. Windows at
the four corners pass the face plate's snap fingers; notches in the top edge clear the MSR-2's back switches. H1–H4:
holes for the M2 screws into the carrier. No fab files until CN2 is confirmed.

## Regenerate

```bash
make pcb        # also builds the wiring board; or pcb/sensor/tools/build.sh
```

`build.sh` runs `tools/gen_sensor.py` (libraries, projects, schematics, boards), ERC and DRC
(all severities, schematic parity), then writes `fab/riser_board/` (the ring
board, the cover flex and the EU boards once confirmed). Reports go to `build/`.

## Open

- CN2 mate (Molex 55909-2474, D-82, D-89): contact map and pin 1 (from the GPIO add-on's plug or Apollo). Then set
  `CN2_CONFIRMED`, regenerate, check the fan-out. The pads' mask webs are 0.18 mm (PCBWay: 0.19 green): one opening
  per row.
- The FFC passes through the mains volume in the pass-through (SAFETY item 4).
- MK1 and U2 pin 1 against parts (footprints from the datasheets' top views).
- Microphone firmware test on an MSR-2 (sample rate, I²S slot, load).
