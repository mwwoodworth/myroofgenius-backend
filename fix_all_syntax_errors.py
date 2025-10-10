#!/usr/bin/env python3
"""Fix all syntax errors in route files"""

import glob
import re

def fix_file(filepath):
    """Fix various syntax errors in a file"""
    with open(filepath, 'r') as f:
        content = f.read()

    original_content = content

    # Fix empty except blocks (line 82, 98, 123, 137)
    content = re.sub(r'except Exception:\s*\n\s*# If table doesn\'t exist, just return success\s*\n\s*\n',
                     'except Exception:\n        # If table doesn\'t exist, just return success\n        pass\n', content)

    content = re.sub(r'except Exception:\s*\n\s*\n',
                     'except Exception:\n        pass\n', content)

    # Fix undefined 'name' variable - replace with actual task name
    if 'task_199' in filepath:
        content = content.replace('{name}', 'Monte Carlo Simulation')
        content = content.replace('f"{name}', 'f"Monte Carlo Simulation')

    # Extract task number and name from filename
    import os
    filename = os.path.basename(filepath)
    if filename.startswith('task_'):
        parts = filename.replace('.py', '').split('_')
        if len(parts) >= 3:
            task_num = parts[1]
            task_name = ' '.join(word.capitalize() for word in parts[2:])
            content = content.replace('{name}', task_name)
            content = content.replace('f"{name}', f'f"{task_name}')

    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    return False

# Process all task files
task_files = glob.glob('routes/task_*.py')
print(f"Fixing {len(task_files)} task files")

fixed_count = 0
for filepath in task_files:
    if fix_file(filepath):
        fixed_count += 1
        print(f"Fixed: {filepath}")

print(f"\nTotal fixed: {fixed_count} files")

# Now verify all files can be parsed
print("\nVerifying syntax...")
import ast
errors = []
for filepath in task_files:
    try:
        with open(filepath) as f:
            ast.parse(f.read())
    except SyntaxError as e:
        errors.append(f"{filepath}: line {e.lineno} - {e.msg}")

if errors:
    print(f"\nRemaining errors: {len(errors)}")
    for error in errors[:5]:
        print(error)
else:
    print("\n✅ All task files are syntactically correct!")