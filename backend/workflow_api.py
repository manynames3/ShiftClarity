"""Authenticated period history and a shared, versioned follow-up queue."""
import base64
import json
from datetime import datetime
from typing import Literal
from fastapi import Request,HTTPException
from pydantic import BaseModel,ConfigDict,Field,StrictInt
from fastapi.encoders import jsonable_encoder
from . import auth
from .db import transaction,head,audit
from .workflow import event

class CaseAction(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    action:Literal['assign','record_correction','record_evidence','reopen']
    expected_version:StrictInt=Field(ge=1)
    owner:str|None=Field(default=None,max_length=80)
    reason:str=Field(min_length=3,max_length=2000)
    reference:str|None=Field(default=None,max_length=160)

def cursor(value):
    if value is None:return (None,None)
    try:
        if len(value)>400:raise ValueError()
        stamp,identifier=json.loads(base64.urlsafe_b64decode(value+'='*((-len(value))%4)))
        datetime.fromisoformat(stamp)
        if not isinstance(identifier,str) or len(identifier)>80:raise ValueError()
        return stamp,identifier
    except (ValueError,TypeError,KeyError):raise HTTPException(422,'Invalid page cursor.') from None

def next_cursor(row,column,key):
    return base64.urlsafe_b64encode(json.dumps([row[column].isoformat(),row[key]]).encode()).decode().rstrip('=')

def mount_workflow(app,settings):
    @app.get('/api/v1/reviews')
    def history(request:Request,before:str|None=None,limit:int=25):
        member=auth.principal(settings,request)
        if not 1<=limit<=50:raise HTTPException(422,'Choose up to 50 periods per page.')
        stamp,identifier=cursor(before)
        with transaction(settings,member['org_id']) as db:
            # Each run remains selectable; version and chronology do not depend on the shared latest run.
            rows=db.execute("""SELECT run_id,version,created_at,updated_at,
                    state#>'{run,manifest}' AS manifest,state#>'{run,totals}' AS totals,
                    jsonb_array_length(state#>'{run,findings}') AS findings,
                    state#>'{run,coverage}' AS coverage
                    FROM review_workspaces WHERE (%s::timestamptz IS NULL OR (created_at,run_id)<(%s::timestamptz,%s))
                    ORDER BY created_at DESC,run_id DESC LIMIT %s""",(stamp,stamp,identifier,limit+1)).fetchall()
            return {'reviews':rows[:limit],'next':next_cursor(rows[limit-1],'created_at','run_id') if len(rows)>limit else None,'latest_run_id':head(db)['state']['run']['id']}

    @app.get('/api/v1/cases')
    def cases(request:Request,scope:Literal['mine','team']='mine',status:str='open',before:str|None=None,limit:int=30):
        member=auth.principal(settings,request)
        if not 1<=limit<=50 or status not in ['open','all','resolved','dismissed']:raise HTTPException(422,'Invalid queue filter.')
        stamp,identifier=cursor(before)
        with transaction(settings,member['org_id']) as db:
            rows=db.execute("""SELECT * FROM billing_cases WHERE (%s='team' OR owner=%s)
                    AND (%s='all' OR (%s='open' AND status NOT IN ('resolved','dismissed')) OR status=%s)
                    AND (%s::timestamptz IS NULL OR (updated_at,id)<(%s::timestamptz,%s)) ORDER BY updated_at DESC,id DESC LIMIT %s""",
                    (scope,member['actor'],status,status,status,stamp,stamp,identifier,limit+1)).fetchall()
            approvals=[]
            if 'approver' in member['roles']:
                approvals=db.execute("SELECT id,creator,data->'period' AS period FROM table_sessions WHERE status='validated' AND creator<>%s ORDER BY created_at LIMIT 50",(member['actor'],)).fetchall()
            return {'cases':rows[:limit],'next':next_cursor(rows[limit-1],'updated_at','id') if len(rows)>limit else None,'approvals':approvals}

    @app.get('/api/v1/cases/{case_id}')
    def case_detail(case_id:str,request:Request):
        member=auth.principal(settings,request)
        with transaction(settings,member['org_id']) as db:
            case=db.execute('SELECT * FROM billing_cases WHERE id=%s',(case_id,)).fetchone()
            if not case:raise HTTPException(404,'Follow-up case not found.')
            return {'case':case,'events':db.execute('SELECT actor,action,run_id,data,created_at,sequence FROM case_events WHERE case_id=%s ORDER BY sequence',(case_id,)).fetchall()}

    @app.post('/api/v1/cases/{case_id}/actions')
    def update_case(case_id:str,body:CaseAction,request:Request):
        member=auth.principal(settings,request)
        reason=body.reason.strip()
        if len(reason)<3 or any(ord(c)<32 and c not in '\n\t' for c in reason):raise HTTPException(422,'Enter a specific follow-up reason.')
        with transaction(settings,member['org_id']) as db:
            head(db,True)
            def apply():
                case=db.execute('SELECT * FROM billing_cases WHERE id=%s FOR UPDATE',(case_id,)).fetchone()
                if not case:raise HTTPException(404,'Follow-up case not found.')
                if 'reviewer' not in member['roles'] and not (body.action=='record_evidence' and case['owner']==member['actor']):
                    raise HTTPException(403,'A reviewer manages this case; its assigned owner may record evidence.')
                if case['version']!=body.expected_version:raise HTTPException(409,'This case changed. Refresh before saving.')
                if body.owner and not db.execute('SELECT 1 FROM memberships WHERE org_id=%s AND actor=%s AND active',(member['org_id'],body.owner)).fetchone():
                    raise HTTPException(422,'Choose an active workspace member.')
                status=case['status'];reference=case['correction_reference'];owner=case['owner']
                if body.action=='assign':owner=body.owner
                elif body.action in ['record_correction','record_evidence']:
                    if case['status'] in ['resolved','dismissed']:raise HTTPException(409,'Reopen this case before recording a follow-up.')
                    if body.action=='record_correction' and case['kind']!='finding':raise HTTPException(422,'A coverage case needs evidence, not an invoice correction.')
                    reference=(body.reference or '').strip()
                    if not reference or any(ord(c)<32 for c in reference):raise HTTPException(422,'Enter a valid corrected invoice or evidence reference.')
                    status='correction_recorded' if body.action=='record_correction' else 'evidence_recorded'
                elif body.action=='reopen':status='open'
                db.execute('UPDATE billing_cases SET status=%s,owner=%s,correction_reference=%s,verified_run_id=CASE WHEN %s=\'reopen\' THEN NULL ELSE verified_run_id END,version=version+1,updated_at=now() WHERE id=%s',
                           (status,owner,reference,body.action,case_id))
                event(db,member['org_id'],case,member['actor'],body.action,case['last_run_id'],{'reason':reason,'owner':owner,'reference':reference})
                audit(db,member['org_id'],member['actor'],'case_'+body.action,case_id)
                return jsonable_encoder({'case':db.execute('SELECT * FROM billing_cases WHERE id=%s',(case_id,)).fetchone()})
            from .app import request_key,write_once
            return write_once(db,member,request_key(request),{'case_id':case_id,**body.model_dump()},apply)
