# Safety rules (humans and agents)

This device puts home-built parts in a mains wall box. Nothing in this repo is
certified, and nothing here makes it code-compliant. Treat every rule below as a
hard requirement.

## Electrical
1. Breaker off and verified dead (non-contact tester + meter) before opening any box.
2. The lighting load (up to 15 A) is switched by the certified rocker only. Line,
   neutral and ground pass through the mains board via listed push-in terminals
   (D-23). That board is not certified: it is the part an inspector is most likely
   to question.
3. Mains-side parts must carry recognised marks: rocker (CSA/cUL; ENEC for EU/UK),
   IRM-03-5 (cURus/CB/TÜV), terminal block, fuse, MOV.
4. The 5 V FFC runs from inside the box to the sensor board, through the single
   pass-through. It is not a rated wire: a stock flat flexible cable, conductors
   exposed only at its two latched ends (J2 on the mains board's 5 V side, J1 on the
   sensor board outside the box). Its distance to mains-side parts along its route, and
   whether its insulation is sufficient where it passes them, are open for human review.
   The same holds for the pin board, its two spring pins and the two spacer posts
   (bare 5 V metal, heatshrink only) in the box under the pocket floor (D-50): they sit
   over the mains board's 5 V area, 8 mm from mains copper on the board; their distance
   to the WAGO block, the rocker and the house wiring in a real box is open for review.
5. Bond grounds per local code. The printed plate is non-conductive and is not grounded.
6. Box fill must be calculated with the barrier, the rocker body and the mains board
   (terminal block, PSU) counted.
7. The rocker breaks line and neutral of the lighting load; the line feed and ground
   stay connected on the board. Use the breaker for work on fixtures.

## Mechanical / material
8. Barrier geometry (NA: the barrier's pocket shell, switch well, collar; EU:
   the barrier) is printed in a UL94 V-0 filament with its datasheet on file. PLA/PETG
   are for test fits only.
9. No holes may be added to the barrier other than (D-80):
   - NA: the 5 V bore and the two spring-pin holes in the pocket floor (D-50, D-74,
     human decision 2026-10-10);
   - EU: the four spring-pin holes (D-54, D-59) and the two device-screw holes in the barrier.

   The rocker panel cutout is closed by the rocker body itself, each pin hole by its
   pin's barrel, each EU screw hole by its screw: never energise with the rocker, the
   NA pin board, the EU pin board, a pin or a barrier screw out. `make check` and `make eu` run a
   barrier-continuity test (mains air must not reach the pocket, plate hollow or
   room); it must pass.

## Regulatory (BC, Canada)
10. Work under a homeowner electrical permit; ask the inspector about the concealed
    emergency switch and the uncertified assembly before installing more than one.
11. Expect questions from your insurer about non-approved equipment.
12. EU/UK: local rules differ (e.g. England Part P). Check before building there.

## For AI agents
- Don't claim compliance, safety, or code approval. Report what was checked.
- Don't relax constraints 2, 8, 9 or the PCB creepage targets to make something fit;
  stop and ask.
