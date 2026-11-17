"""Terminate only a captured subprocess subtree, including detached episode groups."""
import os,signal,subprocess,time
from pathlib import Path
def identity(pid):
 try:
  fields=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()
  return fields[19],fields[0]
 except (FileNotFoundError,ProcessLookupError):return None

def terminate_tree(proc,grace_seconds=5):
 if proc.poll() is not None:return
 rows=subprocess.check_output(['ps','-eo','pid=,ppid='],text=True)
 children={}
 for line in rows.splitlines():
  pid,parent=map(int,line.split());children.setdefault(parent,[]).append(pid)
 selected=[proc.pid]
 for pid in selected:selected.extend(children.get(pid,[]))
 captured={pid:identity(pid) for pid in selected}
 def living(pid):
  current=identity(pid);original=captured[pid]
  return current is not None and original is not None and current[0]==original[0] and current[1]!='Z'
 for pid in reversed(selected):
  if living(pid):
   try:os.kill(pid,signal.SIGTERM)
   except ProcessLookupError:pass
 deadline=time.monotonic()+grace_seconds
 while time.monotonic()<deadline and any(living(pid) for pid in selected):time.sleep(.05)
 for pid in reversed(selected):
  if living(pid):
   try:os.kill(pid,signal.SIGKILL)
   except ProcessLookupError:pass
 proc.wait(timeout=5)
