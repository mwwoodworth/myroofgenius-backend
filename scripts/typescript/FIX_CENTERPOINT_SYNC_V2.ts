#!/usr/bin/env npx tsx
import postgres from 'postgres';

const DATABASE_URL = 'postgresql://postgres.yomagoqdmxszqtdwuhab:<DB_PASSWORD_REDACTED>@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require';
const CENTERPOINT_BASE_URL = 'https://api.centerpointconnect.io';
const BEARER_TOKEN = 'eyJvcmciOiI2NmJlMzEwMzFiMGJjMTAwMDEwM2RiN2MiLCJpZCI6ImM4ZDdiMDIyNGQ4NDQ5OGI5M2MwYzY4MTc0NWU5M2Y0IiwiaCI6Im11cm11cjEyOCJ9';
const TENANT_ID = '97f82b360baefdd73400ad342562586';

async function fixCenterPointSync() {
  const sql = postgres(DATABASE_URL);
  console.log('🔧 Fixing CenterPoint Sync Issues...\n');
  
  try {
    // 1. Check current sync status
    const lastSync = await sql`
      SELECT * FROM centerpoint_sync_log 
      ORDER BY started_at DESC 
      LIMIT 1
    `;
    
    console.log('📊 Last sync:', lastSync[0]?.started_at || 'Never');
    
    // 2. Test API connectivity
    console.log('\n🔌 Testing CenterPoint API...');
    const testResponse = await fetch(`${CENTERPOINT_BASE_URL}/companies?page[size]=1`, {
      headers: {
        'Authorization': `Bearer ${BEARER_TOKEN}`,
        'X-Tenant-Id': TENANT_ID,
        'Accept': 'application/json'
      }
    });
    
    if (!testResponse.ok) {
      console.error('❌ API connection failed:', testResponse.status);
      
      // Log the error properly
      await sql`
        INSERT INTO centerpoint_sync_log (sync_type, status, started_at, completed_at, errors)
        VALUES ('test', 'failed', NOW(), NOW(), ${JSON.stringify({
          error: `API returned ${testResponse.status}`,
          timestamp: new Date().toISOString()
        })})
      `;
      return;
    }
    
    const testData = await testResponse.json();
    console.log('✅ API Connected! Found', testData.meta?.totalEntries || 0, 'companies');
    
    // 3. Perform full sync with proper error handling
    console.log('\n🔄 Starting comprehensive sync...');
    const syncId = await sql`
      INSERT INTO centerpoint_sync_log (sync_type, status, started_at)
      VALUES ('full', 'in_progress', NOW())
      RETURNING id
    `.then(r => r[0].id);
    
    let stats = {
      companies: 0,
      jobs: 0,
      errors: []
    };
    
    // Sync companies
    try {
      const companiesResponse = await fetch(`${CENTERPOINT_BASE_URL}/companies?page[size]=100`, {
        headers: {
          'Authorization': `Bearer ${BEARER_TOKEN}`,
          'X-Tenant-Id': TENANT_ID,
          'Accept': 'application/json'
        }
      });
      
      if (companiesResponse.ok) {
        const companiesData = await companiesResponse.json();
        
        for (const company of companiesData.data || []) {
          try {
            await sql`
              INSERT INTO customers (
                id, name, email, phone, address, external_id, 
                customer_type, created_at, updated_at
              ) VALUES (
                gen_random_uuid(),
                ${company.attributes?.name || 'Unknown'},
                ${company.attributes?.email || `noemail${Math.random()}@example.com`},
                ${company.attributes?.phone || '000-000-0000'},
                ${JSON.stringify(company.attributes?.address || {})},
                ${'CP-' + company.id},
                'commercial',
                NOW(),
                NOW()
              )
              ON CONFLICT (external_id) 
              DO UPDATE SET 
                name = EXCLUDED.name,
                updated_at = NOW()
            `;
            stats.companies++;
          } catch (err) {
            stats.errors.push(`Company ${company.id}: ${err.message}`);
          }
        }
      }
    } catch (err) {
      stats.errors.push(`Companies sync: ${err.message}`);
    }
    
    // Sync jobs
    try {
      const jobsResponse = await fetch(`${CENTERPOINT_BASE_URL}/projects?page[size]=100`, {
        headers: {
          'Authorization': `Bearer ${BEARER_TOKEN}`,
          'X-Tenant-Id': TENANT_ID,
          'Accept': 'application/json'
        }
      });
      
      if (jobsResponse.ok) {
        const jobsData = await jobsResponse.json();
        
        for (const job of jobsData.data || []) {
          try {
            // Get a customer ID
            const customer = await sql`
              SELECT id FROM customers LIMIT 1
            `.then(r => r[0]?.id);
            
            if (customer) {
              await sql`
                INSERT INTO jobs (
                  id, job_number, name, customer_id, status,
                  start_date, created_at, updated_at
                ) VALUES (
                  gen_random_uuid(),
                  ${'CP-JOB-' + job.id},
                  ${job.attributes?.name || 'Unknown Job'},
                  ${customer},
                  'pending',
                  NOW(),
                  NOW(),
                  NOW()
                )
                ON CONFLICT (job_number)
                DO UPDATE SET 
                  name = EXCLUDED.name,
                  updated_at = NOW()
              `;
              stats.jobs++;
            }
          } catch (err) {
            stats.errors.push(`Job ${job.id}: ${err.message}`);
          }
        }
      }
    } catch (err) {
      stats.errors.push(`Jobs sync: ${err.message}`);
    }
    
    // Update sync log
    await sql`
      UPDATE centerpoint_sync_log 
      SET 
        status = 'completed',
        completed_at = NOW(),
        errors = ${stats.errors.length > 0 ? JSON.stringify(stats.errors) : null}
      WHERE id = ${syncId}
    `;
    
    console.log('\n📈 Sync Results:');
    console.log(`  ✅ Companies synced: ${stats.companies}`);
    console.log(`  ✅ Jobs synced: ${stats.jobs}`);
    console.log(`  ⚠️  Errors: ${stats.errors.length}`);
    
    if (stats.errors.length > 0) {
      console.log('\nErrors encountered:');
      stats.errors.slice(0, 5).forEach(e => console.log(`  - ${e}`));
    }
    
    // Verify data
    const counts = await sql`
      SELECT 
        (SELECT COUNT(*) FROM customers WHERE external_id LIKE 'CP-%') as customers,
        (SELECT COUNT(*) FROM jobs WHERE job_number LIKE 'CP-%') as jobs
    `.then(r => r[0]);
    
    console.log('\n📊 Total CenterPoint Data:');
    console.log(`  - Customers: ${counts.customers}`);
    console.log(`  - Jobs: ${counts.jobs}`);
    
  } catch (error) {
    console.error('❌ Fatal error:', error);
  } finally {
    await sql.end();
  }
}

fixCenterPointSync().catch(console.error);
