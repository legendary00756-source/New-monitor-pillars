"""Publication-date checks, conservative duplicate matching and topic gates."""
from datetime import datetime, timezone
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode, urljoin
from difflib import SequenceMatcher
import json,re
from bs4 import BeautifulSoup
from dateutil.parser import isoparse
import requests

UTC=timezone.utc

def iso_date(value):
 try:
  # Date-only / timezone-less evidence cannot prove membership in a rolling 24h window.
  if not isinstance(value,str) or len(value)<16: return None
  d=isoparse(value)
  if d.tzinfo is None: return None
  return d.astimezone(UTC).isoformat()
 except (ValueError,TypeError,OverflowError): return None

def canonical_url(url):
 p=urlsplit(url)
 query=[(k,v) for k,v in parse_qsl(p.query,keep_blank_values=True) if not k.lower().startswith('utm_') and k.lower() not in {'fbclid','gclid','mc_cid','mc_eid','ref','output','oc'}]
 return urlunsplit((p.scheme.lower(),p.netloc.lower().removeprefix('www.'),p.path.rstrip('/') or '/',urlencode(sorted(query)),''))

def headline_key(title,source=''):
 title=title.casefold().strip()
 if source:
  title=re.sub(r'\s*[-–—|]\s*'+re.escape(source.casefold())+r'\s*$','',title)
 return ' '.join(re.findall(r'\w+',title))

def same_story(a,b):
 """Conservative: numeric facts and event-stage changes must match."""
 if a==b: return True
 aa=a.split();bb=b.split()
 if min(len(aa),len(bb))<6: return False
 if re.findall(r'\d+(?:\.\d+)?',a)!=re.findall(r'\d+(?:\.\d+)?',b): return False
 stages={'announces','announced','plans','planned','completes','completed','approved','blocked','resigns','appointed','cancelled'}
 if (set(aa)&stages)!=(set(bb)&stages): return False
 return len(set(aa)&set(bb))/max(1,len(set(aa)|set(bb)))>=0.84 and SequenceMatcher(None,a,b).ratio()>=0.93

def publication_metadata(body,url):
 """Only article publication fields; never dateModified, HTTP Last-Modified or page footer dates."""
 soup=BeautifulSoup(body,'html.parser'); dates=[]
 for script in soup.find_all('script',type='application/ld+json'):
  try: payload=json.loads(script.string or script.get_text())
  except (ValueError,TypeError): continue
  def walk(x):
   if isinstance(x,list):
    for v in x: walk(v)
   elif isinstance(x,dict):
    types=x.get('@type',[]);types=[types] if isinstance(types,str) else types
    if any(str(t).split('/')[-1] in {'NewsArticle','Article','ReportageNewsArticle','BlogPosting','AnalysisNewsArticle'} for t in types):
     d=iso_date(x.get('datePublished'))
     if d: dates.append(d)
    # Walk graph containers only: related-article lists must not date the current article.
    if '@graph' in x: walk(x['@graph'])
  walk(payload)
 for meta in soup.find_all('meta'):
  key=(meta.get('property') or meta.get('name') or '').lower()
  if key in {'article:published_time','datepublished','parsely-pub-date','pubdate','publishdate'}:
   d=iso_date(meta.get('content'))
   if d: dates.append(d)
 canonical=url
 link=soup.find('link',rel='canonical')
 if link and link.get('href'):
  candidate=urljoin(url,link['href'])
  if urlsplit(candidate).scheme in {'http','https'}: canonical=candidate
 return min(dates) if dates else None,canonical_url(canonical)

def inspect_publication(row,provider):
 ident,title,url,source,feed_date,summary,first_seen=row
 base={'original_published':None,'canonical':canonical_url(url),'date_status':'Unverified publication','detail':'Publisher publication timestamp unavailable','feed_date':feed_date}
 # Current Google RSS URLs can hide publisher links. Do not treat discovery date as original publication.
 if urlsplit(url).netloc in {'news.google.com','news.google.co.in'}:
  base['detail']='Google redirect: original publisher timestamp not available; review source'
  return base
 try:
  with requests.get(url,timeout=(4,8),headers={'User-Agent':'MSIntelligenceMonitor/3.0'},stream=True) as response:
   response.raise_for_status()
   if 'html' not in response.headers.get('Content-Type','').lower(): return base
   chunks=[];size=0
   for chunk in response.iter_content(32768):
    chunks.append(chunk);size+=len(chunk)
    if size>=1_000_000: break
   date,canonical=publication_metadata(b''.join(chunks),response.url)
  base['canonical']=canonical
  if date:
   base.update(original_published=date,date_status='Publisher publication',detail='Original publication metadata; page-update dates ignored')
 except requests.RequestException as exc:
  base['detail']='Publisher check failed: '+type(exc).__name__
 return base

HIRING=r'\b(hiring|hires|recruit(?:ment|ing|s)?|job openings?|job vacancies|vacancies|job creation|creates?\s+(?:\d[\d,]*\s+)?jobs|add(?:s|ing)?\s+(?:\d[\d,]*\s+)?jobs|hiring drive|talent acquisition)\b'
TECH=r'\b(tech(?:nology)?|software|engineer\w*|developer\w*|cyber\w*|data|AI|artificial intelligence|cloud|devops|fintech)\b'
MOVES=r'\b(appoint\w*|nam(?:es|ed)\b|joins?|joined|resign\w*|steps? down|stepped down|succeeds?|promot\w*|retir\w*|new CEO|new CFO|new chief|new chairman|takes? (?:over|helm)|leaves?|depart\w*)\b'
LEADERS=r'\b(CEO|CFO|CIO|COO|CTO|CISO|chief|chairman|chairwoman|chairperson|president|director|partner|minister|governor|head|executive|leadership|board|ambassador)\b'

def curate(module,title,summary):
 text=title+' '+summary
 if module=='P3 · Global tech hiring':
  if not re.search(HIRING,title,re.I): return False,'No hiring signal in headline'
  if not (re.search(TECH,text,re.I) or re.search(r'\bIT\b',text)): return False,'No technology hiring context'
  if re.search(r'\b(layoffs?|job cuts?|hiring freeze|hiring slowdown|not hiring|stops? hiring|halts? hiring|fake jobs?|job scams?)\b',title,re.I): return False,'Layoff/freeze/scam article, not active hiring'
 if module=='Global cybersecurity' and not re.search(r'\b(cyber\w*|ransomware|malware|breach\w*|vulnerabilit\w*|zero.day|CVE.\d|phishing|infosec|data security|information security)\b',text,re.I): return False,'No cybersecurity signal'
 if module=='Global data analytics' and not re.search(r'\b(data analy\w*|data scien\w*|business intelligence|data engineer\w*|data warehouse\w*|data lake\w*|analytics|data governance|data platform\w*)\b',text,re.I): return False,'No data analytics signal'
 if module=='UAE · Key people & movements':
  if not re.search(MOVES,title,re.I) or not re.search(LEADERS,text,re.I): return False,'No leadership movement signal'
  if not re.search(r'\b(UAE|United Arab Emirates|Dubai|Abu Dhabi|Sharjah|Emirati|ADGM|DIFC|Mubadala|ADQ|ADIA|Emirates|DP World|ADNOC|FAB)\b',text,re.I): return False,'No UAE connection'
 return True,''

def consolidate_news(data):
 """Collapse old stored duplicates for display without deleting raw records/reviews."""
 if data.empty: return data
 data=data.copy(); representatives=[]; mapping={}
 unique=data.sort_values('published').drop_duplicates('id')
 for row in unique.itertuples():
  key=headline_key(row.title,row.source);url=canonical_url(row.url);chosen=None
  for prev,pkey,purl in representatives:
   close=abs((datetime.fromisoformat(row.published)-datetime.fromisoformat(prev.published)).total_seconds())<=7*86400
   if url==purl or key==pkey or (close and same_story(key,pkey)):
    chosen=prev.id;break
  if chosen is None: representatives.append((row,key,url));chosen=row.id
  mapping[row.id]=chosen
 data['group_id']=data.id.map(mapping)
 data['member_ids']=''
 for ident,group in data.groupby('group_id'):
  mask=data.group_id==ident
  base=group[group.id==ident].iloc[0]
  data.loc[mask,'member_ids']=json.dumps(list(dict.fromkeys(group.id)))
  for col in ['title','url','source','published','summary','first_seen','provider','date_kind']:
   data.loc[mask,col]=base[col]
  proofs=group.original_published.dropna()
  if len(proofs):
   data.loc[mask,'original_published']=proofs.min()
   data.loc[mask,'published']=min(base.published,proofs.min())
   data.loc[mask,'date_status']='Publisher publication'
   data.loc[mask,'date_kind']='Publisher publication'
  for col in ['bookmarked','read_flag','pinned']: data.loc[mask,col]=group[col].max()
  data.loc[mask,'report_count']=max(group.id.nunique(),group.report_count.max())
  data.loc[mask,'note']=' | '.join(dict.fromkeys(x for x in group.note if x))
 data['id']=data.group_id
 return data.drop(columns='group_id').drop_duplicates(['id','module','topic'])
