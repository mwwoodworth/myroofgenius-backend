#!/usr/bin/env python3
"""
BrainOps AI OS Complete System Documentation in Notion
Creates comprehensive documentation for SOPs, Tasks, Env Vars, Prompts, and Architecture
"""

import requests
import json
import time
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import os

class BrainOpsNotionSystem:
    def __init__(self):
        self.notion_token = "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"
        self.headers = {
            "Authorization": f"Bearer {self.notion_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        self.base_url = "https://api.notion.com/v1"

        # Database configuration
        self.db_config = {
            "host": "aws-0-us-east-2.pooler.supabase.com",
            "database": "postgres",
            "user": "postgres.yomagoqdmxszqtdwuhab",
            "password": "Brain0ps2O2S",
            "port": 5432
        }

        # Track created pages
        self.created_pages = {}

    def create_sops_documentation(self):
        """Create comprehensive SOPs documentation"""
        print("\n📝 Creating SOPs Documentation...")

        sops = {
            "Deployment SOPs": [
                "1. Always test locally before deployment",
                "2. Build Docker image with version tag",
                "3. Push to Docker Hub with both version and latest tags",
                "4. Trigger Render deployment",
                "5. Monitor health endpoint for version confirmation",
                "6. Run live API tests"
            ],
            "Database SOPs": [
                "1. Always backup before schema changes",
                "2. Use migrations for all schema updates",
                "3. Test migrations on staging first",
                "4. Document all table relationships",
                "5. Maintain referential integrity",
                "6. Use connection pooling for production"
            ],
            "Code Development SOPs": [
                "1. Follow existing code patterns",
                "2. Always use type hints in Python",
                "3. Test all endpoints before deployment",
                "4. Document all API changes",
                "5. Use atomic commits",
                "6. Update version numbers consistently"
            ],
            "Security SOPs": [
                "1. Never commit credentials to git",
                "2. Use environment variables for secrets",
                "3. Rotate API keys regularly",
                "4. Implement rate limiting",
                "5. Log all authentication attempts",
                "6. Use HTTPS for all external APIs"
            ],
            "AI Integration SOPs": [
                "1. Always provide fallback for AI failures",
                "2. Log all AI API calls",
                "3. Monitor token usage",
                "4. Implement retry logic with backoff",
                "5. Cache AI responses when appropriate",
                "6. Use appropriate models for tasks"
            ],
            "Task Management SOPs": [
                "1. Always use TodoWrite tool for task tracking",
                "2. Update task status in real-time",
                "3. Only one task in_progress at a time",
                "4. Document blockers immediately",
                "5. Complete tasks before starting new ones",
                "6. Sync with Notion task manager"
            ]
        }

        # Create SOPs page
        sops_content = []
        for category, items in sops.items():
            sops_content.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"text": {"content": category}}]}
            })
            for item in items:
                sops_content.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {"rich_text": [{"text": {"content": item}}]}
                })
            sops_content.append({"object": "block", "type": "divider", "divider": {}})

        return sops_content

    def create_task_manager(self):
        """Create AI-Human synchronized task manager"""
        print("\n📋 Creating Task Manager Database...")

        # Define task database properties
        task_properties = {
            "Task": {"title": {}},
            "Status": {
                "select": {
                    "options": [
                        {"name": "🔴 Blocked", "color": "red"},
                        {"name": "⏸️ Pending", "color": "gray"},
                        {"name": "🔄 In Progress", "color": "yellow"},
                        {"name": "✅ Completed", "color": "green"}
                    ]
                }
            },
            "Priority": {
                "select": {
                    "options": [
                        {"name": "🔥 Critical", "color": "red"},
                        {"name": "⚠️ High", "color": "orange"},
                        {"name": "📌 Medium", "color": "yellow"},
                        {"name": "📎 Low", "color": "gray"}
                    ]
                }
            },
            "Assigned To": {
                "select": {
                    "options": [
                        {"name": "AI Agent", "color": "blue"},
                        {"name": "Human", "color": "green"},
                        {"name": "Both", "color": "purple"}
                    ]
                }
            },
            "Created": {"created_time": {}},
            "Updated": {"last_edited_time": {}},
            "Due Date": {"date": {}},
            "Notes": {"rich_text": {}},
            "Dependencies": {"rich_text": {}},
            "Completion %": {"number": {"format": "percent"}}
        }

        return task_properties

    def create_env_vars_table(self):
        """Create master environment variables table"""
        print("\n🔧 Creating Environment Variables Table...")

        env_vars = {
            "DATABASE_URL": {
                "value": "postgresql://postgres.yomagoqdmxszqtdwuhab:***@aws-0-us-east-2.pooler.supabase.com:5432/postgres",
                "status": "Set",
                "category": "Database",
                "notes": "Supabase PostgreSQL connection"
            },
            "JWT_SECRET_KEY": {
                "value": "***",
                "status": "Set",
                "category": "Security",
                "notes": "JWT token signing key"
            },
            "STRIPE_SECRET_KEY": {
                "value": "rk_live_***",
                "status": "Set",
                "category": "Payment",
                "notes": "Live Stripe API key"
            },
            "DOCKER_PAT": {
                "value": "dckr_pat_***",
                "status": "Set",
                "category": "Deployment",
                "notes": "Docker Hub access token"
            },
            "RENDER_API_KEY": {
                "value": "rnd_***",
                "status": "Set",
                "category": "Deployment",
                "notes": "Render deployment API"
            },
            "NOTION_TOKEN": {
                "value": "ntn_***",
                "status": "Set",
                "category": "Integration",
                "notes": "Notion API integration"
            },
            "OPENAI_API_KEY": {
                "value": "",
                "status": "Required",
                "category": "AI",
                "notes": "OpenAI GPT-4 access"
            },
            "ANTHROPIC_API_KEY": {
                "value": "",
                "status": "Required",
                "category": "AI",
                "notes": "Claude API access"
            },
            "SENDGRID_API_KEY": {
                "value": "",
                "status": "Required",
                "category": "Email",
                "notes": "Email automation"
            }
        }

        return env_vars

    def create_prompt_database(self):
        """Create master prompt database"""
        print("\n💭 Creating Prompt Database...")

        prompts = {
            "System Initialization": {
                "prompt": "You are Claude Code, an AI assistant specialized in software development. Always use available tools, track tasks with TodoWrite, and maintain context in CLAUDE.md files.",
                "category": "System",
                "usage": "Initial system setup"
            },
            "Code Review": {
                "prompt": "Review this code for: 1) Security vulnerabilities, 2) Performance issues, 3) Best practices, 4) Type safety, 5) Error handling. Provide specific improvement suggestions.",
                "category": "Development",
                "usage": "Code quality checks"
            },
            "Database Query Optimization": {
                "prompt": "Analyze this query for performance. Consider: indexes, joins, subqueries, connection pooling. Provide optimized version with explanation.",
                "category": "Database",
                "usage": "Query optimization"
            },
            "API Endpoint Creation": {
                "prompt": "Create a FastAPI endpoint with: proper validation, error handling, documentation, type hints, and test cases. Follow RESTful conventions.",
                "category": "API",
                "usage": "Endpoint development"
            },
            "Deployment Preparation": {
                "prompt": "Prepare for deployment: 1) Run tests, 2) Update version, 3) Build Docker image, 4) Push to registry, 5) Update documentation, 6) Monitor health.",
                "category": "DevOps",
                "usage": "Deployment workflow"
            },
            "Error Diagnosis": {
                "prompt": "Diagnose this error: 1) Identify root cause, 2) Check related systems, 3) Review recent changes, 4) Propose fixes, 5) Implement solution, 6) Add preventive measures.",
                "category": "Debugging",
                "usage": "Error resolution"
            }
        }

        return prompts

    def create_architecture_documentation(self):
        """Create comprehensive BrainOps AI OS architecture documentation"""
        print("\n🏗️ Creating Architecture Documentation...")

        architecture = {
            "System Overview": {
                "Backend": "FastAPI v30.3.0 - Python 3.11",
                "Database": "PostgreSQL via Supabase (481 tables)",
                "Frontend": "Next.js (MyRoofGenius, WeatherCraft)",
                "Deployment": "Docker → Docker Hub → Render",
                "AI Services": "Claude, GPT-4, Gemini",
                "Monitoring": "Health endpoints, Papertrail logs"
            },
            "Core Components": {
                "API Layer": [
                    "/api/v1/health - System health check",
                    "/api/v1/auth/* - Authentication endpoints",
                    "/api/v1/crm/* - Customer management",
                    "/api/v1/jobs/* - Job tracking",
                    "/api/v1/invoices/* - Billing system",
                    "/api/v1/ai/* - AI services",
                    "/api/v1/webhooks/* - External integrations"
                ],
                "Database Schema": [
                    "customers (3,587 records)",
                    "jobs (12,820 records)",
                    "invoices (2,004 records)",
                    "ai_agents (34 agents)",
                    "users, estimates, inventory, etc."
                ],
                "AI Agents": [
                    "Lead scoring agent",
                    "Content generation agent",
                    "Data analysis agent",
                    "Customer service agent",
                    "Automation orchestrator"
                ]
            },
            "Infrastructure": {
                "Production URLs": [
                    "https://brainops-backend-prod.onrender.com",
                    "https://myroofgenius.com",
                    "https://weathercraft-erp.vercel.app"
                ],
                "Docker Registry": "mwwoodworth/brainops-backend",
                "Database Host": "db.yomagoqdmxszqtdwuhab.supabase.co",
                "Connection Pool": "aws-0-us-east-2.pooler.supabase.com"
            },
            "Development Workflow": {
                "Local Development": "python3 -m uvicorn main:app",
                "Testing": "pytest + live API tests",
                "Version Control": "Git → GitHub",
                "CI/CD": "Git push → Docker build → Render deploy",
                "Monitoring": "Health checks every 5 minutes"
            },
            "Security": {
                "Authentication": "JWT tokens",
                "API Keys": "Environment variables",
                "Database": "SSL connections",
                "Passwords": "Bcrypt hashing",
                "Rate Limiting": "Per-endpoint limits"
            }
        }

        return architecture

    def create_complete_system(self):
        """Create complete BrainOps system in Notion"""
        print("\n" + "="*60)
        print("  🚀 CREATING BRAINOPS AI OS COMPLETE SYSTEM")
        print("="*60)

        # Get all documentation
        sops = self.create_sops_documentation()
        task_props = self.create_task_manager()
        env_vars = self.create_env_vars_table()
        prompts = self.create_prompt_database()
        architecture = self.create_architecture_documentation()

        # Create master page content
        master_content = [
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {"rich_text": [{"text": {"content": "🧠 BrainOps AI OS Master Documentation"}}]}
            },
            {
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{"text": {"content": f"System Version: v30.3.0\nLast Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nStatus: 73.9% Operational"}}],
                    "icon": {"emoji": "🚀"}
                }
            },
            {"object": "block", "type": "divider", "divider": {}},
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"text": {"content": "📝 Standard Operating Procedures"}}]}
            }
        ]

        # Add SOPs
        master_content.extend(sops)

        # Add Environment Variables section
        master_content.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": "🔧 Environment Variables"}}]}
        })

        for var_name, var_info in env_vars.items():
            status_emoji = "✅" if var_info["status"] == "Set" else "❌"
            master_content.append({
                "object": "block",
                "type": "toggle",
                "toggle": {
                    "rich_text": [{"text": {"content": f"{status_emoji} {var_name} ({var_info['category']})"}}],
                    "children": [
                        {
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [{"text": {"content": f"Value: {var_info['value']}\nStatus: {var_info['status']}\nNotes: {var_info['notes']}"}}]
                            }
                        }
                    ]
                }
            })

        # Add Prompts section
        master_content.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": "💭 Master Prompt Database"}}]}
        })

        for prompt_name, prompt_info in prompts.items():
            master_content.append({
                "object": "block",
                "type": "toggle",
                "toggle": {
                    "rich_text": [{"text": {"content": f"{prompt_name} ({prompt_info['category']})"}}],
                    "children": [
                        {
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [{"text": {"content": f"Usage: {prompt_info['usage']}\n\nPrompt:\n{prompt_info['prompt']}"}}]
                            }
                        }
                    ]
                }
            })

        # Add Architecture section
        master_content.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": "🏗️ System Architecture"}}]}
        })

        for section_name, section_data in architecture.items():
            master_content.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": [{"text": {"content": section_name}}]}
            })

            if isinstance(section_data, dict):
                for key, value in section_data.items():
                    if isinstance(value, list):
                        master_content.append({
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {"rich_text": [{"text": {"content": f"{key}:", "annotations": {"bold": True}}}]}
                        })
                        for item in value:
                            master_content.append({
                                "object": "block",
                                "type": "bulleted_list_item",
                                "bulleted_list_item": {"rich_text": [{"text": {"content": item}}]}
                            })
                    else:
                        master_content.append({
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {"rich_text": [{"text": {"content": f"{key}: {value}"}}]}
                        })

        # Save as JSON for Notion import
        notion_data = {
            "master_content": master_content,
            "task_database_properties": task_props,
            "environment_variables": env_vars,
            "prompts": prompts,
            "architecture": architecture,
            "created_at": datetime.now().isoformat()
        }

        with open('/home/matt-woodworth/fastapi-operator-env/brainops_notion_complete.json', 'w') as f:
            json.dump(notion_data, f, indent=2)

        print("✅ Complete system documentation created!")
        print("📄 Saved to: brainops_notion_complete.json")

        return notion_data

def main():
    print("\n" + "="*60)
    print("  🧠 BRAINOPS AI OS - COMPLETE NOTION SYSTEM")
    print("="*60)
    print(f"Created: {datetime.now()}")
    print("="*60)

    system = BrainOpsNotionSystem()
    data = system.create_complete_system()

    print("\n" + "="*60)
    print("  ✅ SYSTEM DOCUMENTATION COMPLETE!")
    print("="*60)
    print("\n📋 What's Been Created:")
    print("  1. Standard Operating Procedures (SOPs)")
    print("  2. Task Manager Database Schema")
    print("  3. Environment Variables Documentation")
    print("  4. Master Prompt Database")
    print("  5. Complete System Architecture")
    print("\n🎯 Next Steps:")
    print("  1. Import brainops_notion_complete.json to Notion")
    print("  2. Create task manager database with provided schema")
    print("  3. Use task manager for ALL work going forward")
    print("  4. Reference SOPs for all operations")
    print("  5. Keep architecture documentation updated")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()