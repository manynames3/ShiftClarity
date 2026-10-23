-- Runtime users may configure staged sources, never rewrite an accepted selection.
CREATE OR REPLACE FUNCTION protect_table_session() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_OP='DELETE' THEN
  IF OLD.status='accepted' THEN RAISE EXCEPTION 'immutable accepted source selection'; END IF;
  RETURN OLD;
 END IF;
 IF NEW.id<>OLD.id OR NEW.org_id<>OLD.org_id OR NEW.creator<>OLD.creator OR NEW.created_at<>OLD.created_at THEN
  RAISE EXCEPTION 'immutable source selection identity';
 END IF;
 IF OLD.status='accepted' THEN RAISE EXCEPTION 'immutable accepted source selection'; END IF;
 RETURN NEW;
END $$;
DROP TRIGGER immutable_table_session ON table_sessions;
CREATE TRIGGER immutable_table_session BEFORE UPDATE OR DELETE ON table_sessions FOR EACH ROW EXECUTE FUNCTION protect_table_session();
ALTER TABLE table_files ADD CONSTRAINT table_file_status CHECK(status IN ('quarantined','accepted','deleted'));
CREATE FUNCTION protect_table_file() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE is_owner boolean;
BEGIN
 SELECT tableowner=current_user INTO is_owner FROM pg_tables WHERE schemaname='public' AND tablename='table_files';
 IF TG_OP='DELETE' THEN
  IF OLD.status='accepted' AND NOT is_owner THEN RAISE EXCEPTION 'immutable accepted source file'; END IF;
  RETURN OLD;
 END IF;
 IF NEW.id<>OLD.id OR NEW.org_id<>OLD.org_id OR NEW.session_id<>OLD.session_id OR NEW.category<>OLD.category
    OR NEW.filename<>OLD.filename OR NEW.content_hash<>OLD.content_hash OR NEW.created_at<>OLD.created_at THEN
  RAISE EXCEPTION 'immutable original source identity';
 END IF;
 IF is_owner THEN RETURN NEW; END IF;
 IF OLD.status<>'quarantined' THEN RAISE EXCEPTION 'immutable accepted source file'; END IF;
 IF NEW.status<>'accepted' OR NEW.object_key<>replace(OLD.object_key,'/quarantine/','/accepted/')
    OR NEW.expires_at>now()+interval '30 days' OR NEW.expires_at<now()
    OR NOT EXISTS(SELECT 1 FROM table_sessions WHERE id=OLD.session_id AND status='approved') THEN
  RAISE EXCEPTION 'invalid source file acceptance';
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER immutable_table_file BEFORE UPDATE OR DELETE ON table_files FOR EACH ROW EXECUTE FUNCTION protect_table_file();
REVOKE UPDATE ON mapping_profiles FROM shiftclarity_app;
CREATE TRIGGER immutable_mapping_profile BEFORE UPDATE ON mapping_profiles FOR EACH ROW EXECUTE FUNCTION deny_mutation();
