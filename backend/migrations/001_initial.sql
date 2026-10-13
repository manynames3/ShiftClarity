CREATE TABLE organizations (id text PRIMARY KEY, label text NOT NULL);
CREATE TABLE memberships (
  issuer text NOT NULL, subject text NOT NULL, org_id text NOT NULL REFERENCES organizations,
  actor text NOT NULL, roles text[] NOT NULL, active boolean NOT NULL DEFAULT true,
  PRIMARY KEY(issuer,subject), UNIQUE(org_id,actor)
);
CREATE TABLE sessions (
  digest text PRIMARY KEY, issuer text NOT NULL, subject text NOT NULL,
  csrf text NOT NULL, expires_at timestamptz NOT NULL,
  FOREIGN KEY(issuer,subject) REFERENCES memberships(issuer,subject)
);
CREATE TABLE auth_flows (
  digest text PRIMARY KEY, data jsonb NOT NULL, expires_at timestamptz NOT NULL
);
CREATE TABLE workspace_heads (
  org_id text PRIMARY KEY REFERENCES organizations, state jsonb NOT NULL, version integer NOT NULL DEFAULT 1
);
CREATE TABLE imports (
  id text PRIMARY KEY, org_id text NOT NULL REFERENCES organizations,
  request_key text NOT NULL, content_hash text NOT NULL, object_key text NOT NULL,
  status text NOT NULL CHECK(status IN ('quarantined','validated','failed','deleted')),
  diagnostic text, normalized jsonb, created_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz NOT NULL DEFAULT now() + interval '30 days',
  UNIQUE(org_id,request_key), UNIQUE(org_id,content_hash)
);
CREATE TABLE source_revisions (
  org_id text NOT NULL REFERENCES organizations, kind text NOT NULL, external_id text NOT NULL,
  revision text NOT NULL, content_hash text NOT NULL, record jsonb NOT NULL,
  PRIMARY KEY(org_id,kind,external_id,revision)
);
CREATE TABLE source_lineage (
  org_id text NOT NULL, import_id text NOT NULL REFERENCES imports,
  kind text NOT NULL, external_id text NOT NULL, revision text NOT NULL,
  PRIMARY KEY(import_id,kind,external_id,revision),
  FOREIGN KEY(org_id,kind,external_id,revision) REFERENCES source_revisions(org_id,kind,external_id,revision)
);
CREATE TABLE rule_versions (
  org_id text NOT NULL REFERENCES organizations, id text NOT NULL, content jsonb NOT NULL,
  PRIMARY KEY(org_id,id)
);
CREATE TABLE jobs (
  id text PRIMARY KEY, org_id text NOT NULL REFERENCES organizations, request_key text NOT NULL,
  import_id text NOT NULL REFERENCES imports, actor text NOT NULL,
  status text NOT NULL CHECK(status IN ('queued','reconciling','completed','failed')),
  attempts integer NOT NULL DEFAULT 0, available_at timestamptz NOT NULL DEFAULT now(),
  lease_until timestamptz, lease_token text, diagnostic text, created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(org_id,request_key)
);
CREATE TABLE completed_runs (
  org_id text NOT NULL REFERENCES organizations, id text NOT NULL, import_id text NOT NULL REFERENCES imports,
  snapshot jsonb NOT NULL, published_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY(org_id,id)
);
CREATE TABLE audit_events (
  sequence bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  org_id text NOT NULL REFERENCES organizations, actor text NOT NULL,
  action text NOT NULL, resource text NOT NULL, metadata jsonb NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE write_receipts (
  org_id text NOT NULL REFERENCES organizations, actor text NOT NULL, request_key text NOT NULL,
  request_hash text NOT NULL, response jsonb NOT NULL,
  PRIMARY KEY(org_id,actor,request_key)
);
CREATE FUNCTION deny_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'immutable record'; END $$;
CREATE TRIGGER immutable_run BEFORE UPDATE OR DELETE ON completed_runs FOR EACH ROW EXECUTE FUNCTION deny_mutation();
CREATE TRIGGER immutable_rule BEFORE UPDATE OR DELETE ON rule_versions FOR EACH ROW EXECUTE FUNCTION deny_mutation();
CREATE TRIGGER immutable_source BEFORE UPDATE OR DELETE ON source_revisions FOR EACH ROW EXECUTE FUNCTION deny_mutation();
CREATE TRIGGER immutable_audit BEFORE UPDATE OR DELETE ON audit_events FOR EACH ROW EXECUTE FUNCTION deny_mutation();
-- The runtime login must be a nonowner, non-superuser, without BYPASSRLS.
DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY['workspace_heads','imports','source_revisions','source_lineage','rule_versions','jobs','completed_runs','audit_events','write_receipts'] LOOP
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY',t);
    EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY',t);
    EXECUTE format('CREATE POLICY organization_boundary ON %I USING (org_id = current_setting(''app.org_id'',true)) WITH CHECK (org_id = current_setting(''app.org_id'',true))',t);
  END LOOP;
END $$;
