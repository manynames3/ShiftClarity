CREATE FUNCTION protect_import_snapshot() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE is_owner boolean;
BEGIN
  SELECT tableowner=current_user INTO is_owner FROM pg_tables WHERE schemaname='public' AND tablename='imports';
  IF NEW.id<>OLD.id OR NEW.org_id<>OLD.org_id OR NEW.request_key<>OLD.request_key
     OR NEW.content_hash<>OLD.content_hash OR NEW.created_at<>OLD.created_at THEN
    RAISE EXCEPTION 'immutable import identity';
  END IF;
  IF OLD.status='validated' THEN
    IF NEW.status='deleted' AND NEW.normalized IS NULL AND is_owner THEN RETURN NEW; END IF;
    IF NEW.status<>OLD.status OR NEW.normalized IS DISTINCT FROM OLD.normalized OR NEW.object_key<>OLD.object_key
       OR (NEW.expires_at<>OLD.expires_at AND NOT is_owner) THEN
      RAISE EXCEPTION 'immutable accepted import';
    END IF;
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER immutable_import BEFORE UPDATE ON imports FOR EACH ROW EXECUTE FUNCTION protect_import_snapshot();
