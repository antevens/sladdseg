"""Small geometry helpers shared by the printed parts."""
from build123d import (Matrix, Pos, Rot, RectangleRounded, Sphere, Cylinder, Plane,
                       extrude, loft, Vector)


def rr(w, h, r):
    """Rounded rectangle sketch; r is clamped so a stadium (r = w/2) still works."""
    return RectangleRounded(w, h, min(r, min(w, h) / 2 - 0.01))


def stadium(w, h):
    """BILRESA-like rounded-end oval (long axis = Y)."""
    return rr(w, h, w / 2)


def slab(sketch, z0, z1):
    """Extrude a 2D sketch between two absolute z levels."""
    return Pos(0, 0, z0) * extrude(sketch, z1 - z0)


def frame(w, h, wall, r, z0, z1, y=0.0):
    outer = rr(w + 2 * wall, h + 2 * wall, r + wall)
    inner = rr(w, h, max(r, 0.3))
    return Pos(0, y, 0) * (slab(outer, z0, z1) - slab(inner, z0 - 1, z1 + 1))


def taper(w, h, r, z0, z1, grow):
    """Rounded-rect frustum: (w,h,r) at z0, offset outward by `grow` at z1."""
    a = Plane.XY.offset(z0) * rr(w, h, r)
    b = Plane.XY.offset(z1) * rr(w + 2 * grow, h + 2 * grow, r + grow)
    return loft([a, b])


def sound_column(port, mic, port_in, board_top, top_z, bore, gasket, boot):
    """Face plate's sound column over a top-port mic (D-83): a rounded column from top_z down to a gasket on the board
    round the mic, hollow over the mic (boot = clearance round the body, wall, gap over its top), the bore from the
    cavity up over the port. port: (x, y); mic: body w, l, h, port end up."""
    from build123d import Box
    clr, wall, gap = boot
    cy = port[1] - (mic[1] / 2 - port_in)                     # body centre
    w, l = mic[0] + 2 * clr, mic[1] + 2 * clr
    z0, zc = board_top + gasket, board_top + mic[2] + gap     # foot, cavity top
    col = Pos(port[0], cy, 0) * slab(rr(w + 2 * wall, l + 2 * wall, wall), z0, top_z)
    col -= Pos(port[0], cy, (z0 + zc) / 2 - 0.5) * Box(w, l, zc - z0 + 1)
    col -= Pos(port[0], port[1], (zc + top_z) / 2) * Cylinder(bore / 2, top_z - zc + 1)
    return col


def ellipsoid(rx, ry, rz):
    """Poles on the Y axis so no mesh singularity lands on a cut surface."""
    return (Rot(90, 0, 0) * Sphere(1)).transform_geometry(Matrix([[rx, 0, 0, 0], [0, ry, 0, 0], [0, 0, rz, 0]]))


def rod(p0, p1, d):
    """Cylinder of diameter d from point p0 to p1."""
    p0, p1 = Vector(*p0), Vector(*p1)
    v = p1 - p0
    c = Cylinder(d / 2, v.length)
    pl = Plane(origin=(p0 + p1) * 0.5, z_dir=v)
    return pl * c


def radial_prism(p, u, pts, w):
    """Prism from a profile in the vertical plane through plan point p along the plan unit vector u: pts are
    (r, z), r along u from p; w wide across, centred on the plane."""
    from build123d import Plane, Polyline, extrude, make_face
    pl = Plane(origin=(p[0], p[1], 0), x_dir=(u[0], u[1], 0), z_dir=(u[1], -u[0], 0))
    return extrude(pl * make_face(Polyline(*pts, pts[0])), w / 2, both=True)


def ribbon(pts, w, t, wall=(1, 0, 0)):
    """Flat strip along a polyline: thin boxes along each segment, the width kept horizontal (on steep
    segments: across the wall whose normal is `wall`)."""
    from build123d import Box, Plane, Vector
    wall = Vector(*wall)
    out = None
    for a, b in zip(pts, pts[1:]):
        a, b = Vector(*a), Vector(*b)
        d = b - a
        up = Vector(0, 0, 1) if abs(d.normalized().Z) < 0.9 else wall
        x_dir = d.cross(up).normalized()
        s = Plane(origin=(a + b) * 0.5, x_dir=x_dir, z_dir=d) * Box(w, t, d.length + 0.01)
        out = s if out is None else out + s
    return out


def pogo(x, y, z_board, tip_z, flange, barrel, plunger_d):
    """Spring pin standing on a board face at z_board, plunger tip at tip_z: flange (d, h), barrel (d, top above the
    board), plunger."""
    from build123d import Cylinder, Pos
    out = Pos(x, y, z_board + flange[1] / 2) * Cylinder(flange[0] / 2, flange[1])
    out += Pos(x, y, z_board + (flange[1] + barrel[1]) / 2) * Cylinder(barrel[0] / 2, barrel[1] - flange[1])
    zb = z_board + barrel[1]
    return out + Pos(x, y, (zb + tip_z) / 2) * Cylinder(plunger_d / 2, tip_z - zb)
