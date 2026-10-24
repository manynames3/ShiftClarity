import secrets
import time
from datetime import datetime, timezone, timedelta
from functools import lru_cache
from urllib.parse import urlencode,urlsplit
import httpx
import boto3
from authlib.integrations.httpx_client import OAuth2Client
from authlib.oidc.core import CodeIDToken
from joserfc import jwt
from joserfc.jwk import KeySet
from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from psycopg.types.json import Jsonb
from .db import transaction, audit
from .engine import digest

COOKIE="sc_session"
FLOW_COOKIE="sc_flow"

def cookie_name(settings,name):
    return "__Host-"+name if settings.cloud else name

def cookie(response, settings, name, value, age):
    response.set_cookie(cookie_name(settings,name),value,max_age=age,httponly=True,secure=settings.cloud,samesite="lax",path="/")

@lru_cache(maxsize=8)
def metadata(issuer, window):
    with httpx.Client(timeout=5,follow_redirects=False) as client:
        data=client.get(issuer+"/.well-known/openid-configuration").raise_for_status().json()
        if data["issuer"]!=issuer:
            raise ValueError("Issuer mismatch")
        keys=client.get(data["jwks_uri"]).raise_for_status().json()
    return data,keys

def provider(settings):
    return metadata(settings.issuer,int(time.time())//60)

def logout_url(settings,return_path="/pilot/"):
    data,_=provider(settings)
    if settings.cloud:
        authorize=urlsplit(data["authorization_endpoint"])
        endpoint=authorize.scheme+"://"+authorize.netloc+"/logout"
        return endpoint+"?"+urlencode({"client_id":settings.client_id,"logout_uri":settings.origin+return_path})
    return data["end_session_endpoint"]+"?"+urlencode({"client_id":settings.client_id,"post_logout_redirect_uri":settings.origin+"/pilot/"})

def verify_token(settings, token, nonce, access_token=None):
    _,keys=provider(settings)
    decoded=jwt.decode(token,KeySet.import_key_set(keys),algorithms=["RS256"])
    claims=CodeIDToken(decoded.claims,header=decoded.header,
        options={"iss":{"essential":True,"value":settings.issuer},"aud":{"essential":True,"value":settings.client_id}},
        params={"nonce":nonce,"client_id":settings.client_id,"access_token":access_token})
    claims.validate(leeway=30)
    if not claims.get("sub") or (time.time()-claims.get("auth_time",0)>900 or claims.get("auth_time",0)>time.time()+30):
        raise ValueError("Fresh authentication required")
    if not settings.cloud and "otp" not in claims.get("amr",[]):
        raise ValueError("Authenticator verification required")
    if settings.cloud:
        # Cognito can issue first-sign-in tokens before TOTP enrollment is complete.
        username=claims.get("cognito:username")
        if not isinstance(username,str) or not username:
            raise ValueError("Verified Cognito username required")
        client=boto3.client("cognito-idp",region_name=settings.region)
        configuration=client.get_user_pool_mfa_config(UserPoolId=settings.cognito_pool)
        if configuration.get("MfaConfiguration")!="ON" or not configuration.get("SoftwareTokenMfaConfiguration",{}).get("Enabled"):
            raise ValueError("Cognito mandatory TOTP MFA is required")
        user=client.admin_get_user(UserPoolId=settings.cognito_pool,Username=username)
        def matches(user):
            return user.get("Enabled") and any(attribute.get("Name")=="sub" and attribute.get("Value")==claims["sub"] for attribute in user.get("UserAttributes",[]))
        if not matches(user):
            raise ValueError("Cognito identity mismatch or disabled account")
        if "SOFTWARE_TOKEN_MFA" not in (user.get("UserMFASettingList") or []):
            # Classic login can leave preference unset; Cognito rejects unverified tokens here.
            client.admin_set_user_mfa_preference(UserPoolId=settings.cognito_pool,Username=username,
                SoftwareTokenMfaSettings={"Enabled":True,"PreferredMfa":True})
            user=client.admin_get_user(UserPoolId=settings.cognito_pool,Username=username)
        if not matches(user) or "SOFTWARE_TOKEN_MFA" not in (user.get("UserMFASettingList") or []):
            raise ValueError("Complete authenticator enrollment before workspace access")
    return claims

def verify_cloud_mfa(settings):
    if not settings.cloud:
        return
    client=boto3.client("cognito-idp",region_name=settings.region)
    configuration=client.get_user_pool_mfa_config(UserPoolId=settings.cognito_pool)
    if configuration.get("MfaConfiguration")!="ON" or not configuration.get("SoftwareTokenMfaConfiguration",{}).get("Enabled"):
        raise ValueError("Cognito mandatory TOTP MFA is required")
    configuration=client.describe_user_pool_client(UserPoolId=settings.cognito_pool,ClientId=settings.client_id)["UserPoolClient"]
    if configuration.get("AllowedOAuthFlows")!=["code"] or configuration.get("CallbackURLs")!=[settings.origin+"/auth/callback"]:
        raise ValueError("Cognito must use the registered authorization-code callback only")

def login(settings,return_to='/pilot/'):
    try:target=urlsplit(return_to)
    except ValueError:raise HTTPException(422,'Return to a valid workspace page.') from None
    if len(return_to)>1000 or target.scheme or target.netloc or target.path not in ['/pilot','/pilot/'] or '\\' in return_to or any(ord(c)<32 for c in return_to):
        raise HTTPException(422,'Return to a valid workspace page.')
    data,_=provider(settings)
    flow=secrets.token_urlsafe(32)
    state=secrets.token_urlsafe(32)
    verifier=secrets.token_urlsafe(48)
    nonce=secrets.token_urlsafe(32)
    with OAuth2Client(settings.client_id,settings.client_secret,scope="openid",
                      redirect_uri=settings.origin+"/auth/callback",code_challenge_method="S256") as client:
        url,_=client.create_authorization_url(data["authorization_endpoint"],state=state,
                     code_verifier=verifier,nonce=nonce,max_age=0,prompt="login")
    with transaction(settings) as db:
        db.execute("DELETE FROM auth_flows WHERE expires_at < now()")
        db.execute("INSERT INTO auth_flows VALUES(%s,%s,now()+interval '5 minutes')",
                   (digest(flow.encode()),Jsonb({"state":state,"verifier":verifier,"nonce":nonce,"authorization_url":url,"return_to":return_to})))
    # Classic Cognito login does not support prompt=login; clear its SSO cookie first.
    response=RedirectResponse(logout_url(settings,"/auth/continue") if settings.cloud else url,status_code=303)
    cookie(response,settings,FLOW_COOKIE,flow,300)
    return response

def continue_login(settings,request):
    flow=request.cookies.get(cookie_name(settings,FLOW_COOKIE),"")
    with transaction(settings) as db:
        stored=db.execute("SELECT data FROM auth_flows WHERE digest=%s AND expires_at>now()",(digest(flow.encode()),)).fetchone()
    if not stored or not settings.cloud:
        raise HTTPException(401,"Sign-in expired or invalid. Start again.")
    return RedirectResponse(stored["data"]["authorization_url"],status_code=303)

def callback(settings,request):
    flow=request.cookies.get(cookie_name(settings,FLOW_COOKIE),"")
    with transaction(settings) as db:
        stored=db.execute("DELETE FROM auth_flows WHERE digest=%s AND expires_at>now() RETURNING data",
                          (digest(flow.encode()),)).fetchone()
    if not stored or not secrets.compare_digest(stored["data"]["state"].encode(),request.query_params.get("state","").encode()):
        raise HTTPException(401,"Sign-in expired or invalid. Start again.")
    data,_=provider(settings)
    saved=stored["data"]
    try:
        with OAuth2Client(settings.client_id,settings.client_secret,
            redirect_uri=settings.origin+"/auth/callback",token_endpoint_auth_method="client_secret_basic") as client:
            token=client.fetch_token(data["token_endpoint"],code=request.query_params["code"],code_verifier=saved["verifier"])
        claims=verify_token(settings,token["id_token"],saved["nonce"],token.get("access_token"))
    except Exception:
        raise HTTPException(401,"Identity verification failed. Start again.") from None
    session=secrets.token_urlsafe(32)
    csrf=secrets.token_urlsafe(32)
    with transaction(settings) as db:
        member=db.execute("SELECT * FROM memberships WHERE issuer=%s AND subject=%s AND active",
                          (settings.issuer,claims["sub"])).fetchone()
        if not member or member["org_id"]!=settings.org_id:
            raise HTTPException(403,"This account has no workspace membership.")
        if settings.cloud:
            db.execute("SELECT set_config('app.org_id',%s,true)",(member['org_id'],))
            username=claims['cognito:username']
            if member['provider_username'] and member['provider_username']!=username:
                raise HTTPException(403,'Verified identity mapping changed. Contact your workspace owner.')
            db.execute('UPDATE memberships SET provider_username=%s WHERE issuer=%s AND subject=%s',(username,settings.issuer,claims['sub']))
        db.execute("DELETE FROM sessions WHERE expires_at<now()")
        db.execute("INSERT INTO sessions VALUES(%s,%s,%s,%s,%s)",
                   (digest(session.encode()),settings.issuer,claims["sub"],csrf,datetime.now(timezone.utc)+timedelta(minutes=15)))
        db.execute("SELECT set_config('app.org_id',%s,true)",(member["org_id"],))
        audit(db,member["org_id"],member["actor"],"signed_in","session")
    response=RedirectResponse(saved.get('return_to','/pilot/'),status_code=303)
    cookie(response,settings,COOKIE,session,900)
    response.delete_cookie(cookie_name(settings,FLOW_COOKIE),path="/",secure=settings.cloud,httponly=True,samesite="lax")
    return response

def principal(settings,request,permission=None):
    raw=request.cookies.get(cookie_name(settings,COOKIE),"")
    if not raw:
        raise HTTPException(401,"Sign in to access this workspace.")
    with transaction(settings) as db:
        member=db.execute("""
          SELECT m.*,s.csrf FROM sessions s JOIN memberships m USING(issuer,subject)
          WHERE s.digest=%s AND s.expires_at>now() AND m.active
        """,(digest(raw.encode()),)).fetchone()
    if not member or member["org_id"]!=settings.org_id:
        raise HTTPException(401,"Session expired or access revoked.")
    if permission and permission not in member["roles"]:
        raise HTTPException(403,"Your account does not have permission for this action.")
    if request.method not in ("GET","HEAD","OPTIONS"):
        if request.headers.get("origin")!=settings.origin or not secrets.compare_digest(member["csrf"].encode(),request.headers.get("x-csrf-token","").encode()):
            raise HTTPException(403,"Invalid request origin or security token.")
    return member
