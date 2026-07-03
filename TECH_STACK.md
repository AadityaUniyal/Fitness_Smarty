# 🛠️ Tech Stack & Dependencies

Technical breakdown of frameworks, runtimes, and packages driving the Smarty AI ecosystem.

---

## 💻 Frontend (Client-Side)

The frontend is a lightweight Single Page Application built on **React 18** and compiled using **Vite** for optimized assets.

### Core Libraries
* **Framework**: React 18 with TypeScript.
* **Styling**: Vanilla CSS with custom premium material-inspired styling tokens.
* **Visualization**: `recharts` for charting user weight history, calories, and macro breakdown.
* **Icons**: `lucide-react` for responsive icon representation.
* **Authentication**: `@clerk/clerk-react` client-side hooks, with a transparent fallback to local JWT in development.

---

## ⚙️ Backend (Server-Side API)

The backend is built around **FastAPI**, running on a high-throughput **Uvicorn** ASGI server.

### Key Libraries
* **HTTP Server**: `fastapi` and `uvicorn`.
* **Database & ORM**: `sqlalchemy` for relational object mapping, supporting SQLite (development) and Neon Serverless PostgreSQL (production).
* **Security & Auth**: `python-jose` for JWT validation, `bcrypt` for local password hashing.
* **AI & LLM Connectors**: `google-generativeai` client for Gemini API communication.
* **Computer Vision**: `ultralytics` (YOLOv8 implementation) and `opencv-python`.
* **Calculations**: `numpy` and `pandas` for processing local data frames.

---

## 🐳 Containerization & Deployment Infrastructure

* **Docker**: Configured using modular service dockerfiles:
  * [docker/Dockerfile.backend](file:///c:/Users/HP/OneDrive/Desktop/Smarty-reco/docker/Dockerfile.backend): Installs build tools (`build-essential`, `libpq-dev`), graphics dependencies (`libgl1-mesa-glx`), and serves Python via `gunicorn`.
  * [docker/Dockerfile.frontend](file:///c:/Users/HP/OneDrive/Desktop/Smarty-reco/docker/Dockerfile.frontend): Multi-stage node builder producing static files served by an Alpine Nginx image.
  * [docker/Dockerfile.monolithic](file:///c:/Users/HP/OneDrive/Desktop/Smarty-reco/docker/Dockerfile.monolithic): Builds and hosts both static frontend files and API endpoints from a single Python container.
* **Nginx**: Handles reverse proxying and Single Page Application (SPA) routing fallbacks (serving `index.html` on client-side route requests).
