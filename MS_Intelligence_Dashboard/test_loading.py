import unittest,time,threading,tempfile
from pathlib import Path
from unittest.mock import patch
from datetime import datetime,timezone
import monitor
from collector_job import CollectorJob

class LoadingTests(unittest.TestCase):
 def test_background_slow_source_does_not_block_start_or_duplicate_jobs(self):
  started=threading.Event();release=threading.Event()
  def slow(*args,**kwargs):
   started.set();release.wait(5);return []
  with patch('collector_job.refresh',side_effect=slow):
   job=CollectorJob();before=time.monotonic()
   self.assertTrue(job.start(['GIFT City'],1))
   self.assertLess(time.monotonic()-before,1)
   self.assertTrue(started.wait(1))
   self.assertTrue(job.snapshot()['running'])
   self.assertFalse(job.start(['GIFT City'],1))
   job.stop();release.set()
   deadline=time.monotonic()+3
   while job.snapshot()['running'] and time.monotonic()<deadline: time.sleep(.01)
   self.assertFalse(job.snapshot()['running'])
   self.assertIn('Stopped',job.snapshot()['message'])
 def test_background_exception_clears_loading(self):
  with patch('collector_job.refresh',side_effect=RuntimeError('offline')):
   job=CollectorJob();job.start([],1)
   deadline=time.monotonic()+3
   while job.snapshot()['running'] and time.monotonic()<deadline:time.sleep(.01)
   self.assertFalse(job.snapshot()['running']);self.assertIn('offline',job.snapshot()['error'])
 def test_no_publisher_checks_or_fuzzy_matching_on_refresh_and_read(self):
  with tempfile.TemporaryDirectory() as folder,patch.object(monitor,'DB',Path(folder)/'news.sqlite3'):
   now=datetime.now(timezone.utc).isoformat()
   rows=[(str(i),f'Company {i} acquires business','https://example.org/'+str(i),'Publisher',now,'',now) for i in range(300)]
   with patch.object(monitor,'fetch',return_value=rows),patch.object(monitor,'inspect_publication',side_effect=AssertionError('network check')),patch.object(monitor,'same_story',side_effect=AssertionError('fuzzy match')),patch.object(monitor,'consolidate_news',side_effect=AssertionError('archive comparison')):
    monitor.refresh(['India · M&A deals'],providers=['Google News RSS'])
    self.assertEqual(monitor.read_news().id.nunique(),300)
 def test_ui_refresh_remains_usable_with_blocked_source(self):
  from streamlit.testing.v1 import AppTest
  released=threading.Event()
  def slow(*a,**k):released.wait(10);return []
  with tempfile.TemporaryDirectory() as folder,patch.object(monitor,'DB',Path(folder)/'news.sqlite3'),patch('collector_job.refresh',side_effect=slow):
   app=AppTest.from_file(str(Path(__file__).parent/'app.py')).run(timeout=10)
   try:
    next(b for b in app.sidebar.button if b.label=='Refresh all modules').click().run(timeout=5)
    self.assertFalse(app.exception)
    app.sidebar.radio[0].set_value('GIFT City').run(timeout=5)
    self.assertFalse(app.exception)
    next(b for b in app.sidebar.button if b.label=='Stop refresh').click().run(timeout=5)
   finally:released.set()
if __name__=='__main__':unittest.main()
