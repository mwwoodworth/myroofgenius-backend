#!/usr/bin/env python3
"""
Migration Guard — Blocks dangerous SQL patterns in migration files.

Run as a pre-commit hook or CI gate. Scans SQL files for patterns that
would regress the security posture:
- GRANT to anon/authenticated/public
- DISABLE ROW LEVEL SECURITY
- ALTER DEFAULT PRIVILEGES granting to anon/authenticated
- DROP POLICY
- SECURITY DEFINER without explicit review marker

Exit 0 = pass, Exit 1 = blocked.

Usage:
  python3 scripts/migration_guard.py [file1.sql file2.sql ...]
  # Or scan all SQL files:
  python3 scripts/migration_guard.py --all
"""

import re
import sys
import glob
import os

DANGEROUS_PATTERNS = [
    (
        r"GRANT\s+.*\s+TO\s+(?:public|anon|authenticated)\b",
        "GRANT to public/anon/authenticated",
        "P0: Never grant directly to anon/authenticated. Use group roles.",
    ),
    (
        r"ALTER\s+TABLE\s+.*\s+DISABLE\s+ROW\s+LEVEL\s+SECURITY",
        "DISABLE ROW LEVEL SECURITY",
        "P0: RLS must remain enabled on all tables.",
    ),
    (
        r"ALTER\s+DEFAULT\s+PRIVILEGES.*GRANT.*TO\s+(?:anon|authenticated)\b",
        "Default privileges granting to anon/authenticated",
        "P0: Default privileges must not auto-grant to anon/authenticated.",
    ),
    (
        r"DROP\s+POLICY\b",
        "DROP POLICY",
        "P1: Dropping RLS policies requires explicit review. Add -- MIGRATION_GUARD_REVIEWED to suppress.",
    ),
    (
        r"SECURITY\s+DEFINER\b",
        "SECURITY DEFINER function",
        "P1: SECURITY DEFINER functions bypass RLS. Add -- MIGRATION_GUARD_REVIEWED to suppress.",
    ),
    (
        r"REVOKE\s+.*\s+FROM\s+(?:agent_worker|backend_worker|mcp_worker)\b",
        "REVOKE from worker roles",
        "P1: Revoking from worker roles may break production. Add -- MIGRATION_GUARD_REVIEWED to suppress.",
    ),
]

REVIEW_MARKER = "-- MIGRATION_GUARD_REVIEWED"


def scan_file(filepath: str) -> list[dict]:
    """Scan a single SQL file for dangerous patterns."""
    violations = []
    try:
        with open(filepath, "r") as f:
            content = f.read()
    except (OSError, IOError) as e:
        return [{"file": filepath, "line": 0, "pattern": "FILE_ERROR", "msg": str(e)}]

    lines = content.split("\n")
    for line_num, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        for regex, name, guidance in DANGEROUS_PATTERNS:
            if re.search(regex, stripped, re.IGNORECASE):
                # Check if the line or previous line has the review marker
                prev_line = lines[line_num - 2] if line_num > 1 else ""
                if REVIEW_MARKER in line or REVIEW_MARKER in prev_line:
                    continue
                violations.append(
                    {
                        "file": filepath,
                        "line": line_num,
                        "pattern": name,
                        "msg": guidance,
                        "text": stripped[:120],
                    }
                )
    return violations


def main():
    files_to_scan = []

    if "--all" in sys.argv:
        # Scan all SQL files in the repo
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for pattern in ["**/*.sql", "migrations/**/*.sql", "database/**/*.sql"]:
            files_to_scan.extend(
                glob.glob(os.path.join(repo_root, pattern), recursive=True)
            )
    else:
        files_to_scan = [f for f in sys.argv[1:] if f.endswith(".sql")]

    if not files_to_scan:
        print("Migration Guard: No SQL files to scan.")
        sys.exit(0)

    all_violations = []
    for filepath in sorted(set(files_to_scan)):
        all_violations.extend(scan_file(filepath))

    if not all_violations:
        print(
            f"Migration Guard: PASSED ({len(files_to_scan)} files scanned, 0 violations)"
        )
        sys.exit(0)

    print(
        f"Migration Guard: BLOCKED ({len(all_violations)} violations in {len(files_to_scan)} files)"
    )
    print()
    for v in all_violations:
        print(f"  {v['file']}:{v['line']}: {v['pattern']}")
        print(f"    {v['msg']}")
        print(f"    > {v['text']}")
        print()
    print(
        f"To suppress a finding, add '{REVIEW_MARKER}' on the same or preceding line."
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
