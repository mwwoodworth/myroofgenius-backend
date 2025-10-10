# START HERE - MANDATORY FOR EVERY SESSION
## THIS FILE PREVENTS CONTEXT LOSS

## STEP 1: RUN THIS IMMEDIATELY
```bash
# Check what's REAL right now
DATABASE_URL="postgresql://postgres.yomagoqdmxszqtdwuhab:Brain0ps2O2S@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require"

# Get latest context check
psql "$DATABASE_URL" -c "SELECT * FROM context_tracking ORDER BY check_timestamp DESC LIMIT 10;"

# Get current counts
psql "$DATABASE_URL" -c "SELECT * FROM current_system_context;"

# Check backend
curl -s https://brainops-backend-prod.onrender.com/api/v1/health | python3 -m json.tool | head -10
```

## STEP 2: REVIEW THESE FILES
1. `/home/mwwoodworth/code/MasterDBBrainOps81725.md` - ACTUAL database schema (300+ tables)
2. `/home/mwwoodworth/code/OPERATIONAL_CONTEXT_REQUIREMENTS.md` - Rules to prevent context loss
3. `/home/mwwoodworth/code/START_HERE_EVERY_SESSION.md` - This file

## STEP 3: KNOW THE TRUTH

### Database Tables (ACTUAL NAMES)
- `app_users` - NOT "users" (2 test accounts exist)
- `customers` - Only 3 records (NOT 1,089)
- `jobs` - Only 3 records
- `invoices` - 0 records (EMPTY)
- `estimates` - 0 records (EMPTY)
- `products` - 12 records
- `automations` - 8 configured but NOT executing
- `ai_agents` - 7 configured
- `centerpoint_*` tables - For CenterPoint sync
- `landing_*` tables - For data staging

### Backend Status
- **Version**: v4.49 (NOT v5.00)
- **URL**: https://brainops-backend-prod.onrender.com
- **Docker**: mwwoodworth/brainops-backend
- **Issues**: Revenue endpoints 404, automations not running

### What's NOT Working
1. Revenue/marketplace endpoints (404)
2. Automations (not executing)
3. CenterPoint sync (not running)
4. Most tables are EMPTY

## STEP 4: TRACK EVERY CHANGE
After ANY significant action:
```sql
INSERT INTO context_tracking (component, expected_value, actual_value, is_correct, notes)
VALUES ('what_changed', 'expected', 'actual', true/false, 'details');
```

## STEP 5: TEST BEFORE CLAIMING
- Don't say "authentication works" without testing login
- Don't say "1,089 customers" when there are 3
- Don't say "revenue endpoints work" without calling them
- Don't say "automations running" without checking executions

## THE GOLDEN RULES

1. **CHECK MasterDBBrainOps81725.md** - It has the REAL schema
2. **QUERY context_tracking** - It has the current state
3. **TEST endpoints** - Don't assume they work
4. **COUNT actual data** - Don't trust old claims
5. **UPDATE context_tracking** - After every change

## QUICK STATUS CHECK
```bash
# Run this for instant context
DATABASE_URL="postgresql://postgres.yomagoqdmxszqtdwuhab:Brain0ps2O2S@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require"
psql "$DATABASE_URL" -c "
SELECT component, actual_value, is_correct, notes 
FROM context_tracking 
WHERE NOT is_correct 
ORDER BY check_timestamp DESC;"
```

## CRITICAL FACTS TO REMEMBER
- System is ~65% operational, NOT 100%
- Backend is v4.49, NOT v5.00
- Only 3 customers, NOT 1,089
- app_users table, NOT users
- Most tables EXIST but are EMPTY
- Revenue endpoints DON'T WORK despite claims

## IF CONFUSED
1. Read this file
2. Check MasterDBBrainOps81725.md
3. Query context_tracking table
4. Test the actual system
5. Document findings

This is how we prevent context loss!