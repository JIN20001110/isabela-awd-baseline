"""Concise method overview for the three formulations and two spatial scales."""
from __future__ import annotations

import streamlit as st

import release_data as d


STYLE = '''<style>
.method-flowchart{margin:18px 0 28px;padding:18px;border:1px solid #d7e1dd;border-radius:12px;background:#fbfcfc}
.flow-row{display:flex;align-items:stretch;justify-content:center;gap:9px}.flow-row.final{flex-wrap:wrap}
.flow-arrow{display:flex;align-items:center;justify-content:center;color:#55736d;font-size:28px;font-weight:700;min-width:28px}
.flow-down{text-align:center;color:#55736d;font-size:31px;font-weight:700;line-height:1;margin:10px 0}
.flow-label{text-align:center;text-transform:uppercase;letter-spacing:.08em;font-size:11px;font-weight:700;color:#6a7d78;margin:4px 0 10px}
.branch-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
.branch-flow{display:grid;grid-template-columns:minmax(0,1fr) 30px minmax(0,1fr);align-items:stretch;gap:6px;border-radius:9px;padding:9px}
.branch-flow.production{background:#edf6fa}.branch-flow.sensitivity{background:#edf8f5}.branch-flow.wi{background:#f3f0fa}
.method-step{flex:1;background:#f3f7f5;border:1px solid #cbd9d3;border-top:4px solid #287b70;border-radius:7px;padding:12px 11px;min-width:145px;min-height:92px}
.method-step b{display:block;font-size:14px;margin-bottom:7px;color:#183e39}.method-step span{font-size:12px;color:#526964;line-height:1.45}
.method-step.production{border-top-color:#277da1;background:#f7fbfd}.method-step.sensitivity{border-top-color:#1b8f75;background:#f7fcfa}.method-step.wi{border-top-color:#6655a5;background:#faf9fd}.method-step.output{border-top-color:#b07b24;background:#fbf7ee}
.summary-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:10px 0 18px}
.summary-card{border:1px solid #d7e1dd;border-radius:9px;padding:14px;background:white;min-height:145px}
.summary-card b{display:block;color:#23445c;margin-bottom:7px}.summary-card span{font-size:13px;line-height:1.5;color:#4d6260}
.stat-flow{display:flex;align-items:stretch;gap:8px;margin:10px 0 16px}.stat-box{flex:1;border:1px solid #d7e1dd;border-radius:8px;padding:12px;background:#f8faf9}.stat-box b{display:block;color:#23445c;margin-bottom:5px}.stat-box span{font-size:12px;line-height:1.45;color:#526964}.stat-arrow{display:flex;align-items:center;color:#55736d;font-size:24px;font-weight:700}
@media(max-width:1050px){.branch-grid,.summary-grid{grid-template-columns:1fr}.flow-row.final,.stat-flow{display:grid;grid-template-columns:1fr;max-width:620px;margin-left:auto;margin-right:auto}.flow-row.final .flow-arrow,.stat-arrow{transform:rotate(90deg);min-height:28px;justify-content:center}}
@media(max-width:650px){.flow-row.shared{display:grid;grid-template-columns:1fr}.flow-row.shared .flow-arrow{transform:rotate(90deg);min-height:28px}.branch-flow{grid-template-columns:1fr}.branch-flow .flow-arrow{transform:rotate(90deg);min-height:28px}}
</style>'''


FLOW = '''<div class="method-flowchart">
<div class="flow-label">Shared input and preprocessing</div>
<div class="flow-row shared">
  <div class="method-step"><b>1 · Study observations</b><span>Isabela AOI · 2023–2025<br>S1A descending R032 · 88 dates</span></div>
  <div class="flow-arrow">→</div>
  <div class="method-step"><b>2 · Shared β⁰ preparation</b><span>Calibrated σ⁰ + incidence angle<br>β⁰ estimate · 3×3 spatial median</span></div>
</div>
<div class="flow-down">↓</div>
<div class="flow-label">Three fixed-reference branches</div>
<div class="branch-grid">
  <div class="branch-flow production">
    <div class="method-step production"><b>3A · Cropland reference</b><span>Fixed-support Cropland<br>Pooled 2023–2025 min/max</span></div>
    <div class="flow-arrow">→</div>
    <div class="method-step production"><b>4A · Production RI</b><span>Linear normalization + clipping<br>Adjacent ΔRI</span></div>
  </div>
  <div class="branch-flow sensitivity">
    <div class="method-step sensitivity"><b>3B · Rice raw reference</b><span>Historical potential-rice ∩ Cropland<br>Pooled min/max</span></div>
    <div class="flow-arrow">→</div>
    <div class="method-step sensitivity"><b>4B · Rice-reference RI</b><span>Same linear equation<br>Different fixed endpoints</span></div>
  </div>
  <div class="branch-flow wi">
    <div class="method-step wi"><b>3C · QC rice reference</b><span>Historical-rice domain<br>Pooled P1/P99</span></div>
    <div class="flow-arrow">→</div>
    <div class="method-step wi"><b>4C · Published Lovell WI</b><span>Nonlinear · no clipping<br>Numerical eligibility checks</span></div>
  </div>
</div>
<div class="flow-down">↓</div>
<div class="flow-label">Common temporal screening</div>
<div class="flow-row final">
  <div class="method-step"><b>5 · Threshold</b><span>Method-specific P90 primary<br>P80 sensitivity</span></div>
  <div class="flow-arrow">→</div>
  <div class="method-step"><b>6 · Adjacent change</b><span>Valid consecutive observations<br>Gaps break sequences</span></div>
  <div class="flow-arrow">→</div>
  <div class="method-step"><b>7 · Cropping windows</b><span>Regional and system-specific calendars</span></div>
  <div class="flow-arrow">→</div>
  <div class="method-step"><b>8 · Reversals</b><span>Significant changes that switch direction</span></div>
  <div class="flow-arrow">→</div>
  <div class="method-step output"><b>9 · Spatial statistics</b><span>0 · 1 · 2 · 3 · 4 · ≥5 reversals<br>Maps and field review</span></div>
  <div class="flow-arrow">→</div>
  <div class="method-step output"><b>10 · Interpretation</b><span>Potential AWD-like SAR patterns<br>Not confirmed AWD</span></div>
</div>
</div>'''


def _comparison_facts() -> tuple[float, float, float, float, float]:
    gaps = []
    for scope in ["whole_region", "participating_areas"]:
        left = d.table(f"production/{scope}", "window_summary.parquet")
        right = d.table(f"rice_raw/{scope}", "window_summary.parquet")
        merged = left.merge(right, on=["threshold", "window_id"], suffixes=("_production", "_rice"))
        gaps.extend((merged.percent_2plus_reversals_production
                     - merged.percent_2plus_reversals_rice).abs().tolist())
    whole = d.table("production/whole_region", "window_summary.parquet")
    p90 = whole[whole.threshold.eq("p90")]
    wet = p90[p90.season.eq("Wet core")].percent_2plus_reversals
    dry = p90[p90.season.eq("Dry core")].percent_2plus_reversals
    return max(gaps), float(wet.min()), float(wet.max()), float(dry.min()), float(dry.max())


def render():
    st.subheader("Method")
    st.caption("A regional pre-intervention SAR screening framework—not a field-water-level measurement or confirmed AWD classifier.")
    st.markdown(STYLE + FLOW, unsafe_allow_html=True)

    st.markdown("### Why there are six result views")
    st.markdown("**Three index configurations × two spatial scales = six result views.** These are not six independent methods or six separate datasets.")
    st.markdown('''| Index configuration | All area | Participating fields |
|---|---|---|
| Production RI · Cropland reference | Full fixed-support Cropland AOI | Cropland inside supplied MARIIS/UCRIS/MRIS fields |
| Rice-reference RI · rice-derived reference | Same full Cropland AOI | Same participating-field Cropland |
| Experimental Lovell WI · QC rice-derived reference | Eligible Cropland in the full AOI | Eligible Cropland inside participating fields |''')
    st.caption("The dashboard contains the core method and result views, plus a separate calendar-core sensitivity page. That diagnostic does not alter the baseline screening outputs.")

    st.markdown("### Why three index configurations are shown")
    st.markdown('''<div class="summary-grid">
<div class="summary-card"><b>1 · Production RI</b><span>We had no local Isabela wet/dry observations, so the first transparent baseline used one fixed min/max range from the available Cropland domain.</span></div>
<div class="summary-card"><b>2 · Rice-reference RI</b><span>Cropland may include non-rice crops, and its extrema may not represent rice conditions. We therefore repeated the same linear RI using endpoints derived from historical potential-rice pixels.</span></div>
<div class="summary-card"><b>3 · Experimental Lovell WI</b><span>The paper used field-informed wet/dry test-plot references, which we do not have locally. Its printed nonlinear formula, calculation unit and derivation are also insufficiently explained, so we reproduce it separately and label it experimental.</span></div>
</div>''', unsafe_allow_html=True)
    st.info("“Rice reference” describes where the fixed endpoints came from. It does **not** mean that only historical-rice pixels are displayed, or that rice cultivation was confirmed in every 2023–2025 season.")

    st.markdown("### What is actually counted")
    st.markdown('''<div class="stat-flow">
<div class="stat-box"><b>Index at each date</b><span>RI or WI is calculated for each eligible pixel and Sentinel-1 acquisition.</span></div>
<div class="stat-arrow">→</div>
<div class="stat-box"><b>Adjacent change</b><span>ΔX<sub>t</sub> = X<sub>t</sub> − X<sub>t−1</sub>, usually across approximately 12 days.</span></div>
<div class="stat-arrow">→</div>
<div class="stat-box"><b>Significant change</b><span>|ΔX| must reach the method-specific P90 or P80 threshold.</span></div>
<div class="stat-arrow">→</div>
<div class="stat-box"><b>Direction reversal</b><span>The next significant change moves in the opposite direction within the same uninterrupted cropping window.</span></div>
<div class="stat-arrow">→</div>
<div class="stat-box"><b>Spatial statistic</b><span>Share of eligible pixels with 0, 1, 2, 3, 4 or ≥5 reversals.</span></div>
</div>''', unsafe_allow_html=True)

    left, right = st.columns(2)
    with left:
        st.markdown("**P90 · primary result**")
        st.markdown("Keeps the largest **10%** of eligible adjacent-change magnitudes. It is more conservative and reduces small fluctuations.")
    with right:
        st.markdown("**P80 · sensitivity result**")
        st.markdown("Keeps the largest **20%**. It tests whether the spatial pattern remains visible when weaker changes are included.")
    st.caption("P90/P80 are empirical SAR-change thresholds, not physical water-depth, wet/dry or AWD thresholds. Each formulation derives its own values, so the numerical thresholds are not directly comparable.")

    st.markdown("### The Comparison page is the key result")
    gap, wet_low, wet_high, dry_low, dry_high = _comparison_facts()
    st.markdown(f'''- The two linear RI versions are almost identical: their largest difference in the **2+ reversal share is only {gap:.3f} percentage points**.
- The experimental WI can produce different percentages because it is nonlinear and excludes numerically unstable or out-of-range observations, but the broad seasonal/spatial comparison remains available.
- At whole-area P90, Production RI records **{wet_low:.2f}–{wet_high:.2f}%** with 2+ reversals in Wet-core windows, compared with **{dry_low:.2f}–{dry_high:.2f}%** in Dry-core windows.''')
    st.success("Repeated reversals are generally more common in Wet-core windows, where rainfall can also drive SAR changes. Lower Dry-core reversal shares mean that the baseline provides **no strong regional evidence of widespread pre-existing AWD**. This is suggestive—not proof that AWD was absent—because crop timing, rainfall, canopy effects and 12-day sampling can hide or mimic changes.")

    st.markdown("### Cropping windows used")
    st.markdown('''| Spatial view | Dry window | Wet window |
|---|---|---|
| Whole area | December–April | May–October |
| MARIIS | September–February | May–October |
| UCRIS | November–April | July–December |
| MRIS | January–May | August–December |''')
    st.caption("The irrigation-authority 2026 calendar is repeated over 2023–2025 as an explicit simplifying assumption.")

    production = d.metadata()["production"]["thresholds"]
    rice_raw = d.metadata()["rice_raw_relative_index"]
    wi = d.metadata()["wi"]
    refs = wi["references"]
    with st.expander("Equations, reference values and thresholds"):
        st.latex(r"\beta^0_{est,dB}=\sigma^0_{dB}-10\log_{10}(\sin\theta)")
        a, b, c = st.columns(3)
        with a:
            st.markdown("**Production RI**")
            st.latex(r"RI_t=\operatorname{clip}\!\left(\frac{U_{crop}-\beta^0_t}{U_{crop}-L_{crop}},0,1\right)")
            st.markdown(f"P90 **{production['p90']['threshold']:.4f}** · P80 **{production['p80']['threshold']:.4f}**")
        with b:
            st.markdown("**Rice-reference RI**")
            st.latex(r"RI^{rice}_t=\operatorname{clip}\!\left(\frac{U_{rice}-\beta^0_t}{U_{rice}-L_{rice}},0,1\right)")
            st.markdown(f"L/U **{rice_raw['references']['low_db']:.3f}/{rice_raw['references']['high_db']:.3f} dB**")
            st.markdown(f"P90 **{rice_raw['thresholds']['p90']['threshold']:.4f}** · P80 **{rice_raw['thresholds']['p80']['threshold']:.4f}**")
        with c:
            st.markdown("**Experimental Lovell WI**")
            st.latex(r"WI_t=\frac{\beta^0_{low}-\beta^0_t}{\beta^0_{high}-\beta^0_t}")
            st.markdown(f"P1/P99 **{refs['low_db']:.3f}/{refs['high_db']:.3f} dB**")
            st.markdown(f"P90 **{wi['thresholds']['p90']['threshold']:.3f}** · P80 **{wi['thresholds']['p80']['threshold']:.3f}**")

    with st.expander("Why the published WI remains experimental here"):
        st.markdown('''Lovell et al. (2019) used extrema from metered rice test plots informed by field observations. We do not have equivalent wet/dry observations in Isabela. The paper also does not clearly resolve the equation's calculation unit, and its printed formula modifies earlier wetness-index ideas without a verifiable mathematical derivation sufficient to remove the ambiguity. We therefore reproduce the published equation without silently changing it, apply explicit numerical eligibility checks, and avoid calling the output physically validated wetness.''')
        st.markdown("[Lovell et al. (2019)](https://doi.org/10.3390/ijgi8070312)")

    with st.expander("How the experimental WI baseline was developed"):
        st.markdown('''| Step | Evidence added |
|---|---|
| Step 1 · Rice distribution | Open-SEA-Rice-10 supplied historical potential-rice support inside the Cropland AOI. |
| Step 2 · Raw references | Rice-domain extrema were inspected rather than accepted automatically. |
| Step 3 · Extreme diagnostics | Low and high tails were traced through space, time and preprocessing. |
| Step 4 · Robust references | QC historical-rice pooled 2023–2025 P1/P99 were selected as statistical endpoints. |
| Step 5 · Published WI | The printed Lovell equation was reproduced in dB and linear-power branches. |
| Step 6 · Temporal feasibility | Direction, singularity risk, reversals, seasons and rainfall consistency were diagnosed. |
| Step 7 · Baseline screening | WI-specific P90/P80 thresholds and regional/field results were produced. |''')

    with st.expander("Scientific limitations"):
        st.markdown('''- Historical potential rice does not confirm rice cultivation in every study season.
- There are no local Isabela field water-level measurements for direct hydrological validation.
- Rainfall, canopy, crop stage, harvest, roughness and mixed pixels can change β⁰.
- A mathematical reversal is not a complete AWD cycle or an irrigation date.
- Approximately 12-day sampling can miss shorter changes.
- WI near-singular and out-of-range observations are excluded explicitly and break continuity.
- Results indicate potential AWD-like SAR patterns, not confirmed AWD adoption.''')
