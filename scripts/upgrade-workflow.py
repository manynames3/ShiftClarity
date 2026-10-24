"""Apply additive synthetic-workflow migrations without reseeding or replacing evidence."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit,parse_qsl,urlencode
import certifi
import psycopg
from psycopg import sql
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from backend.bootstrap import migrate
from backend.config import ROOT,Settings

parser=argparse.ArgumentParser()
parser.add_argument('--target',choices=['local','verification','cloud'],required=True)
args=parser.parse_args()
name={'local':'config','verification':'neon-app-config','cloud':'aws-cloud-config'}[args.target]
settings=Settings(**json.loads((ROOT/'.local'/f'{name}.json').read_text()))
if args.target=='local':
    assert urlsplit(settings.database_url).hostname in ['127.0.0.1','localhost'] and not settings.cloud
    admin='postgresql://shiftclarity_local@/'+urlsplit(settings.database_url).path.strip('/')+'?host=/tmp&port=55478'
else:
    owner='neon-cloud-owner' if args.target=='cloud' else 'neon-app-owner'
    parsed=urlsplit(json.loads((ROOT/'.local'/f'{owner}.json').read_text())['url'])
    parsed=parsed._replace(netloc=parsed.netloc.replace('-pooler',''))
    expected=json.loads((ROOT/'.local/neon-cloud-metadata.json').read_text())['host'] if args.target=='cloud' else 'ep-spring-paper-b7mh5woh.c-13.us-east-1.aws.neon.tech'
    assert parsed.hostname==expected and parsed.path=='/shiftclarity','Unexpected synthetic database'
    query=dict(parse_qsl(parsed.query));query['sslmode']='verify-full'
    admin=urlunsplit(parsed._replace(query=urlencode(query)))
with psycopg.connect(admin,**({'sslrootcert':certifi.where()} if args.target!='local' else {})) as db:
    immutable=['completed_runs','source_revisions','rule_versions']
    def evidence():
        return {table:hashlib.sha256(json.dumps(sorted(r[0] for r in db.execute(sql.SQL('SELECT row_to_json(t)::text FROM {} t WHERE org_id=%s').format(sql.Identifier(table)),(settings.org_id,)).fetchall())).encode()).hexdigest() for table in immutable}
    before=evidence()
    prior=db.execute('SELECT state FROM workspace_heads WHERE org_id=%s',(settings.org_id,)).fetchone()[0]
    migrate(db)
    assert evidence()==before,'Original evidence changed; migration rolled back'
    assert db.execute('SELECT state FROM workspace_heads WHERE org_id=%s',(settings.org_id,)).fetchone()[0]==prior,'Current review changed; migration rolled back'
    from backend.fingerprints import compact_state
    selected=db.execute('SELECT state FROM review_workspaces WHERE org_id=%s AND run_id=%s',(settings.org_id,prior['run']['id'])).fetchone()[0]
    assert selected['reviews']==compact_state(prior)['reviews'],'Current review history was not preserved'

    bindings=0
    if args.target=='cloud':
        import boto3
        from botocore.exceptions import ClientError
        session=boto3.Session(region_name=settings.region)
        assert ':assumed-role/shiftclarity-deployer/' in session.client('sts').get_caller_identity()['Arn'],'Use the dedicated deployment role'
        provider=session.client('cognito-idp')
        accounts=json.loads((ROOT/'.local/aws-accounts.json').read_text())
        known={a.get('subject'):a['username'] for a in accounts}
        for subject,actor in db.execute('SELECT subject,actor FROM memberships WHERE issuer=%s AND org_id=%s AND provider_username IS NULL',(settings.issuer,settings.org_id)).fetchall():
            try:user=provider.admin_get_user(UserPoolId=settings.cognito_pool,Username=known.get(subject,actor))
            except ClientError as error:
                if error.response['Error']['Code']=='UserNotFoundException':continue
                raise
            assert any(a['Name']=='sub' and a['Value']==subject for a in user['UserAttributes']),'Provider identity mismatch'
            db.execute('UPDATE memberships SET provider_username=%s WHERE issuer=%s AND subject=%s AND org_id=%s',(user['Username'],settings.issuer,subject,settings.org_id));bindings+=1
        reviewer=next(a for a in json.loads((ROOT/'.local/aws-accounts.json').read_text()) if a['username']=='reviewer')
        row=db.execute("SELECT actor,roles FROM memberships WHERE issuer=%s AND subject=%s AND org_id=%s AND active",(settings.issuer,reviewer['subject'],settings.org_id)).fetchone()
        assert row and row[0]==reviewer['actor'],'Approved private reviewer not found'
        if 'owner' not in row[1]:
            db.execute("UPDATE memberships SET roles=roles||array['owner'],version=version+1 WHERE issuer=%s AND subject=%s",(settings.issuer,reviewer['subject']))
            db.execute("INSERT INTO audit_events(org_id,actor,action,resource) VALUES(%s,'OWNER-BOOTSTRAP','synthetic_owner_assigned',%s)",(settings.org_id,row[0]))
    count=db.execute('SELECT count(*) FROM review_workspaces WHERE org_id=%s',(settings.org_id,)).fetchone()[0]
print(json.dumps({'target':args.target,'additive_migrations':'006-009','verified_provider_bindings':bindings,'review_workspaces':count,'reseeded':False,'original_evidence_unchanged':True,'current_reviews_preserved':True,'owner':'existing private reviewer' if args.target=='cloud' else 'unchanged'}))
