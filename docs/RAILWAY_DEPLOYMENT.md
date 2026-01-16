# 🚂 Railway Deployment Guide for PrismDocs

This guide covers deploying PrismDocs to Railway without build timeout issues.

## ⚠️ The Problem

Railway has a **20-minute build timeout** (30 minutes on Pro). Your app has heavy dependencies:

- **Docling** (~1.2GB with PyTorch/Transformers) - Takes 10-15 minutes alone
- **LibreOffice** (~500MB) - Adds 3-5 minutes
- Combined with other deps, you hit the timeout

## 🎯 Solutions

### Option 1: Light Build (Recommended for MVP)

**Build time: ~5 minutes** ✅

Uses `Dockerfile.railway-light` which **removes Docling**:

- Loses: OCR, advanced table extraction, layout analysis
- Keeps: PDF text extraction (pypdf), markdown, URLs, images

```bash
# In Railway dashboard, set:
# Settings → Build → Dockerfile Path: backend/Dockerfile.railway-light
```

### Option 2: Full Build with Caching

**First build: ~15-20 minutes** | **Subsequent builds: ~3-5 minutes** ⚡

Uses `Dockerfile.railway` with multi-stage builds:

- Layers are cached between deployments
- Only changed layers rebuild
- Requires Railway Pro for 30-min timeout

```bash
# In Railway dashboard, set:
# Settings → Build → Dockerfile Path: backend/Dockerfile.railway
```

### Option 3: Pre-built Docker Image (Fastest)

**Build time: 0 minutes** 🚀

Push a pre-built image to Docker Hub or GitHub Container Registry:

```bash
# Build locally (one-time)
cd backend
docker build -t yourusername/prismdocs-backend:latest -f Dockerfile.railway .
docker push yourusername/prismdocs-backend:latest

# In Railway:
# New Service → Docker Image → yourusername/prismdocs-backend:latest
```

---

## 📋 Step-by-Step Railway Deployment

### 1. Create Railway Project

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Create new project
railway init
```

### 2. Configure Backend Service

**Via Dashboard:**

1. New Service → Empty Service
2. Connect your GitHub repo
3. Settings → Build:

   - **Root Directory**: `backend`
   - **Build Command**: (leave empty - uses Dockerfile)
   - **Dockerfile Path**: `Dockerfile.railway-light` (or `Dockerfile.railway`)

4. Settings → Deploy:

   - **Start Command**: `python -m uvicorn doc_generator.infrastructure.api.main:app --host 0.0.0.0 --port $PORT`

5. Variables → Add:

   ```
   PORT=8000
   PYTHONUNBUFFERED=1
   PYTHONPATH=/app
   ENVIRONMENT=production

   # API Keys (use Railway secrets)
   ANTHROPIC_API_KEY=your_key
   OPENAI_API_KEY=your_key
   GOOGLE_API_KEY=your_key

   # Supabase (optional)
   SUPABASE_URL=your_url
   SUPABASE_KEY=your_key
   ```

### 3. Configure Frontend Service

1. New Service → Empty Service
2. Connect same GitHub repo
3. Settings → Build:
   - **Root Directory**: `frontend`
   - **Build Command**: `npm ci && npm run build`
4. Settings → Deploy:

   - **Start Command**: `npm start`

5. Variables:
   ```
   NEXT_PUBLIC_API_URL=https://your-backend.railway.app
   NEXT_PUBLIC_SUPABASE_URL=your_url
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your_key
   ```

---

## 🔧 Railway Configuration Files

### railway.json (root)

Place in your repo root:

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

### railway.toml (alternative)

```toml
[build]
builder = "dockerfile"
dockerfilePath = "backend/Dockerfile.railway-light"

[deploy]
healthcheckPath = "/api/health"
healthcheckTimeout = 120
restartPolicyType = "ON_FAILURE"
```

---

## 🚨 Troubleshooting

### Build Timeout

**Error:** `Build exceeded the 20 minute limit`

**Solutions:**

1. Switch to `Dockerfile.railway-light` (removes Docling)
2. Upgrade to Railway Pro (30-min limit)
3. Use pre-built Docker image

### Port Scan Timeout

**Error:** `Deployment failed: port scan timeout`

Your app took too long to start. Fixes:

1. Increase healthcheck `start-period` in Dockerfile
2. Use lazy loading for heavy imports (already done in `start.sh`)
3. Check that `PORT` environment variable is set

### Out of Memory

**Error:** `SIGKILL` or container crashes

Railway free tier has 512MB RAM. Docling needs ~2GB.

**Solutions:**

1. Use Railway Pro ($20/mo) for more RAM
2. Remove Docling with `Dockerfile.railway-light`
3. Set `WEB_CONCURRENCY=1` to limit workers

### Healthcheck Failing

**Error:** `Healthcheck failed`

```bash
# Debug locally first
docker build -t test -f backend/Dockerfile.railway-light backend/
docker run -p 8000:8000 -e PORT=8000 test

# Check if /api/health responds
curl http://localhost:8000/api/health
```

---

## 📊 Resource Requirements

| Configuration       | RAM   | CPU | Build Time | Recommended Tier |
| ------------------- | ----- | --- | ---------- | ---------------- |
| Light (no Docling)  | 512MB | 0.5 | 5 min      | Hobby ($5/mo)    |
| Full (with Docling) | 2GB   | 1.0 | 20 min     | Pro ($20/mo)     |
| With LibreOffice    | 3GB   | 1.0 | 25 min     | Pro + Team       |

---

## 🔄 Deployment Commands

### Via CLI

```bash
# Deploy backend only
railway up --service backend

# Deploy with specific Dockerfile
railway up --service backend --dockerfile backend/Dockerfile.railway-light

# Check logs
railway logs --service backend

# Open deployed app
railway open
```

### Via GitHub Actions

```yaml
name: Deploy to Railway

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Deploy Backend
        uses: bervProject/railway-deploy@main
        with:
          railway_token: ${{ secrets.RAILWAY_TOKEN }}
          service: backend
```

---

## ✅ Recommended Setup

For **fastest, most reliable deployment**:

1. **Use `Dockerfile.railway-light`** - Skip Docling, build in 5 minutes
2. **Railway Hobby tier** - $5/mo, 8GB RAM, sufficient for most use cases
3. **Pre-download models** - If using Docling later, cache models in Docker image
4. **Health checks** - Set 120s start period for heavy ML deps

Good luck with your deployment! 🚀
