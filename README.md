# Extreme-Climate-Thresholds-and-Exceedance-Mapping
Python workflow for mapping 95th and 99th percentile climate extremes and exceedance frequencies from gridded NetCDF datasets.
# Extreme Climate Threshold and Exceedance Mapping from Gridded NetCDF Datasets

## Overview

This repository contains Python workflows for identifying, quantifying, and mapping climate extremes from gridded NetCDF datasets. The code computes percentile-based threshold values and exceedance frequencies for multiple climate variables and produces publication-quality spatial maps.

The workflow was developed for Northeast England using gridded climate datasets and can be adapted to any region with NetCDF climate data and a boundary shapefile.

The repository provides both:

1. Spatial maps of extreme climate thresholds.
2. Spatial maps of the number of days exceeding those thresholds.

These products are useful for climate hazard assessment, infrastructure vulnerability studies, compound event analysis, and climate change impact assessments.

---

# Repository Structure

The repository consists of two main Python scripts.

## 1. WS-99-95-Percentiles.py

### Purpose

This script computes the spatial distribution of percentile threshold values for climate variables.

### Main Tasks

* Reads gridded NetCDF climate datasets.
* Computes extreme percentile thresholds at each grid cell.
* Interpolates results onto a regular geographic grid.
* Applies spatial smoothing.
* Clips outputs to the study region boundary.
* Produces publication-quality maps.

### Extreme Thresholds

For variables representing high extremes:

* Rainfall
* Maximum Temperature (Tmax)
* Wind Speed
* Solar Radiation
* Potential Evapotranspiration (PET)
* Relative Humidity
* Surface Pressure

the script calculates:

```text
95th percentile
99th percentile
```

For variables representing low extremes:

* Minimum Temperature (Tmin)

the script calculates:

```text
5th percentile
1st percentile
```

### Outputs

Examples include:

```text
95th Percentile Rainfall Threshold Map
99th Percentile Rainfall Threshold Map

95th Percentile Tmax Threshold Map
99th Percentile Tmax Threshold Map

95th Percentile Wind Speed Threshold Map
99th Percentile Wind Speed Threshold Map

5th Percentile Tmin Threshold Map
1st Percentile Tmin Threshold Map
```

Each output represents the threshold value exceeded only by the most extreme events at a given location.

---

## 2. No-Days-95-99-NPG.py

### Purpose

This script computes the frequency of extreme climate events by counting the number of days exceeding previously calculated percentile thresholds.

### Main Tasks

* Reads NetCDF climate datasets.
* Applies percentile thresholds.
* Counts exceedance events for each grid cell.
* Produces spatial maps of extreme-event frequency.
* Visualizes spatial patterns of climate hazard occurrence.

### Frequency Calculations

For rainfall, Tmax, wind speed, and other high-extreme variables:

```text
Number of days ≥ 95th percentile
Number of days ≥ 99th percentile
```

For Tmin:

```text
Number of days ≤ 5th percentile
Number of days ≤ 1st percentile
```

### Outputs

Examples include:

```text
Rainfall Days Above 95th Percentile
Rainfall Days Above 99th Percentile

Tmax Days Above 95th Percentile
Tmax Days Above 99th Percentile

Wind Speed Days Above 95th Percentile
Wind Speed Days Above 99th Percentile

Tmin Days Below 5th Percentile
Tmin Days Below 1st Percentile
```

These maps represent the spatial frequency of extreme events across the study area.

---

# Input Data

The workflow uses gridded climate datasets stored in NetCDF format.

Data structure:

```text
Time × Latitude × Longitude
```

Supported variables include:

### High Extremes

* Rainfall
* Maximum Temperature (Tmax)
* Wind Speed
* Solar Radiation
* Potential Evapotranspiration (PET)
* Relative Humidity
* Surface Pressure

### Low Extremes

* Minimum Temperature (Tmin)

---

# Spatial Processing Workflow

## Step 1: Read NetCDF Data

The climate variable is extracted from the NetCDF file.

## Step 2: Percentile Computation

Percentiles are calculated independently for each grid cell using the complete historical record.

### High Extreme Variables

```text
95th Percentile
99th Percentile
```

### Low Extreme Variables

```text
5th Percentile
1st Percentile
```

---

## Step 3: Exceedance Frequency Calculation

The number of extreme-event days is calculated.

### High Extremes

```text
Value ≥ Percentile Threshold
```

### Low Extremes

```text
Value ≤ Percentile Threshold
```

---

## Step 4: Spatial Interpolation

Irregular grids are interpolated onto a regular WGS84 grid using:

```python
scipy.interpolate.griddata()
```

---

## Step 5: Geographic Masking

The interpolated surfaces are clipped using a regional boundary shapefile.

Libraries used:

```python
GeoPandas
Shapely
```

---

## Step 6: Spatial Smoothing

Spatial fields are smoothed using:

```python
scipy.ndimage.gaussian_filter()
```

to improve map readability and reduce interpolation artefacts.

---

# Mapping Outputs

For each climate variable, the workflow produces:

## Threshold Maps

### High Extremes

```text
95th Percentile Threshold
99th Percentile Threshold
```

### Low Extremes

```text
5th Percentile Threshold
1st Percentile Threshold
```

## Frequency Maps

### High Extremes

```text
Days Above 95th Percentile
Days Above 99th Percentile
```

### Low Extremes

```text
Days Below 5th Percentile
Days Below 1st Percentile
```

---

# Python Dependencies

Required packages:

```text
numpy
netCDF4
geopandas
matplotlib
scipy
shapely
```

Install using:

```bash
pip install numpy netCDF4 geopandas matplotlib scipy shapely
```

---

# Applications

This workflow can be applied to:

* Extreme rainfall analysis
* Heatwave assessment
* Windstorm hazard assessment
* Cold-spell monitoring
* Climate extremes characterization
* Compound climate event analysis
* Power outage risk modelling
* Infrastructure resilience assessment
* Climate change impact studies
* Regional climate hazard mapping

---

# Author

Dr. Tagele Mossie Aschale

Department of Geography

Durham University

---

# Citation

If you use this repository in your research, please cite the associated publication and acknowledge this repository in any resulting publications.

