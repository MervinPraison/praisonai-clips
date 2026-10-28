"""Find scripting-enabled editor instances without touching an open document."""
import json
import os
from pathlib import Path
import re
import subprocess

root=Path(__file__).resolve().parents[1]
result=subprocess.run(['dbus-send','--session','--dest=org.freedesktop.DBus','--print-reply',
 '/org/freedesktop/DBus','org.freedesktop.DBus.ListNames'],capture_output=True,text=True,check=True)
services=re.findall(r'string "(org\.kde\.kdenlive[^\"]*)"',result.stdout)
valid=[]
for service in services:
 r=subprocess.run(['gdbus','introspect','--session','--dest',service,'--object-path','/MainWindow'],
                  capture_output=True,text=True,timeout=10)
 if r.returncode==0 and 'scriptMoveClip(' in r.stdout and 'scriptGetPosition(' in r.stdout:
  valid.append(service)
  out=root/'data/kdenlive-live-test'
  out.mkdir(parents=True,exist_ok=True)
  (out/(service+'.introspection.txt')).write_text(r.stdout)
explicit=os.getenv('KDENLIVE_DBUS_SERVICE')
selected=explicit if explicit in valid else valid[0] if len(valid)==1 else None
out=root/'data/kdenlive-live-test';out.mkdir(parents=True,exist_ok=True)
if selected:(out/'service.txt').write_text(selected+'\n')
print(json.dumps({'stock_or_other_services':services,'live_scripting_services':valid,'selected':selected},indent=2))
raise SystemExit(0 if selected else 1)
