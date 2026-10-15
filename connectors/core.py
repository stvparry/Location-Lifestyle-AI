import re, requests, xml.etree.ElementTree as ET
UA={"User-Agent":"Location-Lifestyle-AI/1.0 educational app"}
OVERPASS=["https://overpass.kumi.systems/api/interpreter","https://overpass-api.de/api/interpreter"]
def get(url,params=None,timeout=30,headers=None):
 r=requests.get(url,params=params,headers=headers or UA,timeout=timeout);r.raise_for_status();return r
def geocode(q,limit=6):
 out=[];q=q.strip();m=re.search(r"\b([A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2})\b",q.upper())
 if m:
  try:
   x=get("https://api.postcodes.io/postcodes/"+m.group(1).replace(" ","")).json()["result"]
   out.append({"label":f"{x['postcode']} · {x.get('admin_district','')}","lat":x['latitude'],"lon":x['longitude'],"postcode":x['postcode']})
  except Exception: pass
 try:
  for x in get("https://nominatim.openstreetmap.org/search",{"q":q+", United Kingdom","format":"jsonv2","limit":limit,"countrycodes":"gb"}).json():
   z={"label":x["display_name"],"lat":float(x["lat"]),"lon":float(x["lon"]),"postcode":x.get("address",{}).get("postcode","")}
   if not any(abs(z["lat"]-a["lat"])<.0001 and abs(z["lon"]-a["lon"])<.0001 for a in out):out.append(z)
 except Exception: pass
 return out[:limit]
def route(a,b):
 if not a or not b:return None,{"ok":False,"source":"OSRM","detail":"Destination not supplied"}
 try:
  x=get(f"https://router.project-osrm.org/route/v1/driving/{a['lon']},{a['lat']};{b['lon']},{b['lat']}",{"overview":"false"}).json()["routes"][0]
  return {"miles":x["distance"]/1609.344,"minutes":x["duration"]/60},{"ok":True,"source":"OSRM","detail":"Approximate road route; no live traffic"}
 except Exception:return None,{"ok":False,"source":"OSRM","detail":"Route unavailable"}
def local_features(loc,radius):
 tags={
 "Travel":['node[railway=station]','node[highway=bus_stop]'],"Green space":['node[leisure=park]','way[leisure=park]','node[natural=wood]','way[natural=wood]'],
 "Shops":['node[shop]','way[shop]'],"Healthcare":['node[amenity~"hospital|clinic|doctors|pharmacy|dentist"]'],
 "Food & drink":['node[amenity~"restaurant|cafe|pub"]','way[amenity~"restaurant|cafe|pub"]'],
 "Active life":['node[leisure~"fitness_centre|sports_centre|swimming_pool|golf_course|marina|pitch"]','way[leisure~"fitness_centre|sports_centre|swimming_pool|golf_course|marina|pitch"]'],
 "Culture":['node[amenity~"theatre|cinema|library|arts_centre"]','node[tourism~"museum|gallery|attraction"]'],
 "Family":['node[leisure~"playground|water_park"]','node[tourism~"zoo|theme_park|museum"]'],
 "Community":['node[amenity~"community_centre|social_centre|place_of_worship"]'],
 "Blue space":['node[leisure=marina]','way[leisure=marina]','node[sport~"rowing|canoe|sailing"]','way[sport~"rowing|canoe|sailing"]']}
 query='[out:json][timeout:28];('+''.join(f'{t}(around:{radius},{loc["lat"]},{loc["lon"]});' for arr in tags.values() for t in arr)+');out center tags;'
 for server in OVERPASS:
  try:
   rows=get(server,{"data":query},48).json().get("elements",[]);items={k:[] for k in tags}
   for e in rows:
    t=e.get("tags",{});name=t.get("name","Unnamed");amen=t.get("amenity","");leisure=t.get("leisure","");tour=t.get("tourism","");sport=t.get("sport","");shop=t.get("shop")
    cats=[]
    if t.get("railway")=="station" or t.get("highway")=="bus_stop":cats+=['Travel']
    if leisure=='park' or t.get('natural')=='wood':cats+=['Green space']
    if shop:cats+=['Shops']
    if amen in ['hospital','clinic','doctors','pharmacy','dentist']:cats+=['Healthcare']
    if amen in ['restaurant','cafe','pub']:cats+=['Food & drink']
    if leisure in ['fitness_centre','sports_centre','swimming_pool','golf_course','marina','pitch']:cats+=['Active life']
    if amen in ['theatre','cinema','library','arts_centre'] or tour in ['museum','gallery','attraction']:cats+=['Culture']
    if leisure in ['playground','water_park'] or tour in ['zoo','theme_park','museum']:cats+=['Family']
    if amen in ['community_centre','social_centre','place_of_worship']:cats+=['Community']
    if leisure=='marina' or sport in ['rowing','canoe','sailing']:cats+=['Blue space']
    for c in cats:
     if name not in items[c]:items[c].append(name)
   if rows:return items,{"ok":True,"source":"OpenStreetMap/Overpass","detail":f"{len(rows)} map objects returned"}
  except Exception:pass
 return {k:[] for k in tags},{"ok":False,"source":"OpenStreetMap/Overpass","detail":"Public endpoints unavailable"}
def police(loc):
 try:
  x=get("https://data.police.uk/api/crimes-street/all-crime",{"lat":loc['lat'],"lng":loc['lon']}).json()
  return len(x),{"ok":True,"source":"Police.uk","detail":f"{len(x)} recent street-level records returned"}
 except Exception:return None,{"ok":False,"source":"Police.uk","detail":"Unavailable"}
def food_hygiene(loc,radius_km):
 try:
  x=get("https://api.ratings.food.gov.uk/Establishments",{"latitude":loc['lat'],"longitude":loc['lon'],"maxDistanceLimit":min(10,radius_km),"pageSize":500},35,{**UA,"x-api-version":"2"}).json().get("establishments",[])
  vals=[]
  for e in x:
   try:vals.append(int(e.get("RatingValue")))
   except Exception:pass
  return {"count":len(x),"rated_4_5":sum(v>=4 for v in vals)},{"ok":True,"source":"Food Standards Agency","detail":f"{len(x)} establishments returned"}
 except Exception:return None,{"ok":False,"source":"Food Standards Agency","detail":"Unavailable"}
def headlines(name):
 try:
  root=ET.fromstring(get("https://news.google.com/rss/search",{"q":f'"{name}" UK when:30d',"hl":"en-GB","gl":"GB","ceid":"GB:en"}).content)
  return [x.findtext("title","") for x in root.findall('.//item')[:6]],{"ok":True,"source":"Google News RSS","detail":"Recent search headlines returned"}
 except Exception:return [],{"ok":False,"source":"Google News RSS","detail":"Unavailable"}
