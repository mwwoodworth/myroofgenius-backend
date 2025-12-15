#!/usr/bin/env python3
"""
Complete Notion Setup with Manual Instructions
Since API access requires proper integration setup, this provides a complete guide
"""

import json
import os
from datetime import datetime

def create_notion_import_file():
    """Create a JSON file that can be imported into Notion"""
    
    workspace_data = {
        "workspace_name": "BrainOps Master Command Center",
        "created_at": datetime.now().isoformat(),
        "system_status": {
            "version": "v30.3.0",
            "operational": "73.9%",
            "endpoints_passing": "17/23"
        },
        "sections": {
            "active_tasks": {
                "title": "🎯 Active Tasks Dashboard",
                "tasks": [
                    {
                        "task": "Fix remaining API endpoints (Products, Lead Scoring, Workflows)",
                        "status": "In Progress",
                        "priority": "🔴 Critical",
                        "assigned_to": "AI Agent",
                        "progress": "75%",
                        "notes": "v30.4.0 deployment pending"
                    },
                    {
                        "task": "Create Stripe products in dashboard",
                        "status": "Not Started",
                        "priority": "🔴 Critical",
                        "assigned_to": "Human",
                        "progress": "0%",
                        "notes": "AI Estimate ($99), Consultation ($299), Maintenance ($199/mo)"
                    },
                    {
                        "task": "Configure SendGrid API key",
                        "status": "Not Started",
                        "priority": "🟡 High",
                        "assigned_to": "Human",
                        "progress": "0%",
                        "notes": "Required for email automation"
                    }
                ]
            },
            "credentials": {
                "title": "🔐 Credentials Vault",
                "items": [
                    {
                        "service": "Supabase Database",
                        "username": "postgres",
                        "password": "<DB_PASSWORD_REDACTED>",
                        "url": "https://supabase.com/dashboard/project/yomagoqdmxszqtdwuhab",
                        "category": "Database",
                        "status": "Active"
                    },
                    {
                        "service": "Docker Hub",
                        "username": "mwwoodworth",
                        "token": "dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho",
                        "url": "https://hub.docker.com",
                        "category": "Deployment",
                        "status": "Active"
                    },
                    {
                        "service": "Render",
                        "api_key": "rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx",
                        "url": "https://dashboard.render.com",
                        "category": "Deployment",
                        "status": "Active"
                    },
                    {
                        "service": "GitHub",
                        "username": "mwwoodworth",
                        "url": "https://github.com/mwwoodworth",
                        "category": "Version Control",
                        "status": "Active"
                    },
                    {
                        "service": "Stripe",
                        "api_key": "<STRIPE_KEY_REDACTED>",
                        "url": "https://dashboard.stripe.com",
                        "category": "Payment",
                        "status": "Active"
                    },
                    {
                        "service": "Notion Integration",
                        "token": "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",
                        "url": "https://www.notion.so",
                        "category": "Productivity",
                        "status": "Active"
                    }
                ]
            },
            "devops_dashboard": {
                "title": "📊 DevOps Dashboard",
                "metrics": {
                    "backend_health": "Healthy",
                    "database_status": "Connected",
                    "active_deployments": 4,
                    "total_customers": 3587,
                    "total_jobs": 12820,
                    "ai_agents": 34,
                    "uptime": "99.9%"
                }
            },
            "environment_variables": {
                "title": "🔧 Environment Variables",
                "variables": [
                    {"name": "DATABASE_URL", "value": "postgresql://...", "status": "Set"},
                    {"name": "JWT_SECRET_KEY", "value": "***", "status": "Set"},
                    {"name": "STRIPE_SECRET_KEY", "value": "rk_live_***", "status": "Set"},
                    {"name": "SENDGRID_API_KEY", "value": "Not Set", "status": "Required"},
                    {"name": "OPENAI_API_KEY", "value": "Not Set", "status": "Optional"},
                    {"name": "ANTHROPIC_API_KEY", "value": "Not Set", "status": "Optional"}
                ]
            }
        }
    }
    
    # Save to file
    with open('/home/matt-woodworth/fastapi-operator-env/notion_workspace_data.json', 'w') as f:
        json.dump(workspace_data, f, indent=2)
    
    print("✅ Created notion_workspace_data.json")
    return workspace_data

def generate_manual_instructions():
    """Generate step-by-step instructions for manual Notion setup"""
    
    instructions = """
============================================================
  📝 MANUAL NOTION SETUP INSTRUCTIONS
============================================================

Since we need proper Notion integration permissions, please follow these steps:

1. OPEN NOTION:
   - Go to https://notion.so
   - Login with: matthew@brainstackstudio.com
   - Password: Mww00dw0rth@2O1S$

2. CREATE NEW WORKSPACE PAGE:
   - Click "+ New Page" 
   - Title it: "🎯 BrainOps Master Command Center"
   - Use the Full Page template

3. CREATE SECTIONS (Copy & Paste from NOTION_MASTER_COMMAND_CENTER_TEMPLATE.md):

   A. ACTIVE TASKS DATABASE:
      - Type /table
      - Name: "📋 Active Tasks"
      - Add columns: Status, Priority, Assigned To, Progress, Notes, Due Date
      - Add the 3 critical tasks from the template

   B. CREDENTIALS VAULT:
      - Type /table
      - Name: "🔐 Credentials Vault"
      - Add columns: Service, Username, Password/Token, URL, Category, Status
      - Import credentials from the template

   C. DEVOPS DASHBOARD:
      - Type /page
      - Name: "📊 DevOps Dashboard"
      - Add current metrics from the template

   D. ENVIRONMENT VARIABLES:
      - Type /table
      - Name: "🔧 Environment Variables"
      - Add columns: Name, Value, Status, Notes
      - Import all env vars from the template

4. ENABLE API INTEGRATION:
   - Go to Settings & Members → Integrations
   - Click "Develop your own integrations"
   - Use token: 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
   - Add integration to your workspace

5. IMPORT DATA:
   - Use the notion_workspace_data.json file
   - Or copy from NOTION_MASTER_COMMAND_CENTER_TEMPLATE.md

============================================================
  📁 FILES READY FOR IMPORT:
============================================================

1. Template File: /home/matt-woodworth/fastapi-operator-env/NOTION_MASTER_COMMAND_CENTER_TEMPLATE.md
2. Data File: /home/matt-woodworth/fastapi-operator-env/notion_workspace_data.json
3. Setup Script: /home/matt-woodworth/fastapi-operator-env/setup_notion_workspace.py

============================================================
"""
    
    print(instructions)
    
    # Save instructions to file
    with open('/home/matt-woodworth/fastapi-operator-env/NOTION_SETUP_INSTRUCTIONS.txt', 'w') as f:
        f.write(instructions)
    
    print("✅ Created NOTION_SETUP_INSTRUCTIONS.txt")

def main():
    print("\n" + "="*60)
    print("  🚀 BRAINOPS NOTION WORKSPACE SETUP")
    print("="*60)
    print(f"Setup Date: {datetime.now()}")
    print(f"System Version: v30.3.0")
    print(f"Operational Status: 73.9%")
    print("="*60 + "\n")
    
    # Create data file
    data = create_notion_import_file()
    
    # Generate instructions
    generate_manual_instructions()
    
    print("\n" + "="*60)
    print("  ✅ NOTION SETUP FILES CREATED!")
    print("="*60)
    print("\nNext Steps:")
    print("1. Follow the instructions in NOTION_SETUP_INSTRUCTIONS.txt")
    print("2. Import data from notion_workspace_data.json")
    print("3. Or copy sections from NOTION_MASTER_COMMAND_CENTER_TEMPLATE.md")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
