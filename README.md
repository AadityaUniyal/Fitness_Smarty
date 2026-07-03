# 🧠 Smarty AI — Elite Fitness Intelligence Platform

> Hybrid AI fitness platform with server-side food scanning, personalized workout plans, live AI coaching, and a Neon PostgreSQL backend.

## ✨ Core Features & Implementation Status

| Module | Description | Implementation Status |
|--------|-------------|-----------------------|
| 🤖 **AI Chat & Coach** | Profile-aware Gemini Flash conversation with quick prompts | **Active (Production-Ready)** |
| 📷 **Food Scanner** | Camera-based meal detection (YOLOv8 + Gemini Flash ensemble) | **Active (Server-Side Only)** |
| 💪 **Workout Planner** | Algorithmic workout generation loaded with 300+ exercises | **Active (Rule-Based Engine)** |
| 🥗 **Nutrition Hub** | Daily macro rings, meal logging, USDA library search | **Active (Real USDA FDC API)** |
| 📈 **Progress Tracking** | Weight history, calorie streaks, weekly charts | **Active (Recharts Visualization)**|
| 🌸 **FemmeCare** | Cycle-synced training and nutrition for female health | **Active (Adaptive Phase Logic + iCal Feed)** |
| 📊 **Predictive Analytics** | Time-series forecasting for weight trends and body metrics | **Active (LSTM with Mock Fallback)** |
| 🧬 **Personalization / RL** | DQN optimal meal sequencing & collaborative recommendations | *Scaffolded (Development Mock)* |
| 🔐 **Auth & Security** | JWT bcrypt auth + Clerk optional integration, secure env check | **Active (Google Fit Light Theme)** |

## 🏗️ Tech Stack

### Active Core Systems
- **Frontend**: React 18 + TypeScript (Vite), Recharts, Lucide Icons, Premium Material Design Light Theme.
- **Backend API**: FastAPI (Python), Uvicorn ASGI server, CORS security configuration.
- **Database / ORM**: Neon Serverless PostgreSQL / SQLite (local dev), SQLAlchemy.
- **Integrations**: Google GenAI SDK (server-side Gemini Flash), USDA FoodData Central (with rate-limiting & retries).

### Machine Learning & Scaffolding
- **Active Vision Models**: YOLOv8 (Ultralytics / PyTorch) running COCO-pretrained weights as general detector + Gemini Flash vision.
- **Scaffolded Modules (Mocks)**: Reinforcement Learning (DQN meal sequencing), Collaborative Filtering (personalization), BERT (recipe processing), CLIP (semantic search), SHAP (AI explainability).

## 📦 Key Packages & Model Status

### Backend (Python)
| Category | Package | Purpose | Status |
|----------|---------|---------|--------|
| **Core** | `fastapi`, `uvicorn` | High-performance API server | **Production-Ready** |
| **Data** | `sqlalchemy`, `pydantic` | ORM and Data Validation | **Production-Ready** |
| **Vision** | `ultralytics`, `opencv-python` | Object Detection & Fallbacks | **Active (COCO Fallback)** |
| **AI/LLM** | `google-generativeai` | Gemini Flash Integration | **Production-Ready** |
| **Time-Series**| `torch` | LSTM Weight Forecasting | **Active (7-day history req.)** |
| **ML Scaffold**| `scikit-learn`, `prophet` | Personalization & Forecast Mocks | *Scaffolded / Mock* |
| **Auth** | `python-jose`, `bcrypt` | Security and JWT Hashing | **Production-Ready** |


### Frontend (TypeScript)
| Category | Package | Purpose |
|----------|---------|---------|
| **Framework** | `react`, `vite` | UI Library and Build Tool |
| **Styling** | `tailwindcss`, `lucide-react` | Utility CSS and Icons |
| **Visualization** | `recharts` | Analytics Charts |
| **Auth** | `@clerk/clerk-react` | User Authentication |
| **AI** | `@google/genai` | Google AI SDK |

## Project Structure

```
fitness-smarty-ai/
├── backend/
│   ├── app/
│   │   ├── models.py              # Database models
│   │   ├── schemas.py             # Pydantic schemas
│   │   ├── database.py            # Database configuration & seeding
│   │   ├── auth.py                # Authentication & JWT handler
│   │   ├── meal_analysis_service.py
│   │   ├── food_service.py
│   │   ├── exercise_service.py
│   │   ├── user_profile_service.py
│   │   ├── recommendation_engine.py
│   │   └── ...
│   ├── migrations/                # Database migrations
│   ├── main.py                    # FastAPI application entry
│   ├── server.py                  # Server configuration
│   └── requirements.txt           # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/            # React components
│   │   ├── FemmeCare.tsx          # Dedicated female health dashboard
│   │   ├── services/              # API services
│   │   ├── hooks/                 # Custom React hooks
│   │   ├── App.tsx                # Main application
│   │   └── ...
│   ├── package.json               # Node dependencies
│   └── vite.config.ts             # Vite configuration
└── meal_images/                   # Uploaded meal images
```

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 16+
- PostgreSQL (Neon Serverless PostgreSQL recommended)

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the backend directory:
```env
DATABASE_URL=postgresql://neondb_owner:npg_roH2CA1qBcIU@ep-orange-field-amzn4w4x.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require
JWT_SECRET_KEY=your-secret-key-here
ENVIRONMENT=development
GEMINI_API_KEY=your-gemini-api-key-here
```

5. Run database initialization and seeds:
```bash
python init_database.py
```

6. Start the backend server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:5173`

## API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Key API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `POST /api/auth/token` - Get access token

### Meal Analysis
- `POST /api/meals/analyze` - Analyze meal photo
- `GET /api/meals/history` - Get meal history
- `GET /api/meals/daily-summary` - Get daily nutrition summary

### Food Database
- `GET /api/nutrition/library` - Get food library
- `GET /api/nutrition/search` - Search foods
- `GET /api/nutrition/categories` - Get food categories

### Exercise Database
- `GET /api/exercise/library` - Get exercise library
- `GET /api/exercise/search` - Search exercises
- `GET /api/exercise/categories` - Get exercise categories

### User Profile
- `GET /api/users/me` - Get current user profile
- `PUT /api/users/profile` - Update user profile
- `POST /api/users/goals` - Create fitness goal
- `GET /api/users/goals` - Get user goals

### Recommendations & Female Health
- `GET /api/recommendations` - Get personalized recommendations
- `GET /api/female/cycle-phase/{user_id}` - Get cycle-synced advice
- `POST /api/female/log-period/{user_id}` - Log new menstrual cycle
- `GET /api/female/calendar-feed/{user_id}` - Get standard iCal (.ics) calendar feed for Google Calendar

## Development

### Running Tests

Backend:
```bash
cd backend
pytest
```

Frontend:
```bash
cd frontend
npm test
```

### Code Style

Backend:
- Follow PEP 8 guidelines
- Use type hints
- Document functions with docstrings

Frontend:
- Follow TypeScript best practices
- Use functional components with hooks
- Maintain component modularity

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- USDA FoodData Central for nutrition data
- Computer vision models for food detection
- FastAPI and React communities

## Support

For issues and questions, please open an issue on GitHub.

