"""Calendar-core reversal timing sensitivity; separate from the baseline classifier."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

import release_data as d


DATA_DIR = d.DATA / "calendar_core"
SEGMENT_COLORS = {"early boundary": "#D99438", "calendar-core": "#318AB5", "late boundary": "#B87045"}
REVERSAL_COLORS = {"0": "#D8C3A5", "1": "#DCEEF7", "2": "#92C9E2", "3": "#4B9CC5", "4": "#216B9A", ">=5": "#0E3F67"}


def _calendar_window(row, days):
    start = pd.Timestamp(row.season_start).date()
    end = pd.Timestamp(row.season_end_exclusive).date()
    core_start = start + pd.Timedelta(days=days)
    core_end = end - pd.Timedelta(days=days)
    return pd.DataFrame({"segment": ["Early boundary", "Calendar-core", "Late boundary"],
                         "start": [start, core_start, core_end],
                         "end": [core_start, core_end, end],
                         "colour": ["#D99438", "#318AB5", "#B87045"]})


def _calendar_figure(row, days):
    blocks = _calendar_window(row, days)
    fig = go.Figure()
    for record in blocks.itertuples():
        duration_ms = (pd.Timestamp(record.end) - pd.Timestamp(record.start)).total_seconds() * 1000
        fig.add_trace(go.Bar(x=[duration_ms], base=[record.start], y=["Assumed irrigation-system calendar"],
                             orientation="h", marker_color=record.colour, name=record.segment,
                             hovertemplate=f"{record.segment}<br>{record.start} to {record.end}<extra></extra>"))
    fig.update_layout(template="plotly_white", barmode="stack", height=190, margin=dict(l=20, r=20, t=15, b=25),
                      legend=dict(orientation="h", y=1.25, x=.5, xanchor="center"),
                      xaxis_title="Calendar date", yaxis_visible=False)
    fig.update_xaxes(type="date")
    return fig


def _load():
    required = [DATA_DIR / "summary.parquet", DATA_DIR / "event_timing.parquet", DATA_DIR / "retention.parquet"]
    if not all(path.exists() for path in required):
        return None
    return tuple(pd.read_parquet(path) for path in required)


def _reversal_donut(full, core):
    categories = ["0", "1", "2", "3", "4", ">=5"]
    column = {"0": "pixels_0_reversals", "1": "pixels_1_reversals", "2": "pixels_2_reversals",
              "3": "pixels_3_reversals", "4": "pixels_4_reversals", ">=5": "pixels_ge5_reversals"}
    fig = make_subplots(rows=1, cols=2, specs=[[{"type": "domain"}, {"type": "domain"}]],
                        subplot_titles=["Full season · no boundary exclusion", "Calendar core · boundary period excluded"])
    for position, (label, row) in enumerate((("Full season", full), ("Calendar core", core)), 1):
        values = [int(row[column[item]]) for item in categories]
        total = sum(values)
        percentages = [100 * value / total if total else 0 for value in values]
        fig.add_trace(go.Pie(labels=[f"{item} reversals" if item != ">=5" else "≥5 reversals" for item in categories],
                             values=values, hole=.60, sort=False, name=label, showlegend=position == 1,
                             marker=dict(colors=[REVERSAL_COLORS[item] for item in categories], line=dict(color="white", width=1)),
                             customdata=[[percent, value] for percent, value in zip(percentages, values)],
                             text=[f"{percent:.1f}%" if percent >= 1 else "" for percent in percentages],
                             textinfo="text", textposition="inside",
                             hovertemplate="%{label}<br>%{customdata[0]:.1f}% of participating-field cropland pixels<br>%{customdata[1]:,} pixels<extra></extra>"), row=1, col=position)
    fig.update_layout(template="plotly_white", height=410, margin=dict(l=15, r=15, t=55, b=60),
                      legend=dict(orientation="h", y=-.08, x=.5, xanchor="center", title="Reversal count"))
    return fig


def render():
    st.subheader("Appendix: Reversal timing & calendar-core sensitivity")
    st.caption("Participating fields only · separate exploratory diagnostic · does not change the production RI/WI baseline.")
    st.warning("The irrigation-system calendars are assumed reference windows, not field-level planting, harvest, or crop-stage observations. A calendar-core signal is not proof of AWD.")
    loaded = _load()
    if loaded is None:
        st.info("The calendar-core result tables have not yet been released to this public dashboard. The analysis is calculated separately from the existing baseline so the original pages remain unchanged.")
        st.markdown("""**What this sensitivity test reports**

- Full-season reversal counts, then independently recomputed calendar-core-only counts.
- Two boundary sensitivity settings: first/last **12** and **24 days** excluded.
- Actual valid adjacent changes and significant-direction comparison opportunities alongside reversal rates.
- Whether full-season ≥2/≥3/≥4/≥5 reversal pixels retain that count in the restricted calendar-core window.

The comparison is about **persistence of repeated SAR signal reversals after a calendar-boundary exclusion**. It is not an AWD classification or a confirmed hydrological interpretation.""")
        return

    summary, timing, retention = loaded
    system = st.selectbox("Irrigation system", sorted(summary.system.unique()), key="core_system")
    season = st.radio("Cropping-season label", ["Dry", "Wet"], horizontal=True, key="core_season")
    method = st.radio("Signal index", ["RI", "WI"], horizontal=True, key="core_method")
    threshold = st.radio("Significant-change threshold", ["p90", "p80"], horizontal=True,
                         format_func=lambda x: "P90 · primary" if x == "p90" else "P80 · sensitivity", key="core_threshold")
    candidates = summary[(summary.system == system) & (summary.season == season)
                         & (summary.method == method) & (summary.threshold == threshold)]
    windows = candidates.drop_duplicates("window_id").sort_values("season_start")
    chosen = st.selectbox("Assumed calendar window", windows.window_id, format_func=dict(zip(windows.window_id, windows.season_year)).get)
    chosen_rows = candidates[candidates.window_id == chosen]
    boundary = st.radio("Boundary exclusion sensitivity", [12, 24], horizontal=True,
                        format_func=lambda x: f"First / last {x} days excluded", key="core_boundary")
    full = chosen_rows[chosen_rows.analysis.eq("full season")].iloc[0]
    core = chosen_rows[(chosen_rows.analysis.eq("calendar-core only")) & (chosen_rows.boundary_days == boundary)].iloc[0]

    st.markdown("### Assumed calendar segmentation")
    st.plotly_chart(_calendar_figure(full, boundary), width="stretch", config={"displayModeBar": False})
    st.caption("Orange and brown are the excluded calendar boundaries; blue is the retained calendar-core interval. Every pair used in the core result has both observation dates inside blue. Direction memory is reset at the blue boundary, so the core result is recalculated—not obtained by subtracting events.")

    st.markdown("### Full season versus calendar core")
    a, b, c, dcol = st.columns(4)
    a.metric("Full-season reversals", f"{int(full.reversals):,}")
    b.metric("Core-only reversals", f"{int(core.reversals):,}")
    c.metric("Full mean valid changes", f"{full.mean_valid_adjacent_changes:.1f}")
    dcol.metric("Core mean valid changes", f"{core.mean_valid_adjacent_changes:.1f}")
    st.caption(f"Both circles use the same denominator: **{int(full.pixels):,} participating-field cropland pixels**.")
    st.plotly_chart(_reversal_donut(full, core), width="stretch", config={"displayModeBar": False})
    st.caption("Both circles use the same reversal-count categories. The left circle uses the full assumed season; the right circle uses only pairs wholly inside the blue calendar-core interval, and recalculates the reversal sequence from zero. A shift toward 0–1 on the right means repeated signals were reduced by the boundary exclusion or by fewer observation opportunities.")
    category_columns = {"2": "pixels_2_reversals", "3": "pixels_3_reversals", "4": "pixels_4_reversals", ">=5": "pixels_ge5_reversals"}
    def detail(row):
        return " · ".join(f"{label}: {100 * int(row[column]) / int(row.pixels):.2f}%"
                          for label, column in category_columns.items())
    st.caption(f"Exact higher-count shares — Full season: {detail(full)} · Calendar core: {detail(core)}")

    st.markdown("### Key takeaway")
    change_reduction = 100 * (1 - core.mean_valid_adjacent_changes / full.mean_valid_adjacent_changes) if full.mean_valid_adjacent_changes else float("nan")
    window_label = str(full.season_year).replace(f"{system} · ", "", 1)
    st.info(
        f"For this assumed **{system} · {window_label}** window, the share of participating-field cropland "
        f"with **≥2 reversals** changes from **{full.percent_ge2:.1f}%** in the full assumed season to "
        f"**{core.percent_ge2:.1f}%** after excluding the first and last {boundary} days. "
        f"Mean valid adjacent changes decline from **{full.mean_valid_adjacent_changes:.1f}** to "
        f"**{core.mean_valid_adjacent_changes:.1f}** per pixel ({change_reduction:.0f}% fewer opportunities). "
        "The exclusion is a conservative sensitivity check for possible crop-establishment, harvest/transition, and assumed-calendar-edge effects, because field-specific planting and harvest dates are not available."
    )
    deliver = pd.DataFrame({
        "Metric": ["Pixels with ≥2 reversals", "Mean valid adjacent changes / pixel", "Reversals / valid adjacent change"],
        "Full assumed season": [f"{full.percent_ge2:.1f}%", f"{full.mean_valid_adjacent_changes:.1f}", f"{full.reversals_per_valid_change:.3f}"],
        "Calendar core": [f"{core.percent_ge2:.1f}%", f"{core.mean_valid_adjacent_changes:.1f}", f"{core.reversals_per_valid_change:.3f}"],
    })
    st.dataframe(deliver, hide_index=True, width="stretch")

    with st.expander("Coverage, exports and interpretation", expanded=False):
        coverage = pd.DataFrame({"Measure": ["Valid adjacent changes", "Significant changes", "Direction-comparison opportunities", "Reversals"],
                                 "Full season": [full.valid_adjacent_changes, full.significant_changes, full.direction_comparison_opportunities, full.reversals],
                                 "Calendar core": [core.valid_adjacent_changes, core.significant_changes, core.direction_comparison_opportunities, core.reversals]})
        st.markdown("**Why direct comparison needs coverage context**")
        st.dataframe(coverage, hide_index=True, width="stretch")
        st.caption("Reversals / valid change and reversals / direction-comparison opportunity are descriptive rates with different denominators; neither is an AWD probability.")
        st.dataframe(chosen_rows.sort_values(["analysis", "boundary_days"]), hide_index=True, width="stretch")
        selected_retention = retention[(retention.method == method) & (retention.threshold == threshold) & (retention.system == system)
                                       & (retention.season == season) & (retention.window_id == chosen) & (retention.boundary_days == boundary)]
        st.download_button("Download selected core-retention rows", selected_retention.to_csv(index=False), "calendar_core_retention.csv", "text/csv")
        st.markdown("Higher counts can also arise from crop structure, rainfall, surface moisture, or SAR scattering. Sentinel-1 sampling can miss actual changes. These results are therefore described as repeated RI/WI signal reversals and calendar-boundary sensitivity—not confirmed water-level changes or AWD adoption.")
