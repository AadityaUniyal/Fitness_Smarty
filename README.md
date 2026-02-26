# Fitness Smarty AI

A comprehensive full-stack fitness application with AI-powered meal analysis, personalized recommendations, and workout tracking.

## Features

- 🍽️ **AI Meal Analysis**: Upload meal photos for automatic food detection and nutrition calculation
- 📹 **Live Food Tracking**: Real-time AR food detection and calorie estimation using camera feed
- 📊 **Nutrition Tracking**: Comprehensive food database with detailed nutritional information
- 💪 **Exercise Database**: Extensive exercise library with difficulty classifications
- 🎯 **Goal Management**: Set and track personalized fitness goals
- 📈 **Progress Tracking**: Monitor your fitness journey with detailed analytics
- 🤖 **Smart Recommendations**: AI-powered personalized meal and exercise suggestions
- 🔐 **Secure Authentication**: JWT-based user authentication and authorization

## Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL (Neon) / SQLite (development)
- **ORM**: SQLAlchemy
- **Authentication**: JWT tokens with bcrypt password hashing
- **AI/ML**: Computer vision for food detection, nutrition analysis

### Frontend
- **Framework**: React with TypeScript
- **Build Tool**: Vite
- **UI Components**: Custom components with responsive design
- **State Management**: React hooks
- **API Communication**: Axios

## 📦 Key Packages

### Backend (Python)
| Category | Package | Purpose |
|----------|---------|---------|
| **Core** | `fastapi`, `uvicorn` | High-performance API server |
| **Data** | `sqlalchemy`, `pydantic` | ORM and Data Validation |
| **Vision** | `ultralytics` (YOLOv8), `opencv-python` | Real-time Object Detection |
| **AI/LLM** | `google-generativeai` | Gemini 1.5 Flash Integration |
| **ML** | `torch`, `scikit-learn`, `prophet` | LSTM, Neural Networks, Forecasting |
| **Auth** | `python-jose`, `bcrypt` | Security and Hashing |

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
│   │   ├── database.py            # Database configuration
│   │   ├── auth.py                # Authentication logic
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
- PostgreSQL (optional, SQLite works for development)

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
DATABASE_URL=sqlite:///./smarty_neural_core.db
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

5. Run database migrations:
```bash
python migrations/create_enhanced_schema.py
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
- `POST /auth/register` - Register new user
- `POST /auth/login` - User login
- `POST /auth/token` - Get access token

### Meal Analysis
- `POST /meals/analyze` - Analyze meal photo
- `GET /meals/history` - Get meal history
- `GET /meals/daily-summary` - Get daily nutrition summary

### Food Database
- `GET /nutrition/library` - Get food library
- `GET /nutrition/search` - Search foods
- `GET /nutrition/categories` - Get food categories

### Exercise Database
- `GET /exercise/library` - Get exercise library
- `GET /exercise/search` - Search exercises
- `GET /exercise/categories` - Get exercise categories

### User Profile
- `GET /users/me` - Get current user profile
- `PUT /users/profile` - Update user profile
- `POST /users/goals` - Create fitness goal
- `GET /users/goals` - Get user goals

### Recommendations
- `GET /recommendations` - Get personalized recommendations

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

## Database Schema

The application uses a comprehensive database schema including:
- Users and authentication
- User profiles and goals
- Food items and nutrition facts
- Exercise library
- Meal logs and components
- Recommendations
- Progress tracking

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- USDA FoodData Central for nutrition data
- Computer vision models for food detection
- FastAPI and React communities

## Support

For issues and questions, please open an issue on GitHub.
