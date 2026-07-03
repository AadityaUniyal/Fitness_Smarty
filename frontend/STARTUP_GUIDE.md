# Frontend Setup & Running Guide

## Prerequisites
- Node.js 16+ (recommended 18+)
- npm 8+ or yarn

## Step 1: Install Dependencies

```bash
cd frontend
npm install
```

### Common Issues:
- If installation is slow, use: `npm install --legacy-peer-deps`
- If you see peer dependency warnings, they're usually safe to ignore

## Step 2: Configure Environment Variables

Create a `.env.local` file in the `frontend/` directory:

```bash
# Frontend API Configuration
VITE_API_BASE_URL=http://localhost:8000
VITE_API_TIMEOUT=30000

# Clerk Authentication (optional - leave blank for dev mode)
VITE_CLERK_PUBLISHABLE_KEY=

# Gemini runs through the backend. Set GEMINI_API_KEY in backend/.env.

# App Configuration
VITE_APP_NAME=Smarty AI
VITE_APP_VERSION=1.0.0
```

**Note:** If `VITE_CLERK_PUBLISHABLE_KEY` is not set, the app runs in **demo mode** without authentication requirements.

## Step 3: Start Development Server

```bash
npm run dev
```

The frontend will be available at **http://localhost:5173**

## Step 4: Verify Setup

1. **Check Console:**
   - Open browser DevTools (F12)
   - Look for any import or API errors
   - Should see: `[Smarty AI] Running in dev mode (no Clerk key). Auth bypassed.`

2. **Test Backend Connection:**
   - Visit: http://localhost:5173
   - If backend is running, API calls should work
   - Check Network tab in DevTools for successful API responses

## Available Commands

```bash
# Development (with hot reload)
npm run dev

# Production build
npm run build

# Preview production build locally
npm run preview

# Run tests
npm test

# Watch tests
npm test:watch

# Test coverage
npm test:coverage

# Type check (if you want to catch TypeScript errors)
npx tsc --noEmit
```

## Configuration

### API Integration

The frontend is configured to connect to the backend at `http://localhost:8000` by default.

To change:
1. Edit `.env.local`
2. Set `VITE_API_BASE_URL` to your backend URL
3. Restart the dev server

### Authentication

**With Clerk (Production):**
1. Get `VITE_CLERK_PUBLISHABLE_KEY` from https://dashboard.clerk.com
2. Set it in `.env.local`
3. Restart the app

**Without Clerk (Development):**
- Leave `VITE_CLERK_PUBLISHABLE_KEY` empty
- App runs in demo mode with bypassed auth
- All routes are accessible

## Troubleshooting

### Issue: "Cannot find module" errors
**Solution:** 
```bash
rm -rf node_modules package-lock.json
npm install
```

### Issue: Port 5173 already in use
**Solution:** 
```bash
# Use a different port
npm run dev -- --port 5174
```

### Issue: API requests failing
**Solution:**
1. Verify backend is running: `curl http://localhost:8000/health`
2. Check `VITE_API_BASE_URL` in `.env.local`
3. Check CORS configuration in backend `.env`

### Issue: TypeScript errors in IDE
**Solution:** 
```bash
# Reinstall TypeScript definitions
npm install --save-dev @types/react @types/react-dom
```

## Building for Production

```bash
npm run build
```

This creates a `dist/` folder with optimized assets ready for deployment.

## Docker Setup (Optional)

See `../Dockerfile.frontend` for containerized deployment.

```bash
docker build -f Dockerfile.frontend -t smarty-frontend .
docker run -p 3000:80 smarty-frontend
```

## Next Steps

1. Ensure backend is running (`python main.py`)
2. Start frontend (`npm run dev`)
3. Visit http://localhost:5173
4. Try the following flows:
   - Sign up / Log in (or use demo mode)
   - Upload a meal photo
   - View dashboard and analytics
   - Create a workout plan
   - Check FemmeCare if applicable

## Support

For issues:
1. Check browser console (F12)
2. Check backend logs
3. Verify API endpoints at http://localhost:8000/docs
