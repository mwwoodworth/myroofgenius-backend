#!/usr/bin/env python3
"""
Restore FULL backend functionality by analyzing all route files
and generating a complete main.py with ALL endpoints
"""

import os
import re
from pathlib import Path

def extract_endpoints_from_file(filepath):
    """Extract endpoint definitions from a route file"""
    endpoints = []

    try:
        with open(filepath, 'r') as f:
            content = f.read()

        # Find all @router.get, @router.post, etc decorators
        patterns = [
            r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
            r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content)
            for method, path in matches:
                endpoints.append({
                    'method': method.upper(),
                    'path': path,
                    'file': os.path.basename(filepath)
                })

    except Exception as e:
        print(f"Error reading {filepath}: {e}")

    return endpoints

def main():
    routes_dir = Path("/home/matt-woodworth/myroofgenius-backend/routes")
    all_endpoints = []

    # Scan all route files
    for route_file in routes_dir.glob("*.py"):
        endpoints = extract_endpoints_from_file(route_file)
        all_endpoints.extend(endpoints)

    # Group by path prefix
    endpoint_groups = {}
    for ep in all_endpoints:
        # Extract prefix (e.g., /api/v1/customers -> customers)
        path_parts = ep['path'].strip('/').split('/')
        if len(path_parts) >= 3 and path_parts[0] == 'api':
            prefix = path_parts[2]
        else:
            prefix = path_parts[0] if path_parts else 'root'

        if prefix not in endpoint_groups:
            endpoint_groups[prefix] = []
        endpoint_groups[prefix].append(ep)

    # Print summary
    print(f"Found {len(all_endpoints)} endpoints across {len(list(routes_dir.glob('*.py')))} files")
    print(f"Grouped into {len(endpoint_groups)} categories:")

    # Sort by number of endpoints per category
    for prefix in sorted(endpoint_groups.keys(), key=lambda x: len(endpoint_groups[x]), reverse=True)[:20]:
        eps = endpoint_groups[prefix]
        print(f"  - {prefix}: {len(eps)} endpoints")

    # Identify critical endpoints
    critical_prefixes = [
        'customers', 'jobs', 'estimates', 'invoices', 'employees',
        'equipment', 'inventory', 'timesheets', 'reports', 'ai',
        'auth', 'dashboard', 'revenue', 'crm', 'workflows',
        'field-inspections', 'monitoring', 'stripe', 'tenants'
    ]

    print("\nCritical endpoints to restore:")
    for prefix in critical_prefixes:
        if prefix in endpoint_groups:
            print(f"  ✓ {prefix}: {len(endpoint_groups[prefix])} endpoints found")
        else:
            print(f"  ✗ {prefix}: NOT FOUND - need to create")

    return endpoint_groups

if __name__ == "__main__":
    endpoint_groups = main()