"""Free RSS collector and durable, many-to-many article archive."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode, urlsplit, parse_qs
from email.utils import parsedate_to_datetime
import hashlib, html, re, sqlite3, xml.etree.ElementTree as ET
import json, time, threading
from contextlib import contextmanager
import feedparser
import pandas as pd
from legacy.config import TECH_FIELDS_P3, UAE_REAL_PLAYERS_E7
from news_quality import canonical_url, headline_key, same_story, inspect_publication, curate, consolidate_news

ROOT = Path(__file__).resolve().parent
DB = ROOT / 'data' / 'news.sqlite3'
UAE = '(UAE OR "United Arab Emirates" OR Dubai OR "Abu Dhabi")'
MODULES = {
 'P1 · Wealth intelligence': {'Market': f'{UAE} (wealth OR "family office" OR "private banking" OR ADGM OR DIFC)'},
 'P2 · UAE & global M&A': {
  'UAE acquisitions': f'{UAE} (acquires OR acquisition OR merger OR takeover OR buyout)',
  'UAE outbound & inbound': f'{UAE} ("cross-border" OR overseas OR foreign) (acquisition OR stake OR takeover)',
  'Global M&A': '(acquires OR merger OR takeover OR buyout) (company OR business OR corporation)',
  'PE-backed buyouts': '("private equity" OR "buyout fund") (acquisition OR buyout OR takeover)',
  'Stake sales & divestments': '("stake sale" OR divestment OR "majority stake" OR "minority stake") (deal OR acquisition)',
  'Approvals & completion': '(merger OR acquisition OR takeover) (antitrust OR approval OR completed OR blocked)',
  'Distressed M&A': '("distressed acquisition" OR "asset sale" OR "bankruptcy sale")'},
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
MODULES.update({
 'Key market developments': {'Global macro': '("interest rate" OR inflation OR tariff OR sanctions) (economy OR investment OR trade)', 'UAE economy': f'{UAE} (economy OR GDP OR inflation OR budget OR policy)'},
 'IPOs & capital markets': {'India IPOs': 'India (IPO OR "public offering" OR "SME IPO")', 'GCC listings': '(UAE OR Saudi OR GCC) (IPO OR listing OR sukuk)'},
 'Sovereign funds & private credit': {'Sovereign capital': '(Mubadala OR ADQ OR ADIA OR "sovereign wealth") (investment OR acquisition OR fund)', 'Private credit': '(India OR UAE OR GCC) ("private credit" OR "direct lending" OR "debt fund")'},
 'Regulatory watch': {'IFSC notices': '(site:ifsca.gov.in) (circular OR notification OR consultation)', 'India funds regulation': 'site:sebi.gov.in (AIF OR "alternative investment" OR FPI)', 'UAE finance regulation': '(site:adgm.com OR site:dfsa.ae OR site:centralbank.ae) (regulation OR consultation OR notice)'},
 'Custom monitoring': {}
})
MODULES['India · Private equity'].update({
 'Fundraising & closes': 'India ("private equity" OR "growth equity") (fundraise OR fundraising OR "final close" OR "first close")',
 'Exits & secondaries': 'India ("private equity" OR "secondary transaction") (exit OR divestment OR secondary)',
 'Sector investments': 'India (healthcare OR manufacturing OR technology) ("private equity" OR buyout)'
})
MODULES['India · Foreign investments'].update({
 'Greenfield & manufacturing': 'India (FDI OR "foreign investment") (factory OR manufacturing OR greenfield)',
 'Policy & approvals': 'India (FDI OR FPI) (policy OR approval OR limit OR regulation)'
})
MODULES['India · AIF'].update({
 'Category II & III': 'India ("Category II" OR "Category III" OR "Cat III") (AIF OR fund)',
 'Fund operations': 'India AIF (valuation OR compliance OR custodian OR administration OR NAV)'
})
MODULES['GIFT City'].update({
 'Managers & launches': '("GIFT City" OR IFSCA) ("fund launch" OR "fund manager" OR "fund management entity")',
 'Cross-border & NRI': '"GIFT City" (NRI OR "cross-border" OR offshore OR "family office")',
 'Service providers': '"GIFT City" (administrator OR trusteeship OR custodian OR "fund accounting")'
})
del MODULES['P3 · Technology & hiring']
MODULES['P3 · Global tech hiring']={
 'AI & data hiring':'("AI" OR "data science" OR "data analytics") (hiring OR recruitment OR "job openings")',
 'Cybersecurity hiring':'(cybersecurity OR "information security") (hiring OR recruitment OR vacancies)',
 'Software & engineering hiring':'(software OR developers OR engineering) (hiring OR "recruitment drive" OR "job openings")',
 'Cloud & DevOps hiring':'(cloud OR DevOps OR "platform engineering") (hiring OR recruitment OR vacancies)',
 'Fintech hiring':'fintech (hiring OR recruitment OR "job openings")',
 'Technology job creation':'technology ("creates jobs" OR "new jobs" OR "hiring plans" OR "hiring drive")'
}
MODULES['Global cybersecurity']={
 'Threats & incidents':'(cybersecurity OR ransomware OR malware OR "data breach") (attack OR incident OR threat)',
 'Vulnerabilities & patches':'(vulnerability OR "zero day" OR CVE) (security OR patch OR exploit)',
 'Cyber businesses & regulation':'cybersecurity (acquisition OR funding OR regulation OR policy)'
}
MODULES['Global data analytics']={
 'Analytics & business intelligence':'("data analytics" OR "business intelligence") (launch OR adoption OR platform OR investment)',
 'Data science & engineering':'("data science" OR "data engineering" OR "data warehouse") (research OR launch OR development)',
 'Data governance & platforms':'("data governance" OR "data platform" OR "data lakehouse") (news OR launch OR regulation OR partnership)'
}
MODULES['UAE · Key people & movements']={
 'Corporate leaders':f'{UAE} (CEO OR CFO OR "chief executive" OR chairman) (appoints OR appointed OR joins OR resigns OR succeeds)',
 'Investment & finance leaders':f'{UAE} ("managing director" OR "investment officer" OR partner OR "fund manager") (appointed OR joins OR promoted OR leaves)',
 'Government & institutions':f'{UAE} (minister OR governor OR ambassador OR director) (appointed OR appointment OR succeeds)',
 'Board & senior management':f'{UAE} (board OR leadership OR "senior management") (appointment OR departure OR promotion OR retirement)'
}
P2 = 'P2 · UAE & global M&A'  
MA = '(acquisition OR acquires OR merger OR takeover OR buyout OR divestment OR "stake sale")'
COUNTRIES = {'India':'India OR Indian', 'USA':'USA OR "United States" OR American', 'Singapore':'Singapore', 'Africa':'Africa OR Kenya OR Nigeria OR Egypt OR Morocco OR "South Africa"', 'China':'China OR Chinese', 'UK':'UK OR Britain OR "United Kingdom"', 'Saudi Arabia':'"Saudi Arabia" OR Saudi', 'Europe':'France OR Germany OR Italy OR Europe', 'Japan & Korea':'Japan OR Korea', 'Other countries':'Australia OR Canada OR Brazil OR Indonesia OR Malaysia OR Pakistan OR Turkey'}
for label, query in COUNTRIES.items():
 MODULES['UAE corridors'][label] = f'{UAE} ({query}) (trade OR investment OR acquisition OR partnership OR CEPA OR business)'

def entities(module):
 name = 'entities.xlsx' if module.startswith('P1') else 'entities (1).xlsx'
 saved=setting('entities_'+module,None)
 return saved if saved is not None else pd.read_excel(ROOT/'legacy'/name).iloc[:,0].dropna().astype(str).tolist()

def queries(module, selected_entities=None):
 out = dict(MODULES[module])
 if module.startswith(('P1','P2')):
  for name in (entities(module) if selected_entities is None else selected_entities):
   out['Entity: '+name] = f'"{name.replace(chr(34), "")}" '+(MA if module.startswith('P2') else UAE)
 for rule in setting('custom_searches',[]):
  if rule['module']==module: out['Custom: '+rule['name']]=rule['query']
 return out

@contextmanager
def connect():
 DB.parent.mkdir(parents=True,exist_ok=True)
 c = sqlite3.connect(DB,timeout=30)
 c.execute('PRAGMA journal_mode=WAL')
 c.executescript('''CREATE TABLE IF NOT EXISTS articles(id TEXT PRIMARY KEY,title TEXT,url TEXT,source TEXT,published TEXT,summary TEXT,first_seen TEXT);
 CREATE TABLE IF NOT EXISTS tags(article_id TEXT,module TEXT,topic TEXT,PRIMARY KEY(article_id,module,topic));
 CREATE TABLE IF NOT EXISTS runs(id INTEGER PRIMARY KEY,checked TEXT,module TEXT,topic TEXT,status TEXT,items INTEGER,detail TEXT);
 CREATE TABLE IF NOT EXISTS saved(article_id TEXT PRIMARY KEY);
 CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT);
 CREATE TABLE IF NOT EXISTS metadata(article_id TEXT PRIMARY KEY,provider TEXT,date_kind TEXT);
 CREATE TABLE IF NOT EXISTS reviews(article_id TEXT PRIMARY KEY,read_flag INTEGER DEFAULT 0,pinned INTEGER DEFAULT 0,note TEXT DEFAULT '',owner TEXT DEFAULT '',action TEXT DEFAULT 'New',buyer TEXT DEFAULT '',target TEXT DEFAULT '',value_note TEXT DEFAULT '',verified_status TEXT DEFAULT 'Unreviewed');
 CREATE TABLE IF NOT EXISTS date_evidence(article_id TEXT PRIMARY KEY,original_published TEXT,canonical TEXT,date_status TEXT,detail TEXT,feed_date TEXT,checked TEXT);
 CREATE TABLE IF NOT EXISTS variants(article_id TEXT,url TEXT,source TEXT,title TEXT,PRIMARY KEY(article_id,url));
 CREATE INDEX IF NOT EXISTS article_url_idx ON articles(url);
 CREATE INDEX IF NOT EXISTS evidence_url_idx ON date_evidence(canonical);
 CREATE TABLE IF NOT EXISTS migrations(version TEXT PRIMARY KEY);''')
 # One-time migration leaves old generic P2 articles archived outside the new M&A feed.
 if not c.execute("SELECT 1 FROM migrations WHERE version='v2'").fetchone():
  c.execute("UPDATE OR IGNORE tags SET module='P2 · Historical entity archive' WHERE module='P2 · Entity intelligence'")
  c.execute("DELETE FROM tags WHERE module='P2 · Entity intelligence'")
  c.execute("INSERT INTO migrations VALUES('v2')")
 if not c.execute("SELECT 1 FROM migrations WHERE version='v3'").fetchone():
  c.execute("UPDATE OR IGNORE tags SET module='P3 · Historical technology archive' WHERE module='P3 · Technology & hiring'")
  c.execute("DELETE FROM tags WHERE module='P3 · Technology & hiring'")
  c.execute("INSERT INTO migrations VALUES('v3')")
 c.commit()
 try:
  yield c
  c.commit()
 except Exception:
  c.rollback(); raise
 finally: c.close()

def setting(key,default=None):
 with connect() as c: row=c.execute('SELECT value FROM settings WHERE key=?',(key,)).fetchone()
 return json.loads(row[0]) if row else default

def save_setting(key,value):
 with connect() as c: c.execute('INSERT OR REPLACE INTO settings VALUES(?,?)',(key,json.dumps(value)))

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
 with urlopen(req,timeout=8) as r: body=r.read(4_000_000)
 return parse_feed(body,days)

def fetch_bing(query,days):
 url='https://www.bing.com/news/search?'+urlencode({'q':query,'format':'rss','sortbydate':'1','count':100})
 with urlopen(Request(url,headers={'User-Agent':'MSIntelligenceMonitor/3.0'}),timeout=8) as r: body=r.read(4_000_000)
 feed=feedparser.parse(body)
 if not feed.version: raise ValueError('Not a Bing RSS response')
 now=datetime.now(timezone.utc);rows=[]
 for a in feed.entries:
  date_parts=a.get('published_parsed')
  if not date_parts: continue
  date=datetime(*date_parts[:6],tzinfo=timezone.utc)
  if not now-timedelta(days=days)<=date<=now: continue
  link=a.get('link','')
  if urlsplit(link).netloc.endswith('bing.com'):
   link=parse_qs(urlsplit(link).query).get('url',[link])[0]
  if urlsplit(link).scheme not in {'http','https'}: continue
  title=clean(a.get('title',''));source=urlsplit(link).netloc
  if title: rows.append((stable_id(title,source),title,link,source,date.isoformat(),clean(a.get('summary','')),now.isoformat()))
 return rows

def stable_id(title,source):
 return hashlib.sha256((re.sub(r'\W+','',title.casefold())+'|'+source.casefold()).encode()).hexdigest()

_gdelt_lock=threading.Lock()
_gdelt_last=0.0
_gdelt_block_until=0.0

def parse_gdelt(payload,days):
 if not isinstance(payload,dict) or 'articles' not in payload: raise ValueError('GDELT response has no article list')
 now=datetime.now(timezone.utc); rows=[]
 for a in payload['articles']:
  title=clean(a.get('title','')); url=a.get('url',''); source=a.get('domain','') or urlsplit(url).netloc
  try: date=datetime.strptime(a.get('seendate',''),'%Y%m%dT%H%M%SZ').replace(tzinfo=timezone.utc)
  except ValueError: continue
  if not title or urlsplit(url).scheme not in ('http','https') or not now-timedelta(days=days)<=date<=now+timedelta(minutes=10): continue
  rows.append((stable_id(title,source),title,url,source,date.isoformat(),'',now.isoformat()))
 return rows

def fetch_gdelt(query,days):
 global _gdelt_last, _gdelt_block_until
 # Serialize GDELT calls and space request starts by at least six seconds.
 with _gdelt_lock:
  if time.monotonic()<_gdelt_block_until: raise RuntimeError('GDELT temporarily paused after HTTP 429; retry after 15 minutes')
  query=query.replace('site:','domain:')
  delay=6-(time.monotonic()-_gdelt_last)
  if delay>0: time.sleep(delay)
  _gdelt_last=time.monotonic()
  url='https://api.gdeltproject.org/api/v2/doc/doc?'+urlencode({'query':query+' sourcelang:english','mode':'artlist','format':'json','maxrecords':250,'timespan':f'{min(days,90)}d','sort':'datedesc'})
  try:
   with urlopen(Request(url,headers={'User-Agent':'MSIntelligenceMonitor/2.0'}),timeout=20) as r: body=r.read(4_000_000)
  except HTTPError as exc:
   if exc.code==429: _gdelt_block_until=time.monotonic()+900
   raise
  return parse_gdelt(json.loads(body),days)

def fetch_rss(url,days):
 if urlsplit(url).scheme!='https': raise ValueError('Use an HTTPS RSS/Atom feed URL')
 with urlopen(Request(url,headers={'User-Agent':'MSIntelligenceMonitor/2.0'}),timeout=8) as r: body=r.read(4_000_000)
 feed=feedparser.parse(body)
 if not feed.version: raise ValueError('Not an RSS/Atom feed')
 now=datetime.now(timezone.utc); rows=[]
 for a in feed.entries:
  date_parts=a.get('published_parsed')
  if not date_parts: continue
  date=datetime(*date_parts[:6],tzinfo=timezone.utc)
  if not now-timedelta(days=days)<=date<=now+timedelta(minutes=10): continue
  title=clean(a.get('title','')); link=a.get('link','')
  if not title or urlsplit(link).scheme not in ('https','http'): continue
  source=urlsplit(link).netloc
  rows.append((stable_id(title,source),title,link,source,date.isoformat(),clean(a.get('summary','')),now.isoformat()))
 return rows

def refresh(modules,days=1,entity_overrides=None,progress=None,providers=None,stop_event=None):
 providers=providers if providers is not None else setting('providers',['Google News RSS','Bing News RSS'])
 jobs=[]
 for m in modules:
  qs=queries(m,(entity_overrides or {}).get(m))
  if 'Google News RSS' in providers: jobs.extend((m,t,q,'Google News RSS') for t,q in qs.items())
  if 'Bing News RSS' in providers: jobs.extend((m,t,q,'Bing News RSS') for t,q in qs.items())
  if 'GDELT API' in providers and qs:
   # Broad supplementary search per module, not every entity query (quota friendly).
   query=(MA if m==P2 else next(iter(qs.values())))
   jobs.append((m,'Supplementary global discovery',query,'GDELT API'))
 for feed in setting('rss_feeds',[]):
  if feed['module'] in modules: jobs.append((feed['module'],feed['name'],feed['url'],'Custom RSS'))
 outcomes=[]
 with ThreadPoolExecutor(max_workers=8) as pool:
  funcs={'Google News RSS':fetch,'Bing News RSS':fetch_bing,'GDELT API':fetch_gdelt,'Custom RSS':fetch_rss}
  def run_job(provider,q):
   if stop_event is not None and stop_event.is_set(): return []
   return funcs[provider](q,days)
  futures={pool.submit(run_job,provider,q):(m,t,provider) for m,t,q,provider in jobs}
  for i,f in enumerate(as_completed(futures),1):
   if stop_event is not None and stop_event.is_set():
    for pending in futures: pending.cancel()
    break
   m,t,provider=futures[f]; now=datetime.now(timezone.utc).isoformat()
   try: rows=f.result(); status='OK'; detail=''
   except Exception as e: rows=[]; status='ERROR'; detail=f'{type(e).__name__}: {e}'[:250]
   rejected=0;duplicate_count=0;eligible=[]
   for row in rows:
    ok,reason=curate(m,row[1],row[5])
    if ok: eligible.append(row)
    else: rejected+=1
   # Fast path: no publisher requests or fuzzy archive-wide comparisons.
   with connect() as c:
    for row in eligible:
     ident=row[0]
     previous=c.execute('SELECT original_published FROM date_evidence WHERE article_id=?',(ident,)).fetchone()
     original=previous[0] if previous else None
     displayed_date=original or row[4]
     inserted=c.execute('INSERT OR IGNORE INTO articles VALUES(?,?,?,?,?,?,?)',(ident,*row[1:4],displayed_date,*row[5:])).rowcount
     if not inserted:
      duplicate_count+=1
      c.execute('UPDATE articles SET published=MIN(published,?) WHERE id=?',(displayed_date,ident))
     else:
      c.execute('INSERT OR REPLACE INTO metadata VALUES(?,?,?)',(ident,provider,'Publisher publication' if original else ('GDELT seen time' if provider=='GDELT API' else 'Feed date — unverified')))
     c.execute('INSERT OR IGNORE INTO variants VALUES(?,?,?,?)',(ident,row[2],row[3],row[1]))
     c.execute('INSERT OR IGNORE INTO tags VALUES(?,?,?)',(ident,m,t))
     c.execute('INSERT OR IGNORE INTO date_evidence VALUES(?,?,?,?,?,?,?)',(ident,None,canonical_url(row[2]),'Unverified publication','Fast mode: feed timestamp; publisher page not checked',row[4],now))
   if status=='OK':
    detail=f'{len(rows)} returned; {rejected} off-topic excluded; {duplicate_count} repeats merged'
    if len(rows)>=100 and provider=='Google News RSS': detail+='; possible feed cap: coverage may be incomplete'
    if len(rows)>=250 and provider=='GDELT API': detail+='; API cap reached: coverage incomplete'
   with connect() as c:
    c.execute('INSERT INTO runs(checked,module,topic,status,items,detail) VALUES(?,?,?,?,?,?)',(now,m,provider+' / '+t,status,len(rows),detail))
   outcomes.append((m,t,status,len(rows)))
   if progress: progress(i/len(jobs),f'{provider} / {m} / {t}')
 return outcomes

def read_news():
 with connect() as c:
  data=pd.read_sql_query("""SELECT a.*,t.module,t.topic,
   CASE WHEN s.article_id IS NULL THEN 0 ELSE 1 END bookmarked,
   COALESCE(md.provider,'Google News RSS') provider, CASE WHEN de.original_published IS NOT NULL THEN 'Publisher publication' ELSE COALESCE(md.date_kind,'Legacy date — unverified') END date_kind,
   de.original_published,COALESCE(de.date_status,'Unverified publication') date_status,COALESCE(de.detail,'Not checked in this version') date_detail,
   (SELECT COUNT(*) FROM variants v WHERE v.article_id=a.id) report_count,
   COALESCE(r.read_flag,0) read_flag,COALESCE(r.pinned,0) pinned,COALESCE(r.note,'') note,
   COALESCE(r.owner,'') owner,COALESCE(r.action,'New') action,COALESCE(r.buyer,'') buyer,
   COALESCE(r.target,'') target,COALESCE(r.value_note,'') value_note,COALESCE(r.verified_status,'Unreviewed') verified_status
   FROM articles a JOIN tags t ON a.id=t.article_id LEFT JOIN saved s ON a.id=s.article_id
   LEFT JOIN date_evidence de ON de.article_id=a.id LEFT JOIN metadata md ON a.id=md.article_id LEFT JOIN reviews r ON a.id=r.article_id ORDER BY published DESC""",c)
 data['member_ids']=data.id.map(lambda ident:json.dumps([ident]))
 return data

def health():
 with connect() as c:
  return pd.read_sql_query('SELECT checked,module,topic,status,items,detail FROM runs WHERE id IN (SELECT MAX(id) FROM runs GROUP BY module,topic) ORDER BY checked DESC',c)

def story_members(ident):
 data=read_news()
 rows=data[data.id==ident]
 return json.loads(rows.member_ids.iloc[0]) if not rows.empty else [ident]

def review(ident,**fields):
 allowed={'read_flag','pinned','note','owner','action','buyer','target','value_note','verified_status'}
 if not fields or not set(fields)<=allowed: raise ValueError('Invalid review field')
 members=story_members(ident)
 with connect() as c:
  for member in members:
   c.execute('INSERT OR IGNORE INTO reviews(article_id) VALUES(?)',(member,))
   c.execute('UPDATE reviews SET '+','.join(k+'=?' for k in fields)+' WHERE article_id=?',(*fields.values(),member))


def bookmark(ident,save):
 members=story_members(ident)
 with connect() as c:
  for member in members: c.execute('INSERT OR IGNORE INTO saved VALUES(?)' if save else 'DELETE FROM saved WHERE article_id=?',(member,))

if __name__=='__main__':
 import argparse,time
 p=argparse.ArgumentParser(); p.add_argument('--every',type=int,default=0,help='Repeat interval in minutes; zero runs once'); p.add_argument('--days',type=int,default=1); args=p.parse_args()
 while True:
  results=refresh(list(MODULES),args.days)
  print(datetime.now().isoformat(), 'queries:',len(results),'failed:',sum(r[2]=='ERROR' for r in results),flush=True)
  if not args.every: break
  time.sleep(max(15,args.every)*60)
