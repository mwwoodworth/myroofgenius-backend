#!/usr/bin/env python3
"""
BrainOps Real-Time Status Check
Shows EXACTLY what's happening RIGHT NOW across all systems
"""

import os
import json
import psycopg2
import requests
import subprocess
from datetime import datetime
from pathlib import Path
import docker

class DevOpsStatusCheck:
    """Real-time status of all BrainOps systems"""

    def __init__(self):
        self.timestamp = datetime.now()
        self.results = {}

    def check_all_systems(self):
        """Check every system and report status"""
        print("\n" + "="*80)
        print(f"  🔍 BRAINOPS REAL-TIME STATUS CHECK")
        print(f"  Time: {self.timestamp}")
        print("="*80 + "\n")

        # Check production API
        self.check_production_api()

        # Check database
        self.check_database()

        # Check Docker
        self.check_docker()

        # Check repositories
        self.check_repositories()

        # Check running processes
        self.check_processes()

        # Check Notion sync
        self.check_notion()

        # Save status to file
        self.save_status()

        # Print summary
        self.print_summary()

    def check_production_api(self):
        """Check production API status"""
        print("🌐 PRODUCTION API STATUS")
        print("-" * 40)

        try:
            # Health check
            response = requests.get("https://brainops-backend-prod.onrender.com/health", timeout=5)
            health = response.json()
            version = health.get("version", "unknown")
            self.results["api_version"] = version
            print(f"  ✅ API Online - Version: {version}")

            # Check endpoints
            endpoints = [
                "/api/v1/customers",
                "/api/v1/jobs",
                "/api/v1/invoices",
                "/api/v1/estimates",
                "/api/v1/inventory",
                "/api/v1/equipment",
                "/api/v1/workflows"
            ]

            working = 0
            for endpoint in endpoints:
                try:
                    url = f"https://brainops-backend-prod.onrender.com{endpoint}"
                    resp = requests.get(url, timeout=3)
                    if resp.status_code == 200:
                        working += 1
                        print(f"  ✅ {endpoint}")
                    else:
                        print(f"  ⚠️ {endpoint} ({resp.status_code})")
                except:
                    print(f"  ❌ {endpoint}")

            self.results["api_endpoints"] = f"{working}/{len(endpoints)} working"

        except Exception as e:
            print(f"  ❌ API Offline: {e}")
            self.results["api_status"] = "offline"

        print()

    def check_database(self):
        """Check database connection and stats"""
        print("🗄️ DATABASE STATUS")
        print("-" * 40)

        try:
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST", "aws-0-us-east-2.pooler.supabase.com"),
                port=os.getenv("DB_PORT", "6543"),
                database=os.getenv("DB_NAME", "postgres"),
                user=os.getenv("DB_USER", "postgres.yomagoqdmxszqtdwuhab"),
                password=os.getenv("DB_PASSWORD", ""),
                sslmode="require"
            )
            cur = conn.cursor()

            # Get counts
            cur.execute("SELECT COUNT(*) FROM customers")
            customers = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM jobs")
            jobs = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM ai_agents")
            agents = cur.fetchone()[0]

            print(f"  ✅ Database Connected")
            print(f"  • Customers: {customers:,}")
            print(f"  • Jobs: {jobs:,}")
            print(f"  • AI Agents: {agents}")

            self.results["database"] = {
                "status": "connected",
                "customers": customers,
                "jobs": jobs,
                "ai_agents": agents
            }

            conn.close()

        except Exception as e:
            print(f"  ❌ Database Error: {e}")
            self.results["database"] = {"status": "error"}

        print()

    def check_docker(self):
        """Check Docker status and containers"""
        print("🐳 DOCKER STATUS")
        print("-" * 40)

        try:
            # Check Docker daemon
            result = subprocess.run(
                ["docker", "version"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                print(f"  ✅ Docker Running")

                # List containers
                client = docker.from_env()
                containers = client.containers.list()

                if containers:
                    print(f"  • Containers: {len(containers)} running")
                    for container in containers:
                        print(f"    - {container.name}: {container.status}")
                else:
                    print(f"  • No containers running")

                self.results["docker"] = {
                    "status": "running",
                    "containers": len(containers)
                }
            else:
                print(f"  ⚠️ Docker not running (needs sudo)")
                self.results["docker"] = {"status": "needs_start"}

        except Exception as e:
            print(f"  ❌ Docker Error: {e}")
            self.results["docker"] = {"status": "error"}

        print()

    def check_repositories(self):
        """Check git repositories"""
        print("📂 REPOSITORY STATUS")
        print("-" * 40)

        repos = {
            "fastapi-operator-env": "/home/matt-woodworth/fastapi-operator-env",
            "myroofgenius-app": "/home/matt-woodworth/code/myroofgenius-app",
            "weathercraft-erp": "/home/matt-woodworth/code/weathercraft-erp"
        }

        for name, path in repos.items():
            repo_path = Path(path)
            if repo_path.exists():
                # Get git status
                try:
                    result = subprocess.run(
                        ["git", "-C", path, "status", "--short"],
                        capture_output=True,
                        text=True
                    )

                    if result.stdout:
                        print(f"  ⚠️ {name}: Has uncommitted changes")
                    else:
                        print(f"  ✅ {name}: Clean")

                    # Get current branch
                    branch_result = subprocess.run(
                        ["git", "-C", path, "branch", "--show-current"],
                        capture_output=True,
                        text=True
                    )
                    branch = branch_result.stdout.strip()
                    print(f"     Branch: {branch}")

                except:
                    print(f"  ❌ {name}: Git error")
            else:
                print(f"  ❌ {name}: Not found")

        print()

    def check_processes(self):
        """Check running processes"""
        print("⚙️ RUNNING PROCESSES")
        print("-" * 40)

        # Check for uvicorn
        uvicorn = subprocess.run(
            ["pgrep", "-f", "uvicorn"],
            capture_output=True
        )

        if uvicorn.returncode == 0:
            print(f"  ✅ Uvicorn running (Backend API)")
        else:
            print(f"  ⚠️ Uvicorn not running")

        # Check for node processes
        node = subprocess.run(
            ["pgrep", "-f", "node"],
            capture_output=True
        )

        if node.returncode == 0:
            print(f"  ✅ Node.js processes running")
        else:
            print(f"  ⚠️ No Node.js processes")

        print()

    def check_notion(self):
        """Check Notion integration status"""
        print("📝 NOTION INTEGRATION")
        print("-" * 40)

        # Check if token is configured
        token = os.getenv("NOTION_TOKEN", "")

        if token:
            print(f"  ✅ Notion token configured")

            # Check last sync time
            sync_file = Path(".ai_persistent/notion_last_sync.json")
            if sync_file.exists():
                with open(sync_file) as f:
                    data = json.load(f)
                    last_sync = data.get("last_sync", "never")
                    print(f"  • Last sync: {last_sync}")
            else:
                print(f"  • No sync history")
        else:
            print(f"  ❌ Notion token not configured")

        print()

    def save_status(self):
        """Save status to file for persistence"""
        status_file = Path(".ai_persistent/current_status.json")
        status_file.parent.mkdir(exist_ok=True)

        status_data = {
            "timestamp": str(self.timestamp),
            "results": self.results
        }

        with open(status_file, "w") as f:
            json.dump(status_data, f, indent=2)

        # Also update DEVOPS_CONTEXT.md
        self.update_context_file()

    def update_context_file(self):
        """Update the DEVOPS_CONTEXT.md with current status"""
        context_file = Path("DEVOPS_CONTEXT.md")

        if context_file.exists():
            # Read current content
            with open(context_file) as f:
                content = f.read()

            # Find and update the timestamp
            import re
            new_content = re.sub(
                r'\*\*Last Updated:\*\* .*',
                f'**Last Updated:** {self.timestamp.strftime("%Y-%m-%d %H:%M:%S")} MDT',
                content
            )

            # Update version if we have it
            if "api_version" in self.results:
                new_content = re.sub(
                    r'\*\*Version:\*\* .*',
                    f'**Version:** {self.results["api_version"]} (Production)',
                    new_content
                )

            # Write back
            with open(context_file, "w") as f:
                f.write(new_content)

    def print_summary(self):
        """Print overall summary"""
        print("="*80)
        print("  📊 SUMMARY")
        print("="*80)

        # Calculate overall health
        issues = []

        if self.results.get("docker", {}).get("status") != "running":
            issues.append("Docker needs to be started")

        if "error" in str(self.results.get("database", {})):
            issues.append("Database connection issue")

        if not issues:
            print("  ✅ ALL SYSTEMS OPERATIONAL")
        else:
            print(f"  ⚠️ ISSUES DETECTED:")
            for issue in issues:
                print(f"    • {issue}")

        print("\n  Quick Actions:")
        print("  • Start Docker: sudo systemctl start docker")
        print("  • Launch DevOps: ./launch_devops.sh")
        print("  • Run Demo: python3 devops_demo.py")
        print("  • Sync Notion: python3 notion_live_integration.py")

        print("\n" + "="*80 + "\n")

def main():
    checker = DevOpsStatusCheck()
    checker.check_all_systems()

if __name__ == "__main__":
    main()