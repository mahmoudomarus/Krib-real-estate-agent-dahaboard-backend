# Render Environment Variables Template

Use this template to set up your environment variables on Render. Copy and paste the values into each service's environment variables section.

## 🔴 IMPORTANT: Get Upstash Redis TCP URL

Before proceeding, you need to get the **TCP connection URL** from Upstash (not the REST URL):

1. Go to: https://console.upstash.com/redis
2. Click on your database: `hardy-wildcat-7433`
3. Go to the **"Connect"** or **"Details"** tab
4. Find the **"Redis URL"** (TLS enabled)
5. It should look like: `rediss://default:YOUR_PASSWORD@hardy-wildcat-7433.upstash.io:6380`

---

## Backend & Worker Environment Variables

Copy these values for **BOTH** Backend and Worker services:

```bash
# Environment Mode
ENV_MODE=production

# ============================================
# Database & Auth - Supabase (FROM YOUR EXISTING .ENV)
# ============================================
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

# ============================================
# Redis - Upstash (GET THE TCP URL!)
# ============================================
# Option 1: Use the full Redis URL (RECOMMENDED)
REDIS_URL=rediss://default:YOUR_PASSWORD@hardy-wildcat-7433.upstash.io:6380

# Option 2: OR use individual settings
# REDIS_HOST=hardy-wildcat-7433.upstash.io
# REDIS_PORT=6380
# REDIS_PASSWORD=your-upstash-password
# REDIS_SSL=true

# ============================================
# RabbitMQ - CloudAMQP (FROM YOUR SCREENSHOT)
# ============================================
# Option 1: Use the full RabbitMQ URL (RECOMMENDED)
RABBITMQ_URL=amqps://jurfbueh:OAmfTSXP5cKYIMnjm3dozpnYvgOS1ReR@horse.lmq.cloudamap.com/jurfbueh

# Option 2: OR use individual settings
# RABBITMQ_HOST=horse.lmq.cloudamap.com
# RABBITMQ_PORT=5671
# RABBITMQ_USER=jurfbueh
# RABBITMQ_PASSWORD=OAmfTSXP5cKYIMnjm3dozpnYvgOS1ReR
# RABBITMQ_VHOST=jurfbueh
# RABBITMQ_USE_SSL=true

# ============================================
# LLM Providers (FROM YOUR EXISTING .ENV)
# ============================================
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
OPENROUTER_API_KEY=
MODEL_TO_USE=anthropic/claude-sonnet-4-20250514

# ============================================
# Search & Scraping (FROM YOUR EXISTING .ENV)
# ============================================
TAVILY_API_KEY=
FIRECRAWL_API_KEY=
FIRECRAWL_URL=https://api.firecrawl.dev

# ============================================
# Agent Execution - Daytona (FROM YOUR EXISTING .ENV)
# ============================================
DAYTONA_API_KEY=
DAYTONA_SERVER_URL=https://app.daytona.io/api
DAYTONA_TARGET=us

# ============================================
# Background Jobs & Webhooks (FROM YOUR EXISTING .ENV)
# ============================================
QSTASH_URL=https://qstash.upstash.io
QSTASH_TOKEN=
QSTASH_CURRENT_SIGNING_KEY=
QSTASH_NEXT_SIGNING_KEY=

# IMPORTANT: Update this after you know your backend URL on Render
# It will be something like: https://askbiggie-backend-XXXXX.onrender.com
WEBHOOK_BASE_URL=https://your-backend-url.onrender.com

# ============================================
# MCP Configuration (FROM YOUR EXISTING .ENV)
# ============================================
MCP_CREDENTIAL_ENCRYPTION_KEY=

# ============================================
# Optional APIs (FROM YOUR EXISTING .ENV)
# ============================================
RAPID_API_KEY=
SMITHERY_API_KEY=

# ============================================
# Stripe (FROM YOUR EXISTING .ENV - IF USING BILLING)
# ============================================
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=

# ============================================
# Optional Integrations (FROM YOUR EXISTING .ENV - IF CONFIGURED)
# ============================================
PIPEDREAM_PROJECT_ID=
PIPEDREAM_CLIENT_ID=
PIPEDREAM_CLIENT_SECRET=
SLACK_CLIENT_ID=
SLACK_CLIENT_SECRET=

# ============================================
# Frontend URL (UPDATE AFTER FRONTEND IS DEPLOYED)
# ============================================
# Will be something like: https://askbiggie-frontend-XXXXX.onrender.com
NEXT_PUBLIC_URL=https://your-frontend-url.onrender.com
```

---

## Frontend Environment Variables

Copy these values for the Frontend service:

```bash
# Node Environment
NODE_ENV=production

# ============================================
# Supabase (FROM YOUR EXISTING .ENV.LOCAL)
# ============================================
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=

# ============================================
# Backend API URL (UPDATE AFTER BACKEND IS DEPLOYED)
# ============================================
# Will be something like: https://askbiggie-backend-XXXXX.onrender.com/api
NEXT_PUBLIC_BACKEND_URL=https://your-backend-url.onrender.com/api

# ============================================
# Frontend URL (THIS SERVICE'S URL)
# ============================================
# Will be something like: https://askbiggie-frontend-XXXXX.onrender.com
NEXT_PUBLIC_URL=https://your-frontend-url.onrender.com

# ============================================
# Environment Mode
# ============================================
NEXT_PUBLIC_ENV_MODE=PRODUCTION
```

---

## 📝 Step-by-Step Process

### 1. Get Upstash Redis TCP URL
- Go to Upstash console
- Get the `rediss://` URL (with TLS)
- Save it for step 3

### 2. Collect Your Existing Environment Variables
- Open your current `.env` file from Heroku/local
- Copy all the API keys you need

### 3. Create Backend Service on Render
- Go to Render Dashboard
- New → Web Service
- Connect your GitHub repo
- Use the environment variables template above
- **IMPORTANT**: Use the Upstash `REDIS_URL` you got in step 1
- **IMPORTANT**: Use the CloudAMQP `RABBITMQ_URL` from the screenshot

### 4. Create Worker Service on Render
- New → Background Worker
- Connect same repo
- Use **SAME** environment variables as Backend

### 5. Create Frontend Service on Render
- New → Web Service
- Connect same repo
- Use the Frontend environment variables template above

### 6. Update Cross-References
After all services are deployed:

1. **Update Backend Environment Variables**:
   - `WEBHOOK_BASE_URL` → Your backend URL
   - `NEXT_PUBLIC_URL` → Your frontend URL

2. **Update Frontend Environment Variables**:
   - `NEXT_PUBLIC_BACKEND_URL` → Your backend URL + `/api`
   - `NEXT_PUBLIC_URL` → Your frontend URL

3. **Redeploy** backend and frontend after updating URLs

---

## 🔍 Quick Checklist

- [ ] Got Upstash Redis TCP URL (rediss://)
- [ ] Copied CloudAMQP RabbitMQ URL from screenshot
- [ ] Collected all API keys from existing .env
- [ ] Created Backend service on Render
- [ ] Created Worker service on Render
- [ ] Created Frontend service on Render
- [ ] Updated WEBHOOK_BASE_URL with actual backend URL
- [ ] Updated NEXT_PUBLIC_BACKEND_URL with actual backend URL
- [ ] Updated NEXT_PUBLIC_URL with actual frontend URL
- [ ] Redeployed services after URL updates
- [ ] Tested backend health endpoint
- [ ] Tested frontend loads correctly
- [ ] Tested user authentication works

---

## 🆘 Need Your Existing Values?

Run these commands to get your current environment variables:

```bash
# From your backend .env file
cd suna/backend
cat .env

# From your frontend .env.local file
cd suna/frontend
cat .env.local
```

Copy the values you need from there!

