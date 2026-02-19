-- 20260219_brainops_neural_dynamics_rls_write_repair.sql
-- Purpose:
-- Repair write-path permissions for BrainOps neural dynamics tables used by
-- Hebbian learning and cluster updates.

BEGIN;

DO $$
DECLARE
    table_name text;
    policy_name text;
    target_tables text[] := ARRAY[
        'brainops_neurons',
        'brainops_synapses',
        'brainops_neural_clusters',
        'brainops_activation_history',
        'brainops_co_activations'
    ];
BEGIN
    FOREACH table_name IN ARRAY target_tables LOOP
        IF EXISTS (
            SELECT 1
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public'
              AND c.relname = table_name
              AND c.relkind = 'r'
        ) THEN
            EXECUTE format(
                'GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.%I TO app_backend_role, brainops_backend, app_agent_role, service_role',
                table_name
            );

            policy_name := format('backend_role_write_%s', table_name);
            IF NOT EXISTS (
                SELECT 1
                FROM pg_policies
                WHERE schemaname = 'public'
                  AND tablename = table_name
                  AND policyname = policy_name
            ) THEN
                EXECUTE format(
                    'CREATE POLICY %I ON public.%I FOR ALL TO app_backend_role, brainops_backend USING (true) WITH CHECK (true)',
                    policy_name,
                    table_name
                );
            END IF;
        END IF;
    END LOOP;
END $$;

COMMIT;
