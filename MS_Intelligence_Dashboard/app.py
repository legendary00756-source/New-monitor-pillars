from pathlib import Path
from datetime import datetime, timezone, timedelta
from io import BytesIO
from xml.sax.saxutils import escape
import pandas as pd
import streamlit as st
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from monitor import MODULES, queries, entities, refresh, read_news, health, bookmark

st.set_page_config(page_title='MS Intelligence | News Monitor',page_icon='🌐',layout='wide')
st.markdown('''<style>.stApp {background:#f5f8fc} [data-testid="stSidebar"]{background:#e9f0f8} h1,h2,h3{color:#10345b} [data-testid="stMetric"]{background:white;border:1px solid #dce5f0;border-radius:10px;padding:14px} .stButton button[kind="primary"]{background:#1762a7}</style>''',unsafe_allow_html=True)
st.sidebar.title('MS Intelligence')
st.sidebar.caption('MARKET & INVESTMENT MONITOR')
page=st.sidebar.radio('Sections',['Overview',*MODULES,'Saved articles','Sources & status'])
days=st.sidebar.selectbox('Published within',[1,3,7,14,30,90],index=2,format_func=lambda x:f'Last {x} days')
auto=st.sidebar.toggle('Auto-refresh selected section',value=False)
interval=st.sidebar.selectbox('Refresh interval (minutes)',[15,30,60],index=1)
st.sidebar.caption('Auto-refresh works while this page is open. Use the included monitor command for background collection.')
selected = [page] if page in MODULES else list(MODULES)
overrides={}
if page.startswith(('P1','P2')):
 with st.sidebar.expander('Entity watchlist',expanded=False):
  upload=st.file_uploader('Optional replacement Excel (first column = entity)',type=['xlsx'])
  options=entities(page)
  if upload:
   try: options=pd.read_excel(upload).iloc[:,0].dropna().astype(str).tolist()
   except Exception as exc: st.error(f'Unable to read watchlist: {exc}')
  overrides[page]=st.multiselect('Entities to fetch',options,default=options)
  st.caption('Uploaded watchlist applies to this browser session. Replace the matching legacy Excel file for permanent background use.')

def collect(target):
 bar=st.progress(0,text='Fetching public news feeds…')
 result=refresh(target,days,overrides,lambda value,label:bar.progress(value,text=label))
 bar.empty(); errors=sum(x[2]=='ERROR' for x in result)
 st.session_state['last_result']=f'Checked {len(result)} queries; {errors} failed. See Sources & status for details.'
 st.session_state['last_auto']=datetime.now(timezone.utc)

if st.sidebar.button('Refresh this section',type='primary',use_container_width=True): collect(selected)
if st.sidebar.button('Refresh all modules',use_container_width=True): collect(list(MODULES))
st.sidebar.caption('No paid API key required. Headlines come from public Google News RSS searches; coverage is not exhaustive.')
st.title('Intelligence dashboard' if page=='Overview' else page)
st.caption('MS HOLDINGS  /  LIVE NEWS WORKSPACE')
if 'last_result' in st.session_state: st.caption(st.session_state.last_result)

@st.fragment(run_every=f'{interval}m' if auto else None)
def workspace():
 if auto and (datetime.now(timezone.utc)-st.session_state.get('last_auto',datetime.min.replace(tzinfo=timezone.utc))).total_seconds()>=interval*60:
  collect(selected)
 data=read_news(); status=health()
 if page=='Sources & status':
  st.subheader('Latest collection result per query')
  st.caption('OK means the feed was retrieved, including when it returned zero matching dated articles. ERROR means a fetch failed; previously saved articles remain available. All times UTC.')
  st.dataframe(status,use_container_width=True,hide_index=True)
  st.subheader('Configured searches')
  st.dataframe(pd.DataFrame([(m,t,q) for m in MODULES for t,q in queries(m).items()],columns=['Module','Topic','Query']),hide_index=True,use_container_width=True)
  return
 if not data.empty:
  dates=pd.to_datetime(data.published,utc=True)
  data=data[dates>=pd.Timestamp.now(tz='UTC')-pd.Timedelta(days=days)]
 if page in MODULES: data=data[data.module==page]
 if page=='Saved articles': data=data[data.bookmarked==1]
 unique=data.drop_duplicates('id')
 cols=st.columns(4)
 cols[0].metric('Unique articles',len(unique)); cols[1].metric('Publishers',unique.source.nunique())
 cols[2].metric('Modules with results',data.module.nunique()); cols[3].metric('Queries with errors',int((status.status=='ERROR').sum()) if not status.empty else 0)
 relevant_status=status[status.module.isin(selected)] if not status.empty else status
 if not relevant_status.empty:
  st.caption('Last attempt (UTC): '+relevant_status.checked.max())
  if (relevant_status.status=='ERROR').any(): st.warning('Some feeds could not be refreshed. Existing articles may be older; check Sources & status.')
 if data.empty:
  st.info('No collected news in this view. Click Refresh this section, widen the date window, or inspect Sources & status. No sample headlines are mixed into live results.')
  return
 if page=='Overview':
  st.subheader('Coverage by module')
  st.bar_chart(data.groupby('module').id.nunique(),color='#1762a7')
 a,b,c=st.columns([2,1,1])
 keyword=a.text_input('Search headlines and snippets',key='search_'+page)
 topics=b.multiselect('Topic / country',sorted(data.topic.unique()),key='topic_'+page)
 sources=c.multiselect('Publisher',sorted(data.source.unique()),key='publisher_'+page)
 if keyword: data=data[(data.title+' '+data.summary).str.contains(keyword,case=False,regex=False)]
 if topics: data=data[data.topic.isin(topics)]
 if sources: data=data[data.source.isin(sources)]
 # Aggregate all matching tags before display so cross-module stories remain discoverable.
 if not data.empty:
  labels=data.groupby('id').apply(lambda g:' | '.join(sorted(set(g.module+' / '+g.topic))),include_groups=False).to_dict()
 else: labels={}
 view=data.drop_duplicates('id').copy()
 view['classification']=view.id.map(labels)
 export=view[['title','source','published','classification','url','summary']].copy()
 for col in export.select_dtypes('object'):
  export[col]=export[col].map(lambda x:"'"+x if isinstance(x,str) and x.startswith(('=','+','-','@')) else x)
 d1,d2,d3=st.columns(3)
 d1.download_button('Download CSV',export.to_csv(index=False).encode('utf-8-sig'),'news.csv','text/csv')
 excel=BytesIO()
 with pd.ExcelWriter(excel,engine='openpyxl') as writer: export.to_excel(writer,index=False,sheet_name='News')
 d2.download_button('Download Excel',excel.getvalue(),'news.xlsx','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
 if d3.button('Prepare PDF digest'):
  out=BytesIO(); styles=getSampleStyleSheet(); story=[Paragraph('MS Intelligence | '+escape(page),styles['Title']),Paragraph(f'Generated {datetime.now(timezone.utc):%d %b %Y %H:%M} UTC | {len(view)} articles',styles['Normal']),Spacer(1,18)]
  for row in view.itertuples():
   story.extend([Paragraph(escape(row.title),styles['Heading3']),Paragraph(escape(row.source+' | '+row.published[:16]+' UTC'),styles['Normal']),Paragraph(escape(row.summary[:700]),styles['BodyText']),Paragraph('<link href="'+escape(row.url,{'"':'&quot;'})+'">Read original source</link>',styles['Normal']),Spacer(1,12)])
  SimpleDocTemplate(out).build(story)
  st.download_button('Save PDF',out.getvalue(),'intelligence_digest.pdf','application/pdf')
 st.subheader(f'Latest news · {len(view)} articles')
 st.caption('Publisher-provided RSS snippets, not AI summaries or independently verified findings. Publication times are UTC. Search tags indicate query matches, not verified deal classifications.')
 page_no=st.number_input('Page',min_value=1,max_value=max(1,(len(view)+19)//20),value=1,key='page_'+page)
 for row in view.iloc[(page_no-1)*20:page_no*20].itertuples():
  with st.container(border=True):
   st.subheader(row.title)
   st.caption(f'{row.source}  •  {row.published[:16]} UTC  •  {row.classification}')
   if row.summary: st.write(row.summary[:650])
   l,r=st.columns([5,1]); l.link_button('Read article ↗',row.url)
   if r.button('Unsave' if row.bookmarked else 'Save',key='save_'+row.id):
    bookmark(row.id,not row.bookmarked); st.rerun()
workspace()
