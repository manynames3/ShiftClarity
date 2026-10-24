import copy
import secrets
import uuid
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor
import psycopg
import pytest
from psycopg.types.json import Jsonb
from backend.db import transaction,head,save_head,store_review
from backend.engine import compute
from backend.workflow import sync_cases
from backend.tests.test_security import decision


def publish(environment,mutate=lambda inputs:None):
    with transaction(environment,environment.org_id) as db:
        state=head(db,True)['state'];store_review(db,environment.org_id,state);inputs=copy.deepcopy(state['inputs']);mutate(inputs)
        inputs['manifest']['run_id']='RUN-'+uuid.uuid4().hex
        state=compute('publish',state=state,inputs=inputs)
        assert not state['stale']
        source=db.execute('SELECT id FROM imports LIMIT 1').fetchone()['id']
        db.execute('INSERT INTO completed_runs(org_id,id,import_id,snapshot) VALUES(%s,%s,%s,%s)',(environment.org_id,state['run']['id'],source,Jsonb(state)))
        save_head(db,environment.org_id,state);sync_cases(db,environment.org_id,state)
        return state


def post(client,path,body):
    return client.post(path,json=body,headers={'Idempotency-Key':secrets.token_hex(16)})


def test_history_period_decisions_and_reports_survive_new_run(environment,clients):
    one,two=clients(),clients();old=one.get('/api/v1/workspace').json()['state'];old_id=old['run']['id']
    newer=publish(environment);new_id=newer['run']['id']
    # Two reviewers operate on different runs; neither changes the other's state.
    with ThreadPoolExecutor(2) as pool:
        replies=list(pool.map(lambda args:post(args[0],'/api/v1/findings/FND-001/decisions',decision(args[1])),[(one,old),(two,newer)]))
    assert [r.status_code for r in replies]==[200,200]
    assert one.get('/api/v1/workspace').json()['state']['run']['id']==new_id
    prior=one.get('/api/v1/workspace',params={'run_id':old_id}).json()['state']
    assert next(iter(prior['reviews'].values()))['state']=='confirmed'
    assert post(one,'/api/v1/findings/FND-001/decisions',decision(old)).status_code==409
    for extension in ['pdf','xlsx']:
        response=one.get(f'/api/v1/runs/{old_id}/report.{extension}');assert response.status_code==200,response.text
    first=one.get('/api/v1/reviews?limit=1').json();assert len(first['reviews'])==1 and first['next']
    second=one.get('/api/v1/reviews',params={'limit':1,'before':first['next']}).json()
    assert {first['reviews'][0]['run_id'],second['reviews'][0]['run_id']}=={old_id,new_id}
    assert one.get('/api/v1/reviews?before=garbage').status_code==422
    assert one.get('/api/v1/workspace?run_id=OTHER').status_code==404
    with transaction(environment,'other-workspace') as db:
        assert not db.execute('SELECT * FROM review_workspaces WHERE run_id=%s',(old_id,)).fetchall()
        assert not db.execute('SELECT * FROM billing_cases').fetchall()
    with transaction(environment,environment.org_id) as db:
        with pytest.raises(psycopg.Error):db.execute("UPDATE review_workspaces SET state=jsonb_set(state,'{run,id}','\"FORGED\"')")


def test_case_assignment_correction_resolution_and_reopening(environment,clients):
    client=clients();case=next(c for c in client.get('/api/v1/cases?scope=team').json()['cases'] if c['source_ref']=='FND-001')
    path='/api/v1/cases/'+case['id']+'/actions'
    body={'action':'assign','expected_version':case['version'],'owner':'DEMO-APPROVER','reason':'Check the corrected statement'}
    response=post(client,path,body);assert response.status_code==200,response.text
    assigned=response.json()['case'];assert assigned['owner']=='DEMO-APPROVER'
    assert post(client,path,body).status_code==409
    assert client.get('/api/v1/cases?scope=mine').json()['cases']==[]
    approver=clients('DEMO-APPROVER')
    assert approver.get('/api/v1/cases').json()['cases'][0]['id']==case['id']
    response=post(approver,path,{'action':'record_evidence','expected_version':assigned['version'],'reference':'RATE-REVIEW-101','reason':'Supplied the independently checked rate evidence'})
    assert response.status_code==200,response.text
    assigned=response.json()['case']
    assert post(clients('DEMO-OBSERVER'),path,{**body,'expected_version':assigned['version']}).status_code==403
    response=post(client,path,{'action':'record_correction','expected_version':assigned['version'],'reference':'INV-CORRECTED-101','reason':'Corrected in the fictional billing system'})
    assert response.status_code==200,response.text
    def corrected(inputs):
        for line in inputs['invoices']:
            if any(i in ['S001','S002','S003','S004'] for i in line['shift_ids']):line.update(amount='650.00',unit_rate='65.0000')
        inputs['batches'][1]['signed_control_total']=str(sum(Decimal(l['amount']) for l in inputs['invoices']))
    verified=publish(environment,corrected)
    detail=client.get('/api/v1/cases/'+case['id']).json();assert detail['case']['status']=='resolved'
    assert detail['case']['verified_run_id']==verified['run']['id']
    assert detail['case']['correction_reference']=='INV-CORRECTED-101'
    assert [e['action'] for e in detail['events']][-1]=='aligned_on_rerun'
    def discrepancy(inputs):
        inputs['invoices'][0].update(amount='600.00',unit_rate='60.0000');inputs['batches'][1]['signed_control_total']=str(sum(Decimal(l['amount']) for l in inputs['invoices']))
    publish(environment,discrepancy)
    assert client.get('/api/v1/cases/'+case['id']).json()['case']['status']=='open'
    with transaction(environment,environment.org_id) as db:
        with pytest.raises(psycopg.Error):db.execute("UPDATE case_events SET actor='FORGED'")


@pytest.mark.parametrize('gap',['omitted','pending','incomplete','partial'])
def test_missing_records_never_close_cases(environment,clients,gap):
    client=clients();case=next(c for c in client.get('/api/v1/cases?scope=team').json()['cases'] if c['source_ref']=='FND-002')
    def omitted(inputs):
        if gap=='omitted':
            inputs['work']=[w for w in inputs['work'] if w['id'] not in ['S005','S006']]
            inputs['batches'][0].update(records=len(inputs['work']),control_total_minutes=sum(w['worked_minutes'] for w in inputs['work']))
        elif gap=='pending':
            for w in inputs['work']:
                if w['id'] in ['S005','S006']:w.update(approval_state='pending',approved_at=None)
        elif gap=='incomplete':
            inputs['manifest']['invoice_coverage_complete']=False;inputs['batches'][1].update(declared_complete=False,state='incomplete')
        else:
            inputs['invoices'].append({'id':'PARTIAL-005','invoice_id':'INV-PARTIAL','facility_id':'FAC-002','state':'posted','document_kind':'invoice','amount':'780.00','currency':'USD','minutes':720,'unit_rate':'65.0000','shift_ids':['S005'],'chain_id':None,'batch_id':inputs['batches'][1]['id']})
            inputs['batches'][1].update(records=len(inputs['invoices']),signed_control_total=str(sum(Decimal(l['amount']) for l in inputs['invoices'])))
    publish(environment,omitted)
    assert client.get('/api/v1/cases/'+case['id']).json()['case']['status']=='open'


def test_legacy_backfill_preserves_original_snapshots_and_recovers_decisions(environment,clients):
    import json
    from backend.tests.conftest import TEST_ADMIN
    from backend.workflow import backfill_workflows,finding_key
    from backend.fingerprints import compact_state
    client=clients();state=client.get('/api/v1/workspace').json()['state'];state['run']['id']='RUN-LEGACY'
    finding=state['run']['findings'][0];finding['fingerprint']='ev1:{"legacy":"source evidence"}'
    original=copy.deepcopy(state)
    state['reviews'][finding_key(finding)]={'state':'confirmed','fingerprint':finding['fingerprint'],'version':2,'history':[{'sequence':1,'action':'confirm','reason':'Legacy evidence checked','actor':'DEMO-REVIEWER','owner':'DEMO-APPROVER','timestamp':'2026-10-20T12:00:00Z','fingerprint':finding['fingerprint']}]}
    with psycopg.connect(TEST_ADMIN) as db:
        source=db.execute('SELECT id FROM imports LIMIT 1').fetchone()[0]
        db.execute("INSERT INTO completed_runs(org_id,id,import_id,snapshot,published_at) VALUES(%s,'RUN-LEGACY',%s,%s,'2026-10-20T12:00:00Z')",(environment.org_id,source,Jsonb(original)))
        db.execute('UPDATE workspace_heads SET state=%s WHERE org_id=%s',(Jsonb(state),environment.org_id))
        backfill_workflows(db)
        saved=db.execute("SELECT snapshot FROM completed_runs WHERE id='RUN-LEGACY'").fetchone()[0]
        assert saved==original
        review,created=db.execute("SELECT state,created_at FROM review_workspaces WHERE run_id='RUN-LEGACY'").fetchone()
        assert created.isoformat().startswith('2026-10-20')
        assert review['reviews'][finding_key(finding)]==compact_state(state)['reviews'][finding_key(finding)]
        assert review['run']['findings'][0]['fingerprint'].startswith('sha256:')


def test_rule_approval_uses_current_register_while_period_stays_selected(environment,clients):
    client=clients();approver=clients('DEMO-APPROVER');old=client.get('/api/v1/workspace').json()['state'];publish(environment)
    assert post(client,'/api/v1/findings/FND-001/decisions',decision(old)).status_code==200
    selected=approver.get('/api/v1/workspace',params={'run_id':old['run']['id']}).json()
    context=selected['approval'];assert context['version']!=selected['version']
    response=post(approver,'/api/v1/rules/'+context['draft']['id']+'/approval',{'action':'approve','reason':'Checked the current source register independently','expected_version':context['version']})
    assert response.status_code==200,response.text
    after=approver.get('/api/v1/workspace',params={'run_id':old['run']['id']}).json()
    assert after['state']['run']==old['run'] and after['approval']['draft']['state']=='approved'
