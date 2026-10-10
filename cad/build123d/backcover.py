"""REPLACEMENT BACK COVER (D-35): replaces the BILRESA E2490's back cover; the remote runs without
cells from the plate's +3V3.

The cover keeps the remote's back shape (cut to a 45 deg chamfer below the curve's 45 deg point,
so it prints back down without supports) and carries the remote's steel plate. Inside, a
single-layer flex lies copper down on a ledge BC_FLEX_Z above the back face; two Harwin S7081-42R
spring fingers on it reach down through windows in the back. The flex runs to the terminal end,
bends up once and stands against two contact blocks; two more S7081-42R fingers on it, on the cell
axes, press on the remote's VBAT (fixed plate) and GND (leaf spring) battery contacts. The fingers
on the back take +5 V; a 3.3 V regulator on the flex (copper down, in a recess in the cover) feeds
VBAT. No cells: the remote's strap joins the bridge-end contacts.

On the face plate side a printed pocket-floor insert carries a tongue of the sensor flex in a
recess, its two gold pads flush under the fingers. The magnet holds the cover's back down on the
insert: that hard stop sets the fingers' working height.

Remote coordinates: origin = remote centre, x / y as the front view, z = 0 the back's outer face.
Sizes marked MEASURE / REF in params.py.
"""
from math import atan2, cos, degrees, pi, sin, sqrt
from build123d import Axis, Box, Cylinder, Plane, Pos, Rot, chamfer, loft
from params import *
from common import stadium, slab
import bilresa

Z_BEND = BC_FLEX_Z + FLEX_T / 2                          # flex mid-plane on the ledge
EDGE_C = 2 * B_BACK_RUN * (1 - sqrt(2) / 2)              # 45 deg chamfer tangent to the R B_BACK_RUN back curve


def copper_y():
    """y of the end section's copper face: FINGER_WH from the fixed contact plate, towards the cells."""
    return BC_COPPER_Y


def stiffener_y():
    """y of the stiffener's far face (towards the cells): the contact blocks start here."""
    return copper_y() - BC_TERM_Y * (FLEX_T + BC_END_T)


def end_blocks():
    """End section outline in the (x, z) plane: two pad blocks and the band under the PCB strip."""
    z0, z1 = BC_FLEX_Z, BC_FLEX_Z + BC_END_H
    xi = BC_PCB_W / 2 + BC_PCB_CLR
    xo = BC_CELL_X + BC_CONTACT_W / 2 + 0.5
    return [(-xo, -xi, z0, z1), (xi, xo, z0, z1), (-xi, xi, z0, z0 + BC_BRIDGE_H)]


def strip_top():
    return max(y for _, y in BC_FINGERS) + FINGER[1] / 2 + BC_PAD_END


def strip_bottom():
    """Lower end of the pad section; the run continues to the terminal end after BC_JOG."""
    return min(y for _, y in BC_FINGERS) - FINGER[1] / 2 - 1.0


def strip_boxes(clr=0.0):
    """Flex path on the ledge as (x0, x1, y0, y1): pad section, jog, run to the terminal end."""
    yc = copper_y()
    yt, yb = strip_top(), strip_bottom()
    yj = yb - BC_JOG
    xs0, xs1 = BC_STRIP
    xr0, xr1 = BC_RUN
    return [(xs0 - clr, xs1 + clr, yb, yt), (min(xs0, xr0) - clr, max(xs1, xr1) + clr, yj, yb),
            (xr0 - clr, xr1 + clr, min(yc, yj), max(yc, yj))]


def back_shape(inset=0.0, lift=0.0):
    """The remote's back (flat pad, quarter-circle round-over, straight sides) inset by `inset` all
    round and raised by `lift`. Below the curve's 45 deg point the round-over is replaced by its
    45 deg tangent (a frustum), so the cover prints back down without supports."""
    n = bilresa.N_SECT
    secs = []
    for i in range(n // 2, n + 1):                        # from the 45 deg point up
        t = (pi / 2) * i / n
        run = B_BACK_RUN * (1 - sin(t)) + inset
        secs.append(Plane.XY.offset(lift + B_BACK_RISE * (1 - cos(t))) * stadium(B_W - 2 * run, B_H - 2 * run))
    w, h = B_W - 2 * inset, B_H - 2 * inset
    zt = EDGE_C / 2                                       # height of the 45 deg point (n even)
    frustum = chamfer(slab(stadium(w, h), lift, lift + B_SEAM_Z).edges().group_by(Axis.Z)[0], EDGE_C)
    frustum &= Pos(0, 0, lift + zt / 2) * Box(B_W + 2, B_H + 2, zt)
    top = slab(stadium(w, h), lift + B_BACK_RISE - 0.01, lift + B_SEAM_Z + 5)
    return frustum + loft(secs, ruled=False) + top


def outer():
    return back_shape() & Pos(0, 0, B_SEAM_Z / 2) * Box(B_W + 2, B_H + 2, B_SEAM_Z)


def shell():
    """Cover shell: back_shape hollowed by BC_WALL (inset sideways and raised), open at the seam."""
    return outer() - back_shape(BC_WALL, BC_WALL)


def corner_cuts():
    """45 deg prisms removing the end section's lower outer corners (flex outline follows)."""
    out = None
    yc = copper_y()
    for sx in (-1, 1):
        xo = BC_CELL_X + BC_CONTACT_W / 2 + 0.5
        c = Pos(sx * xo, yc, BC_FLEX_Z) * Rot(0, 45, 0) * Box(BC_END_CORNER * sqrt(2), 10, BC_END_CORNER * sqrt(2))
        out = c if out is None else out + c
    return out


def latches():
    """Snap clips at both ends (x = 0): columns standing on the shell's curved inner surface, tops BC_LATCH_TOPS
    above the inside floor, a hook at the tip pointing inwards over the housing's wall (45 deg top, so the cover
    prints back down without supports), hook tip BC_LATCH_REACH in from the outside rim."""
    from build123d import Polyline, Plane, extrude, make_face
    out = None
    t = BC_LATCH_T
    for s, i in ((-1, 0), (1, 1)):
        top_in, reach, h = BC_LATCH_TOPS[i], BC_LATCH_REACH[i], BC_LATCH_HOOK[i]
        yi = B_H / 2 - reach + h                        # clip's inner face (the hook stands h further in)
        yo = yi + t                                     # outer face
        top = BC_WALL + top_in
        pts = [(yi, 0.3), (yo, 0.3), (yo, top), (yi - h, top - h), (yi - h, top - 2 * h), (yi, top - 3 * h), (yi, 0.3)]
        prof = extrude(Plane.YZ * make_face(Polyline(*pts)), BC_LATCH_W / 2, both=True)   # profile y / z, along x
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


def cover():
    """Printed cover: shell, flex ledge, contact blocks, finger windows, steel-plate pocket, snap ears, side tabs."""
    body = shell()
    yc, ys = copper_y(), stiffener_y()
    for x0, x1, y0, y1 in strip_boxes():
        body += Pos((x0 + x1) / 2, (y0 + y1) / 2, (BC_WALL + BC_FLEX_Z) / 2 - 0.25) * Box(x1 - x0, y1 - y0,
                                                                                       BC_FLEX_Z - BC_WALL + 0.5)
    for a, b, z0, z1 in end_blocks()[:2]:
        yb = ys - BC_TERM_Y * BC_BLOCK_T / 2
        body += Pos((a + b) / 2, yb, (BC_WALL + z1) / 2 - 0.25) * Box(b - a, BC_BLOCK_T, z1 - BC_WALL + 0.5) & end_round()
    body += end_retainers()
    body -= end_snap_reliefs()
    body += end_snaps()
    body -= run_notch()
    for x0, x1, y0, y1 in strip_boxes(0.1):               # relief over the flex where the 45 deg fill reaches it
        body -= Pos((x0 + x1) / 2, (y0 + y1) / 2, BC_FLEX_Z + (FLEX_T + 0.3) / 2) * Box(x1 - x0, y1 - y0, FLEX_T + 0.3)
    body &= Pos(0, 0, 50) * Box(200, 200, 100)                             # nothing below the back face
    body &= outer() + Pos(0, 0, 50 + B_SEAM_Z - 0.01) * Box(200, 200, 100)  # blocks may rise above the seam
    body += latches() + side_tabs()
    w, d = BC_PRY                                       # flat-blade screwdriver notch in the rim at the bottom end
    body -= Pos(0, -B_H / 2, B_SEAM_Z - d / 2 + 0.01) * Box(w, 2 * (BC_WALL + 1.0), d + 0.02)
    for x, y in BC_FINGERS:
        body -= Pos(x, y, BC_FLEX_Z / 2) * Box(FINGER[0] + 2 * BC_WIN_CLR, FINGER[1] + 2 * BC_WIN_CLR, BC_FLEX_Z + 1.0)
    c = 2 * BC_STEEL_CLR                                # plate's seat: flat floor, the plate plus clearance
    body -= Pos(0, BC_STEEL_Y, BC_STEEL_FLOOR + 5.0) * Box(BC_STEEL[0] + c, BC_STEEL[1] + c, 10.0)
    body += steel_ridge()
    body -= steel_clip_reliefs()
    body += steel_clips()
    z0 = BC_FLEX_Z + FLEX_T                              # room for the pad stiffener up to the snap lips
    z1 = z0 + BC_PAD_STIFF_T + BC_FLEX_SNAP_GAP
    for x0, x1, y0, y1 in strip_boxes(0.1)[:2]:
        body -= Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)
    body -= flex_snap_reliefs()
    body += flex_snaps()
    x0, x1, y0, y1 = BC_REG_RECESS
    body -= Pos((x0 + x1) / 2, (y0 + y1) / 2, (BC_REG_FLOOR + BC_FLEX_Z) / 2) * Box(x1 - x0, y1 - y0,
                                                                                    BC_FLEX_Z - BC_REG_FLOOR)
    return body


def flex_snap_spots():
    """Snap hook sites (x of the section's two long edges, y): beside each finger and the regulator."""
    xs0, xs1 = BC_STRIP
    yb, yj = strip_bottom(), strip_bottom() - BC_JOG
    return [(xs0, xs1, y) for _, y in BC_FINGERS] + [(min(xs0, BC_RUN[0]), max(xs1, BC_RUN[1]), (yb + yj) / 2)]


def flex_snaps():
    """Snap hooks on both long edges of the pad and regulator sections: a post beside the edge rising from the
    bottom of its relief, a lip over the stiffener, a 45 deg lead-in on top (the section presses in from above)."""
    from build123d import Polyline, Plane, extrude, make_face
    w, t, lip, clr = BC_FLEX_SNAP
    zl = BC_FLEX_Z + FLEX_T + BC_PAD_STIFF_T + BC_FLEX_SNAP_GAP          # lip underside
    out = None
    for xl, xr, y in flex_snap_spots():
        for xe, s in ((xr, 1), (xl, -1)):
            xi, xo = xe + s * clr, xe + s * (clr + t)                     # post faces (inner, outer)
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
    for xl, xr, y in flex_snap_spots():
        for xe, s in ((xr, 1), (xl, -1)):
            x0, x1 = xe + s * 0.05, xe + s * (clr + t + r)
            p = Pos((x0 + x1) / 2, y, 5.0) * Box(abs(x1 - x0), w + 2 * r, 10.0)
            out = p if out is None else out + p
    return out & back_shape(BC_FLEX_SNAP_ROOT, BC_FLEX_SNAP_ROOT)


def pad_stiffener():
    """FR4 on the flex's pad and regulator sections (non-copper side)."""
    z0 = BC_FLEX_Z + FLEX_T
    out = None
    for x0, x1, y0, y1 in strip_boxes()[:2]:
        s = Pos((x0 + x1) / 2, (y0 + y1) / 2, z0 + BC_PAD_STIFF_T / 2) * Box(x1 - x0, y1 - y0, BC_PAD_STIFF_T)
        out = s if out is None else out + s
    return out


def end_round():
    """Room for the blocks and the end section: everything below the rim, above it the circle BC_END_R round each
    cell axis (the cell's room in the housing)."""
    out = Pos(0, 0, B_SEAM_Z - 50) * Box(200, 200, 100)
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


def run_notch():
    """Notch through the GND contact block, from the ledge up, for the run: it drops in from above (no threading);
    the end section's stiffener spans the notch behind the GND finger."""
    xr0, xr1 = BC_RUN
    yb = stiffener_y() - BC_TERM_Y * BC_BLOCK_T / 2
    z0 = BC_FLEX_Z
    return Pos((xr0 + xr1) / 2, yb, z0 + 10.0) * Box(xr1 - xr0 + 0.3, BC_BLOCK_T + 1.0, 20.0)


def end_snaps():
    """A snap hook beside each contact block's outer side: a post rising from the bottom of its relief, beside the
    end section's outer edge, with a lip over the section's copper face in the band BC_END_SNAP_Z and a 45 deg
    lead-in on the lip's front (the section folds up onto the blocks and pushes the post outwards)."""
    from build123d import Polyline, extrude, make_face
    t, reach, clr, lt, gap = BC_END_SNAP
    z0, z1 = BC_END_SNAP_Z
    sy = -BC_TERM_Y                                      # +1: cells side (blocks) is +y
    y_l = copper_y() - sy * gap                          # lip's back face, towards the copper
    y_f = y_l - sy * lt                                  # lip's front face
    y_b = stiffener_y() + sy * BC_END_SNAP_BACK
    out = None
    for a, b, _, _ in end_blocks()[:2]:
        s = 1 if a + b > 0 else -1
        ue = b if s > 0 else -a                          # section's outer edge, distance from x 0
        post = [(ue + clr, y_b), (ue + clr + t, y_b), (ue + clr + t, y_f), (ue + clr, y_f)]
        lip = [(ue + clr + t, y_l), (ue + clr + t, y_f), (ue, y_f), (ue - reach, y_f + sy * reach), (ue - reach, y_l)]
        part = None
        for pts, za in ((post, BC_FLEX_SNAP_ROOT), (lip, z0)):
            f = make_face(Polyline(*[(s * u, y) for u, y in pts], (s * pts[0][0], pts[0][1])))
            e = Pos(0, 0, za) * extrude(f, z1 - za)
            part = e if part is None else part + e
        out = part if out is None else out + part
    return out & back_shape(0.0, 0.0)


def end_snap_reliefs():
    """Pockets round each end snap's post, down to BC_FLEX_SNAP_ROOT of shell, so the post bends from there."""
    t, reach, clr, lt, gap = BC_END_SNAP
    r = BC_FLEX_SNAP_RELIEF
    sy = -BC_TERM_Y
    y_f = copper_y() - sy * (gap + lt) - sy * r
    y_b = stiffener_y() + sy * (BC_END_SNAP_BACK + r)
    out = None
    for a, b, _, _ in end_blocks()[:2]:
        s = 1 if a + b > 0 else -1
        ue = b if s > 0 else -a
        u0, u1 = ue + 0.05, ue + clr + t + r
        p = Pos(s * (u0 + u1) / 2, (y_f + y_b) / 2, 5.0) * Box(u1 - u0, abs(y_b - y_f), 10.0)
        out = p if out is None else out + p
    return out & back_shape(BC_FLEX_SNAP_ROOT, BC_FLEX_SNAP_ROOT)


def flex():
    """The flex in place (FLEX_T thick): pad section and strip on the ledge, end section up the blocks."""
    yc = copper_y()
    yf = yc - BC_TERM_Y * FLEX_T / 2
    out = None
    for x0, x1, y0, y1 in strip_boxes():
        b = Pos((x0 + x1) / 2, (y0 + y1) / 2, Z_BEND) * Box(x1 - x0, y1 - y0, FLEX_T)
        out = b if out is None else out + b
    for a, b, z0, z1 in end_blocks():
        out += Pos((a + b) / 2, yf, (z0 + z1) / 2) * Box(b - a, FLEX_T, z1 - z0)
    return (out - corner_cuts()) & end_round()


def stiffener():
    ys = copper_y() - BC_TERM_Y * (FLEX_T + BC_END_T / 2)
    out = None
    for a, b, z0, z1 in end_blocks():
        s = Pos((a + b) / 2, ys, (z0 + z1) / 2) * Box(b - a, BC_END_T, z1 - z0)
        out = s if out is None else out + s
    return (out - corner_cuts()) & end_round()


def pads():
    """The contact fingers' solder pads on the end section's copper face."""
    yc = copper_y()
    out = None
    for sx in (-1, 1):
        p = Pos(sx * BC_CELL_X, yc + BC_TERM_Y * 0.01, BC_CELL_Z) * Box(FINGER_PAD[1], 0.02, FINGER_PAD[0])
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


def fingers(h=FINGER_WH):
    out = None
    for x, y in BC_FINGERS:
        f = Pos(x, y, BC_FLEX_Z) * finger(h)
        out = f if out is None else out + f
    return out


def regulator():
    """TLV75533 and its two capacitors hanging from the flex underside (copper down) into the recess."""
    out = None
    for ref, (x, y) in BC_REG.items():
        w, h, t = BC_REG_BODY if ref == "U1" else BC_CAP0402
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
    """The cover assembly in remote coordinates (fingers free or at working height)."""
    h = FINGER_FREE if free else FINGER_WH
    return {"cover": cover(), "flex": flex(), "stiffener": stiffener(), "pads": pads(),
            "fingers": fingers(h), "contacts": end_fingers(h), "regulator": regulator(), "steel": steel(),
            "pad_stiffener": pad_stiffener()}


def tongue_path(wall_x):
    """Sensor-flex tongue in the floor insert: (x0, x1, y0, y1, layers) boxes. It enters along y =
    BC_TONGUE_Y from the right channel (copper down, as the flex's pin pads), folds 45 deg under the
    pads' column (copper up) and runs up past both pads."""
    w = BC_TONGUE_W
    xf = BC_FINGERS[0][0]
    ys = [y for _, y in BC_FINGERS]
    y_top = max(ys) + BC_FLOOR_PAD[1] / 2 + 1.0
    run = (xf + w / 2, wall_x, BC_TONGUE_Y - w / 2, BC_TONGUE_Y + w / 2, 1)
    fold = (xf - w / 2, xf + w / 2, BC_TONGUE_Y - w / 2, BC_TONGUE_Y + w / 2, 2)
    up = (xf - w / 2, xf + w / 2, BC_TONGUE_Y + w / 2, y_top, 1)
    return [run, fold, up]


def floor_insert(pocket_in, wall_x, cutouts=(), path=None, pads=None, t=FLEX_T, notches=()):
    """Pocket-floor insert (face plate side), z = 0 its underside: printed floor, the tongue, its flush pads.
    cutouts: (x, y, w, h) openings (switch, trim tabs, bosses), each with BC_FLOOR_CLR all round. path: the tongue's
    (x0, x1, y0, y1, layers[, kind]) boxes on the floor (default: tongue_path(wall_x)); kind "top" (in a recess in
    the top, pads flush), "under" (in a channel in the underside, hidden), "channel" (the channel only, the flex
    drawn elsewhere) or "slot" (through the floor, rising from
    under to top). notches: (x0, x1, y0, y1) cuts from a slot to the floor's edge, so the tongue is laid in
    sideways. pads: (x0, x1, y0, y1) of the flush pads (default: BC_FLOOR_PAD under the fingers). t: flex
    thickness."""
    w, h = pocket_in[0] - 2 * BC_FLOOR_CLR, pocket_in[1] - 2 * BC_FLOOR_CLR
    plate = slab(stadium(w, h), 0, BC_FLOOR_T)
    for x, y, cw, ch in cutouts:
        plate -= Pos(x, y, BC_FLOOR_T / 2) * Box(cw + 2 * BC_FLOOR_CLR, ch + 2 * BC_FLOOR_CLR, BC_FLOOR_T + 1)
    tongue = None
    for e in (path or tongue_path(wall_x)):
        x0, x1, y0, y1, n = e[:5]
        kind = e[5] if len(e) > 5 else "top"
        d = n * t
        xc, yc = (x0 + x1) / 2, (y0 + y1) / 2
        if kind == "top":
            plate -= Pos(xc, yc, BC_FLOOR_T - (d + BC_RECESS_CLR) / 2 + 0.005) * \
                Box(x1 - x0 + 0.3, y1 - y0 + 0.3 * (n == 1), d + BC_RECESS_CLR + 0.01)
            z = BC_FLOOR_T - d / 2
        elif kind in ("under", "channel"):
            plate -= Pos(xc, yc, (d + BC_RECESS_CLR) / 2 - 0.005) * Box(x1 - x0 + 0.3, y1 - y0 + 0.3, d + BC_RECESS_CLR + 0.01)
            z = d / 2
            if kind == "channel":
                continue
        else:
            plate -= Pos(xc, yc, BC_FLOOR_T / 2) * Box(x1 - x0 + 0.3, y1 - y0, BC_FLOOR_T + 1)
            z = BC_FLOOR_T / 2
        seg = Pos(xc, yc, z) * Box(x1 - x0, y1 - y0, d)
        tongue = seg if tongue is None else tongue + seg
    for x0, x1, y0, y1 in notches:
        plate -= Pos((x0 + x1) / 2, (y0 + y1) / 2, BC_FLOOR_T / 2) * Box(x1 - x0, y1 - y0, BC_FLOOR_T + 1)
    pd = None
    for x0, x1, y0, y1 in (pads or [(x - BC_FLOOR_PAD[0] / 2, x + BC_FLOOR_PAD[0] / 2, y - BC_FLOOR_PAD[1] / 2,
                                      y + BC_FLOOR_PAD[1] / 2) for x, y in BC_FINGERS]):
        q = Pos((x0 + x1) / 2, (y0 + y1) / 2, BC_FLOOR_T + 0.005) * Box(x1 - x0, y1 - y0, 0.01)
        pd = q if pd is None else pd + q
    return {"floor": plate, "floor_flex": tongue, "floor_pads": pd}


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
