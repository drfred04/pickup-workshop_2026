"""
Normal-incidence acoustic impedance and absorption of rigid-frame porous
absorbers, via three models: Johnson-Champoux-Allard (JCA), the exact
Zwikker-Kosten circular-pore solution, and the Delany-Bazley-Miki
empirical fit.

References
----------
Johnson-Champoux-Allard (JCA) equivalent-fluid model:
    D. L. Johnson, J. Koplik, and R. Dashen, "Theory of dynamic
    permeability and tortuosity in fluid-saturated porous media,"
    J. Fluid Mech. 176, 379-402 (1987).
    Y. Champoux and J.-F. Allard, "Dynamic tortuosity and bulk modulus
    in air-saturated porous media," J. Appl. Phys. 70(4), 1975-1979
    (1991).

Zwikker-Kosten exact circular-pore solution:
    C. Zwikker and C. W. Kosten, Sound Absorbing Materials, Elsevier
    (1949).

Delany-Bazley-Miki empirical model:
    M. E. Delany and E. N. Bazley, "Acoustical properties of fibrous
    absorbent materials," Appl. Acoust. 3(2), 105-116 (1970).
    Y. Miki, "Acoustical properties of porous materials - Modifications
    of Delany-Bazley models," J. Acoust. Soc. Jpn. (E) 11(1), 19-24
    (1990).

General reference tying the above together:
    J. F. Allard and N. Atalla, Propagation of Sound in Porous Media:
    Modelling Sound Absorbing Materials, 2nd ed., Wiley (2009).

Flow resistivity measurement standard:
    ISO 9053-1:2018, Acoustics - Determination of airflow resistance -
    Part 1: Static airflow method.
"""
import numpy as np
import matplotlib.pyplot as plt
from scipy.special import jv

# Ambient air properties (20 C, 101.325 kPa)
rho0 = 1.213       # kg/m^3
P0 = 101325.0      # Pa
gamma = 1.4
Pr = 0.71
eta = 1.839e-5     # Pa s, dynamic viscosity
c0 = np.sqrt(gamma * P0 / rho0)


def jca_impedance(f, phi, alpha_inf, sigma, Lambda, Lambda_p):
    """
    Johnson-Champoux-Allard rigid-frame equivalent-fluid model.
    phi = porosity, alpha_inf = tortuosity, sigma = flow resistivity (Pa s/m^2),
    Lambda, Lambda_p = viscous/thermal characteristic lengths (m).
    Returns complex characteristic impedance Zc and wavenumber k.
    """
    omega = 2 * np.pi * f
    Gj = np.sqrt(1 + 1j * (4 * alpha_inf ** 2 * eta * rho0 * omega) / (sigma ** 2 * Lambda ** 2 * phi ** 2))
    rho_eff = (alpha_inf * rho0 / phi) * (1 + (sigma * phi) / (1j * omega * rho0 * alpha_inf) * Gj)

    Gjp = np.sqrt(1 + 1j * (rho0 * omega * Pr * Lambda_p ** 2) / (16 * eta))
    K_eff = (gamma * P0 / phi) / (gamma - (gamma - 1) * (1 - 1j * (8 * eta) / (rho0 * omega * Pr * Lambda_p ** 2) * Gjp) ** -1)

    Zc = np.sqrt(rho_eff * K_eff)
    k = omega * np.sqrt(rho_eff / K_eff)
    return Zc, k


def zwikker_kosten_impedance(f, phi, a):
    """
    Zwikker & Kosten (1949) exact solution for a bundle of straight,
    parallel circular capillary pores of radius a, porosity phi.

    Unlike JCA (a smooth rational interpolation between the correct low-
    and high-frequency asymptotes), this solves the oscillatory Poiseuille
    (Womersley) flow and heat-conduction problem in the pore exactly via
    Bessel functions, so it is exact at every frequency for this one
    idealized geometry -- but only for this geometry. It's the benchmark
    JCA's circular-pore limit was built to approximate.
    Returns complex characteristic impedance Zc and wavenumber k.
    """
    omega = 2 * np.pi * f

    def G(x):
        # 1 - (2/x) J1(x)/J0(x): ratio of mean to peak oscillatory
        # (Poiseuille/Womersley) flow through a circular tube.
        return 1 - (2 / x) * jv(1, x) / jv(0, x)

    kv = np.sqrt(-1j * omega * rho0 / eta)
    rho_eff = rho0 / (phi * G(kv * a))

    kt = np.sqrt(-1j * omega * rho0 * Pr / eta)
    K_eff = (gamma * P0 / phi) / (gamma - (gamma - 1) * G(kt * a))

    Zc = np.sqrt(rho_eff * K_eff)
    k = omega * np.sqrt(rho_eff / K_eff)
    return Zc, k


def delany_bazley_miki_impedance(f, sigma):
    """
    Miki's (1990) revision of the Delany-Bazley empirical model.
    Fit to flow resistivity alone; nominally valid for 0.01 < X < 1,
    X = rho0*f/sigma. Ignores porosity and tortuosity entirely.
    """
    X = rho0 * f / sigma
    Zc = rho0 * c0 * (1 + 0.070 * X ** -0.632 - 1j * 0.107 * X ** -0.632)
    k = (2 * np.pi * f / c0) * (1 + 0.109 * X ** -0.618 - 1j * 0.160 * X ** -0.618)
    return Zc, k


def circular_pore_parameters(r, phi):
    """
    JCA microstructure parameters for a bundle of straight, parallel
    circular pores of radius r (Johnson, Koplik & Dashen 1987): the pores
    are unobstructed, so tortuosity is exactly 1, and both characteristic
    lengths reduce to the pore radius. Flow resistivity follows from
    Poiseuille flow through the pores.
    """
    alpha_inf = 1.0
    Lambda = r
    Lambda_p = r
    sigma = 8 * eta / (phi * r ** 2)
    return alpha_inf, sigma, Lambda, Lambda_p


def slit_pore_parameters(h, phi):
    """
    JCA microstructure parameters for a bundle of straight, parallel
    slit-like pores (two parallel plates separated by a full gap 2h,
    h = half-width). Poiseuille flow between plates gives a resistivity
    factor of 3 rather than the circular tube's factor of 8; tortuosity
    is again exactly 1 and both characteristic lengths equal h.
    """
    alpha_inf = 1.0
    Lambda = h
    Lambda_p = h
    sigma = 3 * eta / (phi * h ** 2)
    return alpha_inf, sigma, Lambda, Lambda_p


# Poiseuille shape factor c1 relating flow resistivity to the pore's
# characteristic size for straight pores of a given cross-section:
#   sigma = c1 * eta * alpha_inf / (phi * Lambda**2)
# For these idealized straight-pore shapes Lambda' = Lambda, so the same
# factor sets both the viscous and thermal characteristic lengths. This
# lets Lambda be *estimated* from bulk, independently measurable material
# properties (porosity, tortuosity, flow resistivity) plus an assumed pore
# cross-section, when Lambda itself hasn't been measured directly -- the
# same convention used e.g. by COMSOL's "circular / slit-like" JCA pore
# shape presets.
SHAPE_FACTORS = {
    "circular": 8.0,
    "slit": 3.0,
}


def shape_characteristic_length(phi, alpha_inf, sigma, shape="circular"):
    """
    Estimate Lambda (= Lambda_p) from measured bulk parameters plus an
    assumed idealized pore shape, by inverting sigma = c1*eta*alpha_inf /
    (phi*Lambda**2). shape must be a key of SHAPE_FACTORS.
    """
    c1 = SHAPE_FACTORS[shape]
    Lambda = np.sqrt(c1 * eta * alpha_inf / (phi * sigma))
    return Lambda, Lambda


def jca_impedance_from_bulk(f, phi, alpha_inf, sigma, shape="circular"):
    """
    JCA characteristic impedance/wavenumber from only the four bulk
    parameters that are normally reported for a real material -- porosity,
    tortuosity, flow resistivity, and an assumed pore shape -- without
    requiring separately measured characteristic lengths.
    """
    Lambda, Lambda_p = shape_characteristic_length(phi, alpha_inf, sigma, shape)
    return jca_impedance(f, phi, alpha_inf, sigma, Lambda, Lambda_p)


def surface_impedance(Zc, k, L):
    """Normal-incidence impedance of a rigid-backed layer of thickness L."""
    return -1j * Zc / np.tan(k * L)


def absorption_coefficient(Zs):
    """Normal-incidence absorption coefficient at the front face."""
    R = (Zs - rho0 * c0) / (Zs + rho0 * c0)
    return 1 - np.abs(R) ** 2


if __name__ == "__main__":
    # Material defined by the four parameters that are normally reported
    # for a real porous material, rather than by an idealized pore radius:
    phi = 0.95           # porosity (open pore volume fraction)
    alpha_inf = 1.1        # tortuosity (high-frequency limit)
    R_f = 750.0            # flow resistance of the sample, Pa s/m (ISO 9053)
    L = 0.03               # thickness, m

    # Flow resistance R_f is a property of this specific L-thick sample;
    # flow resistivity sigma = R_f / L is the intrinsic material property
    # the wave-propagation model actually needs.
    sigma = R_f / L

    shapes = ["circular", "slit"]

    f = np.logspace(np.log10(20), np.log10(10000), 500)

    results = {}
    for shape in shapes:
        Lambda, Lambda_p = shape_characteristic_length(phi, alpha_inf, sigma, shape)
        Zc, k = jca_impedance(f, phi, alpha_inf, sigma, Lambda, Lambda_p)
        Zs = surface_impedance(Zc, k, L)
        alpha = absorption_coefficient(Zs)
        results[shape] = dict(Lambda=Lambda, Zc=Zc, k=k, Zs=Zs, alpha=alpha)

    Zc_db, k_db = delany_bazley_miki_impedance(f, sigma)
    Zs_db = surface_impedance(Zc_db, k_db, L)
    alpha_db = absorption_coefficient(Zs_db)

    # Exact circular-pore benchmark. Zwikker-Kosten has no tortuosity
    # parameter -- a genuine straight circular pore has alpha_inf=1 exactly
    # -- so the fair, apples-to-apples comparison against JCA's circular
    # shape estimate uses alpha_inf=1 on both sides, at the pore radius
    # that reproduces the same measured flow resistivity sigma. This
    # isolates the error of JCA's rational-function approximation from
    # the (physically separate) effect of the material's real tortuosity.
    a_zk, _ = shape_characteristic_length(phi, 1.0, sigma, "circular")
    Zc_jca1, k_jca1 = jca_impedance(f, phi, 1.0, sigma, a_zk, a_zk)
    Zs_jca1 = surface_impedance(Zc_jca1, k_jca1, L)
    alpha_jca1 = absorption_coefficient(Zs_jca1)

    Zc_zk, k_zk = zwikker_kosten_impedance(f, phi, a_zk)
    Zs_zk = surface_impedance(Zc_zk, k_zk, L)
    alpha_zk = absorption_coefficient(Zs_zk)

    # Miki fit's nominal validity range, X = rho0*f/sigma in [0.01, 1]
    f_lo, f_hi = 0.01 * sigma / rho0, 1.0 * sigma / rho0

    f_probe = 1000.0
    i_probe = np.argmin(np.abs(f - f_probe))
    print(f"phi={phi}, alpha_inf={alpha_inf}, R_f={R_f:.0f} Pa s/m, L={L*100:.1f} cm")
    print(f"-> sigma = R_f/L = {sigma:.0f} Pa s/m^2")
    for shape in shapes:
        Lambda = results[shape]["Lambda"]
        alpha = results[shape]["alpha"][i_probe]
        print(f"  {shape:9s} pores: Lambda=Lambda_p={Lambda*1e6:.0f} um, "
              f"alpha_JCA({f[i_probe]:.0f} Hz)={alpha:.3f}")
    print(f"  straight circular pore matching sigma: a={a_zk*1e6:.0f} um (alpha_inf=1)")
    print(f"  alpha_JCA-circular(alpha_inf=1, {f[i_probe]:.0f} Hz)={alpha_jca1[i_probe]:.3f}, "
          f"alpha_Zwikker-Kosten(exact, {f[i_probe]:.0f} Hz)={alpha_zk[i_probe]:.3f}")
    err_zc = np.abs(Zc_jca1 - Zc_zk) / np.abs(Zc_zk)
    print(f"  JCA-circular vs exact: |Zc| rel. error {err_zc.min()*100:.2f}-{err_zc.max()*100:.2f}% over {f[0]:.0f}-{f[-1]:.0f} Hz")
    print(f"Miki fit nominally valid for {f_lo:.0f} Hz < f < {f_hi:.0f} Hz")
    print(f"At {f[i_probe]:.0f} Hz: alpha_DB-Miki={alpha_db[i_probe]:.3f}")

    colors = {"circular": "C0", "slit": "C1"}

    fig, axes = plt.subplots(2, 3, figsize=(17, 9))

    for shape in shapes:
        Zc = results[shape]["Zc"]
        axes[0, 0].semilogx(f, Zc.real / (rho0 * c0), color=colors[shape], label=f"JCA {shape}, Re")
        axes[0, 0].semilogx(f, Zc.imag / (rho0 * c0), "--", color=colors[shape], label=f"JCA {shape}, Im")
    axes[0, 0].semilogx(f, Zc_zk.real / (rho0 * c0), color="C2", label="Z-K exact, Re")
    axes[0, 0].semilogx(f, Zc_zk.imag / (rho0 * c0), "C2--", label="Z-K exact, Im")
    axes[0, 0].semilogx(f, Zc_db.real / (rho0 * c0), color="k", label="DB-Miki, Re")
    axes[0, 0].semilogx(f, Zc_db.imag / (rho0 * c0), "k--", label="DB-Miki, Im")
    axes[0, 0].set_xlabel("frequency (Hz)")
    axes[0, 0].set_ylabel("Zc / (rho0 c0)")
    axes[0, 0].set_title("Characteristic impedance")
    axes[0, 0].legend(fontsize=7)
    axes[0, 0].grid(alpha=0.3, which="both")

    for shape in shapes:
        Zs = results[shape]["Zs"]
        axes[0, 1].semilogx(f, Zs.real / (rho0 * c0), color=colors[shape], label=f"JCA {shape}, Re")
        axes[0, 1].semilogx(f, Zs.imag / (rho0 * c0), "--", color=colors[shape], label=f"JCA {shape}, Im")
    axes[0, 1].semilogx(f, Zs_zk.real / (rho0 * c0), color="C2", label="Z-K exact, Re")
    axes[0, 1].semilogx(f, Zs_zk.imag / (rho0 * c0), "C2--", label="Z-K exact, Im")
    axes[0, 1].semilogx(f, Zs_db.real / (rho0 * c0), color="k", label="DB-Miki, Re")
    axes[0, 1].semilogx(f, Zs_db.imag / (rho0 * c0), "k--", label="DB-Miki, Im")
    axes[0, 1].set_xlabel("frequency (Hz)")
    axes[0, 1].set_ylabel("Zs / (rho0 c0)")
    axes[0, 1].set_title(f"Surface impedance, L={L*100:.0f} cm rigid-backed")
    axes[0, 1].legend(fontsize=7)
    axes[0, 1].grid(alpha=0.3, which="both")

    for shape in shapes:
        axes[0, 2].semilogx(f, results[shape]["alpha"], color=colors[shape], label=f"JCA, {shape} pores")
    axes[0, 2].semilogx(f, alpha_zk, color="C2", label="Z-K exact, circular")
    axes[0, 2].semilogx(f, alpha_db, color="k", label="DB-Miki")
    axes[0, 2].axvspan(f_lo, f_hi, color="gray", alpha=0.15, label="DB-Miki nominal fit range")
    axes[0, 2].set_xlabel("frequency (Hz)")
    axes[0, 2].set_ylabel("absorption coefficient")
    axes[0, 2].set_title("Normal-incidence absorption")
    axes[0, 2].set_ylim(0, 1.05)
    axes[0, 2].legend(fontsize=7)
    axes[0, 2].grid(alpha=0.3, which="both")

    axes[1, 0].semilogx(f, alpha_jca1 - alpha_zk, color="C3")
    axes[1, 0].axhline(0, color="gray", lw=0.8)
    axes[1, 0].set_xlabel("frequency (Hz)")
    axes[1, 0].set_ylabel("alpha_JCA-circular - alpha_Z-K-exact")
    axes[1, 0].set_title("JCA approximation error, pure\n(both alpha_inf=1, same a; isolates model form)")
    axes[1, 0].grid(alpha=0.3, which="both")

    axes[1, 1].semilogx(f, results["circular"]["alpha"] - results["slit"]["alpha"], color="C2")
    axes[1, 1].axhline(0, color="gray", lw=0.8)
    axes[1, 1].set_xlabel("frequency (Hz)")
    axes[1, 1].set_ylabel("alpha_circular - alpha_slit")
    axes[1, 1].set_title("Pore-shape sensitivity\n(JCA, same phi, alpha_inf, sigma, L)")
    axes[1, 1].grid(alpha=0.3, which="both")

    axes[1, 2].loglog(f, np.abs(Zc_jca1 - Zc_zk) / np.abs(Zc_zk), label="|Zc| rel. error")
    axes[1, 2].loglog(f, np.abs(k_jca1 - k_zk) / np.abs(k_zk), label="|k| rel. error")
    axes[1, 2].set_xlabel("frequency (Hz)")
    axes[1, 2].set_ylabel("relative error")
    axes[1, 2].set_title("JCA vs. exact Zwikker-Kosten\n(circular pores, a=%.0f um, alpha_inf=1)" % (a_zk * 1e6))
    axes[1, 2].legend(fontsize=8)
    axes[1, 2].grid(alpha=0.3, which="both")

    fig.tight_layout()
    fig.savefig("porous_impedance.png", dpi=150)
    print("Saved plot to porous_impedance.png")
