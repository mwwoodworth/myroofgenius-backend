#!/usr/bin/env node

const { createClient } = require('@supabase/supabase-js');

// Your Supabase credentials
const supabaseUrl = 'https://yomagoqdmxszqtdwuhab.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlvbWFnb3FkbXhzenF0ZHd1aGFiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk4MzMyNzYsImV4cCI6MjA2NTQwOTI3Nn0.bxlLdnJ1YKYUNlIulSO2E6iM4wyUSrPFtNcONg-vwPY';
const supabaseServiceKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlvbWFnb3FkbXhzenF0ZHd1aGFiIiwicm9sZSI6InNlcnZpY2Vfc3JvbGUiLCJpYXQiOjE3NDk4MzMyNzYsImV4cCI6MjA2NTQwOTI3Nn0.7C3guJ_0moYGkdyeFmJ9cd2BmduB5NnU00erIIxH3gQ';

async function testConnection() {
  console.log('Testing Supabase connection...\n');

  // Test with anon key
  console.log('1. Testing with anon key...');
  const supabaseAnon = createClient(supabaseUrl, supabaseAnonKey);
  
  try {
    const { data, error } = await supabaseAnon.from('app_users').select('id').limit(1);
    if (error) {
      console.log('❌ Anon key test failed:', error.message);
    } else {
      console.log('✅ Anon key works!');
    }
  } catch (e) {
    console.log('❌ Anon key error:', e.message);
  }

  // Test with service key
  console.log('\n2. Testing with service role key...');
  const supabaseService = createClient(supabaseUrl, supabaseServiceKey);
  
  try {
    const { data, error } = await supabaseService.from('app_users').select('id').limit(1);
    if (error) {
      console.log('❌ Service role key test failed:', error.message);
    } else {
      console.log('✅ Service role key works!');
    }
  } catch (e) {
    console.log('❌ Service role key error:', e.message);
  }

  // Test database connection URL
  console.log('\n3. Testing database connection...');
  const dbUrl = 'postgresql://postgres:Brain0ps2O2S@db.yomagoqdmxszqtdwuhab.supabase.co:5432/postgres';
  console.log('Database URL:', dbUrl.replace('Brain0ps2O2S', '***'));
  
  // Test memory system tables
  console.log('\n4. Testing memory system tables...');
  try {
    const tables = [
      'persistent_memory',
      'task_completions',
      'automation_logs',
      'error_logs',
      'memory_associations',
      'memory_templates',
      'memory_search_index',
      'memory_insights',
      'memory_versions',
      'memory_sync'
    ];

    for (const table of tables) {
      const { data, error } = await supabaseService
        .from(table)
        .select('*')
        .limit(1);
      
      if (error) {
        console.log(`❌ ${table}: ${error.message}`);
      } else {
        console.log(`✅ ${table}: accessible`);
      }
    }
  } catch (e) {
    console.log('❌ Memory tables error:', e.message);
  }

  console.log('\n✅ Supabase connection test complete!');
}

// Run the test
testConnection();