"""Shaded 3D render helpers (pyvista) shared by the variant render scripts and the back cover renders."""
import tempfile
from pathlib import Path
import pyvista as pv
from build123d import export_stl

R = Path(__file__).resolve().parents[2] / "docs" / "renders"
COL = {"face_plate": "#f2f1ee", "barrier": "#8d949b", "remote": "#fbfaf6", "rocker": "#b23a32",
       "board": "#1f6b3a", "posts": "#d9822b", "flex": "#c98a1c", "tongue": "#c98a1c", "plug": "#222222", "sht45": "#5b2a86",
       "fingers": "#e3c565", "target": "#2f7a46", "jumper": "#d99a2b", "irm": "#2b2b2b", "wago": "#c9ccd1", "small": "#c8a03a",
       "msr": "#3a3a3a", "mic": "#2c5d8f", "floor": "#7d8a96", "floor_flex": "#d99a2b", "floor_pads": "#e3c565",
       "cover": "#e9e6df", "stiffener": "#2f7a46", "pads": "#e3c565", "contacts": "#c9a227", "regulator": "#2b2b2b",
       "steel": "#6d7075", "cflex": "#d99a2b", "front_half": "#fbfaf6", "pad_stiffener": "#2f7a46",
       "sensor_board": "#2f7a46", "keep": "#d9534f", "spacers": "#c9ccd1", "cn2": "#222222", "j1": "#e9e6df", "passives": "#8a6d3b",
       "esp": "#b9bcc0", "usb": "#c9ccd1", "radar": "#1d4f91", "cn1": "#222222", "co2": "#3f9a5a", "scd": "#55585c",
       "sw": "#e9e6df", "pin_board": "#2f7a46", "pins": "#c9a227", "pin_posts": "#b8860b", "sleeves": "#2b2b2b", "screws": "#9aa0a6", "pin_pads": "#c9a227"}


def mesh(part, d, name):
    f = Path(d) / f"{name}.stl"
    export_stl(part, str(f), tolerance=0.02, angular_tolerance=0.1)
    return pv.read(str(f))


def shot(name, ps, cam, size=(1400, 1100), hide=(), head=0.55, alpha=None, clip=()):
    """Render parts {key: part} to docs/renders/<name>.png; ps may be (parts, cut): with cut, the meshes of the
    `clip` keys are clipped at x 0 (parts given whole, such as board STEP models)."""
    ps, cut = ps if isinstance(ps, tuple) else (ps, False)
    with tempfile.TemporaryDirectory() as d:
        p = pv.Plotter(off_screen=True, window_size=size, lighting="none")
        p.set_background("white")
        p.add_light(pv.Light(light_type="headlight", intensity=head))
        p.add_light(pv.Light(position=(200, 300, 400), focal_point=(0, 0, 0), intensity=0.6, light_type="scene light"))
        p.add_light(pv.Light(position=(-300, -100, 200), focal_point=(0, 0, 0), intensity=0.25, light_type="scene light"))
        for k, v in ps.items():
            if k in hide or v is None:
                continue
            m = mesh(v, d, k)
            if cut and k in clip:
                m = m.clip(normal="x", origin=(0, 0, 0))
            p.add_mesh(m, color=COL[k], smooth_shading=True, split_sharp_edges=True,
                       specular=0.25, specular_power=20, opacity=(alpha or {}).get(k, 1.0))
        p.camera_position = cam
        p.enable_anti_aliasing("ssaa")
        p.screenshot(str(R / f"{name}.png"))
        p.close()
    print("wrote", R / f"{name}.png")
