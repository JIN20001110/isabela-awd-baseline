"""English Streamlit page for system-specific seasonal reversal distributions."""
import base64
from pathlib import Path

import folium
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots
import release_data as d


def uri(path):return 'data:image/png;base64,'+base64.b64encode(Path(path).read_bytes()).decode()


def map_view(record, static_section):
    bounds=d.metadata()['study']['display_bounds'];center=[sum(x[0] for x in bounds)/2,sum(x[1] for x in bounds)/2]
    m=folium.Map(location=center,zoom_start=10.5,tiles=None,control_scale=True,min_zoom=7,max_zoom=18)
    folium.raster_layers.ImageOverlay(uri(d.STATIC/'context.png'),bounds=bounds,name='Excluded land cover',opacity=.7).add_to(m)
    folium.raster_layers.ImageOverlay(uri(d.STATIC/static_section/'participating_areas'/record['png']),bounds=bounds,name='Reversal count',opacity=.95).add_to(m)
    coverage=d.coverage_geojson()
    def thin_outline(feature):
        color=feature['properties'].get('color',[70,85,95,220])
        return {'color':'#%02x%02x%02x'%tuple(color[:3]),'weight':1,'opacity':.82,
            'fill':False,'fillOpacity':0,'interactive':False}
    folium.GeoJson(coverage,name='Irrigation-system outlines',style_function=thin_outline,
        tooltip=False,control=True).add_to(m)
    folium.LayerControl(collapsed=False).add_to(m);return m


def render(reference='production'):
    rice=reference == 'rice_raw'
    page_name='Rice-derived reference' if rice else 'Cropland reference'
    key_prefix='ri_fields_rice' if rice else 'ri_fields_cropland'
    st.subheader(f'RI · Participating fields · {page_name}')
    st.caption('Cropland inside the supplied MARIIS, UCRIS and MRIS fields. “Rice-derived” describes the fixed endpoints; it does not restrict the displayed pixels to the historical-rice layer.')
    section='rice_raw/participating_areas' if rice else 'production/participating_areas'
    static_section='rice_raw' if rice else 'production'
    meta_key='rice_raw_relative_index' if rice else 'production'
    windows=d.table(section,'window_summary.parquet')
    distribution=d.table(section,'area_distribution.parquet')
    fields=d.table(section,'field_summary.parquet')
    records={(row['threshold'],row['window_id']):row for row in d.map_index(section)}

    st.markdown('''| System | Dry window | Wet window |
|---|---|---|
| MARIIS | September–February | May–October |
| UCRIS | November–April | July–December |
| MRIS | January–May | August–December |''')
    system=st.selectbox('Irrigation system',list(d.CALENDAR),key=f'{key_prefix}_system')
    season=st.radio('Cropping season',['Dry','Wet'],horizontal=True,key=f'{key_prefix}_season')
    threshold=st.radio('Change threshold',['p90','p80'],horizontal=True,key=f'{key_prefix}_threshold',
        format_func=lambda x:'P90 · primary' if x=='p90' else 'P80 · sensitivity')
    threshold_value=d.metadata()[meta_key]['thresholds'][threshold]['threshold']
    reference_note=('Historical potential-rice ∩ Cropland raw min/max (−44.826/+24.132 dB)' if rice
                    else 'fixed-support Cropland raw min/max')
    st.caption(f'{reference_note}. {threshold.upper()} uses |ΔI| ≥ {threshold_value:.4f}; P90 retains the largest 10% and P80 the largest 20% of all 2023–2025 Cropland changes.')
    available=windows.loc[windows.system.eq(system)&windows.season.eq(season)&windows.threshold.eq(threshold)].copy()
    chosen=st.selectbox('Window',available.window_id.tolist(),
        format_func=dict(zip(available.window_id,available.label)).get,key=f'{key_prefix}_window')
    summary=available.loc[available.window_id.eq(chosen)].iloc[0]
    c1,c2,c3,c4=st.columns(4)
    c1.metric('Valid 12-day pairs',f'{int(summary.pairs)}')
    c2.metric('0 reversals',f'{summary.percent_0_reversals:.1f}%')
    c3.metric('1 reversal',f'{summary.percent_1_reversal:.1f}%')
    c4.metric('2+ reversals',f'{summary.percent_2plus_reversals:.1f}%')

    selected=distribution.loc[distribution.window_id.eq(chosen)&distribution.threshold.eq(threshold)].copy()
    colors={'0':'#D8C3A5','1':'#DCEEF7','2':'#72B7D6','3+':'#155A8A'}
    fig=go.Figure(go.Pie(labels=[f'{x} reversals' for x in selected.reversal_group],
        values=selected.percent_system_cropland_area,hole=.58,sort=False,
        marker=dict(colors=[colors[x] for x in selected.reversal_group]),
        customdata=selected[['cropland_area_ha','cropland_pixels']],textinfo='label+percent',textposition='inside',
        hovertemplate='%{label}<br>%{value:.2f}%<br>%{customdata[0]:,.1f} ha<br>%{customdata[1]:,} pixels<extra></extra>'))
    fig.update_layout(template='plotly_white',height=410,showlegend=True,
        legend=dict(orientation='h',y=-.08,x=.5,xanchor='center'),margin=dict(l=20,r=20,t=15,b=55),
        annotations=[dict(text='<b>Cropland<br>area</b>',x=.5,y=.5,showarrow=False)])
    st.plotly_chart(fig,width='stretch')

    st.markdown('### Map')
    st.iframe(map_view(records[(threshold,chosen)],static_section).get_root().render(),height=760)
    st.caption('Light brown = 0 · very light blue = 1 · light blue = 2 · dark blue = 3+ reversals. Only Cropland inside supplied fields is shown.')

    st.markdown('### Compare complete windows')
    compare=distribution.loc[distribution.system.eq(system)&distribution.season.eq(season)&distribution.threshold.eq(threshold)].copy()
    labels=compare[['window_id','label']].drop_duplicates().label.tolist()
    rings=make_subplots(rows=1,cols=len(labels),specs=[[{'type':'domain'}]*len(labels)],subplot_titles=labels)
    for col,label in enumerate(labels,1):
        part=compare.loc[compare.label.eq(label)]
        rings.add_trace(go.Pie(labels=[f'{x} reversals' for x in part.reversal_group],
            values=part.percent_system_cropland_area,hole=.58,sort=False,
            marker=dict(colors=[colors[x] for x in part.reversal_group]),
            customdata=part[['cropland_area_ha','cropland_pixels']],textinfo='percent',textposition='inside',
            hovertemplate='%{label}<br>%{value:.2f}%<br>%{customdata[0]:,.1f} ha<br>%{customdata[1]:,} pixels<extra></extra>',
            name=label,legendgroup='reversals',showlegend=col==1),row=1,col=col)
    rings.update_layout(template='plotly_white',height=390,
        legend=dict(title='Direction reversals',orientation='h',y=-.08,x=.5,xanchor='center'),
        margin=dict(l=20,r=20,t=55,b=60))
    st.plotly_chart(rings,width='stretch')

    selected_fields=fields.loc[fields.window_id.eq(chosen)&fields.threshold.eq(threshold)&fields.cropland_pixels.gt(0)].copy()
    with st.expander('Review candidate fields'):
        minimum=st.number_input('Minimum Cropland pixels',min_value=1,max_value=100,value=5,step=1,key=f'{key_prefix}_min_pixels')
        ranked=selected_fields.loc[selected_fields.cropland_pixels.ge(minimum)].sort_values(
            ['percent_pixels_2plus_reversals','mean_reversals','cropland_pixels'],ascending=False)
        show=ranked[['field_uid','field_id','field_area_ha','cropland_pixels','percent_pixels_0_reversals',
            'percent_pixels_1_reversal','percent_pixels_2_reversals','percent_pixels_3plus_reversals',
            'percent_pixels_2plus_reversals','mean_reversals','material_overlap_flag']]
        st.dataframe(show.head(500).style.format({c:'{:.1f}' for c in show.columns if c.startswith('percent_')}),hide_index=True,width='stretch')
        st.caption('Ranked by the field share with 2+ reversals. Review priority only—not confirmed AWD.')
    with st.expander('Downloads and limitations'):
        st.download_button('Download selected area distribution (CSV)',selected.to_csv(index=False),
            file_name=f'{"36o-rice-raw" if rice else "26o-production"}-{chosen}-area-distribution.csv',mime='text/csv')
        st.download_button('Download selected field summary (CSV)',selected_fields.to_csv(index=False),
            file_name=f'{"36o-rice-raw" if rice else "26o-production"}-{chosen}-field-summary.csv',mime='text/csv')
        st.download_button('Download all window summaries (CSV)',windows.to_csv(index=False),
            file_name=f'{"36o-rice-raw" if rice else "26o-production"}-all-window-summary.csv',mime='text/csv')
        st.markdown('''- P90 and P80 are both fixed from the full 2023–2025 Cropland history and are not refitted by system or season.
- P90 is the primary screening result. P80 is a more inclusive sensitivity result; patterns present under both thresholds are more stable.
- Counts depend on the number of valid 12-day pairs; compare windows with similar coverage and always retain the pair count.
- Lex’s 2026 calendar is repeated over 2023–2025 as an assumption. Overlapping Dry/Wet windows are retained.
- Higher counts identify candidate repeated wetting–drying dynamics; they do not independently confirm AWD.''')
