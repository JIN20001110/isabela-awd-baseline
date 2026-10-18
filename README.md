# Isabela AWD Baseline Screening

An interactive Streamlit dashboard for a regional, pre-intervention assessment of repeated Sentinel-1 SAR signal changes in Isabela, Philippines (2023–2025).

The dashboard presents one production baseline and two experimental sensitivity screenings:

- A production relative SAR index using one fixed Cropland reference range.
- A rice-reference relative SAR index using the pooled historical potential-rice raw min/max range.
- An experimental implementation of the Wetness Index printed by Lovell et al. (2019), using QC historical-rice P1/P99 references.

Both approaches identify repeated SAR direction reversals for research screening. They do **not** directly measure water depth, prove wetting or drying, or confirm AWD adoption.

## Dashboard pages

1. **Method** — equations, reference choices, workflow, and limitations.
2. **Whole region** — switch between production and rice-reference relative-index results across the AOI.
3. **Participating areas** — switch between both relative-index results inside supplied MARIIS, UCRIS, and MRIS fields.
4. **WI · Whole region** — experimental Lovell-WI regional results and numerical eligibility.
5. **WI · Participating areas** — searchable field-level time series and baseline comparisons.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Study scope

- Sentinel-1A descending orbit R032.
- 88 acquisition dates during 2023–2025, usually 12 days apart.
- AOI: the projected envelope of the supplied valid fields plus a 100 m buffer; this is not the whole province of Isabela.
- Cropping calendars use Lex's 2026 irrigation-authority summary repeated over 2023–2025 as an explicit assumption.
- Public field data include Field IDs, locations, field-level summary results, and field-level time series.

## Data included and excluded

This release contains only derived, dashboard-facing tables, map images, the potential-rice support raster, and supplied-field system outlines. The large field time-series table is split into smaller Parquet shards to stay below GitHub's per-file limit.

The release excludes:

- environment files and credentials;
- the Pangasinan water-level SQL database;
- raw and intermediate Sentinel-1 GeoTIFFs;
- computation checkpoints and temporary files.

See [Data provenance](docs/data-provenance.md), the [Step 35 WI report](docs/step35-technical-report.md), and the [Step 36 rice-reference report](docs/step36-technical-report.md) for details.

## Scientific interpretation

The results are best described as **potential AWD-like SAR temporal patterns for pre-intervention prioritization**. Lower β⁰ is provisionally treated as wetter-like and higher β⁰ as drier-like, but canopy structure, crop stage, harvest, rainfall, surface roughness, mixed pixels, and other land conditions can also change the radar signal. Local Isabela water-level observations are not available for direct hydrological validation.

## Citation

Methodological inspiration: Lovell, D. et al. (2019), “Identifying Alternative Wetting and Drying (AWD) Adoption in the Vietnamese Mekong River Delta: A Change Detection Approach,” *ISPRS International Journal of Geo-Information*, 8(7), 312. https://doi.org/10.3390/ijgi8070312
