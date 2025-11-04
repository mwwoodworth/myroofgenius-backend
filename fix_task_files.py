#!/usr/bin/env python3
"""Fix syntax errors in task_*.py files"""

import glob
import re

def fix_task_file(filepath):
    """Fix try block without except in task files"""
    with open(filepath, 'r') as f:
        lines = f.readlines()

    fixed = False
    new_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]
        new_lines.append(line)

        # Look for the problematic pattern around line 46
        if i == 45 and line.strip().startswith('if not rows:'):
            # Check if previous line is try without except
            if i > 0 and lines[i-1].strip() == 'rows = await db.fetch(query, limit, offset)':
                # Insert except block before the if statement
                indent = '    '  # Match the try block indentation
                new_lines.insert(-1, f'{indent}except Exception as e:\n')
                new_lines.insert(-1, f'{indent}    print(f"Error fetching data: {{e}}")\n')
                new_lines.insert(-1, f'{indent}    rows = []\n')
                fixed = True

        i += 1

    if fixed:
        with open(filepath, 'w') as f:
            f.writelines(new_lines)
        return True
    return False

# Process all task files with errors
error_files = [
    'routes/task_199_monte_carlo_simulation.py',
    'routes/task_170_revenue_recognition.py',
    'routes/task_112_microservices_orchestration.py',
    'routes/task_195_anomaly_detection.py',
    'routes/task_115_webhook_management.py',
    'routes/task_164_expense_management.py',
    'routes/task_203_microsoft_365_integration.py',
    'routes/task_136_backup_management.py',
    'routes/task_182_shop_floor_control.py',
    'routes/task_167_financial_reporting.py'
]

# Check all task files for this pattern
all_task_files = glob.glob('routes/task_*.py')
print(f"Found {len(all_task_files)} task files to check")

fixed_count = 0
for filepath in all_task_files:
    try:
        with open(filepath, 'r') as f:
            content = f.read()

        # Look for try without except pattern
        if 'try:\n        rows = await db.fetch(query, limit, offset)\n    if not rows:' in content:
            # Fix it
            content = content.replace(
                'try:\n        rows = await db.fetch(query, limit, offset)\n    if not rows:',
                'try:\n        rows = await db.fetch(query, limit, offset)\n    except Exception as e:\n        print(f"Error fetching data: {e}")\n        rows = []\n    if not rows:'
            )

            with open(filepath, 'w') as f:
                f.write(content)

            fixed_count += 1
            print(f"Fixed: {filepath}")
    except Exception as e:
        print(f"Error processing {filepath}: {e}")

print(f"\nTotal fixed: {fixed_count} files")