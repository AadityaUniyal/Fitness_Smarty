# 🏗️ System Architecture

This document describes the architectural design, component communication, and technical data flow of the Smarty AI Elite Fitness Intelligence Platform.

---

## 🗺️ Architectural Overview

Smarty AI utilizes a modern client-server architecture separating the single-page application (SPA) frontend from the high-performance ASGI backend. 

```mermaid
graph TD
    subgraph Client Layer (Frontend)
        A[React SPA / TypeScript] --> B[Recharts Viz]
        A --> C[Clerk / Local JWT Auth]
    end

    subgraph API Layer (Backend)
        D[FastAPI / Uvicorn] --> E[Auth Guard]
        D --> F[Recommendation Engine]
        D --> G[Meal & Vision Service]
    end

    subgraph AI & ML Layer
        G --> H[YOLOv8 Local Detector]
        G --> I[Gemini Flash Vision]
        F --> J[K-Means User Clustering]
        F --> K[Collaborative Filtering Matrix]
    end

    subgraph Data & Storage Layer
        D --> L[SQLAlchemy ORM]
        L --> M[(Neon PostgreSQL / SQLite)]
        D --> N[USDA FoodData Central API]
    end
```

---

## 🗄️ Database Architecture & Core Models

The storage layer is orchestrated via SQLAlchemy ORM. The relational schema supports target progress tracking, logs, and adaptive biological parameters (e.g., FemmeCare tracking).

* **EnhancedUser**: Stores basic profile data (age, weight, height, gender, activity level) and primary goals.
* **MealLog**: Contains food logs, calorie summaries, macronutrient content, user feedback (like/dislike), and associated image upload references.
* **FoodItem & ExerciseItem**: Seeding entities compiled from USDA and Wger databases to support localized autocomplete queries.
* **UserCluster**: Keeps track of K-Means clustering labels for users, allowing custom recommendations tailored to group personas.

---

## 🤖 AI Services & Intelligent Pipeline

The core intelligence of the platform consists of an ensemble of models and algorithmic engines:

### 1. Hybrid Food Scanner (YOLOv8 + Gemini Flash)
* **Local Computer Vision**: YOLOv8 (PyTorch) processes image uploads locally to locate bounding boxes and identify baseline objects.
* **Generative Refinement**: Gemini Flash analyses the image context to determine exact ingredient breakdown, estimates portion weights, and assigns macronutrient properties.

### 2. Personalization & Adaptation Engines
* **User Clustering**: A K-Means model trained on user profile features (BMI, BMR, TDEE, activity level) classifies users into fitness groups.
* **Collaborative Filtering**: Adapts recommendation lists by analyzing feedback ratings matrices from clustered peers.
* **FemmeCare Cycle Syncing**: An adaptive phase-logic engine that calculates training load and nutrition adjustments based on cycle inputs, exposing standard `iCal (.ics)` feeds for calendar syncing.

---

## 🔐 Security & Request Authentication

* **JWT (JSON Web Tokens)**: Secure token authentication using symmetric encryption (HS256) via PyJWT/python-jose.
* **Clerk integration**: Supports quick authentication offloading in production environments.
* **CORS Middleware**: Strict origin validation restricting resources to trusted hosts in production.
