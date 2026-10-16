"""English method page for the production and experimental WI baselines."""
import streamlit as st
import release_data as d


STYLE='''<style>
.method-flow{display:grid;grid-template-columns:repeat(6,minmax(120px,1fr));gap:8px;margin:18px 0 24px}
.method-step{background:#f3f7f5;border:1px solid #cbd9d3;border-top:4px solid #287b70;border-radius:5px;padding:13px 11px;min-height:112px}
.method-step b{display:block;font-size:14px;margin-bottom:7px;color:#183e39}.method-step span{font-size:12px;color:#526964;line-height:1.45}
@media(max-width:1000px){.method-flow{grid-template-columns:repeat(3,1fr)}}
</style>'''


def render():
    st.subheader('Method')
    st.caption('A regional pre-intervention screening of repeated wetting–drying patterns in Cropland areas, 2023–2025.')
    st.markdown(STYLE+'''<div class="method-flow">
<div class="method-step"><b>1 · Sentinel-1</b><span>S1A · descending R032<br>88 observation dates</span></div>
<div class="method-step"><b>2 · β⁰ estimate</b><span>Convert calibrated σ⁰ using incidence angle<br>Apply 3×3 median</span></div>
<div class="method-step"><b>3 · Fixed reference</b><span>One Cropland min/max range<br>All pixels and dates</span></div>
<div class="method-step"><b>4 · Relative index</b><span>Place every observation on the same wet-like to dry-like scale</span></div>
<div class="method-step"><b>5 · Significant change</b><span>12-day ΔI<br>P90 primary · P80 sensitivity</span></div>
<div class="method-step"><b>6 · Seasonal reversals</b><span>Count opposite directions inside each system’s Dry/Wet window</span></div>
</div>''',unsafe_allow_html=True)

    left,right=st.columns([1.15,1])
    with left:
        st.markdown('#### Core calculations')
        st.latex(r'\beta^0_{est,dB}=\sigma^0_{dB}-10\log_{10}(\sin\theta)')
        st.latex(r'I_t=\operatorname{clip}\!\left(\frac{\beta^0_{dry}-\beta^0_t}{\beta^0_{dry}-\beta^0_{wet}},0,1\right)')
        st.latex(r'\Delta I_t=I_t-I_{t-1}')
    with right:
        st.markdown('#### Fixed choices')
        thresholds=d.metadata()['production']['thresholds']
        st.markdown(f'''- **Reference domain:** fixed-support Cropland
- **Spatial filter:** 3×3 median
- **P90:** |ΔI| ≥ {thresholds['p90']['threshold']:.4f} · primary
- **P80:** |ΔI| ≥ {thresholds['p80']['threshold']:.4f} · sensitivity
- **Output:** 0, 1, 2 or 3+ reversals''')

    st.markdown('#### Cropping windows')
    st.markdown('''| System | Dry | Wet |
|---|---|---|
| MARIIS | Sep–Feb | May–Oct |
| UCRIS | Nov–Apr | Jul–Dec |
| MRIS | Jan–May | Aug–Dec |''')
    st.info('Main interpretation: areas with repeated reversals are priority candidates for wetting–drying review. They are not confirmed AWD adoption.')
    st.markdown('**Result scales:** Whole region uses all fixed-support Cropland in the AOI. Participating areas use the supplied irrigation-system fields and each system’s own calendar.')
    with st.expander('Data and limitations'):
        st.markdown('''- β⁰ is estimated from GEE-calibrated σ⁰ and incidence angle; it is not reconstructed from raw DN and ESA calibration LUTs.
- Lex’s 2026 cropping calendar is repeated over 2023–2025 as an assumption.
- Rainfall, crop growth, harvest, roughness and mixed pixels may also produce reversals.
- Results describe supplied field coverage, not official irrigation-system boundaries.''')

    st.divider()
    st.subheader('Wetness Index: Literature Origin and Methodological Adaptation')
    st.caption('The experimental WI baseline extends the production screening; it does not replace it.')

    st.markdown('#### Formula provenance')
    c1,c2,c3=st.columns(3)
    with c1:
        st.markdown('''**Shoshany et al. (2000)**<br>
Introduced a normalized backscatter moisture index for comparing two SAR observations while reducing multiplicative soil/roughness effects.''')
        st.latex(r'NBMI=\frac{\sigma^0_{t1}+\sigma^0_{t2}}{\sigma^0_{t1}-\sigma^0_{t2}}')
        st.markdown('[Original article](https://doi.org/10.1080/01431160050029620)')
    with c2:
        st.markdown('''**Hassan & Bourque (2015)**<br>
Developed a RADARSAT-1 wetness index using an instantaneous β⁰ value and an image-derived minimum.''')
        st.latex(r'WI_{HB}=\frac{\beta^0_{min}-\beta^0_{ins}}{\beta^0_{min}+\beta^0_{ins}}')
        st.markdown('[Original chapter](https://doi.org/10.1007/978-94-017-9813-6_15)')
    with c3:
        st.markdown('''**Lovell et al. (2019)**<br>
Applied a different nonlinear expression to Sentinel-1 β⁰ and metered rice test-plot extrema for AWD change detection.''')
        st.latex(r'WI_{L}=\frac{\beta^0_{min}-\beta^0_{ins}}{\beta^0_{max}-\beta^0_{ins}}')
        st.markdown('[Original article](https://doi.org/10.3390/ijgi8070312)')
    st.warning('Lovell et al. (2019) followed the broader idea of earlier SAR-based relative wetness research, but printed a modified WI equation. In the verifiable literature reviewed for this project, we did not find an explicit mathematical derivation or a sufficiently detailed explanation for that modification. The formula is therefore reproduced as published and evaluated experimentally, without assuming that the modification has been independently justified.')

    st.markdown('#### Our two baseline equations')
    left,right=st.columns(2)
    with left:
        st.markdown('**Baseline A · production relative SAR index**')
        st.latex(r'I_t=\operatorname{clip}\!\left(\frac{\beta^0_{high}-\beta^0_t}{\beta^0_{high}-\beta^0_{low}},0,1\right)')
        st.markdown('Linear normalization followed by clipping. Its fixed endpoints come from the production **Cropland** domain.')
    with right:
        st.markdown('**Baseline B · experimental Lovell WI**')
        st.latex(r'WI_t=\frac{\beta^0_{low}-\beta^0_t}{\beta^0_{high}-\beta^0_t}')
        refs=d.metadata()['wi']['references']
        st.markdown(f"Uses the Step 32 QC historical-rice P1/P99 references: **{refs['low_db']:.3f} dB** and **{refs['high_db']:.3f} dB**.")
        st.markdown('Nonlinear and singular when β⁰ equals the high reference. It is not clipped in Step 35.')
    st.markdown('''Both equations use β⁰ and fixed endpoints, but the reference populations are different. A nonlinear transformation does not create an independent water observation. With identical references and units, the **unclipped** linear index and Lovell WI satisfy $WI=1-1/I$ wherever the denominator exists and $I\ne0$; this identity does not carry over unchanged after clipping or when the references differ.''')

    st.markdown('#### How the experimental WI baseline was developed')
    st.markdown('''| Step | Evidence added |
|---|---|
| 29 · Rice distribution | Open-SEA-Rice-10 provided a historical potential-rice support layer inside the Cropland AOI. |
| 30 · Raw references | Raw rice-domain extrema were inspected rather than accepted automatically. |
| 31 · Extreme diagnostics | Episodic low values and persistent high features near built-up boundaries were traced in space and time. |
| 32 · Robust references | QC historical-rice pooled 2023–2025 P1/P99 were selected as statistical endpoints. |
| 33 · Published WI | The printed Lovell equation was reproduced in separate dB and linear-power branches. |
| 34 · Temporal feasibility | Change direction, singularity risk, reversals, seasons, and rainfall consistency were diagnosed. |
| 35 · Baseline screening | WI-specific P90/P80 thresholds, regional/field results, and comparison with Baseline A were produced. |''')
    st.markdown('The Step 35 primary branch uses the unchanged published equation with dB values for consistency with Steps 33–34. The publication does not resolve the calculation unit, so linear power remains a separate sensitivity result. Only inside-range, numerically stable observations are screened; exclusions are retained explicitly and break temporal continuity.')

    with st.expander('Scientific interpretation and limitations'):
        st.markdown('''- Historical potential rice does not confirm rice cultivation in every 2023–2025 season.
- There are no local Isabela field water-level measurements for direct hydrological validation.
- Lower β⁰ is provisionally interpreted as wetter-like and higher β⁰ as drier-like; canopy, roughness, rainfall, harvest and mixed pixels can alter that relationship.
- WI is unitless—not soil-moisture percentage or water depth.
- A mathematical reversal is not a complete AWD cycle and cannot establish an irrigation date.
- The approximately 12-day sampling interval can miss shorter physical changes.
- The Lovell WI has a singularity at the high reference; near-singular and out-of-range observations are excluded from conservative screening but remain reported.
- Neither formula is proven superior for retrieving water conditions in Isabela.''')
    st.info('Step 35 result language: potential AWD-like SAR patterns for pre-intervention prioritization—not confirmed AWD adoption.')
