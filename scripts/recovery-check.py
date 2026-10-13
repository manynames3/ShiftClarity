"""Back up and restore only the synthetic test DB; compare durable business records."""
import hashlib
import json
import subprocess
import sys
import time
import shutil
import argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import psycopg
from psycopg import sql
from backend.config import ROOT

ADMIN="postgresql://shiftclarity_local@/postgres?host=/tmp&port=55478"
SOURCE=ADMIN.replace("/postgres","/shiftclarity_test")
TARGET=ADMIN.replace("/postgres","/shiftclarity_restore_check")
BINDIR=Path("/opt/homebrew/opt/postgresql@17/bin")
backup=ROOT/".local/synthetic-recovery.dump"
parser=argparse.ArgumentParser()
parser.add_argument("--storage-dir",required=True)
args=parser.parse_args()
tables=["imports","source_revisions","source_lineage","documents","rule_versions","jobs","completed_runs","workspace_heads","audit_events","write_receipts"]
def snapshot(url):
    with psycopg.connect(url) as db:
        data={}
        for table in tables:
            rows=db.execute(sql.SQL("SELECT row_to_json(t)::text FROM {} t").format(sql.Identifier(table))).fetchall()
            data[table]=sorted(row[0] for row in rows)
        return hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest(),{k:len(v) for k,v in data.items()}
start=time.monotonic()
with psycopg.connect(SOURCE) as db:
    keys=[row[0] for row in db.execute("SELECT object_key FROM imports WHERE status='validated' UNION SELECT object_key FROM documents").fetchall()]
object_backup=ROOT/".local/recovery-object-backup"
restored_objects=ROOT/".local/restored-objects"
object_hashes={}
for key in keys:
    source_file=Path(args.storage_dir)/key
    saved=object_backup/key
    saved.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    shutil.copy2(source_file,saved)
    object_hashes[key]=hashlib.sha256(source_file.read_bytes()).hexdigest()
subprocess.run([str(BINDIR/"pg_dump"),"--format=custom","--file",str(backup),SOURCE],check=True,capture_output=True)
backup.chmod(0o600)
with psycopg.connect(ADMIN,autocommit=True) as db:
    if db.execute("SELECT 1 FROM pg_database WHERE datname='shiftclarity_restore_check'").fetchone():
        db.execute("DROP DATABASE shiftclarity_restore_check")
    db.execute("CREATE DATABASE shiftclarity_restore_check")
subprocess.run([str(BINDIR/"pg_restore"),"--dbname",TARGET,str(backup)],check=True,capture_output=True)
source,counts=snapshot(SOURCE)
restored,_=snapshot(TARGET)
assert restored==source,"Restored business data or lineage differs"
for key,hashed in object_hashes.items():
    restored_file=restored_objects/key
    restored_file.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    shutil.copy2(object_backup/key,restored_file)
    assert hashlib.sha256(restored_file.read_bytes()).hexdigest()==hashed
result={"scope":"synthetic local test database only","result":"matched","tables":counts,"sha256":source,
        "private_sources_restored":len(object_hashes),
        "elapsed_seconds":round(time.monotonic()-start,3),"rpo_rto":"No service target inferred from this rehearsal"}
(ROOT/"artifacts/pilot-recovery.json").write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
