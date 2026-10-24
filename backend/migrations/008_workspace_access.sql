CREATE TABLE agency_settings (
 org_id text PRIMARY KEY REFERENCES organizations,
 label text NOT NULL DEFAULT 'Synthetic pilot workspace', default_facility text NOT NULL DEFAULT 'FAC-A',
 version integer NOT NULL DEFAULT 1, updated_at timestamptz NOT NULL DEFAULT now()
);
INSERT INTO agency_settings(org_id) SELECT id FROM organizations;
ALTER TABLE agency_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE agency_settings FORCE ROW LEVEL SECURITY;
CREATE POLICY organization_boundary ON agency_settings USING(org_id=current_setting('app.org_id',true)) WITH CHECK(org_id=current_setting('app.org_id',true));
GRANT SELECT,INSERT,UPDATE ON agency_settings TO shiftclarity_app;
ALTER TABLE memberships ADD COLUMN version integer NOT NULL DEFAULT 1;
ALTER TABLE memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE memberships FORCE ROW LEVEL SECURITY;
-- Authentication must look up the verified issuer/subject before an organization is known.
CREATE POLICY identity_lookup ON memberships FOR SELECT USING(true);
CREATE POLICY scoped_member_insert ON memberships FOR INSERT WITH CHECK(org_id=current_setting('app.org_id',true));
CREATE POLICY scoped_member_update ON memberships FOR UPDATE USING(org_id=current_setting('app.org_id',true)) WITH CHECK(org_id=current_setting('app.org_id',true));
GRANT INSERT(issuer,subject,org_id,actor,roles,active) ON memberships TO shiftclarity_app;
GRANT UPDATE(roles,active,version) ON memberships TO shiftclarity_app;
