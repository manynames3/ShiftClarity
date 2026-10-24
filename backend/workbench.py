"""Workspace-scoped spreadsheet onboarding. Accepted selections use existing jobs."""
import copy
import json
import re
import uuid
from datetime import date,datetime,timedelta,timezone
from typing import Literal
from fastapi import Request,HTTPException
from fastapi.responses import Response,JSONResponse
from pydantic import Field
from psycopg.types.json import Jsonb
from starlette.concurrency import run_in_threadpool
from . import auth
from .db import transaction,audit,head
from .engine import digest,compute,EngineError
from .tabular import FIELDS,VALUES,MAX_BYTES,TableError,inspect_isolated,value_suggestions
from .table_mapping import normalize_table,error_csv,identifier,decimal_value
from .table_bundle import assemble

def session_row(db,identifier,member,edit=False):
    row=db.execute('SELECT * FROM table_sessions WHERE id=%s'+(' FOR UPDATE' if edit else ''),(identifier,)).fetchone()
    if not row:raise HTTPException(404,'Import session not found.')
    if edit:
        if row['creator']!=member['actor']:raise HTTPException(403,'Only the session creator can change its source selection.')
        if row['status']=='accepted':raise HTTPException(409,'This source selection is accepted. Start a new billing period or import session.')
    return row

def update_session(db,row,data,status='draft'):
    db.execute('UPDATE table_sessions SET data=%s,status=%s,version=version+1 WHERE id=%s',(Jsonb(data),status,row['id']))

def file_row(db,session_id,file_id):
    row=db.execute('SELECT * FROM table_files WHERE id=%s AND session_id=%s AND expires_at>now() AND status!=\'deleted\'',(file_id,session_id)).fetchone()
    if not row:raise HTTPException(404,'Source file is unavailable or expired. Upload it again.')
    return row

def summary(table):
    return {**{k:v for k,v in table.items() if k!='rows'},'preview':table['rows'][:10],'row_count':len(table['rows'])}

def limit(db,action,count):
    n=db.execute("SELECT count(*) AS n FROM audit_events WHERE action=%s AND created_at>now()-interval '1 hour'",(action,)).fetchone()['n']
    if n>=count:raise HTTPException(429,'This workspace reached its hourly import limit. Try again later.')

def mount_workbench(app,settings,storage,wake):
    from .app import StrictBody,request_key,write_once

    class Period(StrictBody):
        facility_id:str=Field(pattern=r'^[A-Za-z0-9_-]{1,80}$')
        service_from:str=Field(max_length=10)
        service_to:str=Field(max_length=10)
        source_as_of:str=Field(max_length=40)
        billing_cutoff:str=Field(max_length=40)
        invoice_complete:bool=False
        work_complete:bool=False
        expected_work_hours:str|None=Field(default=None,max_length=20)
        expected_invoice_total:str|None=Field(default=None,max_length=20)
        use_registered_rates:bool=False
        synthetic:Literal[True]

    class Mapping(StrictBody):
        expected_version:int=Field(ge=1)
        worksheet:str=Field(max_length=100)
        header_row:int=Field(ge=1,le=20)
        mapping:dict[str,str]
        constants:dict[str,str]={}
        value_maps:dict[str,dict[str,str]]={}
        date_format:Literal['ISO','MDY','DMY']='ISO'
        decimal_format:Literal['dot','comma']='dot'
        time_unit:Literal['hours','minutes']='hours'
        end_date_mode:Literal['exclusive','inclusive']='exclusive'
        confirmed:Literal[True]
        profile_id:str|None=None
        profile_version:int|None=None

    class Profile(StrictBody):
        name:str=Field(min_length=3,max_length=80)
        session_id:str=Field(max_length=80)
        file_id:str=Field(max_length=80)

    class Version(StrictBody):
        expected_version:int=Field(ge=1)

    class RateApproval(Version):
        reason:str=Field(min_length=3,max_length=2000)

    class Acceptance(Version):
        confirmed:Literal[True]
        acknowledge_warnings:bool=False

    def take_parse_budget(member):
        # Commit attempts before parsing, including failed files; serialize the budget.
        with transaction(settings,member['org_id']) as db:
            head(db,True)
            limit(db,'table_parse_requested',120)
            audit(db,member['org_id'],member['actor'],'table_parse_requested','import-workbench')

    @app.exception_handler(TableError)
    async def table_error(request,error):
        return JSONResponse({'detail':str(error),'code':error.code},422)

    @app.get('/api/v1/import-workbench')
    def list_workbench(request:Request):
        member=auth.principal(settings,request)
        with transaction(settings,member['org_id']) as db:
            return {'fields':{category:[{'key':k,'label':v[0],'required':v[1]} for k,v in fields.items()] for category,fields in FIELDS.items()},
                    'value_choices':{key:list(values) for key,values in VALUES.items()},
                    'profiles':db.execute('SELECT id,name,category,config,headers,version,verified_by FROM mapping_profiles ORDER BY created_at DESC LIMIT 30').fetchall(),
                    'sessions':db.execute('SELECT id,creator,status,version,import_id,data->\'period\' AS period,created_at FROM table_sessions ORDER BY created_at DESC LIMIT 20').fetchall()}

    @app.get('/api/v1/import-workbench/samples/{filename}')
    def sample(filename:str,request:Request):
        auth.principal(settings,request)
        if filename not in ['rates.xlsx','work.xlsx','invoices.xlsx','rates.csv','work.csv','invoices.csv','templates.zip','layout-b-work.csv','layout-c-statement.csv','period-2-work.csv','period-2-invoices.csv']:
            raise HTTPException(404,'Sample not found.')
        from .config import ROOT
        directory=ROOT/'dist/examples/spreadsheets'
        if not directory.exists():directory=ROOT/'public/examples/spreadsheets'
        path=directory/filename
        if not path.exists():raise HTTPException(404,'Sample unavailable. Build the application first.')
        return Response(path.read_bytes(),media_type='application/octet-stream',headers={'Content-Disposition':f'attachment; filename="{filename}"'})

    @app.post('/api/v1/import-workbench/sessions/{session_id}/files/{file_id}/value-options')
    def mapping_values(session_id:str,file_id:str,request:Request,body:Mapping):
        member=auth.principal(settings,request,'importer')
        take_parse_budget(member)
        with transaction(settings,member['org_id']) as db:
            session_row(db,session_id,member,True)
            limit(db,'mapping_options_read',100)
            audit(db,member['org_id'],member['actor'],'mapping_options_read',file_id)
            source=file_row(db,session_id,file_id)
            if any(k not in FIELDS[source['category']] for k in body.mapping):raise HTTPException(422,'Unknown mapped field.')
            table=inspect_isolated(storage.get(source['object_key']),source['filename'],source['category'],body.worksheet,body.header_row)
            if any(value not in table['headers'] for value in body.mapping.values()):raise HTTPException(422,'Choose columns present in the worksheet.')
            return value_suggestions(table['rows'],table['headers'],body.mapping)

    @app.post('/api/v1/import-workbench/sessions')
    def create_session(body:Period,request:Request):
        member=auth.principal(settings,request,'importer')
        try:
            start,end=date.fromisoformat(body.service_from),date.fromisoformat(body.service_to)
            if end<start or (end-start).days>92:raise ValueError()
            for value in [body.source_as_of,body.billing_cutoff]:
                if datetime.fromisoformat(value.replace('Z','+00:00')).tzinfo is None:raise ValueError()
            if body.expected_work_hours is not None:decimal_value(body.expected_work_hours,'dot',4)
            if body.expected_invoice_total is not None:decimal_value(body.expected_invoice_total,'dot',2,True)
        except ValueError:raise HTTPException(422,'Use a billing period of up to 93 days, timestamps with a timezone, and valid optional source totals.') from None
        with transaction(settings,member['org_id']) as db:
            head(db,True)
            def operation():
                limit(db,'table_session_created',20)
                identifier='SES-'+uuid.uuid4().hex
                data={'period':body.model_dump(),'files':[],'errors':[],'lineage':[]}
                db.execute('INSERT INTO table_sessions(id,org_id,creator,data) VALUES(%s,%s,%s,%s)',(identifier,member['org_id'],member['actor'],Jsonb(data)))
                audit(db,member['org_id'],member['actor'],'table_session_created',identifier)
                return {'id':identifier}
            return write_once(db,member,request_key(request),body.model_dump(),operation)

    @app.get('/api/v1/import-workbench/sessions/{session_id}')
    def get_session(session_id:str,request:Request):
        member=auth.principal(settings,request)
        with transaction(settings,member['org_id']) as db:
            row=session_row(db,session_id,member)
            # Only bounded previews, not the entire normalized source, go to the browser.
            data={k:v for k,v in row['data'].items() if k not in ['normalized','rate_candidates','excerpts','lineage']}
            data=copy.deepcopy(data)
            for file in data['files']:
                if 'importer' not in member['roles'] and not (file['category']=='rates' and 'approver' in member['roles']):
                    file['table'].pop('preview',None);file.pop('normalized_preview',None)
            return {**{k:row[k] for k in ['id','creator','status','version','import_id']},**data}

    @app.post('/api/v1/import-workbench/sessions/{session_id}/files')
    async def upload(session_id:str,request:Request,category:Literal['rates','work','invoices'],filename:str):
        member=auth.principal(settings,request,'importer')
        take_parse_budget(member)
        if request.headers.get('x-data-classification')!='synthetic' or request.headers.get('content-type')!='application/octet-stream':
            raise HTTPException(415,'Attest to fictional data and upload the original CSV/XLSX file.')
        if not re.fullmatch(r'[A-Za-z0-9_. ()-]{1,150}\.(csv|xlsx)',filename,re.I):
            raise HTTPException(422,'Use a CSV/XLSX filename with letters, numbers, spaces, periods, parentheses, underscores or hyphens.')
        with transaction(settings,member['org_id']) as db:
            session_row(db,session_id,member,True)
            limit(db,'table_uploaded',30)
        data=bytearray()
        async for chunk in request.stream():
            data.extend(chunk)
            if len(data)>MAX_BYTES:raise HTTPException(413,'Each file must be at most 2 MiB.')
        def receive():
            object_key=member['org_id']+'/quarantine/'+uuid.uuid4().hex
            storage.put(object_key,bytes(data),content_type='text/csv' if filename.lower().endswith('.csv') else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            try:
                table=inspect_isolated(bytes(data),filename,category)
                with transaction(settings,member['org_id']) as db:
                    row=session_row(db,session_id,member,True)
                    old=db.execute('SELECT id FROM table_files WHERE session_id=%s AND category=%s AND content_hash=%s',(session_id,category,digest(bytes(data)))).fetchone()
                    if old:
                        prior=file_row(db,session_id,old['id'])
                        storage.delete(object_key)
                        return {'id':old['id'],'reused':True}
                    if len(row['data']['files'])>=9:raise HTTPException(422,'Use up to nine files per review session.')
                    identifier='FIL-'+uuid.uuid4().hex
                    db.execute('INSERT INTO table_files(id,org_id,session_id,category,filename,content_hash,object_key) VALUES(%s,%s,%s,%s,%s,%s,%s)',(identifier,member['org_id'],session_id,category,filename,digest(bytes(data)),object_key))
                    updated=copy.deepcopy(row['data'])
                    updated['files'].append({'id':identifier,'category':category,'filename':filename,'table':summary(table),'config':None,'errors':[]})
                    for field in ['normalized','rate_candidates','excerpts','rate_review','summary','warnings','approval']:updated.pop(field,None)
                    updated['errors']=[]
                    update_session(db,row,updated)
                    audit(db,member['org_id'],member['actor'],'table_uploaded',identifier,{'category':category,'rows':len(table['rows'])})
                    return {'id':identifier,'reused':False}
            except Exception:
                storage.delete(object_key)
                raise
        return await run_in_threadpool(receive)

    @app.get('/api/v1/import-workbench/sessions/{session_id}/files/{file_id}/preview')
    def preview(session_id:str,file_id:str,request:Request,worksheet:str|None=None,header_row:int|None=None):
        member=auth.principal(settings,request,'importer')
        take_parse_budget(member)
        with transaction(settings,member['org_id']) as db:
            source=file_row(db,session_id,file_id)
            table=inspect_isolated(storage.get(source['object_key']),source['filename'],source['category'],worksheet,header_row)
            return summary(table)

    @app.delete('/api/v1/import-workbench/sessions/{session_id}/files/{file_id}')
    def remove_file(session_id:str,file_id:str,request:Request):
        member=auth.principal(settings,request,'importer')
        with transaction(settings,member['org_id']) as db:
            row=session_row(db,session_id,member,True)
            source=file_row(db,session_id,file_id)
            data=copy.deepcopy(row['data']);data['files']=[f for f in data['files'] if f['id']!=file_id]
            for key in ['normalized','rate_candidates','excerpts','rate_review','summary','warnings','approval']:data.pop(key,None)
            data['errors']=[]
            update_session(db,row,data)
            db.execute('DELETE FROM table_files WHERE id=%s',(file_id,))
            storage.delete(source['object_key'])
            audit(db,member['org_id'],member['actor'],'table_source_removed',file_id)
            return {'deleted':True}

    @app.post('/api/v1/import-workbench/sessions/{session_id}/files/{file_id}/mapping')
    def configure(session_id:str,file_id:str,body:Mapping,request:Request):
        member=auth.principal(settings,request,'importer')
        take_parse_budget(member)
        with transaction(settings,member['org_id']) as db:
            row=session_row(db,session_id,member,True)
            if row['version']!=body.expected_version:raise HTTPException(409,'This import changed. Refresh and confirm the mapping again.')
            limit(db,'mapping_confirmed',100)
            source=file_row(db,session_id,file_id)
            table=inspect_isolated(storage.get(source['object_key']),source['filename'],source['category'],body.worksheet,body.header_row)
            config=body.model_dump(exclude={'expected_version'})
            if body.profile_id:
                profile=db.execute('SELECT * FROM mapping_profiles WHERE id=%s AND version=%s',(body.profile_id,body.profile_version)).fetchone()
                if not profile or profile['category']!=source['category'] or profile['headers']!=table['headers']:
                    raise HTTPException(409,'Saved profile headers/version do not match. Review the new columns without that profile.')
            result=normalize_table(table,source['category'],config,source['filename'],source['content_hash'])
            data=copy.deepcopy(row['data']);file=next(f for f in data['files'] if f['id']==file_id)
            file.update(table=summary(table),config=config,errors=result['errors'],normalized_preview=result['records'][:10],duplicates=result['duplicates'])
            for field in ['normalized','rate_candidates','excerpts','rate_review','summary','warnings','approval']:data.pop(field,None)
            data['errors']=[]
            update_session(db,row,data)
            audit(db,member['org_id'],member['actor'],'mapping_confirmed',file_id,{'errors':len(result['errors'])})
            return {'errors':result['errors'],'records':len(result['records']),'duplicates':result['duplicates']}

    @app.get('/api/v1/import-workbench/sessions/{session_id}/errors.csv')
    def errors(session_id:str,request:Request):
        member=auth.principal(settings,request)
        with transaction(settings,member['org_id']) as db:
            row=session_row(db,session_id,member)
            errors=[*row['data'].get('errors',[]),*(error for f in row['data']['files'] for error in f.get('errors',[]))]
            return Response(error_csv(errors),media_type='text/csv',headers={'Content-Disposition':'attachment; filename="ShiftClarity-import-corrections.csv"'})

    @app.post('/api/v1/import-workbench/sessions/{session_id}/validate')
    def validate_selection(session_id:str,body:Version,request:Request):
        member=auth.principal(settings,request,'importer')
        take_parse_budget(member)
        with transaction(settings,member['org_id']) as db:
            row=session_row(db,session_id,member,True)
            if body.expected_version!=row['version']:raise HTTPException(409,'The source selection changed. Refresh it first.')
            data=copy.deepcopy(row['data'])
            required={'work','invoices'} if data['period'].get('use_registered_rates') else {'rates','work','invoices'}
            if not required.issubset({f['category'] for f in data['files']}) or any(not f.get('config') for f in data['files']):
                raise HTTPException(422,'Upload and confirm mappings for rates, work and invoices first.')
            limit(db,'table_validated',60)
            sources=[]
            for file in data['files']:
                source=file_row(db,session_id,file['id'])
                table=inspect_isolated(storage.get(source['object_key']),source['filename'],source['category'],file['config']['worksheet'],file['config']['header_row'])
                sources.append(({**source,'config':file['config']},normalize_table(table,source['category'],file['config'],source['filename'],source['content_hash'])))
            known={r['content']['id']:r['content'] for r in db.execute('SELECT content FROM rule_versions').fetchall()}
            result=assemble(data['period'],sources,known,row['creator'],row['created_at'].isoformat())
            if not result['errors']:
                from .imports import conflicting_revisions
                for kind,reference in conflicting_revisions(db,result['normalized']):
                    source=next((line for line in result['lineage'] if line['kind']==kind and line['record_id']==reference),{})
                    result['errors'].append({'filename':source.get('filename',kind),'worksheet':source.get('worksheet',''),'row':source.get('row',0),'field':'source_revision','code':'CONFLICTING_SOURCE_REVISION','message':'This work reference and source version already have different accepted content. Supply the corrected source version; previous results are unchanged.'})
            data.update(result)
            if result['errors']:data.pop('normalized',None)
            data['rate_review']=[{**candidate,'source_file':next((line['filename'] for line in data.get('lineage',[]) if line['kind']=='rates' and line['record_id']==candidate['id']),''),
                                 'source_row':next((line['row'] for line in data.get('lineage',[]) if line['kind']=='rates' and line['record_id']==candidate['id']),0)} for candidate in data.get('rate_candidates',[])] if not result['errors'] else []
            update_session(db,row,data,'draft' if result['errors'] else 'validated' if data['rate_candidates'] else 'approved')
            audit(db,member['org_id'],member['actor'],'table_validated',session_id,{'errors':len(result['errors'])})
            return {'valid':not result['errors'],'errors':result['errors'],'summary':result.get('summary'),'warnings':result.get('warnings',[])}

    @app.post('/api/v1/import-workbench/sessions/{session_id}/approve-rates')
    def approve_rates(session_id:str,body:RateApproval,request:Request):
        member=auth.principal(settings,request,'approver')
        created=[]
        try:
            with transaction(settings,member['org_id']) as db:
                row=session_row(db,session_id,member)
                # Lock the session independently of creator-only editing; approvers cannot alter its files.
                row=db.execute('SELECT * FROM table_sessions WHERE id=%s FOR UPDATE',(session_id,)).fetchone()
                if row['creator']==member['actor']:raise HTTPException(403,'A different account must independently approve these rate versions.')
                if body.expected_version!=row['version'] or row['status']!='validated':raise HTTPException(409,'Validate the current source selection before approving its rates.')
                data=copy.deepcopy(row['data'])
                for file in data['files']:file_row(db,session_id,file['id'])
                head(db,True)
                known=[r['content'] for r in db.execute('SELECT content FROM rule_versions').fetchall()]
                approved=compute('approve_imported_rates',rules=data['rate_candidates'],existing=known,excerpt_ids=[e['id'] for e in data['excerpts']],actor=member['actor'],timestamp=datetime.now(timezone.utc).isoformat())
                used={r['source_excerpt_id'] for r in approved}
                for excerpt in data['excerpts']:
                    if excerpt['id'] not in used:continue
                    registered=db.execute('SELECT content FROM documents WHERE id=%s',(excerpt['document_id'],)).fetchone()
                    if registered:
                        if digest(registered['content'])!=digest(excerpt):raise HTTPException(409,'Source evidence conflicts with an immutable registered document.')
                        continue
                    key=member['org_id']+'/accepted/'+uuid.uuid4().hex
                    storage.put(key,json.dumps(excerpt).encode());created.append(key)
                    db.execute('INSERT INTO documents(org_id,id,content,object_key,content_hash) VALUES(%s,%s,%s,%s,%s)',(member['org_id'],excerpt['document_id'],Jsonb(excerpt),key,digest(excerpt)))
                for rate in approved:
                    db.execute('INSERT INTO rule_versions VALUES(%s,%s,%s)',(member['org_id'],rate['id'],Jsonb(rate)))
                data['normalized']['rules'].extend(approved)
                data['approval']={'actor':member['actor'],'at':datetime.now(timezone.utc).isoformat(),'reason':body.reason}
                update_session(db,row,data,'approved')
                audit(db,member['org_id'],member['actor'],'table_rates_approved',session_id,{'count':len(approved),'reason':body.reason})
                return {'approved':len(approved)}
        except EngineError as error:
            for key in created:storage.delete(key)
            if str(error)=='PARSER_LIMIT_OR_UNAVAILABLE':raise
            raise HTTPException(409,'Rate versions changed or conflict. The creator must validate the source selection again; unchanged approved rates will be reused.') from None
        except Exception:
            for key in created:storage.delete(key)
            raise

    @app.post('/api/v1/import-workbench/sessions/{session_id}/accept')
    def accept_selection(session_id:str,body:Acceptance,request:Request):
        member=auth.principal(settings,request,'importer')
        take_parse_budget(member)
        from .imports import receive
        copied=[]
        try:
            with transaction(settings,member['org_id']) as db:
                row=session_row(db,session_id,member)
                row=db.execute('SELECT * FROM table_sessions WHERE id=%s FOR UPDATE',(session_id,)).fetchone()
                if row['creator']!=member['actor']:raise HTTPException(403,'Only the creator can accept this source selection.')
                if row['status']=='accepted':return {'id':row['import_id'],'status':'validated','reused':True}
                if body.expected_version!=row['version'] or row['status']!='approved':raise HTTPException(409,'Validate the current mappings and obtain approval for new rates first.')
                data=copy.deepcopy(row['data'])
                if data.get('warnings') and not body.acknowledge_warnings:raise HTTPException(422,'Acknowledge the visible coverage and duplicate warnings before accepting.')
                sources=[file_row(db,session_id,f['id']) for f in data['files']]
                normalized=data['normalized']
                needed={r['source_excerpt_id'] for r in normalized['rules']}
                normalized['excerpts']=[r['content'] for r in db.execute('SELECT content FROM documents').fetchall() if r['content']['id'] in needed]
                payload=json.dumps(normalized,separators=(',',':')).encode()
                if len(payload)>2*1024*1024:raise HTTPException(413,'Normalized data exceeds the 2 MiB review limit. Split the period or facility.')
                checked=compute('validate',text=payload.decode())
                projected=compute('publish',state=head(db)['state'],inputs=checked,timestamp=datetime.now(timezone.utc).isoformat())
                if len(json.dumps(projected).encode())>4*1024*1024:raise HTTPException(413,'Review results exceed the safe response limit. Split this export into a shorter period.')
                # Stable canonical content includes facility/period/confirmed mapping results. A
                # retry after interruption reuses the accepted import rather than appending rows.
                imported=receive(settings,storage,member,payload,'table-'+digest(payload)[:48],invalidate_on_failure=False)
                if imported['status']!='validated':raise HTTPException(422,imported.get('help') or 'This source selection is no longer usable. Check its version and retention status, then validate again.')
                for source in sources:
                    target=source['object_key'].replace('/quarantine/','/accepted/')
                    if target!=source['object_key']:
                        copied.append(target)
                        storage.put(target,storage.get(source['object_key']),content_type='text/csv' if source['filename'].lower().endswith('.csv') else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                    db.execute("UPDATE table_files SET object_key=%s,status='accepted',expires_at=now()+interval '30 days' WHERE id=%s",(target,source['id']))
                for file in data['files']:
                    file['table'].pop('preview',None);file.pop('normalized_preview',None)
                db.execute("UPDATE table_sessions SET status='accepted',import_id=%s,data=%s,version=version+1 WHERE id=%s",(imported['id'],Jsonb(data),session_id))
                audit(db,member['org_id'],member['actor'],'table_selection_accepted',session_id,{'import_id':imported['id']})
        except Exception:
            for object_key in copied:storage.delete(object_key)
            raise
        for source in sources:
            if '/quarantine/' in source['object_key']:storage.delete(source['object_key'])
        return imported

    @app.post('/api/v1/import-workbench/profiles')
    def save_profile(body:Profile,request:Request):
        member=auth.principal(settings,request,'importer')
        with transaction(settings,member['org_id']) as db:
            row=session_row(db,body.session_id,member)
            if row['creator']!=member['actor']:raise HTTPException(403,'Only the mapping reviewer can save this configuration.')
            file=next((f for f in row['data']['files'] if f['id']==body.file_id),None)
            if not file or not file.get('config') or file['errors']:raise HTTPException(422,'Confirm a valid mapping before saving a profile.')
            head(db,True)
            def operation():
                if db.execute('SELECT count(*) AS n FROM mapping_profiles').fetchone()['n']>=30:raise HTTPException(429,'Keep up to 30 workspace mapping profiles.')
                profile_id='MAP-'+uuid.uuid4().hex
                config={k:v for k,v in file['config'].items() if k not in ['profile_id','profile_version']}
                db.execute('INSERT INTO mapping_profiles(id,org_id,name,category,config,headers,verified_by) VALUES(%s,%s,%s,%s,%s,%s,%s)',(profile_id,member['org_id'],body.name,file['category'],Jsonb(config),Jsonb(file['table']['headers']),member['actor']))
                audit(db,member['org_id'],member['actor'],'mapping_profile_saved',profile_id)
                return {'id':profile_id,'version':1}
            return write_once(db,member,request_key(request),body.model_dump(),operation)

    @app.delete('/api/v1/import-workbench/profiles/{profile_id}')
    def delete_profile(profile_id:str,request:Request):
        member=auth.principal(settings,request,'importer')
        with transaction(settings,member['org_id']) as db:
            if not db.execute('DELETE FROM mapping_profiles WHERE id=%s RETURNING id',(profile_id,)).fetchone():raise HTTPException(404,'Profile not found.')
            audit(db,member['org_id'],member['actor'],'mapping_profile_deleted',profile_id)
            return {'deleted':True}

    @app.get('/api/v1/import-workbench/sessions/{session_id}/files/{file_id}/source')
    def source(session_id:str,file_id:str,request:Request):
        member=auth.principal(settings,request)
        with transaction(settings,member['org_id']) as db:
            row=file_row(db,session_id,file_id)
            if 'importer' not in member['roles'] and not (row['category']=='rates' and 'approver' in member['roles']):raise HTTPException(403,'Source download permission required.')
            data=storage.get(row['object_key'])
            audit(db,member['org_id'],member['actor'],'table_source_download',file_id)
            return Response(data,media_type='application/octet-stream',headers={'Content-Disposition':f'attachment; filename="{row["filename"]}"'})
