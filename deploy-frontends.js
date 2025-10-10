#!/usr/bin/env node

/**
 * EMERGENCY FRONTEND DEPLOYMENT SCRIPT
 * 
 * This script handles the deployment of both frontend applications:
 * 1. MyRoofGenius - Customer-facing application
 * 2. BrainStackStudio - Internal management application
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🚀 EMERGENCY FRONTEND DEPLOYMENT SCRIPT');
console.log('=======================================\n');

const projects = [
  {
    name: 'MyRoofGenius',
    path: '/home/mwwoodworth/code/myroofgenius-app',
    domain: 'myroofgenius.vercel.app',
    envFile: '.env.production'
  },
  {
    name: 'BrainStackStudio', 
    path: '/home/mwwoodworth/code/brainstackstudio-app',
    domain: 'brainstackstudio.vercel.app',
    envFile: '.env.production'
  }
];

function runCommand(command, cwd = process.cwd()) {
  try {
    console.log(`Running: ${command}`);
    const output = execSync(command, { 
      cwd, 
      stdio: 'inherit',
      encoding: 'utf8'
    });
    return output;
  } catch (error) {
    console.error(`❌ Command failed: ${command}`);
    console.error(error.message);
    return false;
  }
}

function checkProject(project) {
  console.log(`\n🔍 Checking ${project.name}...`);
  
  // Check if directory exists
  if (!fs.existsSync(project.path)) {
    console.log(`❌ Project directory not found: ${project.path}`);
    return false;
  }
  
  // Check package.json
  const packageJsonPath = path.join(project.path, 'package.json');
  if (!fs.existsSync(packageJsonPath)) {
    console.log(`❌ package.json not found in ${project.path}`);
    return false;
  }
  
  // Check build script
  try {
    const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
    if (!packageJson.scripts?.build) {
      console.log(`❌ No build script found in ${project.name}`);
      return false;
    }
  } catch (error) {
    console.log(`❌ Error reading package.json: ${error.message}`);
    return false;
  }
  
  console.log(`✅ ${project.name} project structure OK`);
  return true;
}

function buildProject(project) {
  console.log(`\n🔨 Building ${project.name}...`);
  
  // Install dependencies if node_modules doesn't exist
  const nodeModulesPath = path.join(project.path, 'node_modules');
  if (!fs.existsSync(nodeModulesPath)) {
    console.log('Installing dependencies...');
    if (!runCommand('npm install', project.path)) {
      return false;
    }
  }
  
  // Run build
  if (!runCommand('npm run build', project.path)) {
    console.log(`❌ Build failed for ${project.name}`);
    return false;
  }
  
  console.log(`✅ ${project.name} built successfully`);
  return true;
}

function checkEnvironment(project) {
  console.log(`\n🔐 Checking environment for ${project.name}...`);
  
  const envPath = path.join(project.path, project.envFile);
  if (!fs.existsSync(envPath)) {
    console.log(`⚠️  Environment file not found: ${project.envFile}`);
    return false;
  }
  
  const envContent = fs.readFileSync(envPath, 'utf8');
  
  // Check for required variables based on project
  let requiredVars = [];
  
  if (project.name === 'MyRoofGenius') {
    requiredVars = [
      'NEXT_PUBLIC_SUPABASE_URL',
      'NEXT_PUBLIC_SUPABASE_ANON_KEY',
      'NEXT_PUBLIC_API_URL',
      'NEXTAUTH_URL',
      'NEXTAUTH_SECRET'
    ];
  } else if (project.name === 'BrainStackStudio') {
    requiredVars = [
      'NEXT_PUBLIC_API_URL'
    ];
  }
  
  const missingVars = requiredVars.filter(varName => 
    !envContent.includes(varName + '=')
  );
  
  if (missingVars.length > 0) {
    console.log(`⚠️  Missing environment variables: ${missingVars.join(', ')}`);
    return false;
  }
  
  console.log(`✅ ${project.name} environment configuration OK`);
  return true;
}

function createVercelConfig(project) {
  console.log(`\n⚙️  Creating Vercel config for ${project.name}...`);
  
  const vercelJsonPath = path.join(project.path, 'vercel.json');
  
  let vercelConfig = {
    "version": 2,
    "buildCommand": "npm run build",
    "outputDirectory": ".next",
    "installCommand": "npm install",
    "framework": "nextjs",
    "regions": ["iad1"],
    "functions": {
      "app/**/*.ts": {
        "maxDuration": 30
      },
      "pages/api/**/*.ts": {
        "maxDuration": 30
      }
    }
  };
  
  // MyRoofGenius specific config
  if (project.name === 'MyRoofGenius') {
    vercelConfig.env = {
      "NEXTAUTH_URL": "https://myroofgenius.vercel.app",
      "NODE_ENV": "production"
    };
    vercelConfig.functions = {
      "app/api/webhook/route.ts": {
        "maxDuration": 60
      },
      "app/api/**/*.ts": {
        "maxDuration": 30
      }
    };
  }
  
  fs.writeFileSync(vercelJsonPath, JSON.stringify(vercelConfig, null, 2));
  console.log(`✅ Vercel config created for ${project.name}`);
}

// Main execution
async function main() {
  console.log('🔍 Checking projects...\n');
  
  for (const project of projects) {
    console.log(`\n${'='.repeat(50)}`);
    console.log(`📁 ${project.name.toUpperCase()}`);
    console.log(`${'='.repeat(50)}`);
    
    // Check project structure
    if (!checkProject(project)) {
      console.log(`❌ Skipping ${project.name} due to issues`);
      continue;
    }
    
    // Check environment
    checkEnvironment(project);
    
    // Create Vercel config
    createVercelConfig(project);
    
    // Build project
    if (!buildProject(project)) {
      console.log(`❌ Failed to build ${project.name}`);
      continue;
    }
    
    console.log(`✅ ${project.name} is ready for deployment!`);
  }
  
  console.log('\n🎉 DEPLOYMENT CHECK COMPLETE!\n');
  console.log('Next steps:');
  console.log('1. Commit and push changes to your repositories');
  console.log('2. Deploy to Vercel using:');
  console.log('   - vercel --prod (from each project directory)');
  console.log('   - Or connect to Vercel dashboard for automatic deployments');
  console.log('\n📋 Deployment URLs:');
  projects.forEach(project => {
    console.log(`   - ${project.name}: https://${project.domain}`);
  });
}

main().catch(console.error);