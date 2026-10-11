# Measurements to take (fill in, then update cad/build123d/params.py)

Use calipers; record to 0.1 mm. Measure 2 samples where possible. `status`: TODO / DONE /
REF (published or third-party reference value in use until measured).

| param | what | how | value | status |
|-------|------|-----|-------|--------|
| B_W | BILRESA width (widest) | across the short axis | 45.0 (reference: IKEA UK product size; third-party mount pocket 45.4) | REF |
| B_H | BILRESA height | long axis | 70.0 (reference: IKEA UK product size; third-party mount pocket 70.4) | REF |
| B_D | BILRESA depth | back cover to top of wheel | 20.0 (reference: IKEA UK product size) | REF |
| — | BILRESA face profile | photo + depth of wheel ring vs body | | TODO |
| B_BACK_RUN, B_BACK_RISE | BILRESA back round-over (inset and height of the curve) | radius gauge or profile photo | 9.1 / 9.0 (label drawing, see the estimates below) | ESTIMATE |
| — | BILRESA supply | IKEA manual AA-2675003-2 (2025), technical data | 2 × AAA HR03 (NiMH, 2 × 1.2 V nominal); recommended LADDA HR03 rechargeable; types E2490, E2704; 0–40 °C | DONE (manual) |
| — | BILRESA battery contacts: positions in the compartment, spring travel, polarity | open the back cover; calipers from the remote centre. FCC ID FHO-E2490 internal photos (TÜV Rheinland, pictures 1, 3, 4): 2 cells side by side along the long axis, the PCB strip between them; SERIES, confirmed: at the radio-module end one metal strap (silk P3) joins both contacts; at the system-button (S1) end two separate terminals, silk "GND"/P2 and P1 (P1 = VBAT: the E2489 board, same layout, labels these positions VBAT and GND/P2). Which slot is + / − at the terminal end: from the compartment markings on a unit. Approx. from picture 1 scaled to its ruler (perspective, ±1 mm): contacts centred on the remote, 45 mm apart along the long axis (≈ AAA length), 23 mm apart across | ±22.6 along, ±11.7 across (approx.) | REF |
| — | BILRESA battery contact types at each end | FCC ID FHO-E2490 internal photo 1 (cover open): diagonal pairs, at each end one leaf spring (bent out of its slot, − side) and one fixed plate with a dimple set in a pocket in the end wall (+ side); at the terminal end GND meets the leaf spring, VBAT the fixed plate (series chain). Measure on a unit: the plate's setback behind the end wall face (`BC_TERM_SETBACK`, behind the cell end plane), the pocket opening round the plate (the S7081 dome, Ø1.3, must reach it), the leaf spring's rest position and travel, which end is the terminal end | 0.0 (placeholder) | TODO |
| — | BILRESA dual button (E2489) battery contacts | FCC ID FHO-E2489 internal photos (TÜV Rheinland, pictures 1-4): same layout as the E2490, 2 cells side by side along the long axis with the PCB strip between; SERIES: metal strap along the radio module joins the two contacts at that end, terminals at the other end silk "VBAT" and "GND"/P2. Approx. from picture 1 scaled to its ruler (perspective, ±1 mm): centred on the remote, 44.8 mm apart along the long axis, 20.1 mm across. Outline and depth: measure | ±22.4 along, ±10.0 across (approx.) | REF |
| — | BILRESA supply as the remote sees it | zigbee2mqtt E2490 page: reports battery voltage in mV and a percentage that "seems to be tuned for Alkalines (1.5V)"; Qorvo chipset; sleeps between presses. Read the voltage in HA with the 3.3 V supply | | TODO |
| BC_* | BILRESA back cover: outline, wall, latch hooks (position, depth), magnet plate size and position, cell axis height above the back | calipers on the original cover and the open remote | wall, clips, side ribs, magnet plate measured (below); cell axis height, contact setback, hook size open | partly |
| — | Magnet hold vs. the plate's two spring pins (D-50) | pull the remote (with the printed cover) off the plate with a force gauge; the pins push it away with about 2 x 0.98 N at the datasheet's normal working height (7.1 mm, Harwin P70-2200045), more at the design's 6.7 mm | | TODO |
| MIC_CARRIER, MIC_WIN | mic carrier flat on the ring board, the mic in the window (D-50) | on the first boards: the carrier sits flat, the mic clears the window's walls and the wall | 7 × 6 × 0.8, window 0.3 round | TODO |
| — | BILRESA current: sleep and transmit peak | supply at 2.4 V through a current meter / shunt + scope | | TODO |
| WAGO_ROW (NA) | WAGO 2604 solder-pin rows and body, 2604-11xx (0° entry) | WAGO STEP models 2604-1102 / 2604-1106 (CADENAS download 2026-10-08, kept in scratch/3d/wago/) | pole pitch 5.0; 2 pins per pole in rows 8.2 apart (pins 0.8 × 1.0, 4.0 long); first row 5.0 behind the entry face, second row 2.9 inside the closed back (body 16.1 deep at the board, 16.7 high); levers overhang the entry side at the top to 8.1 beyond the first row | DONE (vendor model) |
| WAGO_ROW (EU) | WAGO 2604-3102 (90° entry) pin rows and body | WAGO STEP model 2604-3102 (CADENAS download 2026-10-08, kept in scratch/3d/wago/) | poles 5.0 apart; 2 pins per pole in rows 8.2 apart (pins 0.8 × 1.0, 4.0 long); body 16.7 along the rows, 3.6 before the first row, 4.9 past the second (lever side, levers up to 21.3); 12.4 across the poles, 0.1 off their centre | 8.2 (rows' centre 0.65 from the body centre) | DONE (vendor model) |
| MAGNET | supplied adhesive plate w × h × t (with its tape): steel, rigid (human, 2026-10-10: cut with metal shears, a hacksaw or a grinder) | calipers | | TODO (size) |
| MAGNET_Y | centre of the magnet inside the remote, from the remote centre | slide a steel piece over the back, mark the strongest pull | | TODO |
| MAGNET_END_R | corner radius of the supplied steel plate's ends (the recess bottom follows it; the piece is cut straight at the top) | radius gauge or trace on paper | | TODO |
| SW_PANEL_T | Marquardt 1802.2504 snap-in panel range | drawing 1802.2504 rev g: 0.75–3 mm, cutout length steps 19.2/19.4/19.8; 1.5 mm chosen; confirm on `coupon_rocker` | 1.5 | TODO |
| SW_BEZEL | 1802.2504 flange w × h | drawing 1802.2504 rev g | 21 × 24 (mounted 24 × 21) | DONE (datasheet) |
| SW_ROCKER_H | rocker top above the panel face | drawing 1802.2504 rev g | 5.3 ± 0.5 | DONE (datasheet) |
| SW_BODY | body w × h; PCB seat below the panel face | drawing 1802.2504 rev g | 18.6 × 22; 16.2 | DONE (datasheet) |
| MSR[2], MSR2_FRONT | front of the MSR-2 + CO2 add-on stack above the board's back (`msr2.py`, D-64): the SCD4x top and the radar's pins | calipers, CO2 version out of its case | 10.4 from the model (Apollo's case face is 10.41 above its board plane) | REF |
| MSR2_CASE | Apollo case cavity w × h; face underside above the board plane | Apollo case STL (Printables 932026, measured) | 38.08 × 21.67; 10.41 | REF |
| MSR2_ESP, MSR2_ESP_ANT | ESP32-C3-MINI-1 size; antenna end | Espressif ESP32-C3-MINI-1 datasheet v1.3 (16.6 less the MINI-1U's 12.5) | 13.2 × 16.6 × 2.4; 4.1 | DONE (datasheet) |
| MSR2_LD, MSR2_LD_PINS | LD2410B module; 5 pin holes at 1.27 | Hi-Link LD2410B user manual 4.1 | 7 × 35 | DONE (datasheet) |
| MSR2_SCD | SCD4x package | Sensirion SCD4x datasheet v1.4, page 1 and Table 36 | 10.1 × 10.1 × 6.5 | DONE (datasheet) |
| MSR2_USB_Y, MSR2_SW_X | USB-C centre across the board; Boot / RST button centres along it | Apollo case STL: USB opening y −9.65..1.35 about the cavity centre 1.19; button holes x ±4.0, 0.5..1.5 behind the board | −5.3; ±4.0 | REF |
| MSR2_ESP_IN, MSR2_NOTCH, MSR2_CN1_IN, MSR2_CO2_BOARD, MSR2_LD_BACK, MSR2_LD_T, MSR2_LD_PARTS, MSR2_LD_PROP, MSR2_USB, MSR2_CN1_STACK | part positions and sizes on the MSR-2 and the CO2 add-on (radar height, add-on board, CN1 stack, antenna notch) | calipers | from Apollo wiki photos (CO2 add-on pics 7, 8, 10; GPIO header pic 3), scaled by the datasheet sizes | ESTIMATE |
| MSR2_HOLES | the MSR-2's two plated holes on CN2's axis, one past each end of CN2: drill and spacing (locating pins for CN2 if they suit, D-64) | calipers, pin gauge | Ø0.9, CN2 centre ± 4.7 (photo scale) | ESTIMATE |
| RING_RIB | crush rib interference into the ring board's window edge (holds for handling, no cracking) | coupon_ribs with the ring board or a 1.6 mm FR4 offcut | 0.15 (0.10 / 0.15 / 0.20 on the coupon) | TODO |
| SNAP, SNAP_GROOVE, SNAP_WEB (EU) | the face plate's snap fingers in the carrier's closed windows (D-77): hold, release by pulling, the bump's 0.4 mm engagement, the 1.6 mm web to the bore | test fit of the PETG carrier and face plate | 2.4 × 6 mm fingers (8 mm key), 0.6 mm groove (design) | TODO |
| MSR2_POSTS / spacers | the MSR-2's back under the three spacers free of parts; B2B_STACK equals the 1.5 mm spacers | look at the board's back; calipers on CN2 mated | (−9.8, −3.9), (6.35, −3.9), (−17.5, 1.5) | TODO |
| MSR2_SW | Boot / RST switch body on the back: size and depth behind the board (it is deeper than the CN2 stack: notches in the ring board, D-64) | calipers | 4.0 × 3.0 × 2.0 | ESTIMATE |
| — | MSR-2 powered from the mezzanine header 5V/GND | bench test | yes (human, 2026-10-07) | DONE |
| — | MSR-2 rear connector CN2: maker + MPN, and the mating plug's MPN (the GPIO add-on's CN4); is the mate a board-mount part, or only on a flex? (D-51: straight on the ring board needs a board-mount mate, else the clip-tower fallback) | read the add-on's plug marking, or ask Apollo | 0.4 mm pitch, 2 rows (photo measurement, D-27) | TODO |
| — | CN2 contact count and contact-to-signal map (5V, 3V3, GND, SDA = IO1, SCL = IO0) | count + meter from the add-on's header to its plug | ~26-30 (photo) | TODO |
| MSR_CN2_IN, B2B, B2B_STACK | CN2 centre from the board end, housing size, mated stack height | calipers | 6.4; 7.6 × 3.0; 1.5 (photo estimates) | REF |
| MSR_BOARD | bare MSR-2 board w × h | calipers | 38.0 × 21.5 (Apollo case cavity 38.08 × 21.67, Printables 932026) | REF |
| MSR_BOARD_T | bare MSR-2 board thickness (the parts' envelope MSR applies above it) | calipers | 1.6 (placeholder; Apollo's case ledges sit 1.6 above its board plane) | TODO |
| — | MSR-2 current draw at 5 V (sizes the sensor board's input protection) | USB meter, radar on | | TODO |
| LUX_POS | LTR-390 offset from board centre, and which face it is on (Apollo's backplate has a 2.4 mm square window at about (16.7, −8.5) from the centre, at a small windowed part on the board's back) | calipers, look at the board | (12.0, 0.0) placeholder; the grille's middle slot is centred on it (D-69) | TODO |
| — | MSR-2 radar antenna position on board | photo | | TODO |
| SHT | face plate bay over the SHT45 (DFN-4, 1.5 × 1.5 × 0.5, datasheet) on the ring board: vents and clearance | on a print with the ring board | 12.0 × 8.0 × 4.0 (bay) | TODO |
| BOX_D | box depth, per room | ruler to back wall | | TODO |
| BOX_DIA (EU) | DIN 49073 box inside diameter (device opening) | calipers on a box | 60.0 (catalogue, e.g. Kaiser 1555-04) | TODO |
| BOX_HOLE (EU) | box rim outer diameter (hole in the wall) | calipers on a box | 68.0 (catalogue) | TODO |
| DOME_PITCH (EU) | device screw domes: spacing of opposite domes | calipers on a box | 60.0 (catalogue) | TODO |
| BOX_D (EU) | box depth | ruler to the box floor | 47.0 (catalogue) | TODO |
| SOCKET (EU) | 1x2 2.54 mm pin socket on the 5 V board's back: body height (sets the header engagement, D-59) | part number + datasheet, or calipers | 8.5 (placeholder) | TODO |
| — | box material per room (metal/plastic) | look | | TODO |
| — | neutral present per box (Y/N) | look/test with breaker off | | TODO |
| — | box ear positions / intrusion into opening | calipers; the insert fills the opening corners to ~10 mm deep (45° taper) and the bottom end to 0.75 mm of the wall | | TODO |
| V0_RATED_T | UL94 V-0 test thickness of the insert filament | filament TDS (cite) | Elegoo PC-FR data sheet states no UL94 class; deferred until a certified spool is chosen (2026-10-08) | TODO |
| — | 1802.2504 latch positions / spring-out below the panel | calipers | | TODO |
| — | wall finish to box face offset | ruler | | TODO |

## Estimates from photos and drawings (2026-10-08)

Human request: assume values from the available pictures, diagrams and drawings until a unit is
measured. Tagged `ESTIMATE` in `params.py`; replace each with a caliper reading before printing
anything final. Sources: FCC FHO-E2490 / FHO-E2489 photos (scratch/sources/fcc/, steel rulers, perspective
fits), the IKEA label drawings for E2490 / E2489 (drawn 1:1, outline checks at 70.1 × 45.1), and
the IKEA UK product page (height 20 mm).

| Name | Estimate | ± | Source / method | Used |
| --- | --- | --- | --- | --- |
| B_D | 20.0 | 0.5 | IKEA UK product page | REF in params |
| B_SEAM_Z | 12.5 | 1.5 | FCC external photos 1 / 2: back shell (battery cover) ~12.5, front housing ~7 | superseded: measured 9.8 (below) |
| B_FRONT_R | 0.8 | 0.5 | FCC external photo 1 | yes |
| B_BACK_RUN / B_BACK_RISE | 9.1 / 9.0 | 0.4 / 3 | label drawing: flat back 51.8 × 26.7; rise not visible | yes |
| B_WHEEL_D / B_WHEEL_Y / B_WHEEL_GAP | 41.5 / +12.5 / 0.3 | 1.0 / 1.0 / 0.2 | FCC photos; wheel concentric with the end arc, at the radio-module (strap) end | yes |
| B_LED_Y / B_LED_PITCH | −12.0 / 3.9 | 1.0 / 0.3 | FCC photos; LEDs at the terminal (P1 / P2) end | yes |
| BC_STEEL (x × y × t) | 12.0 × 20.0 × 2.0 | measured | human, 2026-10-09: the plate in the cover is a magnet, not steel | DONE |
| BC_STEEL_RIDGE | ridge round the plate on the full 1.6 shell, 0.8 thick × 1.2 high, 0.05 clearance (0.15 rattled on the first print) | 0.8 × 1.2 | ESTIMATE (human: "like the original") | partly |
| MAGNET_Y (remote's magnet centre) | 0.0 | 1.0 | FCC internal photo 1: centred in its cover | yes |
| BC_CELL_X | 11.2 | 0.5 | label drawing bays ±10.95; PCB contacts ±11.4 | yes |
| BC_CELL_Z | 6.8 | 0.8 | inferred: cover wall + clearance + cell radius | yes |
| BC_PCB_W | 11.6 (divider) | 0.3 | label drawing: divider 11.1 / 11.6 over its outer edges; the PCB strip is 11.1 | yes (divider) |
| BC_TERM_Y / BC_VBAT_X | −1 / −1 | — | FCC PCB photo: at the terminal end VBAT (P1) is the fixed dimple plate at −x, GND (P2) the leaf spring at +x | confirmed |
| Fixed plate pocket | ~5.6 across × 3.5 along | 0.7 | FCC internal photo 1; depth (BC_TERM_SETBACK) not visible | the S7081 dome (Ø1.3) fits |
| Leaf spring protrusion | ~2–3.5 from the end wall | low | FCC internal photo 1; travel not visible | — |
| MAGNET (supplied steel plate) | ~47.4 × 17.5, full round ends (R8.75), t 1.5–2.5 | 1.0 | label drawing back-view rings, FCC external photo 2 | yes: cut to an 18.5 mm piece (D-43) |
| B_SEAM_Z, BC_WALL | cover depth rim to back 9.8, shell 1.6 | measured | human, 2026-10-09 | DONE |
| BC_PRY | screwdriver notch in the rim at the bottom end | — | human, 2026-10-09: present; size MEASURE (6.0 × 1.2) | TODO |
| BC_SIDE_TAB, BC_SIDE_TAB_GAP, BC_SIDE_TAB_RIM_GAP | side ribs at mid-length, free-standing on the shell's curved floor (stiffening, no hook) | 36.2 inside spacing, top 3.6 below the rim (measured); 0.8 thick (human); length 6.0 (ESTIMATE, photos) | human, 2026-10-09 | DONE |
| — | supplied wall part: magnet or steel? | magnet / compass | steel (human, 2026-10-10, D-52) | DONE |
| BC_LATCH_* (cover snap clips, top and bottom) | one clip per end at x 0, 3.1 wide (measured) × 1.2, the bottom one at the pry notch; bottom: top 4.7 above the inside floor (measured), raised 0.2 towards the rim to 4.9 and its hook 0.1 deeper to 0.8 (test print 2026-10-10), clip face 2.9 in from the outside rim (measured on a print; was 3.6), hook tip 3.7; top: top 1.0 below the rim, hook tip 2.8 in from the outside rim (measured; model 3.0 with a 0.7 hook, the print's top clip did not catch), its back merges into the end wall; hook size MEASURE (0.5) | 0.5 | human photos IMG_5088-5090, measurements 2026-10-09 | partly |
| E2489 outline / depth | 69.5 × 40.0 / ~20 | 0.3 / 2 | label drawing; photo comparison | backlog (E2489 version) |
| E2489 cell axes | ±9.6 across, ends ±22 | 0.4 | label drawing | backlog |

Not determinable from the pictures: BC_TERM_SETBACK, BC_BRIDGE_H, the leaf spring's travel, the
supplied steel plate's thickness. They stay MEASURE.

The supplied steel plate appears to be about 47 × 17.5 mm (the drawing's ring, from a shape fit). Whole,
it would run into the switch well (NA) and the switch cup (EU) under the remote's upper half. The
user cuts it once across (human decision 2026-10-08): an 18.5 mm piece measured from one round end
(`MAGNET`), round end down into the recess's round end, straight cut edge up. Check the real size
before cutting; the piece length follows from `MAGNET_REC_Y` and the switch well.

