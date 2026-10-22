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

    st.markdown("### Do repeated reversals persist inside the calendar core?")
    retained = retention[(retention.method == method) & (retention.threshold == threshold) & (retention.system == system)
                         & (retention.season == season) & (retention.window_id == chosen) & (retention.boundary_days == boundary)].copy()
    retained["Category"] = "Full-season ≥" + retained.threshold_reversals.astype(str)
    fig = px.bar(retained, x="Category", y="retained_percent_of_full_ge", text="retained_percent_of_full_ge",
                 color="Category", color_discrete_sequence=["#B8DDEC", "#7AB8D4", "#318AB5", "#155A8A"])
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(template="plotly_white", height=360, showlegend=False, yaxis_title="Retained in core (% of full-season category)", xaxis_title=None, margin=dict(l=35,r=15,t=20,b=25))
    fig.update_yaxes(range=[0, 105], gridcolor="#E7ECEB")
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    st.markdown("### Timing of full-season reversal events")
    event = timing[(timing.method == method) & (timing.threshold == threshold) & (timing.system == system)
                   & (timing.season == season) & (timing.window_id == chosen) & (timing.boundary_days == 12)
                   & (timing.segment != "cross_segment_history")].copy()
    event["segment_label"] = event.segment.str.replace("boundary", "boundary").str.title()
    fig2 = px.bar(event, x="segment_label", y="reversal_events", color="segment",
                  color_discrete_map=SEGMENT_COLORS, text="percent_of_full_events")
    fig2.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig2.update_layout(template="plotly_white", height=350, showlegend=False, xaxis_title=None, yaxis_title="Full-season reversal events", margin=dict(l=35,r=15,t=20,b=25))
    st.plotly_chart(fig2, width="stretch", config={"displayModeBar": False})
    st.caption("The timing panel assigns an event to the later significant change that triggered its direction switch. Events with history from another segment are retained and reported separately in the exported timing table.")

    with st.expander("Coverage, exports and interpretation", expanded=False):
        st.dataframe(chosen_rows.sort_values(["analysis", "boundary_days"]), hide_index=True, width="stretch")
        st.download_button("Download selected timing rows", event.to_csv(index=False), "reversal_event_timing_summary.csv", "text/csv")
        st.download_button("Download selected core-retention rows", retained.to_csv(index=False), "calendar_core_retention.csv", "text/csv")
        st.markdown("Higher counts can also arise from crop structure, rainfall, surface moisture, or SAR scattering. Sentinel-1 sampling can miss actual changes. These results are therefore described as repeated RI/WI signal reversals and calendar-boundary sensitivity—not confirmed water-level changes or AWD adoption.")
