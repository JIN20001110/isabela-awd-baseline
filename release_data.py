"""Read-only helpers for the public Streamlit release."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pyarrow.dataset as ds


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
STATIC = ROOT / "static"

CALENDAR = {
    "MARIIS": {"Dry": (9, 3), "Wet": (5, 11)},
    "UCRIS": {"Dry": (11, 5), "Wet": (7, 1)},
    "MRIS": {"Dry": (1, 6), "Wet": (8, 1)},
}


def metadata() -> dict:
    return json.loads((DATA / "metadata.json").read_text())


def map_index(section: str) -> list[dict]:
    return json.loads((DATA / section / "map_index.json").read_text())


def table(section: str, filename: str) -> pd.DataFrame:
    return pd.read_parquet(DATA / section / filename)


def field_index() -> pd.DataFrame:
    return pd.read_parquet(DATA / "field_index.parquet")


def field_series(field_uid: str) -> pd.DataFrame:
    dataset = ds.dataset(str(DATA / "field_timeseries"), format="parquet")
    return dataset.to_table(filter=ds.field("field_uid") == str(field_uid)).to_pandas()


def coverage_geojson() -> dict:
    return json.loads((DATA / "system_field_coverage.geojson").read_text())
