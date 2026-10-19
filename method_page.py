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
    st.caption('Three fixed-reference SAR formulations, each shown at two spatial scales. The rice layer defines reference endpoints in two experimental branches; it is not automatically the displayed application mask.')
    st.markdown(STYLE+'''<div class="method-flow">
<div class="method-step"><b>1 · Study observations</b><span>Isabela AOI · 2023–2025<br>S1A descending R032 · 88 dates</span></div>
<div class="method-step"><b>2 · Shared β⁰ preparation</b><span>Calibrated σ⁰ + incidence angle<br>β⁰ estimate · 3×3 spatial median</span></div>
<div class="method-step production"><b>3A · Production reference</b><span>Fixed-support Cropland<br>One pooled 2023–2025 min/max range</span></div>
<div class="method-step sensitivity"><b>3B · Rice raw-extrema reference</b><span>Historical potential-rice ∩ Cropland<br>One pooled 2023–2025 min/max range</span></div>
<div class="method-step wi"><b>3C · Experimental WI reference</b><span>QC historical-rice domain<br>One pooled 2023–2025 P1/P99 range</span></div>
<div class="method-step production"><b>4A · Relative SAR index</b><span>Linear normalization + clipping<br>Calculate adjacent ΔI</span></div>
<div class="method-step sensitivity"><b>4B · Rice-reference relative index</b><span>Same linear equation, different endpoints<br>Calculate adjacent ΔI</span></div>
<div class="method-step wi"><b>4C · Published Lovell WI</b><span>Nonlinear equation · no clipping<br>Exclude unstable/out-of-range observations</span></div>
<div class="method-step"><b>5 · Independent thresholds</b><span>Each formulation derives its own P90 primary and P80 sensitivity threshold</span></div>
<div class="method-step"><b>6 · Temporal continuity</b><span>Use valid adjacent observations only<br>Missing or excluded dates break the sequence</span></div>
<div class="method-step"><b>7 · Cropping windows</b><span>Whole-region common windows<br>System-specific MARIIS/UCRIS/MRIS windows</span></div>
<div class="method-step"><b>8 · Direction reversals</b><span>Count significant changes that switch direction within each window</span></div>
<div class="method-step output"><b>9 · Screening outputs</b><span>0 · 1 · 2 · 3+ reversals<br>Regional maps and field-level review</span></div>
<div class="method-step output"><b>10 · Interpretation</b><span>Potential AWD-like SAR patterns<br>Not measured water level or confirmed AWD</span></div>
</div>''',unsafe_allow_html=True)

    st.markdown('#### How the eight pages fit together')
    st.markdown('''| Page group | Reference source | Application area | Purpose |
|---|---|---|---|
| RI · All area / Participating fields · Cropland ref | Full fixed-support Cropland raw min/max | Cropland in the full AOI or participating fields | Current production baseline |
| RI · All area / Participating fields · Rice ref | Historical potential-rice ∩ Cropland raw min/max | The same Cropland application areas | Reference-range sensitivity |
| WI · All area / Participating fields · Rice ref | QC historical-rice P1/P99 | Eligible Cropland in the same two spatial scales | Experimental published-formula evaluation |
| Comparison | All three configurations | One selected like-for-like spatial window | Direct visual comparison |''')
    st.info('“Rice ref” means **rice-derived endpoints**. It does not mean that only historical-rice pixels are displayed or that rice cultivation was confirmed in 2023–2025.')

    st.markdown('#### Core calculations')
    st.latex(r'\beta^0_{est,dB}=\sigma^0_{dB}-10\log_{10}(\sin\theta)')
    left,middle,right=st.columns(3)
    with left:
        st.markdown('**Baseline A · production relative SAR index**')
        st.latex(r'RI_t=\operatorname{clip}\!\left(\frac{U_{crop}-\beta^0_t}{U_{crop}-L_{crop}},0,1\right)')
        st.latex(r'\Delta RI_t=RI_t-RI_{t-1}')
    with middle:
        st.markdown('**Formulation B · rice raw-min/max relative index**')
        st.latex(r'I^{rice\,raw}_t=\operatorname{clip}\!\left(\frac{U_{rice}-\beta^0_t}{U_{rice}-L_{rice}},0,1\right)')
        st.latex(r'L_{rice}=-44.826,\quad U_{rice}=24.132\ \mathrm{dB}')
    with right:
        st.markdown('**Baseline C · experimental Lovell WI**')
        st.latex(r'WI_t=\frac{\beta^0_{low}-\beta^0_t}{\beta^0_{high}-\beta^0_t}')
        st.latex(r'\Delta WI_t=WI_t-WI_{t-1}')

    production=d.metadata()['production']['thresholds']
    rice_raw=d.metadata()['rice_raw_relative_index']
    wi=d.metadata()['wi']
    refs=wi['references']; wi_thresholds=wi['thresholds']
    st.markdown('#### Fixed screening choices')
    st.markdown(f'''| Formulation | Fixed reference population and endpoints | Application domain | P90 · primary | P80 · sensitivity |
|---|---|---|---:|---:|
| Production RI | Fixed-support Cropland · pooled 2023–2025 min/max | Fixed-support Cropland | {production['p90']['threshold']:.4f} | {production['p80']['threshold']:.4f} |
| Rice-reference RI | Historical potential-rice ∩ Cropland · −44.826/+24.132 dB | The same fixed-support Cropland | {rice_raw['thresholds']['p90']['threshold']:.4f} | {rice_raw['thresholds']['p80']['threshold']:.4f} |
| Experimental Lovell WI | QC historical-rice P1/P99 · {refs['low_db']:.3f}/{refs['high_db']:.3f} dB | Eligible Cropland after WI numerical checks | {wi_thresholds['p90']['threshold']:.3f} | {wi_thresholds['p80']['threshold']:.3f} |''')
    st.caption('All three thresholds were derived independently from each formulation’s full 2023–2025 eligible Cropland pixel-pair distribution. They are not interchangeable moisture thresholds.')

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
        st.markdown('The reference-range sensitivity analysis used independently derived P80/P90 thresholds. Extreme-value diagnostics found that the raw extrema are processed observations but not representative validated wet/dry anchors.')
    with right:
        st.markdown('**Baseline C · experimental Lovell WI**')
        st.latex(r'WI_t=\frac{\beta^0_{low}-\beta^0_t}{\beta^0_{high}-\beta^0_t}')
        refs=d.metadata()['wi']['references']
        st.markdown(f"Uses the QC historical-rice P1/P99 references: **{refs['low_db']:.3f} dB** and **{refs['high_db']:.3f} dB**.")
        st.markdown('Nonlinear and singular when β⁰ equals the high reference. It is not clipped in the experimental screening.')
    st.markdown('''Formulations A and B are the same linear transformation with different reference populations and endpoints; B therefore tests the consequence of selecting a rice-based raw range rather than adding independent moisture information. Formulation C changes both the reference definition and the equation. With identical references and units, the **unclipped** linear index and Lovell WI satisfy $WI=1-1/I$ wherever the denominator exists and $I\ne0$; this identity does not carry over unchanged after clipping or when the references differ.''')

    st.markdown('#### How the experimental WI baseline was developed')
    st.markdown('''| Step | Evidence added |
|---|---|
| Step 1 · Rice distribution | Open-SEA-Rice-10 provided a historical potential-rice support layer inside the Cropland AOI. |
| Step 2 · Raw references | Raw rice-domain extrema were inspected rather than accepted automatically. |
| Step 3 · Extreme diagnostics | Episodic low values and persistent high features near built-up boundaries were traced in space and time. |
| Step 4 · Robust references | QC historical-rice pooled 2023–2025 P1/P99 were selected as statistical endpoints. |
| Step 5 · Published WI | The printed Lovell equation was reproduced in separate dB and linear-power branches. |
| Step 6 · Temporal feasibility | Change direction, singularity risk, reversals, seasons, and rainfall consistency were diagnosed. |
| Step 7 · Baseline screening | WI-specific P90/P80 thresholds, regional/field results, and comparison with Production RI were produced. |''')
    st.markdown('**Step 8 · Rice raw-min/max sensitivity:** the same linear relative-index equation was rerun using the pooled historical-rice raw extrema, with independent P80/P90 thresholds and full regional/field outputs. The resulting reversal distributions were nearly unchanged from production, showing that this endpoint change primarily rescales the index rather than adding new temporal information.')
    st.markdown('The primary WI branch uses the unchanged published equation with dB values. The publication does not resolve the calculation unit, so linear power remains a separate sensitivity result. Only inside-range, numerically stable observations are screened; exclusions are retained explicitly and break temporal continuity.')

    with st.expander('Scientific interpretation and limitations'):
        st.markdown('''- Historical potential rice does not confirm rice cultivation in every 2023–2025 season.
- There are no local Isabela field water-level measurements for direct hydrological validation.
- Lower β⁰ is provisionally interpreted as wetter-like and higher β⁰ as drier-like; canopy, roughness, rainfall, harvest and mixed pixels can alter that relationship.
- WI is unitless—not soil-moisture percentage or water depth.
- A mathematical reversal is not a complete AWD cycle and cannot establish an irrigation date.
- The approximately 12-day sampling interval can miss shorter physical changes.
- The Lovell WI has a singularity at the high reference; near-singular and out-of-range observations are excluded from conservative screening but remain reported.
- Neither formula is proven superior for retrieving water conditions in Isabela.''')
    st.info('Result language: potential AWD-like SAR patterns for pre-intervention prioritization—not confirmed AWD adoption.')
