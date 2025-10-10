#!/usr/bin/env python3
"""
BrainOps Notion API Setup Script
Automatically creates and populates your Notion workspace
"""

import requests
import json
import time
from datetime import datetime

# Notion API Configuration
NOTION_TOKEN = "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"
NOTION_VERSION = "2022-06-28"
HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": NOTION_VERSION
}

BASE_URL = "https://api.notion.com/v1"

def create_page(parent_id, title, content):
    """Create a new page in Notion"""
    url = f"{BASE_URL}/pages"

    data = {
        "parent": {"page_id": parent_id} if parent_id else {"type": "workspace"},
        "properties": {
            "title": {
                "title": [
                    {
                        "type": "text",
                        "text": {"content": title}
                    }
                ]
            }
        },
        "children": content
    }

    response = requests.post(url, headers=HEADERS, json=data)
    if response.status_code == 200:
        print(f"✅ Created page: {title}")
        return response.json()
    else:
        print(f"❌ Failed to create page {title}: {response.text}")
        return None

def create_database(parent_id, title, properties):
    """Create a new database in Notion"""
    url = f"{BASE_URL}/databases"

    data = {
        "parent": {"page_id": parent_id},
        "title": [
            {
                "type": "text",
                "text": {"content": title}
            }
        ],
        "properties": properties
    }

    response = requests.post(url, headers=HEADERS, json=data)
    if response.status_code == 200:
        print(f"✅ Created database: {title}")
        return response.json()
    else:
        print(f"❌ Failed to create database {title}: {response.text}")
        return None

def add_database_row(database_id, properties):
    """Add a row to a Notion database"""
    url = f"{BASE_URL}/pages"

    data = {
        "parent": {"database_id": database_id},
        "properties": properties
    }

    response = requests.post(url, headers=HEADERS, json=data)
    return response.status_code == 200

def setup_workspace():
    """Main setup function"""
    print("\n" + "="*60)
    print("  🚀 BRAINOPS NOTION WORKSPACE AUTOMATED SETUP")
    print("="*60)
    print(f"Setup Date: {datetime.now()}")
    print(f"System Version: v30.3.0")
    print(f"Operational Status: 73.9%")
    print("="*60 + "\n")

    # Create main dashboard page
    main_page_content = [
        {
            "object": "block",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{"type": "text", "text": {"content": "🎯 BrainOps Master Command Center"}}]
            }
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "System Status"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"type": "text", "text": {"content": "Version: v30.3.0"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"type": "text", "text": {"content": "Operational: 73.9% (17/23 endpoints)"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"type": "text", "text": {"content": "Backend: https://brainops-backend-prod.onrender.com"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"type": "text", "text": {"content": "Database: PostgreSQL (Supabase)"}}]
            }
        }
    ]

    # Try to get workspace pages first
    search_url = f"{BASE_URL}/search"
    search_response = requests.post(search_url, headers=HEADERS, json={})

    if search_response.status_code == 200:
        print("✅ Connected to Notion API successfully!")

        # Create the main command center page
        main_page = create_page(None, "🎯 BrainOps Master Command Center", main_page_content)

        if main_page:
            parent_id = main_page["id"].replace("-", "")

            # Create Active Tasks Database
            task_props = {
                "Task": {"title": {}},
                "Status": {
                    "select": {
                        "options": [
                            {"name": "Not Started", "color": "gray"},
                            {"name": "In Progress", "color": "blue"},
                            {"name": "Blocked", "color": "red"},
                            {"name": "Completed", "color": "green"}
                        ]
                    }
                },
                "Priority": {
                    "select": {
                        "options": [
                            {"name": "🔴 Critical", "color": "red"},
                            {"name": "🟡 High", "color": "yellow"},
                            {"name": "🟢 Medium", "color": "green"},
                            {"name": "⚪ Low", "color": "gray"}
                        ]
                    }
                },
                "Assigned To": {
                    "select": {
                        "options": [
                            {"name": "AI Agent", "color": "purple"},
                            {"name": "Human", "color": "blue"},
                            {"name": "Both", "color": "orange"}
                        ]
                    }
                },
                "Progress": {"number": {"format": "percent"}},
                "Notes": {"rich_text": {}},
                "Due Date": {"date": {}},
                "Created": {"created_time": {}}
            }

            tasks_db = create_database(parent_id, "📋 Active Tasks", task_props)

            # Add critical tasks
            if tasks_db:
                tasks = [
                    {
                        "Task": {"title": [{"text": {"content": "Fix remaining API endpoints (Products, Lead Scoring, Workflows)"}}]},
                        "Status": {"select": {"name": "In Progress"}},
                        "Priority": {"select": {"name": "🔴 Critical"}},
                        "Assigned To": {"select": {"name": "AI Agent"}},
                        "Progress": {"number": 0.75},
                        "Notes": {"rich_text": [{"text": {"content": "v30.4.0 deployment pending"}}]}
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

                for task in tasks:
                    add_database_row(tasks_db["id"], task)
                    print(f"  Added task: {task['Task']['title'][0]['text']['content'][:50]}...")

            # Create Credentials Database
            cred_props = {
                "Service": {"title": {}},
                "Username": {"rich_text": {}},
                "Password": {"rich_text": {}},
                "API Key": {"rich_text": {}},
                "URL": {"url": {}},
                "Category": {
                    "select": {
                        "options": [
                            {"name": "Database", "color": "blue"},
                            {"name": "API", "color": "purple"},
                            {"name": "Deployment", "color": "green"},
                            {"name": "Payment", "color": "yellow"},
                            {"name": "Email", "color": "orange"}
                        ]
                    }
                },
                "Status": {
                    "select": {
                        "options": [
                            {"name": "Active", "color": "green"},
                            {"name": "Expired", "color": "red"},
                            {"name": "Needs Update", "color": "yellow"}
                        ]
                    }
                },
                "Notes": {"rich_text": {}}
            }

            creds_db = create_database(parent_id, "🔐 Credentials Vault", cred_props)

            # Add key credentials
            if creds_db:
                credentials = [
                    {
                        "Service": {"title": [{"text": {"content": "Supabase Database"}}]},
                        "Username": {"rich_text": [{"text": {"content": "postgres"}}]},
                        "Password": {"rich_text": [{"text": {"content": "Brain0ps2O2S"}}]},
                        "URL": {"url": "https://supabase.com/dashboard/project/yomagoqdmxszqtdwuhab"},
                        "Category": {"select": {"name": "Database"}},
                        "Status": {"select": {"name": "Active"}}
                    },
                    {
                        "Service": {"title": [{"text": {"content": "Docker Hub"}}]},
                        "Username": {"rich_text": [{"text": {"content": "mwwoodworth"}}]},
                        "Password": {"rich_text": [{"text": {"content": "dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho"}}]},
                        "URL": {"url": "https://hub.docker.com"},
                        "Category": {"select": {"name": "Deployment"}},
                        "Status": {"select": {"name": "Active"}}
                    },
                    {
                        "Service": {"title": [{"text": {"content": "Render"}}]},
                        "API Key": {"rich_text": [{"text": {"content": "rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx"}}]},
                        "URL": {"url": "https://dashboard.render.com"},
                        "Category": {"select": {"name": "Deployment"}},
                        "Status": {"select": {"name": "Active"}}
                    },
                    {
                        "Service": {"title": [{"text": {"content": "Stripe"}}]},
                        "API Key": {"rich_text": [{"text": {"content": "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"}}]},
                        "URL": {"url": "https://dashboard.stripe.com"},
                        "Category": {"select": {"name": "Payment"}},
                        "Status": {"select": {"name": "Active"}}
                    }
                ]

                for cred in credentials:
                    add_database_row(creds_db["id"], cred)
                    print(f"  Added credential: {cred['Service']['title'][0]['text']['content']}")

            print("\n" + "="*60)
            print("  ✅ NOTION WORKSPACE SETUP COMPLETE!")
            print("="*60)
            print("\nYour workspace is ready at: https://www.notion.so")
            print(f"Main page ID: {main_page['id']}")
            print("\nNext steps:")
            print("1. Open Notion in your browser")
            print("2. Navigate to the new workspace pages")
            print("3. Start managing your tasks and credentials")
            print("="*60 + "\n")

    else:
        print(f"❌ Failed to connect to Notion API: {search_response.status_code}")
        print(f"Response: {search_response.text}")
        print("\nPlease ensure:")
        print("1. The integration token is valid")
        print("2. The integration has been added to your workspace")
        print("3. You're logged into the correct Notion account")

if __name__ == "__main__":
    setup_workspace()