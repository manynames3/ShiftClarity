"""Initialize private synthetic sources and provider-verified individual test memberships."""
import json
import secrets
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit,urlencode,quote
import boto3
import certifi
import psycopg
ROOT=Path(__file__).resolve().parent.parent
session=boto3.Session(region_name="us-east-1")
identity=session.client("sts").get_caller_identity()
assert identity["Account"]=="636305658578" and ":assumed-role/shiftclarity-deployer/" in identity["Arn"]
outputs=json.loads((ROOT/".local/aws-outputs.json").read_text())
values={key:value["value"] for key,value in outputs.items()}
metadata=json.loads((ROOT/".local/neon-cloud-metadata.json").read_text())
owner=urlsplit(json.loads((ROOT/".local/neon-cloud-owner.json").read_text())["url"])
owner=owner._replace(netloc=owner.netloc.replace(owner.hostname,owner.hostname.replace("-pooler","")),
                     query=urlencode({"sslmode":"verify-full","sslrootcert":certifi.where()},quote_via=quote))
assert owner.hostname==metadata["host"]
runtime=session.client("secretsmanager").get_secret_value(SecretId=metadata["database_secret_arn"])["SecretString"]
pool=values["cognito_pool"]
provider=session.client("cognito-idp")
client=provider.describe_user_pool_client(UserPoolId=pool,ClientId=values["cognito_client"])["UserPoolClient"]
issuer="https://cognito-idp.us-east-1.amazonaws.com/"+pool
accounts_file=ROOT/".local/aws-accounts.json"
if accounts_file.exists():
    accounts=json.loads(accounts_file.read_text())
else:
    accounts=[{"username":name,"password":"Sc!9"+secrets.token_urlsafe(28),"actor":actor,"roles":roles}
              for name,actor,roles in [("reviewer","DEMO-REVIEWER",["reviewer","importer"]),
                                      ("author","DEMO-AUTHOR",["author","approver"]),
                                      ("approver","DEMO-APPROVER",["approver"]),
                                      ("observer","DEMO-OBSERVER",[]),("outsider","UNASSIGNED-ACCOUNT",[])]]
    accounts_file.write_text(json.dumps(accounts,indent=2))
    accounts_file.chmod(0o600)
for account in accounts:
    try:
        user=provider.admin_get_user(UserPoolId=pool,Username=account["username"])
    except provider.exceptions.UserNotFoundException:
        provider.admin_create_user(UserPoolId=pool,Username=account["username"],MessageAction="SUPPRESS")
        provider.admin_set_user_password(UserPoolId=pool,Username=account["username"],Password=account["password"],Permanent=True)
        user=provider.admin_get_user(UserPoolId=pool,Username=account["username"])
    account["subject"]=next(attribute["Value"] for attribute in user["UserAttributes"] if attribute["Name"]=="sub")
accounts_file.write_text(json.dumps(accounts,indent=2))
base=json.loads((ROOT/".local/neon-base-config.json").read_text())
storage=Path(base["storage_dir"])
s3=session.client("s3")
with psycopg.connect(urlunsplit(owner)) as db:
    assert db.execute("SELECT count(*) FROM organizations").fetchone()[0]==1
    keys=[row[0] for row in db.execute("SELECT object_key FROM imports WHERE status='validated' UNION SELECT object_key FROM documents")]
    for key in keys:
        assert key.startswith("synthetic-pilot/accepted/")
        data=(storage/key).read_bytes()
        s3.put_object(Bucket=values["private_bucket"],Key=key,Body=data,ContentType="application/json",ServerSideEncryption="AES256")
        actual=s3.get_object(Bucket=values["private_bucket"],Key=key)["Body"].read()
        assert actual==data
    # The cloned base contained only local test identities. Keep the cloud branch isolated.
    db.execute("DELETE FROM sessions WHERE issuer<>%s",(issuer,))
    db.execute("DELETE FROM auth_flows")
    db.execute("DELETE FROM memberships WHERE issuer<>%s",(issuer,))
    for account in accounts:
        if account["username"]=="outsider":
            continue
        db.execute("INSERT INTO memberships VALUES(%s,%s,'synthetic-pilot',%s,%s,true) ON CONFLICT DO NOTHING",
                   (issuer,account["subject"],account["actor"],account["roles"]))
configuration={"database_url":runtime,"issuer":issuer,"client_id":values["cognito_client"],"client_secret":client["ClientSecret"],
               "origin":values["app_origin"],"org_id":"synthetic-pilot","storage_dir":"/tmp/unused","cloud":True,
               "bucket":values["private_bucket"],"region":"us-east-1","cognito_pool":pool,"worker_enabled":False,
               "job_queue_url":values["job_queue"],"job_queue_arn":values["job_queue_arn"]}
variables=json.loads((ROOT/".local/aws.tfvars.json").read_text())
if variables.get("public_origin"):
    configuration.update(gateway_host=values["gateway_origin"].split("://",1)[1],edge_proxy_secret=variables["edge_proxy_secret"])
config_file=ROOT/".local/aws-cloud-config.json"
config_file.write_text(json.dumps(configuration,indent=2))
config_file.chmod(0o600)
evidence={"account":identity["Account"],"deployment_role":identity["Arn"],"origin":values["app_origin"],
          "cognito_pool":pool,"private_bucket":values["private_bucket"],"sources_verified":len(keys),
          "individual_memberships":4,"unassigned_account":True,"neon_branch":metadata["branch_id"],"data_mode":"synthetic"}
(ROOT/"artifacts/aws-initialization.json").write_text(json.dumps(evidence,indent=2))
print(json.dumps(evidence))
