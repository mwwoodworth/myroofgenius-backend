# NEXTAUTH_URL Configuration for All Projects

## 🔧 Current Configuration

Based on your setup with Vercel shared environment variables, here's how NEXTAUTH_URL should be configured:

### 1. MyRoofGenius (Primary)
```env
NEXTAUTH_URL=https://myroofgenius.com
```
- Set at the **Vercel Team Level** (shared)
- Used by MyRoofGenius for authentication

### 2. WeatherCraft ERP
```env
NEXTAUTH_URL=https://weathercraft-erp.vercel.app
```
- Set at the **Project Level** in Vercel
- Overrides the shared value for this project only

### 3. WeatherCraft Public Site
```env
# No authentication needed - public site only
```

### 4. BrainOps AIOS
```env
NEXTAUTH_URL=https://brainops-aios-ops.vercel.app
```
- Set at the **Project Level** in Vercel
- Overrides the shared value for this project only

## 📋 Configuration Steps

### For MyRoofGenius (Already Set)
Since you mentioned it's already pointing to MyRoofGenius at the team level, no action needed.

### For WeatherCraft ERP
1. Go to https://vercel.com/[your-team]/weathercraft-erp/settings/environment-variables
2. Add a **Project-specific** environment variable:
   - Key: `NEXTAUTH_URL`
   - Value: `https://weathercraft-erp.vercel.app`
   - Environment: Production, Preview, Development
3. Redeploy for changes to take effect

### For BrainOps AIOS
1. Go to https://vercel.com/[your-team]/brainops-aios-ops/settings/environment-variables
2. Add a **Project-specific** environment variable:
   - Key: `NEXTAUTH_URL`
   - Value: `https://brainops-aios-ops.vercel.app`
   - Environment: Production, Preview, Development
3. Redeploy for changes to take effect

## 🔍 How It Works

1. **Vercel Environment Variable Precedence**:
   - Project-level variables override Team-level variables
   - This allows you to have a default (MyRoofGenius) but override per project

2. **NextAuth Behavior**:
   - Uses NEXTAUTH_URL to determine callback URLs
   - Critical for OAuth providers (Google, GitHub)
   - Must match the actual deployment URL

## ✅ Verification

After setting up, verify each project:

```bash
# Check MyRoofGenius
curl -s https://myroofgenius.com/api/auth/providers | jq .

# Check WeatherCraft ERP
curl -s https://weathercraft-erp.vercel.app/api/auth/providers | jq .

# Check BrainOps AIOS
curl -s https://brainops-aios-ops.vercel.app/api/auth/providers | jq .
```

## 🚨 Common Issues

1. **Login Redirect Errors**
   - Symptom: After login, redirected to wrong domain
   - Fix: Ensure NEXTAUTH_URL matches deployment URL

2. **OAuth Callback Errors**
   - Symptom: "Redirect URI mismatch" from Google/GitHub
   - Fix: Update OAuth app settings to include new callback URL

3. **Cookie Domain Issues**
   - Symptom: Session not persisting
   - Fix: Check NEXTAUTH_URL protocol (https:// required)

## 📝 OAuth Callback URLs

For each project, add these to your OAuth providers:

### MyRoofGenius
- Google: `https://myroofgenius.com/api/auth/callback/google`
- GitHub: `https://myroofgenius.com/api/auth/callback/github`

### WeatherCraft ERP
- Google: `https://weathercraft-erp.vercel.app/api/auth/callback/google`
- GitHub: `https://weathercraft-erp.vercel.app/api/auth/callback/github`

### BrainOps AIOS
- Google: `https://brainops-aios-ops.vercel.app/api/auth/callback/google`
- GitHub: `https://brainops-aios-ops.vercel.app/api/auth/callback/github`

---

**Last Updated**: August 5, 2025