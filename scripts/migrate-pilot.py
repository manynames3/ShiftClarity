"""Explicit owner-side bootstrap for an approved synthetic cloud environment."""
import argparse
import json
import os
import sys
from pathlib import Path
import psycopg
from psycopg import sql
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from backend.config import ROOT,load_settings
from backend.bootstrap import migrate,seed
parser=argparse.ArgumentParser()
parser.add_argument("--memberships",required=True,help="Reviewed issuer/subject/actor/roles mappings from the identity service.")
args=parser.parse_args()
settings=load_settings()
members=json.loads(Path(args.memberships).read_text())
with psycopg.connect(os.environ["ADMIN_DATABASE_URL"]) as db:
    if not db.execute("SELECT 1 FROM pg_roles WHERE rolname='shiftclarity_app'").fetchone():
        password=os.environ["RUNTIME_DATABASE_PASSWORD"]
        db.execute(sql.SQL("CREATE ROLE shiftclarity_app LOGIN PASSWORD {} NOSUPERUSER NOBYPASSRLS").format(sql.Literal(password)))
    migrate(db)
    fixture=ROOT/"handoff/data/synthetic"
    names={"work":"work_records","invoices":"invoice_lines","rules":"rate_rules","batches":"import_batches","excerpts":"source_excerpts","manifest":"manifest"}
    inputs={key:json.loads((fixture/(name+".json")).read_text()) for key,name in names.items()}
    inputs["manifest"]["workspace_label"]="Synthetic pilot workspace"
    seed(db,settings,inputs,json.loads((fixture/"draft_rule.json").read_text()))
    allowed={"author","approver","reviewer","importer"}
    for member in members:
        if set(member)!={"subject","actor","roles"} or not set(member["roles"])<=allowed:
            raise ValueError("Invalid membership mapping")
        db.execute("INSERT INTO memberships VALUES(%s,%s,%s,%s,%s,true) ON CONFLICT DO NOTHING",
                   (settings.issuer,member["subject"],settings.org_id,member["actor"],member["roles"]))
print("Synthetic schema and reviewed memberships initialized. No customer data was imported.")
