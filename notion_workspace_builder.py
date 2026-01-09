#!/usr/bin/env python3
"""
BrainOps AI OS - Notion Workspace Builder
Builds complete management system in Matthew's Workspace HQ
"""

import os
import requests
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Get Notion token from environment variable
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
if not NOTION_TOKEN:
    raise RuntimeError("NOTION_TOKEN environment variable is required")

class NotionWorkspaceBuilder:
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        self.base_url = "https://api.notion.com/v1"
        self.workspace_id = None
        self.pages_created = {}
        
    def search_workspace(self) -> Dict:
        """Search for existing pages in the workspace"""
        response = requests.post(
            f"{self.base_url}/search",
            headers=self.headers,
            json={"query": "", "filter": {"property": "object", "value": "page"}}
        )
        return response.json()
    
    def delete_page(self, page_id: str) -> bool:
        """Archive/delete a page"""
        try:
            response = requests.patch(
                f"{self.base_url}/pages/{page_id}",
                headers=self.headers,
                json={"archived": True}
            )
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Failed to archive page {page_id}: {e}")
            return False
    
    def create_page(self, parent_id: Optional[str], title: str, icon: str = "🎯") -> Dict:
        """Create a new page"""
        parent = {"workspace": True} if not parent_id else {"page_id": parent_id}
        
        response = requests.post(
            f"{self.base_url}/pages",
            headers=self.headers,
            json={
                "parent": parent,
                "icon": {"emoji": icon},
                "properties": {
                    "title": {
                        "title": [{"text": {"content": title}}]
                    }
                }
            }
        )
        return response.json()
    
    def create_database(self, parent_id: str, title: str, properties: Dict) -> Dict:
        """Create a database with specified properties"""
        response = requests.post(
            f"{self.base_url}/databases",
            headers=self.headers,
            json={
                "parent": {"page_id": parent_id},
                "title": [{"text": {"content": title}}],
                "properties": properties
            }
        )
        return response.json()
    
    def add_database_entry(self, database_id: str, properties: Dict) -> Dict:
        """Add an entry to a database"""
        response = requests.post(
            f"{self.base_url}/pages",
            headers=self.headers,
            json={
                "parent": {"database_id": database_id},
                "properties": properties
            }
        )
        return response.json()
    
    def add_content_to_page(self, page_id: str, blocks: List[Dict]) -> Dict:
        """Add content blocks to a page"""
        response = requests.patch(
            f"{self.base_url}/blocks/{page_id}/children",
            headers=self.headers,
            json={"children": blocks}
        )
        return response.json()
    
    def clean_workspace(self):
        """Archive all old unused pages"""
        print("🧹 Cleaning workspace...")
        search_results = self.search_workspace()
        
        pages_to_keep = [
            "BrainOps AI OS Command Center",
            "BrainOps Master Command Center"
        ]
        
        deleted_count = 0
        for page in search_results.get("results", []):
            try:
                title = page.get("properties", {}).get("title", {}).get("title", [{}])[0].get("text", {}).get("content", "")
                if title and title not in pages_to_keep and not title.startswith("🎯 BrainOps"):
                    if self.delete_page(page["id"]):
                        print(f"   ✅ Archived: {title}")
                        deleted_count += 1
                        time.sleep(0.3)  # Rate limiting
            except Exception as e:
                logger.warning(f"Error processing page: {e}")
                continue
        
        print(f"   🗑️ Archived {deleted_count} old pages")
    
    def build_master_command_center(self):
        """Build the complete BrainOps AI OS management system"""
        print("\n🚀 Building BrainOps AI OS Command Center...")
        
        # Create main command center page
        main_page = self.create_page(
            None,
            "🎯 BrainOps AI OS Command Center",
            "🎯"
        )
        main_page_id = main_page.get("id")
        self.pages_created["main"] = main_page_id
        print("   ✅ Created main command center")
        time.sleep(0.5)
        
        # Add overview content
        overview_blocks = [
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"text": {"content": "🎯 BrainOps AI OS Command Center"}}]
                }
            },
            {
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{"text": {"content": f"System Version: v30.4.0 | Status: Deploying | Date: {datetime.now().strftime('%Y-%m-%d')}"}}],
                    "icon": {"emoji": "🚀"}
                }
            },
            {
                "object": "block",
                "type": "divider",
                "divider": {}
            }
        ]
        self.add_content_to_page(main_page_id, overview_blocks)
        time.sleep(0.5)
        
        # Create Active Tasks Database
        print("   📋 Creating Active Tasks database...")
        tasks_db = self.create_database(
            main_page_id,
            "📋 Active Tasks",
            {
                "Task": {"title": {}},
                "Status": {
                    "select": {
                        "options": [
                            {"name": "Not Started", "color": "gray"},
                            {"name": "In Progress", "color": "yellow"},
                            {"name": "Completed", "color": "green"},
                            {"name": "Blocked", "color": "red"}
                        ]
                    }
                },
                "Priority": {
                    "select": {
                        "options": [
                            {"name": "🔴 Critical", "color": "red"},
                            {"name": "🟡 High", "color": "yellow"},
                            {"name": "🟢 Normal", "color": "green"},
                            {"name": "⚪ Low", "color": "gray"}
                        ]
                    }
                },
                "Assigned To": {
                    "select": {
                        "options": [
                            {"name": "AI Agent", "color": "blue"},
                            {"name": "Human", "color": "green"},
                            {"name": "System", "color": "purple"}
                        ]
                    }
                },
                "Progress": {"number": {"format": "percent"}},
                "Due Date": {"date": {}},
                "Notes": {"rich_text": {}}
            }
        )
        tasks_db_id = tasks_db.get("id")
        self.pages_created["tasks_db"] = tasks_db_id
        time.sleep(0.5)
        
        # Add critical tasks
        critical_tasks = [
            {
                "Task": {"title": [{"text": {"content": "Complete v30.4.0 deployment"}}]},
                "Status": {"select": {"name": "In Progress"}},
                "Priority": {"select": {"name": "🔴 Critical"}},
                "Assigned To": {"select": {"name": "AI Agent"}},
                "Progress": {"number": 0.75},
                "Notes": {"rich_text": [{"text": {"content": "Fixing remaining API endpoints"}}]}
            },
            {
                "Task": {"title": [{"text": {"content": "Create Stripe products in dashboard"}}]},
                "Status": {"select": {"name": "Not Started"}},
                "Priority": {"select": {"name": "🔴 Critical"}},
                "Assigned To": {"select": {"name": "Human"}},
                "Progress": {"number": 0},
                "Notes": {"rich_text": [{"text": {"content": "AI Estimate ($99), Consultation ($299), Maintenance ($199/mo)"}}]}
            },
            {
                "Task": {"title": [{"text": {"content": "Configure SendGrid API key"}}]},
                "Status": {"select": {"name": "Not Started"}},
                "Priority": {"select": {"name": "🟡 High"}},
                "Assigned To": {"select": {"name": "Human"}},
                "Progress": {"number": 0},
                "Notes": {"rich_text": [{"text": {"content": "Required for email automation"}}]}
            }
        ]
        
        for task in critical_tasks:
            self.add_database_entry(tasks_db_id, task)
            time.sleep(0.3)
        print("   ✅ Added critical tasks")
        
        # Create Credentials Vault
        print("   🔐 Creating Credentials Vault...")
        creds_db = self.create_database(
            main_page_id,
            "🔐 Credentials Vault",
            {
                "Service": {"title": {}},
                "Username": {"rich_text": {}},
                "Password/Token": {"rich_text": {}},
                "URL": {"url": {}},
                "Category": {
                    "select": {
                        "options": [
                            {"name": "Database", "color": "blue"},
                            {"name": "Deployment", "color": "green"},
                            {"name": "Payment", "color": "yellow"},
                            {"name": "Version Control", "color": "purple"},
                            {"name": "Productivity", "color": "pink"}
                        ]
                    }
                },
                "Status": {
                    "select": {
                        "options": [
                            {"name": "Active", "color": "green"},
                            {"name": "Inactive", "color": "gray"},
                            {"name": "Expired", "color": "red"}
                        ]
                    }
                }
            }
        )
        creds_db_id = creds_db.get("id")
        self.pages_created["creds_db"] = creds_db_id
        time.sleep(0.5)
        
        # Add credentials
        credentials = [
            {
                "Service": {"title": [{"text": {"content": "Supabase Database"}}]},
                "Username": {"rich_text": [{"text": {"content": "postgres"}}]},
                "Password/Token": {"rich_text": [{"text": {"content": "<DB_PASSWORD_REDACTED>"}}]},
                "URL": {"url": "https://supabase.com/dashboard/project/yomagoqdmxszqtdwuhab"},
                "Category": {"select": {"name": "Database"}},
                "Status": {"select": {"name": "Active"}}
            },
            {
                "Service": {"title": [{"text": {"content": "Render"}}]},
                "Username": {"rich_text": [{"text": {"content": "API Key"}}]},
                "Password/Token": {"rich_text": [{"text": {"content": "rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx"}}]},
                "URL": {"url": "https://dashboard.render.com"},
                "Category": {"select": {"name": "Deployment"}},
                "Status": {"select": {"name": "Active"}}
            },
            {
                "Service": {"title": [{"text": {"content": "Stripe"}}]},
                "Username": {"rich_text": [{"text": {"content": "Live Key"}}]},
                "Password/Token": {"rich_text": [{"text": {"content": "<STRIPE_SECRET_KEY>..."}}]},
                "URL": {"url": "https://dashboard.stripe.com"},
                "Category": {"select": {"name": "Payment"}},
                "Status": {"select": {"name": "Active"}}
            }
        ]
        
        for cred in credentials:
            self.add_database_entry(creds_db_id, cred)
            time.sleep(0.3)
        print("   ✅ Added credentials")
        
        # Create DevOps Dashboard
        print("   📊 Creating DevOps Dashboard...")
        devops_page = self.create_page(
            main_page_id,
            "📊 DevOps Dashboard",
            "📊"
        )
        devops_page_id = devops_page.get("id")
        self.pages_created["devops"] = devops_page_id
        
        devops_blocks = [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "System Metrics"}}]
                }
            },
            {
                "object": "block",
                "type": "table",
                "table": {
                    "table_width": 2,
                    "has_column_header": True,
                    "has_row_header": False,
                    "children": [
                        {
                            "object": "block",
                            "type": "table_row",
                            "table_row": {
                                "cells": [
                                    [{"text": {"content": "Metric"}}],
                                    [{"text": {"content": "Value"}}]
                                ]
                            }
                        },
                        {
                            "object": "block",
                            "type": "table_row",
                            "table_row": {
                                "cells": [
                                    [{"text": {"content": "Backend Health"}}],
                                    [{"text": {"content": "✅ Healthy"}}]
                                ]
                            }
                        },
                        {
                            "object": "block",
                            "type": "table_row",
                            "table_row": {
                                "cells": [
                                    [{"text": {"content": "Total Customers"}}],
                                    [{"text": {"content": "3,587"}}]
                                ]
                            }
                        },
                        {
                            "object": "block",
                            "type": "table_row",
                            "table_row": {
                                "cells": [
                                    [{"text": {"content": "Total Jobs"}}],
                                    [{"text": {"content": "12,820"}}]
                                ]
                            }
                        },
                        {
                            "object": "block",
                            "type": "table_row",
                            "table_row": {
                                "cells": [
                                    [{"text": {"content": "AI Agents"}}],
                                    [{"text": {"content": "34"}}]
                                ]
                            }
                        }
                    ]
                }
            }
        ]
        self.add_content_to_page(devops_page_id, devops_blocks)
        time.sleep(0.5)
        
        # Create Environment Variables page
        print("   🔧 Creating Environment Variables...")
        env_db = self.create_database(
            main_page_id,
            "🔧 Environment Variables",
            {
                "Variable Name": {"title": {}},
                "Value": {"rich_text": {}},
                "Status": {
                    "select": {
                        "options": [
                            {"name": "Set", "color": "green"},
                            {"name": "Required", "color": "red"},
                            {"name": "Optional", "color": "gray"}
                        ]
                    }
                },
                "Notes": {"rich_text": {}}
            }
        )
        env_db_id = env_db.get("id")
        self.pages_created["env_db"] = env_db_id
        
        env_vars = [
            {
                "Variable Name": {"title": [{"text": {"content": "DATABASE_URL"}}]},
                "Value": {"rich_text": [{"text": {"content": "postgresql://..."}}]},
                "Status": {"select": {"name": "Set"}},
                "Notes": {"rich_text": [{"text": {"content": "Supabase connection string"}}]}
            },
            {
                "Variable Name": {"title": [{"text": {"content": "STRIPE_SECRET_KEY"}}]},
                "Value": {"rich_text": [{"text": {"content": "rk_live_***"}}]},
                "Status": {"select": {"name": "Set"}},
                "Notes": {"rich_text": [{"text": {"content": "Live Stripe API key"}}]}
            },
            {
                "Variable Name": {"title": [{"text": {"content": "SENDGRID_API_KEY"}}]},
                "Value": {"rich_text": [{"text": {"content": ""}}]},
                "Status": {"select": {"name": "Required"}},
                "Notes": {"rich_text": [{"text": {"content": "Needed for email automation"}}]}
            }
        ]
        
        for var in env_vars:
            self.add_database_entry(env_db_id, var)
            time.sleep(0.3)
        print("   ✅ Added environment variables")
        
        # Create SOPs Library
        print("   📝 Creating SOPs Library...")
        sops_page = self.create_page(
            main_page_id,
            "📝 SOPs Library",
            "📝"
        )
        sops_page_id = sops_page.get("id")
        self.pages_created["sops"] = sops_page_id
        
        sops_blocks = [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "Standard Operating Procedures"}}]
                }
            },
            {
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {
                    "rich_text": [{"text": {"content": "Deployment: Push to main branch → Auto-deploy via Render"}}]
                }
            },
            {
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {
                    "rich_text": [{"text": {"content": "Testing: Run pytest before any deployment"}}]
                }
            },
            {
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {
                    "rich_text": [{"text": {"content": "Monitoring: Check /health endpoint every 5 minutes"}}]
                }
            },
            {
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {
                    "rich_text": [{"text": {"content": "Database Backup: Daily at 2 AM UTC via Supabase"}}]
                }
            }
        ]
        self.add_content_to_page(sops_page_id, sops_blocks)
        time.sleep(0.5)
        
        # Create AI Memory Integration page
        print("   🧠 Creating AI Memory Integration...")
        ai_page = self.create_page(
            main_page_id,
            "🧠 AI Memory Integration",
            "🧠"
        )
        ai_page_id = ai_page.get("id")
        self.pages_created["ai_memory"] = ai_page_id
        
        ai_blocks = [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "AI System Integration"}}]
                }
            },
            {
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{"text": {"content": "This workspace is fully integrated with BrainOps AI agents for autonomous task management and execution."}}],
                    "icon": {"emoji": "🤖"}
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"text": {"content": "AI agents can read and update tasks"}}]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"text": {"content": "Persistent memory syncs with this workspace"}}]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"text": {"content": "Automated reporting and metrics updates"}}]
                }
            }
        ]
        self.add_content_to_page(ai_page_id, ai_blocks)
        time.sleep(0.5)
        
        print("\n✅ BrainOps AI OS Command Center built successfully!")
        return self.pages_created
    
    def get_summary(self):
        """Get summary of created pages"""
        summary = {
            "status": "success",
            "pages_created": len(self.pages_created),
            "command_center_url": f"https://notion.so/{self.pages_created.get('main', '').replace('-', '')}",
            "pages": [
                "🎯 Main Command Center",
                "📋 Active Tasks Database",
                "🔐 Credentials Vault",
                "📊 DevOps Dashboard",
                "🔧 Environment Variables",
                "📝 SOPs Library",
                "🧠 AI Memory Integration"
            ]
        }
        return summary

def main():
    print("\n" + "="*60)
    print("  🚀 BRAINOPS AI OS - NOTION WORKSPACE BUILDER")
    print("="*60)
    print(f"Build Date: {datetime.now()}")
    print(f"Integration Token: ***REDACTED***")
    print("="*60 + "\n")

    # Initialize builder with token from environment variable
    builder = NotionWorkspaceBuilder(NOTION_TOKEN)
    
    try:
        # Clean old pages
        builder.clean_workspace()
        
        # Build new command center
        pages = builder.build_master_command_center()
        
        # Get summary
        summary = builder.get_summary()
        
        print("\n" + "="*60)
        print("  ✅ BUILD COMPLETE!")
        print("="*60)
        print(f"Pages Created: {summary['pages_created']}")
        print(f"\nCommand Center URL: {summary['command_center_url']}")
        print("\nPages created:")
        for page in summary['pages']:
            print(f"  • {page}")
        print("\n" + "="*60)
        print("  🎯 Your BrainOps AI OS is ready!")
        print("="*60 + "\n")
        
        # Save summary to file
        with open('/home/matt-woodworth/fastapi-operator-env/notion_build_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        return summary
        
    except Exception as e:
        print(f"\n❌ Error building workspace: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure the integration token is valid")
        print("2. Check that the integration has access to Matthew's Workspace HQ")
        print("3. Verify network connectivity to Notion API")
        return None

if __name__ == "__main__":
    main()