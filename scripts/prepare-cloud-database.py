"""Prepare only the isolated AWS synthetic branch and store its restricted URL in Secrets Manager."""
import json
import secrets
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit,urlencode,quote
import boto3
import certifi
import psycopg
from psycopg import sql
ROOT=Path(__file__).resolve().parent.parent
session=boto3.Session(region_name="us-east-1")
identity=session.client("sts").get_caller_identity()
assert identity["Account"]=="636305658578" and ":assumed-role/shiftclarity-deployer/" in identity["Arn"]
source=urlsplit(json.loads((ROOT/".local/neon-cloud-owner.json").read_text())["url"])
source=source._replace(netloc=source.netloc.replace(source.hostname,source.hostname.replace("-pooler","")))
metadata_file=ROOT/".local/neon-cloud-metadata.json"
if metadata_file.exists():
    metadata=json.loads(metadata_file.read_text())
    metadata["host"]=metadata["host"].replace("-pooler","")
    password=json.loads((ROOT/".local/neon-cloud-runtime.json").read_text())["password"]
else:
    password=secrets.token_urlsafe(32)
    metadata={"project_id":"lively-field-50384173","branch_id":"br-blue-butterfly-b7fv14zq","host":source.hostname}
    private=ROOT/".local/neon-cloud-runtime.json"
    private.write_text(json.dumps({"password":password}))
    private.chmod(0o600)
    metadata_file.write_text(json.dumps(metadata))
    metadata_file.chmod(0o600)
assert source.hostname==metadata["host"] and "-pooler" not in source.hostname
owner=urlunsplit((source.scheme,source.netloc,source.path,urlencode({"sslmode":"verify-full","sslrootcert":certifi.where()},quote_via=quote),""))
with psycopg.connect(owner) as db:
    assert db.execute("SELECT count(*) FROM organizations").fetchone()[0]==1
    assert db.execute("SELECT id FROM completed_runs").fetchall()==[("RUN-001",)]
    db.execute(sql.SQL("ALTER ROLE shiftclarity_app PASSWORD {}").format(sql.Literal(password)))
runtime=urlunsplit((source.scheme,"shiftclarity_app:"+quote(password,safe="")+"@"+source.hostname.replace(".c-13.","-pooler.c-13."),source.path,"sslmode=verify-full",""))
manager=session.client("secretsmanager")
name="shiftclarity-synthetic-database"
try:
    secret=manager.describe_secret(SecretId=name)
    manager.put_secret_value(SecretId=name,SecretString=runtime)
except manager.exceptions.ResourceNotFoundException:
    secret=manager.create_secret(Name=name,SecretString=runtime,Tags=[{"Key":"Product","Value":"ShiftClarity"},{"Key":"Environment","Value":"synthetic-pilot"}])
metadata["database_secret_arn"]=secret["ARN"]
metadata_file.write_text(json.dumps(metadata,indent=2))
with psycopg.connect(runtime,sslrootcert=certifi.where()) as db:
    assert db.execute("SELECT rolsuper OR rolbypassrls FROM pg_roles WHERE rolname=current_user").fetchone()==(False,)
print(json.dumps({**metadata,"verified_tls":True,"runtime_role":"shiftclarity_app"}))
