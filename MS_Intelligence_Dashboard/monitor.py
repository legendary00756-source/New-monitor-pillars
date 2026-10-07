"""Free RSS collector and durable, many-to-many article archive."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import Request, urlopen
from urllib.parse import urlencode, urlsplit
from email.utils import parsedate_to_datetime
import hashlib, html, re, sqlite3, xml.etree.ElementTree as ET
import pandas as pd
from legacy.config import TECH_FIELDS_P3, UAE_REAL_PLAYERS_E7

ROOT = Path(__file__).resolve().parent
DB = ROOT / 'data' / 'news.sqlite3'
UAE = '(UAE OR "United Arab Emirates" OR Dubai OR "Abu Dhabi")'
MODULES = {
 'P1 · Wealth intelligence': {'Market': f'{UAE} (wealth OR "family office" OR "private banking" OR ADGM OR DIFC)'},
 'P2 · Entity intelligence': {'Market': f'{UAE} ("asset management" OR fund OR investment OR regulation)'},
 'P3 · Technology & hiring': {**{k: f'{UAE} ({" OR ".join(chr(34)+x+chr(34) for x in v[:4])})' for k,v in TECH_FIELDS_P3.items()}, 'Technology market': f'{UAE} (technology OR fintech OR AI) (investment OR expansion OR hiring)'},
 'E7 · Real estate': {'Market': f'{UAE} ("real estate" OR property) (market OR prices OR transactions OR forecast)', 'Developers': f'{UAE} (developer OR "off-plan") (launch OR project OR investment)'},
 'UAE corridors': {},
 'India · Private equity': {'Investments & exits': 'India ("private equity" OR buyout OR "growth capital") (investment OR acquisition OR exit OR fund)'},
 'India · M&A deals': {'Mergers & acquisitions': 'India (acquisition OR merger OR takeover OR "M&A") (company OR stake OR deal)'},
 'India · Foreign investments': {'FDI & FPI': 'India ("foreign investment" OR FDI OR FPI OR "foreign direct investment" OR "foreign portfolio")'},
 'India · AIF': {'Funds & regulation': 'India ("alternative investment fund" OR AIF) (SEBI OR fund OR launch OR regulation OR fundraising)'},
 'GIFT City': {'Ecosystem': '"GIFT City" (investment OR business OR company OR expansion)', 'Funds & administration': '("GIFT City" OR IFSCA) (fund OR FME OR "fund administration" OR AIF)', 'Policy & regulation': '("GIFT City" OR IFSCA) (regulation OR circular OR tax OR policy)', 'Banking & markets': '"GIFT City" (bank OR exchange OR insurance OR aircraft OR bullion)'},
 'ADGM · DIFC · QFC': {'Financial centres': '(ADGM OR DIFC OR QFC) (licence OR license OR fund OR regulation OR expansion)'},
 'Family offices & succession': {'Wealth & succession': '(India OR UAE) ("family office" OR succession OR "family business")'},
 'Industrial & infrastructure deals': {'GCC opportunities': '(UAE OR Saudi OR GCC OR Oman OR Qatar) (manufacturing OR infrastructure OR pipeline) (acquisition OR investment OR contract)'},
}
COUNTRIES = {'India':'India OR Indian', 'USA':'USA OR "United States" OR American', 'Singapore':'Singapore', 'Africa':'Africa OR Kenya OR Nigeria OR Egypt OR Morocco OR "South Africa"', 'China':'China OR Chinese', 'UK':'UK OR Britain OR "United Kingdom"', 'Saudi Arabia':'"Saudi Arabia" OR Saudi', 'Europe':'France OR Germany OR Italy OR Europe', 'Japan & Korea':'Japan OR Korea', 'Other countries':'Australia OR Canada OR Brazil OR Indonesia OR Malaysia OR Pakistan OR Turkey'}
for label, query in COUNTRIES.items():
 MODULES['UAE corridors'][label] = f'{UAE} ({query}) (trade OR investment OR acquisition OR partnership OR CEPA OR business)'

def entities(module):
 name = 'entities.xlsx' if module.startswith('P1') else 'entities (1).xlsx'
 return pd.read_excel(ROOT/'legacy'/name).iloc[:,0].dropna().astype(str).tolist()

def queries(module, selected_entities=None):
 out = dict(MODULES[module])
 if module.startswith(('P1','P2')):
  for name in (entities(module) if selected_entities is None else selected_entities):
   out['Entity: '+name] = f'"{name.replace(chr(34), "")}" {UAE}'
 return out

def connect():
 DB.parent.mkdir(parents=True,exist_ok=True)
 c = sqlite3.connect(DB,timeout=30)
 c.execute('PRAGMA journal_mode=WAL')
 c.executescript('''CREATE TABLE IF NOT EXISTS articles(id TEXT PRIMARY KEY,title TEXT,url TEXT,source TEXT,published TEXT,summary TEXT,first_seen TEXT);
 CREATE TABLE IF NOT EXISTS tags(article_id TEXT,module TEXT,topic TEXT,PRIMARY KEY(article_id,module,topic));
 CREATE TABLE IF NOT EXISTS runs(id INTEGER PRIMARY KEY,checked TEXT,module TEXT,topic TEXT,status TEXT,items INTEGER,detail TEXT);
 CREATE TABLE IF NOT EXISTS saved(article_id TEXT PRIMARY KEY);''')
 return c

def clean(text):
 return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>',' ',text or ''))).strip()

def parse_feed(body, days):
 root=ET.fromstring(body)
 if root.tag not in ('rss','{http://www.w3.org/2005/Atom}feed'):
  raise ValueError('Response is not an RSS/Atom feed')
 now=datetime.now(timezone.utc); rows=[]
 for item in root.findall('.//item'):
  title=clean(item.findtext('title')); url=item.findtext('link') or ''
  if not title or urlsplit(url).scheme not in ('https','http'): continue
  try: date=parsedate_to_datetime(item.findtext('pubDate') or '').astimezone(timezone.utc)
  except (ValueError,TypeError,OverflowError): continue
  if not now-timedelta(days=days)<=date<=now+timedelta(minutes=10): continue
  source=clean(item.findtext('source') or urlsplit(url).netloc)
  # Stable headline+publisher key deduplicates repeated URLs across topics, retaining all tags.
  ident=hashlib.sha256((re.sub(r'\W+','',title.casefold())+'|'+source.casefold()).encode()).hexdigest()
  rows.append((ident,title,url,source,date.isoformat(),clean(item.findtext('description')),now.isoformat()))
 return rows

def fetch(query,days):
 url='https://news.google.com/rss/search?'+urlencode({'q':query+f' when:{days}d','hl':'en','gl':'AE','ceid':'AE:en'})
 req=Request(url,headers={'User-Agent':'MSIntelligenceMonitor/1.0'})
 with urlopen(req,timeout=18) as r: body=r.read(4_000_000)
 return parse_feed(body,days)

def refresh(modules,days=7,entity_overrides=None,progress=None):
 jobs=[(m,t,q) for m in modules for t,q in queries(m,(entity_overrides or {}).get(m)).items()]
 outcomes=[]
 with ThreadPoolExecutor(max_workers=4) as pool:
  futures={pool.submit(fetch,q,days):(m,t) for m,t,q in jobs}
  for i,f in enumerate(as_completed(futures),1):
   m,t=futures[f]; now=datetime.now(timezone.utc).isoformat()
   try: rows=f.result(); status='OK'; detail=''
   except Exception as e: rows=[]; status='ERROR'; detail=f'{type(e).__name__}: {e}'[:250]
   with connect() as c:
    for row in rows:
     c.execute('INSERT OR IGNORE INTO articles VALUES(?,?,?,?,?,?,?)',row)
     c.execute('INSERT OR IGNORE INTO tags VALUES(?,?,?)',(row[0],m,t))
    c.execute('INSERT INTO runs(checked,module,topic,status,items,detail) VALUES(?,?,?,?,?,?)',(now,m,t,status,len(rows),detail))
   outcomes.append((m,t,status,len(rows)))
   if progress: progress(i/len(jobs),f'{m} / {t}')
 return outcomes

def read_news():
 with connect() as c:
  return pd.read_sql_query('SELECT a.*,t.module,t.topic,CASE WHEN s.article_id IS NULL THEN 0 ELSE 1 END bookmarked FROM articles a JOIN tags t ON a.id=t.article_id LEFT JOIN saved s ON a.id=s.article_id ORDER BY published DESC',c)

def health():
 with connect() as c:
  return pd.read_sql_query('SELECT checked,module,topic,status,items,detail FROM runs WHERE id IN (SELECT MAX(id) FROM runs GROUP BY module,topic) ORDER BY checked DESC',c)

def bookmark(ident,save):
 with connect() as c:
  c.execute('INSERT OR IGNORE INTO saved VALUES(?)' if save else 'DELETE FROM saved WHERE article_id=?',(ident,))

if __name__=='__main__':
 import argparse,time
 p=argparse.ArgumentParser(); p.add_argument('--every',type=int,default=0,help='Repeat interval in minutes; zero runs once'); p.add_argument('--days',type=int,default=7); args=p.parse_args()
 while True:
  results=refresh(list(MODULES),args.days)
  print(datetime.now().isoformat(), 'queries:',len(results),'failed:',sum(r[2]=='ERROR' for r in results),flush=True)
  if not args.every: break
  time.sleep(max(15,args.every)*60)
