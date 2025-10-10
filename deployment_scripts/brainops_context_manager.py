#!/usr/bin/env python3
"""
BrainOps Context Manager
Maintains persistent context across all development sessions
"""
import os
import json
import datetime
from pathlib import Path

class BrainOpsContextManager:
    def __init__(self):
        self.context_dir = Path.home() / ".brainops"
        self.context_file = self.context_dir / "context.json"
        self.ensure_context_dir()
        
    def ensure_context_dir(self):
        """Create context directory if it doesn't exist."""
        self.context_dir.mkdir(exist_ok=True)
        
    def load_context(self):
        """Load existing context or create new."""
        if self.context_file.exists():
            with open(self.context_file, 'r') as f:
                return json.load(f)
        return self.create_default_context()
    
    def create_default_context(self):
        """Create default context structure."""
        return {
            "version": "1.0.9",
            "last_updated": datetime.datetime.now().isoformat(),
            "repositories": {
                "backend": {
                    "path": "/home/mwwoodworth/code/fastapi-operator-env",
                    "branch": "main",
                    "last_commit": None,
                    "docker_image": "mwwoodworth/brainops-backend"
                },
                "frontend": {
                    "path": "/home/mwwoodworth/code/myroofgenius-app",
                    "branch": "main",
                    "last_commit": None
                },
                "ai_assistant": {
                    "path": "/home/mwwoodworth/code/brainops-ai-assistant",
                    "branch": "master",
                    "last_commit": None
                }
            },
            "deployments": {
                "backend": {
                    "platform": "Render",
                    "url": "https://brainops-backend-prod.onrender.com",
                    "status": "live",
                    "version": "v1.0.8"
                },
                "frontend": {
                    "platform": "Vercel",
                    "url": "https://myroofgenius.com",
                    "status": "live"
                }
            },
            "current_issues": [
                "Request query parameter validation error",
                "Missing API keys in Render environment",
                "ERP/CRM features temporarily disabled"
            ],
            "next_tasks": [
                "Deploy v1.0.9 with validation fixes",
                "Add API keys to Render",
                "Create minimal frontend for core features",
                "Enable all automations"
            ]
        }
    
    def save_context(self, context):
        """Save context to file."""
        context["last_updated"] = datetime.datetime.now().isoformat()
        with open(self.context_file, 'w') as f:
            json.dump(context, f, indent=2)
    
    def update_version(self, version):
        """Update current version."""
        context = self.load_context()
        context["version"] = version
        self.save_context(context)
    
    def add_issue(self, issue):
        """Add a current issue."""
        context = self.load_context()
        if issue not in context["current_issues"]:
            context["current_issues"].append(issue)
        self.save_context(context)
    
    def resolve_issue(self, issue):
        """Remove a resolved issue."""
        context = self.load_context()
        if issue in context["current_issues"]:
            context["current_issues"].remove(issue)
        self.save_context(context)
    
    def get_status_report(self):
        """Generate current status report."""
        context = self.load_context()
        report = f"""
BrainOps Status Report
=====================
Version: {context['version']}
Last Updated: {context['last_updated']}

Deployments:
- Backend: {context['deployments']['backend']['status']} at {context['deployments']['backend']['version']}
- Frontend: {context['deployments']['frontend']['status']}

Current Issues:
"""
        for issue in context['current_issues']:
            report += f"- {issue}\n"
        
        report += "\nNext Tasks:\n"
        for task in context['next_tasks']:
            report += f"- {task}\n"
        
        return report

if __name__ == "__main__":
    manager = BrainOpsContextManager()
    print(manager.get_status_report())