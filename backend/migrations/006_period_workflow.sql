CREATE TABLE review_workspaces (
 org_id text NOT NULL REFERENCES organizations, run_id text NOT NULL,
 state jsonb NOT NULL, version integer NOT NULL DEFAULT 1,
 created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(org_id,run_id)
);
CREATE INDEX review_periods ON review_workspaces(org_id,created_at DESC,run_id);
CREATE TABLE billing_cases (
 org_id text NOT NULL REFERENCES organizations, id text NOT NULL DEFAULT ('CASE-'||gen_random_uuid()::text),
 case_key text NOT NULL, kind text NOT NULL CHECK(kind IN ('finding','coverage')),
 facility_id text NOT NULL, service_from text NOT NULL, service_to_exclusive text NOT NULL,
 reason_code text NOT NULL, work_ids jsonb NOT NULL, last_run_id text NOT NULL, source_ref text NOT NULL,
 amount numeric(18,2), status text NOT NULL DEFAULT 'open' CHECK(status IN ('open','awaiting_evidence','correction_recorded','evidence_recorded','resolved','dismissed')),
 owner text, correction_reference text, verified_run_id text,
 version integer NOT NULL DEFAULT 1, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(org_id,id), UNIQUE(org_id,case_key)
);
CREATE INDEX case_work_queue ON billing_cases(org_id,status,updated_at DESC,id);
CREATE TABLE case_events (
 org_id text NOT NULL, case_id text NOT NULL, sequence bigint GENERATED ALWAYS AS IDENTITY,
 actor text NOT NULL, action text NOT NULL, run_id text NOT NULL, data jsonb NOT NULL DEFAULT '{}',
 created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(org_id,sequence),
 FOREIGN KEY(org_id,case_id) REFERENCES billing_cases(org_id,id)
);
CREATE TRIGGER immutable_case_event BEFORE UPDATE OR DELETE ON case_events FOR EACH ROW EXECUTE FUNCTION deny_mutation();
CREATE FUNCTION protect_review_evidence() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NEW.org_id<>OLD.org_id OR NEW.run_id<>OLD.run_id OR NEW.created_at<>OLD.created_at
    OR NEW.state->'run' IS DISTINCT FROM OLD.state->'run' OR NEW.state->'inputs' IS DISTINCT FROM OLD.state->'inputs' THEN
  RAISE EXCEPTION 'immutable review evidence';
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER immutable_review_evidence BEFORE UPDATE ON review_workspaces FOR EACH ROW EXECUTE FUNCTION protect_review_evidence();
DO $$ DECLARE t text; BEGIN
 FOREACH t IN ARRAY ARRAY['review_workspaces','billing_cases','case_events'] LOOP
  EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY',t);
  EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY',t);
  EXECUTE format('CREATE POLICY organization_boundary ON %I USING (org_id=current_setting(''app.org_id'',true)) WITH CHECK (org_id=current_setting(''app.org_id'',true))',t);
 END LOOP;
END $$;
GRANT SELECT,INSERT,UPDATE ON review_workspaces,billing_cases TO shiftclarity_app;
GRANT SELECT,INSERT ON case_events TO shiftclarity_app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO shiftclarity_app;
