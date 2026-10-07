"""Offline checks: parsing, persistence, multi-module deduplication and Streamlit UI."""
import tempfile, unittest
from pathlib import Path
from datetime import datetime,timezone,timedelta
from email.utils import format_datetime
from unittest.mock import patch
import monitor

class DashboardTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(); self.old=monitor.DB
  monitor.DB=Path(self.temp.name)/'test.sqlite3'
  monitor.save_setting('providers',['Google News RSS'])
  self.publication_patch=patch.object(monitor,'inspect_publication',side_effect=lambda row,provider: {'original_published':row[4],'canonical':row[2],'date_status':'Publisher publication','detail':'TEST FIXTURE','feed_date':row[4]})
  self.publication_patch.start()
  self.addCleanup(self.publication_patch.stop)
 def tearDown(self):
  monitor.DB=self.old; self.temp.cleanup()
 def feed(self):
  now=format_datetime(datetime.now(timezone.utc))
  old=format_datetime(datetime.now(timezone.utc)-timedelta(days=100))
  return f'<rss><channel><item><title>India UAE investment</title><link>https://example.org/a</link><source>Publisher</source><pubDate>{now}</pubDate><description>News excerpt</description></item><item><title>Old</title><link>https://example.org/b</link><pubDate>{old}</pubDate></item><item><title>Undated</title><link>https://example.org/c</link></item></channel></rss>'.encode()
 def test_dates_and_invalid_feed(self):
  self.assertEqual(len(monitor.parse_feed(self.feed(),7)),1)
  with self.assertRaises(ValueError): monitor.parse_feed(b'<html/>',7)
 def test_dedup_tags_and_failure_preserves_archive(self):
  with patch.object(monitor,'fetch',return_value=monitor.parse_feed(self.feed(),7)):
   monitor.refresh(['India · Private equity','India · M&A deals'])
   monitor.refresh(['India · Private equity'])
  df=monitor.read_news(); self.assertEqual(df.module.nunique(),2); self.assertEqual(df.id.nunique(),1)
  monitor.bookmark(df.id.iloc[0],True); self.assertTrue(monitor.read_news().bookmarked.eq(1).all())
  with patch.object(monitor,'fetch',side_effect=TimeoutError('test timeout')):
   monitor.refresh(['India · Private equity'])
  self.assertEqual(len(monitor.read_news()),len(df))
  self.assertIn('ERROR',monitor.health().status.tolist())
 def test_ui_empty_populated_sections_exports(self):
  from streamlit.testing.v1 import AppTest
  app=AppTest.from_file(str(Path(__file__).parent/'app.py')).run(timeout=20)
  self.assertEqual(len(app.exception),0)
  with patch.object(monitor,'fetch',return_value=monitor.parse_feed(self.feed(),7)):
   monitor.refresh(list(monitor.MODULES))
  app.run(timeout=20); self.assertEqual(len(app.exception),0)
  for section in ['UAE corridors','P1 · Wealth intelligence','GIFT City','Sources & status','Saved articles']:
   app.sidebar.radio[0].set_value(section).run(timeout=20)
   self.assertEqual(len(app.exception),0,section)
  app.sidebar.radio[0].set_value('GIFT City').run(timeout=20)
  next(b for b in app.button if b.label=='Prepare PDF digest').click().run(timeout=20)
  self.assertEqual(len(app.exception),0)
if __name__=='__main__': unittest.main()
