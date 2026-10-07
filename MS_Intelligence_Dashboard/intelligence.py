"""Explainable headline triage, never a verified deal database."""
import re
from datetime import datetime, timezone
import pandas as pd

SECTORS={
 'Financial services':r'\bbank\w*\b|\binsur\w*\b|\bfintech\b|\basset management\b',
 'Technology':r'\bsoftware\b|\bAI\b|\btechnology\b|\bsemiconductor\b|\bdata cent(?:re|er)\b',
 'Industrials':r'\bmanufactur\w*\b|\bpipeline\b|\bGRP\b|\bfactory\b|\bindustrial\b',
 'Energy':r'\boil\b|\bgas\b|\benergy\b|\bsolar\b|\brenewable\w*\b',
 'Healthcare':r'\bhealth\w*\b|\bhospital\b|\bpharma\w*\b',
 'Real estate':r'\bproperty\b|\breal estate\b|\bdeveloper\b',
 'Consumer & retail':r'\bretail\b|\bconsumer\b|\bfood\b|\bbeverage\b',
 'Logistics':r'\blogistics\b|\bport\b|\bshipping\b|\baviation\b',
}
DEAL=r'\bacquir\w*\b|\bacquisition\b|\bmerger\b|\btakeover\b|\bbuyout\b|\bdivest\w*\b|\bstake sale\b|\bmajority stake\b|\bminority stake\b'
MONEY=r'(?:US\$|USD|AED|INR|GBP|EUR|\$|£|€|₹)\s*\d[\d,.]*(?:\s*(?:billion|million|trillion|crore|lakh|bn|mn|[mb])\b)?|\b\d[\d,.]*\s*(?:billion|million|crore|lakh)\s*(?:dollars|dirhams|rupees|pounds|euros)\b'

def analyze(title,summary,published,keywords=(),preferred=False,pinned=False):
 text=title+' '+summary
 matches=[x for x in keywords if x.strip() and x.casefold() in text.casefold()]
 deal=bool(re.search(DEAL,title,re.I))
 sector=next((k for k,v in SECTORS.items() if re.search(v,text,re.I)),'Other / unclear')
 stage='Unclear / not a deal headline'
 if deal:
  stage='Deal mentioned — verify'
  for label,pattern in [
   ('Cancelled / blocked signal',r'\b(blocked|cancelled|canceled|terminated|abandoned|scrapped)\b'),
   ('Talks / proposal signal',r'\b(talks|considering|weighs|plans|proposed|proposal|rumou?r|could|may|seeks|bid)\b'),
   ('Completion signal',r'\b(completes|completed|closes|closed|finali[sz]ed)\b'),
   ('Approval signal',r'\b(approved|approval|cleared|clearance)\b'),
   ('Agreement signal',r'\b(agrees|agreed|agreement|announces|announced|acquires)\b')]:
   if re.search(pattern,title,re.I): stage=label; break
  if re.search(r'\b(not|no|denies|denied)\b',title,re.I): stage='Negation present — review manually'
 amounts=list(dict.fromkeys(re.findall(MONEY,title,flags=re.I)))
 score=0; reasons=[]
 def add(points,reason):
  nonlocal score
  score+=points; reasons.append(f'+{points} {reason}')
 age=(datetime.now(timezone.utc)-pd.to_datetime(published,utc=True).to_pydatetime()).total_seconds()/3600
 if age<=24: add(20,'dated within 24h')
 elif age<=72: add(12,'dated within 72h')
 elif age<=168: add(5,'dated within 7d')
 if deal: add(25,'M&A headline signal')
 if amounts: add(10,'monetary amount in headline')
 if re.search(r'\b(regulation|circular|policy|tax|sanctions|tariff|interest rate)\b',title,re.I): add(15,'policy / macro headline')
 if re.search(r'\b(UAE|Dubai|Abu Dhabi|India|GIFT City|IFSCA)\b',text,re.I): add(10,'core geography mentioned')
 if matches: add(15,'watch keyword matched')
 if preferred: add(10,'priority module')
 if pinned: add(100,'manually pinned')
 return {'priority':score,'priority_reason':'; '.join(reasons) or 'No priority signal',
         'sector':sector,'deal_signal':deal,'stage_signal':stage,'amount_mentions':'; '.join(amounts),
         'alert_matches':', '.join(matches)}

def enrich(data,keywords=(),priority_modules=()):
 data=data.copy()
 if data.empty:
  for key in ['priority','priority_reason','sector','deal_signal','stage_signal','amount_mentions','alert_matches']: data[key]=pd.Series(dtype='object')
  return data
 flags=data.groupby('id').module.apply(lambda x:any(m in priority_modules for m in x)).to_dict()
 unique=data.drop_duplicates('id')
 signals={r.id:analyze(r.title,r.summary,r.published,keywords,flags[r.id],bool(r.pinned)) for r in unique.itertuples()}
 for key in next(iter(signals.values())): data[key]=data.id.map(lambda ident:signals[ident][key])
 return data

def safe_sheet(df):
 df=df.copy()
 for col in df.select_dtypes('object'):
  df[col]=df[col].map(lambda x:"'"+x if isinstance(x,str) and x.lstrip().startswith(('=','+','-','@')) else x)
 return df
