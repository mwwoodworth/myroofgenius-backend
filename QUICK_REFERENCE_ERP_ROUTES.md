# Quick Reference: ERP Routes

## Primary ERP Endpoints

All endpoints are at `/api/v1/erp/*` and require authentication.

### Available Endpoints

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/v1/erp/customers` | GET | List all customers (tenant-scoped) | Yes |
| `/api/v1/erp/jobs` | GET | List all jobs (tenant-scoped) | Yes |
| `/api/v1/erp/estimates` | GET | List all estimates (tenant-scoped) | Yes |
| `/api/v1/erp/invoices` | GET | List all invoices (tenant-scoped) | Yes |
| `/api/v1/erp/inventory` | GET | List all inventory items | Yes |
| `/api/v1/erp/dashboard` | GET | Dashboard metrics | Yes |
| `/api/v1/erp/dashboard/stats` | GET | Dashboard statistics | Yes |
| `/api/v1/erp/schedule` | GET | Scheduled jobs and events | Yes |

### Response Format

All endpoints return JSON with a `status` field:
- `"operational"` - Real database data
- `"offline"` - Fallback mock data (DB unavailable)

Example:
```json
{
  "customers": [...],
  "total": 100,
  "skip": 0,
  "limit": 100,
  "status": "operational"
}
```

## Route Files

| File | Purpose | Mounted |
|------|---------|---------|
| `routes/erp_complete.py` | Primary ERP implementation | Yes |
| `routes/erp_core_runtime.py` | Fallback data store (dependency) | No |
| `routes/weathercraft_integration.py` | WeatherCraft-specific | Yes |
| `routes/public_endpoints.py` | Public ERP access | Yes |

## Adding New ERP Endpoints

To add new ERP endpoints, edit `routes/erp_complete.py`:

```python
@router.get("/my-new-endpoint")
async def get_my_data(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Get my data."""
    try:
        # Your database logic here
        return {"data": [...], "status": "operational"}
    except HTTPException as exc:
        if _should_fallback(exc):
            # Fallback logic using STORE
            data = await STORE.my_fallback_method()
            return {"data": data, "status": "offline"}
        raise
```

## Troubleshooting

### Import Errors
If you see `ImportError: cannot import name 'STORE'`:
- Check that `routes/erp_core_runtime.py` exists
- Verify `erp_core_runtime` is in `EXCLUDED_MODULES`
- The file must be present but NOT mounted as routes

### Route Conflicts
If you see duplicate route warnings:
- Check `routes/route_loader.py` → `EXCLUDED_MODULES`
- Ensure only one router claims each prefix
- Review `archive/deprecated_routes/README.md` for context

### Fallback Not Working
If endpoints always return "offline":
- Check database connection in Render environment
- Verify `DATABASE_URL` is set
- Check Supabase credentials
- Review logs for connection errors

## Key Files

- `/home/matt-woodworth/dev/myroofgenius-backend/ERP_ROUTE_CONSOLIDATION_SUMMARY.md` - Full consolidation details
- `/home/matt-woodworth/dev/myroofgenius-backend/ERP_ROUTES_STRUCTURE.txt` - Visual route map
- `/home/matt-woodworth/dev/myroofgenius-backend/archive/deprecated_routes/README.md` - Archived routes info
- `/home/matt-woodworth/dev/myroofgenius-backend/routes/route_loader.py` - Route loading logic

## Last Updated

2025-12-15 - ERP route consolidation completed
