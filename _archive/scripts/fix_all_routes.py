#!/usr/bin/env python3
"""Fix ALL syntax errors in route files"""

import os
import ast

def fix_empty_class(filepath):
    """Fix empty class bodies in a file"""
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()

        fixed = False
        new_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]
            new_lines.append(line)

            # Check if this is a class definition line
            if line.strip().startswith('class ') and line.strip().endswith(':'):
                # Check if next line exists and is not indented (empty class body)
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    # If next line is not indented or is another class/comment/decorator
                    if (next_line.strip() and not next_line.startswith('    ') and not next_line.startswith('\t')):
                        new_lines.append('    pass\n')
                        fixed = True
                # If this is the last line or next line is empty
                elif i + 1 >= len(lines):
                    new_lines.append('    pass\n')
                    fixed = True

            i += 1

        if fixed:
            with open(filepath, 'w') as f:
                f.writelines(new_lines)
            return True
        return False

    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

# Process all route files
routes_dir = '/home/matt-woodworth/fastapi-operator-env/routes'
fixed_files = []

for filename in sorted(os.listdir(routes_dir)):
    if filename.endswith('.py') and not filename.startswith('__'):
        filepath = os.path.join(routes_dir, filename)
        if fix_empty_class(filepath):
            fixed_files.append(filename)
            print(f"Fixed: {filename}")

print(f"\nTotal fixed: {len(fixed_files)} files")

# Now test if files can be imported
print("\nTesting imports...")
import sys
sys.path.insert(0, '/home/matt-woodworth/fastapi-operator-env')

errors = []
for filename in ['access_control.py', 'admin_dashboard.py', 'ai_assistant.py']:
    try:
        module_name = filename[:-3]
        exec(f"from routes.{module_name} import router")
        print(f"✅ {filename} imports successfully")
    except Exception as e:
        errors.append(f"❌ {filename}: {e}")

if errors:
    print("\nRemaining errors:")
    for error in errors:
        print(error)
else:
    print("\n✅ All tested files import successfully!")