# Data provenance and release scope

## Source processing

The analysis uses calibrated Google Earth Engine Sentinel-1 GRD VV backscatter and incidence angle. β⁰ is estimated as:

\[
\beta^0_{est,dB}=\sigma^0_{dB}-10\log_{10}(\sin\theta)
\]

A 3×3 spatial median filter is applied before extracting the fixed-reference indices. The production baseline and experimental WI remain separate and retain their original reference populations, thresholds, and eligibility rules.

## Included derived products

- Field inventory index: 26,410 supplied records, including coordinates and quality notes.
- Field-level experimental WI time series: 2,291,784 rows, split across Parquet files.
- Production regional and participating-area summaries and reversal maps.
- Experimental WI regional and participating-area summaries and reversal maps.
- Historical potential-rice support layer: Open-SEA-Rice-10 intersected with WorldCover Cropland.
- Supplied field-system outlines for MARIIS, UCRIS, and MRIS. These are not official irrigation-system boundaries.

## Explicit exclusions

Credentials, `.env` files, water-level SQL records, raw Sentinel-1 rasters, intermediate rasters, thresholds checkpoints, and temporary files are not part of this release.

## Reproducibility notes

The public repository is a presentation bundle, not the full 22 GB processing workspace. `scripts/prepare_release.py` records the exact source-output mapping used locally. Full processing provenance and validation checks are summarized in the Step 35 report and validation JSON.
