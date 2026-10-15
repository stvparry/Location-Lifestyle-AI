DIMS=['Active life','Learning & culture','Community','Family visits','Practicality','Outdoors','Water life','Property']
CAPS={'Active life':15,'Learning & culture':12,'Community':12,'Family visits':10,'Practicality':45,'Outdoors':10,'Water life':5}
def scores(e,prop=None):
 out={}
 for k in CAPS:out[k]=min(100,len(e['osm'][k])*100/CAPS[k]) if e['states'][k] else None
 if out['Learning & culture'] is not None:out['Learning & culture']=min(100,out['Learning & culture']+min(25,len(e['wiki']))+min(25,len(e['heritage'])/2))
 if out['Outdoors'] is not None:out['Outdoors']=min(100,out['Outdoors']+(10 if e['benches'] else 0))
 out['Property']=None if prop is None else min(100,35+prop.get('within',0)*15)
 return out
def property_sample(df,budget,name):
 if df is None:return None
 d=df.copy();d.columns=[str(x).lower().strip() for x in d.columns]
 if not {'area','price'}.issubset(d.columns):return {'error':'CSV requires area and price'}
 import pandas as pd
 d['price']=pd.to_numeric(d.price,errors='coerce');g=d[d.area.astype(str).str.contains(name,case=False,na=False)].dropna(subset=['price'])
 return {'count':len(g),'within':int((g.price<=budget).sum()),'median':None if g.empty else float(g.price.median()),'coverage':'USER-SUPPLIED SAMPLE'}
def horizons(user,s,e):
 def known(k):return s.get(k) is not None
 return {'0–3 years':[('Active life','Named provision supports the current brief.' if known('Active life') and s['Active life']>=45 else 'Active-life provision needs direct checking.'),('Interest','Culture, heritage and nearby-interest evidence is encouraging.' if known('Learning & culture') and s['Learning & culture']>=45 else 'Learning and cultural depth remains uncertain.'),('Property','A listing sample has been analysed.' if known('Property') else 'Live property availability remains an evidence gap.')],
 '3–8 years':[('Maintenance','Prioritise manageable upkeep.' if user['maintenance'] in ['Low','Very low'] else 'A broader property search fits the stated maintenance appetite.'),('Terrain',f"Local terrain samples span about {e['terrain']['range']:.0f} m; inspect actual walking routes." if e['terrain'] else 'Terrain evidence unavailable.'),('Adaptability','Prioritise adaptable or step-free layouts.' if user['stairs']!='No concern' else 'No stairs constraint was declared.')],
 '8–15 years':[('One-car test','Test healthcare, shopping, activity and social journeys with reduced car use.'),('Practicality','Returned practical provision is encouraging.' if known('Practicality') and s['Practicality']>=55 else 'Walkable essentials require direct verification.'),('Community','Returned community venues offer participation routes.' if known('Community') and s['Community']>=35 else 'Clubs and social connections need direct research.') ]}
