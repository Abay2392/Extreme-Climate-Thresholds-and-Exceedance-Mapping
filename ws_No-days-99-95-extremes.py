# -*- coding: utf-8 -*-
"""
Created on Mon May 11 10:50:31 2026

@author: khvj92
"""

# -*- coding: utf-8 -*-
"""
Publication-quality plot:
1) Number of days with rainfall >= 40 mm/day
2) Number of days with rainfall >= 99th percentile
for each grid cell over 1990-2022
"""

import numpy as np
import h5py
import geopandas as gpd
import matplotlib.pyplot as plt

# --------------------------------------------------
# File paths
# --------------------------------------------------
clipped_file = r"C:\Users\abaym\OneDrive - Durham University\Met Office\RainAll_clipped.h5"
shp_file     = r"C:\Users\abaym\OneDrive - Durham University\Met Office\NPg-full.shp"

# --------------------------------------------------
# Thresholds
# --------------------------------------------------
threshold_fixed = 40.0   # mm/day

# --------------------------------------------------
# Read dataset dimensions
# --------------------------------------------------
with h5py.File(clipped_file, 'r') as f:
    rain_ds = f['RainAll_clipped']
    nt, ny, nx = rain_ds.shape

print("Dataset shape:", (nt, ny, nx))

# --------------------------------------------------
# Preallocate output maps
# --------------------------------------------------
freq40_map   = np.full((ny, nx), np.nan, dtype=np.float32)
freq99_map   = np.full((ny, nx), np.nan, dtype=np.float32)
pct99_map    = np.full((ny, nx), np.nan, dtype=np.float32)  # stores the threshold value

# --------------------------------------------------
# Block size (safe for Spyder / RAM)
# --------------------------------------------------
block_y = 50
block_x = 50

# --------------------------------------------------
# Process file block by block
# --------------------------------------------------
with h5py.File(clipped_file, 'r') as f:

    rain_ds = f['RainAll_clipped']

    for y0 in range(0, ny, block_y):
        y1 = min(y0 + block_y, ny)

        for x0 in range(0, nx, block_x):
            x1 = min(x0 + block_x, nx)

            print(f"Processing rows {y0}:{y1}, cols {x0}:{x1}")

            # Read one spatial block for all days — shape: (time, y, x)
            block = np.array(rain_ds[:, y0:y1, x0:x1], dtype=np.float32)

            # Skip fully empty blocks
            if np.all(np.isnan(block)):
                continue

            valid = np.any(np.isfinite(block), axis=0)

            # ── Fixed threshold: days >= 40 mm ──────────────────────────
            freq_block_40 = np.sum(block >= threshold_fixed, axis=0)
            freq40_map[y0:y1, x0:x1] = np.where(
                valid, freq_block_40, np.nan
            ).astype(np.float32)

            # ── 99th percentile threshold per grid cell ──────────────────
            # Only use wet days (> 0) to match WMO convention (optional —
            # remove the masking line below to use ALL days instead)
            block_wet = np.where(block > 0, block, np.nan)

            # nanpercentile along time axis → shape (y, x)
            p99 = np.nanpercentile(block_wet, 99, axis=0)   # or use `block` for all days
            pct99_map[y0:y1, x0:x1] = np.where(valid, p99, np.nan).astype(np.float32)

            # Count days that exceed the cell-specific 99th percentile
            # p99 has shape (y, x); expand to (time, y, x) for comparison
            freq_block_99 = np.sum(block >= p99[np.newaxis, :, :], axis=0)
            freq99_map[y0:y1, x0:x1] = np.where(
                valid, freq_block_99, np.nan
            ).astype(np.float32)

            del block, block_wet, freq_block_40, freq_block_99, p99

print("Finished calculations.")

# --------------------------------------------------
# Crop to rainfall extent (shared bounding box)
# --------------------------------------------------
rows, cols = np.where(~np.isnan(freq40_map))
rmin, rmax = rows.min(), rows.max()
cmin, cmax = cols.min(), cols.max()
pad = 15
rmin = max(rmin - pad, 0);  rmax = min(rmax + pad, ny)
cmin = max(cmin - pad, 0);  cmax = min(cmax + pad, nx)

freq40_crop = freq40_map[rmin:rmax, cmin:cmax]
freq99_crop = freq99_map[rmin:rmax, cmin:cmax]
pct99_crop  = pct99_map[rmin:rmax, cmin:cmax]   # optional — for a 3rd panel

# --------------------------------------------------
# Shapefile extent
# --------------------------------------------------
gdf = gpd.read_file(shp_file)
if gdf.crs is None or gdf.crs.to_epsg() != 4326:
    gdf = gdf.to_crs(epsg=4326)
minx, miny, maxx, maxy = gdf.total_bounds
extent = [minx, maxx, miny, maxy]

# --------------------------------------------------
# Plot settings
# --------------------------------------------------
plt.rcParams.update({
    'font.family': 'Arial',
    'font.size': 16,
    'axes.titlesize': 20,
    'axes.labelsize': 19,
    'xtick.labelsize': 15,
    'ytick.labelsize': 15
})

# --------------------------------------------------
# Two-panel figure
# --------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(16, 10), dpi=600)

panels = [
    (axes[0], freq40_crop, 'Blues',
     'Days with Daily Rainfall\n≥ 40 mm/day (1990–2022)'),
    (axes[1], freq99_crop, 'Oranges',
     'Days Exceeding 99th Percentile\nRainfall (1990–2022)'),
]

for ax, data, cmap, title in panels:

    vmin = 1
    vmax = int(np.nanmax(data))

    im = ax.imshow(
        data,
        origin='lower',
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        extent=extent,
        interpolation='nearest'
    )

    ax.set_title(title, fontweight='bold', fontsize=20, pad=14)
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')

    for spine in ax.spines.values():
        spine.set_linewidth(1.2)

    cbar = plt.colorbar(im, ax=ax, fraction=0.04, pad=0.035, shrink=0.78)
    cbar.set_label('Number of Days', fontsize=17)
    cbar.set_ticks(np.linspace(vmin, vmax, 6, dtype=int))
    cbar.ax.tick_params(labelsize=14)

plt.tight_layout()

plt.savefig(
    'Frequency_Map_40mm_and_99pct_Final.png',
    dpi=600,
    bbox_inches='tight'
)
plt.show()