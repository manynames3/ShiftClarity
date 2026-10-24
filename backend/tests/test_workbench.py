import copy
import io
import csv
import secrets
import pytest
from psycopg.types.json import Jsonb
from backend.engine import compute
from backend.db import transaction
from backend.jobs import work_once
from backend.tabular import inspect_file
from backend.tests.test_tabular import config,new_session,csv_bytes

RATES=b'Rate ID,Contract ID,Facility,Role,Rate Type,Bill Rate,Effective From,Authorized On\nRATE-A,CTR-A,FAC-A,RN,Regular,65,2026-10-01,2026-09-30\n'
WORK=b'Shift ID,Facility,Worker ID,Role,Pay Type,Shift Date,Hours,Approval Status,Approved Date\nW-A,FAC-A,E101,RN,Regular,2026-10-05,40,Approved,2026-10-06\n'
INVOICES=b'Line ID,Invoice Number,Facility,Shift ID,Amount,Hours,Bill Rate,Status,Document Type\nL-A,INV-A,FAC-A,W-A,2400,40,60,Posted,Statement\n'

def upload_confirm(client,session,category,data,name=None):
    path='/api/v1/import-workbench/sessions/'+session
    name=name or category+'.csv'
    result=client.post(path+'/files',params={'category':category,'filename':name},content=data,headers={'Content-Type':'application/octet-stream','X-Data-Classification':'synthetic'})
    assert result.status_code==200,result.text
    file_id=result.json()['id'];state=client.get(path).json()
    table=inspect_file(data,name,category);body=config(table);body['date_format']='ISO'
    result=client.post(path+'/files/'+file_id+'/mapping',json={**body,'expected_version':state['version']})
    assert result.status_code==200 and not result.json()['errors'],result.text
    return file_id

def prepare(client):
    client.headers['Idempotency-Key']=secrets.token_hex(16)
    session=new_session(client)
    for kind,data in [('rates',RATES),('work',WORK),('invoices',INVOICES)]:upload_confirm(client,session,kind,data)
    path='/api/v1/import-workbench/sessions/'+session
    result=client.post(path+'/validate',json={'expected_version':client.get(path).json()['version']})
    assert result.status_code==200 and result.json()['valid'],result.text
    return session

def approve(client,session):
    path='/api/v1/import-workbench/sessions/'+session
    response=client.post(path+'/approve-rates',json={'expected_version':client.get(path).json()['version'],'reason':'Inspected the fictional source rates and historical authorization dates.'})
    assert response.status_code==200,response.text

def test_interrupted_approval_is_retryable_without_revalidation(environment,clients,monkeypatch):
    from backend.engine import EngineError
    client=clients();approver=clients('DEMO-APPROVER');session=prepare(client)
    path='/api/v1/import-workbench/sessions/'+session
    before=client.get('/api/v1/workspace').json()
    version=client.get(path).json()['version']
    def interrupted(*args,**kwargs):raise EngineError('PARSER_LIMIT_OR_UNAVAILABLE')
    with monkeypatch.context() as patch:
        patch.setattr('backend.workbench.compute',interrupted)
        response=approver.post(path+'/approve-rates',json={'expected_version':version,'reason':'Inspected the fictional rates and source.'})
    assert response.status_code==503,response.text
    assert 'retry' in response.json()['detail'].lower()
    unchanged=client.get(path).json()
    assert unchanged['status']=='validated' and unchanged['version']==version and not unchanged.get('approval')
    assert client.get('/api/v1/workspace').json()==before
    approve(approver,session)
    assert client.get(path).json()['status']=='approved'

def accept(client,session):
    path='/api/v1/import-workbench/sessions/'+session
    return client.post(path+'/accept',json={'expected_version':client.get(path).json()['version'],'confirmed':True,'acknowledge_warnings':True})

def test_full_file_import_approval_run_replay_and_review(environment,clients):
    client=clients();approver=clients('DEMO-APPROVER');session=prepare(client)
    assert accept(client,session).status_code==409
    path='/api/v1/import-workbench/sessions/'+session
    # Give the creator both roles: the stored actor still cannot approve their own terms.
    with transaction(environment,environment.org_id) as db:
        db.execute("UPDATE memberships SET roles=array['importer','reviewer','approver'] WHERE actor='DEMO-REVIEWER'")
    assert client.post(path+'/approve-rates',json={'expected_version':client.get(path).json()['version'],'reason':'Self approval is forbidden'}).status_code==403
    approve(approver,session)
    imported=accept(client,session)
    assert imported.status_code==200 and imported.json()['status']=='validated',imported.text
    assert accept(client,session).json()['id']==imported.json()['id']
    client.headers['Idempotency-Key']=secrets.token_hex(16)
    queued=client.post('/api/v1/runs',json={'import_id':imported.json()['id']})
    assert queued.status_code==200,queued.text
    assert work_once(environment)
    state=client.get('/api/v1/workspace').json()['state']
    assert state['run']['totals']['underbilling']=='200.00'
    assert state['run']['coverage']['evaluated_records']==1
    rate=state['inputs']['rules'][0]
    assert rate['authorization_date']=='2026-09-30'
    assert rate['approved_at'][:10]>rate['authorization_date']
    assert rate['approver_id']=='DEMO-APPROVER' and rate['author_id']=='DEMO-REVIEWER'
    with transaction(environment,environment.org_id) as db:
        assert db.execute('SELECT count(*) AS n FROM source_lineage WHERE import_id=%s',(imported.json()['id'],)).fetchone()['n']==2
    again=prepare(client)
    assert client.get('/api/v1/import-workbench/sessions/'+again).json()['status']=='approved'
    assert accept(client,again).json()['id']==imported.json()['id']

def test_failed_rows_keep_prior_result_and_block_publication(clients):
    client=clients();before=client.get('/api/v1/workspace').json()['state']['run']
    session=new_session(client)
    path='/api/v1/import-workbench/sessions/'+session
    for kind,data in [('rates',RATES),('work',WORK),('invoices',INVOICES)]:upload_confirm(client,session,kind,data)
    with_bad=WORK.replace(b'2026-10-05',b'2026-11-05')
    upload_confirm(client,session,'work',with_bad,'outside.csv')
    response=client.post(path+'/validate',json={'expected_version':client.get(path).json()['version']})
    assert response.status_code==200 and not response.json()['valid']
    assert accept(client,session).status_code==409
    assert client.get('/api/v1/workspace').json()['state']['run']==before
    assert b'SOURCE_SELECTION' in client.get(path+'/errors.csv').content

def test_profiles_do_not_grant_approval_and_unknown_matching_stays_a_gap(environment,clients):
    client=clients();session=new_session(client);path='/api/v1/import-workbench/sessions/'+session
    ambiguous=INVOICES.replace(b'Shift ID',b'Unknown Reference')
    for kind,data in [('rates',RATES),('work',WORK),('invoices',INVOICES.replace(b'W-A',b'NOT-IN-WORK'))]:upload_confirm(client,session,kind,data)
    response=client.post(path+'/validate',json={'expected_version':client.get(path).json()['version']})
    assert response.json()['warnings']
    approve(clients('DEMO-APPROVER'),session)
    imported=accept(client,session).json()
    client.headers['Idempotency-Key']=secrets.token_hex(16)
    assert client.post('/api/v1/runs',json={'import_id':imported['id']}).status_code==200
    assert work_once(environment)
    run=client.get('/api/v1/workspace').json()['state']['run']
    assert run['totals']['underbilling']=='0.00'
    assert run['records'][0]['category']=='abstained'
    assert run['records'][0]['expected_amount'] is None


def test_repeat_period_can_reuse_registered_rates_without_reupload(environment,clients):
    client=clients();approver=clients('DEMO-APPROVER');first=prepare(client);approve(approver,first);assert accept(client,first).status_code==200
    from backend.tests.test_table_scenarios import PERIOD
    response=client.post('/api/v1/import-workbench/sessions',json={**PERIOD,'use_registered_rates':True},headers={'Idempotency-Key':secrets.token_hex(16)})
    assert response.status_code==200,response.text
    session=response.json()['id'];path='/api/v1/import-workbench/sessions/'+session
    for kind,data in [('work',WORK),('invoices',INVOICES)]:upload_confirm(client,session,kind,data)
    response=client.post(path+'/validate',json={'expected_version':client.get(path).json()['version']})
    assert response.status_code==200 and response.json()['valid'],response.text
    saved=client.get(path).json();assert saved['status']=='approved' and not saved['rate_review']
    assert saved['summary']['rate_versions']==1
    assert accept(client,session).status_code==200
