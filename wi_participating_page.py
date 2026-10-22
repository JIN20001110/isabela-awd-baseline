"""Step 35 field-level WI page; read-only and separate from production pages."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pydeck as pdk
import streamlit as st
import release_data as d


COLORS = {"Insufficient": "#979d9f", "0": "#D8C3A5", "1": "#DCEEF7",
          "2": "#92C9E2", "3": "#4B9CC5", "4": "#216B9A", ">=5": "#0E3F67"}


def aggregate_donut(selected):
    selected = selected.set_index("reversal_group").reindex(
        ["Insufficient", "0", "1", "2", "3", "4", ">=5"]
    ).fillna(0).reset_index()
    fig = go.Figure(go.Pie(
        labels=["Insufficient" if x == "Insufficient" else f"{x} reversals"
                for x in selected.reversal_group],
        values=selected.pixels, hole=.58, sort=False,
        marker=dict(colors=[COLORS[x] for x in selected.reversal_group],
                    line=dict(color="white", width=1)),
        customdata=selected[["area_ha", "percent"]], textinfo="label+percent",
        textposition="inside",
        hovertemplate="%{label}<br>%{value:,} pixels<br>%{customdata[0]:,.1f} ha<extra></extra>",
    ))
    fig.update_layout(
        template="plotly_white", height=410, margin=dict(l=10, r=10, t=20, b=65),
        legend=dict(orientation="h", y=-.12, x=.5, xanchor="center"),
        annotations=[dict(text="<b>Field-area<br>Cropland</b>", x=.5, y=.5, showarrow=False)],
    )
    return fig


@st.cache_data(show_spinner=False)
def field_index(run_id):
    return d.field_index()


@st.cache_data(show_spinner=False, max_entries=50)
def load_field(run_id, field_uid):
    return d.field_series(field_uid)


def prepare_transitions(frame, start, end, threshold):
    part = frame.sort_values("date").copy()
    part["date"] = pd.to_datetime(part.date)
    part["previous_date"] = pd.to_datetime(part.previous_date)
    inside = part.date.ge(pd.Timestamp(start)) & part.date.lt(pd.Timestamp(end))
    eligible = (inside & part.previous_date.ge(pd.Timestamp(start))
                & part.wi_transition_eligible.fillna(False))
    part["direction"] = np.where(eligible & part.delta_wi_db.ge(threshold), 1,
                                 np.where(eligible & part.delta_wi_db.le(-threshold), -1, 0))
    last = 0; reversals = []
    for row in part.itertuples():
        if (not bool(getattr(row, "wi_transition_eligible"))
                or not (pd.Timestamp(start) <= row.previous_date <= row.date < pd.Timestamp(end))):
            last = 0; reversals.append(False); continue
        direction = int(row.direction)
        reversal = bool(direction and last and direction != last)
        reversals.append(reversal)
        if direction: last = direction
    part["reversal"] = reversals
    part["in_window"] = inside
    return part


def chart(frame, start, end, threshold):
    part = prepare_transitions(frame, start, end, threshold)
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=.085,
                        row_heights=[.34, .39, .27],
                        subplot_titles=["Filtered β⁰ field median", "Published WI · eligible observations only",
                                        "Eligible adjacent ΔWI"])
    fig.add_trace(go.Scatter(x=part.date, y=part.beta_db, mode="lines+markers", name="β⁰ estimate",
                             line=dict(color="#176b63", width=1.5), marker=dict(size=4),
                             hovertemplate="%{x|%Y-%m-%d}<br>β⁰ %{y:.2f} dB<extra></extra>"), row=1, col=1)
    for _, segment in part[part.wi_db.notna()].groupby(part.wi_db.isna().cumsum()):
        fig.add_trace(go.Scatter(x=segment.date, y=segment.wi_db, mode="lines+markers", name="WI",
                                 showlegend=False, line=dict(color="#4f46a5", width=1.6), marker=dict(size=4),
                                 connectgaps=False, hovertemplate="%{x|%Y-%m-%d}<br>WI %{y:.3f}<extra></extra>"), row=2, col=1)
    excluded = part[(part.wi_db_status_code != 2) & part.beta_db.notna()]
    if len(excluded):
        fig.add_trace(go.Scatter(x=excluded.date, y=excluded.beta_db, mode="markers", name="WI excluded",
                                 marker=dict(symbol="x", size=9, color="#b23a2b"),
                                 customdata=excluded.wi_db_status,
                                 hovertemplate="%{x|%Y-%m-%d}<br>β⁰ %{y:.2f} dB<br>%{customdata}<extra></extra>"), row=1, col=1)
    colors = np.where(part.delta_wi_db.ge(0), "#1f766e", "#b47a29")
    fig.add_trace(go.Bar(x=part.date, y=part.delta_wi_db, name="ΔWI", showlegend=False,
                         marker_color=colors, hovertemplate="%{x|%Y-%m-%d}<br>ΔWI %{y:+.3f}<extra></extra>"), row=3, col=1)
    significant = part[part.direction != 0]
    if len(significant):
        fig.add_trace(go.Scatter(x=significant.date, y=significant.delta_wi_db, mode="markers", name="Significant change",
                                 marker=dict(symbol="diamond", size=9, color="#162c52")), row=3, col=1)
    reversals = part[part.reversal]
    if len(reversals):
        fig.add_trace(go.Scatter(x=reversals.date, y=reversals.delta_wi_db, mode="markers", name="Direction reversal",
                                 marker=dict(symbol="star", size=15, color="#d94733", line=dict(width=1, color="white"))), row=3, col=1)
    for row in (1, 2, 3):
        fig.add_vrect(x0=start, x1=pd.Timestamp(end) - pd.Timedelta(days=1), fillcolor="#bedfd5", opacity=.16,
                      line_width=0, row=row, col=1)
    fig.add_hline(y=threshold, line_dash="dot", line_color="#87918e", row=3, col=1)
    fig.add_hline(y=-threshold, line_dash="dot", line_color="#87918e", row=3, col=1)
    fig.update_yaxes(title_text="β⁰ (dB)", row=1, col=1)
    fig.update_yaxes(title_text="WI (unitless)", row=2, col=1)
    fig.update_yaxes(title_text="ΔWI", row=3, col=1)
    fig.update_xaxes(title_text="Sentinel-1 acquisition date", row=3, col=1)
    fig.update_layout(template="plotly_white", height=790, hovermode="x unified",
                      margin=dict(l=45, r=20, t=65, b=45),
                      legend=dict(orientation="h", y=1.08, x=0),
                      font=dict(family="Arial, sans-serif", size=12))
    fig.update_xaxes(showgrid=False); fig.update_yaxes(gridcolor="#e8eeec")
    return fig, part


def field_map(points, selected_uid):
    points = points.copy()
    points["color"] = points.screening_status.map({
        "Potential AWD-like pattern": [48, 132, 172, 195],
        "No detected significant pattern": [198, 163, 113, 190],
        "Insufficient eligible observations": [145, 151, 154, 170],
    }).apply(lambda x: x if isinstance(x, list) else [145, 151, 154, 170])
    points.loc[points.field_uid.astype(str).eq(str(selected_uid)), "color"] = pd.Series(
        [[255, 190, 45, 255]], index=points.index[points.field_uid.astype(str).eq(str(selected_uid))])
    chosen = points[points.field_uid.astype(str).eq(str(selected_uid))].iloc[0]
    layer = pdk.Layer("ScatterplotLayer", points, get_position="[longitude, latitude]", get_fill_color="color",
                      get_radius=55, radius_min_pixels=2, radius_max_pixels=8, pickable=True,
                      stroked=True, get_line_color=[255, 255, 255, 150], line_width_min_pixels=.5)
    return pdk.Deck(map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
                    initial_view_state=pdk.ViewState(latitude=float(chosen.latitude), longitude=float(chosen.longitude),
                                                    zoom=11, pitch=0), layers=[layer],
                    tooltip={"html": "<b>{field_uid}</b><br/>{screening_status}<br/>Rice overlap: {rice_fraction_display}"})


def render():
    st.subheader("WI · Participating fields · Rice-derived reference")
    st.caption("Field-level experimental Lovell WI within the supplied inventory and each irrigation system's cropping windows. QC historical-rice pixels define the endpoints; all eligible Cropland pixels inside participating fields are screened.")
    manifest = d.metadata()
    summaries = d.table("wi", "field_season_summary.parquet")
    windows = d.table("wi", "window_summary.parquet")
    distribution = d.table("wi", "reversal_distribution.parquet")
    summaries["field_uid"] = summaries.field_uid.astype(str)
    refs = manifest["wi"]["references"]
    st.info(f"Published WI · fixed QC-rice references {refs['low_db']:.3f}/{refs['high_db']:.3f} dB · no clipping · excluded acquisitions break continuity.")

    system = st.selectbox("Irrigation system", ["MARIIS", "UCRIS", "MRIS"], key="wi35_field_system")
    threshold = st.radio("WI-specific threshold", ["p90", "p80"], horizontal=True, key="wi35_field_threshold",
                         format_func=lambda x: "P90 · primary" if x == "p90" else "P80 · sensitivity")
    wi_threshold = manifest["wi"]["thresholds"][threshold]["threshold"]
    options = summaries[(summaries.system == system) & (summaries.method == "WI") & (summaries.threshold == threshold)]
    season = st.radio("Cropping season", [x for x in ["Dry", "Wet"] if x in options.season.unique()],
                      horizontal=True, key="wi35_field_season")
    options = options[options.season == season]
    window_id = st.selectbox("Window", options.window_id.drop_duplicates().tolist(),
                             format_func=dict(zip(options.window_id, options.label)).get, key="wi35_field_window")
    selected_options = options[options.window_id == window_id].copy()

    aggregate = windows[(windows.scope == system) & (windows.threshold == threshold)
                        & (windows.window_id == window_id)].iloc[0]
    aggregate_distribution = distribution[(distribution.scope == system)
                                          & (distribution.threshold == threshold)
                                          & (distribution.window_id == window_id)].copy()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Eligible screening area", f"{aggregate.eligible_area_ha:,.1f} ha")
    c2.metric("0 reversals", f"{100 * int(aggregate_distribution.loc[aggregate_distribution.reversal_group.eq('0'), 'pixels'].sum()) / int(aggregate.eligible_pixels):.1f}%" if aggregate.eligible_pixels else "N/A")
    c3.metric("1 reversal", f"{100 * int(aggregate_distribution.loc[aggregate_distribution.reversal_group.eq('1'), 'pixels'].sum()) / int(aggregate.eligible_pixels):.1f}%" if aggregate.eligible_pixels else "N/A")
    two_plus = int(aggregate_distribution.loc[aggregate_distribution.reversal_group.isin(['2', '3', '4', '>=5']), 'pixels'].sum())
    c4.metric("2+ reversals", f"{100 * two_plus / int(aggregate.eligible_pixels):.1f}%" if aggregate.eligible_pixels else "N/A")
    shares = aggregate_distribution.set_index("reversal_group").pixels / int(aggregate.eligible_pixels)
    st.caption("Detailed reversal-count shares · eligible screening pixels only")
    d2, d3, d4, d5 = st.columns(4)
    d2.metric("2 reversals", f"{100 * shares.get('2', 0):.2f}%")
    d3.metric("3 reversals", f"{100 * shares.get('3', 0):.2f}%")
    d4.metric("4 reversals", f"{100 * shares.get('4', 0):.2f}%")
    d5.metric("≥5 reversals", f"{100 * shares.get('>=5', 0):.2f}%")
    st.plotly_chart(aggregate_donut(aggregate_distribution), width="stretch")
    st.caption("Aggregate distribution for eligible Cropland inside the selected irrigation-system fields. Grey = insufficient · light brown = 0 · blues = 1, 2, 3, 4 and ≥5 reversals (darker = more).")

    field_ids = sorted(selected_options.field_uid.unique().tolist())
    if st.session_state.get("wi35_field_uid") not in field_ids:
        st.session_state["wi35_field_uid"] = "211_1" if "211_1" in field_ids else field_ids[0]
    field_uid = st.selectbox("Field ID", field_ids, key="wi35_field_uid")
    selected = selected_options[selected_options.field_uid == field_uid].iloc[0]

    index = field_index(manifest["wi"]["run_id"])
    map_points = selected_options[["field_uid", "screening_status", "rice_fraction"]].merge(
        index[["field_uid", "longitude", "latitude", "area_ha"]].assign(field_uid=lambda x: x.field_uid.astype(str)),
        on="field_uid", how="left")
    map_points["rice_fraction_display"] = map_points.rice_fraction.map(lambda x: "Not available" if pd.isna(x) else f"{x:.1%}")
    st.pydeck_chart(field_map(map_points.dropna(subset=["longitude", "latitude"]), field_uid), width="stretch", height=480)
    st.caption("Blue = potential pattern · brown = no detected significant pattern · grey = insufficient · gold = selected field. These are screening labels, not AWD adoption classes.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("WI reversals", int(selected.significant_reversals))
    c2.metric("Valid adjacent changes", int(selected.valid_consecutive_changes))
    c3.metric("Excluded observations", int(selected.excluded_wi_observations))
    c4.metric("Historical rice overlap", "N/A" if pd.isna(selected.rice_fraction) else f"{selected.rice_fraction:.1%}")

    frame = load_field(manifest["wi"]["run_id"], field_uid)
    figure, prepared = chart(frame, selected.start, selected.end_exclusive, wi_threshold)
    st.plotly_chart(figure, width="stretch")
    st.caption("Green ΔWI = movement toward the provisional lower-backscatter/wet-like reference; brown ΔWI = movement toward the high-backscatter/dry-like reference. Stars mark mathematical direction reversals, not complete AWD cycles.")

    st.markdown("### Same field and season · two independent baselines")
    paired = summaries[(summaries.field_uid == field_uid) & (summaries.window_id == window_id)
                       & (summaries.threshold == threshold)].copy()
    comparison = paired[["method", "threshold_value", "valid_consecutive_changes", "significant_changes",
                         "significant_reversals", "screening_status"]].rename(columns={
                             "method": "Baseline", "threshold_value": "Threshold",
                             "valid_consecutive_changes": "Valid changes", "significant_changes": "Significant changes",
                             "significant_reversals": "Reversals", "screening_status": "Screening result"})
    st.dataframe(comparison.style.format({"Threshold": "{:.4f}"}), hide_index=True, width="stretch")
    st.caption("A difference can arise from the equation, reference domain and values, numerical exclusions, or independently derived thresholds—not only from WI nonlinearity.")

    st.markdown("### P80/P90 sensitivity")
    sensitivity = summaries[(summaries.field_uid == field_uid) & (summaries.window_id == window_id)
                            & (summaries.method == "WI")][["threshold", "threshold_value", "valid_consecutive_changes",
                                                           "significant_reversals", "screening_status"]].copy()
    st.dataframe(sensitivity.style.format({"threshold_value": "{:.4f}"}), hide_index=True, width="stretch")

    with st.expander("Observation eligibility and downloads"):
        counts = prepared.wi_db_status.value_counts().rename_axis("status").reset_index(name="acquisitions")
        st.dataframe(counts, hide_index=True, width="stretch")
        excluded = prepared[prepared.wi_db_status_code != 2][["date", "beta_db", "wi_db_status"]]
        st.dataframe(excluded, hide_index=True, width="stretch")
        st.download_button("Download selected field time series", prepared.to_csv(index=False),
                           file_name=f"35o-{field_uid}-wi-timeseries.csv", mime="text/csv")
        st.download_button("Download selected field-season comparison", paired.to_csv(index=False),
                           file_name=f"35o-{field_uid}-{window_id}-comparison.csv", mime="text/csv")
    st.info("Repeated WI reversals are potential AWD-like SAR patterns. They do not confirm field water levels, irrigation dates, complete AWD cycles, or AWD adoption.")
