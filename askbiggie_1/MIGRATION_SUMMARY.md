# 🚀 Render Migration Summary

## ✅ What We've Done

### 1. **Code Updates**
- ✅ **Redis**: Already compatible with Upstash Redis! No changes needed to the Redis client code.
- ✅ **RabbitMQ**: Updated to support CloudAMQP with SSL. Now supports both `RABBITMQ_URL` and individual connection parameters.

### 2. **Documentation Created**
- 📖 `RENDER_DEPLOYMENT_GUIDE.md` - Complete step-by-step deployment guide
- 📝 `RENDER_ENV_TEMPLATE.md` - Environment variables template
- ⚙️ `render.yaml` - Blueprint for automated deployment (optional)

---

## 🎯 Services You Need on Render

You need to create **3 separate services**:

1. **Backend API** (Web Service)
   - Runs the FastAPI application
   - Handles all API requests
   - Port: 8000

2. **Worker** (Background Worker)
   - Runs Dramatiq worker
   - Processes background jobs
   - Connects to same RabbitMQ as backend

3. **Frontend** (Web Service)
   - Runs Next.js application
   - Serves the UI
   - Port: 3000

---

## 📋 What You Need Before Starting

### 1. ✅ Upstash Redis TCP URL (Not REST!)

**CRITICAL**: You need the TCP connection URL, not the REST URL from your screenshot!

**How to get it:**
1. Go to: https://console.upstash.com/redis
2. Click on your database: `hardy-wildcat-7433`
3. Look for **"Redis URL"** with TLS enabled
4. Should look like: `rediss://default:YOUR_PASSWORD@hardy-wildcat-7433.upstash.io:6380`

**From your screenshot, you have the REST URL:**
```
REST URL: https://hardy-wildcat-7433.upstash.io
REST Token: AR0JAAlmcDI3ZWJhZGU3NTdkMDUQYjRjYWUxNDFlYzU3ZDllOTkzM3AyNzQzMw
```

**You need the TCP URL instead!** (It's on the same page, just scroll down or look for "Connect with redis-cli" section)

### 2. ✅ CloudAMQP RabbitMQ URL (You Already Have This!)

From your screenshot:
```
RABBITMQ_URL=amqps://jurfbueh:OAmfTSXP5cKYIMnjm3dozpnYvgOS1ReR@horse.lmq.cloudamap.com/jurfbueh
```

This is perfect! ✅

### 3. ✅ All Your Existing Environment Variables

You need to copy these from your current:
- Backend `.env` file (from Heroku)
- Frontend `.env.local` file (from Vercel)

**Get them by running:**
```bash
# Backend vars
cat suna/backend/.env

# Frontend vars
cat suna/frontend/.env.local
```

---

## 🚀 Quick Start Guide

### Option A: Using Render Dashboard (Recommended for First Time)

1. **Create Backend Service**
   - Go to Render Dashboard
   - Click "New +" → "Web Service"
   - Connect your GitHub repo
   - Configure:
     - Name: `askbiggie-backend`
     - Root Directory: `suna/backend`
     - Dockerfile: `suna/backend/Dockerfile`
     - Add all environment variables from `RENDER_ENV_TEMPLATE.md`

2. **Create Worker Service**
   - Click "New +" → "Background Worker"
   - Connect same repo
   - Configure:
     - Name: `askbiggie-worker`
     - Root Directory: `suna/backend`
     - Dockerfile: `suna/backend/Dockerfile`
     - Start Command: `uv run dramatiq --processes 4 --threads 4 run_agent_background`
     - Use **SAME** environment variables as Backend

3. **Create Frontend Service**
   - Click "New +" → "Web Service"
   - Connect same repo
   - Configure:
     - Name: `askbiggie-frontend`
     - Root Directory: `suna/frontend`
     - Dockerfile: `suna/frontend/Dockerfile`
     - Add frontend environment variables from template

4. **Update URLs**
   - After deployment, copy your actual URLs
   - Update these env vars in Backend & Worker:
     - `WEBHOOK_BASE_URL` → Your backend URL
     - `NEXT_PUBLIC_URL` → Your frontend URL
   - Update these env vars in Frontend:
     - `NEXT_PUBLIC_BACKEND_URL` → Your backend URL + `/api`
     - `NEXT_PUBLIC_URL` → Your frontend URL
   - Redeploy all services

### Option B: Using render.yaml (Advanced)

1. Push `suna/render.yaml` to your repo
2. Go to Render Dashboard → "New +" → "Blueprint"
3. Connect your repo and select `suna/render.yaml`
4. Render will create all 3 services automatically
5. Fill in the environment variables
6. Update URLs as in Option A, step 4

---

## 🔧 Critical Environment Variables

### For Backend & Worker (MUST HAVE):

```bash
# Redis - GET THE TCP URL FROM UPSTASH!
REDIS_URL=rediss://default:YOUR_PASSWORD@hardy-wildcat-7433.upstash.io:6380

# RabbitMQ - You already have this!
RABBITMQ_URL=amqps://jurfbueh:OAmfTSXP5cKYIMnjm3dozpnYvgOS1ReR@horse.lmq.cloudamap.com/jurfbueh

# These you need to copy from your existing .env:
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
ANTHROPIC_API_KEY=  # or OPENAI_API_KEY or OPENROUTER_API_KEY
TAVILY_API_KEY=
FIRECRAWL_API_KEY=
DAYTONA_API_KEY=
QSTASH_TOKEN=
QSTASH_CURRENT_SIGNING_KEY=
QSTASH_NEXT_SIGNING_KEY=
MCP_CREDENTIAL_ENCRYPTION_KEY=

# These will be updated after deployment:
WEBHOOK_BASE_URL=https://YOUR-BACKEND-URL.onrender.com
NEXT_PUBLIC_URL=https://YOUR-FRONTEND-URL.onrender.com
```

### For Frontend (MUST HAVE):

```bash
# Copy from your existing .env.local:
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=

# Update after backend is deployed:
NEXT_PUBLIC_BACKEND_URL=https://YOUR-BACKEND-URL.onrender.com/api
NEXT_PUBLIC_URL=https://YOUR-FRONTEND-URL.onrender.com

# Set to production:
NEXT_PUBLIC_ENV_MODE=PRODUCTION
```

---

## ✅ Verification Checklist

After deployment, verify everything works:

1. **Backend Health Check**
   ```
   https://YOUR-BACKEND-URL.onrender.com/api/health
   ```
   Should return: `{"status": "ok", ...}`

2. **Frontend Loads**
   ```
   https://YOUR-FRONTEND-URL.onrender.com
   ```
   Should show the UI

3. **Check Logs**
   - Backend logs should show: "Successfully connected to Redis"
   - Backend logs should show: "Using RabbitMQ broker with SSL"
   - Worker logs should show same connection messages
   - No error messages

4. **Test Functionality**
   - Try logging in
   - Try creating an agent task
   - Check if worker processes jobs

---

## 🔄 Post-Deployment Updates

After migration is complete, you'll need to update:

### 1. Update CORS in Backend (Later)

After frontend is deployed, update `suna/backend/api.py`:

```python
allowed_origins = [
    "https://askbiggie.ai", 
    "https://www.askbiggie.ai",
    "https://YOUR-FRONTEND-URL.onrender.com",  # ADD THIS
]
```

### 2. Update Supabase Redirect URLs (Later)
- Go to Supabase Dashboard → Authentication → URL Configuration
- Add: `https://YOUR-FRONTEND-URL.onrender.com/*`

### 3. Update Google OAuth (Later)
- Add redirect URI: `https://YOUR-FRONTEND-URL.onrender.com/auth/callback`

### 4. Update QStash Webhooks (Later)
- Update webhook URLs in QStash dashboard to point to your new backend URL

---

## 💡 Important Notes

### About Redis
- ✅ Your code already supports Upstash Redis via `REDIS_URL`
- ✅ Just need to get the TCP URL (not REST URL)
- ✅ Use the `rediss://` URL with TLS (port 6380)

### About RabbitMQ
- ✅ Your code has been updated to support CloudAMQP SSL
- ✅ Use the full URL from your screenshot
- ✅ It will automatically detect SSL from `amqps://` protocol

### About Render Service ID
- You mentioned: `srv-d3fh8smmcj7s738vchr0`
- This is just an ID Render assigns to services
- Each service (backend, worker, frontend) will get its own ID
- You don't need to set this manually

---

## 🐛 Common Issues & Solutions

### "Redis connection failed"
- **Issue**: Wrong Redis URL
- **Solution**: Make sure you're using the TCP URL (rediss://), not REST URL

### "RabbitMQ connection timeout"
- **Issue**: SSL not configured
- **Solution**: Use the full CloudAMQP URL with `amqps://`

### "Worker not processing jobs"
- **Issue**: Environment variables mismatch
- **Solution**: Make sure worker has EXACT same env vars as backend

### "Frontend can't connect to backend"
- **Issue**: Wrong backend URL or CORS
- **Solution**: 
  1. Check `NEXT_PUBLIC_BACKEND_URL` is correct
  2. Update CORS in backend to include frontend URL

---

## 📞 Next Steps

1. **Get Upstash Redis TCP URL** (most important!)
2. **Copy all your existing environment variables**
3. **Create the 3 services on Render**
4. **Test each service**
5. **Update URLs and redeploy**
6. **Update external services** (Supabase, Google OAuth, etc.)

---

## 📚 Files Created

- `RENDER_DEPLOYMENT_GUIDE.md` - Detailed deployment guide
- `RENDER_ENV_TEMPLATE.md` - Environment variables template
- `MIGRATION_SUMMARY.md` - This file
- `suna/render.yaml` - Render blueprint (optional)

---

## ✨ Summary

**What's Ready:**
- ✅ Code is compatible with Upstash Redis
- ✅ Code is compatible with CloudAMQP RabbitMQ
- ✅ Dockerfiles are ready for Render
- ✅ All configuration files are created

**What You Need:**
- 🔴 Upstash Redis TCP URL (get from console)
- ✅ CloudAMQP URL (you have this!)
- ✅ Your existing API keys (from .env files)

**Next Action:**
1. Get the Upstash Redis TCP URL
2. Start creating services on Render following the guide
3. Test and verify everything works

You're all set! 🚀

