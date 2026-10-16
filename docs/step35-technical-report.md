# Step 35 — Lovell-inspired WI-based baseline screening

## Result

This is an additional experimental baseline, not a replacement for the production relative-SAR screening. The primary dB branch uses the unchanged printed Lovell equation with fixed Step-32 QC-rice pooled P1/P99 endpoints (-15.117908/-2.682668 dB). P90 is the primary WI threshold (4.697); P80 (2.534) is the sensitivity threshold.

Across complete common regional windows, the P90 share of eligible Cropland pixels with at least one mathematical WI reversal ranged from 7.66% to 39.68%. These are potential AWD-like SAR patterns, not confirmed AWD adoption. A field or pixel with no detected reversal is distinct from one with insufficient eligible observations.

## Eligibility and numerical handling

Every observation is retained in one of five statuses: eligible stable, near-singular, below low, above high, or missing/invalid. 22,281,557 of 1,072,356,296 full-Cropland pixel-date observations were excluded from the conservative dB screening. No WI value was clipped, zero-filled, or bridged across an excluded acquisition. A valid reversal requires consecutive original Sentinel-1 transitions; neutral eligible transitions retain the last significant direction, matching the production convention.

The dB and linear-power implementations are separate. Their thresholds are estimated from their own eligible change distributions. The publication does not resolve which numerical unit was used, so the dB branch is primary only for consistency with Steps 33–34, not because it has been verified as the authors' implementation.

## Comparison with Baseline A

The matched field-season table compares the frozen production relative index and WI using the same field aggregate dates and calendar windows. Differences cannot be attributed only to the nonlinear equation: the formulas, reference domains, endpoints, exclusions, and threshold distributions also differ. A compact category table reports fields selected by both, either one, or neither baseline.

## Interpretation limits

The historical rice layer is supporting evidence, not confirmation of rice cultivation in 2023–2025. Lower beta0 is provisionally treated as wetward and higher beta0 as dryward, but crop growth, roughness, rainfall, mixed pixels, and other scattering effects remain. WI is not soil-moisture percentage, does not measure water-table depth, and cannot supply exact irrigation dates or true AWD cycle counts.

## Upper-tail numerical-risk diagnostic

Across the full Cropland threshold population, 24,953,907 of 98,486,646 P90-significant eligible changes (25.34%) have at least one endpoint in the nearest 5% below the high reference. The conservative near-singular tolerance still excludes the formal singular neighborhood, but this result shows that the nonlinear upper tail remains materially influenced by proximity to the high reference. It is a limitation, not evidence of stronger hydrological change.

## Participating-field P90 summary

Both acquisitions of every counted transition fall inside the stated cropping window. Percentages below use eligible field-seasons (at least two valid adjacent changes) as the denominator; they are screening percentages, not AWD adoption rates.

| System | Season | Field-seasons | Eligible | Candidates | Candidate % of eligible |
|---|---:|---:|---:|---:|---:|
| MARIIS | Dry | 39,628 | 37,926 | 4,369 | 11.52% |
| MARIIS | Wet | 59,442 | 56,889 | 5,377 | 9.45% |
| MRIS | Dry | 5,736 | 5,730 | 198 | 3.46% |
| MRIS | Wet | 5,736 | 5,730 | 737 | 12.86% |
| UCRIS | Dry | 8,634 | 8,632 | 625 | 7.24% |
| UCRIS | Wet | 12,951 | 12,948 | 1,181 | 9.12% |
