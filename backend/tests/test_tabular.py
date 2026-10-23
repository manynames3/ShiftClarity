import io
import json
import secrets
from zipfile import ZipFile,ZIP_DEFLATED
import pytest
from openpyxl import Workbook
from backend.tabular import inspect_file,inspect_isolated,TableError,value_suggestions
from backend.table_mapping import normalize_table,decimal_value,error_csv,day

HEADERS=['Shift ID','Facility','Employee ID','Role','Pay Type','Shift Date','Approved Hours','Approval Status','Approved Date']
ROWS=[['S-A','FAC-A','E101','RN','Regular','10/05/2026','8','Yes','10/06/2026']]

def csv_bytes(headers=HEADERS,rows=None):
    import csv
    stream=io.StringIO();writer=csv.writer(stream);writer.writerow(headers);writer.writerows(ROWS if rows is None else rows)
    return stream.getvalue().encode()

def workbook(rows,formula=False,hidden=False):
    book=Workbook();sheet=book.active;sheet.title='Time export'
    for row in rows:sheet.append(row)
    if formula:sheet['G2']='=2+2'
    if hidden:book.create_sheet('Private').sheet_state='hidden'
    stream=io.BytesIO();book.save(stream);return stream.getvalue()

def config(table):
    return {'mapping':table['mapping'],'value_maps':table['value_maps'],'confirmed':True,'date_format':'MDY','decimal_format':'dot','time_unit':'hours','end_date_mode':'exclusive','worksheet':table['worksheet'],'header_row':table['header_row']}

def test_csv_and_xlsx_header_suggestions_and_exact_mapping():
    for data,name in [(csv_bytes(),'time.csv'),(workbook([['Fictional time export'],HEADERS,*ROWS]),'time.xlsx')]:
        table=inspect_file(data,name,'work')
        assert table['header_row']==(2 if name.endswith('xlsx') else 1)
        assert table['mapping']['worker_id']=='Employee ID'
        result=normalize_table(table,'work',config(table),name,'testhash')
        assert result['errors']==[]
        assert result['records'][0]['worked_minutes']==480
        assert result['records'][0]['approval_state']=='approved'
        assert result['records'][0]['service_date']=='2026-10-05'
        assert result['lineage'][0]['row']==table['header_row']+1

@pytest.mark.parametrize('data,name,code',[
    (b'PK fake','bad.xlsx','XLSX_FORMAT'),
    (b'x'*1048577,'big.csv','FILE_LIMIT'),
    (workbook([HEADERS,*ROWS],formula=True),'formula.xlsx','ACTIVE_CONTENT'),
    (workbook([HEADERS,*ROWS],hidden=True),'hidden.xlsx','HIDDEN_SHEET'),
    (csv_bytes(['Shift ID','Patient ID'],[['S-A','P1']]),'patient.csv','SENSITIVE_FIELDS'),
    (csv_bytes(['Shift ID','Shift ID'],[['a','b']]),'duplicate.csv','HEADER_FIELDS'),
])
def test_unsafe_inputs_rejected(data,name,code):
    with pytest.raises(TableError) as error:inspect_file(data,name,'work')
    assert error.value.code==code

def test_zip_bomb_and_external_relationship_rejected():
    for name,content,code in [('xl/worksheets/sheet1.xml',b'a'*100000,'ARCHIVE_LIMIT'),('xl/_rels/workbook.xml.rels',b'<Relationships><Relationship TargetMode="External" Target="https://example.invalid"/></Relationships>','ACTIVE_CONTENT')]:
        stream=io.BytesIO()
        with ZipFile(stream,'w',compression=ZIP_DEFLATED) as archive:archive.writestr(name,content)
        with pytest.raises(TableError) as error:inspect_file(stream.getvalue(),'attack.xlsx','work')
        assert error.value.code==code

def test_duplicate_native_ids_and_errors_are_not_dropped():
    table=inspect_file(csv_bytes(rows=[ROWS[0],ROWS[0],['S-A','FAC-A','E101','RN','Regular','10/05/2026','9','Yes','10/06/2026']]),'time.csv','work')
    result=normalize_table(table,'work',config(table),'time.csv','sha')
    assert result['duplicates']==1 and len(result['records'])==1
    assert len(result['errors'])==1 and result['errors'][0]['row']==4
    cfg=config(table);cfg['confirmed']=False
    with pytest.raises(TableError):normalize_table(table,'work',cfg,'time.csv','sha')

def test_value_aliases_never_establish_facts_and_safe_errors():
    table=inspect_file(csv_bytes(),'time.csv','work');cfg=config(table);cfg['value_maps']['component']['Regular']=''
    assert normalize_table(table,'work',cfg,'time.csv','sha')['errors']
    text=error_csv([{'filename':'=HYPERLINK("x")','row':2,'field':'hours','message':'Fix the number'}])
    assert "'=HYPERLINK" in text
    assert decimal_value('1.234,56','comma',2)==decimal_value('1,234.56','dot',2)
    assert day('05/10/2026','DMY')=='2026-10-05'
    with pytest.raises(ValueError):decimal_value('12.345','dot',2)
    with pytest.raises(ValueError):decimal_value('NaN','dot',2)

def new_session(client):
    response=client.post('/api/v1/import-workbench/sessions',json={'facility_id':'FAC-A','service_from':'2026-10-01','service_to':'2026-10-10','source_as_of':'2026-10-12T17:00:00+00:00','billing_cutoff':'2026-10-12T12:00:00+00:00','invoice_complete':True,'work_complete':True,'synthetic':True})
    assert response.status_code==200,response.text
    return response.json()['id']

def test_workspace_files_mapping_profiles_and_isolation(clients,environment):
    client=clients();session=new_session(client)
    path='/api/v1/import-workbench/sessions/'+session
    headers={'Content-Type':'application/octet-stream','X-Data-Classification':'synthetic'}
    uploaded=client.post(path+'/files?category=work&filename=time.csv',content=csv_bytes(),headers=headers)
    assert uploaded.status_code==200,uploaded.text
    file_id=uploaded.json()['id']
    assert client.post(path+'/files?category=work&filename=time.csv',content=csv_bytes(),headers=headers).json()['reused']
    state=client.get(path).json();table=state['files'][0]['table']
    body={'expected_version':state['version'],**config(table)}
    result=client.post(path+'/files/'+file_id+'/mapping',json=body)
    assert result.status_code==200 and not result.json()['errors'],result.text
    client.headers['Idempotency-Key']=secrets.token_hex(16)
    profile=client.post('/api/v1/import-workbench/profiles',json={'name':'Fictional payroll export','session_id':session,'file_id':file_id})
    assert profile.status_code==200,profile.text
    assert client.get('/api/v1/import-workbench').json()['profiles'][0]['id']==profile.json()['id']
    other=clients('OTHER-REVIEWER')
    assert other.get(path).status_code==401  # A session cannot switch the configured workspace.
    from dataclasses import replace
    from fastapi.testclient import TestClient
    from backend.app import create_app
    scoped=TestClient(create_app(replace(environment,org_id='other-workspace')),base_url=environment.origin)
    scoped.cookies.update(other.cookies);scoped.headers.update(other.headers)
    other=scoped
    assert other.get(path).status_code==404
    assert not other.get('/api/v1/import-workbench').json()['profiles']
    assert other.get(path+'/files/'+file_id+'/source').status_code in [403,404]
    observer=clients('DEMO-OBSERVER')
    assert observer.post(path+'/files?category=work&filename=time.csv',content=csv_bytes(),headers=headers).status_code==403
    assert clients('DEMO-AUTHOR').post(path+'/files?category=work&filename=time.csv',content=csv_bytes(),headers=headers).status_code==403

def test_isolated_parser_and_no_data_in_diagnostics():
    table=inspect_isolated(csv_bytes(),'time.csv','work')
    assert table['rows'][0]['values'][0]=='S-A'
    with pytest.raises(TableError):inspect_isolated(b'not a workbook','private.xlsx','work')


def test_semicolon_decimal_comma_fixed_values_and_minute_convention():
    headers=['Work ID','Client ID','Employee ID','Role','Bill Type','Service Date','Minutes','Approved','Time Approved Date']
    stream=io.StringIO();__import__('csv').writer(stream,delimiter=';').writerows([headers,['S1','FAC-A','E1','RN','Regular','05/10/2026','440','Yes','06/10/2026']])
    table=inspect_file(stream.getvalue().encode(),'semi.csv','work');cfg=config(table);cfg.update(date_format='DMY',time_unit='minutes',decimal_format='comma')
    result=normalize_table(table,'work',cfg,'semi.csv','sha');assert not result['errors']
    assert result['records'][0]['worked_minutes']==440 and result['records'][0]['service_date']=='2026-10-05'
    rounded=inspect_file(csv_bytes(rows=[['S-A','FAC-A','E101','RN','Regular','10/05/2026','7.33','Yes','10/06/2026']]),'rounded.csv','work')
    assert 'original minutes column' in normalize_table(rounded,'work',config(rounded),'rounded.csv','sha')['errors'][0]['message']
    from backend.tests.test_workbench import RATES
    rates=inspect_file(RATES,'rates.csv','rates');cfg=config(rates);cfg['date_format']='ISO';del cfg['mapping']['authorization_date'];cfg['constants']={'authorization_date':'2026-09-30'}
    assert not normalize_table(rates,'rates',cfg,'rates.csv','sha')['errors']


def test_parser_receives_no_service_credentials_in_environment():
    from unittest.mock import patch
    import subprocess
    run=subprocess.run
    def inspect(*args,**kwargs):
        assert set(kwargs['env'])=={'PATH','LANG','PYTHONNOUSERSITE','PYTHONDONTWRITEBYTECODE'}
        return run(*args,**kwargs)
    with patch('backend.tabular.subprocess.run',side_effect=inspect):assert inspect_isolated(csv_bytes(),'time.csv','work')['rows']


def test_optional_value_errors_identify_the_correct_source_field():
    for raw,field in [(csv_bytes(rows=[['S-A','FAC-A','E1','RN','Regular','10/05/2026','8','Yes','bad-date']]),'approved_at'),(csv_bytes(headers=[*HEADERS,'Revision'],rows=[[*ROWS[0],'v'*81]]),'source_revision')]:
        table=inspect_file(raw,'time.csv','work');errors=normalize_table(table,'work',config(table),'time.csv','sha')['errors']
        assert len(errors)==1 and errors[0]['field']==field and errors[0]['row']==2


def test_unknown_profile_value_fields_are_rejected():
    table=inspect_file(csv_bytes(),'time.csv','work');cfg=config(table);cfg['value_maps']['unrecognized_source_metadata']={'x':'y'}
    with pytest.raises(TableError) as error:normalize_table(table,'work',cfg,'time.csv','sha')
    assert error.value.code=='VALUE_MAPPING_FIELDS'
