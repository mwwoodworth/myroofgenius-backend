#!/usr/bin/env python3
"""
Create complete endpoint catalog WITH router prefixes
Version 2: Properly extracts full paths including prefixes
"""

import re
import os
from pathlib import Path
from typing import List, Tuple

def extract_router_prefix(content: str) -> str:
    """Extract the router prefix from APIRouter() definition"""
    router_match = re.search(r'router\s*=\s*APIRouter\((.*?)\)', content, re.DOTALL)
    if not router_match:
        return ""

    router_def = router_match.group(1)
    prefix_match = re.search(r'prefix\s*=\s*["\']([^"\']+)["\']', router_def)
    if prefix_match:
        return prefix_match.group(1)
    return ""

def extract_endpoints(file_path: Path) -> List[Tuple[str, str, str, str]]:
    """
    Extract all endpoints from a route file
    Returns: List of (method, full_path, route_file, function_name) tuples
    """
    content = file_path.read_text()
    endpoints = []

    # Get router prefix
    prefix = extract_router_prefix(content)

    # Find all route decorators
    patterns = [
        r'@router\.(get|post|put|patch|delete)\(["\']([^"\']+)["\']',
        r'@router\.(get|post|put|patch|delete)\(path=["\']([^"\']+)["\']',
    ]

    for pattern in patterns:
        matches = re.finditer(pattern, content, re.MULTILINE)
        for match in matches:
            method = match.group(1).upper()
            path = match.group(2)

            # Combine prefix + path
            if prefix:
                # Remove leading slash from path if prefix already has trailing slash
                if prefix.endswith('/') and path.startswith('/'):
                    full_path = prefix + path[1:]
                elif not prefix.endswith('/') and not path.startswith('/'):
                    full_path = prefix + '/' + path
                else:
                    full_path = prefix + path
            else:
                full_path = path

            # Get function name
            func_match = re.search(rf'@router\.{method.lower()}\([^)]+\)\s+(?:async\s+)?def\s+(\w+)', content[match.start():])
            func_name = func_match.group(1) if func_match else "unknown"

            endpoints.append((method, full_path, str(file_path.name), func_name))

    return endpoints

def main():
    routes_dir = Path("routes")
    all_endpoints = []

    print("Extracting endpoints from route files...")
    print()

    # Process all Python files in routes directory
    for route_file in sorted(routes_dir.glob("*.py")):
        if route_file.name in ["__init__.py", "route_loader.py"]:
            continue

        try:
            endpoints = extract_endpoints(route_file)
            all_endpoints.extend(endpoints)

            if endpoints:
                prefix = extract_router_prefix(route_file.read_text())
                print(f"{route_file.name:40} - {len(endpoints):3} endpoints (prefix: {prefix or 'none'})")
        except Exception as e:
            print(f"ERROR processing {route_file.name}: {e}")

    # Save to catalog file
    output_file = "/tmp/all-endpoints-catalog-v2.txt"
    with open(output_file, 'w') as f:
        for method, path, file, func in sorted(all_endpoints, key=lambda x: (x[1], x[0])):
            f.write(f"{method.lower()}|{path}|routes/{file}|{func}\n")

    print()
    print("=" * 70)
    print(f"Total endpoints extracted: {len(all_endpoints)}")
    print(f"Catalog saved to: {output_file}")
    print("=" * 70)

    # Show statistics
    from collections import Counter
    methods = Counter(m for m, _, _, _ in all_endpoints)
    print()
    print("Methods breakdown:")
    for method, count in methods.most_common():
        print(f"  {method:6} : {count:4}")

if __name__ == "__main__":
    main()
