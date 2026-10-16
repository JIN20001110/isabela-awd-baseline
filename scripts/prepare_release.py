"""Build the public dashboard data bundle from the full local research workspace.

This script is intentionally explicit: it copies only derived, app-facing files and
never copies credentials, SQL records, raw Sentinel-1 rasters, or checkpoints.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import numpy as np
from PIL import Image
import rasterio


RELEASE = Path(__file__).resolve().parents[1]
SOURCE = RELEASE.parent

SRC17 = SOURCE / "17o-streamlit_39597a1e0c0a"
SRC26 = SOURCE / "26o-system_season_reversals_ab28d084ea89"
SRC28 = SOURCE / "28o-regional_season_reversals_6e40c2b942fc"
SRC29 = SOURCE / "29o-public_rice_assessment_3b7c334c8af8"
SRC35 = SOURCE / "35o-wi_baseline_89aacc7bbd1b"

STATIC23 = SOURCE / "static/23o-regional_change_ae54eb9901a8"
STATIC26 = SOURCE / "static/26o-system_season_reversals_ab28d084ea89"
STATIC28 = SOURCE / "static/28o-regional_season_reversals_6e40c2b942fc"
STATIC35 = SOURCE / "static/35o-wi_baseline_89aacc7bbd1b"


def copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def copy_pngs(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for item in source.glob("*.png"):
        copy(item, destination / item.name)


def shard_field_timeseries() -> None:
    source = SRC35 / "35o-field_timeseries.parquet"
    target = RELEASE / "data/field_timeseries"
    target.mkdir(parents=True, exist_ok=True)
    for item in target.glob("*.parquet"):
        item.unlink()

    index = pd.read_parquet(SRC17 / "17o-field_index.parquet", columns=["field_uid", "field_bucket"])
    bucket_by_field = dict(zip(index.field_uid.astype(str), index.field_bucket.astype(int)))
    parquet = pq.ParquetFile(source)
    writers: dict[int, pq.ParquetWriter] = {}
    try:
        for batch in parquet.iter_batches(batch_size=100_000):
            frame = batch.to_pandas()
            frame["release_bucket"] = frame.field_uid.astype(str).map(bucket_by_field)
            if frame.release_bucket.isna().any():
                missing = frame.loc[frame.release_bucket.isna(), "field_uid"].unique()[:5]
                raise ValueError(f"Field bucket missing for: {missing}")
            for bucket, part in frame.groupby("release_bucket", sort=False):
                table = pa.Table.from_pandas(part.drop(columns="release_bucket"), preserve_index=False)
                bucket = int(bucket)
                if bucket not in writers:
                    path = target / f"part-{bucket:02d}.parquet"
                    writers[bucket] = pq.ParquetWriter(path, table.schema, compression="zstd", compression_level=9)
                writers[bucket].write_table(table)
    finally:
        for writer in writers.values():
            writer.close()


def build_rice_overlay(height: int = 1200) -> None:
    with rasterio.open(SRC29 / "29o-potential_rice_within_current_cropland.tif") as source:
        scale = height / source.height
        width = max(1, int(round(source.width * scale)))
        values = source.read(
            1,
            out_shape=(height, width),
            resampling=rasterio.enums.Resampling.nearest,
        )
    rgba = np.zeros((height, width, 4), dtype="uint8")
    rgba[values == 1] = [239, 198, 70, 125]
    Image.fromarray(rgba).save(RELEASE / "static/rice_overlay.png", optimize=True)


def main() -> None:
    copy(SRC17 / "17o-field_index.parquet", RELEASE / "data/field_index.parquet")
    copy(SOURCE / "17o-system_field_coverage.geojson", RELEASE / "data/system_field_coverage.geojson")
    copy(SRC29 / "29o-potential_rice_within_current_cropland.tif", RELEASE / "data/public_rice_support.tif")
    copy(STATIC23 / "context.png", RELEASE / "static/context.png")
    build_rice_overlay()

    for source_name, target_name in {
        "26o-window_summary.parquet": "window_summary.parquet",
        "26o-area_distribution.parquet": "area_distribution.parquet",
        "26o-field_summary.parquet": "field_summary.parquet",
        "26o-map_index.json": "map_index.json",
    }.items():
        copy(SRC26 / source_name, RELEASE / "data/production/participating_areas" / target_name)

    for source_name, target_name in {
        "28o-window_summary.parquet": "window_summary.parquet",
        "28o-area_distribution.parquet": "area_distribution.parquet",
        "28o-map_index.json": "map_index.json",
    }.items():
        copy(SRC28 / source_name, RELEASE / "data/production/whole_region" / target_name)

    for source_name, target_name in {
        "35o-window_summary.parquet": "window_summary.parquet",
        "35o-reversal_distribution.parquet": "reversal_distribution.parquet",
        "35o-field_season_summary.parquet": "field_season_summary.parquet",
        "35o-pair_diagnostics.parquet": "pair_diagnostics.parquet",
        "35o-observation_eligibility.parquet": "observation_eligibility.parquet",
        "35o-map_index.json": "map_index.json",
        "35o-baseline_comparison.csv": "baseline_comparison.csv",
    }.items():
        copy(SRC35 / source_name, RELEASE / "data/wi" / target_name)

    copy(SRC35 / "35o-technical_report.md", RELEASE / "docs/step35-technical-report.md")
    copy(SRC35 / "35o-validation.json", RELEASE / "docs/step35-validation.json")
    copy_pngs(STATIC26, RELEASE / "static/production/participating_areas")
    copy_pngs(STATIC28, RELEASE / "static/production/whole_region")
    copy_pngs(STATIC35, RELEASE / "static/wi")
    shard_field_timeseries()


if __name__ == "__main__":
    main()
