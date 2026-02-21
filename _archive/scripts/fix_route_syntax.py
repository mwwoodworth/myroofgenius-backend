#!/usr/bin/env python3
"""Fix syntax errors in route files"""

import os
import re

def fix_empty_class_body(content):
    """Fix empty class bodies by adding pass statement"""
    lines = content.split('\n')
    fixed_lines = []

    for i, line in enumerate(lines):
        fixed_lines.append(line)
        # Check if this is a class definition
        if line.strip().startswith('class ') and line.strip().endswith(':'):
            # Check if next line is another class or empty
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                # If next non-empty line doesn't have proper indentation, add pass
                if next_line.strip() and not next_line.startswith('    '):
                    fixed_lines.append('    pass')

    return '\n'.join(fixed_lines)

def fix_route_file(filepath):
    """Fix a single route file"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()

        # Fix empty class bodies
        fixed_content = fix_empty_class_body(content)

        # Only write if changed
        if fixed_content != content:
            with open(filepath, 'w') as f:
                f.write(fixed_content)
            return True
        return False
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")
        return False

# Fix all route files
routes_dir = '/home/matt-woodworth/fastapi-operator-env/routes'
fixed_count = 0

for filename in os.listdir(routes_dir):
    if filename.endswith('.py') and not filename.startswith('__'):
        filepath = os.path.join(routes_dir, filename)
        if fix_route_file(filepath):
            fixed_count += 1
            print(f"Fixed: {filename}")

print(f"\nFixed {fixed_count} files")