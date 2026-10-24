import secrets
import psycopg
import pytest
from backend.db import transaction
from backend.tests.conftest import TEST_ADMIN
from backend.tests.test_period_workflow import post


def owner(environment,clients):
    with psycopg.connect(TEST_ADMIN) as db:db.execute("UPDATE memberships SET roles=roles||array['owner'] WHERE actor='DEMO-REVIEWER'")
    return clients()


def test_owner_settings_invite_roles_and_revocation(environment,clients,monkeypatch):
    client=owner(environment,clients);approver=clients('DEMO-APPROVER')
    assert approver.get('/api/v1/team').status_code==403
    assert post(approver,'/api/v1/team',{'username':'new-reviewer','roles':['reviewer']}).status_code==403
    agency=client.get('/api/v1/agency').json();assert agency['team']['approvers']==2
    response=post(client,'/api/v1/agency',{'label':'Fictional Staffing Agency','default_facility':'FAC-B','expected_version':agency['settings']['version']})
    assert response.status_code==200,response.text
    assert client.get('/api/v1/agency').json()['settings']['default_facility']=='FAC-B'
    monkeypatch.setattr('backend.onboarding.provision_identity',lambda settings,username:('INVITED-SUB',username,'temporary-test-only'))
    key=secrets.token_hex(16);body={'username':'new-reviewer','roles':['reviewer','importer']}
    invite=client.post('/api/v1/team',json=body,headers={'Idempotency-Key':key})
    assert invite.status_code==200 and invite.json()['temporary_password']=='temporary-test-only',invite.text
    again=client.post('/api/v1/team',json=body,headers={'Idempotency-Key':key})
    assert again.status_code==200 and 'temporary_password' not in again.json()
    with transaction(environment,environment.org_id) as db:
        receipt=db.execute('SELECT response FROM write_receipts WHERE request_key=%s',(key,)).fetchone()
        assert 'temporary-test-only' not in str(receipt)
    # Changes invalidate active sessions immediately; the final owner cannot be removed.
    row=next(m for m in client.get('/api/v1/team').json() if m['actor']=='DEMO-APPROVER')
    assert post(client,'/api/v1/team/DEMO-APPROVER',{**{k:row[k] for k in ['roles','active']},'active':False,'expected_version':row['version']}).status_code==200
    assert approver.get('/api/v1/workspace').status_code==401
    me=next(m for m in client.get('/api/v1/team').json() if m['actor']=='DEMO-REVIEWER')
    assert post(client,'/api/v1/team/DEMO-REVIEWER',{'roles':['reviewer'],'active':True,'expected_version':me['version']}).status_code==409
    with transaction(environment,'other-workspace') as db:
        with pytest.raises(psycopg.Error):
            db.execute("INSERT INTO memberships(issuer,subject,org_id,actor,roles) VALUES('test','forged','synthetic-pilot','forged',array['owner'])")



def test_cognito_invitation_suppresses_messages_and_reset_remains_temporary(environment,monkeypatch):
    from backend.onboarding import provision_identity,reset_identity
    from dataclasses import replace
    import boto3
    from botocore.stub import Stubber
    from botocore.exceptions import ClientError
    config=replace(environment,cloud=True,cognito_pool='us-east-1_test')
    client=boto3.client('cognito-idp',region_name='us-east-1',aws_access_key_id='test',aws_secret_access_key='test')
    monkeypatch.setattr('backend.onboarding.identity_client',lambda settings:client)
    monkeypatch.setattr('backend.onboarding.secrets.token_urlsafe',lambda size:'random-test-only')
    with Stubber(client) as stub:
        stub.add_client_error('admin_get_user','UserNotFoundException',expected_params={'UserPoolId':config.cognito_pool,'Username':'new-member'})
        stub.add_response('admin_create_user',{'User':{'Username':'new-member','Attributes':[{'Name':'sub','Value':'verified-sub'}]}},{'UserPoolId':config.cognito_pool,'Username':'new-member','TemporaryPassword':'Aa1!random-test-only','MessageAction':'SUPPRESS'})
        assert provision_identity(config,'new-member')==('verified-sub','new-member','Aa1!random-test-only')
        stub.add_response('admin_get_user',{'Username':'new-member','Enabled':True,'UserAttributes':[{'Name':'sub','Value':'verified-sub'}]}, {'UserPoolId':config.cognito_pool,'Username':'new-member'})
        stub.add_response('admin_set_user_password',{}, {'UserPoolId':config.cognito_pool,'Username':'new-member','Password':'Aa1!random-test-only','Permanent':False})
        assert reset_identity(config,{'subject':'verified-sub','provider_username':'new-member'})=='Aa1!random-test-only'


def test_reset_rejects_changed_provider_binding(environment,monkeypatch):
    from backend.onboarding import reset_identity
    from dataclasses import replace
    from fastapi import HTTPException
    import boto3
    from botocore.stub import Stubber
    client=boto3.client('cognito-idp',region_name='us-east-1',aws_access_key_id='test',aws_secret_access_key='test')
    monkeypatch.setattr('backend.onboarding.identity_client',lambda settings:client)
    with Stubber(client) as stub:
        stub.add_response('admin_get_user',{'Username':'new-member','Enabled':True,'UserAttributes':[{'Name':'sub','Value':'different-sub'}]}, {'UserPoolId':'us-east-1_test','Username':'new-member'})
        with pytest.raises(HTTPException) as failure:reset_identity(replace(environment,cloud=True,cognito_pool='us-east-1_test'),{'subject':'verified-sub','provider_username':'new-member'})
        assert failure.value.status_code==409
        stub.assert_no_pending_responses()
