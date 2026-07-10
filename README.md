# 🏋️ SMARTY AI – Neural Fitness Intelligence Platform

> **A production-ready, full-stack AI-powered fitness and nutrition platform** that combines machine learning, computer vision, and intelligent recommendation systems to deliver personalized health and fitness guidance.

[![CI](https://github.com/AadityaUniyal/Fitness_Smarty/actions/workflows/ci.yml/badge.svg)](https://github.com/AadityaUniyal/Fitness_Smarty/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![React](https://img.shields.io/badge/React-18-61DAFB)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-blue)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Technology Stack](#-technology-stack)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [Core Modules](#-core-modules)
- [API Documentation](#-api-documentation)
- [Deployment](#-deployment)
- [Environment Variables](#-environment-variables)
- [Testing](#-testing)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🌟 Overview

**SMARTY AI** is an enterprise-grade fitness and nutrition platform that leverages cutting-edge AI technologies to provide:

- **AI-Powered Meal Scanning**: Computer vision (YOLOv8 + Gemini Vision API) for food detection and nutrition analysis
- **Intelligent Workout Planning**: Goal-based exercise recommendations with form correction AI
- **Personalized Coaching**: Real-time voice coaching and AI chat assistant powered by Gemini
- **FemmeCare Integration**: Menstrual cycle tracking with cycle-synced training adjustments
- **Gamification System**: Achievements, badges, streaks, and leaderboards for user engagement
- **Advanced Analytics**: Progress tracking, body measurements, and predictive insights
- **Social Features**: Community feed, challenges, and progress sharing
- **Multi-Platform Support**: Web, mobile-responsive, with wearable device integration

### Live Demo
- **Frontend**: [Deployed on Vercel](https://your-app.vercel.app) *(coming soon)*
- **Backend API**: [API Documentation](https://your-api.com/docs)
- **Database**: Neon PostgreSQL (Serverless)

---

## ✨ Key Features

### 🍽️ Nutrition Intelligence

| Feature | Description | Technology |
|---------|-------------|------------|
| **AI Meal Scanning** | Camera-based food detection and nutrition analysis | YOLOv8, Gemini Vision API |
| **Food Database** | 500+ food items with complete macro profiles | PostgreSQL, USDA Integration |
| **Macro Calculator** | Real-time macro tracking with goal-based targets | Custom Algorithms |
| **Meal Planner** | AI-generated meal plans based on goals and preferences | Gemini AI |
| **Barcode Scanner** | Quick food logging via barcode lookup | OpenFoodFacts API |
| **Smart Portion Control** | Gram-based portion tracking with visual guides | Computer Vision |

### 💪 Workout Intelligence

| Feature | Description | Technology |
|---------|-------------|------------|
| **Goal-Based Exercises** | Exercise recommendations matched to fitness goals | Recommendation Engine |
| **Workout Logging** | Detailed exercise tracking with sets, reps, and calories | REST API + Database |
| **Form Correction AI** | Real-time posture analysis and feedback | MediaPipe, TensorFlow |
| **Quick Workouts** | Pre-built workout routines for different goals | Template System |
| **Progressive Overload** | Automatic weight/rep progression tracking | ML-based Predictions |
| **Workout History** | Complete exercise history with analytics | Time-series Analysis |

### 🤖 AI Coaching

| Feature | Description | Technology |
|---------|-------------|------------|
| **Voice Coaching** | Real-time voice feedback during workouts | Gemini Speech API |
| **Chat Assistant** | 24/7 AI fitness and nutrition advisor | Gemini Pro |
| **Mission Briefings** | Daily tactical fitness directives | Natural Language Generation |
| **Form Analysis** | Biomechanical fault detection | Computer Vision + ML |
| **Recovery Insights** | Mission Readiness Score (MRS) calculation | Multi-factor Analytics |

### 🩺 FemmeCare (Female Health)

| Feature | Description | Technology |
|---------|-------------|------------|
| **Cycle Tracking** | Menstrual cycle logging and predictions | Time-series Forecasting |
| **Symptom Logging** | Track physical and emotional symptoms | Structured Data Storage |
| **Training Adjustments** | Auto-adjust workout intensity based on cycle phase | Adaptive Algorithms |
| **Menopause Support** | Specialized tracking for menopause symptoms | Custom Models |
| **Pregnancy Mode** | Safe exercise recommendations during pregnancy | Medical Guidelines |

### 🎮 Gamification

| Feature | Description | Technology |
|---------|-------------|------------|
| **Achievements** | 19 pre-configured achievements across 5 categories | Threshold-based System |
| **Badges** | 14 badges from Bronze to Diamond tier | Tiered Reward System |
| **Streaks** | Track consecutive workout and nutrition days | Date-based Logic |
| **Points & Levels** | XP system with leveling (100 XP per level) | Progressive Point System |
| **Leaderboards** | Global and friend-based rankings | Real-time Queries |
| **Progress Tracking** | Visual progress on achievements and badges | Percentage Calculations |

### 📊 Analytics & Tracking

| Feature | Description | Technology |
|---------|-------------|------------|
| **Progress Dashboard** | Comprehensive fitness and nutrition metrics | Data Aggregation |
| **Body Measurements** | Track weight, body fat, muscle mass, etc. | Time-series Storage |
| **Weekly Reviews** | AI-generated performance summaries | Natural Language Generation |
| **Calorie Burn Tracking** | Accurate calorie expenditure calculation | Activity Algorithms |
| **Hydration Monitoring** | Water intake tracking with smart reminders | Schedule-based System |
| **Mood & Energy** | Track mental and physical well-being | Sentiment Analysis |

### 👥 Social & Community

| Feature | Description | Technology |
|---------|-------------|------------|
| **Activity Feed** | Share workouts and achievements | Social Graph Database |
| **Challenges** | Group fitness challenges and competitions | Event System |
| **Progress Sharing** | Share transformation photos and stats | Media Storage + CDN |
| **Friend System** | Connect and compete with friends | Social Network Logic |
| **Likes & Comments** | Engage with community posts | Interaction Tracking |

### 🔗 Integrations

| Integration | Description | Status |
|-------------|-------------|--------|
| **Google OAuth** | Sign in with Google | ✅ Live |
| **Apple Sign-In** | Sign in with Apple | ✅ Live |
| **Wearables Sync** | Apple Health, Google Fit, Fitbit | 🚧 In Progress |
| **Email Verification** | SMTP-based email verification | ✅ Live |
| **Push Notifications** | Mobile and web notifications | 🚧 Planned |

---

## 🏗️ Architecture

```mermaid
graph TB
    subgraph "Frontend - React + Vite"
        A[Login/Signup] --> B[Dashboard]
        B --> C[Meal Scanner]
        B --> D[Workout Assistant]
        B --> E[AI Coach]
        B --> F[Analytics]
        B --> G[FemmeCare]
        B --> H[Gamification]
    end

    subgraph "Backend - FastAPI"
        I[Auth Service<br/>JWT + OAuth2]
        J[Meal Analysis<br/>YOLOv8 + Gemini]
        K[Workout Engine<br/>Recommendations]
        L[AI Coach<br/>Gemini API]
        M[Gamification<br/>Achievements & Badges]
        N[Analytics<br/>Data Processing]
        O[Email Service<br/>Verification]
    end

    subgraph "Data Layer"
        P[(Neon PostgreSQL<br/>Cloud Database)]
        Q[Seed Data<br/>Food + Exercise Library]
        R[ML Models<br/>YOLOv8 Weights]
    end

    A --> I
    C --> J
    D --> K
    E --> L
    H --> M
    F --> N
    I --> P
    J --> P
    K --> P
    L --> P
    M --> P
    N --> P
    Q --> P
```

### System Components

1. **Frontend (React 18 + TypeScript + Vite)**
   - Modern, responsive UI with Tailwind CSS
   - Real-time updates and smooth animations
   - Progressive Web App (PWA) support
   - Mobile-first design

2. **Backend (FastAPI + Python 3.10+)**
   - High-performance async API
   - RESTful architecture with OpenAPI docs
   - JWT-based authentication with refresh tokens
   - Rate limiting and security middleware

3. **Database (Neon PostgreSQL - Serverless)**
   - Scalable cloud-hosted database
   - Automatic backups and point-in-time recovery
   - Connection pooling for high performance
   - SSL-encrypted connections

4. **AI/ML Services**
   - **YOLOv8**: Real-time object detection for food items
   - **Gemini Vision API**: Advanced food analysis and nutrition extraction
   - **Gemini Pro**: Conversational AI for coaching
   - **MediaPipe**: Pose detection for form analysis
   - **Custom ML Models**: Recommendation and prediction engines

5. **Infrastructure**
   - **Docker**: Containerized deployment
   - **GitHub Actions**: CI/CD pipeline
   - **Vercel**: Frontend hosting (SSG)
   - **Neon**: Database hosting
   - **S3/Cloudflare**: Media storage and CDN

---

## 🛠️ Technology Stack

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first styling
- **React Router** - Client-side routing
- **Axios** - HTTP client
- **React Query** - Data fetching and caching
- **Zustand** - State management
- **Framer Motion** - Animations

### Backend
- **FastAPI** - Python web framework
- **SQLAlchemy** - ORM
- **Pydantic** - Data validation
- **Alembic** - Database migrations
- **Uvicorn** - ASGI server
- **SlowAPI** - Rate limiting
- **Python-Jose** - JWT handling
- **Bcrypt** - Password hashing
- **Psycopg2** - PostgreSQL adapter

### AI & Machine Learning
- **YOLOv8** - Object detection
- **Gemini Vision API** - Image analysis
- **Gemini Pro** - Natural language processing
- **MediaPipe** - Pose detection
- **TensorFlow** - ML models
- **NumPy & Pandas** - Data processing
- **Scikit-learn** - ML algorithms

### Database & Storage
- **PostgreSQL (Neon)** - Primary database
- **Redis** - Caching (planned)
- **S3/Cloudflare** - Media storage
- **SQLite** - Local development

### DevOps & Tools
- **Docker & Docker Compose** - Containerization
- **GitHub Actions** - CI/CD
- **Pytest** - Testing
- **Black & Flake8** - Code formatting and linting
- **Pre-commit** - Git hooks
- **Vercel** - Frontend deployment

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Node.js 20+** (with npm)
- **PostgreSQL** (or use Neon cloud)
- **Git**

### 1. Clone the Repository

```bash
git clone https://github.com/AadityaUniyal/Fitness_Smarty.git
cd Fitness_Smarty
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements-base.txt

# Copy environment file
copy .env.example .env

# Edit .env with your configuration:
# - DATABASE_URL (Neon PostgreSQL connection string)
# - JWT_SECRET_KEY (generate with: python -c "import secrets; print(secrets.token_urlsafe(64))")
# - GEMINI_API_KEY (from Google AI Studio)
# - GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET (from Google Cloud Console)

# Initialize gamification system
python migrate_gamification.py

# Start the backend server
uvicorn main:app --reload --port 8000
```

Backend will be available at: `http://localhost:8000`
API Documentation: `http://localhost:8000/docs`

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
copy .env.local.example .env.local

# Edit .env.local with:
# VITE_API_URL=http://localhost:8000
# VITE_GOOGLE_CLIENT_ID=your_google_client_id

# Start development server
npm run dev
```

Frontend will be available at: `http://localhost:5173`

### 4. Access the Application

1. Open `http://localhost:5173` in your browser
2. Sign up for a new account or use Google OAuth
3. Complete the onboarding flow
4. Start tracking your fitness journey!

---

## 📁 Project Structure

```
Smarty-reco/
├── backend/                    # FastAPI backend
│   ├── api/                    # API endpoints
│   │   ├── index.py           # Vercel serverless entry
│   │   └── ...
│   ├── app/                    # Core application
│   │   ├── api/               # API routers
│   │   │   ├── auth.py
│   │   │   ├── meals.py
│   │   │   ├── exercises.py
│   │   │   ├── gamification.py
│   │   │   └── ...
│   │   ├── models.py          # SQLAlchemy models
│   │   ├── database.py        # Database configuration
│   │   ├── auth.py            # Authentication logic
│   │   ├── email_service.py   # Email functionality
│   │   ├── gemini_meal_scanner.py  # AI meal analysis
│   │   ├── gamification_service.py  # Gamification logic
│   │   ├── neon_config.py     # Neon DB configuration
│   │   └── ...
│   ├── main.py                # FastAPI application entry
│   ├── Dockerfile             # Production Docker image
│   ├── requirements-base.txt   # Python dependencies
│   ├── vercel.json            # Vercel serverless config
│   └── ...
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── pages/             # React page components
│   │   │   ├── Login.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── MealScanner.tsx
│   │   │   ├── WorkoutAssistant.tsx
│   │   │   └── ...
│   │   ├── components/        # Reusable UI components
│   │   ├── contexts/          # React contexts (Auth, etc.)
│   │   ├── services/          # API service layer
│   │   ├── utils/             # Helper functions
│   │   ├── App.tsx            # Main app component
│   │   └── main.tsx           # Entry point
│   ├── public/                # Static assets
│   ├── Dockerfile             # Production Docker image
│   ├── vite.config.ts         # Vite configuration
│   ├── package.json
│   └── ...
├── docker/                     # Docker orchestration
│   ├── docker-compose.yml     # Production compose file
│   └── nginx.conf             # Nginx configuration
├── .github/
│   └── workflows/
│       ├── ci.yml             # CI/CD pipeline
│       └── pytest.yml         # Python tests
├── docs/                       # Documentation
│   ├── ARCHITECTURE.md        # System architecture
│   ├── TECH_STACK.md          # Technology details
│   ├── CALORIE_TRACKING_GUIDE.md
│   └── GAMIFICATION_GUIDE.md
├── .env.example               # Environment template
├── .gitignore
├── LICENSE
└── README.md
```

---

## 🔧 Core Modules

### Authentication & Authorization
- **JWT-based authentication** with access and refresh tokens
- **OAuth 2.0 integration** (Google, Apple)
- **Email verification** with SMTP
- **Password reset** functionality
- **Role-based access control** (planned)

### Meal Analysis Pipeline
1. User uploads food image
2. YOLOv8 detects food items
3. Gemini Vision API analyzes nutrition
4. Results stored in database
5. Macro recommendations generated
6. Gamification checks triggered

### Workout Recommendation Engine
1. User profile analysis (goals, fitness level)
2. Exercise database query with filters
3. Personalized exercise recommendations
4. Difficulty and progression adjustments
5. Calorie burn calculations
6. Form analysis and corrections

### Gamification System
- **19 Achievements**: Workout, nutrition, streak, and milestone-based
- **14 Badges**: Bronze to Diamond tiers across 4 categories
- **4 Streak Types**: Workout, nutrition, hydration, login
- **Points & Levels**: 100 XP per level progression
- **Real-time unlocking**: Automatic threshold detection
- **Leaderboards**: Global and friend-based rankings

### AI Coaching
- **Real-time voice coaching**: Powered by Gemini Speech API
- **Chat assistant**: 24/7 fitness and nutrition advice
- **Mission briefings**: Daily tactical directives
- **Form analysis**: Biomechanical fault detection
- **Recovery insights**: Mission Readiness Score (MRS)

---

## 📚 API Documentation

### Authentication Endpoints
```http
POST   /api/auth/register          # Register new user
POST   /api/auth/login             # Login with email/password
POST   /api/auth/oauth/google      # Google OAuth login
POST   /api/auth/send-verification # Send email verification
POST   /api/auth/verify-email      # Verify email with code
POST   /api/auth/forgot-password   # Request password reset
POST   /api/auth/reset-password    # Reset password
GET    /api/auth/me                # Get current user
PUT    /api/auth/profile           # Update user profile
```

### Meal & Nutrition Endpoints
```http
POST   /api/meals/analyze          # AI meal analysis (Gemini)
POST   /api/nutrition/cam-detect-log  # Log camera-detected meal
POST   /api/nutrition/calculate-portion  # Calculate portion macros
GET    /api/food/goal/{goal}       # Get goal-based food recommendations
GET    /api/meals/history           # Get meal history
```

### Exercise & Workout Endpoints
```http
GET    /api/exercises/for-goal/{goal}  # Goal-based exercises
POST   /api/workouts/log           # Log completed workout
GET    /api/workouts/history        # Get workout history
GET    /api/exercises/search        # Search exercises
POST   /api/workouts/quick          # Get quick workout
```

### Gamification Endpoints
```http
GET    /api/gamification/users/{user_id}/stats     # Complete stats
GET    /api/gamification/users/{user_id}/summary   # Quick summary
GET    /api/gamification/achievements              # All achievements
GET    /api/gamification/badges                    # All badges
GET    /api/gamification/leaderboard               # Leaderboard
GET    /api/gamification/users/{user_id}/streaks  # User streaks
POST   /api/gamification/users/{user_id}/achievements/check  # Check achievements
```

### AI Coach Endpoints
```http
POST   /api/coach/chat             # Chat with AI coach
GET    /api/neural/briefing        # Get daily mission briefing
GET    /api/neural/recovery        # Mission Readiness Score
GET    /api/neural/integrity       # Kinetic Integrity Score
POST   /api/coach/form-analysis    # Analyze workout form
```

### FemmeCare Endpoints
```http
POST   /api/femmecare/cycle        # Log menstrual cycle
GET    /api/femmecare/predictions  # Cycle predictions
POST   /api/femmecare/symptoms     # Log symptoms
GET    /api/femmecare/insights     # Training adjustments
```

### Analytics Endpoints
```http
GET    /api/analytics/progress     # Progress dashboard
GET    /api/analytics/weekly       # Weekly summary
GET    /api/analytics/trends       # Trend analysis
POST   /api/progress/measurement   # Log body measurement
```

Full API documentation available at `/docs` when running the backend.

---

## 🐳 Deployment

### Docker Deployment

```bash
cd docker

# Copy environment file
copy ../backend/.env.example ../backend/.env
# Edit ../backend/.env with production values

# Build and start containers
docker compose up --build -d

# Check container status
docker compose ps

# View logs
docker compose logs -f

# Stop containers
docker compose down
```

### Vercel Deployment (Frontend)

1. Connect your GitHub repo to Vercel
2. Configure project:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
3. Add environment variables:
   - `VITE_API_URL`: Your backend URL
   - `VITE_GOOGLE_CLIENT_ID`: Google OAuth client ID
4. Deploy

### Vercel Deployment (Backend - Serverless)

1. Create new Vercel project for backend
2. Configure:
   - **Root Directory**: `backend`
   - **Build Command**: Leave empty (Python serverless)
3. Add environment variables:
   - `DATABASE_URL`: Neon PostgreSQL connection
   - `JWT_SECRET_KEY`: JWT secret
   - `GEMINI_API_KEY`: Gemini API key
   - `GOOGLE_CLIENT_ID` & `GOOGLE_CLIENT_SECRET`
   - `ENVIRONMENT=production`
4. Deploy

### Manual Deployment

```bash
# Backend
cd backend
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Frontend
cd frontend
npm run build
# Serve dist/ folder with nginx or your preferred web server
```

---

## 🔐 Environment Variables

### Backend (.env)

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:port/dbname?sslmode=require

# Security
JWT_SECRET_KEY=your_super_secret_jwt_key_here
SECRET_KEY=your_general_secret_key_here
ENVIRONMENT=development  # development, test, production

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Gemini AI
GEMINI_API_KEY=your_gemini_api_key

# Email (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=noreply@smartyai.com
SMTP_FROM_NAME=Smarty AI

# Apple Sign-In (Optional)
APPLE_CLIENT_ID=your_apple_client_id
APPLE_TEAM_ID=your_apple_team_id
APPLE_KEY_ID=your_apple_key_id
APPLE_PRIVATE_KEY=path/to/private_key.p8
```

### Frontend (.env.local)

```bash
# API Configuration
VITE_API_URL=http://localhost:8000

# OAuth
VITE_GOOGLE_CLIENT_ID=your_google_client_id

# Feature Flags (Optional)
VITE_ENABLE_OAUTH=true
VITE_ENABLE_WEARABLES=false
VITE_ENABLE_SOCIAL=true
```

---

## 🧪 Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v

# Run gamification tests
python test_gamification.py
```

### Frontend Tests

```bash
cd frontend

# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run specific test
npm test -- Login.test.tsx

# Run in watch mode
npm test -- --watch
```

### Integration Tests

```bash
# Run E2E tests (if configured)
npm run test:e2e
```

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit your changes**: `git commit -m 'Add amazing feature'`
4. **Push to the branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Code Style

- **Python**: Follow PEP 8, use Black for formatting
- **TypeScript/React**: Follow Airbnb style guide, use Prettier
- **Commits**: Use conventional commit messages

### Testing

- Write unit tests for new features
- Ensure all tests pass before submitting PR
- Maintain or improve code coverage

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](./LICENSE) file for details.

---

## 🙏 Acknowledgments

- **YOLOv8** by Ultralytics for object detection
- **Google Gemini** for AI capabilities
- **Neon** for serverless PostgreSQL
- **FastAPI** for the excellent Python web framework
- **React** team for the UI library
- Open-source community for various libraries and tools

---

## 📞 Support & Contact

- **Issues**: [GitHub Issues](https://github.com/AadityaUniyal/Fitness_Smarty/issues)
- **Discussions**: [GitHub Discussions](https://github.com/AadityaUniyal/Fitness_Smarty/discussions)
- **Email**: support@smartyai.com

---

## 🗺️ Roadmap

### Current Release (v2.0)
- ✅ AI meal scanning with Gemini Vision
- ✅ Goal-based workout recommendations
- ✅ Gamification system (achievements, badges, streaks)
- ✅ FemmeCare cycle tracking
- ✅ Real-time AI coaching
- ✅ Complete authentication system
- ✅ Progress tracking and analytics

### Upcoming (v2.1)
- 🔜 Wearable device integration (Apple Health, Google Fit)
- 🔜 Push notifications (mobile and web)
- 🔜 Social challenges and competitions
- 🔜 Meal planning with shopping lists
- 🔜 Video workout library
- 🔜 Advanced form analysis with pose detection

### Future (v3.0)
- 🔮 AI-powered meal prep guidance
- 🔮 Virtual personal trainer (video calls)
- 🔮 Nutrition supplement recommendations
- 🔮 Integration with gym equipment
- 🔮 AR workout overlays (mobile)
- 🔮 Voice-controlled workout sessions

---

<p align="center">
  <strong>SMARTY AI</strong> — Train Beyond Limits. Intelligently.<br>
  Built with ❤️ by the Smarty AI Team
</p>

<p align="center">
  <a href="#-overview">Back to Top ↑</a>
</p>
