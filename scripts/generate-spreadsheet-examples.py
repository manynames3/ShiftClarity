"""Reproducible fictional layouts, not tested vendor exports or integrations."""
import csv
import io
import json
import sys
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED,ZipInfo
from openpyxl import Workbook

ROOT=Path(__file__).resolve().parent.parent
target=ROOT/'public/examples/spreadsheets'
target.mkdir(parents=True,exist_ok=True)
tables={
 'rates':([
  'Rate ID','Contract ID','Facility','Role','Rate Type','Bill Rate','Effective From','Authorized On','Currency'],[
  ['RATE-REG','CTR-A','FAC-A','RN','Regular','65','2026-10-01','2026-09-28','USD'],
  ['RATE-OT','CTR-A','FAC-A','RN','OT','97.50','2026-10-01','2026-09-28','USD'],
  ['RATE-WEEKEND','CTR-A','FAC-A','LPN','Weekend','85','2026-10-01','2026-09-28','USD']]),
 'work':(['Shift ID','Facility','Worker ID','Discipline','Pay Type','Shift Date','Approved Hours','Approval Status','Approved Date'],[
  *[[f'W00{i}','FAC-A','E101','RN','Regular',f'2026-10-0{i+1}','10','Approved',f'2026-10-0{i+2}'] for i in range(1,5)],
  ['W005','FAC-A','E102','RN','OT','2026-10-06','2','Approved','2026-10-07'],
  ['W006','FAC-A','E103','LPN','Weekend','2026-10-04','6','Approved','2026-10-05'],
  ['W007','FAC-A','E104','RN','Callback','2026-10-07','3','Approved','2026-10-08'],
  ['W008','FAC-A','E105','RN','Regular','2026-10-08','8','Pending','']]),
 'invoices':(['Line ID','Invoice #','Facility','Shift ID','Amount','Billed Hours','Bill Rate','Status','Document Type'],[
  *[[f'L00{i}','INV-A','FAC-A',f'W00{i}','600','10','60','Posted','Statement'] for i in range(1,5)],
  ['L005','INV-A','FAC-A','W005','195','2','97.5','Posted','Statement'],
  ['L006','INV-A','FAC-A','W006','510','6','85','Posted','Statement'],
  ['L007','INV-A','FAC-A','W007','150','3','50','Posted','Statement'],
  ['L008','INV-A','FAC-A','W008','520','8','65','Posted','Statement']])}

def csv_data(headers,rows):
 stream=io.StringIO(newline='');writer=csv.writer(stream);writer.writerow(headers);writer.writerows(rows);return stream.getvalue().encode()

for category,(headers,rows) in tables.items():
 (target/(category+'.csv')).write_bytes(csv_data(headers,rows))
 book=Workbook();sheet=book.active;sheet.title={'rates':'Contract rates','work':'Time export','invoices':'Hospital statement'}[category]
 sheet.append(['FICTIONAL EVALUATION FILE - no real customer records']);sheet.append(headers)
 for row in rows:sheet.append(row)
 sheet.freeze_panes='A3';sheet.auto_filter.ref=f'A2:{sheet.cell(2,len(headers)).column_letter}{len(rows)+2}'
 for col in sheet.columns:sheet.column_dimensions[col[0].column_letter].width=23
 book.save(target/(category+'.xlsx'))
with ZipFile(target/'templates.zip','w',compression=ZIP_DEFLATED) as archive:
 for category,(headers,_) in tables.items():
  entry=ZipInfo(category+'-blank.csv',date_time=(2026,10,22,0,0,0));entry.compress_type=ZIP_DEFLATED
  archive.writestr(entry,csv_data(headers,[]))
# Alternate headers and a hospital-style composite matcher are deliberately generic.
(target/'layout-b-work.csv').write_bytes(csv_data(['Work ID','Client ID','Resource ID','Role','Bill Type','Service Date','Worked Hours','Approved','Time Approved Date'],tables['work'][1]))
invoice_rows=[]
by_work={row[0]:row for row in tables['work'][1]}
for row in tables['invoices'][1]:
 work=by_work[row[3]]
 invoice_rows.append([row[0],row[1],row[2],work[2],work[5],work[3],work[4],*row[4:]])
(target/'layout-c-statement.csv').write_bytes(csv_data(['Billing Line ID','Statement ID','Client ID','Resource ID','Service Date','Discipline','Bill Type','Net Amount','Bill Hours','Unit Rate','Posting Status','Document Type'],invoice_rows))
(target/'expected-results.json').write_text(json.dumps({'synthetic':True,'facility':'FAC-A','period':['2026-10-01','2026-10-10'],'work_records':8,'evaluated_records':6,'underbilling':'200.00','overbilling':'0.00','coverage_gaps':2,'posted_invoice_total':'3775.00','evaluated_invoice_total':'3105.00','notes':'One unsupported callback and one pending approval. No recovered funds or vendor compatibility claim.'},indent=2)+'\n')
print('Generated fictional CSV/XLSX layouts and blank templates in public/examples/spreadsheets.')
# A second scope reuses the same approved rates and headers, with a new export code.
next_work=[]
for source in tables['work'][1]:
 row=list(source)
 for index in [5,8]:
  if row[index]:row[index]=row[index][:8]+f'{int(row[index][8:])+10:02}'
 if row[4]=='Regular':row[4]='RG'
 next_work.append(row)
next_invoices=[[value.replace('INV-A','INV-B') for value in row] for row in tables['invoices'][1]]
(target/'period-2-work.csv').write_bytes(csv_data(tables['work'][0],next_work))
(target/'period-2-invoices.csv').write_bytes(csv_data(tables['invoices'][0],next_invoices))
