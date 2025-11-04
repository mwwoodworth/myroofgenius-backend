#!/usr/bin/env python3
"""
Update production environment with correct database credentials
"""
import urllib.parse

# Correct database password
DB_PASSWORD = "Mww00dw0rth@2O1S$"
DB_PASSWORD_ENCODED = urllib.parse.quote(DB_PASSWORD)

print("🔧 Updating Production Environment")
print("=" * 50)

print(f"\n📝 Correct Database Password: {DB_PASSWORD}")
print(f"📝 URL-encoded Password: {DB_PASSWORD_ENCODED}")

print("\n🔗 Correct DATABASE_URL formats:")
print(f"1. Pooler: postgresql://postgres.yomagoqdmxszqtdwuhab:{DB_PASSWORD_ENCODED}@aws-0-us-east-2.pooler.supabase.com:5432/postgres")
print(f"2. Direct: postgresql://postgres:{DB_PASSWORD_ENCODED}@db.yomagoqdmxszqtdwuhab.supabase.co:5432/postgres")

print("\n⚡ Environment Variables to set in Render:")
print(f"DATABASE_URL=postgresql://postgres.yomagoqdmxszqtdwuhab:{DB_PASSWORD_ENCODED}@aws-0-us-east-2.pooler.supabase.com:5432/postgres")
print(f"SUPABASE_DB_PASSWORD={DB_PASSWORD}")
print(f"FALLBACK_DB_PASSWORD={DB_PASSWORD}")
print(f"ENCODED_DB_PASSWORD={DB_PASSWORD_ENCODED}")

print("\n📋 Copy this DATABASE_URL for Render:")
print(f"postgresql://postgres.yomagoqdmxszqtdwuhab:{DB_PASSWORD_ENCODED}@aws-0-us-east-2.pooler.supabase.com:5432/postgres")

print("\n⚠️  IMPORTANT: Update these in Render Dashboard immediately!")
print("1. Go to https://dashboard.render.com")
print("2. Select the brainops-backend service") 
print("3. Go to Environment tab")
print("4. Update DATABASE_URL with the value above")
print("5. Save and let it redeploy")

# Also update local .env.production file
print("\n📄 Updating local .env.production file...")
try:
    with open('/home/mwwoodworth/code/fastapi-operator-env/.env.production', 'r') as f:
        content = f.read()
    
    # Replace old password with new one
    old_db_url = "DATABASE_URL=postgresql://postgres.yomagoqdmxszqtdwuhab:Matt%402018Rock@aws-0-us-east-2.pooler.supabase.com:5432/postgres"
    new_db_url = f"DATABASE_URL=postgresql://postgres.yomagoqdmxszqtdwuhab:{DB_PASSWORD_ENCODED}@aws-0-us-east-2.pooler.supabase.com:5432/postgres"
    
    content = content.replace(old_db_url, new_db_url)
    content = content.replace("SUPABASE_DB_PASSWORD=Matt@2018Rock", f"SUPABASE_DB_PASSWORD={DB_PASSWORD}")
    
    with open('/home/mwwoodworth/code/fastapi-operator-env/.env.production', 'w') as f:
        f.write(content)
    
    print("✅ Local .env.production updated successfully")
except Exception as e:
    print(f"❌ Error updating .env.production: {e}")