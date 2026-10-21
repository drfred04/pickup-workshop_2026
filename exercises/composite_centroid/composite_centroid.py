"""
Composite-area centroids of the parts defined in geometry_NN.json.

For each geometry file:
1. Checks the geometry: solid parts must not overlap, must form one connected
   piece, and every hole must lie entirely inside the solid (otherwise the
   composite table double-counts or subtracts area that is not there).
2. Builds the composite table: A_i, xbar_i, ybar_i, A_i*xbar_i, A_i*ybar_i.
3. Verifies the result independently by rasterizing the shape on a fine grid.
4. Draws the part twice: composite_object_NN.png (student version, no centroid)
   and composite_object_NN_solution.png (centroid marked).
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Polygon, Rectangle, Wedge
from scipy import ndimage

HERE = Path(__file__).parent
H = 0.05  # grid step for the raster check, mm


def part_properties(p):
    """Return (A, xbar, ybar) for one part; holes have negative area."""
    if p["type"] == "rectangle":
        A = p["width"] * p["height"]
        return A, p["x0"] + p["width"] / 2, p["y0"] + p["height"] / 2
    if p["type"] == "triangle":
        (x1, y1), (x2, y2), (x3, y3) = p["vertices"]
        A = 0.5 * abs((x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1))
        return A, (x1 + x2 + x3) / 3, (y1 + y2 + y3) / 3
    if p["type"] == "hole":
        return -np.pi * p["r"] ** 2, p["cx"], p["cy"]
    raise ValueError(p["type"])


def inside(p, X, Y):
    """Boolean mask of grid points inside part p."""
    if p["type"] == "rectangle":
        return (X >= p["x0"]) & (X <= p["x0"] + p["width"]) & \
               (Y >= p["y0"]) & (Y <= p["y0"] + p["height"])
    if p["type"] == "triangle":
        (x1, y1), (x2, y2), (x3, y3) = p["vertices"]
        d1 = (X - x2) * (y1 - y2) - (x1 - x2) * (Y - y2)
        d2 = (X - x3) * (y2 - y3) - (x2 - x3) * (Y - y3)
        d3 = (X - x1) * (y3 - y1) - (x3 - x1) * (Y - y1)
        neg = (d1 < 0) | (d2 < 0) | (d3 < 0)
        pos = (d1 > 0) | (d2 > 0) | (d3 > 0)
        return ~(neg & pos)
    if p["type"] == "hole":
        return (X - p["cx"]) ** 2 + (Y - p["cy"]) ** 2 <= p["r"] ** 2
    raise ValueError(p["type"])


def bounds(parts):
    """Integer bounding box (xmax, ymax) of the solid parts; parts start at the origin."""
    xmax = ymax = 0
    for p in parts:
        if p["type"] == "rectangle":
            xmax = max(xmax, p["x0"] + p["width"])
            ymax = max(ymax, p["y0"] + p["height"])
        elif p["type"] == "triangle":
            xmax = max(xmax, *(v[0] for v in p["vertices"]))
            ymax = max(ymax, *(v[1] for v in p["vertices"]))
    return xmax, ymax


def rasterize(parts):
    """Validate the geometry; return the grid (X, Y), the solid union and the part with holes."""
    xmax, ymax = bounds(parts)
    X, Y = np.meshgrid(np.arange(-5 + H / 2, xmax + 5, H),
                       np.arange(-5 + H / 2, ymax + 5, H))
    solids = [p for p in parts if p["type"] != "hole"]
    holes = [p for p in parts if p["type"] == "hole"]

    # Cell centers sit at half-step offsets, so shared edges are never hit twice.
    count = sum(inside(p, X, Y).astype(np.uint8) for p in solids)
    assert count.max() <= 1, "solid parts overlap"
    union = count == 1
    # 8-connectivity: a sharp triangle tip can rasterize to diagonal-only pixels.
    assert ndimage.label(union, structure=np.ones((3, 3)))[1] == 1, "solid parts are not one connected piece"
    material = union.copy()
    for hole in holes:
        mask = inside(hole, X, Y)
        assert union[mask].all(), f"{hole['id']} is not fully inside the solid"
        material &= ~mask
    return X, Y, union, material


def solve(path):
    geo = json.loads(path.read_text())
    parts = geo["parts"]
    tag = path.stem.split("_")[-1]

    rows = []
    for p in parts:
        A, xb, yb = part_properties(p)
        rows.append((p["id"], p["label"], A, xb, yb, A * xb, A * yb))

    A_tot = sum(r[2] for r in rows)
    Qy = sum(r[5] for r in rows)
    Qx = sum(r[6] for r in rows)
    X_bar, Y_bar = Qy / A_tot, Qx / A_tot

    print(f"[{tag}] {geo['name']}  (units: {geo['units']})\n")
    print(f"{'Part':<4} {'Description':<18} {'A':>10} {'xbar':>8} {'ybar':>8} "
          f"{'A*xbar':>12} {'A*ybar':>12}")
    for pid, label, A, xb, yb, Axb, Ayb in rows:
        print(f"{pid:<4} {label:<18} {A:10.1f} {xb:8.2f} {yb:8.2f} "
              f"{Axb:12.0f} {Ayb:12.0f}")
    print("-" * 78)
    print(f"{'Sum':<23} {A_tot:10.1f} {'':>17} {Qy:12.0f} {Qx:12.0f}\n")
    print(f"X = {X_bar:.2f} mm,  Y = {Y_bar:.2f} mm")

    X, Y, union, material = rasterize(parts)
    A_g = material.sum() * H * H
    X_g, Y_g = X[material].mean(), Y[material].mean()
    print(f"Grid check: A = {A_g:.1f}, X = {X_g:.2f}, Y = {Y_g:.2f}\n")
    assert abs(A_g - A_tot) / A_tot < 1e-3
    assert abs(X_g - X_bar) < 0.05 and abs(Y_g - Y_bar) < 0.05

    for show_centroid, suffix in ((False, ""), (True, "_solution")):
        draw(geo, X, Y, union, X_bar, Y_bar,
             f"composite_object_{tag}{suffix}.png", show_centroid)
    return tag, geo["name"], A_tot, X_bar, Y_bar


def draw(geo, X, Y, union, X_bar, Y_bar, filename, show_centroid):
    xmax, ymax = bounds(geo["parts"])
    fig, ax = plt.subplots(figsize=(8, 8 * (ymax + 25) / (xmax + 20) + 0.6))
    fill = dict(facecolor="#c9d6e3", edgecolor="none")
    for p in geo["parts"]:
        if p["type"] == "rectangle":
            ax.add_patch(Rectangle((p["x0"], p["y0"]), p["width"], p["height"], **fill))
        elif p["type"] == "triangle":
            ax.add_patch(Polygon(p["vertices"], **fill))
    # Outer boundary of the union, traced from the raster.
    ax.contour(X, Y, union.astype(float), levels=[0.5], colors="#1f2a36", linewidths=1.6)
    for p in geo["parts"]:
        if p["type"] == "hole":
            ax.add_patch(Circle((p["cx"], p["cy"]), p["r"], facecolor="white",
                                edgecolor="#1f2a36", lw=1.4))
            ax.plot([p["cx"] - p["r"] - 3, p["cx"] + p["r"] + 3], [p["cy"]] * 2,
                    color="#1f2a36", lw=0.6, ls="-.")
            ax.plot([p["cx"]] * 2, [p["cy"] - p["r"] - 3, p["cy"] + p["r"] + 3],
                    color="#1f2a36", lw=0.6, ls="-.")
            # Diameter callout along callout_deg (default 45, up-right), placed clear of edges.
            t = np.radians(p.get("callout_deg", 45))
            c, s = np.cos(t), np.sin(t)
            ax.annotate(f"⌀{2 * p['r']}", (p["cx"] + p["r"] * c, p["cy"] + p["r"] * s),
                        xytext=(p["cx"] + (p["r"] + 10) * c, p["cy"] + (p["r"] + 10) * s),
                        ha="left" if c > 0.3 else "right" if c < -0.3 else "center",
                        va="bottom" if s > 0.3 else "top" if s < -0.3 else "center",
                        fontsize=9, arrowprops=dict(arrowstyle="-", lw=0.6))

    if show_centroid:
        # Centroid symbol (quadrant-shaded circle).
        r = 3.5
        ax.add_patch(Circle((X_bar, Y_bar), r, facecolor="white", edgecolor="k", lw=1, zorder=5))
        for start in (0, 180):
            ax.add_patch(Wedge((X_bar, Y_bar), r, start, start + 90, facecolor="k", zorder=6))
        dx, dy = geo.get("centroid_label_offset", [8, 14])
        ax.annotate(f"C ({X_bar:.1f}, {Y_bar:.1f})", (X_bar, Y_bar),
                    xytext=(X_bar + dx, Y_bar + dy),
                    fontsize=9, arrowprops=dict(arrowstyle="-", lw=0.6))

    ax.set_xlim(-10, xmax + 10)
    ax.set_ylim(-10, ymax + 15)
    ax.set_aspect("equal")
    ax.set_xticks(range(0, xmax + 1, 10))
    ax.set_yticks(range(0, ymax + 11, 10))
    ax.grid(True, lw=0.3, alpha=0.5)
    ax.set_xlabel("x (mm)")
    ax.set_ylabel("y (mm)")
    ax.set_title(geo["name"])
    fig.tight_layout()
    fig.savefig(HERE / filename, dpi=200)
    plt.close(fig)


def main():
    results = [solve(path) for path in sorted(HERE.glob("geometry_*.json"))]
    print(f"{'#':<3} {'Part':<34} {'A (mm^2)':>10} {'X (mm)':>8} {'Y (mm)':>8}")
    for tag, name, A, xb, yb in results:
        print(f"{tag:<3} {name:<34} {A:10.1f} {xb:8.2f} {yb:8.2f}")


if __name__ == "__main__":
    main()
