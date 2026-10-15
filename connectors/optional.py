import requests
def propertydata_prices(postcode,bedrooms,key):
 if not key or not postcode:return None,{"ok":False,"source":"PropertyData","detail":"Not configured or no full postcode"}
 try:
  r=requests.get("https://api.propertydata.co.uk/prices",params={"postcode":postcode.replace(' ',''),"bedrooms":bedrooms},headers={"X-API-Key":key},timeout=35);r.raise_for_status();x=r.json()
  if x.get("status")!="success":return None,{"ok":False,"source":"PropertyData","detail":str(x.get("message","Unsuccessful response"))}
  return x.get("data",{}),{"ok":True,"source":"PropertyData","detail":"Licensed asking-price evidence returned"}
 except Exception:return None,{"ok":False,"source":"PropertyData","detail":"Call rejected or unavailable"}
def opentripmap(loc,key,radius=10000):
 if not key:return [],{"ok":False,"source":"OpenTripMap","detail":"Not configured"}
 try:
  r=requests.get("https://api.opentripmap.com/0.1/en/places/radius",params={"radius":radius,"lon":loc['lon'],"lat":loc['lat'],"rate":2,"limit":20,"format":"json","apikey":key},timeout=35);r.raise_for_status();x=r.json()
  return [{"name":a.get("name") or "Unnamed","kinds":a.get("kinds","")} for a in x],{"ok":True,"source":"OpenTripMap","detail":f"{len(x)} attractions returned"}
 except Exception:return [],{"ok":False,"source":"OpenTripMap","detail":"Call rejected or unavailable"}
