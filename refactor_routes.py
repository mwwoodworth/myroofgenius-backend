import os
import re

def refactor_routes():
    routes_dir = "/home/matt-woodworth/dev/myroofgenius-backend/routes"
    db_import_statement = "from ..database import get_db\n"

    # Regex to find the old get_db function
    get_db_regex = re.compile(r"async def get_db\(\):\s*conn = await asyncpg\.connect\(.*\)\s*try:\s*yield conn\s*finally:\s*await conn\.close\(\)", re.DOTALL)
    # Regex to find old postgresql uris
    db_url_regex = re.compile(r'[\'"]postgresql://postgres.*?[\'"]')

    for filename in os.listdir(routes_dir):
        if filename.endswith(".py"):
            filepath = os.path.join(routes_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                print(f"Skipping file with encoding issues: {filename}")
                continue


            # Remove old get_db function
            content = get_db_regex.sub("", content)
            
            # Remove old postgresql uris
            content = db_url_regex.sub('""', content)

            # Add the new import statement if it's not already there
            if db_import_statement not in content and 'Depends(get_db)' in content:
                # Find the first import and add it after
                import_match = re.search(r"^(?:from .* import .*|import .*)$", content, re.MULTILINE)
                if import_match:
                    content = content[:import_match.end()] + "\n" + db_import_statement + content[import_match.end():]
                else:
                    # if no imports, add at the top
                    content = db_import_statement + content


            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

    print("Refactoring complete.")

if __name__ == "__main__":
    refactor_routes()
