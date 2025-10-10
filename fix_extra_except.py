#!/usr/bin/env python3
"""Remove extra except block from task files"""

import glob

def fix_extra_except(filepath):
    """Fix extra except block issue"""
    with open(filepath, 'r') as f:
        lines = f.readlines()

    # Find and remove the extra except block (lines 52-62)
    new_lines = []
    skip_lines = False
    skip_count = 0

    for i, line in enumerate(lines):
        # Check if this is line 51 (0-indexed) and next line is the problematic except
        if i == 51 and i+1 < len(lines) and lines[i+1].strip() == 'except Exception:':
            new_lines.append(line)
            skip_lines = True
            skip_count = 0
            continue

        if skip_lines:
            skip_count += 1
            # Skip the except block and its content (about 11 lines)
            if skip_count <= 11:
                continue
            else:
                skip_lines = False

        new_lines.append(line)

    with open(filepath, 'w') as f:
        f.writelines(new_lines)
    return True

# Process all task files with the issue
task_files = glob.glob('routes/task_*.py')
print(f"Fixing extra except blocks in task files")

fixed_count = 0
for filepath in task_files:
    try:
        with open(filepath, 'r') as f:
            content = f.read()

        # Check if file has the problematic pattern
        if 'return [dict(row) for row in rows]\n    except Exception:' in content:
            # Simply remove the orphaned except block
            content = content.replace(
                'return [dict(row) for row in rows]\n    except Exception:\n        # Return sample data if table doesn\'t exist\n        return [\n            {\n                "id": str(uuid4()),',
                'return [dict(row) for row in rows]'
            )

            # Remove the rest of the orphaned except block
            lines = content.split('\n')
            new_lines = []
            skip_next_few = False
            skip_count = 0

            for i, line in enumerate(lines):
                if i > 0 and lines[i-1].strip() == 'return [dict(row) for row in rows]' and line.strip() == '':
                    # Check if there's orphaned code after this
                    if i+1 < len(lines) and 'for i in range(min(10, limit))' in lines[i+1]:
                        skip_next_few = True
                        skip_count = 0
                        continue

                if skip_next_few:
                    skip_count += 1
                    if skip_count <= 2:  # Skip the remaining lines of the list comprehension
                        continue
                    else:
                        skip_next_few = False

                new_lines.append(line)

            content = '\n'.join(new_lines)

            with open(filepath, 'w') as f:
                f.write(content)

            fixed_count += 1
            print(f"Fixed: {filepath}")
    except Exception as e:
        print(f"Error processing {filepath}: {e}")

print(f"\nTotal fixed: {fixed_count} files")

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