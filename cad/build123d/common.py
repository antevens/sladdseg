"""Small geometry helpers shared by the printed parts."""
from build123d import (Matrix, Pos, Rot, RectangleRounded, Sphere, Cylinder, Plane,
                       extrude, loft, Sketch, Vector)


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


def board_hooks(cy, board_x, back_z, front_z, frame_in, hook, t=0.9, w=6.0, clr=0.2, relief=0.6):
    """Snap hooks at both short ends of a board held in a bay: a tab hangs from the face skin (front_z) at
    x = +-(board_x / 2 + clr), its lip `hook` deep catching the board's back face at back_z, a 45 deg lead-in
    below so the board snaps in from behind. Returns (hooks, reliefs): reliefs are cut from the bay frame
    behind each tab (frame_in = the frame's inner half width) so the tab can flex out past the lip."""
    from build123d import Box, Polyline, extrude, make_face
    hooks = reliefs = None
    xi = board_x / 2 + clr                              # tab's inner face
    zb = back_z - hook                                  # tab bottom
    pts = [(xi, front_z + 0.01), (xi + t, front_z + 0.01), (xi + t, zb), (xi - hook, back_z), (xi, back_z),
           (xi, front_z + 0.01)]
    prof = extrude(Plane.XZ * make_face(Polyline(*pts)), w / 2, both=True)   # profile x / z, along y
    for s in (1, -1):
        h = Pos(0, cy, 0) * (prof if s > 0 else prof.mirror(Plane.YZ))
        r = Pos(s * (frame_in + relief / 2 - 0.01), cy, (zb + front_z) / 2 - 0.5) * Box(relief + 0.02, w + 0.6,
                                                                                       front_z - zb - 1.0)
        hooks = h if hooks is None else hooks + h
        reliefs = r if reliefs is None else reliefs + r
    return hooks, reliefs



def bar(a, b, w, z0, z1, ext=0.0):
    """Box from plan point a to b (extended by ext at both ends), w wide, z0..z1."""
    from math import atan2, degrees, hypot
    from build123d import Box, Pos, Rot
    dx, dy = b[0] - a[0], b[1] - a[1]
    return Pos((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (z0 + z1) / 2) * Rot(0, 0, degrees(atan2(dy, dx))) * Box(
        hypot(dx, dy) + 2 * ext, w, z1 - z0)


def ramp_over(a, b, w, t, top, clr=0.1):
    """Solid from a sloped flex segment a -> b (3D points sharing x, or sharing y) up to the plane z = top: the
    flex (t thick, w wide strip) runs clr under its underside, room for a tape strip that holds it there."""
    from math import hypot
    from build123d import Plane, Polyline, extrude, make_face
    along_y = abs(a[0] - b[0]) < 1e-9
    i = 1 if along_y else 0
    du, dz = b[i] - a[i], b[2] - a[2]
    off = (t / 2 + clr) * hypot(du, dz) / abs(du)
    pts = [(a[i], a[2] + off), (b[i], b[2] + off), (b[i], top), (a[i], top), (a[i], a[2] + off)]
    plane = Plane.YZ if along_y else Plane.XZ
    prism = extrude(plane * make_face(Polyline(*pts)), w / 2, both=True)
    return Pos(a[0], 0, 0) * prism if along_y else Pos(0, a[1], 0) * prism


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
