CREATE TABLE IF NOT EXISTS documents (
  org_id text NOT NULL REFERENCES organizations, id text NOT NULL,
  content jsonb NOT NULL, object_key text NOT NULL, content_hash text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY(org_id,id)
);
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents FORCE ROW LEVEL SECURITY;
CREATE POLICY organization_boundary ON documents
  USING(org_id=current_setting('app.org_id',true))
  WITH CHECK(org_id=current_setting('app.org_id',true));
CREATE TRIGGER immutable_document BEFORE UPDATE OR DELETE ON documents FOR EACH ROW EXECUTE FUNCTION deny_mutation();
GRANT SELECT,INSERT ON documents TO shiftclarity_app;
