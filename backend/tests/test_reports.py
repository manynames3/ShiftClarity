import io
from decimal import Decimal
from pathlib import Path
from openpyxl import load_workbook
from backend.reports import model,xlsx,pdf,key
from backend.db import transaction
from psycopg.types.json import Jsonb

def test_report_totals_current_decisions_and_all_states(environment,clients):
    client=clients();state=client.get('/api/v1/workspace').json()['state'];run=state['run'];f=run['findings'][0]
    state['reviews'][key(f)]={'state':'confirmed','fingerprint':f['fingerprint'],'history':[{'sequence':1,'action':'confirm','actor':'DEMO-REVIEWER','timestamp':'2026-10-23T10:00:00Z','reason':'Private fictional note'}]}
    with transaction(environment,environment.org_id) as db:db.execute('UPDATE workspace_heads SET state=%s',(Jsonb(state),))
    response=client.get('/api/v1/runs/'+run['id']+'/report.xlsx');assert response.status_code==200,response.text
    assert response.headers['cache-control']=='no-store'
    wb=load_workbook(io.BytesIO(response.content),data_only=False)
    rows=list(wb['Findings'].values);assert len(rows)==3
    assert {row[2] for row in rows[1:]}=={'Confirmed discrepancy','Needs review'}
    overview=dict(list(wb['Overview'].values)[1:]);assert overview['Reviewer-confirmed underbilling difference (USD)']==Decimal(f['discrepancy_amount'])
    assert overview['Records evaluated']==12
    assert overview['Net invoiced on evaluated work (USD)']==sum(Decimal(r['invoiced_amount']) for r in run['records'] if r['category'].startswith('evaluated_'))
    assert 'Private fictional note' not in str(list(wb['Review history'].values))
    assert 'Private fictional note' in str(list(load_workbook(io.BytesIO(client.get('/api/v1/runs/'+run['id']+'/report.xlsx?include_notes=true').content))['Review history'].values))
    assert wb['Findings'].freeze_panes=='A2' and wb['Findings'].tables
    assert 'worker_id' not in str([list(ws.values) for ws in wb])
    assert client.get('/api/v1/runs/OTHER/report.xlsx').status_code==409
    assert client.get('/api/v1/runs/'+run['id']+'/report.zip').status_code==404

def test_exports_literal_spreadsheet_text_and_escaped_pdf_markup(clients):
    state=clients().get('/api/v1/workspace').json()['state'];f=state['run']['findings'][0]
    attack='=HYPERLINK("https://example.invalid", "click")'
    state['reviews'][key(f)]={'state':'evidence_requested','fingerprint':f['fingerprint'],'history':[{'sequence':1,'action':'request_evidence','actor':'TEST','timestamp':'2026-10-23','reason':attack+' <img src="file:///etc/passwd"/> & <b>text</b>'}]}
    data=model(state,[{'filename':attack,'record_id':'W1','worksheet':'<img src="file:///bad"/>','row':3,'kind':'work','content_hash':'f'*64}],True)
    wb=load_workbook(io.BytesIO(xlsx(data)),data_only=False)
    cell=wb['Source lineage']['C2'];assert cell.data_type=='s' and cell.value==attack and cell.hyperlink is None
    assert wb['Review history']['G2'].data_type=='s'
    assert all(cell.data_type!='f' for ws in wb for row in ws for cell in row)
    content=pdf(data);assert content.startswith(b'%PDF-')

def test_branded_pdf_and_stale_review_warnings(environment,clients):
    client=clients();state=client.get('/api/v1/workspace').json()['state'];state['stale']=True
    with transaction(environment,environment.org_id) as db:db.execute('UPDATE workspace_heads SET state=%s',(Jsonb(state),))
    result=client.get('/api/v1/runs/'+state['run']['id']+'/report.pdf')
    assert result.status_code==200 and result.headers['content-type']=='application/pdf',result.text
    assert result.content.startswith(b'%PDF-') and len(result.content)>10000
    target=Path('artifacts/reports');target.mkdir(parents=True,exist_ok=True);(target/'canonical-stale.pdf').write_bytes(result.content)
    # Reopened workbook uses current-head decisions, not the immutable run's old snapshot.
    data=model(state);assert dict(__import__('backend.reports',fromlist=['overview']).overview(data))['Result freshness'].startswith('STALE')


def test_imported_report_keeps_unevaluated_billing_separate(environment,clients):
    from backend.tests.test_workbench import upload_confirm,approve,accept
    from backend.tests.test_tabular import new_session
    from backend.jobs import work_once
    client=clients();session=new_session(client)
    for kind in ['rates','work','invoices']:
        upload_confirm(client,session,kind,Path('public/examples/spreadsheets/'+kind+'.csv').read_bytes())
    path='/api/v1/import-workbench/sessions/'+session
    assert client.post(path+'/validate',json={'expected_version':client.get(path).json()['version']}).json()['valid']
    approve(clients('DEMO-APPROVER'),session)
    imported=accept(client,session).json()
    import secrets
    client.headers['Idempotency-Key']=secrets.token_hex(16)
    assert client.post('/api/v1/runs',json={'import_id':imported['id']}).status_code==200
    assert work_once(environment)
    run=client.get('/api/v1/workspace').json()['state']['run']
    report=client.get('/api/v1/runs/'+run['id']+'/report.xlsx')
    assert report.status_code==200,report.text
    wb=load_workbook(io.BytesIO(report.content))
    summary=dict(list(wb['Overview'].values)[1:])
    assert summary['Expected on evaluated work (USD)']==3305
    assert summary['Net invoiced on evaluated work (USD)']==3105
    assert summary['All posted invoice lines, including unchecked work (USD)']==3775
    assert wb['Source lineage'].max_row==20
    assert len(wb['Source lineage']['F2'].value)==64
    target=Path('artifacts/reports');target.mkdir(parents=True,exist_ok=True)
    (target/'fictional-billing-review.xlsx').write_bytes(report.content)
    result=client.get('/api/v1/runs/'+run['id']+'/report.pdf')
    assert result.status_code==200,result.text
    (target/'fictional-billing-review.pdf').write_bytes(result.content)
