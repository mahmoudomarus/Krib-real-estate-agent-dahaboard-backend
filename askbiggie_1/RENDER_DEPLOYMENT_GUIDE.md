# Render Deployment Guide for Ask Biggie

## 🎯 Services to Create on Render

You need to create **3 services**:

1. **Backend API** (Web Service)
2. **Worker** (Background Worker)
3. **Frontend** (Web Service)

---

## 📋 Step-by-Step Setup

### Step 1: Get Upstash Redis Connection URL

**Important**: You need the **TCP connection URL**, not the REST URL.

1. Go to your Upstash Redis dashboard: https://console.upstash.com/redis
2. Click on your Redis database (`hardy-wildcat-7433`)
3. Look for **"Connect"** section
4. Find the **"Redis URL"** (NOT the REST URL)
5. It should look like: `redis://default:your-password@hardy-wildcat-7433.upstash.io:6379`
   - Or with TLS: `rediss://default:your-password@hardy-wildcat-7433.upstash.io:6380`

**Use the `rediss://` URL (with TLS) for production!**

---

### Step 2: RabbitMQ Configuration from CloudAMQP

From your screenshot, here are your CloudAMQP credentials:

```bash
RABBITMQ_URL=amqps://jurfbueh:OAmfTSXP5cKYIMnjm3dozpnYvgOS1ReR@horse.lmq.cloudamap.com/jurfbueh
RABBITMQ_HOST=horse.lmq.cloudamap.com
RABBITMQ_PORT=5671  # Use 5671 for TLS, 5672 for non-TLS
RABBITMQ_USER=jurfbueh
RABBITMQ_PASSWORD=OAmfTSXP5cKYIMnjm3dozpnYvgOS1ReR
RABBITMQ_VHOST=jurfbueh
RABBITMQ_USE_SSL=true
```

---

## 🚀 Service 1: Backend API (Web Service)

### Create Service
1. Go to Render Dashboard
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Select the repository with your code

### Configuration

**Basic Settings:**
- **Name**: `askbiggie-backend` (or your preferred name)
- **Region**: Choose closest to your users (e.g., `Oregon (US West)`)
- **Branch**: `main` (or your default branch)
- **Root Directory**: `suna/backend`
- **Runtime**: `Python 3`

**Build & Deploy:**

**Option A: Using Dockerfile (Recommended)**
- **Build Command**: (leave empty - Dockerfile will handle it)
- **Start Command**: (leave empty - Dockerfile will handle it)
- **Dockerfile Path**: `suna/backend/Dockerfile`

**Option B: Using Native Build**
- **Build Command**: 
```bash
pip install uv && uv sync
```
- **Start Command**: 
```bash
uv run gunicorn api:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --timeout 1800 --graceful-timeout 600 --keep-alive 1800
```

**Instance Type**: Choose based on your needs (start with Starter or Standard)

### Environment Variables

Add these environment variables in Render:

```bash
# Environment Mode
ENV_MODE=production

# Database & Auth (from your existing Supabase)
SUPABASE_URL=your-supabase-url
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key

# Redis - Upstash (GET THE TCP URL FROM UPSTASH CONSOLE!)
REDIS_URL=rediss://default:YOUR_PASSWORD@hardy-wildcat-7433.upstash.io:6380

# OR use individual settings:
REDIS_HOST=hardy-wildcat-7433.upstash.io
REDIS_PORT=6380
REDIS_PASSWORD=your-upstash-password
REDIS_SSL=true

# RabbitMQ - CloudAMQP
RABBITMQ_HOST=horse.lmq.cloudamap.com
RABBITMQ_PORT=5671
RABBITMQ_USER=jurfbueh
RABBITMQ_PASSWORD=OAmfTSXP5cKYIMnjm3dozpnYvgOS1ReR
RABBITMQ_VHOST=jurfbueh
RABBITMQ_USE_SSL=true

# LLM Provider (at least one required)
ANTHROPIC_API_KEY=your-anthropic-key
OPENAI_API_KEY=your-openai-key
OPENROUTER_API_KEY=your-openrouter-key
MODEL_TO_USE=anthropic/claude-sonnet-4-20250514

# Search & Scraping
TAVILY_API_KEY=your-tavily-key
FIRECRAWL_API_KEY=your-firecrawl-key
FIRECRAWL_URL=https://api.firecrawl.dev

# Agent Execution
DAYTONA_API_KEY=your-daytona-key
DAYTONA_SERVER_URL=https://app.daytona.io/api
DAYTONA_TARGET=us

# Background Jobs & Webhooks
QSTASH_URL=https://qstash.upstash.io
QSTASH_TOKEN=your-qstash-token
QSTASH_CURRENT_SIGNING_KEY=your-current-signing-key
QSTASH_NEXT_SIGNING_KEY=your-next-signing-key
WEBHOOK_BASE_URL=https://askbiggie-backend.onrender.com  # Your backend URL on Render

# MCP Configuration
MCP_CREDENTIAL_ENCRYPTION_KEY=your-generated-encryption-key

# Optional APIs
RAPID_API_KEY=your-rapidapi-key
SMITHERY_API_KEY=your-smithery-key

# Stripe (if you're using billing)
STRIPE_SECRET_KEY=your-stripe-secret-key
STRIPE_WEBHOOK_SECRET=your-stripe-webhook-secret

# Optional Integrations
PIPEDREAM_PROJECT_ID=your-pipedream-project-id
PIPEDREAM_CLIENT_ID=your-pipedream-client-id
PIPEDREAM_CLIENT_SECRET=your-pipedream-client-secret
SLACK_CLIENT_ID=your-slack-client-id
SLACK_CLIENT_SECRET=your-slack-client-secret

# Frontend URL (will update after frontend is deployed)
NEXT_PUBLIC_URL=https://askbiggie-frontend.onrender.com
```

### Health Check
- **Path**: `/api/health`

---

## 🔄 Service 2: Worker (Background Worker)

### Create Service
1. Click **"New +"** → **"Background Worker"**
2. Connect same repository

### Configuration

**Basic Settings:**
- **Name**: `askbiggie-worker`
- **Region**: Same as backend
- **Branch**: `main`
- **Root Directory**: `suna/backend`
- **Runtime**: `Python 3`

**Build & Deploy:**

**Option A: Using Dockerfile (Recommended)**
- **Build Command**: (leave empty)
- **Start Command**: 
```bash
uv run dramatiq --processes 4 --threads 4 run_agent_background
```
- **Dockerfile Path**: `suna/backend/Dockerfile`

**Option B: Using Native Build**
- **Build Command**: 
```bash
pip install uv && uv sync
```
- **Start Command**: 
```bash
uv run dramatiq --processes 4 --threads 4 run_agent_background
```

**Instance Type**: Same or higher than backend (workers can be resource-intensive)

### Environment Variables
Use **EXACTLY THE SAME** environment variables as the Backend API above.

---

## 🎨 Service 3: Frontend (Web Service)

### Create Service
1. Click **"New +"** → **"Web Service"**
2. Connect same repository

### Configuration

**Basic Settings:**
- **Name**: `askbiggie-frontend`
- **Region**: Same as backend for lower latency
- **Branch**: `main`
- **Root Directory**: `suna/frontend`
- **Runtime**: `Node`

**Build & Deploy:**

**Option A: Using Dockerfile (Recommended)**
- **Build Command**: (leave empty)
- **Start Command**: (leave empty)
- **Dockerfile Path**: `suna/frontend/Dockerfile`

**Option B: Using Native Build**
- **Build Command**: 
```bash
npm install && npm run build
```
- **Start Command**: 
```bash
npm start
```

**Instance Type**: Starter should be sufficient

### Environment Variables

```bash
# Supabase (same as backend)
NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key

# Backend API URL (from Service 1)
NEXT_PUBLIC_BACKEND_URL=https://askbiggie-backend.onrender.com/api

# Frontend URL (this service's URL)
NEXT_PUBLIC_URL=https://askbiggie-frontend.onrender.com

# Environment Mode
NEXT_PUBLIC_ENV_MODE=PRODUCTION
```

---

## 🔄 Post-Deployment Steps

### 1. Update Backend CORS Settings

After deploying frontend, update backend's CORS to include your Render frontend URL:

The backend automatically handles CORS for production domains in `api.py`, but you may need to add your Render URL:

```python
# In suna/backend/api.py around line 135-140
allowed_origins = [
    "https://askbiggie.ai", 
    "https://www.askbiggie.ai",
    "https://askbiggie.vercel.app",
    "https://askbiggie.bignoodle.com",
    "https://askbiggie-frontend.onrender.com",  # ADD THIS
]
```

### 2. Update Webhook URLs

Update `WEBHOOK_BASE_URL` in backend environment variables to your actual backend URL:
```
WEBHOOK_BASE_URL=https://askbiggie-backend.onrender.com
```

### 3. Update QStash Webhooks
Go to your QStash dashboard and update webhook endpoints to point to your new backend URL.

### 4. Update Supabase Redirect URLs

1. Go to Supabase Dashboard → Authentication → URL Configuration
2. Add these redirect URLs:
   - `https://askbiggie-frontend.onrender.com/*`
   - `https://askbiggie-frontend.onrender.com/auth/callback`

### 5. Update Google OAuth (if using)

Update your Google OAuth redirect URIs to include:
- `https://askbiggie-frontend.onrender.com/auth/callback`

---

## 🔍 Verification Checklist

After deployment, verify:

- [ ] Backend health check: `https://askbiggie-backend.onrender.com/api/health`
- [ ] Frontend loads: `https://askbiggie-frontend.onrender.com`
- [ ] Redis connection working (check backend logs)
- [ ] RabbitMQ connection working (check backend and worker logs)
- [ ] Worker is processing jobs (check worker logs)
- [ ] Database queries working (try logging in)
- [ ] File uploads working (if applicable)
- [ ] Agent execution working (try creating an agent task)

---

## 🐛 Troubleshooting

### Redis Connection Issues

If you see Redis connection errors:

1. **Get the correct Upstash TCP URL**:
   - Go to Upstash Console → Your Database → Connect
   - Copy the "Redis URL" (not REST URL)
   - Should start with `redis://` or `rediss://`

2. **Verify SSL settings**:
   - Use `rediss://` for TLS (port 6380)
   - Set `REDIS_SSL=true`

### RabbitMQ Connection Issues

1. **Check CloudAMQP credentials** in your dashboard
2. **Verify SSL settings**: Use `amqps://` and port 5671 for TLS
3. **Check logs** for connection errors

### Worker Not Processing Jobs

1. Check worker logs for errors
2. Verify RabbitMQ connection
3. Ensure environment variables match backend exactly
4. Check that worker service is running

### Frontend Can't Connect to Backend

1. Verify `NEXT_PUBLIC_BACKEND_URL` is correct
2. Check CORS settings in backend
3. Verify backend is running and healthy

---

## 📊 Monitoring

### View Logs
- **Backend**: Render Dashboard → askbiggie-backend → Logs
- **Worker**: Render Dashboard → askbiggie-worker → Logs
- **Frontend**: Render Dashboard → askbiggie-frontend → Logs

### Metrics
- Monitor CPU and Memory usage in Render dashboard
- Set up alerts for service failures
- Monitor Redis usage in Upstash dashboard
- Monitor RabbitMQ usage in CloudAMQP dashboard

---

## 💰 Cost Optimization

### Free Tier Considerations
- Render free tier spins down after inactivity (15 min)
- First request after spindown will be slow
- Consider keeping services on paid tier if you need 24/7 uptime

### Scaling
- Start with Starter instances
- Monitor resource usage
- Scale up only when needed
- Worker can be scaled independently

---

## 🔐 Security Best Practices

1. **Never commit .env files**
2. **Use Render's environment variable encryption**
3. **Rotate API keys regularly**
4. **Use TLS for all connections** (Redis, RabbitMQ)
5. **Enable CORS only for trusted domains**
6. **Use strong passwords** for all services
7. **Enable 2FA** on all service accounts

---

## 📝 Next Steps

After deployment is complete:

1. Test all functionality thoroughly
2. Set up custom domain (optional)
3. Configure SSL certificate (automatic on Render)
4. Set up monitoring and alerting
5. Create backup strategy
6. Document your deployment
7. Update README with new URLs

---

## 🆘 Need Help?

- **Render Docs**: https://render.com/docs
- **Upstash Docs**: https://docs.upstash.com/redis
- **CloudAMQP Docs**: https://www.cloudamqp.com/docs/
- **Project Issues**: Create an issue in your GitHub repo

