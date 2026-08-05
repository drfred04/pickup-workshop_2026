"""
Same porous-material impedance/absorption models as porous_impedance.py,
driven by an external input file instead of hardcoded parameters. The
input file and the output plot's location/name are both chosen through
native system dialog boxes rather than the command line.

Usage:
    python3 porous_impedance_2.py

See porous_input.txt for the expected key = value input file format.
"""
import os
import platform
import subprocess
import sys

import numpy as np
import matplotlib.pyplot as plt

from porous_impedance import (
    rho0, c0,
    jca_impedance_from_bulk,
    zwikker_kosten_impedance,
    delany_bazley_miki_impedance,
    shape_characteristic_length,
    surface_impedance,
    absorption_coefficient,
)

REQUIRED_FLOAT_KEYS = ["porosity", "tortuosity", "flow_resistance", "thickness", "freq_min", "freq_max"]
MODEL_CHOICES = ["jca_circular", "jca_slit", "zwikker_kosten", "delany_bazley_miki", "all"]


def _open_dialog_tkinter(title):
    """Try Tk's native open-file dialog. Returns (path_or_None, available)."""
    try:
        import tkinter
        from tkinter import filedialog
    except ImportError:
        return None, False
    root = tkinter.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    path = filedialog.askopenfilename(
        title=title,
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
    )
    root.destroy()
    return (path or None), True


def _save_dialog_tkinter(title, default_name):
    """Try Tk's native save-file dialog. Returns (path_or_None, available)."""
    try:
        import tkinter
        from tkinter import filedialog
    except ImportError:
        return None, False
    root = tkinter.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    path = filedialog.asksaveasfilename(
        title=title,
        defaultextension=".png",
        initialfile=default_name,
        filetypes=[("PNG image", "*.png"), ("All files", "*.*")],
    )
    root.destroy()
    return (path or None), True


def _open_dialog_osascript(title):
    """macOS 'choose file' dialog via AppleScript, restricted to .txt files."""
    script = f'POSIX path of (choose file with prompt "{title}" of type {{"txt"}})'
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _save_dialog_osascript(title, default_name):
    """macOS 'choose file name' dialog via AppleScript, for picking a save location/name."""
    safe_name = default_name.replace('"', "'")
    script = f'POSIX path of (choose file name with prompt "{title}" default name "{safe_name}")'
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def ask_for_input_file():
    """Pop a native 'open file' dialog and return the chosen .txt path."""
    path, available = _open_dialog_tkinter("Select the porous material input file (.txt)")
    if not available and platform.system() == "Darwin":
        path = _open_dialog_osascript("Select the porous material input file")
        available = True
    if not available:
        sys.exit(
            "error: no GUI file dialog is available on this system (tkinter is not "
            "installed and this isn't macOS). Install tkinter, e.g. "
            "'brew install python-tk', and try again."
        )
    if not path:
        sys.exit("No input file selected -- exiting.")
    return os.path.abspath(path)


def ask_for_output_file(default_name):
    """Pop a native 'save file' dialog and return the chosen output path."""
    path, available = _save_dialog_tkinter("Save impedance/absorption plot as...", default_name)
    if not available and platform.system() == "Darwin":
        path = _save_dialog_osascript("Save impedance/absorption plot as", default_name)
        available = True
    if not available:
        sys.exit(
            "error: no GUI file dialog is available on this system (tkinter is not "
            "installed and this isn't macOS). Install tkinter, e.g. "
            "'brew install python-tk', and try again."
        )
    if not path:
        sys.exit("No output location chosen -- exiting.")
    return path


def parse_input_file(path):
    """Read 'key = value' pairs, ignoring blank lines and '#' comments."""
    params = {}
    with open(path, "r") as fh:
        for line_no, raw_line in enumerate(fh, start=1):
            line = raw_line.split("#", 1)[0].strip()
            if not line:
                continue
            if "=" not in line:
                sys.exit(f"error: {path}:{line_no}: expected 'key = value', got: {raw_line.rstrip()!r}")
            key, value = line.split("=", 1)
            params[key.strip().lower()] = value.strip()
    return params


def validate_and_convert(params, input_path):
    missing = [k for k in REQUIRED_FLOAT_KEYS + ["model"] if k not in params]
    if missing:
        sys.exit(f"error: {input_path}: missing required parameter(s): {', '.join(missing)}")

    cfg = {}
    for key in REQUIRED_FLOAT_KEYS:
        try:
            cfg[key] = float(params[key])
        except ValueError:
            sys.exit(f"error: {input_path}: '{key}' must be a number, got {params[key]!r}")

    try:
        cfg["n_points"] = int(params.get("n_points", 500))
    except ValueError:
        sys.exit(f"error: {input_path}: 'n_points' must be an integer, got {params['n_points']!r}")

    # model accepts a single name, "all", or a "|"/","-separated subset,
    # e.g. "jca_circular | zwikker_kosten"
    raw_model = params["model"].strip()
    parts = [p.strip().lower() for p in raw_model.replace(",", "|").split("|") if p.strip()]
    if not parts:
        sys.exit(f"error: {input_path}: 'model' must not be empty")
    if "all" in parts:
        model_names = MODEL_CHOICES[:-1]
    else:
        invalid = [p for p in parts if p not in MODEL_CHOICES[:-1]]
        if invalid:
            sys.exit(f"error: {input_path}: unknown model(s) {invalid}; choose from {MODEL_CHOICES}")
        model_names = list(dict.fromkeys(parts))  # de-duplicate, preserve order
    cfg["model"] = raw_model
    cfg["model_names"] = model_names

    return cfg


def run_model(name, f, phi, alpha_inf, sigma, L):
    """Compute Zc, k, Zs, alpha for one named model; returns (result_dict, notes)."""
    notes = []
    if name == "jca_circular":
        Zc, k = jca_impedance_from_bulk(f, phi, alpha_inf, sigma, "circular")
    elif name == "jca_slit":
        Zc, k = jca_impedance_from_bulk(f, phi, alpha_inf, sigma, "slit")
    elif name == "zwikker_kosten":
        # Zwikker-Kosten is the exact solution for a straight circular
        # pore, which has no tortuosity degree of freedom (alpha_inf=1
        # by construction); the input tortuosity is not applicable here.
        if alpha_inf != 1.0:
            notes.append(f"tortuosity={alpha_inf} ignored: Zwikker-Kosten assumes straight pores (alpha_inf=1)")
        a, _ = shape_characteristic_length(phi, 1.0, sigma, "circular")
        Zc, k = zwikker_kosten_impedance(f, phi, a)
    elif name == "delany_bazley_miki":
        notes.append("porosity and tortuosity ignored: Delany-Bazley-Miki is an empirical fit to flow resistivity alone")
        Zc, k = delany_bazley_miki_impedance(f, sigma)
    else:
        raise ValueError(f"unknown model: {name}")

    Zs = surface_impedance(Zc, k, L)
    alpha = absorption_coefficient(Zs)
    return dict(Zc=Zc, k=k, Zs=Zs, alpha=alpha), notes


if __name__ == "__main__":
    input_path = ask_for_input_file()
    raw_params = parse_input_file(input_path)
    cfg = validate_and_convert(raw_params, input_path)

    phi = cfg["porosity"]
    alpha_inf = cfg["tortuosity"]
    R_f = cfg["flow_resistance"]
    L = cfg["thickness"]
    sigma = R_f / L  # flow resistivity, the intrinsic material property

    f = np.logspace(np.log10(cfg["freq_min"]), np.log10(cfg["freq_max"]), cfg["n_points"])
    model_names = cfg["model_names"]

    print(f"Input file:  {input_path}")
    print(f"phi={phi}, alpha_inf={alpha_inf}, R_f={R_f:.1f} Pa s/m, L={L * 100:.2f} cm "
          f"-> sigma={sigma:.0f} Pa s/m^2")
    print(f"Frequency range: {cfg['freq_min']:.0f}-{cfg['freq_max']:.0f} Hz ({cfg['n_points']} points)")
    print(f"Model(s): {', '.join(model_names)}")

    results = {}
    i_probe = len(f) // 2
    for name in model_names:
        result, notes = run_model(name, f, phi, alpha_inf, sigma, L)
        results[name] = result
        for note in notes:
            print(f"  [{name}] note: {note}")
        print(f"  {name}: alpha({f[i_probe]:.0f} Hz) = {result['alpha'][i_probe]:.3f}")

    default_name = f"{os.path.splitext(os.path.basename(input_path))[0]}_{'-'.join(model_names)}.png"
    output_path = ask_for_output_file(default_name)
    out_dir = os.path.dirname(output_path)
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    for name in model_names:
        r = results[name]
        axes[0].semilogx(f, r["Zc"].real / (rho0 * c0), label=f"{name}, Re")
        axes[0].semilogx(f, r["Zc"].imag / (rho0 * c0), "--", label=f"{name}, Im")
        axes[1].semilogx(f, r["Zs"].real / (rho0 * c0), label=f"{name}, Re")
        axes[1].semilogx(f, r["Zs"].imag / (rho0 * c0), "--", label=f"{name}, Im")
        axes[2].semilogx(f, r["alpha"], label=name)

    axes[0].set_xlabel("frequency (Hz)")
    axes[0].set_ylabel("Zc / (rho0 c0)")
    axes[0].set_title("Characteristic impedance")

    axes[1].set_xlabel("frequency (Hz)")
    axes[1].set_ylabel("Zs / (rho0 c0)")
    axes[1].set_title(f"Surface impedance, L={L * 100:.1f} cm rigid-backed")

    axes[2].set_xlabel("frequency (Hz)")
    axes[2].set_ylabel("absorption coefficient")
    axes[2].set_title("Normal-incidence absorption")
    axes[2].set_ylim(0, 1.05)

    for ax in axes:
        ax.legend(fontsize=7)
        ax.grid(alpha=0.3, which="both")

    fig.suptitle(f"phi={phi}, alpha_inf={alpha_inf}, R_f={R_f:.0f} Pa s/m, L={L * 100:.1f} cm")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    print(f"Saved plot to {output_path}")
