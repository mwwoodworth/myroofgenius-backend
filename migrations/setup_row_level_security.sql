-- ============================================================================
-- Row Level Security (RLS) Setup for WeatherCraft ERP
-- Implements multi-tenant data isolation and access control
-- ============================================================================

-- Enable RLS on critical tables
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE estimates ENABLE ROW LEVEL SECURITY;
ALTER TABLE employees ENABLE ROW LEVEL SECURITY;
ALTER TABLE timesheets ENABLE ROW LEVEL SECURITY;
ALTER TABLE materials ENABLE ROW LEVEL SECURITY;
ALTER TABLE equipment ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- CREATE SECURITY POLICIES
-- ============================================================================

-- Customers: Users can only see customers they have permission for
CREATE POLICY customers_select_policy ON customers
    FOR SELECT
    USING (
        -- Admins see all
        EXISTS (
            SELECT 1 FROM users
            WHERE id = current_setting('app.current_user_id')::uuid
            AND role IN ('admin', 'superadmin')
        )
        OR
        -- Users see customers assigned to them
        EXISTS (
            SELECT 1 FROM user_customers uc
            WHERE uc.customer_id = customers.id
            AND uc.user_id = current_setting('app.current_user_id')::uuid
        )
        OR
        -- Employees see customers for their assigned jobs
        EXISTS (
            SELECT 1 FROM jobs j
            JOIN employee_jobs ej ON j.id = ej.job_id
            WHERE j.customer_id = customers.id
            AND ej.employee_id = current_setting('app.current_user_id')::uuid
        )
    );

CREATE POLICY customers_insert_policy ON customers
    FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM users
            WHERE id = current_setting('app.current_user_id')::uuid
            AND role IN ('admin', 'superadmin', 'manager')
        )
    );

CREATE POLICY customers_update_policy ON customers
    FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM users
            WHERE id = current_setting('app.current_user_id')::uuid
            AND role IN ('admin', 'superadmin', 'manager')
        )
        OR
        EXISTS (
            SELECT 1 FROM user_customers uc
            WHERE uc.customer_id = customers.id
            AND uc.user_id = current_setting('app.current_user_id')::uuid
            AND uc.can_edit = true
        )
    );

-- Jobs: Similar pattern for jobs
CREATE POLICY jobs_select_policy ON jobs
    FOR SELECT
    USING (
        -- Admins and managers see all
        EXISTS (
            SELECT 1 FROM users
            WHERE id = current_setting('app.current_user_id')::uuid
            AND role IN ('admin', 'superadmin', 'manager')
        )
        OR
        -- Employees see their assigned jobs
        EXISTS (
            SELECT 1 FROM employee_jobs ej
            WHERE ej.job_id = jobs.id
            AND ej.employee_id = current_setting('app.current_user_id')::uuid
        )
        OR
        -- Crew members see their crew's jobs
        EXISTS (
            SELECT 1 FROM crew_jobs cj
            JOIN crew_members cm ON cj.crew_id = cm.crew_id
            WHERE cj.job_id = jobs.id
            AND cm.employee_id = current_setting('app.current_user_id')::uuid
        )
    );

-- Invoices: Financial data protection
CREATE POLICY invoices_select_policy ON invoices
    FOR SELECT
    USING (
        -- Only admins and finance roles
        EXISTS (
            SELECT 1 FROM users
            WHERE id = current_setting('app.current_user_id')::uuid
            AND role IN ('admin', 'superadmin', 'finance', 'manager')
        )
        OR
        -- Customers can see their own invoices
        EXISTS (
            SELECT 1 FROM customers c
            WHERE c.id = invoices.customer_id
            AND c.user_id = current_setting('app.current_user_id')::uuid
        )
    );

-- Timesheets: Employees see only their own
CREATE POLICY timesheets_select_policy ON timesheets
    FOR SELECT
    USING (
        -- Admins and managers see all
        EXISTS (
            SELECT 1 FROM users
            WHERE id = current_setting('app.current_user_id')::uuid
            AND role IN ('admin', 'superadmin', 'manager', 'hr')
        )
        OR
        -- Employees see their own
        employee_id = current_setting('app.current_user_id')::uuid
        OR
        -- Supervisors see their team's
        EXISTS (
            SELECT 1 FROM employees e
            WHERE e.id = timesheets.employee_id
            AND e.supervisor_id = current_setting('app.current_user_id')::uuid
        )
    );

CREATE POLICY timesheets_insert_policy ON timesheets
    FOR INSERT
    WITH CHECK (
        -- Can only insert own timesheet or if manager
        employee_id = current_setting('app.current_user_id')::uuid
        OR
        EXISTS (
            SELECT 1 FROM users
            WHERE id = current_setting('app.current_user_id')::uuid
            AND role IN ('admin', 'manager', 'hr')
        )
    );

-- ============================================================================
-- HELPER TABLES FOR PERMISSIONS
-- ============================================================================

-- User-Customer associations
CREATE TABLE IF NOT EXISTS user_customers (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    can_view BOOLEAN DEFAULT true,
    can_edit BOOLEAN DEFAULT false,
    can_delete BOOLEAN DEFAULT false,
    assigned_at TIMESTAMP DEFAULT NOW(),
    assigned_by UUID REFERENCES users(id),
    UNIQUE(user_id, customer_id)
);

-- Employee-Job assignments
CREATE TABLE IF NOT EXISTS employee_jobs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'worker',
    assigned_at TIMESTAMP DEFAULT NOW(),
    assigned_by UUID REFERENCES users(id),
    UNIQUE(employee_id, job_id)
);

-- Crew-Job assignments
CREATE TABLE IF NOT EXISTS crew_jobs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    crew_id UUID NOT NULL REFERENCES crews(id) ON DELETE CASCADE,
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT NOW(),
    assigned_by UUID REFERENCES users(id),
    UNIQUE(crew_id, job_id)
);

-- Crew members
CREATE TABLE IF NOT EXISTS crew_members (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    crew_id UUID NOT NULL REFERENCES crews(id) ON DELETE CASCADE,
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'member',
    joined_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(crew_id, employee_id)
);

-- ============================================================================
-- AUDIT LOG FOR RLS BYPASSES
-- ============================================================================

CREATE TABLE IF NOT EXISTS rls_audit_log (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    operation VARCHAR(20) NOT NULL,
    record_id UUID,
    reason TEXT,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- FUNCTIONS FOR RLS
-- ============================================================================

-- Function to set current user context
CREATE OR REPLACE FUNCTION set_current_user_id(user_id UUID)
RETURNS VOID AS $$
BEGIN
    PERFORM set_config('app.current_user_id', user_id::text, false);
END;
$$ LANGUAGE plpgsql;

-- Function to get current user role
CREATE OR REPLACE FUNCTION get_current_user_role()
RETURNS VARCHAR AS $$
DECLARE
    user_role VARCHAR;
BEGIN
    SELECT role INTO user_role
    FROM users
    WHERE id = current_setting('app.current_user_id')::uuid;

    RETURN COALESCE(user_role, 'guest');
END;
$$ LANGUAGE plpgsql;

-- Function to check if user has permission
CREATE OR REPLACE FUNCTION user_has_permission(
    required_role VARCHAR,
    resource_type VARCHAR DEFAULT NULL,
    resource_id UUID DEFAULT NULL
)
RETURNS BOOLEAN AS $$
DECLARE
    user_role VARCHAR;
    has_access BOOLEAN DEFAULT FALSE;
BEGIN
    -- Get user role
    SELECT role INTO user_role
    FROM users
    WHERE id = current_setting('app.current_user_id', true)::uuid;

    -- Check role hierarchy
    IF user_role IN ('superadmin') THEN
        RETURN TRUE;
    ELSIF user_role = 'admin' AND required_role NOT IN ('superadmin') THEN
        RETURN TRUE;
    ELSIF user_role = 'manager' AND required_role IN ('staff', 'user') THEN
        RETURN TRUE;
    ELSIF user_role = required_role THEN
        -- Check specific resource permissions if provided
        IF resource_type IS NOT NULL AND resource_id IS NOT NULL THEN
            -- Custom resource checks here
            RETURN TRUE; -- Simplified for now
        ELSE
            RETURN TRUE;
        END IF;
    END IF;

    RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_user_customers_user_id ON user_customers(user_id);
CREATE INDEX IF NOT EXISTS idx_user_customers_customer_id ON user_customers(customer_id);
CREATE INDEX IF NOT EXISTS idx_employee_jobs_employee_id ON employee_jobs(employee_id);
CREATE INDEX IF NOT EXISTS idx_employee_jobs_job_id ON employee_jobs(job_id);
CREATE INDEX IF NOT EXISTS idx_crew_jobs_crew_id ON crew_jobs(crew_id);
CREATE INDEX IF NOT EXISTS idx_crew_jobs_job_id ON crew_jobs(job_id);
CREATE INDEX IF NOT EXISTS idx_crew_members_crew_id ON crew_members(crew_id);
CREATE INDEX IF NOT EXISTS idx_crew_members_employee_id ON crew_members(employee_id);
CREATE INDEX IF NOT EXISTS idx_rls_audit_log_user_id ON rls_audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_rls_audit_log_created_at ON rls_audit_log(created_at);

-- ============================================================================
-- GRANT PERMISSIONS
-- ============================================================================

GRANT USAGE ON SCHEMA public TO authenticated;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT INSERT, UPDATE, DELETE ON customers, jobs, invoices, estimates TO authenticated;
GRANT INSERT ON rls_audit_log TO authenticated;

-- ============================================================================
-- NOTES
-- ============================================================================
-- To use RLS in application:
-- 1. Call set_current_user_id() at beginning of each request
-- 2. RLS will automatically filter results based on policies
-- 3. Use SECURITY DEFINER functions for admin operations that bypass RLS
-- 4. Monitor rls_audit_log for any security events