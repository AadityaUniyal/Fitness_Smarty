# Smarty-Reco: Technical Architecture & AI Models

This document outlines the technical details, technology stack, and AI models used in the Smarty-Reco application.

## 🏗️ System Overview

Smarty-Reco is a comprehensive fitness and nutrition platform that utilizes a **Hybrid AI Architecture**. It combines cloud-based Large Language Models (LLMs) for complex reasoning with local, efficient models for real-time analysis and personalization.

## 🧠 AI & Machine Learning Models

### 1. Vision & Meal Analysis
- **Primary Model:** **Google Gemini 1.5 Flash**
  - **Purpose:** Comprehensive meal analysis from photos. It identifies food items, estimates portions, calculates nutrition (calories, macros), and assesses meal quality.
  - **Implementation:** `gemini_meal_scanner.py`, `geminiService.ts`
  - **Why:** High accuracy, multimodal capabilities, and fast inference for complex visual tasks.

### 2. Real-Time Object Detection
- **Model:** **YOLOv8 (You Only Look Once)**
  - **Framework:** Ultralytics / PyTorch
  - **Purpose:** Fast, on-device (or low-latency server) detection of food items with bounding boxes.
  - **Implementation:** `yolo_food_detector.py`
  - **Why:** Real-time performance for live camera feeds and immediate feedback.
  - **Status:** Integrated with fallback to mock/pretrained models if custom weights are missing.

### 3. Predictive Analytics
- **Model:** **LSTM (Long Short-Term Memory)**
  - **Framework:** PyTorch
  - **Purpose:** Time-series forecasting for weight trends and body metrics.
  - **Implementation:** `lstm_predictor.py`
  - **Why:** Captures temporal dependencies in user data to predict future progress based on history.

### 4. Personalization Engine
- **Model:** **Custom Neural Networks**
  - **Framework:** PyTorch / Scikit-learn
  - **Purpose:** "Is this good for YOU?" scoring. Learns from user feedback to tailor recommendations.
  - **Implementation:** `train_neural_model.py`, `recommendation_engine.py`
  - **Performance:** Designed to achieve high accuracy (>98%) on personalized datasets.

## 💻 Technology Stack

### Frontend
- **Framework:** **React 18** with **Vite** (Fast build tool)
- **Language:** TypeScript (Strict typing for reliability)
- **Styling:** **Tailwind CSS** (Utility-first styling) & Vanilla CSS for custom animations.
- **Visualization:** Recharts (Data analytics charts)
- **Auth:** Clerk (User authentication and management)
- **Icons:** Lucide-React

### Backend
- **Framework:** **FastAPI** (High-performance Python web framework)
- **Language:** Python 3.9+
- **ORM:** SQLAlchemy (Database interaction)
- **Validation:** Pydantic (Data validation)

### Database
- **Primary:** **PostgreSQL** (Neon Serverless)
- **Fallback:** SQLite (Local development)
- **Vector Search:** (Planned/Integrated for RAG)

## 🔄 Data Flow

1.  **User Action:** User uploads a meal photo via Frontend.
2.  **Vision Pipeline:** 
    -   Image sent to Backend.
    -   YOLOv8 attempts rapid detection.
    -   Gemini 1.5 Flash performs detailed nutritional analysis.
3.  **Personalization:** neural network evaluates if the meal fits the user's specific BioProfile and goals.
4.  **Storage:** Data logged to PostgreSQL.
5.  **Analytics:** LSTM model updates weight predictions based on the new entry.
6.  **Response:** Frontend displays detailed breakdown and "Good/Bad" verdict.
