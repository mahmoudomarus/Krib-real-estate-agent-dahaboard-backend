# 🚀 Quick Start - Render Migration

## 🎯 Your Current Status

✅ **You Have:**
- CloudAMQP RabbitMQ URL (from screenshot)
- Upstash Redis (but need TCP URL, not REST)
- Render account created (Service ID: srv-d3fh8smmcj7s738vchr0)

🔴 **You Need:**
- Upstash Redis TCP URL (see below)
- Your existing environment variables

---

## 🔴 STEP 1: Get Upstash Redis TCP URL (5 mins)

**This is the MOST important step!**

1. Go to: https://console.upstash.com/redis
2. Click on: `hardy-wildcat-7433` (your database)
3. Find the **"Connect"** or **"Details"** section
4. Look for **"Redis URL"** (NOT "REST URL")
5. Copy the URL that looks like:
   ```
   rediss://default:YOUR_PASSWORD@hardy-wildcat-7433.upstash.io:6380
   ```

**Note:** It should start with `rediss://` (with two 's' for TLS)

---

## 📝 STEP 2: Get Your Existing Environment Variables (2 mins)

Run these commands to see what you currently have:

```bash
# Backend variables
cat /Users/mahmoudomar/askbiggie_1/suna/backend/.env

# Frontend variables
cat /Users/mahmoudomar/askbiggie_1/suna/frontend/.env.local
```

Copy these to a text file for reference.

---

## 🚀 STEP 3: Create Services on Render (20 mins)

### Service 1: Backend API

1. Go to: https://dashboard.render.com
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. **Settings:**
   - **Name**: `askbiggie-backend`
   - **Root Directory**: `suna/backend`
   - **Environment**: `Docker`
   - **Dockerfile Path**: `suna/backend/Dockerfile`
   - **Region**: Oregon (US West) or nearest to you
   - **Instance Type**: Starter (can upgrade later)

5. **Environment Variables** - Add these (use values from your .env file):

```bash
# Required
ENV_MODE=production
SUPABASE_URL=<from your .env>
SUPABASE_ANON_KEY=<from your .env>
SUPABASE_SERVICE_ROLE_KEY=<from your .env>

# Redis - USE THE TCP URL YOU GOT IN STEP 1!
REDIS_URL=rediss://default:YOUR_PASSWORD@hardy-wildcat-7433.upstash.io:6380

# RabbitMQ - USE THIS FROM YOUR SCREENSHOT!
RABBITMQ_URL=amqps://jurfbueh:OAmfTSXP5cKYIMnjm3dozpnYvgOS1ReR@horse.lmq.cloudamap.com/jurfbueh

# LLM (at least one)
ANTHROPIC_API_KEY=<from your .env>
MODEL_TO_USE=anthropic/claude-sonnet-4-20250514

# Search
TAVILY_API_KEY=<from your .env>
FIRECRAWL_API_KEY=<from your .env>
FIRECRAWL_URL=https://api.firecrawl.dev

# Daytona
DAYTONA_API_KEY=<from your .env>
DAYTONA_SERVER_URL=https://app.daytona.io/api
DAYTONA_TARGET=us

# QStash
QSTASH_URL=https://qstash.upstash.io
QSTASH_TOKEN=<from your .env>
QSTASH_CURRENT_SIGNING_KEY=<from your .env>
QSTASH_NEXT_SIGNING_KEY=<from your .env>
WEBHOOK_BASE_URL=https://askbiggie-backend.onrender.com

# MCP
MCP_CREDENTIAL_ENCRYPTION_KEY=<from your .env>

# Optional (if you have them)
RAPID_API_KEY=<from your .env>
SMITHERY_API_KEY=<from your .env>
OPENAI_API_KEY=<from your .env>
OPENROUTER_API_KEY=<from your .env>
STRIPE_SECRET_KEY=<from your .env>
STRIPE_WEBHOOK_SECRET=<from your .env>

# Will update after frontend is deployed
NEXT_PUBLIC_URL=http://localhost:3000
```

6. Click **"Create Web Service"**
7. Wait for deployment (~5-10 mins)
8. **Save the URL** (e.g., `https://askbiggie-backend-xyz.onrender.com`)

---

### Service 2: Worker

1. Click **"New +"** → **"Background Worker"**
2. Connect same GitHub repo
3. **Settings:**
   - **Name**: `askbiggie-worker`
   - **Root Directory**: `suna/backend`
   - **Environment**: `Docker`
   - **Dockerfile Path**: `suna/backend/Dockerfile`
   - **Docker Command**: `uv run dramatiq --processes 4 --threads 4 run_agent_background`
   - **Region**: Same as backend
   - **Instance Type**: Starter

4. **Environment Variables** - Use **EXACTLY THE SAME** as Backend above!

5. Click **"Create Background Worker"**

---

### Service 3: Frontend

1. Click **"New +"** → **"Web Service"**
2. Connect same GitHub repo
3. **Settings:**
   - **Name**: `askbiggie-frontend`
   - **Root Directory**: `suna/frontend`
   - **Environment**: `Docker`
   - **Dockerfile Path**: `suna/frontend/Dockerfile`
   - **Region**: Same as backend
   - **Instance Type**: Starter

4. **Environment Variables** - Add these:

```bash
NODE_ENV=production

# Supabase (same as backend)
NEXT_PUBLIC_SUPABASE_URL=<from your .env.local>
NEXT_PUBLIC_SUPABASE_ANON_KEY=<from your .env.local>

# Backend URL - USE THE URL YOU SAVED FROM BACKEND SERVICE!
NEXT_PUBLIC_BACKEND_URL=https://askbiggie-backend-xyz.onrender.com/api

# Frontend URL - will be provided by Render, use placeholder for now
NEXT_PUBLIC_URL=https://askbiggie-frontend.onrender.com

# Environment
NEXT_PUBLIC_ENV_MODE=PRODUCTION
```

5. Click **"Create Web Service"**
6. Wait for deployment
7. **Save the URL** (e.g., `https://askbiggie-frontend-abc.onrender.com`)

---

## 🔄 STEP 4: Update URLs (5 mins)

Now that all services are deployed, update the cross-references:

### Update Backend & Worker:
1. Go to Backend service → Environment
2. Update these variables:
   ```bash
   WEBHOOK_BASE_URL=https://askbiggie-backend-xyz.onrender.com
   NEXT_PUBLIC_URL=https://askbiggie-frontend-abc.onrender.com
   ```
3. Click "Save Changes"
4. Do the same for Worker service

### Update Frontend:
1. Go to Frontend service → Environment
2. Update these variables:
   ```bash
   NEXT_PUBLIC_BACKEND_URL=https://askbiggie-backend-xyz.onrender.com/api
   NEXT_PUBLIC_URL=https://askbiggie-frontend-abc.onrender.com
   ```
3. Click "Save Changes"

All services will automatically redeploy with new settings.

---

## ✅ STEP 5: Verify Everything Works (10 mins)

### Check Backend Health:
```
https://askbiggie-backend-xyz.onrender.com/api/health
```
Should return: `{"status": "ok", "timestamp": "...", "instance_id": "..."}`

### Check Frontend:
```
https://askbiggie-frontend-abc.onrender.com
```
Should load your UI.

### Check Logs:
1. Go to each service in Render
2. Click "Logs" tab
3. Look for:
   - Backend: "Successfully connected to Redis"
   - Backend: "Using RabbitMQ broker with SSL"
   - Worker: Same connection messages
   - No error messages

### Test Login:
1. Go to your frontend URL
2. Try logging in with Supabase auth
3. Try creating a simple agent task

---

## 📊 Summary of Your Configuration

### Redis (Upstash):
```bash
# URL format (you need to get this!)
REDIS_URL=rediss://default:PASSWORD@hardy-wildcat-7433.upstash.io:6380
```

### RabbitMQ (CloudAMQP):
```bash
# From your screenshot - ready to use!
RABBITMQ_URL=amqps://jurfbueh:OAmfTSXP5cKYIMnjm3dozpnYvgOS1ReR@horse.lmq.cloudamap.com/jurfbueh
```

### Services on Render:
1. **Backend**: Web Service (Docker)
2. **Worker**: Background Worker (Docker)
3. **Frontend**: Web Service (Docker)

---

## 🐛 Troubleshooting

### "Redis connection failed"
- ✅ Make sure you're using the TCP URL (`rediss://`)
- ✅ Not the REST URL (`https://`)
- ✅ URL should include port 6380

### "RabbitMQ connection failed"
- ✅ Use the full CloudAMQP URL with `amqps://`
- ✅ Copy it exactly from your screenshot

### "Worker not processing jobs"
- ✅ Check worker has same env vars as backend
- ✅ Check worker logs for errors

### "Frontend can't reach backend"
- ✅ Check `NEXT_PUBLIC_BACKEND_URL` is correct
- ✅ Should end with `/api`
- ✅ Check backend CORS logs

---

## 📞 What's Next? (Do LATER, after migration works)

1. ✅ Update Supabase redirect URLs
2. ✅ Update Google OAuth redirect URIs
3. ✅ Update QStash webhook URLs
4. ✅ Test all functionality
5. ✅ Set up custom domain (optional)
6. ✅ Monitor performance and scale if needed

---

## 📚 More Details?

See the full guides:
- `RENDER_DEPLOYMENT_GUIDE.md` - Complete deployment guide
- `RENDER_ENV_TEMPLATE.md` - Full environment variables template
- `MIGRATION_SUMMARY.md` - Migration overview

---

## ⏱️ Estimated Time

- **Step 1**: Get Redis URL - 5 minutes
- **Step 2**: Get env vars - 2 minutes
- **Step 3**: Create services - 20 minutes
- **Step 4**: Update URLs - 5 minutes
- **Step 5**: Verify - 10 minutes

**Total: ~40 minutes** 🚀

---

## 💡 Pro Tips

1. **Keep your .env files handy** - You'll need to copy values
2. **Use copy-paste carefully** - No typos in API keys!
3. **Save all URLs** - You'll need them for cross-references
4. **Check logs frequently** - They show what's happening
5. **One service at a time** - Don't rush, verify each one

---

## ✨ You're Ready!

Start with **Step 1** and follow the guide. You've got this! 🚀

**Questions? Check:**
- The detailed guides in the repo
- Render documentation: https://render.com/docs
- Your service logs on Render dashboard

