# -*- coding: utf-8 -*-
"""
Created on Mon May 11 11:22:57 2026

@author: khvj92
"""

# -*- coding: utf-8 -*-
"""
Publication-quality plots:
1) 99th percentile rainfall threshold (mm/day) per grid cell
2) 95th percentile rainfall threshold (mm/day) per grid cell
3) Number of days exceeding 99th percentile per grid cell
4) Number of days exceeding 95th percentile per grid cell
for each grid cell over 1990-2022
"""

import numpy as np
import h5py
import geopandas as gpd
import matplotlib.pyplot as plt

# --------------------------------------------------
# File paths
# --------------------------------------------------
clipped_file = r"C:\Users\khvj92\OneDrive - Durham University\Met Office\RainAll_clipped.h5"
shp_file     = r"C:\Users\khvj92\OneDrive - Durham University\Met Office\NPg-full.shp"

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
pct99_map  = np.full((ny, nx), np.nan, dtype=np.float32)  # 99th percentile threshold (mm/day)
pct95_map  = np.full((ny, nx), np.nan, dtype=np.float32)  # 95th percentile threshold (mm/day)
freq99_map = np.full((ny, nx), np.nan, dtype=np.float32)  # days exceeding 99th percentile
freq95_map = np.full((ny, nx), np.nan, dtype=np.float32)  # days exceeding 95th percentile

# --------------------------------------------------
# Block size (safe for Spyder / RAM)
# --------------------------------------------------
block_y = 50
block_x = 50

# --------------------------------------------------
# PASS 1: Compute percentile thresholds block by block
# --------------------------------------------------
print("\n--- Pass 1: Computing percentile thresholds ---")

with h5py.File(clipped_file, 'r') as f:

    rain_ds = f['RainAll_clipped']

    for y0 in range(0, ny, block_y):
        y1 = min(y0 + block_y, ny)

        for x0 in range(0, nx, block_x):
            x1 = min(x0 + block_x, nx)

            print(f"  Percentile pass rows {y0}:{y1}, cols {x0}:{x1}")

            block = np.array(rain_ds[:, y0:y1, x0:x1], dtype=np.float32)

            if np.all(np.isnan(block)):
                continue

            valid = np.any(np.isfinite(block), axis=0)

            # Wet days only (WMO convention)
            block_wet = np.where(block > 0, block, np.nan)

            # 99th and 95th percentile thresholds per cell
            p99 = np.nanpercentile(block_wet, 99, axis=0)
            p95 = np.nanpercentile(block_wet, 95, axis=0)

            pct99_map[y0:y1, x0:x1] = np.where(valid, p99, np.nan).astype(np.float32)
            pct95_map[y0:y1, x0:x1] = np.where(valid, p95, np.nan).astype(np.float32)

            del block, block_wet, p99, p95

print("Pass 1 complete.")

# --------------------------------------------------
# PASS 2: Count exceedances using stored thresholds
# --------------------------------------------------
print("\n--- Pass 2: Counting exceedance days ---")

with h5py.File(clipped_file, 'r') as f:

    rain_ds = f['RainAll_clipped']

    for y0 in range(0, ny, block_y):
        y1 = min(y0 + block_y, ny)

        for x0 in range(0, nx, block_x):
            x1 = min(x0 + block_x, nx)

            print(f"  Exceedance pass rows {y0}:{y1}, cols {x0}:{x1}")

            block = np.array(rain_ds[:, y0:y1, x0:x1], dtype=np.float32)

            if np.all(np.isnan(block)):
                continue

            valid = np.any(np.isfinite(block), axis=0)

            # Retrieve the already-computed thresholds for this block
            p99_block = pct99_map[y0:y1, x0:x1]   # shape (y, x)
            p95_block = pct95_map[y0:y1, x0:x1]   # shape (y, x)

            # Broadcast thresholds across time axis for comparison
            freq99_block = np.sum(block > p99_block[np.newaxis, :, :], axis=0)
            freq95_block = np.sum(block > p95_block[np.newaxis, :, :], axis=0)

            freq99_map[y0:y1, x0:x1] = np.where(valid, freq99_block, np.nan).astype(np.float32)
            freq95_map[y0:y1, x0:x1] = np.where(valid, freq95_block, np.nan).astype(np.float32)

            del block, freq99_block, freq95_block

print("Pass 2 complete.")

# --------------------------------------------------
# Crop to rainfall extent (shared bounding box)
# --------------------------------------------------
rows, cols = np.where(~np.isnan(pct99_map))
rmin, rmax = rows.min(), rows.max()
cmin, cmax = cols.min(), cols.max()
pad = 15
rmin = max(rmin - pad, 0);  rmax = min(rmax + pad, ny)
cmin = max(cmin - pad, 0);  cmax = min(cmax + pad, nx)

pct99_crop  = pct99_map[rmin:rmax, cmin:cmax]
pct95_crop  = pct95_map[rmin:rmax, cmin:cmax]
freq99_crop = freq99_map[rmin:rmax, cmin:cmax]
freq95_crop = freq95_map[rmin:rmax, cmin:cmax]

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
# Four-panel figure (2 rows x 2 cols)
# Row 1: Percentile threshold maps (mm/day)
# Row 2: Exceedance count maps (number of days)
# --------------------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(16, 18), dpi=600)

panels = [
    # Row 1 — threshold maps
    (axes[0, 0], pct99_crop,  'YlOrRd', True,
     '99th Percentile Rainfall Threshold\n(mm/day, 1990–2022)',
     'Rainfall Threshold (mm/day)'),

    (axes[0, 1], pct95_crop,  'YlGnBu', True,
     '95th Percentile Rainfall Threshold\n(mm/day, 1990–2022)',
     'Rainfall Threshold (mm/day)'),

    # Row 2 — exceedance count maps
    (axes[1, 0], freq99_crop, 'OrRd',   False,
     'Days Exceeding 99th Percentile\n(1990–2022)',
     'Number of Days'),

    (axes[1, 1], freq95_crop, 'GnBu',   False,
     'Days Exceeding 95th Percentile\n(1990–2022)',
     'Number of Days'),
]

for ax, data, cmap, stretch, title, cbar_label in panels:

    if stretch:
        # Percentile maps: clip to 2nd-98th to reveal spatial variation
        vmin = np.nanpercentile(data, 2)
        vmax = np.nanpercentile(data, 98)
        tick_vals = np.round(np.linspace(vmin, vmax, 6), 1)
    else:
        # Exceedance maps: use actual data range
        vmin = np.nanmin(data)
        vmax = np.nanmax(data)
        tick_vals = np.linspace(vmin, vmax, 6, dtype=int)

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
    cbar.set_label(cbar_label, fontsize=17)
    cbar.set_ticks(tick_vals)
    cbar.ax.tick_params(labelsize=14)

plt.tight_layout()

# --------------------------------------------------
# Save
# --------------------------------------------------
plt.savefig(
    'Percentile_Maps_Thresholds_and_Exceedances_Final.png',
    dpi=600,
    bbox_inches='tight'
)

plt.show()