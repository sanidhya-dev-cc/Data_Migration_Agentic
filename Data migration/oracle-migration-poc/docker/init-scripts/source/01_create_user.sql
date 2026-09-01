-- Source DB user creation
-- gvenzl/oracle-xe automatically creates APP_USER in XEPDB1 via environment variables.
-- This file is intentionally left as a no-op placeholder;
-- user creation is handled by APP_USER / APP_USER_PASSWORD env vars.
SELECT 'migration_user created via APP_USER env var' AS STATUS FROM DUAL;
