"""The two ridges over the EU pin board (D-129, D-131, D-133), drawn in plan with shapely and extruded:

- the barrier's ridge: down from the barrier's underside onto the pin board's front, a loop round its whole edge (inside
  the dome notches and the two sensor pins), ties the pin board's four bosses together; the board rests on it;
- the blank board's ridge (switch only): up from the blank board to BLANK_LEDGE[1] under the barrier, beside the
  barrier's ridge on its inner side, BLANK_GAP from it; it stiffens the blank board and closes the box under the barrier
  with the barrier's ridge.

Both are rounded in plan (no sharp corners or slivers: RIDGE_ROUND) and break, with round ends, where something passes:
the pins, the parts on the board, the bosses and the cups under the barrier.
"""
from math import atan2, cos, degrees, hypot, radians, sin, sqrt
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from common import prism as solid                          # noqa: F401  (ridges_eu.solid)
from params_eu import *


def _stadium_cup(grow):
    """The steel piece's cup under the barrier in plan (barrier_eu.magnet_outline(BARRIER_MIN)), grown by `grow`."""
    w = MAGNET[0] + 2 * (MAGNET_CLR + BARRIER_MIN)
    r = MAGNET_END_R + MAGNET_CLR + BARRIER_MIN
    y0 = MAGNET_REC_Y - MAGNET[1] / 2 - MAGNET_CLR - BARRIER_MIN
    y1 = MAGNET_REC_Y + MAGNET[1] / 2 + MAGNET_CLR + BARRIER_MIN
    return unary_union([Point(0, y0 + r).buffer(r, 64), box(-w / 2, y0 + r, w / 2, y1)]).buffer(grow, 32)


def board():
    """The pin board's outline (boards_eu.pin_board()) in plan, holes included."""
    b = Point(0, 0).buffer(PB_R, 256).intersection(box(-50, -50, 50, PB_CUT_Y))
    for x, y in DOMES:
        b = b.difference(Point(x, y).buffer(DOME_NOTCH_R, 64))
    for x, y in PB_MOUNT:
        b = b.difference(Point(x, y).buffer(PB_MOUNT_D / 2, 32))
    for x, y in MB_BOSS:
        if y < PB_CUT_Y:
            b = b.difference(Point(x, y).buffer(MB_BOSS_D / 2 + MB_BOSS_CLR, 64))
    return b


def _front_parts(grow):
    """Pins and parts on the pin board's front in plan, grown by `grow`."""
    import boards_eu
    out = [Point(x, y).buffer(PIN_FLANGE[0] / 2 + grow, 32) for x, y in tuple(PINS) + tuple(BC_FINGERS)]
    hx, hy = MB_HDR                                         # the socket J1's two pin tails on the front (on J3, D-133)
    out += [Point(hx, hy - i * 2.54).buffer(1.0 + grow, 32) for i in range(2)]
    for ref, (w, h, _) in FRONT_PARTS.items():
        x, y, rot = boards_eu._ep().PB_PARTS[ref]["pos"]
        bw, bh = (h, w) if rot in (90, 270) else (w, h)
        out.append(box(x - bw / 2, y - bh / 2, x + bw / 2, y + bh / 2).buffer(grow, 16))
    return unary_union(out)


def _smooth(poly):
    """Round convex corners (opening) and concave ones (closing) by RIDGE_ROUND; drop slivers."""
    r = RIDGE_ROUND
    return poly.buffer(r, 32).buffer(-2 * r, 32).buffer(r, 32)


def path():
    """Centre lines of the barrier's ridge (room x, y): a loop round the whole pin board, PB_RIDGE[0] in from its edges,
    smoothly inside the dome notches and inside the two sensor pins by the round edge (PB_RIDGE_PATH), and a spur out to
    each of the two bosses at the far edge (D-133)."""
    hw = BARRIER_MIN / 2
    rr_ = PB_R - PB_RIDGE[0] - hw
    ys = PB_CUT_Y - PB_RIDGE[0] - hw
    dclr = DOME_NOTCH_R + PB_RIDGE[0] + hw

    def inside_domes(p):
        for x, y in DOMES:                                # pushed in round a dome notch it would cross
            d = hypot(p[0] - x, p[1] - y)
            if d < dclr:
                return (x + (p[0] - x) * dclr / d, y + (p[1] - y) * dclr / d)
        return p

    xs = 30.0 - sqrt(dclr ** 2 - ys ** 2)                 # straight edge's ends, clear of the side domes
    (bx, by), (ox, oy) = PB_RIDGE_PATH
    a0 = degrees(atan2(oy, ox))                           # below the sensor pins, round the bottom to the left end
    a1 = 180.0 + degrees(atan2(-ys, sqrt(max(rr_ ** 2 - ys ** 2, 0.0))))
    n = 240
    arc = [inside_domes((rr_ * cos(radians(a0 - (a0 + 360 - a1) * i / n)), rr_ * sin(radians(a0 - (a0 + 360 - a1) * i / n))))
           for i in range(n + 1)]
    arc = [p for p in arc if p[1] <= ys]
    loop = [(-xs, ys), (bx, ys), (bx, by), (ox, oy)] + arc + [(-xs, ys)]
    spurs = []
    for x, y in PB_MOUNT[:2]:                             # the bosses at the far edge, out to the loop
        r = hypot(x, y)
        spurs.append([(x, y), (x * rr_ / r, y * rr_ / r)])
    return loop, spurs


def barrier_ridge():
    """The barrier's ridge in plan: BARRIER_MIN wide along path(), merged smoothly into the four bosses, inside the
    board's outline (PB_RIDGE[0] in), PB_RIDGE[1] clear of the parts on the front and of the long boss."""
    loop, spurs = path()
    line = unary_union([LineString(loop)] + [LineString(s) for s in spurs]).buffer(BARRIER_MIN / 2, 32)
    bosses = unary_union([Point(x, y).buffer(PB_BOSS_D / 2, 32) for x, y in PB_MOUNT])
    shape = _smooth(unary_union([line, bosses]))
    inside = Point(0, 0).buffer(PB_R, 256).intersection(box(-50, -50, 50, PB_CUT_Y))
    for x, y in DOMES:
        inside = inside.difference(Point(x, y).buffer(DOME_NOTCH_R, 64))
    shape = shape.intersection(inside.buffer(-PB_RIDGE[0], 32))
    keep_out = [_front_parts(PB_RIDGE[1])] + [Point(x, y).buffer(MB_BOSS_D / 2 + PB_RIDGE[1], 64) for x, y in MB_BOSS]
    shape = shape.difference(unary_union(keep_out))
    return _smooth(shape).union(bosses).buffer(0)


def blank_ridge():
    """The blank board's ridge in plan: a BARRIER_MIN ring just inside the barrier ridge's loop, BLANK_GAP from it and its
    bosses, clear of the cups and long bosses under the barrier, inside the board's outline."""
    loop, _ = path()
    inner = Polygon(loop).buffer(-(BARRIER_MIN / 2 + BLANK_GAP), 64)      # the barrier ridge's inner side, BLANK_GAP off
    shape = inner.difference(inner.buffer(-BARRIER_MIN, 64))
    cups = [_stadium_cup(BLANK_GAP), box(-CUP_OUT[0] / 2, SW_Y - CUP_OUT[1] / 2, CUP_OUT[0] / 2,
                                         SW_Y + CUP_OUT[1] / 2).buffer(BLANK_GAP, 16)]
    longs = [Point(x, y).buffer(MB_BOSS_D / 2 + BLANK_GAP, 64) for x, y in MB_BOSS]
    shape = shape.difference(unary_union([barrier_ridge().buffer(BLANK_GAP, 32)] + cups + longs))
    shape = shape.intersection(board().buffer(-PB_RIDGE[0], 32))
    shape = _smooth(shape).difference(barrier_ridge().buffer(BLANK_GAP, 32)).buffer(0)
    parts = [g for g in getattr(shape, "geoms", [shape]) if g.area >= RIDGE_MIN_AREA]   # no stubs
    return unary_union(parts)
