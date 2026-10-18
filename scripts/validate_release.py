"""Fail fast when the public release is incomplete or contains unsafe files."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pyarrow.dataset as ds


ROOT = Path(__file__).resolve().parents[1]


def require(path: Path) -> None:
    if not path.exists():
        raise AssertionError(f"Missing: {path.relative_to(ROOT)}")


def main() -> None:
    required = [
        ROOT / "app.py",
        ROOT / "comparison_page.py",
        ROOT / "data/metadata.json",
        ROOT / "data/field_index.parquet",
        ROOT / "data/system_field_coverage.geojson",
        ROOT / "data/public_rice_support.tif",
        ROOT / "data/wi/field_season_summary.parquet",
        ROOT / "static/context.png",
        ROOT / "static/rice_overlay.png",
    ]
    for item in required:
        require(item)

    forbidden_names = {".env", "kit-readings-20260303.sql", "secrets.toml"}
    found = [p for p in ROOT.rglob("*") if p.is_file() and p.name in forbidden_names]
    if found:
        raise AssertionError(f"Forbidden files present: {found}")

    oversized = [p for p in ROOT.rglob("*") if p.is_file() and p.stat().st_size >= 100_000_000]
    if oversized:
        raise AssertionError(f"GitHub-incompatible files: {oversized}")

    meta = json.loads((ROOT / "data/metadata.json").read_text())
    assert meta["study"]["observation_dates"] == 88
    rice_raw = meta["rice_raw_relative_index"]["references"]
    assert rice_raw["low_db"] < rice_raw["high_db"]
    assert meta["rice_raw_relative_index"]["thresholds"]["p80"]["threshold"] < meta["rice_raw_relative_index"]["thresholds"]["p90"]["threshold"]
    assert meta["wi"]["references"]["low_db"] < meta["wi"]["references"]["high_db"]

    field_index = pd.read_parquet(ROOT / "data/field_index.parquet")
    assert len(field_index) == 26_410
    series = ds.dataset(str(ROOT / "data/field_timeseries"), format="parquet")
    assert series.count_rows() == 2_291_784

    for section, expected in [
        ("production/whole_region", 16),
        ("production/participating_areas", 32),
        ("rice_raw/whole_region", 16),
        ("rice_raw/participating_areas", 32),
        ("wi", 64),
    ]:
        table = pd.read_parquet(ROOT / "data" / section / "window_summary.parquet")
        assert len(table) == expected
        records = json.loads((ROOT / "data" / section / "map_index.json").read_text())
        static = ROOT / "static" / section
        for record in records:
            require(static / record["png"])

    print("Public release validation passed.")


if __name__ == "__main__":
    main()
