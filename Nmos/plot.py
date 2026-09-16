import csv
import argparse
from pathlib import Path

import matplotlib

try:
	import tkinter

	matplotlib.use("TkAgg")
	interactive_backend = True
except ImportError:
	matplotlib.use("Agg")
	interactive_backend = False

import matplotlib.pyplot as plt
import numpy as np


DATA_FILE = Path(__file__).with_name("nmos_analysis.csv")


def load_analysis(path):
	with path.open(newline="") as csv_file:
		rows = list(csv.DictReader(csv_file))

	vds_values = np.array(sorted({float(row["vds"]) for row in rows}))
	vgs_values = np.array(sorted({float(row["vgs"]) for row in rows}))
	grids = {
		name: np.full((vgs_values.size, vds_values.size), np.nan)
		for name in ("id", "gm", "gm_over_id")
	}
	vds_index = {value: index for index, value in enumerate(vds_values)}
	vgs_index = {value: index for index, value in enumerate(vgs_values)}

	for row in rows:
		vds = float(row["vds"])
		vgs = float(row["vgs"])
		row_index = vgs_index[vgs]
		column_index = vds_index[vds]
		for name in grids:
			grids[name][row_index, column_index] = float(row[name])

	return vds_values, vgs_values, grids


def show_or_save(figure, path, filename):
	if interactive_backend:
		plt.show()
	else:
		output_path = path.with_name(filename)
		figure.savefig(output_path, dpi=150)
		print(f"Saved plot to {output_path}")


def plot_analysis(path=DATA_FILE, requested_vgs=None):
	vds, vgs, grids = load_analysis(path)

	# gm/id is undefined where the drain current is effectively zero.
	current_scale = np.nanmax(np.abs(grids["id"]))
	invalid_ratio = np.abs(grids["id"]) <= max(current_scale * 1e-12, 1e-30)
	gm_over_id = grids["gm_over_id"].copy()
	gm_over_id[invalid_ratio] = np.nan

	if requested_vgs is not None:
		matching_vgs = vgs[np.isclose(vgs, requested_vgs, rtol=0, atol=1e-9)]
		if matching_vgs.size == 0:
			raise ValueError(
				f"VGS={requested_vgs:g} V is not in the data. "
				f"Choose one of the swept values from {vgs[0]:g} to {vgs[-1]:g} V."
			)

		vgs_value = matching_vgs[0]
		vgs_index = np.flatnonzero(np.isclose(vgs, vgs_value))[0]
		plots = (
			(grids["id"][vgs_index], "$I_D$ (A)", "tab:blue"),
			(grids["gm"][vgs_index], "$g_m$ (S)", "tab:orange"),
			(gm_over_id[vgs_index], "$g_m/I_D$ (1/V)", "tab:green"),
		)
		figure, axes = plt.subplots(1, 3, figsize=(18, 5), constrained_layout=True)
		for axis, (values, y_label, color) in zip(axes, plots):
			axis.plot(vds, values, color=color, linewidth=2)
			axis.set_xlabel("$V_{DS}$ (V)")
			axis.set_ylabel(y_label)
			axis.set_title(f"{y_label} at $V_{{GS}}={vgs_value:g}$ V")
			axis.grid(True, alpha=0.3)
		show_or_save(figure, path, f"nmos_cuts_vgs_{vgs_value:g}.png")
		return

	vds_grid, vgs_grid = np.meshgrid(vds, vgs)

	plots = (
		("id", "$I_D$ (A)", "viridis"),
		("gm", "$g_m$ (S)", "plasma"),
		("gm_over_id", "$g_m/I_D$ (1/V)", "cividis"),
	)
	figure = plt.figure(figsize=(18, 5), constrained_layout=True)

	for plot_number, (name, z_label, color_map) in enumerate(plots, start=1):
		axis = figure.add_subplot(1, 3, plot_number, projection="3d")
		values = gm_over_id if name == "gm_over_id" else grids[name]
		surface = axis.plot_surface(
			vds_grid,
			vgs_grid,
			values,
			cmap=color_map,
			edgecolor="none",
		)
		axis.set_xlabel("$V_{DS}$ (V)")
		axis.set_ylabel("$V_{GS}$ (V)")
		axis.set_zlabel(z_label)
		axis.set_title(z_label)
		figure.colorbar(surface, ax=axis, shrink=0.7, pad=0.1)

	show_or_save(figure, path, "nmos_analysis_3d.png")


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Plot NMOS analysis data.")
	parser.add_argument(
		"--vgs",
		type=float,
		help="show ID, gm, and gm/ID cuts at this swept VGS value",
	)
	args = parser.parse_args()
	plot_analysis(requested_vgs=args.vgs)
