# MOSFET Characterization with ngspice and Python

This project sweeps $V_{DS}$ and $V_{GS}$ for SKY130 NMOS and PMOS devices, then plots:

- $I_D(V_{DS}, V_{GS})$
- $g_m(V_{DS}, V_{GS})$
- $g_m/I_D(V_{DS}, V_{GS})$

## Requirements

- ngspice
- SKY130 PDK with `PDK_ROOT` configured
- Python 3 with `numpy` and `matplotlib`
- `tkinter` for interactive plot windows

Create or activate the project environment:

```bash
cd /home/goose/Projects/Spice/Mos
source .venv/bin/activate
pip install numpy matplotlib
```

On Ubuntu, install Tk separately if interactive windows are needed:

```bash
sudo apt install python3.14-tk
```

## Run Simulations

Run each ngspice deck from its own directory:

```bash
cd Nmos
ngspice -b nmos.spice -o out.log

cd ../Pmos
ngspice -b pmos.spice -o out.log
```

The simulations write `nmos_analysis.csv` and `pmos_analysis.csv`. Both sweeps use `0.05 V` steps.

- NMOS: `VDS` and `VGS` from `0 V` to `1.8 V`
- PMOS: `VDS` and `VGS` from `0 V` to `-1.8 V`

## Plot 3D Surfaces

With no arguments, each script opens three 3D surfaces for $I_D$, $g_m$, and $g_m/I_D$:

```bash
cd Nmos
python plot.py

cd ../Pmos
python plot.py
```

If `tkinter` is unavailable, the scripts use a non-interactive backend and save:

- `Nmos/nmos_analysis_3d.png`
- `Pmos/pmos_analysis_3d.png`

## Plot a VGS Cut

Use `--vgs` to view $I_D$, $g_m$, and $g_m/I_D$ versus $V_{DS}$ at one exact swept gate voltage:

```bash
cd ./Nmos
python plot.py --vgs 1.0

cd ./Pmos
python plot.py --vgs -1.0
```

The requested value must be one of the simulated `VGS` values, in `0.05 V` increments.
