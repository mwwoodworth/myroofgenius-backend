-- RUN THIS TO GET COMPLETE SYSTEM CONTEXT
-- No assumptions, no placeholders, just FACTS

-- 1. Quick Status Check
SELECT * FROM get_brainops_status() WHERE NOT is_correct;

-- 2. System Architecture
SELECT component_name, version, status, health_check_url 
FROM brainops_system_architecture;

-- 3. Critical Facts
SELECT fact_category, fact_key, fact_value, confidence_level 
FROM brainops_operational_facts 
WHERE is_verified = true
ORDER BY fact_category, fact_key;

-- 4. Data Reality Check
SELECT 
    'app_users' as table_name, COUNT(*) as actual_count, '2 test users' as notes
FROM app_users
UNION ALL
SELECT 'customers', COUNT(*), 'ONLY 3 - not 1089!' FROM customers
UNION ALL
SELECT 'jobs', COUNT(*), 'ONLY 3' FROM jobs
UNION ALL
SELECT 'invoices', COUNT(*), 'EMPTY - needs data' FROM invoices
UNION ALL
SELECT 'estimates', COUNT(*), 'EMPTY - needs data' FROM estimates
UNION ALL
SELECT 'products', COUNT(*), '12 products exist' FROM products
UNION ALL
SELECT 'automations', COUNT(*), '8 exist but not running' FROM automations
UNION ALL
SELECT 'automation_executions', COUNT(*), 'Only 5 ever!' FROM automation_executions;

-- 5. Integration Status
SELECT integration_name, is_active, 
       CASE WHEN is_active THEN '✓' ELSE '✗ NEEDS FIX' END as status
FROM brainops_integrations
ORDER BY is_active DESC, integration_name;

-- 6. Environment Variables
SELECT env_key, 
       CASE WHEN is_set_in_production THEN '✓ SET' ELSE '✗ MISSING' END as production_status,
       service
FROM brainops_env_master
WHERE is_required = true
ORDER BY is_set_in_production DESC, env_key;

-- 7. What Needs Fixing
SELECT check_item, current_value, expected_value, action_needed
FROM get_brainops_status() 
WHERE NOT is_correct;