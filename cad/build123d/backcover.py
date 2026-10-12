"""REPLACEMENT BACK COVER (D-35): replaces the BILRESA E2490's back cover; the remote runs without
cells from the plate's +3V3.

The cover keeps the remote's back shape (cut to a 45 deg chamfer below the curve's 45 deg point,
so it prints back down without supports) and carries the remote's magnet plate. Inside, a
single-layer flex lies copper down on a ledge BC_FLEX_Z above the back face, held by snap hooks;
two gold pads on it sit over windows in the back, where the plate's spring pins press (+5 V, GND;
D-50, D-79). The flex runs along the GND contact post to the terminal end, bends up once and stands
against two contact posts; two Harwin S7081-42R fingers on it, on the cell axes, press on the
remote's VBAT (fixed plate) and GND (leaf spring) battery contacts. A 3.3 V regulator on the flex
(copper down, in a recess in the cover) feeds VBAT. No cells: the remote's strap joins the
bridge-end contacts.

The supplied steel piece in the plate's pocket floor holds the cover's back down on the floor: that
hard stop sets the spring pins' working height.

Remote coordinates: origin = remote centre, x / y as the front view, z = 0 the back's outer face.
Sizes marked MEASURE / REF in params.py.
"""
from math import acos, atan2, cos, degrees, pi, sin, sqrt
from build123d import Axis, Box, Cylinder, Plane, Pos, Rot, chamfer, loft
from params import *
from common import stadium, slab
import bilresa

Z_BEND = BC_FLEX_Z + FLEX_T / 2                          # flex mid-plane on the ledge


def copper_y():
    """y of the end section's copper face: FINGER_WH from the fixed contact plate, towards the cells."""
    return BC_COPPER_Y


def stiffener_y():
    """y of the stiffener's far face (towards the cells): the contact blocks start here."""
    return copper_y() - BC_TERM_Y * (FLEX_T + BC_STIFF_ADH + BC_END_T)


def bend_z():
    """Height where the run, bent up from the ledge with inside radius BC_BEND_R, stands vertical (D-116)."""
    return BC_FLEX_Z + FLEX_T + BC_BEND_R


def bend_arc():
    """The run's 90 deg bend: a quarter ring (inside BC_BEND_R, FLEX_T thick) from the ledge up into the end section."""
    sy = -BC_TERM_Y                                      # +1: cells side is +y
    xr0, xr1 = BC_RUN
    yc, zc = copper_y() + sy * (FLEX_T + BC_BEND_R), bend_z()   # bend centre (inside of the bend)
    ring = Pos((xr0 + xr1) / 2, yc, zc) * Rot(0, 90, 0) * (Cylinder(BC_BEND_R + FLEX_T, xr1 - xr0)
                                                          - Cylinder(BC_BEND_R, xr1 - xr0 + 1))
    quad = Pos((xr0 + xr1) / 2, yc - sy * 5, zc - 5) * Box(xr1 - xr0, 10, 10)
    return ring & quad


def slit_cuts(z_top):
    """Room in the end section, (x, z) boxes as end_section(): the relief slits beside the run up to BC_SLIT[1] past
    the bend zone, and the run's own width below the bend (its arc instead)."""
    w = BC_SLIT[0]
    xr0, xr1 = BC_RUN
    zs = bend_z() + BC_SLIT[1]
    return [(xr0 - w, xr0, BC_FLEX_Z - 1, zs), (xr1, xr1 + w, BC_FLEX_Z - 1, zs), (xr0, xr1, BC_FLEX_Z - 1, z_top)]


def end_blocks(xo=BC_BLOCK_XO):
    """Contact block outlines in the (x, z) plane (the end section's pad parts with xo=BC_END_XO) and the band under
    the PCB strip."""
    z0, z1 = BC_FLEX_Z, BC_FLEX_Z + BC_END_H
    xi = BC_PCB_W / 2 + BC_PCB_CLR
    return [(-xo, -xi, z0, z1), (xi, xo, z0, z1), (-xi, xi, z0, z0 + BC_BRIDGE_H)]


def end_section():
    """End section outline in the (x, z) plane: two pad parts and the band under the PCB strip."""
    return end_blocks(BC_END_XO)


def strip_top():
    """Upper end of the pad section; the regulator section continues above it for BC_JOG."""
    return max(y for _, y in BC_FINGERS) + BC_PAD_D / 2 + BC_PAD_END


def strip_bottom():
    """Lower end of the pad section; the run continues from here to the terminal end."""
    return min(y for _, y in BC_FINGERS) - BC_PAD_D / 2 - BC_PAD_LOW


def strip_boxes(clr=0.0):
    """Flex path on the ledge as (x0, x1, y0, y1): pad section, regulator section above it, run to the terminal end,
    the jog from the pad section's inner edge across to the run (D-79)."""
    yc = copper_y()
    yt, yb = strip_top(), strip_bottom()
    xs0, xs1 = BC_STRIP
    xr0, xr1 = BC_RUN
    return [(xs0 - clr, xs1 + clr, yb, yt), (xs0 - clr, xs1 + clr, yt, yt + BC_JOG),
            (xr0 - clr, xr1 + clr, min(yc, yb), max(yc, yb)), (xr0 - clr, xs0 + clr, yb - clr, yb + BC_RUN_JOG + clr)]


def back_shape(inset=0.0, lift=0.0, round_run=B_BACK_RUN):
    """The remote's back (flat pad, round-over `round_run` across and B_BACK_RISE up, straight sides) inset by
    `inset` all round and raised by `lift`. Below the curve's 45 deg point the round-over is replaced by its
    45 deg tangent (a frustum), so the cover prints back down without supports."""
    n = bilresa.N_SECT
    secs = []
    for i in range(n // 2, n + 1):                        # from the 45 deg point up
        t = (pi / 2) * i / n
        run = round_run * (1 - sin(t)) + inset
        secs.append(Plane.XY.offset(lift + B_BACK_RISE * (1 - cos(t))) * stadium(B_W - 2 * run, B_H - 2 * run))
    w, h = B_W - 2 * inset, B_H - 2 * inset
    edge_c = 2 * round_run * (1 - sqrt(2) / 2)            # 45 deg chamfer tangent to the round-over
    zt = edge_c / 2                                       # height of the 45 deg point (n even)
    frustum = chamfer(slab(stadium(w, h), lift, lift + B_SEAM_Z).edges().group_by(Axis.Z)[0], edge_c)
    frustum &= Pos(0, 0, lift + zt / 2) * Box(B_W + 2, B_H + 2, zt)
    top = slab(stadium(w, h), lift + B_BACK_RISE - 0.01, lift + B_SEAM_Z + 5)
    return frustum + loft(secs, ruled=False) + top


def outer():
    return back_shape() & Pos(0, 0, B_SEAM_Z / 2) * Box(B_W + 2, B_H + 2, B_SEAM_Z)


def shell():
    """Cover shell: back_shape hollowed by BC_SIDE_WALL sideways and BC_WALL at the back, the inside round-over
    BC_IN_RUN across, open at the seam."""
    return outer() - back_shape(BC_SIDE_WALL, BC_WALL, BC_IN_RUN)


def corner_cuts():
    """45 deg prisms removing the end section's lower outer corners (flex outline follows)."""
    out = None
    yc = copper_y()
    for sx in (-1, 1):
        c = Pos(sx * BC_END_XO, yc, BC_FLEX_Z) * Rot(0, 45, 0) * Box(BC_END_CORNER * sqrt(2), 10, BC_END_CORNER * sqrt(2))
        out = c if out is None else out + c
    return out


def latches():
    """Snap clips at both ends (x = 0): columns standing on the shell's curved inner surface, tops BC_LATCH_TOPS
    above the inside floor, a hook at the tip pointing inwards over the housing's wall (45 deg top, so the cover
    prints back down without supports), hook tip BC_LATCH_REACH in from the outside rim; underside flat under a
    BC_LATCH_CATCH tip face, or 45 deg back to the column (None)."""
    from build123d import Polyline, Plane, extrude, make_face
    out = None
    t = BC_LATCH_T
    for s, i in ((-1, 0), (1, 1)):
        top_in, reach, h = BC_LATCH_TOPS[i], BC_LATCH_REACH[i], BC_LATCH_HOOK[i]
        yi = B_H / 2 - reach + h                        # clip's inner face (the hook stands h further in)
        yo = yi + t                                     # outer face
        top = BC_WALL + top_in
        f = BC_LATCH_CATCH[i]
        under = [(yi - h, top - 2 * h), (yi, top - 3 * h)] if f is None else [(yi - h, top - h - f), (yi, top - h - f)]
        pts = [(yi, 0.3), (yo, 0.3), (yo, top), (yi - h, top - h)] + under + [(yi, 0.3)]
        prof = extrude(Plane.YZ * make_face(Polyline(*pts)), BC_LATCH_W[i] / 2, both=True)   # profile y / z, along x
        prof &= back_shape(0.0, 0.0)                    # not through the outside
        e = prof if s > 0 else prof.mirror(Plane.XZ)
        out = e if out is None else out + e
    return out


def side_tabs():
    """Free-standing ribs at mid-length, BC_SIDE_TAB_GAP apart on their inner faces, from the shell's
    curved floor up to BC_SIDE_TAB_RIM_GAP below the rim (no hook): they keep the sides from flexing."""
    w, t = BC_SIDE_TAB
    x0 = BC_SIDE_TAB_GAP / 2                            # rib's inner face
    z0, z1 = 0.5, B_SEAM_Z - BC_SIDE_TAB_RIM_GAP        # from inside the shell (fuses with it) to the top
    out = None
    for s in (1, -1):
        tab = Pos(s * (x0 + t / 2), 0, (z0 + z1) / 2) * Box(t, w, z1 - z0)
        out = tab if out is None else out + tab
    out &= back_shape(0.0, 0.0) + Pos(0, 0, 50 + B_SEAM_Z - 0.01) * Box(200, 200, 100)   # not through the outside
    return out


def inner_x(z):
    """Long side wall's inside face (x) at height z: the shell's inner round-over, straight above it."""
    zr = z - BC_WALL
    if zr >= B_BACK_RISE:
        return B_W / 2 - BC_SIDE_WALL
    t = acos(max(-1.0, min(1.0, 1 - zr / B_BACK_RISE)))
    return B_W / 2 - BC_SIDE_WALL - BC_IN_RUN * (1 - sin(t))


def tabs():
    """Small tabs inside both long side walls (D-90), two per side either side of mid-length, into the slots in the
    housing's long sides: BC_TAB along y less BC_TAB_CLR at each end, BC_TAB's height below the rim, standing its
    protrusion in from the side wall's inside face at the tab's mid-height (fused into the wall)."""
    gi, go, top, h, prot = BC_TAB
    y0, y1 = gi / 2 + BC_TAB_CLR, go / 2 - BC_TAB_CLR
    z0, z1 = B_SEAM_Z - top - h, B_SEAM_Z - top
    x_in = inner_x((z0 + z1) / 2)
    x0, x1 = x_in - prot, B_W / 2 - BC_SIDE_WALL + 0.3
    out = None
    for sx in (-1, 1):
        for sy in (-1, 1):
            t = Pos(sx * (x0 + x1) / 2, sy * (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)
            out = t if out is None else out + t
    return out


def cover():
    """Printed cover: shell, flex ledge, contact blocks, spring pin windows, steel-plate pocket, snap ears, side
    ribs, the small tabs into the housing's slots."""
    body = shell()
    ys = stiffener_y()
    for x0, x1, y0, y1 in strip_boxes():
        body += Pos((x0 + x1) / 2, (y0 + y1) / 2, (BC_WALL + BC_FLEX_Z) / 2 - 0.25) * Box(x1 - x0, y1 - y0,
                                                                                       BC_FLEX_Z - BC_WALL + 0.5)
    for a, b, z0, z1 in end_blocks()[:2]:
        yb = ys - BC_TERM_Y * BC_BLOCK_T / 2
        body += Pos((a + b) / 2, yb, (BC_WALL + z1) / 2 - 0.25) * Box(b - a, BC_BLOCK_T, z1 - BC_WALL + 0.5) & end_round()
    body += end_retainers()
    body += end_slots()
    body -= run_notch()
    for x0, x1, y0, y1 in strip_boxes(0.1):               # relief over the flex where the 45 deg fill reaches it
        body -= Pos((x0 + x1) / 2, (y0 + y1) / 2, BC_FLEX_Z + (FLEX_T + 0.3) / 2) * Box(x1 - x0, y1 - y0, FLEX_T + 0.3)
    body &= Pos(0, 0, 50) * Box(200, 200, 100)                             # nothing below the back face
    body &= outer() + Pos(0, 0, 50 + B_SEAM_Z - 0.01) * Box(200, 200, 100)  # blocks may rise above the seam
    body += latches() + side_tabs()
    body += tabs()                                      # into the slots in the housing's long sides (D-90)
    w, d = BC_PRY                                       # flat-blade screwdriver notch in the rim at the bottom end
    body -= Pos(0, -B_H / 2, B_SEAM_Z - d / 2 + 0.01) * Box(w, 2 * (BC_WALL + 1.0), d + 0.02)
    for x, y in BC_FINGERS:                             # windows for the spring pins onto the pads (D-50)
        body -= Pos(x, y, BC_FLEX_Z / 2) * Cylinder(PIN_BARREL[0] / 2 + BC_WIN_CLR, BC_FLEX_Z + 1.0)
    c = 2 * BC_STEEL_CLR                                # plate's seat: flat floor, the plate plus clearance
    body -= Pos(0, BC_STEEL_Y, BC_STEEL_FLOOR + 5.0) * Box(BC_STEEL[0] + c, BC_STEEL[1] + c, 10.0)
    body += steel_ridge()
    body -= steel_clip_reliefs()
    body += steel_clips()
    z0 = BC_FLEX_Z + FLEX_T                              # room for the pad stiffener up to the snap lips
    z1 = z0 + BC_STIFF_ADH + BC_PAD_STIFF_T + BC_FLEX_SNAP_GAP
    for x0, x1, y0, y1 in strip_boxes(0.1)[:2]:
        body -= Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)
    body -= flex_snap_reliefs()
    body += flex_snaps()
    x0, x1, y0, y1 = BC_REG_RECESS
    body -= Pos((x0 + x1) / 2, (y0 + y1) / 2, (BC_REG_FLOOR + BC_FLEX_Z) / 2) * Box(x1 - x0, y1 - y0,
                                                                                    BC_FLEX_Z - BC_REG_FLOOR)
    return body


def flex_snap_spots():
    """Snap hook sites (x of the edge, side: -1 inner / +1 outer, y): both long edges beside each pad and the regulator,
    less the inner edge beside the GND pad, where the jog leaves for the run (D-79)."""
    xs0, xs1 = BC_STRIP
    yg = min(y for _, y in BC_FINGERS)
    ys = [y for _, y in BC_FINGERS] + [strip_top() + BC_JOG / 2]
    return [(xe, s, y) for y in ys for xe, s in ((xs1, 1), (xs0, -1)) if not (s < 0 and abs(y - yg) < 1e-6)]


def flex_snaps():
    """Snap hooks on both long edges of the pad and regulator sections: a post beside the edge rising from the
    bottom of its relief, a lip over the stiffener, a 45 deg lead-in on top (the section presses in from above)."""
    from build123d import Polyline, Plane, extrude, make_face
    w, t, lip, clr = BC_FLEX_SNAP
    zl = BC_FLEX_Z + FLEX_T + BC_STIFF_ADH + BC_PAD_STIFF_T + BC_FLEX_SNAP_GAP   # lip underside
    out = None
    for xe, s, y in flex_snap_spots():
        xi, xo = xe + s * clr, xe + s * (clr + t)                         # post faces (inner, outer)
        pts = [(xi, 0.0), (xo, 0.0), (xo, zl + 2 * lip), (xi - s * lip, zl + lip), (xi - s * lip, zl), (xi, zl),
               (xi, 0.0)]
        prof = Pos(0, y, 0) * extrude(Plane.XZ * make_face(Polyline(*pts)), w / 2, both=True)
        out = prof if out is None else out + prof
    return out & back_shape(0.0, 0.0)


def flex_snap_reliefs():
    """Pockets round each post, down to BC_FLEX_SNAP_ROOT of shell, so the post bends from there."""
    w, t, lip, clr = BC_FLEX_SNAP
    r = BC_FLEX_SNAP_RELIEF
    out = None
    for xe, s, y in flex_snap_spots():
        x0, x1 = xe + s * 0.05, xe + s * (clr + t + r)
        p = Pos((x0 + x1) / 2, y, 5.0) * Box(abs(x1 - x0), w + 2 * r, 10.0)
        out = p if out is None else out + p
    return out & back_shape(BC_FLEX_SNAP_ROOT, BC_FLEX_SNAP_ROOT)


def pad_stiffener():
    """FR4 on the flex's pad and regulator sections (non-copper side), on BC_STIFF_ADH of adhesive."""
    z0 = BC_FLEX_Z + FLEX_T + BC_STIFF_ADH
    out = None
    for x0, x1, y0, y1 in strip_boxes()[:2]:
        s = Pos((x0 + x1) / 2, (y0 + y1) / 2, z0 + BC_PAD_STIFF_T / 2) * Box(x1 - x0, y1 - y0, BC_PAD_STIFF_T)
        out = s if out is None else out + s
    return out


def end_round():
    """Room for the blocks and the end section: the circle BC_END_R round each cell axis (the cell's room in the
    housing), plus everything below the cell axes, plus everything below the rim between the axes. Outboard of the
    cells above their axes the battery holder shell wraps the cells."""
    out = Pos(0, 0, BC_CELL_Z - 50) * Box(200, 200, 100)
    out += Pos(0, 0, B_SEAM_Z - 50) * Box(2 * BC_CELL_X, 200, 100)
    for sx in (-1, 1):
        out += Pos(sx * BC_CELL_X, 0, BC_CELL_Z) * Rot(90, 0, 0) * Cylinder(BC_END_R, 200)
    return out


def end_retainers():
    """End section retention on each contact block: a lip in front of its foot (the section's lower edge drops into
    the slot between lip and stiffener). In use the battery contacts press the section into the blocks."""
    t, h, gap = BC_END_LIP
    yc = copper_y()
    sy = -BC_TERM_Y                                      # +1: cells side (blocks) is +y
    out = None
    for a, b, z0, z1 in end_blocks()[:2]:
        a2, b2 = a + 0.5, b - 1.6                        # clear of the 45 deg corner cut and the notch side
        y_l0, y_l1 = yc - sy * gap, yc - sy * (gap + t)  # lip faces
        lip = Pos((a2 + b2) / 2, (y_l0 + y_l1) / 2, (BC_WALL + BC_FLEX_Z + h) / 2) * Box(
            b2 - a2, t, BC_FLEX_Z + h - BC_WALL)
        out = lip if out is None else out + lip
    return out


def end_slots():
    """A slot along each contact block's outer face, inside the block's outline: a side wall beyond the end
    section's outer edge and a lip over the edge on the copper side, from the ledge to the block's top. The section
    slides down the two slots from above into the slot behind the foot lips."""
    wall, clr, reach, lt, gap = BC_END_SLOT
    sy = -BC_TERM_Y                                      # +1: cells side (blocks) is +y
    yc, ys = copper_y(), stiffener_y()
    y_l, y_f = yc - sy * gap, yc - sy * (gap + lt)       # lip's back and front faces
    z0, z1 = BC_FLEX_Z, BC_FLEX_Z + BC_END_H
    out = None
    for s in (-1, 1):
        u0, u1 = BC_BLOCK_XO - wall, BC_BLOCK_XO          # side wall
        side = Pos(s * (u0 + u1) / 2, (ys + y_f) / 2, (z0 + z1) / 2) * Box(u1 - u0, abs(y_f - ys), z1 - z0)
        l0 = BC_END_XO - reach                             # lip, over the section's edge
        lip = Pos(s * (l0 + u0) / 2, (y_l + y_f) / 2, (z0 + z1) / 2) * Box(u0 - l0, lt, z1 - z0)
        part = side + lip
        out = part if out is None else out + part
    return out & end_round()


def run_notch():
    """Notch along the GND contact block's inner face, from the ledge up, for the run: it drops in from above (no
    threading); the block stays one piece outside it, the end section's stiffener spans the notch beside the GND
    finger (D-79)."""
    x0, x1 = BC_PCB_W / 2 + BC_PCB_CLR - 0.1, BC_RUN[1] + 0.15
    yb = stiffener_y() - BC_TERM_Y * BC_BLOCK_T / 2
    z0 = BC_FLEX_Z
    return Pos((x0 + x1) / 2, yb, z0 + 10.0) * Box(x1 - x0, BC_BLOCK_T + 1.0, 20.0)


def flex():
    """The flex in place (FLEX_T thick): pad section and strip on the ledge, the run bent up (BC_BEND_R) into the end
    section standing up the blocks, relief slits either side of the run (D-116)."""
    yc = copper_y()
    sy = -BC_TERM_Y
    yf = yc + sy * FLEX_T / 2
    boxes = strip_boxes()
    x0, x1, _, yb = boxes[2]
    boxes[2] = (x0, x1, yc + sy * (FLEX_T + BC_BEND_R), yb)     # the run leaves the ledge at the bend
    out = None
    for x0, x1, y0, y1 in boxes:
        b = Pos((x0 + x1) / 2, (y0 + y1) / 2, Z_BEND) * Box(x1 - x0, abs(y1 - y0), FLEX_T)
        out = b if out is None else out + b
    end = None
    for a, b, z0, z1 in end_section():
        e = Pos((a + b) / 2, yf, (z0 + z1) / 2) * Box(b - a, FLEX_T, z1 - z0)
        end = e if end is None else end + e
    for a, b, z0, z1 in slit_cuts(bend_z()):
        end -= Pos((a + b) / 2, yf, (z0 + z1) / 2) * Box(b - a, FLEX_T + 1, z1 - z0)
    return (out + end + bend_arc() - corner_cuts()) & end_round()


def stiffener():
    """FR4 behind the end section (BC_STIFF_ADH of adhesive on the flex), notched round the run and its slits up to
    BC_BEND_CLR past the bend zone (D-116)."""
    ys = copper_y() - BC_TERM_Y * (FLEX_T + BC_STIFF_ADH + BC_END_T / 2)
    out = None
    for a, b, z0, z1 in end_section():
        s = Pos((a + b) / 2, ys, (z0 + z1) / 2) * Box(b - a, BC_END_T, z1 - z0)
        out = s if out is None else out + s
    w, (xr0, xr1) = BC_SLIT[0], BC_RUN
    zn = bend_z() + BC_BEND_CLR
    out -= Pos((xr0 + xr1) / 2, ys, (BC_FLEX_Z - 1 + zn) / 2) * Box(xr1 - xr0 + 2 * (w + 0.2), BC_END_T + 1, zn - BC_FLEX_Z + 1)
    return (out - corner_cuts()) & end_round()


def pads():
    """The contact fingers' solder pads on the end section's copper face."""
    yc = copper_y()
    out = None
    for sx in (-1, 1):
        p = Pos(sx * BC_CELL_X, yc + BC_TERM_Y * 0.01, BC_CELL_Z) * Box(FINGER_PAD[0], 0.02, FINGER_PAD[1])
        out = p if out is None else out + p
    return out


def end_fingers(h=FINGER_WH):
    """S7081-42R on the end section at the cell axes, domes towards the terminals; long axis vertical with the
    bend end up, so the battery contacts ride down the arm's ramp onto the dome as the cover goes on."""
    out = None
    for sx in (-1, 1):
        f = Pos(sx * BC_CELL_X, copper_y(), BC_CELL_Z) * Rot(90 * BC_TERM_Y, 0, 0) * finger(h)
        out = f if out is None else out + f
    return out


def finger(h):
    """One S7081-42R (drawing iss. 7) hanging from the flex underside at height h: foot on the flex,
    arm down from the bend end, contact dome at the bottom. Local: long axis y, origin at the body centre."""
    foot = Pos(0, 0, -0.075) * Box(FINGER[0], FINGER[1], 0.15)
    yb = -FINGER[1] / 2 + 0.3                             # bend end
    yd = BC_DOME_DY                                       # dome
    run, drop = yd - yb, h - 0.15 - 0.33
    length = sqrt(run * run + drop * drop)
    ang = degrees(atan2(drop, run))
    arm = Pos(0, (yb + yd) / 2, -0.15 - drop / 2) * Rot(-ang, 0, 0) * Box(FINGER[0] - 0.4, length, 0.15)
    dome = Pos(0, yd, -h + 0.33 / 2) * Cylinder(1.3 / 2, 0.33)
    return foot + arm + dome


def pin_pads():
    """Gold pads on the flex underside, over the windows: the spring pins from the plate press on them (D-50)."""
    out = None
    for x, y in BC_FINGERS:
        d = Pos(x, y, BC_FLEX_Z + 0.005) * Cylinder(BC_PAD_D / 2, 0.01)
        out = d if out is None else out + d
    return out


def regulator():
    """TLV75533, its two capacitors and the ESD diode hanging from the flex underside (copper down) into the recess."""
    out = None
    for ref, (x, y) in BC_REG.items():
        w, h, t = {"U1": BC_REG_BODY, "D1": BC_TVS}.get(ref, BC_CAP0603)
        p = Pos(x, y, BC_FLEX_Z - t / 2) * Box(w, h, t)
        out = p if out is None else out + p
    return out


def steel_ridge():
    """Ridge round the plate on the cover's floor, inner face BC_STEEL_CLR from the plate, open at the clips."""
    t, h = BC_STEEL_RIDGE
    cw = BC_STEEL_CLIP[0]
    ix, iy = BC_STEEL[0] / 2 + BC_STEEL_CLR, BC_STEEL[1] / 2 + BC_STEEL_CLR
    z0, z1 = BC_STEEL_FLOOR - 0.3, BC_STEEL_FLOOR + h   # down into the shell (fuses with it)
    ring = Box(2 * (ix + t), 2 * (iy + t), z1 - z0) - Box(2 * ix, 2 * iy, z1 - z0 + 1)
    ring -= Box(cw + 2 * BC_STEEL_RIDGE_GAP, 2 * (iy + t) + 1, z1 - z0 + 1)
    ring = Pos(0, BC_STEEL_Y, (z0 + z1) / 2) * ring
    return ring & back_shape(0.0, 0.0)


def steel_clips():
    """A clip at each end of the plate: a tab rising from the bottom of its relief at the pocket's end, a hook over
    the plate's edge with a 45 deg lead-in on top, so the plate snaps in from above."""
    from build123d import Polyline, Plane, extrude, make_face
    cw, ct, ch = BC_STEEL_CLIP
    z0, zh = BC_STEEL_CLIP_ROOT, BC_STEEL_FLOOR + BC_STEEL[2] + 0.1      # tab root, hook underside
    out = None
    for s in (1, -1):
        ye = BC_STEEL[1] / 2 + BC_STEEL_CLIP_CLR        # tab inner face, outwards distance from the plate centre
        pts = [(ye, z0 - 0.01), (ye + ct, z0 - 0.01), (ye + ct, zh + 2 * ch), (ye - ch, zh + ch), (ye - ch, zh),
               (ye, zh), (ye, z0 - 0.01)]
        prof = extrude(Plane.YZ * make_face(Polyline(*pts)), cw / 2, both=True)
        c = Pos(0, BC_STEEL_Y, 0) * (prof if s > 0 else prof.mirror(Plane.XZ))
        out = c if out is None else out + c
    return out


def steel_clip_reliefs():
    """Pockets round each plate clip's tab down to BC_STEEL_CLIP_ROOT of shell, so the tab bends from there."""
    cw, ct, ch = BC_STEEL_CLIP
    r = BC_STEEL_CLIP_RELIEF
    ye = BC_STEEL[1] / 2 + BC_STEEL_CLIP_CLR
    out = None
    for s in (1, -1):
        y0, y1 = ye - r, ye + ct + r
        p = Pos(0, BC_STEEL_Y + s * (y0 + y1) / 2, BC_STEEL_CLIP_ROOT + 5.0) * Box(cw + 2 * r, y1 - y0, 10.0)
        out = p if out is None else out + p
    return out & back_shape(BC_STEEL_CLIP_ROOT, BC_STEEL_CLIP_ROOT)


def steel():
    return Pos(0, BC_STEEL_Y, BC_STEEL_FLOOR + BC_STEEL[2] / 2 + 0.01) * Box(*BC_STEEL)


def cover_parts(free=False):
    """The cover assembly in remote coordinates (end fingers free or at working height)."""
    h = FINGER_FREE if free else FINGER_WH
    return {"cover": cover(), "flex": flex(), "stiffener": stiffener(), "pads": pads(),
            "pin_pads": pin_pads(), "contacts": end_fingers(h), "regulator": regulator(), "steel": steel(),
            "pad_stiffener": pad_stiffener()}


def remote_front():
    """The remote above its parting line (its own back cover removed), z = 0 its back face."""
    r = Pos(0, 0, -SEAT_Z) * bilresa.build()
    r &= Pos(0, 0, 50 + B_SEAM_Z) * Box(200, 200, 100)
    return r


if __name__ == "__main__":
    from pathlib import Path
    from build123d import export_step, export_stl
    out = Path(__file__).resolve().parents[2] / "build"
    out.mkdir(exist_ok=True)
    c = cover()
    print("cover valid:", c.is_valid, "solids:", len(c.solids()), f"volume {c.volume / 1000:.2f} cm3")
    export_step(c, str(out / "back_cover.step"))
    export_stl(c, str(out / "back_cover.stl"))
