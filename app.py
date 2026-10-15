import pandas as pd,plotly.graph_objects as go,streamlit as st
from connectors.core import geocode,local_features,police,food_hygiene,route,headlines
from connectors.optional import propertydata_prices,opentripmap
from engines.profile import DIMENSIONS,score_location,horizon_assessment
from engines.property import analyse_listings
from reports.html_report import make_report
st.set_page_config(page_title='Location Lifestyle AI',page_icon='🏡',layout='wide')
st.markdown('''<style>.hero{padding:28px;border-radius:22px;background:linear-gradient(120deg,#123f52,#0f766e);color:white}.stButton button,.stDownloadButton button{background:#0f766e;color:white;border:none}[data-testid=stMetric]{background:white;border:1px solid #dce9e4;padding:10px;border-radius:14px}</style>''',unsafe_allow_html=True)
st.markdown('<div class=hero><h1>🏡 Location Lifestyle AI</h1><p>Discover what life could really be like, now and over the next 15 years.</p></div>',unsafe_allow_html=True)
if 'result' not in st.session_state:st.session_state.result=None
def picker(title,key,default):
 st.subheader(title);q=st.text_input('Town, county, address or postcode',default,key=key+'q',label_visibility='collapsed');rows=geocode(q) if q else []
 if not rows:return None
 return rows[st.selectbox('Confirm match',range(len(rows)),format_func=lambda i:rows[i]['label'],key=key+'s')]
with st.sidebar:
 st.header('Lifestyle priorities');weights={x:st.slider(x,0,10,7 if x in ['Active life','Outdoors','Practicality'] else 5,key=x) for x in DIMENSIONS};radius=st.select_slider('Local evidence radius',[1000,2000,3000,5000],3000,format_func=lambda x:f'{x/1000:g} km')
a1,a2=st.columns(2)
with a1:a=picker('Current location','a','Marlow, Buckinghamshire')
with a2:b=picker('Possible destination','b','Henley-on-Thames, Oxfordshire')
st.subheader('Regular family, work or care destination');tq=st.text_input('Journey destination',placeholder='e.g. St Albans, Heathrow or a postcode');trs=geocode(tq) if tq else [];target=trs[st.selectbox('Confirm journey destination',range(len(trs)),format_func=lambda i:trs[i]['label'],key='target')] if trs else None
with st.expander('Household and next-chapter profile',expanded=True):
 c1,c2,c3=st.columns(3);household=c1.selectbox('Household',['One person','Couple','Family','Empty nesters','Retired couple','Multi-generational']);life_stage=c2.selectbox('Life stage',['Working','Semi-retired','Retired','Future planning']);budget=c3.number_input('Purchase budget (£)',0,10000000,1000000,25000)
 c1,c2,c3=st.columns(3);stay=c1.selectbox('Expected stay',['Under 5 years','5–10 years','10–15 years','15+ years']);maintenance=c2.selectbox('Maintenance appetite',['High','Moderate','Low','Very low']);stairs=c3.selectbox('Stairs over time',['No concern','Prefer fewer stairs','Step-free important'])
 c1,c2=st.columns(2);future_car=c1.selectbox('Likely car use in 8–15 years',['Two or more cars','One car','No car','Unsure']);bedrooms=c2.selectbox('Target bedrooms',[1,2,3,4,5],index=3);must=st.text_area('Must-haves',placeholder='Tennis, swimming, Spanish, cafés, river walks, family access…');avoid=st.text_area('Deal-breakers',placeholder='Steep hills, isolation, heavy traffic, too much maintenance…')
with st.expander('Optional current-listing sample',expanded=False):
 st.caption('Upload a CSV with area and price. Optional columns: property_type, bedrooms, url. A sample is included in the ZIP.');upload=st.file_uploader('Listings CSV',type=['csv']);listing_df=pd.read_csv(upload) if upload else None
with st.expander('Optional enhanced connectors',expanded=False):
 pd_key=st.secrets.get('PROPERTYDATA_API_KEY','') if hasattr(st,'secrets') else '';otm_key=st.secrets.get('OPENTRIPMAP_API_KEY','') if hasattr(st,'secrets') else ''
 st.write('PropertyData: '+('configured' if pd_key else 'not configured'));st.write('OpenTripMap: '+('configured' if otm_key else 'not configured'))
if st.button('Build lifestyle comparison',type='primary',use_container_width=True) and a and b:
 with st.spinner('Collecting lifestyle evidence…'):
  fa,fsa=local_features(a,radius);fb,fsb=local_features(b,radius);ca,csa=police(a);cb,csb=police(b);fda,fdsa=food_hygiene(a,radius/1000);fdb,fdsb=food_hygiene(b,radius/1000);ha,hsa=headlines(a['label'].split(',')[0]);hb,hsb=headlines(b['label'].split(',')[0]);ja,jsa=route(a,target);jb,jsb=route(b,target);ota,otsa=opentripmap(a,otm_key);otb,otsb=opentripmap(b,otm_key);pda,pdsa=propertydata_prices(a.get('postcode',''),bedrooms,pd_key);pdb,pdsb=propertydata_prices(b.get('postcode',''),bedrooms,pd_key)
  ea={'features':fa,'crime':ca,'food':fda,'headlines':ha,'attractions':ota};eb={'features':fb,'crime':cb,'food':fdb,'headlines':hb,'attractions':otb}
  pa=analyse_listings(listing_df,budget,a['label'].split(',')[0]);pb=analyse_listings(listing_df,budget,b['label'].split(',')[0]);property_score_a=50 if not pa else min(100,50+pa.get('within',0)*10);property_score_b=50 if not pb else min(100,50+pb.get('within',0)*10);sa=score_location(ea,weights,property_score_a);sb=score_location(eb,weights,property_score_b)
  user={'household':household,'life_stage':life_stage,'budget':budget,'stay':stay,'maintenance':maintenance,'stairs':stairs,'future_car':future_car,'must':must,'avoid':avoid};h=horizon_assessment(user,sb)
  statuses=[fsa,fsb,csa,csb,fdsa,fdsb,hsa,hsb,jsa,jsb,otsa,otsb,pdsa,pdsb]
  st.session_state.result={'a':a,'b':b,'target':target,'evidence_a':ea,'evidence_b':eb,'scores_a':sa,'scores_b':sb,'property_a':pa,'property_b':pb,'propertydata_a':pda,'propertydata_b':pdb,'journey_a':ja,'journey_b':jb,'horizons':h,'statuses':statuses,'user':user}
r=st.session_state.result
if r:
 st.success('Lifestyle comparison complete. Missing sources were excluded or labelled.')
 cats=list(r['scores_a']);fig=go.Figure()
 for vals,name,col in [(r['scores_a'],'Current','#2563eb'),(r['scores_b'],'Destination','#0f766e')]:fig.add_trace(go.Scatterpolar(r=[vals[k] for k in cats]+[vals[cats[0]]],theta=cats+[cats[0]],fill='toself',name=name,line_color=col))
 fig.update_layout(polar=dict(radialaxis=dict(range=[0,100],visible=True)),height=500);st.plotly_chart(fig,use_container_width=True)
 st.subheader('Next chapter fit')
 cols=st.columns(3)
 for i,(hz,items) in enumerate(r['horizons'].items()):
  with cols[i]:
   st.markdown('#### '+hz)
   for label,text,good in items:st.write(('✅ ' if good else '⚠️ ')+text)
 for title,key in [('Stay active','Active life'),('Curious mind','Culture'),('Find your tribe','Community'),('Family visits','Family'),('Outdoors','Green space'),('Blue-space life','Blue space')]:
  with st.expander(title):st.write(', '.join(r['evidence_b']['features'][key][:12]) or 'No named examples returned from the live map source.')
 if r['journey_b']:st.metric('Destination to regular journey point',f"{r['journey_b']['miles']:.0f} mi · {r['journey_b']['minutes']:.0f} min")
 st.download_button('⬇ Download personalised lifestyle report',make_report(r),'location_lifestyle_ai_report.html','text/html',type='primary',use_container_width=True)
 with st.expander('Source health',expanded=True):
  for s in r['statuses']:st.markdown(('✅' if s['ok'] else '⚠️')+f" **{s['source']}**: {s['detail']}")
st.caption('Location Lifestyle AI v1.0 · Evidence-led orientation, not property, medical or financial advice.')
