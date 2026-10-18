"""Public Streamlit dashboard for the Isabela pre-intervention SAR baseline."""
from __future__ import annotations

import streamlit as st

import comparison_page
import method_page
import production_participating_page
import production_whole_region_page
import wi_participating_page
import wi_whole_region_page


st.set_page_config(page_title="Isabela · SAR Baseline", page_icon="🌾", layout="wide")
st.markdown(
    """<style>
    .block-container {padding-top:2rem;max-width:1550px;}
    [data-testid="stMetricValue"] {font-size:1.65rem;}
    [data-testid="stSidebar"] {background:#f2f5f4;}
    h1 {letter-spacing:-.035em;} .stCaption {line-height:1.6;}
    </style>""",
    unsafe_allow_html=True,
)

PAGES = [
    "Method",
    "RI · All area · Cropland ref",
    "RI · Fields · Cropland ref",
    "RI · All area · Rice ref",
    "RI · Fields · Rice ref",
    "WI · All area · Rice ref",
    "WI · Fields · Rice ref",
    "Comparison",
]

st.sidebar.title("🌾 SAR Baseline")
st.sidebar.caption("Isabela · 2023–2025\nPublic research dashboard")
page = st.sidebar.radio("Explore", PAGES)
st.sidebar.divider()
st.sidebar.caption(
    "How to read the results:\n"
    "SAR change ≠ measured water level\n"
    "A reversal ≠ a complete AWD cycle\n"
    "Candidate pattern ≠ confirmed AWD adoption"
)

st.title("Isabela · AWD baseline screening")

if page == "Method":
    method_page.render()
elif page == "RI · All area · Cropland ref":
    production_whole_region_page.render(reference="production")
elif page == "RI · Fields · Cropland ref":
    production_participating_page.render(reference="production")
elif page == "RI · All area · Rice ref":
    production_whole_region_page.render(reference="rice_raw")
elif page == "RI · Fields · Rice ref":
    production_participating_page.render(reference="rice_raw")
elif page == "WI · All area · Rice ref":
    wi_whole_region_page.render()
elif page == "WI · Fields · Rice ref":
    wi_participating_page.render()
else:
    comparison_page.render()
