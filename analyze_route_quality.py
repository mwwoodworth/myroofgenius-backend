#!/usr/bin/env python3
"""
Analyze the quality of route implementations to determine which are real vs boilerplate
"""

import os
import re
import json
from pathlib import Path

def analyze_route_file(filepath):
    """Analyze a route file for implementation quality"""
    with open(filepath, 'r') as f:
        content = f.read()

    metrics = {
        'file': filepath.name,
        'lines': len(content.splitlines()),
        'has_db_queries': bool(re.search(r'(SELECT|INSERT|UPDATE|DELETE|FROM|WHERE)', content, re.I)),
        'has_real_logic': bool(re.search(r'(if |for |while |try:|except:|async def |await )', content)),
        'has_todo': bool(re.search(r'(TODO|FIXME|XXX|pass$|NotImplemented)', content, re.I)),
        'has_mock_data': bool(re.search(r'(return \{|"test"|"mock"|"sample"|"example")', content, re.I)),
        'num_endpoints': len(re.findall(r'@router\.(get|post|put|delete|patch)', content)),
        'has_models': bool(re.search(r'(BaseModel|Field|Optional|List|Dict)', content)),
        'has_error_handling': bool(re.search(r'(HTTPException|try:|except:|raise )', content)),
        'imports_db': bool(re.search(r'(asyncpg|psycopg|database|get_db)', content, re.I)),
        'quality_score': 0
    }

    # Calculate quality score
    if metrics['has_db_queries']: metrics['quality_score'] += 3
    if metrics['has_real_logic']: metrics['quality_score'] += 2
    if metrics['has_models']: metrics['quality_score'] += 1
    if metrics['has_error_handling']: metrics['quality_score'] += 1
    if metrics['imports_db']: metrics['quality_score'] += 1
    if not metrics['has_todo']: metrics['quality_score'] += 1
    if not metrics['has_mock_data']: metrics['quality_score'] += 1
    if metrics['num_endpoints'] > 2: metrics['quality_score'] += 1
    if metrics['lines'] > 100: metrics['quality_score'] += 1

    return metrics

def main():
    routes_dir = Path('routes')
    results = []

    # Analyze all route files
    for filepath in sorted(routes_dir.glob('*.py')):
        if filepath.name not in ['__init__.py', 'route_loader.py']:
            metrics = analyze_route_file(filepath)
            results.append(metrics)

    # Sort by quality score
    results.sort(key=lambda x: x['quality_score'], reverse=True)

    # Statistics
    total = len(results)
    high_quality = sum(1 for r in results if r['quality_score'] >= 8)
    medium_quality = sum(1 for r in results if 5 <= r['quality_score'] < 8)
    low_quality = sum(1 for r in results if r['quality_score'] < 5)

    print("=" * 80)
    print("ROUTE IMPLEMENTATION QUALITY ANALYSIS")
    print("=" * 80)
    print(f"Total route files: {total}")
    print(f"High quality (8+): {high_quality} ({high_quality/total*100:.1f}%)")
    print(f"Medium quality (5-7): {medium_quality} ({medium_quality/total*100:.1f}%)")
    print(f"Low quality (<5): {low_quality} ({low_quality/total*100:.1f}%)")
    print()

    # Top 10 best implementations
    print("TOP 10 BEST IMPLEMENTATIONS:")
    print("-" * 40)
    for r in results[:10]:
        flags = []
        if r['has_db_queries']: flags.append('DB')
        if r['has_real_logic']: flags.append('Logic')
        if r['has_error_handling']: flags.append('Errors')
        if r['num_endpoints'] > 2: flags.append(f"{r['num_endpoints']}eps")
        print(f"{r['quality_score']:2d}/12 - {r['file']:40s} [{', '.join(flags)}]")

    print()
    print("BOTTOM 10 IMPLEMENTATIONS (likely boilerplate):")
    print("-" * 40)
    for r in results[-10:]:
        issues = []
        if r['has_todo']: issues.append('TODO')
        if r['has_mock_data']: issues.append('Mock')
        if not r['has_db_queries']: issues.append('NoDB')
        if r['num_endpoints'] <= 2: issues.append('Few')
        print(f"{r['quality_score']:2d}/12 - {r['file']:40s} [{', '.join(issues)}]")

    # Summary stats
    print()
    print("IMPLEMENTATION STATISTICS:")
    print("-" * 40)
    db_count = sum(1 for r in results if r['has_db_queries'])
    logic_count = sum(1 for r in results if r['has_real_logic'])
    todo_count = sum(1 for r in results if r['has_todo'])
    mock_count = sum(1 for r in results if r['has_mock_data'])

    print(f"Routes with DB queries: {db_count}/{total} ({db_count/total*100:.1f}%)")
    print(f"Routes with real logic: {logic_count}/{total} ({logic_count/total*100:.1f}%)")
    print(f"Routes with TODOs: {todo_count}/{total} ({todo_count/total*100:.1f}%)")
    print(f"Routes with mock data: {mock_count}/{total} ({mock_count/total*100:.1f}%)")

    # Save detailed results
    with open('route_quality_report.json', 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nDetailed report saved to route_quality_report.json")

    return results

if __name__ == "__main__":
    main()