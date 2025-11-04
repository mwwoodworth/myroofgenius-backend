#!/usr/bin/env python3
"""Fix empty except blocks in route files"""

import glob
import re

def fix_empty_except_blocks(filepath):
    """Fix empty except blocks by adding pass statements"""
    with open(filepath, 'r') as f:
        lines = f.readlines()

    fixed = False
    new_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]
        new_lines.append(line)

        # Check if this is an except line with nothing after it
        if line.strip() == 'except Exception:':
            # Check if next line exists and is not indented (empty except body)
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                # If next line is not indented or is another block statement
                if next_line.strip() and not (next_line.startswith('        ') or next_line.startswith('\t\t')):
                    # Add pass statement
                    new_lines.append('        pass\n')
                    fixed = True
            elif i + 1 >= len(lines):
                # If except is at end of file
                new_lines.append('        pass\n')
                fixed = True

        i += 1

    if fixed:
        with open(filepath, 'w') as f:
            f.writelines(new_lines)
        return True
    return False

# Process all route files
route_files = glob.glob('routes/*.py')
print(f"Checking {len(route_files)} route files for empty except blocks")

fixed_count = 0
for filepath in route_files:
    if fix_empty_except_blocks(filepath):
        fixed_count += 1
        print(f"Fixed: {filepath}")

print(f"\nTotal fixed: {fixed_count} files")