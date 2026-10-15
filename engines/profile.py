DIMENSIONS=['Property','Active life','Learning & culture','Community','Family visits','Practicality','Outdoors','Water life']
def score_location(evidence,weights,property_rows=None):
 f=evidence['features'];scores={}
 caps={'Active life':18,'Learning & culture':12,'Community':15,'Family visits':12,'Practicality':55,'Outdoors':12,'Water life':6}
 scores['Active life']=min(100,len(f['Active life'])*100/caps['Active life'])
 scores['Learning & culture']=min(100,len(f['Culture'])*100/caps['Learning & culture'])
 scores['Community']=min(100,len(f['Community'])*100/caps['Community'])
 scores['Family visits']=min(100,len(f['Family'])*100/caps['Family visits'])
 scores['Practicality']=min(100,(len(f['Shops'])+len(f['Healthcare'])+len(f['Travel']))*100/caps['Practicality'])
 scores['Outdoors']=min(100,len(f['Green space'])*100/caps['Outdoors'])
 scores['Water life']=min(100,len(f['Blue space'])*100/caps['Water life'])
 scores['Property']=50 if property_rows is None else property_rows
 return scores
def horizon_assessment(user,scores):
 now=[];mid=[];later=[]
 def add(bucket,label,condition,good,bad):bucket.append((label,good if condition else bad,condition))
 add(now,'Active routine',scores['Active life']>=45,'Returned facilities support an active routine.','Named active-life provision is limited in the returned evidence.')
 add(now,'Interest and stimulation',scores['Learning & culture']>=35,'Cultural and learning provision gives useful options.','Learning and cultural opportunities need direct local research.')
 add(now,'Property evidence',scores['Property']>50,'The supplied property evidence supports current fit.','Property availability remains unverified or only partially evidenced.')
 add(mid,'Maintenance fit',user['maintenance'] in ['High','Moderate'],'The selected maintenance appetite is compatible with a wider housing search.','Prioritise easier-to-maintain homes and manageable gardens.')
 add(mid,'Adaptability',user['stairs']=='No concern','No present stairs constraint was declared.','Prioritise step-free access or an adaptable ground-floor layout.')
 add(mid,'Healthcare access',scores['Practicality']>=45,'Returned practical provision gives a reasonable base for direct checks.','GP, pharmacy and hospital journeys require stronger verification.')
 add(later,'One-car resilience',user['future_car'] not in ['One car','No car'],'Two-car use remains possible in the scenario, but one-car resilience should still be tested.','Test shopping, healthcare, activities and social life with reduced car use.')
 add(later,'Community continuity',scores['Community']>=35,'Returned community infrastructure offers routes to participation.','Finding clubs, volunteering and social connections requires targeted research.')
 add(later,'Everyday independence',scores['Practicality']>=55,'Returned services suggest some everyday resilience.','The location may remain car-dependent for essential trips.')
 return {'0–3 years':now,'3–8 years':mid,'8–15 years':later}
