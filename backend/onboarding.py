"""Invite-only workspace administration; credentials are returned once and never stored."""
import secrets
from typing import Literal
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from fastapi import Request,HTTPException
from pydantic import Field,StrictInt
from . import auth
from .db import transaction,head,audit

ROLES=Literal['owner','importer','reviewer','author','approver']

def identity_client(settings):
    if not settings.cloud:raise HTTPException(503,'Account provisioning requires the configured Cognito pilot. Local test identities are managed separately.')
    return boto3.client('cognito-idp',region_name=settings.region,config=Config(connect_timeout=3,read_timeout=5,retries={'max_attempts':1}))

def provision_identity(settings,username):
    client=identity_client(settings)
    try:
        user=client.admin_get_user(UserPoolId=settings.cognito_pool,Username=username)
        if not user.get('Enabled'):raise HTTPException(409,'This Cognito identity is disabled. Restore it through the account administrator first.')
        return next(a['Value'] for a in user['UserAttributes'] if a['Name']=='sub'),user['Username'],None
    except ClientError as error:
        if error.response['Error']['Code']!='UserNotFoundException':raise HTTPException(503,'Identity service unavailable. Retry this action.') from None
    password='Aa1!'+secrets.token_urlsafe(24)
    try:
        user=client.admin_create_user(UserPoolId=settings.cognito_pool,Username=username,TemporaryPassword=password,MessageAction='SUPPRESS')['User']
        return next(a['Value'] for a in user['Attributes'] if a['Name']=='sub'),user['Username'],password
    except ClientError:raise HTTPException(503,'Account creation could not finish. Retry the same username; no membership was granted.') from None

def reset_identity(settings,member):
    client=identity_client(settings);password='Aa1!'+secrets.token_urlsafe(24)
    if not member.get('provider_username'):raise HTTPException(409,'This older identity needs one verified sign-in before an owner can reset it.')
    try:
        user=client.admin_get_user(UserPoolId=settings.cognito_pool,Username=member['provider_username'])
        if not user.get('Enabled') or not any(a['Name']=='sub' and a['Value']==member['subject'] for a in user['UserAttributes']):
            raise HTTPException(409,'Identity mapping changed. No password was reset.')
        client.admin_set_user_password(UserPoolId=settings.cognito_pool,Username=user['Username'],Password=password,Permanent=False)
    except ClientError:raise HTTPException(503,'Password reset could not finish. No credentials were recorded. Retry.') from None
    return password

def mount_onboarding(app,settings):
    from .app import StrictBody,request_key,write_once
    class Agency(StrictBody):
        label:str=Field(min_length=3,max_length=80)
        default_facility:str=Field(pattern=r'^[A-Za-z0-9_-]{1,80}$')
        expected_version:StrictInt=Field(ge=1)
    class Invite(StrictBody):
        username:str=Field(pattern=r'^[A-Za-z0-9][A-Za-z0-9_-]{2,79}$')
        roles:list[ROLES]=Field(min_length=1,max_length=5)
    class MemberChange(StrictBody):
        roles:list[ROLES]=Field(min_length=1,max_length=5)
        active:bool
        expected_version:StrictInt=Field(ge=1)
    class Reset(StrictBody):
        expected_version:StrictInt=Field(ge=1)

    @app.get('/api/v1/agency')
    def agency(request:Request):
        member=auth.principal(settings,request)
        with transaction(settings,member['org_id']) as db:
            row=db.execute('SELECT label,default_facility,version FROM agency_settings').fetchone()
            counts=db.execute("SELECT count(*) FILTER(WHERE active AND 'approver'=ANY(roles)) AS approvers,count(*) FILTER(WHERE active AND 'importer'=ANY(roles)) AS importers,count(*) FILTER(WHERE active) AS members FROM memberships WHERE org_id=%s",(member['org_id'],)).fetchone()
            return {'settings':row or {'label':'Synthetic pilot workspace','default_facility':'FAC-A','version':1},'team':counts,'has_import':bool(db.execute("SELECT 1 FROM table_sessions WHERE status='accepted' LIMIT 1").fetchone()),'has_review':bool(db.execute("SELECT 1 FROM audit_events WHERE action IN ('finding_confirm','finding_dismiss','finding_request_evidence') LIMIT 1").fetchone()),'provisioning_available':settings.cloud}

    @app.post('/api/v1/agency')
    def update_agency(body:Agency,request:Request):
        member=auth.principal(settings,request,'owner')
        if len(body.label.strip())<3 or any(ord(c)<32 for c in body.label):raise HTTPException(422,'Enter a workspace label without control characters.')
        with transaction(settings,member['org_id']) as db:
            head(db,True)
            def operation():
                db.execute('INSERT INTO agency_settings(org_id) VALUES(%s) ON CONFLICT DO NOTHING',(member['org_id'],))
                changed=db.execute('UPDATE agency_settings SET label=%s,default_facility=%s,version=version+1,updated_at=now() WHERE version=%s RETURNING version',(body.label.strip(),body.default_facility,body.expected_version)).fetchone()
                if not changed:raise HTTPException(409,'Workspace settings changed. Refresh first.')
                audit(db,member['org_id'],member['actor'],'agency_updated','settings')
                return {'version':changed['version']}
            return write_once(db,member,request_key(request),body.model_dump(),operation)

    @app.get('/api/v1/team')
    def team(request:Request):
        member=auth.principal(settings,request,'owner')
        with transaction(settings,member['org_id']) as db:
            return db.execute('SELECT actor,roles,active,version FROM memberships WHERE org_id=%s ORDER BY actor',(member['org_id'],)).fetchall()

    @app.post('/api/v1/team')
    def invite(body:Invite,request:Request):
        member=auth.principal(settings,request,'owner');key=request_key(request)
        with transaction(settings,member['org_id']) as db:
            head(db,True)
            # The receipt contains no password. A lost response is recovered with an owner reset.
            def operation():
                if db.execute('SELECT 1 FROM memberships WHERE org_id=%s AND actor=%s',(member['org_id'],body.username)).fetchone():raise HTTPException(409,'This username already has a workspace membership. Manage it below.')
                if db.execute("SELECT count(*) AS n FROM memberships WHERE org_id=%s",(member['org_id'],)).fetchone()['n']>=50:raise HTTPException(429,'This pilot supports up to 50 team members.')
                subject,provider_username,password=provision_identity(settings,body.username)
                if db.execute('SELECT 1 FROM memberships WHERE issuer=%s AND subject=%s',(settings.issuer,subject)).fetchone():raise HTTPException(409,'This identity already belongs to a workspace.')
                db.execute('INSERT INTO memberships(issuer,subject,org_id,actor,roles,active,provider_username) VALUES(%s,%s,%s,%s,%s,true,%s)',(settings.issuer,subject,member['org_id'],body.username,sorted(set(body.roles)),provider_username))
                audit(db,member['org_id'],member['actor'],'member_added',body.username)
                result['temporary_password']=password
                return {'username':provider_username,'sign_in_url':settings.origin+'/pilot/','expires_in_days':3}
            result={}
            receipt=write_once(db,member,key,body.model_dump(),operation)
            return {**receipt,**result}

    @app.post('/api/v1/team/{actor}')
    def change(actor:str,body:MemberChange,request:Request):
        member=auth.principal(settings,request,'owner')
        with transaction(settings,member['org_id']) as db:
            head(db,True)
            def operation():
                target=db.execute('SELECT * FROM memberships WHERE org_id=%s AND actor=%s FOR UPDATE',(member['org_id'],actor)).fetchone()
                if not target:raise HTTPException(404,'Member not found.')
                if target['version']!=body.expected_version:raise HTTPException(409,'Member access changed. Refresh first.')
                if target['active'] and 'owner' in target['roles'] and (not body.active or 'owner' not in body.roles):
                    remaining=db.execute("SELECT 1 FROM memberships WHERE org_id=%s AND actor<>%s AND active AND 'owner'=ANY(roles)",(member['org_id'],actor)).fetchone()
                    if not remaining:raise HTTPException(409,'Keep at least one active workspace owner.')
                db.execute('UPDATE memberships SET roles=%s,active=%s,version=version+1 WHERE issuer=%s AND subject=%s',(sorted(set(body.roles)),body.active,target['issuer'],target['subject']))
                db.execute('DELETE FROM sessions WHERE issuer=%s AND subject=%s',(target['issuer'],target['subject']))
                audit(db,member['org_id'],member['actor'],'member_access_changed',actor,{'roles':body.roles,'active':body.active})
                return {'saved':True}
            return write_once(db,member,request_key(request),{'actor':actor,**body.model_dump()},operation)

    @app.post('/api/v1/team/{actor}/reset')
    def reset(actor:str,body:Reset,request:Request):
        member=auth.principal(settings,request,'owner');request_key(request)
        with transaction(settings,member['org_id']) as db:
            head(db,True)
            target=db.execute('SELECT * FROM memberships WHERE org_id=%s AND actor=%s AND active FOR UPDATE',(member['org_id'],actor)).fetchone()
            if not target:raise HTTPException(404,'Active member not found.')
            if target['version']!=body.expected_version:raise HTTPException(409,'Member changed. Refresh first.')
            if actor==member['actor']:raise HTTPException(409,'Ask another owner to reset your account so you retain access.')
            password=reset_identity(settings,target)
            db.execute('DELETE FROM sessions WHERE issuer=%s AND subject=%s',(target['issuer'],target['subject']))
            db.execute('UPDATE memberships SET version=version+1 WHERE issuer=%s AND subject=%s',(target['issuer'],target['subject']))
            audit(db,member['org_id'],member['actor'],'member_password_reset',actor)
            return {'username':target['provider_username'],'temporary_password':password,'sign_in_url':settings.origin+'/pilot/','expires_in_days':3}
