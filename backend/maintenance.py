"""Privileged retention operation. Never reachable through the application API."""
import argparse
import os
import psycopg
from psycopg import sql
from .config import load_settings
from .storage import PrivateStorage

def expire_sources(settings,admin_url):
    storage=PrivateStorage(settings)
    # Acceptance locks its session before source rows; keep that order here too.
    # Tombstones commit before deletion, retaining object references for retries.
    with psycopg.connect(admin_url) as db:
        sessions=db.execute("SELECT id FROM table_sessions WHERE org_id=%s AND ((status!='accepted' AND created_at<=now()-interval '1 day') OR EXISTS(SELECT 1 FROM table_files WHERE session_id=table_sessions.id AND expires_at<=now())) ORDER BY id FOR UPDATE",(settings.org_id,)).fetchall()
        identifiers=[row[0] for row in sessions]
        files=db.execute("SELECT id,object_key FROM table_files WHERE org_id=%s AND session_id=ANY(%s) AND (expires_at<=now() OR session_id IN (SELECT id FROM table_sessions WHERE status!='accepted' AND created_at<=now()-interval '1 day')) FOR UPDATE",(settings.org_id,identifiers)).fetchall()
        for identifier,key in files:db.execute("UPDATE table_files SET status='deleted' WHERE id=%s",(identifier,))
        rows=db.execute("SELECT id,object_key FROM imports WHERE org_id=%s AND expires_at<=now() FOR UPDATE",(settings.org_id,)).fetchall()
        for identifier,key in rows:db.execute("UPDATE imports SET status='deleted',normalized=NULL WHERE id=%s",(identifier,))
        db.execute("INSERT INTO audit_events(org_id,actor,action,resource) VALUES(%s,'RETENTION-ADMIN','expired_sources_disabled',%s)",(settings.org_id,settings.org_id))
    for identifier,key in [*files,*rows]:storage.delete(key)
    # Remove abandoned previews only after their private bytes were removed.
    with psycopg.connect(admin_url) as db:
        expired=db.execute("SELECT id FROM table_sessions WHERE org_id=%s AND status!='accepted' AND created_at<=now()-interval '1 day' ORDER BY id FOR UPDATE",(settings.org_id,)).fetchall()
        for (identifier,) in expired:
            if db.execute("SELECT 1 FROM table_files WHERE session_id=%s AND status!='deleted'",(identifier,)).fetchone():continue
            db.execute('DELETE FROM table_files WHERE session_id=%s',(identifier,))
            db.execute('DELETE FROM table_sessions WHERE id=%s',(identifier,))
    return len(rows)+len(files)

def purge_workspace(settings,admin_url,confirmation):
    if confirmation!=settings.org_id:
        raise ValueError("Exact organization confirmation required")
    storage=PrivateStorage(settings)
    with psycopg.connect(admin_url) as db:
        # The immutable controls remain enforced for the runtime role. This operation
        # requires the database owner and a recorded, explicit retention decision.
        db.execute("LOCK TABLE workspace_heads,imports,jobs,completed_runs,rule_versions,source_revisions,audit_events,table_sessions,table_files,mapping_profiles,review_workspaces,billing_cases,case_events,agency_settings IN ACCESS EXCLUSIVE MODE")
        objects=db.execute("SELECT object_key FROM imports WHERE org_id=%s UNION SELECT object_key FROM documents WHERE org_id=%s UNION SELECT object_key FROM table_files WHERE org_id=%s",(settings.org_id,settings.org_id,settings.org_id)).fetchall()
        for table,trigger in [("case_events","immutable_case_event"),("completed_runs","immutable_run"),("rule_versions","immutable_rule"),("source_revisions","immutable_source"),("documents","immutable_document"),("table_sessions","immutable_table_session")]:
            db.execute(sql.SQL("ALTER TABLE {} DISABLE TRIGGER {}").format(sql.Identifier(table),sql.Identifier(trigger)))
        for table in ["case_events","billing_cases","review_workspaces","agency_settings","table_files","table_sessions","mapping_profiles","write_receipts","completed_runs","jobs","source_lineage","source_revisions","rule_versions","documents","imports","workspace_heads"]:
            db.execute(sql.SQL("DELETE FROM {} WHERE org_id=%s").format(sql.Identifier(table)),(settings.org_id,))
        db.execute("DELETE FROM sessions WHERE (issuer,subject) IN (SELECT issuer,subject FROM memberships WHERE org_id=%s)",(settings.org_id,))
        db.execute("UPDATE memberships SET active=false WHERE org_id=%s",(settings.org_id,))
        db.execute("INSERT INTO audit_events(org_id,actor,action,resource) VALUES(%s,'RETENTION-ADMIN','workspace_purged',%s)",(settings.org_id,settings.org_id))
        for table,trigger in [("case_events","immutable_case_event"),("completed_runs","immutable_run"),("rule_versions","immutable_rule"),("source_revisions","immutable_source"),("documents","immutable_document"),("table_sessions","immutable_table_session")]:
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
