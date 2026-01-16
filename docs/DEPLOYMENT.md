# 🚀 PrismDocs Deployment Guide

Deploy PrismDocs with **Railway (backend)** + **Vercel (frontend)** for the best performance and free tier options.

---

## 📋 Deployment Overview

| Component    | Platform | Build Time     | Cost              |
| ------------ | -------- | -------------- | ----------------- |
| **Backend**  | Railway  | ~5 min (light) | Free tier / $5/mo |
| **Frontend** | Vercel   | ~2 min         | Free tier         |

```
┌─────────────────┐         ┌─────────────────┐
│    Vercel       │         │    Railway      │
│   (Frontend)    │────────▶│   (Backend)     │
│   Next.js UI    │  API    │   FastAPI       │
│   prismdocs.app │ calls   │   api.railway   │
└─────────────────┘         └─────────────────┘
```

---

## 🔺 Part 1: Vercel Frontend Deployment

Vercel is the **recommended** platform for the Next.js frontend - it's fast, free, and requires minimal configuration.

### Quick Deploy (Recommended)

1. **Go to** [vercel.com](https://vercel.com) and sign in with GitHub
2. **Click** "Add New Project"
3. **Import** your `PrismDocs` repository
4. **Configure:**
   - **Root Directory**: `frontend`
   - **Framework Preset**: Next.js (auto-detected)
5. **Add Environment Variables:**
   ```
   NEXT_PUBLIC_API_URL=https://your-backend.railway.app
   NEXT_PUBLIC_SUPABASE_URL=your_supabase_url (optional)
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_key (optional)
   ```
6. **Click** "Deploy"

That's it! Vercel handles everything automatically.

### Using vercel.json (Already Configured)

Your repo has two `vercel.json` options:

**Option A: Root-level** (`vercel.json`) - For monorepo deployment:

```json
{
  "buildCommand": "cd frontend && npm install && npm run build",
  "outputDirectory": "frontend/.next",
  "framework": "nextjs",
  "installCommand": "cd frontend && npm install",
  "regions": ["iad1"]
}
```

**Option B: Frontend-level** (`frontend/vercel.json`) - If you set root to `frontend`:

```json
{
  "framework": "nextjs",
  "regions": ["iad1"]
}
```

### Vercel CLI Deployment

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy from project root
vercel --prod

# Or deploy frontend only
cd frontend && vercel --prod
```

### Environment Variables

| Variable                        | Required    | Description                     |
| ------------------------------- | ----------- | ------------------------------- |
| `NEXT_PUBLIC_API_URL`           | ✅ Yes      | Your Railway backend URL        |
| `NEXT_PUBLIC_SUPABASE_URL`      | ❌ Optional | Supabase project URL (for auth) |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | ❌ Optional | Supabase anon key (for auth)    |

> **Note:** No LLM API keys needed! Users provide their own keys via the UI (BYOK model).

---

## 🚂 Part 2: Railway Backend Deployment

Railway hosts the FastAPI backend. The main challenge is **build timeouts** due to heavy dependencies.

### ⚠️ The Build Timeout Problem

Railway has a **20-minute build timeout** (30 minutes on Pro). Your app has heavy dependencies:

- **Docling** (~1.2GB with PyTorch/Transformers) - Takes 10-15 minutes alone
- **LibreOffice** (~500MB) - Adds 3-5 minutes
- Combined with other deps, you hit the timeout

### 🎯 Solutions

#### Option 1: Light Build (Recommended) ⭐

**Build time: ~5 minutes** ✅

Uses `Dockerfile.railway-light` which **removes Docling**:

- ❌ Loses: OCR, advanced table extraction, layout analysis
- ✅ Keeps: PDF text extraction (pypdf), markdown, URLs, DOCX, PPTX

```bash
# In Railway dashboard:
# Settings → Build → Dockerfile Path: backend/Dockerfile.railway-light
```

#### Option 2: Full Build with Caching

**First build: ~15-20 minutes** | **Subsequent builds: ~3-5 minutes** ⚡

Uses `Dockerfile.railway` with multi-stage builds:

- Layers are cached between deployments
- Requires Railway Pro for 30-min timeout

#### Option 3: Pre-built Docker Image (Zero Build Time)

**Build time: 0 minutes** 🚀

```bash
# Build locally (one-time)
cd backend
docker build -t yourusername/prismdocs-backend:latest -f Dockerfile.railway-light .
docker push yourusername/prismdocs-backend:latest

# In Railway: New Service → Docker Image → yourusername/prismdocs-backend:latest
```

### Step-by-Step Railway Setup

#### 1. Create Railway Project

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Create new project
railway init
```

#### 2. Configure Backend Service

**Via Dashboard:**

1. New Service → Empty Service
2. Connect your GitHub repo
3. Settings → Build:

   - **Root Directory**: `backend`
   - **Dockerfile Path**: `Dockerfile.railway-light`

4. Settings → Deploy:

   - **Start Command**: `python -m uvicorn doc_generator.infrastructure.api.main:app --host 0.0.0.0 --port $PORT`

5. Variables → Add:

   ```
   PORT=8000
   PYTHONUNBUFFERED=1
   PYTHONPATH=/app
   ENVIRONMENT=production

   # Optional (for database logging/auth)
   SUPABASE_URL=your_url
   SUPABASE_KEY=your_key
   ```

   > **Note:** LLM API keys (Gemini/OpenAI/Anthropic) are NOT required on the server!
   > PrismDocs uses **BYOK (Bring Your Own Key)** - users enter their keys in the frontend.

6. **Get your backend URL** (e.g., `https://prismdocs-api-production.up.railway.app`)

7. **Update Vercel** with the backend URL in `NEXT_PUBLIC_API_URL`

### Railway Configuration Files

**railway.json** (place in repo root):

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "backend/Dockerfile.railway-light"
  },
  "deploy": {
    "healthcheckPath": "/api/health",
    "healthcheckTimeout": 120,
    "restartPolicyType": "ON_FAILURE"
  }
}
```

---

## 🔗 Connecting Frontend to Backend

After deploying both, update Vercel with the Railway backend URL:

1. Go to Vercel Dashboard → Your Project → Settings → Environment Variables
2. Set `NEXT_PUBLIC_API_URL` to your Railway URL:
   ```
   NEXT_PUBLIC_API_URL=https://prismdocs-api-production.up.railway.app
   ```
3. Redeploy the frontend

---

## 🚨 Troubleshooting

### Railway: Build Timeout

**Error:** `Build exceeded the 20 minute limit`

**Solutions:**

1. Use `Dockerfile.railway-light` (removes Docling)
2. Upgrade to Railway Pro (30-min limit)
3. Use pre-built Docker image

### Railway: Port Scan Timeout

**Error:** `Deployment failed: port scan timeout`

**Solutions:**

1. Ensure `PORT` environment variable is set
2. Check that app binds to `0.0.0.0`, not `localhost`
3. Increase healthcheck start period

### Railway: Out of Memory

**Error:** `SIGKILL` or container crashes

**Solutions:**

1. Use `Dockerfile.railway-light` (smaller footprint)
2. Upgrade to Railway Pro for more RAM
3. Set `WEB_CONCURRENCY=1`

### Vercel: Build Fails

**Error:** Build errors

**Solutions:**

1. Ensure `frontend/` is set as root directory
2. Check `package.json` has correct build scripts
3. Verify environment variables are set

### CORS Errors

**Error:** `Access-Control-Allow-Origin` errors

**Solutions:**

1. Verify `NEXT_PUBLIC_API_URL` points to Railway backend
2. Check Railway backend CORS settings allow Vercel domain

---

## 📊 Resource Requirements

| Configuration       | RAM   | Build Time | Railway Tier         |
| ------------------- | ----- | ---------- | -------------------- |
| Light (no Docling)  | 512MB | 5 min      | Free / Hobby ($5/mo) |
| Full (with Docling) | 2GB   | 20 min     | Pro ($20/mo)         |

| Frontend | RAM | Build Time | Vercel Tier |
| -------- | --- | ---------- | ----------- |
| Next.js  | 1GB | 2 min      | Free / Pro  |

---

## ✅ Recommended Production Setup

```
┌─────────────────────────────────────────────────────┐
│                    PrismDocs                         │
├─────────────────────┬───────────────────────────────┤
│      Frontend       │          Backend              │
├─────────────────────┼───────────────────────────────┤
│  Platform: Vercel   │  Platform: Railway            │
│  Framework: Next.js │  Framework: FastAPI           │
│  Build: ~2 min      │  Build: ~5 min (light)        │
│  Cost: Free         │  Cost: Free / $5/mo           │
│  CDN: Global        │  Region: US East              │
└─────────────────────┴───────────────────────────────┘
```

### Quick Checklist

- [ ] Deploy backend to Railway with `Dockerfile.railway-light`
- [ ] Get Railway backend URL
- [ ] Deploy frontend to Vercel
- [ ] Set `NEXT_PUBLIC_API_URL` in Vercel to Railway URL
- [ ] (Optional) Configure Supabase for auth/logging
- [ ] Test the full flow!

---

## 🔄 CI/CD with GitHub Actions

### Auto-deploy on Push

Both Railway and Vercel support automatic deployments on `git push`. No GitHub Actions needed!

- **Vercel**: Auto-deploys when you push to `main`
- **Railway**: Auto-deploys when you push to `main`

### Manual GitHub Action (Optional)

```yaml
name: Deploy PrismDocs

on:
  push:
    branches: [main]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Railway
        uses: bervProject/railway-deploy@main
        with:
          railway_token: ${{ secrets.RAILWAY_TOKEN }}
          service: backend

  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-args: "--prod"
```

---

Good luck with your deployment! 🚀
