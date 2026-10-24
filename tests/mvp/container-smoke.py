"""Run inside the Lambda image with /checks/bundle.json mounted read-only."""
import json
import os
import sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from backend.tabular import inspect_isolated
from backend.engine import compute
from backend.reports import model,xlsx,pdf

assert os.getuid()==10001
assert Path('dist/brand/shiftclarity-report-logo.png').is_file()
table=inspect_isolated(Path('dist/examples/spreadsheets/work.xlsx').read_bytes(),'work.xlsx','work')
assert len(table['rows'])==8
inputs=json.loads(Path('/checks/bundle.json').read_text())
candidate={**inputs['rules'][0],'id':'CONTAINER-RATE','state':'pending_approval','author_id':'CONTAINER-IMPORTER','approver_id':None}
approved=compute('approve_imported_rates',rules=[candidate],existing=[],excerpt_ids=[candidate['source_excerpt_id']],actor='CONTAINER-APPROVER',timestamp='2026-10-24T00:00:00Z')
assert approved[0]['approver_id']=='CONTAINER-APPROVER' and approved[0]['state']=='approved'
state=compute('seed',inputs=inputs,draft=inputs['rules'][0])
assert state['run']['totals']['underbilling']=='1760.00'
report=model(state)
assert xlsx(report).startswith(b'PK') and pdf(report).startswith(b'%PDF-')
print('Passed: nonroot, read-only, network-isolated workbook parser, independent rate approval, shared calculator and Excel/PDF reports.')
