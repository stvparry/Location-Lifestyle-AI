import sqlite3,requests,time,os
from datetime import datetime,timezone
ROOT=os.path.dirname(os.path.dirname(__file__));DB=os.path.join(ROOT,'data','lifestyle.db');UA={'User-Agent':'LocationLifestyleAI/2.1 GitHubAction'}
def get(url,p=None,h=None):r=requests.get(url,params=p,headers=h or UA,timeout=50);r.raise_for_status();return r.json()
def src(c,lid,n,ok,d):c.execute('INSERT INTO sources(location_id,source,status,detail,refreshed_at) VALUES(?,?,?,?,?)',(lid,n,'available' if ok else 'unavailable',d,datetime.now(timezone.utc).isoformat()))
def main():
 c=sqlite3.connect(DB);rows=c.execute('SELECT id,name,query FROM locations ORDER BY id').fetchall();c.execute('DELETE FROM evidence');c.execute('DELETE FROM metrics');c.execute('DELETE FROM sources')
 for lid,name,q in rows:
  try:
   x=get('https://nominatim.openstreetmap.org/search',{'q':q,'format':'jsonv2','limit':1,'countrycodes':'gb'})[0];lat,lon=float(x['lat']),float(x['lon']);c.execute('UPDATE locations SET label=?,lat=?,lon=?,status=? WHERE id=?',(x['display_name'],lat,lon,'geocoded',lid));src(c,lid,'Nominatim',True,x['display_name'])
  except Exception as e:src(c,lid,'Nominatim',False,type(e).__name__);c.commit();continue
  try:
   x=get('https://en.wikipedia.org/w/api.php',{'action':'query','list':'geosearch','gscoord':f'{lat}|{lon}','gsradius':10000,'gslimit':50,'format':'json'}).get('query',{}).get('geosearch',[])
   for a in x:c.execute('INSERT INTO evidence(location_id,category,name,distance_km,detail,source) VALUES(?,?,?,?,?,?)',(lid,'Nearby knowledge',a['title'],a.get('dist',0)/1000,'Geotagged Wikipedia article','Wikipedia'))
   src(c,lid,'Wikipedia',True,f'{len(x)} records')
  except Exception as e:src(c,lid,'Wikipedia',False,type(e).__name__)
  try:
   deg=.08;geom=f'{lon-deg},{lat-deg},{lon+deg},{lat+deg}';url='https://services-eu1.arcgis.com/ZOdPfBS3aqqDYPUQ/arcgis/rest/services/National_Heritage_List_for_England_NHLE_v02_VIEW/FeatureServer/0/query';p={'where':'1=1','geometry':geom,'geometryType':'esriGeometryEnvelope','inSR':4326,'spatialRel':'esriSpatialRelIntersects','outFields':'Name,Grade','returnGeometry':'false','f':'json','resultRecordCount':200};x=get(url,p).get('features',[])
   for a in x:
    z=a.get('attributes',{});c.execute('INSERT INTO evidence(location_id,category,name,detail,source) VALUES(?,?,?,?,?)',(lid,'Heritage',z.get('Name') or 'Unnamed heritage asset','Grade '+str(z.get('Grade','')),'Historic England'))
   src(c,lid,'Historic England',True,f'{len(x)} records')
  except Exception as e:src(c,lid,'Historic England',False,type(e).__name__)
  try:
   h={**UA,'x-api-version':'2'};x=get('https://api.ratings.food.gov.uk/Establishments',{'latitude':lat,'longitude':lon,'maxDistanceLimit':5,'pageSize':500},h).get('establishments',[])
   for a in x:c.execute('INSERT INTO evidence(location_id,category,name,detail,source) VALUES(?,?,?,?,?)',(lid,'Food & drink',a.get('BusinessName') or 'Unnamed',f"{a.get('BusinessType','')} · hygiene {a.get('RatingValue','unrated')}",'Food Standards Agency'))
   src(c,lid,'Food Standards Agency',True,f'{len(x)} records')
  except Exception as e:src(c,lid,'Food Standards Agency',False,type(e).__name__)
  try:
   offs=[(0,0),(.018,0),(-.018,0),(0,.03),(0,-.03)];la=','.join(str(lat+a) for a,b in offs);lo=','.join(str(lon+b) for a,b in offs);v=get('https://api.open-meteo.com/v1/elevation',{'latitude':la,'longitude':lo})['elevation'];c.execute('INSERT INTO metrics(location_id,key,value,unit,source) VALUES(?,?,?,?,?)',(lid,'elevation_range',max(v)-min(v),'metres','Open-Meteo'));src(c,lid,'Open-Meteo',True,f'{max(v)-min(v):.0f} m range')
  except Exception as e:src(c,lid,'Open-Meteo',False,type(e).__name__)
  c.execute('UPDATE locations SET status=? WHERE id=?',('refreshed',lid));c.commit();time.sleep(.7)
 c.close()
if __name__=='__main__':main()
