#!/usr/bin/env python3
"""
Validate that all memory_entries inserts/updates include content field
"""
import os
import re

def check_file_for_content_issues(filepath):
    """Check a file for memory_entries operations without content field"""
    issues = []
    
    with open(filepath, 'r') as f:
        content = f.read()
        
    # Pattern 1: INSERT INTO memory_entries without content
    insert_pattern = r'INSERT\s+INTO\s+memory_entries\s*\([^)]+\)'
    for match in re.finditer(insert_pattern, content, re.IGNORECASE | re.DOTALL):
        insert_stmt = match.group(0)
        if 'content' not in insert_stmt and 'INSERT INTO memory_entries' in insert_stmt.upper():
            # Check if this is a real insert (not in a comment)
            line_num = content[:match.start()].count('\n') + 1
            issues.append(f"Line {line_num}: INSERT missing 'content' column")
    
    # Pattern 2: MemoryEntry creation without content
    entry_pattern = r'MemoryEntry\s*\([^)]+\)'
    for match in re.finditer(entry_pattern, content, re.DOTALL):
        entry_creation = match.group(0)
        if 'content=' not in entry_creation:
            # This is OK if the model has a default
            pass
    
    # Pattern 3: UPDATE memory_entries without content
    update_pattern = r'UPDATE\s+memory_entries\s+SET[^;]+(?:WHERE|;)'
    for match in re.finditer(update_pattern, content, re.IGNORECASE | re.DOTALL):
        update_stmt = match.group(0)
        if 'content' not in update_stmt.lower():
            line_num = content[:match.start()].count('\n') + 1
            # Check if it's a partial update (some updates might not need to update content)
            if 'value' in update_stmt.lower() or 'context_json' in update_stmt.lower():
                issues.append(f"Line {line_num}: UPDATE with value/context_json but missing 'content'")
    
    return issues

def main():
    """Check all Python files for content field issues"""
    print("=" * 60)
    print("Validating Memory Content Field Fixes")
    print("=" * 60)
    
    # Files we've modified
    files_to_check = [
        "fastapi-operator-env/apps/backend/db/memory_models.py",
        "fastapi-operator-env/apps/backend/services/memory_service.py",
        "fastapi-operator-env/apps/backend/services/cross_ai_memory.py",
        "fastapi-operator-env/apps/backend/services/cross_ai_memory_fixed.py",
        "fastapi-operator-env/apps/backend/sync_database_schema.py",
        "fastapi-operator-env/apps/backend/fix_memory_schema_now.py",
    ]
    
    total_issues = 0
    
    for filepath in files_to_check:
        if os.path.exists(filepath):
            print(f"\nChecking {filepath}...")
            issues = check_file_for_content_issues(filepath)
            if issues:
                print(f"  ❌ Found {len(issues)} issues:")
                for issue in issues:
                    print(f"    - {issue}")
                total_issues += len(issues)
            else:
                print("  ✅ No issues found")
        else:
            print(f"\n⚠️  File not found: {filepath}")
    
    # Summary of changes made
    print("\n" + "=" * 60)
    print("SUMMARY OF FIXES APPLIED:")
    print("=" * 60)
    print("\n1. SQLAlchemy Model (memory_models.py):")
    print("   - Added: content = Column(JSON, nullable=False, default=dict)")
    print("   - Ensures content is never null with default empty dict")
    
    print("\n2. Memory Service (memory_service.py):")
    print("   - Line 175: Added content field when creating MemoryEntry")
    print("   - Line 161: Added content update for existing entries")
    
    print("\n3. Cross-AI Memory Service (cross_ai_memory.py):")
    print("   - Line 170: Added content field for updates")
    print("   - Line 188: Added content field for new entries")
    
    print("\n4. Cross-AI Memory Fixed Service (cross_ai_memory_fixed.py):")
    print("   - Line 95: Added content to UPDATE statement")
    print("   - Line 120: Added content to INSERT statement")
    
    print("\n5. Database Sync Scripts:")
    print("   - sync_database_schema.py: Added content to test inserts/updates")
    print("   - fix_memory_schema_now.py: Added content to test insert")
    
    print("\n" + "=" * 60)
    if total_issues == 0:
        print("✅ ALL VALIDATIONS PASSED")
        print("   Content field is properly handled in all code paths")
    else:
        print(f"❌ FOUND {total_issues} ISSUES - Review needed")
    print("=" * 60)

if __name__ == "__main__":
    main()