# 🎯 COMPLETE VERCEL FRONTEND SETUP GUIDE
## All Frontend Systems & Configuration
## Date: 2025-08-06

---

## 📋 FRONTEND SYSTEMS TO DEPLOY

### 1. ✅ MyRoofGenius (MAIN PRODUCT)
**Repository**: `mwwoodworth/myroofgenius-app`
**Vercel Project Name**: `myroofgenius-live`
**Status**: Already deployed and working

#### Vercel Settings:
```
Framework Preset: Next.js
Root Directory: ./
Build Command: npm run build
Output Directory: .next
Install Command: npm install
```

#### Environment Variables Required:
```
NEXT_PUBLIC_API_URL=https://brainops-backend-prod.onrender.com
NEXT_PUBLIC_SUPABASE_URL=https://yomagoqdmxszqtdwuhab.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=[your-key]
STRIPE_SECRET_KEY=[your-stripe-key]
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=[your-stripe-key]
```

---

### 2. ✅ Weathercraft ERP (INTERNAL + PUBLIC)
**Repository**: `mwwoodworth/weathercraft-erp`
**Vercel Project Name**: `weathercraft-erp`
**Status**: Deploying with fixes

#### Vercel Settings:
```
Framework Preset: Next.js
Root Directory: ./
Build Command: npm run build
Output Directory: .next
Install Command: npm install
```

#### Routes:
- `/` - Public Weathercraft company page
- `/dashboard` - Internal ERP with glassmorphism
- `/projects` - Project management
- `/crm` - Customer management

#### Environment Variables Required:
```
NEXT_PUBLIC_SUPABASE_URL=https://yomagoqdmxszqtdwuhab.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=[your-key]
NEXT_PUBLIC_API_URL=https://brainops-backend-prod.onrender.com
```

---

### 3. ⚠️ BrainOps Dashboard (NEEDS RECONFIGURATION)
**Repository**: `mwwoodworth/brainops-ai-assistant`
**Vercel Project Name**: `brainops-aios-ops`
**Status**: NEEDS FIXING - Wrong repository linked

#### CORRECT Vercel Settings:
```
Framework Preset: Next.js
Root Directory: dashboard    ← IMPORTANT!
Build Command: npm run build
Output Directory: .next
Install Command: npm install
```

#### How to Fix:
1. Go to Vercel project settings
2. Under "Git", disconnect current repository
3. Import from: `mwwoodworth/brainops-ai-assistant`
4. Set Root Directory to: `dashboard`
5. Deploy

#### Routes (After Fix):
- `/` - Main dashboard
- `/ultra-dashboard` - Ultra glassmorphism
- `/command-center` - Command center
- `/ultimate-os` - Complete OS view

#### Environment Variables Required:
```
NEXT_PUBLIC_BACKEND_URL=https://brainops-backend-prod.onrender.com
NEXT_PUBLIC_SUPABASE_URL=https://yomagoqdmxszqtdwuhab.supabase.co
```

---

### 4. ❓ Weathercraft App (OPTIONAL - REDUNDANT?)
**Repository**: `mwwoodworth/weathercraft-app`
**Vercel Project Name**: `weathercraft-app`
**Status**: Building

#### Decision Needed:
- **Option A**: DELETE - Use weathercraft-erp for public site
- **Option B**: KEEP - Separate public website

#### If Keeping - Vercel Settings:
```
Framework Preset: Next.js
Root Directory: ./
Build Command: npm run build
Output Directory: .next
Install Command: npm install
```

---

### 5. ❌ BrainStack Studio (DELETE)
**Repository**: `mwwoodworth/brainstackstudio-app`
**Vercel Project Name**: `brainstackstudio-app`
**Status**: Not needed
**Action**: DELETE from Vercel

---

## 🎯 FINAL RECOMMENDED SETUP

### KEEP THESE 3 PROJECTS:

1. **myroofgenius-live**
   - Main SaaS product
   - Already working perfectly
   
2. **weathercraft-erp**
   - Unified public + internal system
   - Glassmorphism at /dashboard
   
3. **brainops-dashboard** (rename from brainops-aios-ops)
   - Master control center
   - Needs repository reconnection

### DELETE THESE:
- weathercraft-app (redundant with weathercraft-erp)
- brainstackstudio-app (not needed)

---

## 🔧 IMMEDIATE ACTIONS

### 1. Fix BrainOps Dashboard:
```bash
# In Vercel:
1. Go to brainops-aios-ops project
2. Settings → Git → Disconnect
3. Import New → Select: brainops-ai-assistant
4. Set Root Directory: dashboard
5. Deploy
```

### 2. Clean Up:
```bash
# Delete redundant projects in Vercel:
- weathercraft-app (if using unified approach)
- brainstackstudio-app
```

---

## 📍 FINAL URLS

After setup, your systems will be at:

### MyRoofGenius:
```
https://myroofgenius.com
https://www.myroofgenius.com
```

### Weathercraft:
```
https://weathercraft-erp.vercel.app         # Public site
https://weathercraft-erp.vercel.app/dashboard  # ERP (glassmorphism)
```

### BrainOps:
```
https://brainops-aios-ops.vercel.app              # Main
https://brainops-aios-ops.vercel.app/ultra-dashboard  # Ultra
https://brainops-aios-ops.vercel.app/command-center   # Command
https://brainops-aios-ops.vercel.app/ultimate-os      # OS
```

---

## ✅ VERIFICATION CHECKLIST

After setup, verify:

- [ ] MyRoofGenius loads at myroofgenius.com
- [ ] Weathercraft ERP shows black glassmorphism at /dashboard
- [ ] BrainOps dashboard shows ultra design at /ultra-dashboard
- [ ] All API connections work (check network tab)
- [ ] Authentication works where needed
- [ ] Delete unused Vercel projects

---

## 🎨 GLASSMORPHISM LOCATIONS

| Project | URL | Design |
|---------|-----|--------|
| MyRoofGenius | / | Partial glassmorphism |
| Weathercraft ERP | /dashboard | Full black glassmorphism |
| BrainOps | /ultra-dashboard | Ultra premium glassmorphism |

---

*This is your complete frontend setup. Follow these configurations exactly!*