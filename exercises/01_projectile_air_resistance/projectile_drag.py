import numpy as np
import matplotlib.pyplot as plt

g = 9.81


def simulate(v0, angle_deg, k, dt=0.001, y0=0.0):
    """Euler-Cromer integration of a projectile with quadratic drag.

    k = Cd * rho * A / (2 * m)  [1/m], drag acceleration = -k * |v| * v
    Returns arrays of t, x, y, vx, vy.
    """
    theta = np.radians(angle_deg)
    vx, vy = v0 * np.cos(theta), v0 * np.sin(theta)
    x, y = 0.0, y0

    t_list, x_list, y_list, vx_list, vy_list = [0.0], [x], [y], [vx], [vy]

    t = 0.0
    while y >= 0.0:
        speed = np.hypot(vx, vy)
        ax = -k * speed * vx
        ay = -g - k * speed * vy

        vx += ax * dt
        vy += ay * dt
        x += vx * dt
        y += vy * dt
        t += dt

        t_list.append(t)
        x_list.append(x)
        y_list.append(y)
        vx_list.append(vx)
        vy_list.append(vy)

    return (np.array(t_list), np.array(x_list), np.array(y_list),
            np.array(vx_list), np.array(vy_list))


def range_no_drag(v0, angle_deg):
    theta = np.radians(angle_deg)
    return v0 ** 2 * np.sin(2 * theta) / g


def drag_coefficient(mass, diameter, Cd=0.5, rho=1.225):
    A = np.pi * (diameter / 2) ** 2
    return Cd * rho * A / (2 * mass)


if __name__ == "__main__":
    # Baseball-like projectile
    mass, diameter = 0.145, 0.074
    k = drag_coefficient(mass, diameter)

    v0, angle = 40.0, 45.0

    t, x, y, vx, vy = simulate(v0, angle, k)
    t0, x0, y0, _, _ = simulate(v0, angle, 0.0)

    print(f"Drag coefficient k = {k:.5f} 1/m")
    print(f"Range with drag:    {x[-1]:.2f} m")
    print(f"Range without drag: {x0[-1]:.2f} m (analytic: {range_no_drag(v0, angle):.2f} m)")

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))

    axes[0].plot(x0, y0, "--", label="no drag")
    axes[0].plot(x, y, label="with drag")
    axes[0].set_xlabel("x (m)")
    axes[0].set_ylabel("y (m)")
    axes[0].set_title(f"Trajectory, v0={v0} m/s, angle={angle}°")
    axes[0].legend()
    axes[0].grid(alpha=0.3)

    angles = np.linspace(10, 80, 60)
    ranges_drag = [simulate(v0, a, k)[1][-1] for a in angles]
    ranges_ideal = [range_no_drag(v0, a) for a in angles]

    axes[1].plot(angles, ranges_ideal, "--", label="no drag")
    axes[1].plot(angles, ranges_drag, label="with drag")
    best_drag = angles[np.argmax(ranges_drag)]
    axes[1].axvline(best_drag, color="gray", lw=0.8)
    axes[1].set_xlabel("launch angle (deg)")
    axes[1].set_ylabel("range (m)")
    axes[1].set_title(f"Optimal angle: {best_drag:.1f}° (drag) vs 45° (ideal)")
    axes[1].legend()
    axes[1].grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig("projectile_drag.png", dpi=150)
    print("Saved plot to projectile_drag.png")
