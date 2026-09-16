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
		for name in ("id", "gm", "gm_over_id", "gm_r0")
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


METRICS = {
	"id": ("$I_D$ (A)", "viridis"),
	"gm": ("$g_m$ (S)", "plasma"),
	"gm_over_id": ("$g_m/I_D$ (1/V)", "cividis"),
	"gm_r0": ("$g_m r_o$", "magma"),
}


def matching_value(values, requested, name):
	matching = values[np.isclose(values, requested, rtol=0, atol=1e-9)]
	if matching.size == 0:
		raise ValueError(
			f"{name}={requested:g} V is not in the data. "
			f"Choose one of the swept values from {values[0]:g} to {values[-1]:g} V."
		)
	return matching[0]


def plot_analysis(path=DATA_FILE, metric_names=None, requested_vds=None, requested_vgs=None):
	vds, vgs, grids = load_analysis(path)
	metric_names = metric_names or list(METRICS)

	# gm/id is undefined where the drain current is effectively zero.
	current_scale = np.nanmax(np.abs(grids["id"]))
	invalid_ratio = np.abs(grids["id"]) <= max(current_scale * 1e-12, 1e-30)
	gm_over_id = grids["gm_over_id"].copy()
	gm_over_id[invalid_ratio] = np.nan

	if requested_vds is not None and requested_vgs is not None:
		vds_value = matching_value(vds, requested_vds, "VDS")
		vgs_value = matching_value(vgs, requested_vgs, "VGS")
		vds_index = np.flatnonzero(np.isclose(vds, vds_value))[0]
		vgs_index = np.flatnonzero(np.isclose(vgs, vgs_value))[0]
		print(
			f"\033[1;36mOperating point:\033[0m "
			f"\033[33mVDS={vds_value:g} V\033[0m, "
			f"\033[35mVGS={vgs_value:g} V\033[0m"
		)
		for name in METRICS:
			value = gm_over_id[vgs_index, vds_index] if name == "gm_over_id" else grids[name][vgs_index, vds_index]
			print(f"{name}={value:g}")
		return

	if requested_vds is not None or requested_vgs is not None:
		figure, axes = plt.subplots(1, len(metric_names), figsize=(6 * len(metric_names), 5), squeeze=False, constrained_layout=True)
		axes = axes[0]
		if requested_vgs is not None:
			vgs_value = matching_value(vgs, requested_vgs, "VGS")
			index = np.flatnonzero(np.isclose(vgs, vgs_value))[0]
			x_values, x_label, suffix = vds, "$V_{DS}$ (V)", f"vgs_{vgs_value:g}"
			values_for = lambda name: (gm_over_id if name == "gm_over_id" else grids[name])[index]
		else:
			vds_value = matching_value(vds, requested_vds, "VDS")
			index = np.flatnonzero(np.isclose(vds, vds_value))[0]
			x_values, x_label, suffix = vgs, "$V_{GS}$ (V)", f"vds_{vds_value:g}"
			values_for = lambda name: (gm_over_id if name == "gm_over_id" else grids[name])[:, index]
		for axis, name in zip(axes, metric_names):
			label, _ = METRICS[name]
			axis.plot(x_values, values_for(name), linewidth=2)
			axis.set(xlabel=x_label, ylabel=label, title=label)
			axis.grid(True, alpha=0.3)
		show_or_save(figure, path, f"nmos_plane_{suffix}.png")
		return

	vds_grid, vgs_grid = np.meshgrid(vds, vgs)
	figure = plt.figure(figsize=(6 * len(metric_names), 5), constrained_layout=True)

	for plot_number, name in enumerate(metric_names, start=1):
		z_label, color_map = METRICS[name]
		axis = figure.add_subplot(1, len(metric_names), plot_number, projection="3d")
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
	parser = argparse.ArgumentParser(
		description="Plot NMOS analysis data.",
		usage="%(prog)s [--id | --gm | --gm_over_id | --gm_r0] [--vgs VGS] [--vds VDS]",
		formatter_class=argparse.RawDescriptionHelpFormatter,
		epilog=(
			"\033[1;36mTwo-bias query:\033[0m "
			"\033[33m--vds VDS\033[0m \033[35m--vgs VGS\033[0m"
		),
	)
	metric_group = parser.add_mutually_exclusive_group()
	for name in METRICS:
		metric_group.add_argument(f"--{name}", action="store_true", help=f"plot {name}")
	parser.add_argument("--vds", type=float, metavar="VDS", help="select a swept VDS value")
	parser.add_argument("--vgs", type=float, metavar="VGS", help="select a swept VGS value")
	args = parser.parse_args()
	selected_metric = next((name for name in METRICS if getattr(args, name)), None)
	plot_analysis(
		metric_names=[selected_metric] if selected_metric else None,
		requested_vds=args.vds,
		requested_vgs=args.vgs,
	)
