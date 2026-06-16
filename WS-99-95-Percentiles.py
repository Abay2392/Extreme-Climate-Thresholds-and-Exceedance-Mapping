# -*- coding: utf-8 -*-
"""
Created on Tue May 12 15:31:55 2026

@author: abaym
"""

# -*- coding: utf-8 -*-
"""
Plot 99th and 95th percentile wind speed threshold values (m/s) per cell
1990-2019
"""

import numpy as np
import netCDF4 as nc
import geopandas as gpd
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
from scipy.interpolate import griddata
from shapely.vectorized import contains

# --------------------------------------------------
# File paths
# --------------------------------------------------
wind_file = r"C:\Users\abaym\OneDrive - Durham University\Met Office\WindSpeed_NPG_v2.nc"
shp_file  = r"C:\Users\abaym\OneDrive - Durham University\Met Office\NPg-full.shp"

# --------------------------------------------------
# Shapefile
# --------------------------------------------------
gdf = gpd.read_file(shp_file)
if gdf.crs is None or gdf.crs.to_epsg() != 4326:
    gdf = gdf.to_crs(epsg=4326)
minx, miny, maxx, maxy = gdf.total_bounds
region_wgs84 = gdf.geometry.unary_union

# --------------------------------------------------
# Read dimensions
# --------------------------------------------------
with nc.Dataset(wind_file, 'r') as ds:
    lat2d    = np.array(ds.variables['lat'][:])
    lon2d    = np.array(ds.variables['lon'][:])
    fill_val = float(ds.variables['sfcWind']._FillValue)
    nt, ny, nx = ds.variables['sfcWind'].shape

print(f"Shape: {nt} x {ny} x {nx}")

# --------------------------------------------------
# Preallocate
# --------------------------------------------------
pct99_map = np.full((ny, nx), np.nan, dtype=np.float32)
pct95_map = np.full((ny, nx), np.nan, dtype=np.float32)

block_y = 50
block_x = 50

# --------------------------------------------------
# Compute per-cell 99th and 95th percentile values
# --------------------------------------------------
print("\n--- Computing per-cell percentile values ---")

with nc.Dataset(wind_file, 'r') as ds:
    v = ds.variables['sfcWind']

    for y0 in range(0, ny, block_y):
        y1 = min(y0 + block_y, ny)

        for x0 in range(0, nx, block_x):
            x1 = min(x0 + block_x, nx)

            print(f"  rows {y0}:{y1}, cols {x0}:{x1}")

            block = np.array(v[:, y0:y1, x0:x1], dtype=np.float32)
            block[block == fill_val] = np.nan

            if np.all(np.isnan(block)):
                continue

            valid = np.any(np.isfinite(block), axis=0)

            p99 = np.nanpercentile(block, 99, axis=0)
            p95 = np.nanpercentile(block, 95, axis=0)

            pct99_map[y0:y1, x0:x1] = np.where(valid, p99, np.nan)
            pct95_map[y0:y1, x0:x1] = np.where(valid, p95, np.nan)

            del block, p99, p95

print("Done.")
print(f"  99th percentile: {np.nanmin(pct99_map):.2f} – {np.nanmax(pct99_map):.2f} m/s")
print(f"  95th percentile: {np.nanmin(pct95_map):.2f} – {np.nanmax(pct95_map):.2f} m/s")

# --------------------------------------------------
# Build regular WGS84 grid and mask
# --------------------------------------------------
print("\nBuilding WGS84 grid ...")
n_lon = int((maxx - minx) / 0.009) + 1
n_lat = int((maxy - miny) / 0.009) + 1
grid_lon, grid_lat = np.meshgrid(
    np.linspace(minx, maxx, n_lon),
    np.linspace(miny, maxy, n_lat)
)
in_region = contains(
    region_wgs84,
    grid_lon.ravel(),
    grid_lat.ravel()
).reshape(grid_lon.shape)

# --------------------------------------------------
# Reproject to regular WGS84
# --------------------------------------------------
def reproject(arr, lon2d, lat2d, grid_lon, grid_lat, in_region):
    valid  = ~np.isnan(arr)
    result = griddata(
        points = np.column_stack([lon2d[valid], lat2d[valid]]),
        values = arr[valid],
        xi     = (grid_lon, grid_lat),
        method = 'linear'
    ).astype(np.float32)
    result[~in_region] = np.nan
    return result

print("Reprojecting ...")
pct99_wgs = reproject(pct99_map, lon2d, lat2d, grid_lon, grid_lat, in_region)
pct95_wgs = reproject(pct95_map, lon2d, lat2d, grid_lon, grid_lat, in_region)

# --------------------------------------------------
# Smooth
# --------------------------------------------------
def smooth(arr):
    s = gaussian_filter(np.where(np.isnan(arr), 0, arr), sigma=1.0)
    return np.where(np.isnan(arr), np.nan, s)

pct99_wgs = smooth(pct99_wgs)
pct95_wgs = smooth(pct95_wgs)

# --------------------------------------------------
# Plot settings
# --------------------------------------------------
plt.rcParams.update({
    'font.family'    : 'Arial',
    'font.size'      : 16,
    'axes.titlesize' : 20,
    'axes.labelsize' : 19,
    'xtick.labelsize': 15,
    'ytick.labelsize': 15
})

extent = [minx, maxx, miny, maxy]

# --------------------------------------------------
# Two-panel figure
# --------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(16, 10), dpi=600)

panels = [
    (axes[0], pct99_wgs, 'YlOrRd',
     '99th Percentile Wind Speed\n(m/s, 1990–2019)',
     'Wind Speed (m/s)'),
    (axes[1], pct95_wgs, 'YlGnBu',
     '95th Percentile Wind Speed\n(m/s, 1990–2019)',
     'Wind Speed (m/s)'),
]

for ax, data, cmap, title, cbar_label in panels:

    vmin = np.nanpercentile(data, 2)
    vmax = np.nanpercentile(data, 98)

    im = ax.imshow(
        data,
        origin='lower',
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        extent=extent,
        interpolation='bilinear'
    )

    gdf.boundary.plot(ax=ax, edgecolor='black', linewidth=0.8)
    ax.set_title(title, fontweight='bold', fontsize=20, pad=14)
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')

    for spine in ax.spines.values():
        spine.set_linewidth(1.2)

    cbar = plt.colorbar(im, ax=ax, fraction=0.04, pad=0.035, shrink=0.78)
    cbar.set_label(cbar_label, fontsize=17)
    cbar.set_ticks(np.round(np.linspace(vmin, vmax, 6), 1))
    cbar.ax.tick_params(labelsize=14)

plt.tight_layout()

plt.savefig(
    r"C:\Users\khvj92\OneDrive - Durham University\Met Office\WindSpeed_99th_95th_Percentile_Values.png",
    dpi=600, bbox_inches='tight'
)
plt.show()
print("Done.")