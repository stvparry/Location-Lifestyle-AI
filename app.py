import pandas as pd,plotly.graph_objects as go,streamlit as st
from connectors.sources import geocode,collect,headlines,route
from engines.analysis import DIMS,scores,property_sample,horizons
from reports.report import make
st.set_page_config(page_title='Location Lifestyle AI v1.2',page_icon='🏡',layout='wide')
st.markdown('<div style="padding:26px;border-radius:20px;background:linear-gradient(120deg,#123f52,#0f766e);color:white"><h1>🏡 Location Lifestyle AI v1.2</h1><p>Multi-source evidence edition: split map queries, heritage, nearby knowledge, terrain, food, crime and local pulse.</p></div>',unsafe_allow_html=True)
if 'r' not in st.session_state:st.session_state.r=None
def pick(label,key,default):
 q=st.text_input(label,default,key=key+'q');x=geocode(q) if q else []
 if not x:return None
 return x[st.selectbox('Confirm '+label,range(len(x)),format_func=lambda i:x[i]['label'],key=key+'s')]
with st.sidebar:radius=st.select_slider('Evidence radius',[1000,2000,3000,5000],5000,format_func=lambda x:f'{x/1000:g} km')
c1,c2=st.columns(2)
with c1:a=pick('Current location','a','Marlow, Buckinghamshire')
with c2:b=pick('Destination','b','Henley-on-Thames, Oxfordshire')
tq=st.text_input('Regular family/work/care destination');t=geocode(tq) if tq else [];target=t[st.selectbox('Confirm regular destination',range(len(t)),format_func=lambda i:t[i]['label'])] if t else None
with st.expander('Household and next chapter',expanded=True):
 c1,c2,c3=st.columns(3);house=c1.selectbox('Household',['Couple','One person','Family','Retired couple']);stage=c2.selectbox('Life stage',['Working','Semi-retired','Retired']);budget=c3.number_input('Budget (£)',0,10000000,1900000,25000);maintenance=st.selectbox('Maintenance appetite',['High','Moderate','Low','Very low']);stairs=st.selectbox('Stairs over time',['No concern','Prefer fewer stairs','Step-free important']);must=st.text_area('Must-haves');avoid=st.text_area('Deal-breakers')
with st.expander('Optional listing evidence'):up=st.file_uploader('CSV columns: area, price',type=['csv']);df=pd.read_csv(up) if up else None
if st.button('Build multi-source comparison',type='primary',use_container_width=True) and a and b:
 with st.spinner('Consulting independent evidence sources…'):
  ea,sta=collect(a,radius);eb,stb=collect(b,radius);pa=property_sample(df,budget,a['label'].split(',')[0]);pb=property_sample(df,budget,b['label'].split(',')[0]);sa,sb=scores(ea,pa),scores(eb,pb);hz=horizons({'maintenance':maintenance,'stairs':stairs},sb,eb);ja,jasa=route(a,target);jb,jbsb=route(b,target);ha,hasa=headlines(a['label'].split(',')[0]);hb,hbsb=headlines(b['label'].split(',')[0]);st.session_state.r={'a':a,'b':b,'ea':ea,'eb':eb,'sa':sa,'sb':sb,'hz':hz,'pa':pa,'pb':pb,'ja':ja,'jb':jb,'ha':ha,'hb':hb,'statuses':sta+stb+[jasa,jbsb,hasa,hbsb]}
r=st.session_state.r
if r:
 st.success('Comparison complete. Each unavailable category is excluded, not scored as zero.')
 records_a=sum(len(v) for v in r['ea']['osm'].values())+len(r['ea']['wiki'])+len(r['ea']['heritage']);records_b=sum(len(v) for v in r['eb']['osm'].values())+len(r['eb']['wiki'])+len(r['eb']['heritage']);c1,c2=st.columns(2);c1.metric('Current named evidence records',records_a);c2.metric('Destination named evidence records',records_b)
 known=[k for k in DIMS if r['sa'].get(k) is not None and r['sb'].get(k) is not None]
 if known:
  fig=go.Figure();fig.add_bar(name='Current',x=known,y=[r['sa'][k] for k in known]);fig.add_bar(name='Destination',x=known,y=[r['sb'][k] for k in known]);fig.update_layout(barmode='group',yaxis_range=[0,100]);st.plotly_chart(fig,use_container_width=True)
 st.subheader('Destination evidence counts')
 st.dataframe(pd.DataFrame({'Dimension':list(r['eb']['osm']),'Named map records':[len(v) for v in r['eb']['osm'].values()],'Status':['Available' if r['eb']['states'][k] else 'Unavailable' for k in r['eb']['osm']]}),hide_index=True,use_container_width=True)
 c1,c2,c3=st.columns(3);c1.metric('Wikipedia nearby',len(r['eb']['wiki']));c2.metric('Listed-building records',len(r['eb']['heritage']));c3.metric('OpenBenches','N/A' if r['eb']['benches'] is None else r['eb']['benches'])
 for title,key in [('Stay active','Active life'),('Culture & learning','Learning & culture'),('Find your tribe','Community'),('Family visits','Family visits'),('Daily practicality','Practicality'),('Outdoors','Outdoors'),('Water life','Water life')]:
  with st.expander(title):st.write(', '.join(r['eb']['osm'][key][:20]) or 'No named records returned, or source unavailable.')
 st.download_button('⬇ Download multi-source report',make(r),'location_lifestyle_ai_v1_2_report.html','text/html',type='primary',use_container_width=True)
 with st.expander('Source health',expanded=True):
  for x in r['statuses']:st.markdown(('✅' if x['ok'] else '⚠️')+f" **{x['source']}**: {x['detail']}")
st.caption('v1.2 · Evidence coverage varies by source and geography. Scores indicate returned provision, not intrinsic quality.')
