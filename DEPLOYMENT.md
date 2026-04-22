# SentinelFarm Deployment Guide

## Deployment to Render

### Prerequisites
1. GitHub account with repository containing this code
2. Render account (https://render.com - free tier available)
3. Environment variables ready

### Steps to Deploy

#### 1. Push to GitHub
```bash
git add .
git commit -m "Ready for production deployment"
git push origin main
```

#### 2. Connect to Render
- Visit https://dashboard.render.com
- Click "New +" → "Web Service"
- Connect your GitHub repository
- Select the SentinelFarm repository

#### 3. Configure Deployment
- **Name**: sentinelfarm
- **Environment**: Node
- **Region**: Ohio (or your choice)
- **Branch**: main
- **Build Command**: `cd frontend && npm install && npm run build && cd ../backend && npm install`
- **Start Command**: `cd backend && node server.js`
- **Plan**: Free or Starter (as needed)

#### 4. Set Environment Variables
In Render dashboard, add these environment variables:

**Required:**
- `DATABASE_URL` - Your PostgreSQL connection string (Supabase)
- `JWT_SECRET` - Your JWT secret key
- `GEMINI_API_KEY` - Your Google Generative AI API key
- `GOOGLE_SERVICE_ACCOUNT_KEY` - Your Earth Engine service account JSON

**Auto-configured:**
- `NODE_ENV` = production
- `PORT` = 3001
- `FLASK_API_URL` = http://localhost:5001

#### 5. Deploy
- Click "Deploy"
- Wait for build to complete (5-10 minutes)
- Access your site at: `https://sentinelfarm.onrender.com`

### Environment Variables Needed

```
DATABASE_URL=postgresql://postgres:[password]@[host]:[port]/postgres
JWT_SECRET=your-very-secure-random-string
GEMINI_API_KEY=your-google-generative-ai-api-key
GOOGLE_SERVICE_ACCOUNT_KEY={"type":"service_account",...}
```

### Troubleshooting

**Build fails:**
- Check that frontend/build exists or runs `npm run build`
- Verify all dependencies are in package.json

**Service won't start:**
- Check server logs in Render dashboard
- Verify DATABASE_URL is correct
- Ensure PORT is set to 3001

**Database connection issues:**
- Verify DATABASE_URL format
- Check if Supabase is accessible from Render region
- Add Render IP to Supabase allowlist if needed

### Production Checklist

- ✅ Environment variables set in Render
- ✅ Frontend built and optimized
- ✅ Database migrations completed
- ✅ Earth Engine credentials configured
- ✅ CORS properly configured
- ✅ SSL/HTTPS enabled (automatic on Render)
- ✅ Health checks enabled
- ✅ Logs accessible in dashboard

### Monitoring

- View logs: Render dashboard → Logs tab
- Monitor uptime: Render dashboard → Metrics tab
- Set up alerts for deployment failures

### Deployment to Other Platforms

**Heroku:**
```bash
heroku create sentinelfarm
git push heroku main
```

**AWS (Elastic Beanstalk):**
```bash
eb init sentinelfarm --platform node.js
eb create sentinelfarm-env
eb deploy
```

**Vercel + external backend:**
- Deploy frontend to Vercel
- Deploy backend to Render or Heroku
- Configure frontend API endpoint in environment

---

*Last updated: April 22, 2026*
