"""Create dedicated, loopback-only synthetic services; reruns preserve records."""
import json
import os
import secrets
import subprocess
import sys
import uuid
import pwd
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb
from backend.config import ROOT, Settings
from backend.engine import compute
from backend.bootstrap import seed,migrate

local=ROOT/".local"
local.mkdir(exist_ok=True,mode=0o700)
configuration=local/"config.json"
admin_url="postgresql://shiftclarity_local@/postgres?host=/tmp&port=55478"
if configuration.exists():
    settings=Settings(**json.loads(configuration.read_text()))
else:
    settings=Settings(database_url="postgresql://shiftclarity_app:"+secrets.token_urlsafe(32)+"@127.0.0.1:55478/shiftclarity",
        issuer="http://127.0.0.1:5181/realms/shiftclarity",client_id="shiftclarity",
        client_secret=secrets.token_urlsafe(32),origin="http://127.0.0.1:5180",org_id="synthetic-pilot",
        storage_dir=str(local/"private"))
    configuration.write_text(json.dumps(settings.__dict__,indent=2))
    configuration.chmod(0o600)

with psycopg.connect(admin_url,autocommit=True) as db:
    if not db.execute("SELECT 1 FROM pg_database WHERE datname='shiftclarity'").fetchone():
        db.execute("CREATE DATABASE shiftclarity")
    if not db.execute("SELECT 1 FROM pg_roles WHERE rolname='shiftclarity_app'").fetchone():
        password=settings.database_url.split("shiftclarity_app:",1)[1].split("@",1)[0]
        db.execute(sql.SQL("CREATE ROLE shiftclarity_app LOGIN PASSWORD {} NOSUPERUSER NOBYPASSRLS").format(sql.Literal(password)))
    if not db.execute("SELECT 1 FROM pg_roles WHERE rolname='shiftclarity_maintenance'").fetchone():
        db.execute("CREATE ROLE shiftclarity_maintenance NOLOGIN")
admin_db=admin_url.replace("/postgres","/shiftclarity")
with psycopg.connect(admin_db) as db:
    migrate(db)
    db.execute("INSERT INTO organizations VALUES(%s,'Synthetic pilot workspace') ON CONFLICT DO NOTHING",(settings.org_id,))
    db.execute("INSERT INTO organizations VALUES('other-workspace','Isolation test workspace') ON CONFLICT DO NOTHING")
    fixture_dir=ROOT/"handoff/data/synthetic"
    files={"work":"work_records","invoices":"invoice_lines","rules":"rate_rules","batches":"import_batches","excerpts":"source_excerpts","manifest":"manifest"}
    inputs={k:json.loads((fixture_dir/(name+".json")).read_text()) for k,name in files.items()}
    inputs["manifest"]["workspace_label"]="Synthetic pilot workspace"
    draft=json.loads((fixture_dir/"draft_rule.json").read_text())
    seed(db,settings,inputs,draft)
    accounts_path=local/"accounts.json"
    if accounts_path.exists():
        accounts=json.loads(accounts_path.read_text())
    else:
        accounts=[]
        for username,actor,roles,org in [
            ("reviewer","DEMO-REVIEWER",["reviewer","importer"],settings.org_id),
            ("author","DEMO-AUTHOR",["author","approver"],settings.org_id),
            ("approver","DEMO-APPROVER",["approver"],settings.org_id),
            ("observer","DEMO-OBSERVER",[],settings.org_id),
            ("outsider","OTHER-REVIEWER",["reviewer","importer"],"other-workspace")]:
            accounts.append({"username":username,"actor":actor,"roles":roles,"org":org,"id":str(uuid.uuid4()),"password":secrets.token_urlsafe(20)})
        accounts_path.write_text(json.dumps(accounts,indent=2))
        accounts_path.chmod(0o600)
    for account in accounts:
        db.execute("INSERT INTO memberships VALUES(%s,%s,%s,%s,%s,true) ON CONFLICT DO NOTHING",
                   (settings.issuer,account["id"],account["org"],account["actor"],account["roles"]))

realm={
 "realm":"shiftclarity","enabled":True,"sslRequired":"none","registrationAllowed":False,
 "resetPasswordAllowed":False,"bruteForceProtected":True,"failureFactor":5,
 "otpPolicyType":"totp","otpPolicyAlgorithm":"HmacSHA1","otpPolicyDigits":6,"otpPolicyPeriod":30,
 "browserFlow":"pilot-browser","ssoSessionMaxLifespan":900,
 "authenticationFlows":[
  {"alias":"pilot-browser","providerId":"basic-flow","topLevel":True,"builtIn":False,"authenticationExecutions":[
   {"authenticator":"auth-cookie","requirement":"DISABLED","priority":10,"userSetupAllowed":False},
   {"flowAlias":"pilot-forms","requirement":"REQUIRED","priority":20,"authenticatorFlow":True,"userSetupAllowed":False}]},
  {"alias":"pilot-forms","providerId":"basic-flow","topLevel":False,"builtIn":False,"authenticationExecutions":[
   {"authenticator":"auth-username-password-form","authenticatorConfig":"pwd-reference","requirement":"REQUIRED","priority":10,"userSetupAllowed":False},
   {"authenticator":"auth-otp-form","authenticatorConfig":"otp-reference","requirement":"REQUIRED","priority":20,"userSetupAllowed":True}]}],
 "authenticatorConfig":[{"alias":"pwd-reference","config":{"default.reference.value":"pwd","default.reference.maxAge":"900"}},
                        {"alias":"otp-reference","config":{"default.reference.value":"otp","default.reference.maxAge":"900"}}],
 "clients":[{"clientId":settings.client_id,"secret":settings.client_secret,"enabled":True,"publicClient":False,
    "standardFlowEnabled":True,"directAccessGrantsEnabled":False,"fullScopeAllowed":False,
    "redirectUris":[settings.origin+"/auth/callback"],"webOrigins":[],
    "attributes":{"pkce.code.challenge.method":"S256","post.logout.redirect.uris":settings.origin+"/pilot/"},
    "protocolMappers":[{"name":"amr","protocol":"openid-connect","protocolMapper":"oidc-amr-mapper",
                       "config":{"id.token.claim":"true","access.token.claim":"true"}}]}],
 "users":[{"id":a["id"],"username":a["username"],"enabled":True,"emailVerified":True,"firstName":"Demo","lastName":a["username"],"email":a["username"]+"@example.invalid",
           "requiredActions":["CONFIGURE_TOTP"],"credentials":[{"type":"password","value":a["password"],"temporary":False}]} for a in accounts]
}
import_dir=local/"keycloak-26.8.0/data/import"
import_dir.mkdir(parents=True,exist_ok=True)
realm_file=import_dir/"shiftclarity-realm.json"
realm_file.write_text(json.dumps(realm,indent=2))
realm_file.chmod(0o600)
# Store a complete normalized, synthetic import template outside private credentials.
(ROOT/"artifacts").mkdir(exist_ok=True)
(ROOT/"artifacts/pilot-template.json").write_text(json.dumps(inputs,indent=2))
# Trust was limited to the dedicated bootstrapping server; subsequent connections require SCRAM.
pg_hba=local/"postgres/pg_hba.conf"
owner=pwd.getpwuid(os.getuid()).pw_name
(local/"postgres/pg_ident.conf").write_text('sc_owner "'+owner+'" shiftclarity_local\n')
pg_hba.write_text("local all shiftclarity_local peer map=sc_owner\nlocal all all scram-sha-256\nhost all all 127.0.0.1/32 scram-sha-256\n")
# Admin stays local socket only after initialization.
subprocess.run([str(Path(subprocess.check_output(["pg_config","--bindir"],text=True).strip())/"pg_ctl"),"-D",str(local/"postgres"),"reload"],check=True,capture_output=True)
print("Dedicated synthetic database and distinct identity accounts prepared. Credentials remain in .local/accounts.json.")
