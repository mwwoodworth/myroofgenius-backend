-- =============================================================================
-- RELATIONSHIP AWARENESS VIEWS (Schema-Corrected)
-- =============================================================================

-- Complete customer view with all relationships
CREATE OR REPLACE VIEW customer_complete_view AS
SELECT
    c.*,
    COUNT(DISTINCT j.id) as total_jobs,
    COUNT(DISTINCT e.id) as total_estimates,
    COUNT(DISTINCT i.id) as total_invoices,
    COALESCE(SUM(i.total_amount), 0) as lifetime_value,
    COALESCE(SUM(p.amount), 0) as total_payments,
    COALESCE(SUM(i.total_amount) - SUM(p.amount), 0) as balance_due,
    MAX(j.completed_at) as last_job_date,
    COUNT(DISTINCT comm.id) FILTER (WHERE comm.entity_type = 'customer') as total_communications
FROM customers c
LEFT JOIN jobs j ON c.id = j.customer_id
LEFT JOIN estimates e ON c.id = e.customer_id
LEFT JOIN invoices i ON c.id = i.customer_id
LEFT JOIN payments p ON c.id = p.customer_id
LEFT JOIN communications comm ON c.id = comm.entity_id AND comm.entity_type = 'customer'
GROUP BY c.id;

-- Complete job view with all relationships
CREATE OR REPLACE VIEW job_complete_view AS
SELECT
    j.*,
    c.name as customer_name,
    COUNT(DISTINCT ja.employee_id) as crew_size,
    COUNT(DISTINCT je.equipment_id) as equipment_count,
    COUNT(DISTINCT jm.material_id) as material_count,
    COALESCE(SUM(t.total_hours), 0) as total_labor_hours,
    COALESCE(SUM(jm.quantity * jm.unit_price), 0) as total_material_cost
FROM jobs j
LEFT JOIN customers c ON j.customer_id = c.id
LEFT JOIN job_assignments ja ON j.id = ja.job_id
LEFT JOIN job_equipment je ON j.id = je.job_id
LEFT JOIN job_materials jm ON j.id = jm.job_id
LEFT JOIN timesheets t ON j.id = t.job_id
GROUP BY j.id, c.name;

-- Complete employee view with all relationships
CREATE OR REPLACE VIEW employee_complete_view AS
SELECT
    e.*,
    hr.employment_status,
    hr.employee_type,
    hr.hire_date,
    COUNT(DISTINCT ja.job_id) as total_jobs_assigned,
    COUNT(DISTINCT c.id) as total_certifications,
    COUNT(DISTINCT tr.id) as total_training_completed,
    COALESCE(SUM(t.total_hours), 0) as total_hours_worked
FROM employees e
LEFT JOIN hr_records hr ON e.id = hr.employee_id
LEFT JOIN job_assignments ja ON e.id = ja.employee_id
LEFT JOIN certifications c ON e.id = c.employee_id
LEFT JOIN training_records tr ON e.id = tr.employee_id
LEFT JOIN timesheets t ON e.id = t.employee_id
GROUP BY e.id, hr.employment_status, hr.employee_type, hr.hire_date;

-- Grant access
GRANT SELECT ON customer_complete_view TO postgres;
GRANT SELECT ON job_complete_view TO postgres;
GRANT SELECT ON employee_complete_view TO postgres;

COMMENT ON VIEW customer_complete_view IS 'Complete customer view with all relationships and computed fields';
COMMENT ON VIEW job_complete_view IS 'Complete job view with crew, equipment, materials, and labor tracking';
COMMENT ON VIEW employee_complete_view IS 'Complete employee view with assignments, certifications, and hours';
