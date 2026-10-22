"""Calendar-core reversal timing sensitivity; separate from the baseline classifier."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import release_data as d


DATA_DIR = d.DATA / "calendar_core"
SEGMENT_COLORS = {"early boundary": "#D99438", "calendar-core": "#318AB5", "late boundary": "#B87045"}


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
        fig.add_trace(go.Bar(x=[(record.end - record.start).days], base=[record.start], y=["Assumed irrigation-system calendar"],
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


def render():
    st.subheader("Reversal timing & calendar-core sensitivity")
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
    st.caption("Every pair used in the calendar-core result has both observation dates inside the blue interval. Direction memory is reset at the interval boundary; the core result is not obtained by subtracting boundary events.")

    st.markdown("### Full season versus independently recalculated calendar core")
    a, b, c, dcol = st.columns(4)
    a.metric("Full-season reversals", f"{int(full.reversals):,}")
    b.metric("Core-only reversals", f"{int(core.reversals):,}")
    c.metric("Full mean valid changes", f"{full.mean_valid_adjacent_changes:.1f}")
    dcol.metric("Core mean valid changes", f"{core.mean_valid_adjacent_changes:.1f}")
    coverage = pd.DataFrame({"Measure": ["Valid adjacent changes", "Significant changes", "Direction-comparison opportunities", "Reversals"],
                             "Full season": [full.valid_adjacent_changes, full.significant_changes, full.direction_comparison_opportunities, full.reversals],
                             "Calendar core": [core.valid_adjacent_changes, core.significant_changes, core.direction_comparison_opportunities, core.reversals]})
    st.dataframe(coverage, hide_index=True, width="stretch")
    st.caption("Reversals / valid change and reversals / direction-comparison opportunity are descriptive rates with different denominators; neither is an AWD probability.")

    st.markdown("### 1. Do high-reversal pixels remain high-reversal pixels after boundary exclusion?")
    retained = retention[(retention.method == method) & (retention.threshold == threshold) & (retention.system == system)
                         & (retention.season == season) & (retention.window_id == chosen) & (retention.boundary_days == boundary)].copy()
    retained["Full-season criterion"] = "≥" + retained.threshold_reversals.astype(str) + " reversals"
    retained["Not retained"] = retained.full_pixels_ge - retained.retained_pixels_ge
    persistence = retained.melt(id_vars=["Full-season criterion", "full_pixels_ge", "retained_pixels_ge"],
                                value_vars=["retained_pixels_ge", "Not retained"], var_name="Core result", value_name="Pixels")
    persistence["Core result"] = persistence["Core result"].map({"retained_pixels_ge": "Still meets the same threshold in core", "Not retained": "Does not meet it in core"})
    persistence["Percent of full-season group"] = 100 * persistence.Pixels / persistence.full_pixels_ge
    fig = px.bar(persistence, x="Percent of full-season group", y="Full-season criterion", color="Core result", orientation="h",
                 barmode="stack", text="Percent of full-season group",
                 color_discrete_map={"Still meets the same threshold in core": "#318AB5", "Does not meet it in core": "#E7D8C1"},
                 custom_data=["Pixels", "full_pixels_ge"])
    fig.update_traces(texttemplate="%{text:.0f}%", textposition="inside",
                      hovertemplate="%{y}<br>%{fullData.name}<br>%{customdata[0]:,} of %{customdata[1]:,} full-season pixels (%{x:.1f}%)<extra></extra>")
    fig.update_layout(template="plotly_white", height=330, legend=dict(orientation="h", y=1.18, x=.5, xanchor="center"),
                      xaxis_title="Share of pixels that met the criterion in the full season (%)", yaxis_title=None,
                      margin=dict(l=35,r=15,t=50,b=35))
    fig.update_xaxes(range=[0, 100], gridcolor="#E7ECEB")
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    st.caption("Read each row from left to right. Example: among all pixels with **≥2 full-season reversals**, the blue share still has **≥2 reversals** when the first and last calendar days are excluded and the sequence is recalculated from scratch.")

    st.markdown("### 2. Where did full-season reversal events occur? · 12-day boundary definition")
    event = timing[(timing.method == method) & (timing.threshold == threshold) & (timing.system == system)
                   & (timing.season == season) & (timing.window_id == chosen) & (timing.boundary_days == 12)
                   & (timing.segment != "cross_segment_history")].copy()
    event["Segment"] = event.segment.map({"early boundary": "Early boundary", "calendar-core": "Calendar core", "late boundary": "Late boundary"})
    total_events = int(event.reversal_events.sum())
    fig2 = px.bar(event, x="percent_of_full_events", y=["All full-season reversal events"] * len(event), color="segment",
                  orientation="h", text="percent_of_full_events", color_discrete_map=SEGMENT_COLORS,
                  custom_data=["reversal_events", "Segment"])
    fig2.update_traces(texttemplate="%{text:.1f}%", textposition="inside",
                       hovertemplate="%{customdata[1]}<br>%{customdata[0]:,} of " + f"{total_events:,}" + " events (%{x:.1f}%)<extra></extra>")
    fig2.update_layout(template="plotly_white", height=250, legend=dict(orientation="h", y=1.2, x=.5, xanchor="center"),
                       xaxis_title="Share of all full-season reversal events (%)", yaxis_visible=False,
                       margin=dict(l=15,r=15,t=55,b=35))
    fig2.update_xaxes(range=[0, 100], gridcolor="#E7ECEB")
    st.plotly_chart(fig2, width="stretch", config={"displayModeBar": False})
    cross = timing[(timing.method == method) & (timing.threshold == threshold) & (timing.system == system)
                   & (timing.season == season) & (timing.window_id == chosen) & (timing.boundary_days == 12)
                   & (timing.segment == "cross_segment_history")]
    cross_count = int(cross.reversal_events.iloc[0]) if len(cross) else 0
    st.caption(f"This chart has one denominator: all **{total_events:,} full-season reversal events**. The event is assigned to the later significant change that triggered the direction switch. {cross_count:,} event(s) had the preceding significant-change history in a different segment; these are retained, not removed.")

    with st.expander("Coverage, exports and interpretation", expanded=False):
        st.dataframe(chosen_rows.sort_values(["analysis", "boundary_days"]), hide_index=True, width="stretch")
        st.download_button("Download selected timing rows", event.to_csv(index=False), "reversal_event_timing_summary.csv", "text/csv")
        st.download_button("Download selected core-retention rows", retained.to_csv(index=False), "calendar_core_retention.csv", "text/csv")
        st.markdown("Higher counts can also arise from crop structure, rainfall, surface moisture, or SAR scattering. Sentinel-1 sampling can miss actual changes. These results are therefore described as repeated RI/WI signal reversals and calendar-boundary sensitivity—not confirmed water-level changes or AWD adoption.")
