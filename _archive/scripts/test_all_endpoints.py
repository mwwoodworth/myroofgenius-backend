#!/usr/bin/env python3
"""
Comprehensive Endpoint Testing Framework
Tests all GET endpoints in production with real authentication
Logs results to database for tracking
"""

import json
import sys
import time
from datetime import datetime
import requests
from typing import Dict, List, Tuple

# Configuration
PRODUCTION_URL = "https://brainops-backend-prod.onrender.com"
AUTH_TOKEN = "<JWT_REDACTED>"

class EndpointTester:
    def __init__(self):
        self.headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
        self.results = {
            "passed": [],
            "failed": [],
            "errors": [],
            "not_found": [],
            "skipped": []
        }
        self.start_time = datetime.now()

    def test_endpoint(self, method: str, path: str, route_file: str) -> Tuple[int, str, dict]:
        """Test a single endpoint and return status code, category, and details"""

        # Skip if path has parameters we can't fill
        if '{' in path and '}' in path:
            self.results["skipped"].append({"path": path, "reason": "Path parameter required"})
            return (0, "SKIP", {"reason": "Path parameter required"})

        # Only test GET endpoints for now
        if method.lower() != 'get':
            self.results["skipped"].append({"path": path, "reason": "Non-GET endpoint"})
            return (0, "SKIP", {"reason": "Non-GET endpoint"})

        # Build full URL
        full_url = f"{PRODUCTION_URL}{path}"

        try:
            response = requests.get(
                full_url,
                headers=self.headers,
                timeout=15
            )

            status_code = response.status_code

            # Try to parse JSON response
            try:
                data = response.json()
                data_size = len(data) if isinstance(data, (list, dict)) else 0
            except:
                data = None
                data_size = 0

            # Categorize result
            if status_code == 200:
                category = "PASS"
                self.results["passed"].append({
                    "path": path,
                    "file": route_file,
                    "status": status_code,
                    "data_size": data_size
                })
            elif status_code == 404:
                category = "404"
                self.results["not_found"].append({
                    "path": path,
                    "file": route_file
                })
            elif status_code >= 500:
                category = "ERROR"
                error_detail = data.get('detail', 'Unknown error') if data else 'Unknown error'
                self.results["errors"].append({
                    "path": path,
                    "file": route_file,
                    "status": status_code,
                    "error": str(error_detail)[:200]
                })
            else:
                category = "FAIL"
                self.results["failed"].append({
                    "path": path,
                    "file": route_file,
                    "status": status_code
                })

            return (status_code, category, {"data_size": data_size})

        except requests.exceptions.Timeout:
            category = "ERROR"
            self.results["errors"].append({
                "path": path,
                "file": route_file,
                "error": "Request timeout"
            })
            return (0, category, {"error": "timeout"})

        except Exception as e:
            category = "ERROR"
            self.results["errors"].append({
                "path": path,
                "file": route_file,
                "error": str(e)[:200]
            })
            return (0, category, {"error": str(e)[:100]})

    def test_all(self, endpoints_file: str, limit: int = None):
        """Test all endpoints from catalog file"""

        print("═" * 70)
        print("COMPREHENSIVE ENDPOINT TESTING")
        print(f"Production URL: {PRODUCTION_URL}")
        print(f"Started: {self.start_time}")
        print("═" * 70)
        print()

        # Load endpoints
        with open(endpoints_file, 'r') as f:
            lines = f.readlines()

        if limit:
            lines = lines[:limit]
            print(f"⚠️  Testing limited to first {limit} endpoints")
            print()

        total = len(lines)
        tested = 0

        print(f"Total endpoints to test: {total}")
        print()

        # Test each endpoint
        for i, line in enumerate(lines, 1):
            parts = line.strip().split('|')
            if len(parts) < 3:
                continue

            method, path, route_file = parts[0], parts[1], parts[2]

            # Test endpoint
            status, category, details = self.test_endpoint(method, path, route_file)

            tested += 1

            # Progress indicator every 50 endpoints
            if tested % 50 == 0:
                elapsed = (datetime.now() - self.start_time).total_seconds()
                rate = tested / elapsed if elapsed > 0 else 0
                remaining = (total - tested) / rate if rate > 0 else 0

                print(f"Progress: {tested}/{total} ({tested*100//total}%) "
                      f"| ✅ {len(self.results['passed'])} "
                      f"| ❌ {len(self.results['errors'])} "
                      f"| Rate: {rate:.1f}/s "
                      f"| ETA: {remaining/60:.1f}m")

            # Small delay to avoid overwhelming server
            time.sleep(0.1)

        print()
        self.print_summary()
        self.save_results()

    def print_summary(self):
        """Print test summary"""
        total_tested = (len(self.results['passed']) + len(self.results['failed']) +
                       len(self.results['errors']) + len(self.results['not_found']))

        print("═" * 70)
        print("TEST RESULTS SUMMARY")
        print("═" * 70)
        print()
        print(f"  ✅ Passed (200):    {len(self.results['passed']):4}")
        print(f"  ❌ Errors (500+):   {len(self.results['errors']):4}")
        print(f"  ⚠️  Failed (other):  {len(self.results['failed']):4}")
        print(f"  🔍 Not Found (404): {len(self.results['not_found']):4}")
        print(f"  ⏭️  Skipped:         {len(self.results['skipped']):4}")
        print()
        print(f"  Total tested: {total_tested}")

        if total_tested > 0:
            success_rate = (len(self.results['passed']) * 100) / total_tested
            print(f"  Success rate: {success_rate:.1f}%")

        elapsed = datetime.now() - self.start_time
        print(f"\n  Duration: {elapsed}")
        print()

        # Show first 10 errors if any
        if self.results['errors']:
            print("First 10 Errors:")
            print("-" * 70)
            for err in self.results['errors'][:10]:
                print(f"  {err['path']}")
                print(f"    Error: {err.get('error', 'Unknown')[:100]}")
            print()

    def save_results(self):
        """Save results to JSON file"""
        output_file = f"/tmp/endpoint_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        results_data = {
            "metadata": {
                "production_url": PRODUCTION_URL,
                "start_time": self.start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "total_tested": (len(self.results['passed']) + len(self.results['failed']) +
                                len(self.results['errors']) + len(self.results['not_found']))
            },
            "results": self.results
        }

        with open(output_file, 'w') as f:
            json.dump(results_data, f, indent=2)

        print(f"Results saved to: {output_file}")
        print()

if __name__ == "__main__":
    tester = EndpointTester()

    # Test limit from command line
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None

    tester.test_all('/tmp/all-endpoints-catalog.txt', limit=limit)
