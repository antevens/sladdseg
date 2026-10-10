"""NA pocket-floor insert (D-35, D-41, D-49): printed floor on the insert's pocket floor for the battery-free
remote (replacement back cover), raising it by BC_FLOOR_T. Opening over the switch well. The sensor flex's tongue
comes down the pocket's top arc behind the trim's strip, runs under the floor (a channel in its underside), rises
through a slot onto the pad strip in its top recess (two gold pads flush under the back cover's fingers) and its
tail drops through a second slot; a notch from each slot to the edge lets the tongue in sideways. A tab with a
window at the arc snaps onto the strip's foot, so the floor insert lifts out with the face plate. Geometry in
backcover.py.
"""
from build123d import Pos
from params import *
import backcover


def cutouts():
    """Switch well, and the board-post bosses that rise into the pocket's corners."""
    out = [(0.0, SW_Y, WELL_IN[0], WELL_IN[1])]
    for (x, y), top in zip(MOUNT_HOLES, MOUNT_BOSS_TOP):
        if top > SEAT_Z and abs(x) < POCKET_IN[0] / 2 and abs(y) < POCKET_IN[1] / 2:
            out.append((x, y, MOUNT_BOSS_D, MOUNT_BOSS_D))
    return out


def tongue_path():
    """The tongue on the floor (x0, x1, y0, y1, layers, kind), copper up: under the floor from the wall (radially in,
    then the strip down), the slot, the pad strip on top under the fingers, the tail slot, the tail under."""
    p, u, q = tongue_arc()
    xd, wd, y_pad = BC_NA_DOWN
    xf = BC_FINGERS[0][0]
    hw = BC_NA_NECK_W / 2
    route = na_tongue_route()
    f = route[-2]
    y_bot = min(y for _, y in BC_FINGERS) - BC_FLOOR_PAD[1] / 2 - 1.0
    s = BC_NA_SLOT
    wall = (min(xd - hw, p[0] - 1.5), p[0] + 1.5, f[1] - hw, p[1] + 1.0, 1, "channel")   # drawn by the tongue
    down = (xd - hw, xd + hw, y_pad + s, f[1] + hw, 1, "channel")
    rise = (xd - hw, xd + hw, y_pad, y_pad + s, 1, "slot")
    pads = (xf - BC_TONGUE_W / 2, xf + BC_TONGUE_W / 2, y_bot, y_pad, 1, "top")
    drop = (xf - hw, xf + hw, y_bot - s, y_bot, 1, "slot")
    tail = (xf - hw, xf + hw, y_bot - s - BC_NA_TAIL, y_bot - s, 1, "under")
    return [wall, down, rise, pads, drop, tail]


def notches():
    """From each slot to the floor's right edge."""
    xd, wd, y_pad = BC_NA_DOWN
    xf = BC_FINGERS[0][0]
    hw = BC_NA_NECK_W / 2
    y_bot = min(y for _, y in BC_FINGERS) - BC_FLOOR_PAD[1] / 2 - 1.0
    s = BC_NA_SLOT
    return [(xd + hw + 0.1, POCKET_IN[0], y_pad, y_pad + s), (xf + hw + 0.1, POCKET_IN[0], y_bot - s, y_bot)]


def tab():
    """Tab at the arc in front of the trim strip's foot, with the window its hook snaps into (z: floor's underside 0)."""
    from build123d import Box
    from common import radial_prism
    p, u, q = tongue_arc()
    w, tt, h = BC_NA_FLOOR_TAB
    reach, hh, (w0, w1) = BC_NA_FOOT_HOOK
    r1 = -(BC_NA_STRIP[1] + BC_NA_TROOM + 0.05)
    r0 = r1 - tt
    out = radial_prism(p, u, [(r0, BC_FLOOR_T - 0.01), (r1, BC_FLOOR_T - 0.01), (r1, BC_FLOOR_T + h),
                              (r0, BC_FLOOR_T + h)], w)
    win = radial_prism(p, u, [(r0 - 0.5, BC_FLOOR_T + w0), (r1 + 0.5, BC_FLOOR_T + w0), (r1 + 0.5, BC_FLOOR_T + w1),
                              (r0 - 0.5, BC_FLOOR_T + w1)], BC_NA_STRIP[0] - 2.0 + 0.4)
    return out - win


def parts():
    p = backcover.floor_insert(POCKET_IN, POCKET_IN[0] / 2, cutouts(), tongue_path(), t=SFLEX_T, notches=notches())
    p["floor"] += tab()
    return {k: Pos(0, 0, SEAT_Z) * v for k, v in p.items()}
