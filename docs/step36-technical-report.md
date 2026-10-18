# Step 36 — Rice-domain raw-min/max relative-index sensitivity

## Configuration

- Reference population: Open-SEA-Rice-10 historical potential-rice support intersected with WorldCover Cropland.
- Fixed pooled 2023–2025 endpoints: **-44.826462 dB** and **24.131746 dB**.
- Application domain: the unchanged production fixed-support Cropland domain.
- Formula: `I_rice_raw = clip((U_rice - beta_t) / (U_rice - L_rice), 0, 1)`.
- P80 threshold: **0.0468**.
- P90 threshold: **0.0621**.

## Reuse and numerical precision

The branch reuses the verified Step 23 index stack stored at 0.0001 resolution,
reconstructs each pixel's position on the production beta range, and applies the
rice-domain endpoints through a deterministic lookup table.  The propagated
reference-index quantization bound is approximately **0.0000528**
index units.  No Sentinel-1 data were redownloaded and the 3x3-filtered source
support was not changed.

## Result inventory

- 16 whole-region window/threshold summaries.
- 32 participating-system window/threshold summaries.
- P90 whole-region 2+ reversal share range: 0.000%–14.673%.
- P90 participating-area 2+ reversal share range: 2.215%–20.980%.

## Interpretation

This is a reference-range sensitivity result, not an independently validated
wetness product.  Step 31 found that the raw endpoints are valid processed
observations but are not representative validated wet/dry anchors.  Because this
formulation is a monotonic linear rescaling of the same beta time series, change
directions are largely preserved; differences arise from endpoint-dependent
clipping, quantization, and the independently derived P80/P90 thresholds.  The
results remain potential AWD-like SAR patterns, not measured water levels or
confirmed AWD adoption.
