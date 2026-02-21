const fetch = require('node-fetch');

async function testMyRoofAPI() {
  console.log('Testing MyRoofGenius API endpoints...\n');

  const baseUrl = 'http://localhost:3001';
  
  // Test API endpoints
  const endpoints = [
    '/api/auth/session',
    '/api/memory/recent',
    '/api/memory/task-completion',
    '/api/memory/error-log'
  ];

  for (const endpoint of endpoints) {
    try {
      const response = await fetch(`${baseUrl}${endpoint}`);
      console.log(`${endpoint}: ${response.status} ${response.status < 400 ? '✅' : '❌'}`);
      
      if (response.status === 200) {
        const data = await response.json();
        console.log(`   Response: ${JSON.stringify(data).substring(0, 100)}...`);
      }
    } catch (error) {
      console.log(`${endpoint}: ❌ Error - ${error.message}`);
    }
  }

  // Test Supabase integration
  console.log('\n2. Testing Supabase integration...');
  try {
    const response = await fetch(`${baseUrl}/api/test/supabase`);
    console.log(`   Status: ${response.status}`);
    if (response.status === 200) {
      const data = await response.json();
      console.log(`   ✅ Supabase connected: ${data.connected}`);
    }
  } catch (error) {
    console.log(`   ❌ Error: ${error.message}`);
  }

  console.log('\n✅ MyRoofGenius API test complete!');
}

testMyRoofAPI();