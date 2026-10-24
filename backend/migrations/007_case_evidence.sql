ALTER TABLE billing_cases ADD COLUMN evidence_hash text;
CREATE FUNCTION protect_case_identity() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF (NEW.org_id,NEW.id,NEW.case_key,NEW.kind,NEW.facility_id,NEW.service_from,NEW.service_to_exclusive,NEW.reason_code,NEW.created_at)
    IS DISTINCT FROM (OLD.org_id,OLD.id,OLD.case_key,OLD.kind,OLD.facility_id,OLD.service_from,OLD.service_to_exclusive,OLD.reason_code,OLD.created_at) THEN
  RAISE EXCEPTION 'immutable case identity';
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER immutable_case_identity BEFORE UPDATE ON billing_cases FOR EACH ROW EXECUTE FUNCTION protect_case_identity();
