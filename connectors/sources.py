import re,math,requests,xml.etree.ElementTree as ET
UA={'User-Agent':'Location-Lifestyle-AI/1.2 contact: educational-use'}
def call(url,params=None,timeout=35,headers=None):
 r=requests.get(url,params=params,headers=headers or UA,timeout=timeout);r.raise_for_status();return r
def geocode(q):
 out=[];q=q.strip();m=re.search(r'\b([A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2})\b',q.upper())
 if m:
  try:
   x=call('https://api.postcodes.io/postcodes/'+m.group(1).replace(' ','')).json()['result'];out.append({'label':f"{x['postcode']} · {x.get('admin_district','')}",'lat':x['latitude'],'lon':x['longitude']})
  except Exception:pass
 try:
  for x in call('https://nominatim.openstreetmap.org/search',{'q':q+', United Kingdom','format':'jsonv2','limit':6,'countrycodes':'gb'}).json():
   z={'label':x['display_name'],'lat':float(x['lat']),'lon':float(x['lon'])}
   if not any(abs(z['lat']-v['lat'])<.0001 and abs(z['lon']-v['lon'])<.0001 for v in out):out.append(z)
 except Exception:pass
 return out
CATEGORIES={
'Active life':'node[leisure~"fitness_centre|sports_centre|swimming_pool|golf_course|pitch|track"];way[leisure~"fitness_centre|sports_centre|swimming_pool|golf_course|pitch|track"];node[sport~"tennis|fitness|swimming|golf|padel"]',
'Learning & culture':'node[amenity~"theatre|cinema|library|arts_centre"];node[tourism~"museum|gallery|attraction"]',
'Community':'node[amenity~"community_centre|social_centre|place_of_worship|marketplace"]',
'Family visits':'node[leisure~"playground|water_park|miniature_golf"];node[tourism~"zoo|theme_park|museum|attraction"]',
'Practicality':'node[shop];node[amenity~"hospital|clinic|doctors|pharmacy|dentist|bank|post_office|atm"];node[railway=station];node[highway=bus_stop]',
'Outdoors':'node[leisure=park];way[leisure=park];node[natural~"wood|peak|beach"];way[natural=wood]',
'Water life':'node[leisure=marina];way[leisure=marina];node[sport~"rowing|canoe|sailing"];way[sport~"rowing|canoe|sailing"]'}
ENDPOINTS=['https://overpass.kumi.systems/api/interpreter','https://overpass-api.de/api/interpreter','https://overpass.nchc.org.tw/api/interpreter']
def overpass_category(loc,radius,category,fragment):
 clauses=''.join(x+f'(around:{radius},{loc["lat"]},{loc["lon"]});' for x in fragment.split(';') if x)
 q='[out:json][timeout:18];('+clauses+');out center tags;'
 for ep in ENDPOINTS:
  try:
   rows=call(ep,{'data':q},30).json().get('elements',[]);names=[]
   for e in rows:
    n=e.get('tags',{}).get('name')
    if n and n not in names:names.append(n)
   return names,{'ok':True,'source':'OpenStreetMap – '+category,'detail':f'{len(rows)} objects, {len(names)} named'},True
  except Exception:pass
 return [],{'ok':False,'source':'OpenStreetMap – '+category,'detail':'All endpoints failed; category unavailable'},False
def overpass_all(loc,radius):
 items={};states={};statuses=[]
 for k,v in CATEGORIES.items():items[k],s,states[k]=overpass_category(loc,radius,k,v);statuses.append(s)
 return items,states,statuses
def wikipedia_nearby(loc,radius=10000):
 try:
  x=call('https://en.wikipedia.org/w/api.php',{'action':'query','list':'geosearch','gscoord':f"{loc['lat']}|{loc['lon']}",'gsradius':min(radius,10000),'gslimit':30,'format':'json','origin':'*'}).json()['query']['geosearch'];return [a['title'] for a in x],{'ok':True,'source':'Wikipedia Geosearch','detail':f'{len(x)} nearby articles'}
 except Exception:return [],{'ok':False,'source':'Wikipedia Geosearch','detail':'Unavailable'}
def historic(loc,radius_m=5000):
 try:
  deg=radius_m/111000;geom=f"{loc['lon']-deg},{loc['lat']-deg},{loc['lon']+deg},{loc['lat']+deg}"
  url='https://services-eu1.arcgis.com/ZOdPfBS3aqqDYPUQ/arcgis/rest/services/National_Heritage_List_for_England_NHLE_v02_VIEW/FeatureServer/0/query'
  p={'where':'1=1','geometry':geom,'geometryType':'esriGeometryEnvelope','inSR':4326,'spatialRel':'esriSpatialRelIntersects','outFields':'Name,Grade,hyperlink','returnGeometry':'false','f':'json','resultRecordCount':100}
  feats=call(url,p,40).json().get('features',[]);rows=[{'name':f.get('attributes',{}).get('Name') or 'Unnamed','grade':f.get('attributes',{}).get('Grade','')} for f in feats]
  return rows,{'ok':True,'source':'Historic England NHLE','detail':f'{len(rows)} listed-building records'}
 except Exception:return [],{'ok':False,'source':'Historic England NHLE','detail':'Unavailable or outside England'}
def benches(loc,distance_km=5):
 try:
  x=call('https://openbenches.org/api/nearest/',{'latitude':loc['lat'],'longitude':loc['lon'],'distance':distance_km},35).json();rows=x.get('features',[]) if isinstance(x,dict) else []
  return len(rows),{'ok':True,'source':'OpenBenches','detail':f'{len(rows)} nearby contributed bench records'}
 except Exception:return None,{'ok':False,'source':'OpenBenches','detail':'Unavailable'}
def terrain(loc):
 try:
  offsets=[(0,0),(.018,0),(-.018,0),(0,.03),(0,-.03),(.013,.021),(-.013,-.021)];lats=','.join(str(loc['lat']+a) for a,b in offsets);lons=','.join(str(loc['lon']+b) for a,b in offsets)
  vals=call('https://api.open-meteo.com/v1/elevation',{'latitude':lats,'longitude':lons},35).json()['elevation'];spread=max(vals)-min(vals)
  return {'centre':vals[0],'range':spread,'min':min(vals),'max':max(vals)},{'ok':True,'source':'Open-Meteo Elevation','detail':f'{len(vals)} terrain samples; {spread:.0f} m range'}
 except Exception:return None,{'ok':False,'source':'Open-Meteo Elevation','detail':'Unavailable'}
def food(loc,radius_km):
 try:
  h={**UA,'x-api-version':'2','Accept-Language':'en-GB'};x=call('https://api.ratings.food.gov.uk/Establishments',{'latitude':loc['lat'],'longitude':loc['lon'],'maxDistanceLimit':min(10,radius_km),'pageSize':500},40,h).json().get('establishments',[]);rated=[]
  for e in x:
   try: rated.append(int(e.get('RatingValue')))
   except Exception:pass
  top=sorted([{'name':e.get('BusinessName',''),'rating':e.get('RatingValue',''),'type':e.get('BusinessType','')} for e in x],key=lambda a:str(a['rating']),reverse=True)[:12]
  return {'count':len(x),'rated_4_5':sum(v>=4 for v in rated),'top':top},{'ok':True,'source':'Food Standards Agency','detail':f'{len(x)} establishments; {sum(v>=4 for v in rated)} with numeric rating 4 or 5'}
 except Exception:return None,{'ok':False,'source':'Food Standards Agency','detail':'Unavailable'}
def police(loc):
 try:
  x=call('https://data.police.uk/api/crimes-street/all-crime',{'lat':loc['lat'],'lng':loc['lon']},40).json();return len(x),{'ok':True,'source':'Police.uk','detail':f'{len(x)} recent records'}
 except Exception:return None,{'ok':False,'source':'Police.uk','detail':'Unavailable'}
def headlines(name):
 try:
  root=ET.fromstring(call('https://news.google.com/rss/search',{'q':f'"{name}" UK when:30d','hl':'en-GB','gl':'GB','ceid':'GB:en'}).content);x=[n.findtext('title','') for n in root.findall('.//item')[:8]];return x,{'ok':True,'source':'Google News RSS','detail':f'{len(x)} recent search headlines'}
 except Exception:return [],{'ok':False,'source':'Google News RSS','detail':'Unavailable'}
def route(a,b):
 if not b:return None,{'ok':False,'source':'OSRM','detail':'No regular destination supplied'}
 try:
  x=call(f"https://router.project-osrm.org/route/v1/driving/{a['lon']},{a['lat']};{b['lon']},{b['lat']}",{'overview':'false'}).json()['routes'][0];return {'miles':x['distance']/1609.344,'minutes':x['duration']/60},{'ok':True,'source':'OSRM','detail':'Approximate road route; no live traffic'}
 except Exception:return None,{'ok':False,'source':'OSRM','detail':'Unavailable'}
def collect(loc,radius):
 osm,states,status=overpass_all(loc,radius);wiki,ws=wikipedia_nearby(loc,radius);heritage,hs=historic(loc,radius);bench,bs=benches(loc,radius/1000);elev,es=terrain(loc);f,fs=food(loc,radius/1000);crime,cs=police(loc)
 return {'osm':osm,'states':states,'wiki':wiki,'heritage':heritage,'benches':bench,'terrain':elev,'food':f,'crime':crime},status+[ws,hs,bs,es,fs,cs]
