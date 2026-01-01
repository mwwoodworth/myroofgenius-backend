
\echo '========== DATABASE ANALYSIS REPORT =========='
\echo ''

\echo '--- 1. TABLE ROW COUNTS (Top 50) ---'
SELECT schemaname, relname as table_name, n_live_tup as row_count 
FROM pg_stat_user_tables 
WHERE schemaname = 'public'
ORDER BY n_live_tup DESC
LIMIT 50;

\echo ''
\echo '--- 2. CORE TABLE SCHEMAS ---'
\echo '[CUSTOMERS]'
\d customers
\echo '[JOBS]'
\d jobs
\echo '[INVOICES]'
\d invoices
\echo '[ESTIMATES]'
\d estimates
\echo '[USERS (public)]'
\d users
\echo '[TENANTS]'
\d tenants

\echo ''
\echo '--- 3. FOREIGN KEY RELATIONSHIPS (Sample) ---'
SELECT
    tc.table_name, kcu.column_name, ccu.table_name AS foreign_table_name, ccu.column_name AS foreign_column_name
FROM
    information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
      AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
      AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public'
ORDER BY tc.table_name, kcu.column_name
LIMIT 50;

\echo ''
\echo '--- 4. TABLES WITHOUT RLS (Security Risk) ---'
SELECT tablename 
FROM pg_tables 
WHERE schemaname = 'public' AND rowsecurity = false
ORDER BY tablename;

\echo ''
\echo '--- 5. ORPHAN RECORDS CHECK (Rows with NULL tenant_id) ---'
DO $$
DECLARE
    r record;
    cnt bigint;
BEGIN
    FOR r IN SELECT table_name FROM information_schema.columns WHERE table_schema = 'public' AND column_name = 'tenant_id'
    LOOP
        EXECUTE format('SELECT count(*) FROM %I WHERE tenant_id IS NULL', r.table_name) INTO cnt;
        IF cnt > 0 THEN
            RAISE NOTICE 'ALERT: Table % has % records with NULL tenant_id', r.table_name, cnt;
        END IF;
    END LOOP;
END $$;

\echo ''
\echo '--- 6. UNINDEXED FOREIGN KEYS (Performance Risk) ---'
SELECT
    c.conrelid::regclass AS table_name,
    a.attname AS column_name
FROM pg_constraint c
JOIN pg_attribute a ON a.attnum = ANY(c.conkey) AND a.attrelid = c.conrelid
WHERE c.contype = 'f'
AND NOT EXISTS (
    SELECT 1 FROM pg_index i
    WHERE i.indrelid = c.conrelid
    AND a.attnum = ANY(i.indkey)
)
AND c.connamespace::regnamespace::text = 'public'
ORDER BY table_name;
