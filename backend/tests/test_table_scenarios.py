import copy
import csv
import io
import json
import time
from pathlib import Path
import pytest
from backend.tabular import inspect_file
from backend.table_mapping import normalize_table
from backend.table_bundle import assemble
from backend.engine import compute,digest
from backend.reports import model,xlsx,pdf
from backend.tests.test_tabular import config
from backend.tests.test_workbench import RATES,WORK,INVOICES

PERIOD={'facility_id':'FAC-A','service_from':'2026-10-01','service_to':'2026-10-10','source_as_of':'2026-10-12T17:00:00+00:00','billing_cutoff':'2026-10-12T12:00:00+00:00','invoice_complete':True,'work_complete':True,'expected_work_hours':None,'expected_invoice_total':None,'synthetic':True}

def result(rates=RATES,work=WORK,invoices=INVOICES,period=None,formats=None):
    sources=[]
    for kind,raw in [('rates',rates),('work',work),('invoices',invoices)]:
        table=inspect_file(raw,kind+'.csv',kind);cfg=config(table);cfg['date_format']='ISO';cfg.update((formats or {}).get(kind,{}))
        sources.append(({'id':'FILE-'+kind,'filename':kind+'.csv','content_hash':digest(raw),'category':kind,'config':cfg},normalize_table(table,kind,cfg,kind+'.csv',digest(raw))))
    combined=assemble(period or PERIOD,sources,{},'IMPORTER','2026-10-01T00:00:00Z')
    assert not combined['errors'],combined['errors']
    inputs=combined['normalized'];approved=compute('approve_imported_rates',rules=combined['rate_candidates'],existing=[],excerpt_ids=[e['id'] for e in combined['excerpts']],actor='APPROVER',timestamp='2026-10-23T10:00:00Z')
    inputs['rules'].extend(approved);inputs['excerpts']=combined['excerpts']
    compute('validate',text=json.dumps(inputs))
    draft=json.loads(Path('handoff/data/synthetic/draft_rule.json').read_text())
    state=compute('seed',inputs=inputs,draft=draft)
    return state,combined

def test_alternate_layout_and_hospital_composite_matching():
    base=Path('public/examples/spreadsheets')
    state,combined=result((base/'rates.csv').read_bytes(),(base/'layout-b-work.csv').read_bytes(),(base/'layout-c-statement.csv').read_bytes())
    assert state['run']['totals']['underbilling']=='200.00'
    assert state['run']['coverage']['evaluated_records']==6 and len(state['run']['tasks'])==2
    assert all(len(i['shift_ids'])==1 for i in state['inputs']['invoices'])
    ambiguous=(base/'layout-b-work.csv').read_bytes().replace(b'W001',b'DUP-W001')
    original=(base/'layout-b-work.csv').read_bytes()
    extra=ambiguous.splitlines()[1]
    state,_=result((base/'rates.csv').read_bytes(),original+b'\n'+extra+b'\n',(base/'layout-c-statement.csv').read_bytes())
    assert state['run']['totals']['underbilling']=='0.00' and state['run']['coverage']['evaluated_records']==0

@pytest.mark.parametrize('component',['OT','Holiday','Weekend','On Call','Callback'])
def test_segmented_hourly_components_require_explicit_rates(component):
    state,_=result(RATES.replace(b'Regular',component.encode()),WORK.replace(b'Regular',component.encode()))
    assert state['run']['records'][0]['expected_amount']=='2600.00'
    assert state['run']['totals']['underbilling']=='200.00'

def test_effective_amendment_partial_credit_void_and_rebill():
    rates=RATES+b'RATE-B,CTR-A,FAC-A,RN,Regular,70,2026-10-05,2026-10-04\n'
    # Explicit predecessor is required for the overlapping amended interval.
    lines=list(csv.reader(io.StringIO(rates.decode())));lines[0].append('Supersedes');lines[1].append('');lines[2].append('RATE-A')
    out=io.StringIO();csv.writer(out).writerows(lines)
    state,_=result(rates=out.getvalue().encode());assert state['run']['records'][0]['expected_amount']=='2800.00'
    state,_=result(invoices=INVOICES.replace(b'2400,40,60',b'1200,20,60'));assert state['run']['totals']['underbilling']=='1400.00'
    header=INVOICES.splitlines()[0]+b',Chain ID\n'
    invoice=header+b'L1,INV-A,FAC-A,W-A,2400,40,60,Posted,Invoice,C1\nL2,INV-C,FAC-A,W-A,-2400,-40,60,Posted,Credit,C1\nL3,INV-R,FAC-A,W-A,2600,40,65,Posted,Rebill,C1\nL4,INV-V,FAC-A,,999,1,999,Void,Invoice,\n'
    state,_=result(invoices=invoice)
    assert state['run']['totals']['invoiced']=='2600.00' and state['run']['totals']['underbilling']=='0.00'
    assert state['run']['records'][0]['category']=='evaluated_aligned'
    state,_=result(invoices=invoice+b'L3,INV-R,FAC-A,W-A,2600,40,65,Posted,Rebill,C1\n')
    assert state['run']['totals']['invoiced']=='2600.00'
    state,_=result(invoices=INVOICES.replace(b'2400,40,60',b'2800,40,70'))
    assert state['run']['totals']['overbilling']=='200.00'

def test_empty_invoice_and_incomplete_coverage_never_claim_false_money():
    period={**PERIOD,'expected_invoice_total':'0'}
    state,_=result(invoices=INVOICES.splitlines()[0]+b'\n',period=period)
    assert state['run']['totals']['underbilling']=='2600.00'
    state,_=result(period={**PERIOD,'invoice_complete':False})
    assert state['run']['totals']['underbilling']=='0.00' and state['run']['records'][0]['expected_amount'] is None

def test_declared_capacity_import_and_report_are_bounded():
    rows=[]
    for index in range(1000):rows.append([f'W{index:04}', 'FAC-A',f'E{index:04}','RN','Regular','2026-10-05','8','Approved','2026-10-06'])
    work=io.StringIO();csv.writer(work).writerows([WORK.decode().splitlines()[0].split(','),*rows])
    invoice=io.StringIO();writer=csv.writer(invoice);writer.writerow(INVOICES.decode().splitlines()[0].split(','))
    for index in range(1000):
        for part in [1,2]:writer.writerow([f'L{index:04}-{part}','INV-A','FAC-A',f'W{index:04}','240','4','60','Posted','Statement'])
    started=time.monotonic();state,combined=result(work=work.getvalue().encode(),invoices=invoice.getvalue().encode())
    assert state['run']['coverage']['evaluated_records']==1000 and state['run']['totals']['underbilling']=='40000.00'
    assert len(json.dumps(state).encode())<4*1024*1024
    data=model(state,combined['lineage']);excel=xlsx(data);document=pdf(data)
    assert document.startswith(b'%PDF-') and len(document)<2*1024*1024 and len(excel)<1024*1024
    elapsed=time.monotonic()-started
    assert elapsed<30
    Path('artifacts/workflow-capacity.json').write_text(json.dumps({'work':1000,'invoices':2000,'state_bytes':len(json.dumps(state).encode()),'xlsx_bytes':len(excel),'pdf_bytes':len(document),'elapsed_seconds':round(elapsed,3)},indent=2))
    target=Path('artifacts/reports');target.mkdir(parents=True,exist_ok=True);(target/'capacity-review.pdf').write_bytes(document)
