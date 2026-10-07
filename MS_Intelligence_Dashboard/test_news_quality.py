import unittest,tempfile
from datetime import datetime,timezone,timedelta
from pathlib import Path
from unittest.mock import patch
import pandas as pd
import monitor
from news_quality import publication_metadata,canonical_url,headline_key,same_story,curate

class QualityTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.old=monitor.DB;monitor.DB=Path(self.temp.name)/'news.sqlite3'
  monitor.save_setting('providers',['Google News RSS'])
 def tearDown(self):monitor.DB=self.old;self.temp.cleanup()
 def test_original_date_beats_update(self):
  body='<script type="application/ld+json">{"@type":"NewsArticle","datePublished":"2024-01-01T12:00:00Z","dateModified":"2026-10-07T12:00:00Z"}</script>'
  date,url=publication_metadata(body,'https://example.org/a?utm_source=test')
  self.assertEqual(date,'2024-01-01T12:00:00+00:00');self.assertEqual(url,'https://example.org/a')
  self.assertIsNone(publication_metadata('<meta property="article:modified_time" content="2026-10-07T12:00:00Z">','https://example.org/a')[0])
 def test_unknown_timezone_and_dates_are_not_guessed(self):
  for value in ['2026-10-07','2026-10-07T12:00:00']:
   body='<meta property="article:published_time" content="'+value+'">'
   self.assertIsNone(publication_metadata(body,'https://example.org')[0])
 def test_curation(self):
  m='P3 · Global tech hiring'
  self.assertTrue(curate(m,'US software company hiring 200 developers','')[0])
  for title in ['AI platform launches new product','Tech company announces layoffs','Tech hiring freeze expands']:
   self.assertFalse(curate(m,title,'technology')[0],title)
  self.assertTrue(curate('Global cybersecurity','New ransomware attack hits banks','')[0])
  self.assertFalse(curate('Global data analytics','New AI chatbot launched','')[0])
  self.assertTrue(curate('Global data analytics','New data analytics platform launches','')[0])
  self.assertTrue(curate('UAE · Key people & movements','Dubai bank appoints new CEO','')[0])
  self.assertFalse(curate('UAE · Key people & movements','Dubai CEO discusses economic outlook','')[0])
 def test_duplicate_matching_keeps_material_updates(self):
  a=headline_key('Company announces acquisition of target for USD 100 million - Publisher','Publisher')
  self.assertEqual(a,headline_key('Company announces acquisition of target for USD 100 million'))
  self.assertFalse(same_story(a,a.replace('announces','completes')))
  self.assertFalse(same_story(a,a.replace('100','200')))
  self.assertEqual(canonical_url('https://www.example.org/a?utm_source=x&fbclid=a&id=1'),canonical_url('https://example.org/a?id=1'))
 def test_repeat_resurfacing_preserves_original_date_and_multi_tags(self):
  now=datetime.now(timezone.utc);old=(now-timedelta(days=10)).isoformat()
  row=('a','Company acquires Target for USD 100 million','https://example.org/a','Publisher',now.isoformat(),'News',now.isoformat())
  with monitor.connect() as c:
   c.execute('INSERT INTO date_evidence VALUES(?,?,?,?,?,?,?)',('a',old,row[2],'Publisher publication','Previously verified',row[4],row[4]))
  def evidence(row,provider): raise AssertionError('Publisher check must not run')
  with patch.object(monitor,'fetch',return_value=[row]),patch.object(monitor,'inspect_publication',side_effect=evidence):
   monitor.refresh(['India · M&A deals'])
   monitor.refresh(['India · Private equity'])
  data=monitor.read_news();self.assertEqual(data.id.nunique(),1)
  self.assertEqual(data.published.iloc[0],old)
  self.assertTrue((pd.to_datetime(data.published,utc=True)<pd.Timestamp.now(tz='UTC')-pd.Timedelta(days=1)).all())
 def test_cross_publisher_reports_retained_and_feed_mode_default(self):
  now=datetime.now(timezone.utc).isoformat()
  a=('a','Company acquires Target for USD 100 million - Source A','https://news.google.com/rss/articles/a','Source A',now,'News',now)
  b=('b','Company acquires Target for USD 100 million','https://example.org/b','Source B',now,'News',now)
  def evidence(row,provider):return {'original_published':None,'canonical':row[2],'date_status':'Unverified publication','detail':'No original date','feed_date':row[4]}
  with patch.object(monitor,'fetch',return_value=[a,b]),patch.object(monitor,'inspect_publication',side_effect=evidence):monitor.refresh(['India · M&A deals'])
  self.assertEqual(monitor.read_news().id.nunique(),2)
  from streamlit.testing.v1 import AppTest
  app=AppTest.from_file(str(Path(__file__).parent/'app.py')).run(timeout=30)
  self.assertEqual(len(app.exception),0)
  self.assertEqual(app.sidebar.selectbox[0].value,1)
  self.assertFalse(app.sidebar.toggle[0].value)
  self.assertTrue(any('Company acquires' in h.value for h in app.subheader))
  app.sidebar.radio[0].set_value('Date review queue').run(timeout=30)
  self.assertEqual(len(app.exception),0)
  self.assertTrue(any('Company acquires' in h.value for h in app.subheader))
if __name__=='__main__':unittest.main()
