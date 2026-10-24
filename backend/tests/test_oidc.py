import time
from unittest.mock import patch
import pytest
from joserfc import jwt
from joserfc.jwk import RSAKey
from backend.auth import verify_token
from urllib.parse import urlparse,parse_qs
import psycopg
from .conftest import TEST_ADMIN
from dataclasses import replace
from backend.auth import cookie,cookie_name,login,continue_login
from fastapi.responses import Response
from fastapi import HTTPException
from starlette.requests import Request

@pytest.mark.parametrize("enabled,factors,allowed",[(True,["SOFTWARE_TOKEN_MFA"],True),(True,[],False),(False,["SOFTWARE_TOKEN_MFA"],False)])
def test_cloud_rejects_cognito_pre_enrollment_tokens(settings,enabled,factors,allowed):
    cloud=replace(settings,cloud=True,cognito_pool="test-pool")
    key=RSAKey.generate_key(2048)
    key.ensure_kid()
    public=key.as_dict(private=False)
    public["use"]="sig"
    timestamp=int(time.time())
    encoded=jwt.encode({"alg":"RS256","kid":public["kid"]},{
        "iss":cloud.issuer,"aud":cloud.client_id,"sub":"verified-user","iat":timestamp,
        "exp":timestamp+60,"auth_time":timestamp,"nonce":"expected","cognito:username":"verified-login"},key)
    with patch("backend.auth.provider",return_value=({},{"keys":[public]})),patch("backend.auth.boto3.client") as provider:
        provider.return_value.get_user_pool_mfa_config.return_value={"MfaConfiguration":"ON","SoftwareTokenMfaConfiguration":{"Enabled":True}}
        provider.return_value.admin_get_user.return_value={"Enabled":enabled,"UserMFASettingList":factors,"UserAttributes":[{"Name":"sub","Value":"verified-user"}]}
        provider.return_value.admin_set_user_mfa_preference.side_effect=ValueError("Complete authenticator enrollment")
        if allowed:
            assert verify_token(cloud,encoded,"expected")["sub"]=="verified-user"
        else:
            with pytest.raises(ValueError,match="enrollment" if enabled else "disabled"):
                verify_token(cloud,encoded,"expected")
        provider.return_value.admin_get_user.assert_called_once_with(UserPoolId="test-pool",Username="verified-login")

@pytest.mark.parametrize("case",["registered-unpreferred","unenrolled","subject-mismatch"])
def test_cognito_classic_enrollment_is_verified_by_service(settings,case):
    cloud=replace(settings,cloud=True,cognito_pool="test-pool")
    key=RSAKey.generate_key(2048)
    key.ensure_kid()
    public=key.as_dict(private=False)
    public["use"]="sig"
    timestamp=int(time.time())
    token=jwt.encode({"alg":"RS256","kid":public["kid"]},{"iss":cloud.issuer,"aud":cloud.client_id,
        "sub":"verified-user","cognito:username":"verified-login","iat":timestamp,"exp":timestamp+60,
        "auth_time":timestamp,"nonce":"expected"},key)
    first={"Enabled":True,"UserAttributes":[{"Name":"sub","Value":"another-user" if case=="subject-mismatch" else "verified-user"}]}
    enrolled={**first,"UserMFASettingList":["SOFTWARE_TOKEN_MFA"]}
    with patch("backend.auth.provider",return_value=({},{"keys":[public]})),patch("backend.auth.boto3.client") as provider:
        provider.return_value.get_user_pool_mfa_config.return_value={"MfaConfiguration":"ON","SoftwareTokenMfaConfiguration":{"Enabled":True}}
        provider.return_value.admin_get_user.side_effect=[first,enrolled]
        if case=="unenrolled":
            provider.return_value.admin_set_user_mfa_preference.side_effect=ValueError("No verified software token")
        if case=="registered-unpreferred":
            assert verify_token(cloud,token,"expected")["sub"]=="verified-user"
            provider.return_value.admin_set_user_mfa_preference.assert_called_once_with(UserPoolId="test-pool",Username="verified-login",SoftwareTokenMfaSettings={"Enabled":True,"PreferredMfa":True})
        else:
            with pytest.raises(ValueError):
                verify_token(cloud,token,"expected")
            if case=="subject-mismatch":provider.return_value.admin_set_user_mfa_preference.assert_not_called()

def test_cloud_cookie_is_host_bound(settings):
    cloud=replace(settings,cloud=True)
    response=Response()
    cookie(response,cloud,"sc_session","opaque-test",900)
    header=response.headers["set-cookie"]
    assert header.startswith("__Host-sc_session=") and "Secure" in header and "HttpOnly" in header
    assert "Path=/" in header and "Domain=" not in header
    assert cookie_name(settings,"sc_session")=="sc_session"

def test_classic_cognito_sso_is_cleared_before_fresh_code_flow(environment):
    cloud=replace(environment,cloud=True,origin="https://pilot.example",cognito_pool="test-pool")
    discovery={"authorization_endpoint":"https://trusted-provider.example/oauth2/authorize"}
    with patch("backend.auth.provider",return_value=(discovery,{})):
        response=login(cloud)
    location=parse_qs(urlparse(response.headers["location"]).query)
    assert urlparse(response.headers["location"]).path=="/logout"
    assert location["logout_uri"]==[cloud.origin+"/auth/continue"]
    flow=response.headers["set-cookie"].split(";",1)[0]
    request=Request({"type":"http","headers":[(b"cookie",flow.encode())]})
    resumed=continue_login(cloud,request)
    code_flow=parse_qs(urlparse(resumed.headers["location"]).query)
    assert code_flow["response_type"]==["code"] and code_flow["code_challenge_method"]==["S256"]
    assert code_flow["state"] and code_flow["nonce"]
    with pytest.raises(HTTPException):
        continue_login(cloud,Request({"type":"http","headers":[]}))

@pytest.mark.parametrize("case",["valid","issuer","audience","nonce","expired","signature","mfa","fresh"])
def test_verified_identity_claims(settings,case):
    key=RSAKey.generate_key(2048)
    key.ensure_kid()
    public=key.as_dict(private=False)
    public["use"]="sig"
    timestamp=int(time.time())
    claims={"iss":settings.issuer,"aud":settings.client_id,"sub":"verified-user",
            "iat":timestamp,"exp":timestamp+60,"auth_time":timestamp,"nonce":"expected","amr":["pwd","otp"]}
    if case=="issuer":claims["iss"]="https://evil.example"
    if case=="audience":claims["aud"]="another-app"
    if case=="nonce":claims["nonce"]="replayed"
    if case=="expired":claims["exp"]=timestamp-1000
    if case=="mfa":claims["amr"]=["pwd"]
    if case=="fresh":claims["auth_time"]=timestamp-1000
    signer=RSAKey.generate_key(2048) if case=="signature" else key
    encoded=jwt.encode({"alg":"RS256","kid":public["kid"]},claims,signer)
    with patch("backend.auth.provider",return_value=({},{"keys":[public]})):
        if case=="valid":
            assert verify_token(settings,encoded,"expected")["sub"]=="verified-user"
        else:
            with pytest.raises(Exception):
                verify_token(settings,encoded,"expected")

@pytest.mark.parametrize('return_to',['/pilot/','/pilot/?view=evidence&id=FND-001&run=RUN-001'])
def test_browser_bound_code_flow_is_single_use_with_secure_session_cookie(environment,clients,return_to):
    client=clients()
    client.cookies.clear()
    key=RSAKey.generate_key(2048)
    key.ensure_kid()
    public=key.as_dict(private=False)
    public["use"]="sig"
    discovery={"authorization_endpoint":"https://trusted-provider.example/authorize",
               "token_endpoint":"https://trusted-provider.example/token"}
    with patch("backend.auth.provider",return_value=(discovery,{"keys":[public]})):
        started=client.get("/auth/login",params={"return_to":return_to},follow_redirects=False)
        params=parse_qs(urlparse(started.headers["location"]).query)
        assert params["code_challenge_method"]==["S256"] and params["response_type"]==["code"]
        with psycopg.connect(TEST_ADMIN) as db:
            flow=db.execute("SELECT data FROM auth_flows").fetchone()[0]
        timestamp=int(time.time())
        token=jwt.encode({"alg":"RS256","kid":public["kid"]},{
            "iss":environment.issuer,"aud":environment.client_id,"sub":"DEMO-REVIEWER",
            "iat":timestamp,"exp":timestamp+60,"auth_time":timestamp,"nonce":flow["nonce"],"amr":["pwd","otp"]
        },key)
        callback="/auth/callback?state="+params["state"][0]+"&code=synthetic-code"
        with patch("backend.auth.OAuth2Client.fetch_token",return_value={"id_token":token}):
            result=client.get(callback,follow_redirects=False)
        assert result.status_code==303,result.text
        assert result.headers["location"]==return_to
        cookie=result.headers["set-cookie"]
        assert "HttpOnly" in cookie and "SameSite=lax" in cookie and "Max-Age=900" in cookie
        assert client.get("/api/v1/session").json()["actor"]=="DEMO-REVIEWER"
        assert client.get(callback,follow_redirects=False).status_code==401
        client.get("/auth/login",follow_redirects=False)
        assert client.get("/auth/callback?state=caf%C3%A9&code=invalid",follow_redirects=False).status_code==401
        with psycopg.connect(TEST_ADMIN) as db:
            stored=db.execute("SELECT digest FROM sessions").fetchall()
            assert all(row[0]!=client.cookies.get("sc_session") for row in stored)


@pytest.mark.parametrize('target',['http://[','https://evil.example/','//evil.example/','/auth/logout','/pilot/\\evil','/pilot/?x=\r\n'])
def test_login_return_cannot_leave_workspace(environment,target):
    with pytest.raises(HTTPException):login(environment,target)
