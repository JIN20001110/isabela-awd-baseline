"""English method page for the production, reference-sensitivity and WI branches."""
import streamlit as st
import release_data as d


STYLE='''<style>
.method-flow{display:grid;grid-template-columns:repeat(4,minmax(170px,1fr));gap:10px;margin:18px 0 24px}
.method-step{background:#f3f7f5;border:1px solid #cbd9d3;border-top:4px solid #287b70;border-radius:5px;padding:13px 11px;min-height:112px}
.method-step b{display:block;font-size:14px;margin-bottom:7px;color:#183e39}.method-step span{font-size:12px;color:#526964;line-height:1.45}
.method-step.production{border-top-color:#277da1;background:#f2f8fb}.method-step.sensitivity{border-top-color:#1b8f75;background:#f1faf7}.method-step.wi{border-top-color:#6655a5;background:#f6f4fb}.method-step.output{border-top-color:#b07b24;background:#fbf7ee}
@media(max-width:1000px){.method-flow{grid-template-columns:repeat(3,1fr)}}
</style>'''


def render():
    st.subheader('Method')
    st.caption('Two screened SAR-change baselines plus one reference-range sensitivity formulation, 2023–2025. Neither experimental branch replaces the production baseline.')
    st.markdown(STYLE+'''<div class="method-flow">
<div class="method-step"><b>1 · Study observations</b><span>Isabela AOI · 2023–2025<br>S1A descending R032 · 88 dates</span></div>
<div class="method-step"><b>2 · Shared β⁰ preparation</b><span>Calibrated σ⁰ + incidence angle<br>β⁰ estimate · 3×3 spatial median</span></div>
<div class="method-step production"><b>3A · Production reference</b><span>Fixed-support Cropland<br>One pooled 2023–2025 min/max range</span></div>
<div class="method-step sensitivity"><b>3B · Rice raw-extrema reference</b><span>Historical potential-rice ∩ Cropland<br>One pooled 2023–2025 min/max range</span></div>
<div class="method-step wi"><b>3C · Experimental WI reference</b><span>QC historical-rice domain<br>One pooled 2023–2025 P1/P99 range</span></div>
<div class="method-step production"><b>4A · Relative SAR index</b><span>Linear normalization + clipping<br>Calculate adjacent ΔI</span></div>
<div class="method-step sensitivity"><b>4B · Rice-reference relative index</b><span>Same linear equation, different endpoints<br>Reference-range sensitivity only</span></div>
<div class="method-step wi"><b>4C · Published Lovell WI</b><span>Nonlinear equation · no clipping<br>Exclude unstable/out-of-range observations</span></div>
<div class="method-step"><b>5 · Screening thresholds</b><span>Production and WI derive independent P90 primary and P80 sensitivity thresholds</span></div>
<div class="method-step"><b>6 · Temporal continuity</b><span>Use valid adjacent observations only<br>Missing or excluded dates break the sequence</span></div>
<div class="method-step"><b>7 · Cropping windows</b><span>Whole-region common windows<br>System-specific MARIIS/UCRIS/MRIS windows</span></div>
<div class="method-step"><b>8 · Direction reversals</b><span>Count significant changes that switch direction within each window</span></div>
<div class="method-step output"><b>9 · Screening outputs</b><span>0 · 1 · 2 · 3+ reversals<br>Regional maps and field-level review</span></div>
<div class="method-step output"><b>10 · Interpretation</b><span>Potential AWD-like SAR patterns<br>Not measured water level or confirmed AWD</span></div>
</div>''',unsafe_allow_html=True)

    st.markdown('#### Core calculations')
    st.latex(r'\beta^0_{est,dB}=\sigma^0_{dB}-10\log_{10}(\sin\theta)')
    left,middle,right=st.columns(3)
    with left:
        st.markdown('**Baseline A · production relative SAR index**')
        st.latex(r'I_t=\operatorname{clip}\!\left(\frac{\beta^0_{dry}-\beta^0_t}{\beta^0_{dry}-\beta^0_{wet}},0,1\right)')
        st.latex(r'\Delta I_t=I_t-I_{t-1}')
    with middle:
        st.markdown('**Formulation B · rice raw-min/max relative index**')
        st.latex(r'I^{rice\,raw}_t=\operatorname{clip}\!\left(\frac{U_{rice}-\beta^0_t}{U_{rice}-L_{rice}},0,1\right)')
        st.latex(r'L_{rice}=-44.826,\quad U_{rice}=24.132\ \mathrm{dB}')
    with right:
        st.markdown('**Baseline C · experimental Lovell WI**')
        st.latex(r'WI_t=\frac{\beta^0_{low}-\beta^0_t}{\beta^0_{high}-\beta^0_t}')
        st.latex(r'\Delta WI_t=WI_t-WI_{t-1}')

    production=d.metadata()['production']['thresholds']
    wi=d.metadata()['wi']
    refs=wi['references']; wi_thresholds=wi['thresholds']
    st.markdown('#### Fixed screening choices')
    st.markdown(f'''| Baseline | Fixed reference population and endpoints | P90 · primary | P80 · sensitivity |
|---|---|---:|---:|
| Production relative index | Fixed-support Cropland · pooled 2023–2025 min/max | {production['p90']['threshold']:.4f} | {production['p80']['threshold']:.4f} |
| Rice raw-min/max relative index | Historical potential-rice ∩ Cropland · −44.826/+24.132 dB | Not rerun | Not rerun |
| Experimental Lovell WI | QC historical-rice P1/P99 · {refs['low_db']:.3f}/{refs['high_db']:.3f} dB | {wi_thresholds['p90']['threshold']:.3f} | {wi_thresholds['p80']['threshold']:.3f} |''')
    st.caption('The rice raw-min/max version is currently a reference-range sensitivity formulation, not a third screening result. Production and WI thresholds are derived independently and are not interchangeable moisture thresholds.')

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
    st.subheader('Reference Formulations and Literature Origin')
    st.caption('The rice-reference relative index isolates the effect of changing endpoints; the experimental WI also changes the equation.')

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

    st.markdown('#### Our three formulations')
    left,middle,right=st.columns(3)
    with left:
        st.markdown('**Baseline A · production relative SAR index**')
        st.latex(r'I_t=\operatorname{clip}\!\left(\frac{\beta^0_{high}-\beta^0_t}{\beta^0_{high}-\beta^0_{low}},0,1\right)')
        st.markdown('Linear normalization followed by clipping. Its fixed endpoints come from the production **Cropland** domain.')
    with middle:
        st.markdown('**Formulation B · rice raw-min/max relative index**')
        st.latex(r'I^{rice\,raw}_t=\operatorname{clip}\!\left(\frac{U_{rice}-\beta^0_t}{U_{rice}-L_{rice}},0,1\right)')
        st.markdown('Uses the same linear equation as Baseline A, but fixes the endpoints to the pooled historical potential-rice domain: **−44.826 dB** and **+24.132 dB**.')
        st.markdown('This is retained as a reference-range sensitivity formulation. Step 31 found that these raw extrema are processed observations but not representative validated wet/dry anchors.')
    with right:
        st.markdown('**Baseline C · experimental Lovell WI**')
        st.latex(r'WI_t=\frac{\beta^0_{low}-\beta^0_t}{\beta^0_{high}-\beta^0_t}')
        refs=d.metadata()['wi']['references']
        st.markdown(f"Uses the Step 32 QC historical-rice P1/P99 references: **{refs['low_db']:.3f} dB** and **{refs['high_db']:.3f} dB**.")
        st.markdown('Nonlinear and singular when β⁰ equals the high reference. It is not clipped in Step 35.')
    st.markdown('''Formulations A and B are the same linear transformation with different reference populations and endpoints; B therefore tests the consequence of selecting a rice-based raw range rather than adding independent moisture information. Formulation C changes both the reference definition and the equation. With identical references and units, the **unclipped** linear index and Lovell WI satisfy $WI=1-1/I$ wherever the denominator exists and $I\ne0$; this identity does not carry over unchanged after clipping or when the references differ.''')

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
