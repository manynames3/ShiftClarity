import copy
import json
import secrets
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch
import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg.types.json import Jsonb
from backend.app import create_app
from backend.db import transaction
from backend.storage import PrivateStorage
from backend.maintenance import expire_sources,purge_workspace
from backend.tests.conftest import TEST_ADMIN
from backend.tests.test_workbench import prepare,approve,accept,upload_confirm,WORK
from backend.tests.test_tabular import new_session,config
from backend.tabular import inspect_file,inspect_isolated,TableError

BASE='/api/v1/import-workbench'

def requests_for(client,session):
    s=client.get(BASE+'/sessions/'+session).json();file=s['files'][1];path=BASE+'/sessions/'+session;version=s['version']
    mapping={**file['config'],'expected_version':version}
    period=s['period']
    return [('GET',BASE,None),('GET',BASE+'/samples/work.csv',None),('GET',path,None),('GET',path+'/errors.csv',None),
            ('GET',path+'/files/'+file['id']+'/preview',None),('GET',path+'/files/'+file['id']+'/source',None),
            ('GET','/api/v1/runs/RUN-001/report.xlsx',None),('GET','/api/v1/runs/RUN-001/report.pdf',None),
            ('POST',BASE+'/sessions',period),('POST',path+'/files?category=work&filename=time.csv','file'),
            ('POST',path+'/files/'+file['id']+'/value-options',mapping),('POST',path+'/files/'+file['id']+'/mapping',mapping),
            ('POST',path+'/validate',{'expected_version':version}),('POST',path+'/approve-rates',{'expected_version':version,'reason':'Independent review'}),
            ('POST',path+'/accept',{'expected_version':version,'confirmed':True,'acknowledge_warnings':True}),
            ('POST',BASE+'/profiles',{'name':'Work export','session_id':session,'file_id':file['id']}),
            ('DELETE',path+'/files/'+file['id'],None),('DELETE',BASE+'/profiles/UNKNOWN',None)]

def send(client,method,path,body):
    if body=='file':return client.request(method,path,content=WORK,headers={'Content-Type':'application/octet-stream','X-Data-Classification':'synthetic'})
    return client.request(method,path,json=body) if body is not None else client.request(method,path)

def test_every_new_endpoint_requires_identity_and_writes_require_csrf(environment,clients):
    client=clients();session=prepare(client);cases=requests_for(client,session)
    anonymous=TestClient(create_app(environment),base_url=environment.origin)
    for method,path,body in cases:assert send(anonymous,method,path,body).status_code==401,(method,path)
    client.headers.pop('X-CSRF-Token')
    for method,path,body in cases:
        if method!='GET':assert send(client,method,path,body).status_code==403,(method,path)
    observer=clients('DEMO-OBSERVER')
    for method,path,body in cases:
        if method!='GET':assert send(observer,method,path,body).status_code==403,(method,path)
    assert observer.get(BASE+'/sessions/'+session+'/files/'+client.get(BASE+'/sessions/'+session).json()['files'][1]['id']+'/source').status_code==403
    anonymous.close()

def test_guessed_ids_do_not_cross_workspace_rls(environment,clients):
    client=clients();session=prepare(client);cases=requests_for(client,session)
    other_login=clients('OTHER-REVIEWER')
    with transaction(environment,'other-workspace') as db:db.execute("UPDATE memberships SET roles=array['importer','approver','reviewer'] WHERE actor='OTHER-REVIEWER'")
    with TestClient(create_app(replace(environment,org_id='other-workspace')),base_url=environment.origin) as other:
        other.cookies.update(other_login.cookies);other.headers.update(other_login.headers)
        assert other.get(BASE).json()['sessions']==[]
        for method,path,body in cases:
            if '/sessions/'+session in path:assert send(other,method,path,body).status_code==404,(method,path)
        assert other.delete(BASE+'/profiles/UNKNOWN').status_code==404
    # Independent approver can inspect only rate originals, and cannot change a creator's files.
    colleague=clients('DEMO-APPROVER');s=client.get(BASE+'/sessions/'+session).json()
    assert colleague.get(BASE+'/sessions/'+session+'/files/'+s['files'][0]['id']+'/source').status_code==200
    assert colleague.get(BASE+'/sessions/'+session+'/files/'+s['files'][1]['id']+'/source').status_code==403
    with transaction(environment,environment.org_id) as db:db.execute("UPDATE memberships SET roles=array['importer','approver'] WHERE actor='DEMO-APPROVER'")
    assert colleague.delete(BASE+'/sessions/'+session+'/files/'+s['files'][1]['id']).status_code==403


def test_accepted_snapshots_and_profiles_cannot_be_rewritten(environment,clients):
    client=clients();session=prepare(client);s=client.get(BASE+'/sessions/'+session).json();fid=s['files'][1]['id']
    client.headers['Idempotency-Key']=secrets.token_hex(16)
    profile=client.post(BASE+'/profiles',json={'name':'Verified work layout','session_id':session,'file_id':fid})
    assert profile.status_code==200,profile.text
    assert client.post(BASE+'/profiles',json={'name':'Verified work layout','session_id':session,'file_id':fid}).json()['id']==profile.json()['id']
    approve(clients('DEMO-APPROVER'),session);assert accept(client,session).status_code==200
    for statement,args in [
        ("UPDATE table_sessions SET data='{}' WHERE id=%s",(session,)),('DELETE FROM table_sessions WHERE id=%s',(session,)),
        ("UPDATE table_files SET filename='replacement.csv' WHERE id=%s",(fid,)),("UPDATE table_files SET object_key='other' WHERE id=%s",(fid,)),
        ('DELETE FROM table_files WHERE id=%s',(fid,)),("UPDATE mapping_profiles SET config='{}' WHERE id=%s",(profile.json()['id'],))]:
        with pytest.raises(psycopg.Error):
            with transaction(environment,environment.org_id) as db:db.execute(statement,args)
    assert client.delete(BASE+'/sessions/'+session+'/files/'+fid).status_code==409
    current=client.get(BASE+'/sessions/'+session).json()
    assert client.post(BASE+'/sessions/'+session+'/files/'+fid+'/mapping',json={**s['files'][1]['config'],'expected_version':current['version']}).status_code==409


def test_interrupted_raw_copy_keeps_previous_run_and_retries_without_duplicates(environment,clients):
    client=clients();session=prepare(client);approve(clients('DEMO-APPROVER'),session)
    before=client.get('/api/v1/workspace').json()['state']['run'];original=PrivateStorage.put;copies=[]
    def failing(storage,key,data,content_type='application/json'):
        if '/accepted/' in key and content_type=='text/csv':
            copies.append(key)
            if len(copies)==2:raise OSError('Simulated storage interruption')
        return original(storage,key,data,content_type)
    with patch.object(PrivateStorage,'put',failing):assert accept(client,session).status_code==503
    assert all(not (Path(environment.storage_dir)/key).exists() for key in copies)
    assert client.get(BASE+'/sessions/'+session).json()['status']=='approved'
    with transaction(environment,environment.org_id) as db:
        staged=db.execute("SELECT id FROM imports WHERE request_key LIKE 'table-%%'").fetchone()['id']
    client.headers['Idempotency-Key']=secrets.token_hex(16)
    assert client.post('/api/v1/runs',json={'import_id':staged}).status_code==409
    assert client.get('/api/v1/workspace').json()['state']['run']==before
    first=accept(client,session);assert first.status_code==200,first.text
    assert accept(client,session).json()['id']==first.json()['id']
    with transaction(environment,environment.org_id) as db:
        assert db.execute("SELECT count(*) AS n FROM imports WHERE request_key LIKE 'table-%%'").fetchone()['n']==1
        assert db.execute("SELECT count(*) AS n FROM table_files WHERE status='accepted'").fetchone()['n']==3


def test_concurrent_acceptance_and_expiry(environment,clients):
    client=clients();session=prepare(client);approve(clients('DEMO-APPROVER'),session)
    path=BASE+'/sessions/'+session;body={'expected_version':client.get(path).json()['version'],'confirmed':True,'acknowledge_warnings':True}
    peers=[clients(),clients()]
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lambda c:c.post(path+'/accept',json=body),peers))
    assert [r.status_code for r in results]==[200,200]
    assert len({r.json()['id'] for r in results})==1
    fid=client.get(path).json()['files'][1]['id']
    with psycopg.connect(TEST_ADMIN) as db:db.execute("UPDATE table_files SET expires_at=now()-interval '1 second' WHERE id=%s",(fid,))
    assert client.get(path+'/files/'+fid+'/source').status_code==404
    assert expire_sources(environment,TEST_ADMIN)>=1
    with transaction(environment,environment.org_id) as db:
        row=db.execute('SELECT object_key,status FROM table_files WHERE id=%s',(fid,)).fetchone()
        assert row['status']=='deleted' and not (Path(environment.storage_dir)/row['object_key']).exists()
    purge_workspace(environment,TEST_ADMIN,environment.org_id)
    with psycopg.connect(TEST_ADMIN) as db:
        for table in ['table_files','table_sessions','mapping_profiles']:assert db.execute('SELECT count(*) FROM '+table+' WHERE org_id=%s',(environment.org_id,)).fetchone()[0]==0
    assert client.get('/api/v1/workspace').status_code==401


def test_stale_versions_and_parser_failure_preserve_prior_sources(environment,clients):
    client=clients();session=new_session(client);path=BASE+'/sessions/'+session
    before=client.get('/api/v1/workspace').json()['state']['run']
    from subprocess import TimeoutExpired
    with patch('backend.tabular.subprocess.run',side_effect=TimeoutExpired('python',10)):
        response=client.post(path+'/files?category=work&filename=time.csv',content=WORK,headers={'Content-Type':'application/octet-stream','X-Data-Classification':'synthetic'})
    assert response.status_code==422 and 'PRIVATE' not in response.text
    assert client.get(path).json()['files']==[]
    fid=upload_confirm(client,session,'work',WORK);current=client.get(path).json()
    assert client.post(path+'/files/'+fid+'/mapping',json={**current['files'][0]['config'],'expected_version':1}).status_code==409
    assert client.get('/api/v1/workspace').json()['state']['run']==before
    # An accepted approval is invalidated if any confirmed source mapping changes.
    session=prepare(client);approve(clients('DEMO-APPROVER'),session);path=BASE+'/sessions/'+session;s=client.get(path).json()
    assert client.post(path+'/files/'+s['files'][1]['id']+'/mapping',json={**s['files'][1]['config'],'expected_version':s['version']}).status_code==200
    changed=client.get(path).json();assert changed['status']=='draft' and 'approval' not in changed and 'summary' not in changed
    assert accept(client,session).status_code==409


def test_concurrent_rate_approval_serializes_across_import_sessions(environment,clients):
    from backend.tests.test_workbench import RATES,INVOICES
    importer=clients();first=prepare(importer)
    importer.headers['Idempotency-Key']=secrets.token_hex(16);second=new_session(importer)
    for kind,raw in [('rates',RATES.replace(b'RATE-A',b'RATE-B')),('work',WORK),('invoices',INVOICES)]:upload_confirm(importer,second,kind,raw)
    path=BASE+'/sessions/'+second
    assert importer.post(path+'/validate',json={'expected_version':importer.get(path).json()['version']}).json()['valid']
    approvals=[(clients('DEMO-APPROVER'),first),(clients('DEMO-AUTHOR'),second)]
    bodies=[(client,BASE+'/sessions/'+sid+'/approve-rates',{'expected_version':importer.get(BASE+'/sessions/'+sid).json()['version'],'reason':'Independently inspected the proposed source terms'}) for client,sid in approvals]
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lambda args:args[0].post(args[1],json=args[2]),bodies))
    assert sorted(r.status_code for r in results)==[200,409]
    assert 'validate the source selection again' in next(r for r in results if r.status_code==409).text
    with transaction(environment,environment.org_id) as db:assert db.execute("SELECT count(*) AS n FROM rule_versions WHERE content->>'facility_id'='FAC-A'").fetchone()['n']==1


def test_revision_conflict_is_actionable_and_does_not_poison_prior_run(environment,clients):
    from backend.engine import digest
    importer=clients();session=prepare(importer);approve(clients('DEMO-APPROVER'),session)
    before=importer.get('/api/v1/workspace').json()['state']
    with transaction(environment,environment.org_id) as db:
        row=db.execute('SELECT data FROM table_sessions WHERE id=%s',(session,)).fetchone()['data']['normalized']['work'][0]
        identity={k:v for k,v in row.items() if k!='batch_id'};identity['worked_minutes']+=60
        db.execute("INSERT INTO source_revisions VALUES(%s,'work',%s,%s,%s,%s)",(environment.org_id,row['id'],row['source_revision'],digest(identity),Jsonb(identity)))
    rejected=accept(importer,session)
    assert rejected.status_code==422 and 'source revision' in rejected.text.lower(),rejected.text
    assert importer.get('/api/v1/workspace').json()['state']==before
    path=BASE+'/sessions/'+session
    validation=importer.post(path+'/validate',json={'expected_version':importer.get(path).json()['version']})
    assert validation.status_code==200 and not validation.json()['valid']
    assert validation.json()['errors'][0]['code']=='CONFLICTING_SOURCE_REVISION' and validation.json()['errors'][0]['row']==2
    assert importer.get('/api/v1/workspace').json()['state']==before


def test_previews_are_role_gated_and_not_retained_in_accepted_files(environment,clients):
    importer=clients();session=prepare(importer);path=BASE+'/sessions/'+session
    observer=clients('DEMO-OBSERVER').get(path).json()
    assert all('preview' not in f['table'] and 'normalized_preview' not in f for f in observer['files'])
    approver=clients('DEMO-APPROVER');limited=approver.get(path).json()
    assert limited['files'][0]['table']['preview']
    assert all('preview' not in f['table'] for f in limited['files'][1:])
    approve(approver,session);assert accept(importer,session).status_code==200
    with transaction(environment,environment.org_id) as db:
        accepted=db.execute('SELECT data FROM table_sessions WHERE id=%s',(session,)).fetchone()['data']
        assert all('preview' not in f['table'] and 'normalized_preview' not in f for f in accepted['files'])


def test_failed_parse_attempts_are_counted_and_limited(environment,clients):
    client=clients();session=new_session(client);path=BASE+'/sessions/'+session
    failed=client.post(path+'/files?category=work&filename=bad.xlsx',content=b'not a workbook',headers={'Content-Type':'application/octet-stream','X-Data-Classification':'synthetic'})
    assert failed.status_code==422
    with transaction(environment,environment.org_id) as db:
        assert db.execute("SELECT count(*) AS n FROM audit_events WHERE action='table_parse_requested'").fetchone()['n']==1
        db.execute("INSERT INTO audit_events(org_id,actor,action,resource) SELECT %s,'DEMO-REVIEWER','table_parse_requested','test-budget' FROM generate_series(1,119)",(environment.org_id,))
    blocked=client.post(path+'/files?category=work&filename=time.csv',content=WORK,headers={'Content-Type':'application/octet-stream','X-Data-Classification':'synthetic'})
    assert blocked.status_code==429 and client.get(path).json()['files']==[]


def test_retention_failure_keeps_a_retryable_tombstone(environment,clients):
    client=clients();session=prepare(client);approve(clients('DEMO-APPROVER'),session);assert accept(client,session).status_code==200
    path=BASE+'/sessions/'+session;fid=client.get(path).json()['files'][1]['id']
    with psycopg.connect(TEST_ADMIN) as db:db.execute("UPDATE table_files SET expires_at=now()-interval '1 second' WHERE id=%s",(fid,))
    with patch.object(PrivateStorage,'delete',side_effect=OSError('Synthetic storage outage')):
        with pytest.raises(OSError):expire_sources(environment,TEST_ADMIN)
    assert client.get(path+'/files/'+fid+'/source').status_code==404
    with transaction(environment,environment.org_id) as db:
        row=db.execute('SELECT status,object_key FROM table_files WHERE id=%s',(fid,)).fetchone()
        assert row['status']=='deleted' and (Path(environment.storage_dir)/row['object_key']).exists()
    assert expire_sources(environment,TEST_ADMIN)>=1
    assert not (Path(environment.storage_dir)/row['object_key']).exists()
