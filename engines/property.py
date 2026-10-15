import pandas as pd
def analyse_listings(df,budget,area_name):
 if df is None or df.empty:return None
 d=df.copy();d.columns=[str(c).strip().lower() for c in d.columns]
 if not {'area','price'}.issubset(d.columns):return {'error':'CSV requires area and price columns'}
 d['price']=pd.to_numeric(d['price'],errors='coerce');d=d.dropna(subset=['price']);g=d[d['area'].astype(str).str.contains(area_name,case=False,na=False)]
 if g.empty:return {'count':0,'within':0,'median':None,'detached':0,'coverage':'USER-SUPPLIED SAMPLE'}
 typ=g['property_type'].astype(str).str.lower() if 'property_type' in g else pd.Series('',index=g.index)
 return {'count':len(g),'within':int((g.price<=budget).sum()),'median':float(g.price.median()),'detached':int((typ=='detached').sum()),'coverage':'USER-SUPPLIED SAMPLE'}
