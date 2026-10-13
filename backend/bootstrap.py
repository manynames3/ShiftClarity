"""Owner-only migration and synthetic seeding; never called by an HTTP request."""
import json
import uuid
from psycopg.types.json import Jsonb
from psycopg import sql
from .config import ROOT
from .engine import compute,digest
from .storage import PrivateStorage

def seed(db,settings,inputs,draft):
    state=compute("seed",inputs=inputs,draft=draft)
    org=settings.org_id
    db.execute("INSERT INTO organizations VALUES(%s,'Synthetic pilot workspace') ON CONFLICT DO NOTHING",(org,))
    db.execute("INSERT INTO workspace_heads(org_id,state) VALUES(%s,%s) ON CONFLICT DO NOTHING",(org,Jsonb(state)))
    for rule in inputs["rules"]:
        db.execute("INSERT INTO rule_versions VALUES(%s,%s,%s) ON CONFLICT DO NOTHING",(org,rule["id"],Jsonb(rule)))
    for excerpt in inputs["excerpts"]:
        if not db.execute("SELECT 1 FROM documents WHERE org_id=%s AND id=%s",(org,excerpt["document_id"])).fetchone():
            key=org+"/accepted/"+uuid.uuid4().hex
            PrivateStorage(settings).put(key,json.dumps(excerpt).encode())
            db.execute("INSERT INTO documents(org_id,id,content,object_key,content_hash) VALUES(%s,%s,%s,%s,%s)",
                       (org,excerpt["document_id"],Jsonb(excerpt),key,digest(excerpt)))
    if not db.execute("SELECT 1 FROM completed_runs WHERE org_id=%s AND id=%s",(org,state["run"]["id"])).fetchone():
        identifier="IMP-"+uuid.uuid4().hex
        data=json.dumps(inputs).encode()
        key=org+"/accepted/"+uuid.uuid4().hex
        PrivateStorage(settings).put(key,data)
        db.execute("INSERT INTO imports(id,org_id,request_key,content_hash,object_key,status,normalized) VALUES(%s,%s,'synthetic-seed',%s,%s,'validated',%s)",
                   (identifier,org,digest(data),key,Jsonb(inputs)))
        for kind in ("work","invoices"):
            for row in inputs[kind]:
                record={k:v for k,v in row.items() if k!="batch_id"}
                revision=row["source_revision"] if kind=="work" else digest(record)
                db.execute("INSERT INTO source_revisions VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                           (org,kind,row["id"],revision,digest(record),Jsonb(record)))
                db.execute("INSERT INTO source_lineage VALUES(%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                           (org,identifier,kind,row["id"],revision))
        db.execute("INSERT INTO completed_runs(org_id,id,import_id,snapshot) VALUES(%s,%s,%s,%s)",
                   (org,state["run"]["id"],identifier,Jsonb(state)))
        db.execute("INSERT INTO audit_events(org_id,actor,action,resource) VALUES(%s,'SYNTHETIC-SEED','workspace_seeded',%s)",(org,state["run"]["id"]))

def migrate(db):
    if not db.execute("SELECT to_regclass('public.organizations')").fetchone()[0]:
        db.execute((ROOT/"backend/migrations/001_initial.sql").read_text())
    if not db.execute("SELECT to_regclass('public.documents')").fetchone()[0]:
        db.execute((ROOT/"backend/migrations/002_documents.sql").read_text())
    if not db.execute("SELECT 1 FROM pg_trigger WHERE tgname='immutable_import'").fetchone():
        db.execute((ROOT/"backend/migrations/003_import_immutability.sql").read_text())
    db.execute(sql.SQL("GRANT CONNECT ON DATABASE {} TO shiftclarity_app").format(sql.Identifier(db.info.dbname)))
    db.execute("GRANT USAGE ON SCHEMA public TO shiftclarity_app")
    db.execute("GRANT SELECT ON ALL TABLES IN SCHEMA public TO shiftclarity_app")
    db.execute("GRANT INSERT ON imports,source_revisions,source_lineage,rule_versions,jobs,completed_runs,audit_events,write_receipts,sessions,auth_flows TO shiftclarity_app")
    db.execute("GRANT UPDATE ON workspace_heads,imports,jobs TO shiftclarity_app")
    db.execute("GRANT DELETE ON sessions,auth_flows TO shiftclarity_app")
    db.execute("GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO shiftclarity_app")
