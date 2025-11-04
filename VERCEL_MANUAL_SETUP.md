# 🔧 VERCEL MANUAL SETUP INSTRUCTIONS
## To Fix BrainOps Dashboard Deployment

---

## ⚠️ THE PROBLEM
The `brainops-aios-ops` Vercel project can't find the dashboard directory.

---

## ✅ THE SOLUTION - DO THIS NOW:

### In Vercel Dashboard:

1. **Go to**: `brainops-aios-ops` project
2. **Click**: Settings (top menu)
3. **Find**: "General" section
4. **Locate**: "Root Directory"
5. **Change to**: `dashboard`
6. **Save** the changes
7. **Go to**: Deployments tab
8. **Click**: Redeploy (on latest deployment)

---

## 📍 AFTER REDEPLOYMENT:

### Your glassmorphism dashboards will be at:
```
https://brainops-aios-ops.vercel.app/
https://brainops-aios-ops.vercel.app/ultra-dashboard
https://brainops-aios-ops.vercel.app/command-center
https://brainops-aios-ops.vercel.app/ultimate-os
```

---

## 🎨 WHAT YOU'LL SEE:

- Black background with transparency
- Glassmorphic panels with blur effects
- Cyan and purple neon accents
- Real-time data visualizations
- Holographic UI elements
- Animated backgrounds

---

## 🔍 CURRENT STATUS OF ALL SYSTEMS:

### ✅ Working:
1. **MyRoofGenius** - https://myroofgenius.com
2. **Weathercraft ERP** - https://weathercraft-erp.vercel.app/dashboard

### 🔧 Needs This Fix:
3. **BrainOps Dashboard** - Set Root Directory to `dashboard`

### ❌ Can Delete:
4. **Weathercraft App** - Redundant
5. **BrainStack Studio** - Not needed

---

## 📝 VERCEL SETTINGS FOR BRAINOPS:

```
Root Directory: dashboard
Framework Preset: Next.js
Build Command: (auto-detected)
Output Directory: (auto-detected)
Install Command: (auto-detected)
```

---

*Just change Root Directory to "dashboard" and redeploy!*