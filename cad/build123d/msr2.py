"""APOLLO MSR-2 with the SCD40 CO2 add-on, out of its case: a part-level model for fit checks and renders.

Board frame (params.py): origin at the board's centre on its back face, x along the board (+x: the CN1 / CN2 end),
y across (+y: the radar's edge), z out of the front. Front: USB-C at the -x end, ESP32-C3-MINI-1 with its antenna over
a notch at the -y edge, the LD2410B radar along the +y edge on a 5-pin header at its +x end and a support at its -x
end, CN1 at the +x / -y corner with the CO2 add-on (SCD4x) on it. Back: CN2 at the +x end (its mated stack is drawn with the mate: sensor_board_na.py, sensor_board_eu.py), Boot / RST side-push
switches at the +y edge; two small plated holes on CN2's axis, one past each end.
Run:  python msr2.py  -> ../../build/msr2.step
"""
from build123d import Box, Cylinder, Location, Pos
from params import *

HX, HY = MSR_BOARD[0] / 2, MSR_BOARD[1] / 2


def _box(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def board():
    b = _box(-HX, HX, -HY, HY, 0, MSR_BOARD_T)
    ex = HX - MSR2_ESP_IN - MSR2_ESP[0] / 2                  # ESP centre x
    nw, nh = MSR2_NOTCH
    b -= _box(ex - nw / 2, ex + nw / 2, -HY - 1, -HY + nh, -1, MSR_BOARD_T + 1)
    d, dx = MSR2_HOLES
    for s in (-1, 1):                                       # the two holes either side of CN2
        b -= Pos(HX - MSR_CN2_IN + s * dx, 0, MSR_BOARD_T / 2) * Cylinder(d / 2, MSR_BOARD_T + 1)
    return b


def esp():
    x1 = HX - MSR2_ESP_IN
    z0 = MSR_BOARD_T
    return _box(x1 - MSR2_ESP[0], x1, -HY, -HY + MSR2_ESP[1], z0, z0 + MSR2_ESP[2])


def usb():
    w, d, h = MSR2_USB
    return _box(-HX, -HX + d, MSR2_USB_Y - w / 2, MSR2_USB_Y + w / 2, MSR_BOARD_T, MSR_BOARD_T + h)


def radar():
    lx, ly = MSR2_LD
    z0, z1 = MSR2_LD_BACK, MSR2_LD_BACK + MSR2_LD_T
    r = _box(HX - lx, HX, HY - ly, HY, z0, z1)
    r += _box(HX - lx + 8.0, HX - lx + 13.0, HY - ly / 2 - 2.5, HY - ly / 2 + 2.5, z1, z1 + MSR2_LD_PARTS)   # chip
    n, pitch, xin, tip = MSR2_LD_PINS
    for i in range(n):
        y = HY - ly / 2 + (i - (n - 1) / 2) * pitch
        r += Pos(HX - xin, y, (MSR_BOARD_T + z1 + tip) / 2) * Cylinder(0.32, z1 + tip - MSR_BOARD_T)
    r += _box(HX - xin - 0.6, HX - xin + 0.6, HY - ly / 2 - n * pitch / 2, HY - ly / 2 + n * pitch / 2,
              z0 - 1.5, z0)                                                 # header body under the radar
    pw, ph = MSR2_LD_PROP
    r += _box(HX - lx, HX - lx + pw, HY - ph, HY, MSR_BOARD_T, z0)             # support at the far end
    return r


def cn1():
    cx, cy = HX - MSR2_CN1_IN[0], -HY + MSR2_CN1_IN[1]
    return Pos(cx, cy, MSR_BOARD_T + MSR2_CN1_STACK / 2) * Box(B2B[0], B2B[1], MSR2_CN1_STACK)


def co2():
    """Add-on board on CN1."""
    cx, cy = HX - MSR2_CN1_IN[0], -HY + MSR2_CN1_IN[1]
    w, h, t = MSR2_CO2_BOARD
    return Pos(cx, cy, MSR_BOARD_T + MSR2_CN1_STACK + t / 2) * Box(w, h, t)


def scd():
    """SCD4x on the add-on board."""
    cx, cy = HX - MSR2_CN1_IN[0], -HY + MSR2_CN1_IN[1]
    sw, sh, st = MSR2_SCD
    return Pos(cx, cy, MSR_BOARD_T + MSR2_CN1_STACK + MSR2_CO2_BOARD[2] + st / 2) * Box(sw, sh, st)


def switches():
    w, d, h = MSR2_SW
    out = None
    for x in MSR2_SW_X:
        s = _box(x - w / 2, x + w / 2, HY - d, HY, -h, 0)
        out = s if out is None else out + s
    return out


def scd_centre():
    """SCD4x centre in the board frame."""
    return HX - MSR2_CN1_IN[0], -HY + MSR2_CN1_IN[1]


def vent_length():
    """Grille slot length: the SCD4x's side less the inset, shortened (symmetric about the light sensor) to stay
    VENT_RADAR_CLR off the radar module."""
    inset = MSR2_SCD_VENT[3]
    room = 2 * (HY - MSR2_LD[1] - VENT_RADAR_CLR - LUX_POS[1])
    return min(MSR2_SCD[1] - 2 * inset, room)


def scd_vents(x, y, top_z, wall):
    """Grille through the face skin (top_z, wall thick) of an MSR-2 centred at (x, y), room axes: slots along y, the
    middle one centred on the light sensor (LUX_POS), the rest beside it over the SCD4x (D-69)."""
    w, n, pitch, _ = MSR2_SCD_VENT
    cx, cy = x + LUX_POS[0], y + LUX_POS[1]
    length = vent_length()
    out = None
    for i in range(n):
        s = Pos(cx + (i - (n - 1) / 2) * pitch, cy, top_z - wall / 2) * Box(w, length, wall + 1)
        out = s if out is None else out + s
    return out


def posts(x, y, back_z, skin_z):
    """Face plate posts (D-66, D-67) from the skin's underside (skin_z) onto the board of an MSR-2 whose back centre
    is at (x, y, back_z), room axes."""
    z0, z1 = back_z + MSR_BOARD_T, skin_z + 0.01
    out = None
    for px, py in MSR2_POSTS:
        c = Pos(x + px, y + py, (z0 + z1) / 2) * Cylinder(MSR2_POST_D / 2, z1 - z0)
        out = c if out is None else out + c
    return out


def parts():
    return {"board": board(), "esp": esp(), "usb": usb(), "radar": radar(), "cn1": cn1(), "co2": co2(), "scd": scd(),
            "sw": switches()}


def model():
    out = None
    for v in parts().values():
        out = v if out is None else out + v
    return out


def placed(x, y, back_z):
    """The model with its board's back centre at (x, y, back_z), room axes."""
    return Location((x, y, back_z)) * model()


def placed_parts(x, y, back_z):
    return {k: Location((x, y, back_z)) * v for k, v in parts().items()}


if __name__ == "__main__":
    from pathlib import Path
    from build123d import export_step
    out = Path(__file__).resolve().parents[2] / "build"
    out.mkdir(exist_ok=True)
    for k, v in parts().items():
        bb = v.bounding_box()
        print(f"{k:6s} z {bb.min.Z:6.2f} .. {bb.max.Z:6.2f}  valid {v.is_valid}")
    m = model()
    bb = m.bounding_box()
    print("model", [round(c, 2) for c in (bb.size.X, bb.size.Y, bb.size.Z)], "front", round(bb.max.Z, 2),
          "case face", MSR2_CASE[2])
    export_step(m, str(out / "msr2.step"))
