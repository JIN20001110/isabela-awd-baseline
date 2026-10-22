"""Step 35 WI whole-region page; read-only and separate from production pages."""
from __future__ import annotations

import base64
from pathlib import Path

import folium
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import release_data as d

COLORS = {"Insufficient": "#979d9f", "0": "#D8C3A5", "1": "#DCEEF7",
          "2": "#92C9E2", "3": "#4B9CC5", "4": "#216B9A", ">=5": "#0E3F67"}


def uri(path):
    return "data:image/png;base64," + base64.b64encode(Path(path).read_bytes()).decode()


@st.cache_data(show_spinner=False)
def rice_overlay_uri(run_id):
    return uri(d.STATIC / "rice_overlay.png")


def production_record(scope, threshold, window_id):
    if scope == "Full Cropland AOI":
        section, static = "production/whole_region", d.STATIC / "production" / "whole_region"
    elif scope in {"MARIIS", "UCRIS", "MRIS"}:
        section, static = "production/participating_areas", d.STATIC / "production" / "participating_areas"
    else:
        return None
    records = d.map_index(section)
    record = next((x for x in records if x["threshold"] == threshold and x["window_id"] == window_id), None)
    return (static, record) if record else None


def map_view(static, manifest, record, scope, show_rice, show_production):
    bounds = manifest["study"]["display_bounds"]
    center = [sum(x[0] for x in bounds) / 2, sum(x[1] for x in bounds) / 2]
    m = folium.Map(location=center, zoom_start=9.5, tiles=None, control_scale=True, min_zoom=7, max_zoom=18)
    context = d.STATIC / "context.png"
    folium.raster_layers.ImageOverlay(uri(context), bounds=bounds, name="Land-cover context", opacity=.65).add_to(m)
    folium.raster_layers.ImageOverlay(uri(static / record["png"]), bounds=bounds,
                                      name="WI reversals", opacity=.94).add_to(m)
    if show_rice:
        folium.raster_layers.ImageOverlay(rice_overlay_uri(manifest["wi"]["run_id"]), bounds=bounds,
                                          name="Historical potential rice (supporting layer)", opacity=.72).add_to(m)
    baseline = production_record(scope, record["threshold"], record["window_id"])
    if show_production and baseline:
        baseline_static, baseline_record = baseline
        folium.raster_layers.ImageOverlay(uri(baseline_static / baseline_record["png"]), bounds=bounds,
                                          name="Production relative-index reversals", opacity=.88,
                                          show=False).add_to(m)
    coverage = d.coverage_geojson()
    def outline(feature):
        color = feature["properties"].get("color", [70, 85, 95, 220])
        return {"color": "#%02x%02x%02x" % tuple(color[:3]), "weight": 1,
                "opacity": .82, "fill": False, "interactive": False}
    folium.GeoJson(coverage, name="Supplied field-system outlines", style_function=outline,
                   tooltip=False, control=True).add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    return m


def donut(selected):
    selected = selected.set_index("reversal_group").reindex(["Insufficient", "0", "1", "2", "3", "4", ">=5"]).fillna(0).reset_index()
    fig = go.Figure(go.Pie(
        labels=["Insufficient" if x == "Insufficient" else f"{x} reversals" for x in selected.reversal_group],
        values=selected.pixels, hole=.58, sort=False,
        marker=dict(colors=[COLORS[x] for x in selected.reversal_group]),
        customdata=selected[["area_ha", "percent"]], textinfo="label+percent", textposition="inside",
        hovertemplate="%{label}<br>%{value:,} pixels<br>%{customdata[0]:,.1f} ha<extra></extra>"))
    fig.update_layout(template="plotly_white", height=420, margin=dict(l=10, r=10, t=20, b=65),
                      legend=dict(orientation="h", y=-.12, x=.5, xanchor="center"),
                      annotations=[dict(text="<b>Screening<br>domain</b>", x=.5, y=.5, showarrow=False)])
    return fig


def existing_summary(scope, threshold, window_id):
    if scope == "Full Cropland AOI":
        section, filename = "production/whole_region", "window_summary.parquet"
    elif scope in {"MARIIS", "UCRIS", "MRIS"}:
        section, filename = "production/participating_areas", "window_summary.parquet"
    else:
        return None
    table = d.table(section, filename)
    row = table[(table.threshold == threshold) & (table.window_id == window_id)]
    return None if row.empty else row.iloc[0]


def render():
    st.subheader("WI · All area · Rice-derived reference")
    st.caption("Experimental Lovell WI across the full fixed-support Cropland AOI. The QC historical-rice layer supplies the reference endpoints; it is not the application mask.")
    output, static, manifest = d.DATA / "wi", d.STATIC / "wi", d.metadata()
    windows = d.table("wi", "window_summary.parquet")
    distribution = d.table("wi", "reversal_distribution.parquet")
    records = {(x["scope"], x["threshold"], x["window_id"]): x for x in d.map_index("wi")}
    refs = manifest["wi"]["references"]

    with st.container(border=True):
        a, b = st.columns([1.05, 1])
        with a:
            st.markdown("**Published equation (primary experimental dB branch)**")
            st.latex(r"WI_t=\frac{\beta^0_{low}-\beta^0_t}{\beta^0_{high}-\beta^0_t}")
        with b:
            st.markdown(
                f"**Fixed QC rice-domain references**  \\\n"
                f"Low = **{refs['low_db']:.3f} dB** · High = **{refs['high_db']:.3f} dB**  \\\n"
                "Pooled 2023–2025 P1/P99 after spatial QC."
            )
            st.caption("The source publication does not resolve whether the equation used dB or linear power. dB is primary here only for consistency with Steps 33–34; linear power is retained as sensitivity output.")
    st.warning("Only observations inside the reference interval and numerically stable are screened. Below-low, above-high, near-singular, missing, and invalid observations remain recorded—not changed to zero or silently clipped.")

    scope = "Full Cropland AOI"
    threshold = st.radio("WI-specific change threshold", ["p90", "p80"], horizontal=True, key="wi35_threshold",
                         format_func=lambda x: "P90 · primary" if x == "p90" else "P80 · sensitivity")
    value = manifest["wi"]["thresholds"][threshold]["threshold"]
    st.caption(f"{threshold.upper()} uses |ΔWI| ≥ {value:.3f}, derived independently from all eligible 12-day Cropland pixel-pairs. It is not the production index threshold.")
    available = windows[(windows.scope == scope) & (windows.threshold == threshold)].copy()
    seasons = available.season.drop_duplicates().tolist()
    season = st.radio("Cropping period", seasons, horizontal=True, key="wi35_season")
    available = available[available.season == season]
    chosen = st.selectbox("Window", available.window_id.tolist(),
                          format_func=dict(zip(available.window_id, available.label)).get, key="wi35_window")
    summary = available[available.window_id == chosen].iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Eligible screening area", f"{summary.eligible_area_ha:,.1f} ha")
    c2.metric("Potential-pattern area", f"{summary.candidate_area_ha:,.1f} ha")
    c3.metric("Candidate share", f"{summary.candidate_percent_of_eligible:.1f}%", help="Denominator: pixels with at least two eligible consecutive WI changes in this window.")
    c4.metric("Insufficient area", f"{summary.insufficient_pixels * .01:,.1f} ha")

    selected = distribution[(distribution.scope == scope) & (distribution.threshold == threshold)
                            & (distribution.window_id == chosen)].copy()
    shares = selected.set_index("reversal_group").pixels / int(summary.eligible_pixels)
    st.caption("Detailed reversal-count shares · eligible screening pixels only")
    d2, d3, d4, d5 = st.columns(4)
    d2.metric("2 reversals", f"{100 * shares.get('2', 0):.2f}%")
    d3.metric("3 reversals", f"{100 * shares.get('3', 0):.2f}%")
    d4.metric("4 reversals", f"{100 * shares.get('4', 0):.2f}%")
    d5.metric("≥5 reversals", f"{100 * shares.get('>=5', 0):.2f}%")
    left, right = st.columns([1.05, 1])
    with left: st.plotly_chart(donut(selected), width="stretch")
    with right:
        st.markdown("#### What is counted")
        st.markdown("A reversal is a change from one **significant eligible** WI direction to the opposite direction. Excluded observations break continuity; no 24-day bridge is created across a missing 12-day acquisition.")
        st.markdown(f"- Eligible 12-day pixel-pairs: **{int(summary.eligible_pixel_pairs):,}**\n- Excluded pixel-pairs: **{int(summary.excluded_pixel_pairs):,}**\n- Significant changes: **{int(summary.significant_changes):,}**\n- Mathematical reversals: **{int(summary.reversals):,}**")
        pair_diagnostics = pd.read_parquet(output / "pair_diagnostics.parquet")
        risk = pair_diagnostics[(pair_diagnostics.scope == scope)
                                & (pair_diagnostics.threshold == threshold)
                                & pair_diagnostics.previous_date.ge(summary.start)
                                & pair_diagnostics.date.lt(summary.end_exclusive)]
        significant = int((risk.positive_changes + risk.negative_changes).sum())
        near_high = int(risk.significant_near_high_5pct.sum())
        risk_share = 100 * near_high / significant if significant else np.nan
        st.markdown(f"- Significant changes with an endpoint in the nearest 5% below the high reference: **{near_high:,}** ({risk_share:.1f}% of significant changes)" if significant else
                    "- Near-high-reference share: **not defined** (no significant eligible changes)")

    st.markdown("### Spatial pattern")
    c1, c2 = st.columns(2)
    show_rice = c1.checkbox("Show historical potential-rice support layer", value=False, key="wi35_rice_overlay")
    comparable = scope != "Historical rice overlap"
    show_production = c2.checkbox("Add production-baseline layer", value=False, disabled=not comparable,
                                  key="wi35_production_overlay")
    record = records[(scope, threshold, chosen)]
    st.iframe(map_view(static, manifest, record, scope, show_rice, show_production).get_root().render(),
              height=760)
    st.caption("Grey = insufficient · light brown = 0 · blues = 1, 2, 3, 4 and ≥5 WI reversals (darker = more). The yellow overlay is historical potential rice, not confirmed rice cultivation in 2023–2025.")

    st.markdown("### Comparison with the production baseline")
    old = existing_summary(scope, threshold, chosen)
    if old is None:
        st.info("A like-for-like production regional map is not available for this historical-rice-only scope.")
    else:
        old_candidate = 100 - float(old.percent_0_reversals)
        comparison = pd.DataFrame({"Baseline": ["Production relative index", "Experimental Lovell WI"],
                                   "Candidate share (%)": [old_candidate, summary.candidate_percent_of_eligible],
                                   "Reference": ["Production Cropland min/max", "QC rice-domain P1/P99"],
                                   "Exclusions": ["Production quality rules", "Inside-range + stable WI only"]})
        st.dataframe(comparison.style.format({"Candidate share (%)": "{:.1f}"}), hide_index=True, width="stretch")
        st.caption("These percentages use different eligibility rules and cannot isolate the nonlinear equation by themselves.")

    eligibility = pd.read_parquet(output / "observation_eligibility.parquet")
    status_scope = eligibility[(eligibility.scope == scope) & (eligibility.units == "dB")]
    with st.expander("Numerical eligibility, downloads, and interpretation"):
        totals = status_scope[["eligible_stable", "near_singular", "below_low", "above_high", "invalid"]].sum()
        st.dataframe(totals.rename("pixel-date observations").rename_axis("status").reset_index(), hide_index=True, width="stretch")
        st.download_button("Download selected window summary", available[available.window_id == chosen].to_csv(index=False),
                           file_name=f"35o-{threshold}-{chosen}-summary.csv", mime="text/csv")
        st.download_button("Download all WI window summaries", windows.to_csv(index=False),
                           file_name="35o-wi-window-summary.csv", mime="text/csv")
    st.info("Repeated WI reversals indicate SAR temporal patterns potentially consistent with wetting–drying dynamics. They do not confirm actual AWD irrigation or subsurface water-table fluctuations.")
