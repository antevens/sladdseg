# Bill of materials (per plate)

Prices/stock as seen Oct 2026; re-check. Bold = safety-critical, don't substitute without review.

| Ref | Part | MPN / source | Notes |
|-----|------|--------------|-------|
| — | IKEA BILRESA remote, scroll wheel | IKEA 906.174.56 (white) | Kept intact: 2×AAA, or the replacement back cover (no cells). |
| — | Adhesive steel plate, cut | supplied with the BILRESA | D-43, D-52: cut once across to an 18.5 mm piece from one round end (~47.4 × 17.5, ESTIMATE) in the hacksaw guide (`print/plate_jig_PLA.3mf`, D-81); round end down in the pocket-floor recess (NA insert; EU cap, D-72). |
| S1 | **Rocker DPST, PCB pins** | **Marquardt 1802.2504** (drawing 1802.2504 rev g); Mouser 979-1802.2504. Second source (NA and EU): **E-Switch RA412C1100** (4.8 mm tabs into the slots, D-88); the order lists take it for both variants (D-97) | ENEC 12(4) A 250 V~; UL-recognized/CSA 15 A 125–250 VAC; cutout 19.4 × 21.9 (1.25–2 mm panel); 5.3 mm above the panel, PCB seat 16.2 mm below. Pinout to be checked with a meter (D-26). |
| J1 | **Terminal block, push-in lever, 6-pole, 5 mm, 4 mm² / 12 AWG** | **WAGO 2604-1106** | L/N/PE in and out; 400 V (III/2). On the board's back, wire entries face the top edge. |
| PS1 | **AC-DC 5 V 600 mA** | **Mean Well IRM-03-5** (DigiKey 1866-3020-ND) | 85–305 VAC, 37×24×15 mm, on the board's back. |
| F1 | **Fuse T1A 250 VAC, SMD** | **Schurter UMT 250 3403.0166.11** (bag of 100; .24 = reel of 2000) | Rating is the designer's choice (Mean Well gives none); 200 A breaking capacity: human review. |
| RV1 | **Varistor 275 VAC, SMD** | **TDK B72660M0271K093** (CU4032K275G2) | Covers 120 V and 230 V. |
| J2 | FPC connector, 6 contacts, 0.5 mm, SMD, slide lock | Hirose FH12-6S-0.5SH(55) | 5 V out to the ring board's FFC (GND 1, 3, 4, 6; +5V 2, 5: mirror-symmetric, D-50). |
| P1, P2 | SMT steel spacer M2, 7 mm, tin | Würth WA-SMSI 9774070243R | D-50: spacer posts on the 5 V area (+5V, GND), reflowed on a Ø5.3 pad over a Ø3.0 unplated hole. |
| — | Brass spacer stud M2 male-female, 10 mm, 4 mm hex ×2 | Würth WA-SBRIE 971100244 | D-50: screwed into P1 / P2 (5 mm male thread, ends inside the 7 mm spacer); carry the riser and its 5 V. |
| — | Heatshrink 6 mm 2:1, 15 mm ×2 | any | D-50: over each spacer post. |
| — | FFC 0.5 mm, 6 contacts, 152 mm, Type 1 | Würth WR-FFC 687606152002 | D-50, D-74: wiring board J2 → straight bore → ring board J1; 140 mm along the route incl. 46 mm folded flat beside J1, 4 mm into each connector. |
| PCB | Wiring board 47 × 72 mm, 2-layer 1.6 mm | PCBWay; order pack in `pcb/fab/` | Routed isolation slot in the outline. S1 is soldered by hand last: after it is snapped into the insert and the board is screwed down (slotted holes, D-88). Copper weight: thermal review. |
| — | Apollo MSR-2 mmWave multisensor | apolloautomation.com / The Pi Hut | ESP32-C3, LD2410B, DPS310, LTR-390; optional SCD-40. Used out of case. |
| PCB | Ring board, 2-layer FR4 1.6 mm, 66.3 × 125.9 mm with a 53.9 × 79.3 mm window | PCBWay; `pcb/sensor/` ring_board (no fab files until CN2 is confirmed) | D-50, D-68: on the insert's collar (crush ribs), under the face plate. Copper 8 mm from the box opening. |
| H1–H3 (ring) | SMT steel spacer M2, 1.5 mm, tin | Würth WA-SMSI 9774015243R | D-68: the MSR-2's board rests on them under the face plate's posts. |
| J1 (ring) | FPC connector, 6 contacts, 0.5 mm | Hirose FH12-6S-0.5SH(55) | D-50: 5 V in from the FFC. |
| C1 (ring, EU cap board, EU 5 V board) | 22 µF 16 V X5R ±20 % 1206, 1.8 mm max | KEMET C1206C226M4PACTU (DigiKey 399-12290-1-ND) | At J1 / the 5 V input (D-95; was Samsung CL31A226KPHNNNE, 61-week maker lead time). |
| U1 (ring) | SHT45 | Sensirion SHT45-AD1B-R2 (DFN-4 1.5 × 1.5) | On the ring board under its vents, I²C from the MSR-2. |
| C2, C4, R1 (ring, EU cap board) | 100 nF X7R 0402 ×2; 100 kΩ 1 % 0402 | any (Murata GRM155R71C104KA88J, Yageo RC0402FR-07100KL in the order lists) | SHT45 and ADAU7002 decoupling; I²S SD pull-down (the ADAU7002 tristates SDATA). |
| C3 (ring, EU cap board) | 100 nF C0G 25 V ±5 % 1206, 3.2 × 1.6 × 1.8 max | KEMET C1206C104J3GACTU | D-85: the mic's decoupling; Knowles: no Class 2 dielectrics near the mic. 100 nF C0G starts at 1206 (KEMET, TDK, AVX, Murata catalogs). |
| J2 (ring board, EU cap board) | CN2 mating plug, SlimStack 24 contacts, 0.4 mm, 2 rows | Molex 55909-2474 | D-82, D-89: mates the MSR-2's CN2, assumed Molex 51338-2474 (1.5 mm mated); land pattern from Molex SD-55909-003 rev J; contact map and pin 1 wait for Apollo's pinout. |
| MK1 (ring, EU cap board) | PDM MEMS microphone, top port, 3 × 4 × 1 mm | Knowles SPK0641HT4H-1 (DigiKey lists it under Syntiant) | D-83: on the board, port end up under the face plate's sound column. |
| U2 (ring, EU cap board) | PDM to I²S converter, WLCSP-8 0.4 mm | Analog Devices ADAU7002ACBZ-R7 | D-83: the ESP32-C3 has no PDM input; CONFIG high = I²S. Needs PCBWay assembly. |
| — | Mic gasket: adhesive rectangular ring 5.0 × 6.0 outside, 3.4 × 4.4 inside, 0.3 mm | die-cut | D-83: under the sound column's foot on the board round the mic (NA and EU). |
| PCB | Riser board, 2-layer FR4 0.8 mm, 14 × 12 mm | PCBWay; `pcb/sensor/fab/riser_board/` | D-50: on the spacer posts, in a pocket under the pocket floor. |
| J1, J2 (riser) | SMT spring pin with locating peg, 2 A, gold | **Harwin P70-2200045** | D-50, D-59: +5V, GND through the pocket floor onto the back cover's pads at 6.7 mm working height; part of the barrier (they fill the floor holes). |
| P1–P4 (EU 5 V board) | SMT spring pin with locating peg, 2 A, gold | **Harwin P70-2200045** | D-54, D-59: all four at 6.8 mm working height: P1 / P2 onto the cap board's pads, P3 / P4 onto the back cover's pads. |
| J3 (EU mains board) | SMT pin header 1 × 2, 2.54 mm, 8.13 mm post | Samtec TSM-102-02-L-SV | D-59: into the 5 V board's socket (3.07 mm engaged). |
| — | M2 × 5 pan head screw ISO 7045 ×2 | any | D-50: riser onto the brass studs (WA-SBRIE). |
| — | Replacement back cover (BILRESA E2490): printed cover + single-layer flex with 0.4 mm FR4 stiffener, ENIG; the remote's own magnet plate | printed; PCBWay flex, `pcb/sensor/` cover_flex (no fab files yet) | D-35: replaces the remote's back cover; no cells. |
| — | SMT spring fingers ×2 (back cover) | **Harwin S7081-42R** | D-35, D-40: on the cover flex, VBAT and GND onto the remote's battery contacts. The +5V / GND inputs are Ø2.6 gold pads under the plate's spring pins (D-50). |
| U1 (cover flex) | LDO 3.3 V 500 mA, SOT-23-5 | **TI TLV75533PDBVR** | D-41: the remote's 3.3 V from the pins' +5 V, on the cover flex. Datasheet: https://www.ti.com/lit/ds/symlink/tlv755p.pdf |
| C3, C4 (cover flex) | 1 µF 16 V X5R 0402 | Samsung CL05A105KO5NNNC (Murata GRM155R61A105KE15D: obsolete; CL05A105KP5NNNC: out of stock at both, 2026-10-11) | LDO input / output (TLV755P: ≥ 1 µF). |
| — | Cover flex stiffener, FR4 0.8 mm, flush with the flex's long edges | PCBWay (with the cover flex) | D-45: on the pad and regulator sections; the cover's snap hooks hold it by its long edges. |
| PCB | EU cap board, 2-layer FR4 1.6 mm, round the remote pocket | PCBWay; `pcb/sensor/` eu_cap_board (no fab files until CN2 is confirmed) | D-56, D-70: pin pads underneath, CN2 mate (MSR-2 straight on it), three 1.5 mm SMT spacers H5–H7 (Würth 9774015243R), SHT45, the microphone and the ADAU7002 (D-83). |
| — | EU cap board carrier | printed, `print/eu_carrier_PLA.3mf` | D-56: the carrier under the cap board, its lip pinned to the wall by the cap's edge, the cap's teeth stop it turning (D-71). |
| — | M2 × 6 thread-forming screws ×4 (EU) | any | D-70: cap board into the carrier. |
| — | Board standoffs ×4: nylon M3 male-female hex, 15 mm, 5.0 mm hex | **Keystone 25503** | D-57: stud into the insert's tapped boss, the top-right one's stud cut to 5 mm. Nylon 6/6 UL94 V-2 (catalog M65 p.76). |
| — | Board screws ×4: nylon M3 × 8 slotted pan head (ISO 1580) | any | D-57: through the board's Ø3.2 holes into the standoffs (6.4 mm engaged). |
| — | M3 × 0.5 tap | any | Tap the insert's four boss holes (2.5 mm tap-drill size as printed; 8.5 mm deep, top right 5.5). |
| — | #6-32 × 1" oval-head screws | — | ×2, to box ears. |
| — | **Filament, NA insert and EU cap: Elegoo PC-FR** (UL 94 V-0 per listing) | see PRINTING.md | ≈ 52 g insert with supports, ≈ 10 g EU cap (PRINTING.md). Keep the TDS on file. |
| — | Filament: test fits Elegoo PLA; installed trim PETG / ABS / ASA; barrier parts PC-FR | see PRINTING.md | Per part in PRINTING.md (NA trim ≈ 22 g, EU trim ≈ 42 g). |
| — | EU mains board and 5 V board parts (rocker, WAGO 2604-3102 ×2, Traco TMPS 03-105, F1, RV1, header, socket, C1) | `pcb/eu/README.md`; order lists in `pcb/order/` | D-32, D-36, D-59. |
| PE1 (EU) | **Lever splicing connector, 2 conductors, 0.2–4 mm²** | **WAGO 221-412** (DigiKey 2946-221-412-ND) | D-94: PE in from the supply to PE out to the lights, joined in the box; the boards carry no PE. A third PE conductor takes a 221-413. |

## Links

- PCB order pack + human-review checklist: `pcb/fab/README.md`
- DigiKey / Mouser order lists for test plates (`make order`): `pcb/order/README.md`
- IRM-03 datasheet (2025-08-08): https://www.meanwell.com/Upload/PDF/IRM-03/IRM-03-SPEC.PDF
- Harwin S7081-42R drawing: https://content.harwin.com/asset/8cd5d0a8-d578-46b3-8278-7289045a1613/DRG-02322-Technical-Drawing-Datasheet-S7081R-pdf.pdf
- Elegoo PC-FR listing (UL 94 V-0 claim): https://www.3djake.com/elegoo (search PC-FR); get Elegoo's TDS
- MSR-2 GPIO add-on (mezzanine pins 3V, 5V, GND, I²C, 6 GPIO): https://thepihut.com/products/gpio-add-on-for-apollo-automation-msr-2
- MSR-2 ESPHome page: https://devices.esphome.io/devices/apollo-automation-msr-2
- MSR-2 firmware repo: https://github.com/ApolloAutomation/MSR-2
- SPK0641HT4H-1 datasheet (rev A): https://www.knowles.com/docs/default-source/model-downloads/spk0641ht4h-1-rev-a.pdf
- KEMET C0G SMD datasheet (C1003_C0G, 2/20/2025): https://content.kemet.com/datasheets/KEM_C1003_C0G_SMD.pdf
- ADAU7002 datasheet (rev C): https://www.analog.com/media/en/technical-documentation/data-sheets/ADAU7002.pdf
- BILRESA: https://www.ikea.com/us/en/p/-70617457/
