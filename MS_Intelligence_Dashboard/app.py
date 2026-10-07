from datetime import datetime, timezone
from io import BytesIO
from xml.sax.saxutils import escape
import json
from collector_job import CollectorJob
import sqlite3, tempfile
from pathlib import Path
import pandas as pd
import streamlit as st
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from monitor import MODULES, P2, queries, entities, refresh, read_news, health, bookmark, setting, save_setting, review, connect
from intelligence import enrich, safe_sheet

st.set_page_config(page_title='MS Intelligence | News & Deals',page_icon='🌐',layout='wide')
st.markdown('''<style>.stApp{background:#f5f8fc}[data-testid="stSidebar"]{background:#e9f0f8}h1,h2,h3{color:#10345b}[data-testid="stMetric"]{background:white;border:1px solid #dce5f0;border-radius:10px;padding:14px}</style>''',unsafe_allow_html=True)
st.sidebar.title('MS Intelligence')
st.sidebar.caption('NEWS • DEALS • OPPORTUNITIES')
page=st.sidebar.radio('Sections',['Overview','Key news',*MODULES,'Deal tracker','Keyword alerts','Saved articles','P2 · Historical entity archive','P3 · Historical technology archive','Date review queue','Sources & status','Settings & watchlists'])
days=st.sidebar.selectbox('News date window',[1,3,7,14,30,90],index=0,format_func=lambda x:'Rolling last 24 hours' if x==1 else f'Last {x} days')
strict=st.sidebar.toggle('Strict original-publication dates',value=False,help='Exclude feed-only, updated-only and discovery-only timestamps from the main news views. Uncertain dates remain in Date review queue.')
auto=st.sidebar.toggle('Auto-refresh selected section',value=False)
interval=st.sidebar.selectbox('Refresh interval (minutes)',[15,30,60],index=1)
selected=[page] if page in MODULES else ([P2,'India · M&A deals'] if page=='Deal tracker' else list(MODULES))
providers=setting('providers',['Google News RSS','Bing News RSS'])
st.sidebar.caption('Active sources: '+(', '.join(providers) or 'Custom feeds only'))
st.sidebar.caption('Auto-refresh runs while this page is open. Background collector also uses your saved settings.')

@st.cache_resource
def collector():
 return CollectorJob()

job=collector()
def collect(target):
 if job.start(target,days):
  st.session_state['last_auto_'+page]=datetime.now(timezone.utc)

if st.sidebar.button('Refresh this section',type='primary',width='stretch'): collect(selected)
if st.sidebar.button('Refresh all modules',width='stretch'): collect(list(MODULES))
if st.sidebar.button('Stop refresh',width='stretch'): job.stop()

@st.fragment(run_every='2s')
def collection_status():
 state=job.snapshot()
 if state['running']:
  st.progress(state['progress'],text=state['message'])
  st.caption('Collection runs in the background. You can browse saved news now. New results appear as searches finish.')
 elif state['message']:
  st.caption(state['message'])
 if state['error']: st.error(state['error'])
 if st.session_state.get('collector_revision',0)!=state['revision']:
  st.session_state['collector_revision']=state['revision']
  st.rerun()

st.sidebar.caption('No paid API keys required. Google/Bing RSS + optional GDELT API + your RSS feeds.')
st.title('Intelligence dashboard' if page=='Overview' else page)
st.caption('MS HOLDINGS / MARKET INTELLIGENCE • All timestamps shown in UTC')
collection_status()


def settings_page():
 st.subheader('Free sources & key-news preferences')
 with st.form('prefs'):
  p=st.multiselect('Enabled discovery sources',['Google News RSS','Bing News RSS','GDELT API'],default=providers)
  st.caption('GDELT is optional and requires no key. One broad query per module, paced 6 seconds apart; coverage may overlap. RSS feeds configured below run independently. GDELT dates are discovery times, not confirmed publication times.')
  keywords=st.text_area('Alert keywords (one per line)',value='\n'.join(setting('keywords',['Mubadala','ADQ','GIFT City','fund administration','GRP','succession'])))
  priority=st.multiselect('Priority modules',list(MODULES),default=setting('priority_modules',[P2,'GIFT City','UAE corridors']))
  if st.form_submit_button('Save preferences'):
   save_setting('providers',p);save_setting('keywords',list(dict.fromkeys(x.strip() for x in keywords.splitlines() if x.strip())));save_setting('priority_modules',priority);st.rerun()
 st.subheader('Persistent entity watchlists')
 module=st.selectbox('Entity module',['P1 · Wealth intelligence',P2])
 upload=st.file_uploader('Import entities from first Excel column',type=['xlsx'])
 current=entities(module)
 if upload:
  try: current=pd.read_excel(upload).iloc[:,0].dropna().astype(str).tolist()
  except Exception as exc: st.error(f'Invalid spreadsheet: {exc}')
 names=st.text_area('Entity names (one per line)',value='\n'.join(current),key='entities_'+module+('_'+str(upload.file_id) if upload else ''))
 if st.button('Save entity watchlist'):
  save_setting('entities_'+module,list(dict.fromkeys(x.strip() for x in names.splitlines() if x.strip())));st.success('Saved for dashboard and background collector.')
 st.caption('P2 entity searches require an M&A term and search worldwide; geographic UAE searches run separately.')
 st.subheader('Custom searches and RSS / Atom feeds')
 with st.form('custom_add'):
  kind=st.selectbox('Type',['Keyword search','RSS / Atom feed'])
  name=st.text_input('Name'); module=st.selectbox('Assign to module',list(MODULES),index=list(MODULES).index('Custom monitoring'))
  value=st.text_input('Search query or HTTPS feed URL')
  if st.form_submit_button('Add monitor'):
   if not name.strip() or not value.strip(): st.error('Enter a name and query/feed URL.')
   elif kind=='RSS / Atom feed' and not value.startswith('https://'): st.error('Enter an HTTPS feed URL.')
   else:
    key='custom_searches' if kind=='Keyword search' else 'rss_feeds'; field='query' if kind=='Keyword search' else 'url'
    records=setting(key,[])
    if any(r['name']==name.strip() and r['module']==module for r in records): st.error('This name already exists in that module. Remove it first to replace it.')
    else:
     records.append({'name':name.strip(),'module':module,field:value.strip()});save_setting(key,records);st.rerun()
 for key in ['custom_searches','rss_feeds']:
  for i,item in enumerate(setting(key,[])):
   cols=st.columns([5,1]);cols[0].write(f"{item['module']} / {item['name']} — {item.get('query',item.get('url'))}")
   if cols[1].button('Remove',key=f'del_{key}_{i}'):
    records=setting(key,[]);records.pop(i);save_setting(key,records);st.rerun()
 st.caption('Custom feeds in hiring, cybersecurity, data analytics and UAE people modules pass topic filters. Other modules use your feed assignment. Entries without publication dates are skipped. Settings and reviews are local to this installation and shared by its users.')
 config={k:setting(k,[]) for k in ['providers','keywords','priority_modules','custom_searches','rss_feeds']}
 st.download_button('Export monitoring settings',json.dumps(config,indent=2),'monitoring_settings.json','application/json')
 if st.button('Prepare archive backup'):
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'news.sqlite3'
   dest=sqlite3.connect(path)
   try:
    with connect() as source: source.backup(dest)
   finally: dest.close()
   st.download_button('Download database backup',path.read_bytes(),'news.sqlite3','application/octet-stream')
 st.caption('Backup includes news, bookmarks, reviews and settings. To restore, stop the app and collector, keep a copy of your existing data folder, then place this file at data/news.sqlite3. Start the app again.')


def export_buttons(view):
 columns=['title','source','published','date_kind','provider','classification','priority','priority_reason','date_status','date_detail','report_count','sector','stage_signal','amount_mentions','buyer','target','value_note','verified_status','owner','action','note','url','summary']
 output=safe_sheet(view[columns])
 d1,d2,d3=st.columns(3)
 d1.download_button('Download CSV',output.to_csv(index=False).encode('utf-8-sig'),'news.csv','text/csv')
 excel=BytesIO()
 with pd.ExcelWriter(excel,engine='openpyxl') as writer: output.to_excel(writer,index=False,sheet_name='Intelligence')
 d2.download_button('Download Excel',excel.getvalue(),'intelligence.xlsx','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
 if d3.button('Prepare PDF digest'):
  out=BytesIO(); styles=getSampleStyleSheet(); story=[Paragraph('MS Intelligence | '+escape(page),styles['Title']),Paragraph(f'Generated {datetime.now(timezone.utc):%d %b %Y %H:%M} UTC | {len(view)} articles',styles['Normal']),Paragraph('Automated headline signals require source verification. Amount mentions are not verified transaction values.',styles['Normal']),Spacer(1,18)]
  for row in view.itertuples():
   story.extend([Paragraph(escape(row.title),styles['Heading3']),Paragraph(escape(row.source+' | '+row.published[:16]+' UTC | '+row.date_kind),styles['Normal']),Paragraph(escape(row.classification),styles['Normal']),Paragraph(escape('Priority '+str(row.priority)+' | '+row.priority_reason),styles['Normal']),Paragraph(escape(row.summary[:700]),styles['BodyText'])])
   if row.note: story.append(Paragraph('Analyst note: '+escape(row.note),styles['BodyText']))
   story.extend([Paragraph('<link href="'+escape(row.url,{'"':'&quot;'})+'">Read original source</link>',styles['Normal']),Spacer(1,12)])
  SimpleDocTemplate(out).build(story)
  st.download_button('Save PDF',out.getvalue(),'intelligence_digest.pdf','application/pdf')
 brief='\n\n'.join(f'{i+1}. {r.title}\n{r.source} | {r.published[:10]}\n{r.url}' for i,r in enumerate(view.head(10).itertuples()))
 st.download_button('Download top-10 text brief',brief,'daily_brief.txt','text/plain')


def article_card(row):
 with st.container(border=True):
  st.subheader(('📌 ' if row.pinned else '')+row.title)
  st.caption(f'{row.source} • {row.published[:16]} UTC • {row.date_kind} • {row.provider}')
  st.caption(row.classification)
  st.caption(f'{row.date_status} · {row.date_detail} · {max(1,row.report_count)} collected report(s)')
  st.write(f'**Priority {row.priority}** · {row.sector} · {row.stage_signal}')
  if row.alert_matches: st.info('Keyword match: '+row.alert_matches)
  if row.summary: st.write(row.summary[:650])
  if row.amount_mentions: st.caption('Headline amount mention (not verified deal value): '+row.amount_mentions)
  a,b,c,d=st.columns([4,1,1,1]);a.link_button('Read source ↗',row.url)
  if b.button('Unsave' if row.bookmarked else 'Save',key='save_'+row.id): bookmark(row.id,not row.bookmarked);st.rerun()
  if c.button('Unread' if row.read_flag else 'Read',key='read_'+row.id): review(row.id,read_flag=not row.read_flag);st.rerun()
  if d.button('Unpin' if row.pinned else 'Pin',key='pin_'+row.id): review(row.id,pinned=not row.pinned);st.rerun()
  with st.expander('Why this matters / analyst review'):
   st.write(row.priority_reason)
   st.caption('Priority, sector and deal stage are keyword heuristics—not a factual assessment. Buyer, target and confirmed status below are analyst-entered fields.')
   with st.form('review_'+row.id):
    left,right=st.columns(2)
    buyer=left.text_input('Buyer / investor',value=row.buyer);target=right.text_input('Target / asset',value=row.target)
    value=left.text_input('Verified value and currency / source note',value=row.value_note)
    options=['Unreviewed','Rumoured / talks','Announced','Agreed','Approved','Completed','Cancelled / blocked','Not a deal']
    stage=right.selectbox('Analyst-reviewed status',options,index=options.index(row.verified_status) if row.verified_status in options else 0)
    owner=left.text_input('Internal owner',value=row.owner)
    actions=['New','Research','Contact candidate','Monitor','Closed']
    action=right.selectbox('Next action',actions,index=actions.index(row.action) if row.action in actions else 0)
    note=st.text_area('Notes and next steps',value=row.note)
    if st.form_submit_button('Save review'):
     review(row.id,buyer=buyer,target=target,value_note=value,verified_status=stage,owner=owner,action=action,note=note);st.rerun()


@st.fragment(run_every=f'{interval}m' if auto and page!='Settings & watchlists' else None)
def workspace():
 if page=='Settings & watchlists': settings_page();return
 if auto and (datetime.now(timezone.utc)-st.session_state.get('last_auto_'+page,datetime.min.replace(tzinfo=timezone.utc))).total_seconds()>=interval*60: collect(selected)
 data=read_news(); status=health()
 if page=='Sources & status':
  st.caption('Latest attempt per source/query: OK includes zero results; ERROR retains previous news. Query coverage is not comprehensive. No scraped full articles are stored.')
  st.dataframe(status,width='stretch',hide_index=True)
  st.subheader('Configured searches')
  st.dataframe(pd.DataFrame([(m,t,q) for m in MODULES for t,q in queries(m).items()],columns=['Module','Topic','Query']),hide_index=True,width='stretch')
  st.link_button('GDELT API documentation','https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/')
  return
 if not data.empty:
  now=pd.Timestamp.now(tz='UTC'); dates=pd.to_datetime(data.published,utc=True)
  data=data[(dates>=now-pd.Timedelta(days=days)) & (dates<=now)]
  pending=data[data.original_published.isna()].id.nunique()
  if page=='Date review queue': data=data[data.original_published.isna()]
  elif strict:
   data=data[data.original_published.notna()]
   st.caption(f'{pending} story/stories with uncertain publication dates withheld. See Date review queue to inspect them; they are not confirmed as new.')
  else: st.caption('Fast mode: last 24 hours uses feed timestamps unless an original date was previously verified. Resurfaced stories may appear. Similar headlines are not merged.')
 data=enrich(data,setting('keywords',['Mubadala','ADQ','GIFT City','fund administration','GRP','succession']),setting('priority_modules',[P2,'GIFT City','UAE corridors']))
 if page in MODULES or page in ['P2 · Historical entity archive','P3 · Historical technology archive']: data=data[data.module==page]
 if page=='Saved articles': data=data[data.bookmarked==1]
 if page=='Keyword alerts': data=data[data.alert_matches!='']
 if page=='Deal tracker': data=data[(data.deal_signal==True)|(data.verified_status!='Unreviewed')]
 unique=data.drop_duplicates('id'); cols=st.columns(4)
 cols[0].metric('Unique articles',len(unique));cols[1].metric('Unread',int((unique.read_flag==0).sum()));cols[2].metric('Keyword matches',int((unique.alert_matches!='').sum()));cols[3].metric('Deal headline signals',int(unique.deal_signal.sum()) if not unique.empty else 0)
 relevant=status[status.module.isin(selected)] if not status.empty else status
 if not relevant.empty:
  st.caption('Last fetch attempt: '+relevant.checked.max()[:16]+' UTC')
  if (relevant.status=='ERROR').any(): st.warning('Some sources failed on their latest attempt. Previously collected articles remain visible. See Sources & status.')
 if page==P2: st.info('P2 covers UAE and global M&A. Use Topic to separate UAE acquisitions, cross-border deals, global deals, buyouts, stake sales and approvals. Older generic P2 coverage remains in Historical entity archive.')
 if data.empty:
  st.info('No dated stories match this view. If strict mode is on, check Date review queue for stories whose original publication could not be verified. Refresh this section, widen the date window, or check source status. No sample headlines are shown.')
  return
 if page=='Overview':
  c1,c2=st.columns(2)
  with c1: st.caption('Collected article coverage—not deal counts');st.bar_chart(data.groupby('module').id.nunique(),color='#1762a7')
  with c2:
   st.caption('Daily coverage by displayed publication date')
   timeline=unique.assign(day=pd.to_datetime(unique.published,utc=True).dt.date).groupby('day').size()
   st.line_chart(timeline,color='#1762a7')
 a,b,c=st.columns([2,1,1]); keyword=a.text_input('Search headlines and snippets',key='search_'+page)
 topics=b.multiselect('Topic / country',sorted(data.topic.unique()),key='topic_'+page)
 sources=c.multiselect('Publisher',sorted(data.source.unique()),key='publisher_'+page)
 with st.expander('More filters & sorting',expanded=page in ['Deal tracker','Key news']):
  a,b,c=st.columns(3)
  sectors=a.multiselect('Sector signal',sorted(data.sector.unique()))
  stages=b.multiselect('Headline deal-stage signal',sorted(data.stage_signal.unique()))
  sort=c.selectbox('Sort by',['Priority','Latest'],index=1)
  a,b,c=st.columns(3)
  unread=a.checkbox('Unread only'); alerts=b.checkbox('Keyword matches only'); score=c.slider('Minimum priority',0,100,0)
 if keyword: data=data[(data.title+' '+data.summary).str.contains(keyword,case=False,regex=False)]
 if topics: data=data[data.topic.isin(topics)]
 if sources: data=data[data.source.isin(sources)]
 if sectors: data=data[data.sector.isin(sectors)]
 if stages: data=data[data.stage_signal.isin(stages)]
 if unread: data=data[data.read_flag==0]
 if alerts: data=data[data.alert_matches!='']
 data=data[data.priority>=score]
 labels=data.groupby('id').apply(lambda g:' | '.join(sorted(set(g.module+' / '+g.topic))),include_groups=False).to_dict() if not data.empty else {}
 view=data.drop_duplicates('id').copy();view['classification']=view.id.map(labels)
 view=view.sort_values(['pinned','priority','published'] if sort=='Priority' else ['published'],ascending=False)
 if page=='Key news':
  limit=st.selectbox('Key-news shortlist size',['All',10,20,50],index=0)
  if limit!='All': view=view.head(limit)
  st.caption('Rule-based shortlist, ranked by freshness, M&A/policy signals, geography, watch keywords and manual pins. Score is not a probability or independent verification.')
 if page=='Deal tracker':
  st.caption('Article-based research queue. Several articles can refer to one deal. Amount mentions can refer to valuation, revenue or fund size; they are never summed as deal volume.')
  st.dataframe(view[['title','sector','stage_signal','amount_mentions','buyer','target','verified_status','owner','action','url']],hide_index=True,width='stretch')
 export_buttons(view)
 st.subheader(f'News workspace · {len(view)} articles')
 st.caption('All matching stories are available through pagination and exports; there is no default top-news cutoff. RSS snippets are publisher excerpts. GDELT headlines may have no snippet and show seen time. Search tags and automated signals need source verification. Keyword alerts stay inside this dashboard; no messages are sent.')
 pages=max(1,(len(view)+14)//15)
 page_key='page_'+page
 if st.session_state.get(page_key,1)>pages: st.session_state[page_key]=1
 number=st.number_input('Page',min_value=1,max_value=pages,value=1,key=page_key)
 for row in view.iloc[(number-1)*15:number*15].itertuples(): article_card(row)
workspace()
