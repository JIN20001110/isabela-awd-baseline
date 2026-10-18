"""Direct visual comparison of the three fixed-reference screening versions."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

import release_data as d


CATEGORY_COLORS = {
    "Insufficient": "#9CA3A5",
    "0": "#D8C3A5",
    "1": "#DCEEF7",
    "2": "#72B7D6",
    "3+": "#155A8A",
}
METHOD_COLORS = {
    "Production RI": "#277DA1",
    "Rice-reference RI": "#23866F",
    "Experimental Lovell WI": "#6B5AA6",
}
REFERENCES = {
    "Production RI": "Cropland pooled raw min/max",
    "Rice-reference RI": "Historical-rice ∩ Cropland pooled raw min/max",
    "Experimental Lovell WI": "QC historical-rice pooled P1/P99",
}


def _linear_result(branch: str, scope_mode: str, threshold: str, window_id: str) -> dict:
    method = "Production RI" if branch == "production" else "Rice-reference RI"
    section = f"{branch}/{'whole_region' if scope_mode == 'All area' else 'participating_areas'}"
    summary = d.table(section, "window_summary.parquet")
    row = summary[(summary.threshold == threshold) & (summary.window_id == window_id)].iloc[0]
    distribution = d.table(section, "area_distribution.parquet")
    selected = distribution[(distribution.threshold == threshold) & (distribution.window_id == window_id)]
    pixels = {str(x.reversal_group): int(x.cropland_pixels) for x in selected.itertuples()}
    domain_pixels = int(sum(pixels.values()))
    return {
        "method": method,
        "reference": REFERENCES[method],
        "threshold": float(row.threshold_value),
        "domain_pixels": domain_pixels,
        "eligible_pixels": domain_pixels,
        "insufficient_pixels": 0,
        "pixels": {"Insufficient": 0, **{x: pixels.get(x, 0) for x in ["0", "1", "2", "3+"]}},
        "pct_0": float(row.percent_0_reversals),
        "pct_1": float(row.percent_1_reversal),
        "pct_2": float(row.percent_2_reversals),
        "pct_3plus": float(row.percent_3plus_reversals),
        "pct_2plus": float(row.percent_2plus_reversals),
        "mean_reversals": float(row.mean_reversals),
        "mean_significant": float(row.mean_significant_transitions),
        "pairs": int(row.pairs),
    }


def _wi_result(scope: str, threshold: str, window_id: str) -> dict:
    windows = d.table("wi", "window_summary.parquet")
    match = windows[(windows.scope == scope) & (windows.threshold == threshold)
                    & (windows.window_id == window_id)]
    if match.empty:
        raise KeyError((scope, threshold, window_id))
    row = match.iloc[0]
    distribution = d.table("wi", "reversal_distribution.parquet")
    selected = distribution[(distribution.scope == scope) & (distribution.threshold == threshold)
                            & (distribution.window_id == window_id)]
    pixels = {str(x.reversal_group): int(x.pixels) for x in selected.itertuples()}
    eligible = int(row.eligible_pixels)

    def eligible_percent(group: str) -> float:
        return 100 * pixels.get(group, 0) / eligible if eligible else np.nan

    return {
        "method": "Experimental Lovell WI",
        "reference": REFERENCES["Experimental Lovell WI"],
        "threshold": float(row.threshold_value),
        "domain_pixels": int(row.domain_pixels),
        "eligible_pixels": eligible,
        "insufficient_pixels": int(row.insufficient_pixels),
        "pixels": {x: pixels.get(x, 0) for x in ["Insufficient", "0", "1", "2", "3+"]},
        "pct_0": eligible_percent("0"),
        "pct_1": eligible_percent("1"),
        "pct_2": eligible_percent("2"),
        "pct_3plus": eligible_percent("3+"),
        "pct_2plus": eligible_percent("2") + eligible_percent("3+") if eligible else np.nan,
        "mean_reversals": float(row.reversals) / eligible if eligible else np.nan,
        "mean_significant": float(row.significant_changes) / eligible if eligible else np.nan,
        "pairs": int(row.pairs),
    }


def _results(scope_mode: str, system: str | None, threshold: str, window_id: str) -> list[dict]:
    scope = "Full Cropland AOI" if scope_mode == "All area" else system
    return [
        _linear_result("production", scope_mode, threshold, window_id),
        _linear_result("rice_raw", scope_mode, threshold, window_id),
        _wi_result(scope, threshold, window_id),
    ]


def _donuts(results: list[dict]) -> go.Figure:
    fig = make_subplots(
        rows=1, cols=3,
        specs=[[{"type": "domain"}, {"type": "domain"}, {"type": "domain"}]],
        subplot_titles=[x["method"] for x in results],
    )
    order = ["Insufficient", "0", "1", "2", "3+"]
    for col, result in enumerate(results, 1):
        used = order
        values = [result["pixels"][x] for x in used]
        labels = ["Insufficient" if x == "Insufficient" else f"{x} reversals" for x in used]
        custom = [[100 * value / result["domain_pixels"], value * .01] for value in values]
        fig.add_trace(go.Pie(
            labels=labels, values=values, hole=.58, sort=False,
            marker=dict(colors=[CATEGORY_COLORS[x] for x in used], line=dict(color="white", width=1)),
            customdata=custom, textinfo="percent", textposition="inside",
            hovertemplate="%{label}<br>%{customdata[0]:.2f}% of full domain"
                          "<br>%{customdata[1]:,.1f} ha<extra></extra>",
            name=result["method"], legendgroup="categories", showlegend=col == 1,
        ), row=1, col=col)
    fig.update_layout(
        template="plotly_white", height=430, margin=dict(l=20, r=20, t=65, b=70),
        legend=dict(title="Reversal category", orientation="h", y=-.08, x=.5, xanchor="center"),
        font=dict(family="Arial, sans-serif", size=12),
    )
    return fig


def _comparison_table(results: list[dict]) -> pd.DataFrame:
    rows = []
    for result in results:
        insufficient = 100 * result["insufficient_pixels"] / result["domain_pixels"]
        rows.append({
            "Version": result["method"],
            "Reference": result["reference"],
            "Threshold": result["threshold"],
            "Eligible area (ha)": result["eligible_pixels"] * .01,
            "Insufficient (% domain)": insufficient,
            "0 reversals (% eligible)": result["pct_0"],
            "1 reversal (% eligible)": result["pct_1"],
            "2 reversals (% eligible)": result["pct_2"],
            "3+ reversals (% eligible)": result["pct_3plus"],
            "2+ reversals (% eligible)": result["pct_2plus"],
            "Mean reversals": result["mean_reversals"],
        })
    return pd.DataFrame(rows)


def _across_windows(scope_mode: str, system: str | None, threshold: str,
                    available: pd.DataFrame) -> go.Figure:
    records = []
    ordered = available.sort_values("start").drop_duplicates("window_id")
    for row in ordered.itertuples():
        for result in _results(scope_mode, system, threshold, row.window_id):
            records.append({"Window": row.label, "Start": row.start, "Version": result["method"],
                            "2+ reversals (% eligible)": result["pct_2plus"]})
    frame = pd.DataFrame(records)
    fig = go.Figure()
    for method in METHOD_COLORS:
        part = frame[frame.Version == method]
        dash = "dot" if method == "Rice-reference RI" else "solid"
        fig.add_trace(go.Scatter(
            x=part.Window, y=part["2+ reversals (% eligible)"], mode="lines+markers",
            name=method, line=dict(color=METHOD_COLORS[method], width=3, dash=dash),
            marker=dict(size=9), connectgaps=False,
            hovertemplate="%{x}<br>%{y:.2f}% with 2+ reversals<extra>%{fullData.name}</extra>",
        ))
    fig.update_layout(
        template="plotly_white", height=440, margin=dict(l=35, r=20, t=35, b=75),
        yaxis_title="Pixels with 2+ reversals (% of eligible)", xaxis_title=None,
        legend=dict(orientation="h", y=1.13, x=.5, xanchor="center"),
        hovermode="x unified", font=dict(family="Arial, sans-serif", size=12),
    )
    fig.update_xaxes(tickangle=-20, showgrid=False)
    fig.update_yaxes(gridcolor="#E6ECEA", rangemode="tozero")
    return fig


def render():
    st.subheader("Comparison · All versions")
    st.caption("Compare the same threshold quantile, spatial support and cropping window across Production RI, Rice-reference RI and the experimental Lovell WI.")

    scope_mode = st.radio("Spatial scale", ["All area", "Participating fields"], horizontal=True,
                          key="compare_scope")
    threshold = st.radio("Change threshold", ["p90", "p80"], horizontal=True,
                         format_func=lambda x: "P90 · primary" if x == "p90" else "P80 · sensitivity",
                         key="compare_threshold")

    system = None
    if scope_mode == "All area":
        base = d.table("production/whole_region", "window_summary.parquet")
        period = st.radio("Period", ["Wet core", "Dry core", "November transition"],
                          horizontal=True, key="compare_period")
        available = base[(base.threshold == threshold) & (base.season == period)].copy()
    else:
        system = st.selectbox("Irrigation system", list(d.CALENDAR), key="compare_system")
        season = st.radio("Cropping season", ["Dry", "Wet"], horizontal=True,
                          key="compare_season")
        base = d.table("production/participating_areas", "window_summary.parquet")
        available = base[(base.threshold == threshold) & (base.system == system)
                         & (base.season == season)].copy()

    options = available.drop_duplicates("window_id")
    chosen = st.selectbox("Window", options.window_id.tolist(),
                          format_func=dict(zip(options.window_id, options.label)).get,
                          key="compare_window")
    results = _results(scope_mode, system, threshold, chosen)

    st.markdown("### Selected window · three versions at a glance")
    metric_columns = st.columns(3)
    for column, result in zip(metric_columns, results):
        with column:
            st.markdown(f"**{result['method']}**")
            display = "N/A" if pd.isna(result["pct_2plus"]) else f"{result['pct_2plus']:.2f}%"
            st.metric("2+ reversals", display)
            st.caption(f"Threshold {result['threshold']:.4f} · {result['reference']}")

    st.plotly_chart(_donuts(results), width="stretch")
    st.caption("Each circle uses the same reversal colors: light brown = 0, very light blue = 1, light blue = 2, dark blue = 3+. Grey appears only where WI observations are insufficient or numerically excluded. Circle percentages use each method's full spatial domain.")

    table = _comparison_table(results)
    st.dataframe(
        table.style.format({
            "Threshold": "{:.4f}", "Eligible area (ha)": "{:,.2f}",
            "Insufficient (% domain)": "{:.3f}", "0 reversals (% eligible)": "{:.2f}",
            "1 reversal (% eligible)": "{:.2f}", "2 reversals (% eligible)": "{:.2f}",
            "3+ reversals (% eligible)": "{:.2f}", "2+ reversals (% eligible)": "{:.2f}",
            "Mean reversals": "{:.3f}",
        }),
        hide_index=True, width="stretch",
    )

    st.markdown("### Pattern across comparable windows")
    st.plotly_chart(_across_windows(scope_mode, system, threshold, available), width="stretch")

    linear_gap = abs(results[0]["pct_2plus"] - results[1]["pct_2plus"])
    st.info(
        f"For the selected window, the two linear RI versions differ by only **{linear_gap:.3f} percentage points** in the 2+ reversal share. "
        "They use the same β⁰ observations and linear formula, with different fixed endpoints and independently scaled percentile thresholds. "
        "WI is a nonlinear transformation with additional numerical eligibility rules, so its percentages are diagnostic rather than a direct accuracy ranking."
    )
    st.warning("Repeated reversals are SAR screening patterns—not measured water-level changes, complete AWD cycles, or confirmed AWD adoption.")
