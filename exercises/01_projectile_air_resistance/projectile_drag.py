import numpy as np
import matplotlib.pyplot as plt

g = 9.81


def derivatives(state, k):
    """state = [x, y, vx, vy]; k = Cd*rho*A/(2m), drag accel = -k*|v|*v."""
    x, y, vx, vy = state
    speed = np.hypot(vx, vy)
    return np.array([vx, vy, -k * speed * vx, -g - k * speed * vy])


def step(state, k, dt, method):
    if method == "euler_cromer":
        x, y, vx, vy = state
        speed = np.hypot(vx, vy)
        ax = -k * speed * vx
        ay = -g - k * speed * vy
        vx_new = vx + ax * dt
        vy_new = vy + ay * dt
        return np.array([x + vx_new * dt, y + vy_new * dt, vx_new, vy_new])
    elif method == "rk4":
        k1 = derivatives(state, k)
        k2 = derivatives(state + 0.5 * dt * k1, k)
        k3 = derivatives(state + 0.5 * dt * k2, k)
        k4 = derivatives(state + dt * k3, k)
        return state + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
    else:
        raise ValueError(f"unknown method: {method}")


def simulate(v0, angle_deg, k, dt=0.001, y0=0.0, method="euler_cromer"):
    """Integrate the trajectory. Returns arrays of t, x, y, vx, vy."""
    theta = np.radians(angle_deg)
    state = np.array([0.0, y0, v0 * np.cos(theta), v0 * np.sin(theta)])

    states = [state.copy()]
    t_list = [0.0]
    t = 0.0
    while state[1] >= 0.0:
        state = step(state, k, dt, method)
        t += dt
        states.append(state.copy())
        t_list.append(t)

    states = np.array(states)
    return np.array(t_list), states[:, 0], states[:, 1], states[:, 2], states[:, 3]


def compute_range(v0, angle_deg, k, dt, method="rk4", y0=0.0):
    """Landing range, linearly interpolated to the y=0 crossing (avoids O(dt)
    error from overshooting the ground on the last step)."""
    theta = np.radians(angle_deg)
    state = np.array([0.0, y0, v0 * np.cos(theta), v0 * np.sin(theta)])
    prev = state.copy()
    while state[1] >= 0.0:
        prev = state
        state = step(state, k, dt, method)

    frac = prev[1] / (prev[1] - state[1])
    return prev[0] + frac * (state[0] - prev[0])


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

    t, x, y, vx, vy = simulate(v0, angle, k, dt=0.01, method="euler_cromer")
    t_rk4, x_rk4, y_rk4, _, _ = simulate(v0, angle, k, dt=0.01, method="rk4")
    t0, x0, y0, _, _ = simulate(v0, angle, 0.0)

    print(f"Drag coefficient k = {k:.5f} 1/m")
    print(f"Range, Euler-Cromer (dt=0.01): {x[-1]:.3f} m")
    print(f"Range, RK4 (dt=0.01):          {x_rk4[-1]:.3f} m")
    print(f"Range without drag:            {x0[-1]:.2f} m (analytic: {range_no_drag(v0, angle):.2f} m)")

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.5))

    axes[0].plot(x0, y0, "--", label="no drag")
    axes[0].plot(x, y, label="Euler-Cromer")
    axes[0].plot(x_rk4, y_rk4, ":", label="RK4")
    axes[0].set_xlabel("x (m)")
    axes[0].set_ylabel("y (m)")
    axes[0].set_title(f"Trajectory, v0={v0} m/s, angle={angle}°, dt=0.01 s")
    axes[0].legend()
    axes[0].grid(alpha=0.3)

    # Convergence study: error in landing range vs step size, against a
    # fine-step RK4 reference solution.
    dt_ref = 1e-5
    ref_range = compute_range(v0, angle, k, dt_ref, method="rk4")

    dts = np.logspace(-3, -1, 7)
    err_ec = [abs(compute_range(v0, angle, k, dt, "euler_cromer") - ref_range) for dt in dts]
    err_rk4 = [abs(compute_range(v0, angle, k, dt, "rk4") - ref_range) for dt in dts]

    axes[1].loglog(dts, err_ec, "o-", label="Euler-Cromer")
    axes[1].loglog(dts, err_rk4, "s-", label="RK4")
    axes[1].loglog(dts, err_ec[0] * (dts / dts[0]) ** 1, "--", color="gray", lw=0.8, label="O(dt)")
    axes[1].loglog(dts, err_rk4[0] * (dts / dts[0]) ** 4, ":", color="gray", lw=0.8, label="O(dt⁴)")
    axes[1].set_xlabel("time step dt (s)")
    axes[1].set_ylabel("|range error| (m)")
    axes[1].set_title(f"Convergence (ref: RK4, dt={dt_ref:g} s)")
    axes[1].legend(fontsize=8)
    axes[1].grid(alpha=0.3, which="both")

    angles = np.linspace(10, 80, 60)
    ranges_drag = [compute_range(v0, a, k, 0.01, "rk4") for a in angles]
    ranges_ideal = [range_no_drag(v0, a) for a in angles]

    axes[2].plot(angles, ranges_ideal, "--", label="no drag")
    axes[2].plot(angles, ranges_drag, label="with drag (RK4)")
    best_drag = angles[np.argmax(ranges_drag)]
    axes[2].axvline(best_drag, color="gray", lw=0.8)
    axes[2].set_xlabel("launch angle (deg)")
    axes[2].set_ylabel("range (m)")
    axes[2].set_title(f"Optimal angle: {best_drag:.1f}° (drag) vs 45° (ideal)")
    axes[2].legend()
    axes[2].grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig("projectile_drag.png", dpi=150)
    print("Saved plot to projectile_drag.png")
