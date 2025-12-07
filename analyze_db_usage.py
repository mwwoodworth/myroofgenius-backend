
import os
import csv
import re
import sys

# Configuration
TABLES_FILE = 'all_tables_categorized.csv'
SEARCH_DIRS = [
    '.',
    '../brainops-ai-agents'
]
IGNORE_DIRS = {
    '.git', 'node_modules', '__pycache__', '.venv', 'venv', 'dist', 'build', 
    '.idea', '.vscode', '.pytest_cache', 'site-packages'
}
# Only scan these extensions for code usage
CODE_EXTS = {
    '.py', '.js', '.ts', '.tsx', '.jsx', '.sh', '.go', '.rs', '.java'
}

IGNORE_FILES = {
    'analyze_db_usage.py',
    'all_tables_categorized.csv',
    'top_100_tables.csv',
    'schema_analysis.json', # Likely contains schema dump
    'schema_analysis_report.md'
}

def load_tables(filepath):
    tables = set()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'table_name' in row:
                    tables.add(row['table_name'].strip())
    except Exception as e:
        print(f"Error reading table list: {e}")
        sys.exit(1)
    return tables

def get_all_files(search_dirs):
    files_to_scan = []
    for d in search_dirs:
        if not os.path.exists(d):
            print(f"Warning: Directory {d} does not exist.")
            continue
            
        for root, dirs, files in os.walk(d):
            # Modify dirs in-place to skip ignored
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
            for file in files:
                if file in IGNORE_FILES:
                    continue
                # Check if file has a code extension
                _, ext = os.path.splitext(file)
                if ext in CODE_EXTS:
                    files_to_scan.append(os.path.join(root, file))
    return files_to_scan

def scan_codebase(files, known_tables):
    used_tables = set()
    # Regex to find potential table names: whole words composed of letters, numbers, underscores
    # stricter pattern: must have at least one underscore or be a known word? 
    # Actually, just matching known_tables is safer and faster.
    
    # Optimization: Pre-compile regex? No, 1500|... is too big.
    # Better: Find all word tokens in file, intersect with known_tables.
    
    word_pattern = re.compile(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b')
    
    for i, filepath in enumerate(files):
        if i % 100 == 0:
            print(f"Scanning file {i}/{len(files)}...", end='\r')
            
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                # Find all words
                words = set(word_pattern.findall(content))
                # Intersect with known tables
                found = words.intersection(known_tables)
                used_tables.update(found)
        except Exception as e:
            pass # Skip file read errors
            
    print(f"Scanning complete. Scanned {len(files)} files.")
    return used_tables

def find_duplicates(tables):
    duplicates = []
    sorted_tables = sorted(list(tables))
    
    # Pattern 1: agent_X vs ai_agent_X
    for t in sorted_tables:
        if t.startswith('agent_'):
            suffix = t[6:] # remove agent_ 
            ai_variant = f'ai_agent_{suffix}'
            if ai_variant in tables:
                duplicates.append((t, ai_variant, "Agent/AI_Agent Prefix"))
        elif t.startswith('ai_'):
            # Pattern 2: X vs ai_X
            base = t[3:]
            if base in tables:
                duplicates.append((base, t, "AI Prefix"))
    
    return duplicates

def main():
    print("Loading table definitions...")
    all_tables = load_tables(TABLES_FILE)
    print(f"Loaded {len(all_tables)} tables.")
    
    print("Locating source files...")
    files = get_all_files(SEARCH_DIRS)
    print(f"Found {len(files)} files to scan.")
    
    print("Scanning code for table references...")
    used_tables = scan_codebase(files, all_tables)
    print(f"Found {len(used_tables)} active tables.")
    
    orphaned = all_tables - used_tables
    
    print("\nAnalysis duplicated patterns...")
    dupes = find_duplicates(all_tables)
    
    # Output Report
    report_file = 'table_usage_report.txt'
    with open(report_file, 'w') as f:
        f.write("=== DATABASE TABLE USAGE REPORT ===\n\n")
        
        f.write(f"Total Tables: {len(all_tables)}\n")
        f.write(f"Active Tables: {len(used_tables)}\n")
        f.write(f"Orphaned Tables: {len(orphaned)}\n\n")
        
        f.write("--- DUPLICATE PATTERNS DETECTED ---\n")
        for t1, t2, reason in dupes:
            f.write(f"{t1} <-> {t2} ({reason})\n")
        
        f.write("\n--- ORPHANED TABLES (No code references found) ---\n")
        for t in sorted(list(orphaned)):
            f.write(f"{t}\n")
            
        f.write("\n--- ACTIVE TABLES ---\n")
        for t in sorted(list(used_tables)):
            f.write(f"{t}\n")

    print(f"Report generated: {report_file}")
    
    # Also print summary to stdout
    print("\nSummary:")
    print(f"Orphaned: {len(orphaned)}")
    print(f"Active: {len(used_tables)}")
    print(f"Potential Duplicates: {len(dupes)}")

if __name__ == "__main__":
    main()
