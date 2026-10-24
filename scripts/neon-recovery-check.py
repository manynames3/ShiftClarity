"""Restore the authorized synthetic Neon branch into a dedicated local rehearsal DB."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import argparse
from pathlib import Path
from urllib.parse import urlsplit,parse_qsl,unquote
import certifi
import psycopg
from psycopg import sql
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from backend.config import ROOT,Settings
from backend.storage import PrivateStorage

parser=argparse.ArgumentParser()
parser.add_argument("--cloud",action="store_true",help="Restore the authorized AWS synthetic branch and private S3 sources.")
args=parser.parse_args()
label="aws" if args.cloud else "neon"
settings=Settings(**json.loads((ROOT/(".local/aws-cloud-config.json" if args.cloud else ".local/neon-app-config.json")).read_text()))
parsed=urlsplit(json.loads((ROOT/(".local/neon-cloud-owner.json" if args.cloud else ".local/neon-app-owner.json")).read_text())["url"])
parsed=parsed._replace(netloc=parsed.netloc.replace("-pooler",""))
expected=json.loads((ROOT/".local/neon-cloud-metadata.json").read_text())["host"] if args.cloud else "ep-spring-paper-b7mh5woh.c-13.us-east-1.aws.neon.tech"
if parsed.hostname!=expected:
    raise ValueError("Not the authorized synthetic application branch")
admin="postgresql://shiftclarity_local@/postgres?host=/tmp&port=55478"
restore_database="shiftclarity_aws_restore" if args.cloud else "shiftclarity_neon_restore"
target=admin.replace("/postgres","/"+restore_database)
bindir=Path(subprocess.check_output(["pg_config","--bindir"],text=True).strip())
service=ROOT/(".local/"+label+"-recovery.pg_service.conf")
service.write_text("\n".join([
    "[sc_neon_recovery]","host="+parsed.hostname,"dbname=shiftclarity",
    "user="+unquote(parsed.username),"password="+unquote(parsed.password),
    "sslmode=verify-full","sslrootcert="+certifi.where(),
])+"\n")
service.chmod(0o600)
environment=os.environ.copy()
environment["PGSERVICEFILE"]=str(service)
os.environ["PGSERVICEFILE"]=str(service)
backup=ROOT/(".local/"+label+"-synthetic-recovery.dump")
tables=["imports","source_revisions","source_lineage","documents","rule_versions","jobs","completed_runs","workspace_heads","audit_events","write_receipts"]
if args.cloud:tables.extend(["organizations","memberships"])
with psycopg.connect("service=sc_neon_recovery") as db:
    tables.extend(table for table in ["table_sessions","table_files","mapping_profiles"]
                  if db.execute("SELECT to_regclass(%s)",(table,)).fetchone()[0])
def snapshot(connection):
    connection.execute("SET TIME ZONE 'UTC'")
    result={}
    for table in tables:
        rows=connection.execute(sql.SQL("SELECT row_to_json(t)::text FROM {} t").format(sql.Identifier(table))).fetchall()
        result[table]=sorted(row[0] for row in rows)
    return hashlib.sha256(json.dumps(result,sort_keys=True).encode()).hexdigest(),{k:len(v) for k,v in result.items()}

started=time.monotonic()
subprocess.run([str(bindir/"pg_dump"),"--format=custom","--schema=public","--no-owner","--no-acl","--file",str(backup),"service=sc_neon_recovery"],env=environment,check=True,capture_output=True)
backup.chmod(0o600)
with psycopg.connect(admin,autocommit=True) as db:
    if db.execute("SELECT 1 FROM pg_database WHERE datname=%s",(restore_database,)).fetchone():
        db.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(restore_database)))
    db.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(restore_database)))
with psycopg.connect(target) as db:
    db.execute("DROP SCHEMA public")
subprocess.run([str(bindir/"pg_restore"),"--no-owner","--no-acl","--dbname",target,str(backup)],check=True,capture_output=True)
with psycopg.connect("service=sc_neon_recovery") as db:
    source_hash,counts=snapshot(db)
    object_query="SELECT object_key FROM imports WHERE status='validated' UNION SELECT object_key FROM documents"
    if "table_files" in tables:
        object_query+=" UNION SELECT object_key FROM table_files WHERE status IN ('quarantined','accepted') AND expires_at>now()"
    objects=[row[0] for row in db.execute(object_query).fetchall()]
with psycopg.connect(target) as db:
    restored_hash,_=snapshot(db)
assert source_hash==restored_hash,"Neon snapshot restore differs"
restored=ROOT/(".local/"+label+"-restored-sources")
storage=PrivateStorage(settings)
for key in objects:
    source=storage.get(key)
    destination=restored/key
    destination.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    destination.write_bytes(source)
    destination.chmod(0o600)
    assert hashlib.sha256(source).digest()==hashlib.sha256(destination.read_bytes()).digest()
result={"scope":"authorized synthetic "+("AWS/Neon/S3" if args.cloud else "Neon local application")+" branch to isolated local restore","result":"matched",
        "project_id":"lively-field-50384173","branch_id":"br-blue-butterfly-b7fv14zq" if args.cloud else "br-holy-block-b75wbmjb","tables":counts,
        "sha256":source_hash,"private_sources_restored":len(objects),"elapsed_seconds":round(time.monotonic()-started,3),
        "rpo_rto":"No production service target inferred"}
(ROOT/("artifacts/"+label+"-recovery.json")).write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
