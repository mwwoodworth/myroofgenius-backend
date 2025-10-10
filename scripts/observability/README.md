# Render Observability Tools

## CRITICAL: These tools are PERMANENT infrastructure for BrainOps

### Tools Overview

1. **render_monitor.py** - Comprehensive deployment and health monitoring
2. **watch_deployment.py** - Real-time deployment tracking
3. **check_deployment.sh** - Quick bash status checker
4. **test_all_revenue_routes.py** - Revenue system validation

### Usage

#### Continuous Monitoring
```bash
python3 render_monitor.py --watch
```

#### Check Deployment Status
```bash
./check_deployment.sh
```

#### Watch Specific Deployment
```bash
python3 watch_deployment.py <deployment-id>
```

#### Test Revenue System
```bash
python3 test_all_revenue_routes.py
```

### Integration with CI/CD

These tools should be run:
- After every deployment
- During health checks
- As part of monitoring dashboards
- In response to alerts

### Environment Variables
```bash
export RENDER_API_KEY=rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx
export RENDER_SERVICE_ID=srv-d1tfs4idbo4c73di6k00
```

### Webhook Integration

Deploy webhook: `https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM`

### SSH Access

For debugging: `ssh srv-d1tfs4idbo4c73di6k00@ssh.oregon.render.com`