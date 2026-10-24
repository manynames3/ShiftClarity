ALTER TABLE memberships ADD COLUMN provider_username text CHECK(provider_username IS NULL OR length(provider_username) BETWEEN 1 AND 128);
CREATE FUNCTION protect_provider_username() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF OLD.provider_username IS NOT NULL AND NEW.provider_username IS DISTINCT FROM OLD.provider_username THEN
  RAISE EXCEPTION 'immutable provider username';
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER immutable_provider_username BEFORE UPDATE ON memberships FOR EACH ROW EXECUTE FUNCTION protect_provider_username();
GRANT INSERT(provider_username),UPDATE(provider_username) ON memberships TO shiftclarity_app;
