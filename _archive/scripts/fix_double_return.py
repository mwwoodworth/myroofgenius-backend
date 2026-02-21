#!/usr/bin/env python3
"""Fix double return statement issue in task files"""

import glob

def fix_double_return(filepath):
    """Fix double return statement"""
    with open(filepath, 'r') as f:
        content = f.read()

    # Fix the specific pattern of double return
    content = content.replace(
        'if not rows:\n        return []\n        return [dict(row) for row in rows]',
        'if not rows:\n        return []\n    return [dict(row) for row in rows]'
    )

    with open(filepath, 'w') as f:
        f.write(content)
    return True

# Process all task files
task_files = glob.glob('routes/task_*.py')
print(f"Fixing double return in {len(task_files)} task files")

for filepath in task_files:
    fix_double_return(filepath)

print("Fixed all files")

# Verify
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