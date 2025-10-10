#!/usr/bin/env python3
"""Final fix for all task file syntax errors"""

import glob
import re

def clean_task_file(filepath):
    """Remove orphaned code from task files"""
    with open(filepath, 'r') as f:
        lines = f.readlines()

    # Find lines with the orphaned code pattern and remove them
    new_lines = []
    skip_mode = False

    for i, line in enumerate(lines):
        # Check if we hit the orphaned code at line 52 (0-indexed = 51)
        if ('                "name": f"' in line and 'Item {i}",' in line):
            skip_mode = True
            continue

        # Skip related lines
        if skip_mode:
            if 'for i in range(min(10, limit))' in line or \
               '"status": "active",' in line or \
               '"created_at": datetime.now().isoformat()' in line or \
               '}' == line.strip() or \
               ']' == line.strip():
                continue
            else:
                skip_mode = False

        new_lines.append(line)

    with open(filepath, 'w') as f:
        f.writelines(new_lines)

# Process all task files
task_files = glob.glob('routes/task_*.py')
print(f"Final cleanup of {len(task_files)} task files")

for filepath in task_files:
    clean_task_file(filepath)

# Final verification
import ast
errors = []
for filepath in task_files:
    try:
        with open(filepath) as f:
            ast.parse(f.read())
    except SyntaxError as e:
        errors.append(f"{filepath}: line {e.lineno}")

if errors:
    print(f"\nRemaining errors: {len(errors)}")
    for error in errors[:5]:
        print(error)
else:
    print("\n✅ All task files are syntactically correct!")