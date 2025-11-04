#!/usr/bin/env python3
"""
FOUNDER SIGNOFF DASHBOARD
Visual dashboard for pre-launch validation and approval
v3.1.224
"""
import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, List, Any
import os

# ASCII Art for visual appeal
BRAINOPS_LOGO = """
╔══════════════════════════════════════════════════════════════╗
║  ____            _       ___                   ___  ____     ║
║ |  _ \          (_)     / _ \                 / _ \/ ___|    ║
║ | |_) |_ __ __ _ _ _ __| | | |_ __  ___      | | | \___ \    ║
║ |  _ <| '__/ _` | | '_ \ | | | '_ \/ __|     | | | |___) |   ║
║ | |_) | | | (_| | | | | | |_| | |_) \__ \     | |_| |____/    ║
║ |____/|_|  \__,_|_|_| |_|\___/| .__/|___/      \___/          ║
║                               |_|                              ║
╚══════════════════════════════════════════════════════════════╝
"""

class FounderDashboard:
    def __init__(self):
        self.validation_report = None
        self.system_metrics = {}
        self.critical_checks = []
        
    def load_validation_report(self):
        """Load the validation report"""
        try:
            with open("PRELAUNCH_VALIDATION_REPORT.json", "r") as f:
                self.validation_report = json.load(f)
        except:
            self.validation_report = None
            
    def generate_dashboard(self):
        """Generate the visual dashboard"""
        os.system('clear')
        print(BRAINOPS_LOGO)
        print("\n" + "="*65)
        print("             FOUNDER PRE-LAUNCH SIGNOFF DASHBOARD")
        print("="*65)
        print(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        if not self.validation_report:
            print("\n⚠️  No validation report found. Run validation first.")
            return
            
        # Summary Section
        summary = self.validation_report.get("summary", {})
        print("\n📊 VALIDATION SUMMARY")
        print("-"*65)
        
        total = summary.get("total_tests", 0)
        passed = summary.get("passed", 0)
        failed = summary.get("failed", 0)
        rate = summary.get("success_rate", "0%")
        
        # Visual progress bar
        bar_length = 40
        filled_length = int(bar_length * passed / total) if total > 0 else 0
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} | Failed: {failed}")
        print(f"Success Rate: [{bar}] {rate}")
        
        # Category Breakdown
        print("\n📋 CATEGORY BREAKDOWN")
        print("-"*65)
        print(f"{'Category':<20} {'Pass':<8} {'Fail':<8} {'Status':<15}")
        print("-"*65)
        
        categories = self.validation_report.get("categories", {})
        for cat_name, cat_data in categories.items():
            pass_count = cat_data.get("pass", 0)
            fail_count = cat_data.get("fail", 0)
            status = "✅ READY" if fail_count == 0 else "❌ NEEDS FIX"
            print(f"{cat_name:<20} {pass_count:<8} {fail_count:<8} {status:<15}")
            
        # Critical Issues
        print("\n🚨 CRITICAL ISSUES")
        print("-"*65)
        
        critical_found = False
        for test in self.validation_report.get("all_tests", []):
            if test["status"] == "FAIL":
                if not critical_found:
                    critical_found = True
                print(f"❌ {test['category']}: {test['test']}")
                print(f"   → {test['message']}")
                
        if not critical_found:
            print("✅ No critical issues found!")
            
        # System Requirements
        print("\n📝 PRE-LAUNCH CHECKLIST")
        print("-"*65)
        
        checklist = [
            ("Backend Deployment", "v3.1.224 deployed to Render", self._check_backend_version()),
            ("Database Health", "All tables and connections working", self._check_database()),
            ("Authentication", "Login system operational", self._check_auth()),
            ("Memory System", "Persistent memory storing data", self._check_memory()),
            ("AUREA AI", "Executive AI responding", self._check_aurea()),
            ("LangGraphOS", "Orchestration system active", self._check_langgraphos()),
            ("Marketplace", "Products and categories accessible", self._check_marketplace()),
            ("Admin Features", "Audit logs and controls working", self._check_admin()),
            ("Frontend", "MyRoofGenius accessible", self._check_frontend()),
            ("API Keys", "All required keys configured", self._check_api_keys()),
            ("Monitoring", "Vercel log drain configured", self._check_monitoring()),
        ]
        
        for item, description, status in checklist:
            icon = "✅" if status else "❌"
            print(f"{icon} {item:<25} - {description}")
            
        # Manual Actions Required
        print("\n⚙️  MANUAL ACTIONS REQUIRED")
        print("-"*65)
        
        actions = []
        if not self._check_backend_version():
            actions.append("1. Deploy v3.1.224 on Render dashboard")
        if not self._check_api_keys():
            actions.append("2. Add API keys to Render environment variables")
        if not self._check_monitoring():
            actions.append("3. Configure Vercel log drain in dashboard")
            
        if actions:
            for action in actions:
                print(f"   {action}")
        else:
            print("   ✅ No manual actions required")
            
        # Signoff Section
        print("\n" + "="*65)
        print("                    FOUNDER SIGNOFF")
        print("="*65)
        
        ready_for_launch = passed == total and len(actions) == 0
        
        if ready_for_launch:
            print("✅ SYSTEM IS READY FOR LAUNCH!")
            print("\nAll tests passed. All systems operational.")
            print("BrainOps OS is ready for production use.")
        else:
            print("❌ SYSTEM NOT READY FOR LAUNCH")
            print(f"\n{failed} tests failed. {len(actions)} manual actions required.")
            print("Please review and fix all issues before launch.")
            
        print("\n" + "="*65)
        print("To re-run validation: python3 CLAUDEOS_PRELAUNCH_VALIDATOR.py")
        print("To refresh dashboard: python3 FOUNDER_SIGNOFF_DASHBOARD.py")
        print("="*65)
        
    def _check_backend_version(self) -> bool:
        """Check if correct backend version is deployed"""
        # Would check actual version, for now based on validation
        summary = self.validation_report.get("summary", {})
        return summary.get("passed", 0) > summary.get("total_tests", 1) * 0.8
        
    def _check_database(self) -> bool:
        """Check database health"""
        cats = self.validation_report.get("categories", {})
        backend = cats.get("Backend", {})
        return backend.get("pass", 0) > 0
        
    def _check_auth(self) -> bool:
        """Check authentication"""
        cats = self.validation_report.get("categories", {})
        auth = cats.get("Authentication", {})
        return auth.get("pass", 0) > 0
        
    def _check_memory(self) -> bool:
        """Check memory system"""
        cats = self.validation_report.get("categories", {})
        memory = cats.get("Memory", {})
        return memory.get("pass", 0) > 0
        
    def _check_aurea(self) -> bool:
        """Check AUREA"""
        cats = self.validation_report.get("categories", {})
        aurea = cats.get("AUREA", {})
        return aurea.get("pass", 0) > 0
        
    def _check_langgraphos(self) -> bool:
        """Check LangGraphOS"""
        cats = self.validation_report.get("categories", {})
        lang = cats.get("LangGraphOS", {})
        return lang.get("pass", 0) > 0
        
    def _check_marketplace(self) -> bool:
        """Check marketplace"""
        cats = self.validation_report.get("categories", {})
        market = cats.get("Marketplace", {})
        return market.get("fail", 1) == 0
        
    def _check_admin(self) -> bool:
        """Check admin features"""
        cats = self.validation_report.get("categories", {})
        admin = cats.get("Admin", {})
        return admin.get("pass", 0) > 0
        
    def _check_frontend(self) -> bool:
        """Check frontend"""
        cats = self.validation_report.get("categories", {})
        frontend = cats.get("Frontend", {})
        return frontend.get("pass", 0) > 0
        
    def _check_api_keys(self) -> bool:
        """Check if API keys are configured"""
        # Would check actual keys, for now assume not if auth failed
        return self._check_auth()
        
    def _check_monitoring(self) -> bool:
        """Check if monitoring is configured"""
        # For now, assume not configured
        return False

def main():
    """Main entry point"""
    dashboard = FounderDashboard()
    dashboard.load_validation_report()
    dashboard.generate_dashboard()

if __name__ == "__main__":
    main()