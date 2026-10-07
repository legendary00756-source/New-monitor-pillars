"""Process-wide background collector. Worker never calls Streamlit APIs."""
import threading
import time
from monitor import refresh

class CollectorJob:
 def __init__(self):
  self.lock=threading.Lock()
  self.cancel=threading.Event()
  self.state=dict(running=False,progress=0.0,message='',error='',revision=0)
 def snapshot(self):
  with self.lock: return self.state.copy()
 def start(self,modules,days):
  with self.lock:
   if self.state['running']: return False
   self.cancel.clear()
   self.state.update(running=True,progress=0.0,message='Starting news collection…',error='')
  threading.Thread(target=self._run,args=(list(modules),days),daemon=True).start()
  return True
 def stop(self):
  self.cancel.set()
  with self.lock:
   if self.state['running']: self.state['message']='Stopping; waiting for active source requests to finish…'
 def _run(self,modules,days):
  started=time.monotonic()
  def progress(value,label):
   with self.lock:
    self.state.update(progress=value,message=f'{value:.0%} · {label} · {time.monotonic()-started:.0f}s elapsed')
    self.state['revision']+=1
  try:
   result=refresh(modules,days,progress=progress,stop_event=self.cancel)
   message=('Stopped' if self.cancel.is_set() else 'Finished')+f': {len(result)} searches; {sum(r[2]=="ERROR" for r in result)} failed. See Sources & status.'
   with self.lock: self.state['message']=message
  except Exception as exc:
   with self.lock: self.state.update(error=f'{type(exc).__name__}: {exc}',message='Refresh failed. Saved news is retained.')
  finally:
   with self.lock:
    self.state['running']=False
    self.state['revision']+=1
