#!/usr/bin/env python3
"""
Fix CNS service to use correct table names
"""

def fix_cns_table_names():
    print("🔧 Fixing CNS table references...")

    # Read the current cns_service.py
    with open('cns_service.py', 'r') as f:
        content = f.read()

    # Table name mappings (wrong -> correct)
    table_mappings = {
        'system_memory': 'cns_memory',
        'task_memory': 'cns_tasks',
        'project_memory': 'cns_projects',
        'thread_memory': 'cns_threads',
        'system_learnings': 'cns_learning_patterns',
        'system_automations': 'cns_automations',
        'system_decisions': 'cns_decisions',
        'context_persistence': 'cns_context_persistence'
    }

    # Column name mappings for cns_memory table
    column_mappings = {
        # cns_memory specific
        'embeddings': 'embedding',  # Change embeddings to embedding
        'created_by': 'tags',  # We don't have created_by, use tags instead
        'source_system': 'category',  # Map source_system to category
    }

    # Fix table names
    changes_made = 0
    for old_table, new_table in table_mappings.items():
        if old_table in content:
            content = content.replace(f'FROM {old_table}', f'FROM {new_table}')
            content = content.replace(f'INTO {old_table}', f'INTO {new_table}')
            content = content.replace(f'UPDATE {old_table}', f'UPDATE {new_table}')
            content = content.replace(f'DELETE FROM {old_table}', f'DELETE FROM {new_table}')
            content = content.replace(f'"{old_table}"', f'"{new_table}"')
            content = content.replace(f"'{old_table}'", f"'{new_table}'")
            changes_made += 1
            print(f"  Fixed: {old_table} -> {new_table}")

    # Fix column references for cns_memory
    # The CNS schema has different column names than what the service expects

    # Fix the INSERT statement for cns_memory
    old_insert = """INSERT INTO system_memory (
                    id, memory_type, category, title, content,
                    embeddings, importance_score, expires_at,
                    tags, source_system, created_by, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6::vector, $7, $8, $9, $10, $11, $12)"""

    new_insert = """INSERT INTO cns_memory (
                    memory_id, memory_type, category, title, content,
                    embedding, importance_score, expires_at,
                    tags, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6::vector, $7, $8, $9, $10)"""

    if old_insert in content:
        content = content.replace(old_insert, new_insert)
        # Also fix the parameter list
        content = content.replace(
            """await conn.execute(
                query,
                memory_id,
                data.get('type', 'context'),
                data.get('category', 'general'),
                data.get('title', 'Untitled Memory'),
                json.dumps(data.get('content', data)),
                embedding_str,
                importance,
                expires_at,
                data.get('tags', []),
                data.get('source', 'api'),
                data.get('created_by', 'system'),
                json.dumps(data.get('metadata', {}))
            )""",
            """await conn.execute(
                query,
                memory_id,
                data.get('type', 'context'),
                data.get('category', 'general'),
                data.get('title', 'Untitled Memory'),
                json.dumps(data.get('content', data)),
                embedding_str,
                importance,
                expires_at,
                data.get('tags', []),
                json.dumps(data.get('metadata', {}))
            )"""
        )
        print("  Fixed: cns_memory INSERT statement")

    # Fix SELECT statements
    content = content.replace('SELECT id FROM', 'SELECT memory_id FROM')
    content = content.replace('RETURNING id', 'RETURNING memory_id')

    # Fix task table column references
    content = content.replace('task_memory WHERE task_id', 'cns_tasks WHERE task_id')
    content = content.replace('INSERT INTO task_memory', 'INSERT INTO cns_tasks')

    # Fix project table references
    content = content.replace('INSERT INTO project_memory', 'INSERT INTO cns_projects')
    content = content.replace('UPDATE project_memory', 'UPDATE cns_projects')
    content = content.replace('FROM project_memory', 'FROM cns_projects')

    # Write the fixed content
    with open('cns_service.py', 'w') as f:
        f.write(content)

    print(f"\n✅ Fixed {len(table_mappings)} table references")
    print("✅ CNS service updated with correct table names")

    return True

if __name__ == "__main__":
    fix_cns_table_names()
    print("\nNext steps:")
    print("  1. Build Docker image v135.0.0")
    print("  2. Push to Docker Hub")
    print("  3. Deploy to Render")