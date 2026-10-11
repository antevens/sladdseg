"""Section renders of STL parts for review: python sections.py out.png part.stl[:color[|label]] ... --cut AXIS=VALUE ...

Each --cut makes one panel; all parts are sliced on that plane and filled.
--cut AXIS=VALUE@U0,U1,V0,V1 limits that panel to a window (zoom); --cut AXIS=VALUE#TEXT titles the panel;
--dpi N sets the output resolution. Parts with a label go into one legend for the sheet.
"""
import sys
import textwrap
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, PathPatch
from matplotlib.path import Path as MPath
from shapely.geometry import Polygon

AX = {"x": (0, (1, 2), ("y", "z")), "y": (1, (0, 2), ("x", "z")), "z": (2, (0, 1), ("x", "y"))}


def main(argv):
    out = argv[0]
    parts, cuts, title, dpi = [], [], "", 80
    i = 1
    while i < len(argv):
        a = argv[i]
        if a == "--cut":
            cuts.append(argv[i + 1]); i += 2; continue
        if a == "--title":
            title = argv[i + 1]; i += 2; continue
        if a == "--dpi":
            dpi = int(argv[i + 1]); i += 2; continue
        path, _, col = a.partition(":")
        col, _, label = col.partition("|")
        parts.append((trimesh.load(path), col or "tab:blue", label))
        i += 1
    n = len(cuts)
    cols = min(n, 3)
    rows = (n + cols - 1) // cols
    fig, axs = plt.subplots(rows, cols, figsize=(6.5 * cols, 6.5 * rows), squeeze=False)
    for k, c in enumerate(cuts):
        ax = axs[k // cols][k % cols]
        c, _, text = c.partition("#")
        c, _, win = c.partition("@")
        axis, val = c.split("=")
        ai, (u, v), (lu, lv) = AX[axis]
        normal = np.zeros(3); normal[ai] = 1
        origin = np.zeros(3); origin[ai] = float(val)
        for mesh, col, _ in parts:
            sec = mesh.section(plane_origin=origin, plane_normal=normal)
            if sec is None:
                continue
            region = None
            for loop in sec.discrete:
                if len(loop) < 4:
                    continue
                ring = Polygon(loop[:, [u, v]]).buffer(0)
                region = ring if region is None else region.symmetric_difference(ring)
            if region is None or region.is_empty:
                continue
            for poly in getattr(region, "geoms", [region]):
                if poly.geom_type != "Polygon":
                    continue
                verts, codes = [], []
                for r in [poly.exterior] + list(poly.interiors):
                    xy = np.asarray(r.coords)
                    verts += xy.tolist(); codes += [MPath.MOVETO] + [MPath.LINETO] * (len(xy) - 2) + [MPath.CLOSEPOLY]
                ax.add_patch(PathPatch(MPath(verts, codes), fc=col, ec="k", lw=0.4, alpha=0.75))
        ax.set_title(f"{axis} = {val}" + (f": {text}" if text else ""), fontsize=10)
        ax.set_xlabel(lu); ax.set_ylabel(lv)
        ax.set_aspect("equal"); ax.autoscale_view(); ax.grid(alpha=0.3)
        if win:
            u0, u1, v0, v1 = (float(t) for t in win.split(","))
            ax.set_xlim(u0, u1); ax.set_ylim(v0, v1)
        if axis != "z":
            ax.axhline(0, color="r", lw=0.8, ls="--")  # wall surface
    for k in range(n, rows * cols):
        axs[k // cols][k % cols].axis("off")
    legend = [Patch(fc=col, ec="k", alpha=0.75, label=label) for _, col, label in parts if label]
    if legend:
        per_row = max(2, 2 * cols)
        fig.legend(handles=legend, loc="lower center", ncol=min(len(legend), per_row), fontsize=9, frameon=False)
    rows_legend = (len(legend) + max(2, 2 * cols) - 1) // max(2, 2 * cols) if legend else 0
    fig.suptitle(textwrap.fill(title, 75 * cols), fontsize=11)
    fig.tight_layout(rect=(0, 0.06 * rows_legend / rows, 1, 1 - 0.02 / rows))
    fig.savefig(out, dpi=dpi)


if __name__ == "__main__":
    main(sys.argv[1:])
