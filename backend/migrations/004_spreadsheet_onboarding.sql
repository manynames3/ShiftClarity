CREATE TABLE table_sessions (
 id text PRIMARY KEY, org_id text NOT NULL REFERENCES organizations, creator text NOT NULL,
 status text NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','validated','approved','accepted')),
 data jsonb NOT NULL, version integer NOT NULL DEFAULT 1,
 import_id text REFERENCES imports, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE table_files (
 id text PRIMARY KEY, org_id text NOT NULL REFERENCES organizations, session_id text NOT NULL REFERENCES table_sessions,
 category text NOT NULL CHECK(category IN ('rates','work','invoices')), filename text NOT NULL,
 content_hash text NOT NULL, object_key text NOT NULL, status text NOT NULL DEFAULT 'quarantined',
 created_at timestamptz NOT NULL DEFAULT now(),
 expires_at timestamptz NOT NULL DEFAULT now()+interval '1 day',
 UNIQUE(org_id,session_id,category,content_hash)
);
CREATE TABLE mapping_profiles (
 id text PRIMARY KEY, org_id text NOT NULL REFERENCES organizations, name text NOT NULL,
 category text NOT NULL, config jsonb NOT NULL, headers jsonb NOT NULL,
 version integer NOT NULL DEFAULT 1, verified_by text NOT NULL, created_at timestamptz NOT NULL DEFAULT now()
);
DO $$ DECLARE t text; BEGIN
 FOREACH t IN ARRAY ARRAY['table_sessions','table_files','mapping_profiles'] LOOP
  EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY',t);
  EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY',t);
  EXECUTE format('CREATE POLICY organization_boundary ON %I USING (org_id=current_setting(''app.org_id'',true)) WITH CHECK (org_id=current_setting(''app.org_id'',true))',t);
 END LOOP;
END $$;
CREATE FUNCTION protect_table_session() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF OLD.status='accepted' THEN RAISE EXCEPTION 'immutable accepted source selection'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER immutable_table_session BEFORE UPDATE ON table_sessions FOR EACH ROW EXECUTE FUNCTION protect_table_session();
GRANT SELECT,INSERT,UPDATE,DELETE ON table_sessions,table_files,mapping_profiles TO shiftclarity_app;
