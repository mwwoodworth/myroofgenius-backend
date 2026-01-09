# Vercel Log Drain Secrets (DO NOT COMMIT REAL VALUES)

This file is intentionally a **template**. Store real secret values in a password manager and/or in the Vercel dashboard log drain configuration.

If any real values were ever committed to this repo, rotate them immediately.

## Required Values (Template)

### Log Drain Authentication Secret
```
<LOG_DRAIN_SECRET>
```

### Verification Header
```
x-vercel-verify: <X_VERCEL_VERIFY>
```

### Previous Secrets (Keep for Rotation History Only)
```
<ROTATED_SECRET>
```

## Expected Request Headers

```
Authorization: Bearer <LOG_DRAIN_SECRET>
```

