from __future__ import annotations

import json
import os
import secrets
import subprocess
import time
from pathlib import Path

owner = 'cleanpaste-fixture-' + secrets.token_hex(12)
volume = owner + '-data'
environment = {**os.environ, 'CLEAN_PASTE_TOKEN': secrets.token_hex(32)}

def docker(*args):
    return subprocess.check_output(['docker', *args], text=True, encoding='utf-8', env=environment, timeout=120).strip()

probe = r'''
import hashlib,json,os,urllib.request,urllib.error,zipfile,io,sys
base='http://127.0.0.1:8765'
def request(route, body=None, authorized=True):
 headers={'Authorization':'Bearer '+os.environ['CLEAN_PASTE_TOKEN']} if authorized else {}
 if body is not None: headers['Content-Type']='application/json'
 with urllib.request.urlopen(urllib.request.Request(base+route,data=json.dumps(body).encode() if body is not None else None,headers=headers),timeout=30) as response:
  return response.read(),{key.lower():value for key,value in response.headers.items()}
health=json.loads(request('/health')[0]);assert health['database']['version']=='3.54.1';assert health['runtime']['python']=='3.15.1'
if os.environ['FIXTURE_STAGE']=='create':
 try:
  request('/api/projects',authorized=False)
  raise AssertionError('Unauthenticated project access succeeded')
 except urllib.error.HTTPError as error: assert error.code==401
 page,headers=request('/');assert b'<title>AI Clean Paste' in page;assert headers['x-content-type-options']=='nosniff'
 project=json.loads(request('/api/projects',{'title':'Synthetic conversion fixture','source':'# Synthetic conversion\n\nNo personal data or provider calls.','source_format':'markdown'})[0])
 result=json.loads(request('/api/projects/'+project['id']+'/generate',{'formats':['docx','pdf','markdown','text'],'template_id':'standard_business_brief'})[0])
 assert {a['format'] for a in result['artifacts']}=={'docx','pdf','markdown','text'}
 for artifact in result['artifacts']:
  content,_=request('/api/projects/'+project['id']+'/versions/1/artifacts/'+artifact['name'])
  assert hashlib.sha256(content).hexdigest()==artifact['sha256']
  if artifact['format']=='pdf':assert content.startswith(b'%PDF-')
  if artifact['format']=='docx':assert 'word/document.xml' in zipfile.ZipFile(io.BytesIO(content)).namelist()
 print(json.dumps({'projectId':project['id'],'sqlite':health['database']['version'],'python':sys.version.split()[0],'artifactFormats':['docx','pdf','markdown','text'],'artifactHashesVerified':True,'unauthorizedDenied':True,'productIdentity':True}))
else:
 projects=json.loads(request('/api/projects')[0]);assert any(p['id']==os.environ['FIXTURE_PROJECT'] for p in projects)
 print(json.dumps({'persistedAfterRestart':True}))
'''

compile(probe, '<container-probe>', 'exec')
report = {'syntheticOnly': True, 'providerRequests': 0, 'network': 'none'}
container = None
volume_created = False

def healthy():
    for _ in range(60):
        try:
            docker('exec', owner, 'python', '-c', "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8765/health',timeout=2)")
            return
        except subprocess.CalledProcessError:
            time.sleep(0.5)
    raise RuntimeError('Owned synthetic container did not become healthy')

try:
    docker('volume', 'create', '--label', 'cleanpaste.fixture='+owner, volume)
    volume_created = True
    container = docker('run', '--detach', '--name', owner, '--label', 'cleanpaste.fixture='+owner, '--network', 'none', '--read-only', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges:true', '--tmpfs', '/tmp:rw,size=192m', '--mount', 'type=volume,source='+volume+',target=/data', '--env', 'CLEAN_PASTE_TOKEN', 'cleanpaste:ci')
    healthy()
    report.update(json.loads(docker('exec', '--env', 'FIXTURE_STAGE=create', owner, 'python', '-c', probe)))
    docker('restart', '--time', '10', container)
    healthy()
    report.update(json.loads(docker('exec', '--env', 'FIXTURE_STAGE=restart', '--env', 'FIXTURE_PROJECT='+report['projectId'], owner, 'python', '-c', probe)))
    report['outcome'] = 'passed'
finally:
    if container:
        state = json.loads(docker('inspect', container))[0]
        assert state['Id']==container and state['Config']['Labels']['cleanpaste.fixture']==owner
        assert state['Config']['User']=='studio'
        assert all((m['Type']=='volume' and m['Name']==volume) or m['Type']=='tmpfs' for m in state['Mounts'])
        docker('rm', '--force', container)
    if volume_created:
        state = json.loads(docker('volume', 'inspect', volume))[0]
        assert state['Name']==volume and state['Labels']['cleanpaste.fixture']==owner
        docker('volume', 'rm', volume)
    report['ownedFixturesRemoved'] = True
    Path('artifacts').mkdir(exist_ok=True)
    Path('artifacts/container-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report))
