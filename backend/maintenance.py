"""Privileged retention operation. Never reachable through the application API."""
import argparse
import os
import psycopg
from psycopg import sql
from .config import load_settings
from .storage import PrivateStorage

def expire_sources(settings,admin_url):
    storage=PrivateStorage(settings)
    with psycopg.connect(admin_url) as db:
        rows=db.execute("SELECT id,object_key FROM imports WHERE org_id=%s AND expires_at<=now() AND status!='deleted'",
                        (settings.org_id,)).fetchall()
        for identifier,key in rows:
            storage.delete(key)
            db.execute("UPDATE imports SET status='deleted',normalized=NULL WHERE id=%s",(identifier,))
    return len(rows)

def purge_workspace(settings,admin_url,confirmation):
    if confirmation!=settings.org_id:
        raise ValueError("Exact organization confirmation required")
    storage=PrivateStorage(settings)
    with psycopg.connect(admin_url) as db:
        # The immutable controls remain enforced for the runtime role. This operation
        # requires the database owner and a recorded, explicit retention decision.
        db.execute("LOCK TABLE workspace_heads,imports,jobs,completed_runs,rule_versions,source_revisions,audit_events IN ACCESS EXCLUSIVE MODE")
        objects=db.execute("SELECT object_key FROM imports WHERE org_id=%s UNION SELECT object_key FROM documents WHERE org_id=%s",(settings.org_id,settings.org_id)).fetchall()
        for table,trigger in [("completed_runs","immutable_run"),("rule_versions","immutable_rule"),("source_revisions","immutable_source"),("documents","immutable_document")]:
            db.execute(sql.SQL("ALTER TABLE {} DISABLE TRIGGER {}").format(sql.Identifier(table),sql.Identifier(trigger)))
        for table in ["write_receipts","completed_runs","jobs","source_lineage","source_revisions","rule_versions","documents","imports","workspace_heads"]:
            db.execute(sql.SQL("DELETE FROM {} WHERE org_id=%s").format(sql.Identifier(table)),(settings.org_id,))
        db.execute("DELETE FROM sessions WHERE (issuer,subject) IN (SELECT issuer,subject FROM memberships WHERE org_id=%s)",(settings.org_id,))
        db.execute("UPDATE memberships SET active=false WHERE org_id=%s",(settings.org_id,))
        db.execute("INSERT INTO audit_events(org_id,actor,action,resource) VALUES(%s,'RETENTION-ADMIN','workspace_purged',%s)",(settings.org_id,settings.org_id))
        for table,trigger in [("completed_runs","immutable_run"),("rule_versions","immutable_rule"),("source_revisions","immutable_source"),("documents","immutable_document")]:
            db.execute(sql.SQL("ALTER TABLE {} ENABLE TRIGGER {}").format(sql.Identifier(table),sql.Identifier(trigger)))
        for (key,) in objects:
            storage.delete(key)
    return len(objects)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("action",choices=["expire-sources","purge-workspace"])
    parser.add_argument("--confirm-organization")
    args=parser.parse_args()
    settings=load_settings()
    url=os.environ["ADMIN_DATABASE_URL"]
    count=expire_sources(settings,url) if args.action=="expire-sources" else purge_workspace(settings,url,args.confirm_organization)
    print(f"Retention operation completed for {count} source objects.")
