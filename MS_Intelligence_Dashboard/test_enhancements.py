import unittest,tempfile,json
from pathlib import Path
from unittest.mock import patch,MagicMock
from datetime import datetime,timezone
import monitor
from intelligence import analyze,safe_sheet
import pandas as pd

class EnhancementTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.old=monitor.DB;monitor.DB=Path(self.temp.name)/'db.sqlite3'
  monitor.save_setting('providers',['Google News RSS'])
  self.publication_patch=patch.object(monitor,'inspect_publication',side_effect=lambda row,provider: {'original_published':row[4],'canonical':row[2],'date_status':'Publisher publication','detail':'TEST FIXTURE','feed_date':row[4]})
  self.publication_patch.start()
  self.addCleanup(self.publication_patch.stop)
 def tearDown(self): monitor.DB=self.old;self.temp.cleanup()
 def test_p2_queries_and_watchlist_persistence(self):
  monitor.save_setting('entities_'+monitor.P2,['Buyer Group'])
  qs=monitor.queries(monitor.P2)
  self.assertIn('Global M&A',qs);self.assertIn('UAE acquisitions',qs)
  self.assertIn('acquisition',qs['Entity: Buyer Group'])
  self.assertNotIn('UAE',qs['Entity: Buyer Group'])
  monitor.save_setting('custom_searches',[{'name':'Test','module':monitor.P2,'query':'manufacturing takeover'}])
  self.assertEqual(monitor.queries(monitor.P2)['Custom: Test'],'manufacturing takeover')
 def test_gdelt_seen_time_and_partial_failure(self):
  now=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
  rows=monitor.parse_gdelt({'articles':[{'title':'Buyer acquires Target for USD 100 million','url':'https://example.org/a','domain':'example.org','seendate':now}]},7)
  with patch.object(monitor,'fetch',side_effect=TimeoutError()),patch.object(monitor,'fetch_gdelt',return_value=rows):
   monitor.refresh(['India · M&A deals'],providers=['Google News RSS','GDELT API'])
  df=monitor.read_news();self.assertEqual(len(df),1);self.assertEqual(df.date_kind.iloc[0],'GDELT seen time')
  self.assertEqual(set(monitor.health().status),{'OK','ERROR'})
  monitor.review(df.id.iloc[0],buyer='Buyer',target='Target',pinned=1,note='Check filing')
  self.assertEqual(monitor.read_news().buyer.iloc[0],'Buyer')
 def test_atom_feed(self):
  now=datetime.now(timezone.utc).isoformat()
  body=f'<feed xmlns="http://www.w3.org/2005/Atom"><title>News</title><entry><title>Deal update</title><link href="https://example.org/a"/><updated>{now}</updated></entry></feed>'.encode()
  response=MagicMock();response.__enter__.return_value.read.return_value=body
  with patch.object(monitor,'urlopen',return_value=response): self.assertEqual(len(monitor.fetch_rss('https://example.org/feed',7)),0)
 def test_signals_are_cautious(self):
  now=datetime.now(timezone.utc).isoformat()
  a=analyze('Buyer may acquire factory for USD 100 million','',now,['factory'])
  self.assertEqual(a['stage_signal'],'Talks / proposal signal');self.assertEqual(a['amount_mentions'],'USD 100 million')
  self.assertEqual(a['sector'],'Industrials')
  b=analyze('Buyer denies completed acquisition','',now)
  self.assertEqual(b['stage_signal'],'Negation present — review manually')
  self.assertTrue(safe_sheet(pd.DataFrame({'x':[' =HYPERLINK("x")']})).x.iloc[0].startswith("'"))
 def test_legacy_migration(self):
  with monitor.connect() as c:
   c.execute("DELETE FROM migrations WHERE version='v2'")
   c.execute("INSERT INTO tags VALUES('legacy','P2 · Entity intelligence','Market')")
  with monitor.connect() as c: row=c.execute('SELECT module FROM tags').fetchone()
  self.assertEqual(row[0],'P2 · Historical entity archive')
 def test_new_ui_sections_and_review(self):
  from streamlit.testing.v1 import AppTest
  now=datetime.now(timezone.utc).isoformat()
  row=('test-id','UAE buyer completes acquisition for USD 100 million','https://example.org/a','Publisher',now,'Manufacturing deal',now)
  with patch.object(monitor,'fetch',return_value=[row]): monitor.refresh([monitor.P2,'GIFT City'])
  monitor.save_setting('keywords',['UAE'])
  app=AppTest.from_file(str(Path(__file__).parent/'app.py')).run(timeout=30)
  for section in ['Key news',monitor.P2,'Deal tracker','Keyword alerts','Settings & watchlists','Sources & status']:
   app.sidebar.radio[0].set_value(section).run(timeout=30)
   self.assertEqual(len(app.exception),0,section)
  app.sidebar.radio[0].set_value('Deal tracker').run(timeout=30)
  app.button(key='pin_test-id').click().run(timeout=30)
  self.assertEqual(monitor.read_news().pinned.iloc[0],1)
  next(b for b in app.button if b.label=='Save review').click().run(timeout=30)
  self.assertEqual(len(app.exception),0)
if __name__=='__main__':unittest.main()
