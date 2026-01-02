# CRITICAL DEPLOYMENT SOP - MUST READ
## NEVER FORGET THESE REQUIREMENTS

## 🚨 RENDER PORT REQUIREMENT
**CRITICAL**: Render ALWAYS sets PORT=10000
- Your app MUST listen on the PORT environment variable
- NEVER hardcode port 8000 or any other port
- Use: `--port ${PORT:-10000}` in CMD
- This has caused multiple deployment failures

## Docker Build Requirements
```bash
# ALWAYS use this pattern in Dockerfile:
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}

# NOT THIS (WILL FAIL):
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Deployment Checklist
- [ ] PORT environment variable used (not hardcoded)
- [ ] Docker image tagged with version AND latest
- [ ] Push BOTH tags to Docker Hub
- [ ] Trigger Render deployment
- [ ] Monitor logs for port binding confirmation
- [ ] Wait for "Port detected" message

## Common Failures
1. **Port scan timeout** - App using wrong port
2. **404 on HEAD /** - Normal, Render health check
3. **No open ports detected** - PORT env var not used

## Correct Deployment Sequence
```bash
# 1. Build with correct port handling
docker build -t mwwoodworth/brainops-backend:vX.XX -f Dockerfile .

# 2. Tag as latest
docker tag mwwoodworth/brainops-backend:vX.XX mwwoodworth/brainops-backend:latest

# 3. Push both
docker push mwwoodworth/brainops-backend:vX.XX
docker push mwwoodworth/brainops-backend:latest

# 4. Trigger deployment
curl -X POST "https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=${RENDER_DEPLOY_KEY}"
```

## Test Endpoints
- Health: https://brainops-backend-prod.onrender.com/api/v1/health
- Root: https://brainops-backend-prod.onrender.com/

## Lessons Learned
- v5.00 FAILED: Hardcoded port 8000
- v5.01 FIXED: Uses PORT environment variable
- This SOP created after port binding failure

---
LAST UPDATED: 2025-08-17 after v5.00 deployment failure